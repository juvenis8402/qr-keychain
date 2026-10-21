# -*- coding: utf-8 -*-
"""get_earcut.py — скачать earcut (триангуляция с дырками) в TEMP/qrlib."""
import json
import os
import urllib.request
import zipfile

TMP = os.environ["TEMP"]
LIB = os.path.join(TMP, "qrlib")
os.makedirs(LIB, exist_ok=True)

meta = json.loads(urllib.request.urlopen(
    "https://pypi.org/pypi/earcut/json", timeout=30).read())
wheel = None
for u in meta["urls"]:
    if u["filename"].endswith(".whl"):
        wheel = u
        break
if wheel is None:
    raise SystemExit("wheel не найден")

path = os.path.join(TMP, wheel["filename"])
print("качаю:", wheel["filename"])
urllib.request.urlretrieve(wheel["url"], path)

with zipfile.ZipFile(path) as z:
    z.extractall(LIB)
print("распаковано")

import sys
sys.path.insert(0, LIB)
import earcut
print("earcut ok, версия:", getattr(earcut, "__version__", "?"))

# проверка: квадрат с дыркой
verts = [0, 0, 10, 0, 10, 10, 0, 10,   3, 3, 7, 3, 7, 7, 3, 7]
idx = earcut.earcut(verts, [4], 2)
print("индексов:", len(idx), "треугольников:", len(idx) // 3)
