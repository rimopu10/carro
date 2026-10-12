# Cabina, vista del conductor y puertas — diseño

**Fecha:** 2026-10-12 · **Estado:** diseño aprobado en conversación, falta revisión del documento · **Alcance:** posición del piloto,
visibilidad, aspecto de la cabina, y sistema de puertas de gaviota (estructura, herraje, cierre, encaje) con las
interfaces que exigen al chasis. Complementa `2026-07-05-carro-electrico-design.md`.

## 1. Por qué existe este diseño

Dos observaciones del usuario sobre el chasis rediseñado (2026-10-12):

1. **El chasis tapa mucho la vista del conductor y se nota mucho en la cabina.**
2. **No hay nada para las puertas**: sólo existía el hueco libre y el eje de bisagra. Hace falta que cierren, ajusten y se
   sientan sólidas ("no de papel").

Revisando (1) se encontró un error de base: **el maniquí del proyecto no es un adulto de 1.75 m** (`calculos/carroceria.py`:
cadera→hombro 41 cm, un adulto real tiene ~51 cm). La cabina "validada" estaba medida con un cuerpo encogido.

## 2. Datos medidos que fundamentan el diseño

| Dato | Valor | Fuente |
|---|---|---|
| Cabecera del parabrisas (hdr–sp_f) | a 0.42 m del ojo; ocupa **3.2° a 10.0°** sobre la línea de los ojos; tubo de 51 mm se ve de **6.9°** de ancho | geometría de `cad/chasis.json`, ojo en (1.87, 0.885, 0.31) |
| Efecto de la altura del ojo en el borde inferior de la cabecera | −3 cm → 7.3° · −5 cm → 9.9° · −7 cm → 12.6° | cálculo directo |
| Piel de Tripo sobre el piloto (x 1.90, z 0.31) | cara exterior 1.096 m, **cara interior 1.053 m** (techo de ~43 mm) | rayos sobre `cad/carroceria-tripo-solida-mm.stl` |
| Piel en la cabecera (x 1.45, z 0.31) | exterior 1.010, interior 0.998 | ídem |
| Límite útil de cabeza (interior − forro de 20 mm) | **1.033 m** a x≈1.9 | derivado |
| Cuerpo humano de referencia (hombre p50, 1.75 m) | tronco cadera→hombro 0.51 m; hombro→ojo 0.19; ojo→coronilla 0.12; muslo 0.43; pierna 0.41 | antropometría estándar |

## 3. Posición del piloto (la decisión que condiciona todo)

**Se diseña para 1.75 m y el asiento corre sobre rieles** para que alguien más alto lo mueva hacia atrás.

Posición nominal para 1.75 m (centro del recorrido de los rieles), calculada con el cuerpo real:

- **Cubeta delgada a medida** (fibra + 2–3 cm de espuma), **hundida entre los tubos del piso**: cadera a **y≈0.26 m** (hoy 0.30–0.345).
- **Respaldo recostado ~40°** desde la vertical.
- **Cadera en x≈1.50 m** (hoy el nodo del asiento está en 1.62): 12 cm más adelante.
- Resultado esperado: ojo y≈0.84; coronilla ≈0.96 → **~70 mm bajo el límite útil del techo**; nuca a x≈1.90 → **~100 mm hasta el arco**
  (x=2.02); **borde inferior de la cabecera a ~+11° sobre el ojo** (hoy +3°); objetivo de diseño ≥ +12° subiendo la cabecera 1–2 cm
  dentro de los ~38 mm que deja la piel.
- **Rieles: recorrido de cadera x 1.42–1.58 m (160 mm), con 1.75 m en el centro (x=1.50).** Un conductor de 1.60 m usa el extremo
  delantero; uno de 1.85 m el trasero, donde su nuca queda a ~20 mm del arco. El recorrido da espacio de **piernas, no de cabeza** (la altura sentado crece 3–4 cm por cada 10 cm de estatura): el
  límite práctico es ~1.80 m cómodo y 1.85 m justo.
- **Barra de cinturones** baja de y 0.742 a ≈0.66 (altura real del hombro) y se ajusta a la nueva x; arnés de longitud ajustable
  porque el asiento se mueve.
- **Pedales** quedan en x≈0.62–0.70, dentro de la caja delantera (entre cremalleras y travesaños fx/fb). Hay que verificar que
  quepan con su cilindro de freno, y el travesaño `dash_lo` (x=1.10) pasa a quedar bajo las rodillas, no bajo los pies.
- **Volante y columna** se definen en la maqueta de asiento (`buck`); ya hay un volumen prohibido para la columna en
  `rediseno_chasis.py`.

### Aspecto de la cabina
- Lo grande va **tapado por forro**: pilar A, rieles del techo (bajo cielo raso), estribos (bajo moldura de umbral). Se reserva
  **20 mm** alrededor de cada tubo visible para el forro.
- Regla: en la cabina sólo queda a la vista lo que se decida mostrar; se lista en el plano de cabina.
- La cabecera deja de ser el elemento dominante del campo de visión: sube 1–2 cm y se evalúa bajarla de sección sin perder FS.

## 4. Puertas de gaviota

### Construcción (por puerta)
- **Piel de fibra sándwich**: 2 capas de fibra de vidrio (~300 g/m²) + 5 mm de espuma de celda cerrada. Da la rigidez de viga
  en caja.
- **Esqueleto de tubo redondo delgado**: Ø16 × 1.2 mm (≈0.45 kg/m), doblado en un anillo con un travesaño (~2.5 kg).
  Sin PTR (decisión del usuario). Sirve para repartir cargas de herraje y mantener la forma.
- **Placas de acero de 3 mm** (corte láser, mismo flujo que `planos/*.dxf`) sólo en los puntos de bisagra, cierre y amortiguador,
  atornilladas a través del sándwich.
- **Cristal fijo de policarbonato 3 mm.** Sin elevalunas.
- **Masa estimada: 9–10 kg por puerta** (a confirmar en el plan).

### Herraje y cierre
| Pieza | Especificación inicial |
|---|---|
| Bisagras | 2 por puerta, acero forjado, sobre el espinazo (rieles sp_f–sp_r, x≈1.55 y x≈1.95, y≈1.01, z=±0.15), agujeros ranurados |
| Apoyo | 1 amortiguador de gas por puerta (~250 N) que sostiene 65°; extremo del chasis cerca de la cabecera |
| Cierre | **3 puntos**: techo delantero (esquina de cabecera), estribo, trasero (pierna del arco). Pernos ajustables + topes de goma |
| Manijas | exterior al ras + tirador interior; cable de liberación de emergencia |
| Sello | goma tipo D sobre la brida del vano; holgura puerta–carrocería **5 mm** |

### Encaje
- El chasis soldado se deforma 2–3 mm: **la puerta se termina sobre el carro ya armado**, usando el vano real como referencia
  (plantilla de vano + modelado sobre el carro), con herraje ajustable en 3 ejes.
- Brida del vano continua (carrocería pegada a los tubos del estribo, pilar A, arco y espinazo).

### Geometría verificada de apertura
Eje de bisagra en (y≈1.01, z=±0.15). Con la puerta abierta a 65°, su borde inferior queda a ~1.39 m del suelo y ~24 cm fuera de
la carrocería. A verificar en el plan: barrido contra carrocería, cabeza y hombros al entrar/salir.

## 5. Cambios al chasis que exige este diseño
1. Nodos de asiento `smL/smR` más adelante (x≈1.50) y más bajos (y≈0.26), con rieles de asiento y su travesaño.
2. Barra de cinturones `mh_belt` a y≈0.66 (revisar LC5/LC5c).
3. Cabecera (`hdr`, `sp_f`) +1–2 cm si la piel lo permite (`verificar_piel_tripo.py`).
4. **Bases de herraje**: pads de bisagra en el espinazo; soporte del amortiguador; pernos de cierre en estribo, esquina de cabecera
   y pierna del arco.
5. Soporte de pedalera dentro de la caja delantera.
6. **Nuevo caso de carga LC7 (puerta abierta):** 2 puertas de ~10 kg × 3 g vertical + 400 N lateral de viento en el centro de cada
   puerta, aplicado en los pads de bisagra. Criterio: FS ≥ 2 en la viga del espinazo y sus extremos.
7. Todo vuelve a pasar por `rediseno_chasis.py`, `analisis_chasis.py`, `holguras.py`, `hueco_puerta.py` y
   `verificar_piel_tripo.py`.

## 6. Criterios de aceptación
- Borde inferior de la cabecera ≥ **+12°** sobre el ojo (conductor 1.75 m, posición nominal).
- Coronilla ≥ **40 mm** bajo el límite útil del techo en toda la banda de recorrido para 1.75 m.
- Nuca ≥ **80 mm** del arco en la posición nominal (1.75 m) y ≥ **20 mm** en el extremo trasero del recorrido para 1.85 m.
- Entrada/salida con la puerta a 65°: ningún tubo ni herraje a menos de 30 mm del recorrido de hombros y cadera.
- LC1–LC6 sin empeorar los pisos actuales (FS≥2, volcadura≥1.5, cabecera≥1.3, torsión≥2.0) + LC7 FS≥2.
- Lista de corte sin cortes negativos ni < 40 mm; ningún nodo con más de 5 tubos.
- Puerta cerrada: holgura uniforme 5 ± 1 mm y sin vibración con los 3 cierres (verificable al armar).

## 7. Riesgos y puntos abiertos
- **Pedales en la caja delantera** (x≈0.65): puede chocar con cilindro de freno, cremallera o travesaños fx/fb.
- **Cinturones con asiento deslizable:** requiere arnés ajustable; con asiento fijo sería más simple.
- **Holgura de cabeza vs forro:** el espesor real del forro del techo (20 mm) es supuesto.
- **Cabecera:** el ojo a +11° no llega al +15° de un coche normal; el techo de Tripo no deja más.
- **Estatura >1.80 m:** el recorrido no da más espacio de cabeza.
- La altura de la cara interior del techo se midió sobre la malla de Tripo (espesor ~43 mm); si la carrocería real se lamina más
  delgada, la holgura sube.

## 8. Fuera de alcance
Elevalunas, cierre centralizado eléctrico, homologación de choque, diseño de la butaca (cubeta), diseño detallado de la
pedalera y de la columna de dirección (aquí sólo se reserva su espacio), tapicería.

## 9. Entregables previstos
`calculos/buck_piloto.py` (maniquí + barridos), actualización de `analisis_chasis.py`/`rediseno_chasis.py` (nodos, volúmenes,
LC7), `calculos/puertas.py` (geometría de apertura, fuerzas de bisagra/amortiguador, coordenadas de herraje),
visor con vistas "Ojos piloto" y puerta abierta, filas nuevas en `docs/bom-maestro.*` (herraje, amortiguadores, policarbonato,
tubo Ø16, placas) y secuencia de armado "encaje sobre el carro".
