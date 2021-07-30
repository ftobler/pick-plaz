import time

import cv2
import numpy as np

def make_orthogonal_basis_transform(xyz_0, xyz_x_max, xyz_y_max):
    """ Creates a 4x4 orthogonal basis transformation matrix """

    t_vec = np.array(xyz_0)
    x_vec = np.array(xyz_x_max) - t_vec
    y_vec = np.array(xyz_y_max) - t_vec

    x_size = np.linalg.norm(x_vec)
    y_size = np.linalg.norm(y_vec)
    size = (x_size, y_size)

    x_vec = x_vec / x_size
    y_vec = y_vec / y_size
    z_vec = np.cross(x_vec, y_vec)

    basis = np.eye(4)
    basis[:3, 0] = x_vec
    basis[:3, 1] = y_vec
    basis[:3, 2] = z_vec
    basis[:3, 3] = t_vec

    return basis, size

class UnderstandablePointProjector():

    def __init__(self, camera_mat):

        self.camera_mat = camera_mat
        self.camera_mat_inverse = np.linalg.inv(self.camera_mat[:, :3])
        self.offset = self.camera_mat[:, 3:]
        self.b = self.camera_mat_inverse[2] @ self.offset

    def pix2obj(self, xy, Z=0):
        ones = np.expand_dims(np.ones_like(xy[0]), axis=0)
        uv1 = np.concatenate((xy, ones), axis=0)
        a = self.camera_mat_inverse[2] @ uv1
        s = (Z+self.b)/a
        XYZ = self.camera_mat_inverse@(s*uv1 - self.offset)
        return XYZ

    def obj2pix(self, XYZ):
        pix_xys = self.camera_mat[:, :3] @ XYZ + self.offset
        pix_xy = pix_xys[:2] / pix_xys[2:]
        return pix_xy

    @staticmethod
    def test():
        cam_mat = np.array([ # This is a real camera matrix
            [ 1.20030032e+03,  2.47982911e+02,  5.83920422e+02, 8.07622521e+04],
            [-2.30030880e+01, -8.32897510e+02,  1.20491774e+03, 4.11438112e+05],
            [-4.08406072e-02,  3.76333679e-01,  9.25583603e-01, 3.31611357e+02]
        ], dtype=np.float32)
        pp = UnderstandablePointProjector(cam_mat)
        obj = np.random.uniform(0, 100, (3, 1000)).astype(np.float32)
        t = time.time()
        for _ in range(1000):
            pix = pp.obj2pix(obj)
            obj2 = pp.pix2obj(pix, obj[2:3])
        print("untis time: {}".format(time.time() - t))

        assert np.isclose(obj, obj2, rtol=1e-3, atol=1e-5).all(), "test failed"

        print("nics mse", np.square(np.subtract(obj, obj2)).mean())
        print("nics max", np.max(np.abs(np.subtract(obj, obj2))))

class PointProjector(object):

    def __init__(self, camera_mat):

        self.camera_mat = camera_mat
        self.camera_mat_inverse = self.calc_corr2obj_transform(self.camera_mat)

    def update(self, camera_mat):
        """ fast function that uses cache if possible
        """
        if np.array_equal(self.camera_mat, camera_mat):
            return
        else:
            self.__init__(camera_mat)

    def calc_corr2obj_transform(self, forward_transform):
        """
        Algebraicly reforms the equation

        |x|     |                   | |X|
        |y| = s | forward_transform | |Y|
        |1|     |                   | |Z|
                                      |1|
        to
                                       | x |
        |X|     |                    | | y |
        |Y| = s | transform_corr2obj | |x*Z|
        |1|     |                    | |y*Z| ,
                                       | Z |
                                       | 1 |

        where X,Y,Z are object coordinates, x, y are pixel coordinates
        (source : wolfram alpha)
        """
        a, b, c, d = forward_transform[0]
        e, f, g, h = forward_transform[1]
        i, j, k, l = forward_transform[2]

        transform_corr2obj = np.array([
            [h*j - f*l, b*l - d*j, g*j - f*k, b*k - c*j, c*f - b*g, d*f - b*h],
            [e*l - h*i, d*i - a*l, e*k - g*i, c*i - a*k, a*g - c*e, a*h - d*e],
            [f*i - e*j, a*j - b*i, 0        , 0        , 0        , b*e - a*f]
        ])
        return transform_corr2obj

    def pix2obj(self, xy, Z=0):
        ones = np.expand_dims(np.ones_like(xy[0]), axis=0)
        inp = np.concatenate((xy, xy*Z, ones*Z, ones), axis=0)
        XYs = self.camera_mat_inverse @ inp
        XYZ = XYs / XYs[2:]
        XYZ[2] = Z
        return XYZ

    def obj2pix(self, XYZ):
        t = self.camera_mat
        pix_xys = t[:, :3] @ XYZ + t[:, 3:]
        pix_xy = pix_xys[:2] / pix_xys[2:]
        return pix_xy

    @staticmethod
    def test():
        cam_mat = np.array([ # This is a real camera matrix
            [ 1.20030032e+03,  2.47982911e+02,  5.83920422e+02, 8.07622521e+04],
            [-2.30030880e+01, -8.32897510e+02,  1.20491774e+03, 4.11438112e+05],
            [-4.08406072e-02,  3.76333679e-01,  9.25583603e-01, 3.31611357e+02]
        ], dtype=np.float32)
        pp = PointProjector(cam_mat)
        obj = np.random.uniform(0, 100, (3, 1000)).astype(np.float32)
        t = time.time()
        for _ in range(1000):
            pix = pp.obj2pix(obj)
            obj2 = pp.pix2obj(pix, obj[2:3])
        print("nics time: {}".format(time.time() - t))

        assert np.isclose(obj, obj2, rtol=1e-3, atol=1e-5).all(), "test failed"

        print("nics mse", np.square(np.subtract(obj, obj2)).mean())
        print("nics max", np.max(np.abs(np.subtract(obj, obj2))))

class Homography(object):

    def __init__(self, calibration, extrinsic, pixel_per_mm, size=None, basis=None, size_padding=None):

        self.calibration = calibration
        self.extrinsic = extrinsic
        self.pixel_per_mm = pixel_per_mm

        self.basis = basis

        if size_padding is None:
            self.size_padding = (0, 0)
        else:
            self.size_padding = size_padding

        self.size = None
        if size is None:
            self.size = calibration.chessboard_pattern.size
        else:
            self.size = size

        self.update()

    def set_extrinsic(self, extrinsic):
        self.extrinsic = extrinsic
        self.update()

    def update(self):

        # Calculate output size considering margins and resolution
        self.pix_size = (
            int((self.size[0] + self.size_padding[0]) * self.pixel_per_mm),
            int((self.size[1] + self.size_padding[1]) * self.pixel_per_mm)
        )

        #Prevent allocating of HUUUGE arrays
        if np.max(self.pix_size) > 4000:
            raise ValueError("pixel_per_mm of {} result in a output size of {} which is too high".format(self.pixel_per_mm, self.pix_size))

        # Build zoom matrix
        camera_zoom = np.eye(3)
        camera_zoom[0,0] = self.pixel_per_mm
        camera_zoom[1,1] = self.pixel_per_mm
        camera_zoom[:2,2] = np.array(self.size_padding) * self.pixel_per_mm / 2 #translate to middle of output
        self.camera_zoom = camera_zoom

        if self.basis is not None:
            if self.basis.shape != (4, 4):
                raise ValueError("Basis must be a 4x4 matrix")
            self.extrinsic_basis = self.extrinsic @ self.basis
        else:
            self.extrinsic_basis = self.extrinsic

        extrinsic_basis33 = self.extrinsic_basis[:3, [0,1,3]]
        self.intrinsic = self.calibration.intrinsic
        self.dist_coeffs = self.calibration.dist_coeffs

        # calculate transform matrices
        self.transform_obj2pix = self.intrinsic @ self.extrinsic_basis
        self.transform_pix2corr = camera_zoom @ np.linalg.inv(self.intrinsic @ extrinsic_basis33)
        self.transform_corr2obj = self.calc_corr2obj_transform(self.transform_pix2corr @ self.transform_obj2pix)

        # Calculate object coordinate of camera
        extrinsic_basis44 = np.concatenate((self.extrinsic_basis, [[0, 0, 0, 1]]), axis=0)
        a = np.linalg.inv(extrinsic_basis44)
        self.camera_obj = a[:3, 3:]

    def calc_corr2obj_transform(self, forward_transform):
        """
        Algebraicly reforms the equation

        |x|     |                   | |X|
        |y| = s | forward_transform | |Y|
        |1|     |                   | |Z|
                                      |1|
        to
                                       | 1 |
        |X|     |                    | | Z |
        |Y| = s | transform_corr2obj | |y*Z|
        |1|     |                    | | y | ,
                                       |x*Z|
                                       | x |

        where X,Y,Z are object coordinates, x, y are pixel coordinates
        (source : wolfram alpha)
        """
        a, b, c, d = forward_transform[0]
        e, f, g, h = forward_transform[1]
        i, j, k, l = forward_transform[2]

        transform_corr2obj = np.array([
            [d*f - b*h, c*f - b*g, b*k - c*j, b*l - d*j, g*j - f*k, h*j - f*l],
            [a*h - d*e, a*g - c*e, c*i - a*k, d*i - a*l, e*k - g*i, e*l - h*i],
            [b*e - a*f, 0        , 0        , a*j - b*i, 0        , f*i - e*j]
        ])
        return transform_corr2obj

    def pix2obj(self, xy, Z=0):
        p, q = xy
        ones = np.ones_like(p)
        z = Z * ones
        pz = p*z
        qz = q*z

        inp = np.stack((ones, z, qz, q, pz, p), axis=0)

        XYs = self.transform_corr2obj @ inp
        XYZ = XYs / XYs[2:]
        XYZ[2] = Z
        return XYZ

    def obj2pix(self, XYZ):
        t = self.transform_pix2corr @ self.transform_obj2pix
        pix_xys = t[:, :3] @ XYZ + t[:, 3:]
        pix_xy = pix_xys[:2] / pix_xys[2:]
        return pix_xy

    def project_corrected_to_offset(self, pix_uv, to_obj_z, from_obj_z):
        obj_xyz = self.pix2obj(pix_uv, Z=from_obj_z)
        obj_xyz[2] = to_obj_z
        pix_xy = self.obj2pix( obj_xyz)
        return pix_xy

    def project_coordinates_to_pixels(self, obj_xyz,):
        pix_uvs = self.transform_obj2pix[:, :3] @ obj_xyz + self.transform_obj2pix[:, 3:]
        pix_uv = pix_uvs[:2] / pix_uvs[2:]
        return pix_uv

    def project_pixels_to_corrected(self, pix_uv):
        pix_xys = self.transform_pix2corr[:, :2] @ pix_uv + self.transform_pix2corr[:, 2:]
        pix_xy = pix_xys[:2] / pix_xys[2:]
        return pix_xy

class ImageProjector:

    def __init__(self, homography, interp=cv2.INTER_LINEAR, border_value=255):

        self.homography = homography
        self.interp = interp
        self.border_value = border_value

        self.update()

    def update(self): #recalculates maps using given homography

        intrinsic = self.homography.intrinsic
        dist_coeffs = self.homography.dist_coeffs
        camera_zoom = self.homography.camera_zoom
        extrinsic_basis33 = self.homography.extrinsic_basis[:3, [0,1,3]]
        size = self.homography.pix_size

        # Initialize maps
        self.map1, self.map2 = cv2.initUndistortRectifyMap(intrinsic, dist_coeffs, np.eye(3), camera_zoom @ np.linalg.inv(extrinsic_basis33), size, cv2.CV_32FC1 )

    def project(self, image):
        corrected_image = cv2.remap(image, self.map1, self.map2, self.interp, borderMode=cv2.BORDER_CONSTANT, borderValue=self.border_value)
        return corrected_image

def run_tests():
    PointProjector.test()
    UnderstandablePointProjector.test()

if __name__=="__main__":
    run_tests()
