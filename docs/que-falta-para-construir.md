# ¿Qué falta para tener todo lo necesario? — inventario de huecos

**2026-07-06** · complementa el documento maestro (`2026-07-05-carro-electrico-design.md`).
Regla de lectura: ✅ resuelto · 🟡 parcial (existe pero no está listo para construir) · ❌ falta por completo.

## 1. Estado por sistema

| Sistema | Estado | Qué existe | Qué falta para construir |
|---|---|---|---|
| Concepto y arquitectura | ✅ | Doc maestro v1.0, todas las decisiones validadas | — |
| Chasis (estructura) | 🟡 | FEM de vigas (10,868 N·m/°, FS ok), lista de corte 73 tubos, 3 DXF de cartelas, 5 nodos generativos STL, ensamble 3D | FEM formal de validación, jig de soldadura, secuencia de soldadura, decisión nodos impresos vs cartelas |
| Suspensión delantera | ✅ 2026-07-06 | Geometría completa con cinemática 3D (`calculos/resultados-suspension-delantera.md`): camber −1°, caster 4.9°, bump steer 0.04°/25mm, resorte 270 lb/in, largos de brazos | Comprar donantes (mangueta ATV, cremallera) y fabricar brazos |
| Suspensión trasera | ✅ 2026-07-06 | Brazo tirado resuelto (`calculos/resultados-suspension-trasera.md`): PTR 70×50×4 FS 2.4, MR 0.68, resorte 351 lb/in, anti-squat 258% documentado, rin resuelto (QS273 versión carro 14", 175/70R14) | Compras |
| Placa de torque QS273 | ✅ 2026-08-04 | Sándwich de 2 placas por rueda por optimización topológica (`calculos/resultados-placa-torque.md`): 0.69 + 0.58 kg, FS 2.3/2.8, ménsula de caliper integrada, doblador del cubo. 3 DXF de corte listos | Confirmar cotas del eje con QS Motor y cortar |
| Dirección | ✅ 2026-08-04 | Geometría resuelta (`calculos/resultados-direccion.md`): Ackermann +42%→+87% moviendo solo la cremallera a x=370/z=504, bump steer mejora a 0.028°/25mm, 2.4 vueltas, 13:1, giro 9.9 m, 34 N de volante parado | Donante exacto (medir su carrera y avance por vuelta) y columna |
| Frenos | ✅ 2026-08-04 | Dimensionado completo (`calculos/resultados-frenos.md`): reparto 57/43, disco Ø220 ×4, pistones 938/740 mm², bombas Ø14.3 con pedal 6:1 → 428 N para 1g, térmico, límite de regen y freno de mano | Conseguir donantes y **limitar el regen a 0.24g en los controladores** (seguridad, F3) |
| Batería (pack) | 🟡 | Spec de celdas y BMS, placa de cuna DXF, cuna en el frame | Diseño de la caja completa (arreglo 30S, busbars, compresión, venteo), plano de armado con técnico |
| Eléctrico HV + 12V | ❌ | Lista conceptual de componentes | Diagrama unifilar completo, calibres de cable, lista de conectores, layout en la nariz |
| Carrocería | 🟡 | Concepto 3D v2 (visor), método definido, 10 paneles decididos | CAD final de superficie, corte en paneles, archivos CNC de espuma, anclajes Dzus, diseño de puerta mariposa (bisagra/pistón/cerrojo), spec exacta del parabrisas |
| Cabina/interior | 🟡 | Posición de manejo validada (maniquí 1.75 m, cabeza −5 cm del arco), barra de cinturones en frame | Butacas donantes, pedalera, volante/columna, montaje de tablet |
| Térmico | ❌ | — | Verificación térmica de motores y controladores a 8 kW sostenidos; ventilación de la nariz |
| BOM / compras | ❌ | Presupuesto por sistema | Lista de compra ítem por ítem con specs de pedido y 3 cotizaciones (motores y celdas = tiempo de entrega largo, pedir primero) |
| Herramientas | ❌ | Presupuesto (~$12 mil) | Comprar: soldadora MIG, esmeril, tronzadora, taladro, torquímetro, multímetro CAT III, herramienta aislada |
| Habilidades | 🟡 | Plan de aprendizaje en el doc | Práctica de soldadura (jig de prueba), práctica de fibra (panel difusor), curso/lectura seguridad HV |

## 2. Lo que podemos producir nosotros en sesiones (ingeniería pendiente)

En orden de dependencia — cada uno es un entregable concreto tipo los que ya hicimos:

1. ~~**Suspensión delantera**~~ ✅ hecho 2026-07-06 (`calculos/suspension_delantera.py`).
2. ~~**Suspensión trasera**~~ ✅ hecho 2026-07-06 (`calculos/suspension_trasera.py`). Rin resuelto: QS273 versión rin de carro 14" — confirmar por escrito con QS Motor al cotizar. *Bloquea F1.*
3. ~~**Placa de torque del QS273**~~ ✅ hecho 2026-08-04 (`calculos/placa_torque.py`). Sándwich de 2 placas de acero 8 mm por rueda, corte láser, con la ménsula del caliper integrada. Falta confirmar con QS Motor el Ø del eje, la entrecaras de los planos y **el largo del eje libre del lado interior (≥78 mm)** antes de cortar.
4. ~~**Cálculo de frenos**~~ ✅ hecho 2026-08-04 (`calculos/frenos.py`). Hallazgo: el freno del donante ATV **no alcanza** — se reusa mangueta y maza pero con disco de Ø220 y caliper mayor. Y el regen hay que limitarlo a 0.24g o el trasero se bloquea en mojado.
5. ~~**Dirección**~~ ✅ hecho 2026-08-04 (`calculos/direccion.py`). El Ackermann heredado era de solo +42%; se corrige a +87% **moviendo la cremallera 40 mm**, sin tocar la mangueta del donante ni fabricar ninguna pieza. La altura de la cremallera (207 mm) sigue sin tocarse.
6. **BOM maestro** — hoja con cada pieza, spec exacta de pedido (ej. "BMS 30S LiFePO4 300A continuo con Bluetooth"), proveedor candidato y precio. *Cierra F0: sin esto no se puede pedir nada.* **Ahora es el camino crítico** — sin él no se pueden pedir motores ni celdas, que son las entregas más largas.
7. **Diagrama eléctrico HV + 12V** — unifilar completo con calibres y protecciones. *Bloquea F2.*
8. **Caja de batería** — CAD del arreglo 30S con compresión y montaje a la cuna. *Bloquea F2.*
9. **Jig de soldadura + secuencia** — plano de la mesa de armado y orden de soldeo anti-distorsión. *Bloquea F1.*
10. **FEM formal del chasis** — modelo de validación independiente (FreeCAD FEM) como marca el doc maestro. *Bloquea F1 (obligatorio antes de soldar).*
11. **Carrocería CAD final** — superficie definitiva → corte en 10 paneles → archivos de rebanado CNC. *Bloquea F4 (puede ir en paralelo desde F1).*

## 3. Lo que solo se resuelve fuera (dinero, terceros, tiempo)

- **Pedidos largos:** kit 2× QS273 + controladores; 30 celdas LiFePO4 105 Ah + BMS. Semanas de entrega — pedir apenas cierre el BOM.
- **Terceros:** soldador experimentado (inspección + arcos críticos), técnico para BMS y primera energización, corte láser de cartelas, CNC de espuma (F4).
- **Donantes de deshuesadero:** cremallera, columna, manguetas ATV/compacto, butacas, bombas de freno.
- **Taller:** espacio techado con 110/220V donde soldar y armar — requisito previo a F1.

## 4. Decisiones abiertas (se deciden sobre la marcha)

1. Color/wrap (F5).
2. Proveedor final de celdas y kit motor (al cotizar el BOM).
3. Limpiaparabrisas: hidrofóbico vs brazo manual (probar en F3).
4. Donantes exactos según deshuesadero local.
5. **Nueva (2026-07-06):** piso a 160 mm vs bajarlo a ~120 mm (más deportivo, cambio menor de suspensión) — decidir al diseñar la suspensión (punto 2.1).
6. **Nueva (2026-07-06):** cabina de 1.16 m interior (apretada tipo Atom) vs ensanchar el frame a ~1.4 m (re-correr FEM + nodos + lista de corte, ~1 sesión).

## 5. Resumen ejecutivo

**El diseño conceptual y el chasis están resueltos; falta la ingeniería de detalle de todo lo que se atornilla al chasis.** El camino crítico es: suspensión → frenos/dirección → BOM → pedir motores y celdas (lo más tardado) → jig + FEM formal → empezar a soldar F1. Nada de la carrocería urge todavía: el carro debe funcionar feo antes de ser bonito.
