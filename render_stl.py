# -*- coding: utf-8 -*-
"""render_stl.py — простая изометрия STL в PNG, чтобы глазами проверить форму."""
import math
import os
import struct
import sys

from PIL import Image, ImageDraw


def read_stl(path):
    data = open(path, "rb").read()
    n = struct.unpack("<I", data[80:84])[0]
    tris = []
    for i in range(n):
        off = 84 + i * 50
        v = struct.unpack("<9f", data[off + 12:off + 48])
        tris.append((v[0:3], v[3:6], v[6:9]))
    return tris


def render(path, out, size=700):
    tris = read_stl(path)
    img = Image.new("RGB", (size, size), "white")
    d = ImageDraw.Draw(img)

    ax, ay = math.radians(35), math.radians(25)
    ca, sa = math.cos(ax), math.sin(ax)
    cb, sb = math.cos(ay), math.sin(ay)

    def proj(p):
        x, y, z = p
        x1 = x * ca - y * sa
        y1 = (x * sa + y * ca) * cb - z * sb
        return x1, y1

    pts = [proj(v) for t in tris for v in t]
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    minx, maxx = min(xs), max(xs)
    miny, maxy = min(ys), max(ys)
    scale = (size - 80) / max(maxx - minx, maxy - miny, 1e-6)
    cx = size / 2 - (minx + maxx) / 2 * scale
    cy = size / 2 - (miny + maxy) / 2 * scale

    order = []
    for t in tris:
        depth = sum(v[0] * 0.5 + v[1] * 0.7 + v[2] * 0.3 for v in t)
        order.append((depth, t))
    order.sort(key=lambda p: p[0])

    lx, ly, lz = 0.4, 0.5, 0.75
    for _depth, t in order:
        a, b, c = t
        ux = [b[i] - a[i] for i in range(3)]
        vx = [c[i] - a[i] for i in range(3)]
        nx = ux[1] * vx[2] - ux[2] * vx[1]
        ny = ux[2] * vx[0] - ux[0] * vx[2]
        nz = ux[0] * vx[1] - ux[1] * vx[0]
        ln = math.sqrt(nx * nx + ny * ny + nz * nz) or 1.0
        shade = abs((nx * lx + ny * ly + nz * lz) / ln)
        col = int(120 + 120 * shade)
        p = [proj(v) for v in t]
        poly = [(p[0][0] * scale + cx, p[0][1] * scale + cy),
                (p[1][0] * scale + cx, p[1][1] * scale + cy),
                (p[2][0] * scale + cx, p[2][1] * scale + cy)]
        d.polygon(poly, fill=(col, col, col))
    img.save(out)
    print("картинка:", out)


if __name__ == "__main__":
    t = os.path.join(os.environ["TEMP"], "body_30.stl")
    o = os.path.join(os.environ["TEMP"], "body_30.png")
    render(t, o)
