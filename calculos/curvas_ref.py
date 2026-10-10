# -*- coding: utf-8 -*-
"""
Curvas maestras de la carrocería, MEDIDAS de las cuatro vistas ortográficas.

Por qué existe: la jaula de control del modelo 3D (carro3d_jaula.py) no se teclea a
ojo; se mide. Esto lee las vistas ortográficas de la referencia (ref/gemini/ia-*.png,
fondo transparente) y saca, columna por columna, lo que cada vista SÍ define:

  lateral   techo(x), piso(x)                      → alturas de la piel
  cenital   semiancho(x), cristal(x), luneta(x)    → planta y huella del invernadero
  frontal   contorno superior y(z)                 → sección envolvente delantera
  trasera   contorno superior y(z), barra de luz   → sección envolvente trasera

Las vistas NO son consistentes entre sí (cada una fue generada por separado): las
ruedas caen en distinto sitio en la lateral y en la cenital, y la frontal está
estirada en alto. Por eso cada vista se lleva al paquete REAL por sus propias marcas:
en x, tramo a tramo entre nariz, eje delantero, eje trasero y cola (la batalla de
2.130 no se toca); en alto, normalizando al alto del paquete; en ancho, al semiancho.
Lo que sale es la FORMA de la referencia sobre NUESTRAS cotas.

Correr:  python calculos/curvas_ref.py
Salidas: ref/curvas-referencia.json      curvas en metros, en el marco del chasis
         ref/curvas-verificacion.png     qué se midió, dibujado sobre cada vista
"""
import json
import os

import numpy as np
from PIL import Image
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.join(HERE, "..")
REF = os.path.join(RAIZ, "ref", "gemini")

# ---- paquete real (mismos puntos duros que carroceria.py) --------------------------
EJE_DEL, EJE_TRAS = 0.550, 2.680
BATALLA = EJE_TRAS - EJE_DEL
X_MORRO, X_COLA = -0.134, 3.246           # voladizos medidos de la lámina del dueño
SEMI = 0.890                               # semiancho: 1.78 m, manda la trocha
ALTO = 1.060                               # arco 1.010 + tubo + 20 mm de piel

# ---- marcas en píxeles de cada vista (medidas sobre la rejilla, ver scratch) -------
# lateral: nariz, centro rueda del, centro rueda tras, cola ; suelo ; techo
LAT = dict(nariz=47, r_del=232, r_tras=766, cola=976, suelo=637, techo=385)
# cenital: nariz, centro rueda del, centro rueda tras, cola ; fila del eje
CEN = dict(nariz=47, r_del=232, r_tras=742, cola=976, eje=511.5)
# frontal / trasera: columna central, semiancho en px, suelo (fondo de llanta), techo
FRO = dict(centro=511.0, semi=465.0, suelo=798, techo=181)
TRA = dict(centro=511.5, semi=465.0, suelo=789, techo=191)

ALFA = 250      # por debajo hay sombra suave y antialias, no carro


def cargar(nombre):
    a = np.asarray(Image.open(os.path.join(REF, nombre)).convert("RGBA")).astype(np.int32)
    return a[..., :3], a[..., 3] >= ALFA


def x_paquete(px, marcas):
    """px de la vista -> x en metros, lineal por tramos anclado en las 4 marcas."""
    xp = [marcas["nariz"], marcas["r_del"], marcas["r_tras"], marcas["cola"]]
    xm = [X_MORRO, EJE_DEL, EJE_TRAS, X_COLA]
    return float(np.interp(px, xp, xm))


def suavizar(v, k=7):
    """Mediana móvil: mata el antialias del borde sin comerse las esquinas."""
    v = np.asarray(v, float)
    pad = np.pad(v, k // 2, mode="edge")
    return np.array([np.median(pad[i:i + k]) for i in range(len(v))])


def lateral():
    rgb, m = cargar("ia-lateral.png")
    esc_y = ALTO / (LAT["suelo"] - LAT["techo"])
    xs, techo, piso = [], [], []
    for c in range(LAT["nariz"], LAT["cola"] + 1):
        col = np.where(m[:, c])[0]
        if len(col) == 0:
            continue
        xs.append(x_paquete(c, LAT))
        techo.append((LAT["suelo"] - col.min()) * esc_y)
        piso.append((LAT["suelo"] - col.max()) * esc_y)
    techo, piso = suavizar(techo), suavizar(piso)
    # el piso medido incluye las llantas: donde hay rueda, el piso es el suelo. Lo que
    # queremos es el borde inferior de la PIEL, así que se toma fuera de los pasos.
    return {"x": xs, "techo": techo.tolist(), "piso": piso.tolist()}


def cenital():
    rgb, m = cargar("ia-cenital.png")
    L = rgb.mean(axis=2)
    esc_z = SEMI / max((np.where(m.any(axis=1))[0].max() - CEN["eje"]),
                       (CEN["eje"] - np.where(m.any(axis=1))[0].min()))
    # cristal: lo único oscuro grande sobre el techo. Dos manchas: canopy y luneta.
    oscuro = m & (L < 70)
    lab, n = ndimage.label(oscuro)
    tam = ndimage.sum(oscuro, lab, range(1, n + 1))
    orden = np.argsort(tam)[::-1]
    manchas = []
    for i in orden[:4]:
        yy, xx = np.where(lab == i + 1)
        # se descartan las que tocan el borde inferior (sombra de las llantas)
        if yy.max() > CEN["eje"] + 0.9 * (CEN["eje"] - np.where(m.any(axis=1))[0].min()):
            continue
        manchas.append((xx.min(), xx.max(), lab == i + 1, int(tam[i])))
    # las dos más grandes son canopy y luneta (la tercera es la arista del techo);
    # después se ordenan por x para saber cuál es cuál
    manchas = sorted(manchas, key=lambda t: -t[3])[:2]
    manchas.sort(key=lambda t: t[0])
    canopy, luneta = manchas[0][2], manchas[1][2]

    xs, semi, cris, lun = [], [], [], []
    for c in range(CEN["nariz"], CEN["cola"] + 1):
        col = np.where(m[:, c])[0]
        if len(col) == 0:
            continue
        xs.append(x_paquete(c, CEN))
        semi.append(0.5 * (col.max() - col.min()) * esc_z)
        for mask, out in ((canopy, cris), (luneta, lun)):
            cc = np.where(mask[:, c])[0]
            out.append(0.5 * (cc.max() - cc.min()) * esc_z if len(cc) > 6 else 0.0)
    return {"x": xs, "semiancho": suavizar(semi).tolist(),
            "cristal": suavizar(cris, 5).tolist(), "luneta": suavizar(lun, 5).tolist()}


def frente(nombre, marcas, luz=None):
    rgb, m = cargar(nombre)
    esc_z = SEMI / marcas["semi"]
    esc_y = ALTO / (marcas["suelo"] - marcas["techo"])
    zs, techo = [], []
    for c in range(int(marcas["centro"]), int(marcas["centro"] + marcas["semi"]) + 1):
        col = np.where(m[:, c])[0]
        if len(col) == 0:
            continue
        zs.append((c - marcas["centro"]) * esc_z)
        techo.append((marcas["suelo"] - col.min()) * esc_y)
    out = {"z": zs, "techo": suavizar(techo).tolist()}
    if luz:
        r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
        rojo = m & (r - b > 55) & (r > 90)
        ys, xs = np.where(rojo)
        # la barra: la fila más poblada de rojo
        filas = np.bincount(ys, minlength=rgb.shape[0])
        fila = int(np.argmax(filas))
        out["barra_y"] = (marcas["suelo"] - fila) * esc_y
        out["barra_z"] = float((xs.max() - marcas["centro"]) * esc_z)
    return out


def figura(cur):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(2, 2, figsize=(16, 9), facecolor="#0d1117")
    for a in ax.flat:
        a.set_facecolor("#0d1117")
        a.tick_params(colors="#7d8590", labelsize=8)
        for s in a.spines.values():
            s.set_color("#30363d")
        a.set_aspect("equal")
    lat, cen, fro, tra = cur["lateral"], cur["cenital"], cur["frontal"], cur["trasera"]
    a = ax[0, 0]
    a.plot(lat["x"], lat["techo"], color="#f0a868", lw=1.4, label="techo")
    a.plot(lat["x"], lat["piso"], color="#7aa5cc", lw=1.4, label="piso (con llantas)")
    for xe in (EJE_DEL, EJE_TRAS):
        a.axvline(xe, color="#30363d", ls="--", lw=0.8)
    a.axhline(0, color="#30363d", lw=0.8)
    a.set_title("LATERAL en el paquete real", color="#c9d1d9", loc="left")
    a.legend(fontsize=8, facecolor="#161b22", labelcolor="#c9d1d9")
    a = ax[0, 1]
    a.plot(cen["x"], cen["semiancho"], color="#f0a868", lw=1.4, label="semiancho")
    a.plot(cen["x"], cen["cristal"], color="#5b8ddb", lw=1.4, label="canopy")
    a.plot(cen["x"], cen["luneta"], color="#9b6bd6", lw=1.4, label="luneta")
    for xe in (EJE_DEL, EJE_TRAS):
        a.axvline(xe, color="#30363d", ls="--", lw=0.8)
    a.set_title("CENITAL (medio carro)", color="#c9d1d9", loc="left")
    a.legend(fontsize=8, facecolor="#161b22", labelcolor="#c9d1d9")
    for a, v, t in ((ax[1, 0], fro, "FRONTAL"), (ax[1, 1], tra, "TRASERA")):
        a.plot(v["z"], v["techo"], color="#f0a868", lw=1.4)
        if "barra_y" in v:
            a.plot([0, v["barra_z"]], [v["barra_y"]] * 2, color="#f85149", lw=2)
        a.axhline(0, color="#30363d", lw=0.8)
        a.set_title(t + " contorno superior (medio carro)", color="#c9d1d9", loc="left")
    fig.tight_layout()
    out = os.path.join(RAIZ, "ref", "curvas-verificacion.png")
    fig.savefig(out, dpi=110, facecolor="#0d1117")
    return out


def main():
    cur = {"paquete": {"x_morro": X_MORRO, "x_cola": X_COLA, "eje_del": EJE_DEL,
                       "eje_tras": EJE_TRAS, "semi": SEMI, "alto": ALTO},
           "lateral": lateral(), "cenital": cenital(),
           "frontal": frente("ia-frontal.png", FRO),
           "trasera": frente("ia-trasera.png", TRA, luz=True)}
    out = os.path.join(RAIZ, "ref", "curvas-referencia.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump({k: ({kk: ([round(float(q), 4) for q in vv] if isinstance(vv, list)
                             else round(float(vv), 4)) for kk, vv in v.items()})
                   for k, v in cur.items()}, f, separators=(",", ":"))
    lat, cen = cur["lateral"], cur["cenital"]
    print(f"OK  {out}")
    print(f"    lateral  techo max {max(lat['techo']):.3f} m en x="
          f"{lat['x'][int(np.argmax(lat['techo']))]:.2f}   morro y="
          f"{lat['techo'][0]:.3f}   cola y={lat['techo'][-1]:.3f}")
    print(f"    cenital  semiancho max {max(cen['semiancho']):.3f} en x="
          f"{cen['x'][int(np.argmax(cen['semiancho']))]:.2f}   canopy max "
          f"{max(cen['cristal']):.3f}   luneta max {max(cen['luneta']):.3f}")
    xc = [x for x, c in zip(cen["x"], cen["cristal"]) if c > 0]
    xl = [x for x, c in zip(cen["x"], cen["luneta"]) if c > 0]
    print(f"    canopy x {min(xc):.2f}..{max(xc):.2f}   luneta x {min(xl):.2f}..{max(xl):.2f}")
    print(f"    trasera  barra de luz y={cur['trasera']['barra_y']:.3f}  hasta z="
          f"{cur['trasera']['barra_z']:.3f}")
    print(f"OK  {figura(cur)}")


if __name__ == "__main__":
    main()
