
import time
import queue

import cv2

import camera
import save_robot
import bottle_svr
import fiducial
import calibrator


class AbortException(Exception):
    """ All calibration is broken"""
    pass

class StateContext:
    def __init__(self, robot, camera, event_queue):
        self.robot = robot
        self.camera = camera
        self.event_queue = event_queue

        self.data = {
        }

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
            },
            "state": "idle",
        }

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

        except calibrator.CalibrationError as e:
            print(f"Sorry calibration failed: {e}")
            return self.idle_state
        except AbortException:
            return self.idle_state

        return self.setup_state

    def setup_state(self):

        self.nav["state"] = "setup"

        try:
            item = self.event_queue.get()
            if item["type"] == "setpos":

                x = item["x"]
                y = item["y"]

                self.nav["camera"]["x"] = float(x)
                self.nav["camera"]["y"] = float(y)

                self.robot.drive(x,y)
                self.robot.flush()

                time.sleep(0.5)
                cache = self.camera.cache
                cam_image = cv2.cvtColor(cache["image"], cv2.COLOR_GRAY2BGR)

                try:
                    self.nav["detection"]["fiducial"] =  self.fd(cam_image, (x, y))
                except fiducial.NoFiducialFoundException:
                    self.nav["detection"]["fiducial"] = (0, 0)

            elif item["type"] == "setfiducial":
                self.nav["pcb"]["fiducials"][item["id"]] = (item["x"], item["y"])
                transform, mse = fiducial.get_transform(self.nav["pcb"]["fiducials"])
                self.nav["pcb"]["transform"] = transform
                self.nav["pcb"]["transform_mse"] = float(mse)

            elif item["type"] == "run":
                return self.init_state

        except AbortException:
            return self.idle_state

        return self.setup_state

    def run_state(self):

        self.nav["state"] = "run"

        try:

            print("get next part information")

            print("pick part")

            print("place part")

            item = self.event_queue.get(block=False)
            if item is not None:
                if item["type"] == "run":
                    return self.init_state
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