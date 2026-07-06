# -*- coding: utf-8 -*-
"""
Genera DXF R12 (ASCII) listos para cotizar corte láser en placa de acero 4.7 mm (3/16").
Piezas con aligeramiento inspirado en la optimización topológica del proyecto.
Unidades: mm.
"""
import math, os

def dxf_open():
    return ["0", "SECTION", "2", "ENTITIES"]

def dxf_close(lines):
    lines += ["0", "ENDSEC", "0", "EOF"]
    return "\n".join(lines) + "\n"

def line(lines, x1, y1, x2, y2):
    lines += ["0", "LINE", "8", "CORTE",
              "10", f"{x1:.3f}", "20", f"{y1:.3f}", "30", "0",
              "11", f"{x2:.3f}", "21", f"{y2:.3f}", "31", "0"]

def circle(lines, cx, cy, r):
    lines += ["0", "CIRCLE", "8", "CORTE",
              "10", f"{cx:.3f}", "20", f"{cy:.3f}", "30", "0", "40", f"{r:.3f}"]

def polygon(lines, pts):
    for i in range(len(pts)):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % len(pts)]
        line(lines, x1, y1, x2, y2)

HERE = os.path.dirname(__file__)

# ---------- 1) Cartela de torre coilover trasera (x4: 2 por lado, tipo sandwich) ----------
# Triángulo estructural con chaflanes; 2 barrenos M10 a chasis, 1 barreno 12mm perno coilover,
# aligeramientos orgánicos (del patrón del caso 'soporte' de la optimización topológica).
d = dxf_open()
outline = [
    (0, 0), (150, 0), (150, 22), (30, 108), (0, 120), (0, 0)
]
polygon(d, outline[:-1])
circle(d, 18, 14, 5.25)     # M10 chasis
circle(d, 132, 14, 5.25)    # M10 chasis
circle(d, 16, 104, 6.10)    # perno 12mm coilover
# aligeramientos siguiendo el camino de carga (diagonal)
circle(d, 62, 34, 15)
circle(d, 95, 24, 11)
circle(d, 38, 62, 11)
with open(os.path.join(HERE, "cartela-torre-coilover.dxf"), "w") as f:
    f.write(dxf_close(d))

# ---------- 2) Placa lateral de cuna de batería (x2) ----------
# 540 x 140, 4 barrenos M8 a los travesaños, ranuras para cinchos de la caja,
# aligeramientos centrales (zona de baja carga según el caso 'chasis' del topopt).
d = dxf_open()
polygon(d, [(0, 0), (540, 0), (540, 140), (0, 140)])
for cx in (20, 520):
    for cy in (20, 120):
        circle(d, cx, cy, 4.25)          # M8
for cx in (135, 270, 405):
    # ranura vertical 12 x 40 para cincho (como obround: 2 líneas + 2 semicírculos aprox por líneas)
    x1, x2 = cx - 6, cx + 6
    y1, y2 = 50, 90
    line(d, x1, y1, x1, y2); line(d, x2, y1, x2, y2)
    # semicírculos como arcos aproximados con segmentos
    for (cyc, start) in [(y2, 0.0), (y1, math.pi)]:
        prev = None
        for k in range(13):
            a = start + math.pi * k / 12
            px, py = cx + 6 * math.cos(a), cyc + 6 * math.sin(a) * (1 if cyc == y2 else 1)
            if cyc == y1:
                py = cyc - abs(6 * math.sin(a))
            else:
                py = cyc + abs(6 * math.sin(a))
            if prev:
                line(d, prev[0], prev[1], px, py)
            prev = (px, py)
for cx in (75, 205, 335, 465):
    circle(d, cx, 70, 22)                # aligeramiento
with open(os.path.join(HERE, "placa-cuna-bateria.dxf"), "w") as f:
    f.write(dxf_close(d))

# ---------- 3) Cartela de pivote de brazo trasero (x4) ----------
d = dxf_open()
polygon(d, [(0, 0), (110, 0), (110, 26), (26, 90), (0, 90)])
circle(d, 16, 16, 5.25)     # M10
circle(d, 94, 13, 5.25)     # M10
circle(d, 14, 74, 7.15)     # buje 14mm pivote
circle(d, 52, 32, 12)       # aligeramiento
with open(os.path.join(HERE, "cartela-pivote-brazo.dxf"), "w") as f:
    f.write(dxf_close(d))

print("OK dxf: cartela-torre-coilover.dxf (x4), placa-cuna-bateria.dxf (x2), cartela-pivote-brazo.dxf (x4)")
