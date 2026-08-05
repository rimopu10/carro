# Suspensión delantera — geometría, cinemática y especificación

Horquillas dobles + coilover a la torre `fx_hi`. Cinemática 3D exacta de cuerpo rígido (`suspension_delantera.py`). Rueda 175/70R13, trocha delantera 1.50 m.

## Puntos duros (mm, lado izquierdo; el derecho es espejo)

| Punto | x | y | z | Nota |
|---|---|---|---|---|
| Pivote inf. del. | 350 | 200 | 470 | en nodo fb_lo del chasis |
| Pivote inf. tras. | 750 | 200 | 520 | en nodo fx_lo |
| Pivote sup. del. | 350 | 409 | 500 | ménsula 71 mm bajo fb_hi |
| Pivote sup. tras. | 750 | 409 | 550 | ménsula 71 mm bajo fx_hi |
| Rótula inferior LBJ | 545 | 190 | 710 | cónica tipo ATV |
| Rótula superior UBJ | 565 | 425 | 685 | cónica tipo ATV |
| Extremo cremallera | 430 | 340 | 520 | rótula axial |
| Terminal dirección | 430 | 350 | 695 | en brazo de mangueta |
| Centro de rueda | 550 | 288 | 750 | 175/70R13 |
| Coilover inferior | 580 | 215 | 660 | sobre brazo inf., 75% a la rótula |
| Coilover superior | 700 | 480 | 480 | torre fx_hi (nodo del FEM) |

## Alineación estática

| Parámetro | Valor | Típico deportivo |
|---|---|---|
| Camber | -1.0° | −0.5 a −1.5° |
| Caster | 4.9° | 3–7° |
| Inclinación de kingpin | 6.1° | 6–12° |
| Radio de pivotamiento (scrub) | 20 mm | <40 mm |
| Avance mecánico (trail) | 24 mm | 15–30 mm |
| Centro de balanceo | 121 mm | 30–100 mm |
| Convergencia | 0° (ajustar 1–2 mm toe-in total en piso) | |

## Cinemática en el recorrido (±70 mm)

- Ganancia de camber: **-0.59°/25 mm** en compresión (la rueda se inclina hacia adentro al comprimir: correcto).
- Bump steer máximo: **0.064°/25 mm** en ±50 mm — excelente (<0.1).
- Cambio de semitrocha: -13.4 a 0.0 mm.
- Motion ratio del coilover: **0.60** (shock/rueda) — casi constante en el recorrido.

## Resortes y coilover (especificación de compra)

- Masa por esquina: 131 kg (113 suspendida) · frecuencia objetivo 1.9 Hz.
- Tasa en rueda 16.1 N/mm → **resorte 44 N/mm ≈ 252 lb/in**.
- Largo ojo-a-ojo estático: **342 mm** · carrera usada: 85 mm → pedir coilover ~380 mm extendido, carrera ≥100 mm.
- Carga estática por shock: 1837 N · en bache 3g: **5510 N** (carga de diseño de la ménsula en la torre, con FS 2 soldar para 11.0 kN).
- Amortiguación crítica en rueda 2700 N·s/m → ajustar ζ≈0.5–0.7 (coilover con clicks).

## Largos de fabricación de brazos (centro a centro, mm)

- brazo inf. tubo del.: **309 mm**
- brazo inf. tubo tras.: **280 mm**
- brazo sup. tubo del.: **284 mm**
- brazo sup. tubo tras.: **230 mm**
- tie rod (centro-centro): **175 mm**

## Piezas (BOM parcial de esta sección)

- 4 × rótula cónica ATV (tipo Honda TRX300/Rancher) — LBJ y UBJ por lado
- 8 × buje de poliuretano + tubo interno para pivotes de brazos (Ø12 mm)
- Tubo redondo 25.4×2.1 mm para brazos (~2.1 m total delantero)
- 2 × coilover con resorte según spec de arriba
- 2 × terminal de dirección ATV + cremallera manual de compacto (donante)
- Mangueta/maza/freno: donante ATV 300 (verificar cono de rótulas al comprar)

**Notas:** los pivotes superiores requieren ménsulas que bajen el eje 71 mm bajo el tubo superior (la geometría de camber/centro de balanceo lo exige); cortarlas en láser junto con las cartelas. La altura de la cremallera es SENSIBLE: ±5 mm duplican el bump steer — montarla con barrenos ovalados y calzas para afinar en el carro. Rines 13" requieren verificar que la mangueta donante quepa (ATV usa 12"; medir antes de comprar). La convergencia se ajusta con el largo del tie rod.
