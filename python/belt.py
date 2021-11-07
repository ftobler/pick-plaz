
import cv2
import numpy as np

import debug

class NoBeltHoleFoundException(Exception):
    pass

TYPE_NUMBER = 1

class Belt:

    def __init__(self, eye, picker):
        self.eye = eye
        self.picker = picker

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

    def set_start(self, state):
        x, y = self.detected_pos
        state["x"] = x
        state["y"] = y

    def set_end(self, state):
        x, y = self.detected_pos
        state["x_end"] = x
        state["y_end"] = y

    def pick(self, state, robot):

        p = np.array((state["x"], state["y"]))
        p_end =np.array((state["x_end"], state["y_end"]))
        p_offset = np.array((state["x_offset"], state["y_offset"]))

        vec = p_end - p
        dx, dy = vec
        angle = np.arctan2(dy, dx)

        x_pitch = np.cos(angle) * state["pitch"]
        y_pitch = np.sin(angle) * state["pitch"]

        rotm = np.array((
            (np.cos(angle), np.sin(angle)),
            (-np.sin(angle), np.cos(angle)),
        ))

        x, y = (rotm @ p_offset[:, None] + p[:, None])[:, 0]

        pick_pos = (float(x), float(y))

        x = state["x"] + x_pitch
        y = state["y"] + y_pitch

        robot.drive(x, y)
        x, y = self.find_hole()

        state["x"] = x
        state["y"] = y

        #TODO test angle

        self.picker.pick(robot, pick_pos[0], pick_pos[1], angle)

        # self.picker.place(robot, pick_pos[0], pick_pos[1] + 10, 0)
