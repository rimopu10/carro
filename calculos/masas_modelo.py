# -*- coding: utf-8 -*-
"""
MASAS DEL MODELO FEM (presupuesto por componente, 2026-10-21). Sustituye al reparto de la masa «faltante» por longitud de tubo, que daba un
CG de 45% delante sin que nadie decidiera dónde iba la batería. Ver docs/masas-y-bateria.md y calculos/masas_cg.py (mismas posiciones).

Decisión de diseño: batería de 30 celdas prismáticas COMPLETA en el túnel central entre los asientos (soportada por 4 travesaños del piso
cf1, cfF, cf2 y cfB = centro del travesaño bat_f en x=2.10), electrónica de potencia atrás junto a los motores de cubo (cables de fase cortos), nariz libre.

`fijas(nodos)` devuelve {nodo: kg} (sin la masa del propio chasis, que se reparte por longitud de tubo) o None si el diseño cargado no tiene
los nodos del rediseño (p. ej. CHASIS_BASE=1): entonces los llamadores usan el reparto antiguo.
"""
PACK_KG = 90.0
PACK_NODOS = {"cf1": 0.16, "cfF": 0.25, "cf2": 0.33, "cfB": 0.26}      # fracción de la pila (x 1.05-2.16) que carga cada travesaño (x 1.10, 1.36, 1.66, 2.10)
PACK_H = 0.13                  # m: el centro de la pila queda 0.13 sobre el travesaño del piso (y 0.29 contra 0.16)

_FIJAS = {
    # suspensión suspendida (mitad interna de brazos, coilovers) en los nodos de los anclajes
    "fb_loL": 4.0, "fb_loR": 4.0, "fx_loL": 4.0, "fx_loR": 4.0,
    "taL": 6.0, "taR": 6.0, "coilL": 5.0, "coilR": 5.0,
    # electrónica de potencia (2 controladores, cargador, DC-DC, contactores): atrás, sobre los travesaños bat_f / bat_r
    "bat_fL": 3.75, "bat_fR": 3.75, "bat_rL": 3.75, "bat_rR": 3.75,
    # butacas (5 kg c/estación) + ocupantes de 90 kg (45 kg por estación del riel)
    "smFL": 50.0, "smFR": 50.0, "smRL": 50.0, "smRR": 50.0,
    # carrocería (piel) en sus anclajes, puertas en sus bisagras, vidrios en cabecera y base del pilar A
    "dash_loL": 5.0 + 9.5, "dash_loR": 5.0 + 9.5, "mh_loL": 15.0, "mh_loR": 15.0,     # piel: CG de la carrocería a x~1.80 (1/4 delante, 3/4 atrás)
    "h1L": 6.0, "h2L": 6.0, "h1R": 6.0, "h2R": 6.0,
    "hdrL": 3.0, "hdrR": 3.0, "dash_hiL": 3.0, "dash_hiR": 3.0,
    # dirección, pedalera, frenos (líneas y cilindros): CG a x~0.92 (19 kg en dash_lo, 6 kg en fb_hi); las 5 kg de piel de dash_lo van aparte
    "fb_hiL": 3.0, "fb_hiR": 3.0,
    # cableado, tablet, luces, piso, varios: eje central
    "cf1": 5.0, "cfF": 10.0, "cf2": 10.0, "cfB": 5.0,
}


# Masas cuyo CG está ARRIBA del nodo del piso donde se atornillan: (kg, metros sobre el nodo). Su fuerza de inercia se aplica en el nodo con el
# momento F x h (cargas_suspension.masas_todas). Sin esto el modelo subestima la transferencia de carga: CG de 0.365 m contra 0.40 del presupuesto.
ELEVACION = {
    "smFL": [(45.0, 0.30), (5.0, 0.14)], "smFR": [(45.0, 0.30), (5.0, 0.14)],      # ocupante (cadera y=0.26 + torso) y butaca
    "smRL": [(45.0, 0.30), (5.0, 0.14)], "smRR": [(45.0, 0.30), (5.0, 0.14)],
    "dash_loL": [(5.0, 0.34)], "dash_loR": [(5.0, 0.34)], "mh_loL": [(15.0, 0.34)], "mh_loR": [(15.0, 0.34)],   # piel (CG y~0.50)
    "bat_fL": [(3.75, 0.14)], "bat_fR": [(3.75, 0.14)], "bat_rL": [(3.75, 0.14)], "bat_rR": [(3.75, 0.14)],      # electrónica
    "cf1": [(5.0, 0.14)], "cfF": [(10.0, 0.14)], "cf2": [(10.0, 0.14)], "cfB": [(5.0, 0.14)],                     # varios
}


def elevadas(nodo):
    """Lista (kg, dy) de las masas elevadas de un nodo, incluida la parte de la pila de la batería."""
    lista = list(ELEVACION.get(nodo, []))
    if nodo in PACK_NODOS:
        lista.append((PACK_KG * PACK_NODOS[nodo], PACK_H))
    return lista


def fijas(nodos):
    """Masas puntuales (kg) para los nodos presentes en `nodos`, o None si falta alguno (diseño base sin el rediseño)."""
    d = dict(_FIJAS)
    for n, f in PACK_NODOS.items():
        d[n] = d.get(n, 0.0) + PACK_KG * f
    if any(n not in nodos for n in d):
        return None
    return d


def total():
    return sum(_FIJAS.values()) + PACK_KG
