# -*- coding: utf-8 -*-
"""
Suspensión trasera — brazo tirado (swingarm) con motor de cubo QS273.

La arquitectura más simple que existe: un brazo que pivotea en el nodo `ta` del
chasis, el motor DENTRO de la rueda al final del brazo, y un coilover a la torre
`coil`. Sin flechas, sin juntas homocinéticas, sin brazos múltiples. Como una
moto, pero por lado.

Este script resuelve la ingeniería real de esa sencillez:
  - cinemática del brazo (recorrido, motion ratio, cambio de distancia entre ejes)
  - anti-squat / anti-lift con motor de cubo (la línea de empuje pasa por el pivote)
  - tasa de resorte y spec de compra del coilover
  - sección del brazo verificada a flexión + torsión (par del motor y frenado)
  - ajuste del rin: el QS273 NO cabe en rin 13 — decisión documentada

Salidas:
  calculos/resultados-suspension-trasera.md
  calculos/suspension-trasera.png
"""
import numpy as np
import os

HERE = os.path.dirname(os.path.abspath(__file__))

# ---------------- rueda trasera y motor ----------------
# QS273: estátor de 273 mm, carcasa ~350 mm de diámetro. En rin 13" de carro
# (asiento 330 mm) NO CABE. Opciones reales:
#   A) pedir el QS273 versión "rin desmontable de carro" 14" → llanta 175/70R14
#   B) rin de moto 17×3.5 con llanta 130/70-17 (estándar QS de fábrica)
# Se diseña con la opción A (llanta de carro adelante y atrás, mismo compuesto).
R_RUEDA = 0.3005          # m, 175/70R14 (Ø601 mm; adelante 13" Ø575 → nariz 1° abajo)
MASA_TOTAL = 690.0        # kg con 2 ocupantes
DIST_TRAS = 0.53          # fracción al eje trasero. 2026-10-21: 0.62 -> 0.53 (batería en el túnel central; calculos/masas_cg.py)
M_NOSUSP = 45.0           # kg no suspendidos por esquina: motor 27 + rueda 12 + ½brazo 6
FREC_OBJ = 2.05           # Hz atrás (siempre un poco más que adelante: 1.9)
H_CG = 0.40               # m, altura del centro de gravedad. 2026-10-21: 0.33 -> 0.40 (presupuesto por componente; ocupantes, techo y puertas lo suben)

m_esq = MASA_TOTAL * DIST_TRAS / 2
m_susp = m_esq - M_NOSUSP

# ---------------- geometría (m, lado izquierdo z+) ----------------
PIV = np.array([2.28, 0.16, 0.552])   # pivote = nodo `ta` del chasis (cartela ya dibujada)
EJE0 = np.array([2.68, R_RUEDA, 0.76])# centro de rueda estático → dist. entre ejes 2.13 m
SHK_SUP = np.array([2.58, 0.712, 0.425])  # torre coilover trasera (nodo `coil` del FEM)
# T_SHK afinado por barrido (2026-07-06): 0.80 baja el resorte a ~350 lb/in y la
# carga de la torre a 7.4 kN manteniendo MR estable (0.63-0.70).
T_SHK = float(os.environ.get("SUSP_T_SHK", "0.80"))  # posición del shock en el brazo
X_EJE_DEL = 0.55                       # eje delantero (de suspension_delantera.py)

L_brazo = np.linalg.norm(EJE0[:2] - PIV[:2])         # largo efectivo en vista lateral
ang0 = np.arctan2(EJE0[1] - PIV[1], EJE0[0] - PIV[0])
# El brazo NO llega al centro de rueda: termina antes del motor, en Z_PUNTA. El
# coilover se ancla SOBRE el eje del brazo, no sobre la línea pivote–centro de rueda.
# CORREGIDO 2026-08-05: antes se anclaba en PIV+T_SHK·(EJE0−PIV), que cae 94 mm fuera
# del brazo y 47 mm DENTRO de la llanta. No existía pieza que lo llevara ahí.
Z_PUNTA = 0.640                                      # z del extremo del brazo (placa_torque)
Z_SHK = PIV[2] + T_SHK * (Z_PUNTA - PIV[2])          # z del anclaje, sobre el brazo
SHK_INF0 = np.array([*(PIV + T_SHK * (EJE0 - PIV))[:2], Z_SHK])

# ---------------- cinemática del brazo (rotación pura, sin solver) ----------------
CARRERA = 0.070
angs = np.linspace(ang0 - 0.35, ang0 + 0.35, 161)
rows = []
for a in angs:
    eje = PIV + np.array([L_brazo * np.cos(a), L_brazo * np.sin(a), EJE0[2] - PIV[2]])
    # el brazo gira alrededor de un eje lateral, así que la z del anclaje no cambia
    shk = np.array([*(PIV + T_SHK * (eje - PIV))[:2], Z_SHK])
    rows.append(dict(a=a, y=eje[1], x=eje[0], Lshk=np.linalg.norm(SHK_SUP - shk)))

y0 = EJE0[1]
rows = [r for r in rows if -CARRERA <= r["y"] - y0 <= CARRERA]
viaje = np.array([r["y"] - y0 for r in rows]) * 1000         # mm, + = compresión
Lshk = np.array([r["Lshk"] for r in rows]) * 1000
d_eje = (np.array([r["x"] for r in rows]) - EJE0[0]) * 1000  # cambio de batalla
MR = -np.gradient(Lshk, viaje)
i0 = int(np.argmin(np.abs(viaje)))
mr0 = MR[i0]

# ---------------- anti-squat con motor de cubo ----------------
# Con motor EN la rueda, la fuerza de tracción reacciona por el brazo: la línea de
# empuje va del parche de contacto al pivote. AS% = tan(θ_empuje)/(h_cg/L) × 100.
L_batalla = EJE0[0] - X_EJE_DEL
AS = []
for r in rows:
    th = np.arctan2(PIV[1], r["x"] - PIV[0])          # contacto (x,0) → pivote
    AS.append(np.tan(th) / (H_CG / L_batalla) * 100)
AS = np.array(AS)

# ---------------- resorte y coilover ----------------
k_rueda = (2 * np.pi * FREC_OBJ) ** 2 * m_susp
k_resorte = k_rueda / mr0 ** 2
lbin = k_resorte / 1000 / 0.175127
F_est = m_susp * 9.81 / mr0
F_3g = 3 * m_susp * 9.81 / mr0
c_crit = 2 * np.sqrt(k_rueda * m_susp)

# ---------------- verificación de la sección del brazo ----------------
g = 9.81
F_rueda_3g = 3 * g * m_esq                    # N, bache 3g en la rueda
F_lat_1g = g * m_esq                          # N, curva 1g en el parche
T_frenado = 0.9 * g * m_esq * R_RUEDA         # N·m, frenado ~0.9g en la rueda trasera
brazo_shk = (1 - T_SHK) * L_brazo             # el momento flector máximo es en el shock

def revisa_seccion(b, h, t):
    """PTR rectangular b(ancho)×h(alto)×t: flexión vertical + lateral + torsión"""
    bi, hi = b - 2 * t, h - 2 * t
    Iy = (b * h ** 3 - bi * hi ** 3) / 12.0       # flexión vertical (eje fuerte)
    Iz = (h * b ** 3 - hi * bi ** 3) / 12.0       # flexión lateral
    Am = (b - t) * (h - t)                        # Bredt
    sig_v = F_rueda_3g * brazo_shk * (h / 2) / Iy
    sig_l = F_lat_1g * L_brazo * (b / 2) / Iz     # lateral: brazo completo al pivote
    tau = T_frenado / (2 * Am * t)
    sig_vm = np.sqrt((sig_v + sig_l) ** 2 + 3 * tau ** 2)
    return sig_v / 1e6, sig_l / 1e6, tau / 1e6, sig_vm / 1e6, 250e6 / sig_vm

SECCIONES = [(0.050, 0.050, 0.003), (0.060, 0.040, 0.003), (0.060, 0.060, 0.003),
             (0.070, 0.050, 0.004), (0.080, 0.060, 0.004)]
tabla_sec = [(f"{int(h*1000)}×{int(b*1000)}×{t*1000:.0f}",) + revisa_seccion(b, h, t)
             for (h, b, t) in SECCIONES]
elegida = next(row[0] for row in tabla_sec if row[5] >= 2.0)

# ---------------- informe ----------------
out_md = os.path.join(HERE, "resultados-suspension-trasera.md")
with open(out_md, "w", encoding="utf-8") as f:
    f.write("# Suspensión trasera — brazo tirado con motor de cubo\n\n")
    f.write("La pieza de filosofía kart del carro: **3 componentes por lado** (brazo, pivote, "
            "coilover) y el motor dentro de la rueda. Sin flechas ni juntas. "
            f"Generado por `suspension_trasera.py`.\n\n")
    f.write("## Decisión de rin (resuelta)\n\n")
    f.write("El QS273 tiene carcasa de ~350 mm: **no cabe en rin 13\"** (asiento 330 mm). "
            "Decisión: pedir los QS273 en **versión rin desmontable de carro 14\"** con llanta "
            "**175/70R14** (Ø601 mm) — misma llanta de carro adelante (13\", Ø575) y atrás, la nariz "
            "queda ~1° abajo (postura deportiva). Alternativa si el proveedor no la tiene: rin de "
            "moto 17×3.5 con 130/70-17. **Confirmar con QS Motor por escrito antes de pagar.**\n\n")
    f.write("## Geometría\n\n")
    f.write(f"| Parámetro | Valor |\n|---|---|\n")
    f.write(f"| Pivote del brazo | nodo `ta` (2280, 160, ±552) — usa la cartela láser ya dibujada |\n")
    f.write(f"| Centro de rueda | (2680, {R_RUEDA*1000:.0f}, ±760) → trocha 1.52 m |\n")
    f.write(f"| Distancia entre ejes | **{L_batalla:.2f} m** |\n")
    f.write(f"| Largo efectivo del brazo | {L_brazo*1000:.0f} mm (barrido ±{np.degrees(np.arcsin(CARRERA/L_brazo)):.1f}° en ±70 mm) |\n")
    f.write(f"| Cambio de batalla en recorrido | {d_eje.min():+.0f} a {d_eje.max():+.0f} mm |\n")
    f.write(f"| Motion ratio | **{mr0:.2f}** (estable: {MR.min():.2f}–{MR.max():.2f}) |\n\n")
    f.write("## Anti-squat (comportamiento con motor de cubo)\n\n")
    f.write(f"La línea de empuje pasa por el pivote: anti-squat estático **{AS[i0]:.0f}%**.\n\n")
    f.write(f"- A fondo (~0.34g máx de los QS273): la cola **sube ~{(AS[i0]/100-1)*0.34*MASA_TOTAL*H_CG/L_batalla*9.81/(2*k_rueda)*1000:.0f} mm** en vez de "
            "sentarse — cabeceo leve, inofensivo a esta potencia.\n")
    f.write("- En **regen** (el freno de diario): el mismo número actúa como anti-lift — la cola se "
            "queda plantada al frenar. Para un carro que frena con regen, es la dirección correcta.\n")
    f.write("- Si en las pruebas F3 el cabeceo molesta: bajar el pivote 50 mm con ménsula → AS ~170%. "
            "Ajuste de una tarde, ya previsto.\n\n")
    f.write("**Límite conocido del brazo tirado puro:** la rueda rueda con la carrocería (en curva "
            "fuerte el camber exterior se hace positivo lo que rola el chasis, ~2°/g). A 100 km/h y "
            "0.34g de tracción es aceptable; se compensa con resortes traseros firmes (ya "
            "especificados) y toe-in estático de 1-2 mm con calzas en el pivote.\n\n")
    f.write("## Resorte y coilover (spec de compra)\n\n")
    f.write(f"- Masa por esquina {m_esq:.0f} kg ({m_susp:.0f} suspendida — el motor de cubo pesa 27 kg "
            f"y NO lo carga el resorte) · frecuencia {FREC_OBJ} Hz.\n")
    f.write(f"- Tasa en rueda {k_rueda/1000:.1f} N/mm → **resorte {k_resorte/1000:.0f} N/mm ≈ {lbin:.0f} lb/in**.\n")
    f.write(f"- Largo ojo-a-ojo estático **{Lshk[i0]:.0f} mm**, carrera usada {Lshk.max()-Lshk.min():.0f} mm → "
            f"pedir ~{round(Lshk.max()/10)*10+10:.0f} mm extendido, carrera ≥{(Lshk.max()-Lshk.min())+15:.0f} mm.\n")
    f.write(f"- Carga estática {F_est:.0f} N · bache 3g **{F_3g:.0f} N** por shock (la torre `coil` del "
            f"FEM ya soporta este caso; ménsula con FS 2 → {2*F_3g/1000:.1f} kN).\n")
    f.write(f"- Amortiguación crítica {c_crit:.0f} N·s/m → coilover con clicks, ζ 0.5–0.7.\n\n")
    f.write("## Sección del brazo (verificada a 3g + curva 1g + frenado 0.9g)\n\n")
    f.write("| PTR alto×ancho×pared | σ flexión vert. | σ lateral | τ torsión | σ von Mises | FS |\n")
    f.write("|---|---|---|---|---|---|\n")
    for (nom, sv, sl, ta_, svm, fs) in tabla_sec:
        marca = " ✓" if fs >= 2 else ""
        f.write(f"| {nom} | {sv:.0f} MPa | {sl:.0f} MPa | {ta_:.0f} MPa | {svm:.0f} MPa | **{fs:.1f}**{marca} |\n")
    f.write(f"\nElegida: **PTR {elegida}** (primera con FS≥2). El brazo es UNA pieza recta de "
            f"{L_brazo*1000+80:.0f} mm con: manga del pivote (buje poli Ø16, base ancha ≥150 mm), "
            "oreja del shock al 75%, y la punta recibe la **placa de torque del QS273**, "
            "resuelta por optimización topológica en `placa_torque.py` "
            "(ver `resultados-placa-torque.md`).\n\n")
    f.write("## BOM parcial de esta sección\n\n")
    f.write(f"- 2 × PTR {elegida}, ~0.5 m c/u (los brazos)\n")
    f.write("- 2 × kit buje poliuretano Ø16 + manga de acero (pivote, base 150 mm)\n")
    f.write(f"- 2 × coilover ~{round(Lshk.max()/10)*10+10:.0f} mm / carrera {(Lshk.max()-Lshk.min())+15:.0f} mm / resorte {lbin:.0f} lb/in\n")
    f.write("- 4 × placa de torque QS273 en acero 8 mm — 2 `placa-torque-motor.dxf` (llevan\n"
            "  integrada la ménsula del caliper) + 2 `placa-torque-refuerzo.dxf`. Van en\n"
            "  sándwich abrazando la punta del PTR. Ver `resultados-placa-torque.md`\n")
    f.write("- 4 × doblador del cubo `placa-torque-doblador.dxf`, acero 8 mm (soldado; sin él\n"
            "  el aplastamiento en los planos del eje se queda en FS 1.1)\n")
    f.write("- 16 × tornillo M12 10.9 + tuerca autoblocante, y 8 × camisa de acero soldada\n"
            "  a través del PTR (si no, el apriete aplasta el tubo)\n")
    f.write("- 2 × caliper mecánico/hidráulico de ATV (el QS273 trae disco) + separadores\n"
            "  para alcanzar el plano del disco\n")

# ---------------- gráfica ----------------
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

fig, axs = plt.subplots(2, 2, figsize=(12.5, 8.2), facecolor="#0d1117")
for ax in axs.flat:
    ax.set_facecolor("#0d1117"); ax.grid(color="#21262d", lw=0.6)
    ax.tick_params(colors="#8b949e", labelsize=8.5)
    for sp in ax.spines.values(): sp.set_color("#30363d")

ax = axs[0, 0]
xx = lambda p: p[0] * 1000; yy = lambda p: p[1] * 1000
th = np.linspace(0, 2 * np.pi, 60)
ax.plot(EJE0[0]*1000 + R_RUEDA*1000*np.cos(th), EJE0[1]*1000 + R_RUEDA*1000*np.sin(th),
        color="#8b949e", lw=1.4)
ax.plot([xx(PIV), xx(EJE0)], [yy(PIV), yy(EJE0)], color="#f97316", lw=4)
ax.plot([xx(SHK_INF0), xx(SHK_SUP)], [yy(SHK_INF0), yy(SHK_SUP)], color="#c084fc", lw=2.5)
ax.plot([2020, 3000], [160, 160], color="#30363d", lw=2)          # riel del chasis
ax.plot(xx(PIV), yy(PIV), marker="o", color="#38bdf8", ms=8)
ax.plot([xx(EJE0), xx(PIV)], [0, yy(PIV)], color="#4ade80", lw=1.2, ls="--")
ax.annotate(f"línea de empuje → AS {AS[i0]:.0f}%", (2450, 60), color="#4ade80", fontsize=8.5)
ax.annotate("pivote (nodo ta)", (xx(PIV), yy(PIV)), textcoords="offset points",
            xytext=(-10, 10), color="#38bdf8", fontsize=8.5, ha="right")
ax.axhline(0, color="#30363d", lw=1)
ax.set_xlim(1950, 3080); ax.set_ylim(-50, 800); ax.set_aspect("equal")
ax.set_title("Vista lateral (mm): brazo tirado, coilover, línea de empuje", color="#e6edf3", fontsize=10)

ax = axs[0, 1]
ax.plot(viaje, MR, color="#c084fc", lw=2); ax.axvline(0, color="#30363d", lw=1)
ax.set_title(f"Motion ratio (estático {mr0:.2f})", color="#e6edf3", fontsize=10)
ax.set_xlabel("recorrido de rueda (mm, + compresión)", color="#8b949e", fontsize=9)

ax = axs[1, 0]
ax.plot(viaje, AS, color="#4ade80", lw=2); ax.axvline(0, color="#30363d", lw=1)
ax.set_title("Anti-squat % vs recorrido", color="#e6edf3", fontsize=10)
ax.set_xlabel("recorrido de rueda (mm)", color="#8b949e", fontsize=9)

ax = axs[1, 1]
ax.plot(viaje, d_eje, color="#f97316", lw=2); ax.axvline(0, color="#30363d", lw=1)
ax.set_title("Cambio de distancia entre ejes (mm)", color="#e6edf3", fontsize=10)
ax.set_xlabel("recorrido de rueda (mm)", color="#8b949e", fontsize=9)

fig.suptitle("Suspensión trasera — brazo tirado con QS273 (filosofía kart: 3 piezas por lado)",
             color="#e6edf3", fontsize=12)
fig.tight_layout()
out_png = os.path.join(HERE, "suspension-trasera.png")
fig.savefig(out_png, dpi=150, facecolor="#0d1117", bbox_inches="tight")

print(f"brazo {L_brazo*1000:.0f} mm  batalla {L_batalla:.2f} m  MR {mr0:.2f} "
      f"(rango {MR.min():.2f}-{MR.max():.2f})  AS {AS[i0]:.0f}%")
print(f"resorte {k_resorte/1000:.1f} N/mm ({lbin:.0f} lb/in)  shock est {Lshk[i0]:.0f} mm  "
      f"carrera {Lshk.max()-Lshk.min():.0f} mm  F_3g {F_3g:.0f} N")
for (nom, sv, sl, ta_, svm, fs) in tabla_sec:
    print(f"  PTR {nom}: vM {svm:.0f} MPa  FS {fs:.2f}")
print(f"OK  informe: {out_md}\nOK  grafica: {out_png}")
