
import time

import calibrator

class Eye:

    def __init__(self, robot, camera, cal, res=20, cam_range=20):
        self.robot = robot
        self.camera = camera
        self.res = res # pixel per mm
        self.cam_range = cam_range # image size in mm

        h = calibrator.Homography(cal, self.res, (int(self.res*self.cam_range),int(self.res*self.cam_range)))
        self.ip = calibrator.ImageProjector(h, border_value=(0,0,0))

        self.robot_pos = None

    def get_valid_image(self):
        """ return a corrected grayscale image"""

        self.robot_pos = (
            self.robot.pos_logger["x"],
            self.robot.pos_logger["y"],
        )

        self.robot.done()
        time.sleep(0.6)
        image = self.camera.cache["image"]
        image = self.ip.project(image)
        return image

    def get_pos_from_image_indices(self, index_x, index_y):

        if self.robot_pos is None:
            raise Exception("get_valid_image must be invoked prior to get_pos_from_image_indices")

        return (
            index_x/self.res - self.cam_range/2 + self.robot_pos[0],
            index_y/self.res - self.cam_range/2 + self.robot_pos[1],
        )
