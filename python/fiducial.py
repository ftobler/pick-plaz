
import calibrator

import cv2
import numpy as np

import debug
import math

class NoFiducialFoundException(Exception):
    pass

class FiducialMultiDetector:

    def __init__(self, eye, radius_list=[1, 0.7/2]):
        self.fd = [FiducialDetector(eye, radius=r) for r in radius_list]
        self.eye = eye
        self.shape = eye.get_valid_image().shape

    def __call__(self):
        positions = []
        for fd in self.fd:
            try:
                positions.append(fd())
            except NoFiducialFoundException as _e:
                pass

        if len(positions) == 0:
            raise NoFiducialFoundException("No viable fiducial found")

        center = self.eye.get_pos_from_image_indices(self.shape[0]/2, self.shape[1]/2)
        closest_position = min(positions, key=lambda pos: self.__calculate_distance(center, pos))

        return closest_position

    def __calculate_distance(self, point1, point2):
        return math.sqrt((point1[0] - point2[0]) ** 2 + (point1[1] - point2[1]) ** 2)

class FiducialDetector:

    def __init__(self, eye, radius=0.7/2):

        self.eye = eye

        self.radius = radius # 0.7/2
        self.r_tol= 0.2

    def __call__(self):

        image = self.eye.get_valid_image()

        # image = cv2.medianBlur(image,5)
        image = cv2.GaussianBlur(image,(5, 5), 1, 1)

        _, image = cv2.threshold(image, 50, 255, cv2.THRESH_BINARY)

        circles = cv2.HoughCircles(image,cv2.HOUGH_GRADIENT,1,0.1,
                            param1=50,param2=10, # 50,20
                            minRadius=int((self.radius - self.r_tol) * self.eye.res),
                            maxRadius=int((self.radius + self.r_tol) * self.eye.res))

        image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)

        if circles is not None:
            circles = np.uint16(np.around(circles))
            circle = circles[0,0]

            # draw the outer circle
            image = cv2.circle(image,(circle[0], circle[1]), circle[2], (0,255,0),1)
            # draw the center of the circle
            image = cv2.circle(image,(circle[0], circle[1]), 2, (0,0,255), 3)
            debug.set_image("FiducialDetector", image)

            pos = self.eye.get_pos_from_image_indices(circle[0], circle[1])

            return pos

        raise NoFiducialFoundException("No fiducial found")

def get_transform(fid_map, fiducial_designators):
    """
    Fit transform between fiducials and robot coordinates

    Return affine transform (as used by cairo contect) and mean squared error in mm^2
    """

    bot_pos = np.asarray(list(fid_map.values()))

    fid_pos = np.asarray([
        (float(fiducial_designators[id]["x"]), float(fiducial_designators[id]["y"]))
        for id in fid_map.keys()
    ])

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