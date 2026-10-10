# Juguete 1:20 con puertas de gaviota y ruedas que giran (2026-10-09)

`calculos/tripo_gaviota.py` → piezas acostadas aquí; armado para ver en Blender con
`blender --python render/abrir_gaviota.py` (puerta izquierda abierta 65°).

| Archivo | Qué es |
|---|---|
| `gaviota-1a20-carroceria.stl` | 198 × 89 × 53 mm, cabina hueca con asientos y tablero; cristales como lámina de 1.2 mm |
| `gaviota-1a20-puerta-der.stl` / `-izq.stl` | 50 × 37 × 43 mm c/u, se imprimen paradas sobre su canto de abajo |
| `gaviota-1a20-ruedas-x4.stl` | las 4 ruedas |

**Armado:**
1. Ruedas: dos ejes de filamento 1.75 de 87 mm (libres en la carrocería, a presión en las ruedas).
2. Puertas: pon el nudillo de la puerta entre los dos nudillos del techo y mete por el
   frente del nudillo delantero un tramo de filamento de **17 mm**. Entra justo en la
   carrocería (1.9) y la puerta gira libre (2.1). Si queda flojo, una gota de pegamento
   en la punta delantera.

**Impresión:** la carrocería lleva soportes de árbol también dentro de la cabina, bajo el
techo; se sacan por los huecos de las puertas. La holgura puerta–carrocería es de
0.3 mm.

---

# Juguete de la carrocería de Tripo (la nueva, 2026-10-09)

Sale de `calculos/tripo_juguete.py` (ver ahí cómo se cierran los cristales y se rellena
la cabina). Medidas reales de esa carrocería: 3.95 × 1.79 × 1.11 m, batalla 2.13.

| Archivo | Qué es | Tamaño |
|---|---|---|
| `juguete-tripo-1a20.stl` | todo en una pieza, ruedas fijas | 198 × 89 × 56 mm, ~155 g |
| `juguete-tripo-1a20-rodante-carroceria.stl` | carrocería sin ruedas, con ejes en gota de 2.1 | 198 × 89 × 52 mm, ~140 g |
| `juguete-tripo-1a20-rodante-ruedas-x4.stl` | las 4 ruedas (rin de Tripo + llanta lisa), cara interior abajo | Ø30 × 14 mm c/u |
| `juguete-tripo-1a64.stl` | tamaño Hot Wheels, una pieza | 62 × 28 × 17 mm, ~10 g |

**Rodante:** dos ejes de filamento 1.75 de 87 mm. El eje gira libre en la carrocería y
entra a presión en el cubo de la rueda (1.85). Antes, imprime
`prueba-tolerancias-ejes.stl`: si el cubo bueno no es 1.85, cámbialo en
`ruedas_que_giran(cubo_mm=...)`. Hay 0.75 mm de aire entre la llanta y el pozo.

**Carrocería:** imprímela sobre su piso, con soportes de árbol que solo toquen la cama
(debajo de la nariz, de la cola y de los pozos), y capas de 0.12 mm en el techo.

---

# Maqueta impresa — vista previa del diseño (antes del RC)

Para **Ender 3 V3 SE** (cama 220 × 220 × 250, boquilla 0.4) en PLA. Todo sale de la
carrocería v3 por código; si cambia el diseño, se regenera igual (ver abajo).

## Qué imprimir

| Opción | Archivos | Tamaño | PLA aprox. |
|---|---|---|---|
| **1:16 — una pieza** (empezar por ésta) | `maqueta-1a16-carroceria.stl` + `-ruedas-delantera-x2` + `-ruedas-trasera-x2` + `-arandelas-x4` | 211 × 110 × 59 mm | ~230 g |
| 1:12 — dos piezas pegadas | `maqueta-1a12-carroceria-frente.stl` + `-cola.stl` + ruedas y arandelas 1:12 | 282 × 146 × 78 mm armada | ~500 g |
| Antes de las ruedas | `prueba-tolerancias-ejes.stl` | 62 × 16 × 10 mm | 5 g |

El 1:12 se parte en x = 2.15 m reales, sobre la pierna trasera de la puerta, para que
la costura caiga en una junta que ya existe. Lleva 4 pernos de filamento de 1.75 en
agujeros de gota de 2.2 mm, 6 mm por lado: córtalos a 11 mm.

## Ajustes en el slicer

- **Orientación:** como viene, apoyada en el piso plano de la carrocería. No la
  voltees ni la pongas de pie (cama que se mueve + pieza alta = se tambalea).
- **Sin brim**, falda mínima o desactivada: el 1:16 mide 211 mm en una cama de 220.
- 3 perímetros, 5 capas arriba / 4 abajo, relleno **giroide 12 %**.
- **Altura de capa variable**: 0.12 en techo y cofre (casi planos, son los que más
  escalonan), 0.20 en costados.
- **Soportes de árbol sólo tocando la cama**: pozos de rueda, labio de la nariz y
  bajo el difusor. Revisa en la vista previa que no se metan a los surcos.
- Compensación de pata de elefante activada; costura Z "atrás" o alineada.

## Qué trae grabado

- **Juntas de las puertas de gaviota** (0.8 × 0.5 mm): guía para pintar o
  simplemente sombra.
- **Orilla de los cristales** (surco de 0.5 mm): enmascara siguiendo el surco y pinta
  de negro brillante el cristal.
- **Luces**: las Y delanteras, la barra trasera de tres tramos y el triángulo son
  surcos. Se pueden pintar o meter fibra óptica de 1 mm.
- **Difusor, parrilla y branquias** hundidos, para pintar de negro mate.
- Sin espejos: a esta escala se rompen al quitar soportes.

## Ruedas y ejes

1. Imprime **primero** `prueba-tolerancias-ejes.stl`.
   - Placa (agujeros verticales, 1.70 → 2.00 mm de izquierda a derecha; la muesca
     marca el lado chico): busca el que **aprieta** un tramo de filamento de 1.75 sin
     rajarse. Ése es el agujero del cubo de la rueda.
   - Pared (gotas horizontales de 2.0, 2.1, 2.2 y 2.3): el filamento debe **girar
     libre**. La carrocería trae 2.1; si no gira, pasa una broca de 2 mm.
2. Si el agujero bueno no es 1.85, regenera las ruedas con
   `python calculos/maqueta.py 16 --agujero-cubo 1.90`.
3. Ruedas acostadas, cara interior en la cama, sin soportes.
4. Ejes de filamento: **104 mm** el delantero y **105 mm** el trasero a 1:16
   (139/140 mm a 1:12). Orden por lado: rueda → arandela → pozo.
   Para una maqueta estática basta con pegar las ruedas.

## Cómo se regenera

```
"C:\Users\ILV PC\AppData\Local\blender-portable\blender-4.5.10-windows-x64\blender.exe" ^
    --background --python render/carro_v3.py -- --sin-render --maqueta 16,12
python calculos/maqueta.py 16
python calculos/maqueta.py 12 --partir 2150
blender --background --python render/ver_maqueta.py -- impresion/maqueta-1a16-carroceria.stl vista.png
```

Blender deja en `cad/_maqueta-1aN/` la piel, lo que se le suma (splitter y aletas
engrosadas a 1.2 mm) y lo que se le resta (surcos y ejes). `maqueta.py` hace los
booleanos con manifold3d, que garantiza un sólido cerrado: el solver de Blender sobre
la piel ya cortada dejaba aristas abiertas. Ese script escala la pieza, la acuesta
para la cama, la parte si no cabe y reporta medidas y gramos.
