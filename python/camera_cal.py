import pickle
import time
import numpy as np
import cv2
import calibrator

CALIBRATION_POS = (155.7,124.2)

aruco_dict = cv2.aruco.Dictionary_get(cv2.aruco.DICT_4X4_100)
arucoParams = cv2.aruco.DetectorParameters_create()

def calibrate(robot, camera):
    """
    Drive to calibration board and calibrate
    """

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

    for i, (x,y) in enumerate(positions):
        robot.drive(x, y)
        robot.done()
        time.sleep(0.5)

        image = cv2.cvtColor(camera.cache["image"], cv2.COLOR_GRAY2BGR)

        arucoParams = cv2.aruco.DetectorParameters_create()
        (corners, ids, rejected) = cv2.aruco.detectMarkers(image, aruco_dict, parameters=arucoParams)
        image = cv2.aruco.drawDetectedMarkers(image, corners, ids)

        markers_corners.append(corners)
        marker_ids.append(ids)

        cv2.imwrite(f"{i}.jpg", image)

    cal = calibrator.Calibration(positions, marker_ids, markers_corners)
    mp = calibrator.ModelPixConverter(cal)

    return cal
