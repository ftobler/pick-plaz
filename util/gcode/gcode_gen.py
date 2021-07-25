
from HersheyFonts import HersheyFonts
import matplotlib.pyplot as plt


class gcode:
    lift = 20
    safe = 1
    f_travel = 2000
    f_mill = 100
    is_mill = False

    def __init__(self):
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
        