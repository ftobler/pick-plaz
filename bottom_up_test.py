# %% Imports and stuff

import numpy as np
import cv2

import matplotlib.pyplot as plt

import yaml
import glob

with open("conf.yml", "r") as f:
    conf = yaml.safe_load(f)


file = glob.glob(conf["datasetpath"] + "/*")[0]


# %%

def get_crop(file, plot=False):

    img = cv2.imread(file)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # plt.imshow(gray)
    # plt.show()


    img = gray

    cx, cy = np.array(img.shape) // 2

    size = 170

    crop = img[cx-size:cx+size, cy-size:cy+size]

    # Masking circle does not work since opencv has no masked otsu feature :(
    # x, y = np.meshgrid(np.arange(crop.shape[0]), np.arange(crop.shape[1]))
    # x -= size
    # y -= size
    # x *= x
    # y *= y
    # x += y
    # mask = x > (size-30)**2
    # mask = mask.view(np.uint8)
    # mask *= 255
    # crop = np.where(mask, 0, crop)

    img = crop

    blur = cv2.GaussianBlur(img,(5,5),0)
    threshold, binary = cv2.threshold(blur,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)

    if plot:
        plt.imshow(binary)
        plt.show()

        plt.imshow(crop)
        plt.show()


    return crop, binary

crop, binary = get_crop(file, plot=True)

# %% Method 1 regions/pca

from skimage.draw import ellipse
from skimage.measure import label, regionprops, regionprops_table
from skimage.transform import rotate
import math

def method1(binary, plot=False):

    image = binary

    regions = regionprops(image)

    if plot:
        fig, ax = plt.subplots()
        ax.imshow(image, cmap=plt.cm.gray)

    props = regions[0]
    y0, x0 = props.centroid
    orientation = props.orientation

    angle = (orientation*180/math.pi)
    angle = angle % 90
    if angle > 45: angle -= 90

    print(f"correct by {angle:.1f} deg clockwise")


    x1 = x0 + math.cos(orientation) * 0.5 * props.minor_axis_length
    y1 = y0 - math.sin(orientation) * 0.5 * props.minor_axis_length
    x2 = x0 - math.sin(orientation) * 0.5 * props.major_axis_length
    y2 = y0 - math.cos(orientation) * 0.5 * props.major_axis_length

    if plot:
        ax.plot((x0, x1), (y0, y1), '-r', linewidth=2.5)
        ax.plot((x0, x2), (y0, y2), '-r', linewidth=2.5)

        ax.plot(x0, y0, '.g', markersize=15)

        minr, minc, maxr, maxc = props.bbox

        bx = (minc, maxc, maxc, minc, minc)
        by = (minr, minr, maxr, maxr, minr)
        ax.plot(bx, by, '-b', linewidth=2.5)

    if plot:
        plt.show()

    return angle

method1(binary, plot=True)

# %% Method 2: hough lines

def method2(crop, plot=False):

    img = crop

    canny = cv2.Canny(img, 200, 200, None, 3)

    # plt.imshow(canny)
    # plt.show()
        
    # lines = cv2.HoughLines(canny, 1, np.pi / 180, 150, None, 0, 0)

    linesP = cv2.HoughLinesP(canny, 1, np.pi / 180, 50, None, 50, 10)

    angles = []
    cdstP = cv2.cvtColor(canny, cv2.COLOR_GRAY2BGR)
    if linesP is not None:
        for i in range(0, len(linesP)):
            l = linesP[0][0]
            cv2.line(cdstP, (l[0], l[1]), (l[2], l[3]), (255,0,0), 3, cv2.LINE_AA)
        
            dx, dy = l[:2] - l[2:]
            angle = math.atan2(dx,dy) * 180/math.pi
            angle = angle % 90
            if angle > 45: angle -= 90
            angles.append(angle)

    if angles:
        angle = np.median(angles)
        print(f"correct by {angle:.1f} deg clockwise")
    else:
        print(f"Error no angle found")
        angle = 0

    if plot:
        plt.imshow(cdstP)
        plt.show()

    return angle

method2(crop, plot=True)
    

# %% Run on Dataset

files = glob.glob(conf["datasetpath"] + "/*")
files = sorted(list(files))[:5]

for file in files:
    print(file)

    crop, binary = get_crop(file)

    print("Method1: ", end="")
    angle1 = method1(binary)
    print("Method2: ", end="")
    angle2 = method2(crop)
