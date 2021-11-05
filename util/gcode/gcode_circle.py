from gcode_gen import gcode
import math


r = 3.9
endmill = 1.00  #radius
g = gcode(lift=10, f_mill=500)
depth = -0.3



g.mill_circle( 0.0,  0.0, depth, r - endmill, angle=360*2)
g.mill_circle(12.7,  5.5, depth, r - endmill, angle=360*2)
g.mill_circle(12.7, -5.5, depth, r - endmill, angle=360*2)
g.lift = 10.0
g.end()