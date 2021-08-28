
import json
from importlib import reload
import pnp_bom_parser


class DataManager:

    def __init__(self):
        with open("web/api/data.json", "r") as f:
            self.data = json.load(f)


    def get(self):
        return self.data


    def replace(self, bom_str, pnp_str):
        reload(pnp_bom_parser)
        self.data["bom"] = pnp_bom_parser.pnp_bom_parse(pnp_str, bom_str)

