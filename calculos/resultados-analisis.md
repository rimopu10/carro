# Resultados del análisis estructural del chasis

Método: rigidez directa, vigas 3D 12-GDL, uniones rígidas, estático lineal.
Acero fy=250 MPa · E=200 GPa · PTR 38×38×1.9 y arcos RED 44.5×2.1.

**Miembros:** 91 tubos · **masa del chasis:** 90.1 kg · **longitud total de tubo:** 35.9 m

## Rigidez torsional

**8,702 N·m/°** con par de 1500 N·m (objetivo para deportivo ligero artesanal: >4,000 N·m/°; un kit car típico ronda 2,000-6,000).

## LC1 Bache 3g

Factor de seguridad mínimo: **3.2** (>2.0 requerido, >3.0 deseable)

Los 10 tubos más esforzados:

| Tubo | Función | Sección | σ máx (MPa) | FS fluencia | FS pandeo |
|---|---|---|---|---|---|
| dash_loL-seatFL | gen | PTR 44x44x1.9 | 79.1 | 3.2 | 1726.5 |
| dash_loR-seatFR | gen | PTR 44x44x1.9 | 79.1 | 3.2 | 1726.5 |
| dash_loL-dash_hiL | safe | PTR 38x38x1.9 | 76.1 | 3.3 | 407.1 |
| dash_loR-dash_hiR | safe | PTR 38x38x1.9 | 76.1 | 3.3 | 407.1 |
| smFR-cfF | asiento | PTR 38x38x1.9 | 68.3 | 3.7 | 3533.0 |
| smFL-cfF | asiento | PTR 38x38x1.9 | 68.3 | 3.7 | 3533.0 |
| mh_loL-mh_beltL | safe | RED 57.2x3.2 | 68.2 | 3.7 | 1490.0 |
| mh_loR-mh_beltR | safe | RED 57.2x3.2 | 68.2 | 3.7 | 1490.0 |
| mh_loL-smRL | tors | PTR 44x44x1.9 | 67.4 | 3.7 | 26248.5 |
| mh_loR-smRR | tors | PTR 44x44x1.9 | 67.4 | 3.7 | 26248.5 |

## LC5 Volcadura (2.0W vert + 0.75W lat)

Factor de seguridad mínimo: **1.7** (>2.0 requerido, >3.0 deseable)

Los 10 tubos más esforzados:

| Tubo | Función | Sección | σ máx (MPa) | FS fluencia | FS pandeo |
|---|---|---|---|---|---|
| seatL-mh_loL | gen | PTR 44x44x1.9 | 145.6 | 1.7 | 400.2 |
| mh_loL-bat_fL | gen | PTR 38x38x3.0 | 139.9 | 1.8 | 6947.3 |
| dash_loL-seatFL | gen | PTR 44x44x1.9 | 136.7 | 1.8 | 803.6 |
| mh_beltR-mh_hiR | safe | RED 57.2x3.2 | 112.0 | 2.2 | 972.7 |
| mh_hiL-coilL | safe | RED 50.8x2.1 | 106.9 | 2.3 | 127.9 |
| taL-bat_rL | gen | PTR 38x38x1.9 | 106.7 | 2.3 | 959.8 |
| dash_hiL-hdrL | safe | RED 57.2x3.2 | 104.6 | 2.4 | 289.4 |
| coilL-r_hiL | safe | RED 50.8x2.1 | 104.2 | 2.4 | 2372.1 |
| bat_fL-taL | gen | PTR 38x38x1.9 | 103.8 | 2.4 | 28109.2 |
| mh_hiL-sp_rL | safe | RED 57.2x3.2 | 102.5 | 2.4 | 8776.6 |

## LC5b Volcadura FIA (7.5W + 5.5W)

Factor de seguridad mínimo: **0.3** (>2.0 requerido, >3.0 deseable)

Los 10 tubos más esforzados:

| Tubo | Función | Sección | σ máx (MPa) | FS fluencia | FS pandeo |
|---|---|---|---|---|---|
| mh_loL-bat_fL | gen | PTR 38x38x3.0 | 790.6 | 0.3 | 1476.0 |
| seatL-mh_loL | gen | PTR 44x44x1.9 | 772.0 | 0.3 | 75.9 |
| taL-bat_rL | gen | PTR 38x38x1.9 | 769.1 | 0.3 | 124.7 |
| bat_fL-taL | gen | PTR 38x38x1.9 | 748.0 | 0.3 | 2809.6 |
| r_hiL-r_hiR | gen | PTR 38x38x1.9 | 703.5 | 0.4 | 41.7 |
| dash_loL-seatFL | gen | PTR 44x44x1.9 | 692.1 | 0.4 | 157.1 |
| coilL-r_hiL | safe | RED 50.8x2.1 | 677.6 | 0.4 | 321.0 |
| mh_hiL-sp_rL | safe | RED 57.2x3.2 | 665.9 | 0.4 | 1095.8 |
| mh_beltR-baR | safe | RED 57.2x3.2 | 657.3 | 0.4 | 8413.9 |
| mh_hiR-sp_rR | safe | RED 57.2x3.2 | 620.8 | 0.4 | 897.9 |

## LC5c Volcadura sobre la cabecera (1.0W vert + 0.5W lat)

Factor de seguridad mínimo: **1.8** (>2.0 requerido, >3.0 deseable)

Los 10 tubos más esforzados:

| Tubo | Función | Sección | σ máx (MPa) | FS fluencia | FS pandeo |
|---|---|---|---|---|---|
| dash_hiL-hdrL | safe | RED 57.2x3.2 | 141.4 | 1.8 | 395.5 |
| dash_hiR-hdrR | safe | RED 57.2x3.2 | 110.6 | 2.3 | 654.3 |
| sp_fR-h1R | safe | RED 57.2x3.2 | 110.5 | 2.3 | 45845.7 |
| fx_hiL-dash_hiL | safe | PTR 38x38x1.9 | 101.3 | 2.5 | 1013.7 |
| hdrL-saL | safe | RED 57.2x3.2 | 92.4 | 2.7 | 88311.9 |
| h2L-sp_rL | safe | RED 57.2x3.2 | 89.3 | 2.8 | 8676.9 |
| sp_fL-h1L | safe | RED 57.2x3.2 | 88.1 | 2.8 | 25076.3 |
| sp_fL-sp_fR | safe | RED 50.8x2.1 | 85.8 | 2.9 | 4217.8 |
| h1R-h2R | safe | RED 57.2x3.2 | 80.9 | 3.1 | 5094.0 |
| mh_beltL-mh_hiL | safe | RED 57.2x3.2 | 79.5 | 3.1 | 2913.8 |

## LC7 Puertas abiertas a 65° (3g + viento 400 N + amortiguador)

Factor de seguridad mínimo: **7.0** (>2.0 requerido, >3.0 deseable)

Los 10 tubos más esforzados:

| Tubo | Función | Sección | σ máx (MPa) | FS fluencia | FS pandeo |
|---|---|---|---|---|---|
| sp_fL-sp_fR | safe | RED 50.8x2.1 | 35.6 | 7.0 | 41381.6 |
| dash_hiL-hdrL | safe | RED 57.2x3.2 | 27.6 | 9.1 | 3157.1 |
| dash_hiR-hdrR | safe | RED 57.2x3.2 | 27.6 | 9.1 | 3157.1 |
| sp_fL-h1L | safe | RED 57.2x3.2 | 22.6 | 11.0 | 126967.6 |
| sp_fR-h1R | safe | RED 57.2x3.2 | 22.6 | 11.0 | 126967.6 |
| saR-sp_fR | safe | RED 57.2x3.2 | 20.6 | 12.2 | 39273.9 |
| saL-sp_fL | safe | RED 57.2x3.2 | 20.6 | 12.2 | 39273.9 |
| hdrL-saL | safe | RED 57.2x3.2 | 19.3 | 12.9 | 956297.4 |
| hdrR-saR | safe | RED 57.2x3.2 | 19.3 | 12.9 | 956297.4 |
| fx_hiL-dash_hiL | safe | PTR 38x38x1.9 | 18.8 | 13.3 | 9914.2 |

## LC8 Arnés 10 g (5.3 kN por asiento en la barra de cinturones)

Factor de seguridad mínimo: **2.2** (>2.0 requerido, >3.0 deseable)

Los 10 tubos más esforzados:

| Tubo | Función | Sección | σ máx (MPa) | FS fluencia | FS pandeo |
|---|---|---|---|---|---|
| mh_beltR-mh_hiR | safe | RED 57.2x3.2 | 114.9 | 2.2 | 4958.0 |
| mh_beltL-mh_hiL | safe | RED 57.2x3.2 | 114.9 | 2.2 | 4958.0 |
| mh_loR-mh_beltR | safe | RED 57.2x3.2 | 101.8 | 2.5 | 2561.1 |
| mh_loL-mh_beltL | safe | RED 57.2x3.2 | 101.8 | 2.5 | 2561.1 |
| seatR-mh_loR | gen | PTR 44x44x1.9 | 91.8 | 2.7 | 8291.0 |
| seatL-mh_loL | gen | PTR 44x44x1.9 | 91.8 | 2.7 | 8291.0 |
| mh_hiL-coilL | safe | RED 50.8x2.1 | 86.8 | 2.9 | 502.8 |
| mh_hiR-coilR | safe | RED 50.8x2.1 | 86.8 | 2.9 | 502.8 |
| mh_beltR-baR | safe | RED 57.2x3.2 | 77.2 | 3.2 | 59273.8 |
| mh_beltL-baL | safe | RED 57.2x3.2 | 77.2 | 3.2 | 59273.8 |

## LC3 Frenada 1g

Factor de seguridad mínimo: **2.7** (>2.0 requerido, >3.0 deseable)

Los 10 tubos más esforzados:

| Tubo | Función | Sección | σ máx (MPa) | FS fluencia | FS pandeo |
|---|---|---|---|---|---|
| fb_loL-fx_loL | susp | PTR 38x38x1.9 | 94.0 | 2.7 | 144.8 |
| fx_loL-dash_loL | gen | PTR 38x38x1.9 | 75.3 | 3.3 | 184.7 |
| seatFL-smFL | asiento | PTR 38x38x1.9 | 75.0 | 3.3 | 2662.6 |
| fb_loR-fx_loR | susp | PTR 38x38x1.9 | 68.4 | 3.7 | 929.0 |
| dash_loR-seatFR | gen | PTR 44x44x1.9 | 60.3 | 4.1 | 13630.1 |
| dash_loL-seatFL | gen | PTR 44x44x1.9 | 60.0 | 4.2 | 994.4 |
| smRL-cf2 | asiento | PTR 38x38x1.9 | 56.8 | 4.4 | 1591.2 |
| fb_loL-fb_loR | gen | PTR 38x38x1.9 | 55.1 | 4.5 | — |
| fb_hiL-fx_hiL | susp | PTR 38x38x1.9 | 53.7 | 4.7 | 1555.7 |
| smFR-cfF | asiento | PTR 38x38x1.9 | 51.7 | 4.8 | 2425.5 |

## LC4 Curva 1g

Factor de seguridad mínimo: **2.9** (>2.0 requerido, >3.0 deseable)

Los 10 tubos más esforzados:

| Tubo | Función | Sección | σ máx (MPa) | FS fluencia | FS pandeo |
|---|---|---|---|---|---|
| taL-bat_rL | gen | PTR 38x38x1.9 | 86.3 | 2.9 | 2125.6 |
| bat_fL-taL | gen | PTR 38x38x1.9 | 85.7 | 2.9 | 13750.1 |
| smRR-cf2 | asiento | PTR 38x38x1.9 | 61.6 | 4.1 | 2343.8 |
| smRL-cf2 | asiento | PTR 38x38x1.9 | 52.2 | 4.8 | 57303.2 |
| fb_loL-fx_loL | susp | PTR 38x38x1.9 | 51.7 | 4.8 | 66560.0 |
| mh_loL-bat_fL | gen | PTR 38x38x3.0 | 45.3 | 5.5 | 40936.0 |
| fx_loL-dash_loL | gen | PTR 38x38x1.9 | 45.0 | 5.6 | 4701.8 |
| dash_loL-seatFL | gen | PTR 44x44x1.9 | 44.9 | 5.6 | 2420.3 |
| dash_loR-seatFR | gen | PTR 44x44x1.9 | 44.9 | 5.6 | 37951.7 |
| fb_loR-fx_loR | susp | PTR 38x38x1.9 | 44.6 | 5.6 | 1351.8 |

## Supuestos y límites

- Masas: batería 90 kg, 2 ocupantes 180 kg, controladores 15 kg, carrocería 40 kg en anclajes.
- Motores de cubo = masa no suspendida: no cargan el chasis en estos casos.
- No incluye: fatiga de soldadura, abolladura local, choque. Validar con FEM 3D antes de soldar.
