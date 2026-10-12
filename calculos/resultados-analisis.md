# Resultados del análisis estructural del chasis

Método: rigidez directa, vigas 3D 12-GDL, uniones rígidas, estático lineal.
Acero fy=250 MPa · E=200 GPa · PTR 38×38×1.9 y arcos RED 44.5×2.1.

**Miembros:** 89 tubos · **masa del chasis:** 83.8 kg · **longitud total de tubo:** 35.9 m

## Rigidez torsional

**8,022 N·m/°** con par de 1500 N·m (objetivo para deportivo ligero artesanal: >4,000 N·m/°; un kit car típico ronda 2,000-6,000).

## LC1 Bache 3g

Factor de seguridad mínimo: **2.8** (>2.0 requerido, >3.0 deseable)

Los 10 tubos más esforzados:

| Tubo | Función | Sección | σ máx (MPa) | FS fluencia | FS pandeo |
|---|---|---|---|---|---|
| dash_loR-dash_hiR | safe | PTR 38x38x1.9 | 88.7 | 2.8 | 351.0 |
| dash_loL-dash_hiL | safe | PTR 38x38x1.9 | 88.7 | 2.8 | 351.0 |
| seatR-smRR | asiento | PTR 32x32x1.9 | 86.6 | 2.9 | 11695.3 |
| seatL-smRL | asiento | PTR 32x32x1.9 | 86.6 | 2.9 | 11695.3 |
| mh_loR-mh_beltR | safe | RED 50.8x2.1 | 84.8 | 2.9 | 740.1 |
| mh_loL-mh_beltL | safe | RED 50.8x2.1 | 84.8 | 2.9 | 740.1 |
| mh_loL-smRL | tors | PTR 25x25x1.9 | 81.0 | 3.1 | 7588.1 |
| mh_loR-smRR | tors | PTR 25x25x1.9 | 81.0 | 3.1 | 7588.1 |
| smFL-cfF | asiento | PTR 32x32x1.9 | 80.2 | 3.1 | 2094.2 |
| smFR-cfF | asiento | PTR 32x32x1.9 | 80.2 | 3.1 | 2094.2 |

## LC5 Volcadura (2.0W vert + 0.75W lat)

Factor de seguridad mínimo: **1.5** (>2.0 requerido, >3.0 deseable)

Los 10 tubos más esforzados:

| Tubo | Función | Sección | σ máx (MPa) | FS fluencia | FS pandeo |
|---|---|---|---|---|---|
| seatL-mh_loL | gen | PTR 44x44x1.9 | 164.1 | 1.5 | 386.3 |
| mh_beltR-mh_hiR | safe | RED 57.2x2.1 | 150.9 | 1.7 | 718.1 |
| dash_loL-seatFL | gen | PTR 44x44x1.9 | 146.3 | 1.7 | 797.9 |
| mh_hiL-sp_rL | safe | RED 57.2x2.1 | 139.9 | 1.8 | 5070.7 |
| mh_loL-bat_fL | gen | PTR 44x44x1.9 | 138.9 | 1.8 | 7937.0 |
| mh_hiR-sp_rR | safe | RED 57.2x2.1 | 129.3 | 1.9 | 3459.3 |
| bat_fL-taL | gen | PTR 38x38x1.9 | 129.0 | 1.9 | 57658.1 |
| mh_hiL-coilL | safe | RED 50.8x2.1 | 127.6 | 2.0 | 139.2 |
| coilL-r_hiL | safe | RED 50.8x2.1 | 125.6 | 2.0 | 2159.4 |
| mh_loR-mh_beltR | safe | RED 50.8x2.1 | 124.5 | 2.0 | 306.4 |

## LC5b Volcadura FIA (7.5W + 5.5W)

Factor de seguridad mínimo: **0.3** (>2.0 requerido, >3.0 deseable)

Los 10 tubos más esforzados:

| Tubo | Función | Sección | σ máx (MPa) | FS fluencia | FS pandeo |
|---|---|---|---|---|---|
| mh_hiL-sp_rL | safe | RED 57.2x2.1 | 990.1 | 0.3 | 624.6 |
| bat_fL-taL | gen | PTR 38x38x1.9 | 918.6 | 0.3 | 4292.1 |
| mh_hiR-sp_rR | safe | RED 57.2x2.1 | 908.7 | 0.3 | 508.9 |
| r_hiL-r_hiR | gen | PTR 38x38x1.9 | 861.6 | 0.3 | 38.5 |
| seatL-mh_loL | gen | PTR 44x44x1.9 | 833.4 | 0.3 | 73.9 |
| coilL-r_hiL | safe | RED 50.8x2.1 | 820.2 | 0.3 | 293.6 |
| mh_beltR-mh_hiR | safe | RED 57.2x2.1 | 785.5 | 0.3 | 268.8 |
| dash_loL-seatFL | gen | PTR 44x44x1.9 | 745.8 | 0.3 | 157.9 |
| mh_loL-bat_fL | gen | PTR 44x44x1.9 | 741.4 | 0.3 | 1716.2 |
| mh_beltL-mh_beltR | safe | PTR 38x38x3.0 | 720.4 | 0.3 | 104.2 |

## LC5c Volcadura sobre la cabecera (1.0W vert + 0.5W lat)

Factor de seguridad mínimo: **1.7** (>2.0 requerido, >3.0 deseable)

Los 10 tubos más esforzados:

| Tubo | Función | Sección | σ máx (MPa) | FS fluencia | FS pandeo |
|---|---|---|---|---|---|
| dash_hiL-hdrL | safe | RED 57.2x3.2 | 150.2 | 1.7 | 401.5 |
| dash_hiR-hdrR | safe | RED 57.2x3.2 | 117.7 | 2.1 | 670.0 |
| mh_hiL-sp_rL | safe | RED 57.2x2.1 | 115.7 | 2.2 | 2289.1 |
| sp_fR-h1R | safe | RED 57.2x3.2 | 109.0 | 2.3 | 35818.3 |
| fx_hiL-dash_hiL | safe | PTR 38x38x1.9 | 107.1 | 2.3 | 1032.7 |
| mh_beltL-mh_hiL | safe | RED 57.2x2.1 | 101.9 | 2.5 | 1879.5 |
| hdrL-saL | safe | RED 57.2x3.2 | 99.3 | 2.5 | 108958.3 |
| sp_fL-h1L | safe | RED 57.2x3.2 | 93.0 | 2.7 | 32255.6 |
| saL-sp_fL | safe | RED 57.2x3.2 | 86.7 | 2.9 | 47092.3 |
| h2L-sp_rL | safe | RED 57.2x3.2 | 83.7 | 3.0 | 11161.1 |

## LC7 Puertas abiertas a 65° (3g + viento 400 N + amortiguador)

Factor de seguridad mínimo: **26.9** (>2.0 requerido, >3.0 deseable)

Los 10 tubos más esforzados:

| Tubo | Función | Sección | σ máx (MPa) | FS fluencia | FS pandeo |
|---|---|---|---|---|---|
| mh_hiL-sp_rL | safe | RED 57.2x2.1 | 9.3 | 26.9 | 83494.9 |
| mh_hiR-sp_rR | safe | RED 57.2x2.1 | 9.3 | 26.9 | 83494.9 |
| sp_fL-h1L | safe | RED 57.2x3.2 | 9.0 | 27.9 | 378561.5 |
| sp_fR-h1R | safe | RED 57.2x3.2 | 9.0 | 27.9 | 378561.5 |
| fx_hiL-dash_hiL | safe | PTR 38x38x1.9 | 7.4 | 33.7 | 14099.8 |
| fx_hiR-dash_hiR | safe | PTR 38x38x1.9 | 7.4 | 33.7 | 14099.8 |
| h2R-sp_rR | safe | RED 57.2x3.2 | 7.2 | 34.7 | 132220.6 |
| h2L-sp_rL | safe | RED 57.2x3.2 | 7.2 | 34.7 | 132220.6 |
| dash_hiL-hdrL | safe | RED 57.2x3.2 | 6.6 | 37.9 | 5772.0 |
| dash_hiR-hdrR | safe | RED 57.2x3.2 | 6.6 | 37.9 | 5772.0 |

## LC3 Frenada 1g

Factor de seguridad mínimo: **2.6** (>2.0 requerido, >3.0 deseable)

Los 10 tubos más esforzados:

| Tubo | Función | Sección | σ máx (MPa) | FS fluencia | FS pandeo |
|---|---|---|---|---|---|
| fx_loL-dash_loL | gen | PTR 38x38x1.9 | 97.0 | 2.6 | 179.5 |
| fb_loL-fx_loL | susp | PTR 38x38x1.9 | 91.6 | 2.7 | 142.1 |
| cf1-cfF | tors | PTR 38x38x1.9 | 76.4 | 3.3 | 6944.7 |
| smRL-cf2 | asiento | PTR 32x32x1.9 | 69.4 | 3.6 | 15833.3 |
| smRR-cf2 | asiento | PTR 32x32x1.9 | 64.9 | 3.9 | 15833.3 |
| seatFL-smFL | asiento | PTR 38x38x1.9 | 64.8 | 3.9 | 3591.7 |
| fb_loR-fx_loR | susp | PTR 38x38x1.9 | 63.0 | 4.0 | 1064.9 |
| seatL-smRL | asiento | PTR 32x32x1.9 | 60.8 | 4.1 | 972.0 |
| fx_loR-dash_loR | gen | PTR 38x38x1.9 | 60.3 | 4.1 | 1352.1 |
| fb_loL-fb_loR | gen | PTR 38x38x1.9 | 52.5 | 4.8 | — |

## LC4 Curva 1g

Factor de seguridad mínimo: **2.5** (>2.0 requerido, >3.0 deseable)

Los 10 tubos más esforzados:

| Tubo | Función | Sección | σ máx (MPa) | FS fluencia | FS pandeo |
|---|---|---|---|---|---|
| bat_fL-taL | gen | PTR 38x38x1.9 | 102.0 | 2.5 | 17025.7 |
| smRR-cf2 | asiento | PTR 32x32x1.9 | 83.0 | 3.0 | 2862.8 |
| smRL-cf2 | asiento | PTR 32x32x1.9 | 76.4 | 3.3 | 3116.6 |
| taL-bat_rL | gen | PTR 44x44x1.9 | 75.4 | 3.3 | 3013.6 |
| seatL-smRL | asiento | PTR 32x32x1.9 | 67.2 | 3.7 | 1596.0 |
| seatR-smRR | asiento | PTR 32x32x1.9 | 67.1 | 3.7 | 10029.1 |
| fx_loL-dash_loL | gen | PTR 38x38x1.9 | 56.0 | 4.5 | 3451.1 |
| fb_loL-fx_loL | susp | PTR 38x38x1.9 | 50.6 | 4.9 | 9620.2 |
| fx_loR-dash_loR | gen | PTR 38x38x1.9 | 46.1 | 5.4 | 1795.0 |
| bat_fL-bat_fR | batt | PTR 32x32x1.9 | 46.0 | 5.4 | 32.7 |

## Supuestos y límites

- Masas: batería 90 kg, 2 ocupantes 180 kg, controladores 15 kg, carrocería 40 kg en anclajes.
- Motores de cubo = masa no suspendida: no cargan el chasis en estos casos.
- No incluye: fatiga de soldadura, abolladura local, choque. Validar con FEM 3D antes de soldar.
