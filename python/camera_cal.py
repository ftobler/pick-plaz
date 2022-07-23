import pickle
import time
import numpy as np
import cv2
import calibrator

import debug
import config

#should be the center pos of the aruco matrix in machine coordinates
CALIBRATION_POS = config.CALIBRATION_CENTER

aruco_dict = cv2.aruco.Dictionary_get(cv2.aruco.DICT_4X4_100)
arucoParams = cv2.aruco.DetectorParameters_create()

def calibrate(robot, camera):
    """
    Drive to calibration board and calibrate
    """

    #array of positions where a picture is taken. Ehere (0/0) is
    #the aruco center position
    positions = np.array([
        (0,0),
        (1,0),
        (1,1),
        (0,1),
        (-1,1),
        (-1,0),
        (-1,-1),
        (0,-1),
        (1,-1),
    ]) * 10 + np.asarray(CALIBRATION_POS)[np.newaxis]

    markers_corners = []
    marker_ids = []

    robot.light_topdn(True)
    robot.light_tray(False)

    for i, (x,y) in enumerate(positions):
        print(x, y)
        robot.drive(x, y)
        robot.done()
        time.sleep(1.0) #@0.5s camera image was skewed/blurred

        image = cv2.cvtColor(camera.cache["image"], cv2.COLOR_GRAY2BGR)

        arucoParams = cv2.aruco.DetectorParameters_create()
        (corners, ids, rejected) = cv2.aruco.detectMarkers(image, aruco_dict, parameters=arucoParams)
        image = cv2.aruco.drawDetectedMarkers(image, corners, ids)

        markers_corners.append(corners)
        marker_ids.append(ids)

        debug.set_image(f"Calibrate{i}", image)

    cal = calibrator.Calibration(positions, marker_ids, markers_corners)

    return cal
