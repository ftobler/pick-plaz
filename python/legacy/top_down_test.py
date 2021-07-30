
# %% Imports

import glob

import cv2
import numpy as np

import yaml

import matplotlib.pyplot as plt

import cv2.aruco

import homography

from skimage.measure import label, regionprops
import math


# %% Load render image

with open("conf.yml", "r") as f:
    conf = yaml.safe_load(f)

file = glob.glob(conf["top_down_dataset_path"] + "/*")[0]

img = cv2.imread(file)
image = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

plt.imshow(image)
plt.show()

# %% Generate aruco markers

def get_cal(plot=False):

    aruco_dict = cv2.aruco.Dictionary_get(cv2.aruco.DICT_4X4_100)

    for i in range(50):
        aruco = cv2.aruco.drawMarker(aruco_dict, i, 300)
        cv2.imwrite(f"aruco/aruco_{i:03d}.png", aruco)

    # make ground truth img

    gt_canvas = np.ones((1000,1000), dtype=np.uint8)
    gt_canvas *= 255

    gt_factor = 21.5 / 700
    gt_marker_radius = gt_factor * 50 * 1.415

    positions = [
        [0,0],
        [0,700],
        [700,0],
        [700,700]
    ]

    gt_corners = []
    gt_centers = []

    for i, (x, y) in enumerate(positions):
        aruco = cv2.aruco.drawMarker(aruco_dict, i, 100)
        gt_canvas[x:x+100, y:y+100] = aruco

        gt_corners.extend([
            [x, y],
            [x+99, y],
            [x+99, y+99],
            [x, y+99],
        ])
        gt_centers.append((x+50,y+50))
    gt_corners = np.array(gt_corners) * gt_factor
    gt_centers = np.array(gt_centers) * gt_factor

    if plot:
        plt.imshow(gt_canvas)
        plt.show()

        cv2.imwrite(f"aruco.png", gt_canvas)

    # Calibrate

    class Calibration:
        def __init__(self, intrinsic, dist_coeffs):
            self.intrinsic = intrinsic
            self.dist_coeffs = dist_coeffs

    cal = Calibration( np.eye(3, dtype=np.float64), None)

    return cal, aruco_dict, gt_corners, gt_canvas, gt_factor, gt_marker_radius, gt_centers

cal, aruco_dict, gt_corners, gt_canvas, gt_factor, gt_marker_radius, gt_centers = get_cal(plot=True)

# %% Calibrate

def calibrate(image, cal, aruco_dict, gt_corners, gt_canvas, gt_factor, plot=False):

    # Find aruco markers

    arucoParams = cv2.aruco.DetectorParameters_create()
    (corners, ids, rejected) = cv2.aruco.detectMarkers(image, aruco_dict,
        parameters=arucoParams)

    if plot:
        outputImage = np.copy(image)
        cv2.aruco.drawDetectedMarkers(outputImage, corners, ids)
        plt.imshow(outputImage)
        plt.show()

    indices = np.argsort(ids[:,0])
    corners = np.array(corners)
    # corners = corners[indices, 0]
    corners = np.reshape(corners, (-1, 2))

    gt_corners = gt_corners.reshape((-1,4,2))[ids[:,0]].reshape((-1,2))

    # %% Get extrinsic

    object_points = np.concatenate((gt_corners, np.zeros_like(gt_corners[:,:1])), axis=-1).astype(np.float32)
    image_points = np.expand_dims(corners ,1)

    retval, rvec, tvec = cv2.solvePnP(object_points, image_points, cal.intrinsic, cal.dist_coeffs)
    projectedImagePoints, _ = cv2.projectPoints(object_points, rvec, tvec, cal.intrinsic, cal.dist_coeffs)
    diff = (projectedImagePoints - image_points)[:, 0]
    quality =  np.max(np.linalg.norm(diff, axis=1)) # max deviation in pixels

    print(f"Homograph max error is {quality:.2f} pixels")
    if quality > 10:
        print(f"Warning: maximum error is abnormally high ({quality:.2f} pixels)")

    extrinsic = np.concatenate((cv2.Rodrigues(rvec)[0], tvec), axis=1)

    camera_mat = cal.intrinsic @ extrinsic



    pixel_per_mm = 10
    h = homography.Homography(cal, extrinsic, pixel_per_mm, size=(25,26))
    ip = homography.ImageProjector(h, border_value=0)
    pp = homography.PointProjector(camera_mat)


    if plot:
        # %% Plot marker

        shape = np.max([gt_canvas.shape, image.shape], axis=0)

        img = np.zeros(shape, np.uint8)
        img[:gt_canvas.shape[0], :gt_canvas.shape[1]] = gt_canvas // 2
        img[:image.shape[0], :image.shape[1]] += image // 2

        plt.imshow(img)

        for (x0, y0), (x1, y1, _) in zip(image_points[:,0], object_points/gt_factor):

            plt.plot((x0,x1), (y0, y1))

        plt.axis("equal")
        plt.show()

    return ip, pp

ip, pp = calibrate(image, cal, aruco_dict, gt_corners, gt_canvas, gt_factor, plot=True)

# %% Filter and threshold

def process(image, ip, gt_centers, gt_marker_radius, plot=False):

    pixel_per_mm = ip.homography.pixel_per_mm

    blur = cv2.GaussianBlur(image,(11,11),0)
    threshold, binary = cv2.threshold(blur,0,255,cv2.THRESH_BINARY_INV+cv2.THRESH_OTSU)

    projected = ip.project(binary)


    pos = (projected.shape[1]-1, projected.shape[0]-1)
    cv2.floodFill(projected, None, pos, 128)

    projected = (projected != 128).view(np.uint8)
    projected *= 255

    disk = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    projected = cv2.morphologyEx(projected, cv2.MORPH_OPEN, disk)

    if plot > 1:
        plt.imshow(projected)
        plt.show()

    # %% Find positions/rotations
    image = projected

    if plot > 1:
        fig, ax = plt.subplots()
        ax.imshow(image, cmap=plt.cm.gray)

    image = image.astype(np.float32) / 255

    l = label(image)
    regions = regionprops(l)

    positions = []
    angles = []

    for props in regions:
        y0, x0 = props.centroid

        positions.append((x0, y0))

        orientation = props.orientation
        angle = (orientation*180/math.pi)
        angle = angle % 90
        if angle > 45: angle -= 90
        angles.append(angle)

        x1 = x0 + math.cos(orientation) * 0.5 * props.minor_axis_length
        y1 = y0 - math.sin(orientation) * 0.5 * props.minor_axis_length
        x2 = x0 - math.sin(orientation) * 0.5 * props.major_axis_length
        y2 = y0 - math.cos(orientation) * 0.5 * props.major_axis_length

        if plot > 1:
            ax.plot((x0, x1), (y0, y1), '-r', linewidth=2.5)
            ax.plot((x0, x2), (y0, y2), '-r', linewidth=2.5)
            ax.plot(x0, y0, '.g', markersize=15)

            minr, minc, maxr, maxc = props.bbox
            bx = (minc, maxc, maxc, minc, minc)
            by = (minr, minr, maxr, maxr, minr)
            ax.plot(bx, by, '-b', linewidth=2.5)

    if plot > 1:
        plt.show()

    positions = np.array(positions) / pixel_per_mm
    angles = np.array(angles)

    # Remove objects that are in proximity of markers
    diffs =np.expand_dims(positions, axis=0) - np.expand_dims(gt_centers, axis=1)
    dists = np.linalg.norm(diffs, axis=-1)
    nearest_distance = np.min(dists, axis=0)
    dist_ok = nearest_distance > gt_marker_radius

    positions = positions[dist_ok]
    angles = angles[dist_ok]

    if plot > 0:
        plt.imshow(projected, cmap="gray")
        for (x, y), a in zip(positions * pixel_per_mm, angles):
            plt.plot((x,), (y,), "o")
            plt.text(x, y, f"{x:.0f}\n{y:.0f}\n{a:.1f} deg", color="r")
        plt.axis("equal")
        plt.title(f"positions in 1/{pixel_per_mm} of a mm")
        plt.show()


    return positions, angles

positions, angles = process(image, ip, gt_centers, gt_marker_radius, plot=5)

# %% Run on Dataset

files = glob.glob(conf["top_down_dataset_path"] + "/*")
files = sorted(list(files))

for file in files:
    print(file)

    img = cv2.imread(file)
    image = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    plt.imshow(image, cmap="gray")
    plt.show()

    ip, pp = calibrate(image, cal, aruco_dict, gt_corners, gt_canvas, gt_factor, plot=False)

    positions, angles = process(image, ip, gt_centers, gt_marker_radius, plot=1)

# %%

import camera

bias = []

def bias_cal(x):

    cv2.imshow("test", x)
    cv2.waitKey(10)

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

    image = cv2.cvtColor(x, cv2.COLOR_BGR2GRAY)
    # image -= bias
    # image = 255 - image

    cv2.imshow("test", image)
    cv2.waitKey(10)

    try:
        ip, pp = calibrate(image, cal, aruco_dict, gt_corners, gt_canvas, gt_factor, plot=False)
        positions, angles = process(image, ip, gt_centers, gt_marker_radius, plot=1)
    except:
        pass

camera.cam(live, count=100)

# cv2.destroyWindow("test")
