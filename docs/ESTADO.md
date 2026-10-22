# Estado del proyecto y cómo retomarlo

**Última actualización:** 2026-10-21 (cargas de suspensión, refuerzo, caja estrecha, auditoría de cabina, visor nuevo y auditoría independiente aplicada; sin commit aún) · **Último commit de la línea de cabina/puertas:** `96ef643`.
**Cambio mayor del 2026-10-21:** el chasis ya NO es el de 90.1 kg. Con las cargas reales de la suspensión pasando por los brazos (`calculos/cargas_suspension.py`) el diseño anterior daba FS 1.26 en bache; `calculos/reforzar_suspension.py` subió 5 tubos y quedó en **92.9 kg, K 8,905 N·m/°**, FS de suspensión ≥ 2.32 (servicio) y ≥ 1.81 (casos raros).
**Tercer cambio mayor (misma fecha, decisión del usuario «ponlo donde sea mejor»): la batería pasó al túnel central** (30 celdas en una caja entre las butacas) y la electrónica de potencia atrás junto a los motores: reparto 46.7% delante, CG 0.40 m, inercia de guiñada −26%. El chasis ahora pesa **99.0 kg, K 9,748 N·m/°** (ver `docs/masas-y-bateria.md`); resortes 397/238 lb/in, disco delantero Ø240, pedal 6.5:1.
**Segundo cambio mayor (misma fecha): la caja delantera se estrechó 35–70 mm** (nodos `fb_lo/fb_hi/fx_lo/fx_hi` en `analisis_chasis.py`): los brazos atravesaban el larguero hasta 31 mm porque los pivotes caían sobre el eje de los tubos. Mover los pivotes arruinaba la cinemática (bump steer 0.06→1.2°/25 mm), así que se movió el chasis. `holguras.py` ahora revisa brazos contra tubos en todo el recorrido (≥31 mm). Ver `docs/cargas-suspension.md`.
Si eres una sesión nueva de Claude: lee primero este archivo, luego `docs/herraje-puertas.md` (números y criterios medidos).

## 1. Ver el 3D (lo primero)

**Abre `carro-tripo-chasis-3d.html` con doble clic.** Necesita internet (three.js se carga de un CDN). Trae:
- carrocería de Tripo semitransparente + el **chasis de 101 miembros (87 tubos de corte)** (colores por función) + ruedas de relleno;
- **piloto de 1.75 m** sentado (cápsulas), con el asiento hundido y reclinado 40°;
- **puertas de gaviota que abren** (deslizador 0–65°) con su herraje: bisagras (amarillo), cierres (cian), amortiguador (blanco);
- botones de vista: 3/4, Lado, Arriba, Frente, Debajo, **Ojos piloto**, Ojos pasajero, Atrás piloto, **Puerta abierta**;
- pasar el mouse sobre un tubo muestra su nombre.

Para **regenerarlo** (si cambias el chasis):
```
python calculos/analisis_chasis.py            # lee calculos/chasis_rediseno.json y escribe lista de corte + informe
python calculos/exportar_blender.py           # escribe cad/chasis.json (lo que lee el visor)
python calculos/preparar_piel_tripo.py        # una vez: cad/_vista/*.stl (piel de Tripo cerrada y decimada; ~1 min)
python calculos/visor_tripo_chasis.py cad/_vista/tripo-vista.stl
```
`preparar_piel_tripo.py` necesita `cad/carroceria-tripo-solida-mm.stl` (60 MB, NO va en git). Si falta:
`blender --background --python render/tripo_base.py` (requiere `ref/tripo/tripo-multivista-h31.glb`). Dependencias:
`trimesh`, `rtree`, `manifold3d`, `matplotlib`, `fast-simplification`, `pytest`.

## 2. Qué se hizo (resumen; el detalle está en los commits y en `docs/`)

| Tema | Resultado |
|---|---|
| Carrocería vigente | **Tripo** (3.95×1.79×1.11 m, batalla 2.13). Sus ruedas son de IA y se rehacen. La v3 por subdivisión quedó superada. |
| Tubo en la puerta | Era la diagonal `dash_hi–mh_lo`: quitada. Hueco de entrada **libre** (`calculos/hueco_puerta.py`). |
| Chasis rediseñado | **104 miembros (91 tubos + 8 nodos de anclaje + 2 puntales de la torre + 3 tubos de piso: apoyo de la pila y aro del arco), 90 tubos de corte, 99.0 kg, K 9,748 N·m/°**, **7 secciones. Antes del refuerzo y de estrechar la caja: 90.1 kg, K 8,702. Diseño base anterior: 94.7 kg, K 14,058. |
| Cargas de suspensión | Piso → mangueta → brazos/amortiguador/cremallera → anclajes; chasis libre en equilibrio (reacciones 0.0 N). S1 bache 3 g 2.03 · S2 frenada 4.15 · S3 curva 2.44 · S4 bache en 1 rueda 2.36 (servicio, exigido ≥ 2.0); S5 bache+curva 1.54 · S6 alabeo diagonal 1.79 y extremos del reparto axial de las bisagras (exigido ≥ 1.5, carga excepcional). Fluencia con torsión (von Mises). Cargas de ménsula en `docs/cargas-suspension.md` (amortiguador del. 6.6 kN, tras. 5.8 kN, pivote inf. 3.6 kN). |
| Auditoría de cabina | `calculos/auditoria_cabina.py`: tubos vs cuerpo (3 posiciones de riel, 3 estaturas), huella del asiento, obscuración de vista, holguras. Hallazgos abiertos en §6. |
| Piloto | Maniquí de 1.75 m real (el anterior estaba encogido). Cadera nominal (x 1.50, y 0.26), 40°; rieles x 1.43–1.51. Cabe hasta **1.77 m** (`buck_piloto.ESTATURA_MAX`: tope del riel; espalda–barra de cinturones ≥ 20 mm). |
| Vista | Cabecera a **+12.9°** sobre los ojos (antes +3°). |
| Puertas | Piel sándwich + esqueleto Ø16×1.2 + placas 3 mm; 2 bisagras (eje inclinado), amortiguador **500 N**, 3 cierres. Puerta abierta: el ala baja a **1.26 m** (hay que agacharse). |
| Casos de carga | LC1 3.16 · LC3 2.66 · LC4 2.90 · LC5 1.72 · LC5c 1.77 · LC6 2.13 · **LC7 puertas 7.0 · LC8 arnés 10 g 2.18**. FIA (LC5b) 0.32: no homologable. |
| Topes de la calle | `calculos/topes.py`: la piel de Tripo cuelga a 75–95 mm del piso. Plan: vientre central oculto a ~126 mm + placa de sacrificio; la nariz NO se sube. **No aplicado al modelo.** |
| Auditorías | Dos rondas con agentes. Encontraron errores reales cada vez; hacerlas siempre antes de cerrar. |

## 3. Comandos de verificación (todo debe seguir en verde)

```
python -m pytest calculos -q                       # 16 pruebas (buck_piloto, puertas, ke)
python calculos/analisis_chasis.py                 # FS de LC1..LC8, masa, K; reescribe planos/lista-corte-tubos.csv
python calculos/hueco_puerta.py                    # "LIBRE"
python calculos/holguras.py                        # "TODO LIBRE" (suspensión vs tubos)
python calculos/verificar_piel_tripo.py cad/_vista/tripo-cerrado-sin-ruedas-mm.stl   # "0 tubos asoman"
python calculos/buck_piloto.py                     # techo/nuca/cabecera por estatura
python calculos/puertas.py                         # amortiguador, esfuerzo de manija, cargas LC7
python calculos/bom.py                             # regenera docs/bom-maestro.md/.csv
python calculos/cargas_suspension.py               # S1..S4 con las ruedas por los brazos; reescribe docs/cargas-suspension.md
python calculos/auditoria_cabina.py                # cuerpo/asiento/vista; dibuja docs/auditoria-cabina/*.png
```
`python -m pytest calculos -q` son ahora **29** pruebas (incluye `test_masas.py` — reparto y CG de resortes/frenos = presupuesto de masas — y `test_cargas_suspension.py`: equilibrio de fuerzas y momentos, ningún anclaje flota, FS por niveles, distancia entre segmentos contra fuerza bruta).
**Orden si se rehace la topología:** `rediseno_chasis.py` → **`reforzar_suspension.py`** (reescribe `chasis_rediseno.json`, idempotente) → `analisis_chasis.py` → resto. El optimizador NO conoce las cargas de suspensión: sin el paso de refuerzo los tubos junto a las ruedas quedan en FS ~1.3.

## 4. Cómo se cambia el chasis (no editar los tubos a mano)

La topología sale del optimizador, **no** de `analisis_chasis.py` (que sólo conserva el diseño base de nodos duros):

```
python calculos/rediseno_chasis.py 8000 calculos/_rd_nuevo.json   # 3–5 min; 8000 = rigidez mínima N·m/°
# revisar la última línea 'final:' y que NO diga 'AVISO: nodo ... saturado' ni 'cruces sin nodo: [...]'
cp calculos/_rd_nuevo.json calculos/chasis_rediseno.json && rm calculos/_rd_nuevo.json
# luego los comandos de la sección 1 y 3
```
- `CHASIS_BASE=1 python calculos/analisis_chasis.py` calcula el **diseño anterior** (sirve para comparar). Borrar `chasis_rediseno.json` hace lo mismo.
- `PALETA=todas` libera las secciones (9 secciones: ~3.5 kg menos). `calculos/chasis_rediseno_9secciones.json` es ese resultado guardado (sin LC8).
- Reglas del optimizador (constantes al inicio de `rediseno_chasis.py`): FS≥2 en bache/frenada/curva; volcadura≥1.65; cabecera≥1.3; torsión≥2.0;
  puertas≥2.0; arnés≥1.5; K≥8000; pandeo≥2. Volúmenes prohibidos: hueco de puerta, cuerpo del piloto (3 posiciones del riel), batería,
  parabrisas, plano del arco, nariz. Pisos de sección por función; pared mínima 1.9 mm.

## 5. Decisiones del usuario que mandan

- Quiere **ingeniería real**, no demos; responde en español; juzga proporciones viendo renders (con ruedas y escala).
- Carrocería de Tripo **no se toca** (se ajusta el chasis; si algo choca, se cambia el chasis o se retoca la piel localmente sin cambiar la estética).
- Nada de PTR en las puertas (tubo/varilla delgada); ligero y barato.
- Diseño para 1.75 m con asiento deslizable (alguien más alto lo mueve atrás); butaca de cubeta delgada a medida.
- Prototipo funcional a **1:5** (~79×36×22 cm, tubo 8×8×1) generado desde una sola fuente a tamaño real: **todavía no empezado**.
- Quiere que "embone bien" y no se sienta "de papel": piensa en herraje, encaje y construcción real.

## 6. Pendiente, en orden sugerido

**Hecho el 2026-10-21:** cargas de suspensión en el FEM (antes eran apoyos fijos) y refuerzo de los tubos que fallaban; visor con
corte lateral, grupos de tubos, asientos de cubeta, suspensión/ménsulas y tubos a <30 mm del cuerpo en rojo; auditoría de cabina.

1. **Secciones de tubo:** hoy 7 (las 6 de la paleta + RED 57.2×4.0 sólo en las patas del arco). 9 secciones bajarían unos 3.5 kg; sin respuesta del usuario.
2. ~~Dónde va la masa~~ RESUELTO (ver `docs/masas-y-bateria.md`): batería en el túnel central, electrónica atrás; resortes y frenos recalculados. Falta confirmar con proveedor las dimensiones reales de la celda (130×36×200 mm supuestas) y la pared de la caja.
3. **Soporte de la cremallera.** Hoy está a 82 mm del poste `fb` y sin diseño (la carga es pequeña, 0.3 kN, pero el bastidor no existe).
   La cremallera pasa a 88 mm de la punta del pie. La ménsula del soporte sale a 106 mm del eje del poste (no 82). Viene del diseño de dirección (`calculos/direccion.py`).
4. **Columna de dirección:** trazo geométrico resuelto en `docs/mandos-cabina.md` (volante de fondo plano Ø300, cubo x=1.30 y=0.58, cardán en (0.73,0.53)); falta el soporte (viga `dash_hi` L–R), los dos cardanes y la columna colapsable. **Pedalera:** bola del pie en x≈0.52,
   punta x≈0.46, `fb_lo` a 24 mm de los dedos con el riel adelantado; definir caja de pedales y cilindro de freno.
5. **Barra de cinturones:** RESUELTO con tope del riel: `buck_piloto.ESTATURA_MAX = 1.77` (recorrido de cadera x 1.43–1.51; espalda–barra +24 mm). Un piloto de 1.80 m ya no cabe sin mover la barra. Los travesaños del piso bajo el asiento (x=1.36 y 1.66) son soporte de los rieles, no un error.
6. **Vista:** el ojo queda a 373 mm de la esquina de la cabecera (304 mm con 1.60 m); el pilar A tapa 13° por ojo a 9° de la línea de visión y la
   cabecera queda a +12.9° (+9.5° con 1.80 m; un semáforo a 10 m está a ~15°). Depende de la piel de Tripo (no se toca): documentar como compromiso.
   **Revisado 2026-10-21 (el usuario preguntó si conviene mover el tubo):** el pilar A (`dash_hi–hdr`) y la cabecera ya están a ~10 mm de la cara exterior de la piel
   (`verificar_piel_tripo.py`), o sea que no se pueden mover hacia afuera ni hacia arriba sin asomar; hacia adentro empeora la vista y la volcadura. Binocularmente tapan 0° (el otro ojo
   ve por detrás); la piel de Tripo del pilar es más ancha que el tubo, así que moverlo no cambia lo que se ve. Decisión: no moverlo.
7. **Aplicar los topes**: vientre central a ~126 mm + placa de sacrificio (ver `calculos/topes.py`).
8. **Torre del amortiguador delantero:** una tornapunta de la ménsula a `fx_lo` (PTR 38x38x1.9) ahorraba ~1 kg medido con la caja anterior; falta rehacer la prueba con la caja estrecha y comprobar que no roce el buje del brazo inferior. Verificar localmente la pared del tubo en cada ménsula.
9. **DXF de las ~14 placas de herraje de las puertas** (3 mm; ahora llevan 2 pernos M8 por cierre) y diseño detallado de la puerta (el visor usa las piezas del juguete 1:20). Seguridad de la puerta ya definida: `docs/seguridad-puertas.md` (viga de impacto, salida de emergencia, retención); falta fijar la posición real de la viga contra el vano y un ensayo estático.
10. **Mini 1:5**: generador con parámetro `escala` (lista de corte con tubo 8×8×1, plantilla de soldadura en tabla, paneles ≤206 mm para la Ender 3 V3 SE).
11. Rehacer las **ruedas** (las de Tripo son de IA) y volver a medir los tubos cerca de las ruedas (marcados con `(*)` en `verificar_piel_tripo.py`).
12. Puerta del juguete impreso: es una simplificación (contorno trazado a mano, cristal rehecho, sin panel interior, bisagra añadida), no tolerancias.

## 7. Trampas conocidas

- **Hilos de BLAS**: numpy con muchos hilos tarda 60× en sistemas pequeños. Los scripts fijan `OPENBLAS_NUM_THREADS=1`; si escribes uno nuevo, hazlo antes de importar numpy.
- **El optimizador necesita una partida factible** (todo en la sección máxima): si imprime `partida ... cumple=False`, el resultado es basura (212 miembros, 340 kg). Se vio al
  acotar el diámetro del pilar A; se descartó.
- `analisis_chasis.py` **sobrescribe** `planos/lista-corte-tubos.csv` y `calculos/resultados-analisis.md` cada vez que se ejecuta como script
  (`fem_chasis.py` y `rediseno_chasis.py` no los tocan). Con `CHASIS_BASE=1` los escribe con el diseño anterior: volver a correrlo sin la
  variable antes de commitear.
- En Windows/Git Bash, un heredoc largo con apóstrofes puede romper el comando; para scripts grandes, escribir el archivo con la herramienta de archivos.
- Servidor local para ver el HTML sin internet no sirve (three.js es CDN); `python -m http.server` sólo hace falta si el navegador bloquea `file://`.
- La extensión de Chrome de Claude no abre `file://` ni `localhost`; para verificar el visor se usa Playwright (Python) con Chromium: ver el guion en el historial de la sesión 2026-10-21 (carga el HTML por `file:///`, pulsa botones y toma capturas).
- `fem_chasis.py` carga el diseño BASE, no el rediseño (su `__file__` falso no encuentra el JSON): para evaluar el chasis vigente usar `cargas_suspension.cargar_vigente()` (replica lo que hace `analisis_chasis.py`).
- Un nodo de anclaje ya registrado pero sin tubos queda FLOTANDO y la carga se pierde en silencio: `evaluar_suspension` lanza error si pasa (ocurrió en el desarrollo y daba FS falsos de 2.03).
- `impresion/ender3v3se.zip` está sin versionar (no es de esta línea de trabajo).

- `holguras.py` importa `analisis_chasis`, que **reescribe** `calculos/resultados-analisis.md` y `planos/lista-corte-tubos.csv`: correr solo el chequeo modifica archivos versionados.
- El pandeo de `esfuerzo_max` usa la longitud del TRAMO entre nodos, no la del tubo continuo (tubos partidos por nodos de anclaje): conservador, sin consecuencia hoy (FS de pandeo ≥ 100), pero habría que agrupar tramos colineales.
- La fluencia usa σ_vm = √(σ² + 3τ²) con τ = T·c/J (desde 2026-10-21): los FS de todos los casos bajaron algo respecto a documentos anteriores.
- El reparto axial de las bisagras (a lo largo del eje de los pivotes) es hiperestático: las cargas de LA1/UA1/UA2 varían hasta ±60% según la rigidez de los bujes; `cargas_suspension.py` cubre los extremos (`[axial a/b]`).
- Páginas HTML antiguas (`chasis-completo.html`, `carro-completo-3d.html`, `carroceria-3d.html`, `carro-diseno-3d.html`) y `planos/lista-corte-tubos-optimizada.csv` son de antes del rediseño: no regenerar sin decidir si se retiran.
- `resultados-direccion.md` está desfasado (el `direccion.py` actual imprime un bloque CONFLICTO del Ackermann +3.5%, previo a estos cambios).

## 8. Mapa de archivos nuevos (esta línea de trabajo)

| Archivo | Para qué |
|---|---|
| `calculos/rediseno_chasis.py`, `fem_chasis.py` | optimizador de topología y secciones; FEM reutilizable (LC1–LC8) |
| `calculos/chasis_rediseno.json` | **el chasis vigente** (lo lee `analisis_chasis.py`) |
| `calculos/buck_piloto.py`, `test_buck_piloto.py` | cuerpo humano real, métricas de cabina |
| `calculos/puertas.py`, `test_puertas.py` | cinemática, amortiguador, LC7, herraje |
| `calculos/hueco_puerta.py` | qué tubos cruzan la entrada |
| `calculos/verificar_piel_tripo.py`, `arreglar_chasis_tripo.py`, `preparar_piel_tripo.py` | chasis vs piel de Tripo |
| `calculos/topes.py` | simulación de tope (speed bump) |
| `calculos/cargas_suspension.py`, `test_cargas_suspension.py` | cargas del piso → brazos → anclajes; FS del chasis; escribe `docs/cargas-suspension.md` |
| `calculos/reforzar_suspension.py` | sube la sección de los tubos que fallan con esas cargas y deja los anclajes (`an*`) como nodos |
| `calculos/auditoria_cabina.py` | cuerpo/asiento/vista vs tubos; imágenes en `docs/auditoria-cabina/` |
| `calculos/masas_cg.py`, `masas_modelo.py`, `test_masas.py` | presupuesto de masas por componente; masas explícitas del FEM; amarre de reparto/CG (`docs/masas-y-bateria.md`) |
| `calculos/espacios_libres.py` | volúmenes libres bajo la piel: frunk 36 L, bandeja 45 L, maletero 175 L (`docs/espacios-y-cajuela.md`) |
| `calculos/seguridad_puertas.py` | viga de impacto, retención, salida de emergencia de las puertas (`docs/seguridad-puertas.md`) |
| `calculos/cabina_mandos.py` | posición del volante y trazo de la columna (`docs/mandos-cabina.md`) |
| `calculos/visor_tripo_chasis.py` → `carro-tripo-chasis-3d.html` | visor 3D |
| `docs/herraje-puertas.md` | puertas: construcción, coordenadas, armado, criterios medidos, abierto |
| `docs/superpowers/specs/2026-10-12-cabina-y-puertas-design.md`, `plans/2026-10-12-cabina-y-puertas.md` | diseño y plan (con §10 de cambios) |
| `docs/bom-maestro.md/.csv` | lista de compra regenerada (herraje, tubo Ø16, rieles, etc.) |
