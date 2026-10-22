# Puertas de gaviota: construcción, herraje y armado

**Fecha:** 2026-10-12 (revisado tras dos auditorías cruzadas) · Diseño: `docs/superpowers/specs/2026-10-12-cabina-y-puertas-design.md`
· Números de `calculos/puertas.py` y `calculos/buck_piloto.py` (se regeneran con `python calculos/puertas.py`).

> **Actualización 2026-10-21 — seguridad de las puertas** (detalle y cálculos en `docs/seguridad-puertas.md`): viga de impacto lateral de tubo redondo
> RED 50.8×2.1 (colapsa a 7.6 kN, pide 4.5 kN), cierres con segunda posición, **pasadores de bisagra de extracción rápida** (salida de emergencia en volcadura y
> desmontaje en 1 minuto), manijas rojas de emergencia, varilla de apoyo contra falla del amortiguador y sensor de puerta que inhibe el par. La masa de diseño de la
> puerta pasa de 12 a **13.5 kg** (amortiguador de gas de 500 N, esfuerzo de manija +88 N al empezar a abrir; LC7 del chasis queda en FS 6.8). Las cifras de arriba de
> LC7 (1,300 N, etc.) son de la versión de 12 kg: se regeneran con `python calculos/puertas.py`.

Ejes: x hacia **atrás**, y arriba, z lateral (**z>0 = izquierda, lado del piloto**). Todo en metros. El lado derecho es el
espejo en z.

## 1. Qué es cada puerta

Piel de **fibra de vidrio sándwich** (2 capas de ~300 g/m² con 5 mm de espuma de celda cerrada) sobre un **esqueleto de tubo
redondo Ø16 × 1.2 mm** (anillo perimetral + un travesaño, ~5.5 m por puerta), con **placas de acero de 3 mm** sólo donde
van bisagras, cierres y amortiguador, y **cristal fijo de policarbonato de 3 mm**. Sin PTR (decisión del usuario).
Objetivo **9–10 kg por puerta**; **todo se calcula con 12 kg** (margen de 20%).

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
| Bisagra 1 (perno) | (1.55, 1.012, 0.15) | eje **inclinado** siguiendo el techo: 53 mm bajo la piel exterior |
| Bisagra 2 (perno) | (1.85, 1.049, 0.15) | 60 mm bajo la piel exterior; flanquean el centro de masa (x=1.70) |
| Base de bisagra en el chasis | riel del espinazo, y≈0.98–0.99 | ménsula de placa de 3 mm que sube 3–6 cm hasta el perno |
| Amortiguador, extremo chasis | (1.45, 0.949, 0.30) | travesaño de la cabecera |
| Amortiguador, extremo puerta | (1.55, 0.90, 0.50) | placa en el esqueleto; **verificado libre del pilar A** (≥ 20 mm) de 0° a 65° |
| Cierre techo delantero | (1.45, 0.94, 0.40) | esquina de la cabecera (nodo `hdr`) |
| Cierre estribo delantero | (1.40, 0.16, 0.59) | sobre el tubo del estribo |
| Cierre estribo trasero | (1.90, 0.16, 0.59) | sobre el tubo del estribo |
| Cierre trasero | (2.02, 0.660, 0.506) | pierna del arco (nodo `mh_belt`) |

> El eje de giro es el de las piezas de la puerta, pero **inclinado** (de y=1.00 a 1.07 entre x=1.45 y 2.02) porque el techo de Tripo
> baja hacia adelante. Con un eje horizontal a y=1.06 el perno de la bisagra delantera asomaba 5 mm sobre la piel (hallazgo de la
> auditoría).

**Amortiguador de gas: 500 N de catálogo**, carrera ≥ 140 mm, uno por puerta. Sostener la puerta de 12 kg a 65° pide 392 N; se
elige el siguiente de catálogo con 10% de margen. Esfuerzo en la manija (a 0.8 m del eje): **78 N al empezar a abrir** (como
levantar 8 kg), 21 N a 30°, y **a partir de 45° el amortiguador la lleva solo**; a 65° la ayuda con 21 N.

**Puerta abierta a 65°:** el punto más bajo del ala exterior queda a **1.26 m del suelo** (z≈0.88). **Una persona de 1.75 m que
se para junto al estribo tiene que agacharse** para pasar bajo la puerta; no es un borde que se pueda caminar por debajo.
(Una versión anterior de este documento decía 1.41 m: era un punto del borde, no el más bajo.)

## 3. Cargas que recibe el chasis

**LC7: puertas abiertas a 65°**, en equilibrio: peso de 12 kg × 3 g (bache o portazo) + 400 N de viento lateral, con el amortiguador
extendido a tope actuando como biela rígida:

| Punto | Fuerza | Momento |
|---|---|---|
| Bisagra 1 (cada lado) | 1,300 N vertical + 780 N lateral | 31 N·m (excentricidad de la ménsula) |
| Bisagra 2 (cada lado) | 380 N vertical + 230 N lateral | 12 N·m |
| Ancla del amortiguador | 2,030 N hacia abajo + 610 N hacia adentro | — |

FS mínimo **7.0**, en el travesaño central del espinazo (`sp_fL–sp_fR`). Es un caso de abuso: la puerta de 10–12 kg a 3 g con el
amortiguador a tope; una persona colgada de la puerta abierta sería mucho peor y **no está modelada**.

**LC8: choque frontal a 10 g con arnés** (5.3 kN por asiento en la barra de cinturones, repartido por inercia): FS mínimo **2.18**
en la pata del arco (`mh_belt–mh_hi`). Para que cumpla, las patas del arco y la barra de cinturones son **RED 57.2×3.2** (la
versión anterior las tenía en 2.1 mm de pared y el arnés las llevaba a FS 1.1).

## 4. Secuencia de armado: "encaje sobre el carro"

Un chasis soldado se tuerce unos milímetros, así que las puertas **no se fabrican contra el plano sino contra el carro
real**:

1. Soldar el chasis **por módulos** y unirlos (no sale de una sola plantilla plana): piso (35 tubos a y≤0.2), plano del arco
   principal (x=2.02), planos de la caja delantera (`fb`, `fx`) y el resto en 3D (nariz, cowl, cabecera, cola). Liberar tensiones
   (golpes de martillo en las soldaduras largas antes de enfriar).
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
| Borde inferior de la cabecera sobre el ojo (1.75 m, nominal; cabecera Ø57.2) | ≥ +12° | **+12.9°** | ✓ |
| Coronilla bajo el límite útil del techo | ≥ 40 mm | **+67 mm** | ✓ |
| Nuca al arco (nominal) | ≥ 80 mm | **+97 mm** | ✓ |
| Espalda a la barra de cinturones (nominal) | ≥ 0 | +37 mm | ✓ |
| LC1 bache 3g / LC3 frenada / LC4 curva | FS ≥ 2 | 3.16 / 2.66 / 2.90 | ✓ |
| LC5 volcadura / LC5c cabecera / LC6 torsión 4,500 N·m | ≥ 1.65 / 1.3 / 2.0 | 1.72 / 1.77 / 2.13 | ✓ |
| LC7 puertas abiertas / LC8 arnés 10 g | ≥ 2.0 / 1.5 | 7.0 / 2.18 | ✓ |
| Rigidez torsional | ≥ 8,000 N·m/° | 8,702 | ✓ |
| Hueco de la puerta, holguras de suspensión, piel de Tripo | libre | libre / libre / 0 tubos asoman | ✓ |
| Lista de corte | sin cortes negativos ni < 40 mm | sin negativos; el más corto 53 mm | ✓ |
| Nodos | ≤ 5 tubos | máximo 5 | ✓ |

**Recorrido útil del asiento** (pedales fijos, bola del pie a x≈0.52):

| Conductor | Cadera x | Techo | Nuca–arco | Espalda–barra | Cabecera |
|---|---|---|---|---|---|
| 1.60 m | 1.43 | +118 mm | +195 mm | +135 mm | +27° |
| **1.75 m** | **1.50** | **+67 mm** | **+97 mm** | **+37 mm** | **+13°** |
| 1.80 m | 1.52 | +48 mm | +67 mm | ≈0 | +9° |
| 1.85 m | 1.55 | +30 mm | +31 mm | **−29 mm** | +6° |

El diseño es para **1.75 m**. Hasta **~1.78 m** cabe; a 1.80 m la espalda roza la barra de cinturones, y a 1.85 m la toca.
Rieles: cadera x 1.43–1.52.

## 6. Qué cambió respecto al diseño anterior (honesto)

| | Anterior | Ahora |
|---|---|---|
| Masa del chasis | 94.7 kg | **90.1 kg** (−5%) |
| Rigidez torsional | 14,058 | **8,702 (−38%)** |
| Bache / frenada / curva | 2.05 / 3.13 / 2.83 | 3.16 / 2.66 / 2.90 |
| Volcadura / cabecera | 1.65 / 1.31 | 1.72 / 1.77 |
| Torsión 4,500 N·m | 2.33 | 2.13 |
| Puertas abiertas (LC7) / arnés (LC8) | no existían | 7.0 / 2.18 |
| Hueco de puerta | **bloqueado** por una diagonal | libre |
| Asiento | sin travesaño (el peso iba en el estribo) | sobre rieles con 2 travesaños |

Se pierde **38% de rigidez torsional** y algo de frenada y torsión a cambio de la puerta libre, el piloto real y las puertas. El
caso de volcadura FIA (7.5 W + 5.5 W) da FS 0.32: **no es una jaula homologable**, y ya estaba declarado así. La mejora de bache
no es comparable: antes los 90 kg del piloto se concentraban en un solo nodo.

## 7. Abierto (no resuelto)

- **Cremallera de dirección y poste `fb`:** la cremallera termina en (0.36, 0.34, ±0.516), a 11 mm del eje del poste `fb` (x=0.35,
  z=0.5), o sea dentro del tubo. Viene del diseño de dirección anterior; hay que revisarlo.
- **Columna de dirección:** una columna recta de la cremallera a un volante en x≈1.2 cruza el travesaño `fx_hi` (y≈0.49). Pasar
  por encima exige un volante muy alto o una junta cardán.
- **Pedalera:** la bola del pie queda en x≈0.52. No hay tubos del piso entre x=0.35 y 1.10 (0.75 m): hace falta definir el soporte
  de la caja de pedales y dónde va el cilindro de freno antes de cortar.
- **Cargas de rueda en los anclajes de suspensión:** el FEM las toma como apoyos, no las aplica. Los tubos de esa zona están en su
  piso (PTR 38×1.9) por esa razón.
- **Una persona colgada de la puerta, o el portazo con el cierre:** no modelados.
- **Visibilidad:** la cabecera (+12.9° a 1.75 m) mejora los +3° anteriores pero no llega a los +15° de un coche normal. El pilar A
  y la cabecera (Ø57) se ven de 6° a 9° de ancho desde los ojos; acotar el diámetro a Ø51 compraba ~1° y costaba la volcadura,
  así que se descartó.
- **Corte láser pendiente:** 4 placas de bisagra, 6 de cierre y 4 de amortiguador (3 mm). Hay que dibujar los DXF.
- **Cinturones con asiento deslizable:** arnés de longitud ajustable, anclajes de hombro en la barra `mh_belt` (y=0.66), libre de
  diagonales.
- **Soldadura:** las ménsulas de bisagra son lo único que carga la puerta; practicar el tubo RED 57.2×3.2 antes. Pared mínima 1.9 mm
  en todo el chasis (la de 1.5 se perfora con MIG de principiante); hacer cupones y puntear antes de soldar.
