# -*- coding: utf-8 -*-
"""
Prototipo funcional a escala (1:5 por defecto) del chasis, generado desde la MISMA fuente
que el carro a tamaño real: planos/lista-corte-tubos.csv (lo escribe analisis_chasis.py).

Nada se dibuja aparte: se escalan los nodos, se cambia la sección por la del tubo comercial
del modelo y se vuelven a calcular los cortes (inglete / descuento en cada nudo) con LA MISMA
regla que usa analisis_chasis.py. Con escala=1 y las secciones reales el resultado tiene que
coincidir con el CSV de tamaño real (test_mini.py lo comprueba).

Correr:  python calculos/mini.py [--escala 5] [--stock 1000]
Salida:  planos/mini-1a5/lista-corte.csv, nodos.csv, barras.csv, resumen.md
"""
import argparse
import csv
import os
import re
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
CSV_REAL = os.path.join(HERE, "..", "planos", "lista-corte-tubos.csv")

# Tubo del modelo: único (el que se consigue). b = lado, t = pared, en mm.
MINI_B, MINI_T = 8.0, 1.0
THETA_MIN = 12.0            # igual que analisis_chasis.py
KERF = 1.0                  # mm de disco/sierra
SOBRANTE_PUNTA = 5.0        # mm que se pierden al escuadrar la punta de cada barra


def c_real(seccion):
    """Semiancho del tubo real a partir de su nombre ('PTR 38x38x1.9', 'RED 57.2x3.2')."""
    return float(re.search(r"(\d+(?:\.\d+)?)x", seccion).group(1)) / 2.0


def leer(path=CSV_REAL):
    """Miembros (ya fusionados por el taller) del CSV a tamaño real. Coordenadas en metros."""
    out = []
    with open(path, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if not r["#"].isdigit():
                continue
            out.append({
                "a": r["de_nodo"], "b": r["a_nodo"], "sec": r["seccion"], "tag": r["funcion"],
                "pa": np.array([float(r[k]) for k in ("x1", "y1", "z1")]) / 1000.0,
                "pb": np.array([float(r[k]) for k in ("x2", "y2", "z2")]) / 1000.0,
                "real": r,
            })
    return out


def cortes(miembros, c_de):
    """Largo de corte e inglete de cada extremo. Misma regla que analisis_chasis.py.

    c_de(miembro) -> semiancho del tubo en m. Devuelve una lista paralela a `miembros`.
    """
    def vecinos(nodo, propio):
        return [o for o in miembros if o is not propio and nodo in (o["a"], o["b"])]

    def dirv(e, desde):
        v = e["pb"] - e["pa"]
        return v / np.linalg.norm(v) * (1 if e["a"] == desde else -1)

    res = []
    for e in miembros:
        L = float(np.linalg.norm(e["pb"] - e["pa"]))
        desc, det = 0.0, []
        for nodo in (e["a"], e["b"]):
            vs = vecinos(nodo, e)
            if not vs:
                det.append(("libre", 90.0, "recto"))
                continue
            mio = dirv(e, nodo)
            best = max(vs, key=lambda o: (c_de(o), abs(float(np.dot(mio, dirv(o, nodo))))))
            dot = float(np.dot(mio, dirv(best, nodo)))
            phi = np.degrees(np.arccos(np.clip(dot, -1, 1)))
            if phi > 150.0:
                defl = 180.0 - phi
                desc += c_de(best) * np.tan(np.radians(defl / 2))
                det.append((f'{best["a"]}-{best["b"]}', phi, "recto" if defl < 2 else f"inglete {defl/2:.0f}°"))
                continue
            th = max(np.degrees(np.arccos(np.clip(abs(dot), 0, 1))), THETA_MIN)
            desc += c_de(best) / np.sin(np.radians(th))
            redondo = best["sec"].startswith("RED") and best.get("redondo", True)
            det.append((f'{best["a"]}-{best["b"]}', th, "destaje de silla" if redondo else f"inglete {th/2:.0f}°"))
        res.append({"L": L, "corte": L - desc, "extremos": det})
    return res


def distancia_segmentos(p1, q1, p2, q2):
    """Distancia mínima entre dos segmentos 3D (Ericson, Real-Time Collision Detection)."""
    d1, d2, r = q1 - p1, q2 - p2, p1 - p2
    a, e, f = d1 @ d1, d2 @ d2, d2 @ r
    if a < 1e-12 and e < 1e-12:
        return float(np.linalg.norm(r))
    if a < 1e-12:
        s, t = 0.0, np.clip(f / e, 0, 1)
    else:
        c = d1 @ r
        if e < 1e-12:
            s, t = np.clip(-c / a, 0, 1), 0.0
        else:
            b = d1 @ d2
            den = a * e - b * b
            s = np.clip((b * f - c * e) / den, 0, 1) if den > 1e-12 else 0.0
            t = (b * s + f) / e
            if t < 0:
                t, s = 0.0, np.clip(-c / a, 0, 1)
            elif t > 1:
                t, s = 1.0, np.clip((b - c) / a, 0, 1)
    return float(np.linalg.norm((p1 + d1 * s) - (p2 + d2 * t)))


def choques(miembros, k, luz_min_mm=0.5):
    """Pares sin nodo común con luz a tamaño real pero sin luz a escala k.

    El tubo del modelo no se encoge con la escala (8 mm contra 38/5 = 7.6 mm, y 8 contra
    25/5 = 5 mm): lo que en el carro tiene luz, en la mini puede rozar.
    """
    out = []
    n = len(miembros)
    for i in range(n):
        for j in range(i + 1, n):
            e, o = miembros[i], miembros[j]
            if {e["a"], e["b"]} & {o["a"], o["b"]}:
                continue
            d = distancia_segmentos(e["pa"], e["pb"], o["pa"], o["pb"]) * 1000       # mm, tamaño real
            luz_real = d - c_real(e["sec"]) - c_real(o["sec"])
            luz_mini = d / k - MINI_B
            if luz_real > 0 and luz_mini < luz_min_mm:
                out.append((e, o, luz_real, luz_mini))
    return out


def barras(piezas, stock, kerf=KERF, punta=SOBRANTE_PUNTA):
    """First-fit decreasing sobre barras de `stock` mm. piezas: [(id, largo_mm)]."""
    libre = stock - 2 * punta
    lista = []
    for pid, largo in sorted(piezas, key=lambda p: -p[1]):
        if largo > libre:
            raise ValueError(f"pieza {pid} de {largo:.0f} mm no cabe en barra de {stock} mm")
        for b in lista:
            if b["resta"] >= largo + kerf:
                b["piezas"].append((pid, largo))
                b["resta"] -= largo + kerf
                break
        else:
            lista.append({"piezas": [(pid, largo)], "resta": libre - largo - kerf})
    return lista


def plantilla(r, k, salida):
    """PDF a tamaño 1:1 de la mini (página = envolvente en mm): lado (x-y) y planta (x-z).

    Se imprime en copistería a escala 100% y se sueldan los tubos sobre el papel: cada nodo
    lleva su nombre y cada tubo su número de la lista de corte.
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    P = np.array(list(r["nodos"].values()))
    ancho = P[:, 0].max() - P[:, 0].min() + 40
    for nombre, (i, j), etiqueta in (("lado", (0, 1), "LADO (x atrás →, y arriba)"),
                                     ("planta", (0, 2), "PLANTA (x atrás →, z ancho)")):
        lo = P[:, [i, j]].min(axis=0) - 20
        hi = P[:, [i, j]].max(axis=0) + 20
        w, h = (hi - lo) / 25.4
        fig = plt.figure(figsize=(w, h + 0.4))
        ax = fig.add_axes([0, 0, 1, h / (h + 0.4)])
        ax.set_xlim(lo[0], hi[0]); ax.set_ylim(lo[1], hi[1])
        ax.set_aspect("equal"); ax.axis("off")
        for f in r["filas"]:
            a, b = r["nodos"][f["de"]], r["nodos"][f["a"]]
            ax.plot([a[i], b[i]], [a[j], b[j]], color="#555", lw=MINI_B * 72 / 25.4, solid_capstyle="butt", alpha=0.25)
            ax.plot([a[i], b[i]], [a[j], b[j]], color="k", lw=0.4)
            ax.text((a[i] + b[i]) / 2, (a[j] + b[j]) / 2, str(f["n"]), fontsize=5, color="#b00", ha="center", va="center")
        for n, p in r["nodos"].items():
            ax.plot(p[i], p[j], "o", ms=1.5, color="#06c")
            ax.text(p[i] + 1.5, p[j] + 1.5, n, fontsize=4, color="#06c")
        fig.text(0.005, 0.99, f"Mini 1:{k:g} — {etiqueta} — imprimir al 100% (1 mm = 1 mm); rojo = # de lista-corte.csv, azul = nodo",
                 fontsize=6, va="top")
        fig.savefig(os.path.join(salida, f"plantilla-{nombre}.pdf"))
        plt.close(fig)


def resumen(r, k, stock, salida):
    corto = [f for f in r["filas"] if f["largo_corte_mm"] < 20]
    secs = {}
    for f in r["filas"]:
        secs[f["seccion_real"]] = secs.get(f["seccion_real"], 0) + 1
    with open(os.path.join(salida, "resumen.md"), "w", encoding="utf-8") as f:
        f.write(f"# Mini 1:{k:g} — resumen (generado por calculos/mini.py; no editar a mano)\n\n")
        f.write(f"- Fuente: `planos/lista-corte-tubos.csv` (tamaño real), coordenadas ÷ {k:g}.\n")
        f.write(f"- Tubo del modelo: **{MINI_B:g}×{MINI_B:g}×{MINI_T:g}** para todo (el tubo no escala; ver tabla).\n")
        f.write(f"- {len(r['filas'])} tubos, {len(r['nodos'])} nodos, **{r['total_mm']/1000:.2f} m** de tubo "
                f"en {len(r['barras'])} barras de {stock:g} mm (sierra {KERF:g} mm, {SOBRANTE_PUNTA:g} mm por punta).\n")
        f.write(f"- Choques a escala (tubos que tienen luz en el real y se tocan en la mini): "
                f"**{len(r['choques'])}**.\n")
        f.write(f"- Cortes de menos de 20 mm ({len(corto)}): " + (", ".join(f"#{x['n']} {x['de']}–{x['a']} ({x['largo_corte_mm']:.0f} mm)" for x in corto) or "ninguno") + ".\n\n")
        f.write("## Qué tubo real representa cada tubo de 8 mm\n\n| Sección real | Equivale a 1:%g | Tubos | Lado del modelo ÷ lado escalado |\n|---|---|---|---|\n" % k)
        for s_, n in sorted(secs.items()):
            b = c_real(s_) * 2 / k
            f.write(f"| {s_} | {b:.1f} mm | {n} | {MINI_B / (c_real(s_) * 2 / k):.2f} |\n")
        f.write("\nLa mini es un prototipo de **forma, encaje y mecanismos** (cinemática de suspensión, puertas, "
                "dirección), no de resistencia: el tubo 8×8×1 no escala las secciones, así que sus esfuerzos no "
                "representan los del carro.\n")


def generar(k=5, stock=1000, salida=None):
    miembros = leer()
    # a escala: coordenadas / k, sección única del modelo (si k == 1 se conservan las reales)
    mini = []
    for e in miembros:
        m = dict(e)
        m["pa"], m["pb"] = e["pa"] / k, e["pb"] / k
        m["redondo"] = False
        mini.append(m)
    c_mini = (lambda e: MINI_B / 2000.0)
    cs = cortes(mini, c_mini)
    cs_real = cortes(miembros, lambda e: c_real(e["sec"]) / 1000.0)

    filas, problemas = [], []
    for i, (e, c, cr) in enumerate(zip(mini, cs, cs_real), 1):
        ext = c["extremos"]
        fila = {
            "n": i, "de": e["a"], "a": e["b"], "funcion": e["tag"], "seccion_real": e["sec"],
            "largo_centros_mm": c["L"] * 1000, "largo_corte_mm": c["corte"] * 1000,
            "corte_A": f"{ext[0][2]} (contra {ext[0][0]}, {ext[0][1]:.0f}°)",
            "corte_B": f"{ext[1][2]} (contra {ext[1][0]}, {ext[1][1]:.0f}°)",
            "largo_real_mm": cr["corte"] * 1000,
        }
        filas.append(fila)
        if c["corte"] * 1000 < 10:
            problemas.append(f"#{i} {e['a']}–{e['b']}: corte de {c['corte']*1000:.1f} mm (menor de 10 mm: "
                             f"mejor un nodo de lámina o un solo tubo)")
    piezas = [(f["n"], f["largo_corte_mm"]) for f in filas if f["largo_corte_mm"] >= 10]
    bl = barras(piezas, stock)

    # nodos únicos (plantilla de soldadura)
    nodos = {}
    for e in mini:
        nodos.setdefault(e["a"], e["pa"] * 1000)
        nodos.setdefault(e["b"], e["pb"] * 1000)

    ch = choques(miembros, k)
    if salida:
        os.makedirs(salida, exist_ok=True)
        with open(os.path.join(salida, "lista-corte.csv"), "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["#", "de_nodo", "a_nodo", "funcion", "seccion_real", "largo_entre_centros_mm",
                        "largo_de_corte_mm", "corte_A", "corte_B"])
            for r in filas:
                w.writerow([r["n"], r["de"], r["a"], r["funcion"], r["seccion_real"],
                            f"{r['largo_centros_mm']:.1f}", f"{r['largo_corte_mm']:.1f}", r["corte_A"], r["corte_B"]])
        with open(os.path.join(salida, "nodos.csv"), "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["nodo", "x_mm", "y_mm", "z_mm"])
            for n, p in sorted(nodos.items()):
                w.writerow([n, *[f"{v:.1f}" for v in p]])
        with open(os.path.join(salida, "barras.csv"), "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["barra", "piezas(#:largo_mm)", "sobrante_mm"])
            for j, b in enumerate(bl, 1):
                w.writerow([j, " ".join(f"{p}:{l:.0f}" for p, l in b["piezas"]), f"{b['resta']:.0f}"])
        plantilla({"filas": filas, "nodos": nodos}, k, salida)
    res = {"filas": filas, "barras": bl, "nodos": nodos, "problemas": problemas, "choques": ch,
            "total_mm": sum(l for _, l in piezas)}
    if salida:
        resumen(res, k, stock, salida)
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--escala", type=float, default=5.0, help="denominador (5 = 1:5)")
    ap.add_argument("--stock", type=float, default=1000.0, help="largo de la barra comprada, mm")
    a = ap.parse_args()
    sal = os.path.join(HERE, "..", "planos", f"mini-1a{a.escala:g}")
    r = generar(a.escala, a.stock, sal)
    print(f"1:{a.escala:g}  {len(r['filas'])} tubos | {len(r['nodos'])} nodos | "
          f"{r['total_mm']/1000:.1f} m de tubo {MINI_B:g}x{MINI_B:g}x{MINI_T:g} | {len(r['barras'])} barras de {a.stock:g} mm")
    for p in r["problemas"]:
        print("AVISO", p)
    for e, o, lr, lm in r["choques"]:
        print(f"CHOQUE a escala: {e['a']}–{e['b']} vs {o['a']}–{o['b']}  luz real {lr:.0f} mm, mini {lm:.1f} mm")
    print("escrito en", os.path.normpath(sal))


if __name__ == "__main__":
    sys.exit(main())
