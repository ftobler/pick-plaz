
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
import belt
import tray
import eye

class LiveCam:

    def __init__(self, camera, cal, nav_camera):
        self.camera = camera
        res = nav_camera["res"]
        width = nav_camera["width"]
        height = nav_camera["height"]
        h = calibrator.Homography(cal, int(res), (int(res*width),int(res*height)))
        self.ip = calibrator.ImageProjector(h, border_value=(31, 23, 21))

    def get_cam(self):

        cam_image = self.camera.cache["image"]
        cam_image = cv2.cvtColor(cam_image, cv2.COLOR_GRAY2BGR)
        if self.ip is not None:
            cam_image = self.ip.project(cam_image)
        else:
            cam_image = cam_image
        return cam_image

class AbortException(Exception):
    """ All calibration is broken"""
    pass

class StateContext:
    def __init__(self, robot, camera, context, context_manager, event_queue):

        self.robot = robot
        self.camera = camera
        self.event_queue = event_queue
        self.context = context
        self.context_manager = context_manager

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

        #Load camera calibration
        try:
            with open("cal.pkl", "rb") as f:
                self.cal = pickle.load(f)
        except FileNotFoundError:
            self._push_alert(f"Calibration not found. Using default calibration instead. Please calibrate.")
            with open("default_cal.pkl", "rb") as f:
                self.cal = pickle.load(f)

        wide_eye = eye.Eye(self.robot, self.camera, self.cal, res=20, cam_range=20)
        narrow_eye = eye.Eye(self.robot, self.camera, self.cal, res=60, cam_range=5)

        self.live_cam = LiveCam(self.camera, self.cal, self.nav["camera"])
        self.fd = fiducial.FiducialDetector(narrow_eye)
        self.picker = pick.Picker(wide_eye)
        self.belt = belt.Belt(narrow_eye, self.picker)
        self.tray = tray.Tray(self.picker)

        self.center_pcb()

    def center_pcb(self):
        positions = []
        for part in self.context["bom"]:
            for designator in part["designators"].values():
                if "x" in designator:
                    positions.append((float(designator["x"]), float(designator["y"])))
        positions = np.asarray(positions)
        if positions.size != 0:
            bed_center = [self.nav["bed"]["width"] / 2, self.nav["bed"]["height"] / 2]
            x, y = -(np.min(positions, axis=0) + np.max(positions, axis=0)) / 2 + bed_center
            self.nav["pcb"]["transform"] = [1, 0, 0, -1, float(x), float(y)]

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

        except AbortException as e:
            self._push_alert(e)
            return self.idle_state

        return self.setup_state

    def get_cam(self):
        return self.live_cam.get_cam()

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
        """ In this state, the user makes machine setup and can freely roam the pick-platz bed"""

        self.nav["state"] = "setup"

        try:
            item = self.event_queue.get()
            if item["type"] == "setpos":

                x = item["x"]
                y = item["y"]
                if item["system"] == "pcb":
                    x, y = self._pcb2robot(x, y)

                self.robot.default_settings()
                self.robot.drive(x,y)

                # p.make_collage(self.robot, self.camera)

                try:
                    self.belt.find_hole()
                except belt.NoBeltHoleFoundException:
                    pass

                try:
                    self.nav["detection"]["fiducial"] = self.fd()
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
                    self.context_manager.file_save()
                    self._reset_error_parts()
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
                        self.nav["pcb"]["fiducials"][name] = self.fd()

                elif item["method"] == "shutdown":
                    import subprocess
                    process = subprocess.run(['shutdown', '-h', '+0'],
                                              stdout=subprocess.PIPE,
                                              universal_newlines=True)
                    if process.returncode != 0:
                        self._push_alert("Shutdown failed")
                elif item["method"] == "place_part":
                    name = item["param"]
                    part, partdes = self._get_part_from_designator(name)
                    if part != None:
                        try:
                            self._place_part(part, partdes)
                        except Exception as e:
                            self._push_alert(e)
                    else:
                        self._push_alert("designator not found '%s'", name)
                elif item["method"] == "belt_set_start":
                    name = item["param"]
                    self.belt.set_start(self.context["feeder"][name])
                elif item["method"] == "belt_set_end":
                    name = item["param"]
                    self.belt.set_end(self.context["feeder"][name])
                elif item["method"] == "test_feeder":
                    name = item["param"]
                    feeder = self.context["feeder"][name]
                    if feeder["type"] == tray.TYPE_NUMBER:
                        self.tray.pick(feeder, self.robot)
                    elif feeder["type"] == belt.TYPE_NUMBER:
                        self.belt.pick(feeder, self.robot)
                    self.robot.dwell(1000)
                    self.robot.vacuum(False)
                    self.robot.valve(False)
                    self.robot.default_settings()
                    #TODO: place part again
                elif item["method"] == "reset_board":
                    self._reset_for_new_board()
            else:
                self._handle_common_event(item)
        except calibrator.CalibrationError as e:
            self._push_alert(f"Calibration Failed: {e}")
        except save_robot.OutOfSaveSpaceException as e:
            self._push_alert(e)
        except fiducial.NoFiducialFoundException as e:
            self._push_alert(e)
        except pick.NoPartFoundException as e:
            self._push_alert(e)
        except AbortException as e:
            self._push_alert(e)
            return self.idle_state

        return self.setup_state

    def run_state(self):
        """ Parts of the BOM are being pick-and-placed """

        self.nav["state"] = "run"

        try:
            print("get next part information")
            part, partdes = self._get_next_part_from_bom()
            if part is None:
                self._push_alert("Placing finished")
                return self.setup_state
            self._place_part(part, partdes)

        except pick.NoPartFoundException as e:
            self._push_alert(e)
            return self.setup_state
        except save_robot.OutOfSaveSpaceException as e:
            self._push_alert(e)
        except AbortException as e:
            self._push_alert(e)
            return self.idle_state
        return self.run_state

    def _reset_error_parts(self):
        for part in self.context["bom"]:
            for name, partdes in part["designators"].items():
                if partdes["state"] == data_manager.PART_STATE_ERROR and partdes["place"] and not part["fiducial"]:
                    partdes["state"] = data_manager.PART_STATE_READY

    def _reset_for_new_board(self):
        for part in self.context["bom"]:
            for name, partdes in part["designators"].items():
                partdes["state"] = data_manager.PART_STATE_READY

    def _get_part_from_designator(self, name):
        """ find part to place only from its designator """
        for part in self.context["bom"]:
            partdes = part["designators"].get(name)
            if partdes != None:
                return part, partdes
        return None, None

    def _place_part(self, part, partdes):
        self.robot.default_settings()
        partdes["state"] = data_manager.PART_STATE_ERROR

        place_pos = float(partdes["x"]), float(partdes["y"])
        place_angle = float(partdes["rot"]) + float(part["rot"])

        #skip if feeder not defined
        #TODO maybe a bit ugly:
        feeder = part.get("feeder")
        if feeder is None:
            partdes["state"] = data_manager.PART_STATE_ERROR
            return self.run_state
        feeder = self.context["feeder"][feeder]

        self._poll_for_pause()

        print("pick part")
        if feeder["type"] == tray.TYPE_NUMBER:
            self.tray.pick(feeder, self.robot)
        elif feeder["type"] == belt.TYPE_NUMBER:
            self.belt.pick(feeder, self.robot)
        else:
            raise Exception(f"Feeder type {feeder['type']} unknown")

        self._poll_for_pause()

        print("place part")
        x, y = place_pos
        x, y, place_angle = self._pcb2robot2(x, y, place_angle)
        # make sure rotation is minimal
        if place_angle < -180:
            place_angle += 360
        if place_angle > 180:
            place_angle -= 360
        # angle is is pcb coordinates, thus inverted
        self.picker.place(self.robot, x, y, -place_angle)

        print("update part state")
        partdes["state"] = data_manager.PART_STATE_PLACED

        self.robot.default_settings()
        self._poll_for_pause()

    def _poll_for_pause(self):
        try:
            item = self.event_queue.get(block=False)
            if item["type"] == "sequence":
                if item["method"] == "pause":
                    return self.setup_state
            else:
                self._handle_common_event(item)
        except queue.Empty:
            pass

    def _get_next_part_from_bom(self):
        """ find next part in bom that is eligable for placing"""
        for part in self.context["bom"]:
            for name, partdes in part["designators"].items():
                if "x" not in partdes:
                    continue
                if partdes["state"] == data_manager.PART_STATE_READY and partdes["place"] and not part["fiducial"]:
                    return part, partdes
        return None, None

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
            if "alert" in self.nav:
                del self.nav["alert"]

def main(mock=False):
    if mock:
        print("starting in mock mode")

    event_queue = queue.Queue()

    print("connect robot")
    robot = save_robot.SaveRobot(None if mock else "/dev/ttyUSB0")

    print("connect camera")
    if not mock:
        c = camera.CameraThread(0)
    else:
        c = camera.CameraThreadMock()

    d = data_manager.ContextManager()

    s = StateContext(robot, c, d.get(), d, event_queue)

    b = bottle_svr.BottleServer(
        lambda: s.get_cam(),
        lambda x: event_queue.put(x),
        d,
        lambda: s.center_pcb(),
        lambda: s.nav)


    time.sleep(0.1) #give webserver thread time to start
    print("pick-plaz running. press [ctrl]+[C] to shutdown")
    with c:
        try:
            s.run()
        except KeyboardInterrupt:
            pass
    print("")
    print("parking robot")

    d.file_save()

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
