# Dónde va la masa: batería en el túnel central (decisión 2026-10-21)

Nada está construido, así que la ubicación de la batería y la electrónica se eligió por rendimiento dentro de la filosofía del proyecto
(`docs/superpowers/specs/2026-07-05-carro-electrico-design.md`: pocas piezas, reparable por su dueño, look de motor central). Las cifras salen de
`calculos/masas_cg.py` (presupuesto por componente) y las usa el FEM a través de `calculos/masas_modelo.py`.

## Por qué no se quedó como estaba
El documento maestro decía «cuna entre ejes» y corregía con la electrónica en la nariz «a ~38/62». Medido por componente:

* la cuna estaba en x = 2.10–2.64 m y el eje trasero en 2.68: no entre ejes, **sobre** el eje trasero;
* el reparto real era **44/56**, no 38/62 (con la electrónica en la nariz);
* el **CG real queda a 0.40 m**, no a 0.33 m (ocupantes, techo y puertas lo suben): la transferencia de peso en frenada y curva es ~20% mayor
  de lo que suponían resortes y frenos.

## Alternativas medidas (690 kg, ocupantes de 90 kg)
| Batería | Electrónica | Peso delante | I guiñada (kg·m², relativa) |
|---|---|---|---|
| tras los asientos (antes) | nariz | 44.1% | 263 |
| tras los asientos | trasera | 42.0% | 233 |
| túnel, 30 celdas | nariz | 48.8% | 219 |
| **túnel, 30 celdas (elegida)** | **trasera, junto a los motores** | **46.7%** | **195 (−26%)** |
| túnel 20 + 10 tras los asientos | trasera | 46.0% | 211 |

Se descartó la pila bajo los asientos (el techo deja solo 67 mm sobre la coronilla) y la partida en dos cajas (más piezas, más cable HV, menos ganancia).

## Lo elegido
* **30 celdas prismáticas LiFePO4 de 105 Ah en UNA caja** en el túnel central entre las cubetas: x 1.05–2.16 m, ancho 142 mm, alto 206 mm (y 0.19–0.40),
  pila de celdas de canto. Pesa 90 kg y su CG queda a x = 1.60, y = 0.29 (el del carro está en x = 1.66–1.69, y = 0.40): masa al centro y baja.
* **Controladores, cargador, DC-DC y contactores atrás**, junto a los motores de cubo: cables de fase de 300 A cortos (antes 2 m desde la nariz). La
  nariz queda libre (cremallera, pedalera, zona de deformación).
* La parte trasera detrás de los asientos queda libre: sirve de **maletero** bajo el clamshell.
* Ventajas de servicio: una sola caja, se abre desde la cabina por la tapa de la consola; el túnel es la zona más protegida en un choque lateral.

## Costos y consecuencias (todo ya aplicado en el modelo)
| Tema | Antes | Ahora |
|---|---|---|
| Chasis | 92.9 kg | **99.0 kg** (+6.1: 3 tubos de piso para soportar la pila y cerrar el aro del arco, patas del arco en RED 57.2×4.0, y refuerzo del riel trasero que ya no se alivia con la masa atrás) |
| Rigidez torsional | 8,905 N·m/° | 9,748 N·m/° |
| Resorte delantero | 311 lb/in | **397 lb/in** (carga de bache 7.8 kN) |
| Resorte trasero | 292 lb/in | **238 lb/in** |
| Reparto de frenado | 57% delante | **70% delante** |
| Disco delantero | Ø220 | **Ø240** (cabe en rin 13") |
| Pedal | 6.0:1, 428 N | **6.5:1 ajustable, 442 N y 65 mm** |
| Regeneración | – | limitada a ~0.20 g (el eje trasero carga menos al frenar) |
| Secciones de tubo | 6 | **7** (se añadió RED 57.2×4.0, sólo las 2 patas del arco) |

Sin booster el freno tiene poco margen en cualquier arquitectura: con CG 0.40 y la batería atrás tampoco había solución con pedal 6:1.

## Lo que hay que verificar al construir
* La caja de la pila deja **9 mm por lado** hasta las cubetas (z = ±0.31, ancho 0.46): conviene butacas de ≤ 0.44 m o separar los asientos 1–2 cm.
* Tapa de servicio en la consola, ventilación/venteo de la caja hacia afuera de la cabina, fusible y desconectador de servicio accesibles.
* Los resortes y la barra de balance se afinan en pruebas: los números son del presupuesto, no de un carro pesado.
