import numpy as np
import math

import pick

TYPE_NUMBER = 0

AUTO_DETECT_ZONE_MARGIN = 4

class Tray:

    def __init__(self, picker):
        self.picker = picker
        self.eye = picker.eye #TODO reference directly to self.picker.eye instead of self.eye

    def pick(self, feeder, robot, only_camera=False):
        pick_pos = self._find_in_tray(feeder, robot)
        # self.nav["detection"]["part"] = pick_pos #TODO remove nav/detection/part

        x, y, a, A = pick_pos
        self.apply_area_slowdown(robot, A)
        if only_camera:
            robot.drive(pick_pos[0], pick_pos[1])
        else:
            self.picker.pick(robot, x, y, a)

    def _find_in_tray(self, feeder, robot):

        r = self.eye.cam_range + AUTO_DETECT_ZONE_MARGIN

        w = feeder["position"][2] - r
        h = feeder["position"][3] - r
        xs = feeder["position"][0] + r/2 + np.linspace(0, w, 2 + int(np.floor(w/(r*2/3))))
        ys = feeder["position"][1] + r/2 + np.linspace(0, h, 2 + int(np.floor(h/(r*2/3))))
        tray_angle = feeder["rot"] #FIXME not used yet
        search_positions = np.stack(np.meshgrid(xs, ys), axis=-1).reshape((-1,2))

        # self._plot_search_positions(search_positions, feeder)

        robot.light_topdn(False)
        robot.light_tray(True)

        if "last_found_index" in feeder:
            last_found_index = feeder["last_found_index"]
            search_positions = np.roll(search_positions, -last_found_index, axis=0)
        else:
            last_found_index = 0

        for robot_pos in search_positions:

            robot.drive(*robot_pos)
            image = self.eye.get_valid_image()

            p, a, _A = self.picker.find_components(image)
            if len(p):
                break
            last_found_index = last_found_index + 1 % len(search_positions)
        else:
            last_found_index = 0
            raise pick.NoPartFoundException("Could not find part to pick")

        feeder["last_found_index"] = last_found_index

        pos = np.array(p[0])
        pos = tuple((pos / self.eye.res) - (self.eye.cam_range/2) + robot_pos)

        #drive to part and measure again without paralax
        robot_pos = pos
        robot.drive(*pos)
        image = self.eye.get_valid_image()

        p, a, A = self.picker.find_components(image)
        if len(p):
            pos = np.array(p[0])
            pos = tuple((pos / self.eye.res) - (self.eye.cam_range/2) + robot_pos)
        else:
            raise pick.NoPartFoundException("Could not find part to pick")

        robot.light_tray(False)
        robot.light_topdn(True)

        #angle in degrees
        return (pos[0], pos[1], a[0], A[0])

    def apply_area_slowdown(self, robot, area):
        size = math.sqrt(area)
        #calculate a speed factor which goes from 1=fast to 0=slowest
        factor = 1.0
        pos_zero = 90 #175
        pos_one = 35   #75
        if size > pos_zero:
            factor = 0.0
        elif size > pos_one:
            #fitting a cosine between (75/1) and (175/0)
            factor = math.cos((size - pos_one) * math.pi / (pos_zero - pos_one)) * 0.5 + 0.5

        rf = factor * 0.95 + 0.05  #rotation factor
        tf = factor * 0.70 + 0.30  #travel factor
        zf = factor * 0.85 + 0.15  #z axies factor
        of = factor * 0.80 + 0.20  #other axies factor
        print("area=%f, size=%f, factor=%f"% (area, size, factor))
        # note: if we ever have a second picker the rotating motor needs also a factor of 12 here
        #       and the STM32 Firmware also needs to reset it correctly.
        robot.feedrate_multiplier(x=tf, y=tf, z=zf, e=rf*12, a=of, b=of, c=of)