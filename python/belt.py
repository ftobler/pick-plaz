import hole_finder
import numpy as np


TYPE_NUMBER = 1


# Belt feeder.
# SMD belt is in a 3d printed fixture and pnp head advances its position every
# time (belt does not move)
class Belt:

    def __init__(self, eye, picker):
        self.picker = picker
        self.hole_finder = hole_finder.HoleFinder(eye)

    def set_start(self, state, hole_pos):
        x, y = hole_pos
        state["start"] = [x, y]
        state["current_number"] = 0          #the part nuber
        state["current"] = [x, y]
        self._recalculate_fields(state)

    def set_end(self, state, hole_pos):
        x, y = hole_pos
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
        x, y = self.hole_finder.find_hole()

        #save the newly found hole position
        state["current"] = [x, y]

        #pick the part
        if only_camera:
            robot.drive(pick_pos[0], pick_pos[1])
        else:
            #must apply a slowdown on pick, because some belts are loose in the tray
            #and because the packing tape is missing, the picker could generate enough
            #vibrations that the parts are flying out.
            state["pos"] += 1
            self._apply_general_pick_slowdown(robot, apply=True)
            self.picker.pick(robot, pick_pos[0], pick_pos[1], angle + state["rot"])
            self._apply_general_pick_slowdown(robot, apply=False)

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

    def _apply_general_pick_slowdown(self, robot, apply):
        z_speed = 0.2 if apply else 1.0
        robot.feedrate_multiplier(x=1.0, y=1.0, z=z_speed, e=1.0*12, a=1.0, b=1.0, c=1.0)
