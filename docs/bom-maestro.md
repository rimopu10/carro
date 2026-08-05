# BOM maestro — la hoja con la que se compra el carro

**2026-08-04** · generado por `calculos/bom.py`. Cierra F0: sin esto no se puede pedir nada.

Hoja para cotizar: **`docs/bom-maestro.csv`** (trae una columna `precio_cotizado` vacía para llenar).

> **Sobre los precios.** Son estimados anclados al presupuesto del doc maestro (julio 2026) y sirven para dimensionar, **no para pagar**. Lo que este documento aporta de verdad es la *especificación de pedido* y la *cantidad* de cada pieza, que salen de los cálculos y no de una suposición. Pedir 3 cotizaciones de los renglones grandes antes de comprometerse.

## 1. Orden de compra (esto es lo que importa)

No se compra todo junto. El orden lo dicta el tiempo de entrega, no el gusto:

1. **HOY — los dos pedidos largos:** el kit de motores y las celdas + BMS. Entre 4 y 10 semanas de entrega, y **todo F1 y F2 dependen de ellos**. Antes de pagar hay que cerrar la lista de confirmaciones de §5.
2. **En cuanto haya taller — acero y corte:** con el acero en casa se puede empezar a soldar el frame mientras llegan los motores.
3. **Deshuesadero, sin prisa pero antes de F1:** cremallera, columna, manguetas ATV, calipers, butacas. Es la parte que depende de la suerte, así que conviene empezar a buscar temprano (§4).
4. **F2 en adelante:** eléctrico, cabina, carrocería. **El cableado HV todavía no se puede pedir** — faltan los calibres del diagrama unifilar.

## 2. La lista

### Propulsión — $49,700 a $73,200

| Fase | Item | Especificación de pedido | Cant. | Entrega | Estimado |
|---|---|---|---|---|---|
| F0 | Kit 2× motor de cubo + controladores | QS273 8 kW 96 V, **versión rin desmontable de carro 14"** (en 13" no cabe), 2 controladores tipo APT96600 / Fardriver ND96530 con regen configurable, acelerador de pedal hall, selector F/N/R | 1 kit | 6-10 semanas | $38,700–53,700 |
| F2 | Protecciones y mando HV | Contactor principal 400 A + fusible 400 A + resistencia de precarga + paro de emergencia + desconectador de servicio | 1 kit | 2-4 semanas | $4,500–8,000 |
| F2 | Convertidor DC-DC | 96→12 V, 30 A, **aislado** (no hay batería de 12 V en el carro) | 1 pza | 2-4 semanas | $2,500–4,500 |
| F2 | Cableado HV + 12 V | Cable naranja de calibre según el diagrama unifilar, conectores, fundas, pasamuros. **Calibres PENDIENTES: no se puede pedir hasta tener el unifilar** (punto 7) | 1 lote | — | $4,000–7,000 |

### Batería — $40,000 a $58,500

| Fase | Item | Especificación de pedido | Cant. | Entrega | Estimado |
|---|---|---|---|---|---|
| F0 | Celdas LiFePO4 | 30 × prismática 105 Ah grado A (EVE/CATL), mismo lote, con busbars y tornillería | 30 pza | 4-8 semanas | $26,000–36,000 |
| F0 | BMS | 30S LiFePO4, **250-300 A de descarga continua** (crítico: menos capa los motores), balanceo activo, Bluetooth | 1 pza | 4-6 semanas | $6,000–9,000 |
| F2 | Cargador | LiFePO4 96 V, 15-18 A, enchufable a 120 V | 1 pza | 2-4 semanas | $5,000–8,000 |
| F2 | Caja de batería | Lámina/perfil + compresión de celdas + venteo + aislamiento. **CAD pendiente** (punto 8 de que-falta-para-construir) | 1 lote | — | $3,000–5,500 |

### Estructura — $11,888 a $20,013

| Fase | Item | Especificación de pedido | Cant. | Entrega | Estimado |
|---|---|---|---|---|---|
| F1 | Tubo PTR 25x25x1.5 | 2 tramos de 6 m = 14 kg (9 piezas, 9.0 m netos, +15% de merma) | 2 tramo 6 m | local, días | $452–706 |
| F1 | Tubo PTR 38x38x1.9 | 5 tramos de 6 m = 68 kg (49 piezas, 23.9 m netos, +15% de merma) | 5 tramo 6 m | local, días | $2,176–3,401 |
| F1 | Tubo RED 44.5x3.2 | 2 tramos de 6 m = 42 kg (15 piezas, 9.0 m netos — los arcos requieren ROLADO, +15% de merma) | 2 tramo 6 m | local, días | $1,770–2,739 |
| F1 | Tubo PTR 70×50×4 | 1 tramo de 6 m = 45 kg — brazos tirados traseros (2 × 504 mm) y sobrante para ménsulas | 1 tramo 6 m | local, días | $1,447–2,261 |
| F1 | Tubo RED 25.4×2.1 | 1 tramo de 6 m = 8 kg — horquillas delanteras (~2.1 m netos) | 1 tramo 6 m | local, días | $331–513 |
| F1 | Placa de acero 8 mm | 1 hoja 300×600 mm = 11 kg — placas de torque (4) y dobladores (4), anidados | 1 hoja | local, días | $362–565 |
| F1 | Placa de acero 4.7 mm | 1 hoja 600×1200 mm = 27 kg — cartelas y ménsulas | 1 hoja | local, días | $850–1,328 |
| F1 | Servicio de corte láser | 18 piezas con DXF listo + 10 por dibujar (ver §3). Mandar UN solo pedido: lo que pesa es el arranque, no el metro cortado | 1 servicio | 1-2 semanas | $1,500–3,000 |
| F1 | Rolado de arcos | 2 arcos de tubo RED 44.5×2.1 al radio del plano — con dobladora de mandril, NO con dobladora de rodillos (aplasta la sección) | 2 pza | 1-2 semanas | $1,200–2,500 |
| F1 | Consumibles de soldadura | Alambre MIG ER70S-6 Ø0.9 (5 kg) + gas 75/25 (renta y carga) + discos de corte y desbaste + boquillas de repuesto | 1 lote | local | $1,800–3,000 |

### Rodaje — $35,200 a $63,400

| Fase | Item | Especificación de pedido | Cant. | Entrega | Estimado |
|---|---|---|---|---|---|
| F1 | Rótula cónica ATV | Tipo Honda TRX300/Rancher — LBJ y UBJ por lado. **Verificar el cono contra la mangueta donante antes de comprar** | 4 pza | local/importado | $1,400–2,400 |
| F1 | Buje de poliuretano Ø12 + tubo interno | Pivotes de horquillas delanteras | 8 pza | local | $1,600–2,800 |
| F1 | Kit buje poliuretano Ø16 + manga | Pivote de brazo tirado trasero, base ancha ≥150 mm | 2 kit | local | $800–1,400 |
| F1 | Coilover delantero | Resorte **270 lb/in** · pedir ~**380 mm extendido, carrera ≥96 mm** (ojo a ojo estático 342 mm) · amortiguación ajustable por clicks (ζ 0.5-0.7) · 5,703 N en bache 3g · **especificar Ø del ojo y ancho de montaje** | 2 pza | 2-4 semanas | $4,000–7,000 |
| F1 | Coilover trasero | Resorte **292 lb/in** · pedir ~**540 mm extendido, carrera ≥117 mm** (ojo a ojo estático 482 mm) · ajustable · 6,710 N en bache 3g · **especificar Ø del ojo**. OJO: cambió respecto a versiones previas del BOM (era 351 lb/in) al corregir el anclaje inferior, que estaba fuera del brazo | 2 pza | 2-4 semanas | $4,500–7,500 |
| F1 | Tornillería 10.9 de placa de torque | **8** × M12 10.9 + tuerca autoblocante (4 por rueda, atraviesan las dos placas) y **8** × camisa de acero soldada a través del PTR (sin camisa, el apriete aplasta el tubo) · apretar a 95 N·m | 1 lote | local | $900–1,500 |
| F1 | Disco de freno delantero | Ø220 × 5 mm macizo. **El disco del donante ATV (Ø180-200) NO da el par** — con él ninguna pedalera cumple | 2 pza | local | $1,200–2,200 |
| F1 | Caliper delantero | Área de pistón ≥ **938 mm²** (equivale a un pistón de Ø35 mm) — de compacto o de moto deportiva de 2-4 pistones | 2 pza | deshuesadero/local | $2,000–4,000 |
| F1 | Caliper trasero CON palanca de freno de mano | Área de pistón ≥ **740 mm²** (Ø31 mm equivalente), palanca mecánica integrada. **Verificar patrón de barrenos: 82 mm a radio 110** o se re-corre placa_torque.py. El disco lo trae el QS273 | 2 pza | deshuesadero/local | $2,400–4,200 |
| F1 | Bombas de freno + barra de balance | 2 × bomba Ø14.3 mm (9/16") + barra de balance ajustable + 2 depósitos. Doble circuito: una bomba por eje | 1 kit | 2-3 semanas | $3,500–6,000 |
| F1 | Pedal de freno | Relación **6.0:1** (da 428 N de pie para 1g sin booster) | 1 pza | local | $1,200–2,500 |
| F1 | Pastillas de freno | **Semi-metálicas o sinterizadas, NO las más baratas** — con µ 0.45 el pedal baja de 428 a 381 N. Juego para cada caliper elegido | 4 juego | local | $1,200–2,400 |
| F1 | Líneas de freno | 4 tramos de manguera flexible DOT con malla + línea rígida de acero + niples + líquido DOT4 | 1 lote | local | $1,800–3,000 |
| F1 | Palanca de freno de mano + cables | Palanca con trinquete + cable doble + tensores (2.7 kN de apriete necesarios) | 1 kit | local | $900–1,600 |
| F1 | Cremallera manual de compacto | Donante. **Medir su carrera real y su avance por vuelta antes de comprar** — el cálculo supuso ±75 mm y 45 mm/vuelta. Sin servo | 1 pza | deshuesadero | $1,500–3,000 |
| F1 | Columna de dirección | Con 2 crucetas, **preferentemente colapsable**. Las crucetas en ángulos parecidos y en fase, si no la dirección pulsa al girar | 1 pza | deshuesadero | $1,200–2,500 |
| F1 | Volante + maza | Ø330 mm (con él, 34 N para girar parado en seco) | 1 pza | local | $900–2,000 |
| F1 | Terminales de dirección | 2 × terminal (rótula) + 2 × rótula axial de cremallera + tubo roscado derecha/izquierda para ajustar convergencia sin desmontar | 1 kit | local | $1,200–2,200 |
| F1 | Llantas y rines | 2 × 175/70R13 delanteras + rines 13"; las traseras (175/70R14) vienen con el kit QS273 versión rin de carro | 2 pza | local | $3,000–5,200 |

### Cabina — $14,400 a $27,000

| Fase | Item | Especificación de pedido | Cant. | Entrega | Estimado |
|---|---|---|---|---|---|
| F3 | Butacas | 2 × butaca comercial atornillada (deshuesadero o tipo bucket) | 2 pza | local | $3,000–7,000 |
| F3 | Cinturones | 2 × arnés de 4 puntos con anclajes a la barra del frame | 2 pza | local | $2,400–4,000 |
| F3 | Parabrisas | Laminado plano o semi-curvo tipo buggy + burlete | 1 pza | 2-3 semanas | $4,000–7,000 |
| F3 | Laterales y ventanas | Policarbonato 4 mm, corredizo manual | 1 lote | local | $2,500–4,500 |
| F3 | Tablero | Tablet Android + soporte + fuente 12 V (velocímetro GPS, BMS y controladores por Bluetooth) | 1 pza | local | $2,500–4,500 |

### Carrocería — $31,500 a $55,000

| Fase | Item | Especificación de pedido | Cant. | Entrega | Estimado |
|---|---|---|---|---|---|
| F4 | Espuma EPS en bloque | Para rebanado CNC de los 10 paneles | 1 lote | — | $4,000–7,000 |
| F4 | Servicio de CNC de espuma | Rebanado de los moldes de panel | 1 servicio | 2-4 semanas | $6,000–12,000 |
| F4 | Fibra de vidrio y resina | Tela, resina, gelcoat, desmoldante, consumibles | 1 lote | local | $7,000–12,000 |
| F4 | Fijaciones de panel | Dzus + insertos roscados + separadores (10 paneles) | 1 lote | local | $2,500–4,000 |
| F5 | Wrap satinado | 10 paneles — puede esperar a F5 | 1 servicio | 1-2 semanas | $12,000–20,000 |

### Luces — $7,000 a $12,000

| Fase | Item | Especificación de pedido | Cant. | Entrega | Estimado |
|---|---|---|---|---|---|
| F5 | Iluminación | Barra LED frontal + cejas + aros y línea trasera + intermitentes + cámara trasera con pantalla | 1 lote | 2-3 semanas | $7,000–12,000 |

### Herramientas (una sola vez) — $16,300 a $30,200

| Item | Especificación | Estimado |
|---|---|---|
| Soldadora MIG | Inversor 200 A con gas, 110/220 V | $6,000–11,000 |
| Tronzadora de metal | 355 mm, para cortar los 73 tubos a escuadra | $2,000–3,500 |
| Esmeril angular | 115 mm + discos de corte y laminares | $900–1,600 |
| Taladro + brocas | Taladro de banco chico + juego de brocas para acero | $2,500–4,500 |
| Torquímetro | 1/2", 20-200 N·m — la tornillería 10.9 se aprieta a torque, no a ojo | $900–1,800 |
| Multímetro CAT III | **Obligatorio** para trabajar 96 V: CAT III 600 V mínimo | $800–1,800 |
| Herramienta aislada | Juego de llaves y desarmadores aislados 1000 V para la batería | $1,200–2,500 |
| Equipo de protección | Careta de soldar automática, guantes, mandil, lentes, extintor ABC | $2,000–3,500 |

## 3. Piezas de corte láser

| Archivo | Cant. | Espesor | Para |
|---|---|---|---|
| `cartela-torre-coilover.dxf` ✅ | 4 | 4.7 mm | torres de coilover (2 por lado) |
| `cartela-pivote-brazo.dxf` ✅ | 4 | 4.7 mm | pivotes de brazo trasero |
| `placa-cuna-bateria.dxf` ✅ | 2 | 4.7 mm | laterales de la cuna de batería |
| `placa-torque-motor.dxf` ✅ | 2 | 8.0 mm | placa de torque exterior, con ménsula de caliper |
| `placa-torque-refuerzo.dxf` ✅ | 2 | 8.0 mm | placa de torque interior |
| `placa-torque-doblador.dxf` ✅ | 4 | 8.0 mm | doblador del cubo del eje (se suelda) |
| ménsula de pivote superior delantero ❌ | 4 | 4.7 mm | baja el eje 63 mm bajo el tubo superior — DXF pendiente |
| ménsula de cremallera al mamparo ❌ | 2 | 6.0 mm | posición nueva x=370 / z=±504, barrenos ovalados — DXF pendiente |
| ménsula de caliper delantero ❌ | 2 | 8.0 mm | adapta el caliper elegido a la mangueta ATV — DXF pendiente |
| adaptador de disco Ø220 a maza ATV ❌ | 2 | 8.0 mm | el disco del donante no da el par necesario — DXF pendiente |

**18 piezas ya tienen su DXF listo para el cortador; 10 faltan por dibujar** — todas son ménsulas simples, pero conviene juntarlas y mandar un solo pedido de corte porque el costo de arranque es lo que pesa.

**Decisión abierta:** los 5 nodos generativos (`cad/*.stl`) — impresos/fundidos o resueltos con cartelas de lámina. No está cerrada y no bloquea las compras de arriba.

## 4. Lista para el deshuesadero

Llevar esta lista y un calibrador. Lo que hay que medir **antes de pagar** está en negritas:

- **Mangueta, maza y rótulas de ATV 300** — verificar el cono de las rótulas y **que la mangueta quepa en rin 13"** (los ATV usan 12")
- **Cremallera manual de compacto** — **medir carrera total y avance por vuelta** (el cálculo supuso ±75 mm y 45 mm/vuelta)
- **Columna de dirección** con 2 crucetas, de preferencia colapsable
- **Calipers**: delanteros de área ≥938 mm²; traseros **con palanca de freno de mano** y ≥740 mm², **con patrón de barrenos de 82 mm**
- Butacas, bombas de freno, rines 13"

## 5. Confirmar por escrito ANTES de pagar

Todo lo de abajo está parametrizado en los scripts: si un dato cambia se ajusta la constante y se re-corre. Pero si se descubre **después** de cortar acero, se vuelve a cortar acero.

| Qué | A quién | Por qué importa |
|---|---|---|
| Versión de rin de carro 14" del QS273 | QS Motor | En rin 13" el motor no cabe — es la base de toda la suspensión trasera |
| Ø del eje y entrecaras de los planos | QS Motor | Definen el cubo de la placa de torque y su doblador |
| **Largo del eje libre del lado interior (≥84 mm)** | QS Motor | **El más crítico.** Si es menor, el sándwich de placas no cabe y hay que rediseñar. Incluye los 30 mm que ocupan el disco y el caliper entre la cara del motor y la placa |
| Ancho del cuerpo del motor (supuesto 130 mm) | QS Motor | Cambia el voladizo y todo el reparto de carga entre las dos placas |
| Ø del disco de freno y patrón del caliper | QS Motor | Fija la posición de las orejas ya cortadas en la placa de torque |
| Corriente real de descarga del BMS | proveedor | Menos de 250 A continuos capa los motores |
| Celdas del mismo lote | proveedor | Celdas mezcladas se desbalancean y el pack vale lo que su peor celda |

## 6. Totales y contraste con el presupuesto original

| Sistema | BOM (estimado) | Presupuesto doc maestro | |
|---|---|---|---|
| Estructura | $11,888–20,013 | $7,200–11,000 | **se pasa** |
| Rodaje | $35,200–63,400 | $20,300–33,500 | **se pasa** |
| Propulsión | $49,700–73,200 | $38,700–53,700 | dentro |
| Batería | $40,000–58,500 | $35,000–49,000 | dentro |
| Carrocería | $31,500–55,000 | $21,000–36,000 | dentro |
| Cabina | $14,400–27,000 | $14,400–24,100 | dentro |
| Luces | $7,000–12,000 | $7,000–12,000 | dentro |
| **Total del carro** | **$189,700–309,100** | $143,600–219,300 | |
| Herramientas | $16,300–30,200 | $10,000–15,000 | |

El rango es ancho a propósito: el **mínimo** es comprando bien y usando deshuesadero donde se puede; el **máximo** es todo nuevo a precio de mostrador. La realidad cae en medio y depende sobre todo de la suerte en el deshuesadero.

### De dónde viene el sobrecosto

El BOM detallado sale **$189,700–309,100** contra los $143,600–219,300 del doc maestro. Solo se pasan dos sistemas, y hay una razón concreta en cada uno:

**Rodaje** es el grande. Desglosado por entregable:

| Grupo | Estimado | |
|---|---|---|
| Frenos | $14,200–25,900 | |
| Suspensión y placa de torque | $13,200–22,600 | |
| Dirección | $4,800–9,700 | |
| Llantas y rines | $3,000–5,200 | |

Los **frenos solos se comen casi la mitad del rodaje**, y es consecuencia directa de un hallazgo del cálculo: el freno del donante ATV no alcanza para 690 kg, así que hay que comprar discos de Ø220 y calipers de mayor área en vez de reusar los del donante. El doc maestro presupuestó dando por hecho que el freno venía con la mangueta.

**Estructura** se pasa por los servicios, no por el acero: el acero puro son ~215 kg ($6,888–10,763), y lo que empuja son el corte láser, el rolado de los arcos y los consumibles de soldadura — que el presupuesto original no tenía desglosados.

> Ojo con ese número: **215 kg es lo que se COMPRA**, no lo que pesa el carro. El frame soldado son 90.6 kg (`analisis_chasis.py`); la diferencia son los tramos comerciales de 6 m que sobran, la merma de corte y las placas. El sobrante sirve para el jig de soldadura y las ménsulas, así que no se tira.

**Qué hacer con esto.** No es motivo de alarma: el carro sigue siendo un proyecto de rango medio y **se construye por fases**, así que el desembolso se reparte. Las palancas reales para bajarlo, en orden de efecto:

1. **Deshuesadero agresivo en frenos y rodaje** — calipers, bombas, columna, butacas y rines usados mueven la aguja más que cualquier otra cosa.
2. **Wrap hasta el final** (F5): son $12-20 mil que el carro no necesita para andar.
3. **Herramientas prestadas o rentadas** donde se pueda — pero **el multímetro CAT III y la herramienta aislada se compran, no se piden prestados**.
4. Lo que **nunca** se recorta (doc maestro §9): BMS, frenos, coilovers, cinturones, fusible.

### Desembolso por fase

| Fase | Qué es | Estimado |
|---|---|---|
| F0 | pedidos largos (motores y celdas) — **primero** | $70,700–98,700 |
| F1 | chasis rodante: acero, suspensión, frenos, dirección | $47,100–83,400 |
| F2 | tren eléctrico | $19,000–33,000 |
| F3 | pruebas y cabina | $14,400–27,000 |
| F4 | carrocería | $19,500–35,000 |
| F5 | acabado | $19,000–32,000 |

El carro **rueda, frena y dirige al terminar F1**, y **anda solo al terminar F2**. Todo lo de F4 y F5 es apariencia: se puede estirar en el tiempo sin que el carro deje de servir.

## 7. Lo que este BOM todavía NO puede cotizar

Honestidad sobre los huecos — cada uno es un entregable de ingeniería pendiente:

- **Cableado HV y 12 V**: los calibres salen del diagrama unifilar, que no está hecho. Es lo único que bloquea cerrar F2.
- **Caja de batería**: falta el CAD del arreglo 30S con compresión y venteo.
- **Nodos del chasis**: impresos/fundidos vs cartelas — decisión abierta.
- **Carrocería**: los volúmenes de espuma y fibra dependen del CAD final de superficie, que es de F4.

Ninguno de los cuatro bloquea los pedidos largos, que es lo que urge.
