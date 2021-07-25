from pick_plaz_robot import Robot
import math

robot = Robot("COM3")
robot.home()
robot.drive(0,0)
robot.drive(800,0)
robot.drive(800,800)
robot.drive(0,800)

n = 100
r = 400
for i in range(n):
    angle = 2*math.pi*i/n
    x = 400 + math.sin(angle) * r
    y = 400 + math.cos(angle) * r
    robot.drive(x=x, y=y)

robot.done()
print("this line reached")
robot.vacuum(True)
robot.drive(10,10)
robot.vacuum(False)
