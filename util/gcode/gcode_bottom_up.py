#generate Gcode file to manufacture the bottom up bracket from cast acrylic (plexiglas)
#use 'python gcode_bottom_up.py | tee output.gcode' to generate a file
#use a endmill with the radius of the endmill variable
#ftobler

from gcode_gen import gcode
import math

endmill = 1.25  #radius
endmill_rough = endmill + 0.2


g = gcode(lift=5, f_mill=500)




def circular_hole(x, y, r, depth, passes):
    '''for i in range(passes):
        d = (i+1)/passes*depth
        g.mill_circle(x, y, d, r - endmill_rough)
    g.mill_circle(x, y, depth, r - endmill)
'''
    g.mill_hole(x, y, depth+0.2, r-endmill_rough)
    g.mill_hole(x, y, depth, r-endmill)

#hole in the middle
circular_hole(25.0, 50.0, 33/2, -3.0, 3)

#bolt pattern for lamp
for i in range(4):
    deg = i*360/4+45
    x = math.sin(deg/360*2*math.pi)*14*math.sqrt(2) + 25
    y = math.cos(deg/360*2*math.pi)*14*math.sqrt(2) + 50
    #circular_hole(x, y, 2.5/2, -3.0, 3)
    g.travel(x, y)
    g.mill(x, y, -1)
    g.travel(x, y)
    g.mill(x, y, -2)
    g.travel(x, y)
    g.mill(x, y, -3)
    circular_hole(x, y, 4.5/2, -1.5, 2)

#bolt pattern for mount
for i in range(2):
    for j in range(2):
        x = 5+40*i
        y = 25+50*j
        circular_hole(x, y, 3.3/2, -3.0, 3)
        circular_hole(x, y, 4.8/2, -1.5, 2)
        circular_hole(x, y, 6.3/2, -1.5, 2)


#cut the stock in half
for i in range(6):
    g.travel(0-endmill_rough, -3)
    g.mill(0-endmill_rough, 103, (-i-1)/2)
g.travel(0-endmill, -3)
g.mill(0-endmill, 103, -3)



#go to save position and turn off
g.lift = 20.0
g.end()