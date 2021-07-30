
import threading

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

class CameraThread:
    """Reads frames from a v4l2 camera in a new thread.
    Use the `with` statement to ensure proper closing of the camera
    Result is appended as a dict {
        "image", : frame
        "timestamp" : milliseconds since cam start
    } to queue.
    """

    def __init__(self, device_number):
        """
        device_number : integer of /dev/video?
        """
        self.device = device_number


        self.cap = cv2.VideoCapture(self.device, apiPreference=cv2.CAP_V4L2)

        # os.system("v4l2-ctl -d {} -c exposure={}".format(self.device, exposure * 100))
        # os.system("v4l2-ctl -d {} -c gain={}".format(self.device, gain))
        # os.system("v4l2-ctl -d {} -c trigger_mode={}".format(self.device, trigger_mode)) # 0=internal, 1=external

        if not self.cap.isOpened():
            raise IOError("Video Capture could not be opened")

        self.thread = threading.Thread(target=self._update, args=())
        self.thread.name = "CameraThread"
        self.thread.daemon = False

        self.thread_exit_request = False
        self.cache = {}

        self.on_terminate_callback = lambda: None #dummy function

    def _update(self):
        try:
            while not self.thread_exit_request:
                ok, frame = self.cap.read()
                if ok:
                    timestamp = time.time()
                    self.cache = {
                        "image" : frame[:,:,0],
                        "timestamp": timestamp
                    }
        finally:
            self.cap.release()
            print("cap released")

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, type, value, tb):
        self.thread_exit_request = True

import time
t0 = time.monotonic()

def imshow(frame):
    cv2.putText(frame, f"{time.monotonic()-t0:.3f}", (50,50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2, cv2.LINE_AA)
    cv2.imshow("test", frame)
    cv2.waitKey(10)

if __name__ == "__main__":
    cam(imshow, device=0, count=1000)
