# -*- coding: utf-8 -*-
"""
Suspensión delantera — horquillas dobles (double wishbone), diseño y cinemática 3D.

Entradas fijas: los anclajes reales del chasis (nodos fb_lo/fb_hi/fx_lo/fx_hi de
analisis_chasis.py), rueda 175/70R13 delantera (sin motor: los QS273 van atrás),
mangueta tipo ATV con rótulas cónicas.

Método: cinemática de cuerpo rígido exacta. El brazo inferior se barre en su eje;
para cada posición se resuelve (fsolve) el ángulo del brazo superior y la posición
del extremo de la varilla de dirección que satisfacen las distancias rígidas de la
mangueta y el largo del tie rod. La rueda viaja como cuerpo rígido anclado al triedro
(LBJ, UBJ, TR). De ahí salen las curvas REALES de camber, convergencia (bump steer),
cambio de trocha, motion ratio del coilover y el centro de balanceo.

Salidas:
  calculos/resultados-suspension-delantera.md   informe con especificaciones
  calculos/suspension-delantera.png             curvas + diagrama en vista frontal
"""
import numpy as np
from scipy.optimize import fsolve
import os

HERE = os.path.dirname(os.path.abspath(__file__))

# ---------------- rueda y masas ----------------
# 175/70R13: diámetro = 13*25.4 + 2*0.70*175 = 575 mm
R_RUEDA = 0.2876          # m, radio de la llanta
ANCHO_LLANTA = 0.177
MASA_TOTAL = 690.0        # kg: 540 en vacío + 2 ocupantes (150)
DIST_DEL = 0.38           # fracción de peso al eje delantero (doc maestro: 38/62)
M_NOSUSP = 18.0           # kg no suspendidos por esquina del. (rueda+mangueta+freno+½brazos)
FREC_OBJ = 1.9            # Hz, frecuencia de rebote objetivo (deportivo cómodo p/ topes)

m_esq = MASA_TOTAL * DIST_DEL / 2          # masa por esquina delantera
m_susp = m_esq - M_NOSUSP                  # masa suspendida por esquina

# ---------------- puntos duros (m, lado izquierdo z+) ----------------
# Anclajes al chasis (los nodos existentes; los pivotes superiores llevan ménsula
# que baja el eje 63 mm bajo el tubo fb_hi–fx_hi para lograr la geometría).
# Valores afinados por barrido numérico (2026-07-06): ganancia de camber -0.49°/25mm,
# RC +8 mm. No mover sin re-correr el barrido.
# ACTUALIZADO 2026-08-05: la cremallera pasó de (410, 207, 510) a (370, 207, 504) por
# el barrido de `direccion.py`, que lleva el Ackermann de +42% a +87% y de paso BAJA el
# bump steer de 0.043 a 0.028°/25mm. Este archivo es la única fuente de la geometría
# delantera: `direccion.py` la importa de aquí.
UA_Y = float(os.environ.get("SUSP_UA_Y", "0.417"))     # altura eje pivote superior
# RESUELTO 2026-08-05. A 207 mm de altura el tie rod atravesaba el larguero inferior
# del chasis (la rótula quedaba DENTRO del tubo) y no había salida moviendo solo la
# cremallera: de 1561 posiciones libres, la mejor daba 2.7°/25mm de bump steer.
# La salida fue subir TODO el plano de dirección —rótula de cremallera Y terminal en la
# mangueta— por encima del larguero. El tie rod sigue el mismo arco que el brazo, así
# que el bump steer se conserva: **0.057°/25mm con 46.5 mm de holgura**. Cuesta un
# brazo de dirección fabricado en la mangueta (que ya hacía falta por el Ackermann).
# Se toma la posición que certifica `holguras.py`, que es el chequeo MÁS ESTRICTO
# (revisa todos los tubos del chasis, no solo los de la caja frontal). El barrido de
# `direccion.py` prefiere x=361 por 3 puntos más de Ackermann, pero ahí la holgura
# queda al filo. Entre Ackermann y poder montar la pieza, gana poder montarla.
RACK_X = float(os.environ.get("SUSP_RACK_X", "0.430")) # posición longitudinal
RACK_Y = float(os.environ.get("SUSP_RACK_Y", "0.310")) # altura rótula de cremallera
RACK_Z = float(os.environ.get("SUSP_RACK_Z", "0.520")) # posición lateral de la rótula
TR_Y   = float(os.environ.get("SUSP_TR_Y",  "0.310"))  # altura del brazo de mangueta

LA1 = np.array([0.35, 0.200, 0.50])   # pivote brazo inf. delantero (en nodo fb_lo)
LA2 = np.array([0.75, 0.200, 0.55])   # pivote brazo inf. trasero  (en nodo fx_lo)
UA1 = np.array([0.35, UA_Y, 0.50])    # pivote brazo sup. delantero (ménsula bajo fb_hi)
UA2 = np.array([0.75, UA_Y, 0.55])    # pivote brazo sup. trasero  (ménsula bajo fx_hi)

LBJ0 = np.array([0.545, 0.190, 0.710])   # rótula inferior (caster: adelante del eje)
UBJ0 = np.array([0.565, 0.425, 0.685])   # rótula superior (atrás y arriba → caster +)

RACK = np.array([RACK_X, RACK_Y, RACK_Z]) # extremo de la cremallera (rótula axial)
TR0  = np.array([0.430, TR_Y, 0.695])    # terminal de dirección en la mangueta

W0 = np.array([0.55, R_RUEDA, 0.75])     # centro de rueda (trocha del. 1.50 m)
CAMBER_EST = -1.0                        # ° camber estático
a0 = np.array([0.0, np.sin(np.radians(-CAMBER_EST)), np.cos(np.radians(-CAMBER_EST))])
S0 = W0 + 0.10 * a0                      # punto del eje del husillo (define camber/toe)

# Coilover: del brazo inferior a una ménsula en la caja frontal.
# CORREGIDO 2026-08-05: el anclaje superior estaba EN el nodo fx_hi (750,480,550) y
# desde ahí el coilover pasaba a 2.6 mm de la pata trasera de la horquilla superior —
# se atravesaban. Se movió a (700,480,480), sobre una ménsula 50 mm adelante y 70 mm
# adentro del nodo, que da 62 mm de holgura contra brazos y tubos (`holguras.py`) y
# CONSERVA el motion ratio en 0.59, así que el resorte de 270 lb/in no cambia.
SHK_SUP = np.array([0.70, 0.48, 0.48])   # ménsula sobre el travesaño fx_hi
SHK_INF0 = np.array([0.58, 0.215, 0.66]) # sobre el brazo inferior, al 75% hacia la rótula

# ---------------- cinemática de cuerpo rígido ----------------
def rot_eje(A, B, th, p):
    """rota el punto p un ángulo th alrededor del eje A→B (Rodrigues)"""
    u = (B - A) / np.linalg.norm(B - A)
    v = p - A
    return A + (v * np.cos(th) + np.cross(u, v) * np.sin(th)
                + u * np.dot(u, v) * (1 - np.cos(th)))

# distancias rígidas de la mangueta y largo del tie rod (se conservan siempre)
d_kp = np.linalg.norm(UBJ0 - LBJ0)
d_lt = np.linalg.norm(TR0 - LBJ0)
d_ut = np.linalg.norm(TR0 - UBJ0)
d_tr = np.linalg.norm(TR0 - RACK)

# el centro de rueda y el husillo viajan anclados al triedro (LBJ, UBJ, TR)
def base(lbj, ubj, tr):
    e1 = ubj - lbj; e2 = tr - lbj; e3 = np.cross(e1, e2)
    return np.column_stack([e1, e2, e3])

Minv = np.linalg.inv(base(LBJ0, UBJ0, TR0))
cW = Minv @ (W0 - LBJ0)
cS = Minv @ (S0 - LBJ0)
cSh = None  # el coilover va en el brazo inferior, no en la mangueta

def resolver(thL, x0):
    """dado el ángulo del brazo inferior, resuelve brazo superior + tie rod"""
    lbj = rot_eje(LA1, LA2, thL, LBJ0)
    def eqs(x):
        thU, tx, ty, tz = x
        ubj = rot_eje(UA1, UA2, thU, UBJ0)
        tr = np.array([tx, ty, tz])
        return [np.linalg.norm(ubj - lbj) - d_kp,
                np.linalg.norm(tr - lbj) - d_lt,
                np.linalg.norm(tr - ubj) - d_ut,
                np.linalg.norm(tr - RACK) - d_tr]
    x = fsolve(eqs, x0, full_output=False)
    thU = x[0]
    ubj = rot_eje(UA1, UA2, thU, UBJ0)
    tr = np.array(x[1:4])
    M = base(lbj, ubj, tr)
    W = lbj + M @ cW
    a = (lbj + M @ cS - W) / 0.10
    shk = rot_eje(LA1, LA2, thL, SHK_INF0)
    return x, W, a, shk

# ---------------- barrido de recorrido ----------------
CARRERA = 0.070   # m de recorrido de rueda a cada lado
ths = np.linspace(-0.38, 0.38, 121)
filas = []
x0 = np.array([0.0, *TR0])
for thL in ths:
    x0, W, a, shk = resolver(thL, x0)
    camber = -np.degrees(np.arctan2(a[1], a[2]))
    f = np.cross(np.array([0, 1.0, 0]), a)          # dirección de avance de la rueda
    toe = np.degrees(np.arctan2(-f[2], f[0]))       # + = convergencia (toe-in)
    filas.append(dict(thL=thL, y=W[1], z=W[2], camber=camber, toe=toe,
                      largo_shk=np.linalg.norm(SHK_SUP - shk)))

# recorte a la carrera útil y referencia estática
y0 = [f_["y"] for f_ in filas if abs(f_["thL"]) < 1e-9][0]
filas = [f_ for f_ in filas if -CARRERA <= f_["y"] - y0 <= CARRERA]
viaje = np.array([f_["y"] - y0 for f_ in filas]) * 1000        # mm (+ = compresión)
camber = np.array([f_["camber"] for f_ in filas])
toe = np.array([f_["toe"] for f_ in filas])
trocha = (np.array([f_["z"] for f_ in filas]) - W0[2]) * 1000  # mm
Lshk = np.array([f_["largo_shk"] for f_ in filas]) * 1000      # mm

i0 = int(np.argmin(np.abs(viaje)))
MR = -np.gradient(Lshk, viaje)          # compresión de shock por mm de rueda
mr0 = MR[i0]

# ---------------- características estáticas ----------------
kp = UBJ0 - LBJ0
kpi = np.degrees(np.arctan2(abs(kp[2]), kp[1]))
caster = np.degrees(np.arctan2(kp[0], kp[1]))
z_suelo = LBJ0[2] - kp[2] / kp[1] * LBJ0[1]
scrub = (W0[2] - z_suelo) * 1000
trail = (np.tan(np.radians(caster)) * R_RUEDA) * 1000

# centro de balanceo: RC = semitrocha × d(migración lateral)/d(recorrido vertical)
dzdy = np.gradient(trocha, viaje)[i0]
h_rc = W0[2] * dzdy * 1000              # mm

# ---------------- resortes y coilover ----------------
k_rueda = (2 * np.pi * FREC_OBJ) ** 2 * m_susp          # N/m tasa en la rueda
k_resorte = k_rueda / mr0 ** 2                          # N/m tasa del resorte
lbin = k_resorte / 1000 / 0.175127                      # lb/in
F_est_shk = m_susp * 9.81 / mr0                         # N carga estática en el shock
F_3g_shk = 3 * m_susp * 9.81 / mr0                      # N en bache 3g (para la torre)
carrera_shk = (Lshk.max() - Lshk.min())                 # mm de carrera usada
c_crit = 2 * np.sqrt(k_rueda * m_susp)                  # N·s/m amortiguación crítica

# bump steer: peor pendiente de toe en ±50 mm
sel = np.abs(viaje) <= 50
bs = np.max(np.abs(np.gradient(toe, viaje)[sel])) * 25  # °/25mm

# largos de fabricación
def largo(a, b): return np.linalg.norm(a - b) * 1000
resumen_brazos = {
    "brazo inf. tubo del.": largo(LA1, LBJ0),
    "brazo inf. tubo tras.": largo(LA2, LBJ0),
    "brazo sup. tubo del.": largo(UA1, UBJ0),
    "brazo sup. tubo tras.": largo(UA2, UBJ0),
    "tie rod (centro-centro)": largo(RACK, TR0),
}

# ---------------- informe ----------------
out_md = os.path.join(HERE, "resultados-suspension-delantera.md")
with open(out_md, "w", encoding="utf-8") as f:
    f.write("# Suspensión delantera — geometría, cinemática y especificación\n\n")
    f.write("Horquillas dobles + coilover a la torre `fx_hi`. Cinemática 3D exacta de cuerpo rígido "
            "(`suspension_delantera.py`). Rueda 175/70R13, trocha delantera 1.50 m.\n\n")
    f.write("## Puntos duros (mm, lado izquierdo; el derecho es espejo)\n\n")
    f.write("| Punto | x | y | z | Nota |\n|---|---|---|---|---|\n")
    for nom, p, nota in [
        ("Pivote inf. del.", LA1, "en nodo fb_lo del chasis"),
        ("Pivote inf. tras.", LA2, "en nodo fx_lo"),
        ("Pivote sup. del.", UA1, f"ménsula {480-UA_Y*1000:.0f} mm bajo fb_hi"),
        ("Pivote sup. tras.", UA2, f"ménsula {480-UA_Y*1000:.0f} mm bajo fx_hi"),
        ("Rótula inferior LBJ", LBJ0, "cónica tipo ATV"),
        ("Rótula superior UBJ", UBJ0, "cónica tipo ATV"),
        ("Extremo cremallera", RACK, "rótula axial"),
        ("Terminal dirección", TR0, "en brazo de mangueta"),
        ("Centro de rueda", W0, "175/70R13"),
        ("Coilover inferior", SHK_INF0, "sobre brazo inf., 75% a la rótula"),
        ("Coilover superior", SHK_SUP, "torre fx_hi (nodo del FEM)"),
    ]:
        f.write(f"| {nom} | {p[0]*1000:.0f} | {p[1]*1000:.0f} | {p[2]*1000:.0f} | {nota} |\n")
    f.write("\n## Alineación estática\n\n")
    f.write(f"| Parámetro | Valor | Típico deportivo |\n|---|---|---|\n")
    f.write(f"| Camber | {CAMBER_EST:.1f}° | −0.5 a −1.5° |\n")
    f.write(f"| Caster | {caster:.1f}° | 3–7° |\n")
    f.write(f"| Inclinación de kingpin | {kpi:.1f}° | 6–12° |\n")
    f.write(f"| Radio de pivotamiento (scrub) | {scrub:.0f} mm | <40 mm |\n")
    f.write(f"| Avance mecánico (trail) | {trail:.0f} mm | 15–30 mm |\n")
    f.write(f"| Centro de balanceo | {h_rc:.0f} mm | 30–100 mm |\n")
    f.write(f"| Convergencia | 0° (ajustar 1–2 mm toe-in total en piso) | |\n\n")
    f.write("## Cinemática en el recorrido (±70 mm)\n\n")
    f.write(f"- Ganancia de camber: **{(camber[-1]-camber[i0])/ (viaje[-1]) * 25:.2f}°/25 mm** en compresión "
            f"(la rueda se inclina hacia adentro al comprimir: correcto).\n")
    f.write(f"- Bump steer máximo: **{bs:.3f}°/25 mm** en ±50 mm — "
            f"{'excelente (<0.1)' if bs < 0.1 else 'ALTO: revisar altura de cremallera'}.\n")
    f.write(f"- Cambio de semitrocha: {trocha.min():.1f} a {trocha.max():.1f} mm.\n")
    f.write(f"- Motion ratio del coilover: **{mr0:.2f}** (shock/rueda) — casi constante en el recorrido.\n\n")
    f.write("## Resortes y coilover (especificación de compra)\n\n")
    f.write(f"- Masa por esquina: {m_esq:.0f} kg ({m_susp:.0f} suspendida) · frecuencia objetivo {FREC_OBJ} Hz.\n")
    f.write(f"- Tasa en rueda {k_rueda/1000:.1f} N/mm → **resorte {k_resorte/1000:.0f} N/mm ≈ {lbin:.0f} lb/in**.\n")
    f.write(f"- Largo ojo-a-ojo estático: **{Lshk[i0]:.0f} mm** · carrera usada: {carrera_shk:.0f} mm → "
            f"pedir coilover ~{round((Lshk[i0]+ (Lshk.max()-Lshk[i0]))/10)*10:.0f} mm extendido, carrera ≥{carrera_shk/ mr0 * mr0 + 15:.0f} mm.\n")
    f.write(f"- Carga estática por shock: {F_est_shk:.0f} N · en bache 3g: **{F_3g_shk:.0f} N** "
            f"(carga de diseño de la ménsula en la torre, con FS 2 soldar para {2*F_3g_shk/1000:.1f} kN).\n")
    f.write(f"- Amortiguación crítica en rueda {c_crit:.0f} N·s/m → ajustar ζ≈0.5–0.7 (coilover con clicks).\n\n")
    f.write("## Largos de fabricación de brazos (centro a centro, mm)\n\n")
    for k, v in resumen_brazos.items():
        f.write(f"- {k}: **{v:.0f} mm**\n")
    f.write("\n## Piezas (BOM parcial de esta sección)\n\n")
    f.write("- 4 × rótula cónica ATV (tipo Honda TRX300/Rancher) — LBJ y UBJ por lado\n")
    f.write("- 8 × buje de poliuretano + tubo interno para pivotes de brazos (Ø12 mm)\n")
    f.write("- Tubo redondo 25.4×2.1 mm para brazos (~2.1 m total delantero)\n")
    f.write("- 2 × coilover con resorte según spec de arriba\n")
    f.write("- 2 × terminal de dirección ATV + cremallera manual de compacto (donante)\n")
    f.write("- Mangueta/maza/freno: donante ATV 300 (verificar cono de rótulas al comprar)\n\n")
    f.write(f"**Notas:** los pivotes superiores requieren ménsulas que bajen el eje {480-UA_Y*1000:.0f} mm "
            "bajo el tubo superior (la geometría de camber/centro de balanceo lo exige); cortarlas en "
            "láser junto con las cartelas. La altura de la cremallera es SENSIBLE: ±5 mm duplican el "
            "bump steer — montarla con barrenos ovalados y calzas para afinar en el carro. Rines 13\" "
            "requieren verificar que la mangueta donante quepa (ATV usa 12\"; medir antes de comprar). "
            "La convergencia se ajusta con el largo del tie rod.\n")

# ---------------- gráfica ----------------
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

fig, axs = plt.subplots(2, 2, figsize=(12.5, 8.5), facecolor="#0d1117")
for ax in axs.flat:
    ax.set_facecolor("#0d1117"); ax.grid(color="#21262d", lw=0.6)
    ax.tick_params(colors="#8b949e", labelsize=8.5)
    for sp in ax.spines.values(): sp.set_color("#30363d")

# (1) vista frontal con la geometría real
ax = axs[0, 0]
zz = lambda p: p[2] * 1000; yy = lambda p: p[1] * 1000
mid = lambda a, b: (a + b) / 2
ax.add_patch(plt.Rectangle((zz(W0) - ANCHO_LLANTA*500, 0), ANCHO_LLANTA*1000, 2*R_RUEDA*1000,
             fill=False, edgecolor="#8b949e", lw=1.4))
ax.plot([zz(mid(LA1, LA2)), zz(LBJ0)], [yy(mid(LA1, LA2)), yy(LBJ0)], color="#f97316", lw=3)
ax.plot([zz(mid(UA1, UA2)), zz(UBJ0)], [yy(mid(UA1, UA2)), yy(UBJ0)], color="#f97316", lw=3)
ax.plot([zz(LBJ0), zz(UBJ0)], [yy(LBJ0), yy(UBJ0)], color="#38bdf8", lw=2, ls="--")
ax.plot([zz(RACK), zz(TR0)], [yy(RACK), yy(TR0)], color="#4ade80", lw=2)
ax.plot([zz(SHK_SUP), zz(SHK_INF0)], [yy(SHK_SUP), yy(SHK_INF0)], color="#c084fc", lw=2.5)
ax.plot([0], [h_rc], marker="o", color="#f87171", ms=7)
ax.annotate(f"RC {h_rc:.0f} mm", (0, h_rc), textcoords="offset points", xytext=(8, 6),
            color="#f87171", fontsize=9)
ax.axhline(0, color="#30363d", lw=1)
ax.plot([0, 0], [0, 1100], color="#21262d", lw=1, ls=":")
ax.set_xlim(-80, 980); ax.set_ylim(-40, 700); ax.set_aspect("equal")
ax.set_title("Vista frontal (mm): brazos, kingpin, tie rod, coilover", color="#e6edf3", fontsize=10)

# (2) camber
ax = axs[0, 1]
ax.plot(viaje, camber, color="#f97316", lw=2)
ax.axvline(0, color="#30363d", lw=1)
ax.set_title("Camber vs recorrido (− = arriba hacia adentro)", color="#e6edf3", fontsize=10)
ax.set_xlabel("recorrido de rueda (mm, + compresión)", color="#8b949e", fontsize=9)
ax.set_ylabel("camber (°)", color="#8b949e", fontsize=9)

# (3) toe / bump steer
ax = axs[1, 0]
ax.plot(viaje, toe * 60, color="#4ade80", lw=2)
ax.axvline(0, color="#30363d", lw=1)
ax.set_title("Convergencia vs recorrido (bump steer)", color="#e6edf3", fontsize=10)
ax.set_xlabel("recorrido de rueda (mm)", color="#8b949e", fontsize=9)
ax.set_ylabel("toe (minutos de arco)", color="#8b949e", fontsize=9)

# (4) motion ratio
ax = axs[1, 1]
ax.plot(viaje, MR, color="#c084fc", lw=2)
ax.axvline(0, color="#30363d", lw=1)
ax.set_title(f"Motion ratio del coilover (estático {mr0:.2f})", color="#e6edf3", fontsize=10)
ax.set_xlabel("recorrido de rueda (mm)", color="#8b949e", fontsize=9)
ax.set_ylabel("mm de shock / mm de rueda", color="#8b949e", fontsize=9)

fig.suptitle("Suspensión delantera — cinemática real de los puntos duros elegidos",
             color="#e6edf3", fontsize=12)
fig.tight_layout()
out_png = os.path.join(HERE, "suspension-delantera.png")
fig.savefig(out_png, dpi=150, facecolor="#0d1117", bbox_inches="tight")

print(f"camber estatico {CAMBER_EST:.1f}°  caster {caster:.1f}°  KPI {kpi:.1f}°  "
      f"scrub {scrub:.0f} mm  trail {trail:.0f} mm  RC {h_rc:.0f} mm")
print(f"ganancia camber {(camber[-1]-camber[i0])/(viaje[-1])*25:.2f}°/25mm  "
      f"bump steer {bs:.3f}°/25mm  MR {mr0:.2f}")
print(f"resorte {k_resorte/1000:.1f} N/mm ({lbin:.0f} lb/in)  shock estatico {Lshk[i0]:.0f} mm  "
      f"carrera {carrera_shk:.0f} mm  F_3g {F_3g_shk:.0f} N")
print(f"OK  informe: {out_md}\nOK  grafica: {out_png}")
