from sys import argv
import json
import re
from pprint import pprint


def parse_csv(raw):
    data = []
    for line in raw:
        if line == "":
            continue
        if '"' in line:
            data.append(re.split('";"|","|"\t"', line[1:-1]))
        else:
            data.append(re.split(';|,|\t', line))
    #pprint(data)
    return data


def parse_text_formatted_table(raw):
    heads = raw[0].split(" ")
    heads = [x for x in heads if x != ""]
    heads_pos_start = [raw[0].find(x) for x in heads]
    heads_pos_end = heads_pos_start[1::] + [len(raw[0])]
    raw.pop(0)
    data = [heads]
    for line in raw:
        data_line = []
        data.append(data_line)
        for col in range(len(heads)):
            cell = line[heads_pos_start[col]:heads_pos_end[col]].strip()
            data_line.append(cell)
    #pprint(data)
    #print(heads)
    #print(heads_pos_start)
    #print(heads_pos_end)
    return data


def parse_raw_content(raw):
    if raw[0].find(";")!=-1 or raw[0].find(",")!=-1 or raw[0].find("\t")!=-1:
        #its a CSV we can parse
        return parse_csv(raw)
    else:
        #its a space formatted table
        return parse_text_formatted_table(raw)


def find_indexes(data, probable_list, default=None):
    data_lower = [s.lower() for s in data]
    for checkit in probable_list:
        try:
            return data_lower.index(checkit.lower())
        except:
            pass #ignore it and check the next entry
    if default == None:
        raise Exception("index %s not found in %s" % (data, json.dumps(probable_list)))
    else:
        return default

def find_matching_footprint(footprints, footprint):
    try:
        #for speed first check obvious solutions
        if footprint in footprints:
            return footprint
        footprint_reduced = footprint.upper().replace("-", "").replace("_", "")
        if footprint_reduced in footprints:
            return footprint_reduced

        #check if it is matching without special characters
        for footprint_name in footprints.keys():
            footprint_name_reduced = footprint_name.replace("-", "").replace("_", "")
            if footprint_reduced == footprint_name_reduced:
                return footprint_name

        #check if it is matching the alternative list
        for footprint_name, x in footprints.items():
            for footprint_name_alt in x["alt"]:
                if footprint_reduced == footprint_name_alt:
                    return footprint_name
    except Exception as e:
        print(
            type(e).__name__,          # TypeError
            __file__,                  # /tmp/example.py
            e.__traceback__.tb_lineno  # 2
        )
        pass

    return footprint

def pnp_bom_parse_internal(pnp, bom):
    #parse file and get it to a python double array
    pnp_data = parse_raw_content(pnp)
    bom_data = parse_raw_content(bom)
    footprints = {}
    try:
        footprints = json.load(open("web/footprints.json"))
    except:
        pass

    #get the matchig header indexes for the BOM file
    #eagle uses 'parts', jlcpcb uses 'designator', easyeda uses 'designator', altium uses 'designator'
    bom_index_id        = find_indexes(bom_data[0], ["parts", "designator", "id", "ref"])
    #eagle uses 'value', jlcpcb uses 'comment' , easyeda uses 'name', altium uses 'description'
    bom_index_value     = find_indexes(bom_data[0], ["value", "comment", "name", "description"])
    #eagle uses 'package', jlcpcb uses 'footprint', easyeda uses 'footprint', altium uses 'Footprint'
    bom_index_footprint = find_indexes(bom_data[0], ["package", "footprint"])
    #eagle uses 'device', jlcpcb uses 'JLCPCB Part #（optional', easyeda uses 'supplier part', 'Manufacturer part', altium uses 'Manufacturer Part Number'
    bom_index_part      = find_indexes(bom_data[0], ["device", "JLCPCB Part #（optional", "supplier part", "manufacturer part", "part", "partnr", "manufacturer part number", "mpn"])

    #get the matchig header indexes for the PNP file
    #eagle uses 'id', jlcpcb uses 'ref', easyeda uses 'designator', altium uses 'designator'
    pnp_index_id        = find_indexes(pnp_data[0], ["id", "ref", "designator", "part"])
    #eagle uses 'x', jlcpcb uses 'posX', easyeda uses '', altium uses 'Center-X(mm)'
    pnp_index_x         = find_indexes(pnp_data[0], ["x", "posX", "mid x", "Center-X(mm)", "xmid", "midx", "x-mid", "mid-x"])
    #eagle uses 'y', jlcpcb uses 'posY', easyeda uses '', altium uses 'Center-Y(mm)'
    pnp_index_y         = find_indexes(pnp_data[0], ["y", "posY", "mid y", "Center-Y(mm)", "ymid", "midy", "y-mid", "mid-y"])
    #eagle uses 'rot', jlcpcb uses 'rot', easyeda uses '', altium uses 'rotation'
    pnp_index_rot       = find_indexes(pnp_data[0], ["rot", "rotation"])
    #eagle uses '', jlcpcb uses 'side', easyeda uses '', altium uses 'layer'
    pnp_index_layer     = find_indexes(pnp_data[0], ["layer", "side"], default=-1)

    #build the data tree for every BOM entry
    data = []
    for bom in bom_data[1:]:
        #exctact the list of designators from the BOM table
        id_list = [x.strip() for x in bom[bom_index_id].split(",") if x != ""]
        #build the BOM dict
        parts_list = {}
        bom_entry = {
            "place": False,
            "fiducial": "fiducial" in bom[bom_index_footprint].lower(),
            "footprint": find_matching_footprint(footprints, bom[bom_index_footprint]),
            "value": bom[bom_index_value],
            "partnr": bom[bom_index_part],
            "feeder": None,
            "rot": 0,
            "designators": parts_list
        }
        if bom_entry["fiducial"]:
            bom_entry["footprint"] = "fiducial"

        data.append(bom_entry)
        #search the matching PNP table entry for each designator
        for id in id_list:
            parts_data = {
                "state": 0,
            }
            for part in pnp_data[1:]:
                if part[pnp_index_id] == id:
                    #matching PNP line found. Now assign it.
                    parts_data["x"]     = float(part[pnp_index_x].replace("mm", ""))
                    parts_data["y"]     = float(part[pnp_index_y].replace("mm", ""))
                    parts_data["rot"]   = float(part[pnp_index_rot])
                    if pnp_index_layer != -1: #this could be non existing
                        parts_data["layer"] = part[pnp_index_layer]
                    else:
                        parts_data["layer"] = None
                    parts_data["place"] = True
                    bom_entry["place"] = True
                    break
            parts_list[id] = parts_data

    return data

def pnp_bom_parse(pnp, bom):
    try:
        return pnp_bom_parse_internal(pnp, bom)
    except Exception as e:
        #in case it's a Eagle BOM, there is something to adjust and then try again
        bom = bom[1::]
        pnp = ["id	x	y	rot"] + pnp
        return pnp_bom_parse_internal(pnp, bom)


def pnp_bom_parse_generic(pnp, bom):
    """
    The generic bom starts directly with the titles on the first line.

    CSV and space deliminated data is accepted with general header types

    BOM:
    ```
        Qty Value  Device            Package         Parts         Description
        1          C-EU102-054X133   C102-054X133    C3            JST CONNECTOR
        2          CPOL-EUE2-5       E2-5            C1, C2        SMD Capacitor
    ```

    PNP:
    ```
        id	x	y	rot
        C1	-8.50	8.75	180.00	100n	0603_CAP
        C10	14.35	12.20	180.00	100n	0603_CAP
        C11	9.70	12.20	0.00	100n	0603_CAP
    ```


    """
    return pnp_bom_parse_internal(pnp, bom)

def pnp_bom_parse_eagle(pnp, bom):
    """
    A Eagle BOM looks something like this:
    ```
        Stückliste exportiert aus C:/data/git/ev-charger-solar-control/pcb/pcb-putwatt/pcb-putwatt.sch am 04.11.2023 14:04

        Qty Value  Device            Package         Parts         Description
        1          C-EU102-054X133   C102-054X133    C3            JST CONNECTOR
        2          CPOL-EUE2-5       E2-5            C1, C2        SMD Capacitor
    ```
    And the pnp data has no titles
    ```
        C1	-8.50	8.75	180.00	100n	0603_CAP
        C10	14.35	12.20	180.00	100n	0603_CAP
        C11	9.70	12.20	0.00	100n	0603_CAP
    ```
    """
    #in case it's a Eagle BOM, there is something to adjust and then try again
    bom = bom[1::]
    pnp = ["id	x	y	rot"] + pnp
    return pnp_bom_parse_internal(pnp, bom)


if __name__ == "__main__":
    #this is the old test case.
    bom_file = argv[1]
    pnp_file = argv[2]
    pnp_str = ""
    bom_str = ""
    with open(pnp_file, "r") as f:
        pnp_str = f.read().splitlines()
    with open(bom_file, "r") as f:
        bom_str = f.read().splitlines()

    data = pnp_bom_parse(pnp_str, bom_str)

    print(json.dumps(data, indent=4, sort_keys=True))