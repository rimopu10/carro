# ¿Qué falta para tener todo lo necesario? — inventario de huecos

## ⛔ BLOQUEANTES ENCONTRADOS EN LA REVISIÓN DEL 2026-08-05

Cuatro revisiones cruzadas (coherencia entre documentos, realismo del 3D, armabilidad
y rigor de los cálculos) encontraron esto. **Nada de acero se corta hasta cerrarlos.**

| # | Qué | Estado |
|---|---|---|
| B1 | **El tie rod choca con el larguero inferior del chasis.** La rótula de la cremallera queda dentro del tubo. Se barrieron 1561 posiciones libres: la mejor da bump steer de 2.7°/25 mm contra un tope de 0.10. No se arregla moviendo la cremallera — hay que **bajar los pivotes de la horquilla inferior a ménsulas**. Ver §0 de `resultados-direccion.md` | ❌ ABIERTO |
| B2 | **Los pivotes de la horquilla inferior caen DENTRO de los nodos del chasis** (`LA1`=`fb_lo`, `LA2`=`fx_lo`): el buje no cabe. Necesitan ménsula con offset, igual que los superiores (63 mm) — y eso re-abre toda la cinemática delantera | ❌ ABIERTO |
| B3 | **El aplastamiento en los planos del eje del QS273 estaba mal calculado** (brazo de palanca a través del eje en vez de a lo largo del plano). La fuerza real es el doble: 43.7 kN. El doblador pasa de 8 a **22 mm** para llegar a FS 2.1 | ✅ CORREGIDO |
| B4 | **El FEM del chasis aplicaba 325 kg de los 564 kg suspendidos** — le faltaba el peso propio del frame y el resto del carro. Corregido repartiendo el faltante por nodo. FS baja de 2.14 a **2.05** (sigue ≥2) y la optimización de secciones sobrevive | ✅ CORREGIDO |
| B5 | **El coilover delantero atravesaba la horquilla superior** (2.6 mm entre ejes, hacen falta 57). Anclaje movido a (700,480,480): 62 mm de holgura, motion ratio intacto | ✅ CORREGIDO |
| B6 | **El coilover trasero se anclaba 94 mm fuera del brazo y 47 mm dentro de la llanta.** Corregido sobre el eje del brazo: el resorte pasa de **351 a 292 lb/in** y el amortiguador de ~590 a ~540 mm | ✅ CORREGIDO |
| B7 | **La lista de corte no es una lista de corte**: da longitud entre centros de nodo, sin ángulos de inglete ni destajes. No se pueden cortar los 73 tubos con ella | ❌ ABIERTO |
| B8 | **El arco principal son 5 tubos rectos, no un arco rolado** — con una soldadura a tope justo donde se anclan los arneses. Y el FEM no tiene caso de volcadura ni de choque | ❌ ABIERTO |
| B9 | **No hay plano de ninguna pieza que se fabrica** (brazos, ménsulas, camisas, pedalera) ni cotas de posición de las ménsulas al chasis | ❌ ABIERTO |

Se agregó `calculos/holguras.py`, que detecta interferencias entre piezas móviles y
contra los tubos del chasis. **Correrlo después de mover cualquier punto duro.**

---


**2026-07-06** · complementa el documento maestro (`2026-07-05-carro-electrico-design.md`).
Regla de lectura: ✅ resuelto · 🟡 parcial (existe pero no está listo para construir) · ❌ falta por completo.

## 1. Estado por sistema

| Sistema | Estado | Qué existe | Qué falta para construir |
|---|---|---|---|
| Concepto y arquitectura | ✅ | Doc maestro v1.0, todas las decisiones validadas | — |
| Chasis (estructura) | 🟡 | FEM de vigas, lista de corte 73 tubos, 3 DXF de cartelas, 5 nodos generativos STL. **Secciones optimizadas 2026-08-04: 90.5 → 81.0 kg** (`resultados-optimizacion-chasis.md`), 10,032 N·m/° y FS 2.14 | FEM formal de validación, jig de soldadura, secuencia de soldadura, decisión nodos impresos vs cartelas |
| Modelo 3D del carro completo | ✅ 2026-08-05 | `carro-completo-3d.html` (se regenera con `calculos/exportar_carro_3d.py`): **248 piezas con geometría de mecanismo real** — resortes helicoidales, rines con rayos, discos barrenados, y las piezas de lámina extruidas **desde su propio DXF de corte**. Explorador por sistema, armado en 7 pasos con lista de verificación y pares de apriete, vista explotada según dirección de montaje, clic para inspeccionar | — |
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
| BOM / compras | ✅ 2026-08-04 | `docs/bom-maestro.md` + `.csv`: 47 renglones con spec exacta de pedido, cantidad, entrega y fuente; acero derivado de la lista de corte real; orden de compra por tiempo de entrega | Pedir 3 cotizaciones de los renglones grandes y **cerrar la lista de confirmaciones con QS Motor antes de pagar** |
| Herramientas | ❌ | Presupuesto (~$12 mil) | Comprar: soldadora MIG, esmeril, tronzadora, taladro, torquímetro, multímetro CAT III, herramienta aislada |
| Habilidades | 🟡 | Plan de aprendizaje en el doc | Práctica de soldadura (jig de prueba), práctica de fibra (panel difusor), curso/lectura seguridad HV |

## 2. Lo que podemos producir nosotros en sesiones (ingeniería pendiente)

En orden de dependencia — cada uno es un entregable concreto tipo los que ya hicimos:

1. ~~**Suspensión delantera**~~ ✅ hecho 2026-07-06 (`calculos/suspension_delantera.py`).
2. ~~**Suspensión trasera**~~ ✅ hecho 2026-07-06 (`calculos/suspension_trasera.py`). Rin resuelto: QS273 versión rin de carro 14" — confirmar por escrito con QS Motor al cotizar. *Bloquea F1.*
3. ~~**Placa de torque del QS273**~~ ✅ hecho 2026-08-04 (`calculos/placa_torque.py`). Sándwich de 2 placas de acero 8 mm por rueda, corte láser, con la ménsula del caliper integrada. Falta confirmar con QS Motor el Ø del eje, la entrecaras de los planos y **el largo del eje libre del lado interior (≥78 mm)** antes de cortar.
4. ~~**Cálculo de frenos**~~ ✅ hecho 2026-08-04 (`calculos/frenos.py`). Hallazgo: el freno del donante ATV **no alcanza** — se reusa mangueta y maza pero con disco de Ø220 y caliper mayor. Y el regen hay que limitarlo a 0.24g o el trasero se bloquea en mojado.
5. ~~**Dirección**~~ ✅ hecho 2026-08-04 (`calculos/direccion.py`). El Ackermann heredado era de solo +42%; se corrige a +87% **moviendo la cremallera 40 mm**, sin tocar la mangueta del donante ni fabricar ninguna pieza. La altura de la cremallera (207 mm) sigue sin tocarse.
6. ~~**BOM maestro**~~ ✅ hecho 2026-08-04 (`calculos/bom.py` → `docs/bom-maestro.md` y `.csv`). **Ya se pueden pedir motores y celdas**, que son las entregas largas — antes hay que cerrar la lista de confirmaciones con QS Motor (§5 del BOM). Hallazgo: el BOM detallado sale ~$190-309 mil contra los $143-219 mil estimados, empujado por los frenos (el donante ATV no alcanzaba).
7. **Diagrama eléctrico HV + 12V** — unifilar completo con calibres y protecciones. *Bloquea F2.* **Ahora es el camino crítico de ingeniería**: es lo único que impide cotizar y pedir el cableado.
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
