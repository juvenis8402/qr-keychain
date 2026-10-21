# -*- coding: utf-8 -*-
"""render_top.py — вид сверху на STL (по умолчанию body_30.stl, можно указать путь)."""
import os
import struct
import sys

from PIL import Image, ImageDraw


def read_stl(path):
    data = open(path, "rb").read()
    n = struct.unpack("<I", data[80:84])[0]
    out = []
    for i in range(n):
        off = 84 + i * 50
        v = struct.unpack("<9f", data[off + 12:off + 48])
        out.append((v[0:3], v[3:6], v[6:9]))
    return out


path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.environ["TEMP"], "body_30.stl")
tris = read_stl(path)
zmax = max(v[2] for t in tris for v in t)
top = [t for t in tris if min(v[2] for v in t) > zmax - 0.01]
print("треугольников:", len(top), "z:", zmax)

size = 700
img = Image.new("RGB", (size, size), "white")
d = ImageDraw.Draw(img)
pts = [(v[0], -v[1]) for t in top for v in t]
xs = [p[0] for p in pts]
ys = [p[1] for p in pts]
s = (size - 60) / max(max(xs) - min(xs), max(ys) - min(ys))
cx = size / 2 - (min(xs) + max(xs)) / 2 * s
cy = size / 2 - (min(ys) + max(ys)) / 2 * s

for t in top:
    poly = [(v[0] * s + cx, -v[1] * s + cy) for v in t]
    d.polygon(poly, fill=(200, 60, 20))

out = os.path.join(os.environ["TEMP"], "top_view.png")
img.save(out)
print("картинка:", out)
