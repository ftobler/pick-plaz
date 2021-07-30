

import pickle
import time

import cv2
import cv2.aruco

import camera
import save_robot

CALIBRATION_POS = (226, 294)

def main():

    aruco_dict = cv2.aruco.Dictionary_get(cv2.aruco.DICT_4X4_100)

    robot = save_robot.SaveRobot("/dev/ttyUSB0")
    robot.home()

    captures = []

    x, y = CALIBRATION_POS
    robot.drive(x, y)

    with camera.CameraThread(0) as c:

        time.sleep(0.5)

        while True:

            time.sleep(0.1)

            cache = c.cache            
            image = cv2.cvtColor(cache["image"], cv2.COLOR_GRAY2BGR)

            arucoParams = cv2.aruco.DetectorParameters_create()
            (corners, ids, rejected) = cv2.aruco.detectMarkers(image, aruco_dict, parameters=arucoParams)
            image = cv2.aruco.drawDetectedMarkers(image, corners, ids)

            image = cv2.putText(image, f"x={x}, y={y}", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 2/2,(255,255,255), int(2), cv2.LINE_AA)

            cv2.imshow("window", image)

            keyCode = cv2.waitKey(100) & 0xFF

            if keyCode == ord("w"):
                x -= 10
            elif keyCode == ord("s"):
                x += 10
            elif keyCode == ord("a"):
                y += 10
            elif keyCode == ord("d"):
                y -= 10
            elif keyCode == ord("c"):
                captures.append({
                    "pos": (x, y),
                    "markers_corners" : corners,
                    "marker_ids" : ids,
                })
            elif keyCode == 27: #escape
                break

            robot.drive(x,y)

    print("finished")

    # drive close to home
    robot.drive(5,5)

    with open("captures.pkl", "wb") as f:
        pickle.dump(captures, f)

if __name__ == "__main__":
    main()