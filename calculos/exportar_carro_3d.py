# -*- coding: utf-8 -*-
"""
EL CARRO COMPLETO EN 3D — todo lo diseñado, junto y armable.

Junta en un solo modelo todo lo que salió de los entregables de ingeniería, cada
pieza en sus coordenadas reales:

  chasis (73 tubos, secciones optimizadas)      analisis_chasis.py / optimizar_chasis.py
  nodos generativos (5 tipos, 12 piezas)        nodo_generativo.py
  suspensión delantera (horquillas, manguetas)  suspension_delantera.py
  suspensión trasera (brazos tirados)           suspension_trasera.py
  placas de torque del QS273                    placa_torque.py
  frenos (4 discos, calipers, pedalera)         frenos.py
  dirección (cremallera, tie rods, columna)     direccion.py
  ruedas y motores de cubo                      spec del kit QS273
  batería (30 celdas en su cuna)                doc maestro
  cabina (butacas, arneses, pilotos)            doc maestro

Genera un visor Three.js autocontenido con:
  - explorador por sistema (encender/apagar cada uno)
  - secuencia de armado paso a paso (lo que se monta en cada etapa)
  - vista explotada con deslizador
  - clic en cualquier pieza para ver qué es, su spec y de qué documento salió
  - carrocería envolvente translúcida para ver dónde queda todo

Uso:  python exportar_carro_3d.py [salida.html]
"""
import json, sys, os
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
CAD = os.path.join(HERE, "..", "cad")
sys.path.insert(0, HERE)
import analisis_chasis as ac

V = lambda *a: [round(float(x), 4) for x in a]

# ============================================================================
# 1. PUNTOS DUROS (de los entregables — no se re-teclean valores inventados)
# ============================================================================
# --- suspensión delantera (suspension_delantera.py) ---
LA1 = np.array([0.35, 0.200, 0.50]);  LA2 = np.array([0.75, 0.200, 0.55])
UA1 = np.array([0.35, 0.417, 0.50]);  UA2 = np.array([0.75, 0.417, 0.55])
LBJ = np.array([0.545, 0.190, 0.710]); UBJ = np.array([0.565, 0.425, 0.685])
TR  = np.array([0.430, 0.198, 0.695])
RACK = np.array([0.370, 0.207, 0.504])          # posición optimizada (direccion.py)
WD  = np.array([0.55, 0.2876, 0.75])            # centro de rueda delantera
SHK_SUP_D = np.array([0.75, 0.48, 0.55]); SHK_INF_D = np.array([0.58, 0.215, 0.66])
R_DEL, ANCHO_LL = 0.2876, 0.177

# --- suspensión trasera (suspension_trasera.py) ---
PIV = np.array([2.28, 0.16, 0.552])
EJE = np.array([2.68, 0.3005, 0.76])
SHK_SUP_T = np.array([2.58, 0.712, 0.425])
SHK_INF_T = PIV + 0.80 * (EJE - PIV)
R_TRAS = 0.3005
R_MOTOR, W_MOTOR = 0.175, 0.130                  # carcasa QS273 ~Ø350
R_DISCO, W_DISCO = 0.110, 0.005

# --- placas de torque (placa_torque.py) ---
# El brazo NO llega al centro de rueda: termina antes del motor y el eje del QS273
# salva el resto en voladizo. De adentro hacia afuera, en z:
#   placa interior · placa exterior · doblador · disco · cara interna del motor
GAP_PLACAS, T_PLACA = 0.050, 0.008
Z_MOTOR_INT = EJE[2] - W_MOTOR / 2            # cara interna del motor: 0.695
Z_DISCO = Z_MOTOR_INT - 0.012                 # el disco monta en la tapa giratoria
Z_PLACA_EXT = Z_MOTOR_INT - 0.030             # placa exterior (la del caliper)
Z_PLACA_INT = Z_PLACA_EXT - GAP_PLACAS        # placa interior
Z_PUNTA_BRAZO = (Z_PLACA_EXT + Z_PLACA_INT) / 2   # el PTR va entre las dos placas
PUNTA = np.array([EJE[0], EJE[1], Z_PUNTA_BRAZO])
# largo de eje libre que esto exige (el dato crítico a confirmar con QS Motor)
EJE_LIBRE_REQ = Z_MOTOR_INT - Z_PLACA_INT + T_PLACA / 2

# ============================================================================
# 2. CONSTRUCTOR DE PIEZAS
# ============================================================================
PIEZAS = []
def pieza(sistema, nombre, spec, paso, color, **geo):
    p = dict(id=len(PIEZAS), sis=sistema, nom=nombre, spec=spec, paso=paso, col=color)
    p.update(geo)
    PIEZAS.append(p)
    return p

def tubo(sistema, nombre, spec, paso, color, a, b, w=None, r=None):
    g = dict(t="tubo_r", a=V(*a), b=V(*b), r=r) if r else \
        dict(t="tubo_c", a=V(*a), b=V(*b), w=w)
    return pieza(sistema, nombre, spec, paso, color, **g)

def cil(sistema, nombre, spec, paso, color, a, b, r):
    return pieza(sistema, nombre, spec, paso, color, t="cil", a=V(*a), b=V(*b), r=r)

def caja(sistema, nombre, spec, paso, color, pos, size, yaw=0.0):
    return pieza(sistema, nombre, spec, paso, color, t="caja", pos=V(*pos),
                 size=V(*size), yaw=round(float(yaw), 4))

def espejo(p):
    """Devuelve los mismos argumentos con z invertida (lado derecho)."""
    return np.array([p[0], p[1], -p[2]])

# ============================================================================
# 3. CHASIS — 73 tubos con las secciones ya optimizadas
# ============================================================================
COL_ACERO = "#b7bfc7"
for e in ac.elems:
    a, b = ac.NODES[e["a"]], ac.NODES[e["b"]]
    nom = e["sec"]["nombre"]
    if nom.startswith("RED"):
        tubo("chasis", f"Tubo {e['a']}–{e['b']}",
             f"{nom} · célula de seguridad · {e['L']*1000:.0f} mm", 1, "#e06c75",
             a, b, r=0.02225)
    else:
        lado = float(nom.split("x")[0].split()[1]) / 1000.0
        col = "#8b949e" if e["tag"] == "tors" else COL_ACERO
        tubo("chasis", f"Tubo {e['a']}–{e['b']}",
             f"{nom} · {e['tag']} · {e['L']*1000:.0f} mm", 1, col, a, b, w=lado)

# --- nodos generativos ---
COLOCACION = [
    ("susp_del",  "nodo-suspension-datos.json", "#fb923c",
     "Torre de coilover delantera — le llegan 5 tubos y la carga de la rueda",
     ["fx_hiL", "fx_hiR"]),
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
for tipo, fname, color, desc, juntas in COLOCACION:
    nd = json.load(open(os.path.join(CAD, fname), encoding="utf-8"))
    VOXELS[tipo] = {"nelx": nd["nelx"], "nely": nd["nely"], "nelz": nd["nelz"],
                    "vox": nd["vox"]}
    for j in juntas:
        pieza("nodos", f"Nodo generativo «{tipo}»", desc, 1, color,
              t="voxel", tipo=tipo, pos=V(*ac.NODES[j]), mir=j.endswith("R"))

# ============================================================================
# 4. SUSPENSIÓN DELANTERA
# ============================================================================
COL_BRAZO, COL_SHOCK, COL_RESORTE = "#f97316", "#a78bfa", "#facc15"
for s in (1, -1):
    m = (lambda p: p if s > 0 else espejo(p))
    lado = "izq" if s > 0 else "der"
    tubo("susp_del", f"Horquilla inferior delantera ({lado}) — tubo delantero",
         "Tubo redondo 25.4×2.1 · 205 mm centro a centro", 2, COL_BRAZO,
         m(LA1), m(LBJ), r=0.0127)
    tubo("susp_del", f"Horquilla inferior delantera ({lado}) — tubo trasero",
         "Tubo redondo 25.4×2.1 · 250 mm centro a centro", 2, COL_BRAZO,
         m(LA2), m(LBJ), r=0.0127)
    tubo("susp_del", f"Horquilla superior delantera ({lado}) — tubo delantero",
         "Tubo redondo 25.4×2.1", 2, COL_BRAZO, m(UA1), m(UBJ), r=0.0127)
    tubo("susp_del", f"Horquilla superior delantera ({lado}) — tubo trasero",
         "Tubo redondo 25.4×2.1", 2, COL_BRAZO, m(UA2), m(UBJ), r=0.0127)
    cil("susp_del", f"Mangueta delantera ({lado})",
        "Donante ATV 300 · camber −1° · caster 4.9° · KPI 6.1°", 2, "#9aa4af",
        m(LBJ), m(UBJ), 0.021)
    cil("susp_del", f"Husillo delantero ({lado})",
        "Eje de maza del donante", 2, "#9aa4af",
        m(WD + np.array([0, 0, -0.05 * s])), m(WD + np.array([0, 0, 0.03 * s])), 0.017)
    cil("susp_del", f"Coilover delantero ({lado})",
        "Resorte 270 lb/in · ojo a ojo 334 mm · carrera 81 mm · ζ 0.5-0.7", 2,
        COL_RESORTE, m(SHK_INF_D), m(SHK_SUP_D), 0.032)
    cil("susp_del", f"Brazo de dirección ({lado})",
        "En la mangueta del donante · 117 mm · da +87% de Ackermann", 3, "#4ade80",
        m(LBJ), m(TR), 0.011)
    cil("susp_del", f"Tie rod ({lado})",
        "Tubo roscado der/izq + 2 rótulas · ajusta convergencia sin desmontar", 3,
        "#4ade80", m(RACK), m(TR), 0.010)

# ============================================================================
# 5. SUSPENSIÓN TRASERA + PLACAS DE TORQUE
# ============================================================================
for s in (1, -1):
    m = (lambda p: p if s > 0 else espejo(p))
    lado = "izq" if s > 0 else "der"
    tubo("susp_tras", f"Brazo tirado ({lado})",
         "PTR 70×50×4 · 504 mm · FS 2.4 · motion ratio 0.68 — termina antes del motor: "
         "el eje del QS273 salva el resto en voladizo", 2, COL_BRAZO,
         m(PIV), m(PUNTA), w=0.050)
    cil("susp_tras", f"Eje del QS273 ({lado})",
        f"Ø20 con caras planas a 16 mm · necesita ≥{EJE_LIBRE_REQ*1000:.0f} mm libres del "
        "lado interior — CONFIRMAR con QS Motor antes de cortar", 4, "#e5e7eb",
        m(np.array([EJE[0], EJE[1], Z_PLACA_INT - 0.012])), m(EJE), 0.010)
    cil("susp_tras", f"Buje de pivote trasero ({lado})",
        "Poliuretano Ø16 + manga de acero, base 150 mm", 2, "#9aa4af",
        m(PIV + np.array([0, 0, 0.04 * s])), m(PIV - np.array([0, 0, 0.04 * s])), 0.022)
    cil("susp_tras", f"Coilover trasero ({lado})",
        "Resorte 351 lb/in · ~590 mm extendido · carrera ≥108 mm · 7,358 N en bache 3g",
        2, COL_RESORTE, m(SHK_INF_T), m(SHK_SUP_T), 0.034)
    # placas de torque: sándwich que abraza la punta del brazo
    for zpl, nom, spec, alto in [
            (Z_PLACA_EXT, "Placa de torque exterior",
             "Acero 8 mm, corte láser · 0.69 kg · FS 2.3 · lleva integrada la ménsula del "
             "caliper", 0.158),
            (Z_PLACA_INT, "Placa de torque interior",
             "Acero 8 mm, corte láser · 0.58 kg · FS 2.8 · con la exterior forma el par que "
             "toma el momento de vuelco del motor en voladizo", 0.092)]:
        c = np.array([EJE[0] - 0.050, EJE[1], zpl])
        caja("susp_tras", f"{nom} ({lado})", spec, 2, "#38bdf8",
             m(c), (0.143, alto, T_PLACA))
        cil("susp_tras", f"Doblador del cubo ({lado}, {nom.split()[-1]})",
            "Anillo Ø56 de acero 8 mm soldado alrededor del eje · sube el FS de "
            "aplastamiento de 1.1 a 2.2", 2, "#0ea5e9",
            m(np.array([EJE[0], EJE[1], zpl + 0.004 * s])),
            m(np.array([EJE[0], EJE[1], zpl + 0.012 * s])), 0.028)

# ============================================================================
# 6. RUEDAS, MOTORES DE CUBO Y FRENOS
# ============================================================================
COL_LLANTA, COL_RIN, COL_MOTOR, COL_DISCO = "#14181d", "#9aa4af", "#5b6470", "#c9d1d9"
for (cx, R, rin_pulg, llanta, trasera) in [
        (WD[0], R_DEL, 13, "175/70R13", False),
        (EJE[0], R_TRAS, 14, "175/70R14", True)]:
    for s in (1, -1):
        zc = (EJE[2] if trasera else WD[2]) * s
        lado = "izq" if s > 0 else "der"
        pos = "trasera" if trasera else "delantera"
        cil("ruedas", f"Llanta {pos} ({lado})",
            f"{llanta} · Ø{R*2000:.0f} mm · perfil 70 para absorber topes", 4,
            COL_LLANTA, (cx, R, zc - ANCHO_LL / 2 * s), (cx, R, zc + ANCHO_LL / 2 * s), R)
        cil("ruedas", f"Rin {pos} ({lado})",
            f"Rin {rin_pulg}\"" + (" — versión desmontable de carro del QS273" if trasera
                                   else " — de deshuesadero"), 4,
            COL_RIN, (cx, R, zc - ANCHO_LL / 2 * s), (cx, R, zc + ANCHO_LL / 2 * s),
            rin_pulg * 0.0127)
        if trasera:
            cil("motores", f"Motor de cubo QS273 ({lado})",
                "8 kW · 96 V · 350 N·m · carcasa Ø350 · 27 kg de masa NO suspendida", 4,
                COL_MOTOR, (cx, R, zc - W_MOTOR / 2 * s), (cx, R, zc + W_MOTOR / 2 * s),
                R_MOTOR)
        # freno
        zd = Z_DISCO * s if trasera else zc - 0.055 * s
        cil("frenos", f"Disco de freno {pos} ({lado})",
            ("Ø220 — lo trae el QS273" if trasera else
             "Ø220×5 macizo — el del donante ATV NO alcanza para 690 kg"), 3,
            COL_DISCO, (cx, R, zd - W_DISCO / 2), (cx, R, zd + W_DISCO / 2), R_DISCO)
        ang = np.radians(55 if trasera else 120)
        cpos = (cx + R_DISCO * 0.86 * np.cos(ang), R + R_DISCO * 0.86 * np.sin(ang), zd)
        caja("frenos", f"Caliper {pos} ({lado})",
             ("Con palanca de freno de mano integrada · pistón ≥740 mm²" if trasera
              else "Pistón ≥938 mm² (Ø35 equivalente) · de compacto o moto deportiva"),
             3, "#f59e0b", cpos, (0.075, 0.055, 0.050))

# ============================================================================
# 7. DIRECCIÓN
# ============================================================================
PINON = np.array([RACK[0], RACK[1], 0.16])
VOL = np.array([1.44, 0.76, 0.30])
INT = np.array([1.02, 0.50, 0.24])
cil("direccion", "Cremallera manual", "De compacto, sin servo · 2.4 vueltas · relación 13:1 · "
    "posición optimizada x=370 z=±504 (da +87% de Ackermann)", 3, "#4ade80",
    RACK, espejo(RACK), 0.024)
cil("direccion", "Columna — tramo bajo", "Con cruceta al piñón; ángulos parecidos y en fase o "
    "la dirección pulsa", 3, "#9aa4af", PINON, INT, 0.014)
cil("direccion", "Columna — tramo alto", "Preferentemente colapsable: en impacto frontal no "
    "debe empujar el volante al pecho", 3, "#9aa4af", INT, VOL, 0.014)
cil("direccion", "Volante", "Ø330 mm · 34 N para girar parado en seco, 6 N rodando", 3,
    "#2f3742", VOL - np.array([0.02, 0, 0]), VOL + np.array([0.02, 0, 0]), 0.165)

# --- pedalera ---
for i, (dx, nom, spec, col) in enumerate([
        (0.00, "Pedal de freno", "Relación 6.0:1 · 428 N de pie para 1g sin booster", "#f59e0b"),
        (0.16, "Pedal de acelerador", "Tipo hall, sin cable", "#4ade80")]):
    caja("frenos", nom, spec, 3, col, (1.05 + dx, 0.30, 0.22 + dx * 0.9),
         (0.035, 0.16, 0.055))
for s in (1, -1):
    caja("frenos", f"Bomba de freno ({'del.' if s > 0 else 'tras.'})",
         "Ø14.3 mm (9/16\") · doble circuito con barra de balance ajustable", 3, "#f59e0b",
         (0.98, 0.26, 0.06 * s), (0.14, 0.05, 0.05))

# ============================================================================
# 8. BATERÍA Y ELÉCTRICO
# ============================================================================
BAT_X0, BAT_X1, BAT_Y0, BAT_HW, BAT_H = 2.11, 2.63, 0.175, 0.47, 0.20
caja("bateria", "Caja de batería", "30 celdas LiFePO4 105 Ah en serie · 96 V nominal · "
     "10 kWh · ~90 kg · acero con compresión y venteo", 5, "#22c55e",
     ((BAT_X0 + BAT_X1) / 2, BAT_Y0 + BAT_H / 2, 0), (BAT_X1 - BAT_X0, BAT_H, BAT_HW * 2))
# celdas individuales (2 filas de 15)
for fila in range(2):
    for k in range(15):
        cx = BAT_X0 + 0.028 + k * (BAT_X1 - BAT_X0 - 0.05) / 14
        cz = (-1 if fila else 1) * 0.21
        caja("celdas", f"Celda {fila*15+k+1}/30", "LiFePO4 prismática 105 Ah, 3.2 V · "
             "todas del mismo lote o el pack vale lo que su peor celda", 5, "#16a34a",
             (cx, BAT_Y0 + BAT_H / 2, cz), (0.030, 0.165, 0.36))
caja("electrico", "BMS", "30S · 250-300 A continuos (menos capa los motores) · Bluetooth", 5,
     "#0ea5e9", (2.66, 0.30, 0.0), (0.10, 0.09, 0.28))
for s in (1, -1):
    caja("electrico", f"Controlador ({'izq' if s > 0 else 'der'})",
         "APT96600 / Fardriver ND96530 · regen configurable — van en la nariz para "
         "compensar el sesgo de peso trasero", 5, "#0ea5e9",
         (0.22, 0.33, 0.15 * s), (0.22, 0.10, 0.14))
caja("electrico", "Contactor + fusible 400 A", "Con precarga, paro de emergencia y "
     "desconectador de servicio", 5, "#0ea5e9", (0.20, 0.47, 0.0), (0.16, 0.10, 0.18))
caja("electrico", "DC-DC 96→12 V", "30 A aislado — no hay batería de 12 V en el carro", 5,
     "#0ea5e9", (0.42, 0.34, 0.0), (0.16, 0.08, 0.16))

# ============================================================================
# 9. CABINA
# ============================================================================
for s in (1, -1):
    z = 0.30 * s
    lado = "izq" if s > 0 else "der"
    caja("cabina", f"Butaca ({lado})", "Comercial atornillada al estribo y al piso", 6,
         "#374151", (1.62, 0.34, z), (0.50, 0.10, 0.46))
    caja("cabina", f"Respaldo ({lado})", "Reclinado 25° — cabeza 5 cm bajo el arco", 6,
         "#374151", (1.93, 0.60, z), (0.12, 0.60, 0.46), yaw=0.0)
caja("cabina", "Tablet del tablero", "Velocímetro GPS + BMS + controladores por Bluetooth", 6,
     "#1f2937", (1.22, 0.70, 0.0), (0.02, 0.16, 0.26))

# --- pilotos (contexto de escala) ---
def piloto(z):
    seg = [(0.13, (1.72, 0.30, z), (1.87, 0.75, z), "torso"),
           (0.09, (1.70, 0.28, z), (1.38, 0.38, z), "muslos"),
           (0.06, (1.38, 0.38, z), (1.16, 0.22, z), "piernas"),
           (0.05, (1.85, 0.72, z), (1.50, 0.72, z), "brazos")]
    for r, a, b, nom in seg:
        cil("pilotos", f"Piloto — {nom}", "Maniquí de 1.75 m en posición real de manejo",
            6, "#64748b", a, b, r)
    pieza("pilotos", "Piloto — cabeza", "Cabeza 5 cm por debajo del arco principal", 6,
          "#64748b", t="esfera", pos=V(1.90, 0.92, z), r=0.11)
piloto(+0.30); piloto(-0.30)

# ============================================================================
# 10. CARROCERÍA ENVOLVENTE (translúcida, solo para ver dónde queda todo)
# ============================================================================
# Secciones a lo largo del carro: (x, semiancho, y_bajo, y_alto)
ESTACIONES = [
    (0.00, 0.34, 0.30, 0.42), (0.22, 0.56, 0.17, 0.52), (0.55, 0.78, 0.13, 0.60),
    (0.85, 0.76, 0.12, 0.68), (1.10, 0.74, 0.12, 0.78), (1.34, 0.72, 0.12, 1.04),
    (1.70, 0.74, 0.12, 1.10), (2.02, 0.76, 0.12, 1.09), (2.35, 0.79, 0.13, 0.92),
    (2.68, 0.78, 0.15, 0.72), (3.00, 0.52, 0.24, 0.54),
]
def anillo(x, hw, y0, y1, n=28, sup=2.6):
    """Superelipse: da una sección con hombros, no un tubo redondo."""
    cy, ry = (y0 + y1) / 2, (y1 - y0) / 2
    pts = []
    for k in range(n):
        th = 2 * np.pi * k / n
        c, s_ = np.cos(th), np.sin(th)
        pts.append([x,
                    cy + ry * np.sign(s_) * abs(s_) ** (2.0 / sup),
                    hw * np.sign(c) * abs(c) ** (2.0 / sup)])
    return pts

tris = []
anillos = [anillo(*e) for e in ESTACIONES]
for i in range(len(anillos) - 1):
    A, B = anillos[i], anillos[i + 1]
    n = len(A)
    for k in range(n):
        k2 = (k + 1) % n
        tris += A[k] + B[k] + B[k2]
        tris += A[k] + B[k2] + A[k2]
for extremo, ring in [(0, anillos[0]), (1, anillos[-1])]:
    cx = [sum(p[j] for p in ring) / len(ring) for j in range(3)]
    n = len(ring)
    for k in range(n):
        k2 = (k + 1) % n
        tris += (cx + ring[k2] + ring[k]) if extremo == 0 else (cx + ring[k] + ring[k2])
pieza("carroceria", "Carrocería", "10 paneles independientes de fibra sándwich sobre espuma "
      "CNC · estilo i8 × 33 Stradale · se re-fabrica un panel por su archivo CAD", 7,
      "#3b82f6", t="malla", tris=[round(v, 4) for v in tris])

# ============================================================================
# 11. METADATOS Y SALIDA
# ============================================================================
SISTEMAS = [
    ("chasis", "Chasis (73 tubos)", "#b7bfc7"),
    ("nodos", "Nodos generativos", "#c084fc"),
    ("susp_del", "Suspensión delantera", "#f97316"),
    ("susp_tras", "Suspensión trasera", "#fb923c"),
    ("frenos", "Frenos", "#f59e0b"),
    ("direccion", "Dirección", "#4ade80"),
    ("ruedas", "Ruedas", "#9aa4af"),
    ("motores", "Motores de cubo", "#5b6470"),
    ("bateria", "Caja de batería", "#22c55e"),
    ("celdas", "Celdas (30)", "#16a34a"),
    ("electrico", "Eléctrico", "#0ea5e9"),
    ("cabina", "Cabina", "#374151"),
    ("pilotos", "Pilotos (escala)", "#64748b"),
    ("carroceria", "Carrocería", "#3b82f6"),
]
PASOS = [
    (1, "Chasis soldado", "Cortar los 73 tubos con la lista de corte, armar sobre el jig y "
        "soldar. Los arcos van rolados con mandril. Inspección de soldadura antes de seguir."),
    (2, "Suspensión", "Horquillas y brazos tirados, manguetas, coilovers y las placas de "
        "torque del QS273. Al terminar el carro ya se para en sus cuatro ruedas."),
    (3, "Frenos y dirección", "Discos, calipers, líneas, pedalera con doble bomba y barra de "
        "balance; cremallera, columna y volante. Purgar y verificar topes de giro."),
    (4, "Ruedas y motores", "Rines y llantas; los QS273 van dentro de los rines traseros. "
        "Fin de F1: el carro rueda, frena y dirige empujado."),
    (5, "Tren eléctrico", "Caja de batería con las 30 celdas, BMS, contactor y fusible, "
        "controladores en la nariz. Los dos pasos delicados con técnico."),
    (6, "Cabina", "Butacas, arneses de 4 puntos y tablet. Fin de F2: la mula anda sola."),
    (7, "Carrocería", "Espuma CNC, fibra sándwich y los 10 paneles con Dzus. F4 — el carro "
        "debe funcionar feo antes de ser bonito."),
]

por_sis = {}
for p in PIEZAS:
    por_sis[p["sis"]] = por_sis.get(p["sis"], 0) + 1

DATA = {
    "piezas": PIEZAS,
    "voxels": VOXELS,
    "sistemas": [{"id": i, "nom": n, "col": c, "n": por_sis.get(i, 0)}
                 for (i, n, c) in SISTEMAS],
    "pasos": [{"n": n, "tit": t, "desc": d} for (n, t, d) in PASOS],
    "stats": {
        "n_piezas": len(PIEZAS),
        "n_tubos": len(ac.elems),
        "masa_chasis": round(ac.masa_acero, 1),
        "ktors": round(ac.K_tors),
        "largo": 3.0, "ancho": 1.66, "alto": 1.10, "batalla": 2.13,
        "masa_total": 690,
    },
}

TEMPLATE = r"""<!DOCTYPE html>
<html lang="es"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>El carro completo en 3D</title>
<style>
 html,body{margin:0;height:100%;background:#0b0e13;overflow:hidden;font-family:system-ui,-apple-system,sans-serif;}
 #app{position:fixed;inset:0}
 .panel{background:#12161ceb;border:1px solid #2a313b;border-radius:12px;padding:11px 13px;color:#c9d1d9;font-size:12px;line-height:1.55;backdrop-filter:blur(8px)}
 #izq{position:fixed;top:12px;left:12px;z-index:10;display:flex;flex-direction:column;gap:9px;width:266px;max-height:calc(100vh - 24px);overflow-y:auto}
 #der{position:fixed;top:12px;right:12px;z-index:10;width:290px;display:flex;flex-direction:column;gap:9px}
 h1{color:#e6edf3;font-size:15px;margin:0 0 3px}
 h2{color:#8b949e;font-size:10.5px;margin:0 0 7px;text-transform:uppercase;letter-spacing:.09em;font-weight:600}
 .sis{display:flex;align-items:center;gap:8px;padding:3.5px 5px;border-radius:6px;cursor:pointer}
 .sis:hover{background:#1c222b}
 .sis.off{opacity:.32}
 .chip{width:11px;height:11px;border-radius:3px;flex:none}
 .sis .n{margin-left:auto;color:#6e7781;font-size:10.5px}
 button{background:#1c222b;color:#c9d1d9;border:1px solid #2a313b;border-radius:7px;padding:6px 10px;font-size:11.5px;cursor:pointer}
 button:hover{background:#252c37}
 button.on{background:#1f6feb;border-color:#1f6feb;color:#fff}
 .row{display:flex;flex-wrap:wrap;gap:5px}
 input[type=range]{width:100%;accent-color:#1f6feb}
 #paso{color:#e6edf3;font-weight:600;font-size:12.5px}
 #pdesc{color:#8b949e;font-size:11.5px;margin-top:5px}
 #info{display:none}
 #info .t{color:#e6edf3;font-weight:600;font-size:13px}
 #info .s{color:#8b949e;font-size:11.5px;margin-top:5px}
 #info .sis-tag{display:inline-block;margin-top:7px;padding:2px 7px;border-radius:5px;font-size:10.5px;background:#1c222b}
 #hint{position:fixed;bottom:12px;left:50%;transform:translateX(-50%);z-index:10;color:#6e7781;font-size:11px;background:#12161ceb;border:1px solid #2a313b;border-radius:9px;padding:6px 14px}
 b{color:#e6edf3}
</style></head><body>
<div id="app"></div>
<div id="izq">
 <div class="panel">
  <h1>🏎️ El carro completo</h1>
  <div id="stats"></div>
 </div>
 <div class="panel">
  <h2>Secuencia de armado</h2>
  <div id="paso"></div><div id="pdesc"></div>
  <input type="range" id="rpaso" min="1" max="7" value="7" style="margin-top:9px">
 </div>
 <div class="panel">
  <h2>Vista</h2>
  <div class="row">
   <button id="brot" class="on">⟳ Girar</button>
   <button id="bcar">🎨 Carrocería</button>
   <button id="bxray">🩻 Rayos X</button>
  </div>
  <h2 style="margin-top:11px">Vista explotada</h2>
  <input type="range" id="rexp" min="0" max="100" value="0">
 </div>
</div>
<div id="der">
 <div class="panel">
  <h2>Sistemas — clic para ocultar</h2>
  <div id="lista"></div>
 </div>
 <div class="panel" id="info">
  <div class="t"></div><div class="s"></div><div class="sis-tag"></div>
 </div>
</div>
<div id="hint">Clic en cualquier pieza para ver qué es · arrastra para girar · rueda para acercar</div>

<script type="importmap">
{"imports":{"three":"https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js",
"three/addons/":"https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/"}}
</script>
<script type="module">
import * as THREE from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {RoomEnvironment} from 'three/addons/environments/RoomEnvironment.js';
const D = __DATA__;

const renderer = new THREE.WebGLRenderer({antialias:true});
renderer.setPixelRatio(Math.min(devicePixelRatio,2));
renderer.setSize(innerWidth,innerHeight);
renderer.shadowMap.enabled=true; renderer.shadowMap.type=THREE.PCFSoftShadowMap;
renderer.toneMapping=THREE.ACESFilmicToneMapping; renderer.toneMappingExposure=1.05;
document.getElementById('app').appendChild(renderer.domElement);

const scene=new THREE.Scene();
scene.background=new THREE.Color(0x0b0e13);
scene.fog=new THREE.Fog(0x0b0e13,9,26);
scene.environment=new THREE.PMREMGenerator(renderer).fromScene(new RoomEnvironment(),0.04).texture;
const camera=new THREE.PerspectiveCamera(36,innerWidth/innerHeight,0.05,120);
camera.position.set(4.9,2.0,3.7);
const controls=new OrbitControls(camera,renderer.domElement);
controls.target.set(1.5,0.45,0); controls.enableDamping=true;
controls.autoRotate=true; controls.autoRotateSpeed=0.85;
scene.add(new THREE.HemisphereLight(0xdce8ff,0x141820,0.75));
const sun=new THREE.DirectionalLight(0xfff4e6,2.0);
sun.position.set(4.5,7,3.5); sun.castShadow=true;
sun.shadow.mapSize.set(2048,2048); sun.shadow.camera.left=-4; sun.shadow.camera.right=4;
sun.shadow.camera.top=4; sun.shadow.camera.bottom=-4; sun.shadow.bias=-0.0004;
scene.add(sun);
scene.add(new THREE.DirectionalLight(0x88aaff,0.45).translateX(-5));
const piso=new THREE.Mesh(new THREE.PlaneGeometry(40,40),new THREE.ShadowMaterial({opacity:0.42}));
piso.rotation.x=-Math.PI/2; piso.receiveShadow=true; scene.add(piso);
scene.add(new THREE.GridHelper(24,48,0x1f2630,0x161b22));

// ---------- geometría de los nodos generativos (voxels -> caras expuestas) ----------
const CARAS=[[[1,0,0],[[1,0,0],[1,1,0],[1,1,1],[1,0,1]]],[[-1,0,0],[[0,0,0],[0,0,1],[0,1,1],[0,1,0]]],
[[0,1,0],[[0,1,0],[0,1,1],[1,1,1],[1,1,0]]],[[0,-1,0],[[0,0,0],[1,0,0],[1,0,1],[0,0,1]]],
[[0,0,1],[[0,0,1],[1,0,1],[1,1,1],[0,1,1]]],[[0,0,-1],[[0,0,0],[0,1,0],[1,1,0],[1,0,0]]]];
const cacheVox={};
function geomVoxel(tipo,mir){
 const k=tipo+(mir?'R':'L'); if(cacheVox[k])return cacheVox[k];
 const nd=D.voxels[tipo], s=0.15/Math.max(nd.nelx,nd.nely,nd.nelz);
 const cx=nd.nelx/2,cy=nd.nely/2,cz=nd.nelz/2;
 const set=new Set(); for(const v of nd.vox) set.add(v[0]+v[1]*64+v[2]*4096);
 const hay=(x,y,z)=>x>=0&&y>=0&&z>=0&&x<nd.nelx&&y<nd.nely&&z<nd.nelz&&set.has(x+y*64+z*4096);
 const P=[],push=p=>P.push((p[0]-cx)*s,(p[1]-cy)*s,(mir?-(p[2]-cz):(p[2]-cz))*s);
 for(const v of nd.vox){const[ix,iy,iz]=v;
  for(const[d0,q0] of CARAS){ if(hay(ix+d0[0],iy+d0[1],iz+d0[2]))continue;
   const q=q0.map(o=>[ix+o[0],iy+o[1],iz+o[2]]);
   if(mir){push(q[0]);push(q[2]);push(q[1]);push(q[0]);push(q[3]);push(q[2]);}
   else{push(q[0]);push(q[1]);push(q[2]);push(q[0]);push(q[2]);push(q[3]);}}}
 const g=new THREE.BufferGeometry();
 g.setAttribute('position',new THREE.Float32BufferAttribute(P,3)); g.computeVertexNormals();
 return cacheVox[k]=g;
}

// ---------- construir todas las piezas ----------
const V3=a=>new THREE.Vector3(a[0],a[1],a[2]);
const CENTRO=new THREE.Vector3(1.5,0.45,0);
const objetos=[];
function entre(a,b,geoFn){
 const A=V3(a),B=V3(b),d=new THREE.Vector3().subVectors(B,A),L=d.length();
 const m=new THREE.Mesh(geoFn(L),null);
 m.position.copy(A).addScaledVector(d,0.5);
 m.quaternion.setFromUnitVectors(new THREE.Vector3(0,1,0),d.clone().normalize());
 return m;
}
for(const p of D.piezas){
 let mesh;
 if(p.t==='tubo_c') mesh=entre(p.a,p.b,L=>new THREE.BoxGeometry(p.w,L,p.w));
 else if(p.t==='tubo_r'||p.t==='cil') mesh=entre(p.a,p.b,L=>new THREE.CylinderGeometry(p.r,p.r,L,20));
 else if(p.t==='caja'){mesh=new THREE.Mesh(new THREE.BoxGeometry(...p.size));mesh.position.set(...p.pos);if(p.yaw)mesh.rotation.y=p.yaw;}
 else if(p.t==='esfera'){mesh=new THREE.Mesh(new THREE.SphereGeometry(p.r,18,14));mesh.position.set(...p.pos);}
 else if(p.t==='voxel'){mesh=new THREE.Mesh(geomVoxel(p.tipo,p.mir));mesh.position.set(...p.pos);}
 else if(p.t==='malla'){const g=new THREE.BufferGeometry();
  g.setAttribute('position',new THREE.Float32BufferAttribute(p.tris,3));g.computeVertexNormals();
  mesh=new THREE.Mesh(g);}
 else continue;
 const esCar=p.sis==='carroceria', esPil=p.sis==='pilotos';
 mesh.material=new THREE.MeshStandardMaterial({
  color:new THREE.Color(p.col),
  metalness:esCar||esPil?0.1:(p.sis==='chasis'||p.sis==='ruedas'?0.8:0.55),
  roughness:esCar?0.25:(esPil?0.85:0.38),
  flatShading:p.t==='voxel',
  transparent:esCar||esPil, opacity:esCar?0.13:(esPil?0.55:1),
  side:esCar?THREE.DoubleSide:THREE.FrontSide, depthWrite:!esCar});
 mesh.castShadow=!esCar; mesh.receiveShadow=!esCar;
 mesh.userData=p;
 // dirección de explosión: radial desde el centro del carro
 const base=mesh.position.clone();
 const dir=base.clone().sub(CENTRO); if(dir.length()<0.01)dir.set(0,1,0);
 dir.normalize().multiplyScalar(p.sis==='ruedas'||p.sis==='motores'?1.5:1.0);
 scene.add(mesh);
 objetos.push({mesh,p,base,dir});
}

// ---------- UI ----------
const S=D.stats;
document.getElementById('stats').innerHTML=
 `<b>${S.n_piezas} piezas</b> en sus coordenadas reales<br>`+
 `${S.largo} m × ${S.ancho} m × ${S.alto} m · batalla ${S.batalla} m<br>`+
 `Chasis: <b>${S.n_tubos} tubos</b>, ${S.masa_chasis} kg, ${S.ktors.toLocaleString()} N·m/°<br>`+
 `Masa objetivo del carro: <b>${S.masa_total} kg</b> con 2 ocupantes`;

const apagados=new Set();
const lista=document.getElementById('lista');
for(const s of D.sistemas){
 const row=document.createElement('div'); row.className='sis';
 row.innerHTML=`<span class="chip" style="background:${s.col}"></span><span>${s.nom}</span><span class="n">${s.n}</span>`;
 row.onclick=()=>{ row.classList.toggle('off');
  if(apagados.has(s.id))apagados.delete(s.id); else apagados.add(s.id); refrescar(); };
 lista.appendChild(row);
}
// la carrocería arranca oculta: estorba para ver la mecánica
apagados.add('carroceria');
lista.children[D.sistemas.findIndex(s=>s.id==='carroceria')].classList.add('off');

let pasoMax=7;
const rp=document.getElementById('rpaso');
function pintarPaso(){
 const info=D.pasos.find(x=>x.n===pasoMax);
 document.getElementById('paso').textContent=`Paso ${info.n} de 7 — ${info.tit}`;
 document.getElementById('pdesc').textContent=info.desc;
}
rp.oninput=()=>{pasoMax=+rp.value;pintarPaso();refrescar();};
pintarPaso();

let explosion=0;
document.getElementById('rexp').oninput=e=>{explosion=+e.target.value/100;refrescar();};

function refrescar(){
 for(const o of objetos){
  o.mesh.visible=!apagados.has(o.p.sis)&&o.p.paso<=pasoMax;
  o.mesh.position.copy(o.base).addScaledVector(o.dir,explosion*0.85);
 }
}
refrescar();

document.getElementById('brot').onclick=e=>{controls.autoRotate=!controls.autoRotate;e.target.classList.toggle('on',controls.autoRotate);};
document.getElementById('bcar').onclick=e=>{
 if(apagados.has('carroceria'))apagados.delete('carroceria');else apagados.add('carroceria');
 e.target.classList.toggle('on',!apagados.has('carroceria'));
 lista.children[D.sistemas.findIndex(s=>s.id==='carroceria')].classList.toggle('off',apagados.has('carroceria'));
 refrescar();};
let xray=false;
document.getElementById('bxray').onclick=e=>{xray=!xray;e.target.classList.toggle('on',xray);
 for(const o of objetos){ if(o.p.sis==='carroceria'||o.p.sis==='pilotos')continue;
  o.mesh.material.transparent=xray; o.mesh.material.opacity=xray?0.22:1;
  o.mesh.material.depthWrite=!xray; o.mesh.castShadow=!xray; o.mesh.material.needsUpdate=true;}};

// ---------- clic para inspeccionar ----------
const ray=new THREE.Raycaster(), mouse=new THREE.Vector2();
const info=document.getElementById('info');
let sel=null, colSel=null;
addEventListener('pointerdown',ev=>{
 if(ev.target!==renderer.domElement)return;
 mouse.x=(ev.clientX/innerWidth)*2-1; mouse.y=-(ev.clientY/innerHeight)*2+1;
 ray.setFromCamera(mouse,camera);
 const hits=ray.intersectObjects(objetos.filter(o=>o.mesh.visible&&o.p.sis!=='carroceria').map(o=>o.mesh));
 if(sel){sel.material.emissive.setHex(0x000000);sel=null;}
 if(!hits.length){info.style.display='none';return;}
 sel=hits[0].object; sel.material.emissive=new THREE.Color(0x1f6feb);
 sel.material.emissiveIntensity=0.55;
 const p=sel.userData, s=D.sistemas.find(x=>x.id===p.sis);
 info.style.display='block';
 info.querySelector('.t').textContent=p.nom;
 info.querySelector('.s').textContent=p.spec;
 const tag=info.querySelector('.sis-tag');
 tag.textContent=`${s.nom} · paso ${p.paso}`; tag.style.color=s.col;
});

addEventListener('resize',()=>{camera.aspect=innerWidth/innerHeight;camera.updateProjectionMatrix();renderer.setSize(innerWidth,innerHeight);});
renderer.setAnimationLoop(()=>{controls.update();renderer.render(scene,camera);});
</script></body></html>
"""

out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "carro-completo-3d.html")
html = TEMPLATE.replace("__DATA__", json.dumps(DATA, separators=(",", ":")))
with open(out, "w", encoding="utf-8") as f:
    f.write(html)

print(f"OK  {len(PIEZAS)} piezas en {len(SISTEMAS)} sistemas, {len(PASOS)} pasos de armado")
for (i, n, c) in SISTEMAS:
    print(f"  {n:26s} {por_sis.get(i,0):4d}")
print(f"OK  {os.path.normpath(out)}  ({len(html)//1024} KB)")
