# -*- coding: utf-8 -*-
"""get_earcut2.py — скачать mapbox-earcut (колёса для Windows)."""
import json
import os
import sys
import urllib.request
import zipfile

TMP = os.environ["TEMP"]
LIB = os.path.join(TMP, "qrlib")
os.makedirs(LIB, exist_ok=True)

meta = json.loads(urllib.request.urlopen(
    "https://pypi.org/pypi/mapbox-earcut/json", timeout=30).read())
pick = None
for u in meta["urls"]:
    fn = u["filename"]
    if fn.endswith(".whl") and "cp312" in fn and "win_amd64" in fn:
        pick = u
        break

path = os.path.join(TMP, pick["filename"])
print("качаю:", pick["filename"])
urllib.request.urlretrieve(pick["url"], path)
with zipfile.ZipFile(path) as z:
    z.extractall(LIB)

sys.path.insert(0, LIB)
import numpy as np
import mapbox_earcut as earcut

verts = np.array([[0, 0], [10, 0], [10, 10], [0, 10],
                  [3, 3], [7, 3], [7, 7], [3, 7]], dtype=np.float64)
rings = np.array([4, 8], dtype=np.uint32)
tris = earcut.triangulate_float64(verts, rings)
print("треугольников:", len(tris) // 3, " (ожидание 8)")
