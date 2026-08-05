# Suspensión trasera — brazo tirado con motor de cubo

La pieza de filosofía kart del carro: **3 componentes por lado** (brazo, pivote, coilover) y el motor dentro de la rueda. Sin flechas ni juntas. Generado por `suspension_trasera.py`.

## Decisión de rin (resuelta)

El QS273 tiene carcasa de ~350 mm: **no cabe en rin 13"** (asiento 330 mm). Decisión: pedir los QS273 en **versión rin desmontable de carro 14"** con llanta **175/70R14** (Ø601 mm) — misma llanta de carro adelante (13", Ø575) y atrás, la nariz queda ~1° abajo (postura deportiva). Alternativa si el proveedor no la tiene: rin de moto 17×3.5 con 130/70-17. **Confirmar con QS Motor por escrito antes de pagar.**

## Geometría

| Parámetro | Valor |
|---|---|
| Pivote del brazo | nodo `ta` (2280, 160, ±552) — usa la cartela láser ya dibujada |
| Centro de rueda | (2680, 300, ±760) → trocha 1.52 m |
| Distancia entre ejes | **2.13 m** |
| Largo efectivo del brazo | 424 mm (barrido ±9.5° en ±70 mm) |
| Cambio de batalla en recorrido | -31 a +18 mm |
| Motion ratio | **0.74** (estable: 0.71–0.75) |

## Anti-squat (comportamiento con motor de cubo)

La línea de empuje pasa por el pivote: anti-squat estático **258%**.

- A fondo (~0.34g máx de los QS273): la cola **sube ~10 mm** en vez de sentarse — cabeceo leve, inofensivo a esta potencia.
- En **regen** (el freno de diario): el mismo número actúa como anti-lift — la cola se queda plantada al frenar. Para un carro que frena con regen, es la dirección correcta.
- Si en las pruebas F3 el cabeceo molesta: bajar el pivote 50 mm con ménsula → AS ~170%. Ajuste de una tarde, ya previsto.

**Límite conocido del brazo tirado puro:** la rueda rueda con la carrocería (en curva fuerte el camber exterior se hace positivo lo que rola el chasis, ~2°/g). A 100 km/h y 0.34g de tracción es aceptable; se compensa con resortes traseros firmes (ya especificados) y toe-in estático de 1-2 mm con calzas en el pivote.

## Resorte y coilover (spec de compra)

- Masa por esquina 214 kg (169 suspendida — el motor de cubo pesa 27 kg y NO lo carga el resorte) · frecuencia 2.05 Hz.
- Tasa en rueda 28.0 N/mm → **resorte 51 N/mm ≈ 292 lb/in**.
- Largo ojo-a-ojo estático **482 mm**, carrera usada 102 mm → pedir ~540 mm extendido, carrera ≥117 mm.
- Carga estática 2237 N · bache 3g **6710 N** por shock (la torre `coil` del FEM ya soporta este caso; ménsula con FS 2 → 13.4 kN).
- Amortiguación crítica 4351 N·s/m → coilover con clicks, ζ 0.5–0.7.

## Sección del brazo (verificada a 3g + curva 1g + frenado 0.9g)

| PTR alto×ancho×pared | σ flexión vert. | σ lateral | τ torsión | σ von Mises | FS |
|---|---|---|---|---|---|
| 50×50×3 | 64 MPa | 107 MPa | 43 MPa | 186 MPa | **1.3** |
| 60×40×3 | 58 MPa | 124 MPa | 45 MPa | 199 MPa | **1.3** |
| 60×60×3 | 43 MPa | 72 MPa | 29 MPa | 126 MPa | **2.0** |
| 70×50×4 | 31 MPa | 64 MPa | 23 MPa | 104 MPa | **2.4** ✓ |
| 80×60×4 | 23 MPa | 45 MPa | 17 MPa | 73 MPa | **3.4** ✓ |

Elegida: **PTR 70×50×4** (primera con FS≥2). El brazo es UNA pieza recta de 504 mm con: manga del pivote (buje poli Ø16, base ancha ≥150 mm), oreja del shock al 75%, y la punta recibe la **placa de torque del QS273**, resuelta por optimización topológica en `placa_torque.py` (ver `resultados-placa-torque.md`).

## BOM parcial de esta sección

- 2 × PTR 70×50×4, ~0.5 m c/u (los brazos)
- 2 × kit buje poliuretano Ø16 + manga de acero (pivote, base 150 mm)
- 2 × coilover ~540 mm / carrera 117 mm / resorte 292 lb/in
- 4 × placa de torque QS273 en acero 8 mm — 2 `placa-torque-motor.dxf` (llevan
  integrada la ménsula del caliper) + 2 `placa-torque-refuerzo.dxf`. Van en
  sándwich abrazando la punta del PTR. Ver `resultados-placa-torque.md`
- 4 × doblador del cubo `placa-torque-doblador.dxf`, acero 8 mm (soldado; sin él
  el aplastamiento en los planos del eje se queda en FS 1.1)
- 16 × tornillo M12 10.9 + tuerca autoblocante, y 8 × camisa de acero soldada
  a través del PTR (si no, el apriete aplasta el tubo)
- 2 × caliper mecánico/hidráulico de ATV (el QS273 trae disco) + separadores
  para alcanzar el plano del disco
