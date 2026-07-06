# -*- coding: utf-8 -*-
"""
Post-procesador visual: genera un visor 3D (Three.js) con los resultados REALES
del análisis — tubos coloreados por esfuerzo y deformación exagerada, como el
software FEM comercial.

Uso:  python exportar_visor.py <ruta_salida.html>
"""
import json, sys, os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import analisis_chasis as ac

data = {
    "K_tors": round(ac.K_tors),
    "masa": round(ac.masa_acero, 1),
    "nodes": {n: [round(v, 4) for v in ac.NODES[n]] for n in ac.NODES},
    "elems": [{"a": e["a"], "b": e["b"], "tag": e["tag"],
               "sec": e["sec"]["nombre"], "r": 0.024 if "RED" in e["sec"]["nombre"] else 0.019}
              for e in ac.elems],
    "cases": {},
}
for lc, (U, filas) in ac.resultados.items():
    sigs = []
    for e in ac.elems:
        sig, _ = ac.esfuerzo_max(e, U)
        sigs.append(round(sig / 1e6, 1))
    disp = {n: [round(U[6*ac.idx[n]+k]*1000, 3) for k in range(3)] for n in ac.NODES}
    data["cases"][lc] = {
        "sig": sigs, "disp": disp,
        "fsmin": round(filas[0][4], 2), "worst": filas[0][0],
        "sigmax": round(max(sigs), 1),
    }

TEMPLATE = r"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Resultados FEM del chasis — visor</title>
<style>
  html,body{margin:0;padding:0;height:100%;background:#0d1117;overflow:hidden;font-family:system-ui,sans-serif;}
  #app{position:fixed;inset:0;}
  #ui{position:fixed;top:14px;left:14px;z-index:10;display:flex;flex-direction:column;gap:8px;max-width:270px;}
  #ui h1{color:#e6edf3;font-size:15px;margin:0;}
  .btnrow{display:flex;flex-wrap:wrap;gap:6px;}
  button{background:#21262d;color:#c9d1d9;border:1px solid #30363d;border-radius:7px;padding:7px 10px;font-size:12px;cursor:pointer;}
  button.active{background:#1f6feb;border-color:#1f6feb;color:#fff;}
  #stats{background:#161b22dd;border:1px solid #30363d;border-radius:10px;padding:10px 12px;color:#c9d1d9;font-size:12px;line-height:1.6;}
  #stats b{color:#e6edf3;}
  #defrow{display:flex;align-items:center;gap:8px;color:#8b949e;font-size:11.5px;background:#161b22dd;border:1px solid #30363d;border-radius:10px;padding:8px 12px;}
  input[type=range]{width:130px;}
  #cbar{position:fixed;bottom:16px;left:50%;transform:translateX(-50%);z-index:10;background:#161b22dd;border:1px solid #30363d;border-radius:10px;padding:8px 16px;color:#c9d1d9;font-size:11.5px;display:flex;align-items:center;gap:10px;}
  #grad{width:220px;height:12px;border-radius:6px;background:linear-gradient(90deg,#3b5bdb,#22b8cf,#40c057,#fab005,#f03e3e);}
</style>
</head>
<body>
<div id="app"></div>
<div id="ui">
  <h1>🔬 Resultados FEM reales del chasis</h1>
  <div class="btnrow" id="cases"></div>
  <div id="defrow">Deformación ×<span id="dval">150</span>
    <input type="range" id="defs" min="0" max="500" value="150">
  </div>
  <div id="stats"></div>
  <div class="btnrow"><button id="rot" class="active">⟳ Rotación</button></div>
</div>
<div id="cbar"><span>0 MPa</span><div id="grad"></div><span id="smax"></span><span style="color:#8b949e">· esfuerzo por tubo</span></div>

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
controls.target.set(1.6, 0.5, 0);
controls.enableDamping = true;
controls.autoRotate = true;
controls.autoRotateSpeed = 1.0;
scene.add(new THREE.HemisphereLight(0xdde7ff, 0x1a1d24, 0.8));
const sun = new THREE.DirectionalLight(0xffffff, 1.6);
sun.position.set(4,6,3); sun.castShadow = true; scene.add(sun);
const ground = new THREE.Mesh(new THREE.PlaneGeometry(30,30), new THREE.ShadowMaterial({opacity:0.4}));
ground.rotation.x = -Math.PI/2; ground.receiveShadow = true; scene.add(ground);
scene.add(new THREE.GridHelper(24, 48, 0x21262d, 0x161b22));

// colores tipo FEM: azul → cian → verde → amarillo → rojo
function femColor(t){
  const stops = [[0.23,0.36,0.86],[0.13,0.72,0.81],[0.25,0.75,0.34],[0.98,0.69,0.02],[0.94,0.24,0.24]];
  const s = Math.min(Math.max(t,0),1)*(stops.length-1);
  const i = Math.min(Math.floor(s), stops.length-2), f = s-i;
  const c = stops[i].map((v,k)=>v+(stops[i+1][k]-v)*f);
  return new THREE.Color(c[0],c[1],c[2]);
}

const tubes = [];
for (const e of DATA.elems){
  const mat = new THREE.MeshStandardMaterial({color:0x888888, metalness:0.4, roughness:0.45});
  const mesh = new THREE.Mesh(new THREE.CylinderGeometry(e.r, e.r, 1, 10), mat);
  mesh.castShadow = true;
  scene.add(mesh);
  tubes.push({e, mesh});
}

let caseName = Object.keys(DATA.cases)[0];
let defScale = 150;

function nodePos(n){
  const p = DATA.nodes[n], d = DATA.cases[caseName].disp[n];
  // disp está en mm → m, exagerada
  return new THREE.Vector3(
    p[0] + d[0]/1000*defScale,
    p[1] + d[1]/1000*defScale,
    p[2] + d[2]/1000*defScale);
}
function update(){
  const c = DATA.cases[caseName];
  for (let i = 0; i < tubes.length; i++){
    const {e, mesh} = tubes[i];
    const a = nodePos(e.a), b = nodePos(e.b);
    const d = new THREE.Vector3().subVectors(b, a);
    mesh.scale.set(1, d.length(), 1);
    mesh.position.copy(a).addScaledVector(d, 0.5);
    mesh.quaternion.setFromUnitVectors(new THREE.Vector3(0,1,0), d.clone().normalize());
    mesh.material.color.copy(femColor(c.sig[i]/c.sigmax));
  }
  document.getElementById('smax').textContent = c.sigmax + ' MPa';
  document.getElementById('stats').innerHTML =
    `<b>${caseName}</b><br>` +
    `FS mínimo: <b>${c.fsmin}</b> (límite fluencia 250 MPa)<br>` +
    `Tubo más esforzado: <b>${c.worst}</b> → ${c.sigmax} MPa<br>` +
    `Rigidez torsional: <b>${DATA.K_tors.toLocaleString()} N·m/°</b><br>` +
    `Masa del chasis: <b>${DATA.masa} kg</b> · 73 tubos · 41.9 m<br>` +
    `<span style="color:#8b949e">rojo = trabaja más · azul = descansa.<br>La deformación está exagerada ×${defScale} — la real es de milímetros.</span>`;
}

const cw = document.getElementById('cases');
Object.keys(DATA.cases).forEach((k, i) => {
  const b = document.createElement('button');
  b.textContent = k;
  if (i === 0) b.classList.add('active');
  b.onclick = () => {
    cw.querySelectorAll('button').forEach(x => x.classList.remove('active'));
    b.classList.add('active');
    caseName = k;
    update();
  };
  cw.appendChild(b);
});
document.getElementById('defs').oninput = (ev) => {
  defScale = +ev.target.value;
  document.getElementById('dval').textContent = defScale;
  update();
};
document.getElementById('rot').onclick = (e) => {
  controls.autoRotate = !controls.autoRotate;
  e.target.classList.toggle('active', controls.autoRotate);
};

camera.position.set(4.6, 1.8, 3.2);
update();
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
print(f"OK visor escrito: {out}  ({len(html)//1024} KB)")
