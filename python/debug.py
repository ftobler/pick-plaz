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

        cv2.imwrite(f"{self.debug_data.file_dir}/{self.name}.jpg", image)

        self.data = {
            "type" : "image",
            "src" : f"{self.debug_data.dir}/{self.name}.jpg",
        }

    def set_text(self, text):
        self.data = {
            "type" : "text",
            "text" : text,
        }


class DebugData:

    def __init__(self):
        self.active = True
        self.dir = "debug"
        self.file_dir = "web/debug"
        if not os.path.exists(self.file_dir):
            os.mkdir(self.file_dir)
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
