# Placa de torque del QS273 — diseño

**2026-08-04** · pieza que une el eje del motor de cubo QS273 a la punta del brazo tirado trasero.
Entrada: `calculos/resultados-suspension-trasera.md`. Salida esperada: DXF de corte láser.

## 1. Qué problema resuelve

El eje del QS273 **no gira**: es el estátor. Cuando el motor empuja la rueda, la rueda
devuelve el mismo par al eje (tercera ley). Si nada lo detiene, el eje gira en su
alojamiento, lo ovala y termina arrancando los cables de fase que salen por dentro del
propio eje — la falla clásica de los motores de cubo potentes sin brazo de torque.

Además el eje **solo se apoya de un lado**: dentro del rin 14" con llanta 175/70R14 no
cabe una horquilla que abrace la rueda. El motor de 27 kg queda en voladizo.

La placa hace tres trabajos: sujeta el eje contra el giro, mete toda la carga de la
rueda al brazo, y fija el toe-in con calzas.

## 2. Decisiones tomadas

| Decisión | Elección | Razón |
|---|---|---|
| Unión al brazo | **Atornillada**, 4× M12 10.9 en camisas soldadas a través del PTR | Se cambia sin cortar el brazo; las calzas dan el toe-in de 1-2 mm. Con M10 el aplastamiento en la placa quedaba en FS 2.0, al filo |
| Ménsula de caliper | **Integrada** en la placa exterior | Par de motor y de freno al mismo punto; una pieza menos, sin tolerancias acumuladas |
| Fabricación | **Sándwich de 2 placas de acero 8 mm, corte láser** | Ver §3 |

## 3. Por qué sándwich y no placa única

El voladizo del motor genera un momento de vuelco que intenta doblar la placa **fuera de
su plano**, que es donde una placa es débil. Con una sola placa habría que irse a 25-30 mm
de acero: cara, pesada, y masa no suspendida (lo peor para el agarre en baches).

Con dos placas separadas, ese momento se convierte en **fuerzas verticales dentro del
plano de cada placa**, que es justo lo que una placa hace bien. Estática del bache 3g,
placa exterior en y=0, interior en y=−50 mm, rueda en y=+90 mm:

```
ΣFz:  Fa + Fb = 6295 N
ΣMx (respecto a la placa interior):  6295 × 140 = Fa × 50
      →  Fa = +17.6 kN (exterior, hacia arriba)
      →  Fb = −11.3 kN (interior, hacia abajo)
```

Ambas son cargas en el plano — acero de 8 mm las traga sin despeinarse. **La separación
la regala el brazo**: el PTR es 70 alto × 50 ancho, así que las placas abrazan sus caras
y quedan a 50 mm sin piezas extra.

Sigue siendo el proceso más barato que existe (corte láser plano), pesa la mitad que la
placa gruesa, y si golpeas una la desatornillas y pones otra.

## 4. Arquitectura

```
        ── vista desde arriba ──

   brazo PTR 70×50×4
  ══════════════╗
                ║ ▓▓  ← placa REFUERZO (interior, 8 mm)
                ║ ▓▓     eje doble-D + 4 pads de tornillo
   4× M10 10.9  ║
   en camisas   ║ ▓▓  ← placa MOTOR (exterior, 8 mm)
   soldadas     ║ ▓▓     eje doble-D + pads + orejas de caliper
  ══════════════╝  └── eje QS273 ──►
```

- Las camisas de acero soldadas a través del PTR evitan que el apriete aplaste el tubo.
- Las calzas entre placa y flanco del PTR ajustan el toe-in que pide el brazo tirado.
- Las orejas del caliper nacen de la placa exterior, esculpidas por el mismo optimizador.

## 5. Casos de carga

Los cuatro se optimizan **simultáneamente** (suma de compliances). Optimizar solo el peor
caso da una pieza excelente en ese caso y frágil en los demás.

| # | Caso | Magnitud | Cómo entra a la placa |
|---|---|---|---|
| 1 | Tracción máxima | 350 N·m sobre el eje | Par en el plano, en el cubo doble-D |
| 2 | Frenado 1g | **630 N·m** | Par en el plano. Dos rutas: regen (por el eje) y fricción (por las orejas del caliper) — se modelan por separado |
| 3 | Bache 3g | 6295 N vertical → **+17.6 / −11.3 kN** por placa | Fuerza vertical en el cubo (§3) |
| 4 | Curva 1g | 2098 N lateral → momento de vuelco 630 N·m adicional | Igual que §3, con el brazo de palanca del radio de rueda |

Nota sobre el caso 2: `suspension_trasera.py:95` usa 0.9g (568 N·m) para dimensionar el
brazo. Aquí se usa **1g = 630 N·m** porque es el objetivo declarado del cálculo de frenos
(`que-falta-para-construir.md`) y porque esta pieza es la que no debe fallar.

## 6. Motor generativo — qué se construye

Archivo nuevo `calculos/placa_torque.py`. Reutiliza el núcleo SIMP de
`nodo_generativo.py` (filtro de densidad, actualización por criterio de optimalidad) pero
en **2D esfuerzo plano** con elemento Q4, no en 3D.

El 2D no es una simplificación: es el modelo correcto de una placa plana cargada en su
plano, y de paso impone la restricción de fabricación por construcción — lo que sale del
algoritmo *es* el contorno que corta el láser, sin tener que forzar nada.

Sobre eso, tres cosas que el optimizador de nodos no tiene:

1. **Multi-caso de carga.** Los cuatro casos se resuelven en el mismo sistema y la
   sensibilidad es la suma. Optimizar solo el peor caso da una pieza excelente en ese
   caso y frágil en los demás.
2. **Superficies funcionales impuestas.** El cubo del eje, la **brida de la junta
   atornillada** (banda continua a lo largo de cada hilera de tornillos) y los pads del
   caliper se fuerzan a material sólido. El algoritmo esculpe solo lo que las conecta.
   La brida hay que imponerla: minimizar deformación **siempre descarta apoyos
   redundantes**, así que sin ella el optimizador agarra los dos tornillos más cercanos y
   deja los otros dos como islas flotantes. El reparto de carga entre tornillos y la cara
   de apriete son requisitos de la junta, no de la rigidez.
3. **Apoyos elásticos.** Cada tornillo es un resorte de rigidez `G·A/t`, no un
   empotramiento rígido — un empotramiento reacciona momento él solo y falsea el reparto.
4. **Barrido de fracción de volumen.** La masa **no es un resultado del optimizador: es
   la restricción que se le impone**. Se barre y se elige la más ligera que todavía cumple
   FS ≥ 2. Sin esto la "masa optimizada" es solo el número que uno eligió de entrada.

Se corre dos veces: placa motor (con orejas de caliper) y placa refuerzo.

## 7. Verificación

Después de optimizar, chequeo de esfuerzos a escala real contra acero estructural
(σy = 250 MPa, igual que el resto del proyecto): aplastamiento en los planos del eje,
cortante y aplastamiento en los tornillos —**con las reacciones que salen del propio FEM**
(R = K·U − F), no de estática de mano, para ver si los cuatro tornillos de verdad
trabajan— y von Mises en el material del contorno resultante. **Objetivo FS ≥ 2**, el
mismo criterio que el chasis y el brazo.

**Hallazgo:** el aplastamiento en los planos del eje es el eslabón débil real. El par se
transmite como un par de fuerzas sobre las dos caras planas separadas 16 mm, o sea 21.9 kN
sobre 12 mm de ancho de plano: la placa desnuda de 8 mm da **FS 1.1**. Se resuelve con un
**doblador de 8 mm** soldado alrededor del cubo (anillo Ø56, misma hoja, mismo corte) →
FS 2.2. Esta es la razón por la que se arrancan los cables de fase en los montajes de
motor de cubo mal resueltos.

## 8. Entregables

- `calculos/placa_torque.py` — el optimizador
- `planos/placa-torque-motor.dxf` y `planos/placa-torque-refuerzo.dxf` — para el cortador
- `calculos/resultados-placa-torque.md` — geometría, masa, esfuerzos y FS
- `calculos/placa-torque.png` — la pieza con contexto de escala
- BOM de la suspensión trasera y `que-falta-para-construir.md` actualizados

## 9. Datos a confirmar con QS Motor antes de cortar

Van en la misma lista de "confirmar por escrito antes de pagar" donde ya está la versión
de rin 14". Todo el diseño queda parametrizado: si un dato cambia, se ajusta la constante
y se re-corre.

| Dato | Valor supuesto | Impacto si cambia |
|---|---|---|
| Ø del eje | 20 mm | Tamaño del cubo doble-D |
| Entrecaras de los planos | 16 mm | Igual |
| **Largo del eje que sobresale del lado interior** | **≥ 78 mm** | Crítico: se necesita 8 + 50 + 8 + tuerca. Si es menor, las placas se acercan con separadores y se re-corre |
| Ancho del cuerpo del motor | 130 mm | Voladizo de 90 mm → cambia el momento de vuelco |
| Ø del disco de freno y su patrón | 220 mm | Posición de las orejas del caliper |

**Fallback si el eje interior resulta corto:** las placas dejan de abrazar el PTR y se
atornillan a orejas soldadas en sus flancos, con separación reducida (~34 mm). El momento
de vuelco sube un 45% en cada placa, que el acero de 8 mm sigue aguantando; se re-corre el
optimizador con el parámetro nuevo.
