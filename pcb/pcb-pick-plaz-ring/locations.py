import math

num = 15
angle = 360 / num
series_r = 3
radius = 12.3
radius_res = 14.0

def torad(deg):
    return deg * math.pi * 2 / 360

netname = 1
designator_resistor = 1
for i in range(num):
    deg = angle * i
    pos_x = math.sin(torad(deg)) * radius
    pos_y = math.cos(torad(deg)) * radius
    print("move d%d (%f %f);" % (i+1, pos_x, pos_y))
    print("rotate =R%d d%d;" % (-deg+90, i+1))
    if (i % 3) == 1 or (i % 3) == 2:
        #handle area
        angle_coeff = 2.3
        radius_add = 4
        radius_sub = 5
        x1 = math.sin(torad(deg + angle/angle_coeff)) * (radius + radius_add)
        y1 = math.cos(torad(deg + angle/angle_coeff)) * (radius + radius_add)
        x2 = math.sin(torad(deg + angle/angle_coeff)) * (radius - radius_sub)
        y2 = math.cos(torad(deg + angle/angle_coeff)) * (radius - radius_sub)
        x3 = math.sin(torad(deg - angle/angle_coeff)) * (radius - radius_sub)
        y3 = math.cos(torad(deg - angle/angle_coeff)) * (radius - radius_sub)
        x4 = math.sin(torad(deg - angle/angle_coeff)) * (radius + radius_add)
        y4 = math.cos(torad(deg - angle/angle_coeff)) * (radius + radius_add)
        print("polygon N$%d 0.2 (%f %f) (%f %f) (%f %f) (%f %f) (%f %f);" % (netname, x1, y1, x2, y2, x3, y3, x4, y4, x1, y1))
        netname += 1
    if (i % 3) == 2:
        #handle led placement
        pos_x = math.sin(torad(deg + angle/2)) * radius_res
        pos_y = math.cos(torad(deg + angle/2)) * radius_res
        print("move r%d (%f %f);" % (designator_resistor, pos_x, pos_y))
        print("rotate =R%d 'r%d';" % (-deg - angle/2 +90, designator_resistor))
        designator_resistor += 1
        netname += 1
    



