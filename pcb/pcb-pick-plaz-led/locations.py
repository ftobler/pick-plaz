


base_x = 8
base_y = 13

increment_x = 12
increment_y = 15

count_x = 8
count_y = 6

netname = 1
designator_led = 1
designator_resistor = 1
for x in range(count_x):
    for y in range(count_y):
        pos_x = base_x + increment_x * x
        pos_y = base_y + increment_y * y
        print("move d%d (%d %d);" % (designator_led, pos_x, pos_y))
        designator_led += 1
        if y == 1 or y == 2 or y == 4 or y == 5:
            x1 = pos_x - 5
            x2 = pos_x + 5
            y1 = pos_y - 7.5
            y2 = pos_y + 7
            print("polygon N$%d 0.2 (%f %f) (%f %f) (%f %f) (%f %f) (%f %f);" % (netname, x1, y1, x1, y2, x2, y2, x2, y1, x1, y1))
            netname += 1
        if y == 2 or y == 5:
            netname += 1
        if y == 2 or y == 5:
            pos_y += 3
            pos_x += 2
            print("move r%d (%d %d);" % (designator_resistor, pos_x, pos_y))
            designator_resistor += 1
        


#polygon N$1 0.2 (-10 -10) (-10 -30) (-50 -30) (-50 -10) (-10 -10) 