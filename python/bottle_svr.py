#tornado needs this or it does not run
import asyncio
try:
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
except AttributeError:
    print("Probably running on linux")

from bottle import route, run, response, static_file, request, post
import threading

class BottleServer:

    def __init__(self, get_camera_fcn, event_put_fcn, get_pos_fcn, listen="0.0.0.0", port=8080):

        self.get_camera_fcn = get_camera_fcn
        self.event_put_fcn = event_put_fcn
        self.get_pos_fcn = get_pos_fcn

        self.port = port
        self.listen = listen

        self.thread = threading.Thread(target=self._run,args=())
        self.thread.name = "BottleServerThread"
        self.thread.daemon = True
        self.thread.start()

    def _api(self, name):
        if name == "topdn.jpg":
            import cv2
            img = self.get_camera_fcn()
            status, encoded = cv2.imencode('.jpg', img)
            if status:
                jpg = encoded.tobytes()
                response.set_header('Content-type', 'image/jpeg')
                return jpg
            else:
                return "{}"
        elif name == "nav.json":

            x, y = self.get_pos_fcn()
            print("nav", x, y)
            return {
                "camera": {
                    "x": float(x),
                    "y": float(y),
                    "width": 50.0,
                    "height": 50.0,
                    "framenr": 1245
                },
                "bed": { 
                    "x": -0.0,
                    "y": -0.0,
                    "width": 400,
                    "height": 400
                }
            }
        else:
            return static_file(name, root='web/api')

    def _setpos(self):
        
        r = dict(request.query.decode())
        try:
            self.event_put_fcn({
                "x" : int(r["x"]),
                "y" : int(r["y"]),
            })
            print("setpos", int(r["x"]), int(r["y"]))
        except:
            pass

    def _home(self):
        return static_file("pickplaz.html", root='web')

    def _files(self, name):
        print(name)
        return static_file(name, root='web')


    def _run(self):

        route('/')(self._home)
        route('/api/<name>')(self._api)
        route('/api/setpos')(self._setpos)
        route('/<name:path>')(self._files)

        run(host=self.listen, port=self.port, debug=False, threaded=True, quiet=True)

class BottleServerMock(BottleServer):

    def _api(self, name):
        if name == "topdn.jpg":
            import numpy as np
            import cv2
            img = np.random.uniform(0,255, size=(480,640)).astype(np.uint8)
            status, encoded = cv2.imencode('.jpg', img)
            if status:
                jpg = encoded.tobytes()
                response.set_header('Content-type', 'image/jpeg')
                return jpg
            else:
                return "{}"
        else:
            return static_file(name, root='web/api')


if __name__ == "__main__":
        

    import time

    # Use mock api if argument "mock" is passed
    import sys
    mock_api = sys.argv[1] == "mock" if len(sys.argv) > 1 else False
    if mock_api:

        def dummy_fcn(*args):
            pass

        b = BottleServerMock(dummy_fcn, dummy_fcn)
        while(True):
            time.sleep(1)

    else:

        import camera
        with camera.CameraThread(0) as c:


            def get_camera():
                return c.cache["image"]

            def put_event(x):
                pass

            b = BottleServer(get_camera, put_event)
            while(True):
                time.sleep(1)

