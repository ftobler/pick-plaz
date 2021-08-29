import os

import cv2

class DebugItem:

    def __init__(self, debug_data, name):
        self.name = name
        self.debug_data = debug_data
        self.data = {}

    @property
    def active(self):
        return self.debug_data.active

    def set_image(self, image):

        filename = f"{self.debug_data.dir}/{self.name}.jpg"

        cv2.imwrite(filename, image)

        self.data = {
            "type" : "image",
            "src" : filename,
        }

    def set_text(self, text):
        self.data = {
            "type" : "text",
            "text" : text,
        }


class DebugData:

    def __init__(self):
        self.active = True
        self.dir = "web/debug"
        if not os.path.exists(self.dir):
            os.mkdir(self.dir)
        self.data = {}

        i = self.get("test1")
        i.set_text("please püll")

    def get_dict(self):
        return {name : item.data for name, item in self.data.items()}

    def get(self, name):
        item = self.data.get(name)
        if item is None:
            item = DebugItem(self, name)
            self.data[name] = item
        return item
