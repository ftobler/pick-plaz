
import calibrator

import cv2
import numpy as np

class NoFiducialFoundException(Exception):
    pass

class FiducialDetector:

    def __init__(self, cal):

        self.res = 30 # pixel per mm
        self.range = 5 # range in mm

        self.h = calibrator.Homography(cal, self.res, (self.res*self.range,self.res*self.range))
        self.ip = calibrator.ImageProjector(self.h)

    def __call__(self, camera_image, robot_pos):

        image_color = self.ip.project(camera_image)
        image = image_color[..., 0]


        # image = cv2.medianBlur(image,5)
        image = cv2.GaussianBlur(image,(5, 5), 1, 1)

        _, image = cv2.threshold(image, 100, 255, cv2.THRESH_BINARY)

        cv2.imwrite("b.png", cv2.cvtColor(image, cv2.COLOR_GRAY2BGR))

        circles = cv2.HoughCircles(image,cv2.HOUGH_GRADIENT,1,5,
                            param1=50,param2=10, # 50,20
                            minRadius=5,#int(0.3*self.res),
                            maxRadius=10)#int(0.7*self.res))
        if circles is not None:
            circles = np.uint16(np.around(circles))
            for i in circles[0,:][:1]:
                # draw the outer circle
                image_color = cv2.circle(image_color,(i[0],i[1]),i[2],(0,255,0),2)
                # draw the center of the circle
                image_color = cv2.circle(image_color,(i[0],i[1]),2,(0,0,255),3)

            cv2.imwrite("a.png", image_color)

            pos = tuple((i[:2] / self.res) - (self.range/2) + robot_pos)
            return pos

        raise NoFiducialFoundException("No fiducial found")
