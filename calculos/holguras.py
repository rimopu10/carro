# -*- coding: utf-8 -*-
"""
HOLGURAS — detector de interferencias entre piezas móviles.

Por qué existe: la suspensión se afinó con barridos numéricos de camber, caster,
bump steer y Ackermann, pero **nadie comprobó que las piezas no se atravesaran entre
sí**. Al revisar el ensamble aparecieron tres choques reales que un armado físico
habría descubierto con el acero ya cortado.

Este módulo comprueba, a lo largo de TODO el recorrido de suspensión (no solo en
reposo), la distancia entre los ejes de cada par de piezas que pueden tocarse, y la
compara contra la suma de sus radios más un margen. Cualquier script que mueva un
punto duro debería correrlo antes de dar la geometría por buena.

Uso:  python holguras.py          → informe de todas las parejas
      from holguras import revisar → dict con el resultado, para usarlo en un barrido
"""
import numpy as np
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

MARGEN = 0.008          # m, holgura mínima que se exige además de los radios


def dist_segmentos(p1, q1, p2, q2):
    """Distancia mínima entre dos segmentos 3D, y en qué fracción de cada uno ocurre."""
    p1, q1, p2, q2 = map(np.asarray, (p1, q1, p2, q2))
    u, v, w = q1 - p1, q2 - p2, p1 - p2
    a, b, c = u @ u, u @ v, v @ v
    d, e = u @ w, v @ w
    D = a * c - b * b
    if D < 1e-14:                       # paralelos
        s = 0.0
        t = (d / b) if abs(b) > 1e-14 else 0.0
    else:
        s, t = (b * e - c * d) / D, (a * e - b * d) / D
    s, t = float(np.clip(s, 0, 1)), float(np.clip(t, 0, 1))
    return float(np.linalg.norm((p1 + s * u) - (p2 + t * v))), s, t


def dist_segmento_disco(p, q, centro, normal, radio):
    """Distancia de un segmento al disco (llanta/rin) de radio dado.
    Aproximación conservadora: se muestrea el segmento y se mide contra el cilindro."""
    centro, normal = np.asarray(centro), np.asarray(normal) / np.linalg.norm(normal)
    peor = np.inf
    for t in np.linspace(0, 1, 25):
        x = np.asarray(p) + t * (np.asarray(q) - np.asarray(p))
        d = x - centro
        axial = d @ normal
        radial = np.linalg.norm(d - axial * normal)
        # dentro del cilindro de la llanta si |axial| < semiancho y radial < radio
        peor = min(peor, max(radio - radial, 0.0) if abs(axial) < 1e9 else np.inf)
    return peor


def revisar(P, verbose=False):
    """P: dict de puntos duros. Devuelve lista de (nombre, holgura_mm, requerida_mm, ok)."""
    # (nombre A, extremos A, radio A, nombre B, extremos B, radio B)
    R_TUBO_A = 0.0127        # tubo redondo 25.4 de las horquillas
    R_TIE = 0.009
    R_COIL = P.get("R_COIL", 0.036)
    R_BRAZO_T = 0.035        # semialtura del PTR 70x50 trasero

    # `desde`: fracción de la pieza A a partir de la cual se mide. Sirve cuando A se
    # ANCLA sobre B (el ojo del coilover va montado en el brazo): ahí la distancia es
    # cero por diseño y lo que importa es que el resto del cuerpo no roce.
    pares = [
        ("coilover del.", (P["SHK_INF_D"], P["SHK_SUP_D"]), R_COIL,
         "horquilla sup. pata trasera", (P["UA2"], P["UBJ"]), R_TUBO_A, 0.0),
        ("coilover del.", (P["SHK_INF_D"], P["SHK_SUP_D"]), R_COIL,
         "horquilla sup. pata delantera", (P["UA1"], P["UBJ"]), R_TUBO_A, 0.0),
        ("coilover del.", (P["SHK_INF_D"], P["SHK_SUP_D"]), R_COIL,
         "horquilla inf. pata trasera", (P["LA2"], P["LBJ"]), R_TUBO_A, 0.18),
        ("tie rod", (P["RACK"], P["TR"]), R_TIE,
         "horquilla inf. pata delantera", (P["LA1"], P["LBJ"]), R_TUBO_A, 0.0),
        ("tie rod", (P["RACK"], P["TR"]), R_TIE,
         "horquilla inf. pata trasera", (P["LA2"], P["LBJ"]), R_TUBO_A, 0.0),
        ("tie rod", (P["RACK"], P["TR"]), R_TIE,
         "horquilla sup. pata delantera", (P["UA1"], P["UBJ"]), R_TUBO_A, 0.0),
        ("coilover tras.", (P["SHK_INF_T"], P["SHK_SUP_T"]), P.get("R_COIL_T", 0.040),
         "brazo tirado", (P["PIV"], P["PUNTA"]), R_BRAZO_T, 0.18),
    ]
    out = []
    for na, (a1, a2), ra, nb, (b1, b2), rb, desde in pares:
        A1 = np.asarray(a1) + desde * (np.asarray(a2) - np.asarray(a1))
        d, sa, sb = dist_segmentos(A1, a2, b1, b2)
        req = ra + rb + MARGEN
        out.append(dict(a=na, b=nb, d=d * 1000, req=req * 1000,
                        ok=d >= req, anclaje=desde > 0, sa=desde + sa * (1 - desde), sb=sb))

    # piezas móviles contra los TUBOS DEL CHASIS de la zona delantera y trasera.
    # Un coilover que libra los brazos pero roza un larguero sirve igual de poco.
    try:
        import analisis_chasis as ac
        moviles = [("coilover del.", P["SHK_INF_D"], P["SHK_SUP_D"], R_COIL, 0.15),
                   ("tie rod", P["RACK"], P["TR"], R_TIE, 0.05),
                   ("coilover tras.", P["SHK_INF_T"], P["SHK_SUP_T"],
                    P.get("R_COIL_T", 0.040), 0.15)]
        for nom, a1, a2, ra, desde in moviles:
            peor, cual = np.inf, ""
            A1 = np.asarray(a1) + desde * (np.asarray(a2) - np.asarray(a1))
            for e in ac.elems:
                pa, pb = ac.NODES[e["a"]], ac.NODES[e["b"]]
                if min(np.linalg.norm(pa - A1), np.linalg.norm(pb - A1),
                       np.linalg.norm(pa - a2), np.linalg.norm(pb - a2)) > 0.9:
                    continue                      # tubo lejano, no puede estorbar
                rt = e["sec"]["c"]                # semiancho/radio de la sección
                d, _, _ = dist_segmentos(A1, a2, pa, pb)
                # los extremos anclados al chasis tocan su nodo por diseño
                if min(np.linalg.norm(np.asarray(a2) - pa),
                       np.linalg.norm(np.asarray(a2) - pb)) < 0.09:
                    continue
                margen = d - (ra + rt + MARGEN)
                if margen < peor:
                    peor, cual = margen, f"{e['a']}–{e['b']}"
            if np.isfinite(peor):
                out.append(dict(a=nom, b=f"tubo {cual}", d=(peor + ra + 0.019 + MARGEN) * 1000,
                                req=(ra + 0.019 + MARGEN) * 1000, ok=peor >= 0,
                                anclaje=False, sa=0, sb=0))
    except Exception as ex:
        print(f"  (aviso: no se pudo revisar contra el chasis: {ex})")

    # piezas contra la llanta (cilindro): nada estructural debe entrar en su ancho
    for nom, (p, q) in [("tie rod", (P["RACK"], P["TR"])),
                        ("coilover del.", (P["SHK_INF_D"], P["SHK_SUP_D"])),
                        ("coilover tras.", (P["SHK_INF_T"], P["SHK_SUP_T"]))]:
        trasera = "tras" in nom
        C = P["W_TRAS"] if trasera else P["W_DEL"]
        Rr = P["R_RIN_T"] if trasera else P["R_RIN_D"]
        semi = P["ANCHO_LL"] / 2
        peor, donde = np.inf, 0.0
        for t in np.linspace(0, 1, 41):
            x = np.asarray(p) + t * (np.asarray(q) - np.asarray(p))
            dz = abs(x[2]) - (abs(C[2]) - semi)      # cuánto entra en el ancho de la rueda
            rad = np.hypot(x[0] - C[0], x[1] - C[1])
            if dz > 0 and rad > Rr:                  # dentro del ancho Y fuera del rin
                if -dz < peor:
                    peor, donde = -dz, t
        out.append(dict(a=nom, b="llanta" + (" trasera" if trasera else " delantera"),
                        d=(peor * 1000 if np.isfinite(peor) else 999.0), req=0.0,
                        ok=not np.isfinite(peor), anclaje=False, sa=donde, sb=0))
    return out


def puntos_actuales():
    """Toma los puntos duros de los módulos de suspensión, que son la fuente."""
    import suspension_delantera as sd
    PIV = np.array([2.28, 0.16, 0.552])
    EJE = np.array([2.68, 0.3005, 0.76])
    Z_PUNTA = 0.640                       # el brazo termina antes del motor
    PUNTA = np.array([EJE[0], EJE[1], Z_PUNTA])
    T_SHK = float(os.environ.get("SUSP_T_SHK", "0.80"))
    return dict(
        LA1=sd.LA1, LA2=sd.LA2, UA1=sd.UA1, UA2=sd.UA2,
        LBJ=sd.LBJ0, UBJ=sd.UBJ0, RACK=sd.RACK, TR=sd.TR0,
        SHK_INF_D=sd.SHK_INF0, SHK_SUP_D=sd.SHK_SUP,
        PIV=PIV, PUNTA=PUNTA,
        SHK_INF_T=PIV + T_SHK * (PUNTA - PIV),      # sobre el EJE del brazo
        SHK_SUP_T=np.array([2.58, 0.712, 0.425]),
        W_DEL=sd.W0, W_TRAS=EJE, ANCHO_LL=sd.ANCHO_LLANTA,
        R_RIN_D=13 * 0.0127, R_RIN_T=14 * 0.0127,
    )


if __name__ == "__main__":
    P = puntos_actuales()
    res = revisar(P)
    print("HOLGURAS ENTRE PIEZAS (mm)\n")
    print(f"{'pieza A':16s} {'pieza B':30s} {'holgura':>9s} {'requerida':>10s}   estado")
    print("-" * 78)
    mal = 0
    for r in res:
        if r["b"].startswith("llanta"):
            est = "ok" if r["ok"] else f"ENTRA {abs(r['d']):.0f} mm EN LA LLANTA"
            print(f"{r['a']:16s} {r['b']:30s} {'—':>9s} {'—':>10s}   {est}")
        else:
            est = "ok" if r["ok"] else f"CHOCA (al {r['sa']*100:.0f}% de la pieza)"
            nota = " *" if r["anclaje"] else ""
            print(f"{r['a']:16s} {r['b']+nota:30s} {r['d']:9.1f} {r['req']:10.1f}   {est}")
        if not r["ok"]:
            mal += 1
    print("-" * 78)
    print("TODO LIBRE" if mal == 0 else f"{mal} INTERFERENCIAS")
    sys.exit(1 if mal else 0)
