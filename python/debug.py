import os

import cv2

active = True
dir = "debug"
file_dir = "web/debug"
if not os.path.exists(file_dir):
    os.mkdir(file_dir)
data = {}

def set_image(name, image):
    cv2.imwrite(f"{file_dir}/{name}.jpg", image)
    data[name] = {
        "type" : "image",
        "src" : f"{dir}/{name}.jpg",
    }

def set_text(name, text):
    data[name] = {
        "type" : "text",
        "text" : text,
    }

#set_text("test1", "please püll")
