# ¿Qué falta para tener todo lo necesario? — inventario de huecos

**2026-07-06** · complementa el documento maestro (`2026-07-05-carro-electrico-design.md`).
Regla de lectura: ✅ resuelto · 🟡 parcial (existe pero no está listo para construir) · ❌ falta por completo.

## 1. Estado por sistema

| Sistema | Estado | Qué existe | Qué falta para construir |
|---|---|---|---|
| Concepto y arquitectura | ✅ | Doc maestro v1.0, todas las decisiones validadas | — |
| Chasis (estructura) | 🟡 | FEM de vigas (10,868 N·m/°, FS ok), lista de corte 73 tubos, 3 DXF de cartelas, 5 nodos generativos STL, ensamble 3D | FEM formal de validación, jig de soldadura, secuencia de soldadura, decisión nodos impresos vs cartelas |
| Suspensión delantera | ❌ | Solo los puntos de anclaje en el frame | Geometría completa (camber/caster/kingpin/Ackermann), diseño de horquillas, mangueta donante especificada, spec de coilovers (carrera, tarado, motion ratio) |
| Suspensión trasera | ❌ | Puntos de anclaje + cartela de pivote | Diseño del brazo tirado, placa de torque QS273, spec de coilovers traseros |
| Dirección | ❌ | Decisión: cremallera manual de compacto | Donante exacto, geometría (bump steer, Ackermann), columna y montaje |
| Frenos | ❌ | Decisión: disco ×4, doble bomba | Cálculo de frenado (650 kg, 1g), selección discos/calipers/bombas, pedalera, balance F/R |
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

1. **Suspensión delantera** — geometría en código (como el FEM): puntos duros, curvas de camber, largo de horquillas, spec de rótulas y coilover. *Bloquea F1.*
2. **Suspensión trasera** — brazo tirado + **placa de torque del QS273** (candidata ideal para el optimizador generativo, escala de pieza de dron). *Bloquea F1.*
3. **Cálculo de frenos** — dimensionado real y lista de partes con donantes. *Bloquea F1.*
4. **Dirección** — geometría Ackermann + verificación de bump steer con la suspensión ya definida. *Bloquea F1.*
5. **BOM maestro** — hoja con cada pieza, spec exacta de pedido (ej. "BMS 30S LiFePO4 300A continuo con Bluetooth"), proveedor candidato y precio. *Cierra F0: sin esto no se puede pedir nada.*
6. **Diagrama eléctrico HV + 12V** — unifilar completo con calibres y protecciones. *Bloquea F2.*
7. **Caja de batería** — CAD del arreglo 30S con compresión y montaje a la cuna. *Bloquea F2.*
8. **Jig de soldadura + secuencia** — plano de la mesa de armado y orden de soldeo anti-distorsión. *Bloquea F1.*
9. **FEM formal del chasis** — modelo de validación independiente (FreeCAD FEM) como marca el doc maestro. *Bloquea F1 (obligatorio antes de soldar).*
10. **Carrocería CAD final** — superficie definitiva → corte en 10 paneles → archivos de rebanado CNC. *Bloquea F4 (puede ir en paralelo desde F1).*

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
