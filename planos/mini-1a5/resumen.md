# Mini 1:5 — resumen (generado por calculos/mini.py; no editar a mano)

- Fuente: `planos/lista-corte-tubos.csv` (tamaño real), coordenadas ÷ 5.
- Tubo del modelo: **8×8×1** para todo (el tubo no escala; ver tabla).
- 90 tubos, 54 nodos, **7.01 m** de tubo en 8 barras de 1000 mm (sierra 1 mm, 5 mm por punta).
- Choques a escala (tubos que tienen luz en el real y se tocan en la mini): **0**.
- Cortes de menos de 20 mm (4): #59 fx_hiL–anAMORTL (19 mm), #60 anAMORTR–fx_hiR (19 mm), #61 mh_loL–bat_fL (15 mm), #62 mh_loR–bat_fR (15 mm).

## Qué tubo real representa cada tubo de 8 mm

| Sección real | Equivale a 1:5 | Tubos | Lado del modelo ÷ lado escalado |
|---|---|---|---|
| PTR 25x25x1.9 | 5.0 mm | 6 | 1.60 |
| PTR 38x38x1.9 | 7.6 mm | 44 | 1.05 |
| PTR 38x38x3.0 | 7.6 mm | 12 | 1.05 |
| PTR 44x44x1.9 | 8.8 mm | 7 | 0.91 |
| RED 50.8x2.1 | 10.2 mm | 5 | 0.79 |
| RED 57.2x3.2 | 11.4 mm | 14 | 0.70 |
| RED 57.2x4.0 | 11.4 mm | 2 | 0.70 |

La mini es un prototipo de **forma, encaje y mecanismos** (cinemática de suspensión, puertas, dirección), no de resistencia: el tubo 8×8×1 no escala las secciones, así que sus esfuerzos no representan los del carro.
