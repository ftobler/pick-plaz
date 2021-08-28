
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

class AbortException(Exception):
    """ All calibration is broken"""
    pass

DX, DY = 200 - 127.33, 200 - 218.39
PICK_Z = -18

class StateContext:
    def __init__(self, robot, camera, data, event_queue):
        self.robot = robot
        self.camera = camera
        self.event_queue = event_queue
        self.data = data

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

                # self.nav["detection"]["part"] = self.picker.detect_pick_location2((x, y), self.robot, self.camera)
                # p.make_collage(self.robot, self.camera)

                try:
                    self.nav["detection"]["fiducial"] =  self.fd(cam_image, (x, y))
                except fiducial.NoFiducialFoundException:
                    self.nav["detection"]["fiducial"] = (0, 0)

            elif item["type"] == "setfiducial":
                self.nav["pcb"]["fiducials"][item["id"]] = (item["x"], item["y"])
                transform, mse = fiducial.get_transform(self.nav["pcb"]["fiducials"], self.data["bom"])
                self.nav["pcb"]["transform"] = transform
                self.nav["pcb"]["transform_mse"] = float(mse)
            elif item["type"] == "autosetfiducial":
                #TODO make button in web ui, test

                fiducial_parts = [x["parts"] for x in self.data["bom"] if x["fiducial"]]

                for name, part in fiducial_parts.items():
                    x, y = self._pcb2robot(float(part["x"]), float(part["y"]))

                    self.robot.drive(x,y)
                    self.robot.done()

                    time.sleep(0.5)
                    cache = self.camera.cache
                    cam_image = cv2.cvtColor(cache["image"], cv2.COLOR_GRAY2BGR)

                    self.nav["pcb"]["fiducials"][name] = self.fd(cam_image, (x, y))

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
                elif item["method"] == "shutdown":
                    import subprocess
                    process = subprocess.run(['shutdown', '-h', '+0'],
                                              stdout=subprocess.PIPE,
                                              universal_newlines=True)
                    if process.returncode != 0:
                        self._push_alert("Shutdown failed")
        except calibrator.CalibrationError as e:
            self._push_alert(f"Calibration Failed: {e}")
        except save_robot.OutOfSaveSpaceException as e:
            self._push_alert(e)
        except AbortException as e:
            self._push_alert(e)
            return self.idle_state

        return self.setup_state

    def _get_next_part(self):
        """ find next part in bom that is eligable for placing"""
        for part in self.data["bom"]:
            for name, partdes in part["parts"].items():
                if "x" not in partdes:
                    continue
                part_pos = float(partdes["x"]), float(partdes["y"])
                if partdes["state"] == 0 and partdes["place"] and not part["fiducial"]:
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
            place_angle = float(partdes["rot"])
            tray = self.data["feeder"][part["feeder"]]

            print("get pick position")
            pick_pos = self.picker.pick_from_tray(tray, self.robot, self.camera)
            self.nav["detection"]["part"] = pick_pos

            print("pick part")

            self.robot.vacuum(True)
            self.robot.valve(False)
            x, y, angle_rad = pick_pos
            self.robot.drive(x=x+DX, y=y+DY)
            self.robot.drive(e=angle_rad*180/np.pi, f=350)
            self.robot.drive(z=PICK_Z)
            self.robot.done()
            self.robot.valve(True)
            self.robot.drive(z=0)
            self.robot.drive(e=0, f=350)

            print("place part")

            x, y = place_pos
            x, y, place_angle = self._pcb2robot2(x, y, place_angle)
            self.robot.drive(x=x+DX, y=y+DY)
            self.robot.drive(e=-place_angle, f=350)
            self.robot.drive(z=PICK_Z)
            self.robot.done()
            self.robot.valve(False)
            self.robot.vacuum(False)
            self.robot.drive(z=0)

            print("update part")
            partdes["state"] = 1

            try:
                item = self.event_queue.get(block=False)
                if item["type"] == "sequence":
                    if item["method"] == "pause":
                        return self.setup_state
            except queue.Empty:
                pass

        except pick.NoPartFoundException as e:
            self._push_alert(e)
            return self.setup_state
        except AbortException as e:
            self._push_alert(e)
            return self.idle_state
        return self.run_state

    def _push_alert(self, msg, answers=None):
        if "alert" in self.nav:
            uid = self.nav["alert"]["id"] + 1
        else:
            uid = 0

        if answers is None:
            answers = ["ok"]

        self.nav["alert"] = {
            "id" : uid,
            "msg" : str(msg),
            "answers" : [str(a) for a in answers],
        }

def main(mock=False):
    if mock:
        print("starting in mock mode")

    event_queue = queue.Queue()

    robot = save_robot.SaveRobot(None if mock else "/dev/ttyUSB0")

    if not mock:
        c = camera.CameraThread(0)
    else:
        c = camera.CameraThreadMock()

    d = data_manager.DataManager()

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