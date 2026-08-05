# Resultados del análisis estructural del chasis

Método: rigidez directa, vigas 3D 12-GDL, uniones rígidas, estático lineal.
Acero fy=250 MPa · E=200 GPa · PTR 38×38×1.9 y arcos RED 44.5×2.1.

**Miembros:** 73 tubos · **masa del chasis:** 81.0 kg · **longitud total de tubo:** 41.9 m

## Rigidez torsional

**10,032 N·m/°** con par de 1500 N·m (objetivo para deportivo ligero artesanal: >4,000 N·m/°; un kit car típico ronda 2,000-6,000).

## LC1 Bache 3g

Factor de seguridad mínimo: **2.1** (>2.0 requerido, >3.0 deseable)

Los 10 tubos más esforzados:

| Tubo | Función | Sección | σ máx (MPa) | FS fluencia | FS pandeo |
|---|---|---|---|---|---|
| seatL-mh_loL | gen | PTR 38x38x1.9 | 121.9 | 2.1 | 575.8 |
| dash_loL-seatL | gen | PTR 38x38x1.9 | 121.9 | 2.1 | 340.7 |
| seatR-mh_loR | gen | PTR 38x38x1.9 | 121.7 | 2.1 | 589.1 |
| dash_loR-seatR | gen | PTR 38x38x1.9 | 121.7 | 2.1 | 348.6 |
| coilL-r_hiL | susp | PTR 38x38x1.9 | 116.9 | 2.1 | 28486.5 |
| coilR-r_hiR | susp | PTR 38x38x1.9 | 114.6 | 2.2 | 33340.0 |
| fx_hiR-dash_hiR | gen | PTR 38x38x1.9 | 110.8 | 2.3 | 376.5 |
| fx_hiL-dash_hiL | gen | PTR 38x38x1.9 | 109.4 | 2.3 | 368.3 |
| mh_hiL-coilL | susp | PTR 38x38x1.9 | 105.1 | 2.4 | 117.2 |
| mh_hiR-coilR | susp | PTR 38x38x1.9 | 104.3 | 2.4 | 118.2 |

## LC3 Frenada 1g

Factor de seguridad mínimo: **2.5** (>2.0 requerido, >3.0 deseable)

Los 10 tubos más esforzados:

| Tubo | Función | Sección | σ máx (MPa) | FS fluencia | FS pandeo |
|---|---|---|---|---|---|
| fx_hiL-dash_hiL | gen | PTR 38x38x1.9 | 99.6 | 2.5 | 1251.2 |
| fx_loL-dash_loL | gen | PTR 38x38x1.9 | 88.2 | 2.8 | 224.7 |
| fx_loL-fx_hiL | susp | PTR 38x38x1.9 | 72.6 | 3.4 | 3371.7 |
| fb_loL-fx_loL | susp | PTR 38x38x1.9 | 71.8 | 3.5 | 138.8 |
| seatL-mh_loL | gen | PTR 38x38x1.9 | 55.5 | 4.5 | 388.8 |
| fx_loR-dash_loR | gen | PTR 38x38x1.9 | 53.2 | 4.7 | 38306.9 |
| dash_loL-seatL | gen | PTR 38x38x1.9 | 51.5 | 4.9 | 155.5 |
| dash_loL-dash_hiL | safe | PTR 38x38x1.9 | 51.1 | 4.9 | 1094.1 |
| seatR-mh_loR | gen | PTR 38x38x1.9 | 50.0 | 5.0 | 1099.6 |
| mh_loL-bat_fL | gen | PTR 38x38x1.9 | 49.3 | 5.1 | 17379.1 |

## LC4 Curva 1g

Factor de seguridad mínimo: **2.8** (>2.0 requerido, >3.0 deseable)

Los 10 tubos más esforzados:

| Tubo | Función | Sección | σ máx (MPa) | FS fluencia | FS pandeo |
|---|---|---|---|---|---|
| taL-bat_rL | gen | PTR 38x38x1.9 | 89.1 | 2.8 | 2244.3 |
| bat_fL-taL | gen | PTR 38x38x1.9 | 88.7 | 2.8 | 11890.1 |
| seatR-mh_loR | gen | PTR 38x38x1.9 | 86.8 | 2.9 | 9262.5 |
| dash_loR-seatR | gen | PTR 38x38x1.9 | 86.7 | 2.9 | 7313.9 |
| dash_loL-seatL | gen | PTR 38x38x1.9 | 85.7 | 2.9 | 943.8 |
| seatL-mh_loL | gen | PTR 38x38x1.9 | 85.6 | 2.9 | 1666.7 |
| fx_hiL-dash_hiL | gen | PTR 38x38x1.9 | 72.4 | 3.5 | 2743.3 |
| mh_loR-bat_fR | gen | PTR 38x38x1.9 | 54.6 | 4.6 | 26837.2 |
| fx_loL-dash_loL | gen | PTR 38x38x1.9 | 54.4 | 4.6 | 2122.3 |
| coilL-r_hiL | susp | PTR 38x38x1.9 | 49.5 | 5.0 | 13203.9 |

## Supuestos y límites

- Masas: batería 90 kg, 2 ocupantes 180 kg, controladores 15 kg, carrocería 40 kg en anclajes.
- Motores de cubo = masa no suspendida: no cargan el chasis en estos casos.
- No incluye: fatiga de soldadura, abolladura local, choque. Validar con FEM 3D antes de soldar.
