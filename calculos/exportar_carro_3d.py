# -*- coding: utf-8 -*-
"""
EL CARRO COMPLETO EN 3D — modelo de ensamble, no una maqueta.

Cada mecanismo se construye con su geometría real, no con una caja que lo
represente: los coilovers llevan su resorte helicoidal, las ruedas su rin con
rayos y su llanta con perfil, los discos su campana y sus barrenos, los calipers
sus pastillas. Y las piezas de corte láser se dibujan con **el contorno real de
su DXF** — el mismo archivo que va al cortador, incluidas las placas de torque
que salieron de la optimización topológica.

Todo en coordenadas reales sacadas de su propio entregable:

  chasis (73 tubos, secciones optimizadas)      analisis_chasis / optimizar_chasis
  nodos generativos (5 tipos, 12 piezas)        nodo_generativo
  cartelas de lámina                            planos/*.dxf
  suspensión delantera (horquillas, manguetas)  suspension_delantera
  suspensión trasera (brazos tirados)           suspension_trasera
  placas de torque del QS273                    placa_torque + su DXF
  frenos (4 discos, calipers, pedalera)         frenos
  dirección (cremallera, tie rods, columna)     direccion
  ruedas y motores de cubo                      spec del kit QS273
  batería (30 celdas con busbars)               doc maestro
  cabina (butacas, arneses, pilotos)            doc maestro

Salida: visor Three.js autocontenido con explorador por sistema, secuencia de
armado con lista de verificación y pares de apriete, vista explotada según la
dirección real de montaje, y clic para inspeccionar cualquier pieza.

Uso:  python exportar_carro_3d.py [salida.html]
"""
import json, sys, os, math
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
CAD = os.path.join(HERE, "..", "cad")
PLANOS = os.path.join(HERE, "..", "planos")
sys.path.insert(0, HERE)
import analisis_chasis as ac

R4 = lambda *a: [round(float(x), 4) for x in a]

# ============================================================================
# 1. LECTOR DE DXF — las piezas de lámina se dibujan con su contorno real
# ============================================================================
def leer_dxf(nombre):
    """Devuelve (contorno_exterior, barrenos) en mm. El contorno sale de encadenar
    los LINE consecutivos; los barrenos son los CIRCLE."""
    ruta = os.path.join(PLANOS, nombre)
    t = [l.strip() for l in open(ruta, encoding="utf-8")]
    lineas, circulos, i = [], [], 0
    while i < len(t) - 1:
        if t[i] == "0" and t[i + 1] in ("LINE", "CIRCLE"):
            tipo, d, j = t[i + 1], {}, i + 2
            while j + 1 < len(t) and t[j] != "0":
                d[t[j]] = t[j + 1]; j += 2
            if tipo == "LINE":
                lineas.append(((float(d["10"]), float(d["20"])),
                               (float(d["11"]), float(d["21"]))))
            else:
                circulos.append((float(d["10"]), float(d["20"]), float(d["40"])))
            i = j
        else:
            i += 1
    # encadenar: se escribieron en orden, cada segmento empieza donde acabó el anterior
    lazos, actual = [], []
    for (p, q) in lineas:
        if actual and (abs(actual[-1][0] - p[0]) > 1e-6 or abs(actual[-1][1] - p[1]) > 1e-6):
            lazos.append(actual); actual = []
        if not actual:
            actual.append(p)
        actual.append(q)
    if actual:
        lazos.append(actual)
    # solo cadenas cerradas: las ranuras dibujadas con arcos sueltos quedan abiertas
    cerrado = lambda l: (l[0][0] - l[-1][0])**2 + (l[0][1] - l[-1][1])**2 < 1.0
    lazos = [l for l in lazos if len(l) > 3 and cerrado(l)]
    if not lazos:
        return [], circulos
    def area(l):
        return abs(sum(l[k][0] * l[(k + 1) % len(l)][1] - l[(k + 1) % len(l)][0] * l[k][1]
                       for k in range(len(l)))) / 2
    lazos.sort(key=area, reverse=True)
    # Caso anillo (el doblador del cubo): su contorno exterior es un CIRCLE y las
    # líneas son el hueco doble-D de adentro. Si hay un círculo más grande que el
    # lazo de líneas, ese círculo es el contorno y las líneas pasan a ser hueco.
    rext = max(math.hypot(*p) for p in lazos[0])
    grandes = [c for c in circulos if c[2] > rext]
    if grandes:
        g = max(grandes, key=lambda c: c[2])
        aro = [(g[0] + g[2] * math.cos(2 * math.pi * k / 64),
                g[1] + g[2] * math.sin(2 * math.pi * k / 64)) for k in range(64)]
        return [aro] + lazos, [c for c in circulos if c is not g]
    return lazos, circulos

def simplifica(pts, tol=0.6):
    """Quita puntos casi colineales: el contorno del topopt trae ~250 y con 90 basta."""
    if len(pts) < 4:
        return pts
    out = [pts[0]]
    for p in pts[1:]:
        if (p[0] - out[-1][0])**2 + (p[1] - out[-1][1])**2 >= tol * tol:
            out.append(p)
    if (out[0][0] - out[-1][0])**2 + (out[0][1] - out[-1][1])**2 < tol * tol:
        out.pop()
    return out

PERFILES = {}
for arch in ["placa-torque-motor.dxf", "placa-torque-refuerzo.dxf",
             "placa-torque-doblador.dxf", "cartela-torre-coilover.dxf",
             "cartela-pivote-brazo.dxf", "placa-cuna-bateria.dxf"]:
    try:
        lazos, circ = leer_dxf(arch)
        if not lazos:
            continue
        PERFILES[arch] = {
            "ext": [R4(*p) for p in simplifica(lazos[0])],
            "int": [[R4(*p) for p in simplifica(l)] for l in lazos[1:]],
            "cir": [R4(*c) for c in circ],
        }
    except Exception as ex:
        print(f"  aviso: no se pudo leer {arch}: {ex}")

# ============================================================================
# 2. PUNTOS DUROS (de los entregables)
# ============================================================================
LA1 = np.array([0.35, 0.200, 0.50]);  LA2 = np.array([0.75, 0.200, 0.55])
UA1 = np.array([0.35, 0.417, 0.50]);  UA2 = np.array([0.75, 0.417, 0.55])
LBJ = np.array([0.545, 0.190, 0.710]); UBJ = np.array([0.565, 0.425, 0.685])
TR  = np.array([0.430, 0.198, 0.695])
RACK = np.array([0.370, 0.207, 0.504])
WD  = np.array([0.55, 0.2876, 0.75])
SHK_SUP_D = np.array([0.75, 0.48, 0.55]); SHK_INF_D = np.array([0.58, 0.215, 0.66])
R_DEL, ANCHO_LL = 0.2876, 0.177

PIV = np.array([2.28, 0.16, 0.552])
EJE = np.array([2.68, 0.3005, 0.76])
SHK_SUP_T = np.array([2.58, 0.712, 0.425])
SHK_INF_T = PIV + 0.80 * (EJE - PIV)
R_TRAS = 0.3005
R_MOTOR, W_MOTOR = 0.175, 0.130
R_DISCO, W_DISCO = 0.110, 0.005

GAP_PLACAS, T_PLACA = 0.050, 0.008
Z_MOTOR_INT = EJE[2] - W_MOTOR / 2
Z_DISCO = Z_MOTOR_INT - 0.012
Z_PLACA_EXT = Z_MOTOR_INT - 0.030
Z_PLACA_INT = Z_PLACA_EXT - GAP_PLACAS
Z_PUNTA = (Z_PLACA_EXT + Z_PLACA_INT) / 2
PUNTA = np.array([EJE[0], EJE[1], Z_PUNTA])
EJE_LIBRE_REQ = Z_MOTOR_INT - Z_PLACA_INT + T_PLACA / 2

esp = lambda p: np.array([p[0], p[1], -p[2]])

# ============================================================================
# 3. CONSTRUCTOR DE PIEZAS
# ============================================================================
PIEZAS = []
def P(sis, nom, spec, paso, col, exp=None, **geo):
    """exp: dirección real de montaje (hacia dónde se separa al explotar)."""
    d = dict(id=len(PIEZAS), sis=sis, nom=nom, spec=spec, paso=paso, col=col)
    if exp is not None:
        d["exp"] = R4(*exp)
    d.update(geo)
    PIEZAS.append(d)
    return d

def eje_de(a, b):
    return dict(a=R4(*a), b=R4(*b))

# ============================================================================
# 4. CHASIS
# ============================================================================
for e in ac.elems:
    a, b = ac.NODES[e["a"]], ac.NODES[e["b"]]
    nom = e["sec"]["nombre"]
    red = nom.startswith("RED")
    lado = 0.0445 if red else float(nom.split("x")[0].split()[1]) / 1000.0
    P("chasis", f"Tubo {e['a']}–{e['b']}",
      f"{nom} · {e['tag']} · corte {e['L']*1000:.0f} mm", 1,
      "#e06c75" if red else ("#7d8590" if e["tag"] == "tors" else "#aab2bb"),
      exp=(0, 0.35, 0),
      t="tubo_r" if red else "tubo_c", r=lado / 2, w=lado, **eje_de(a, b))

# --- cordones de soldadura en cada nudo (lo que hace que se vea soldado) ---
grados = {}
for e in ac.elems:
    for n in (e["a"], e["b"]):
        grados[n] = grados.get(n, 0) + 1
for n, g in grados.items():
    if g >= 3:
        P("chasis", f"Nudo soldado {n}", f"Confluyen {g} tubos · inspección de soldadura "
          "obligatoria antes de seguir", 1, "#8a939c", exp=(0, 0.35, 0),
          t="esfera", pos=R4(*ac.NODES[n]), r=0.027)

# --- nodos generativos ---
COLOCACION = [
    ("susp_del",  "nodo-suspension-datos.json", "#fb923c",
     "Torre de coilover delantera — le llegan 5 tubos y la carga de la rueda · "
     "optimización topológica SIMP 3D", ["fx_hiL", "fx_hiR"]),
    ("susp_tras", "nodo-susp_tras-datos.json",  "#f87171",
     "Torre de coilover trasera — coilover más el empuje del motor de cubo",
     ["coilL", "coilR"]),
    ("arco_ppal", "nodo-arco_ppal-datos.json",  "#c084fc",
     "Base del arco principal — baja la carga de vuelco al estribo",
     ["mh_loL", "mh_loR"]),
    ("cuna_bat",  "nodo-cuna_bat-datos.json",   "#4ade80",
     "Esquina de la cuna de batería — sostiene los 90 kg del pack",
     ["bat_fL", "bat_fR", "bat_rL", "bat_rR"]),
    ("pilar_a",   "nodo-pilar_a-datos.json",    "#38bdf8",
     "Nodo del pilar A — recibe techo, parabrisas y diagonal de puerta",
     ["dash_hiL", "dash_hiR"]),
]
VOXELS = {}
for tipo, fn, color, desc, juntas in COLOCACION:
    nd = json.load(open(os.path.join(CAD, fn), encoding="utf-8"))
    VOXELS[tipo] = {"nelx": nd["nelx"], "nely": nd["nely"], "nelz": nd["nelz"], "vox": nd["vox"]}
    for j in juntas:
        P("nodos", f"Nodo generativo «{tipo}»", desc, 1, color, exp=(0, 0.5, 0),
          t="voxel", tipo=tipo, pos=R4(*ac.NODES[j]), mir=j.endswith("R"))

# --- cartelas de lámina, con su contorno real ---
def cartela(sis, nom, spec, paso, col, arch, pos, rotz=0.0, esp_m=0.0047, s=1, exp=None):
    if arch not in PERFILES:
        return
    P(sis, nom, spec, paso, col, exp=exp or (0, 0, 0.35 * s),
      t="perfil", perfil=arch, pos=R4(*pos), rotz=round(rotz, 4), esp=esp_m, s=s)

for s in (1, -1):
    m = (lambda p: p if s > 0 else esp(p))
    lado = "izq" if s > 0 else "der"
    for dz, sufijo in [(0.028, "exterior"), (-0.028, "interior")]:
        cartela("chasis", f"Cartela de torre de coilover trasera ({lado}, {sufijo})",
                "Lámina 4.7 mm, corte láser · `cartela-torre-coilover.dxf` · reparte la "
                "carga del coilover al nudo", 1, "#94a3b8", "cartela-torre-coilover.dxf",
                m(SHK_SUP_T + np.array([-0.02, -0.09, dz * s])), rotz=math.radians(78), s=s)
        cartela("chasis", f"Cartela de pivote de brazo trasero ({lado}, {sufijo})",
                "Lámina 4.7 mm · `cartela-pivote-brazo.dxf` · aguanta el par del brazo "
                "tirado contra el riel", 1, "#94a3b8", "cartela-pivote-brazo.dxf",
                m(PIV + np.array([-0.05, -0.015, dz * s])), rotz=math.radians(8), s=s)
    cartela("chasis", f"Placa lateral de cuna de batería ({lado})",
            "Lámina 4.7 mm · `placa-cuna-bateria.dxf` · lleva las ranuras de los cinchos",
            1, "#94a3b8", "placa-cuna-bateria.dxf",
            m(np.array([2.10, 0.17, 0.50 * s])), rotz=0.0, s=s)

# ============================================================================
# 5. SUSPENSIÓN DELANTERA
# ============================================================================
COL_BRAZO, COL_MUELLE, COL_SHOCK = "#f97316", "#fbbf24", "#3f4756"
for s in (1, -1):
    m = (lambda p: p if s > 0 else esp(p))
    lado = "izq" if s > 0 else "der"
    P("susp_del", f"Horquilla inferior delantera ({lado})",
      "Tubo redondo 25.4×2.1 en A · pivotes con buje de poliuretano Ø12 · rótula cónica "
      "ATV en la punta", 2, COL_BRAZO, exp=(0, -0.15, 0.4 * s),
      t="brazo_a", p1=R4(*m(LA1)), p2=R4(*m(LA2)), ap=R4(*m(LBJ)), r=0.0127)
    P("susp_del", f"Horquilla superior delantera ({lado})",
      "Tubo redondo 25.4×2.1 en A · la ménsula baja el eje 63 mm bajo el tubo superior",
      2, COL_BRAZO, exp=(0, 0.15, 0.4 * s),
      t="brazo_a", p1=R4(*m(UA1)), p2=R4(*m(UA2)), ap=R4(*m(UBJ)), r=0.0127)
    P("susp_del", f"Mangueta delantera ({lado})",
      "Donante ATV 300 · camber −1° · caster 4.9° · KPI 6.1° · scrub 20 mm · trail 24 mm",
      2, "#8d97a3", exp=(0, 0, 0.5 * s),
      t="mangueta", lbj=R4(*m(LBJ)), ubj=R4(*m(UBJ)), cubo=R4(*m(WD)),
      tr=R4(*m(TR)), s=s)
    for pt, nom in [(LBJ, "inferior"), (UBJ, "superior")]:
        P("susp_del", f"Rótula cónica {nom} ({lado})",
          "Tipo Honda TRX300 · verificar el cono contra la mangueta ANTES de comprar",
          2, "#cbd5e1", exp=(0, 0, 0.3 * s), t="rotula", pos=R4(*m(pt)),
          dir=R4(*(np.array([0, 1.0, 0]) if nom == "inferior" else np.array([0, -1.0, 0]))))
    P("susp_del", f"Coilover delantero ({lado})",
      "Resorte 270 lb/in · ojo a ojo 334 mm · carrera 81 mm · ζ 0.5-0.7 · motion ratio "
      "0.58 · 5,705 N en bache 3g", 2, COL_MUELLE, exp=(0, 0.3, 0.25 * s),
      t="coilover", **eje_de(m(SHK_INF_D), m(SHK_SUP_D)), rc=0.036, rb=0.021, hilo=0.007,
      vueltas=7)
    for pt in (LA1, LA2, UA1, UA2):
        P("susp_del", f"Buje de pivote ({lado})",
          "Poliuretano Ø12 + tubo interno de acero · se cambia sin cortar nada",
          2, "#475569", exp=(0, 0, 0.25 * s), t="buje", pos=R4(*m(pt)),
          dir=R4(*(m(LA2) - m(LA1))), d=0.026, L=0.05)

# ============================================================================
# 6. SUSPENSIÓN TRASERA + PLACAS DE TORQUE
# ============================================================================
ang_brazo = math.atan2(PIV[1] - EJE[1], PIV[0] - EJE[0])
for s in (1, -1):
    m = (lambda p: p if s > 0 else esp(p))
    lado = "izq" if s > 0 else "der"
    P("susp_tras", f"Brazo tirado ({lado})",
      "PTR 70×50×4 · corte 504 mm · FS 2.4 · motion ratio 0.68 · anti-squat 258% — "
      "termina antes del motor: el eje del QS273 salva el resto en voladizo",
      2, COL_BRAZO, exp=(0, -0.2, 0.3 * s),
      t="tubo_rect", **eje_de(m(PIV), m(PUNTA)), w=0.050, h=0.070)
    P("susp_tras", f"Buje de pivote trasero ({lado})",
      "Poliuretano Ø16 + manga de acero, base 150 mm · aquí se calzan 1-2 mm de toe-in",
      2, "#475569", exp=(0, 0, 0.3 * s), t="buje", pos=R4(*m(PIV)),
      dir=R4(0, 0, 1), d=0.034, L=0.09)
    P("susp_tras", f"Coilover trasero ({lado})",
      "Resorte 351 lb/in · ~590 mm extendido · carrera ≥108 mm · 7,358 N en bache 3g",
      2, COL_MUELLE, exp=(0, 0.35, 0.25 * s),
      t="coilover", **eje_de(m(SHK_INF_T), m(SHK_SUP_T)), rc=0.040, rb=0.024, hilo=0.008,
      vueltas=7)
    for zpl, arch, nom, spec in [
        (Z_PLACA_EXT, "placa-torque-motor.dxf", "Placa de torque exterior",
         "Acero 8 mm · 0.69 kg · FS 2.3 · contorno de optimización topológica SIMP 2D · "
         "lleva integradas las orejas del caliper"),
        (Z_PLACA_INT, "placa-torque-refuerzo.dxf", "Placa de torque interior",
         "Acero 8 mm · 0.58 kg · FS 2.8 · con la exterior forma el par que toma el "
         "momento de vuelco del motor en voladizo")]:
        cartela("susp_tras", f"{nom} ({lado})", spec, 2, "#38bdf8", arch,
                m(np.array([EJE[0], EJE[1], zpl])), rotz=ang_brazo, esp_m=T_PLACA, s=s,
                exp=(0, 0, 0.6 * s))
        cartela("susp_tras", f"Doblador del cubo ({lado})",
                "Anillo Ø56 de acero 8 mm soldado alrededor del eje · sube el FS de "
                "aplastamiento de 1.1 a 2.2 — sin él se arrancan los cables de fase",
                2, "#0ea5e9", "placa-torque-doblador.dxf",
                m(np.array([EJE[0], EJE[1], zpl + 0.009 * s])), rotz=ang_brazo,
                esp_m=T_PLACA, s=s, exp=(0, 0, 0.7 * s))
    # tornillería de la junta: 4 × M12 10.9 en las posiciones reales del cálculo
    for (bu, bv) in [(0.036, 0.025), (0.036, -0.025), (0.096, 0.025), (0.096, -0.025)]:
        loc = np.array([EJE[0] + bu * math.cos(ang_brazo) - bv * math.sin(ang_brazo),
                        EJE[1] + bu * math.sin(ang_brazo) + bv * math.cos(ang_brazo),
                        (Z_PLACA_EXT + Z_PLACA_INT) / 2])
        P("susp_tras", f"Tornillo M12 10.9 de placa de torque ({lado})",
          "Pasa por camisa de acero soldada a través del PTR (sin camisa el apriete "
          "aplasta el tubo) · el más cargado toma 12.4 kN · apretar a 95 N·m",
          2, "#e2e8f0", exp=(0, 0, 0.8 * s), t="tornillo", pos=R4(*m(loc)),
          dir=R4(0, 0, 1), d=0.012, L=GAP_PLACAS + 2 * T_PLACA + 0.02)

# ============================================================================
# 7. RUEDAS, MOTORES Y FRENOS
# ============================================================================
for (cx, R, rin, llanta, tras) in [(WD[0], R_DEL, 13, "175/70R13", False),
                                   (EJE[0], R_TRAS, 14, "175/70R14", True)]:
    for s in (1, -1):
        zc = (EJE[2] if tras else WD[2]) * s
        lado, pos_ = ("izq" if s > 0 else "der"), ("trasera" if tras else "delantera")
        P("ruedas", f"Rueda {pos_} ({lado})",
          f"{llanta} · Ø{R*2000:.0f} mm · rin {rin}\"" +
          (" desmontable de carro, atornillado a la brida del QS273: la carcasa del "
           "motor (Ø350) llena el rin (Ø356) y hace de centro de rueda — por eso no "
           "lleva rayos" if tras else " de deshuesadero, con maza y 5 rayos") +
          " · perfil 70 para absorber topes (masa no suspendida alta)",
          4, "#1a1e24", exp=(0, 0, 0.9 * s),
          t="rueda", pos=R4(cx, R, zc), s=s, R=R, W=ANCHO_LL, Rr=rin * 0.0127, rayos=5,
          tipo="motor" if tras else "rayos")
        if tras:
            P("motores", f"Motor de cubo QS273 ({lado})",
              "8 kW · 96 V · 350 N·m · carcasa Ø350 · 27 kg de masa NO suspendida · "
              "los cables de fase salen por dentro del eje", 4, "#4b5563",
              exp=(0, 0, 1.1 * s),
              t="motor", pos=R4(cx, R, zc), s=s, R=R_MOTOR, W=W_MOTOR)
            P("susp_tras", f"Eje del QS273 ({lado})",
              f"Ø20 con caras planas a 16 mm · **necesita ≥{EJE_LIBRE_REQ*1000:.0f} mm "
              "libres del lado interior** — el dato más crítico a confirmar con QS Motor",
              4, "#e5e7eb", exp=(0, 0, 1.0 * s), t="cil",
              **eje_de((cx, R, (Z_PLACA_INT - 0.012) * s), (cx, R, zc)), r=0.010)
        zd = Z_DISCO * s if tras else zc - 0.055 * s
        P("frenos", f"Disco de freno {pos_} ({lado})",
          ("Ø220 — lo trae el QS273" if tras else
           "Ø220×5 macizo · el del donante ATV (Ø180-200) NO alcanza para 690 kg") +
          f" · par requerido {'437' if tras else '555'} N·m a 1g",
          3, "#b9c0c8", exp=(0, 0, 0.75 * s),
          t="disco", pos=R4(cx, R, zd), s=s, R=R_DISCO, Rh=0.045, t_=W_DISCO)
        ang = math.radians(55 if tras else 120)
        P("frenos", f"Caliper {pos_} ({lado})",
          ("Con palanca de freno de mano integrada · pistón ≥740 mm² (Ø31 eq.) · "
           "2.7 kN de apriete para sujetar en pendiente del 20%" if tras else
           "Pistón ≥938 mm² (Ø35 eq.) · de compacto o moto deportiva de 2-4 pistones · "
           "pastilla semi-metálica, NO la más barata"),
          3, "#f59e0b", exp=(0, 0.3, 0.5 * s),
          t="caliper", pos=R4(cx + R_DISCO * 0.88 * math.cos(ang),
                              R + R_DISCO * 0.88 * math.sin(ang), zd),
          s=s, ang=round(ang, 4), Rd=R_DISCO)

# ============================================================================
# 8. DIRECCIÓN
# ============================================================================
PINON = np.array([RACK[0], RACK[1], 0.16])
VOL = np.array([1.44, 0.76, 0.30])
INT = np.array([1.02, 0.50, 0.24])
P("direccion", "Cremallera manual", "De compacto, sin servo · 2.4 vueltas tope a tope · "
  "relación 13:1 · **posición optimizada x=370, z=±504** (lleva el Ackermann de +42% a "
  "+87% sin tocar la mangueta) · montar con barrenos ovalados: ±5 mm de altura duplican "
  "el bump steer", 3, "#22c55e", exp=(0, -0.3, 0),
  t="cremallera", **eje_de(RACK, esp(RACK)), r=0.024)
for s in (1, -1):
    m = (lambda p: p if s > 0 else esp(p))
    lado = "izq" if s > 0 else "der"
    P("direccion", f"Tie rod ({lado})",
      "Tubo roscado derecha/izquierda + 2 rótulas · la convergencia se ajusta girándolo "
      "sin desmontar nada", 3, "#4ade80", exp=(0, 0, 0.35 * s),
      t="tierod", **eje_de(m(RACK), m(TR)), r=0.009)
P("direccion", "Columna — tramo bajo", "Con cruceta al piñón · los ángulos de las dos "
  "crucetas deben ser parecidos y estar EN FASE, si no la dirección pulsa al girar",
  3, "#8d97a3", exp=(0, -0.2, 0), t="columna", **eje_de(PINON, INT), r=0.014)
P("direccion", "Columna — tramo alto", "Preferentemente colapsable: en impacto frontal no "
  "debe empujar el volante contra el pecho", 3, "#8d97a3", exp=(0, 0.2, 0),
  t="columna", **eje_de(INT, VOL), r=0.014)
P("direccion", "Volante", "Ø330 mm · 34 N para girar parado en seco, 6 N rodando",
  3, "#23272e", exp=(0.3, 0.1, 0), t="volante", pos=R4(*VOL), R=0.165)

# --- pedalera ---
P("frenos", "Pedal de freno", "Relación 6.0:1 · 428 N de pie para 1g sin booster · "
  "frenado normal de ciudad son 150 N", 3, "#f59e0b", exp=(-0.25, 0, 0),
  t="pedal", pos=R4(1.06, 0.20, 0.22), h=0.20)
P("frenos", "Pedal de acelerador", "Tipo hall, sin cable · el regen entra al soltarlo, "
  "limitado a 0.24g o el eje trasero se bloquea en mojado", 3, "#4ade80", exp=(-0.25, 0, 0),
  t="pedal", pos=R4(1.06, 0.20, 0.40), h=0.17)
for i, s in enumerate((1, -1)):
    P("frenos", f"Bomba de freno ({'delantera' if s > 0 else 'trasera'})",
      "Ø14.3 mm (9/16\") con depósito · circuito independiente por eje: si revienta una "
      "manguera, el otro eje sigue frenando", 3, "#e2a03f", exp=(-0.3, 0, 0.1 * s),
      t="bomba", pos=R4(0.97, 0.27, 0.07 * s), dir=R4(1, 0.12, 0), L=0.17, r=0.026)

# ============================================================================
# 9. BATERÍA Y ELÉCTRICO
# ============================================================================
BX0, BX1, BY, BHW, BH = 2.11, 2.63, 0.175, 0.47, 0.20
P("bateria", "Caja de batería", "Acero con compresión de celdas, venteo y aislamiento · "
  "30 celdas LiFePO4 en serie · 96 V nominal (109 V cargada) · 10 kWh · ~90 kg · "
  "CAD del arreglo todavía pendiente", 5, "#16a34a", exp=(0, 0.6, 0),
  t="caja_bat", pos=R4((BX0 + BX1) / 2, BY + BH / 2, 0), size=R4(BX1 - BX0, BH, BHW * 2))
for fila in range(2):
    for k in range(15):
        cx = BX0 + 0.030 + k * (BX1 - BX0 - 0.058) / 14
        P("celdas", f"Celda {fila*15+k+1} de 30",
          "LiFePO4 prismática 105 Ah · 3.2 V · **todas del mismo lote**: el pack vale lo "
          "que su peor celda", 5, "#15803d", exp=(0, 0.9, 0),
          t="celda", pos=R4(cx, BY + BH / 2, (-1 if fila else 1) * 0.21),
          size=R4(0.028, 0.160, 0.355))
P("electrico", "BMS 30S", "250-300 A de descarga continua (menos capa los motores) · "
  "balanceo activo · Bluetooth al tablero · **nunca recortar aquí**", 5, "#0ea5e9",
  exp=(0.4, 0.3, 0), t="caja", pos=R4(2.665, 0.30, 0.0), size=R4(0.10, 0.09, 0.28))
for s in (1, -1):
    P("electrico", f"Controlador ({'izq' if s > 0 else 'der'})",
      "APT96600 / Fardriver ND96530 · regen configurable — **van en la nariz** para "
      "compensar el sesgo de peso trasero", 5, "#0284c7", exp=(-0.5, 0.2, 0.15 * s),
      t="caja", pos=R4(0.22, 0.33, 0.15 * s), size=R4(0.22, 0.10, 0.14))
P("electrico", "Contactor + fusible 400 A", "Con resistencia de precarga, paro de "
  "emergencia al alcance del piloto y desconectador de servicio", 5, "#0284c7",
  exp=(-0.5, 0.35, 0), t="caja", pos=R4(0.20, 0.47, 0.0), size=R4(0.16, 0.10, 0.18))
P("electrico", "DC-DC 96→12 V", "30 A aislado — este carro NO lleva batería de 12 V",
  5, "#0284c7", exp=(-0.4, 0.25, 0), t="caja", pos=R4(0.42, 0.34, 0.0),
  size=R4(0.16, 0.08, 0.16))
P("electrico", "Cable HV de tracción", "Naranja, calibre según el diagrama unifilar "
  "(PENDIENTE) · todo cable HV forrado y señalizado", 5, "#f97316", exp=(0, 0.5, 0),
  t="cable", pts=[R4(0.30, 0.40, 0.10), R4(0.9, 0.22, 0.30), R4(1.7, 0.20, 0.34),
                  R4(2.2, 0.24, 0.30), R4(2.62, 0.30, 0.12)], r=0.011)

# ============================================================================
# 10. CABINA
# ============================================================================
for s in (1, -1):
    z = 0.30 * s
    lado = "izq" if s > 0 else "der"
    # el respaldo va reclinado y debe quedar JUSTO delante del arco principal (x=2.02)
    P("cabina", f"Butaca ({lado})", "Comercial atornillada al estribo y al piso · "
      "posición validada con maniquí de 1.75 m, cabeza 5 cm bajo el arco", 6, "#2f3540",
      exp=(0, 0.7, 0), t="butaca", pos=R4(1.56, 0.29, z))
    P("cabina", f"Arnés de 4 puntos ({lado})", "Anclado a la barra de cinturones del frame "
      "(PTR 38×38×1.9, no se optimizó a la baja por eso) · **nunca recortar aquí**",
      6, "#b91c1c", exp=(0, 0.8, 0), t="arnes", pos=R4(1.56, 0.29, z))
P("cabina", "Tablet del tablero", "Velocímetro GPS + BMS + controladores por Bluetooth · "
  "reemplaza todo el tablero convencional", 6, "#111827", exp=(0, 0.4, 0),
  t="caja", pos=R4(1.22, 0.70, 0.0), size=R4(0.015, 0.16, 0.26))

def piloto(z):
    for r, a, b, nom in [(0.13, (1.72, 0.30, z), (1.87, 0.75, z), "torso"),
                         (0.09, (1.70, 0.28, z), (1.38, 0.38, z), "muslos"),
                         (0.06, (1.38, 0.38, z), (1.16, 0.24, z), "piernas"),
                         (0.05, (1.85, 0.72, z), (1.50, 0.74, z), "brazos")]:
        P("pilotos", f"Piloto — {nom}", "Maniquí de 1.75 m en posición real de manejo",
          6, "#64748b", exp=(0, 0.9, 0), t="cil", **eje_de(a, b), r=r)
    P("pilotos", "Piloto — cabeza", "Cabeza 5 cm por debajo del arco principal", 6,
      "#64748b", exp=(0, 0.9, 0), t="esfera", pos=R4(1.90, 0.92, z), r=0.11)
piloto(+0.30); piloto(-0.30)

# ============================================================================
# 11. CARROCERÍA
# ============================================================================
ESTACIONES = [
    (0.00, 0.34, 0.30, 0.42), (0.22, 0.56, 0.17, 0.52), (0.55, 0.80, 0.13, 0.60),
    (0.85, 0.76, 0.12, 0.68), (1.10, 0.74, 0.12, 0.78), (1.34, 0.72, 0.12, 1.04),
    (1.70, 0.74, 0.12, 1.10), (2.02, 0.76, 0.12, 1.09), (2.35, 0.80, 0.13, 0.92),
    (2.68, 0.81, 0.15, 0.72), (3.00, 0.52, 0.24, 0.54),
]
def anillo(x, hw, y0, y1, n=32, sup=2.7):
    cy, ry = (y0 + y1) / 2, (y1 - y0) / 2
    return [[x, cy + ry * np.sign(np.sin(2*np.pi*k/n)) * abs(np.sin(2*np.pi*k/n))**(2/sup),
             hw * np.sign(np.cos(2*np.pi*k/n)) * abs(np.cos(2*np.pi*k/n))**(2/sup)]
            for k in range(n)]
tris, anillos = [], [anillo(*e) for e in ESTACIONES]
for i in range(len(anillos) - 1):
    A, B = anillos[i], anillos[i + 1]
    for k in range(len(A)):
        k2 = (k + 1) % len(A)
        tris += A[k] + B[k] + B[k2] + A[k] + B[k2] + A[k2]
for extremo, ring in [(0, anillos[0]), (1, anillos[-1])]:
    cx = [sum(p[j] for p in ring) / len(ring) for j in range(3)]
    for k in range(len(ring)):
        k2 = (k + 1) % len(ring)
        tris += (cx + ring[k2] + ring[k]) if extremo == 0 else (cx + ring[k] + ring[k2])
P("carroceria", "Carrocería", "10 paneles independientes de fibra sándwich sobre molde de "
  "espuma CNC · estilo i8 × 33 Stradale · un panel chocado se re-fabrica por su archivo",
  7, "#3b82f6", exp=(0, 1.2, 0), t="malla", tris=[round(v, 4) for v in tris])

# ============================================================================
# 12. METADATOS
# ============================================================================
SISTEMAS = [
    ("chasis", "Chasis y cartelas", "#aab2bb"), ("nodos", "Nodos generativos", "#c084fc"),
    ("susp_del", "Suspensión delantera", "#f97316"),
    ("susp_tras", "Suspensión trasera", "#fb923c"),
    ("frenos", "Frenos", "#f59e0b"), ("direccion", "Dirección", "#22c55e"),
    ("ruedas", "Ruedas", "#1a1e24"), ("motores", "Motores de cubo", "#4b5563"),
    ("bateria", "Caja de batería", "#16a34a"), ("celdas", "Celdas (30)", "#15803d"),
    ("electrico", "Eléctrico", "#0ea5e9"), ("cabina", "Cabina", "#2f3540"),
    ("pilotos", "Pilotos (escala)", "#64748b"), ("carroceria", "Carrocería", "#3b82f6"),
]
PASOS = [
    (1, "Chasis soldado", "F1",
     "Cortar los 73 tubos con la lista de corte y armar sobre el jig. Los arcos van "
     "rolados con mandril, nunca con rodillos. Soldar por puntos todo primero y cerrar "
     "cordones en cruz para no jalar la geometría.",
     ["Verificar diagonales del jig antes de soldar nada",
      "Los 9 tubos de PTR 25×25×1.5 son los diagonales — pared delgada, menos amperaje",
      "Cartelas de láser en torres de coilover y pivotes traseros",
      "Inspección de soldadura por un soldador con experiencia ANTES de seguir"]),
    (2, "Suspensión", "F1",
     "Horquillas delanteras y brazos tirados traseros, manguetas, coilovers y las placas "
     "de torque del QS273. Al terminar, el carro se para en sus cuatro ruedas.",
     ["Rótulas cónicas: verificar el cono contra la mangueta antes de comprar",
      "Placas de torque: sándwich que abraza la punta del PTR, 4 × M12 10.9 a 95 N·m",
      "Las camisas van soldadas a través del PTR o el apriete lo aplasta",
      "Toe-in trasero de 1-2 mm con calzas en el pivote"]),
    (3, "Frenos y dirección", "F1",
     "Discos, calipers, líneas y pedalera con doble bomba y barra de balance. Cremallera "
     "en su posición optimizada, columna y volante.",
     ["Reparto 57% adelante / 43% atrás en la barra de balance",
      "Cremallera con barrenos ovalados: ±5 mm de altura duplican el bump steer",
      "Purgar hasta que el pedal quede firme; verificar topes de giro sin que pegue",
      "Rueda interior no debe pasar de 40° ni tocar el brazo o el rin"]),
    (4, "Ruedas y motores", "F1",
     "Rines y llantas. Los QS273 van dentro de los rines traseros de 14\". Fin de F1: el "
     "carro rueda, frena y dirige empujado.",
     ["Confirmar con QS Motor el eje libre ≥84 mm ANTES de haber cortado las placas",
      "Los cables de fase salen por dentro del eje: no pellizcarlos al montar",
      "Apretar tuerca de eje y verificar que la rueda gire sin juego lateral"]),
    (5, "Tren eléctrico", "F2",
     "Caja de batería con las 30 celdas, BMS, contactor y fusible; controladores en la "
     "nariz. Los dos pasos delicados (armado del BMS y primera energización) con técnico.",
     ["96 V SÍ es peligroso: herramienta aislada, sin joyería, nunca solo",
      "Celdas del mismo lote y balanceadas antes de cerrar el pack",
      "Precarga antes del contactor principal, siempre",
      "Limitar el regen a 0.24g en los controladores: seguridad, no comodidad"]),
    (6, "Cabina", "F2",
     "Butacas, arneses de 4 puntos anclados a la barra de cinturones y tablet. "
     "Fin de F2: la mula anda sola en el patio.",
     ["Arneses a la barra del frame, nunca a lámina",
      "Extintor ABC a bordo y al alcance sentado"]),
    (7, "Carrocería", "F4",
     "Espuma CNC, fibra sándwich y los 10 paneles con Dzus. Va al final a propósito: "
     "el carro debe funcionar feo antes de ser bonito.",
     ["Toda la mecánica probada en F3 con el chasis desnudo, cuando todo está accesible",
      "Un panel dañado se re-fabrica por su archivo CAD"]),
]
por_sis = {}
for p in PIEZAS:
    por_sis[p["sis"]] = por_sis.get(p["sis"], 0) + 1

DATA = {
    "piezas": PIEZAS, "voxels": VOXELS, "perfiles": PERFILES,
    "sistemas": [{"id": i, "nom": n, "col": c, "n": por_sis.get(i, 0)} for (i, n, c) in SISTEMAS],
    "pasos": [{"n": n, "tit": t, "fase": f, "desc": d, "chk": c} for (n, t, f, d, c) in PASOS],
    "stats": {"n_piezas": len(PIEZAS), "n_tubos": len(ac.elems),
              "masa_chasis": round(ac.masa_acero, 1), "ktors": round(ac.K_tors),
              "largo": 3.0, "ancho": 1.66, "alto": 1.10, "batalla": 2.13, "masa_total": 690},
}

TEMPLATE = open(os.path.join(HERE, "_visor_carro.html"), encoding="utf-8").read()
out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "carro-completo-3d.html")
html = TEMPLATE.replace("__DATA__", json.dumps(DATA, separators=(",", ":")))
open(out, "w", encoding="utf-8").write(html)

print(f"OK  {len(PIEZAS)} piezas · {len(SISTEMAS)} sistemas · {len(PASOS)} pasos")
print(f"    perfiles DXF leidos: {', '.join(PERFILES)}")
for (i, n, c) in SISTEMAS:
    print(f"    {n:26s} {por_sis.get(i,0):4d}")
print(f"OK  {os.path.normpath(out)}  ({len(html)//1024} KB)")
