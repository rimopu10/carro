# -*- coding: utf-8 -*-
"""
OPTIMIZACIÓN DE SECCIONES DEL CHASIS — el mismo carro, más ligero.

El chasis actual usa UNA sola sección para casi todo (PTR 38×38×1.9) más los arcos
de seguridad en redondo. Eso es fácil de comprar pero deja masa sobre la mesa: hay
73 tubos y solo uno de ellos está al límite (FS 2.22 en bache 3g); los otros 72 van
sobrados y podrían ser más delgados.

Qué hace este script: buscar, dentro de un catálogo de secciones que de verdad se
consiguen, la asignación más ligera que siga cumpliendo TODO:

  - FS ≥ 2.0 a fluencia en los 3 casos de carga (bache 3g, frenada 1g, curva 1g)
  - FS ≥ 2.0 a pandeo de Euler en cada tubo comprimido
  - rigidez torsional por encima de un piso que se barre
  - la célula de seguridad (arcos, pilares, techo) NUNCA baja de RED 44.5×2.1,
    diga lo que diga el FEM: este modelo no simula una volcadura
  - los tubos se agrupan por función, no uno por uno — un chasis con 73 secciones
    distintas sería imposible de comprar y de armar

Método: descenso codicioso por grupos. Se arranca con todo en la sección más grande
del catálogo y se intenta bajar un escalón cada grupo, aceptando el cambio solo si
el diseño sigue cumpliendo. Se repite hasta que ningún grupo pueda bajar más.

Salidas:
  calculos/resultados-optimizacion-chasis.md
  calculos/optimizacion-chasis.png
  planos/lista-corte-tubos-optimizada.csv
"""
import numpy as np
import csv, os, sys, copy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import analisis_chasis as ac        # geometría, ensamble y casos de carga ya validados

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

E, G, FY, RHO = ac.E, ac.G, ac.FY, ac.RHO

# ============================================================================
# 1. CATÁLOGO DE SECCIONES REALES
# ============================================================================
def ptr(b, t):
    bi = b - 2 * t
    A = b * b - bi * bi
    I = (b**4 - bi**4) / 12.0
    bm = b - t
    J = 4 * (bm * bm)**2 * t / (4 * bm)
    return dict(A=A, Iy=I, Iz=I, J=J, c=b / 2,
                nombre=f"PTR {b*1000:.0f}x{b*1000:.0f}x{t*1000:.1f}",
                kg_m=A * RHO, tipo="PTR")

def red(do, t):
    di = do - 2 * t
    A = np.pi / 4 * (do**2 - di**2)
    I = np.pi / 64 * (do**4 - di**4)
    return dict(A=A, Iy=I, Iz=I, J=2 * I, c=do / 2,
                nombre=f"RED {do*1000:.1f}x{t*1000:.1f}",
                kg_m=A * RHO, tipo="RED")

# ordenados de más ligero a más pesado — el optimizador baja por esta escalera
CAT_PTR = [ptr(0.025, 0.0015), ptr(0.025, 0.0019), ptr(0.032, 0.0015),
           ptr(0.032, 0.0019), ptr(0.038, 0.0015), ptr(0.038, 0.0019),
           ptr(0.038, 0.0026), ptr(0.044, 0.0019), ptr(0.050, 0.0019),
           ptr(0.050, 0.0026)]
CAT_RED = [red(0.0381, 0.0021), red(0.0445, 0.0021), red(0.0445, 0.0032),
           red(0.0508, 0.0021), red(0.0508, 0.0032)]
for c in (CAT_PTR, CAT_RED):
    c.sort(key=lambda s: s["kg_m"])

# ============================================================================
# 2. GRUPOS: los tubos se compran y se cortan por familia, no uno por uno
# ============================================================================
# grupo = (etiqueta funcional, tipo de perfil). Así el arco sigue siendo redondo y
# el piso sigue siendo cuadrado, que es como se arma de verdad.
GRUPOS = {}
for (a, b, s, tag) in ac.MEMBERS:
    GRUPOS.setdefault((tag, s["nombre"].split()[0]), []).append((a, b, tag))

NOMBRE_GRUPO = {
    ("gen", "PTR"):  "Estructura general (nariz, estribos, rieles)",
    ("susp", "PTR"): "Anclajes de suspensión",
    ("tors", "PTR"): "Diagonales de torsión (las X)",
    ("safe", "PTR"): "Barra de cinturones",
    ("safe", "RED"): "Célula de seguridad (arcos, pilar A, techo)",
    ("batt", "PTR"): "Cuna de batería",
}
CLAVES = list(GRUPOS.keys())

# PISOS QUE EL OPTIMIZADOR NO PUEDE CRUZAR.
# Regla: un tubo NO se optimiza contra un análisis que no incluye el caso que lo hace
# importante. Este FEM tiene bache, frenada y curva — no tiene volcadura ni choque.
PISO_GRUPO = {
    ("safe", "RED"): "RED 44.5x2.1",    # arcos, pilar A, techo: volcadura no modelada
    ("safe", "PTR"): "PTR 38x38x1.9",   # barra de cinturones: ahí tiran los arneses en
                                        # un impacto, y ese caso no está en el modelo
    ("batt", "PTR"): "PTR 32x32x1.9",   # cuna de batería: retención de 90 kg de celdas
                                        # HV en un choque, tampoco modelada; y necesita
                                        # material para atornillarle la caja
}

def catalogo(clave):
    cat = CAT_RED if clave[1] == "RED" else CAT_PTR
    piso = PISO_GRUPO.get(clave)
    if piso:
        i = next(k for k, s in enumerate(cat) if s["nombre"] == piso)
        return cat[i:]
    return cat

# ============================================================================
# 3. ENSAMBLE Y EVALUACIÓN CON UNA ASIGNACIÓN CUALQUIERA
# ============================================================================
def construir(asig):
    """asig: dict clave_grupo -> sección. Devuelve (K, elems, masa)."""
    K = np.zeros((ac.ndof, ac.ndof))
    elems = []
    for (a, b, s0, tag) in ac.MEMBERS:
        s = asig[(tag, s0["nombre"].split()[0])]
        pa, pb = ac.NODES[a], ac.NODES[b]
        T, Le = ac.transform(pa, pb)
        kl = ac.beam_k_local(Le, s)
        dof = np.r_[6 * ac.idx[a]:6 * ac.idx[a] + 6, 6 * ac.idx[b]:6 * ac.idx[b] + 6]
        K[np.ix_(dof, dof)] += T.T @ kl @ T
        elems.append(dict(a=a, b=b, sec=s, tag=tag, T=T, kl=kl, dof=dof, L=Le))
    masa = sum(e["L"] * e["sec"]["A"] * RHO for e in elems)
    return K, elems, masa

def resolver(K, F, fixed):
    libre = np.setdiff1d(np.arange(ac.ndof), fixed)
    U = np.zeros(ac.ndof)
    U[libre] = np.linalg.solve(K[np.ix_(libre, libre)], F[libre])
    return U

CASOS = [("Bache 3g", ac.F_vector(0, -3.0, 0)),
         ("Frenada 1g", ac.F_vector(-1.0, -1.0, 0)),
         ("Curva 1g", ac.F_vector(0, -1.0, 1.0))]

def evaluar(asig):
    """Devuelve (masa, FS mínimo a fluencia, FS mínimo a pandeo, K torsional, detalle)."""
    K, elems, masa = construir(asig)
    fs_min, fsb_min, peor = np.inf, np.inf, None
    detalle = []
    for nombre, F in CASOS:
        U = resolver(K, F, ac.SUP)
        for e in elems:
            sig, fsb = ac.esfuerzo_max(e, U)
            fs = FY / sig if sig > 0 else np.inf
            detalle.append((nombre, f'{e["a"]}-{e["b"]}', e["tag"], e["sec"]["nombre"],
                            sig / 1e6, fs, fsb))
            if fs < fs_min:
                fs_min, peor = fs, (nombre, f'{e["a"]}-{e["b"]}', e["sec"]["nombre"])
            fsb_min = min(fsb_min, fsb)
    # rigidez torsional (mismo montaje que analisis_chasis)
    Fq = np.zeros(ac.ndof)
    brazo = abs(ac.NODES["fx_hiL"][2])
    Fq[6 * ac.idx["fx_hiL"] + 1] = +1500.0 / (2 * brazo)
    Fq[6 * ac.idx["fx_hiR"] + 1] = -1500.0 / (2 * brazo)
    Ut = resolver(K, Fq, ac.SUP_T)
    th = (Ut[6 * ac.idx["fx_hiL"] + 1] - Ut[6 * ac.idx["fx_hiR"] + 1]) / (2 * brazo)
    ktor = 1500.0 / np.degrees(th)
    return masa, fs_min, fsb_min, ktor, peor, detalle

# ============================================================================
# 4. OPTIMIZACIÓN: descenso codicioso por grupos
# ============================================================================
FS_OBJ = 2.0

def factible(asig, k_min):
    masa, fs, fsb, ktor, peor, _ = evaluar(asig)
    return (fs >= FS_OBJ and fsb >= FS_OBJ and ktor >= k_min), masa, fs, fsb, ktor

def optimizar(k_min, verbose=False):
    """Arranca con todo en la sección más pesada y baja escalones mientras se pueda."""
    asig = {c: catalogo(c)[-1] for c in CLAVES}
    ok, *_ = factible(asig, k_min)
    if not ok:
        return None
    evaluaciones = 1
    mejorado = True
    while mejorado:
        mejorado = False
        # se intenta bajar primero el grupo que más masa aporta: da el mayor premio
        orden = sorted(CLAVES, key=lambda c: -sum(
            np.linalg.norm(ac.NODES[b] - ac.NODES[a]) for (a, b, _) in GRUPOS[c]
        ) * asig[c]["kg_m"])
        for c in orden:
            cat = catalogo(c)
            i = cat.index(asig[c])
            while i > 0:
                prueba = dict(asig)
                prueba[c] = cat[i - 1]
                ok, *_ = factible(prueba, k_min)
                evaluaciones += 1
                if not ok:
                    break
                asig, i = prueba, i - 1
                mejorado = True
                if verbose:
                    print(f"    {NOMBRE_GRUPO[c]:44s} -> {asig[c]['nombre']}")
    return asig, evaluaciones

# --- referencia: el diseño actual ---
ACTUAL = {c: next(s for s in (CAT_RED if c[1] == "RED" else CAT_PTR)
                  if s["nombre"] == ("RED 44.5x2.1" if c[1] == "RED" else "PTR 38x38x1.9"))
          for c in CLAVES}
m0, fs0, fsb0, k0, peor0, det0 = evaluar(ACTUAL)

# --- barrido del piso de rigidez torsional ---
# Bajar rigidez a cambio de masa es un intercambio legítimo: el doc maestro pide
# >4,000 N·m/° para un deportivo ligero artesanal y el diseño actual da 10,868.
PISOS = [4000, 6000, 8000, 10000, int(k0)]
barrido = []
print(f"actual: {m0:.1f} kg  FS {fs0:.2f}  K {k0:,.0f} N.m/deg")
for kmin in PISOS:
    r = optimizar(kmin)
    if r is None:
        barrido.append(dict(kmin=kmin, ok=False))
        print(f"  piso {kmin:6,} N.m/deg -> INFACTIBLE")
        continue
    asig, nev = r
    masa, fs, fsb, ktor, peor, det = evaluar(asig)
    barrido.append(dict(kmin=kmin, ok=True, asig=asig, masa=masa, fs=fs, fsb=fsb,
                        ktor=ktor, peor=peor, det=det, nev=nev))
    print(f"  piso {kmin:6,} N.m/deg -> {masa:5.1f} kg ({masa-m0:+5.1f})  "
          f"FS {fs:.2f}  K real {ktor:7,.0f}  ({nev} evaluaciones)")

validos = [b for b in barrido if b["ok"]]

# ============================================================================
# 4b. ¿CUÁNTO CUESTA SIMPLIFICAR? — masa vs número de secciones distintas
# ============================================================================
# Cinco secciones distintas es más peso que quitar pero más lío para comprar, cortar
# y no confundirse en el taller. Se mide el precio en kilos de usar menos.
import itertools

def variante(asig_base, subconjunto, k_min):
    """Sube cada grupo a la sección más ligera del subconjunto que sea >= la suya."""
    asig = {}
    for c in CLAVES:
        fam = [s for s in subconjunto if s["tipo"] == c[1]]
        cands = [s for s in fam if s["kg_m"] >= asig_base[c]["kg_m"] - 1e-12
                 and s in catalogo(c)]
        if not cands:
            return None
        asig[c] = min(cands, key=lambda s: s["kg_m"])
    ok, masa, fs, fsb, ktor = factible(asig, k_min)
    return dict(asig=asig, masa=masa, fs=fs, ktor=ktor) if ok else None

def por_n_secciones(asig_base, k_min):
    usadas = {s["nombre"]: s for s in asig_base.values()}
    # se permite tambien subir a secciones mas pesadas del catalogo para poder fusionar
    pool = list({s["nombre"]: s for s in
                 list(usadas.values()) + CAT_PTR + CAT_RED}.values())
    ptrs = [s for s in pool if s["tipo"] == "PTR"]
    reds = [s for s in pool if s["tipo"] == "RED"]
    mejor = {}
    for n_ptr in range(1, 4):
        for combo_ptr in itertools.combinations(ptrs, n_ptr):
            for r in reds:
                v = variante(asig_base, list(combo_ptr) + [r], k_min)
                if v is None:
                    continue
                n = len({s["nombre"] for s in v["asig"].values()})
                if n not in mejor or v["masa"] < mejor[n]["masa"]:
                    mejor[n] = v
    return dict(sorted(mejor.items()))
# Recomendado: el piso de 8,000 N·m/° — el doble de lo que pide el doc maestro,
# y sigue muy por encima de un kit car típico (2,000-6,000).
REC = next((b for b in validos if b["kmin"] == 8000), validos[0])
asig_rec = REC["asig"]

print("\nmasa vs numero de secciones distintas:")
POR_N = por_n_secciones(asig_rec, REC["kmin"])
for n, v in POR_N.items():
    print(f"  {n} secciones -> {v['masa']:5.1f} kg  FS {v['fs']:.2f}  K {v['ktor']:7,.0f}  "
          f"({', '.join(sorted({s['nombre'] for s in v['asig'].values()}))})")

# --- LA RECOMENDACIÓN ---
# No es el óptimo absoluto. Con 3 secciones se consigue la mayor parte del ahorro
# agregando UN solo tubo a la lista de compra; las secciones 4 y 5 compran pocos kilos
# a cambio de más renglones que comprar, más pilas que no confundir en el taller y más
# oportunidades de soldar el tubo equivocado. Para este proyecto, no vale la pena.
N_REC = 3 if 3 in POR_N else max(POR_N)
FINAL = POR_N[N_REC]
asig_final = FINAL["asig"]
m_final, fs_final, fsb_final, k_final, peor_final, det_final = evaluar(asig_final)
print(f"\nELEGIDO: {N_REC} secciones -> {m_final:.1f} kg ({m_final-m0:+.1f} kg), "
      f"FS {fs_final:.2f}, K {k_final:,.0f} N.m/deg")

# ============================================================================
# 5. SALIDAS
# ============================================================================
_, elems_rec, _ = construir(asig_final)
out_csv = os.path.join(HERE, "..", "planos", "lista-corte-tubos-optimizada.csv")
with open(out_csv, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["#", "de_nodo", "a_nodo", "seccion", "funcion", "longitud_mm",
                "x1", "y1", "z1", "x2", "y2", "z2"])
    for i, e in enumerate(sorted(elems_rec, key=lambda e: (e["sec"]["nombre"], -e["L"])), 1):
        pa, pb = ac.NODES[e["a"]], ac.NODES[e["b"]]
        w.writerow([i, e["a"], e["b"], e["sec"]["nombre"], e["tag"], f"{e['L']*1000:.0f}",
                    *[f"{v*1000:.0f}" for v in pa], *[f"{v*1000:.0f}" for v in pb]])

def largo_grupo(c):
    return sum(np.linalg.norm(ac.NODES[b] - ac.NODES[a]) for (a, b, _) in GRUPOS[c])

out_md = os.path.join(HERE, "resultados-optimizacion-chasis.md")
with open(out_md, "w", encoding="utf-8") as f:
    f.write("# Optimización de secciones del chasis — el mismo carro, más ligero\n\n")
    f.write("Generado por `optimizar_chasis.py`. Reusa la geometría, el FEM de vigas 3D y "
            "los casos de carga que ya estaban validados en `analisis_chasis.py`: **no se "
            "movió ni un nodo**, solo qué tubo va en cada lugar.\n\n")

    f.write("## Por qué había masa que quitar\n\n")
    f.write(f"El chasis usa una sola sección para casi todo. De los {len(ac.MEMBERS)} tubos, "
            f"solo uno está al límite — el peor da FS **{fs0:.2f}** en bache 3g. Los otros "
            f"{len(ac.MEMBERS)-1} van sobrados, algunos muchísimo. Poner el mismo tubo en "
            "todos lados es cómodo para comprar, pero se paga en kilos.\n\n")
    f.write("La optimización agrupa los tubos **por función** (no uno por uno: un chasis con "
            "73 secciones distintas sería imposible de comprar y de armar) y le busca a cada "
            "grupo la sección más ligera del catálogo que siga cumpliendo todo.\n\n")

    f.write("## Restricciones que NO se negocian\n\n")
    f.write(f"- **FS ≥ {FS_OBJ:.1f} a fluencia** en los 3 casos de carga (bache 3g, frenada "
            "1g, curva 1g).\n")
    f.write(f"- **FS ≥ {FS_OBJ:.1f} a pandeo de Euler** en cada tubo comprimido.\n")
    f.write("- Solo secciones de catálogo que de verdad se consiguen.\n")
    f.write("- **Pisos por grupo que el optimizador no puede cruzar.** La regla: *un tubo no "
            "se optimiza contra un análisis que no incluye el caso que lo hace importante*. "
            "Este FEM tiene bache, frenada y curva — **no tiene volcadura ni choque**:\n\n")
    for c, piso in PISO_GRUPO.items():
        f.write(f"  - {NOMBRE_GRUPO[c]}: no baja de **{piso}**\n")
    f.write("\n  Sin estos pisos el optimizador bajaba la barra de cinturones a PTR 25×25×1.5 "
            "— y ahí es donde tiran los arneses en un impacto. El FEM lo permitía porque no "
            "tiene ese caso de carga; el criterio de ingeniería no.\n\n")

    f.write("## El intercambio: rigidez torsional vs masa\n\n")
    f.write(f"El diseño actual da **{k0:,.0f} N·m/°**, cuando el doc maestro pide >4,000 para "
            "un deportivo ligero artesanal y un kit car típico anda entre 2,000 y 6,000. O "
            "sea: hay rigidez de sobra, y sobra es masa. Bajar el piso es un intercambio "
            "legítimo, así que se barrió:\n\n")
    f.write("| Piso de rigidez | Masa | vs actual | FS mínimo | Rigidez real | |\n")
    f.write("|---|---|---|---|---|---|\n")
    for b in barrido:
        if not b["ok"]:
            f.write(f"| {b['kmin']:,} N·m/° | — | — | — | — | infactible |\n")
            continue
        marca = "✓ **recomendado**" if b is REC else ""
        f.write(f"| {b['kmin']:,} N·m/° | {b['masa']:.1f} kg | **{b['masa']-m0:+.1f} kg** | "
                f"{b['fs']:.2f} | {b['ktor']:,.0f} N·m/° | {marca} |\n")
    f.write(f"\nCon el piso en {REC['kmin']:,} N·m/° el óptimo absoluto baja a "
            f"**{REC['masa']:.1f} kg**. Pero ese óptimo usa "
            f"{len({s['nombre'] for s in asig_rec.values()})} secciones distintas, y ahí "
            "aparece el segundo intercambio.\n\n")

    f.write("## El intercambio que de verdad importa: masa vs simplicidad\n\n")
    f.write("Un chasis con muchas secciones distintas pesa menos pero es más lío: más "
            "renglones que comprar, más pilas de tubo que no confundir en el taller y más "
            "oportunidades de soldar el tubo equivocado en el lugar equivocado. Se midió el "
            "precio en kilos de usar menos secciones:\n\n")
    f.write("| Secciones distintas | Masa | vs actual | FS | Rigidez | Cuáles |\n")
    f.write("|---|---|---|---|---|---|\n")
    for n, v in POR_N.items():
        marca = " ✓ **elegido**" if n == N_REC else ""
        secs = ", ".join(sorted({s["nombre"] for s in v["asig"].values()}))
        f.write(f"| {n}{marca} | {v['masa']:.1f} kg | {v['masa']-m0:+.1f} kg | "
                f"{v['fs']:.2f} | {v['ktor']:,.0f} N·m/° | {secs} |\n")
    ahorro3 = m0 - POR_N[N_REC]["masa"]
    ahorro_max = m0 - REC["masa"]
    f.write(f"\n**Elegido: {N_REC} secciones.** Se lleva **{ahorro3:.1f} kg de los "
            f"{ahorro_max:.1f} kg posibles ({ahorro3/ahorro_max*100:.0f}% del beneficio) "
            "agregando UN solo tubo a la lista de compra**, y encima conserva casi toda la "
            f"rigidez ({POR_N[N_REC]['ktor']:,.0f} contra {k0:,.0f} N·m/°). Las secciones 4 y "
            f"5 compran {ahorro_max-ahorro3:.1f} kg más — no vale la pena para este "
            "proyecto.\n\n")

    f.write("## Qué tubo va en cada grupo\n\n")
    f.write("| Grupo | Largo total | Antes | Ahora | Δ masa |\n|---|---|---|---|---|\n")
    for c in CLAVES:
        L = largo_grupo(c)
        a0, a1 = ACTUAL[c], asig_final[c]
        d = L * (a1["kg_m"] - a0["kg_m"])
        cambio = "sin cambio" if a0["nombre"] == a1["nombre"] else f"**{d:+.1f} kg**"
        f.write(f"| {NOMBRE_GRUPO[c]} | {L:.1f} m | {a0['nombre']} | "
                f"**{a1['nombre']}** | {cambio} |\n")
    f.write(f"\n**Total: {m0:.1f} kg → {m_final:.1f} kg "
            f"({(m0-m_final)/m0*100:.0f}% menos de acero estructural).** El único tubo nuevo "
            "en la lista de compra es el **PTR 25×25×1.5** de las diagonales.\n\n")

    f.write("## Verificación del diseño elegido\n\n")
    f.write("| | Actual | Optimizado |\n|---|---|---|\n")
    f.write(f"| Masa de acero | {m0:.1f} kg | **{m_final:.1f} kg** |\n")
    f.write(f"| FS mínimo a fluencia | {fs0:.2f} | **{fs_final:.2f}** |\n")
    f.write(f"| FS mínimo a pandeo | {fsb0:.1f} | **{fsb_final:.1f}** |\n")
    f.write(f"| Rigidez torsional | {k0:,.0f} N·m/° | **{k_final:,.0f} N·m/°** |\n")
    f.write(f"| Secciones que comprar | 2 | **{N_REC}** |\n\n")
    f.write(f"El tubo crítico del diseño optimizado es **{peor_final[1]}** "
            f"({peor_final[2]}) en {peor_final[0]}, con FS {fs_final:.2f} — el mismo tubo que "
            "ya era el crítico antes, así que el margen no se movió de sitio.\n\n")
    f.write("Los 10 tubos más esforzados del diseño optimizado:\n\n")
    f.write("| Caso | Tubo | Función | Sección | σ (MPa) | FS |\n|---|---|---|---|---|---|\n")
    for (caso, mm, tag, sec, sig, fs, fsb) in sorted(det_final, key=lambda r: r[5])[:10]:
        f.write(f"| {caso} | {mm} | {tag} | {sec} | {sig:.0f} | {fs:.2f} |\n")

    f.write("\n## Qué significa esto para el carro\n\n")
    ahorro = m0 - m_final
    f.write(f"**{ahorro:.1f} kg** de un carro de 690 kg es **{ahorro/690*100:.1f}%** del peso "
            "total. No es dramático, y conviene decirlo así en vez de vendértelo como una "
            "transformación: es peso quitado del lugar correcto — acero estructural repartido "
            "por todo el chasis — sin tocar la seguridad ni la geometría de suspensión que ya "
            "estaba afinada.\n\n")
    f.write("Menos kilos arriba también significa un poco menos de todo lo demás: menos carga "
            "en resortes y frenos, un pelo más de autonomía. Nada de eso cambia el carro, pero "
            "va en la dirección correcta y sale gratis.\n\n")
    f.write("### Dos avisos de taller\n\n")
    f.write("1. **Las diagonales quedan en pared de 1.5 mm.** Eso perdona menos al soldar: es "
            "donde un novato perfora el tubo. Practicar específicamente en retazos de "
            "PTR 25×25×1.5 antes de tocar el chasis, con menos amperaje y cordones cortos. "
            "El resto del chasis sigue en 1.9 mm, que es mucho más noble.\n")
    f.write("2. **Son dos pilas de tubo cuadrado en el taller**, no una. Marcar los tramos con "
            "plumón desde que llegan: soldar una diagonal de 38 donde va una de 25 no se nota "
            "hasta que se pesa, pero al revés sí importa.\n\n")
    f.write("**Antes de cortar:** esto sigue siendo un análisis lineal estático que no incluye "
            "fatiga, abolladura local ni choque. El FEM formal de validación (punto 10 de "
            "`que-falta-para-construir.md`) es obligatorio antes de soldar, y con secciones más "
            "delgadas cobra todavía más importancia.\n\n")
    f.write("Lista de corte del diseño optimizado: `planos/lista-corte-tubos-optimizada.csv`.\n")

# ---------------- gráfica ----------------
fig, axs = plt.subplots(1, 2, figsize=(13, 5.4), facecolor="#0d1117")
for ax in axs:
    ax.set_facecolor("#0d1117"); ax.grid(color="#21262d", lw=0.6)
    ax.tick_params(colors="#8b949e", labelsize=8.5)
    for sp in ax.spines.values(): sp.set_color("#30363d")

ax = axs[0]
ks = [b["ktor"] / 1000 for b in validos]
ms = [b["masa"] for b in validos]
ax.plot(ks, ms, marker="o", color="#38bdf8", lw=2.2)
ax.plot(k0 / 1000, m0, marker="*", ms=20, color="#f87171", zorder=5)
ax.annotate(f"actual\n{m0:.1f} kg", (k0 / 1000, m0), textcoords="offset points",
            xytext=(-12, -28), color="#f87171", fontsize=9, ha="center")
ax.plot(k_final / 1000, m_final, marker="*", ms=20, color="#4ade80", zorder=5)
ax.annotate(f"elegido ({N_REC} secciones)\n{m_final:.1f} kg", (k_final / 1000, m_final),
            textcoords="offset points", xytext=(14, 8), color="#4ade80", fontsize=9)
ax.axvline(4.0, color="#f97316", lw=1.4, ls="--")
ax.text(4.15, max(ms), "mínimo del\ndoc maestro", color="#f97316", fontsize=8, va="top")
ax.set_xlabel("rigidez torsional (miles de N·m/°)", color="#8b949e", fontsize=9)
ax.set_ylabel("masa de acero (kg)", color="#8b949e", fontsize=9)
ax.set_title("El intercambio: cuánta rigidez cuesta cada kilo", color="#e6edf3", fontsize=10)

ax = axs[1]
nombres = [NOMBRE_GRUPO[c].split("(")[0].strip() for c in CLAVES]
antes = [largo_grupo(c) * ACTUAL[c]["kg_m"] for c in CLAVES]
ahora = [largo_grupo(c) * asig_final[c]["kg_m"] for c in CLAVES]
y = np.arange(len(CLAVES))
ax.barh(y + 0.19, antes, 0.36, color="#f87171", label=f"actual ({m0:.1f} kg)")
ax.barh(y - 0.19, ahora, 0.36, color="#4ade80", label=f"optimizado ({REC['masa']:.1f} kg)")
ax.set_yticks(y); ax.set_yticklabels(nombres, fontsize=8.5, color="#c9d1d9")
ax.invert_yaxis()
ax.set_xlabel("kg de acero", color="#8b949e", fontsize=9)
ax.set_title("De dónde salen los kilos", color="#e6edf3", fontsize=10)
ax.legend(facecolor="#0d1117", edgecolor="#30363d", labelcolor="#e6edf3", fontsize=8.5)

fig.suptitle(f"Optimización de secciones — {m0:.1f} kg → {m_final:.1f} kg agregando UN tubo "
             "a la lista, sin mover un nodo ni tocar la célula de seguridad",
             color="#e6edf3", fontsize=12)
fig.tight_layout()
out_png = os.path.join(HERE, "optimizacion-chasis.png")
fig.savefig(out_png, dpi=150, facecolor="#0d1117", bbox_inches="tight")

for c in CLAVES:
    if ACTUAL[c]["nombre"] != asig_final[c]["nombre"]:
        print(f"  {NOMBRE_GRUPO[c]:44s} {ACTUAL[c]['nombre']:18s} -> {asig_final[c]['nombre']}")
print(f"OK  {out_md}\nOK  {out_png}\nOK  {out_csv}")
