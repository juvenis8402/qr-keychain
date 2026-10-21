# -*- coding: utf-8 -*-
"""
app.py — генератор брелоков с QR.

Вводишь текст → приложение считает QR, подбирает диаметр брелока
и показывает превью. Сохранение — 3MF, где ТЕЛО и QR+ПРИЦЕЛ
разные части одного объекта (в Bambu красится одной кнопкой).
"""
import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import body
import mesh
import qrgen

COLOUR_BG = "#f4f4f4"
COLOUR_DARK = "#111111"


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Брелок с QR")
        self.geometry("780x580")
        self.minsize(700, 520)

        self.text_var = tk.StringVar(value="ЕСЛИ НАШЛИ 81234567899")
        self.info_var = tk.StringVar(value="")
        self.limit_var = tk.StringVar(value="")
        self.result = None

        self._build_ui()
        self.refresh()

    def _build_ui(self):
        top = tk.Frame(self, padx=12, pady=10)
        top.pack(fill="x")

        tk.Label(top, text="Текст для QR:", font=("Segoe UI", 10)).grid(row=0, column=0, sticky="w")
        entry = tk.Entry(top, textvariable=self.text_var, font=("Segoe UI", 11))
        entry.grid(row=1, column=0, sticky="we")
        entry.bind("<KeyRelease>", lambda e: self.refresh())
        top.columnconfigure(0, weight=1)

        mid = tk.Frame(self, padx=12)
        mid.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(mid, width=340, height=340, bg=COLOUR_BG,
                                highlightthickness=1, highlightbackground="#cccccc")
        self.canvas.pack(side="left", padx=(0, 14), pady=6)

        side = tk.Frame(mid)
        side.pack(side="left", fill="both", expand=True)

        tk.Label(side, textvariable=self.info_var, font=("Consolas", 10),
                 justify="left", anchor="nw").pack(fill="x", pady=(6, 10))
        tk.Label(side, textvariable=self.limit_var, font=("Segoe UI", 9),
                 fg="#555555", justify="left", anchor="nw").pack(fill="x")

        tk.Label(side, text="Диаметр подбирается автоматически под QR и прицел.\n"
                            "Модуль QR — 0,80 мм (оптимум для сканера).\n\n"
                            "В файле 3MF три части: тело, QR, прицел.\n"
                            "В Bambu каждую можно покрасить отдельно.",
                 font=("Segoe UI", 9), fg="#336633", justify="left",
                 anchor="nw", wraplength=330).pack(fill="x", pady=(12, 0))

        bottom = tk.Frame(self, padx=12, pady=12)
        bottom.pack(fill="x")
        self.btn_3mf = tk.Button(bottom, text="Сохранить 3MF", width=18,
                                 font=("Segoe UI", 10), command=self.save_3mf)
        self.btn_3mf.pack(side="left")
        self.btn_stl = tk.Button(bottom, text="Сохранить два STL", width=18,
                                 font=("Segoe UI", 10), command=self.save_stl)
        self.btn_stl.pack(side="left", padx=8)
        tk.Button(bottom, text="Закрыть", width=10,
                  command=self.destroy).pack(side="right")

    def refresh(self):
        text = self.text_var.get().strip()
        self.canvas.delete("all")
        self.limit_var.set(self._limits_text())

        if not text:
            self.info_var.set("Введи текст")
            self._set_buttons(False)
            self.result = None
            return

        try:
            res = qrgen.fit(text)
        except Exception as e:                       # noqa: BLE001
            self.info_var.set("Ошибка QR: %s" % e)
            self._set_buttons(False)
            self.result = None
            return

        self.result = res
        ok = res["fits"]
        self.info_var.set(
            "версия QR: %d\n"
            "модулей: %d   модуль: %.2f мм\n"
            "код: %.1f мм   брелок: Ø%.0f мм\n"
            "байт: %d / %d" % (
                res["version"], res["modules"], res["module_mm"],
                res["size_mm"], res["diameter_mm"],
                res["used"], res["capacity"]))

        if not ok:
            self.info_var.set(self.info_var.get() +
                              "\n\nТекст слишком длинный: брелок больше Ø%.0f мм."
                              % qrgen.MAX_D)
        self._set_buttons(ok)
        self._draw(res["matrix"])

    def _limits_text(self):
        lines = ["версия | модулей | до байт | брелок"]
        for v, mods, cap, d in qrgen.limits():
            lines.append("%7d | %7d | %7d | Ø%d" % (v, mods, cap, d))
        return "\n".join(lines)

    def _set_buttons(self, enabled):
        state = "normal" if enabled else "disabled"
        self.btn_3mf.config(state=state)
        self.btn_stl.config(state=state)

    def _draw(self, matrix):
        n = len(matrix)
        w = self.canvas.winfo_width() or 340
        h = self.canvas.winfo_height() or 340
        pad = 14
        cell = (min(w, h) - 2 * pad) / float(n)
        x0 = (w - cell * n) / 2.0
        y0 = (h - cell * n) / 2.0
        self.canvas.create_rectangle(x0, y0, x0 + cell * n, y0 + cell * n,
                                     fill="white", outline="")
        for cy in range(n):
            for cx in range(n):
                if matrix[cy][cx] == "1":
                    self.canvas.create_rectangle(
                        x0 + cx * cell, y0 + cy * cell,
                        x0 + (cx + 1) * cell, y0 + (cy + 1) * cell,
                        fill=COLOUR_DARK, outline="")

    def _build(self):
        dia = self.result["diameter_mm"]
        body_t = body.body_triangles(dia)[0]
        qr_t = mesh.qr_triangles(self.result["matrix"], self.result["module_mm"])
        sight_t = mesh.sight_triangles(self.result["matrix"], self.result["module_mm"],
                                       qrgen.GAP_MM, qrgen.SIGHT_MM, qrgen.SIGHT_LEN)
        return body_t, qr_t, sight_t

    def save_3mf(self):
        if not self.result or not self.result["fits"]:
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".3mf", filetypes=[("3MF", "*.3mf")],
            initialfile="brelok.3mf")
        if not path:
            return
        try:
            body_t, qr_t, sight_t = self._build()
            mesh.write_3mf(body_t, qr_t, sight_t, path)
            messagebox.showinfo("Готово",
                                "Сохранено:\n%s\n\nТри части: тело, QR, прицел — "
                                "каждую можно красить отдельно." % path)
        except Exception as e:                       # noqa: BLE001
            messagebox.showerror("Ошибка", str(e))

    def save_stl(self):
        if not self.result or not self.result["fits"]:
            return
        base = filedialog.asksaveasfilename(
            defaultextension="_body.stl", filetypes=[("STL", "*.stl")],
            initialfile="brelok")
        if not base:
            return
        try:
            body_t, qr_t, sight_t = self._build()
            root, _ = os.path.splitext(base)
            mesh.write_stl(body_t, root + "_body.stl")
            mesh.write_stl(qr_t, root + "_qr.stl")
            mesh.write_stl(sight_t, root + "_sight.stl")
            messagebox.showinfo("Готово",
                                "Сохранено три файла:\n%s_body.stl\n%s_qr.stl\n%s_sight.stl"
                                % (root, root, root))
        except Exception as e:                       # noqa: BLE001
            messagebox.showerror("Ошибка", str(e))


if __name__ == "__main__":
    App().mainloop()
