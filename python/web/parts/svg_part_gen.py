

import cairo
import math
import json

IC_GRAY = 50/256
IC_MARK = 127/256
PIN_GRAY = 229/256

dat = {}

def make_soic(filename, pins):
    make_ic(filename, pins, pitch=1.27, height=6.2, pack_height=4.0, pin_width=0.51, nominal_package_width=5.0, nominal_package_pins=4)

def make_sopic(filename, pins):
    make_ic(filename, pins, pitch=1.27, height=10.3, pack_height=7.5, pin_width=0.51, nominal_package_width=5.0, nominal_package_pins=4)

def make_ssopic(filename, pins):
    make_ic(filename, pins, pitch=1.27/2, height=6.4, pack_height=4.4, pin_width=0.22, nominal_package_width=3.0, nominal_package_pins=4)

def make_ic(filename, pins, pitch, height, pack_height, pin_width, nominal_package_width, nominal_package_pins):
    pinpitch_offset = nominal_package_width - (pitch * nominal_package_pins)
    width = (pins//2)*pitch+pinpitch_offset
    with cairo.SVGSurface(filename, width, height) as surface:
        surface.set_document_unit(cairo.SVG_UNIT_MM)
        ctx = cairo.Context(surface)
        #ctx.set_source_rgb(100, 0, 255)
        ctx.set_line_width(0)
        ctx.set_source_rgb(PIN_GRAY, PIN_GRAY, PIN_GRAY)
        for i in range(pins//2):
            ctx.rectangle(pitch/2+pinpitch_offset/2-pin_width/2+i*pitch, 0, pin_width, height)
            ctx.fill()

        ctx.set_source_rgb(IC_GRAY, IC_GRAY, IC_GRAY)
        ctx.rectangle(0, (height-pack_height)/2, pins/2*pitch+pinpitch_offset, pack_height)
        ctx.fill()

        ctx.set_source_rgb(IC_MARK, IC_MARK, IC_MARK)
        ctx.arc(0.7, height-1.8, .35, 0, math.pi*2)
        ctx.fill()
    dat[filename.replace("_img.svg", "")] = {
        "img": filename,
        "sym": "U_sym.svg",
        "x": width,
        "y": height
    }
        

def make_lqfp_ic(filename, pins):
    make_quad_ic(filename, pins, pitch=0.5, pin_width=0.2, nominal_package_width=9.0, nominal_package_inner=7.0, nominal_package_pins=48)

def make_tqfp_ic(filename, pins):
    make_quad_ic(filename, pins, pitch=0.8, pin_width=0.3, nominal_package_width=9.0, nominal_package_inner=7.0, nominal_package_pins=32)

def make_qfn_ic(filename, pins):
    make_quad_ic(filename, pins, pitch=0.5, pin_width=0.25, nominal_package_width=6.4, nominal_package_inner=6.0, nominal_package_pins=36, dot_offset=0.8)

def make_quad_ic(filename, pins, pitch, pin_width, nominal_package_width, nominal_package_inner, nominal_package_pins, dot_offset=2):
    pinpitch_offset = nominal_package_width - (pitch * nominal_package_pins/4)
    outer_width = (pins//4)*pitch+pinpitch_offset
    inner_width = outer_width - nominal_package_width + nominal_package_inner
    with cairo.SVGSurface(filename, outer_width, outer_width) as surface:
        surface.set_document_unit(cairo.SVG_UNIT_MM)
        ctx = cairo.Context(surface)
        ctx.set_source_rgb(100, 0, 255)
        ctx.set_line_width(0)

        for angle in range(2):
            ctx.save()
            if angle == 1:
                ctx.translate(outer_width/2, outer_width/2)
                ctx.rotate(math.pi/2)
                ctx.translate(-outer_width/2, -outer_width/2)
            ctx.set_source_rgb(PIN_GRAY, PIN_GRAY, PIN_GRAY)
            for i in range(pins//4):
                ctx.rectangle(pitch/2+pinpitch_offset/2-pin_width/2+i*pitch, 0, pin_width, outer_width)
                ctx.fill()
            ctx.restore()

        ctx.set_source_rgb(IC_GRAY, IC_GRAY, IC_GRAY)
        ctx.rectangle((outer_width - inner_width) / 2, (outer_width - inner_width) / 2, inner_width, inner_width)
        ctx.fill()

        ctx.set_source_rgb(IC_MARK, IC_MARK, IC_MARK)
        ctx.arc(dot_offset, outer_width-dot_offset, .35, 0, math.pi*2)
        ctx.fill()
    dat[filename.replace("_img.svg", "")] = {
        "img": filename,
        "sym": "U_sym.svg",
        "x": outer_width,
        "y": outer_width
    }

print("svg part gen")

for i in range(4,10):
    i *= 2
    make_soic("SOIC%d_img.svg" % i, i)
for i in range(4,20):
    i *= 2
    make_sopic("SOP%d_img.svg" % i, i)
for i in range(4,20):
    i *= 2
    make_ssopic("SSOP%d_img.svg" % i, i)
for i in [24, 32, 44, 48, 52, 60, 64, 100, 128, 144, 160, 176, 208]:
    make_lqfp_ic("LQFP%d_img.svg" % i, i)
for i in [16, 24, 32, 44, 48, 52, 60, 64, 100]:
    make_qfn_ic("QFN%d_img.svg" % i, i)
for i in [24, 32, 44, 48, 52, 60, 64, 100, 128, 144, 160, 176, 208]:
    make_tqfp_ic("TQFP%d_img.svg" % i, i)


print(json.dumps(dat, indent=4, sort_keys=True))