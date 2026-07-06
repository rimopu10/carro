# Resultados del análisis estructural del chasis

Método: rigidez directa, vigas 3D 12-GDL, uniones rígidas, estático lineal.
Acero fy=250 MPa · E=200 GPa · PTR 38×38×1.9 y arcos RED 44.5×2.1.

**Miembros:** 73 tubos · **masa del chasis:** 90.5 kg · **longitud total de tubo:** 41.9 m

## Rigidez torsional

**10,868 N·m/°** con par de 1500 N·m (objetivo para deportivo ligero artesanal: >4,000 N·m/°; un kit car típico ronda 2,000-6,000).

## LC1 Bache 3g

Factor de seguridad mínimo: **2.2** (>2.0 requerido, >3.0 deseable)

Los 10 tubos más esforzados:

| Tubo | Función | Sección | σ máx (MPa) | FS fluencia | FS pandeo |
|---|---|---|---|---|---|
| seatR-mh_loR | gen | PTR 38x38x1.9 | 112.7 | 2.2 | 641.3 |
| dash_loR-seatR | gen | PTR 38x38x1.9 | 112.7 | 2.2 | 379.5 |
| seatL-mh_loL | gen | PTR 38x38x1.9 | 112.7 | 2.2 | 649.2 |
| dash_loL-seatL | gen | PTR 38x38x1.9 | 112.7 | 2.2 | 384.2 |
| coilL-r_hiL | susp | PTR 38x38x1.9 | 75.0 | 3.3 | 10074.0 |
| coilR-r_hiR | susp | PTR 38x38x1.9 | 74.7 | 3.3 | 9382.3 |
| fx_hiL-dash_hiL | gen | PTR 38x38x1.9 | 71.6 | 3.5 | 440.5 |
| fx_hiR-dash_hiR | gen | PTR 38x38x1.9 | 71.5 | 3.5 | 433.9 |
| mh_hiR-coilR | susp | PTR 38x38x1.9 | 64.9 | 3.9 | 158.6 |
| mh_hiL-coilL | susp | PTR 38x38x1.9 | 64.8 | 3.9 | 159.7 |

## LC3 Frenada 1g

Factor de seguridad mínimo: **4.7** (>2.0 requerido, >3.0 deseable)

Los 10 tubos más esforzados:

| Tubo | Función | Sección | σ máx (MPa) | FS fluencia | FS pandeo |
|---|---|---|---|---|---|
| fx_hiL-dash_hiL | gen | PTR 38x38x1.9 | 53.7 | 4.7 | 1505.7 |
| fx_loL-dash_loL | gen | PTR 38x38x1.9 | 52.2 | 4.8 | 387.4 |
| seatL-mh_loL | gen | PTR 38x38x1.9 | 44.1 | 5.7 | 1022.9 |
| seatR-mh_loR | gen | PTR 38x38x1.9 | 42.5 | 5.9 | 957.7 |
| dash_loL-seatL | gen | PTR 38x38x1.9 | 42.1 | 5.9 | 272.0 |
| fx_loL-fx_hiL | susp | PTR 38x38x1.9 | 39.8 | 6.3 | 15851.0 |
| fb_loL-fx_loL | susp | PTR 38x38x1.9 | 37.0 | 6.7 | 238.1 |
| dash_loR-seatR | gen | PTR 38x38x1.9 | 36.5 | 6.9 | 3845.6 |
| fx_loR-dash_loR | gen | PTR 38x38x1.9 | 35.3 | 7.1 | 27530.6 |
| mh_loL-bat_fL | gen | PTR 38x38x1.9 | 33.0 | 7.6 | 26405.3 |

## LC4 Curva 1g

Factor de seguridad mínimo: **3.2** (>2.0 requerido, >3.0 deseable)

Los 10 tubos más esforzados:

| Tubo | Función | Sección | σ máx (MPa) | FS fluencia | FS pandeo |
|---|---|---|---|---|---|
| seatR-mh_loR | gen | PTR 38x38x1.9 | 78.4 | 3.2 | 5133.2 |
| dash_loR-seatR | gen | PTR 38x38x1.9 | 78.3 | 3.2 | 3511.9 |
| dash_loL-seatL | gen | PTR 38x38x1.9 | 77.1 | 3.2 | 903.9 |
| seatL-mh_loL | gen | PTR 38x38x1.9 | 77.0 | 3.2 | 1591.4 |
| bat_fL-taL | gen | PTR 38x38x1.9 | 53.0 | 4.7 | 13804.1 |
| taL-bat_rL | gen | PTR 38x38x1.9 | 52.7 | 4.7 | 5437.6 |
| fx_hiL-dash_hiL | gen | PTR 38x38x1.9 | 42.6 | 5.9 | 2630.5 |
| fx_loL-dash_loL | gen | PTR 38x38x1.9 | 37.0 | 6.8 | 2352.1 |
| mh_loR-bat_fR | gen | PTR 38x38x1.9 | 33.1 | 7.5 | 33611.1 |
| coilR-r_hiR | susp | PTR 38x38x1.9 | 33.0 | 7.6 | 16370.6 |

## Supuestos y límites

- Masas: batería 90 kg, 2 ocupantes 180 kg, controladores 15 kg, carrocería 40 kg en anclajes.
- Motores de cubo = masa no suspendida: no cargan el chasis en estos casos.
- No incluye: fatiga de soldadura, abolladura local, choque. Validar con FEM 3D antes de soldar.
