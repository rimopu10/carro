# Estado del proyecto y cómo retomarlo

**Última actualización:** 2026-10-12 · **Último commit de la línea de cabina/puertas:** `eb96f22` (+ el que agrega este documento).
Si eres una sesión nueva de Claude: lee primero este archivo, luego `docs/herraje-puertas.md` (números y criterios medidos).

## 1. Ver el 3D (lo primero)

**Abre `carro-tripo-chasis-3d.html` con doble clic.** Necesita internet (three.js se carga de un CDN). Trae:
- carrocería de Tripo semitransparente + el **chasis de 91 tubos** (colores por función) + ruedas de relleno;
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
| Chasis rediseñado | **91 miembros, 83 tubos de corte, 90.1 kg, K 8,702 N·m/°**, 6 secciones. Anterior: 94.7 kg, K 14,058. |
| Piloto | Maniquí de 1.75 m real (el anterior estaba encogido). Cadera nominal (x 1.50, y 0.26), 40°; rieles x 1.43–1.52. Cabe hasta ~1.78 m. |
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
```

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

1. **Decidir 6 vs 9 secciones de tubo** (hoy 6, 90.1 kg). Preguntar al usuario.
2. **Cremallera vs poste `fb`**: la cremallera termina a 11 mm del eje del poste (dentro del tubo). Viene del diseño de dirección; revisar `calculos/direccion.py`.
3. **Columna de dirección**: una recta cruza `fx_hi`; definir cardán o rediseñar la altura del volante.
4. **Pedalera**: bola del pie en x≈0.52; no hay tubos del piso entre x=0.35 y 1.10; definir soporte de caja de pedales y cilindro de freno.
5. **Aplicar los topes**: vientre central a ~126 mm + placa de sacrificio (ver `calculos/topes.py`).
6. **Cargas de rueda en anclajes de suspensión** en el FEM (hoy son apoyos; por eso esos tubos están en su piso).
7. **DXF de las ~14 placas de herraje de las puertas** (3 mm) y diseño detallado de la puerta (el visor usa las piezas del juguete 1:20).
8. **Mini 1:5**: generador con parámetro `escala` (lista de corte con tubo 8×8×1, plantilla de soldadura en tabla, paneles ≤206 mm para la Ender 3 V3 SE).
9. Rehacer las **ruedas** (las de Tripo son de IA) y volver a medir los tubos cerca de las ruedas (marcados con `(*)` en `verificar_piel_tripo.py`).
10. Puerta del juguete impreso: es una simplificación (contorno trazado a mano, cristal rehecho, sin panel interior, bisagra añadida), no tolerancias.

## 7. Trampas conocidas

- **Hilos de BLAS**: numpy con muchos hilos tarda 60× en sistemas pequeños. Los scripts fijan `OPENBLAS_NUM_THREADS=1`; si escribes uno nuevo, hazlo antes de importar numpy.
- **El optimizador necesita una partida factible** (todo en la sección máxima): si imprime `partida ... cumple=False`, el resultado es basura (212 miembros, 340 kg). Se vio al
  acotar el diámetro del pilar A; se descartó.
- `analisis_chasis.py` **sobrescribe** `planos/lista-corte-tubos.csv` y `calculos/resultados-analisis.md` cada vez que se ejecuta como script
  (`fem_chasis.py` y `rediseno_chasis.py` no los tocan). Con `CHASIS_BASE=1` los escribe con el diseño anterior: volver a correrlo sin la
  variable antes de commitear.
- En Windows/Git Bash, un heredoc largo con apóstrofes puede romper el comando; para scripts grandes, escribir el archivo con la herramienta de archivos.
- Servidor local para ver el HTML sin internet no sirve (three.js es CDN); `python -m http.server` sólo hace falta si el navegador bloquea `file://`.
- `impresion/ender3v3se.zip` está sin versionar (no es de esta línea de trabajo).

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
| `calculos/visor_tripo_chasis.py` → `carro-tripo-chasis-3d.html` | visor 3D |
| `docs/herraje-puertas.md` | puertas: construcción, coordenadas, armado, criterios medidos, abierto |
| `docs/superpowers/specs/2026-10-12-cabina-y-puertas-design.md`, `plans/2026-10-12-cabina-y-puertas.md` | diseño y plan (con §10 de cambios) |
| `docs/bom-maestro.md/.csv` | lista de compra regenerada (herraje, tubo Ø16, rieles, etc.) |
