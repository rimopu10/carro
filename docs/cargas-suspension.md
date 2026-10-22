# Cargas de suspensión y ménsulas

Generado por `calculos/cargas_suspension.py` (no editar a mano). Las fuerzas del piso pasan por la mangueta, los brazos,
el amortiguador y la cremallera hasta cada anclaje del chasis; el chasis se resuelve libre en equilibrio (reacciones de
los apoyos mínimos = 0).

Masa total 690 kg (564 suspendida + 126 no suspendida) · CG (1.66, 0.40) m · reparto estático por esquina: FL 165 kg, FR 165 kg, RL 180 kg, RR 180 kg

## Factor de seguridad del chasis con las ruedas pasando por los brazos

| Caso | FS mínimo | Tubo crítico |
|---|---|---|
| S1 bache 3 g | 2.03 | `taL-bat_rL` |
| S2 frenada 1 g | 4.15 | `seatFR-smFR` |
| S3 curva 1 g | 2.44 | `bat_fL-taL` |
| S4 bache 3 g en rueda del. izq. | 2.36 | `fx_loL-dash_loL` |
| S5 bache 3 g + curva 1 g | 1.54 | `bat_fR-taR` |
| S6 bache 3 g con alabeo diagonal | 1.79 | `taR-bat_rR` |
| **Peor extremo del reparto axial de las bisagras** (S5 bache 3 g + curva 1 g [axial 1/0]) | 1.54 | `bat_fR-taR` |

## Carga de diseño de cada ménsula (lado izquierdo; el derecho es el espejo)

Resultante en N, máximo de los 4 casos, en el punto duro. `exc.` = distancia del punto duro al eje del tubo que la
recibe (la ménsula transmite además el momento F·exc). Dimensionar la soldadura y la placa con FS ≥ 2 sobre este valor. El valor es el MÁXIMO de
todos los casos, incluidos los extremos del reparto axial de las bisagras (hiperestático: depende de la rigidez de los bujes) y el alabeo diagonal.

| Anclaje | Resultante máx. (N) | Caso | Nodo del chasis | exc. (mm) |
|---|---|---|---|---|
| Torre del amortiguador (delantera) | 9359 | S6 bache 3 g con alabeo diagonal | `anAMORTL` | 50 |
| Cremallera (soporte, HIPÓTESIS) | 335 | S3 curva 1 g | `anDIRECL` | 106 |
| Brazo inf., pivote delantero | 3136 | S2 frenada 1 g | `fb_loL` | 35 |
| Brazo inf., pivote trasero | 5749 | S6 bache 3 g con alabeo diagonal [axial 0/0] | `fx_loL` | 35 |
| Brazo sup., pivote delantero | 1366 | S2 frenada 1 g | `anUA1L` | 42 |
| Brazo sup., pivote trasero | 1156 | S2 frenada 1 g | `anUA2L` | 42 |
| Torre del amortiguador (trasera) | 6567 | S5 bache 3 g + curva 1 g | `coilL` | 0 |
| Brazo trasero, pivote (+ momentos Mx, My) | 2392 | S1 bache 3 g | `taL` | 64 |

Pivote trasero: además de la fuerza, transmite un MOMENTO de hasta **727 N·m** (S1 bache 3 g [axial 1/1]) por la base de 150 mm entre bujes: eso son ±4847 N por buje (vertical/lateral). El brazo se monta entre dos orejas a 6 mm de sus caras; el riel queda 64 mm hacia adentro del pivote (nodo ta en z=0.488).


## Fuerzas internas (N)

| Caso | Amortiguador del. | Tirante de dirección | Amortiguador tras. |
|---|---|---|---|
| S1 bache 3 g | 7975 | -148 | 5371 |
| S2 frenada 1 g | 3732 | 292 | 1767 |
| S3 curva 1 g | 3539 | 335 | 2987 |
| S4 bache 3 g en rueda del. izq. | 7700 | -135 | 1525 |
| S5 bache 3 g + curva 1 g | 9029 | 140 | 6567 |
| S6 bache 3 g con alabeo diagonal | 9359 | -173 | 4365 |
| S1 bache 3 g [axial 0/0] | 7975 | -148 | 5371 |
| S1 bache 3 g [axial 1/1] | 7975 | -148 | 5371 |
| S1 bache 3 g [axial 0/1] | 7975 | -148 | 5371 |
| S1 bache 3 g [axial 1/0] | 7975 | -148 | 5371 |
| S4 bache 3 g en rueda del. izq. [axial 0/0] | 7700 | -135 | 1525 |
| S4 bache 3 g en rueda del. izq. [axial 1/1] | 7700 | -135 | 1525 |
| S4 bache 3 g en rueda del. izq. [axial 0/1] | 7700 | -135 | 1525 |
| S4 bache 3 g en rueda del. izq. [axial 1/0] | 7700 | -135 | 1525 |
| S5 bache 3 g + curva 1 g [axial 0/0] | 9029 | 140 | 6567 |
| S5 bache 3 g + curva 1 g [axial 1/1] | 9029 | 140 | 6567 |
| S5 bache 3 g + curva 1 g [axial 0/1] | 9029 | 140 | 6567 |
| S5 bache 3 g + curva 1 g [axial 1/0] | 9029 | 140 | 6567 |
| S6 bache 3 g con alabeo diagonal [axial 0/0] | 9359 | -173 | 4365 |
| S6 bache 3 g con alabeo diagonal [axial 1/1] | 9359 | -173 | 4365 |
| S6 bache 3 g con alabeo diagonal [axial 0/1] | 9359 | -173 | 4365 |
| S6 bache 3 g con alabeo diagonal [axial 1/0] | 9359 | -173 | 4365 |

## Supuestos y límites

- Fuerzas de piso: reparto con Fx, Fy proporcionales a Fz (frenado y curva ideales) y Fz de mínima norma; el exceso se
  cierra con aceleración de cuerpo rígido (alivio de inercia). S4 pone 3 g en una rueda delantera y 1 g en las otras.
- Masa no suspendida concentrada en el centro de rueda (18 kg delante, 45 kg atrás); sin su inercia de rotación.
- Cinemática en posición de reposo (sin recorrido, sin ángulo de giro).
- El soporte de la cremallera se supone en el poste del bulkhead, a 82 mm del eje: AÚN NO está diseñado.
- Las ménsulas no están modeladas como sólidos: cada una es un punto rígido con su excentricidad.
- El CG sale de las masas del FEM (carga repartida por longitud de tubo): da 45% de peso delante, no el 38% con que se
  calcularon los resortes. Hay que fijar dónde va la masa real (batería, controladores) y recalcular resortes.
