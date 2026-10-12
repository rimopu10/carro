# Puertas de gaviota: construcción, herraje y armado

**Fecha:** 2026-10-12 · Diseño: `docs/superpowers/specs/2026-10-12-cabina-y-puertas-design.md` · Números de
`calculos/puertas.py` y `calculos/buck_piloto.py` (se regeneran con `python calculos/puertas.py`).

Ejes: x hacia **atrás**, y arriba, z lateral (**z>0 = izquierda, lado del piloto**). Todo en metros. El lado derecho es el
espejo en z.

## 1. Qué es cada puerta

Piel de **fibra de vidrio sándwich** (2 capas de ~300 g/m² con 5 mm de espuma de celda cerrada) sobre un **esqueleto de tubo
redondo Ø16 × 1.2 mm** (anillo perimetral + un travesaño, ~5.5 m por puerta), con **placas de acero de 3 mm** sólo donde
van bisagras, cierres y amortiguador, y **cristal fijo de policarbonato de 3 mm**. Sin PTR (decisión del usuario).
Masa estimada **9–10 kg por puerta**.

La rigidez sale de la piel cerrada (viga en caja); el esqueleto reparte las cargas del herraje y mantiene la forma. Lo que hace
que una puerta se sienta sólida es el herraje y el cierre, no el grosor del tubo:

- **3 puntos de cierre** por puerta, cada uno con perno ajustable, y **topes de goma** en las esquinas: sin juego no hay vibración.
- **Sello tipo D** sobre la brida del vano, con holgura puerta–carrocería de **5 ± 1 mm**.
- **Bisagras ajustables en 3 ejes** (agujeros ranurados): el chasis soldado se deforma 2–3 mm.

> Las puertas que se ven en `carro-tripo-chasis-3d.html` son las piezas del **juguete 1:20** a escala real (piel sin panel
> interior ni esqueleto). Sirven para ver contorno, eje y apertura; **no son el diseño constructivo** de la puerta.

## 2. Herraje y coordenadas (lado izquierdo, puerta cerrada)

| Pieza | Coordenadas (x, y, z) | Notas |
|---|---|---|
| Bisagra 1 (perno) | (1.55, 1.06, 0.15) | eje horizontal a y=1.06, dentro de la piel del techo |
| Bisagra 2 (perno) | (1.85, 1.06, 0.15) | flanquean el centro de masa de la puerta (x=1.70) |
| Base de bisagra en el chasis | riel del espinazo, y≈0.98–0.99 | ménsula de placa de 3 mm que sube 7–8 cm hasta el perno |
| Amortiguador, extremo chasis | (1.45, 0.949, 0.30) | travesaño de la cabecera |
| Amortiguador, extremo puerta | (1.45, 0.75, 0.75) | placa en el esqueleto, borde delantero |
| Cierre techo delantero | (1.45, 0.94, 0.40) | esquina de la cabecera (nodo `hdr`) |
| Cierre estribo delantero | (1.40, 0.16, 0.59) | sobre el tubo del estribo |
| Cierre estribo trasero | (1.90, 0.16, 0.59) | sobre el tubo del estribo |
| Cierre trasero | (2.02, 0.742, 0.492) | pierna del arco principal (`mh_belt`) |

**Amortiguador de gas: 350 N de catálogo**, carrera ≥ 158 mm. Sostener la puerta a 65° pide 284 N; 350 N deja 23% de margen.
Esfuerzo en la manija (que está a 0.8 m del eje): **50 N al empezar a abrir** (como levantar 5 kg), 15 N a 30°, y **a partir de 45°
el amortiguador la lleva solo**. A 65° la puerta queda sostenida con 15 N de ayuda.

**Puerta abierta a 65°:** el borde inferior queda en (1.70, **1.41 m**, z=1.17) → **1.41 m del suelo y ~28 cm fuera de la
carrocería** (que mide 0.89 de semiancho). Una persona pasa sin agacharse bajo la puerta.

## 3. Lo que el chasis recibe (caso de carga LC7)

Puertas abiertas a 65°, con 3 g sobre el peso y 400 N de viento lateral, y el amortiguador a su fuerza nominal:

| Punto | Fuerza | Momento |
|---|---|---|
| Bisagra 1 (cada lado) | 304 N lateral | 26 N·m (excentricidad de la ménsula) |
| Bisagra 2 (cada lado) | 304 N lateral | 19 N·m |
| Ancla del amortiguador | 282 N hacia abajo + 207 N hacia adentro | — |

Resultado del FEM: **FS mínimo 28.6** en el riel del espinazo. Las puertas casi no castigan al chasis; el cuidado está en
soldar bien las ménsulas, no en reforzar el riel.

## 4. Secuencia de armado: "encaje sobre el carro"

Un chasis soldado se tuerce unos milímetros, así que las puertas **no se fabrican contra el plano sino contra el carro
real**:

1. Soldar el chasis en la plantilla y liberar tensiones (golpes de martillo en las soldaduras largas antes de enfriar).
2. Pegar y asentar la carrocería. Marcar el contorno real del vano (estribo, pilar A, arco, espinazo).
3. Pegar la **brida del vano** continua y el **sello tipo D**.
4. Soldar las **ménsulas de bisagra** al riel y los **soportes de cierre** (pernos de cierre ajustables) y del amortiguador.
   Usar una plantilla de cartón/MDF del vano para fijar bisagra–perno–cierre antes de soldar.
5. **Modelar la puerta contra el vano real**: colocar el esqueleto en su sitio con calzas de 5 mm, laminar la piel sobre el
   carro (cera desmoldante sobre la carrocería) y sacar la puerta ya con la forma exacta.
6. Montar bisagras y amortiguador. Ajustar las 3 direcciones hasta la holgura de **5 ± 1 mm** en todo el perímetro.
7. Ajustar los 3 pernos de cierre hasta que cierre con golpe seco y sin juego; poner los topes de goma.
8. Comprobar con la puerta abierta a 65°: que la sostenga el amortiguador y que no roce la carrocería.

## 5. Criterios de aceptación (spec §6), con lo medido

| Criterio | Meta | Medido | |
|---|---|---|---|
| Borde inferior de la cabecera sobre el ojo (1.75 m, nominal) | ≥ +12° | **+13.4°** | ✓ |
| Coronilla bajo el límite útil del techo | ≥ 40 mm | **+67 mm** | ✓ |
| Nuca al arco (nominal) | ≥ 80 mm | **+97 mm** | ✓ |
| Espalda a la barra de cinturones (nominal) | ≥ 0 | +37 mm | ✓ |
| LC1 bache 3g / LC3 frenada / LC4 curva | FS ≥ 2 | 3.03 / 2.60 / 2.74 | ✓ |
| LC5 volcadura / LC5c cabecera / LC6 torsión 4,500 N·m | ≥ 1.5 / 1.3 / 2.0 | 1.52 / 1.72 / 2.09 | ✓ |
| LC7 puertas abiertas | FS ≥ 2 | 28.6 | ✓ |
| Rigidez torsional | ≥ 8,000 N·m/° | 8,706 | ✓ |
| Hueco de la puerta, holguras de suspensión, piel de Tripo | libre | libre / libre / 0 tubos asoman | ✓ |
| Lista de corte | sin cortes negativos ni < 40 mm | sin negativos; el más corto 56 mm | ✓ |
| Nodos | ≤ 5 tubos | máximo 5 | ✓ |

**Recorrido útil del asiento** (con pedales fijos, la bola del pie a x≈0.52):

| Conductor | Cadera x | Techo | Nuca–arco | Espalda–barra | Cabecera |
|---|---|---|---|---|---|
| 1.60 m | 1.43 | +118 mm | +195 mm | +135 mm | +28° |
| **1.75 m** | **1.50** | **+67 mm** | **+97 mm** | **+37 mm** | **+13°** |
| 1.80 m | 1.52 | +48 mm | +67 mm | +7 mm | +10° |
| 1.85 m | 1.55 | +30 mm | +31 mm | **−29 mm** | +7° |

Hasta **1.80 m** cabe; a 1.85 m la espalda toca la barra de cinturones. Rieles: **cadera x 1.43–1.52 (90 mm)**.

## 6. Abierto

- **Corte láser pendiente:** 4 placas de bisagra, 6 de cierre y 4 de amortiguador (3 mm). Hay que dibujar los DXF.
- **Pedales** en x≈0.52 (bola del pie), dentro de la caja delantera: verificar contra cremallera, travesaños fx/fb y el
  cilindro de freno antes de cortar.
- **Cinturones con asiento deslizable:** arnés de longitud ajustable, con los anclajes de hombro en la barra `mh_belt`
  (y=0.66), que quedó libre de diagonales (volumen prohibido del plano del arco).
- **Visibilidad:** la cabecera (+13° a 1.75 m) es mejor que antes (+3°) pero no llega a los +15° de un coche normal; el techo de
  Tripo no deja más. Con 1.80 m baja a +10°.
- **Soldadura de las ménsulas de bisagra:** son lo único que carga la puerta; practicar el tubo RED de 50.8×2.1 antes.
