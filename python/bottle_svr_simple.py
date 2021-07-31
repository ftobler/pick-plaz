#tornado needs this or it does not run
import asyncio
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

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

@route('/api/<name>')
def home(name):
    resp = static_file(name, root='web/api')
    resp.headers['Cache-Control'] = 'no-cache'
    return resp
    
@route('/parts/<name>')
def home(name):
    return static_file(name, root='web/parts')

@route('/api/topdn.jpg')
def home():
    import numpy as np
    import cv2
    img = np.random.uniform(0,255, size=(480,640)).astype(np.uint8)
    status, encoded = cv2.imencode('.jpg', img)
    if status:
        jpg = encoded.tobytes()
        response.set_header('Content-type', 'image/jpeg')
        response.headers['Cache-Control'] = 'no-cache'
        return jpg
    else:
        return "{}"



run(host=listen, port=port, server="tornado")

