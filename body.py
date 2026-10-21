# -*- coding: utf-8 -*-
"""
body.py — параметрическое тело брелока со скруглениями, без Fusion.

Ключевая идея: контур скругления строится АНАЛИТИЧЕСКИ — со сдвинутыми
радиусами (круг R-r, стенки x=±(w2-r), верх ear-r, углы e-r), а не числовым
offset по нормалям. Поэтому на стыке ушка и круга нет ни залома, ни щели,
и у всех колец одинаковое число точек.

Триангуляция «полигон с дыркой» — mapbox_earcut (lib/).
"""
import math
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_LIB = os.path.join(_HERE, "lib")
if _LIB not in sys.path:
    sys.path.insert(0, _LIB)

import numpy as np
import mapbox_earcut as earcut

HOLE_D = 4.5
SINK = 2.0
WALL = 2.5
THICK = 3.0
ARC_STEPS = 96
HOLE_STEPS = 48
EAR_R = 3.0
TOP_R = 1.5
BOT_R = 1.0
FILLET_STEPS = 4


def _arc(cx, cy, r, a0, a1, steps):
    return [(cx + r * math.cos(a0 + (a1 - a0) * i / steps),
             cy + r * math.sin(a0 + (a1 - a0) * i / steps))
            for i in range(steps + 1)]


def geometry(diameter):
    """Базовые размеры профиля без сдвига."""
    R = diameter / 2.0
    W = max(10.0, 0.40 * diameter)
    w2 = W / 2.0
    hole_r = HOLE_D / 2.0
    hole_cy = (R - SINK) + hole_r
    ear_top = hole_cy + hole_r + WALL
    e = min(EAR_R, w2 - 0.5, (ear_top - math.sqrt(max(R * R - w2 * w2, 0.0))) / 2.0)
    e = max(e, 0.5)
    return {"R": R, "w2": w2, "hole_r": hole_r,
            "hole_cy": hole_cy, "ear_top": ear_top, "ear_r": e}


def contour(diameter, shrink=0.0):
    """Внешний контур (CCW) со сдвигом внутрь на shrink, мм."""
    g = geometry(diameter)
    R = g["R"] - shrink
    w2 = g["w2"] - shrink
    ear_top = g["ear_top"] - shrink
    e = max(g["ear_r"] - shrink, 0.01)

    y0 = math.sqrt(max(R * R - w2 * w2, 0.0))
    th1 = math.atan2(y0, -w2)
    th2 = math.atan2(y0, w2) + 2.0 * math.pi
    pts = _arc(0, 0, R, th1, th2, ARC_STEPS)

    pts.append((w2, ear_top - e))
    pts += _arc(w2 - e, ear_top - e, e, 0.0, math.pi / 2.0, 8)[1:]
    pts.append((-w2 + e, ear_top))
    pts += _arc(-w2 + e, ear_top - e, e, math.pi / 2.0, math.pi, 8)[1:]
    pts.append((-w2, y0))
    return pts


def hole_contour(diameter):
    g = geometry(diameter)
    return _arc(0, g["hole_cy"], g["hole_r"], 0.0, -2.0 * math.pi, HOLE_STEPS)[:-1]


def _ring(inner, outer, z_inner, z_outer):
    n = len(inner)
    tris = []
    for i in range(n):
        j = (i + 1) % n
        a = (inner[i][0], inner[i][1], z_inner)
        b = (inner[j][0], inner[j][1], z_inner)
        c = (outer[j][0], outer[j][1], z_outer)
        dd = (outer[i][0], outer[i][1], z_outer)
        tris.append((a, b, c))
        tris.append((a, c, dd))
    return tris


def body_triangles(diameter):
    """3D-треугольники тела со скруглениями. Возвращает (tris, meta)."""
    g = geometry(diameter)
    hole = hole_contour(diameter)
    tris = []

    z_bot = BOT_R
    z_top = THICK - TOP_R

    ext = contour(diameter, 0.0)

    # боковина
    n = len(ext)
    for i in range(n):
        x1, y1 = ext[i]
        x2, y2 = ext[(i + 1) % n]
        tris.append(((x1, y1, z_bot), (x2, y2, z_bot), (x2, y2, z_top)))
        tris.append(((x1, y1, z_bot), (x2, y2, z_top), (x1, y1, z_top)))

    # скругление снизу: r от BOT_R (стенка) к 0 (грань z=0)
    for s in range(FILLET_STEPS):
        t0 = s / float(FILLET_STEPS)
        t1 = (s + 1) / float(FILLET_STEPS)
        r0 = BOT_R * (1.0 - math.cos(t0 * math.pi / 2.0))
        r1 = BOT_R * (1.0 - math.cos(t1 * math.pi / 2.0))
        z0 = z_bot - BOT_R * math.sin(t0 * math.pi / 2.0)
        z1 = z_bot - BOT_R * math.sin(t1 * math.pi / 2.0)
        tris += _ring(contour(diameter, r1), contour(diameter, r0), z1, z0)

    # скругление сверху: от стенки z_top к грани z=THICK
    for s in range(FILLET_STEPS):
        t0 = s / float(FILLET_STEPS)
        t1 = (s + 1) / float(FILLET_STEPS)
        r0 = TOP_R * (1.0 - math.cos(t0 * math.pi / 2.0))
        r1 = TOP_R * (1.0 - math.cos(t1 * math.pi / 2.0))
        z0 = z_top + TOP_R * math.sin(t0 * math.pi / 2.0)
        z1 = z_top + TOP_R * math.sin(t1 * math.pi / 2.0)
        tris += _ring(contour(diameter, r0), contour(diameter, r1), z0, z1)

    # грани
    def faces(poly, z, flip):
        verts = np.array(poly + hole, dtype=np.float64)
        rings = np.array([len(poly), len(poly) + len(hole)], dtype=np.uint32)
        idx = earcut.triangulate_float64(verts, rings)
        pts = poly + hole
        for k in range(0, len(idx), 3):
            a, b, c = pts[idx[k]], pts[idx[k + 1]], pts[idx[k + 2]]
            if flip:
                tris.append(((a[0], a[1], z), (c[0], c[1], z), (b[0], b[1], z)))
            else:
                tris.append(((a[0], a[1], z), (b[0], b[1], z), (c[0], c[1], z)))

    faces(contour(diameter, TOP_R), THICK, False)
    faces(contour(diameter, BOT_R), 0.0, True)

    # стенка отверстия
    nh = len(hole)
    for i in range(nh):
        x1, y1 = hole[i]
        x2, y2 = hole[(i + 1) % nh]
        tris.append(((x1, y1, 0.0), (x2, y2, 0.0), (x2, y2, THICK)))
        tris.append(((x1, y1, 0.0), (x2, y2, THICK), (x1, y1, THICK)))

    meta = {"R": g["R"], "W": 2 * g["w2"], "ear_top": g["ear_top"],
            "hole_r": g["hole_r"], "hole_cy": g["hole_cy"]}
    return tris, meta


def volume(tris):
    v = 0.0
    for a, b, c in tris:
        v += (a[0] * (b[1] * c[2] - b[2] * c[1])
              - a[1] * (b[0] * c[2] - b[2] * c[0])
              + a[2] * (b[0] * c[1] - b[1] * c[0])) / 6.0
    return abs(v)
