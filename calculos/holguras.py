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
    """Distancia mínima entre dos segmentos 3D (Ericson, Real-Time Collision Detection 5.1.9) y la fracción de cada uno donde ocurre.
    CORREGIDO 2026-10-21 (auditoría): antes se recortaban s y t por separado a [0,1] y se sobreestimaba la holgura (hasta 495 mm)."""
    p1, q1, p2, q2 = map(lambda v: np.asarray(v, float), (p1, q1, p2, q2))
    d1, d2, r = q1 - p1, q2 - p2, p1 - p2
    a, e, f = d1 @ d1, d2 @ d2, d2 @ r
    if a <= 1e-14 and e <= 1e-14:
        return float(np.linalg.norm(r)), 0.0, 0.0
    if a <= 1e-14:
        s, t = 0.0, float(np.clip(f / e, 0, 1))
    else:
        c = d1 @ r
        if e <= 1e-14:
            s, t = float(np.clip(-c / a, 0, 1)), 0.0
        else:
            b = d1 @ d2
            den = a * e - b * b
            s = float(np.clip((b * f - c * e) / den, 0, 1)) if den > 1e-14 else 0.0
            t = (b * s + f) / e
            if t < 0.0:
                t, s = 0.0, float(np.clip(-c / a, 0, 1))
            elif t > 1.0:
                t, s = 1.0, float(np.clip((b - c) / a, 0, 1))
    return float(np.linalg.norm((p1 + s * d1) - (p2 + t * d2))), float(s), float(t)


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
                # el tubo que lleva la ménsula del extremo superior lo toca por diseño: SÓLO ese (nodos anAMORT*), no toda la caja
                # (auditoría 2026-10-21: la regla de 90 mm al nodo eximía el riel superior y ocultó un choque de 33 mm)
                if "AMORT" in e["a"] or "AMORT" in e["b"] or "coil" in (e["a"][:4], e["b"][:4]):
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


def brazos_vs_chasis(paso_mm=35, margen_min=0.0):
    """Brazos de la suspensión DELANTERA contra los TUBOS DEL CHASIS, a lo largo de todo el recorrido (±75 mm).
    Mide cada brazo (tubo Ø25.4) desde `paso_mm` del pivote (el buje y la ménsula tocan al larguero por diseño) hasta la rótula.
    Añadido 2026-10-21: antes sólo se comparaban piezas móviles entre sí y nadie vio que los brazos inferiores atravesaban el
    larguero (hasta 31 mm), porque el pivote caía sobre el eje del tubo. Devuelve (peor_holgura_mm, quién, lista)."""
    import contextlib, io
    with contextlib.redirect_stdout(io.StringIO()):
        import suspension_delantera as sd
        import analisis_chasis as ac
    r_brazo = 0.0127
    R_COIL_DEL = 0.036
    x0 = np.array([0.0, *sd.TR0])
    peor = {}
    for thL in np.linspace(-0.38, 0.38, 61):
        x0, W, a, shk = sd.resolver(thL, x0)
        if abs(W[1] - sd.W0[1]) > 0.075:
            continue
        lbj = sd.rot_eje(sd.LA1, sd.LA2, thL, sd.LBJ0)
        ubj = sd.rot_eje(sd.UA1, sd.UA2, x0[0], sd.UBJ0)
        for nom, (p, q) in {"brazo inf. del.": (sd.LA1, lbj), "brazo inf. tras.": (sd.LA2, lbj),
                            "brazo sup. del.": (sd.UA1, ubj), "brazo sup. tras.": (sd.UA2, ubj)}.items():
            p, q = np.asarray(p, float), np.asarray(q, float)
            A1 = p + (paso_mm / 1000 / np.linalg.norm(q - p)) * (q - p)
            for e in ac.elems:
                pa, pb = ac.NODES[e["a"]], ac.NODES[e["b"]]
                if pa[2] < -0.01 or pb[2] < -0.01:                 # lado izquierdo (el derecho es el espejo)
                    continue
                d, _, _ = dist_segmentos(A1, q, pa, pb)
                m = d - (r_brazo + e["sec"]["c"])
                k = (nom, f"{e['a']}–{e['b']}")
                if k not in peor or m < peor[k]:
                    peor[k] = m
        # coilover delantero (ojo inferior sobre el brazo inferior, sigue su giro): desde el 15% hasta el ojo superior, radio del resorte
        inf = sd.rot_eje(sd.LA1, sd.LA2, thL, sd.SHK_INF0)
        sup = np.asarray(sd.SHK_SUP, float)
        A1 = inf + 0.15 * (sup - inf)
        for e in ac.elems:
            pa, pb = ac.NODES[e["a"]], ac.NODES[e["b"]]
            if pa[2] < -0.01 or pb[2] < -0.01 or "AMORT" in e["a"] or "AMORT" in e["b"]:
                continue
            d, _, _ = dist_segmentos(A1, sup, pa, pb)
            m = d - (R_COIL_DEL + e["sec"]["c"])
            k = ("coilover del.", f"{e['a']}–{e['b']}")
            if k not in peor or m < peor[k]:
                peor[k] = m
    # brazo tirado trasero (PTR 70x50, semialtura 35 mm): del pivote a la punta, a lo largo del recorrido. Se excluyen los primeros 60 mm
    # (la raíz va entre las orejas de la ménsula, soldada al riel por diseño). Añadido tras la auditoría independiente 2026-10-21.
    with contextlib.redirect_stdout(io.StringIO()):
        import suspension_trasera as st
    piv = np.asarray(st.PIV, float)
    for r in st.rows:
        punta = np.array([r["x"], r["y"], st.Z_PUNTA])
        A1 = piv + (0.060 / np.linalg.norm(punta - piv)) * (punta - piv)
        for e in ac.elems:
            pa, pb = ac.NODES[e["a"]], ac.NODES[e["b"]]
            if pa[2] < -0.01 or pb[2] < -0.01:
                continue
            d, _, _ = dist_segmentos(A1, punta, pa, pb)
            m = d - (0.035 + e["sec"]["c"])
            k = ("brazo trasero", f"{e['a']}–{e['b']}")
            if k not in peor or m < peor[k]:
                peor[k] = m
    lista = sorted(((m * 1000, k[0], k[1]) for k, m in peor.items()))
    return lista[0][0], f"{lista[0][1]} / {lista[0][2]}", lista


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
    pm, quien, lista = brazos_vs_chasis()
    for m, brazo, tubo in lista[:3]:
        est = "ok" if m >= 0 else f"ATRAVIESA {abs(m):.0f} mm"
        print(f"{brazo:16s} {tubo:30s} {m:9.1f} {0.0:10.1f}   {est}")
    if pm < 0:
        mal += 1
    print("-" * 78)
    print("TODO LIBRE" if mal == 0 else f"{mal} INTERFERENCIAS")
    sys.exit(1 if mal else 0)
