# -*- coding: utf-8 -*-
"""
SEGURIDAD DE LAS PUERTAS DE GAVIOTA (2026-10-21): viga de impacto lateral, retención (cierres y bisagras), salida de emergencia y respaldos.
Mismas coordenadas que puertas.py (x atrás, y arriba, z lateral; lado izquierdo). Escribe docs/seguridad-puertas.md.

Criterio de impacto lateral: de REFERENCIA, no homologación (el carro no es homologable). Se toma el de la prueba estática de aplastamiento de puerta
FMVSS 214: resistencia intermedia de 4.5 kN (promedio entre 150 y 300 mm de intrusión) y pico de 2 x el peso del carro (13.5 kN).
Una viga de tubo da energía por flexión plástica; el pico lo comparten sillín, piel con espuma y estructura.

    python calculos/seguridad_puertas.py
"""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
import buck_piloto as BK
import puertas as PU

FY = 250e6                      # Pa, acero estructural
G = 9.81
MASA_CARRO = 690.0

# --- viga de impacto: tubo redondo entre las placas de los cierres (soldado a ellas), por dentro de la puerta ------------------
# Extremos sobre las placas de cierre: delantero junto al estribo, trasero en la pierna del arco; z 0.62-0.66 = cara interior de la puerta,
# libre de la cubeta (borde exterior del asiento en z = 0.31 + 0.23 = 0.54; se exige >= 30 mm de aire al tubo).
VIGA_A = PU.herraje()["viga_impacto_a"]      # una sola fuente: puertas.herraje() (el borde inferior de la puerta está en y~0.28)
VIGA_B = PU.herraje()["viga_impacto_b"]
HOLG_ASIENTO_MIN = 0.030
Z_BORDE_CUBETA = 0.54

REQ_INTERMEDIA_N = 4500.0       # 4.5 kN promedio hasta 300 mm
REQ_PICO_N = 2.0 * MASA_CARRO * G

CATALOGO_REDONDO = [(25.4, 1.6), (31.8, 2.0), (38.1, 2.0), (44.5, 2.1), (44.5, 3.2), (50.8, 2.1), (50.8, 3.2), (57.2, 3.2)]
EN_PALETA = {(50.8, 2.1), (57.2, 3.2)}      # secciones redondas que el chasis ya compra (reforzar_suspension.PALETA)


def tubo(do, t):
    do, t = do / 1000, t / 1000
    di = do - 2 * t
    A = np.pi / 4 * (do ** 2 - di ** 2)
    I = np.pi / 64 * (do ** 4 - di ** 4)
    Z = I / (do / 2)
    Mp = FY * (do ** 3 - di ** 3) / 6.0          # momento plástico
    return dict(do=do, t=t, A=A, I=I, Z=Z, Mp=Mp, My=FY * Z, kg_m=A * 7850)


def viga(do, t, L):
    s = tubo(do, t)
    return dict(s, L=L, P_ceda=4 * s["My"] / L, P_colapso=4 * s["Mp"] / L, kg=s["kg_m"] * L,
                E_300=4 * s["Mp"] / L * 0.30)       # J absorbidos por flexión plástica hasta 300 mm (rígido-plástico, sin efecto membrana)


def alcance_emergencia():
    """Distancia del hombro del piloto a cada perno de bisagra (donde va el aro de extracción del pasador), para las estaturas de diseño."""
    out = []
    for est, hx in ((1.60, BK.RIELES[0]), (1.75, BK.NOMINAL["hx"]), (BK.ESTATURA_MAX, BK.RIELES[1])):
        p = BK.postura(hx, BK.NOMINAL["hy"], BK.NOMINAL["recline"], estatura=est)
        hombro = np.array([p["hombro"][0], p["hombro"][1], 0.31])
        for nom, pin in (("bisagra 1", PU.punto_eje(PU.X_H1)), ("bisagra 2", PU.punto_eje(PU.X_H2))):
            out.append((est, nom, float(np.linalg.norm(pin - hombro))))
    return out


def reacciones_viga(P, L):
    """Viga biapoyada con carga central P: reacción P/2 en cada placa. Verificación de la placa de cierre (3 mm) con perno M8 8.8."""
    R = P / 2
    t, d, fu = 0.003, 0.008, 400e6
    aplast = 1.5 * d * t * fu                     # aplastamiento de la placa por perno
    corte_m8 = 0.6 * 800e6 * np.pi / 4 * 0.008 ** 2 * 0.8   # cortante M8 8.8 (área resistente ~80%)
    return R, aplast, corte_m8


def main(escribir=True):
    L = float(np.linalg.norm(VIGA_B - VIGA_A))
    print(f"Viga de impacto: de {np.round(VIGA_A, 2)} a {np.round(VIGA_B, 2)}  largo {L:.2f} m")
    print(f"Requisito (referencia FMVSS 214 estática): intermedia {REQ_INTERMEDIA_N/1000:.1f} kN · pico {REQ_PICO_N/1000:.1f} kN (2 x peso)")
    print(f"{'tubo':14s} {'kg':>5s} {'cede (kN)':>10s} {'colapso (kN)':>13s} {'E 300 mm (J)':>13s}  paleta  cumple intermedia")
    filas, elegido = [], None
    for do, t in CATALOGO_REDONDO:
        v = viga(do, t, L)
        ok = v["P_colapso"] >= REQ_INTERMEDIA_N
        filas.append(((do, t), v, ok))
        print(f"RED {do:4.1f}x{t:3.1f} {v['kg']:5.2f} {v['P_ceda']/1000:10.1f} {v['P_colapso']/1000:13.1f} {v['E_300']:13.0f}   {'sí' if (do, t) in EN_PALETA else '  '}     {'✓' if ok else '✗'}")
        if ok and (do, t) in EN_PALETA and (elegido is None or v["kg"] < elegido[1]["kg"]):
            elegido = ((do, t), v)
    (do, t), v = elegido
    print(f"-> ELEGIDA (la más ligera que cumple y ya está en la paleta): RED {do}x{t}: colapsa a {v['P_colapso']/1000:.1f} kN, cede a {v['P_ceda']/1000:.1f} kN, {v['kg']:.2f} kg")
    print(f"   cubre {v['P_colapso']/REQ_INTERMEDIA_N:.2f}x la intermedia y {v['P_colapso']/REQ_PICO_N*100:.0f}% del pico: el resto lo toman piel+espuma, sillín y chasis")
    R, aplast, corte = reacciones_viga(v["P_colapso"], L)
    print(f"   reacción en cada placa de cierre al colapso: {R/1000:.1f} kN · aplastamiento de placa 3 mm por perno M8: {aplast/1000:.1f} kN · cortante M8 8.8: {corte/1000:.1f} kN "
          f"-> pernos necesarios por placa: {int(np.ceil(R / min(aplast, corte)))} (se ponen 2 M8)")
    aire = (VIGA_A[2] + (VIGA_B[2] - VIGA_A[2]) * 0.5) - v["do"] / 2 - Z_BORDE_CUBETA
    print(f"   aire entre el tubo y el borde exterior de la cubeta (z={Z_BORDE_CUBETA}): {aire*1000:.0f} mm (se exige >= {HOLG_ASIENTO_MIN*1000:.0f})")
    print()
    print("Salida de emergencia: alcance del hombro a los pernos de bisagra (aro de extracción del pasador)")
    for est, nom, d in alcance_emergencia():
        print(f"   {est:.2f} m · {nom}: {d:.2f} m {'✓' if d <= 0.55 else '(con arnés puesto el alcance cómodo es ~0.50-0.55 m)'}")
    print()
    print(f"Masa de diseño de la puerta: antes 12.0 kg -> ahora {PU.MASA_PUERTA:.1f} kg (viga {v['kg']:.1f} + aros de extracción + gancho secundario ≈ +2.5 kg, menos el travesaño que reemplaza)")
    print(f"Amortiguador de gas: {PU.FUERZA_NOMINAL:.0f} N · esfuerzo en la manija al empezar a abrir {PU.esfuerzo_manual(0.0):+.0f} N")
    res = dict(L=L, tubo=(do, t), viga=v, filas=filas, aire=aire, R=R, aplast=aplast, corte=corte)
    if escribir:
        escribir_md(res)
    return res


def escribir_md(r):
    do, t = r["tubo"]
    v = r["viga"]
    L = ["# Seguridad de las puertas de gaviota", "",
         "Generado por `calculos/seguridad_puertas.py` (no editar a mano). Mismas coordenadas que `docs/herraje-puertas.md` (x atrás, y arriba, z lateral; lado izquierdo).",
         "**El carro no es homologable**: los criterios son de referencia para dar una puerta decente, no una certificación.", "",
         "## 1. Qué faltaba",
         "- Sin protección contra intrusión lateral: la puerta era piel de fibra con un esqueleto de tubo Ø16 × 1.2 mm.",
         "- Si el carro queda sobre el techo, las bisagras (en el espinazo) y el piso hacen imposible empujar la puerta: **no había salida**.",
         "- Si falla el amortiguador de gas con la puerta abierta, una puerta de 12 kg cae sobre la cabeza de quien entra.",
         "- Sin aviso de puerta mal cerrada.", "",
         "## 2. Viga de impacto lateral",
         f"Un tubo redondo **RED {do}×{t}** por dentro de la puerta, soldado a las placas de cierre (3 mm) en ambos extremos: de {np.round(VIGA_A, 2).tolist()} a "
         f"{np.round(VIGA_B, 2).tolist()}, largo {r['L']:.2f} m, a la altura de cadera–pecho del ocupante. Es la sección redonda más ligera que cumple y **ya está en la paleta de tubo** (sin compra nueva);"
         " respeta «sin PTR en las puertas».", "",
         f"Requisito de referencia (estático tipo FMVSS 214): resistencia **intermedia {REQ_INTERMEDIA_N/1000:.1f} kN** y pico {REQ_PICO_N/1000:.1f} kN (2 × el peso del carro).", "",
         "| Tubo | kg | Cede (kN) | Colapsa (kN) | Energía a 300 mm (J) | En paleta | ≥ 4.5 kN |", "|---|---|---|---|---|---|---|"]
    for (d_, t_), vv, ok in r["filas"]:
        L.append(f"| RED {d_}×{t_} | {vv['kg']:.2f} | {vv['P_ceda']/1000:.1f} | {vv['P_colapso']/1000:.1f} | {vv['E_300']:.0f} | {'sí' if (d_, t_) in EN_PALETA else ''} | {'✓' if ok else '✗'} |")
    L += ["", f"La elegida colapsa a **{v['P_colapso']/1000:.1f} kN** ({v['P_colapso']/REQ_INTERMEDIA_N:.2f}× la intermedia) y cede a {v['P_ceda']/1000:.1f} kN; "
          f"cubre {v['P_colapso']/REQ_PICO_N*100:.0f}% del pico, el resto lo toman piel con espuma, sillín y chasis (**no medido**: falta un ensayo).",
          f"Reacción en cada placa de cierre al colapso: {r['R']/1000:.1f} kN; la placa de 3 mm con un perno M8 aguanta {r['aplast']/1000:.1f} kN al aplastamiento y {r['corte']/1000:.1f} kN al cortante: **2 pernos M8 por placa**.",
          f"Aire entre el tubo y el borde exterior de la cubeta: {r['aire']*1000:.0f} mm (se exigen 30).", "",
          "Aproximaciones: viga biapoyada, flexión plástica rígido-plástica sin efecto membrana (conservador), sin interacción con la piel.", "",
          "## 3. Salida de emergencia (volcadura)",
          "Un gull-wing no abre si el carro queda sobre el techo: se resuelve con **tres acciones desde adentro y a mano**, sin pirotecnia ni piezas nuevas que mantener:",
          "1. **Manija roja de emergencia** en el larguero del techo, junto a cada hombro: libera los cierres (cable de acero, un solo jalón).",
          "2. **Pasadores de bisagra de extracción rápida** (pasador de bolas Ø10 con aro y cordón rojo): al jalarlos la puerta queda libre y se empuja hacia afuera. Son los mismos pasadores que se sacan para **desmontar la puerta en 1 minuto** al dar servicio.",
          "3. El amortiguador de gas lleva rótulas con clip de liberación, así que no ata la puerta.", "",
          "Alcance del hombro al perno de bisagra (con arnés puesto el alcance cómodo es 0.50–0.55 m):", "", "| Estatura | Bisagra | Distancia |", "|---|---|---|"]
    for est, nom, d in alcance_emergencia():
        L.append(f"| {est:.2f} m | {nom} | {d:.2f} m |")
    L += ["", "## 4. Retención y respaldos",
          "- **Cierres con segunda posición de seguridad** (cerrojo primario y secundario): de pestillo de puerta de auto de deshuesadero, que ya trae las dos etapas. 4 puntos de cierre; con **2 de 4** basta para retener la puerta.",
          "- **Varilla de apoyo** (varilla de acero Ø8 con clip, guardada en el larguero del techo): respalda al amortiguador de gas. Se usa para trabajar bajo la puerta y si el amortiguador pierde presión.",
          "- **Sensor de puerta** (interruptor magnético tipo reed por puerta, ~$1): lo lee la tablet; avisa «puerta abierta» e **inhibe el par de los motores** con la puerta mal cerrada.",
          "- **Pasadores de bisagra en doble cortante**: Ø10 acero 8.8 aguanta ~75 kN; las cargas de abuso (LC7) son de 1.3 kN.", "",
          "## 5. Efecto en el diseño",
          f"- Masa de diseño de la puerta: de 12.0 a **{PU.MASA_PUERTA:.1f} kg** (viga ≈ {v['kg']:.1f} kg, aros y gancho ≈ 0.7 kg; el travesaño del esqueleto desaparece). Eso agrega ~3 kg al carro.",
          f"- Amortiguador de gas: **{PU.FUERZA_NOMINAL:.0f} N** (catálogo). Esfuerzo en la manija al empezar a abrir: {PU.esfuerzo_manual(0.0):+.0f} N.",
          "- Armado y mantenimiento no cambian: la viga se suelda a las mismas placas de cierre antes de laminar la piel; pasadores y cierres son piezas estándar atornilladas.", "",
          "## 6. Pendiente de comprobar en el carro",
          "- La posición real de la viga se fija al modelar la puerta contra el vano (z de la cara interior de la puerta); debe quedar ≥ 30 mm del borde exterior de la cubeta.",
          "- Un ensayo estático de empuje sobre la puerta terminada (con gato y celda de carga) para verificar los 4.5 kN a 300 mm."]
    open(os.path.join(HERE, "..", "docs", "seguridad-puertas.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")


if __name__ == "__main__":
    main()
