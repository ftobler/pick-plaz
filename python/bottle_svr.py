#tornado needs this or it does not run
import asyncio
try:
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
except AttributeError:
    print("Probably running on linux")

from bottle import route, run, response, static_file, request, post
import threading

import json

class BottleServer:

    def __init__(self, get_camera_fcn, event_put_fcn, data_fcn, nav_fcn, listen="0.0.0.0", port=8080):

        self.get_camera_fcn = get_camera_fcn
        self.event_put_fcn = event_put_fcn
        self.data_fcn = data_fcn
        self.nav_fcn = nav_fcn

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
            return self.nav_fcn()

        elif name == "data.json":
            with open("web/api/data.json", "r") as f:
                data = json.load(f)
            data.update(self.data_fcn())
            return data
        else:
            return static_file(name, root='web/api')

    def _setpos(self):
        r = dict(request.query.decode())
        try:
            self.event_put_fcn({
                "type" : "setpos",
                "x" : float(r["x"]),
                "y" : float(r["y"]),
                "system" : r.get("system", "cam")
            })
        except:
            pass

    def _setfiducial(self):
        r = dict(request.query.decode())
        try:
            self.event_put_fcn({
                "type" : "setfiducial",
                "x" : float(r["x"]),
                "y" : float(r["y"]),
                "id" : r["id"],
            })
        except:
            pass

    def _sequencecontrol(self):
        r = dict(request.query.decode())
        try:
            self.event_put_fcn({
                "type" : "sequence",
                "method" : r["method"]
            })
        except:
            pass

    def _home(self):
        return static_file("pickplaz.html", root='web')

    def _files(self, name):
        return static_file(name, root='web')

    def _run(self):

        route('/')(self._home)
        route('/api/<name>')(self._api)
        route('/api/setpos')(self._setpos)
        route('/api/setfiducal')(self._setfiducial)
        route('/api/sequencecontrol')(self._sequencecontrol)
        route('/<name:path>')(self._files)

        print(f"Starting server at {self.listen}:{self.port}")
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


def mock():
    import time

    def dummy_fcn(*args):
        pass

    b = BottleServerMock(dummy_fcn, dummy_fcn, dummy_fcn, dummy_fcn)
    while(True):
        time.sleep(1)

if __name__ == "__main__":
    mock()
