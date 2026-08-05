# -*- coding: utf-8 -*-
"""
BOM MAESTRO — la hoja con la que se compra el carro.

Consolida todo lo que salió de los entregables de ingeniería en una sola lista con
cantidad, especificación exacta de pedido y de dónde salió cada número. Es el
documento que cierra F0: sin él no se puede pedir nada, y los motores y las celdas
son las entregas más largas.

Qué se deriva automáticamente (no se teclea):
  - acero estructural, de `planos/lista-corte-tubos.csv` (el mismo archivo que va al
    taller), agregando por sección y convirtiendo a tramos comerciales de 6 m
  - inventario de piezas de corte láser, de los .dxf que existen en `planos/`

Qué está escrito a mano: las piezas de compra, cada una con su fuente citada en la
columna correspondiente. Los precios son ESTIMADOS anclados al presupuesto del doc
maestro (julio 2026) y están para dimensionar, no para pagar: el CSV trae una
columna vacía `precio_cotizado` para llenar con cotizaciones reales.

Salidas:
  docs/bom-maestro.md
  docs/bom-maestro.csv
"""
import csv, os, glob
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.normpath(os.path.join(HERE, ".."))
PLANOS = os.path.join(RAIZ, "planos")
DOCS = os.path.join(RAIZ, "docs")

import sys
sys.path.insert(0, HERE)
import analisis_chasis as _ac      # única fuente de la masa real del frame
ac_masa = _ac.masa_acero

MERMA = 1.15          # 15% extra de acero por cortes, errores y ajustes
TRAMO = 6.0           # m, largo comercial estándar de tubo
RHO = 7850.0          # kg/m³
# El acero no se cotiza a ojo: se pesa. Precio de tubo estructural puesto en obra.
PRECIO_KG = (32.0, 50.0)      # $/kg, PTR y placa
PRECIO_KG_RED = (42.0, 65.0)  # $/kg, redondo (más caro que el cuadrado)

# ============================================================================
# 1. ACERO: se deriva de la lista de corte real
# ============================================================================
largos = defaultdict(float)
piezas = defaultdict(int)
with open(os.path.join(PLANOS, "lista-corte-tubos.csv"), encoding="utf-8") as fh:
    for r in csv.DictReader(fh):
        largos[r["seccion"]] += float(r["largo_entre_centros_mm"]) / 1000.0
        piezas[r["seccion"]] += 1

def tramos(metros):
    """Tramos comerciales de 6 m, con merma, redondeando hacia arriba."""
    return int(-(-(metros * MERMA) // TRAMO))

def masa_tramo(seccion, largo=TRAMO):
    """kg de un tramo, calculados de la sección real (no tecleados)."""
    tipo, dims = seccion.split()[0], [float(v) for v in seccion.split()[1].split("x")]
    if tipo == "PTR":
        b, h, t = dims
        perim = 2 * (b + h) / 1000.0
    else:                                    # RED: tubo redondo
        d, t = dims
        perim = 3.14159 * d / 1000.0
    return perim * (t / 1000.0) * largo * RHO

def precio_acero(kg, red=False):
    a, b = PRECIO_KG_RED if red else PRECIO_KG
    return round(kg * a), round(kg * b)

def precio_placa(largo_m, ancho_m, esp_mm):
    kg = largo_m * ancho_m * (esp_mm / 1000.0) * RHO
    return kg, precio_acero(kg)

# ============================================================================
# 2. PIEZAS DE CORTE LÁSER: se derivan de los DXF que existen
# ============================================================================
# (archivo, cantidad, espesor mm, para qué)
LASER = [
    ("cartela-torre-coilover.dxf", 4, 4.7, "torres de coilover (2 por lado)"),
    ("cartela-pivote-brazo.dxf",   4, 4.7, "pivotes de brazo trasero"),
    ("placa-cuna-bateria.dxf",     2, 4.7, "laterales de la cuna de batería"),
    ("placa-torque-motor.dxf",     2, 8.0, "placa de torque exterior, con ménsula de caliper"),
    ("placa-torque-refuerzo.dxf",  2, 8.0, "placa de torque interior"),
    ("placa-torque-doblador.dxf",  4, 8.0, "doblador del cubo del eje (se suelda)"),
]
laser_faltantes = [
    ("ménsula de pivote superior delantero", 4, 4.7,
     "baja el eje 63 mm bajo el tubo superior — DXF pendiente"),
    ("ménsula de cremallera al mamparo", 2, 6.0,
     "posición nueva x=370 / z=±504, barrenos ovalados — DXF pendiente"),
    ("ménsula de caliper delantero", 2, 8.0,
     "adapta el caliper elegido a la mangueta ATV — DXF pendiente"),
    ("adaptador de disco Ø220 a maza ATV", 2, 8.0,
     "el disco del donante no da el par necesario — DXF pendiente"),
]
existentes = {os.path.basename(p) for p in glob.glob(os.path.join(PLANOS, "*.dxf"))}

# ============================================================================
# 3. LA LISTA
# ============================================================================
# (sistema, item, especificación de pedido, cant, unidad, $min, $max, entrega, fuente, fase)
ITEMS = []
def add(sistema, item, spec, cant, unidad, pmin, pmax, entrega, fuente, fase):
    ITEMS.append(dict(sistema=sistema, item=item, spec=spec, cant=cant, unidad=unidad,
                      pmin=pmin, pmax=pmax, entrega=entrega, fuente=fuente, fase=fase))

# --- PEDIDOS LARGOS: esto se pide el día 1, todo lo demás espera ---
add("Propulsión", "Kit 2× motor de cubo + controladores",
    "QS273 8 kW 96 V, **versión rin desmontable de carro 14\"** (en 13\" no cabe), "
    "2 controladores tipo APT96600 / Fardriver ND96530 con regen configurable, "
    "acelerador de pedal hall, selector F/N/R",
    1, "kit", 38700, 53700, "6-10 semanas", "doc maestro §6 · resultados-suspension-trasera",
    "F0")
add("Batería", "Celdas LiFePO4",
    "30 × prismática 105 Ah grado A (EVE/CATL), mismo lote, con busbars y tornillería",
    30, "pza", 26000, 36000, "4-8 semanas", "doc maestro §6", "F0")
add("Batería", "BMS",
    "30S LiFePO4, **250-300 A de descarga continua** (crítico: menos capa los motores), "
    "balanceo activo, Bluetooth",
    1, "pza", 6000, 9000, "4-6 semanas", "doc maestro §6", "F0")

# --- ACERO (derivado de la lista de corte) ---
acero_kg = 0.0
for sec, m in sorted(largos.items()):
    n = tramos(m)
    red = sec.startswith("RED")
    kg = masa_tramo(sec) * n
    acero_kg += kg
    nota = (f"{piezas[sec]} piezas, {m:.1f} m netos"
            + (" — los arcos requieren ROLADO" if red else ""))
    pmin, pmax = precio_acero(kg, red)
    add("Estructura", f"Tubo {sec}",
        f"{n} tramos de {TRAMO:.0f} m = {kg:.0f} kg ({nota}, +{(MERMA-1)*100:.0f}% de merma)",
        n, "tramo 6 m", pmin, pmax, "local, días", "planos/lista-corte-tubos.csv", "F1")
for sec, cuantos, para, fuente in [
        ("PTR 70x50x4", 1, "brazos tirados traseros (2 × 504 mm) y sobrante para ménsulas",
         "resultados-suspension-trasera"),
        ("RED 25.4x2.1", 1, "horquillas delanteras (~2.1 m netos)",
         "resultados-suspension-delantera")]:
    kg = masa_tramo(sec) * cuantos
    acero_kg += kg
    pmin, pmax = precio_acero(kg, sec.startswith("RED"))
    add("Estructura", f"Tubo {sec.replace('x', '×')}",
        f"{cuantos} tramo de {TRAMO:.0f} m = {kg:.0f} kg — {para}",
        cuantos, "tramo 6 m", pmin, pmax, "local, días", fuente, "F1")
for esp, L, A, para, fuente in [
        (8.0, 0.30, 0.60, "placas de torque (4) y dobladores (4), anidados",
         "resultados-placa-torque"),
        (4.7, 0.60, 1.20, "cartelas y ménsulas", "planos/*.dxf")]:
    kg, (pmin, pmax) = precio_placa(L, A, esp)
    acero_kg += kg
    add("Estructura", f"Placa de acero {esp:g} mm",
        f"1 hoja {L*1000:.0f}×{A*1000:.0f} mm = {kg:.0f} kg — {para}",
        1, "hoja", pmin, pmax, "local, días", fuente, "F1")
add("Estructura", "Servicio de corte láser",
    f"{sum(c for _, c, _, _ in LASER)} piezas con DXF listo + "
    f"{sum(c for _, c, _, _ in laser_faltantes)} por dibujar (ver §3). "
    "Mandar UN solo pedido: lo que pesa es el arranque, no el metro cortado",
    1, "servicio", 1500, 3000, "1-2 semanas", "planos/*.dxf", "F1")
add("Estructura", "Rolado de arcos",
    "2 arcos de tubo RED 44.5×2.1 al radio del plano — con dobladora de mandril, "
    "NO con dobladora de rodillos (aplasta la sección)",
    2, "pza", 1200, 2500, "1-2 semanas", "analisis_chasis", "F1")
add("Estructura", "Consumibles de soldadura",
    "Alambre MIG ER70S-6 Ø0.9 (5 kg) + gas 75/25 (renta y carga) + discos de corte y "
    "desbaste + boquillas de repuesto",
    1, "lote", 1800, 3000, "local", "—", "F1")

# --- SUSPENSIÓN ---
add("Rodaje", "Rótula cónica ATV",
    "Tipo Honda TRX300/Rancher — LBJ y UBJ por lado. **Verificar el cono contra la "
    "mangueta donante antes de comprar**",
    4, "pza", 1400, 2400, "local/importado", "resultados-suspension-delantera", "F1")
add("Rodaje", "Buje de poliuretano Ø12 + tubo interno",
    "Pivotes de horquillas delanteras",
    8, "pza", 1600, 2800, "local", "resultados-suspension-delantera", "F1")
add("Rodaje", "Kit buje poliuretano Ø16 + manga",
    "Pivote de brazo tirado trasero, base ancha ≥150 mm",
    2, "kit", 800, 1400, "local", "resultados-suspension-trasera", "F1")
add("Rodaje", "Coilover delantero",
    "Resorte **270 lb/in** · pedir ~**380 mm extendido, carrera ≥96 mm** (ojo a ojo "
    "estático 342 mm) · amortiguación ajustable por clicks (ζ 0.5-0.7) · 5,703 N en "
    "bache 3g · **especificar Ø del ojo y ancho de montaje**",
    2, "pza", 4000, 7000, "2-4 semanas", "resultados-suspension-delantera", "F1")
add("Rodaje", "Coilover trasero",
    "Resorte **292 lb/in** · pedir ~**540 mm extendido, carrera ≥117 mm** (ojo a ojo "
    "estático 482 mm) · ajustable · 6,710 N en bache 3g · **especificar Ø del ojo**. "
    "OJO: cambió respecto a versiones previas del BOM (era 351 lb/in) al corregir el "
    "anclaje inferior, que estaba fuera del brazo",
    2, "pza", 4500, 7500, "2-4 semanas", "resultados-suspension-trasera", "F1")
add("Rodaje", "Tornillería 10.9 de placa de torque",
    "**8** × M12 10.9 + tuerca autoblocante (4 por rueda, atraviesan las dos placas) "
    "y **8** × camisa de acero soldada a través del PTR (sin camisa, el apriete "
    "aplasta el tubo) · apretar a 95 N·m",
    1, "lote", 900, 1500, "local", "resultados-placa-torque", "F1")

# --- FRENOS ---
add("Rodaje", "Disco de freno delantero",
    "Ø220 × 5 mm macizo. **El disco del donante ATV (Ø180-200) NO da el par** — con él "
    "ninguna pedalera cumple",
    2, "pza", 1200, 2200, "local", "resultados-frenos §2", "F1")
add("Rodaje", "Caliper delantero",
    "Área de pistón ≥ **938 mm²** (equivale a un pistón de Ø35 mm) — de compacto o de "
    "moto deportiva de 2-4 pistones",
    2, "pza", 2000, 4000, "deshuesadero/local", "resultados-frenos §2", "F1")
add("Rodaje", "Caliper trasero CON palanca de freno de mano",
    "Área de pistón ≥ **740 mm²** (Ø31 mm equivalente), palanca mecánica integrada. "
    "**Verificar patrón de barrenos: 82 mm a radio 110** o se re-corre placa_torque.py. "
    "El disco lo trae el QS273",
    2, "pza", 2400, 4200, "deshuesadero/local", "resultados-frenos §2 y §6", "F1")
add("Rodaje", "Bombas de freno + barra de balance",
    "2 × bomba Ø14.3 mm (9/16\") + barra de balance ajustable + 2 depósitos. "
    "Doble circuito: una bomba por eje",
    1, "kit", 3500, 6000, "2-3 semanas", "resultados-frenos §3", "F1")
add("Rodaje", "Pedal de freno",
    "Relación **6.0:1** (da 428 N de pie para 1g sin booster)",
    1, "pza", 1200, 2500, "local", "resultados-frenos §3", "F1")
add("Rodaje", "Pastillas de freno",
    "**Semi-metálicas o sinterizadas, NO las más baratas** — con µ 0.45 el pedal baja de "
    "428 a 381 N. Juego para cada caliper elegido",
    4, "juego", 1200, 2400, "local", "resultados-frenos §3", "F1")
add("Rodaje", "Líneas de freno",
    "4 tramos de manguera flexible DOT con malla + línea rígida de acero + niples + "
    "líquido DOT4",
    1, "lote", 1800, 3000, "local", "resultados-frenos", "F1")
add("Rodaje", "Palanca de freno de mano + cables",
    "Palanca con trinquete + cable doble + tensores (2.7 kN de apriete necesarios)",
    1, "kit", 900, 1600, "local", "resultados-frenos §6", "F1")

# --- DIRECCIÓN ---
add("Rodaje", "Cremallera manual de compacto",
    "Donante. **Medir su carrera real y su avance por vuelta antes de comprar** — el "
    "cálculo supuso ±75 mm y 45 mm/vuelta. Sin servo",
    1, "pza", 1500, 3000, "deshuesadero", "resultados-direccion §3", "F1")
add("Rodaje", "Columna de dirección",
    "Con 2 crucetas, **preferentemente colapsable**. Las crucetas en ángulos parecidos "
    "y en fase, si no la dirección pulsa al girar",
    1, "pza", 1200, 2500, "deshuesadero", "resultados-direccion §5", "F1")
add("Rodaje", "Volante + maza",
    "Ø330 mm (con él, 34 N para girar parado en seco)",
    1, "pza", 900, 2000, "local", "resultados-direccion §4", "F1")
add("Rodaje", "Terminales de dirección",
    "2 × terminal (rótula) + 2 × rótula axial de cremallera + tubo roscado "
    "derecha/izquierda para ajustar convergencia sin desmontar",
    1, "kit", 1200, 2200, "local", "resultados-direccion", "F1")
add("Rodaje", "Llantas y rines",
    "2 × 175/70R13 delanteras + rines 13\"; las traseras (175/70R14) vienen con el kit "
    "QS273 versión rin de carro",
    2, "pza", 3000, 5200, "local", "resultados-suspension-delantera/trasera", "F1")

# --- ELÉCTRICO ---
add("Propulsión", "Protecciones y mando HV",
    "Contactor principal 400 A + fusible 400 A + resistencia de precarga + paro de "
    "emergencia + desconectador de servicio",
    1, "kit", 4500, 8000, "2-4 semanas", "doc maestro §7", "F2")
add("Propulsión", "Convertidor DC-DC",
    "96→12 V, 30 A, **aislado** (no hay batería de 12 V en el carro)",
    1, "pza", 2500, 4500, "2-4 semanas", "doc maestro §6", "F2")
add("Batería", "Cargador",
    "LiFePO4 96 V, 15-18 A, enchufable a 120 V",
    1, "pza", 5000, 8000, "2-4 semanas", "doc maestro §6", "F2")
add("Batería", "Caja de batería",
    "Lámina/perfil + compresión de celdas + venteo + aislamiento. **CAD pendiente** "
    "(punto 8 de que-falta-para-construir)",
    1, "lote", 3000, 5500, "—", "PENDIENTE", "F2")
add("Propulsión", "Cableado HV + 12 V",
    "Cable naranja de calibre según el diagrama unifilar, conectores, fundas, pasamuros. "
    "**Calibres PENDIENTES: no se puede pedir hasta tener el unifilar** (punto 7)",
    1, "lote", 4000, 7000, "—", "PENDIENTE", "F2")

# --- CABINA ---
add("Cabina", "Butacas", "2 × butaca comercial atornillada (deshuesadero o tipo bucket)",
    2, "pza", 3000, 7000, "local", "doc maestro §6", "F3")
add("Cabina", "Cinturones", "2 × arnés de 4 puntos con anclajes a la barra del frame",
    2, "pza", 2400, 4000, "local", "doc maestro §7", "F3")
add("Cabina", "Parabrisas", "Laminado plano o semi-curvo tipo buggy + burlete",
    1, "pza", 4000, 7000, "2-3 semanas", "doc maestro §6", "F3")
add("Cabina", "Laterales y ventanas", "Policarbonato 4 mm, corredizo manual",
    1, "lote", 2500, 4500, "local", "doc maestro §6", "F3")
add("Cabina", "Tablero", "Tablet Android + soporte + fuente 12 V (velocímetro GPS, BMS y "
    "controladores por Bluetooth)",
    1, "pza", 2500, 4500, "local", "doc maestro §6", "F3")

# --- CARROCERÍA (no urge: el carro debe funcionar feo antes de ser bonito) ---
add("Carrocería", "Espuma EPS en bloque", "Para rebanado CNC de los 10 paneles",
    1, "lote", 4000, 7000, "—", "doc maestro §6", "F4")
add("Carrocería", "Servicio de CNC de espuma", "Rebanado de los moldes de panel",
    1, "servicio", 6000, 12000, "2-4 semanas", "doc maestro §6", "F4")
add("Carrocería", "Fibra de vidrio y resina", "Tela, resina, gelcoat, desmoldante, consumibles",
    1, "lote", 7000, 12000, "local", "doc maestro §6", "F4")
add("Carrocería", "Fijaciones de panel", "Dzus + insertos roscados + separadores (10 paneles)",
    1, "lote", 2500, 4000, "local", "doc maestro §3", "F4")
add("Carrocería", "Wrap satinado", "10 paneles — puede esperar a F5",
    1, "servicio", 12000, 20000, "1-2 semanas", "doc maestro §9", "F5")
add("Luces", "Iluminación", "Barra LED frontal + cejas + aros y línea trasera + "
    "intermitentes + cámara trasera con pantalla",
    1, "lote", 7000, 12000, "2-3 semanas", "doc maestro §6", "F5")

# --- HERRAMIENTAS (una sola vez) ---
HERRAMIENTAS = [
    ("Soldadora MIG", "Inversor 200 A con gas, 110/220 V", 6000, 11000),
    ("Tronzadora de metal", "355 mm, para cortar los 73 tubos a escuadra", 2000, 3500),
    ("Esmeril angular", "115 mm + discos de corte y laminares", 900, 1600),
    ("Taladro + brocas", "Taladro de banco chico + juego de brocas para acero", 2500, 4500),
    ("Torquímetro", "1/2\", 20-200 N·m — la tornillería 10.9 se aprieta a torque, no a ojo", 900, 1800),
    ("Multímetro CAT III", "**Obligatorio** para trabajar 96 V: CAT III 600 V mínimo", 800, 1800),
    ("Herramienta aislada", "Juego de llaves y desarmadores aislados 1000 V para la batería", 1200, 2500),
    ("Equipo de protección", "Careta de soldar automática, guantes, mandil, lentes, extintor ABC", 2000, 3500),
]

# ============================================================================
# 4. AGREGADOS Y VERIFICACIÓN CONTRA EL PRESUPUESTO DEL DOC MAESTRO
# ============================================================================
PRESUPUESTO_MAESTRO = {          # doc maestro §9 (julio 2026)
    "Estructura": (7200, 11000),
    "Rodaje": (20300, 33500),
    "Propulsión": (38700, 53700),
    "Batería": (35000, 49000),
    "Carrocería": (21000, 36000),
    "Cabina": (14400, 24100),
    "Luces": (7000, 12000),
}
por_sistema = defaultdict(lambda: [0, 0])
for it in ITEMS:
    por_sistema[it["sistema"]][0] += it["pmin"]
    por_sistema[it["sistema"]][1] += it["pmax"]
tot_min = sum(v[0] for v in por_sistema.values())
tot_max = sum(v[1] for v in por_sistema.values())
her_min = sum(h[2] for h in HERRAMIENTAS)
her_max = sum(h[3] for h in HERRAMIENTAS)

# por fase (lo que hay que desembolsar en cada etapa)
por_fase = defaultdict(lambda: [0, 0])
for it in ITEMS:
    por_fase[it["fase"]][0] += it["pmin"]
    por_fase[it["fase"]][1] += it["pmax"]

def r100(v):
    """Redondeo a centenas: estos son estimados, no cotizaciones."""
    return round(v / 100.0) * 100

# ============================================================================
# 5. SALIDAS
# ============================================================================
os.makedirs(DOCS, exist_ok=True)
csv_path = os.path.join(DOCS, "bom-maestro.csv")
with open(csv_path, "w", newline="", encoding="utf-8-sig") as fh:
    w = csv.writer(fh)
    w.writerow(["sistema", "fase", "item", "especificacion_de_pedido", "cantidad",
                "unidad", "precio_est_min", "precio_est_max", "precio_cotizado",
                "proveedor", "entrega", "fuente"])
    for it in ITEMS:
        w.writerow([it["sistema"], it["fase"], it["item"],
                    it["spec"].replace("**", ""), it["cant"], it["unidad"],
                    it["pmin"], it["pmax"], "", "", it["entrega"], it["fuente"]])
    for nom, spec, a, b in HERRAMIENTAS:
        w.writerow(["Herramientas", "F0", nom, spec.replace("**", ""), 1, "pza",
                    a, b, "", "", "local", "doc maestro §9"])

md_path = os.path.join(DOCS, "bom-maestro.md")
with open(md_path, "w", encoding="utf-8") as f:
    f.write("# BOM maestro — la hoja con la que se compra el carro\n\n")
    f.write("**2026-08-04** · generado por `calculos/bom.py`. Cierra F0: sin esto no se puede "
            "pedir nada.\n\n")
    f.write("Hoja para cotizar: **`docs/bom-maestro.csv`** (trae una columna "
            "`precio_cotizado` vacía para llenar).\n\n")
    f.write("> **Sobre los precios.** Son estimados anclados al presupuesto del doc maestro "
            "(julio 2026) y sirven para dimensionar, **no para pagar**. Lo que este documento "
            "aporta de verdad es la *especificación de pedido* y la *cantidad* de cada pieza, "
            "que salen de los cálculos y no de una suposición. Pedir 3 cotizaciones de los "
            "renglones grandes antes de comprometerse.\n\n")

    f.write("## 1. Orden de compra (esto es lo que importa)\n\n")
    f.write("No se compra todo junto. El orden lo dicta el tiempo de entrega, no el gusto:\n\n")
    f.write("1. **HOY — los dos pedidos largos:** el kit de motores y las celdas + BMS. "
            "Entre 4 y 10 semanas de entrega, y **todo F1 y F2 dependen de ellos**. Antes de "
            "pagar hay que cerrar la lista de confirmaciones de §5.\n")
    f.write("2. **En cuanto haya taller — acero y corte:** con el acero en casa se puede "
            "empezar a soldar el frame mientras llegan los motores.\n")
    f.write("3. **Deshuesadero, sin prisa pero antes de F1:** cremallera, columna, manguetas "
            "ATV, calipers, butacas. Es la parte que depende de la suerte, así que conviene "
            "empezar a buscar temprano (§4).\n")
    f.write("4. **F2 en adelante:** eléctrico, cabina, carrocería. **El cableado HV todavía "
            "no se puede pedir** — faltan los calibres del diagrama unifilar.\n\n")

    f.write("## 2. La lista\n\n")
    for sistema in ["Propulsión", "Batería", "Estructura", "Rodaje", "Cabina",
                    "Carrocería", "Luces"]:
        items = [i for i in ITEMS if i["sistema"] == sistema]
        if not items:
            continue
        a, b = por_sistema[sistema]
        f.write(f"### {sistema} — ${a:,.0f} a ${b:,.0f}\n\n")
        f.write("| Fase | Item | Especificación de pedido | Cant. | Entrega | Estimado |\n")
        f.write("|---|---|---|---|---|---|\n")
        for it in items:
            f.write(f"| {it['fase']} | {it['item']} | {it['spec']} | "
                    f"{it['cant']} {it['unidad']} | {it['entrega']} | "
                    f"${it['pmin']:,.0f}–{it['pmax']:,.0f} |\n")
        f.write("\n")

    f.write(f"### Herramientas (una sola vez) — ${her_min:,.0f} a ${her_max:,.0f}\n\n")
    f.write("| Item | Especificación | Estimado |\n|---|---|---|\n")
    for nom, spec, a, b in HERRAMIENTAS:
        f.write(f"| {nom} | {spec} | ${a:,.0f}–{b:,.0f} |\n")
    f.write("\n")

    f.write("## 3. Piezas de corte láser\n\n")
    f.write("| Archivo | Cant. | Espesor | Para |\n|---|---|---|---|\n")
    for arch, cant, esp, para in LASER:
        estado = "✅" if arch in existentes else "❌ falta el DXF"
        f.write(f"| `{arch}` {estado} | {cant} | {esp} mm | {para} |\n")
    for nom, cant, esp, para in laser_faltantes:
        f.write(f"| {nom} ❌ | {cant} | {esp} mm | {para} |\n")
    f.write(f"\n**{sum(c for _, c, _, _ in LASER)} piezas ya tienen su DXF listo para el "
            f"cortador; {sum(c for _, c, _, _ in laser_faltantes)} faltan por dibujar** — "
            "todas son ménsulas simples, pero conviene juntarlas y mandar un solo pedido de "
            "corte porque el costo de arranque es lo que pesa.\n\n")
    f.write("**Decisión abierta:** los 5 nodos generativos (`cad/*.stl`) — impresos/fundidos "
            "o resueltos con cartelas de lámina. No está cerrada y no bloquea las compras de "
            "arriba.\n\n")

    f.write("## 4. Lista para el deshuesadero\n\n")
    f.write("Llevar esta lista y un calibrador. Lo que hay que medir **antes de pagar** está "
            "en negritas:\n\n")
    f.write("- **Mangueta, maza y rótulas de ATV 300** — verificar el cono de las rótulas y "
            "**que la mangueta quepa en rin 13\"** (los ATV usan 12\")\n")
    f.write("- **Cremallera manual de compacto** — **medir carrera total y avance por vuelta** "
            "(el cálculo supuso ±75 mm y 45 mm/vuelta)\n")
    f.write("- **Columna de dirección** con 2 crucetas, de preferencia colapsable\n")
    f.write("- **Calipers**: delanteros de área ≥938 mm²; traseros **con palanca de freno de "
            "mano** y ≥740 mm², **con patrón de barrenos de 82 mm**\n")
    f.write("- Butacas, bombas de freno, rines 13\"\n\n")

    f.write("## 5. Confirmar por escrito ANTES de pagar\n\n")
    f.write("Todo lo de abajo está parametrizado en los scripts: si un dato cambia se ajusta "
            "la constante y se re-corre. Pero si se descubre **después** de cortar acero, se "
            "vuelve a cortar acero.\n\n")
    f.write("| Qué | A quién | Por qué importa |\n|---|---|---|\n")
    f.write("| Versión de rin de carro 14\" del QS273 | QS Motor | En rin 13\" el motor no cabe "
            "— es la base de toda la suspensión trasera |\n")
    f.write("| Ø del eje y entrecaras de los planos | QS Motor | Definen el cubo de la placa "
            "de torque y su doblador |\n")
    f.write("| **Largo del eje libre del lado interior (≥84 mm)** | QS Motor | **El más "
            "crítico.** Si es menor, el sándwich de placas no cabe y hay que rediseñar. "
            "Incluye los 30 mm que ocupan el disco y el caliper entre la cara del motor y "
            "la placa |\n")
    f.write("| Ancho del cuerpo del motor (supuesto 130 mm) | QS Motor | Cambia el voladizo y "
            "todo el reparto de carga entre las dos placas |\n")
    f.write("| Ø del disco de freno y patrón del caliper | QS Motor | Fija la posición de las "
            "orejas ya cortadas en la placa de torque |\n")
    f.write("| Corriente real de descarga del BMS | proveedor | Menos de 250 A continuos capa "
            "los motores |\n")
    f.write("| Celdas del mismo lote | proveedor | Celdas mezcladas se desbalancean y el pack "
            "vale lo que su peor celda |\n\n")

    f.write("## 6. Totales y contraste con el presupuesto original\n\n")
    f.write("| Sistema | BOM (estimado) | Presupuesto doc maestro | |\n|---|---|---|---|\n")
    for sistema, (bm, bM) in PRESUPUESTO_MAESTRO.items():
        a, b = por_sistema.get(sistema, [0, 0])
        if a == 0:
            continue
        if b < bm:
            marca = "por debajo"
        elif a > bM:
            marca = "**se pasa**"
        else:
            marca = "dentro"
        f.write(f"| {sistema} | ${a:,.0f}–{b:,.0f} | ${bm:,.0f}–{bM:,.0f} | {marca} |\n")
    pm = sum(v[0] for v in PRESUPUESTO_MAESTRO.values())
    pM = sum(v[1] for v in PRESUPUESTO_MAESTRO.values())
    f.write(f"| **Total del carro** | **${r100(tot_min):,.0f}–{r100(tot_max):,.0f}** | "
            f"${pm:,.0f}–{pM:,.0f} | |\n")
    f.write(f"| Herramientas | ${her_min:,.0f}–{her_max:,.0f} | $10,000–15,000 | |\n\n")
    f.write("El rango es ancho a propósito: el **mínimo** es comprando bien y usando "
            "deshuesadero donde se puede; el **máximo** es todo nuevo a precio de mostrador. "
            "La realidad cae en medio y depende sobre todo de la suerte en el deshuesadero.\n\n")

    f.write("### De dónde viene el sobrecosto\n\n")
    f.write(f"El BOM detallado sale **${r100(tot_min):,.0f}–{r100(tot_max):,.0f}** contra los "
            f"${pm:,.0f}–{pM:,.0f} del doc maestro. Solo se pasan dos sistemas, y hay una "
            "razón concreta en cada uno:\n\n")
    f.write("**Rodaje** es el grande. Desglosado por entregable:\n\n")
    f.write("| Grupo | Estimado | |\n|---|---|---|\n")
    for etiqueta, clave in [("Frenos", "frenos"), ("Suspensión y placa de torque", "suspension"),
                            ("Dirección", "direccion"), ("Llantas y rines", "llantas")]:
        a = b = 0
        for it in ITEMS:
            if it["sistema"] != "Rodaje":
                continue
            fu = it["fuente"].lower() + " " + it["item"].lower()
            if clave == "llantas":
                hit = "llantas" in fu
            elif clave == "suspension":
                hit = ("suspension" in fu or "torque" in fu) and "llantas" not in fu
            else:
                hit = clave in fu
            if hit:
                a += it["pmin"]; b += it["pmax"]
        f.write(f"| {etiqueta} | ${a:,.0f}–{b:,.0f} | |\n")
    f.write("\nLos **frenos solos se comen casi la mitad del rodaje**, y es consecuencia "
            "directa de un hallazgo del cálculo: el freno del donante ATV no alcanza para "
            "690 kg, así que hay que comprar discos de Ø220 y calipers de mayor área en vez de "
            "reusar los del donante. El doc maestro presupuestó dando por hecho que el freno "
            "venía con la mangueta.\n\n")
    f.write("**Estructura** se pasa por los servicios, no por el acero: el acero puro son "
            f"~{acero_kg:.0f} kg (${precio_acero(acero_kg)[0]:,.0f}–"
            f"{precio_acero(acero_kg)[1]:,.0f}), y lo que empuja son el corte láser, el rolado "
            "de los arcos y los consumibles de soldadura — que el presupuesto original no "
            "tenía desglosados.\n\n")
    f.write(f"> Ojo con ese número: **{acero_kg:.0f} kg es lo que se COMPRA**, no lo que pesa "
            f"el carro. El frame soldado son {ac_masa:.1f} kg (`analisis_chasis.py`); la "
            "diferencia son "
            "los tramos comerciales de 6 m que sobran, la merma de corte y las placas. El "
            "sobrante sirve para el jig de soldadura y las ménsulas, así que no se tira.\n\n")
    f.write("**Qué hacer con esto.** No es motivo de alarma: el carro sigue siendo un proyecto "
            "de rango medio y **se construye por fases**, así que el desembolso se reparte. "
            "Las palancas reales para bajarlo, en orden de efecto:\n\n")
    f.write("1. **Deshuesadero agresivo en frenos y rodaje** — calipers, bombas, columna, "
            "butacas y rines usados mueven la aguja más que cualquier otra cosa.\n")
    f.write("2. **Wrap hasta el final** (F5): son $12-20 mil que el carro no necesita para "
            "andar.\n")
    f.write("3. **Herramientas prestadas o rentadas** donde se pueda — pero **el multímetro "
            "CAT III y la herramienta aislada se compran, no se piden prestados**.\n")
    f.write("4. Lo que **nunca** se recorta (doc maestro §9): BMS, frenos, coilovers, "
            "cinturones, fusible.\n\n")
    f.write("### Desembolso por fase\n\n")
    f.write("| Fase | Qué es | Estimado |\n|---|---|---|\n")
    nombres = {"F0": "pedidos largos (motores y celdas) — **primero**",
               "F1": "chasis rodante: acero, suspensión, frenos, dirección",
               "F2": "tren eléctrico", "F3": "pruebas y cabina",
               "F4": "carrocería", "F5": "acabado"}
    for fase in ["F0", "F1", "F2", "F3", "F4", "F5"]:
        if fase in por_fase:
            a, b = por_fase[fase]
            f.write(f"| {fase} | {nombres[fase]} | ${r100(a):,.0f}–{r100(b):,.0f} |\n")
    f.write("\nEl carro **rueda, frena y dirige al terminar F1**, y **anda solo al terminar "
            "F2**. Todo lo de F4 y F5 es apariencia: se puede estirar en el tiempo sin que el "
            "carro deje de servir.\n\n")

    f.write("## 7. Lo que este BOM todavía NO puede cotizar\n\n")
    f.write("Honestidad sobre los huecos — cada uno es un entregable de ingeniería pendiente:\n\n")
    f.write("- **Cableado HV y 12 V**: los calibres salen del diagrama unifilar, que no está "
            "hecho. Es lo único que bloquea cerrar F2.\n")
    f.write("- **Caja de batería**: falta el CAD del arreglo 30S con compresión y venteo.\n")
    f.write("- **Nodos del chasis**: impresos/fundidos vs cartelas — decisión abierta.\n")
    f.write("- **Carrocería**: los volúmenes de espuma y fibra dependen del CAD final de "
            "superficie, que es de F4.\n\n")
    f.write("Ninguno de los cuatro bloquea los pedidos largos, que es lo que urge.\n")

print(f"acero derivado de la lista de corte:")
for sec, m in sorted(largos.items()):
    print(f"  {sec:22s} {piezas[sec]:3d} piezas  {m:6.1f} m netos  -> {tramos(m)} tramos de 6 m")
print(f"laser: {sum(c for _, c, _, _ in LASER)} piezas con DXF, "
      f"{sum(c for _, c, _, _ in laser_faltantes)} por dibujar")
print(f"items: {len(ITEMS)} + {len(HERRAMIENTAS)} herramientas")
print(f"total carro   ${tot_min:,.0f} - ${tot_max:,.0f}")
print(f"herramientas  ${her_min:,.0f} - ${her_max:,.0f}")
for fase in ["F0", "F1", "F2", "F3", "F4", "F5"]:
    if fase in por_fase:
        print(f"  {fase}: ${por_fase[fase][0]:,.0f} - ${por_fase[fase][1]:,.0f}")
print(f"OK  {md_path}\nOK  {csv_path}")
