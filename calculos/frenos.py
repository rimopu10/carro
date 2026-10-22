# -*- coding: utf-8 -*-
"""
FRENOS — dimensionado real del sistema hidráulico de 4 discos.

Arquitectura ya fijada en el doc maestro: disco hidráulico ×4, doble bomba con
balance bar, SIN booster, más regen. Adelante mangueta/freno de donante ATV;
atrás el disco propio del QS273 con la ménsula ya integrada en la placa de torque.

Este script resuelve lo que faltaba:
  - reparto dinámico de peso al frenar y reparto de frenado ideal vs fijo
  - elección del balance bar con el criterio de seguridad (que SIEMPRE bloquee
    primero el eje delantero; si bloquea primero el trasero el carro trompea)
  - par requerido por rueda y de ahí el diámetro de disco y área de pistón
  - pedalera: combinación de bombas y relación de pedal que da <450 N sin booster,
    con verificación de recorrido de pedal
  - verificación térmica de una frenada de pánico y de una bajada sostenida
  - interacción con el regen (que solo actúa atrás: hay un límite de seguridad)
  - freno de estacionamiento por palanca integrada en el caliper trasero

Criterio: el freno de fricción solo debe dar 1g POR SÍ SOLO, sin contar con el
regen. El regen puede fallar (batería llena, BMS abierto, controlador en falla) y
el carro tiene que frenar igual.

Salidas:
  calculos/resultados-frenos.md
  calculos/frenos.png
"""
import numpy as np
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
G = 9.81

# ============================================================================
# 1. DATOS DEL CARRO (de los entregables ya cerrados)
# ============================================================================
MASA      = 690.0     # kg con 2 ocupantes (doc maestro)
DIST_TRAS = 0.53      # fracción estática al eje trasero (47/53; 2026-10-21, antes 38/62: batería en el túnel central)
BATALLA   = 2.13      # m (suspension_trasera.py)
H_CG      = 0.40      # m (2026-10-21, antes 0.33: presupuesto por componente)
R_DEL     = 0.2875    # m, 175/70R13 (Ø575)
R_TRAS    = 0.3005    # m, 175/70R14 (Ø601)
A_OBJ     = 1.0       # g, deceleración de diseño (objetivo declarado del proyecto)

# --- pastillas e hidráulica ---
MU_PAD    = 0.40      # pastilla-disco. Se usa el valor CALIENTE de una pastilla
                      # orgánica/semi-metálica corriente. En frío da 0.45-0.50, o sea
                      # que el sistema se dimensiona para el peor momento, no el mejor.
P_MAX     = 80e5      # Pa (80 bar) — presión de línea de diseño sin booster
F_PEDAL_MAX = 450.0   # N, tope de fuerza de pedal aceptable sin booster
REC_PEDAL_MAX = 70.0  # mm, recorrido de pedal aceptable
CARRERA_PISTON = 0.7e-3   # m, avance de pistón por frenada (holgura + knock-back)
F_COMPLIANCE   = 1.35     # factor por dilatación de mangueras y flexión del pedal

# --- regen ---
PAR_REGEN = 350.0     # N·m por rueda trasera (tope del QS273)

# --- discos candidatos ---
DISCOS_DEL = [0.180, 0.200, 0.220, 0.240, 0.260]   # m, diámetro exterior
DISCO_TRAS = 0.220    # m, el que trae el QS273
DISCO_DEL_MAX = 0.250 # m, lo que cabe en un rin 13" dejando lugar al caliper
# radio efectivo ≈ 0.42·Ø  (centro de pastilla en un disco de auto/moto típico)
def r_ef(d_ext): return 0.42 * d_ext
# pistón de caliper realista: por debajo de Ø26 no hay donantes, por arriba de Ø46 tampoco
D_PISTON_MIN, D_PISTON_MAX = 0.0254, 0.046   # 2026-10-21: 0.026 -> 0.0254 (pistón de 1", el estándar de los calipers de ATV): con 47/53 el trasero pide Ø25.6

# --- bombas y pedal candidatos ---
BOMBAS = [0.0143, 0.0159, 0.0175, 0.01905]   # m, calibres comunes (9/16", 5/8", 11/16", 3/4")
RATIOS = [4.5, 5.0, 5.5, 6.0, 6.5, 7.0]   # 2026-10-21: hasta 7:1 (pedalera ajustable estándar); con 47/53 y CG 0.40 nada cumple con 6:1

# ============================================================================
# 2. REPARTO DINÁMICO DE PESO Y REPARTO DE FRENADO IDEAL
# ============================================================================
def cargas(a_g):
    """Carga normal por eje (N) a una deceleración de a_g veces g."""
    W = MASA * G
    trans = W * a_g * H_CG / BATALLA          # transferencia de peso al frenar
    N_del = W * (1 - DIST_TRAS) + trans
    N_tras = W * DIST_TRAS - trans
    return N_del, N_tras

aa = np.linspace(0.02, 1.15, 200)
Nd, Nt = cargas(aa)
reparto_ideal = Nd / (Nd + Nt)                 # fracción de frenado que toca adelante

# --- elección del reparto fijo (balance bar) ---
# La barra de balance da un reparto FIJO; el ideal cambia con la deceleración.
# Criterio de seguridad: el trasero nunca debe bloquear primero. Eso exige
#   (1-phi) <= DIST_TRAS - a_g*H_CG/BATALLA   para toda a_g hasta la de diseño.
phi_min = 1 - (DIST_TRAS - A_OBJ * H_CG / BATALLA)
PHI = np.ceil((phi_min + 0.035) * 100) / 100   # + margen, redondeado a 1%

# --- coeficiente de adherencia que exige cada eje con el reparto fijo ---
F_tot = MASA * G * aa
mu_del = (PHI * F_tot) / Nd
mu_tras = ((1 - PHI) * F_tot) / Nt

# ============================================================================
# 3. PAR REQUERIDO POR RUEDA A LA DECELERACIÓN DE DISEÑO
# ============================================================================
F_dis = MASA * G * A_OBJ
T_del = PHI * F_dis / 2 * R_DEL
T_tras = (1 - PHI) * F_dis / 2 * R_TRAS

def area_piston(par, d_disco, p=P_MAX):
    """Área TOTAL de pistón por caliper para dar 'par' a la presión p.
    Caliper de pastilla doble: fricción = 2·mu·F_clamp, con F_clamp = p·A."""
    return par / (2 * MU_PAD * p * r_ef(d_disco))

def d_eq(a):
    """Diámetro de un pistón único de la misma área (para comparar con donantes)."""
    return 2 * np.sqrt(a / np.pi)

A_TRAS = area_piston(T_tras, DISCO_TRAS)
D_TRAS_EQ = d_eq(A_TRAS)

# --- el trabajo del pie es INVARIANTE ---------------------------------------
# F_pedal = P·A_bomba/ratio  y  recorrido = (V/A_bomba)·ratio, así que
#   F_pedal × recorrido = 2·(P·A_caliper)·s·k
# El calibre de bomba y la relación de pedal solo intercambian fuerza por
# recorrido: NO se puede ganar por ahí. Lo único que baja el producto es disco
# más grande (más brazo de palanca), mejor pastilla, o desplazar menos fluido.
def trabajo_pedal(d_del):
    c_del = T_del / (2 * MU_PAD * r_ef(d_del))          # P·A del caliper delantero
    c_tras = T_tras / (2 * MU_PAD * r_ef(DISCO_TRAS))
    return 2 * (c_del + c_tras) * CARRERA_PISTON * F_COMPLIANCE

# ============================================================================
# 4. SELECCIÓN ACOPLADA DE DISCO Y PEDALERA
# ============================================================================
# El disco y la pedalera NO se pueden elegir por separado: el disco fija el
# trabajo que el pie tiene que meter, y la pedalera solo lo reparte entre fuerza
# y recorrido. Se buscan las dos cosas juntas.
def evalua(d_del, bore_del, bore_tras, ratio):
    A_del = area_piston(T_del, d_del)
    A_mc_d, A_mc_t = np.pi * (bore_del / 2)**2, np.pi * (bore_tras / 2)**2
    f_pedal = P_MAX * (A_mc_d + A_mc_t) / ratio
    v_del = 2 * A_del * CARRERA_PISTON * F_COMPLIANCE
    v_tras = 2 * A_TRAS * CARRERA_PISTON * F_COMPLIANCE
    rec = max(v_del / A_mc_d, v_tras / A_mc_t) * ratio * 1000
    ok = (f_pedal <= F_PEDAL_MAX and rec <= REC_PEDAL_MAX
          and d_del <= DISCO_DEL_MAX
          and D_PISTON_MIN <= d_eq(A_del) <= D_PISTON_MAX
          and D_PISTON_MIN <= D_TRAS_EQ <= D_PISTON_MAX)
    return dict(disco=d_del, bore_del=bore_del, bore_tras=bore_tras, ratio=ratio,
                A_del=A_del, f=f_pedal, rec=rec, ok=ok)

combos = [evalua(d, bd, bt, r)
          for d in DISCOS_DEL for bd in BOMBAS for bt in BOMBAS for r in RATIOS]
validos = [c for c in combos if c["ok"]]
# Entre los que cumplen, el mejor es el de disco más chico (más barato, más ligero,
# más fácil de acomodar en el rin); a igualdad de disco, el de menor fuerza de pedal.
elegido = (min(validos, key=lambda c: (c["disco"], c["f"])) if validos
           else min(combos, key=lambda c: c["f"] * c["rec"]))
DISCO_DEL = elegido["disco"]
A_DEL = elegido["A_del"]

# tabla por diámetro de disco: qué pide el caliper y cuál es el mejor pedal posible
tabla_del = []
for d in DISCOS_DEL:
    a = area_piston(T_del, d)
    mejores = [c for c in combos if abs(c["disco"] - d) < 1e-9 and c["ok"]]
    mejor = min(mejores, key=lambda c: c["f"]) if mejores else None
    tabla_del.append((d, a, d_eq(a), trabajo_pedal(d), mejor))

# ============================================================================
# 5. TÉRMICO
# ============================================================================
V_PANICO = 100 / 3.6          # m/s, frenada de pánico desde 100 km/h
E_PANICO = 0.5 * MASA * V_PANICO**2
CP_ACERO = 460.0              # J/kg·K
def masa_disco(d_ext, espesor=0.005, d_int_frac=0.62):
    """Masa aproximada de la corona de fricción de un disco macizo de acero."""
    r_e, r_i = d_ext / 2, d_ext / 2 * d_int_frac
    return np.pi * (r_e**2 - r_i**2) * espesor * 7850

m_disco_del = masa_disco(DISCO_DEL)
m_disco_tras = masa_disco(DISCO_TRAS)
dT_del = (PHI * E_PANICO / 2) / (m_disco_del * CP_ACERO)
dT_tras = ((1 - PHI) * E_PANICO / 2) / (m_disco_tras * CP_ACERO)

# Bajada sostenida: 10% de pendiente a 40 km/h, sin regen
PEND, V_BAJADA = 0.10, 40 / 3.6
P_BAJADA = MASA * G * PEND * V_BAJADA
# con regen los motores se comen esta potencia (2 × 8 kW nominal)
P_REGEN_DISP = 2 * 8000.0

# ============================================================================
# 6. REGEN — solo actúa atrás, y eso tiene un límite de seguridad
# ============================================================================
F_REGEN = 2 * PAR_REGEN / R_TRAS
A_REGEN = F_REGEN / (MASA * G)                  # en g
_, Nt_regen = cargas(A_REGEN)
MU_REGEN = F_REGEN / Nt_regen                   # adherencia que exige al eje trasero
# ¿a qué deceleración de regen el eje trasero exige mu = 0.4 (mojado/terracería)?
def mu_tras_regen(a_g):
    return (MASA * G * a_g) / cargas(a_g)[1]
a_seguro = float(aa[np.argmin(np.abs([mu_tras_regen(x) - 0.40 for x in aa]))])

# ============================================================================
# 7. FRENO DE ESTACIONAMIENTO (palanca integrada en el caliper trasero)
# ============================================================================
PEND_PARK = 0.20                                # 20% de pendiente
th = np.arctan(PEND_PARK)
F_PARK = MASA * G * np.sin(th)
N_tras_park = MASA * G * (np.cos(th) * DIST_TRAS - np.sin(th) * H_CG / BATALLA)
MU_PARK = F_PARK / N_tras_park
T_PARK = F_PARK / 2 * R_TRAS
F_CLAMP_PARK = T_PARK / (2 * MU_PAD * r_ef(DISCO_TRAS))

# ============================================================================
# 8. INFORME
# ============================================================================
out_md = os.path.join(HERE, "resultados-frenos.md")
with open(out_md, "w", encoding="utf-8") as f:
    f.write("# Frenos — dimensionado del sistema de 4 discos\n\n")
    f.write("Disco hidráulico ×4, doble bomba con balance bar, **sin booster**, más regen. "
            "Generado por `frenos.py`.\n\n")
    f.write("**Criterio de partida:** el freno de fricción tiene que dar **1g él solo**, sin "
            "contar con el regen. El regen puede desaparecer sin avisar (batería llena, BMS "
            "abierto, controlador en falla) y el carro tiene que frenar igual. Todo lo que "
            "sigue está dimensionado así; el regen es un extra que alarga la vida de las "
            "pastillas, no parte del cálculo de seguridad.\n\n")

    f.write("## 1. Reparto de frenado (lo que decide si el carro trompea)\n\n")
    f.write(f"Al frenar, el peso se pasa adelante: {MASA:.0f} kg × {A_OBJ:.1f}g × "
            f"{H_CG:.2f} m / {BATALLA:.2f} m = **{MASA*G*A_OBJ*H_CG/BATALLA/G:.0f} kg** "
            "de transferencia.\n\n")
    f.write("| | Estático | A 1g |\n|---|---|---|\n")
    Nd0, Nt0 = cargas(0.0); Nd1, Nt1 = cargas(A_OBJ)
    f.write(f"| Eje delantero | {Nd0/G:.0f} kg ({(1-DIST_TRAS)*100:.0f}%) | "
            f"{Nd1/G:.0f} kg ({Nd1/(Nd1+Nt1)*100:.0f}%) |\n")
    f.write(f"| Eje trasero | {Nt0/G:.0f} kg ({DIST_TRAS*100:.0f}%) | "
            f"{Nt1/G:.0f} kg ({Nt1/(Nd1+Nt1)*100:.0f}%) |\n\n")
    f.write("El carro es de motor central y batería atrás: parado carga **62% atrás**, pero "
            f"frenando a 1g se le da la vuelta y queda **{Nd1/(Nd1+Nt1)*100:.0f}% adelante**. "
            "Un reparto de frenado pensado con el peso estático bloquearía el trasero.\n\n")
    f.write("La barra de balance da un reparto **fijo**; el ideal cambia con la deceleración. "
            "La regla de seguridad es que el eje trasero **nunca** bloquee primero — si "
            "bloquea atrás el carro se sale de cola sin remedio; si bloquea adelante solo "
            "pierde dirección y sigue derecho.\n\n")
    f.write(f"- Mínimo teórico para que no bloquee atrás a {A_OBJ:.1f}g: "
            f"**{phi_min*100:.1f}%** adelante.\n")
    f.write(f"- **Reparto elegido: {PHI*100:.0f}% adelante / {(1-PHI)*100:.0f}% atrás** "
            "(con margen). La barra de balance permite afinarlo en las pruebas de F3.\n\n")

    f.write("## 2. Par y hardware por rueda\n\n")
    f.write(f"A {A_OBJ:.1f}g la fuerza total de frenado es {F_dis:.0f} N.\n\n")
    f.write("| | Par por rueda | Disco | Radio efectivo |\n|---|---|---|---|\n")
    f.write(f"| Delantero | **{T_del:.0f} N·m** | Ø{DISCO_DEL*1000:.0f} mm | "
            f"{r_ef(DISCO_DEL)*1000:.0f} mm |\n")
    f.write(f"| Trasero | **{T_tras:.0f} N·m** | Ø{DISCO_TRAS*1000:.0f} mm (el del QS273) | "
            f"{r_ef(DISCO_TRAS)*1000:.0f} mm |\n\n")
    f.write(f"Área de pistón necesaria por caliper delantero, a {P_MAX/1e5:.0f} bar de línea "
            f"y µ de pastilla {MU_PAD}:\n\n")
    f.write("| Disco delantero | Área de pistón | Pistón equivalente | Mejor pedal posible | |\n")
    f.write("|---|---|---|---|---|\n")
    for (d, a, deq, _w, mejor) in tabla_del:
        if mejor is None:
            best = "ninguna combinación cumple"
            marca = "✗"
        else:
            best = f"{mejor['f']:.0f} N / {mejor['rec']:.0f} mm"
            marca = "✓ elegido" if abs(d - DISCO_DEL) < 1e-9 else "ok"
        if d > DISCO_DEL_MAX:
            best = f"no cabe en rin 13\""
            marca = "✗"
        f.write(f"| Ø{d*1000:.0f} mm | {a*1e6:.0f} mm² | Ø{deq*1000:.0f} mm | {best} | {marca} |\n")
    f.write(f"\nTrasero (disco Ø{DISCO_TRAS*1000:.0f} fijo, el del QS273): "
            f"**{A_TRAS*1e6:.0f} mm²** → pistón equivalente Ø{D_TRAS_EQ*1000:.0f} mm.\n\n")
    f.write(f"**Si el pedal se siente largo en las pruebas**, el disco de Ø240 es el cambio "
            f"directo: misma fuerza de pedal pero {[m['rec'] for (d,_a,_e,_w,m) in tabla_del if abs(d-0.240)<1e-9][0]:.0f} mm "
            f"de recorrido en vez de {elegido['rec']:.0f}, y menos temperatura por tener más "
            "masa de corona. Solo hay que verificar que libre el rin de 13\".\n\n")
    f.write(f"**Comprobación cruzada con la placa de torque.** El servicio pide "
            f"{T_tras:.0f} N·m por rueda trasera, pero `placa_torque.py` la dimensionó para "
            f"**630 N·m**. No es contradicción: 630 N·m es el tope real que una rueda trasera "
            f"puede transmitir antes de patinar, y ocurre a **baja** deceleración, cuando el "
            f"eje trasero todavía carga sus {MASA*DIST_TRAS/2:.0f} kg estáticos (µ=1 × "
            f"{MASA*DIST_TRAS/2:.0f} kg × {R_TRAS:.3f} m). Bien: la placa tiene "
            f"{630/T_tras:.2f}× de margen sobre el caso de servicio.\n\n")
    f.write("**Aviso sobre el donante ATV.** Un freno de ATV 300 típico trae disco de "
            "Ø180-200 mm con caliper de un pistón chico. Por la tabla, esos diámetros no dan: "
            "el pistón tendría que ser irreal y la pedalera se vuelve imposible. Se reusa la "
            "**mangueta y la maza** del ATV — que es lo que define la geometría de suspensión "
            f"ya calculada — pero se le monta **disco de Ø{DISCO_DEL*1000:.0f} mm** y caliper "
            "de compacto o de moto deportiva de 2-4 pistones, con una ménsula de adaptación "
            "cortada en láser (del mismo tipo que las cartelas que ya hicimos).\n\n")

    f.write("## 3. Pedalera (sin booster) — y por qué no se elige aparte del disco\n\n")
    f.write("Hay una trampa aquí que vale la pena entender antes de ver la tabla. La fuerza "
            "de pedal es `P·A_bomba/relación` y el recorrido es `(V/A_bomba)·relación`. "
            "Multiplicando las dos, el calibre de bomba y la relación **se cancelan**:\n\n")
    f.write("```\nfuerza de pedal × recorrido = 2 · (P·A_caliper) · avance de pistón\n```\n\n")
    f.write("O sea: **el trabajo que tiene que meter el pie es invariante**. La relación de "
            "pedal y el calibre de bomba solo intercambian fuerza por recorrido — no se puede "
            "ganar por ahí. Lo único que baja ese producto es **disco más grande** (más brazo "
            "de palanca), mejor pastilla, o desplazar menos fluido (mangueras de malla, buen "
            "purgado, poco knock-back).\n\n")
    f.write("Por eso el disco y la pedalera se eligen **juntos**. Con el disco de Ø180 del "
            "donante ATV el trabajo de pedal sale de "
            f"{trabajo_pedal(0.180):.1f} N·m y **ninguna** combinación de bomba y relación "
            f"cumple; con Ø{DISCO_DEL*1000:.0f} baja a {trabajo_pedal(DISCO_DEL):.1f} N·m y ya "
            "hay margen.\n\n")
    f.write(f"Objetivo: **≤ {F_PEDAL_MAX:.0f} N** de pie y **≤ {REC_PEDAL_MAX:.0f} mm** de "
            f"recorrido, a {P_MAX/1e5:.0f} bar de línea.\n\n")
    f.write("| Bomba delantera | Bomba trasera | Relación de pedal | Fuerza de pedal | "
            "Recorrido | |\n|---|---|---|---|---|---|\n")
    muestra = [c for c in combos if abs(c["disco"] - DISCO_DEL) < 1e-9]
    muestra.sort(key=lambda c: (not c["ok"], c["f"]))
    for c in muestra[:12]:
        marca = ("✓ elegida" if c is elegido else "ok" if c["ok"] else "no cumple")
        f.write(f"| Ø{c['bore_del']*1000:.1f} mm | Ø{c['bore_tras']*1000:.1f} mm | "
                f"{c['ratio']:.1f}:1 | {c['f']:.0f} N | {c['rec']:.0f} mm | {marca} |\n")
    f.write(f"\n**Elegida: bomba delantera Ø{elegido['bore_del']*1000:.1f} mm + trasera "
            f"Ø{elegido['bore_tras']*1000:.1f} mm, pedal {elegido['ratio']:.1f}:1** → "
            f"**{elegido['f']:.0f} N** de pie y **{elegido['rec']:.0f} mm** de recorrido "
            f"para {A_OBJ:.1f}g.\n\n")
    f.write("Para referencia: un carro con booster pide 200-250 N; un fórmula sin booster "
            "500-700 N. Estamos en el rango de un kart pesado, que es exactamente lo que es "
            "este carro. **Doble circuito** (una bomba por eje): si revienta una manguera, el "
            "otro eje sigue frenando.\n\n")
    f.write(f"**Margen: escaso.** De {len(combos)} combinaciones evaluadas solo "
            f"**{len(validos)}** cumplen fuerza y recorrido a la vez. No es un sistema con "
            "holgura: es el precio de no llevar booster en un carro de 690 kg.\n\n")
    f.write("Lo que se siente al manejar (la fuerza es proporcional a la deceleración):\n\n")
    f.write("| Frenada | Deceleración | Fuerza de pedal |\n|---|---|---|\n")
    for nom, ag in [("suave, de ciudad", 0.20), ("normal", 0.35),
                    ("fuerte", 0.60), ("pánico", A_OBJ)]:
        f.write(f"| {nom} | {ag:.2f}g | {elegido['f']*ag/A_OBJ:.0f} N |\n")
    f.write(f"\nY casi todo el frenado de ciudad ni siquiera llega al pedal: lo hace el regen "
            f"al soltar el acelerador (§5).\n\n")
    f.write(f"**Sensibilidad a la pastilla.** Todo esto está calculado con µ = {MU_PAD} "
            "(pastilla orgánica corriente, **caliente** — el peor momento, no el mejor):\n\n")
    f.write("| µ de pastilla | Fuerza de pedal para 1g | |\n|---|---|---|\n")
    for mu_ in (0.33, 0.40, 0.45, 0.50):
        f_mu = elegido["f"] * MU_PAD / mu_
        est = "pastilla barata recalentada" if mu_ < 0.36 else (
              "valor de diseño" if abs(mu_ - MU_PAD) < 1e-9 else "semi-metálica / sinterizada")
        f.write(f"| {mu_:.2f} | {f_mu:.0f} N | {est} |\n")
    f.write("\n**Comprar pastilla semi-metálica o sinterizada, no la más barata.** Es la "
            "palanca más efectiva que queda para aligerar el pedal, y cuesta unos pesos.\n\n")

    f.write("## 4. Térmico\n\n")
    f.write(f"Frenada de pánico desde 100 km/h: **{E_PANICO/1000:.0f} kJ** que hay que "
            "convertir en calor.\n\n")
    f.write("| | Masa de la corona | Energía por disco | Subida de temperatura |\n|---|---|---|---|\n")
    f.write(f"| Disco delantero Ø{DISCO_DEL*1000:.0f} | {m_disco_del:.2f} kg | "
            f"{PHI*E_PANICO/2/1000:.0f} kJ | **+{dT_del:.0f} °C** |\n")
    f.write(f"| Disco trasero Ø{DISCO_TRAS*1000:.0f} | {m_disco_tras:.2f} kg | "
            f"{(1-PHI)*E_PANICO/2/1000:.0f} kJ | **+{dT_tras:.0f} °C** |\n\n")
    if max(dT_del, dT_tras) < 350:
        f.write("Una frenada aislada no es problema. El riesgo real son las frenadas "
                "repetidas: sin ventilación forzada, el tercer o cuarto pánico seguido ya "
                "llega a temperatura de fade con pastilla orgánica.\n\n")
    else:
        f.write("**Ojo:** una sola frenada de pánico ya sube demasiado la temperatura — hay "
                "que subir masa de disco o pasar a disco ventilado.\n\n")
    f.write(f"Bajada sostenida al {PEND*100:.0f}% a {V_BAJADA*3.6:.0f} km/h: "
            f"**{P_BAJADA/1000:.1f} kW** continuos. Los dos QS273 aguantan "
            f"{P_REGEN_DISP/1000:.0f} kW nominales, así que **en bajada el regen se lo come "
            "entero y los discos ni se enteran** — siempre que la batería tenga dónde meter "
            "la energía. Con la batería llena el regen se corta: en bajada larga hay que "
            "salir con la batería por debajo del 90%.\n\n")

    f.write("## 5. Regen — dónde está su límite\n\n")
    f.write(f"Los dos QS273 dan {PAR_REGEN:.0f} N·m por rueda de regen → {F_REGEN:.0f} N → "
            f"**{A_REGEN:.2f}g**. Eso cubre casi todo el frenado de diario.\n\n")
    f.write(f"**Pero el regen actúa SOLO atrás.** A {A_REGEN:.2f}g el eje trasero tiene que "
            f"generar toda esa fuerza él solo, lo que le exige un coeficiente de adherencia "
            f"de **µ = {MU_REGEN:.2f}**:\n\n")
    f.write(f"- Pavimento seco (µ ≈ 0.9): sobra. ✓\n")
    f.write(f"- Mojado o terracería (µ ≈ 0.4): **el eje trasero se bloquea** y el carro se "
            f"sale de cola, sin que el piloto haya tocado el pedal.\n\n")
    f.write(f"**Configuración obligatoria en los controladores:** limitar el regen a "
            f"~**{a_seguro:.2f}g** (el punto donde el trasero solo exige µ 0.40), y ponerlo "
            "progresivo con el pedal en vez de todo-o-nada al soltar el acelerador. Es un "
            "parámetro de software: se afina en F3 y no cuesta hardware. Sin esto el carro "
            "es peligroso en piso mojado.\n\n")

    f.write("## 6. Freno de estacionamiento\n\n")
    f.write(f"Con motores de cubo no hay transmisión donde \"dejarlo en velocidad\": el freno "
            f"de mano es la única cosa que sujeta el carro. Se resuelve con **caliper trasero "
            f"con palanca mecánica integrada** — la misma pinza hace freno de servicio y de "
            f"mano, sin ménsulas ni pinzas extra, y la placa de torque ya tiene su montaje.\n\n")
    f.write(f"En pendiente del {PEND_PARK*100:.0f}% (la más fuerte que se ve en calle):\n\n")
    f.write(f"- Fuerza a sujetar: {F_PARK:.0f} N · adherencia que exige al eje trasero: "
            f"**µ = {MU_PARK:.2f}** (sobra con cualquier piso decente) ✓\n")
    f.write(f"- Par por rueda trasera: {T_PARK:.0f} N·m → fuerza de apriete de la palanca "
            f"**{F_CLAMP_PARK/1000:.1f} kN**\n\n")
    f.write("Un caliper de palanca de cable entrega 3-5 kN, así que cumple con margen. "
            "**Al comprar:** verificar que el patrón de barrenos coincida con las orejas de "
            f"la placa de torque ({82:.0f} mm de separación, a "
            f"{110:.0f} mm de radio); si no, se re-corre `placa_torque.py` con las cotas "
            "nuevas — son 5 minutos.\n\n")

    f.write("## 7. Lista de compra de esta sección\n\n")
    f.write(f"- 2 × disco delantero Ø{DISCO_DEL*1000:.0f} mm × 5 mm (macizo) + ménsula de "
            "adaptación a la maza del ATV (corte láser)\n")
    f.write(f"- 2 × caliper delantero de área de pistón ≥ {A_DEL*1e6:.0f} mm² "
            f"(equivalente a un pistón de Ø{2*np.sqrt(A_DEL/np.pi)*1000:.0f} mm) + ménsula\n")
    f.write(f"- 2 × caliper trasero **con palanca de freno de mano**, área de pistón ≥ "
            f"{A_TRAS*1e6:.0f} mm² (Ø{D_TRAS_EQ*1000:.0f} mm equivalente); el disco lo trae "
            "el QS273\n")
    f.write(f"- 1 × bomba de freno Ø{elegido['bore_del']*1000:.1f} mm (circuito delantero) + "
            f"1 × Ø{elegido['bore_tras']*1000:.1f} mm (trasero) + barra de balance ajustable "
            "+ depósitos\n")
    f.write(f"- 1 × pedal de freno colgante o de piso, relación **{elegido['ratio']:.1f}:1**\n")
    f.write("- Manguera flexible DOT (4 tramos) + línea rígida de acero + niples; líquido DOT4\n")
    f.write("- 1 × palanca de freno de mano con cable doble + tensores\n\n")
    f.write("**Nunca recortar aquí** (doc maestro §9): frenos es de las cuatro cosas donde no "
            "se ahorra.\n")

# ============================================================================
# 9. GRÁFICA
# ============================================================================
fig, axs = plt.subplots(2, 2, figsize=(13, 8.6), facecolor="#0d1117")
for ax in axs.flat:
    ax.set_facecolor("#0d1117"); ax.grid(color="#21262d", lw=0.6)
    ax.tick_params(colors="#8b949e", labelsize=8.5)
    for sp in ax.spines.values(): sp.set_color("#30363d")

ax = axs[0, 0]
ax.plot(aa, reparto_ideal * 100, color="#38bdf8", lw=2.2, label="reparto ideal")
ax.axhline(PHI * 100, color="#f97316", lw=2.2, label=f"barra de balance ({PHI*100:.0f}%)")
ax.axvline(A_OBJ, color="#8b949e", lw=1, ls="--")
ax.fill_between(aa, reparto_ideal * 100, 100, color="#4ade80", alpha=0.10)
ax.text(0.12, 92, "zona segura:\nbloquea primero adelante", color="#4ade80", fontsize=8)
ax.set_ylim(30, 100)
ax.set_title("Reparto de frenado adelante (%)", color="#e6edf3", fontsize=10)
ax.set_xlabel("deceleración (g)", color="#8b949e", fontsize=9)
ax.legend(facecolor="#0d1117", edgecolor="#30363d", labelcolor="#e6edf3", fontsize=8)

ax = axs[0, 1]
ax.plot(aa, mu_del, color="#f97316", lw=2.2, label="eje delantero")
ax.plot(aa, mu_tras, color="#c084fc", lw=2.2, label="eje trasero")
ax.plot(aa, aa, color="#8b949e", lw=1, ls=":", label="µ disponible = a/g")
ax.axhline(0.40, color="#f87171", lw=1, ls="--")
ax.text(0.05, 0.42, "mojado / terraceria", color="#f87171", fontsize=8)
ax.set_ylim(0, 1.4)
ax.set_title("Adherencia que exige cada eje\n(el de arriba bloquea primero → debe ser el delantero)",
             color="#e6edf3", fontsize=10)
ax.set_xlabel("deceleración (g)", color="#8b949e", fontsize=9)
ax.legend(facecolor="#0d1117", edgecolor="#30363d", labelcolor="#e6edf3", fontsize=8)

ax = axs[1, 0]
# Fuerza vs recorrido: cada disco es una hipérbola (su trabajo de pedal es fijo);
# moverse sobre la curva = cambiar bomba o relación, y no sirve de nada.
rr_ = np.linspace(20, 130, 200)
for d in DISCOS_DEL:
    w = trabajo_pedal(d)
    ax.plot(rr_, w / (rr_ / 1000), lw=1.8,
            color="#4ade80" if abs(d - DISCO_DEL) < 1e-9 else "#3a4a5a",
            label=f"disco Ø{d*1000:.0f}" if abs(d - DISCO_DEL) < 1e-9 or d in (0.180, 0.260) else None)
ax.add_patch(plt.Rectangle((0, 0), REC_PEDAL_MAX, F_PEDAL_MAX, color="#4ade80", alpha=0.10))
ax.text(4, F_PEDAL_MAX * 0.55, "zona\naceptable", color="#4ade80", fontsize=8)
for c in combos:
    if abs(c["disco"] - DISCO_DEL) < 1e-9:
        ax.plot(c["rec"], c["f"], marker="o", ms=3.5,
                color="#4ade80" if c["ok"] else "#8b949e", zorder=4)
ax.plot(elegido["rec"], elegido["f"], marker="*", ms=18, color="#f97316", zorder=5)
ax.set_xlim(0, 130); ax.set_ylim(0, 900)
ax.set_title("Fuerza de pedal × recorrido = invariante\n"
             "(bomba y relación solo mueven el punto sobre su curva)",
             color="#e6edf3", fontsize=10)
ax.set_xlabel("recorrido de pedal (mm)", color="#8b949e", fontsize=9)
ax.set_ylabel("fuerza de pedal (N)", color="#8b949e", fontsize=9)
ax.legend(facecolor="#0d1117", edgecolor="#30363d", labelcolor="#e6edf3", fontsize=8)

ax = axs[1, 1]
n = np.arange(1, 7)
ax.plot(n, 25 + dT_del * n, marker="o", color="#f97316", lw=2, label=f"disco del. Ø{DISCO_DEL*1000:.0f}")
ax.plot(n, 25 + dT_tras * n, marker="o", color="#c084fc", lw=2, label=f"disco tras. Ø{DISCO_TRAS*1000:.0f}")
ax.axhline(350, color="#f87171", lw=1.4, ls="--")
ax.text(1.1, 365, "fade de pastilla organica", color="#f87171", fontsize=8)
ax.set_title("Frenadas de pánico seguidas desde 100 km/h\n(sin enfriamiento entre ellas)",
             color="#e6edf3", fontsize=10)
ax.set_xlabel("número de frenadas", color="#8b949e", fontsize=9)
ax.set_ylabel("°C", color="#8b949e", fontsize=9)
ax.legend(facecolor="#0d1117", edgecolor="#30363d", labelcolor="#e6edf3", fontsize=8)

fig.suptitle(f"Frenos — 4 discos, doble bomba con balance, sin booster · "
             f"{MASA:.0f} kg a {A_OBJ:.1f}g", color="#e6edf3", fontsize=12)
fig.tight_layout()
out_png = os.path.join(HERE, "frenos.png")
fig.savefig(out_png, dpi=150, facecolor="#0d1117", bbox_inches="tight")

print(f"reparto: minimo {phi_min*100:.1f}% -> elegido {PHI*100:.0f}% adelante")
print(f"par: delantero {T_del:.0f} N.m  trasero {T_tras:.0f} N.m")
print(f"disco delantero elegido {DISCO_DEL*1000:.0f} mm, piston {A_DEL*1e6:.0f} mm2 "
      f"(D eq {2*np.sqrt(A_DEL/np.pi)*1000:.0f} mm)")
print(f"trasero: piston {A_TRAS*1e6:.0f} mm2 (D eq {D_TRAS_EQ*1000:.0f} mm)")
print(f"pedalera: bombas {elegido['bore_del']*1000:.1f}/{elegido['bore_tras']*1000:.1f} mm "
      f"ratio {elegido['ratio']:.1f} -> {elegido['f']:.0f} N, recorrido {elegido['rec']:.0f} mm "
      f"({len(validos)} combinaciones validas de {len(combos)})")
print(f"termico: dT delantero {dT_del:.0f} C  trasero {dT_tras:.0f} C")
print(f"regen: {A_REGEN:.2f}g exige mu {MU_REGEN:.2f} atras -> limitar a {a_seguro:.2f}g")
print(f"parking: mu {MU_PARK:.2f}, clamp {F_CLAMP_PARK/1000:.1f} kN")
print(f"OK  informe: {out_md}\nOK  grafica: {out_png}")
