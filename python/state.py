
import time
import queue
import pickle

import cv2
import numpy as np

import camera
import save_robot
import bottle_svr
import fiducial
import calibrator
import pick
import camera_cal
import data_manager
import debug

class AbortException(Exception):
    """ All calibration is broken"""
    pass

class StateContext:
    def __init__(self, robot, camera, context, event_queue):
        self.robot = robot
        self.camera = camera
        self.event_queue = event_queue
        self.context = context

        self.alert_id = 0

        self.nav = {
            "camera": {
                "x": 0,
                "y": 0,
                "width": 35.0,
                "height": 35.0,
                "res": 20, # resolution in pixel per millimeter
                "framenr": 1245,
            },
            "bed": {
                "x": -0.0,
                "y": -0.0,
                "width": 400,
                "height": 400,
            },
            "pcb": {
                "transform": [1, 0, 0, -1, 10, -10],
                "transform_mse" : 0.1,
                "fiducials": {},
            },
            # "pcb": {
            #     "transform": [0.7731953990297232, 0.6349855425247388, 0.6334672579790972, -0.7721192569425455, 58.60784553169759, 195.32190030743706],
            #     "transform_mse": 2.271919407036514e-26,
            #     "fiducials": {
            #         "V1": [76.68486786123627, 191.42850482080448],
            #         "V2": [62.53430535086904, 213.40856212888522],
            #         "V3": [40.5308232021589, 199.21529579406945]
            #     }
            # },
            "detection": {
                "fiducial": [0, 0],
                "part" : [0,0,0],
            },
            "state": "idle",
        }

        self.robot.pos_logger = self.nav["camera"]

        self.cal = None
        self.ip = None
        self.fd = None

        self._center_pcb()

    def _center_pcb(self):
        positions = []
        for part in self.context["bom"]:
            for designator in part["designators"].values():
                if "x" in designator:
                    positions.append((float(designator["x"]), float(designator["y"])))
        positions = np.asarray(positions)
        bed_center = [self.nav["bed"]["width"] / 2, self.nav["bed"]["height"] / 2]
        x, y = -(np.min(positions, axis=0) + np.max(positions, axis=0)) / 2 + bed_center
        self.nav["pcb"]["transform"] = [1, 0, 0, -1, float(x), float(y)]

    def get_cam(self):

        cam_image = self.camera.cache["image"]
        cam_image = cv2.cvtColor(cam_image, cv2.COLOR_GRAY2BGR)
        if self.ip is not None:
            cam_image = self.ip.project(cam_image)
        else:
            cam_image = cam_image
        return cam_image

    def run(self):

        state = self.init_state
        while(True):
            state = state()

    def idle_state(self):

        self.nav["state"] = "idle"

        item = self.event_queue.get()
        if item["type"] == "init":
            return self.init_state
        else:
            self._handle_common_event(item)

        return self.idle_state

    def init_state(self):

        self.nav["state"] = "init"

        try:
            self.robot.vacuum(False)
            self.robot.valve(False)
            self.robot.home()
            self.robot.light_topdn(True)

            try:
                with open("cal.pkl", "rb") as f:
                    self.cal = pickle.load(f)
            except FileNotFoundError:
                self._push_alert(f"Calibration not found. Using default calibration instead. Please calibrate.")
                with open("default_cal.pkl", "rb") as f:
                    self.cal = pickle.load(f)

            res = self.nav["camera"]["res"]
            width = self.nav["camera"]["width"]
            height = self.nav["camera"]["height"]
            h = calibrator.Homography(self.cal, int(res), (int(res*width),int(res*height)))
            self.ip = calibrator.ImageProjector(h, border_value=(31, 23, 21))
            self.fd = fiducial.FiducialDetector(self.cal)

            self.picker = pick.Picker(self.cal)

        except AbortException as e:
            self._push_alert(e)
            return self.idle_state

        return self.setup_state

    def _pcb2robot(self, x, y):
        m = np.array(self.nav["pcb"]["transform"]).reshape((3,2)).T
        x, y = m[:2,:2] @ (x, y) + m[:2,2]
        return x, y

    def _pcb2robot2(self, x, y, a):
        m = np.array(self.nav["pcb"]["transform"]).reshape((3,2)).T
        a = a * np.pi/180
        x2 = x + np.cos(a)
        y2 = y + np.sin(a)

        x, y = m[:2,:2] @ (x, y) + m[:2,2]

        x2, y2 = m[:2,:2] @ (x2, y2) + m[:2,2]

        a = np.arctan2(y2-y, x2-x)
        a = a*180/np.pi

        return x, y, a

    def setup_state(self):

        self.nav["state"] = "setup"

        try:
            item = self.event_queue.get()
            if item["type"] == "setpos":

                x = item["x"]
                y = item["y"]
                if item["system"] == "pcb":
                    x, y = self._pcb2robot(x, y)

                self.robot.drive(x,y)
                self.robot.done()
                time.sleep(0.5)
                cache = self.camera.cache
                cam_image = cv2.cvtColor(cache["image"], cv2.COLOR_GRAY2BGR)

                # p.make_collage(self.robot, self.camera)

                try:
                    self.nav["detection"]["fiducial"] =  self.fd(cam_image, (x, y))
                except fiducial.NoFiducialFoundException:
                    self.nav["detection"]["fiducial"] = (0, 0)

            elif item["type"] == "setfiducial":
                self.nav["pcb"]["fiducials"][item["id"]] = (item["x"], item["y"])
                fiducial_designators = [part["designators"] for part in self.context["bom"] if part["fiducial"]][0]
                transform, mse = fiducial.get_transform(self.nav["pcb"]["fiducials"], fiducial_designators)
                self.nav["pcb"]["transform"] = transform
                self.nav["pcb"]["transform_mse"] = float(mse)

            elif item["type"] == "sequence":
                if item["method"] == "play":
                    return self.run_state
                elif item["method"] == "home":
                    self.robot.home()
                    self.robot.done()
                elif item["method"] == "motor_off":
                    self.robot.steppers(False)
                elif item["method"] == "motor_on":
                    self.robot.steppers(True)
                elif item["method"] == "calibrate_topdn":
                    self.cal = camera_cal.calibrate(self.robot, self.camera)
                    with open("cal.pkl", "wb") as f:
                        pickle.dump(self.cal, f)
                elif item["method"] == "calibrate_picker":
                    try:
                        pos = (self.nav["camera"]["x"], self.nav["camera"]["y"])
                        self.picker.calibrate(pos, self.robot, self.camera)
                    except Exception as e:
                        print(e)
                elif item["method"] == "auto_set_fiducial":

                    fiducial_designators = [part["designators"] for part in self.context["bom"] if part["fiducial"]][0]

                    for name, part in fiducial_designators.items():
                        x, y = self._pcb2robot(float(part["x"]), float(part["y"]))

                        self.robot.drive(x,y)
                        self.robot.done()
                        time.sleep(0.5)
                        cache = self.camera.cache
                        cam_image = cv2.cvtColor(cache["image"], cv2.COLOR_GRAY2BGR)
                        self.nav["pcb"]["fiducials"][name] = self.fd(cam_image, (x, y))

                elif item["method"] == "shutdown":
                    import subprocess
                    process = subprocess.run(['shutdown', '-h', '+0'],
                                              stdout=subprocess.PIPE,
                                              universal_newlines=True)
                    if process.returncode != 0:
                        self._push_alert("Shutdown failed")
            else:
                self._handle_common_event(item)
        except calibrator.CalibrationError as e:
            self._push_alert(f"Calibration Failed: {e}")
        except save_robot.OutOfSaveSpaceException as e:
            self._push_alert(e)
        except fiducial.NoFiducialFoundException as e:
            self._push_alert(e)
        except AbortException as e:
            self._push_alert(e)
            return self.idle_state

        return self.setup_state

    def _get_next_part(self):
        """ find next part in bom that is eligable for placing"""
        for part in self.context["bom"]:
            for name, partdes in part["designators"].items():
                if "x" not in partdes:
                    continue
                part_pos = float(partdes["x"]), float(partdes["y"])
                if partdes["state"] == 1 and partdes["place"] and not part["fiducial"]:
                    return part, partdes
        return None, None


    def run_state(self):

        self.nav["state"] = "run"

        try:

            print("get next part information")

            part, partdes = self._get_next_part()
            if part is None:
                self._push_alert("Placing finished")
                return self.setup_state
            place_pos = float(partdes["x"]), float(partdes["y"])
            place_angle = float(partdes["rot"]) + float(part["rot"])
            tray = self.context["feeder"][part["feeder"]]

            print("get pick position")
            pick_pos = self.picker.pick_from_feeder(tray, self.robot, self.camera)
            self.nav["detection"]["part"] = pick_pos

            print("pick part")
            x, y, a = pick_pos
            self.picker.pick(self.robot, x, y, a)

            print("place part")
            x, y = place_pos
            x, y, place_angle = self._pcb2robot2(x, y, place_angle)
            self.picker.place(self.robot, x, y, -place_angle)

            print("update part")
            partdes["state"] = 2

            try:
                item = self.event_queue.get(block=False)
                if item["type"] == "sequence":
                    if item["method"] == "pause":
                        return self.setup_state
                else:
                    self._handle_common_event(item)
            except queue.Empty:
                pass

        except pick.NoPartFoundException as e:
            self._push_alert(e)
            return self.setup_state
        except save_robot.OutOfSaveSpaceException as e:
            self._push_alert(e)
        except AbortException as e:
            self._push_alert(e)
            return self.idle_state
        return self.run_state

    def _push_alert(self, msg, answers=None):

        if answers is None:
            answers = ["OK"]

        self.nav["alert"] = {
            "id" : self.alert_id,
            "msg" : str(msg),
            "answers" : [str(a) for a in answers],
        }

        self.alert_id += 1

    def _handle_common_event(self, item):
        if item["type"] == "alertquit":
            del self.nav["alert"]

def main(mock=False):
    if mock:
        print("starting in mock mode")

    event_queue = queue.Queue()

    robot = save_robot.SaveRobot(None if mock else "/dev/ttyUSB0")

    if not mock:
        c = camera.CameraThread(0)
    else:
        c = camera.CameraThreadMock()

    d = data_manager.ContextManager()

    s = StateContext(robot, c, d.get(), event_queue)

    b = bottle_svr.BottleServer(
        lambda: s.get_cam(),
        lambda x: event_queue.put(x),
        d,
        lambda: s.nav)

    with c:
        try:
            s.run()
        except KeyboardInterrupt:
            pass

    print("parking robot")

    # park robot
    robot.vacuum(False)
    robot.valve(False)
    robot.drive(z=0)
    robot.drive(5,5) # drive close to home
    robot.done()
    robot.dwell(1000)
    robot.steppers(False)
    robot.light_topdn(False)
    robot.light_botup(False)

    print("finished")

if __name__ == "__main__":
    main()