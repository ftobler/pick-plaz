#tornado needs this or it does not run
import asyncio
try:
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
except AttributeError:
    print("Probably running on linux")

from bottle import route, run, template, request, response, static_file

listen = "0.0.0.0"
port = 8080


#bottle web handler
#serve (static) start page
@route('/')
def home():
    return static_file("pickplaz.html", root='web')

#bottle web handler
#serve a generic (static) file
@route('/<name>')
def home(name):
    return static_file(name, root='web')

# Use mock api if argument "mock" is passed
import sys
mock_api = sys.argv[1] == "mock" if len(sys.argv) > 1 else False
if mock_api:
    @route('/api/<name>')
    def mock_api(name):
        if name == "image.jpg":
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
else:
    @route('/api/<name>')
    def raspberrypi_api(name):
        # for now same as mock api
        if name == "image.jpg":
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
        
@route('/parts/<name>')
def home(name):
    return static_file(name, root='web/parts')



run(host=listen, port=port, server="tornado")