import time
import hole_finder
import numpy as np


TYPE_NUMBER = 2

# Roll Feeder
# SMD belt is unrolled from a roll and a motor pulls away the backing
# tape and exposes one part. pnp head can then pick it up on always the
# same location.
class Roll:

    def __init__(self, eye, picker):
        self.picker = picker
        self.hole_finder = hole_finder.HoleFinder(eye)

    def set_pickpos(self, state, hole_pos):
        x, y = hole_pos
        state["pickpos"] = [x, y]

    def set_channel(self, state, channel):
        state["channel"] = channel

    def pick(self, state, robot, only_camera=False):
        #setup correct light
        robot.light_topdn(True)
        robot.light_tray(False)

        #drive to the hole and correct its position
        robot.drive(state["pickpos"][0], state["pickpos"][1])
        x, y = self.hole_finder.find_hole()

        x = x + state["offset"][0]
        y = y + state["offset"][1]

        if only_camera == False:
            #normal case
            t = time.time() + 1.5
            self.advance(state, robot)
            self.picker.pick(robot, x, y, state["rot"], done_time=t)
        else:
            robot.drive(x, y)

    def advance(self, state, robot):
        robot.feeder_advance(state["channel"])
        if "pos" in state:
            state["pos"] += 1
        else:
            state["pos"] = 1

    def retract(self, state, robot):
        robot.feeder_advance(state["channel"], direction_forward=False)
        if "pos" in state:
            state["pos"] -= 1
        else:
            state["pos"] = 1



