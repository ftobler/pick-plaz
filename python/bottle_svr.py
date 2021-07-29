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
    return static_file(name, root='web/api')
@route('/parts/<name>')
def home(name):
    return static_file(name, root='web/parts')



run(host=listen, port=port, server="tornado")