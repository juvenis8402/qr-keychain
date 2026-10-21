# -*- coding: utf-8 -*-
"""
mesh.py — треугольники: тело, QR, прицел — отдельными частями.

В 3MF один объект из трёх частей: Brelok / QR / Sight.
Тогда в Bambu каждую часть можно красить отдельно.
"""
import struct
import zipfile

Z_BODY_TOP = 3.0
Z_SINK = 0.1
Z_RAISE = 0.6


def read_stl(path):
    data = open(path, "rb").read()
    n = struct.unpack("<I", data[80:84])[0]
    tris = []
    for i in range(n):
        off = 84 + i * 50
        v = struct.unpack("<9f", data[off + 12:off + 48])
        tris.append((v[0:3], v[3:6], v[6:9]))
    return tris


def write_stl(tris, path):
    with open(path, "wb") as f:
        f.write(b"\0" * 80)
        f.write(struct.pack("<I", len(tris)))
        for t in tris:
            f.write(struct.pack("<3f", 0, 0, 0))
            for v in t:
                f.write(struct.pack("<3f", *v))
            f.write(b"\0\0")


def _box(x0, x1, y0, y1, z0, z1):
    p = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
         (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    faces = [(0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1),
             (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
    out = []
    for a, b, c, d in faces:
        out.append((p[a], p[b], p[c]))
        out.append((p[a], p[c], p[d]))
    return out


def qr_triangles(matrix, module_mm):
    """Кубики QR — отдельная часть."""
    n = len(matrix)
    half = n * module_mm / 2.0
    z0 = Z_BODY_TOP - Z_SINK
    z1 = Z_BODY_TOP + Z_RAISE
    out = []
    for cy in range(n):
        for cx in range(n):
            if matrix[cy][cx] != "1":
                continue
            x0 = -half + cx * module_mm
            x1 = x0 + module_mm
            yt = half - cy * module_mm
            yb = yt - module_mm
            out.extend(_box(x0, x1, yb, yt, z0, z1))
    return out


def sight_triangles(matrix, module_mm, gap=0.35, sight_t=0.8, sight_len=3.0):
    """Прицел вокруг QR — отдельная часть."""
    n = len(matrix)
    half = n * module_mm / 2.0
    z0 = Z_BODY_TOP - Z_SINK
    z1 = Z_BODY_TOP + Z_RAISE

    inner = half + gap
    outer = inner + sight_t
    out = []

    def plank(sx, sy, axial):
        if axial == "x":
            xa, xb = sorted((sx * outer, sx * (outer - sight_len)))
            ya, yb = sorted((sy * outer, sy * inner))
        else:
            xa, xb = sorted((sx * outer, sx * inner))
            ya, yb = sorted((sy * outer, sy * (outer - sight_len)))
        out.extend(_box(xa, xb, ya, yb, z0, z1))

    for sx in (-1, 1):
        for sy in (-1, 1):
            plank(sx, sy, "x")
            plank(sx, sy, "y")
    return out


def _mesh_xml(tris):
    verts = []
    index = {}
    tris_idx = []
    for t in tris:
        ids = []
        for v in t:
            key = (round(v[0], 4), round(v[1], 4), round(v[2], 4))
            if key not in index:
                index[key] = len(verts)
                verts.append(key)
            ids.append(index[key])
        tris_idx.append(ids)
    vx = "".join('<vertex x="%.4f" y="%.4f" z="%.4f"/>' % v for v in verts)
    tx = "".join('<triangle v1="%d" v2="%d" v3="%d"/>' % tuple(i) for i in tris_idx)
    return "<mesh><vertices>%s</vertices><triangles>%s</triangles></mesh>" % (vx, tx)


def write_3mf(body_tris, qr_tris, sight_tris, path,
              body_name="Brelok", qr_name="QR", sight_name="Sight"):
    """3MF: один объект, три части — тело, QR, прицел."""
    content_types = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>'
        '</Types>')

    rels = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Target="/3D/3dmodel.model" Id="rel0" '
        'Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>'
        '</Relationships>')

    model = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<model unit="millimeter" xml:lang="ru-RU" '
        'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">'
        '<resources>'
        '<object id="2" type="model" name="%s">%s</object>'
        '<object id="3" type="model" name="%s">%s</object>'
        '<object id="4" type="model" name="%s">%s</object>'
        '<object id="1" type="model" name="%s">'
        '<components>'
        '<component objectid="2"/>'
        '<component objectid="3"/>'
        '<component objectid="4"/>'
        '</components>'
        '</object>'
        '</resources>'
        '<build><item objectid="1"/></build>'
        '</model>') % (
            body_name, _mesh_xml(body_tris),
            qr_name, _mesh_xml(qr_tris),
            sight_name, _mesh_xml(sight_tris),
            body_name)

    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", content_types)
        z.writestr("_rels/.rels", rels)
        z.writestr("3D/3dmodel.model", model)
    return path
