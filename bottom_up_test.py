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

def load_file(file):
    img = cv2.imread(file)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return gray

img = load_file(file)


def get_crop(gray, plot=False, inv=False):


    # plt.imshow(gray)
    # plt.show()


    img = gray if inv == False else 255 - gray

    cx, cy = np.array(img.shape) // 2

    size = 170

    blur = cv2.GaussianBlur(img,(11,11),0)
    threshold, binary = cv2.threshold(blur,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)

    # threshold, binary = cv2.threshold(blur,150,255,cv2.THRESH_BINARY)


    crop = img[cx-size:cx+size, cy-size:cy+size]
    binary = binary[cx-size:cx+size, cy-size:cy+size]
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

    if plot:
        plt.imshow(binary)
        plt.show()

        plt.imshow(crop)
        plt.show()


    return crop, binary

crop, binary = get_crop(img, plot=True)

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

    if len(regions) > 0:
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

        cdstP = cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR)

        cv2.line(cdstP, (int(x0), int(y0)), (int(x1), int(y1)), (255,0,0), 3, cv2.LINE_AA)
        cv2.line(cdstP, (int(x0), int(y0)), (int(x2), int(y2)), (255,0,0), 3, cv2.LINE_AA)


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
    else:
        print("error")
        angle = 0
        cdstP = cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR)


    return angle, cdstP

_ = method1(binary, plot=True)

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

    return angle, cdstP

_ = method2(crop, plot=True)


# %% Run on Dataset

files = glob.glob(conf["datasetpath"] + "/*")
files = sorted(list(files))[:5]

for file in files:
    print(file)

    img = load_file(file)
    crop, binary = get_crop(img)

    print("Method1: ", end="")
    angle1 = method1(binary)
    print("Method2: ", end="")
    angle2 = method2(crop)


# %% Record bias image

import camera

bias = []

def bias_cal(x):

    gray = cv2.cvtColor(x, cv2.COLOR_BGR2GRAY)
    bias.append(gray)

camera.cam(bias_cal, count=10)

bias = np.median(bias, axis=0)

bias -= np.min(bias)
bias = bias.astype(np.uint8)

plt.imshow(bias)
plt.show()




# %% Live test

# cv2.namedWindow("test")

def live(x):

    gray = cv2.cvtColor(x, cv2.COLOR_BGR2GRAY)
    gray -= bias

    crop, binary = get_crop(gray, inv=True)
    print("Method1: ", end="")
    angle1, res = method1(binary)
    print("Method2: ", end="")
    # angle2, res = method2(crop)

    cv2.imshow("test", res)
    cv2.waitKey(10)


camera.cam(live, count=200)

# cv2.destroyWindow("test")
