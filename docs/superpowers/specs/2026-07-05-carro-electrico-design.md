# Proyecto CARRO — Deportivo eléctrico artesanal 2 plazas

**Documento maestro de diseño · 2026-07-05 · v1.0**

---

## 1. Visión y filosofía

Carro deportivo eléctrico de construcción artesanal con tres mandamientos:

1. **Mínimas piezas que fallen** — se elimina de raíz todo lo que en un carro normal se descompone: motor de combustión, transmisión, clutch, diferencial, radiador, bomba de agua, batería de 12V, elevadores eléctricos, aire acondicionado.
2. **Todo reparable rápido y barato por su dueño** — panel dañado se re-fabrica por su archivo CAD; pieza rota se reimprime en 3D; sistema modular con conectores; tornillería estandarizada.
3. **Look de revista** — proporciones de superdeportivo de motor central, estilo **BMW i8 × Alfa Romeo 33 Stradale**, logrado con métodos que perdonan al constructor novato (wrap satinado, ranuras intencionales, firma de luz LED).

Uso: terreno privado y calles tipo México (topes) — no requiere legalización. Constructor: aprenderá todas las habilidades necesarias sobre la marcha; el diseño está pensado para eso.

## 2. Especificaciones objetivo

| Parámetro | Valor |
|---|---|
| Configuración | 2 plazas lado a lado, cabina cerrada, puertas mariposa |
| Dimensiones | 3.20 m largo × 1.65 m ancho × ~1.30 m alto |
| Distancia entre ejes / altura libre | 2.10 m / 16 cm |
| Peso objetivo | 500-550 kg (con batería) |
| Propulsión | 2 × motor de cubo QS273 8 kW (trasera), 96V |
| Par / velocidad máx | ~700 N·m combinados al piso / 100-110 km/h |
| Batería | LiFePO4 96V ~105Ah (10 kWh), 30 celdas prismáticas + BMS 250-300A |
| Autonomía / carga | 80-100 km / enchufe doméstico nocturno |
| Frenos | Disco hidráulico ×4, doble bomba con balance, sin booster + regen |
| Chasis | Space frame PTR 38×38 cal.14 + arcos RED 44.5×2.1 (90.5 kg, 73 tubos) |
| Rigidez torsional (calculada) | 10,868 N·m/° (excelente; kit cars: 2,000-6,000) |
| Carrocería | Sándwich fibra de vidrio/espuma EPS, 10 paneles independientes |
| Presupuesto | $143-219 mil MXN (realista ~$165 mil) + herramientas ~$12 mil |

## 3. Decisiones de arquitectura (todas validadas con el dueño)

| # | Decisión | Elección | Por qué |
|---|---|---|---|
| 1 | Tipo | Carro real manejable, terreno privado | Sin trámites; libertad de diseño |
| 2 | Plazas | 2 lado a lado | Formato deportivo clásico, compartible |
| 3 | Motor | Eléctrico, 2× cubo QS273 96V | ~20 piezas móviles vs ~2,000; cero transmisión |
| 4 | Batería | LiFePO4, celdas+BMS armado con técnico (camino 2.5) | Química más segura, 10-15 años, ahorro 25%, aprende el sistema |
| 5 | Posición batería | Central-trasera baja (no piso tipo Tesla) | Proporciones Ferrari gratis; celdas prismáticas no sirven para piso plano; mismo CG bajo |
| 6 | Balance de peso | Controladores/cargador/DC-DC en la nariz | Corrige sesgo trasero a ~38/62 |
| 7 | Cabina | Cerrada con puertas mariposa simplificadas | Sin mecanismos: vidrio fijo/corredera manual, pistón de gas, cerrojo mecánico |
| 8 | Estilo | Curvas — i8 × 33 Stradale | Elección del dueño; burbuja + caderas + contrafuertes flotantes |
| 9 | Carrocería | "Digital": CAD→rebanadas→CNC espuma→fibra sándwich→wrap | Las curvas las hace la máquina; sándwich = rígido, aislante, sin retumbar |
| 10 | Paneles | 10 independientes, Dzus + insertos, 1 conector eléctrico c/u | Panel chocado = panel re-fabricado ($1-3 mil); wrap por panel |
| 11 | Chasis | Space frame por caminos de carga (ver §5) | Optimización topológica aplicada a tubos soldables |
| 12 | Color | **PENDIENTE** — se decide al final (wrap permite cambiarlo) | Wrap satinado recomendado: perdona imperfecciones |

**Mejoras "fuera de serie" incluidas:** sin batería 12V (DC-DC del pack), regen como freno de diario, tablet como tablero, techo doble piel + extractor solar (sin A/C), cola clamshell de una pieza, cámara en vez de medallón trasero, nariz sellada + barra LED tras policarbonato ahumado, piso plano (undertray), biblioteca CAD de refacciones. **Rechazada:** asientos fijos moldeados (se usan butacas comerciales atornilladas). **Opcional futuro:** panel solar flexible laminado.

## 4. Estilo exterior — lenguaje i8 × 33 Stradale

- **Del 33 Stradale:** burbuja de cristal envolvente, caderas voluptuosas sobre las 4 ruedas, aros de luz redondos traseros, puertas mariposa.
- **Del i8:** contrafuertes flotantes techo→cadera, cejas LED frontales, tomas esculpidas, capa técnica negra inferior.
- **Trucos de acabado:** ranuras entre paneles marcadas a propósito (shadow lines), wrap satinado, zona baja negra mate, gaps uniformados con separadores impresos 3D de 5 mm, firma de luz continua adelante y atrás.
- Modelo 3D iterable: `\.superpowers\brainstorm\...\modelo-3d-v2.html` (visor) · exportable a OBJ para Blender/Fusion.

## 5. Estructura — chasis space frame

Diseñado por caminos de carga (principio del diseño generativo aplicado a tubos):
tubos rojos = suspensión, amarillos = célula de seguridad (2 arcos + pilares + barra
de cinturones), azules = diagonales anti-torsión, verdes = cuna de batería.
PTR cuadrado 38mm (fácil de cortar/soldar para novato); arcos en tubo redondo.

**Análisis estructural real** (método de rigidez directa, vigas 3D — `calculos/analisis_chasis.py`):

| Caso | Resultado | Criterio |
|---|---|---|
| Rigidez torsional | **10,868 N·m/°** | >4,000 deseable ✓ |
| Bache 3g | FS mín **2.22** (estribo bajo asiento) | >2.0 ✓ |
| Frenada 1g | FS mín **4.65** | ✓ |
| Curva lateral 1g | FS mín **3.19** | ✓ |

Nota de diseño: el tubo crítico es el estribo en el tramo del asiento — el asiento real
repartirá su carga en un travesaño dedicado (mejora el FS). **Obligatorio antes de soldar:**
validación FEM 3D formal (FreeCAD FEM o Altair Inspire student) + revisión por soldador
con experiencia estructural. Piezas de placa optimizadas topológicamente y cortadas a
láser: `planos/*.dxf`. Lista de corte completa: `planos/lista-corte-tubos.csv` (41.9 m).

## 6. Sistemas

- **Propulsión:** kit dual QS273 8kW 96V + 2 controladores (APT96600/Fardriver ND96530 o equiv.) con regen configurable; selector F/N/R por switch; acelerador de pedal tipo hall.
- **Batería:** 30 × celda prismática LiFePO4 105Ah (EVE/CATL) en serie (96V nom), BMS 30S **250-300A descarga** (especificación crítica para no capar los motores) con Bluetooth; caja de acero con compresión, en cuna entre ejes; contactor principal + fusible 400A + precarga + paro de emergencia + desconectador de servicio.
- **Energía auxiliar:** DC-DC 96→12V 30A aislado (sin batería 12V); cargador LiFePO4 96V 15-18A enchufable a 120V.
- **Rodaje:** horquillas dobles delanteras (tubo + rótulas), manguetas/frenos ATV 300 adelante; brazos tirados traseros con los motores de cubo; 4 coilovers UTV calidad media; cremallera manual de compacto; llantas 175/70R13 (perfil alto absorbe topes — compensa masa no suspendida de los motores de cubo).
- **Cabina:** 2 butacas comerciales atornilladas, cinturones 4 puntos, tablet Android (velocímetro GPS + BMS + controladores por BT), parabrisas laminado plano/semi de buggy, laterales policarbonato corredizo manual.
- **Luces:** barra LED frontal tras policarbonato ahumado, cejas LED, aros + línea LED trasera, intermitentes, cámara trasera con pantalla.

## 7. Seguridad

1. **Estructural:** 2 arcos (delantero y principal) de tubo redondo unidos por rieles de techo — célula completa; diagonal de puerta contra impacto lateral; nariz = zona de deformación.
2. **Eléctrica (96V = ~109V cargada, SÍ es peligrosa):** contactor + fusible principal + precarga + E-stop al alcance del piloto + desconectador de servicio; todo cable HV naranja y forrado; trabajo en batería solo con herramienta aislada, sin joyería, y los 2 pasos críticos (BMS + primera energización) con técnico.
3. **Operativa:** cinturones 4 puntos; extintor ABC a bordo; freno mecánico independiente del regen (doble circuito con balance); pruebas por etapas obligatorias (ver fases).
4. **Química:** LiFePO4 específicamente por no entrar en fuga térmica con abuso mecánico/eléctrico típico.

## 8. Fases de construcción (con criterios de salida)

| Fase | Contenido | Sale cuando... |
|---|---|---|
| **F0 Diseño fino** | CAD 3D final carrocería + chasis; FEM formal; pedidos largos (motores, celdas) | FEM aprobado; kit motor y celdas pedidos |
| **F1 Chasis rodante** | Soldar frame; suspensión, dirección, frenos; ruedas | Rueda empujado, frena, dirige; soldaduras inspeccionadas |
| **F2 Tren eléctrico** | Batería (con técnico), controladores en nariz, cableado HV+12V | "Mula" anda sola en patio a <20 km/h |
| **F3 Pruebas** | 200 km de pruebas incrementales solo el piloto, terreno privado | Sin fallas térmicas/mecánicas; frenos y regen calibrados |
| **F4 Carrocería** | Espuma CNC, fibra sándwich, corte de paneles, montaje con separadores | 10 paneles montados con gaps uniformes |
| **F5 Acabado** | Resane, wrap, luces, detalles 3D, interior | Foto de revista 📸 |

Regla de oro: **el carro debe funcionar feo antes de ser bonito** — toda la mecánica se
prueba en F2-F3 con el chasis desnudo, cuando todo está accesible.

## 9. Presupuesto resumen (MXN)

| Sistema | Rango |
|---|---|
| Estructura acero | $7,200-11,000 |
| Rodaje | $20,300-33,500 |
| Propulsión | $38,700-53,700 |
| Batería | $35,000-49,000 |
| Carrocería digital | $21,000-36,000 |
| Cabina y vidrios | $14,400-24,100 |
| Luces y acabados | $7,000-12,000 |
| **Total** | **$143,000-219,000** (realista ~$165 mil) |
| Herramientas (si parte de cero, una vez) | ~$10,000-15,000 |

Ahorros sin traicionar filosofía: deshuesadero (cremallera, columna, rines, butacas);
wrap puede esperar a F5. **Nunca recortar:** BMS, frenos, coilovers, cinturones, fusible.

## 10. Riesgos y mitigaciones

| Riesgo | Mitigación |
|---|---|
| BMS insuficiente capa la potencia | Especificar 250-300A por escrito al comprar |
| Golpes de tope dañan motores de cubo (masa no suspendida) | Llanta perfil 70 + coilovers de calidad + 16 cm libres; ruta de migración a motor central preservada en el chasis |
| Sesgo de peso trasero | Electrónica de potencia en nariz (decidido) |
| Fibra primera vez con mal acabado | El wrap satinado perdona; práctica previa en el panel más pequeño (difusor) |
| Soldaduras de novato en estructura | Practicar en jig de prueba; inspección por soldador experimentado antes de F2; arcos críticos soldables por profesional local ($) |
| Presupuesto se estira | Construcción por fases F1→F5, el carro es usable desde F3 |

## 11. Archivos del proyecto

```
carro/
├── docs/superpowers/specs/2026-07-05-carro-electrico-design.md  ← este documento
├── calculos/analisis_chasis.py        FEM de vigas 3D del chasis (correr: python)
├── calculos/resultados-analisis.md    Informe de esfuerzos y FS
├── planos/lista-corte-tubos.csv       73 tubos con longitudes y coordenadas
├── planos/generar_dxf.py              Generador de placas láser
├── planos/*.dxf                       Cartelas y placas para corte láser
├── cad/                               (F0: modelos finales)
└── .superpowers/brainstorm/           Visores 3D interactivos y pantallas del diseño
```

## 12. Decisiones abiertas

1. **Color/wrap** — el dueño decide en F5 (recomendación: satinado).
2. Proveedor final de celdas y kit motor (cotizar 3 en F0).
3. Limpiaparabrisas: tratamiento hidrofóbico vs brazo manual (probar en F3).
4. Donante exacto de cremallera y manguetas (según disponibilidad de deshuesadero local).
