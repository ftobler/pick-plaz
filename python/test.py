#from pick_plaz_robot import Robot

import math
from save_robot import SaveRobot


robot = None
try:
    robot = SaveRobot("/dev/ttyUSB0")
except Exception as e:
    print(e)
robot = SaveRobot("COM3")

robot.home()
robot.light_topdn(True)
robot.drive(0,0)
robot.drive(400,0)
robot.drive(400,400)
robot.drive(0,400)

n = 100
r = 200
for i in range(n):
    angle = 2*math.pi*i/n
    x = 200 + math.sin(angle) * r
    y = 200 + math.cos(angle) * r
    robot.drive(x=x, y=y)
    robot.light_topdn(False if i % 2 == 0 else True)

robot.done()
print("this line reached")
robot.vacuum(True)
robot.drive(10,10)
robot.vacuum(False)
robot.light_topdn(False)
robot.steppers(False)
