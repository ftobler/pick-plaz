
import time
import queue

import cv2
import numpy as np

import camera
import save_robot
import bottle_svr
import fiducial
import calibrator
import pick


class AbortException(Exception):
    """ All calibration is broken"""
    pass

class StateContext:
    def __init__(self, robot, camera, event_queue):
        self.robot = robot
        self.camera = camera
        self.event_queue = event_queue

        import json
        with open("web/api/data.json", "r") as f:
            self.data = json.load(f)

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
            self.robot.home()
            self.robot.light_topdn(True)

            from pcb_cal import calibrate
            self.cal = calibrate(self.robot, self.camera)

            res = self.nav["camera"]["res"]
            width = self.nav["camera"]["width"]
            height = self.nav["camera"]["height"]
            h = calibrator.Homography(self.cal, int(res), (int(res*width),int(res*height)))
            self.ip = calibrator.ImageProjector(h, border_value=(31, 23, 21))
            self.fd = fiducial.FiducialDetector(self.cal)

            self.picker = pick.Picker(self.cal)

        except calibrator.CalibrationError as e:
            print(f"Sorry calibration failed: {e}")
            return self.idle_state
        except AbortException as e:
            print(f"Abort Exception: {e}")
            return self.idle_state

        return self.setup_state

    def _pcb2robot(self, x, y):
        m = np.array(self.nav["pcb"]["transform"]).reshape((3,2)).T
        x, y = m[:2,:2] @ (x, y) + m[:2,2]
        return x, y

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
                self.robot.flush()

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
                transform, mse = fiducial.get_transform(self.nav["pcb"]["fiducials"])
                self.nav["pcb"]["transform"] = transform
                self.nav["pcb"]["transform_mse"] = float(mse)

            elif item["type"] == "sequence":
                if item["method"] == "play":
                    return self.run_state

        except save_robot.OutOfSaveSpaceException as e:
            print(e)
        except AbortException:
            return self.idle_state

        return self.setup_state

    def _get_next_part(self):
        for part in self.data["bom"]:
            for name, partdes in part["parts"].items():
                if "x" not in partdes:
                    continue
                part_pos = float(partdes["x"]), float(partdes["y"])
                if partdes["state"] == 0:
                    return part, partdes
        return None, None


    def run_state(self):

        self.nav["state"] = "run"

        try:

            print("get next part information")

            part, partdes = self._get_next_part()
            if part is None:
                return self.setup_state
            part_pos = float(partdes["x"]), float(partdes["y"])
            tray = self.data["feeder"]["tray 5"] #TODO where to retrive tray of a part


            print("pick part")

            self.nav["detection"]["part"] = self.picker.pick_from_tray(tray, self.robot, self.camera)

            print("place part")

            pos = self._pcb2robot(*part_pos)
            self.robot.drive(*pos)
            self.robot.done()
            time.sleep(1.5)

            partdes["state"] = 1

            try:
                item = self.event_queue.get(block=False)
                if item["type"] == "sequence":
                    if item["method"] == "pause":
                        return self.setup_state
            except queue.Empty:
                pass

        except pick.NoPartFoundException as e:
            print(e)
            return self.setup_state
        except AbortException:
            return self.idle_state
        return self.run_state


def main():

    event_queue = queue.Queue()

    robot = save_robot.SaveRobot("/dev/ttyUSB0")

    c = camera.CameraThread(0)

    s = StateContext(robot, c, event_queue)

    b = bottle_svr.BottleServer(
        lambda: s.get_cam(),
        lambda x: event_queue.put(x),
        lambda: s.data,
        lambda: s.nav)

    with c:
        try:
            s.run()
        except KeyboardInterrupt:
            pass

    print("finished")

    # park robot
    robot.drive(5,5) # drive close to home
    robot.dwell(1000)
    robot.steppers(False)
    robot.light_topdn(False)

if __name__ == "__main__":
    main()