
import time
import json

import numpy as np
import cv2

import debug
import config

class NoPartFoundException(Exception):
    pass

class Picker():

    def __init__(self, eye):

        self.min_area_mm2 = 0.75

        self.eye = eye

        try:
            with open("user/picker.json", "r") as f:
                d = json.load(f)
                self.DX = d["DX"]
                self.DY = d["DY"]
                print("read picker calibration")
        except FileNotFoundError:
            with open("template/picker.json", "r") as f:
                d = json.load(f)
                self.DX = d["DX"]
                self.DY = d["DY"]
                print("picker default calibration")

    def _detect_pick_location(self, robot_pos, robot):

        robot.light_topdn(False)
        robot.drive(*robot_pos)
        image = self.eye.get_valid_image()

        p, a, _ = self.find_components(image)
        if len(p):
            pos = np.array(p[0])
            pos = tuple((pos / self.eye.res) - (self.eye.cam_range/2) + robot_pos)
        else:
            raise NoPartFoundException("Could not find part to pick")

        return pos[0], pos[1], a[0]

    def pick(self, robot, x, y, angle):
        robot.vacuum(True)
        robot.valve(False)
        robot.drive(x=x+self.DX, y=y+self.DY, e=angle, f=200, r=10.0)
        robot.drive(e=angle) #finish angle
        robot.drive(z=config.PICK_Z)
        robot.done()
        robot.valve(True)
        robot.drive(z=0)
        # robot.drive(e=0, r=10.0)
        # robot.drive(e=0, f=200, r=0.75)

    def place(self, robot, x, y, angle):
        robot.drive(x=x+self.DX, y=y+self.DY, e=angle, f=200, r=10.0)
        robot.drive(e=angle)
        robot.drive(z=config.PICK_Z)
        robot.done()
        robot.valve(False)
        robot.vacuum(False)
        robot.drive(z=0)

    def calibrate_legacy(self, pos, robot, camera):

        x1, y1, a = self._detect_pick_location(pos, robot)
        self.pick(robot, x1, y1, 0)
        self.place(robot, x1, y1, 180)

        x2, y2, a = self._detect_pick_location((x1, y1), robot)
        self.pick(robot, x1, y1, 0)
        self.place(robot, x1, y1, 180)

        robot.drive(x1, y1)

        correction_x = (x2-x1)/2
        correction_y = (y2-y1)/2
        self.DX -= correction_x
        self.DY -= correction_y

        d = {
            "DX" : self.DX,
            "DY" : self.DY,
        }
        with open("user/picker.json", "w") as f:
            json.dump(d, f)

        print(f"Picker calibration correction : x={correction_x:.3f}, y={correction_y:.3f}")

    def calibrate(self, pos, robot, camera):

        robot.light_topdn(False)
        robot.light_tray(True)

        print("old calibration: %f/%f" % (self.DX, self.DY))

        x, y = pos
        positions = []
        x0, y0, _ = self._detect_pick_location((x, y), robot)
        for _ in range(6):
            self.pick(robot, x0, y0, 0)
            self.place(robot, x0, y0, 360/6)
            x, y, _ = self._detect_pick_location((x, y), robot)
            positions.append((x, y))

        positions = np.asarray(positions)
        a, b, r = taubin(positions)

        distances = np.linalg.norm(positions - [a, b], axis=-1)
        rms_error = np.sqrt(np.mean((distances - r)**2))

        correction_x = a - x0
        correction_y = b - y0
        self.DX -= correction_x
        self.DY -= correction_y


        print("new calibration: %f/%f" % (self.DX, self.DY))
        d = {
            "DX" : self.DX,
            "DY" : self.DY,
        }
        with open("user/picker.json", "w") as f:
            json.dump(d, f)

        robot.light_topdn(False)
        robot.light_tray(False)

        print(f"Picker calibration correction : x={correction_x:.3f}, y={correction_y:.3f}, rms_error={rms_error:.3f}")

    def find_components(self, image, lock_angle="both", plot=False):

        from skimage.measure import label, regionprops
        import math

        blur = cv2.GaussianBlur(image, (11, 11), 0)
        threshold, binary = cv2.threshold(blur,0,255,cv2.THRESH_BINARY_INV+cv2.THRESH_OTSU)

        disk = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, disk)

        # Floodfill filter
        shape = (binary.shape[0] + 2, binary.shape[1] + 2)
        outer = np.ones(shape, dtype=np.uint8)*255
        inner = outer[1:-1, 1:-1]
        inner[:] = binary
        cv2.floodFill(outer, None, (0,0), 0)
        image = inner

        debug.set_image("PickDetection", image)

        # Find positions/rotations
        if plot:
            import matplotlib.pyplot as plt
            _, ax = plt.subplots()
            ax.imshow(image, cmap=plt.cm.gray)

        image = image.astype(np.float32) / 255

        l = label(image)
        regions = regionprops(l)

        positions = []
        angles = []
        areas = []

        for props in regions:

            if props.area < self.min_area_mm2 * (self.eye.res ** 2):
                continue
            areas.append(props.area)

            y0, x0 = props.centroid

            positions.append((x0, y0))

            orientation = props.orientation
            angle = (orientation*180/math.pi)
            if lock_angle == "both":
                # lock angles to next 90 degree step
                angle = angle % 90
                if angle > 45: angle -= 90
            elif lock_angle == "horizontal":
                # lock angles to horizontal axis
                angle = angle % 180
                if angle > 90: angle -= 180
            else:
                raise ValueError("lock_angle not in ['both', 'horizontal']")

            angles.append(angle)

            if plot:
                x1 = x0 + math.cos(orientation) * 0.5 * props.minor_axis_length
                y1 = y0 - math.sin(orientation) * 0.5 * props.minor_axis_length
                x2 = x0 - math.sin(orientation) * 0.5 * props.major_axis_length
                y2 = y0 - math.cos(orientation) * 0.5 * props.major_axis_length

                ax.plot((x0, x1), (y0, y1), '-r', linewidth=2.5)
                ax.plot((x0, x2), (y0, y2), '-r', linewidth=2.5)
                ax.plot(x0, y0, '.g', markersize=15)

                minr, minc, maxr, maxc = props.bbox
                bx = (minc, maxc, maxc, minc, minc)
                by = (minr, minr, maxr, maxr, minr)
                ax.plot(bx, by, '-b', linewidth=2.5)

                plt.text(x0, y0, f"{angle:.1f}")

        if plot:
            plt.show()

        positions = np.array(positions)
        angles = np.array(angles)

        return positions, angles, areas

    def make_collage(self, robot, camera):
        # TODO move this somewhere else

        x0, y0 = 103, 125

        mm_step = self.ip.homography.size_mm[0]
        pix_step = self.ip.homography.size_pix[0]

        s = int(10 * pix_step)

        res = np.empty((s, s), np.uint8)

        for x in range(10):
            r = range(10)

            if x % 2:
                r = reversed(r)

            for y in r:
                robot.drive(x0+x*mm_step, y0+y*mm_step)
                robot.done()
                time.sleep(0.5)

                image = camera.cache["image"]
                image = self.ip.project(image)
                res[y*pix_step:(y+1)*pix_step, x*pix_step:(x+1)*pix_step] = image

        cv2.imwrite(f"collage.jpg", res)

    def _plot_search_positions(self, search_positions, feeder):
        import matplotlib.pyplot as plt

        r = self.eye.cam_range/2
        for x, y in search_positions:
            plt.plot([x-r, x-r, x+r, x+r, x-r],[y-r, y+r, y+r, y-r, y-r], "-")
            plt.plot([x],[y], "o")

        x, y, w, h = feeder["x"], feeder["y"], feeder["width"], feeder["height"]

        plt.plot([x, x, x+w, x+w, x], [y, y+h, y+h, y, y], "o-")
        plt.axis("equal")
        plt.savefig("plot.png")
        plt.close()

def taubin(p):
    """
    Circle fit by Taubin
    p : array[number of samples, 2]

    returns (x, y, r) coordinates and radius
    """
    p = np.asarray(p)
    X = p[:,0] - np.mean(p[:,0])
    Y = p[:,1] - np.mean(p[:,1])

    Z = X * X + Y * Y
    Zmean = np.mean(Z)
    Z0 = (Z - Zmean) / (2 * np.sqrt(Zmean))
    ZXY = np.array([Z0, X, Y]).T
    U, S, V = np.linalg.svd(ZXY, full_matrices=False)
    A0, A1, A2 = V[2]

    A0 /= np.sqrt(Zmean)

    x = -A1 / (2*A0) + np.mean(p[:,0])
    y = -A2 / (2*A0) + np.mean(p[:,1])
    r = np.abs(np.sqrt(A1*A1 + A2*A2 + A0*A0*Zmean) / A0)

    return x, y, r
