# Resultados del análisis estructural del chasis

Método: rigidez directa, vigas 3D 12-GDL, uniones rígidas, estático lineal.
Acero fy=250 MPa · E=200 GPa · PTR 38×38×1.9 y arcos RED 44.5×2.1.

**Miembros:** 89 tubos · **masa del chasis:** 87.3 kg · **longitud total de tubo:** 35.9 m

## Rigidez torsional

**8,706 N·m/°** con par de 1500 N·m (objetivo para deportivo ligero artesanal: >4,000 N·m/°; un kit car típico ronda 2,000-6,000).

## LC1 Bache 3g

Factor de seguridad mínimo: **3.0** (>2.0 requerido, >3.0 deseable)

Los 10 tubos más esforzados:

| Tubo | Función | Sección | σ máx (MPa) | FS fluencia | FS pandeo |
|---|---|---|---|---|---|
| dash_loR-dash_hiR | safe | PTR 38x38x1.9 | 82.4 | 3.0 | 359.8 |
| dash_loL-dash_hiL | safe | PTR 38x38x1.9 | 82.4 | 3.0 | 359.8 |
| mh_loR-mh_beltR | safe | RED 50.8x2.1 | 77.2 | 3.2 | 714.9 |
| mh_loL-mh_beltL | safe | RED 50.8x2.1 | 77.2 | 3.2 | 714.9 |
| seatFR-seatR | gen | PTR 44x44x1.9 | 70.6 | 3.5 | 1331.6 |
| seatFL-seatL | gen | PTR 44x44x1.9 | 70.6 | 3.5 | 1331.6 |
| mh_loR-smRR | tors | PTR 25x25x1.9 | 68.9 | 3.6 | 5185.4 |
| mh_loL-smRL | tors | PTR 25x25x1.9 | 68.9 | 3.6 | 5185.4 |
| dash_loR-fx_hiR | tors | PTR 25x25x1.9 | 67.5 | 3.7 | 50.0 |
| dash_loL-fx_hiL | tors | PTR 25x25x1.9 | 67.5 | 3.7 | 50.0 |

## LC5 Volcadura (2.0W vert + 0.75W lat)

Factor de seguridad mínimo: **1.5** (>2.0 requerido, >3.0 deseable)

Los 10 tubos más esforzados:

| Tubo | Función | Sección | σ máx (MPa) | FS fluencia | FS pandeo |
|---|---|---|---|---|---|
| seatL-mh_loL | gen | PTR 44x44x1.9 | 164.0 | 1.5 | 380.4 |
| dash_loL-seatFL | gen | PTR 44x44x1.9 | 138.4 | 1.8 | 803.4 |
| mh_loL-bat_fL | gen | PTR 44x44x1.9 | 137.1 | 1.8 | 7925.5 |
| mh_loR-mh_beltR | safe | RED 50.8x2.1 | 124.5 | 2.0 | 315.3 |
| mh_hiL-coilL | safe | RED 50.8x2.1 | 123.7 | 2.0 | 137.3 |
| mh_beltR-mh_hiR | safe | RED 57.2x3.2 | 117.8 | 2.1 | 1086.3 |
| coilL-r_hiL | safe | RED 50.8x2.1 | 116.7 | 2.1 | 2180.1 |
| taL-bat_rL | gen | PTR 38x38x1.9 | 114.9 | 2.2 | 935.2 |
| dash_hiL-hdrL | safe | RED 57.2x3.2 | 114.6 | 2.2 | 276.9 |
| mh_loL-mh_beltL | safe | RED 50.8x2.1 | 112.1 | 2.2 | 131.8 |

## LC5b Volcadura FIA (7.5W + 5.5W)

Factor de seguridad mínimo: **0.3** (>2.0 requerido, >3.0 deseable)

Los 10 tubos más esforzados:

| Tubo | Función | Sección | σ máx (MPa) | FS fluencia | FS pandeo |
|---|---|---|---|---|---|
| seatL-mh_loL | gen | PTR 44x44x1.9 | 849.3 | 0.3 | 71.9 |
| taL-bat_rL | gen | PTR 38x38x1.9 | 824.5 | 0.3 | 121.0 |
| bat_fL-taL | gen | PTR 38x38x1.9 | 803.3 | 0.3 | 2398.6 |
| r_hiL-r_hiR | gen | PTR 38x38x1.9 | 778.6 | 0.3 | 40.8 |
| coilL-r_hiL | safe | RED 50.8x2.1 | 767.3 | 0.3 | 295.2 |
| mh_loL-bat_fL | gen | PTR 44x44x1.9 | 742.8 | 0.3 | 1716.0 |
| mh_hiL-sp_rL | safe | RED 57.2x3.2 | 741.6 | 0.3 | 907.7 |
| mh_hiR-sp_rR | safe | RED 57.2x3.2 | 712.1 | 0.4 | 757.5 |
| mh_loL-mh_beltL | safe | RED 50.8x2.1 | 706.7 | 0.4 | 27.5 |
| dash_loL-seatFL | gen | PTR 44x44x1.9 | 702.7 | 0.4 | 158.6 |

## LC5c Volcadura sobre la cabecera (1.0W vert + 0.5W lat)

Factor de seguridad mínimo: **1.7** (>2.0 requerido, >3.0 deseable)

Los 10 tubos más esforzados:

| Tubo | Función | Sección | σ máx (MPa) | FS fluencia | FS pandeo |
|---|---|---|---|---|---|
| dash_hiL-hdrL | safe | RED 57.2x3.2 | 145.1 | 1.7 | 399.7 |
| dash_hiR-hdrR | safe | RED 57.2x3.2 | 114.0 | 2.2 | 666.8 |
| sp_fR-h1R | safe | RED 57.2x3.2 | 108.2 | 2.3 | 38146.3 |
| fx_hiL-dash_hiL | safe | PTR 38x38x1.9 | 103.9 | 2.4 | 1009.4 |
| hdrL-saL | safe | RED 57.2x3.2 | 95.9 | 2.6 | 99975.8 |
| sp_fL-h1L | safe | RED 57.2x3.2 | 88.6 | 2.8 | 29278.7 |
| h2L-sp_rL | safe | RED 57.2x3.2 | 88.2 | 2.8 | 10131.0 |
| mh_loL-mh_beltL | safe | RED 50.8x2.1 | 85.3 | 2.9 | 476.2 |
| mh_beltL-mh_hiL | safe | RED 57.2x3.2 | 84.0 | 3.0 | 2482.7 |
| saL-sp_fL | safe | RED 57.2x3.2 | 83.1 | 3.0 | 43242.8 |

## LC7 Puertas abiertas a 65° (3g + viento 400 N + amortiguador)

Factor de seguridad mínimo: **28.6** (>2.0 requerido, >3.0 deseable)

Los 10 tubos más esforzados:

| Tubo | Función | Sección | σ máx (MPa) | FS fluencia | FS pandeo |
|---|---|---|---|---|---|
| sp_fL-h1L | safe | RED 57.2x3.2 | 8.7 | 28.6 | 369784.1 |
| sp_fR-h1R | safe | RED 57.2x3.2 | 8.7 | 28.6 | 369784.1 |
| h2R-sp_rR | safe | RED 57.2x3.2 | 7.9 | 31.5 | 129126.9 |
| h2L-sp_rL | safe | RED 57.2x3.2 | 7.9 | 31.5 | 129126.9 |
| fx_hiR-dash_hiR | safe | PTR 38x38x1.9 | 7.2 | 34.7 | 13796.5 |
| fx_hiL-dash_hiL | safe | PTR 38x38x1.9 | 7.2 | 34.7 | 13796.5 |
| mh_hiR-sp_rR | safe | RED 57.2x3.2 | 6.9 | 36.4 | 117790.6 |
| mh_hiL-sp_rL | safe | RED 57.2x3.2 | 6.9 | 36.4 | 117790.6 |
| dash_hiR-hdrR | safe | RED 57.2x3.2 | 6.4 | 39.1 | 5743.9 |
| dash_hiL-hdrL | safe | RED 57.2x3.2 | 6.4 | 39.1 | 5743.9 |

## LC3 Frenada 1g

Factor de seguridad mínimo: **2.6** (>2.0 requerido, >3.0 deseable)

Los 10 tubos más esforzados:

| Tubo | Función | Sección | σ máx (MPa) | FS fluencia | FS pandeo |
|---|---|---|---|---|---|
| fx_loL-dash_loL | gen | PTR 38x38x1.9 | 96.0 | 2.6 | 180.3 |
| fb_loL-fx_loL | susp | PTR 38x38x1.9 | 91.6 | 2.7 | 142.7 |
| cf1-cfF | tors | PTR 38x38x1.9 | 72.5 | 3.4 | 7275.9 |
| fb_loR-fx_loR | susp | PTR 38x38x1.9 | 63.5 | 3.9 | 1028.5 |
| seatFL-smFL | asiento | PTR 38x38x1.9 | 61.4 | 4.1 | 3172.6 |
| fx_loR-dash_loR | gen | PTR 38x38x1.9 | 60.5 | 4.1 | 1304.4 |
| smRL-cf2 | asiento | PTR 38x38x1.9 | 57.0 | 4.4 | 50414.0 |
| smRR-cf2 | asiento | PTR 38x38x1.9 | 55.0 | 4.5 | 50414.0 |
| seatL-smRL | asiento | PTR 38x38x1.9 | 53.0 | 4.7 | 1552.3 |
| fb_loL-fb_loR | gen | PTR 38x38x1.9 | 50.6 | 4.9 | — |

## LC4 Curva 1g

Factor de seguridad mínimo: **2.7** (>2.0 requerido, >3.0 deseable)

Los 10 tubos más esforzados:

| Tubo | Función | Sección | σ máx (MPa) | FS fluencia | FS pandeo |
|---|---|---|---|---|---|
| taL-bat_rL | gen | PTR 38x38x1.9 | 91.4 | 2.7 | 1788.7 |
| bat_fL-taL | gen | PTR 38x38x1.9 | 90.2 | 2.8 | 19820.3 |
| smRR-cf2 | asiento | PTR 38x38x1.9 | 69.1 | 3.6 | 4477.5 |
| smRL-cf2 | asiento | PTR 38x38x1.9 | 64.2 | 3.9 | 4835.0 |
| seatL-smRL | asiento | PTR 38x38x1.9 | 59.4 | 4.2 | 2180.0 |
| seatR-smRR | asiento | PTR 38x38x1.9 | 59.1 | 4.2 | 8324.8 |
| fx_loL-dash_loL | gen | PTR 38x38x1.9 | 55.4 | 4.5 | 3457.0 |
| fb_loL-fx_loL | susp | PTR 38x38x1.9 | 50.4 | 5.0 | 10375.4 |
| fx_loR-dash_loR | gen | PTR 38x38x1.9 | 45.1 | 5.5 | 1788.0 |
| bat_fL-bat_fR | batt | PTR 38x38x1.9 | 43.8 | 5.7 | 54.0 |

## Supuestos y límites

- Masas: batería 90 kg, 2 ocupantes 180 kg, controladores 15 kg, carrocería 40 kg en anclajes.
- Motores de cubo = masa no suspendida: no cargan el chasis en estos casos.
- No incluye: fatiga de soldadura, abolladura local, choque. Validar con FEM 3D antes de soldar.
