# -*- coding: utf-8 -*-
"""mov_info.py — длительность и разрешение MOV без ffmpeg."""
import os
import struct
import sys

D = r"D:\Harness\brelok_app\Видеоматериал"


def boxes(data, start, end):
    """Перебрать боксы в диапазоне."""
    pos = start
    while pos + 8 <= end:
        size, kind = struct.unpack(">I4s", data[pos:pos + 8])
        if size == 0:
            size = end - pos
        if size < 8:
            break
        yield kind.decode("latin1"), pos, pos + size
        pos += size


def find(data, start, end, path):
    if not path:
        return None
    for kind, a, b in boxes(data, start, end):
        if kind == path[0]:
            if len(path) == 1:
                return a, b
            inner = a + 8
            if kind in ("meta",):
                inner = a + 12
            r = find(data, inner, b, path[1:])
            if r:
                return r
    return None


for name in sorted(os.listdir(D)):
    if not name.lower().endswith(".mov"):
        continue
    p = os.path.join(D, name)
    data = open(p, "rb").read()
    res = find(data, 0, len(data), ["moov", "mvhd"])
    dur = None
    if res:
        a, _b = res
        ver = data[a + 8]
        if ver == 0:
            timescale, duration = struct.unpack(">II", data[a + 20:a + 28])
        else:
            timescale, duration = struct.unpack(">IQ", data[a + 28:a + 40])
        if timescale:
            dur = duration / float(timescale)

    # размеры из tkhd
    wh = None
    r2 = find(data, 0, len(data), ["moov", "trak", "tkhd"])
    if r2:
        a, b = r2
        raw = data[b - 8:b]
        w = struct.unpack(">I", data[b - 8:b - 4])[0] / 65536.0
        h = struct.unpack(">I", data[b - 4:b])[0] / 65536.0
        wh = (round(w), round(h))

    print("%-42s %6.1f с (%d:%02d)  %s" % (
        name,
        dur or 0, int((dur or 0) // 60), int((dur or 0) % 60), wh))
