# -*- coding: utf-8 -*-
"""
PRESUPUESTO DE MASAS POR COMPONENTE y ubicación de la batería: reparto estático, altura del CG e inercias para cada alternativa.

Base: docs/superpowers/specs/2026-07-05-carro-electrico-design.md (filosofía: pocas piezas, reparable, motor de cubo trasero 2xQS273,
LiFePO4 96V 105Ah = 30 celdas prismáticas, electrónica de potencia en la nariz). Posiciones en el sistema del proyecto
(x hacia atrás, y arriba, z lateral); todas las masas son simétricas en z salvo indicación.

    python calculos/masas_cg.py
"""
import contextlib
import io
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

X_EJE_DEL, X_EJE_TRAS = 0.55, 2.68
BATALLA = X_EJE_TRAS - X_EJE_DEL

# celda prismática LiFePO4 105 Ah (EVE LF105 y similares): 130 x 36 x 200 mm, ~2.0 kg; 30 celdas en serie = 96 V
CELDAS, CELDA_ESPESOR, CELDA_ANCHO, CELDA_ALTO, KG_PACK = 30, 0.036, 0.130, 0.200, 90.0


def chasis_masas():
    """Tubos del chasis vigente como masas puntuales en el punto medio de cada tubo."""
    with contextlib.redirect_stdout(io.StringIO()):
        import cargas_suspension as C
        mem = C.cargar_vigente()
        F = C.F
    out = []
    for a, b, s, tag in mem:
        L = float(np.linalg.norm(F.NODES[b] - F.NODES[a]))
        m = L * s["A"] * F.RHO
        mid = (F.NODES[a] + F.NODES[b]) / 2
        out.append((m, mid[0], mid[1], mid[2]))
    return out


def componentes(bateria, electronica=(0.25, 0.30)):
    """Lista (nombre, kg, x, y, z) sin la batería + la batería según `bateria` = lista de (kg, x, y)."""
    ch = chasis_masas()
    kg_ch = sum(m for m, *_ in ch)
    c = [("chasis", kg_ch, sum(m * x for m, x, y, z in ch) / kg_ch, sum(m * y for m, x, y, z in ch) / kg_ch, 0.0)]
    c += [
        ("ruedas+mangueta+freno del. (no susp.)", 36.0, 0.55, 0.29, 0.0),
        ("motores de cubo+rueda tras. (no susp.)", 90.0, 2.68, 0.30, 0.0),
        ("brazos y coilovers del. (susp.)", 16.0, 0.60, 0.30, 0.0),
        ("brazos y coilovers tras. (susp.)", 22.0, 2.50, 0.30, 0.0),
        ("electrónica de potencia (controladores, cargador, DC-DC, contactores)", 15.0, electronica[0], electronica[1], 0.0),
        ("butacas (2)", 20.0, 1.58, 0.30, 0.0),
        ("ocupantes (2 x 90 kg: el 690 kg del proyecto)", 180.0, 1.55, 0.46, 0.0),
        ("carrocería de Tripo (piel)", 40.0, 1.80, 0.50, 0.0),
        ("puertas (2)", 24.0, 1.70, 0.72, 0.0),
        ("vidrios y policarbonato", 12.0, 1.25, 0.85, 0.0),
        ("dirección, pedales, frenos (líneas, cilindros)", 25.0, 0.95, 0.35, 0.0),
        ("cableado, tablet, luces, piso, varios", 30.0, 1.60, 0.30, 0.0),
    ]
    c += [(f"batería #{i+1}", kg, x, y, 0.0) for i, (kg, x, y) in enumerate(bateria)]
    return c


def metricas(comp):
    M = sum(k for _, k, *_ in comp)
    x = sum(k * px for _, k, px, py, pz in comp) / M
    y = sum(k * py for _, k, px, py, pz in comp) / M
    I_guin = sum(k * ((px - x) ** 2 + pz ** 2) for _, k, px, py, pz in comp)
    I_cab = sum(k * ((px - x) ** 2 + (py - y) ** 2) for _, k, px, py, pz in comp)
    I_bal = sum(k * ((py - y) ** 2 + pz ** 2) for _, k, px, py, pz in comp)
    return dict(M=M, x=x, y=y, delante=(X_EJE_TRAS - x) / BATALLA, I_guin=I_guin, I_cab=I_cab, I_bal=I_bal)


# geometría de la batería: pila de 30 celdas, largo = 30 x 36 mm + placas = ~1.14 m; ancho 0.13, alto 0.20 (más caja 2 cm)
def pila(n, x0, y_centro):
    L = n * CELDA_ESPESOR + 0.03
    return (KG_PACK * n / CELDAS, x0 + L / 2, y_centro), L


def escenarios():
    out = {}
    out["A actual: cuna tras los asientos (x 2.10-2.64)"] = [(KG_PACK / 2, 2.19, 0.31), (KG_PACK / 2, 2.55, 0.31)]
    for n_tunel in (30, 24, 20, 15, 10):
        b1, L1 = pila(n_tunel, 1.05, 0.293)
        b = [b1]
        if n_tunel < CELDAS:
            b2, _ = pila(CELDAS - n_tunel, 2.12, 0.31)
            b.append(b2)
        out[f"túnel central {n_tunel} celdas ({L1:.2f} m)" + (f" + {CELDAS - n_tunel} tras los asientos" if n_tunel < CELDAS else "")] = b
    # pila en el piso bajo los asientos está descartada por altura de techo (+67 mm sobre la coronilla)
    return out


ELECTRONICA = {"nariz": (0.25, 0.30), "trasera, junto a los motores": (2.30, 0.30)}


if __name__ == "__main__":
    print(f"{'escenario':76s} {'masa':>5s} {'delante':>8s} {'CG x':>5s} {'CG y':>6s} {'I guiñ.':>8s} {'I cab.':>7s}")
    for nom, bat in escenarios().items():
        for en, ep in ELECTRONICA.items():
            if "túnel central" in nom and nom.count("+") and "30 celdas" not in nom and "20 celdas" not in nom:
                continue
            m = metricas(componentes(bat, ep))
            print(f"{nom + ' | electrónica ' + en.split(',')[0]:76s} {m['M']:5.0f} {m['delante']*100:7.1f}% {m['x']:5.2f} {m['y']:6.3f} {m['I_guin']:8.0f} {m['I_cab']:7.0f}")
