import time


TYPE_NUMBER = 2

# Roll Feeder
# SMD belt is unrolled from a roll and a motor pulls away the backing
# tape and exposes one part. pnp head can then pick it up on always the
# same location.
class Roll:

    def __init__(self, picker):
        self.picker = picker

        self.radius = 1.5/2
        self.r_tol= 0.2

        self.detected_pos = (0,0)

    def set_pickpos(self, state, pos):
        x = pos["x"]
        y = pos["y"]
        state["pickpos"] = [x, y]

    def set_channel(self, state, channel):
        state["channel"] = channel

    def pick(self, state, robot):
        pickpos = state["pickpos"]
        if not "rot" in state:
            rot = 0
        else:
            rot = state["rot"]
        t = time.time() + 1.5
        self.advance(state, robot)
        self.picker.pick(robot, pickpos[0], pickpos[1], rot, done_time=t)

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
