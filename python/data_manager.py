
import json
from importlib import reload
import pnp_bom_parser

class ContextManager:

    part_state = ["skip", "not placed", "placed"]
    feeder_type = ["auto detect zone", "fixed grid", "strip"]
    feeder_attribute = ["x", "y", "width", "height", "pitch"]
    feeder_state = ["disabled", "ready", "empty"]

    def __init__(self):
        with open("web/api/context.json", "r") as f:
            self.context = json.load(f)
            self.context["const"] = {}
            self.context["const"]["part_state"] = self.part_state
            self.context["const"]["feeder_type"] = self.feeder_type
            self.context["const"]["feeder_attribute"] = self.feeder_attribute
            self.context["const"]["feeder_state"] = self.feeder_state

    def file_save(self, filename):
        #TODO use filename
        with open("web/api/context.json", "w") as f:
            json.dump(self.context, f)
        print("data saved")

    def file_list(self):
        #TODO implement
        return {}

    def file_read(self, filename):
        #TODO implement
        pass

    def get(self):
        return self.context


    def replace(self, bom_str, pnp_str):
        reload(pnp_bom_parser)
        self.context["bom"] = pnp_bom_parser.pnp_bom_parse(pnp_str, bom_str)


    def modify_bom_place(self, index, do_place):
        print((index, do_place))
        self._get_bom_by_index(index)["place"] = do_place


    def modify_bom_fiducial(self, index, is_fiducial):
        print((index, is_fiducial))
        self._get_bom_by_index(index)["fiducial"] = is_fiducial


    def modify_bom_foorprint(self, index, footprint):
        self._get_bom_by_index(index)["footprint"] = footprint


    def modify_bom_feeder(self, index, feeder_name):
        self._get_bom_by_index(index)["feeder"] = feeder_name


    def modify_bom_rot(self, index, rotation=None):
        bom = self._get_bom_by_index(index)
        if rotation == None:
            rot = bom["rot"]
            rot = rot - 90 # clockwhise in pcb frame
            if rot < 0:
                rot = rot + 360
            bom["rot"] = rot
        else:
            bom["rot"] = rotation


    def modify_part_state(self, part_id, state=None):
        part = self._get_part_by_id(part_id)
        if state == None:
            if not "state" in part:
                part["state"] = 0
            part["state"] = (part["state"] + 1) % len(self.part_state)
        else:
            part["state"] = state


    def modify_feeder_name(self, feeder_id, new_id):
        feeder = self._get_feeder_by_id(feeder_id)
        del self.context["feeder"][feeder_id]
        self.context["feeder"][new_id] = feeder


    def modify_feeder_type(self, feeder_id, type=None):
        feeder = self._get_feeder_by_id(feeder_id)
        if type == None:
            if not "type" in feeder:
                feeder["type"] = 0
            feeder["type"] = (feeder["type"] + 1) % len(self.feeder_type)
        else:
            feeder["type"] = type


    def modify_feeder_rot(self, feeder_id, rotation=None):
        feeder = self._get_feeder_by_id(feeder_id)
        if rotation == None:
            rot = feeder["rot"]
            rot = rot + 90 #clockwhise in pick-platz frame
            if rot >= 360:
                rot = rot - 360
            feeder["rot"] = rot
        else:
            feeder["rot"] = rotation


    def modify_feeder_state(self, feeder_id, state=None):
        feeder = self._get_feeder_by_id(feeder_id)
        if state == None:
            if not "state" in feeder:
                feeder["state"] = 0
            feeder["state"] = (feeder["state"] + 1) % len(self.feeder_state)
        else:
            feeder["state"] = state


    def modify_feeder_delete(self, feeder_id):
        if feeder_id in self.context["feeder"]:
            del self.context["feeder"][feeder_id]


    def modify_feeder_create(self, feeder_id):
        self.context["feeder"][feeder_id] = {
            "type": 0,
            "x": 100,
            "y": 100,
            "width": 50,
            "height": 50,
            "pitch": None,
            "rot": 0,
            "state": 1
        }


    def modify_feeder_attribute(self, feeder_id, attribute, value):
        if not attribute in self.feeder_attribute:
            raise Exception("setting or modifying feeder attribute %s is not allowed" % attribute)
        feeder = self._get_feeder_by_id(feeder_id)
        feeder[attribute] = value




    def _get_feeder_by_id(self, feeder_id, state=None):
        feeder = self._get_bom_by_index(feeder_id)
        if state == None:
            if not "state" in feeder:
                feeder["state"] = 0
            feeder["state"] = (feeder["state"] + 1) % len(self.feeder_state)
        else:
            feeder["state"] = state


    def _get_bom_by_index(self, index):
        return self.context["bom"][index]

    def _get_bom_by_id(self, designator):
        for part in self.context["bom"]:
            if designator in part["designators"]:
                return part
        raise Exception("id %s not found in BOM" % designator)

    def _get_part_by_id(self, designator):
        for part in self.context["bom"]:
            if designator in part["designators"]:
                return part["designators"][designator]
        raise Exception("id %s not found in parts" % designator)

    def _get_feeder_by_id(self, id):
        try:
            return self.context["feeder"][id]
        except:
            raise Exception("id %s not found in Feeder" % id)

