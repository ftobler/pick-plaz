
import cv2

def cam(func, device=0, count=10):
    """
    use v42l-ctl to change parameters of the camera.
    Usefull commands:
    v4l2-ctl --list-ctrls-menus
    v4l2-ctl -d 0 -c exposure_absolute=500
    v4l2-ctl -d 0 -c gain=0
    """

    cap = cv2.VideoCapture(device, apiPreference=cv2.CAP_V4L2)

    # os.system("v4l2-ctl -d {} -c exposure={}".format(device, exposure))

    try:
        if not cap.isOpened():
            raise IOError("Video Capture could not be opened")
        for _ in range(count):
            ok, frame = cap.read()
            if ok:
                func(frame)
            else:
                print("Not ok")

    finally:
        cap.release()
        print("cap released")


def imshow(frame):
    cv2.imshow("test", frame)
    cv2.waitKey(10)

cam(imshow)
