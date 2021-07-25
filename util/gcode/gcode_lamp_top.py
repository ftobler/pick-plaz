#generate Gcode file to manufacture the 6x parts trays from cast acrylic (plexiglas)
#use 'python gcode_lamp_top.py | tee output.gcode' to generate a file
#use a 30* engraving cutter
#ftobler

from gcode_gen import gcode


g = gcode()

#mill the Grid
depth = -0.6

g.travel(1.5, 5.5)
g.mill(98.49, 5.5, depth)
g.mill(98.49, 94.5, depth)
g.mill(1.5, 94.5, depth)
g.mill(1.5, 5.5, depth)


g.travel(1.5, 35.166666)
g.mill(98.49, 35.166666, depth)

g.travel(1.5, 64.833333)
g.mill(98.49, 64.833333, depth)

g.travel(50, 5.5)
g.mill(50, 94.5, depth)

#mill the engraving
depth = -0.4

g.textsize(4)
text_nr = 0
#text_nr = 6
#text_nr = 12

for i in range(6):
    x = 2.5
    y = 29.5 + ((2-(i % 3)) * 29.66666)
    if i >= 3:
        x += 48.5
    g.text(str(text_nr), x, y, depth)
    text_nr += 1

#go to save position and turn off
g.end()