# Dirección — Ackermann, relación, esfuerzo y círculo de giro

Cremallera manual de compacto, sin servo. Generado por `direccion.py`, que importa la geometría de `suspension_delantera.py` para que no haya dos verdades.

**Método:** al girar el volante con la suspensión quieta, las rótulas no se mueven — la mangueta solo rota alrededor del eje de kingpin. Eso deja una sola incógnita (el ángulo de rotación) con una sola ecuación (el tie rod conserva su largo), y se resuelve exacto para las dos ruedas. Nada de fórmulas aproximadas de Ackermann.

> ## ⛔ CONFLICTO GEOMÉTRICO SIN RESOLVER — leer antes que nada
>
> **La rótula de la cremallera y el larguero inferior del chasis se pelean por el mismo espacio, y no hay forma de resolverlo moviendo la cremallera.**
>
> - En su posición actual (x=385, y=207, z=505) el tie rod pasa a **29 mm por dentro** de la holgura mínima contra el larguero `fb_lo–fx_lo` y la pata delantera de la horquilla inferior. Físicamente no se puede montar.
> - Se barrieron **1561 posiciones libres de interferencia** (x, y y z). La mejor de todas da un bump steer de **2.72°/25 mm**, contra el tope de 0.10. Es casi cien veces peor: el carro se dirigiría solo al pasar un tope.
> - La razón es de fondo: el bump steer se minimiza cuando el tie rod sigue el arco de la horquilla inferior, o sea a **su misma altura** — y esa altura es exactamente donde vive el larguero inferior del chasis.
>
> **Esto NO se arregla con la dirección: se arregla con el chasis.** Las tres salidas reales son:
>
> 1. **Bajar los pivotes de la horquilla inferior a ménsulas por debajo del larguero** (~50 mm). Es lo que de todas formas hace falta: hoy `LA1` y `LA2` caen *dentro* de los nodos del chasis y el buje no cabe. Al bajarlos, se abre el hueco por donde pasa el tie rod. Obliga a re-correr toda la cinemática delantera (camber, centro de balanceo, bump steer).
> 2. **Partir el larguero inferior** con un quiebre local que libre el paso del tie rod. Más soldadura y hay que re-verificar el FEM.
> 3. **Cremallera de montaje trasero** (detrás del eje), que cambia el signo de todo el planteamiento de Ackermann de este documento.
>
> Mientras tanto, **los números de abajo son válidos como cinemática pero la pieza no se puede montar**. No cortar la ménsula de cremallera.

## 1. Qué Ackermann trae la geometría heredada

Los puntos duros venían afinados para camber, caster y bump steer, pero el Ackermann nunca se había medido. Medido ahora, con la rueda exterior a 20°:

| | Valor |
|---|---|
| Largo del brazo de mangueta (vista superior) | 117 mm |
| **Ackermann heredado** | **+42%** |
| Bump steer heredado | 0.043°/25 mm |

**+42% no es un desastre, pero se queda corto para un carro que estaciona.** Ackermann por debajo de 100% significa que la rueda interior gira menos de lo que pide el giro, así que las dos llantas van algo peleadas en maniobra lenta: chirrían, se comen los hombros y el volante se siente pegajoso al dar vuelta en una esquina. En pista se usa a propósito — a alto ángulo de deriva la rueda interior quiere menos ángulo — pero este carro es de calle y terreno privado, donde manda el estacionamiento. Objetivo: **85%**.

**Una aclaración que vale la pena, porque yo mismo me equivadué al empezar.** La regla de manual dice que el brazo de mangueta debe apuntar al centro del eje trasero. Eso vale para un varillaje **trapezoidal**, donde una sola barra une los dos brazos. Con **cremallera** no aplica: el Ackermann depende también de dónde está la cremallera y de qué tan largo es el tie rod, porque el varillaje es otro. Por eso el brazo heredado apunta 7° hacia adentro (la regla del trapecio pediría 18° hacia afuera) y aun así el Ackermann sale positivo. Aquí todo se midió resolviendo el varillaje real, no aplicando la regla.

## 2. La corrección no cuesta ni una pieza

Como el Ackermann de una cremallera depende de dónde está la cremallera, lo primero que hay que probar es **moverla** — que es gratis, porque solo cambia dónde se atornilla al mamparo. Barrido de su posición longitudinal y su ancho (280–520 mm × 400–610 mm, 255 posiciones), con la mangueta del donante **intacta**:

- Rango de Ackermann alcanzable moviendo solo la cremallera: hasta **+223%**.
- **La altura (y = 207 mm) no se toca**: es la que fija el bump steer y ±5 mm lo duplican.

Alcanza de sobra. **No hay que tocar la mangueta ni fabricar ningún brazo.**

Pero subir el Ackermann no sale gratis: mover la cremallera cambia el largo del tie rod, y con él qué tan bien sigue el arco de los brazos. Así que no se busca "el que dé 85%" sino el **compromiso**. Cada posición candidata se verificó re-corriendo el barrido 3D completo de bump steer; ésta es la frontera de lo alcanzable (ninguna de estas es peor que otra en las dos cosas a la vez):

| Cremallera x | Cremallera z | Ackermann | Bump steer | |
|---|---|---|---|---|
| 385 mm | 475 mm | +64% | 2.723°/25mm | más Ackermann, peor bump steer |
| 385 mm | 490 mm | +69% | 3.236°/25mm | más Ackermann, peor bump steer |
| 355 mm | 490 mm | +91% | 3.248°/25mm | más Ackermann, peor bump steer |
| 370 mm | 505 mm | +79% | 3.458°/25mm | más Ackermann, peor bump steer |
| 355 mm | 490 mm | +90% | 3.793°/25mm | más Ackermann, peor bump steer |
| 370 mm | 520 mm | +86% | 4.125°/25mm | más Ackermann, peor bump steer |
| 370 mm | 520 mm | +85% | 5.070°/25mm | más Ackermann, peor bump steer |

**Criterio: el bump steer manda.** Uno hace que el carro se dirija solo al pasar un tope; el otro solo desgasta llanta al estacionar. Así que se toma el mejor Ackermann que quepa bajo **0.060°/25 mm**, en vez de apurar el Ackermann hasta el tope duro de 0.10.

**Elegida: cremallera en x = 385 mm, z = 505 mm** (antes 410 / 510). Se mueve 25 mm en largo y 5 mm en ancho — nada más que la posición de sus dos ménsulas al mamparo.

> **Autoverificación:** la posición que vive hoy en `suspension_delantera.py` es x=385, z=505. Coincide con la que este barrido vuelve a elegir, así que las dos fuentes dicen lo mismo.

| | Heredado | Corregido |
|---|---|---|
| Ackermann | +42% | **+68%** |
| Bump steer | 0.043°/25mm | **0.018°/25mm** |

| Punto duro | x | y | z |
|---|---|---|---|
| Terminal de dirección (sin cambio) | 430 | 198 | 695 |
| **Extremo de cremallera (nuevo)** | **385** | 207 | **505** |
| Tie rod (centro a centro) | 195 mm | | |

**El bump steer no solo se conserva: mejora**, de 0.043 a 0.018°/25 mm. Al mover la cremallera cambia el largo del tie rod, y resulta que hay largos que siguen mejor el arco de los brazos. No era el objetivo — salió de buscar el compromiso en vez de apurar el Ackermann — pero es la confirmación de que valía la pena re-correr la cinemática 3D de cada candidato en vez de suponer que mover la cremallera es inocuo.

**La altura de la cremallera (207 mm) no se toca**: ±5 mm duplican el bump steer. Montarla con barrenos ovalados y calzas para afinar en el carro, como ya decía la suspensión delantera.

## 3. Relación, topes y círculo de giro

El tope no lo pone la cremallera sino la **rueda interior**, que es la que pega con el brazo inferior o con el interior del rin. Se limita a 40°.

| Parámetro | Heredado | Corregido |
|---|---|---|
| Carrera de cremallera usada | ±62 mm | ±57 mm |
| Ángulo rueda exterior | 30.8° | 27.8° |
| Ángulo rueda interior | 40.5° | 40.3° |
| Vueltas de tope a tope | 2.8 | **2.5** |
| Relación total | 14:1 | **13:1** |
| Diámetro de giro | 8.5 m | **9.3 m** |

**El Ackermann alto se paga con círculo de giro.** Con más Ackermann la rueda interior gira más para el mismo ángulo exterior, así que llega antes a su tope de 40° y el exterior se queda en 27.8° en vez de 30.8°. El círculo pasa de 8.5 a 9.3 m. Es un intercambio real, no un defecto: se gana que las llantas no peleen en maniobra lenta y se pierde algo de radio. Si al armarlo resulta que la rueda interior sí libra más de 40°, se sube el tope y se recupera el radio — por eso hay que medirlo en el carro (§5).

2.5 vueltas y 13:1 es relación directa de carro deportivo ligero (un compacto con servo anda en 3.2 vueltas y 16-18:1). Directo se siente mejor y además es lo único que se puede hacer sin servo: más desmultiplicación aligeraría el volante pero habría que dar más vueltas.

## 4. Esfuerzo en el volante (sin servo)

El caso duro es girar **parado en seco**, que es cuando hay que torcer la huella de la llanta sobre el piso. Fórmula de Taborek para el par de pivotamiento:

| | Valor |
|---|---|
| Carga por rueda delantera | 131 kg |
| Par de pivotamiento por rueda | 45 N·m |
| Fuerza en cada tie rod | 390 N |
| Par en el volante | 5.6 N·m |
| **Fuerza en el aro (Ø330 mm), parado** | **34 N** |
| Fuerza en el aro rodando | ~6 N |

34 N con las dos manos es un volante firme pero perfectamente manejable — comparable a un carro chico de los 80 sin servo. Ayudan tres cosas que ya están en la geometría: el eje delantero solo carga 38% del peso (los motores van atrás), el radio de pivotamiento es chico, y la llanta es angosta. **Y casi nunca se gira totalmente parado**: rodando aunque sea a paso de hombre baja a ~6 N.

Si al armarlo se siente pesado, la salida es subir la presión de las llantas o alargar el brazo de dirección — pero alargarlo baja el ángulo de giro máximo y sube el diámetro de vuelta. Es un intercambio, no una mejora gratis.

## 5. Columna y montaje

- Columna de compacto de deshuesadero con **2 crucetas (junta universal)**: una en el volante y otra en el piñón. Los ángulos de las crucetas deben ser parecidos entre sí y **en fase**, si no la dirección se siente que "pulsa" al girar.
- **Junta de seguridad plegable o columna colapsable del donante**: en un impacto frontal la columna no debe empujar la barra del volante contra el pecho.
- La cremallera va atornillada al mamparo delantero con **barrenos ovalados y calzas** para afinar altura en el carro (§3).
- Topes de giro: verificar en el carro que a tope la llanta no pegue con el brazo inferior ni con el interior del rin, ANTES de confiar en la carrera de ±75 mm de la cremallera. Si pega, se limita con topes en la cremallera y se re-corre este script.

## 6. Lista de compra de esta sección

- 1 × cremallera manual de compacto (donante) — medir su carrera real y su avance por vuelta; aquí se supuso ±75 mm y 45 mm/vuelta
- 1 × columna con 2 crucetas + soporte, preferentemente colapsable
- 1 × volante Ø330 mm con maza
- 2 × terminal de dirección (rótula) + 2 × rótula axial de cremallera
- 2 × ménsula de cremallera al mamparo, corte láser, con barrenos ovalados (posición nueva: x = 385 mm, z = ±505 mm)
- **Brazo de dirección: ninguno.** El de la mangueta del donante se queda como viene.
- Tubo roscado derecha/izquierda para el tie rod (permite ajustar convergencia sin desmontar)
