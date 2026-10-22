# Mandos de la cabina: volante y columna de dirección

Generado/validado con `calculos/cabina_mandos.py` (`python calculos/cabina_mandos.py`). Cuerpo de 1.75 m en la posición nominal del riel
(`buck_piloto.py`: cadera x=1.50, y=0.26, reclinado 40°; ojo y=0.84; muslo a y≈0.45 en x=1.27).

## Hallazgo
Un volante **redondo de Ø330–360 mm no cabe**: con el asiento reclinado 40° y el techo bajo, el aro tendría que subir hasta el nivel de los ojos para
librar los muslos (0 posiciones válidas exigiendo el aro ≥ 50 mm bajo el ojo). Con **fondo plano** (40 mm cortados abajo) y Ø300 hay 68 posiciones válidas
con el aro ≥ 90 mm bajo el ojo.

## Diseño propuesto (lado del piloto, z = +0.31; el pasajero no lleva volante)
| Dato | Valor |
|---|---|
| Volante | Ø300 mm de fondo plano (corte de 40 mm), maza de seguridad |
| Cubo del volante | x = 1.30, y = 0.58 |
| Aro ↔ muslos/rodillas | 76 mm (exigido ≥ 50) |
| Alcance hombro → agarre (9 y 3) | 0.53 m (rango 0.50–0.62) |
| Borde superior del aro | y = 0.73 → 115 mm bajo los ojos |
| Piñón de la cremallera | (0.43, 0.37) |
| Cardán intermedio | (0.73, 0.53), ángulo de la junta 23° |
| Holgura de la columna | ≥ 22 mm a todo tubo y al cuerpo |

La columna recta pasa a solo 3 mm bajo el travesaño de la torre del amortiguador (`fx_hi`, y=0.48); la solución es subirla con un cardán **antes** del
travesaño para cruzarlo por arriba (el trazo por debajo se arrima a la rodilla: 9–11 mm).

## Lo que falta (no se ha modificado el chasis)
- Un cardán de 23° da ~8.6% de variación de relación por media vuelta: el trazo final necesita **dos cardanes** (eje intermedio) con ángulos iguales, y
  fijar el ángulo real del piñón de la cremallera elegida.
- **Soporte de la columna:** no hay tubo cerca del cubo. Propuesta: viga transversal del tablero `dash_hiL–dash_hiR` (x=0.95, y=0.65, 0.96 m de PTR 38x1.9,
  ~2.1 kg) que además rigidiza la base de los pilares A; el optimizador ya reservaba ese volumen como "columna".
- Columna colapsable o junta de seguridad (ver `direccion.py`), y comprobar que el aro plano no tapa el tablero de instrumentos.
- Pedalera (bola del pie en x≈0.52, `fb_lo` a 24 mm de los dedos con el riel adelantado) y cilindro de freno: sin diseñar.
