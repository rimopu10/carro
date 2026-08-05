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
| seatR-mh_loR | gen | PTR 38x38x1.9 | 116.9 | 2.1 | 637.5 |
| dash_loR-seatR | gen | PTR 38x38x1.9 | 116.9 | 2.1 | 377.2 |
| seatL-mh_loL | gen | PTR 38x38x1.9 | 116.7 | 2.1 | 642.5 |
| dash_loL-seatL | gen | PTR 38x38x1.9 | 116.7 | 2.1 | 380.2 |
| fx_hiR-dash_hiR | gen | PTR 38x38x1.9 | 78.2 | 3.2 | 422.4 |
| fx_hiL-dash_hiL | gen | PTR 38x38x1.9 | 77.8 | 3.2 | 427.7 |
| coilL-r_hiL | susp | PTR 38x38x1.9 | 71.3 | 3.5 | 9039.6 |
| coilR-r_hiR | susp | PTR 38x38x1.9 | 70.6 | 3.5 | 8526.4 |
| mh_hiL-coilL | susp | PTR 38x38x1.9 | 67.0 | 3.7 | 157.3 |
| mh_hiR-coilR | susp | PTR 38x38x1.9 | 66.9 | 3.7 | 156.7 |

## LC3 Frenada 1g

Factor de seguridad mínimo: **4.4** (>2.0 requerido, >3.0 deseable)

Los 10 tubos más esforzados:

| Tubo | Función | Sección | σ máx (MPa) | FS fluencia | FS pandeo |
|---|---|---|---|---|---|
| fx_hiL-dash_hiL | gen | PTR 38x38x1.9 | 57.0 | 4.4 | 1409.9 |
| fx_loL-dash_loL | gen | PTR 38x38x1.9 | 47.5 | 5.3 | 386.0 |
| seatL-mh_loL | gen | PTR 38x38x1.9 | 44.2 | 5.7 | 988.5 |
| dash_loL-seatL | gen | PTR 38x38x1.9 | 43.0 | 5.8 | 267.8 |
| seatR-mh_loR | gen | PTR 38x38x1.9 | 41.7 | 6.0 | 1001.4 |
| fb_loL-fx_loL | susp | PTR 38x38x1.9 | 40.8 | 6.1 | 239.3 |
| fx_loL-fx_hiL | susp | PTR 38x38x1.9 | 40.6 | 6.2 | 20206.8 |
| dash_loR-seatR | gen | PTR 38x38x1.9 | 38.3 | 6.5 | 2967.1 |
| fx_loR-dash_loR | gen | PTR 38x38x1.9 | 37.7 | 6.6 | 29325.9 |
| mh_loL-bat_fL | gen | PTR 38x38x1.9 | 34.7 | 7.2 | 25562.2 |

## LC4 Curva 1g

Factor de seguridad mínimo: **3.0** (>2.0 requerido, >3.0 deseable)

Los 10 tubos más esforzados:

| Tubo | Función | Sección | σ máx (MPa) | FS fluencia | FS pandeo |
|---|---|---|---|---|---|
| seatR-mh_loR | gen | PTR 38x38x1.9 | 82.9 | 3.0 | 5447.7 |
| dash_loR-seatR | gen | PTR 38x38x1.9 | 82.8 | 3.0 | 3762.4 |
| dash_loL-seatL | gen | PTR 38x38x1.9 | 80.4 | 3.1 | 831.5 |
| seatL-mh_loL | gen | PTR 38x38x1.9 | 80.3 | 3.1 | 1459.0 |
| bat_fL-taL | gen | PTR 38x38x1.9 | 55.1 | 4.5 | 14111.3 |
| taL-bat_rL | gen | PTR 38x38x1.9 | 54.8 | 4.6 | 5257.2 |
| mh_loR-bat_fR | gen | PTR 38x38x1.9 | 45.5 | 5.5 | 31406.6 |
| fx_hiL-dash_hiL | gen | PTR 38x38x1.9 | 44.4 | 5.6 | 2516.9 |
| bat_fL-bat_fR | batt | PTR 38x38x1.9 | 35.6 | 7.0 | 77.8 |
| dash_loL-dash_loR | gen | PTR 38x38x1.9 | 34.6 | 7.2 | 1077.2 |

## Supuestos y límites

- Masas: batería 90 kg, 2 ocupantes 180 kg, controladores 15 kg, carrocería 40 kg en anclajes.
- Motores de cubo = masa no suspendida: no cargan el chasis en estos casos.
- No incluye: fatiga de soldadura, abolladura local, choque. Validar con FEM 3D antes de soldar.
