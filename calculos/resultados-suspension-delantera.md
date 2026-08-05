# Suspensión delantera — geometría, cinemática y especificación

Horquillas dobles + coilover a la torre `fx_hi`. Cinemática 3D exacta de cuerpo rígido (`suspension_delantera.py`). Rueda 175/70R13, trocha delantera 1.50 m.

## Puntos duros (mm, lado izquierdo; el derecho es espejo)

| Punto | x | y | z | Nota |
|---|---|---|---|---|
| Pivote inf. del. | 350 | 200 | 500 | en nodo fb_lo del chasis |
| Pivote inf. tras. | 750 | 200 | 550 | en nodo fx_lo |
| Pivote sup. del. | 350 | 417 | 500 | ménsula 63 mm bajo fb_hi |
| Pivote sup. tras. | 750 | 417 | 550 | ménsula 63 mm bajo fx_hi |
| Rótula inferior LBJ | 545 | 190 | 710 | cónica tipo ATV |
| Rótula superior UBJ | 565 | 425 | 685 | cónica tipo ATV |
| Extremo cremallera | 430 | 310 | 520 | rótula axial |
| Terminal dirección | 430 | 310 | 695 | en brazo de mangueta |
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
| Centro de balanceo | 8 mm | 30–100 mm |
| Convergencia | 0° (ajustar 1–2 mm toe-in total en piso) | |

## Cinemática en el recorrido (±70 mm)

- Ganancia de camber: **-0.49°/25 mm** en compresión (la rueda se inclina hacia adentro al comprimir: correcto).
- Bump steer máximo: **0.074°/25 mm** en ±50 mm — excelente (<0.1).
- Cambio de semitrocha: -14.4 a 0.0 mm.
- Motion ratio del coilover: **0.58** (shock/rueda) — casi constante en el recorrido.

## Resortes y coilover (especificación de compra)

- Masa por esquina: 131 kg (113 suspendida) · frecuencia objetivo 1.9 Hz.
- Tasa en rueda 16.1 N/mm → **resorte 47 N/mm ≈ 270 lb/in**.
- Largo ojo-a-ojo estático: **342 mm** · carrera usada: 81 mm → pedir coilover ~380 mm extendido, carrera ≥96 mm.
- Carga estática por shock: 1901 N · en bache 3g: **5703 N** (carga de diseño de la ménsula en la torre, con FS 2 soldar para 11.4 kN).
- Amortiguación crítica en rueda 2700 N·s/m → ajustar ζ≈0.5–0.7 (coilover con clicks).

## Largos de fabricación de brazos (centro a centro, mm)

- brazo inf. tubo del.: **287 mm**
- brazo inf. tubo tras.: **260 mm**
- brazo sup. tubo del.: **284 mm**
- brazo sup. tubo tras.: **229 mm**
- tie rod (centro-centro): **175 mm**

## Piezas (BOM parcial de esta sección)

- 4 × rótula cónica ATV (tipo Honda TRX300/Rancher) — LBJ y UBJ por lado
- 8 × buje de poliuretano + tubo interno para pivotes de brazos (Ø12 mm)
- Tubo redondo 25.4×2.1 mm para brazos (~2.1 m total delantero)
- 2 × coilover con resorte según spec de arriba
- 2 × terminal de dirección ATV + cremallera manual de compacto (donante)
- Mangueta/maza/freno: donante ATV 300 (verificar cono de rótulas al comprar)

**Notas:** los pivotes superiores requieren ménsulas que bajen el eje 63 mm bajo el tubo superior (la geometría de camber/centro de balanceo lo exige); cortarlas en láser junto con las cartelas. La altura de la cremallera es SENSIBLE: ±5 mm duplican el bump steer — montarla con barrenos ovalados y calzas para afinar en el carro. Rines 13" requieren verificar que la mangueta donante quepa (ATV usa 12"; medir antes de comprar). La convergencia se ajusta con el largo del tie rod.
