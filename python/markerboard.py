
import numpy as np

import cv2.aruco
import cairo

def to_svg(filename, markers, positions, markersize):
    """ Save marker board as svg to print on paper or pcb"""

    positions = np.array(positions)

    size = tuple(positions.max(axis=0) + markersize+1)

    aruco_dict = cv2.aruco.Dictionary_get(cv2.aruco.DICT_4X4_100)

    with cairo.SVGSurface(filename, size[0], size[1]) as surface:
        surface.set_document_unit(cairo.SVG_UNIT_MM)
        ctx = cairo.Context(surface)
        ctx.set_source_rgb(0, 0, 0)
        ctx.set_line_width(0)
        for marker_id, (x0, y0) in zip(markers, positions):
            marker_image = cv2.aruco.drawMarker(aruco_dict, marker_id, 6)
            ctx.save()
            ctx.translate(x0, y0)
            ctx.scale(markersize/6, markersize/6)

            for x in range(6):
                for y in range(6):
                    if not marker_image[y, x]:
                        ctx.move_to(x, y)
                        ctx.line_to(x+1, y)
                        ctx.line_to(x+1, y+1)
                        ctx.line_to(x, y+1)
                        ctx.fill()
            ctx.restore()

size_x = 10
size_y = 10
marker_size = 3
stride = 4

x, y = np.meshgrid(np.arange(size_x), np.arange(size_y))
positions = np.stack((x, y), axis=-1).reshape((-1,2)) * stride
ids = np.arange(len(positions))

if __name__ == "__main__":
    to_svg("test.svg", ids, positions, marker_size)
