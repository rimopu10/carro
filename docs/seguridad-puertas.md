# Seguridad de las puertas de gaviota

Generado por `calculos/seguridad_puertas.py` (no editar a mano). Mismas coordenadas que `docs/herraje-puertas.md` (x atrás, y arriba, z lateral; lado izquierdo).
**El carro no es homologable**: los criterios son de referencia para dar una puerta decente, no una certificación.

## 1. Qué faltaba
- Sin protección contra intrusión lateral: la puerta era piel de fibra con un esqueleto de tubo Ø16 × 1.2 mm.
- Si el carro queda sobre el techo, las bisagras (en el espinazo) y el piso hacen imposible empujar la puerta: **no había salida**.
- Si falla el amortiguador de gas con la puerta abierta, una puerta de 12 kg cae sobre la cabeza de quien entra.
- Sin aviso de puerta mal cerrada.

## 2. Viga de impacto lateral
Un tubo redondo **RED 50.8×2.1** por dentro de la puerta, soldado a las placas de cierre (3 mm) en ambos extremos: de [1.4, 0.34, 0.66] a [2.0, 0.6, 0.62], largo 0.66 m, a la altura de cadera–pecho del ocupante. Es la sección redonda más ligera que cumple y **ya está en la paleta de tubo** (sin compra nueva); respeta «sin PTR en las puertas».

Requisito de referencia (estático tipo FMVSS 214): resistencia **intermedia 4.5 kN** y pico 13.5 kN (2 × el peso del carro).

| Tubo | kg | Cede (kN) | Colapsa (kN) | Energía a 300 mm (J) | En paleta | ≥ 4.5 kN |
|---|---|---|---|---|---|---|
| RED 25.4×1.6 | 0.62 | 1.0 | 1.4 | 416 |  | ✗ |
| RED 31.8×2.0 | 0.96 | 2.0 | 2.7 | 815 |  | ✗ |
| RED 38.1×2.0 | 1.17 | 3.0 | 4.0 | 1195 |  | ✗ |
| RED 44.5×2.1 | 1.44 | 4.3 | 5.8 | 1730 |  | ✓ |
| RED 44.5×3.2 | 2.14 | 6.1 | 8.3 | 2504 |  | ✓ |
| RED 50.8×2.1 | 1.65 | 5.7 | 7.6 | 2282 | sí | ✓ |
| RED 50.8×3.2 | 2.46 | 8.2 | 11.1 | 3325 |  | ✓ |
| RED 57.2×3.2 | 2.79 | 10.6 | 14.3 | 4278 | sí | ✓ |

La elegida colapsa a **7.6 kN** (1.69× la intermedia) y cede a 5.7 kN; cubre 56% del pico, el resto lo toman piel con espuma, sillín y chasis (**no medido**: falta un ensayo).
Reacción en cada placa de cierre al colapso: 3.8 kN; la placa de 3 mm con un perno M8 aguanta 14.4 kN al aplastamiento y 19.3 kN al cortante: **2 pernos M8 por placa**.
Aire entre el tubo y el borde exterior de la cubeta: 75 mm (se exigen 30).

Aproximaciones: viga biapoyada, flexión plástica rígido-plástica sin efecto membrana (conservador), sin interacción con la piel.

## 3. Salida de emergencia (volcadura)
Un gull-wing no abre si el carro queda sobre el techo: se resuelve con **tres acciones desde adentro y a mano**, sin pirotecnia ni piezas nuevas que mantener:
1. **Manija roja de emergencia** en el larguero del techo, junto a cada hombro: libera los cierres (cable de acero, un solo jalón).
2. **Pasadores de bisagra de extracción rápida** (pasador de bolas Ø10 con aro y cordón rojo): al jalarlos la puerta queda libre y se empuja hacia afuera. Son los mismos pasadores que se sacan para **desmontar la puerta en 1 minuto** al dar servicio.
3. El amortiguador de gas lleva rótulas con clip de liberación, así que no ata la puerta.

Alcance del hombro al perno de bisagra (con arnés puesto el alcance cómodo es 0.50–0.55 m):

| Estatura | Bisagra | Distancia |
|---|---|---|
| 1.60 m | bisagra 1 | 0.46 m |
| 1.60 m | bisagra 2 | 0.48 m |
| 1.75 m | bisagra 1 | 0.48 m |
| 1.75 m | bisagra 2 | 0.43 m |
| 1.77 m | bisagra 1 | 0.49 m |
| 1.77 m | bisagra 2 | 0.43 m |

## 4. Retención y respaldos
- **Cierres con segunda posición de seguridad** (cerrojo primario y secundario): de pestillo de puerta de auto de deshuesadero, que ya trae las dos etapas. 4 puntos de cierre; con **2 de 4** basta para retener la puerta.
- **Varilla de apoyo** (varilla de acero Ø8 con clip, guardada en el larguero del techo): respalda al amortiguador de gas. Se usa para trabajar bajo la puerta y si el amortiguador pierde presión.
- **Sensor de puerta** (interruptor magnético tipo reed por puerta, ~$1): lo lee la tablet; avisa «puerta abierta» e **inhibe el par de los motores** con la puerta mal cerrada.
- **Pasadores de bisagra en doble cortante**: Ø10 acero 8.8 aguanta ~75 kN; las cargas de abuso (LC7) son de 1.3 kN.

## 5. Efecto en el diseño
- Masa de diseño de la puerta: de 12.0 a **13.5 kg** (viga ≈ 1.7 kg, aros y gancho ≈ 0.7 kg; el travesaño del esqueleto desaparece). Eso agrega ~3 kg al carro.
- Amortiguador de gas: **500 N** (catálogo). Esfuerzo en la manija al empezar a abrir: +88 N.
- Armado y mantenimiento no cambian: la viga se suelda a las mismas placas de cierre antes de laminar la piel; pasadores y cierres son piezas estándar atornilladas.

## 6. Pendiente de comprobar en el carro
- La posición real de la viga se fija al modelar la puerta contra el vano (z de la cara interior de la puerta); debe quedar ≥ 30 mm del borde exterior de la cubeta.
- Un ensayo estático de empuje sobre la puerta terminada (con gato y celda de carga) para verificar los 4.5 kN a 300 mm.
