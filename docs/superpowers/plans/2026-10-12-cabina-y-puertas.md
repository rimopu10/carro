# Cabina, vista y puertas — Plan de implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Poner al piloto en una postura real (1.75 m, asiento hundido y deslizable), mejorar su vista, y dotar al chasis de lo que necesitan las puertas de gaviota (bases de herraje, caso de carga LC7), con todo verificado numéricamente.

**Architecture:** Dos módulos nuevos y autocontenidos (`buck_piloto.py`: cuerpo humano y métricas de cabina; `puertas.py`: cinemática, fuerzas y coordenadas de herraje) que alimentan al optimizador de chasis ya existente (`rediseno_chasis.py` + `fem_chasis.py`), que sigue siendo la única fuente de la topología. `analisis_chasis.py` lee el resultado desde `chasis_rediseno.json`.

**Tech Stack:** Python 3.12, numpy, trimesh (+rtree), pytest 9, three.js (visor HTML).

Spec: `docs/superpowers/specs/2026-10-12-cabina-y-puertas-design.md`.

**Convención de ejes (todo el proyecto):** x crece hacia ATRÁS (nariz x≈-0.3, cola x≈3.6), y arriba, z lateral con **z>0 = lado izquierdo (piloto)**. Un punto "más adelante" tiene x menor.

---

## Mapa de archivos

| Archivo | Acción | Responsabilidad |
|---|---|---|
| `calculos/buck_piloto.py` | crear | Cuerpo humano p50 1.75 m, postura, métricas (holgura de techo, nuca-arco, cabecera, pedales), cápsulas de volumen ocupado |
| `calculos/test_buck_piloto.py` | crear | pytest de la postura nominal y los extremos del recorrido |
| `calculos/puertas.py` | crear | Eje de bisagra, centro de masa, amortiguador, fuerzas, carga LC7, coordenadas de herraje, barrido |
| `calculos/test_puertas.py` | crear | pytest de equilibrio y rango de fuerzas |
| `calculos/fem_chasis.py` | modificar | Masas por estación de riel, caso LC7, `registrar_nodo` ya existe |
| `calculos/rediseno_chasis.py` | modificar | Nodos de rieles/bisagras/amortiguador, volúmenes prohibidos desde `buck_piloto`, LC7 en `cumple` |
| `calculos/analisis_chasis.py` | modificar | `nodos_movidos`, reparto de masa por estación, barra de cinturones, LC7 en informe |
| `calculos/visor_tripo_chasis.py` | modificar | Vistas "Ojos piloto", puerta que abre, herraje |
| `docs/herraje-puertas.md` | crear | Lista de herraje, secuencia de armado "encaje sobre el carro" |
| `docs/bom-maestro.md` / `.csv` | modificar | Filas nuevas |

---

### Task 1: `buck_piloto.py` — el cuerpo real y sus métricas

**Files:**
- Create: `calculos/buck_piloto.py`
- Test: `calculos/test_buck_piloto.py`

- [ ] **Step 1: Escribir la prueba que falla**

```python
# calculos/test_buck_piloto.py
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import buck_piloto as B


def test_maniqui_es_adulto_real():
    # el maniquí viejo del proyecto tenía 0.41 m cadera->hombro
    assert abs(B.TRONCO - 0.51) < 1e-9


def test_postura_nominal_cumple_el_diseno():
    m = B.metricas(B.postura(1.50, 0.26, 40.0))
    assert m["holgura_techo"] >= 0.060       # coronilla vs límite útil del techo
    assert m["nuca_arco"] >= 0.080           # nuca vs cara delantera del arco
    assert m["cabecera_grados"] >= 10.5      # borde inferior de la cabecera sobre el ojo


def test_postura_vieja_no_cabe():
    m = B.metricas(B.postura(1.62, 0.30, 30.0))
    assert m["holgura_techo"] < 0.0          # la coronilla pasa el techo


def test_recorrido_rieles_1_85_atras():
    # 1.85 m en el extremo trasero del recorrido: nuca a >= 20 mm del arco
    m = B.metricas(B.postura(1.58, 0.26, 40.0, estatura=1.85))
    assert m["nuca_arco"] >= 0.020


def test_capsulas_cubren_piernas_y_cabeza():
    caps = B.capsulas(B.postura(1.50, 0.26, 40.0), z=0.31)
    nombres = {c["nombre"] for c in caps}
    assert {"muslo", "pierna", "pie", "torso", "cabeza"} <= nombres
```

- [ ] **Step 2: Verificar que falla**

Run: `cd "C:/Users/ILV PC/Desktop/proyectos/carro" && python -m pytest calculos/test_buck_piloto.py -q`
Expected: FAIL (`ModuleNotFoundError: No module named 'buck_piloto'`)

- [ ] **Step 3: Implementar**

```python
# calculos/buck_piloto.py
# -*- coding: utf-8 -*-
"""
Maqueta de asiento (seating buck) del piloto: cuerpo humano real y las métricas que deciden si la
cabina funciona. Reemplaza al maniquí de carroceria.py (cadera->hombro 0.41 m; un adulto de 1.75 m
tiene ~0.51).

Plano (x, y): x crece hacia ATRÁS, y arriba. Todo en metros.

    python calculos/buck_piloto.py        # tabla de la postura nominal y del recorrido
"""
import numpy as np

# --- hombre p50, 1.75 m (antropometría estándar) ---
ESTATURA_REF = 1.75
TRONCO = 0.51          # cadera -> hombro
HOMBRO_OJO = 0.19      # hombro -> ojo, vertical
OJO_CORONILLA = 0.12
OJO_NUCA = 0.10        # ojo -> parte de atrás de la cabeza, horizontal
MUSLO = 0.43           # cadera -> rodilla
PIERNA = 0.41          # rodilla -> tobillo
Y_SUELA = 0.18         # suela sobre el tablero del piso (tubo del piso y=0.16 + radio)
TOBILLO_ALTO = 0.08
PIE_BOLA = 0.15        # tobillo -> bola del pie (hacia adelante)

# --- carrocería de Tripo medida (cara INTERIOR del techo, z=0.31) ---
TECHO_INT = [(1.45, 0.998), (1.60, 1.025), (1.75, 1.045), (1.90, 1.053), (2.00, 1.048), (2.10, 1.039)]
FORRO = 0.020
ARCO_X_FRENTE = 2.02 - 0.0254      # cara delantera del arco (RED 50.8)
CABECERA = (1.45, 0.934)           # eje de la cabecera sobre el piloto (x, y)
CABECERA_R = 0.0254


def limite_techo(x):
    xs, ys = zip(*TECHO_INT)
    return float(np.interp(x, xs, ys)) - FORRO


def postura(hx, hy, recline_deg, estatura=ESTATURA_REF, muslo_deg=10.0):
    """Cuerpo sentado con la cadera en (hx, hy). Segmentos escalados por estatura/1.75."""
    k = estatura / ESTATURA_REF
    th, al = np.radians(recline_deg), np.radians(muslo_deg)
    cadera = np.array([hx, hy])
    hombro = cadera + k * TRONCO * np.array([np.sin(th), np.cos(th)])
    ojo = hombro + np.array([-0.03, k * HOMBRO_OJO])
    coronilla = ojo + np.array([0.0, k * OJO_CORONILLA])
    nuca = ojo + np.array([OJO_NUCA, 0.0])
    rodilla = cadera + k * MUSLO * np.array([-np.cos(al), np.sin(al)])
    y_tob = Y_SUELA + TOBILLO_ALTO
    dx = np.sqrt(max((k * PIERNA) ** 2 - (rodilla[1] - y_tob) ** 2, 0.0))
    tobillo = np.array([rodilla[0] - dx, y_tob])
    bola = tobillo + np.array([-PIE_BOLA, -TOBILLO_ALTO + 0.02])
    return dict(cadera=cadera, hombro=hombro, ojo=ojo, coronilla=coronilla, nuca=nuca,
                rodilla=rodilla, tobillo=tobillo, bola=bola)


def metricas(p):
    ojo = p["ojo"]
    borde = CABECERA[1] - CABECERA_R
    return dict(
        holgura_techo=limite_techo(p["coronilla"][0]) - p["coronilla"][1],
        nuca_arco=ARCO_X_FRENTE - p["nuca"][0],
        cabecera_grados=float(np.degrees(np.arctan((borde - ojo[1]) / (ojo[0] - CABECERA[0])))),
        pedal_x=float(p["bola"][0]),
        ojo=(float(ojo[0]), float(ojo[1])),
    )


def capsulas(p, z=0.31):
    """Volumen que ocupa el cuerpo, como cápsulas 3D (a, b, radio) en el plano z=z. Los tubos del chasis no
    pueden pasar por ahí. Torso con holgura de respaldo de 4 cm."""
    def v(q):
        return np.array([q[0], q[1], z])
    centro_cabeza = p["ojo"] + np.array([0.045, -0.04])
    return [
        dict(nombre="muslo", a=v(p["cadera"]), b=v(p["rodilla"]), r=0.11),
        dict(nombre="pierna", a=v(p["rodilla"]), b=v(p["tobillo"]), r=0.08),
        dict(nombre="pie", a=v(p["tobillo"]), b=v(p["bola"]), r=0.06),
        dict(nombre="torso", a=v(p["cadera"]), b=v(p["hombro"]), r=0.17),
        dict(nombre="cabeza", a=v(centro_cabeza), b=v(centro_cabeza + np.array([0.04, 0.0])), r=0.115),
    ]


def dist_punto_capsula(P, c):
    """Distancia (m) de los puntos P (n,3) al eje de la cápsula c, menos su radio."""
    a, b = c["a"], c["b"]
    ab = b - a
    t = np.clip(((P - a) @ ab) / max(ab @ ab, 1e-12), 0.0, 1.0)
    return np.linalg.norm(P - (a + t[:, None] * ab), axis=1) - c["r"]


NOMINAL = dict(hx=1.50, hy=0.26, recline=40.0)
RIELES = (1.42, 1.58)        # recorrido de la cadera en x


if __name__ == "__main__":
    for hx in (RIELES[0], NOMINAL["hx"], RIELES[1]):
        m = metricas(postura(hx, NOMINAL["hy"], NOMINAL["recline"]))
        print(f"cadera x={hx:.2f}: techo {m['holgura_techo']*1000:+.0f} mm  nuca-arco {m['nuca_arco']*1000:+.0f} mm  "
              f"cabecera {m['cabecera_grados']:+.1f}°  pedal x {m['pedal_x']:.2f}")
```

- [ ] **Step 4: Verificar que pasa**

Run: `python -m pytest calculos/test_buck_piloto.py -q`
Expected: `5 passed`. Si `test_recorrido_rieles_1_85_atras` falla, anotar el valor real en `docs/superpowers/specs/2026-10-12-cabina-y-puertas-design.md` §3 y ajustar el umbral de la prueba (la prueba documenta lo medido).

- [ ] **Step 5: Commit**

```bash
git add calculos/buck_piloto.py calculos/test_buck_piloto.py
git commit -m "Maqueta de asiento: cuerpo real de 1.75 m y metricas de cabina"
```

---

### Task 2: `puertas.py` — cinemática, fuerzas y herraje

**Files:**
- Create: `calculos/puertas.py`
- Test: `calculos/test_puertas.py`

- [ ] **Step 1: Escribir la prueba que falla**

```python
# calculos/test_puertas.py
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import puertas as P


def test_eje_de_bisagra_sobre_el_espinazo():
    assert abs(P.EJE_A0[2] - 0.15) < 1e-9
    assert abs(np.linalg.norm(P.EJE_U) - 1) < 1e-9
    assert P.EJE_U[0] > 0.99                 # el eje va casi a lo largo del carro


def test_amortiguador_de_catalogo():
    f = P.fuerza_amortiguador(65.0)
    assert 150.0 < f < 400.0                 # ~250 N
    assert 0.08 <= P.carrera_amortiguador() <= 0.18


def test_equilibrio_de_momentos_sobre_el_eje():
    # peso + viento + amortiguador no deben dejar momento neto sobre el eje (la bisagra no lo resiste)
    for th in (20.0, 45.0, 65.0):
        est = P.estatica(th)
        tau = sum(np.dot(np.cross(r - P.EJE_A0, f), P.EJE_U) for r, f in est["fuerzas_en_puerta"])
        assert abs(tau) < 1e-6


def test_lc7_es_simetrica_y_tiene_las_tres_estaciones():
    lc = P.lc7()
    assert set(lc) == {"h1L", "h2L", "saL", "h1R", "h2R", "saR"}
    for n in ("h1", "h2", "sa"):
        L, R = lc[n + "L"], lc[n + "R"]
        assert np.allclose([L[0], L[1], -L[2]], R)       # espejo en z


def test_lc7_reacciones_suman_cero_con_la_puerta():
    est = P.estatica(65.0, factor_peso=P.FACTOR_BACHE, viento=P.VIENTO_N)
    lc = P.lc7()
    suma_chasis = lc["h1L"] + lc["h2L"] + lc["saL"]
    suma_puerta = sum(f for r, f in est["fuerzas_en_puerta"])
    assert np.allclose(suma_chasis + suma_puerta, 0.0, atol=1e-6)


def test_la_puerta_abierta_deja_el_borde_alto():
    assert P.borde_inferior_abierto(65.0)[1] > 1.30
```

- [ ] **Step 2: Verificar que falla**

Run: `python -m pytest calculos/test_puertas.py -q`
Expected: FAIL (`ModuleNotFoundError: No module named 'puertas'`)

- [ ] **Step 3: Implementar**

```python
# calculos/puertas.py
# -*- coding: utf-8 -*-
"""
Puertas de gaviota: eje de bisagra, amortiguador de gas, fuerzas con la puerta abierta (caso LC7 del chasis)
y coordenadas del herraje. Lado izquierdo (z>0); el derecho es el espejo en z.

Ejes del proyecto: x hacia atrás, y arriba, z lateral. La puerta gira hacia ARRIBA y hacia afuera: rotación de
-theta (regla de la mano derecha) sobre el eje +x del riel del techo.

    python calculos/puertas.py
"""
import itertools
import numpy as np

G = 9.81
MASA_PUERTA = 10.0          # kg (piel sándwich + esqueleto Ø16 + cristal PC + herraje)
FACTOR_BACHE = 3.0          # la puerta abierta recibe 3 g al pasar un bache / un portazo
VIENTO_N = 400.0            # N laterales, en el centro de la puerta abierta
THETA_MAX = 65.0

# eje: el riel del espinazo sp_f -> sp_r, lado izquierdo
A_SF = np.array([1.45, 0.95, 0.15])
A_SR = np.array([2.02, 1.01, 0.15])
EJE_A0 = A_SF.copy()
EJE_U = (A_SR - A_SF) / np.linalg.norm(A_SR - A_SF)
S_H1, S_H2 = 0.12, 0.86     # estaciones de las 2 bisagras a lo largo del riel (fracción)

CM_CERRADA = np.array([1.70, 0.72, 0.70])     # centro de masa de la puerta cerrada
BORDE_INF = np.array([1.70, 0.28, 0.90])      # punto bajo del borde de la puerta
SA = np.array([1.45, 0.938, 0.30])            # ancla del amortiguador en el chasis (cabecera, lado izq.)


def punto_riel(s):
    return A_SF + (A_SR - A_SF) * s


def giro(p, theta_deg):
    """Rota el punto p (puerta cerrada) theta grados hacia arriba/afuera sobre el eje de la bisagra."""
    a = np.radians(-theta_deg)
    q = np.asarray(p, float) - EJE_A0
    u = EJE_U
    qr = q * np.cos(a) + np.cross(u, q) * np.sin(a) + u * np.dot(u, q) * (1 - np.cos(a))
    return EJE_A0 + qr


def _fuerza_para(pd, theta, factor_peso=1.0, viento=0.0):
    """Fuerza del amortiguador (N) que anula el momento sobre el eje con la puerta a theta."""
    cm = giro(CM_CERRADA, theta)
    tau_ext = np.dot(np.cross(cm - EJE_A0, np.array([0.0, -MASA_PUERTA * G * factor_peso, viento])), EJE_U)
    p = giro(pd, theta)
    d = (p - SA) / np.linalg.norm(p - SA)           # el amortiguador EMPUJA a la puerta lejos del chasis
    lever = np.dot(np.cross(p - EJE_A0, d), EJE_U)
    return None if abs(lever) < 1e-9 else float(-tau_ext / lever)


def _disenar_ancla():
    """Busca el ancla del amortiguador en la puerta (PD, cerrada) para que sostenga THETA_MAX con una fuerza
    de catálogo (~250 N), con carrera de 80-180 mm y longitud comprimida >= 0.20 m."""
    best, best_score = None, 1e9
    for x, y, z in itertools.product(np.arange(1.30, 1.56, 0.05), np.arange(0.55, 0.91, 0.05),
                                     np.arange(0.50, 0.91, 0.05)):
        pd = np.array([x, y, z])
        l0 = np.linalg.norm(pd - SA)
        carrera = np.linalg.norm(giro(pd, THETA_MAX) - SA) - l0
        if not (0.08 <= carrera <= 0.18) or l0 < 0.20:
            continue
        f = _fuerza_para(pd, THETA_MAX)
        if f is None or f <= 0:
            continue
        score = abs(f - 250.0)
        if score < best_score:
            best, best_score = pd, score
    if best is None:
        raise RuntimeError("no hay ancla de amortiguador que cumpla las restricciones")
    return best


PD = _disenar_ancla()


def fuerza_amortiguador(theta, factor_peso=1.0, viento=0.0):
    return _fuerza_para(PD, theta, factor_peso, viento)


def carrera_amortiguador():
    return float(np.linalg.norm(giro(PD, THETA_MAX) - SA) - np.linalg.norm(PD - SA))


def estatica(theta, factor_peso=1.0, viento=0.0):
    """Fuerzas sobre la puerta a theta: peso+viento, amortiguador y reacción total de las bisagras."""
    cm = giro(CM_CERRADA, theta)
    p = giro(PD, theta)
    fs = _fuerza_para(PD, theta, factor_peso, viento)
    f_ext = np.array([0.0, -MASA_PUERTA * G * factor_peso, viento])
    f_amort = fs * (p - SA) / np.linalg.norm(p - SA)
    f_bis = -(f_ext + f_amort)
    punto_bisagras = punto_riel((S_H1 + S_H2) / 2)
    return dict(fuerza_amortiguador=fs,
                fuerzas_en_puerta=[(cm, f_ext), (p, f_amort), (punto_bisagras, f_bis)])


def lc7(theta=THETA_MAX):
    """Cargas sobre el CHASIS con la puerta abierta: reacción de las 2 bisagras (reparto por posición del centro
    de masa) y del amortiguador. Dict nodo -> fuerza (3,) en N, ambos lados."""
    est = estatica(theta, factor_peso=FACTOR_BACHE, viento=VIENTO_N)
    f_bis = est["fuerzas_en_puerta"][2][1]
    f_amort = est["fuerzas_en_puerta"][1][1]
    cm_x = giro(CM_CERRADA, theta)[0]
    x1, x2 = punto_riel(S_H1)[0], punto_riel(S_H2)[0]
    w2 = float(np.clip((cm_x - x1) / (x2 - x1), 0.0, 1.0))
    L = {"h1L": -f_bis * (1 - w2), "h2L": -f_bis * w2, "saL": -f_amort}
    out = dict(L)
    for k, v in L.items():
        out[k[:-1] + "R"] = np.array([v[0], v[1], -v[2]])
    return out


def borde_inferior_abierto(theta):
    return giro(BORDE_INF, theta)


def herraje():
    """Coordenadas (lado izquierdo, puerta cerrada) del herraje, en metros."""
    return {
        "bisagra_1": punto_riel(S_H1), "bisagra_2": punto_riel(S_H2),
        "amortiguador_chasis": SA.copy(), "amortiguador_puerta": PD.copy(),
        "cierre_techo_delantero": np.array([1.45, 0.93, 0.40]),     # esquina de la cabecera
        "cierre_estribo_delantero": np.array([1.40, 0.16, 0.59]),
        "cierre_estribo_trasero": np.array([1.90, 0.16, 0.59]),
        "cierre_trasero": np.array([2.02, 0.742, 0.492]),           # pierna del arco
    }


if __name__ == "__main__":
    print(f"ancla del amortiguador en la puerta: {np.round(PD, 3)}  carrera {carrera_amortiguador()*1000:.0f} mm")
    for th in (10, 30, 45, 65):
        print(f"  puerta a {th:2d}°: amortiguador {fuerza_amortiguador(th):6.0f} N")
    print("borde inferior abierto a 65°:", np.round(borde_inferior_abierto(65.0), 3))
    for k, v in lc7().items():
        print(f"  LC7 {k}: {np.round(v, 1)} N")
```

- [ ] **Step 4: Verificar que pasa**

Run: `python -m pytest calculos/test_puertas.py -q && python calculos/puertas.py`
Expected: `6 passed` y una tabla con la fuerza del amortiguador ~150–400 N a 65° y el borde inferior abierto a y>1.30.

- [ ] **Step 5: Commit**

```bash
git add calculos/puertas.py calculos/test_puertas.py
git commit -m "Puertas de gaviota: cinematica, amortiguador, carga LC7 y herraje"
```

---

### Task 3: El chasis recibe al piloto real y a las puertas

**Files:**
- Modify: `calculos/analisis_chasis.py` (barra de cinturones, `nodos_movidos`, reparto de masas, LC7 en el informe)
- Modify: `calculos/fem_chasis.py` (reparto de masas, caso LC7)
- Modify: `calculos/rediseno_chasis.py` (nodos de rieles/bisagras/amortiguador, volúmenes del cuerpo desde `buck_piloto`, LC7 en `cumple`)

- [ ] **Step 1: `analisis_chasis.py` — barra de cinturones y nodos movidos**

En la línea del nodo `mh_belt` cambiar `NM("mh_belt",2.02, 0.742, 0.492)` por `NM("mh_belt",2.02, 0.660, 0.506)` (altura real del hombro, spec §3). En el bloque `REDISEÑO`, después de `N(_n, *_p)` de los nodos nuevos, agregar:

```python
    for _n, _p in _d.get("nodos_movidos", {}).items():      # nodos del diseño base que el rediseño reubica
        N(_n, *_p)
```

Reemplazar el manejo de `_MOVER` por reparto de fracciones (el JSON trae `"masas_mover": {"seatL": {"smFL": 0.5, "smRL": 0.5}}`):

```python
for _o, _t in _MOVER.items():       # el ocupante pesa donde se atornillan los rieles de su asiento
    _m = MASAS.pop(_o)
    for _n, _f in (_t.items() if isinstance(_t, dict) else [(_t, 1.0)]):
        MASAS[_n] = MASAS.get(_n, 0.0) + _m * _f
```

Agregar al informe del final el caso LC7 con las cargas de `puertas.lc7()` (mismo patrón que `F_vuelco_cabecera`).

- [ ] **Step 2: `fem_chasis.py` — reparto de masas y caso LC7**

Reemplazar `mover_masa` por:

```python
def mover_masa(origen, destino):
    """destino: nodo (todo) o dict nodo->fracción. El ocupante pesa donde se atornillan sus rieles."""
    m = _MASAS_FIJAS.pop(origen)
    for n, f in (destino.items() if isinstance(destino, dict) else [(destino, 1.0)]):
        _MASAS_FIJAS[n] = _MASAS_FIJAS.get(n, 0.0) + m * f
```

Agregar `import puertas as _PU` y, después de `_F_vuelco_frontal`:

```python
def _F_puerta():
    """LC7: puertas abiertas. Reacciones de las bisagras y del amortiguador en los nodos h1/h2/sa."""
    F = np.zeros(NDOF)
    for n, f in _PU.lc7().items():
        if n in IDX:
            F[6 * IDX[n]:6 * IDX[n] + 3] += f
    return F
```

En `evaluar`: agregar `"LC7"` a `nombres` y `_F_puerta()` como columna de `Fm`. LC7 cae en la rama de resistencia normal (`fs_miembro`), no en `fs5`.

- [ ] **Step 3: `rediseno_chasis.py` — nodos y topología**

(a) Importar: `import buck_piloto as BK` y `import puertas as PU`.

(b) Reemplazar `NUEVOS` y `OBLIGADOS`:

```python
H1, H2, SA = PU.punto_riel(PU.S_H1), PU.punto_riel(PU.S_H2), PU.SA
XF, XR = 1.36, 1.66                       # estaciones de los rieles del asiento
NUEVOS = {
    "cf1": (1.10, 0.16, 0.0), "cfF": (XF, 0.16, 0.0), "cf2": (XR, 0.16, 0.0), "cf3": (2.02, 0.16, 0.0),
    "seatFL": (XF, 0.16, 0.591), "seatFR": (XF, 0.16, -0.591),
    "smFL": (XF, 0.16, 0.31), "smFR": (XF, 0.16, -0.31),
    "smRL": (XR, 0.16, 0.31), "smRR": (XR, 0.16, -0.31),
    "h1L": tuple(H1), "h2L": tuple(H2), "saL": tuple(SA),
    "h1R": (H1[0], H1[1], -H1[2]), "h2R": (H2[0], H2[1], -H2[2]), "saR": (SA[0], SA[1], -SA[2]),
}
OBLIGADOS = {"smFL", "smFR", "smRL", "smRR", "seatFL", "seatFR", "h1L", "h2L", "saL", "h1R", "h2R", "saR"}
MOVIDOS = {"seatL": (XR, 0.16, 0.591), "seatR": (XR, 0.16, -0.591)}
```

(c) Aplicar `MOVIDOS` a `F.NODES` justo después de registrar `NUEVOS`; reparto de masa: `F.mover_masa("seatL", {"smFL": 0.5, "smRL": 0.5})` y `F.mover_masa("seatR", {"smFR": 0.5, "smRR": 0.5})` (quitar las líneas viejas de `smL/smR`). Escribir `nodos_movidos` y `masas_mover` en el JSON de salida.

(d) En `base_miembros()`: `SPLIT` pasa a mapear a una LISTA de nodos intermedios:

```python
SPLIT = {
    frozenset(("dash_loL", "dash_loR")): ["cf1"],
    frozenset(("dash_loL", "mh_loR")): ["cf2"],
    frozenset(("dash_loR", "mh_loL")): ["cf2"],
    frozenset(("dash_loL", "seatL")): ["seatFL"],
    frozenset(("dash_loR", "seatR")): ["seatFR"],
    frozenset(("sp_fL", "sp_rL")): ["h1L", "h2L"],
    frozenset(("sp_fR", "sp_rR")): ["h1R", "h2R"],
    frozenset(("hdrL", "sp_fL")): ["saL"],
    frozenset(("hdrR", "sp_fR")): ["saR"],
}
```

y la partición encadena `a -> n1 -> n2 -> b` con la misma sección y etiqueta:

```python
        if i in SPLIT:
            cadena = [a] + SPLIT[i] + [b]
            for p, q in zip(cadena[:-1], cadena[1:]):
                out.append((p, q, s, tag))
```

Los travesaños de asiento reemplazan al bloque anterior `seat -> sm -> cf2`:

```python
    s32 = sec_por_nombre("PTR 32x32x1.9")
    for lado in ("L", "R"):
        out += [("seatF" + lado, "smF" + lado, s32, "asiento"), ("smF" + lado, "cfF", s32, "asiento"),
                ("seat" + lado, "smR" + lado, s32, "asiento"), ("smR" + lado, "cf2", s32, "asiento")]
```

(e) `CAB` (nodos candidatos): quitar `smL`, `smR`; agregar `seatFL, seatFR, smFL, smFR, smRL, smRR, cfF`.

(f) Volúmenes del cuerpo desde `buck_piloto`: reemplazar las máscaras `piernas`, `torso`, `cab` y `cabeza_arco` dentro de `bloquea()` por cápsulas en tres posiciones del recorrido:

```python
CAPS = []
for _hx in (BK.RIELES[0], BK.NOMINAL["hx"], BK.RIELES[1]):
    for _z in (0.31, -0.31):
        CAPS += BK.capsulas(BK.postura(_hx, BK.NOMINAL["hy"], BK.NOMINAL["recline"]), z=_z)
```

y dentro de `bloquea`, tras construir `P`: `cuerpo = np.zeros(len(P), bool)`; `for c in CAPS: cuerpo |= BK.dist_punto_capsula(P, c) < 0.0`; usar `cuerpo` en el `return` en lugar de `piernas | torso | cab | cabeza_arco`.

(g) `cumple()`: agregar `or res["fs"]["LC7"] < FS_PUERTA` con `FS_PUERTA = 2.0`, y en `margenes()` el término `res["fs"]["LC7"] / FS_PUERTA`.

- [ ] **Step 4: Verificar que el FEM sigue dando lo de antes en el diseño base**

Run: `CHASIS_BASE=1 python calculos/fem_chasis.py`
Expected: LC1, LC3, LC4, LC5 como antes (2.05, 3.13, 2.83, 1.64); LC7 no aparece porque los nodos h1/h2/sa no existen en el diseño base.

- [ ] **Step 5: Commit**

```bash
git add calculos/analisis_chasis.py calculos/fem_chasis.py calculos/rediseno_chasis.py
git commit -m "Chasis: rieles de asiento, bisagras, amortiguador y caso LC7"
```

---

### Task 4: Re-optimizar, adoptar y verificar todo

**Files:**
- Modify (regenerados): `calculos/chasis_rediseno.json`, `cad/chasis.json`, `planos/lista-corte-tubos.csv`, `calculos/resultados-analisis.md`

- [ ] **Step 1: Correr el optimizador**

Run: `python calculos/rediseno_chasis.py 8000 calculos/_rd_nuevo.json`
Expected: termina con `cruces sin nodo: ninguno` y `final: N miembros ... FS [LC1, LC3, LC4, LC5, LC5c, LC6]` con todos ≥ sus pisos. Si hay `AVISO: nodo ... se queda con 6 tubos`, anotarlo.

- [ ] **Step 2: Adoptar y correr el análisis oficial**

```bash
cp calculos/_rd_nuevo.json calculos/chasis_rediseno.json && rm calculos/_rd_nuevo.json
python calculos/analisis_chasis.py | tail -n 10
python calculos/exportar_blender.py | tail -n 1
```

Expected: misma masa y K que el optimizador (± redondeo) y LC7 con FS ≥ 2.

- [ ] **Step 3: Batería de verificación**

```bash
python calculos/hueco_puerta.py                        # LIBRE
python calculos/holguras.py | tail -n 2                # TODO LIBRE
python calculos/verificar_piel_tripo.py "$TEMP/tripo-cerrado-sin-ruedas-mm.stl" | tail -n 3   # 0 tubos asoman
python calculos/buck_piloto.py                         # cabecera, techo y nuca en los 3 puntos del recorrido
python -m pytest calculos -q                           # todas las pruebas
```

Si falta `$TEMP/tripo-cerrado-sin-ruedas-mm.stl`, regenerarlo con `cerrar_invernadero` (de `tripo_juguete.py`) y quitando las ruedas, como el 2026-10-11.

- [ ] **Step 4: Criterios del spec §6**

Anotar en `docs/herraje-puertas.md` (Tarea 6) la tabla: cabecera ≥ +12° (si falta, subir `hdr`/`sp_f` 1–2 cm y repetir el paso 1), coronilla ≥ 40 mm, nuca ≥ 80 mm nominal, LC1–LC7 sobre sus pisos, cortes sin negativos ni < 40 mm, ningún nodo con > 5 tubos.

- [ ] **Step 5: Commit**

```bash
git add calculos/chasis_rediseno.json cad/chasis.json planos/lista-corte-tubos.csv calculos/resultados-analisis.md
git commit -m "Chasis rediseñado para el piloto real y las puertas de gaviota"
```

---

### Task 5: Visor — ojos del piloto, puerta que abre y herraje

**Files:**
- Modify: `calculos/visor_tripo_chasis.py`

- [ ] **Step 1: Vistas de ojos**

En el diccionario `V` del JS agregar `'ojo':[[ojo_x,ojo_y,0.31],[0.5,0.80,0.28],85]`, `'ojoP'` (z=-0.31) y `'ojoA'` (mirando atrás), con `ojo_x, ojo_y` tomados de `buck_piloto.metricas(postura(...))["ojo"]` e inyectados en el HTML por Python; el manejador de botones fija `C.fov = v[2]||35` y llama `C.updateProjectionMatrix()`. Botones nuevos: "Ojos piloto", "Ojos pasajero", "Atrás piloto".

- [ ] **Step 2: Puerta que abre**

En Python, separar las caras de la malla decimada cuyo centroide cae dentro de `CONTORNO_LADO` (de `tripo_gaviota.py`, encogido 30 mm) con `|z| > 0.17`, en dos mallas `puertaL` y `puertaR`; exportarlas como buffers aparte. En JS, un `THREE.Group` por puerta que gira `-theta` (izq.) / `+theta` (der.) alrededor del eje `puertas.EJE_A0`/`EJE_U`, con un deslizador "Puerta (0–65°)". Dibujar con marcadores el herraje de `puertas.herraje()` (bisagras, amortiguador, cierres).

- [ ] **Step 3: Verificar visualmente**

Run: `python calculos/visor_tripo_chasis.py "$TEMP/tripo-vista.stl"` y abrir con un servidor local (`python -m http.server 8765`). Comprobar con capturas: (a) "Ojos piloto" muestra la cabecera sobre el borde superior del parabrisas, (b) la puerta abre a 65° sin atravesar la cabeza ni los hombros del maniquí.

- [ ] **Step 4: Commit**

```bash
git add calculos/visor_tripo_chasis.py carro-tripo-chasis-3d.html
git commit -m "Visor: ojos del piloto, puerta que abre y herraje"
```

---

### Task 6: Documentación de herraje y lista de compra

**Files:**
- Create: `docs/herraje-puertas.md`
- Modify: `docs/bom-maestro.md`, `docs/bom-maestro.csv`

- [ ] **Step 1: `docs/herraje-puertas.md`**

Contenido obligatorio: (1) lista de herraje con las coordenadas de `puertas.herraje()` y la fuerza del amortiguador de `puertas.py`; (2) construcción de la puerta (piel sándwich, anillo Ø16×1.2, placas 3 mm, policarbonato 3 mm); (3) secuencia de armado **"encaje sobre el carro"**: soldar el chasis en la plantilla → pegar la carrocería → armar el marco del vano → modelar la puerta contra el vano real → ajustar bisagras y pernos de cierre (holgura 5 ± 1 mm) → sellos; (4) la tabla de criterios del spec §6 con los números medidos en la Tarea 4.

- [ ] **Step 2: BOM**

Agregar a `docs/bom-maestro.csv` y `.md`: bisagras de acero forjado (4), amortiguadores de gas ~250 N (2), cierres rotativos con perno ajustable (6) y manijas (4), tubo redondo Ø16×1.2 (m según corte), placa de acero 3 mm para herrajes (DXF por generar), policarbonato 3 mm, sello tipo D, rieles de asiento (2), espuma de celda cerrada 5 mm y tela de fibra de vidrio.

- [ ] **Step 3: Commit**

```bash
git add docs/herraje-puertas.md docs/bom-maestro.md docs/bom-maestro.csv
git commit -m "Herraje de las puertas, secuencia de armado y filas de la lista de compra"
```

---

### Task 7: Auditoría cruzada y cierre

- [ ] **Step 1:** Lanzar dos agentes independientes (estructura/FEM y ergonomía/fabricación), como en la revisión del 2026-10-12, con el chasis nuevo, pidiéndoles verificar LC7, la entrada y salida con la puerta a 65°, la visibilidad desde los ojos y la lista de corte.
- [ ] **Step 2:** Corregir lo que reporten como BLOQUEANTE o ALTA y repetir la Tarea 4, pasos 2 y 3.
- [ ] **Step 3:** Actualizar la memoria del proyecto (`plan-mini-1a5-y-tripo.md`) con el estado final y avisar al usuario de lo que queda abierto.

---

## Autorrevisión del plan contra el spec

| Requisito del spec | Tarea |
|---|---|
| §3 postura 1.75 m, asiento hundido, 40°, cadera x 1.50 | 1, 3 (nodos `sm*`, rieles x 1.36/1.66) |
| §3 recorrido de rieles 1.42–1.58 | 1 (`RIELES`), 3 (cápsulas en 3 posiciones) |
| §3 barra de cinturones a y≈0.66 | 3 (Step 1) |
| §3 cabecera ≥ +12° | 4 (Step 4) |
| §3 aspecto de cabina / forro 20 mm | 1 (`FORRO`), 6 (docs) |
| §4 construcción, herraje, encaje de la puerta | 2, 6 |
| §4 geometría de apertura | 2 (`borde_inferior_abierto`), 5 |
| §5 bases de herraje y LC7 | 2, 3 |
| §6 criterios de aceptación | 4 |
| §9 entregables | 1–6 |

Placeholders: ninguno; los puntos que dependen de un número medido (umbral del 1.85 m, cabecera ≥ +12°) tienen una acción explícita si no se cumplen.
