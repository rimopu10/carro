# Placa de torque del QS273 — diseño generativo

La pieza que impide que el eje del motor de cubo gire dentro del brazo tirado, y que mete toda la carga de la rueda al brazo. Generada por `placa_torque.py` (SIMP 2D esfuerzo plano, 4 casos de carga simultáneos).

## Por qué son dos placas y no una

El eje del QS273 se apoya de un solo lado — dentro del rin 14" no cabe una horquilla que abrace la rueda — así que el motor de 27 kg queda en voladizo a **90 mm** del plano de la placa. Ese voladizo genera un momento que intenta doblar la placa FUERA de su plano, justo donde una placa es débil.

Con dos placas separadas **50 mm** (el ancho del PTR, que las abraza sin piezas extra), el momento se convierte en fuerzas verticales **dentro del plano** de cada placa:

| Caso en la rueda | Placa exterior | Placa interior |
|---|---|---|
| Bache 3g (6.3 kN vertical) | **+17.6 kN** | **-11.3 kN** |
| Curva 1g (2.1 kN lateral) | +18.5 kN | -16.4 kN |
| Frenado 1g (2.1 kN longitudinal) | +5.9 kN | -3.8 kN |

Son cargas en el plano: acero de 8 mm las traga. Una placa sola tendría que irse a 25-30 mm — cara, pesada, y masa no suspendida (lo peor para el agarre en baches).

## Casos de carga optimizados

Los cuatro se optimizan **a la vez** (suma de compliances). Optimizar solo el peor da una pieza excelente en ese caso y frágil en los demás.

1. par por el eje 350 N·m
2. bache 3g +17.6 kN vertical
3. curva 1g +18.5 kN vertical
4. frenado 1g: 6.6 kN en el caliper + +5.9 kN long.

El par por el eje se limita a **350 N·m** (tope del QS273, y por tanto también el tope del regen). El par de frenado de fricción (**630 N·m**, 1g) NO pasa por el eje: va del disco al caliper y de ahí a la placa exterior — por eso solo esa lleva orejas.

## Qué impuse yo y qué decidió el algoritmo

Vale la pena separarlo, porque "diseño generativo" no quiere decir que la máquina invente la pieza sola. Se le declaran las **superficies funcionales** — lo que la pieza tiene que tener sí o sí — y el algoritmo resuelve el material que las conecta.

**Impuesto (material obligatorio):**

- El cubo alrededor del eje: anillo sólido de Ø56 mm.
- La **brida de la junta**: banda continua de 32 mm de alto a lo largo de cada hilera de tornillos. Es la cara que aprieta contra el flanco del PTR y donde asientan las calzas del toe.
- Los pads de los tornillos y de las orejas del caliper.

**Por qué la brida hay que imponerla.** Sin ella el optimizador entrega una pieza que solo agarra los dos tornillos más cercanos y deja los otros dos como islas flotantes, sin material que llegue hasta ellos. No es un error del algoritmo: **minimizar deformación siempre descarta apoyos redundantes**, porque estirarse hasta el tornillo lejano cuesta material y no rigidiza. Lo que ese criterio no ve es que con dos tornillos la carga por tornillo se dispara y la junta no se puede apretar bien. El reparto de carga entre tornillos y la cara de apriete son requisitos de la junta, no de la rigidez.

**Decidido por el algoritmo:** toda la telaraña que une el cubo con la brida y con las orejas del caliper — que es donde estaba el trabajo de verdad.

## Barrido de material (de dónde sale la masa)

La fracción de volumen **no es un resultado del optimizador: es la restricción que se le impone**. El algoritmo reparte el material que se le da, no decide cuánto. Para una pieza gobernada por resistencia hay que barrerla y quedarse con la más ligera que todavía cumple el criterio.

**placa motor (exterior)**

| Fracción de volumen | Masa | von Mises (p99.5) | FS | |
|---|---|---|---|---|
| 0.40 | 1.157 kg | 69 MPa | **3.61** | ok |
| 0.36 | 1.041 kg | 72 MPa | **3.47** | ok |
| 0.33 | 0.955 kg | 75 MPa | **3.32** | ok |
| 0.30 | 0.868 kg | 80 MPa | **3.12** | ok |
| 0.28 | 0.810 kg | 86 MPa | **2.91** | ok |
| 0.26 | 0.752 kg | 95 MPa | **2.63** | ok |
| 0.24 | 0.694 kg | 107 MPa | **2.34** | ✓ elegida |
| 0.22 | 0.636 kg | 197 MPa | **1.27** | insuficiente |
| 0.20 | 0.592 kg | 175 MPa | **1.43** | desconectada |

**placa refuerzo (interior)**

| Fracción de volumen | Masa | von Mises (p99.5) | FS | |
|---|---|---|---|---|
| 0.40 | 1.163 kg | 65 MPa | **3.84** | ok |
| 0.36 | 1.046 kg | 66 MPa | **3.78** | ok |
| 0.33 | 0.959 kg | 67 MPa | **3.72** | ok |
| 0.30 | 0.872 kg | 68 MPa | **3.68** | ok |
| 0.28 | 0.814 kg | 71 MPa | **3.53** | ok |
| 0.26 | 0.756 kg | 72 MPa | **3.45** | ok |
| 0.24 | 0.698 kg | 76 MPa | **3.27** | ok |
| 0.22 | 0.639 kg | 80 MPa | **3.11** | ok |
| 0.20 | 0.581 kg | 89 MPa | **2.81** | ✓ elegida |
| 0.18 | 0.537 kg | 131 MPa | **1.90** | insuficiente |

## Resultado

| | Placa motor (exterior) | Placa refuerzo (interior) |
|---|---|---|
| Espesor | 8 mm | 8 mm |
| Área de material | 111 cm² | 93 cm² |
| Masa por pieza | **0.69 kg** | **0.58 kg** |
| von Mises máx (p99.5) | 107 MPa | 89 MPa |
| FS contra σy 250 MPa | **2.3** | **2.8** |

Masa del juego completo del carro — 2 ruedas × (2 placas + 2 dobladores de 0.38 kg): **4.1 kg**. Es masa NO suspendida, así que cada gramo cuenta doble para el agarre en baches.

## Verificaciones que el topopt no ve

**Aplastamiento en los planos del eje.** El par se transmite como un par de fuerzas sobre las dos caras planas, separadas 16 mm: F = 350/0.016 = **43.7 kN** sobre un ancho de plano de 12.0 mm.

- Con la placa desnuda de 8 mm: σ = 456 MPa → FS **0.5** — **insuficiente**.
- Con un **doblador de 22 mm** soldado alrededor del cubo (Ø56 mm, misma placa, mismo corte láser): espesor local 30 mm → σ = 122 MPa → FS **2.1** ✓

Este es el eslabón débil real de los montajes de motor de cubo y la razón por la que se arrancan los cables de fase. El doblador cuesta un anillo extra en la misma hoja y un cordón de soldadura.

**Grupo de 4 tornillos M12 10.9.** Las reacciones salen del propio FEM (R = K·U − F en los grados sujetos), no de estática de mano — así se ve si los cuatro tornillos realmente trabajan:

| Tornillo (u, v) mm | Placa motor | Placa refuerzo |
|---|---|---|
| (36, +25) | 12.4 kN | 10.9 kN |
| (36, -25) | 12.2 kN | 10.9 kN |
| (96, +25) | 7.3 kN | 3.0 kN |
| (96, -25) | 3.2 kN | 3.0 kN |

El más cargado toma **12.4 kN**.

- Cortante: 110 MPa contra 624 MPa de capacidad → FS **5.7** ✓
- Aplastamiento en la placa: 129 MPa contra 375 MPa (1.5·σy) → FS **2.9** ✓

Los tornillos pasan por **camisas de acero soldadas a través del PTR**, si no el apriete aplasta el tubo. Las calzas entre placa y flanco del PTR dan el toe-in de 1-2 mm que pide el brazo tirado.

## Archivos de corte

- `planos/placa-torque-motor.dxf` — ×2 (una por rueda), acero 8 mm
- `planos/placa-torque-refuerzo.dxf` — ×2, acero 8 mm
- `planos/placa-torque-doblador.dxf` — ×4 (uno por placa), acero 22 mm

Todos en mm, capa `CORTE`, listos para cotizar. El hueco del eje va con doble-D; pedir corte y luego **rimar a medida con el eje en mano** (holgura 0 — cualquier juego aquí se convierte en golpeteo y termina ovalando).

## Confirmar con QS Motor antes de cortar

| Dato | Valor usado | Si cambia |
|---|---|---|
| Ø del eje | 20 mm | Cambia el cubo y el doblador |
| Entrecaras de los planos | 16 mm | Cambia el aplastamiento (va al cuadrado del espesor requerido) |
| Largo del eje libre del lado interior | **≥ 84 mm** | **El dato crítico.** No es solo 8+50+8+tuerca: entre la cara del motor y la placa exterior viven el disco y el caliper, que piden 30 mm más. Si el eje es más corto, ver el fallback del spec |
| Ancho del cuerpo del motor | 130 mm | Cambia el voladizo y todo el reparto entre placas |
| Ø del disco y patrón del caliper | 220 mm / 82 mm | Cambia la posición de las orejas |
