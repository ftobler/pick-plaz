

import pickle
import time

import cv2
import cv2.aruco
import numpy as np

import camera
import save_robot
import calibrator
import fiducial
import bottle_svr

CALIBRATION_POS = (276//2, 314//2)


CALIBRATION_POS = (105,196)

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

    for i, (x,y) in enumerate(positions):
        robot.drive(x, y)
        robot.flush()
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

    x, y = CALIBRATION_POS
    robot.drive(x, y)

    try:

        with camera.CameraThread(0) as c:

            import queue

            image_cache = None
            event_queue = queue.Queue()

            data = {
            }

            CAM_RES = 20

            nav = {
                "camera": {
                    "x": float(x),
                    "y": float(y),
                    "width": 35.0,
                    "height": 35.0,
                    "framenr": 1245
                },
                "bed": {
                    "x": -0.0,
                    "y": -0.0,
                    "width": 400,
                    "height": 400
                },
                "pcb": {
                    "transform": [1, 0, 0, -1, 10, -10],
                    "transform_mse" : 0.1,
                    "fiducials": {}
                },
                "detection": {
                    "fiducial": [0, 0],
                },
            }

            b = bottle_svr.BottleServer(lambda: image_cache, lambda x: event_queue.put(x),  lambda: data, lambda: nav)

            robot.flush()

            time.sleep(0.5)

            cal = calibrate(robot, c)
            mp = None # calibrator.ModelPixConverter(cal)
            h = calibrator.Homography(cal, CAM_RES, (CAM_RES*35,CAM_RES*35))
            ip = calibrator.ImageProjector(h, border_value=(31, 23, 21))

            fd = fiducial.FiducialDetector(cal)

            while True:

                cache = c.cache
                cam_image = cv2.cvtColor(cache["image"], cv2.COLOR_GRAY2BGR)

                if mp is not None:
                    cam_image = cv2.putText(cam_image, f"x={x}, y={y}", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 2/2,(255,255,255), int(2), cv2.LINE_AA)
                    xx, yy = mp.model_to_pix(np.array([[CALIBRATION_POS[0]], [CALIBRATION_POS[1]]]), (x, y))[0]
                    cam_image = cv2.putText(cam_image, "L", (int(xx),int(yy)), cv2.FONT_HERSHEY_SIMPLEX, 2/2,(0,0,255), int(2), cv2.LINE_AA)
                    draw_grid(mp, cam_image, (x, y))

                if ip is not None:
                    image = ip.project(cam_image)
                else:
                    image = cam_image

                image_cache = image

                try:
                    event = event_queue.get(block=False)

                    if event["type"] == "setpos":

                        x = event["x"]
                        y = event["y"]

                        nav["camera"]["x"] = float(x)
                        nav["camera"]["y"] = float(y)

                        robot.drive(x,y)

                        time.sleep(1)
                        cache = c.cache
                        cam_image = cv2.cvtColor(cache["image"], cv2.COLOR_GRAY2BGR)
                        nav["detection"]["fiducial"] =  fd(cam_image, (x, y))

                    if event["type"] == "setfiducial":
                        nav["pcb"]["fiducials"][event["id"]] = (event["x"], event["y"])
                        transform, mse = fiducial.get_transform(nav["pcb"]["fiducials"])
                        nav["pcb"]["transform"] = transform
                        nav["pcb"]["transform_mse"] = float(mse)

                except queue.Empty:
                    pass
                except fiducial.NoFiducialFoundException:
                    pass

                time.sleep(0.1)

    except KeyboardInterrupt:
        pass

    print("finished")

    # park robot
    robot.drive(5,5) # drive close to home
    robot.dwell(1000)
    robot.steppers(False)
    robot.light_topdn(False)

if __name__ == "__main__":
    main()
