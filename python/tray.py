import numpy as np

import pick

TYPE_NUMBER = 0

AUTO_DETECT_ZONE_MARGIN = 4

class Tray:

    def __init__(self, picker):
        self.picker = picker
        self.eye = picker.eye #TODO reference directly to self.picker.eye instead of self.eye

    def pick(self, feeder, robot):
        pick_pos = self._find_in_tray(feeder, robot)
        # self.nav["detection"]["part"] = pick_pos #TODO remove nav/detection/part

        x, y, a = pick_pos
        self.picker.pick(robot, x, y, a)

    def _find_in_tray(self, feeder, robot):

        r = self.eye.cam_range + AUTO_DETECT_ZONE_MARGIN

        w = feeder["width"] - r
        h = feeder["height"] - r
        xs = feeder["x"] + r/2 + np.linspace(0, w, 2 + int(np.floor(w/(r*2/3))))
        ys = feeder["y"] + r/2 + np.linspace(0, h, 2 + int(np.floor(h/(r*2/3))))
        tray_angle = feeder["rot"] #FIXME not used yet
        search_positions = np.stack(np.meshgrid(xs, ys), axis=-1).reshape((-1,2))

        # self._plot_search_positions(search_positions, feeder)

        robot.light_topdn(False)

        if "last_found_index" in feeder:
            last_found_index = feeder["last_found_index"]
            search_positions = np.roll(search_positions, -last_found_index, axis=0)
        else:
            last_found_index = 0

        for robot_pos in search_positions:

            robot.drive(*robot_pos)
            image = self.eye.get_valid_image()

            p, a = self.picker.find_components(image)
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

        p, a = self.picker.find_components(image)
        if len(p):
            pos = np.array(p[0])
            pos = tuple((pos / self.eye.res) - (self.eye.cam_range/2) + robot_pos)
        else:
            raise pick.NoPartFoundException("Could not find part to pick")

        robot.light_topdn(True)

        #angle in degrees
        return (pos[0], pos[1], a[0])
