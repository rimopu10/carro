# -*- coding: utf-8 -*-
"""
REFUERZO POR SUSPENSIÓN: sube la sección de los tubos que fallan bajo las cargas reales de la suspensión
(cargas_suspension.py: S1 bache 3 g, S2 frenada 1 g, S3 curva 1 g, S4 bache en una rueda), con la paleta de 6 secciones
de siempre, y deja los anclajes (ménsulas) como NODOS del chasis.

Por qué existe: rediseno_chasis.py optimizó con las ruedas como apoyos fijos y dejó los tubos junto a las ruedas en su
piso de sección ("no hay análisis que justifique adelgazarlos"). Con las cargas del piso pasando por los brazos esos tubos
quedan en FS 1.26. Este paso es idempotente y va DESPUÉS de rediseno_chasis.py:

    python calculos/rediseno_chasis.py 8000 ...      (si se rehace la topología)
    python calculos/reforzar_suspension.py           (reescribe calculos/chasis_rediseno.json; la versión anterior está en git: `git show HEAD:calculos/chasis_rediseno.json`)
"""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import cargas_suspension as C

F = C.F
FS_MIN = 2.0           # cargas de servicio: S1..S4 nominales
FS_RARO = 1.5          # casos raros o combinados (S5 bache+curva, S6 alabeo) y cotas de la hiperestaticidad de las bisagras ([axial ..]);
                       # el mismo criterio que LC8 (arnés 1.5) y LC5 (volcadura 1.65): carga excepcional, no de servicio
# 2026-10-21: 7ª sección, RED 57.2x4.0 (2-1/4" x 0.156"), SOLO para las patas del arco y tubos que ya estén en RED 57.2x3.2: con la batería en el túnel central
# el momento de balanceo del pivote trasero ya no se compensa con la masa de la pila atrás y el pie del arco llega a FS 1.74 con el tubo máximo anterior.
PALETA = ["PTR 25x25x1.9", "PTR 38x38x1.9", "PTR 44x44x1.9", "PTR 38x38x3.0", "RED 50.8x2.1", "RED 57.2x3.2", "RED 57.2x4.0"]
SIN_LADO = ("cf1", "cfF", "cf2", "cf3", "cfB")
NODOS_EXTRA = {"cfB": [2.10, 0.16, 0.0]}      # centro del travesaño bat_f: cuarto apoyo de la pila de la batería
# Puntales estructurales que el refuerzo por espesor no sustituye: sin ellos el travesaño fx_hi (que lleva la torre del amortiguador
# a 115 mm de la esquina y 6 kN) no llega a FS 1.5 ni con el tubo más grande de la paleta. Triangulan la torre al nodo fx_lo.
PUNTALES = [("anAMORTL", "fx_loL", "PTR 38x38x1.9", "susp"), ("anAMORTR", "fx_loR", "PTR 38x38x1.9", "susp"),
            # cuarto soporte de la pila (x=2.10): el centro del travesaño bat_f (nodo cfB) se une a la viga central cf2
            ("cf2", "cfB", "PTR 38x38x1.9", "batt"),
            # cierra el aro del arco principal por abajo (travesaño de piso entre sus pies, x=2.02): con la batería en el túnel el pie del
            # arco recibe la flexión de los rieles y las patas ya están en la sección máxima de la paleta
            ("mh_loL", "mh_loR", "PTR 38x38x1.9", "safe")]


def _sec(nombre):
    t, dims = nombre.split(" ", 1)
    v = [float(x) for x in dims.split("x")]
    return F.sec_ptr(v[0] / 1000, v[2] / 1000) if t == "PTR" else F.sec_red(v[0] / 1000, v[1] / 1000)


SECC = {n: _sec(n) for n in PALETA}
ORDEN = sorted(PALETA, key=lambda n: SECC[n]["Iy"])   # flexión y pandeo mandan: se ordena por inercia, no por área


def siguiente(nombre):
    """Siguiente sección con >= 8% más inercia; un tubo redondo (arco, cabecera, tirantes) sigue siendo redondo."""
    i0 = SECC[nombre]["Iy"]
    for n in ORDEN:
        if SECC[n]["Iy"] > 1.08 * i0 and (n.startswith("RED") or not nombre.startswith("RED")):
            return n
    return None


def esp(n):
    return n[:-1] + ("R" if n[-1] == "L" else "L") if n[-1] in "LR" and n not in SIN_LADO else n


def grupos(miembros):
    """Índices de miembros que deben llevar la misma sección: el espejo y los tramos colineales de un mismo tubo
    (nodos de valencia 2 sin cambio de dirección)."""
    padre = list(range(len(miembros)))

    def f(i):
        while padre[i] != i:
            padre[i] = padre[padre[i]]
            i = padre[i]
        return i

    def u(i, j):
        padre[f(i)] = f(j)
    ids = {frozenset((a, b)): i for i, (a, b, s, t) in enumerate(miembros)}
    for i, (a, b, s, t) in enumerate(miembros):
        j = ids.get(frozenset((esp(a), esp(b))))
        if j is not None:
            u(i, j)
    inc = {}
    for i, (a, b, s, t) in enumerate(miembros):
        inc.setdefault(a, []).append(i)
        inc.setdefault(b, []).append(i)
    for n, lst in inc.items():
        if len(lst) == 2:
            i, j = lst
            vi = F.NODES[miembros[i][1]] - F.NODES[miembros[i][0]]
            vj = F.NODES[miembros[j][1]] - F.NODES[miembros[j][0]]
            c = abs(vi @ vj) / np.linalg.norm(vi) / np.linalg.norm(vj)
            if c > 0.9998:
                u(i, j)
    g = {}
    for i in range(len(miembros)):
        g.setdefault(f(i), set()).add(i)
    return {i: g[f(i)] for i in range(len(miembros))}


def peor_por_tubo(out):
    """Margen mínimo por tubo ORIGINAL, normalizado a su requisito (>= 1 cumple): cargas de suspensión (fluencia y pandeo >= FS_MIN)
    y los casos de siempre por tubo (LC1/3/4 >= 2, volcadura >= 1.65, pandeo)."""
    peor = {}
    for nom, r in out["casos"].items():
        req = FS_MIN if (nom[:2] in ("S1", "S2", "S3", "S4") and "[axial" not in nom) else FS_RARO
        for a, b, s, tag in out["miembros"]:
            w = min(r["fs"][(a, b)], r["pandeo"][(a, b)]) / req
            peor[tag[1]] = min(peor.get(tag[1], np.inf), w)
    ev = F.evaluar([(a, b, s, tag[0]) for a, b, s, tag in out["miembros"]])
    for a, b, s, tag in out["miembros"]:
        k = (a, b)
        w = min(ev["fs_miembro"].get(k, np.inf) / FS_MIN, ev["pandeo"].get(k, np.inf) / FS_MIN,
                ev["fs5"].get(k, np.inf) / 1.65, ev["pandeo5"].get(k, np.inf) / 1.65)
        peor[tag[1]] = min(peor.get(tag[1], np.inf), w)
    return peor


def reforzar(mem, verbose=True, estricto=True):
    mem = list(mem)
    gr = grupos(mem)
    historia = []
    for it in range(60):
        out = C.evaluar_suspension(mem)
        peor = peor_por_tubo(out)
        fallan = [i for i, w in peor.items() if w < 1.0]
        if not fallan:
            return mem, out, historia
        cambiar = set()
        for i in fallan:
            cambiar |= gr[i]
        subieron = 0
        for i in sorted(cambiar):
            a, b, s, tag = mem[i]
            nuevo = siguiente(s["nombre"])
            if nuevo is None:
                continue
            mem[i] = (a, b, SECC[nuevo], tag)
            historia.append((it, f"{a}-{b}", s["nombre"], nuevo, peor.get(i, np.nan)))
            subieron += 1
        if verbose:
            print(f"  iteración {it}: {len(fallan)} tubos bajo el requisito (peor margen {min(peor.values()):.2f}) -> {subieron} suben de sección", flush=True)
        if subieron == 0 and not estricto:
            return mem, out, historia
        if subieron == 0:
            sin = [f"{mem[i][0]}-{mem[i][1]} ({mem[i][2]['nombre']}, margen {peor[i]:.2f})" for i in fallan]
            raise RuntimeError(f"no hay sección mayor en la paleta para: {sin}")
    raise RuntimeError("el refuerzo no convergió en 60 iteraciones")


def masa(mem):
    return sum(float(np.linalg.norm(F.NODES[b] - F.NODES[a])) * s["A"] * F.RHO for a, b, s, t in mem)


def resumen_fs(out):
    base = [f"{r['fs_min']:.2f}" for n, r in out["casos"].items() if "[axial" not in n]
    peor = min(out["casos"].items(), key=lambda kv: kv[1]["fs_min"])
    return ", ".join(base) + f"  | peor de todos: {peor[1]['fs_min']:.2f} ({peor[0]})"


def main():
    ruta = os.path.join(HERE, "chasis_rediseno.json")
    mem0 = C.cargar_vigente()
    split, _ = C.preparar(mem0)                          # crea los nodos de anclaje y parte los tubos que los reciben
    mem0 = [(a, b, s, t[0]) for a, b, s, t in split]
    pos_json = dict(json.load(open(os.path.join(HERE, "chasis_rediseno.json"), encoding="utf-8"))["nodos_nuevos"], **NODOS_EXTRA)
    for n, p in NODOS_EXTRA.items():
        if n not in F.NODES:
            F.registrar_nodo(n, p)
    for k_, (a_, b_, s_, t_) in enumerate(list(mem0)):                     # parte el travesaño bat_f en el centro (idempotente)
        if {a_, b_} == {"bat_fL", "bat_fR"}:
            mem0.remove((a_, b_, s_, t_))
            mem0 += [("bat_fL", "cfB", s_, t_), ("cfB", "bat_fR", s_, t_)]
    for a, b, sn, tag in PUNTALES:
        for n in (a, b):
            if n not in F.NODES and n in pos_json:          # nodo del rediseño que el JSON no usaba (p. ej. cf3, apoyo de la pila)
                F.registrar_nodo(n, pos_json[n])
        if not any({x, y} == {a, b} for x, y, s_, t_ in mem0):
            mem0.append((a, b, SECC[sn], tag))
    out0 = C.evaluar_suspension(mem0)
    print(f"antes:   {len(mem0)} miembros, {masa(mem0):.1f} kg, FS (S1..S6) = {resumen_fs(out0)}")
    mem1, out1, hist = reforzar(mem0)
    # el resultado (partido en los anclajes) es lo que se guarda: miembros con el tag original
    final = [(a, b, s, tag[0]) for a, b, s, tag in out1["miembros"]]
    print(f"después: {len(final)} miembros, {masa(final):.1f} kg, FS (S1..S6) = {resumen_fs(out1)}")
    print(f"masa añadida: {masa(final) - masa(mem0):+.1f} kg")
    vistos = {}
    for it, nom, antes, desp, w in hist:
        vistos.setdefault(nom, [antes, desp, w])[1] = desp
    for nom, (antes, desp, w) in sorted(vistos.items()):
        print(f"   {nom:22s} {antes:14s} -> {desp:14s} (FS peor al inicio {w:.2f})")
    r = F.evaluar(final)
    print("casos de siempre con el chasis reforzado: " + "  ".join(f"{c} {v:.2f}" for c, v in r["fs"].items()) + f"   K {r['K_tors']:,.0f} N·m/°  masa {r['masa']:.1f} kg")
    if "--no-escribir" in sys.argv:
        return
    d = json.load(open(ruta, encoding="utf-8"))
    for n, p in NODOS_EXTRA.items():
        d["nodos_nuevos"].setdefault(n, p)
    for n in out1["nodos"].values():
        nodo = n[0]
        if nodo not in d["nodos_nuevos"] and nodo.startswith("an"):
            d["nodos_nuevos"][nodo] = [float(v) for v in F.NODES[nodo]]
    d["miembros"] = [[a, b, s["nombre"], tag] for a, b, s, tag in final]
    d["resumen"] = dict(masa=float(r["masa"]), K_tors=float(r["K_tors"]), fs={k: float(v) for k, v in r["fs"].items()},
                        suspension={k: float(v["fs_min"]) for k, v in out1["casos"].items()})
    json.dump(d, open(ruta, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("escrito", os.path.relpath(ruta))


if __name__ == "__main__":
    main()
