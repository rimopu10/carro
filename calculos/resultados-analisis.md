# Resultados del análisis estructural del chasis

Método: rigidez directa, vigas 3D 12-GDL, uniones rígidas, estático lineal.
Acero fy=250 MPa · E=200 GPa · PTR 38×38×1.9 y arcos RED 44.5×2.1.

**Miembros:** 90 tubos · **masa del chasis:** 85.8 kg · **longitud total de tubo:** 36.5 m

## Rigidez torsional

**8,037 N·m/°** con par de 1500 N·m (objetivo para deportivo ligero artesanal: >4,000 N·m/°; un kit car típico ronda 2,000-6,000).

## LC1 Bache 3g

Factor de seguridad mínimo: **2.6** (>2.0 requerido, >3.0 deseable)

Los 10 tubos más esforzados:

| Tubo | Función | Sección | σ máx (MPa) | FS fluencia | FS pandeo |
|---|---|---|---|---|---|
| seatR-smRR | asiento | PTR 32x32x1.9 | 94.5 | 2.6 | 9678.2 |
| seatL-smRL | asiento | PTR 32x32x1.9 | 94.5 | 2.6 | 9678.2 |
| dash_loR-seatFR | gen | PTR 44x44x1.9 | 82.1 | 3.0 | 1729.6 |
| dash_loL-seatFL | gen | PTR 44x44x1.9 | 82.1 | 3.0 | 1729.6 |
| smRR-cf2 | asiento | PTR 32x32x1.9 | 76.1 | 3.3 | 9152.8 |
| smRL-cf2 | asiento | PTR 32x32x1.9 | 76.1 | 3.3 | 9152.8 |
| bat_fL-smRL | tors | PTR 25x25x1.9 | 73.1 | 3.4 | 2838.4 |
| bat_fR-smRR | tors | PTR 25x25x1.9 | 73.1 | 3.4 | 2838.4 |
| mh_hiL-sp_rL | safe | RED 50.8x3.2 | 69.1 | 3.6 | 5402.9 |
| mh_hiR-sp_rR | safe | RED 50.8x3.2 | 69.1 | 3.6 | 5402.9 |

## LC5 Volcadura (2.0W vert + 0.75W lat)

Factor de seguridad mínimo: **1.5** (>2.0 requerido, >3.0 deseable)

Los 10 tubos más esforzados:

| Tubo | Función | Sección | σ máx (MPa) | FS fluencia | FS pandeo |
|---|---|---|---|---|---|
| mh_loL-bat_fL | gen | PTR 38x38x1.9 | 163.0 | 1.5 | 4119.2 |
| seatL-mh_loL | gen | PTR 44x44x1.9 | 157.1 | 1.6 | 393.2 |
| dash_loL-seatFL | gen | PTR 44x44x1.9 | 153.9 | 1.6 | 782.7 |
| mh_beltR-mh_hiR | safe | RED 57.2x2.1 | 151.1 | 1.7 | 721.1 |
| mh_hiL-sp_rL | safe | RED 50.8x3.2 | 128.6 | 1.9 | 4966.5 |
| mh_hiL-coilL | safe | RED 50.8x2.1 | 124.9 | 2.0 | 136.5 |
| coilL-r_hiL | safe | RED 50.8x2.1 | 123.9 | 2.0 | 2207.4 |
| r_hiL-r_hiR | gen | PTR 38x38x1.9 | 121.6 | 2.1 | 144.2 |
| mh_hiR-sp_rR | safe | RED 50.8x3.2 | 118.3 | 2.1 | 3535.6 |
| taL-bat_rL | gen | PTR 38x38x1.9 | 117.5 | 2.1 | 989.9 |

## LC5b Volcadura FIA (7.5W + 5.5W)

Factor de seguridad mínimo: **0.3** (>2.0 requerido, >3.0 deseable)

Los 10 tubos más esforzados:

| Tubo | Función | Sección | σ máx (MPa) | FS fluencia | FS pandeo |
|---|---|---|---|---|---|
| mh_hiL-sp_rL | safe | RED 50.8x3.2 | 907.5 | 0.3 | 621.3 |
| mh_loL-bat_fL | gen | PTR 38x38x1.9 | 874.0 | 0.3 | 808.2 |
| r_hiL-r_hiR | gen | PTR 38x38x1.9 | 845.2 | 0.3 | 39.3 |
| taL-bat_rL | gen | PTR 38x38x1.9 | 841.4 | 0.3 | 128.9 |
| mh_hiR-sp_rR | safe | RED 50.8x3.2 | 826.2 | 0.3 | 515.1 |
| coilL-r_hiL | safe | RED 50.8x2.1 | 808.0 | 0.3 | 300.0 |
| mh_beltR-mh_hiR | safe | RED 57.2x2.1 | 786.1 | 0.3 | 272.4 |
| dash_loL-seatFL | gen | PTR 44x44x1.9 | 783.3 | 0.3 | 153.7 |
| seatL-mh_loL | gen | PTR 44x44x1.9 | 772.4 | 0.3 | 75.6 |
| mh_beltL-mh_beltR | safe | PTR 38x38x3.0 | 738.3 | 0.3 | 98.8 |

## LC5c Volcadura sobre la cabecera (1.0W vert + 0.5W lat)

Factor de seguridad mínimo: **1.7** (>2.0 requerido, >3.0 deseable)

Los 10 tubos más esforzados:

| Tubo | Función | Sección | σ máx (MPa) | FS fluencia | FS pandeo |
|---|---|---|---|---|---|
| dash_hiL-hdrL | safe | RED 57.2x3.2 | 151.3 | 1.7 | 395.3 |
| dash_hiR-hdrR | safe | RED 57.2x3.2 | 118.3 | 2.1 | 676.7 |
| fx_hiL-dash_hiL | safe | PTR 38x38x1.9 | 111.0 | 2.3 | 1069.3 |
| sp_fR-h1R | safe | RED 57.2x3.2 | 108.8 | 2.3 | 75790.5 |
| mh_hiL-sp_rL | safe | RED 50.8x3.2 | 104.4 | 2.4 | 2255.4 |
| hdrL-saL | safe | RED 57.2x3.2 | 101.6 | 2.5 | 114949.5 |
| mh_beltL-mh_hiL | safe | RED 57.2x2.1 | 99.1 | 2.5 | 1919.6 |
| sp_fL-h1L | safe | RED 57.2x3.2 | 91.9 | 2.7 | 68624.6 |
| h1R-h2R | safe | RED 57.2x3.2 | 90.7 | 2.8 | 1993.0 |
| saL-sp_fL | safe | RED 57.2x3.2 | 87.9 | 2.8 | 49732.5 |

## LC7 Puertas abiertas a 65° (3g + viento 400 N + amortiguador)

Factor de seguridad mínimo: **29.4** (>2.0 requerido, >3.0 deseable)

Los 10 tubos más esforzados:

| Tubo | Función | Sección | σ máx (MPa) | FS fluencia | FS pandeo |
|---|---|---|---|---|---|
| dash_hiL-hdrL | safe | RED 57.2x3.2 | 8.5 | 29.4 | 5552.9 |
| dash_hiR-hdrR | safe | RED 57.2x3.2 | 8.5 | 29.4 | 5552.9 |
| sp_fR-h1R | safe | RED 57.2x3.2 | 8.5 | 29.5 | 640644.6 |
| sp_fL-h1L | safe | RED 57.2x3.2 | 8.5 | 29.5 | 640644.6 |
| fx_hiL-dash_hiL | safe | PTR 38x38x1.9 | 7.8 | 31.9 | 14089.8 |
| fx_hiR-dash_hiR | safe | PTR 38x38x1.9 | 7.8 | 31.9 | 14089.8 |
| mh_hiR-sp_rR | safe | RED 50.8x3.2 | 6.5 | 38.7 | 62893.2 |
| mh_hiL-sp_rL | safe | RED 50.8x3.2 | 6.5 | 38.7 | 62893.2 |
| h2L-sp_rL | safe | RED 57.2x3.2 | 5.8 | 43.3 | 597016.9 |
| h2R-sp_rR | safe | RED 57.2x3.2 | 5.8 | 43.3 | 597016.9 |

## LC3 Frenada 1g

Factor de seguridad mínimo: **3.2** (>2.0 requerido, >3.0 deseable)

Los 10 tubos más esforzados:

| Tubo | Función | Sección | σ máx (MPa) | FS fluencia | FS pandeo |
|---|---|---|---|---|---|
| fb_loL-fx_loL | susp | PTR 44x44x1.9 | 78.5 | 3.2 | 229.9 |
| fx_loL-dash_loL | gen | PTR 38x38x1.9 | 69.2 | 3.6 | 184.1 |
| smFR-cfF | asiento | PTR 44x44x1.9 | 61.3 | 4.1 | 6676.1 |
| dash_loR-seatFR | gen | PTR 44x44x1.9 | 60.1 | 4.2 | 10062.3 |
| fb_loL-fb_loR | gen | PTR 38x38x1.9 | 59.2 | 4.2 | — |
| smFL-cfF | asiento | PTR 44x44x1.9 | 58.6 | 4.3 | 6676.1 |
| dash_loL-seatFL | gen | PTR 44x44x1.9 | 57.8 | 4.3 | 1014.7 |
| fb_loR-fx_loR | susp | PTR 44x44x1.9 | 57.7 | 4.3 | 1452.1 |
| smRL-cf2 | asiento | PTR 32x32x1.9 | 57.3 | 4.4 | 3526.7 |
| seatFR-smFR | asiento | PTR 44x44x1.9 | 55.7 | 4.5 | 2946.5 |

## LC4 Curva 1g

Factor de seguridad mínimo: **2.7** (>2.0 requerido, >3.0 deseable)

Los 10 tubos más esforzados:

| Tubo | Función | Sección | σ máx (MPa) | FS fluencia | FS pandeo |
|---|---|---|---|---|---|
| taL-bat_rL | gen | PTR 38x38x1.9 | 92.1 | 2.7 | 2131.6 |
| smRR-cf2 | asiento | PTR 32x32x1.9 | 75.8 | 3.3 | 3311.5 |
| smRL-cf2 | asiento | PTR 32x32x1.9 | 72.6 | 3.4 | 3649.0 |
| seatL-smRL | asiento | PTR 32x32x1.9 | 71.3 | 3.5 | 2608.3 |
| bat_fL-taL | gen | PTR 44x44x1.9 | 67.0 | 3.7 | 21679.9 |
| seatR-smRR | asiento | PTR 32x32x1.9 | 63.4 | 3.9 | 13880.2 |
| seatFR-seatR | gen | PTR 44x44x1.9 | 50.6 | 4.9 | 3631.5 |
| dash_loR-seatFR | gen | PTR 44x44x1.9 | 49.5 | 5.0 | 136207.9 |
| seatFL-seatL | gen | PTR 44x44x1.9 | 49.3 | 5.1 | 1287.8 |
| dash_loL-seatFL | gen | PTR 44x44x1.9 | 45.1 | 5.5 | 2539.7 |

## Supuestos y límites

- Masas: batería 90 kg, 2 ocupantes 180 kg, controladores 15 kg, carrocería 40 kg en anclajes.
- Motores de cubo = masa no suspendida: no cargan el chasis en estos casos.
- No incluye: fatiga de soldadura, abolladura local, choque. Validar con FEM 3D antes de soldar.
