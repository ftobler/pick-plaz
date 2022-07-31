import cv2
import numpy as np
import debug


class NoBeltHoleFoundException(Exception):
    pass



class HoleFinder:

    def __init__(self, eye):
        self.eye = eye

        self.radius = 1.5/2
        self.r_tol= 0.2

        self.detected_pos = (0,0)


    def find_hole(self):

        image = self.eye.get_valid_image()

        image = cv2.GaussianBlur(image, (5, 5), 1, 1)

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
            debug.set_image("BeltHole", image)

            pos = self.eye.get_pos_from_image_indices(circle[0], circle[1])

            self.detected_pos = pos
            return pos

        raise NoBeltHoleFoundException("No belt found")