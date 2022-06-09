
import json
from importlib import reload
import pnp_bom_parser
import os

FEEDER_STATE_DIABLED = 0
FEEDER_STATE_READY = 1
FEEDER_STATE_EMPTY = 2

PART_STATE_READY = 0
PART_STATE_PLACED = 1
PART_STATE_ERROR = 2
PART_STATE_SKIP = 3

class ContextManager:

    part_state = ["ready", "placed", "error", "skip"]
    feeder_type = ["tray", "strip"]
    feeder_state = ["disabled", "ready", "empty"]
    feeder_attribute = ["pitch", "x_offset", "y_offset"]

    def __init__(self):
        self.file_read()

    def file_save(self, filename="context"):
        filename = filename.lower()
        if not filename.endswith(".json"):
            filename += ".json"
        with open("user/context/%s" % filename, "w") as f:
            json.dump(self.context, f)
        print("context data saved to '%s'" % filename)

    def file_list(self):
        return os.listdir("user/context")

    def file_read(self, filename="context"):
        filename = filename.lower()
        if not filename.endswith(".json"):
            filename += ".json"
        if "\\" in filename or "/" in filename:
            raise Exception("filename '%s' not allowed")
        try:
            with open("user/context/%s" % filename, "r") as f:
                        self.context = json.load(f)
                        self.context["const"] = {}
                        self.context["const"]["part_state"] = self.part_state
                        self.context["const"]["feeder_type"] = self.feeder_type
                        self.context["const"]["feeder_state"] = self.feeder_state
            print("context data restored from '%s'" % filename)
        except:
            with open("template/context.json", "r") as f:
                        self.context = json.load(f)
                        self.context["const"] = {}
                        self.context["const"]["part_state"] = self.part_state
                        self.context["const"]["feeder_type"] = self.feeder_type
                        self.context["const"]["feeder_state"] = self.feeder_state
            print("context template loaded from '%s'" % filename)

    def get(self):
        return self.context


    def replace(self, bom_str, pnp_str):
        reload(pnp_bom_parser)
        self.context["bom"] = pnp_bom_parser.pnp_bom_parse(pnp_str, bom_str)
        self._auto_assign_symbols()


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


    def modify_feeder_attribute(self, feeder_id, attribute, value):
        feeder = self._get_feeder_by_id(feeder_id)
        if attribute == "pitch":
            feeder[attribute] = value
        if attribute == "x_offset":
            feeder["offset"][0] = value
        if attribute == "y_offset":
            feeder["offset"][1] = value
        if attribute == "position":
            feeder[attribute] = int(value)


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

    def _auto_assign_symbols(self):
        for part in self.context["bom"]:
            footprint = part["footprint"].upper()
            size = None
            type = None
            if "01005" in footprint:
                size = "01005"
            if "0201" in footprint:
                size = "0201"
            if "0402" in footprint:
                size = "0402"
            if "0603" in footprint:
                size = "0603"
            if "0805" in footprint:
                size = "0805"
            if "1206" in footprint:
                size = "1206"
            if "1210" in footprint:
                size = "1210"
            if "1812" in footprint:
                size = "1812"
            if "2010" in footprint:
                size = "2010"
            if "2512" in footprint:
                size = "2512"
            if "R" in footprint:
                type = "R"
            if "C" in footprint:
                type = "C"
            if "L" in footprint:
                type = "L"
            if "RES" in footprint:
                type = "R"
            if "CAP" in footprint:
                type = "C"
            if "IND" in footprint:
                type = "L"
            if size != None and type != None:
                part["footprint"] = size + "_" + type

