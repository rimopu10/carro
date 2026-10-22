# Frenos — dimensionado del sistema de 4 discos

Disco hidráulico ×4, doble bomba con balance bar, **sin booster**, más regen. Generado por `frenos.py`.

**Criterio de partida:** el freno de fricción tiene que dar **1g él solo**, sin contar con el regen. El regen puede desaparecer sin avisar (batería llena, BMS abierto, controlador en falla) y el carro tiene que frenar igual. Todo lo que sigue está dimensionado así; el regen es un extra que alarga la vida de las pastillas, no parte del cálculo de seguridad.

## 1. Reparto de frenado (lo que decide si el carro trompea)

Al frenar, el peso se pasa adelante: 690 kg × 1.0g × 0.40 m / 2.13 m = **130 kg** de transferencia.

| | Estático | A 1g |
|---|---|---|
| Eje delantero | 324 kg (47%) | 454 kg (66%) |
| Eje trasero | 366 kg (53%) | 236 kg (34%) |

El carro es de motor central y batería atrás: parado carga **62% atrás**, pero frenando a 1g se le da la vuelta y queda **66% adelante**. Un reparto de frenado pensado con el peso estático bloquearía el trasero.

La barra de balance da un reparto **fijo**; el ideal cambia con la deceleración. La regla de seguridad es que el eje trasero **nunca** bloquee primero — si bloquea atrás el carro se sale de cola sin remedio; si bloquea adelante solo pierde dirección y sigue derecho.

- Mínimo teórico para que no bloquee atrás a 1.0g: **65.8%** adelante.
- **Reparto elegido: 70% adelante / 30% atrás** (con margen). La barra de balance permite afinarlo en las pruebas de F3.

## 2. Par y hardware por rueda

A 1.0g la fuerza total de frenado es 6769 N.

| | Par por rueda | Disco | Radio efectivo |
|---|---|---|---|
| Delantero | **681 N·m** | Ø240 mm | 101 mm |
| Trasero | **305 N·m** | Ø220 mm (el del QS273) | 92 mm |

Área de pistón necesaria por caliper delantero, a 80 bar de línea y µ de pastilla 0.4:

| Disco delantero | Área de pistón | Pistón equivalente | Mejor pedal posible | |
|---|---|---|---|---|
| Ø180 mm | 1408 mm² | Ø42 mm | ninguna combinación cumple | ✗ |
| Ø200 mm | 1267 mm² | Ø40 mm | ninguna combinación cumple | ✗ |
| Ø220 mm | 1152 mm² | Ø38 mm | ninguna combinación cumple | ✗ |
| Ø240 mm | 1056 mm² | Ø37 mm | 442 N / 65 mm | ✓ elegido |
| Ø260 mm | 975 mm² | Ø35 mm | no cabe en rin 13" | ✗ |

Trasero (disco Ø220 fijo, el del QS273): **516 mm²** → pistón equivalente Ø26 mm.

**Si el pedal se siente largo en las pruebas**, el disco de Ø240 es el cambio directo: misma fuerza de pedal pero 65 mm de recorrido en vez de 65, y menos temperatura por tener más masa de corona. Solo hay que verificar que libre el rin de 13".

**Comprobación cruzada con la placa de torque.** El servicio pide 305 N·m por rueda trasera, pero `placa_torque.py` la dimensionó para **630 N·m**. No es contradicción: 630 N·m es el tope real que una rueda trasera puede transmitir antes de patinar, y ocurre a **baja** deceleración, cuando el eje trasero todavía carga sus 183 kg estáticos (µ=1 × 183 kg × 0.300 m). Bien: la placa tiene 2.06× de margen sobre el caso de servicio.

**Aviso sobre el donante ATV.** Un freno de ATV 300 típico trae disco de Ø180-200 mm con caliper de un pistón chico. Por la tabla, esos diámetros no dan: el pistón tendría que ser irreal y la pedalera se vuelve imposible. Se reusa la **mangueta y la maza** del ATV — que es lo que define la geometría de suspensión ya calculada — pero se le monta **disco de Ø240 mm** y caliper de compacto o de moto deportiva de 2-4 pistones, con una ménsula de adaptación cortada en láser (del mismo tipo que las cartelas que ya hicimos).

## 3. Pedalera (sin booster) — y por qué no se elige aparte del disco

Hay una trampa aquí que vale la pena entender antes de ver la tabla. La fuerza de pedal es `P·A_bomba/relación` y el recorrido es `(V/A_bomba)·relación`. Multiplicando las dos, el calibre de bomba y la relación **se cancelan**:

```
fuerza de pedal × recorrido = 2 · (P·A_caliper) · avance de pistón
```

O sea: **el trabajo que tiene que meter el pie es invariante**. La relación de pedal y el calibre de bomba solo intercambian fuerza por recorrido — no se puede ganar por ahí. Lo único que baja ese producto es **disco más grande** (más brazo de palanca), mejor pastilla, o desplazar menos fluido (mangueras de malla, buen purgado, poco knock-back).

Por eso el disco y la pedalera se eligen **juntos**. Con el disco de Ø180 del donante ATV el trabajo de pedal sale de 29.1 N·m y **ninguna** combinación de bomba y relación cumple; con Ø240 baja a 23.8 N·m y ya hay margen.

Objetivo: **≤ 450 N** de pie y **≤ 70 mm** de recorrido, a 80 bar de línea.

| Bomba delantera | Bomba trasera | Relación de pedal | Fuerza de pedal | Recorrido | |
|---|---|---|---|---|---|
| Ø15.9 mm | Ø14.3 mm | 6.5:1 | 442 N | 65 mm | ✓ elegida |
| Ø14.3 mm | Ø14.3 mm | 7.0:1 | 367 N | 87 mm | no cumple |
| Ø14.3 mm | Ø14.3 mm | 6.5:1 | 395 N | 81 mm | no cumple |
| Ø14.3 mm | Ø15.9 mm | 7.0:1 | 410 N | 87 mm | no cumple |
| Ø15.9 mm | Ø14.3 mm | 7.0:1 | 410 N | 70 mm | no cumple |
| Ø14.3 mm | Ø14.3 mm | 6.0:1 | 428 N | 75 mm | no cumple |
| Ø14.3 mm | Ø15.9 mm | 6.5:1 | 442 N | 81 mm | no cumple |
| Ø15.9 mm | Ø15.9 mm | 7.0:1 | 454 N | 70 mm | no cumple |
| Ø14.3 mm | Ø17.5 mm | 7.0:1 | 458 N | 87 mm | no cumple |
| Ø17.5 mm | Ø14.3 mm | 7.0:1 | 458 N | 58 mm | no cumple |
| Ø14.3 mm | Ø14.3 mm | 5.5:1 | 467 N | 68 mm | no cumple |
| Ø14.3 mm | Ø15.9 mm | 6.0:1 | 479 N | 75 mm | no cumple |

**Elegida: bomba delantera Ø15.9 mm + trasera Ø14.3 mm, pedal 6.5:1** → **442 N** de pie y **65 mm** de recorrido para 1.0g.

Para referencia: un carro con booster pide 200-250 N; un fórmula sin booster 500-700 N. Estamos en el rango de un kart pesado, que es exactamente lo que es este carro. **Doble circuito** (una bomba por eje): si revienta una manguera, el otro eje sigue frenando.

**Margen: escaso.** De 480 combinaciones evaluadas solo **1** cumplen fuerza y recorrido a la vez. No es un sistema con holgura: es el precio de no llevar booster en un carro de 690 kg.

Lo que se siente al manejar (la fuerza es proporcional a la deceleración):

| Frenada | Deceleración | Fuerza de pedal |
|---|---|---|
| suave, de ciudad | 0.20g | 88 N |
| normal | 0.35g | 155 N |
| fuerte | 0.60g | 265 N |
| pánico | 1.00g | 442 N |

Y casi todo el frenado de ciudad ni siquiera llega al pedal: lo hace el regen al soltar el acelerador (§5).

**Sensibilidad a la pastilla.** Todo esto está calculado con µ = 0.4 (pastilla orgánica corriente, **caliente** — el peor momento, no el mejor):

| µ de pastilla | Fuerza de pedal para 1g | |
|---|---|---|
| 0.33 | 536 N | pastilla barata recalentada |
| 0.40 | 442 N | valor de diseño |
| 0.45 | 393 N | semi-metálica / sinterizada |
| 0.50 | 354 N | semi-metálica / sinterizada |

**Comprar pastilla semi-metálica o sinterizada, no la más barata.** Es la palanca más efectiva que queda para aligerar el pedal, y cuesta unos pesos.

## 4. Térmico

Frenada de pánico desde 100 km/h: **266 kJ** que hay que convertir en calor.

| | Masa de la corona | Energía por disco | Subida de temperatura |
|---|---|---|---|
| Disco delantero Ø240 | 1.09 kg | 93 kJ | **+185 °C** |
| Disco trasero Ø220 | 0.92 kg | 40 kJ | **+95 °C** |

Una frenada aislada no es problema. El riesgo real son las frenadas repetidas: sin ventilación forzada, el tercer o cuarto pánico seguido ya llega a temperatura de fade con pastilla orgánica.

Bajada sostenida al 10% a 40 km/h: **7.5 kW** continuos. Los dos QS273 aguantan 16 kW nominales, así que **en bajada el regen se lo come entero y los discos ni se enteran** — siempre que la batería tenga dónde meter la energía. Con la batería llena el regen se corta: en bajada larga hay que salir con la batería por debajo del 90%.

## 5. Regen — dónde está su límite

Los dos QS273 dan 350 N·m por rueda de regen → 2329 N → **0.34g**. Eso cubre casi todo el frenado de diario.

**Pero el regen actúa SOLO atrás.** A 0.34g el eje trasero tiene que generar toda esa fuerza él solo, lo que le exige un coeficiente de adherencia de **µ = 0.74**:

- Pavimento seco (µ ≈ 0.9): sobra. ✓
- Mojado o terracería (µ ≈ 0.4): **el eje trasero se bloquea** y el carro se sale de cola, sin que el piloto haya tocado el pedal.

**Configuración obligatoria en los controladores:** limitar el regen a ~**0.20g** (el punto donde el trasero solo exige µ 0.40), y ponerlo progresivo con el pedal en vez de todo-o-nada al soltar el acelerador. Es un parámetro de software: se afina en F3 y no cuesta hardware. Sin esto el carro es peligroso en piso mojado.

## 6. Freno de estacionamiento

Con motores de cubo no hay transmisión donde "dejarlo en velocidad": el freno de mano es la única cosa que sujeta el carro. Se resuelve con **caliper trasero con palanca mecánica integrada** — la misma pinza hace freno de servicio y de mano, sin ménsulas ni pinzas extra, y la placa de torque ya tiene su montaje.

En pendiente del 20% (la más fuerte que se ve en calle):

- Fuerza a sujetar: 1327 N · adherencia que exige al eje trasero: **µ = 0.41** (sobra con cualquier piso decente) ✓
- Par por rueda trasera: 199 N·m → fuerza de apriete de la palanca **2.7 kN**

Un caliper de palanca de cable entrega 3-5 kN, así que cumple con margen. **Al comprar:** verificar que el patrón de barrenos coincida con las orejas de la placa de torque (82 mm de separación, a 110 mm de radio); si no, se re-corre `placa_torque.py` con las cotas nuevas — son 5 minutos.

## 7. Lista de compra de esta sección

- 2 × disco delantero Ø240 mm × 5 mm (macizo) + ménsula de adaptación a la maza del ATV (corte láser)
- 2 × caliper delantero de área de pistón ≥ 1056 mm² (equivalente a un pistón de Ø37 mm) + ménsula
- 2 × caliper trasero **con palanca de freno de mano**, área de pistón ≥ 516 mm² (Ø26 mm equivalente); el disco lo trae el QS273
- 1 × bomba de freno Ø15.9 mm (circuito delantero) + 1 × Ø14.3 mm (trasero) + barra de balance ajustable + depósitos
- 1 × pedal de freno colgante o de piso, relación **6.5:1**
- Manguera flexible DOT (4 tramos) + línea rígida de acero + niples; líquido DOT4
- 1 × palanca de freno de mano con cable doble + tensores

**Nunca recortar aquí** (doc maestro §9): frenos es de las cuatro cosas donde no se ahorra.
