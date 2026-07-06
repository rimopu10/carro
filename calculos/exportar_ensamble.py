# -*- coding: utf-8 -*-
"""
Ensamble del chasis híbrido completo — space frame + nodos generativos.

Junta las dos piezas del diseño en un solo modelo 3D:
  - los 73 tubos del space frame (coordenadas reales de analisis_chasis.py)
  - los 5 tipos de nodos generativos (voxels de cad/nodo-*-datos.json),
    colocados en las coordenadas reales de las uniones que les corresponden,
    con espejo para el lado derecho.

Genera un visor Three.js autocontenido (un solo HTML, sin servidor).

Uso:  python exportar_ensamble.py <salida.html>
"""
import json, sys, os

HERE = os.path.dirname(os.path.abspath(__file__))
CAD = os.path.join(HERE, "..", "cad")
sys.path.insert(0, HERE)
import analisis_chasis as ac

# ---------------- colocación de nodos generativos en las uniones reales ----------------
# (tipo, archivo de voxels, color, descripción, uniones del chasis donde va)
COLOCACION = [
    ("susp_del",  "nodo-suspension-datos.json", "#fb923c",
     "Torre coilover delantera — recibe 5 tubos + carga de rueda",
     ["fx_hiL", "fx_hiR"]),
    ("susp_tras", "nodo-susp_tras-datos.json",  "#f87171",
     "Torre coilover trasera — coilover + empuje del motor de cubo",
     ["coilL", "coilR"]),
    ("arco_ppal", "nodo-arco_ppal-datos.json",  "#c084fc",
     "Base del arco principal — baja la carga de vuelco al estribo",
     ["mh_loL", "mh_loR"]),
    ("cuna_bat",  "nodo-cuna_bat-datos.json",   "#4ade80",
     "Esquina de la cuna de batería — soporta los 90 kg del pack",
     ["bat_fL", "bat_fR", "bat_rL", "bat_rR"]),
    ("pilar_a",   "nodo-pilar_a-datos.json",    "#38bdf8",
     "Nodo pilar A / tablero — recibe techo, parabrisas y diagonal de puerta",
     ["dash_hiL", "dash_hiR"]),
]

RHO_ALU = 2670.0  # kg/m3, AlSi10Mg impreso (estilo Czinger)

tipos, colocaciones = {}, []
masa_nodos = 0.0
for tipo, fname, color, desc, juntas in COLOCACION:
    nd = json.load(open(os.path.join(CAD, fname), encoding="utf-8"))
    n = max(nd["nelx"], nd["nely"], nd["nelz"])
    sc = 0.15 / n                                  # mismo escalado que el STL (~150 mm)
    vol = len(nd["vox"]) * sc ** 3
    tipos[tipo] = {
        "nelx": nd["nelx"], "nely": nd["nely"], "nelz": nd["nelz"],
        "vox": nd["vox"], "color": color, "desc": desc,
        "n_juntas": len(juntas), "masa_kg": round(vol * RHO_ALU, 2),
    }
    for j in juntas:
        colocaciones.append({
            "tipo": tipo, "junta": j,
            "pos": [round(v, 4) for v in ac.NODES[j]],
            "mirror": j.endswith("R"),
        })
        masa_nodos += vol * RHO_ALU

fs_min_bache = ac.resultados["LC1 Bache 3g"][1][0][4]
data = {
    "stats": {
        "n_tubos": len(ac.elems),
        "long_tubo": round(sum(e["L"] for e in ac.elems), 1),
        "masa_acero": round(ac.masa_acero, 1),
        "K_tors": round(ac.K_tors),
        "fs_bache": round(fs_min_bache, 2),
        "n_nodos": len(colocaciones),
        "masa_nodos": round(masa_nodos, 1),
    },
    "nodes": {n: [round(v, 4) for v in ac.NODES[n]] for n in ac.NODES},
    "elems": [{"a": e["a"], "b": e["b"], "tag": e["tag"], "sec": e["sec"]["nombre"]}
              for e in ac.elems],
    "tipos": tipos,
    "colocaciones": colocaciones,
}

TEMPLATE = r"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Chasis híbrido completo — space frame + nodos generativos</title>
<style>
  html,body{margin:0;padding:0;height:100%;background:#0d1117;overflow:hidden;font-family:system-ui,sans-serif;}
  #app{position:fixed;inset:0;}
  #ui{position:fixed;top:14px;left:14px;z-index:10;display:flex;flex-direction:column;gap:8px;max-width:300px;}
  #ui h1{color:#e6edf3;font-size:15px;margin:0;}
  .btnrow{display:flex;flex-wrap:wrap;gap:6px;}
  button{background:#21262d;color:#c9d1d9;border:1px solid #30363d;border-radius:7px;padding:7px 10px;font-size:12px;cursor:pointer;}
  button.active{background:#1f6feb;border-color:#1f6feb;color:#fff;}
  #stats,#leyenda{background:#161b22dd;border:1px solid #30363d;border-radius:10px;padding:10px 12px;color:#c9d1d9;font-size:12px;line-height:1.6;}
  #stats b{color:#e6edf3;}
  .tipo{display:flex;align-items:center;gap:8px;cursor:pointer;padding:2px 0;}
  .tipo:hover{color:#e6edf3;}
  .tipo.off{opacity:0.35;}
  .chip{width:12px;height:12px;border-radius:3px;flex:none;}
  #pie{position:fixed;bottom:16px;left:50%;transform:translateX(-50%);z-index:10;background:#161b22dd;border:1px solid #30363d;border-radius:10px;padding:8px 16px;color:#8b949e;font-size:11.5px;max-width:640px;text-align:center;}
</style>
</head>
<body>
<div id="app"></div>
<div id="ui">
  <h1>🏎️ Chasis híbrido completo</h1>
  <div class="btnrow">
    <button id="rot" class="active">⟳ Rotación</button>
    <button id="bnodos" class="active">🔩 Nodos</button>
    <button id="bruedas" class="active">🛞 Ruedas</button>
    <button id="bpilotos" class="active">👤 Pilotos</button>
    <button id="bxray">🩻 Rayos X</button>
    <button id="bfun">🎨 Por función</button>
  </div>
  <div id="stats"></div>
  <div id="leyenda"></div>
</div>
<div id="pie">Enfoque híbrido tipo Czinger: tubos rectos baratos y soldables + nodos orgánicos
impresos en 3D donde se cruzan varios tubos. Los nodos salieron de optimización topológica real
(SIMP + FEA 3D) — clic en un tipo de la lista para ocultarlo/mostrarlo.</div>

<script type="importmap">
{"imports":{
  "three":"https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js",
  "three/addons/":"https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/"
}}
</script>
<script type="module">
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';

const DATA = __DATA__;

const app = document.getElementById('app');
const renderer = new THREE.WebGLRenderer({antialias:true});
renderer.setPixelRatio(Math.min(devicePixelRatio,2));
renderer.setSize(innerWidth, innerHeight);
renderer.shadowMap.enabled = true;
app.appendChild(renderer.domElement);
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x0d1117);
scene.environment = new THREE.PMREMGenerator(renderer).fromScene(new RoomEnvironment(), 0.04).texture;
const camera = new THREE.PerspectiveCamera(38, innerWidth/innerHeight, 0.05, 100);
const controls = new OrbitControls(camera, renderer.domElement);
controls.target.set(1.55, 0.45, 0);
controls.enableDamping = true;
controls.autoRotate = true;
controls.autoRotateSpeed = 1.0;
scene.add(new THREE.HemisphereLight(0xdde7ff, 0x1a1d24, 0.8));
const sun = new THREE.DirectionalLight(0xffffff, 1.6);
sun.position.set(4,6,3); sun.castShadow = true;
sun.shadow.mapSize.set(2048,2048); scene.add(sun);
const ground = new THREE.Mesh(new THREE.PlaneGeometry(30,30), new THREE.ShadowMaterial({opacity:0.4}));
ground.rotation.x = -Math.PI/2; ground.receiveShadow = true; scene.add(ground);
scene.add(new THREE.GridHelper(24, 48, 0x21262d, 0x161b22));

// ---------- tubos del space frame ----------
const COL_ACERO = 0xb7bfc7;
const COL_TAG = {gen:0x8b949e, susp:0xfb923c, tors:0x60a5fa, safe:0xf87171, batt:0x4ade80};
const tubos = [];
for (const e of DATA.elems){
  const a = new THREE.Vector3(...DATA.nodes[e.a]);
  const b = new THREE.Vector3(...DATA.nodes[e.b]);
  const d = new THREE.Vector3().subVectors(b, a);
  const L = d.length();
  const esRed = e.sec.includes('RED');
  const geo = esRed
    ? new THREE.CylinderGeometry(0.02225, 0.02225, L, 14)
    : new THREE.BoxGeometry(0.038, L, 0.038);
  const mat = new THREE.MeshStandardMaterial({color:COL_ACERO, metalness:0.75, roughness:0.35});
  const mesh = new THREE.Mesh(geo, mat);
  mesh.position.copy(a).addScaledVector(d, 0.5);
  mesh.quaternion.setFromUnitVectors(new THREE.Vector3(0,1,0), d.clone().normalize());
  mesh.castShadow = true;
  scene.add(mesh);
  tubos.push({mesh, tag:e.tag});
}

// ---------- nodos generativos: superficie a partir de los voxels ----------
// caras expuestas de cada voxel lleno, en el mismo orden que el export STL
const CARAS = [
  [[ 1,0,0], [[1,0,0],[1,1,0],[1,1,1],[1,0,1]]],
  [[-1,0,0], [[0,0,0],[0,0,1],[0,1,1],[0,1,0]]],
  [[0, 1,0], [[0,1,0],[0,1,1],[1,1,1],[1,1,0]]],
  [[0,-1,0], [[0,0,0],[1,0,0],[1,0,1],[0,0,1]]],
  [[0,0, 1], [[0,0,1],[1,0,1],[1,1,1],[0,1,1]]],
  [[0,0,-1], [[0,0,0],[0,1,0],[1,1,0],[1,0,0]]],
];
const geomCache = {};
function nodoGeom(tipo, mirror){
  const key = tipo + (mirror ? '|R' : '|L');
  if (geomCache[key]) return geomCache[key];
  const nd = DATA.tipos[tipo];
  const s = 0.15 / Math.max(nd.nelx, nd.nely, nd.nelz);
  const cx = nd.nelx/2, cy = nd.nely/2, cz = nd.nelz/2;
  const lleno = new Set();
  for (const v of nd.vox) lleno.add(v[0] + v[1]*32 + v[2]*1024);
  const hay = (x,y,z) => x>=0 && y>=0 && z>=0 && x<nd.nelx && y<nd.nely && z<nd.nelz
                          && lleno.has(x + y*32 + z*1024);
  const pos = [];
  const push = (p) => {
    pos.push((p[0]-cx)*s, (p[1]-cy)*s, (mirror ? -(p[2]-cz) : (p[2]-cz))*s);
  };
  for (const v of nd.vox){
    const [ix, iy, iz] = v;
    for (const [dir, quad] of CARAS){
      if (hay(ix+dir[0], iy+dir[1], iz+dir[2])) continue;
      const q = quad.map(o => [ix+o[0], iy+o[1], iz+o[2]]);
      if (mirror){ // espejo en z: invertir el orden de los triángulos
        push(q[0]); push(q[2]); push(q[1]);
        push(q[0]); push(q[3]); push(q[2]);
      } else {
        push(q[0]); push(q[1]); push(q[2]);
        push(q[0]); push(q[2]); push(q[3]);
      }
    }
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  g.computeVertexNormals();
  geomCache[key] = g;
  return g;
}

const nodos = [];
for (const c of DATA.colocaciones){
  const nd = DATA.tipos[c.tipo];
  const mat = new THREE.MeshStandardMaterial({
    color: new THREE.Color(nd.color), metalness:0.55, roughness:0.42, flatShading:true});
  const mesh = new THREE.Mesh(nodoGeom(c.tipo, c.mirror), mat);
  mesh.position.set(...c.pos);
  mesh.castShadow = true;
  scene.add(mesh);
  nodos.push({mesh, tipo:c.tipo});
}

// ---------- contexto de escala: ruedas y pilotos (no son estructura) ----------
// QS273 en rin 17" de moto: llanta ~Ø620 mm. Ejes en las posiciones reales:
// delantero al centro de la caja de suspensión, trasero bajo la torre coilover.
const R_LLANTA = 0.31, ANCHO_LLANTA = 0.14, Z_RUEDA = 0.76;
const ruedas = [], pilotos = [];
const matLlanta = new THREE.MeshStandardMaterial({color:0x14181d, metalness:0.1, roughness:0.9});
const matRin = new THREE.MeshStandardMaterial({color:0x9aa4af, metalness:0.85, roughness:0.3});
for (const ax of [0.55, 2.58]){
  for (const lado of [1, -1]){
    const g = new THREE.Group();
    const llanta = new THREE.Mesh(new THREE.CylinderGeometry(R_LLANTA, R_LLANTA, ANCHO_LLANTA, 28), matLlanta);
    const rin = new THREE.Mesh(new THREE.CylinderGeometry(0.19, 0.19, ANCHO_LLANTA + 0.006, 24), matRin);
    llanta.rotation.x = rin.rotation.x = Math.PI/2;
    llanta.castShadow = true;
    g.add(llanta); g.add(rin);
    g.position.set(ax, R_LLANTA, lado * Z_RUEDA);
    scene.add(g); ruedas.push(g);
  }
}
// piloto de 1.75 m sentado en posición real de manejo (cabeza 5 cm bajo el arco)
function piloto(z){
  const g = new THREE.Group();
  const mat = new THREE.MeshStandardMaterial({color:0x566270, metalness:0.1, roughness:0.8,
                                              transparent:true, opacity:0.85});
  const cap = (r, a, b) => {
    const A = new THREE.Vector3(...a), B = new THREE.Vector3(...b);
    const d = new THREE.Vector3().subVectors(B, A);
    const m = new THREE.Mesh(new THREE.CapsuleGeometry(r, d.length(), 6, 12), mat);
    m.position.copy(A).addScaledVector(d, 0.5);
    m.quaternion.setFromUnitVectors(new THREE.Vector3(0,1,0), d.clone().normalize());
    m.castShadow = true;
    g.add(m);
  };
  const cab = new THREE.Mesh(new THREE.SphereGeometry(0.11, 16, 12), mat);
  cab.position.set(1.90, 0.92, z); cab.castShadow = true; g.add(cab);
  cap(0.13, [1.72, 0.30, z], [1.87, 0.75, z]);   // torso reclinado
  cap(0.09, [1.70, 0.28, z], [1.38, 0.38, z]);   // muslos
  cap(0.06, [1.38, 0.38, z], [1.16, 0.20, z]);   // piernas hacia pedales
  cap(0.05, [1.85, 0.72, z], [1.52, 0.55, z]);   // brazos al volante
  scene.add(g);
  pilotos.push(g);
}
piloto(+0.30); piloto(-0.30);

// ---------- paneles ----------
const S = DATA.stats;
document.getElementById('stats').innerHTML =
  `Alto total: <b>1.08 m</b> (i8: 1.29 · Atom: 1.20 · 33 Stradale: 0.99)<br>` +
  `Ancho con ruedas: <b>~1.66 m</b> · largo chasis: <b>3.0 m</b><br>` +
  `<b>${S.n_tubos} tubos</b> · ${S.long_tubo} m · ${S.masa_acero} kg de acero<br>` +
  `<b>${S.n_nodos} nodos impresos</b> (5 tipos) · ~${S.masa_nodos} kg en AlSi10Mg<br>` +
  `Rigidez torsional: <b>${S.K_tors.toLocaleString()} N·m/°</b><br>` +
  `FS mínimo (bache 3g): <b>${S.fs_bache}</b><br>` +
  `<span style="color:#8b949e">PTR 38×38×1.9 (cuadrado) + arcos RED 44.5×2.1.<br>` +
  `El pivote del brazo trasero lleva cartela de láser, no nodo impreso.</span>`;

const ley = document.getElementById('leyenda');
for (const [tipo, nd] of Object.entries(DATA.tipos)){
  const row = document.createElement('div');
  row.className = 'tipo';
  row.innerHTML = `<span class="chip" style="background:${nd.color}"></span>` +
    `<span><b style="color:#e6edf3">${tipo}</b> ×${nd.n_juntas} · ${nd.masa_kg} kg c/u<br>` +
    `<span style="color:#8b949e">${nd.desc}</span></span>`;
  row.onclick = () => {
    row.classList.toggle('off');
    const on = !row.classList.contains('off');
    for (const n of nodos) if (n.tipo === tipo) n.mesh.visible = on && verNodos;
  };
  ley.appendChild(row);
}

// ---------- controles ----------
let verNodos = true, xray = false, porFuncion = false;
document.getElementById('rot').onclick = (e) => {
  controls.autoRotate = !controls.autoRotate;
  e.target.classList.toggle('active', controls.autoRotate);
};
document.getElementById('bnodos').onclick = (e) => {
  verNodos = !verNodos;
  e.target.classList.toggle('active', verNodos);
  document.querySelectorAll('.tipo').forEach(r => r.classList.toggle('off', !verNodos));
  for (const n of nodos) n.mesh.visible = verNodos;
};
document.getElementById('bruedas').onclick = (e) => {
  const on = !ruedas[0].visible;
  e.target.classList.toggle('active', on);
  for (const r of ruedas) r.visible = on;
};
document.getElementById('bpilotos').onclick = (e) => {
  const on = !pilotos[0].visible;
  e.target.classList.toggle('active', on);
  for (const p of pilotos) p.visible = on;
};
document.getElementById('bxray').onclick = (e) => {
  xray = !xray;
  e.target.classList.toggle('active', xray);
  for (const t of tubos){
    t.mesh.material.transparent = xray;
    t.mesh.material.opacity = xray ? 0.16 : 1.0;
    t.mesh.material.depthWrite = !xray;
    t.mesh.castShadow = !xray;
    t.mesh.material.needsUpdate = true;
  }
};
document.getElementById('bfun').onclick = (e) => {
  porFuncion = !porFuncion;
  e.target.classList.toggle('active', porFuncion);
  for (const t of tubos)
    t.mesh.material.color.set(porFuncion ? (COL_TAG[t.tag] || COL_ACERO) : COL_ACERO);
  document.getElementById('pie').textContent = porFuncion
    ? 'Color por función del tubo: gris genérico · naranja suspensión · azul torsión (diagonales) · rojo seguridad (arcos/célula) · verde cuna de batería.'
    : 'Enfoque híbrido tipo Czinger: tubos rectos baratos y soldables + nodos orgánicos impresos en 3D donde se cruzan varios tubos. Clic en un tipo de la lista para ocultarlo/mostrarlo.';
};

camera.position.set(4.6, 1.9, 3.4);
addEventListener('resize', () => {
  camera.aspect = innerWidth/innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(innerWidth, innerHeight);
});
renderer.setAnimationLoop(() => { controls.update(); renderer.render(scene, camera); });
</script>
</body>
</html>
"""

out = sys.argv[1]
html = TEMPLATE.replace("__DATA__", json.dumps(data))
with open(out, "w", encoding="utf-8") as f:
    f.write(html)
print(f"OK ensamble escrito: {out}  ({len(html)//1024} KB)  "
      f"{data['stats']['n_tubos']} tubos + {data['stats']['n_nodos']} nodos generativos")
