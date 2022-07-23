


TYPE_NUMBER = 2

# Roll Feeder
# SMD belt is unrolled from a roll and a motor pulls away the backing
# tape and exposes one part. pnp head can then pick it up on always the
# same location.
class Roll:

    def __init__(self, eye, picker):
        self.eye = eye
        self.picker = picker

        self.radius = 1.5/2
        self.r_tol= 0.2

        self.detected_pos = (0,0)

    def set_pickpos(self, state, pos):
        x, y = pos
        state["pickpos"] = [x, y]

    def set_channel(self, state, channel):
        state["channel"] = channel

    def pick(self, state, robot):
        pickpos = state["pickpos"]
        if not "rot" in state:
            rot = 0
        else:
            rot = state["rot"]
        self.advance(state, robot)
        self.picker.pick(robot, pickpos[0], pickpos[1], rot)

    def advance(self, state, robot):
        #robot.feeder_advance(state["channel"])
        if "counter" in state:
            state["counter"] += 1
        else:
            state["counter"] = 1
