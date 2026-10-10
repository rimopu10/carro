# Carrocería v3 — modelo 3D a escala por superficie de subdivisión

**2026-09-05.** Sustituye la reconstrucción por IA local (`cad/gem-mv3.glb`, Hunyuan3D,
licencia no comercial, volumen blando sin aristas ni cristal). Ahora la carrocería sale
de código: una jaula de control medida de las cuatro vistas de la lámina, subdividida
con creases en las líneas de carácter, sobre los puntos duros reales del chasis.

## Qué hay

| Archivo | Qué es |
|---|---|
| `carro-diseno-3d.html` | Visor interactivo autónomo (doble clic; usa three.js del CDN de jsdelivr, necesita internet la primera vez). Vistas de la lámina, cristal, luces, interior, pilotos, malla. |
| `cad/carro-v3.glb` | Modelo completo con materiales: carrocería, cristal, luces, parrilla, splitter, difusor, espejos, 4 ruedas con rines de 10 rayos, discos y calipers, butacas, tablero, volante, 2 pilotos de 1.75 m. 101 piezas, 143 k triángulos, ejes del proyecto (X largo, Y alto, Z lateral). |
| `cad/carro-v3-carroceria-mm.stl` | Solo la piel, en mm, sólido con pozos de rueda, 79 k triángulos. Le quedan 10 aristas no manifold en la punta de la cola (donde los booleanos comen las caras diminutas de la tapa); cualquier slicer lo repara. Para impresión 3D a escala o CNC de espuma. |
| `cad/carro-v3.blend` | Escena completa en Blender 4.5 con cámaras y luces de estudio. |
| `cad/carro-v3-jaula.json` | La jaula de control (660 vértices, 660 caras, 394 creases). Es el archivo fuente editable de la forma. |
| `render/salida/v3/` | Renders Cycles: frontal, trasera, lateral, cenital (fondo transparente), dos tres cuartos; `comparacion.png` y `siluetas.png` contra la referencia. |

## Cómo se regenera

```
python calculos/curvas_ref.py          # mide las vistas de referencia -> ref/curvas-referencia.json
python calculos/carro3d_jaula.py       # jaula de control -> cad/carro-v3-jaula.json (+ verificación)
"C:\Users\ILV PC\AppData\Local\blender-portable\blender-4.5.10-windows-x64\blender.exe" ^
    --background --python render/carro_v3.py -- --muestras 128      # ~4 min con RTX 4060 Ti
python render/comparar_v3.py           # IoU por vista contra la referencia
python calculos/visor_carro_v3.py      # carro-diseno-3d.html
```

`--rapido` (EEVEE, subdivisión 2) tarda ~40 s y sirve para iterar la forma;
`--sin-render` y `--sin-exportar` recortan más.

## Método

1. **Curvas medidas, no tecleadas** (`curvas_ref.py`). De `ref/gemini/ia-lateral.png`
   sale techo(x) y piso(x); de `ia-cenital.png` el semiancho(x), la huella del canopy
   y la de la luneta; de `ia-frontal.png` e `ia-trasera.png` el contorno superior y(z)
   y la altura de la barra de luz. Las vistas NO son consistentes entre sí (cada una
   tiene su propia escala y sus ruedas en otro sitio), así que cada una se lleva al
   paquete real por sus propias marcas: en x, tramo a tramo entre nariz, eje delantero,
   eje trasero y cola —la batalla de 2.130 no se toca—; en alto al 1.06 del paquete; en
   ancho al semiancho de 0.89.
2. **Jaula de 12 anillos por estación** (`carro3d_jaula.py`): piso, canto del piso,
   quilla, tope del faldón, flanco, hombro (el ancho máximo, que es la planta medida),
   arista de salpicadera, repisa, base del cristal, cristal medio, borde del techo y
   techo centro. 30 estaciones de nariz a cola. Los anillos 8-10 son el invernadero
   donde hay cristal y se tienden sobre el cofre / la cubierta donde no lo hay, así
   que es una sola jaula sin costuras. Las tapas de nariz y cola son "escaleras" de
   cuadriláteros, no n-gons (ver "lo que costó").
3. **Crease en las líneas de carácter**: quilla 0.8, faldón 0.55, hombro 0.7 en las
   salpicaderas, arista de salpicadera 0.95, base del cristal 0.95, borde del techo
   0.3. Eso es lo que hace que la luz se quiebre donde debe.
4. **Blender** (`render/carro_v3.py`): Catmull-Clark nivel 3 → materiales por región
   (anillo y estación viajan como atributos de cara, así que los bordes del cristal
   quedan alineados a la jaula) → booleanos exactos: pozos de rueda, boca de la
   parrilla, branquias laterales → luces proyectadas sobre la piel (Shrinkwrap) con
   los polígonos de la lámina (`cad/firma-luces.json`) → juntas de puerta como cinta
   de 6 mm sobre la piel → detalle duro y contexto de escala.
5. **Verificación**: `carro3d_jaula.verificar()` mide la piel contra la envolvente del
   chasis; `comparar_v3.py` mide la silueta del render contra la referencia.

## Números

**Cotas:** 3.380 × 1.754 (sin espejos; 1.78 nominal) × 1.061 m · batalla 2.130 ·
voladizos 684 / 566 mm · piso de la piel a 125 mm.

**Silueta contra la referencia (IoU, 1.00 = idéntica):**

| Vista | IoU | Por qué no es 1 |
|---|---|---|
| cenital | 0.967 | — |
| trasera | 0.867 | la referencia lleva llantas de ~255 mm que llenan el ancho abajo; las nuestras son 175/70 |
| frontal | 0.860 | ídem, y el labio de la referencia baja a ~50 mm del suelo; el nuestro a 125 |
| lateral | 0.850 | el parabrisas sube por el chasis (abajo) y las llantas son más chicas que las de la lámina |

(2026-10-09: frontal y trasera bajan 0.01 porque los espejos nuevos son más bajos y
chicos que la paleta anterior; no es la carrocería.)

**Conflicto lámina vs chasis (no se esconde):** el techo medido en la lámina queda por
debajo del nodo `dash_hi` (0.95, 0.72) y del pilar A hacia `hdr` (1.45, 0.95). Gana
el chasis, validado por FEM con la gaviota:

| x | lámina | mínimo chasis | modelo |
|---|---|---|---|
| 0.92 | 0.711 | 0.766 | 0.796 (+85 mm) |
| 1.04 | 0.745 | 0.824 | 0.852 (+108 mm) |
| 1.18 | 0.829 | 0.890 | 0.915 (+86 mm) |
| 1.46 | 0.972 | 1.004 | 1.010 (+39 mm) |

Es el mismo conflicto reportado el 2026-08-18; con la línea medida de la lámina crece
de 101 a 108 mm porque ahora el techo va donde la lámina lo pide en vez de a ojo.

## Pulido del 2026-10-09

Revisado contra la lámina en acercamientos (`--vistas detalle_frente,detalle_cola`):

| Qué | Antes | Ahora |
|---|---|---|
| Pintura | clearcoat 1.0 tipo espejo: cada ondita de la piel se leía como defecto | satinada (el doc maestro pide wrap satinado) |
| Luces delanteras | calcas envueltas por proyección frontal, de 35-55 mm y con la orilla mordida en las esquinas de la nariz | **surcos de 22 mm** barridos sobre la piel con la normal de la piel (`ranura_sobre_piel`); ejes trazados sobre la lámina |
| Cola | todo lo que quedaba bajo la barra pintado de negro por altura (escalones de malla); barra sin tramo central | **difusor como bolsillo en V** real que deja en color carrocería las caderas y una V alrededor del triángulo; barra de tres tramos con gancho; triángulo como bolsillo con centro de malla |
| Cofre | burbuja: valle de 50 mm entre salpicaderas | valle de 70 mm y crease 0.45 en el anillo 9: dos lomos y una flecha central |
| Faldón | banda negra de 170 mm entre ruedas | color carrocería; el negro queda en el canto del piso |
| Splitter | contorno dentado por rayos, 13 mm bajo el piso | suavizado y con la cara inferior en el plano del piso |
| Rines / espejos | cromo / paleta redonda en poste | grafito satinado / gota baja sobre brazo corto |

`bolsillo()` ahora hunde el fondo a lo largo del eje de proyección, no por la normal:
con la normal el contorno se corría de lado en las zonas curvas y la orilla salía
ondulada. `verificar_piel_v3.py` da los mismos 11 conflictos del arco/cabecera (el
pendiente #0) y nada nuevo por el cofre más hondo.

## Maqueta impresa (2026-10-09)

`render/carro_v3.py --maqueta 16,12` + `calculos/maqueta.py` → `impresion/` (ver
`impresion/LEEME.md`). 1:16 en una pieza de 211 mm para la Ender 3 V3 SE; 1:12 en dos
piezas cortadas sobre la junta trasera de la puerta con pernos de filamento. Ruedas,
arandelas y una regla de tolerancias para elegir el agujero del cubo. Los booleanos de
la pieza imprimible van en manifold3d: el solver exacto de Blender, aplicado otra vez
sobre la piel ya cortada, dejaba aristas abiertas y una unión le BAJABA el volumen.

## Auditoría numérica (2026-09-05, `calculos/verificar_piel_v3.py`)

La verificación de la jaula sólo comparaba la altura del centro del techo contra la
envolvente del chasis. Medido el STL real contra cada tubo (aire = distancia del eje a
la piel menos el radio; conflicto si es menor que los 12 mm del sándwich, aviso si es
menor que 20), salieron tres cosas que esa comprobación no veía. Correr
`python calculos/verificar_piel_v3.py` después de tocar la jaula o el chasis.

**1. El arco principal y la cabecera no caben bajo la burbuja del techo** (11 tubos en
conflicto, todos en esas dos esquinas). El techo medido de la lámina es una cúpula: en
x=2.02 baja de 1.060 (centro) a 0.996 en |z|=0.44, que es donde están las esquinas
`mh_hi` (y=1.01, RED 57.2): el eje del tubo queda 11 mm FUERA de la piel, o sea el tubo
asoma **40 mm**. Con 20 mm de aire la piel tendría que estar en 1.059 ahí (faltan 63).
La cabecera `hdr` (1.45, 0.95, ±0.42) tiene el eje a 19 mm de la piel, dentro del
sándwich (−10 mm de aire); pide 0.992 y la piel da 0.959.

| x | tubo | la piel debe estar ≥ | cabe hasta |z| = | esquina real en |z| = |
|---|---|---|---|---|
| 2.02 | arco `mh_hi` | 1.059 | 0.08 | 0.44 |
| 1.45 | cabecera `hdr` | 0.992 | 0.28 | 0.42 |

No se parchó estirando el techo: la lámina no tiene ese techo plano, y la instrucción
del proyecto es que **el chasis se derive de la carrocería**. Lo que toca es rehacer
la parte alta de la célula como arco trapezoidal/redondeado —esquinas a |z|≈0.28-0.30
y y≈0.98-1.00, piernas abiertas hacia `mh_belt` (±0.49)— y volver a correr el FEM de
volcadura (LC5), que es el que manda ahí. Las cabezas van en z=±0.31, así que un arco
de ±0.30 arriba sigue cubriéndolas con 75 mm de claro sobre la cabeza.

**2. El larguero delantero `fx_lo→dash_lo` (z=0.53-0.60) caía dentro del pozo de la
rueda**, que arrancaba en |z|=0.55. Corregido: el pozo arranca en 0.615 (quedan 45 mm
a la cara interior de la llanta).

**3. Las esquinas del cowl `dash_hi` (0.95, 0.72, ±0.48) quedaban a 8 mm de la piel**,
dentro del sándwich: el levantamiento del techo por el chasis se aplicaba al centro,
no a la repisa ni a la base del cristal. Corregido en la jaula: `Y_ARISTA` y `Y_DLO`
suben 25-35 mm entre x=0.85 y 1.05. Ahora ningún tubo fuera de las dos esquinas del
punto 1 tiene menos de 12 mm de aire; 31 tubos del piso y del espinazo tienen entre
12 y 20 (por diseño, el piso va a 16 mm bajo el tubo más bajo).

**Lo demás:** llantas con 46 mm de holgura radial al pozo y ningún vértice de piel
dentro de ellas; cabezas de los pilotos con 75 mm de claro al techo; ruedas del GLB en
x=0.550/2.680, z=±0.750/0.760, R 0.2876/0.3005 (las del chasis, exactas).

## Lo que costó (para no repetirlo)

- **Tapas n-gon con crease se pliegan al subdividir** y el booleano exacto de Blender
  lee entonces el sólido al revés (difference = unión, o malla vacía). Tapas en
  escalera de cuadriláteros: cero problemas.
- **Al vaciar los slots de material, Blender pone a 0 el índice de todas las caras**:
  cualquier dato que viaje ahí se pierde. Los atributos INT de cara sí sobreviven al
  modificador de subdivisión (verificado en 4.5) y son la vía correcta.
- **Solidify con "even offset" dispara el espesor en esquinas agudas** (1/sin): un
  cortador de 1 m salía de 22 m. Y con offset positivo deja las normales hacia
  adentro; hay que recalcular (y comprobar el volumen firmado) antes de un booleano.
- **Shrinkwrap deja en el plano de origen lo que no encuentra piel** y arma picos de
  metros al unirse con lo que sí proyectó: se borran esos vértices.
- **El vértice espejado en la posición k es el anillo `n_ring - k`; la cara entre k y
  k+1 es el `n_ring - k - 1`.** Usar la fórmula de cara para las aristas desfasó los
  creases del lado -z y dejó la carrocería 5-9 mm asimétrica. Se detectó midiendo el
  STL por tramos, no a ojo.

## Lo que queda

0. **Célula alta del chasis vs burbuja del techo** (arriba): decisión de ingeniería
   pendiente, con re-FEM. Es lo primero.
1. **Puertas de gaviota abiertas** en el visor (la v2 las tenía). La junta ya está
   dibujada por el contorno del chasis (pilar A → espinazo |z|=0.15 → pierna del arco);
   separarla como pieza y colgarla del espinazo es el paso siguiente.
2. **Ancho**: 1.78 m lo manda la trocha. La cenital de la referencia normalizada por
   batalla da 1.82, así que ya no es una duda de proporción; es cosa de decidir si
   sobra o falta cadera.
3. **Llantas**: la lámina trae ~255/35 en rin 21"; el paquete lleva 175/70 en 13/14"
   (QS273). Es la mayor diferencia visual que queda y no se arregla en la carrocería.
4. **Espesor y corte en paneles** (12 mm sándwich, 10 paneles), y derivar el chasis
   de la carrocería, siguen pendientes igual que antes.
5. Los bordes del cristal en el parabrisas van por una V en planta y quedan a la
   resolución de la subdivisión (~15 mm); los demás van alineados a la jaula.
