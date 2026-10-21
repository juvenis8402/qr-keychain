# -*- coding: utf-8 -*-
"""
qrgen.py — локальная генерация QR и расчёт диаметра брелока под него.

Логика: текст -> QR (segno) -> модуль 0.8 мм -> размер кода ->
диаметр брелока = √2 × (код + 2 × обвязка), где обвязка — зазор + прицел + поле.

Кириллица в QR — UTF-8, 2 байта на букву.
"""
import math
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_LIB = os.path.join(_HERE, "lib")
if _LIB not in sys.path:
    sys.path.insert(0, _LIB)

import segno  # noqa: E402

MODULE_MM = 0.80       # размер модуля QR
GAP_MM = 0.35          # зазор от кода до прицела
SIGHT_MM = 0.80        # толщина линий прицела
SIGHT_LEN = 3.0        # длина луча прицела
EDGE_MM = 1.5          # поле от прицела до кромки
MAX_D = 70.0           # разумный предел брелока

CAPACITY_BYTE_L = {1: 17, 2: 32, 3: 53, 4: 78, 5: 106, 6: 134,
                   7: 154, 8: 192, 9: 230, 10: 271}


def modules_of(version):
    return 17 + 4 * version


def fit(text, module_mm=MODULE_MM):
    """
    Подобрать QR и диаметр брелока под него.

    Возвращает: matrix, version, modules, module_mm, size_mm (код),
    diameter_mm (брелок), fits (не превышает MAX_D), used/capacity.
    """
    if not text:
        raise ValueError("пустой текст")

    qr = segno.make(text, error="l", micro=False)
    version = qr.version
    modules = modules_of(version)
    size = modules * module_mm

    margin = GAP_MM + SIGHT_MM + EDGE_MM
    diameter = math.sqrt(2.0) * (size + 2.0 * margin)
    diameter = float(math.ceil(diameter))

    cap = CAPACITY_BYTE_L.get(version, 0)
    used = len(text.encode("utf-8"))

    matrix = ["".join("1" if b else "0" for b in row) for row in qr.matrix]
    return {
        "matrix": matrix,
        "version": version,
        "modules": modules,
        "module_mm": module_mm,
        "size_mm": round(size, 2),
        "diameter_mm": diameter,
        "used": used,
        "capacity": cap,
        "fits": diameter <= MAX_D,
    }


def limits(module_mm=MODULE_MM):
    """Таблица: версия -> нужный диаметр и ёмкость."""
    margin = GAP_MM + SIGHT_MM + EDGE_MM
    out = []
    for v, cap in sorted(CAPACITY_BYTE_L.items()):
        size = modules_of(v) * module_mm
        d = math.ceil(math.sqrt(2.0) * (size + 2.0 * margin))
        out.append((v, modules_of(v), cap, d))
    return out
