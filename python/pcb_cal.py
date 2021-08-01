

import pickle
import time

import cv2
import cv2.aruco
import numpy as np

import camera
import save_robot
import calibrator

CALIBRATION_POS = (276, 314)
aruco_dict = cv2.aruco.Dictionary_get(cv2.aruco.DICT_4X4_100)
arucoParams = cv2.aruco.DetectorParameters_create()

def calibrate(robot, camera):
    """
    Drive to calibration board and calibrate
    
    If calibration is saved, load from pickle instead
    """

    try:
        with open("cal.pkl", "rb") as f:
            cal = pickle.load(f)
        return cal
    except FileNotFoundError:
        pass

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

    for x,y in positions:
        robot.drive(x, y)
        robot.flush()
        time.sleep(0.5)
         
        image = cv2.cvtColor(camera.cache["image"], cv2.COLOR_GRAY2BGR)

        cv2.imshow("window", image)
        cv2.waitKey(100)

        arucoParams = cv2.aruco.DetectorParameters_create()
        (corners, ids, rejected) = cv2.aruco.detectMarkers(image, aruco_dict, parameters=arucoParams)
        image = cv2.aruco.drawDetectedMarkers(image, corners, ids)

        markers_corners.append(corners)
        marker_ids.append(ids)

    cal = calibrator.Calibration(positions, marker_ids, markers_corners)
    mp = calibrator.ModelPixConverter(cal)

    with open("cal.pkl", "wb") as f:
        pickle.dump(cal, f)

    return cal

def draw_grid(mp, image, pos):
    """ Draw 1cm grid on image"""

    x, y = (pos[0]//10*10, pos[1]//10*10)

    ran = 50
    interval = 10

    obj_grid = np.stack(np.meshgrid(np.arange(x-ran, x+ran, interval), np.arange(y-ran, y+ran, interval)), -1)
    obj_grid = obj_grid.reshape((-1,2)).T
    pix_grid = mp.model_to_pix(obj_grid, pos)

    s = int(np.sqrt(pix_grid.shape[0]))
    pix_grid = pix_grid.reshape((s,s,2))
    for grid in [pix_grid, np.transpose(pix_grid, (1,0,2))]:
        for line in grid:
            a = line[0]
            for b in line[1:]:
                cv2.line(image, (int(a[0]), int(a[1])),  (int(b[0]), int(b[1])), (255,0,255), 1)
                a = b

def main():

    robot = save_robot.SaveRobot("/dev/ttyUSB0")
    robot.home()
    robot.light_topdn(True)

    captures = []

    x, y = CALIBRATION_POS
    robot.drive(x, y)

    with camera.CameraThread(0) as c:

        import queue

        image_cache = None
        event_queue = queue.Queue()

        import bottle_svr
        b = bottle_svr.BottleServer(lambda: image_cache, lambda x: event_queue.put(x),  lambda: (x, y))

        robot.flush()

        time.sleep(0.5)

        try:
            cal = calibrate(robot, c)
            mp = None # calibrator.ModelPixConverter(cal)
            h = calibrator.Homography(cal, 5, (5*70,5*70))
            ip = calibrator.ImageProjector(h, border_value=(31, 23, 21))
        except Exception as e:
            print(f"Calibration could not be loaded. Reason: {e}")

        while True:

            cache = c.cache            
            image = cv2.cvtColor(cache["image"], cv2.COLOR_GRAY2BGR)

            if mp is not None:
                image = cv2.putText(image, f"x={x}, y={y}", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 2/2,(255,255,255), int(2), cv2.LINE_AA)
                xx, yy = mp.model_to_pix(np.array([[CALIBRATION_POS[0]], [CALIBRATION_POS[1]]]), (x, y))[0]
                image = cv2.putText(image, "L", (int(xx),int(yy)), cv2.FONT_HERSHEY_SIMPLEX, 2/2,(0,0,255), int(2), cv2.LINE_AA)
                draw_grid(mp, image, (x, y))

            if ip is not None:
                image = ip.project(image)

            image_cache = image

            try:
                event = event_queue.get(block=False)
                x = event["x"]
                y = event["y"]
            except queue.Empty as e:
                pass
            robot.drive(x,y)

            time.sleep(0.1)

    print("finished")

    # park robot
    robot.drive(5,5) # drive close to home
    robot.dwell(100)
    robot.steppers(False)
    robot.light_topdn(False)

    # with open("captures.pkl", "wb") as f:
    #     pickle.dump(captures, f)

if __name__ == "__main__":
    main()
