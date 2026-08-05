# Optimización de secciones del chasis — el mismo carro, más ligero

Generado por `optimizar_chasis.py`. Reusa la geometría, el FEM de vigas 3D y los casos de carga que ya estaban validados en `analisis_chasis.py`: **no se movió ni un nodo**, solo qué tubo va en cada lugar.

## Por qué había masa que quitar

El chasis usa una sola sección para casi todo. De los 73 tubos, solo uno está al límite — el peor da FS **2.22** en bache 3g. Los otros 72 van sobrados, algunos muchísimo. Poner el mismo tubo en todos lados es cómodo para comprar, pero se paga en kilos.

La optimización agrupa los tubos **por función** (no uno por uno: un chasis con 73 secciones distintas sería imposible de comprar y de armar) y le busca a cada grupo la sección más ligera del catálogo que siga cumpliendo todo.

## Restricciones que NO se negocian

- **FS ≥ 2.0 a fluencia** en los 3 casos de carga (bache 3g, frenada 1g, curva 1g).
- **FS ≥ 2.0 a pandeo de Euler** en cada tubo comprimido.
- Solo secciones de catálogo que de verdad se consiguen.
- **Pisos por grupo que el optimizador no puede cruzar.** La regla: *un tubo no se optimiza contra un análisis que no incluye el caso que lo hace importante*. Este FEM tiene bache, frenada y curva — **no tiene volcadura ni choque**:

  - Célula de seguridad (arcos, pilar A, techo): no baja de **RED 44.5x2.1**
  - Barra de cinturones: no baja de **PTR 38x38x1.9**
  - Cuna de batería: no baja de **PTR 32x32x1.9**

  Sin estos pisos el optimizador bajaba la barra de cinturones a PTR 25×25×1.5 — y ahí es donde tiran los arneses en un impacto. El FEM lo permitía porque no tiene ese caso de carga; el criterio de ingeniería no.

## El intercambio: rigidez torsional vs masa

El diseño actual da **10,868 N·m/°**, cuando el doc maestro pide >4,000 para un deportivo ligero artesanal y un kit car típico anda entre 2,000 y 6,000. O sea: hay rigidez de sobra, y sobra es masa. Bajar el piso es un intercambio legítimo, así que se barrió:

| Piso de rigidez | Masa | vs actual | FS mínimo | Rigidez real | |
|---|---|---|---|---|---|
| 4,000 N·m/° | 77.5 kg | **-13.0 kg** | 2.13 | 9,559 N·m/° |  |
| 6,000 N·m/° | 77.5 kg | **-13.0 kg** | 2.13 | 9,559 N·m/° |  |
| 8,000 N·m/° | 77.5 kg | **-13.0 kg** | 2.13 | 9,559 N·m/° | ✓ **recomendado** |
| 10,000 N·m/° | 80.6 kg | **-9.9 kg** | 2.16 | 10,068 N·m/° |  |
| 10,868 N·m/° | 90.2 kg | **-0.3 kg** | 2.20 | 10,884 N·m/° |  |

Con el piso en 8,000 N·m/° el óptimo absoluto baja a **77.5 kg**. Pero ese óptimo usa 5 secciones distintas, y ahí aparece el segundo intercambio.

## El intercambio que de verdad importa: masa vs simplicidad

Un chasis con muchas secciones distintas pesa menos pero es más lío: más renglones que comprar, más pilas de tubo que no confundir en el taller y más oportunidades de soldar el tubo equivocado en el lugar equivocado. Se midió el precio en kilos de usar menos secciones:

| Secciones distintas | Masa | vs actual | FS | Rigidez | Cuáles |
|---|---|---|---|---|---|
| 2 | 90.5 kg | +0.0 kg | 2.22 | 10,868 N·m/° | PTR 38x38x1.9, RED 44.5x2.1 |
| 3 ✓ **elegido** | 81.0 kg | -9.5 kg | 2.14 | 10,032 N·m/° | PTR 25x25x1.5, PTR 38x38x1.9, RED 44.5x2.1 |
| 4 | 77.9 kg | -12.6 kg | 2.12 | 9,169 N·m/° | PTR 25x25x1.5, PTR 32x32x1.9, PTR 38x38x1.9, RED 44.5x2.1 |

**Elegido: 3 secciones.** Se lleva **9.5 kg de los 13.0 kg posibles (73% del beneficio) agregando UN solo tubo a la lista de compra**, y encima conserva casi toda la rigidez (10,032 contra 10,868 N·m/°). Las secciones 4 y 5 compran 3.5 kg más — no vale la pena para este proyecto.

## Qué tubo va en cada grupo

| Grupo | Largo total | Antes | Ahora | Δ masa |
|---|---|---|---|---|
| Estructura general (nariz, estribos, rieles) | 14.9 m | PTR 38x38x1.9 | **PTR 38x38x1.9** | sin cambio |
| Anclajes de suspensión | 5.4 m | PTR 38x38x1.9 | **PTR 38x38x1.9** | sin cambio |
| Diagonales de torsión (las X) | 9.0 m | PTR 38x38x1.9 | **PTR 25x25x1.5** | **-9.5 kg** |
| Barra de cinturones | 2.1 m | PTR 38x38x1.9 | **PTR 38x38x1.9** | sin cambio |
| Célula de seguridad (arcos, pilar A, techo) | 7.1 m | RED 44.5x2.1 | **RED 44.5x2.1** | sin cambio |
| Cuna de batería | 3.2 m | PTR 38x38x1.9 | **PTR 38x38x1.9** | sin cambio |

**Total: 90.5 kg → 81.0 kg (10% menos de acero estructural).** El único tubo nuevo en la lista de compra es el **PTR 25×25×1.5** de las diagonales.

## Verificación del diseño elegido

| | Actual | Optimizado |
|---|---|---|
| Masa de acero | 90.5 kg | **81.0 kg** |
| FS mínimo a fluencia | 2.22 | **2.14** |
| FS mínimo a pandeo | 63.6 | **14.9** |
| Rigidez torsional | 10,868 N·m/° | **10,032 N·m/°** |
| Secciones que comprar | 2 | **3** |

El tubo crítico del diseño optimizado es **seatR-mh_loR** (PTR 38x38x1.9) en Bache 3g, con FS 2.14 — el mismo tubo que ya era el crítico antes, así que el margen no se movió de sitio.

Los 10 tubos más esforzados del diseño optimizado:

| Caso | Tubo | Función | Sección | σ (MPa) | FS |
|---|---|---|---|---|---|
| Bache 3g | seatR-mh_loR | gen | PTR 38x38x1.9 | 117 | 2.14 |
| Bache 3g | dash_loR-seatR | gen | PTR 38x38x1.9 | 117 | 2.14 |
| Bache 3g | seatL-mh_loL | gen | PTR 38x38x1.9 | 117 | 2.14 |
| Bache 3g | dash_loL-seatL | gen | PTR 38x38x1.9 | 117 | 2.14 |
| Curva 1g | seatR-mh_loR | gen | PTR 38x38x1.9 | 83 | 3.02 |
| Curva 1g | dash_loR-seatR | gen | PTR 38x38x1.9 | 83 | 3.02 |
| Curva 1g | dash_loL-seatL | gen | PTR 38x38x1.9 | 80 | 3.11 |
| Curva 1g | seatL-mh_loL | gen | PTR 38x38x1.9 | 80 | 3.11 |
| Bache 3g | fx_hiR-dash_hiR | gen | PTR 38x38x1.9 | 78 | 3.20 |
| Bache 3g | fx_hiL-dash_hiL | gen | PTR 38x38x1.9 | 78 | 3.21 |

## Qué significa esto para el carro

**9.5 kg** de un carro de 690 kg es **1.4%** del peso total. No es dramático, y conviene decirlo así en vez de vendértelo como una transformación: es peso quitado del lugar correcto — acero estructural repartido por todo el chasis — sin tocar la seguridad ni la geometría de suspensión que ya estaba afinada.

Menos kilos arriba también significa un poco menos de todo lo demás: menos carga en resortes y frenos, un pelo más de autonomía. Nada de eso cambia el carro, pero va en la dirección correcta y sale gratis.

### Dos avisos de taller

1. **Las diagonales quedan en pared de 1.5 mm.** Eso perdona menos al soldar: es donde un novato perfora el tubo. Practicar específicamente en retazos de PTR 25×25×1.5 antes de tocar el chasis, con menos amperaje y cordones cortos. El resto del chasis sigue en 1.9 mm, que es mucho más noble.
2. **Son dos pilas de tubo cuadrado en el taller**, no una. Marcar los tramos con plumón desde que llegan: soldar una diagonal de 38 donde va una de 25 no se nota hasta que se pesa, pero al revés sí importa.

**Antes de cortar:** esto sigue siendo un análisis lineal estático que no incluye fatiga, abolladura local ni choque. El FEM formal de validación (punto 10 de `que-falta-para-construir.md`) es obligatorio antes de soldar, y con secciones más delgadas cobra todavía más importancia.

Lista de corte del diseño optimizado: `planos/lista-corte-tubos-optimizada.csv`.
