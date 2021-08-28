
import json
from importlib import reload
import pnp_bom_parser




class DataManager:

    part_state = ["skip", "not placed", "placed"]
    feeder_type = ["auto detect zone", "fixed grid", "strip"]
    feeder_attribute = ["x", "y", "width", "height", "pitch"]
    feeder_state = ["disabled", "ready", "empty"]

    def __init__(self):
        with open("web/api/data.json", "r") as f:
            self.data = json.load(f)
            self.data["const"] = {}
            self.data["const"]["part_state"] = self.part_state
            self.data["const"]["feeder_type"] = self.feeder_type
            self.data["const"]["feeder_attribute"] = self.feeder_attribute
            self.data["const"]["feeder_state"] = self.feeder_state


    def get(self):
        return self.data


    def replace(self, bom_str, pnp_str):
        reload(pnp_bom_parser)
        self.data["bom"] = pnp_bom_parser.pnp_bom_parse(pnp_str, bom_str)


    def modify_bom_place(self, index, do_place):
        self._get_bom_by_index(index)["place"] = do_place


    def modify_bom_fiducial(self, index, is_fiducial):
        self._get_bom_by_index(index)["fiducial"] = is_fiducial


    def modify_bom_foorprint(self, index, footprint):
        self._get_bom_by_index(index)["footprint"] = footprint


    def modify_bom_rot(self, index, rotation=None):
        bom = self._get_bom_by_index(index)
        if rotation == None:
            rot = bom["rot"]
            rot = rot + 90
            if rot > 360:
                rot = rot - 360
            bom["rot"] = rot
        else:
            bom["rot"] = rotation


    def modify_bom_feeder(self, index, feeder_name):
        self._get_bom_by_index(index)["feeder"] = feeder_name


    def modify_part_status(self, part_id, status=None):
        part = self._get_bom_by_index(part_id)
        if status == None:
            part["status"] = (part["status"] + 1) % len(self.part_state)
        else:
            part["status"] = status


    def modify_feeder_name(self, feeder_id, new_id):
        feeder = self._get_feeder_by_id(feeder_id)
        del self.data["feeder"][feeder_id]
        self.data["feeder"][new_id] = feeder


    def modify_feeder_type(self, feeder_id, type=None):
        feeder = self._get_feeder_by_id(feeder_id)
        if type == None:
            feeder["type"] = (feeder["type"] + 1) % len(self.feeder_type)
        else:
            feeder["type"] = type


    def modify_feeder_attribute(self, feeder_id, attribute, value):
        if not attribute in self.feeder_attribute:
            raise Exception("setting or modifying feeder attribute %s is not allowed" % attribute)
        feeder = self._get_feeder_by_id(feeder_id)
        feeder[attribute] = value


    def modify_feeder_rot(self, feeder_id, rotation=None):
        feeder = self._get_feeder_by_id(feeder_id)
        if rotation == None:
            rot = feeder["rot"]
            rot = rot + 90
            if rot > 360:
                rot = rot - 360
            feeder["rot"] = rot
        else:
            feeder["rot"] = rotation


    def _get_feeder_by_id(self, feeder_id, status=None):
        feeder = self._get_bom_by_index(feeder_id)
        if status == None:
            feeder["status"] = (feeder["status"] + 1) % len(self.feeder_state)
        else:
            feeder["status"] = status


    def _get_bom_by_index(self, index):
        return self.data["bom"][index]

    def _get_bom_by_id(self, id):
        for bom in self.data["bom"]:
            if id in bom["parts"]:
                return bom
        raise Exception("id %s not found in BOM" % id)

    def _get_feeder_by_id(self, id):
        try:
            return self.data["feeder"][id]
        except:
            raise Exception("id %s not found in Feeder" % id)

