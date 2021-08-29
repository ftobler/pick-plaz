#tornado needs this or it does not run
import asyncio
try:
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
except AttributeError:
    print("Probably running on linux")

from bottle import route, run, response, static_file, request, post
import threading

import json

import debug




class BottleServer:

    def __init__(self, get_camera_fcn, event_put_fcn, data, nav_fcn, listen="0.0.0.0", port=8080):

        self.get_camera_fcn = get_camera_fcn
        self.event_put_fcn = event_put_fcn
        self.data = data
        self.nav_fcn = nav_fcn

        self.port = port
        self.listen = listen

        self.thread = threading.Thread(target=self._run,args=())
        self.thread.name = "BottleServerThread"
        self.thread.daemon = True
        self.thread.start()

    def _api(self, name):
        return static_file(name, root='web/api')

    def _camera_topdn(self):
        import cv2
        img = self.get_camera_fcn()
        status, encoded = cv2.imencode('.jpg', img)
        if status:
            jpg = encoded.tobytes()
            response.set_header('Content-type', 'image/jpeg')
            return jpg
        else:
            return "{}"

    def _nav(self):
        return self.nav_fcn()

    def _data(self):
        return self.data.get()

    def _debug(self):
        return debug.data

    def _setpos(self):
        r = dict(request.query.decode())
        try:
            self.event_put_fcn({
                "type" : "setpos",
                "x" : _float(r["x"]),
                "y" : _float(r["y"]),
                "system" : _str(r.get("system", "cam"))
            })
        except Exception as e:
            raise e

    def _setfiducial(self):
        r = dict(request.query.decode())
        try:
            self.event_put_fcn({
                "type" : "setfiducial",
                "x" : _float(r["x"]),
                "y" : _float(r["y"]),
                "id" : _str(r["id"]),
            })
        except:
            pass

    def _sequencecontrol(self):
        r = dict(request.query.decode())
        try:
            self.event_put_fcn({
                "type" : "sequence",
                "method" : _str(r["method"])
            })
        except:
            pass

    def _alertquit(self):
        r = dict(request.query.decode())
        try:
            self.event_put_fcn( {
                "type" : "alertquit",
                "id": _int(r["id"]),
                "answer": _str(r["answer"])
            })
        except:
            pass

    def _upload(self):
        bom = request.files.get('bom_upload')
        pnp = request.files.get('pnp_upload')
        #print(bom.filename)
        error = None
        if bom != None and pnp != None:
            try:
                bom_lines = [b.decode("utf-8") for b in bom.file.read().splitlines()]
                pnp_lines = [b.decode("utf-8") for b in pnp.file.read().splitlines()]
                self.data.replace(bom_lines, pnp_lines)
            except Exception as e:
                error = "Parsing of BOM or PNP failed. Exception: '" + str(e) + "'"
        else:
            error = "Need a BOM and a PNP file"
        return {'error': error}

    def _feeder_action(self):
        r = dict(request.query.decode())
        print("_feeder_action: feeder='%s' action='%s' (['goto', 'test'])" % (_str(r["feeder"]), _str(r["action"])))
        raise Exception("TODO: @Nic implement dis")

    def _file_context(self):
        r = dict(request.query.decode())
        try:
            method = _str(r["method"])
            if method == "list":
                return self.data.file_list()
            elif method == "save":
                return self.data.file_save(_str(r["filename"]))
            elif method == "read":
                return self.data.file_read(_str(r["filename"]))
        except:
            pass

    def _bom_modify(self):
        r = dict(request.query.decode())
        try:
            method = _str(r["method"])
            index = _int(r["index"])
            if method == "place":
                self.data.modify_bom_place(index, _bool(r["data"]))
            elif method == "fiducial":
                self.data.modify_bom_fiducial(index, _bool(r["data"]))
            elif method == "footprint":
                self.data.modify_bom_foorprint(index, _str(r["data"]))
            elif method == "feeder":
                self.data.modify_bom_feeder(index, _str(r["data"]))
            elif method == "rotation":
                self.data.modify_bom_rot(index, _int_none(r["data"]))
        except:
            pass

    def _part_modify(self):
        r = dict(request.query.decode())
        try:
            method = _str(r["method"])
            id = _str(r["id"])
            if method == "state":
                self.data.modify_part_state(id, _int_none(r["data"]))
        except:
            pass

    def _feeder_modify(self):
        r = dict(request.query.decode())
        try:
            method = _str(r["method"])
            feeder = _str(r["feeder"])
            if method == "rename":
                self.data.modify_feeder_name(feeder, _str(r["data"]))
            elif method == "type":
                self.data.modify_feeder_type(feeder, _int_none(r["data"]))
            elif method == "rotation":
                self.data.modify_feeder_rot(feeder, _int_none(r["data"]))
            elif method == "state":
                self.data.modify_feeder_state(feeder, _int_none(r["data"]))
            elif method in self.data.feeder_attribute:
                self.data.modify_feeder_attribute(feeder, method, _int(r["data"]))
        except:
            pass

    def _home(self):
        return static_file("pickplaz.html", root='web')

    def _files(self, name):
        return static_file(name, root='web')

    def _run(self):

        route('/')(self._home)
        #route('/api/<name>')(self._api)
        route('/api/topdn.jpg', method='GET')(self._camera_topdn)
        route('/api/nav.json', method='POST')(self._nav)
        route('/api/data.json', method='POST')(self._data)
        route('/api/setpos', method='POST')(self._setpos)
        route('/api/setfiducal', method='POST')(self._setfiducial)
        route('/api/sequencecontrol', method='POST')(self._sequencecontrol)
        route('/api/alertquit', method='POST')(self._alertquit)
        route('/api/upload', method='POST')(self._upload)
        route('/api/debug', method='POST')(self._debug)
        route('/api/feeder_action', method='POST')(self._feeder_action)
        route('/api/file_context', method='POST')(self._file_context)
        route('/api/bom_modify', method='POST')(self._bom_modify)
        route('/api/part_modify', method='POST')(self._part_modify)
        route('/api/feeder_modify', method='POST')(self._feeder_modify)
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

    import data_manager
    d = data_manager.DataManager()

    b = BottleServer(dummy_fcn, dummy_fcn, d, dummy_fcn)
    while(True):
        time.sleep(1)

if __name__ == "__main__":
    mock()







def _int(string):
    return int(string)

def _int_none(string):
    if string == None:
        return None
    if string == "null" or string == "":
        return None
    return int(string)

def _float(string):
    return float(string)

def _str(string):
    if string == None:
        raise Exception("None is not a string.")
    if string == "":
        raise Exception("String is empty.")
    return string

def _bool(string):
    if string == None:
        raise Exception("None is not a bool.")
    if string == "true":
        return True
    if string == "false":
        return False
    raise Exception("'%s' is not a bool." % string)