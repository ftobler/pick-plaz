
from HersheyFonts import HersheyFonts
import matplotlib.pyplot as plt
import math


class gcode:
    lift = 20
    safe = 1
    f_travel = 2000
    f_mill = 100
    is_mill = False

    def __init__(self, lift=20, safe=1, f_travel=2000, f_mill=100):
        self.lift = lift
        self.safe = safe
        self.f_travel = f_travel
        self.f_mill = f_mill
        # Exec G92 if you want to start at your Zero. Otherwise leave out
        # G92 X0 Y0 Z0 ;set current position as zero position
        print("G90 ; Set to Absolute Positioning")
        print("G1 F%f Z%f" % (self.f_travel, self.lift))
        print("M3 S5000 ; Spindle On")
        self.font = HersheyFonts()
        self.font.load_default_font()
        self.font.normalize_rendering(5)

    def travel(self, x, y):
        if self.is_mill:
            self.is_mill = False
            print("G1 F%f Z%f" % (self.f_mill, self.safe))
            print("G1 F%f Z%f" % (self.f_travel, self.lift))
        print("G1 F%f X%f Y%f" % (self.f_travel, x, y))

    def mill(self, x, y, z):
        if not self.is_mill:
            self.is_mill = True
            print("G1 F%f Z%f" % (self.f_travel, self.safe))
            print("G1 F%f Z%f" % (self.f_mill, z))
        print("G1 F%f X%f Y%f Z%f" % (self.f_mill, x, y, z))

    def mill_circle(self, x, y, z, r, angle=360):
        rotations = angle / 360
        n = int(2*r*math.pi*2/0.5*rotations)
        if n < 36:
            n = 36
        self.travel(x, y + r)
        for i in range(n+1):
            rad = 2 * math.pi * i / n * rotations
            self.mill(x + math.sin(rad)*r, y + math.cos(rad)*r, z)

    def mill_hole(self, x, y, z, r, pitch=1.0, r_backout = 0.3):
        #pitch of 2 makes 2mm per rotation
        self.travel(x, y + r)
        z_dist = self.safe - z #positive number, z is given as negative number (depth)
        turns = z_dist/pitch
        n = int(2*r*math.pi*2/1.0*turns)
        if n < 36*turns:
            n = int(36*turns)
        rad = 0
        rads = 2*math.pi*turns
        #spiral down
        for i in range(n+1):
            rad = rads * i / n
            self.mill(x + math.sin(rad)*r, y + math.cos(rad)*r, self.safe - (i / n * z_dist))
        #make additional circle
        n = int(2*r*math.pi*2/1.0)
        if n < 36:
            n = 36
        rad_offset = rad % (2*math.pi)
        for i in range(n+1):
            rad = 2 * math.pi * i / n + rad_offset
            self.mill(x + math.sin(rad)*r, y + math.cos(rad)*r, z)
        self.mill(x + math.sin(rad)*(r-r_backout), y + math.cos(rad)*(r-r_backout), z)

    def textsize(self, height):
        self.font.normalize_rendering(height)

    def text(self, text, x, y, z):
        current = (0,0)
        for (x1, y1), (x2, y2) in self.font.lines_for_text(text):
            if (x1, y1) != current:
                self.travel(x+x1, y+y1)
            self.mill(x+x2, y+y2, z)
            current = (x2, y2)
            #plt.plot((x1, x2), (y1, y2))
        #plt.axis("equal")
        #plt.show()
        pass


    def end(self):
        print("G1 F%f Z%f" % (self.f_travel, self.lift))
        print("M5 ; Spindle Off")
        