
import json
from pnp_bom_parser import pnp_bom_parse


class DataManager:

    def __init__(self):
        with open("web/api/data.json", "r") as f:
            self.data = json.load(f)


    def get(self):
        return self.data


    def replace(self, bom_str, pnp_str):
        self.data = pnp_bom_parse(pnp_str, bom_str)


