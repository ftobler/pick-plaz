
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
        state["start"] = [x, y]
        state["current_number"] = 0          #the part nuber
        state["current"] = [x, y]
        self._recalculate_fields(state)

    def set_end(self, state):
        x, y = self.detected_pos
        state["end"] = [x, y]
        self._recalculate_fields(state)

    def pick(self, state, robot, only_camera=False):

        p_start = np.array(state["start"])    #the start hole of the belt
        p = np.array(state["current"])        #the current hole of the belt
        p_end =np.array(state["end"])         #the last hole of the belt
        p_offset = np.array(state["offset"])  #the pick position offset relative to the hole

        vec = p_end - p  #vector to end
        dx, dy = vec
        angle = np.arctan2(dy, dx) #angle to end

        #next hole offset
        x_pitch = np.cos(angle) * state["pitch"]
        y_pitch = np.sin(angle) * state["pitch"]

        #calculate pick position
        #this is done by rotating the x/y offset by the angle
        rotm = np.array((
            (np.cos(angle), np.sin(angle)),
            (-np.sin(angle), np.cos(angle)),
        ))
        x, y = (rotm @ p_offset[:, None] + p[:, None])[:, 0]
        pick_pos = (float(x), float(y))

        #calculate (x/y) for next hole lookup (camera)
        x = p[0] + x_pitch
        y = p[1] + y_pitch

        #setup correct light
        robot.light_topdn(True)
        robot.light_tray(False)

        #drive to the hole and correct its position
        robot.drive(x, y)
        x, y = self.find_hole()

        #save the newly found hole position
        state["current"] = [x, y]
        state["pos"] += 1

        #pick the part
        #TODO test angle
        if only_camera:
            robot.drive(pick_pos[0], pick_pos[1])
        else:
            self.picker.pick(robot, pick_pos[0], pick_pos[1], angle + state["rot"])

        # self.picker.place(robot, pick_pos[0], pick_pos[1] + 10, 0)


    def recalculate_fields(self, state):
        self._recalculate_fields(state)

    #recalculate capacity and carry over pos or truncate it.
    #reccalculate current-position from pos.
    def _recalculate_fields(self, state):
        p_start = np.array(state["start"])     #the start hole of the belt must be given
        p_end = np.array(state["end"])         #the last hole of the belt must be given
        try:
            pitch = state["pitch"]
        except:
            pitch = 4
            state["pitch"] = pitch

        #calculate the length for the capacity
        length = np.linalg.norm(p_end - p_start)
        count = round(length / pitch)
        state["capacity"] = count

        try:
            pos = state["pos"] #try to read it
            if pos >= count: #max it out
                pos = count
        except:
            pos = 0  #set default value
        state["pos"] = pos

        #re-evaluate current position (without camera)
        vec = p_end - p_start  #vector to end
        dx, dy = vec
        angle = np.arctan2(dy, dx) #angle to end
        x_current = p_start[0] + np.cos(angle) * pitch * pos
        y_current = p_start[1] + np.sin(angle) * pitch * pos
        state["current"] = [x_current, y_current]
