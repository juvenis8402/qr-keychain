# -*- coding: utf-8 -*-
"""test_gen.py — проверка: текст -> QR -> диаметр -> тело -> 3MF (3 части)."""
import os
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import body
import mesh
import qrgen

for v, mods, cap, d in qrgen.limits():
    print("v%d: %d модулей, до %d байт, брелок Ø%d" % (v, mods, cap, d))

for text in ("ЕСЛИ НАШЛИ 81234567899",
             "ЕСЛИ НАШЛИ ПОЗВОНИТЕ ПО НОМЕРУ 81234567899",
             "81234567899"):
    r = qrgen.fit(text)
    print("\nтекст: %r" % text[:40])
    print("  v%d, модулей %d, код %.1f, брелок Ø%.0f, байт %d/%d"
          % (r["version"], r["modules"], r["size_mm"], r["diameter_mm"],
             r["used"], r["capacity"]))
    tb = body.body_triangles(r["diameter_mm"])[0]
    tq = mesh.qr_triangles(r["matrix"], r["module_mm"])
    ts = mesh.sight_triangles(r["matrix"], r["module_mm"])
    print("  тело %.3f см3, QR %d тр., прицел %d тр."
          % (body.volume(tb) / 1000.0, len(tq), len(ts)))
    out = os.path.join(os.environ["TEMP"], "test_%d.3mf" % r["version"])
    mesh.write_3mf(tb, tq, ts, out)
    with zipfile.ZipFile(out) as z:
        model = z.read("3D/3dmodel.model").decode("utf-8")
    print("  3MF %.0f КБ, объект(ов) %d, компонент %d, части QR/Sight: %s/%s"
          % (os.path.getsize(out) / 1024.0, model.count("<object "),
             model.count("<component "),
             'name="QR"' in model, 'name="Sight"' in model))
