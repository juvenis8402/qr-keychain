# -*- coding: utf-8 -*-
"""test_body.py — проверка параметрического тела без Fusion."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import body
import mesh

for d in (30, 38, 45):
    tris, meta = body.body_triangles(d)
    vol = body.volume(tris)
    print("D%d: треугольников %d, объём %.3f см3, R %.1f, W %.1f, верх ушка %.1f, отверстие Y %.2f..%.2f"
          % (d, len(tris), vol / 1000.0, meta["R"], meta["W"], meta["ear_top"],
             meta["hole_cy"] - meta["hole_r"], meta["hole_cy"] + meta["hole_r"]))
    out = os.path.join(os.environ["TEMP"], "body_%d.stl" % d)
    mesh.write_stl(tris, out)
    print("   записано:", out, os.path.getsize(out))
