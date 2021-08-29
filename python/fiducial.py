
import calibrator

import cv2
import numpy as np

import debug

class NoFiducialFoundException(Exception):
    pass

class FiducialDetector:

    def __init__(self, cal):

        self.res = 60 # pixel per mm
        self.range = 5 # range in mm

        self.radius = 0.7/2
        self.r_tol= 0.2

        self.h = calibrator.Homography(cal, self.res, (self.res*self.range,self.res*self.range))
        self.ip = calibrator.ImageProjector(self.h)

    def __call__(self, camera_image, robot_pos):

        image_color = self.ip.project(camera_image)
        image = image_color[..., 0]


        # image = cv2.medianBlur(image,5)
        image = cv2.GaussianBlur(image,(5, 5), 1, 1)

        _, image = cv2.threshold(image, 50, 255, cv2.THRESH_BINARY)

        debug.set_image("FiducialDetector", cv2.cvtColor(image, cv2.COLOR_GRAY2BGR))

        circles = cv2.HoughCircles(image,cv2.HOUGH_GRADIENT,1,0.1,
                            param1=50,param2=10, # 50,20
                            minRadius=int((self.radius - self.r_tol) * self.res),
                            maxRadius=int((self.radius + self.r_tol) * self.res))

        image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)

        if circles is not None:
            circles = np.uint16(np.around(circles))
            for i in circles[0,:][:1]:
                # draw the outer circle
                image = cv2.circle(image,(i[0],i[1]),i[2],(0,255,0),1)
                # draw the center of the circle
                image = cv2.circle(image,(i[0],i[1]),2,(0,0,255),3)

            debug.set_image("FiducialDetector2", image)

            pos = tuple((i[:2] / self.res) - (self.range/2) + robot_pos)
            return pos

        raise NoFiducialFoundException("No fiducial found")

def get_transform(fid_map, bom):
    """
    Fit transform between fiducials and robot coordinates

    Return transform as used by cairo and mean squared error in mm^2"""

    import json

    with open("web/api/data.json", "r") as f:
        data = json.load(f)

    bot_pos = []
    fid_pos = []
    for x in bom:
        if x["fiducial"]:
            for id, pos in fid_map.items():
                part =  x["parts"][id]
                bot_pos.append(pos)
                fid_pos.append((float(part["x"]), float(part["y"])))

    fid_pos = np.asarray(fid_pos)
    bot_pos = np.asarray(bot_pos)

    n_points = len(fid_pos)
    if n_points >= 3:
        m, mse = calibrator.fit_affine(fid_pos, bot_pos)
    elif n_points == 2:
        m, mse = calibrator.fit_scaled_rigid(fid_pos, bot_pos)
    elif n_points == 1:
        m, mse = calibrator.fit_translation(fid_pos, bot_pos)
    else:
        m, mse = np.eye(3), 0

    t = tuple(m[:2].T.flatten())

    return t, mse

if __name__ == "__main__":
    get_transform(None)