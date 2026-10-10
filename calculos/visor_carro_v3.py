# -*- coding: utf-8 -*-
"""
Visor 3D interactivo del carro v3 (carrocería de subdivisión + detalle + interior).

Embebe cad/carro-v3.glb en un HTML autónomo con three.js: se abre con doble clic, sin
servidor. Vistas de la lámina (frontal, lateral, cenital, trasera, tres cuartos),
cristal transparente, luces encendidas, cotas del paquete, y se pueden ocultar las
ruedas / interior / pilotos para inspeccionar la piel sola.

Correr:  python calculos/visor_carro_v3.py
Salida:  carro-diseno-3d.html
"""
import base64
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.join(HERE, "..")
GLB = os.path.join(RAIZ, "cad", "carro-v3.glb")
JAULA = json.load(open(os.path.join(RAIZ, "cad", "carro-v3-jaula.json"), encoding="utf-8"))
P = JAULA["paquete"]

b64 = base64.b64encode(open(GLB, "rb").read()).decode("ascii")
cotas = {"largo": round(P["x_cola"] - P["x_morro"], 3), "ancho": round(2 * P["semi"], 3),
         "alto": P["alto"], "batalla": round(P["eje_tras"] - P["eje_del"], 3),
         "x_morro": P["x_morro"], "x_cola": P["x_cola"], "eje_del": P["eje_del"],
         "eje_tras": P["eje_tras"]}

HTML = r"""<!DOCTYPE html>
<html lang="es"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Carro v3 — diseño 3D</title>
<style>
 *{box-sizing:border-box}
 html,body{margin:0;height:100%;background:#0c1016;overflow:hidden;color:#c9d1d9;
  font-family:ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif}
 #app{position:fixed;inset:0}
 .panel{background:#131820ee;border:1px solid #262d38;border-radius:12px;padding:12px 14px;
  font-size:12px;line-height:1.55;backdrop-filter:blur(10px);box-shadow:0 6px 24px #0007}
 #izq{position:fixed;top:12px;left:12px;z-index:10;width:270px;display:flex;
  flex-direction:column;gap:9px}
 h1{color:#f0f6fc;font-size:15px;margin:0 0 6px;letter-spacing:-.01em}
 h2{color:#7d8590;font-size:10px;margin:0 0 8px;text-transform:uppercase;
  letter-spacing:.1em;font-weight:650}
 button{background:#1a212b;color:#c9d1d9;border:1px solid #2b3441;border-radius:8px;
  padding:6px 10px;font-size:11.5px;cursor:pointer;font-family:inherit;transition:all .12s}
 button:hover{background:#232c38}
 button.on{background:#1f6feb;border-color:#1f6feb;color:#fff}
 .row{display:flex;flex-wrap:wrap;gap:5px}
 table{border-collapse:collapse;width:100%}
 td{padding:2px 0;color:#7d8590}
 td:last-child{text-align:right;color:#e6edf3;font-family:ui-monospace,monospace}
 #hint{position:fixed;bottom:12px;left:50%;transform:translateX(-50%);z-index:10;
  color:#5c6570;font-size:11px;text-align:center}
 #carga{position:fixed;inset:0;display:flex;align-items:center;justify-content:center;
  color:#7d8590;font-size:14px;z-index:20;background:#0c1016}
</style></head><body>
<div id="carga">cargando modelo…</div>
<div id="izq">
 <div class="panel">
  <h1>Carro v3 — diseño 3D</h1>
  <div style="color:#7d8590">Carrocería de subdivisión sobre el paquete real. Luces, parrilla,
  difusor y cristal tomados de tu lámina; ruedas y ejes donde ya están.</div>
 </div>
 <div class="panel"><h2>Vistas de la lámina</h2>
  <div class="row">
   <button data-v="34">3/4 frente</button><button data-v="34t">3/4 atrás</button>
   <button data-v="frontal">frontal</button><button data-v="trasera">trasera</button>
   <button data-v="lateral">lateral</button><button data-v="cenital">cenital</button>
  </div></div>
 <div class="panel"><h2>Ver</h2>
  <div class="row">
   <button id="bRuedas" class="on">ruedas</button><button id="bInterior" class="on">interior</button>
   <button id="bPilotos" class="on">pilotos</button><button id="bLuces" class="on">luces</button>
   <button id="bCristal" class="on">cristal</button><button id="bMalla">malla</button>
   <button id="bGiro">girar</button>
  </div></div>
 <div class="panel"><h2>Paquete</h2>
  <table>
   <tr><td>largo</td><td>__LARGO__ m</td></tr>
   <tr><td>ancho</td><td>__ANCHO__ m</td></tr>
   <tr><td>alto</td><td>__ALTO__ m</td></tr>
   <tr><td>batalla</td><td>__BATALLA__ m</td></tr>
   <tr><td>piezas</td><td id="npiezas">…</td></tr>
  </table></div>
</div>
<div id="hint">arrastra para girar · rueda para acercar · clic derecho para desplazar</div>
<div id="app"></div>
<script type="importmap">{"imports":{
 "three":"https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js",
 "three/addons/":"https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/"}}</script>
<script type="module">
import * as THREE from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {RoomEnvironment} from 'three/addons/environments/RoomEnvironment.js';

const COTAS = __COTAS__;
const GLB_B64 = "__GLB__";

const app = document.getElementById('app');
const renderer = new THREE.WebGLRenderer({antialias:true});
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
renderer.setSize(innerWidth, innerHeight);
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.0;
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
app.appendChild(renderer.domElement);

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x0c1016);
const pmrem = new THREE.PMREMGenerator(renderer);
scene.environment = pmrem.fromScene(new RoomEnvironment(renderer), 0.04).texture;

const camera = new THREE.PerspectiveCamera(32, innerWidth/innerHeight, 0.05, 200);
const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.maxPolarAngle = Math.PI/2 - 0.01;
const centro = new THREE.Vector3((COTAS.x_morro + COTAS.x_cola)/2, 0.45, 0);
controls.target.copy(centro);

// luces: una clave alta, relleno frío, y sombra al piso
const sol = new THREE.DirectionalLight(0xfff2e0, 2.2);
sol.position.set(centro.x + 3, 6, -4); sol.castShadow = true;
sol.shadow.mapSize.set(2048, 2048);
sol.shadow.camera.left = -4; sol.shadow.camera.right = 4;
sol.shadow.camera.top = 4; sol.shadow.camera.bottom = -4;
sol.shadow.bias = -0.0005;
scene.add(sol);
const relleno = new THREE.DirectionalLight(0xd8e6ff, 0.8);
relleno.position.set(centro.x - 4, 3, 4); scene.add(relleno);
scene.add(new THREE.HemisphereLight(0xa9b8cc, 0x1a1d24, 0.5));

// piso con sombra y rejilla de 0.5 m
const piso = new THREE.Mesh(new THREE.PlaneGeometry(40, 40),
  new THREE.MeshStandardMaterial({color:0x141820, roughness:0.95, metalness:0}));
piso.rotation.x = -Math.PI/2; piso.receiveShadow = true; scene.add(piso);
const grid = new THREE.GridHelper(40, 80, 0x2a313c, 0x1c2229);
grid.position.y = 0.001; scene.add(grid);

// el modelo
const grupos = {ruedas:[], interior:[], pilotos:[], luces:[], cristal:[], cuerpo:[]};
const loader = new GLTFLoader();
const bin = Uint8Array.from(atob(GLB_B64), c => c.charCodeAt(0));
loader.parse(bin.buffer, '', (gltf) => {
  const raiz = gltf.scene;
  let n = 0;
  raiz.traverse(o => {
    if (!o.isMesh) return;
    n++;
    o.castShadow = true; o.receiveShadow = true;
    const nom = o.name || '';
    const mat = o.material;
    const mnom = (mat && mat.name) || '';
    if (mnom.startsWith('vidrio')) {
      o.material = new THREE.MeshPhysicalMaterial({color:0x1a1c20, metalness:0, roughness:0.05,
        transmission:0.0, transparent:true, opacity:0.42, envMapIntensity:1.6, clearcoat:1,
        side:THREE.DoubleSide});
      grupos.cristal.push(o);
    } else if (mnom.startsWith('pintura')) {
      o.material = new THREE.MeshPhysicalMaterial({color:0x4e4744, metalness:0.25, roughness:0.34,
        clearcoat:1.0, clearcoatRoughness:0.04, envMapIntensity:1.0});
      grupos.cuerpo.push(o);
    } else if (mnom.startsWith('luz_d')) {
      o.material = new THREE.MeshStandardMaterial({color:0xbfe6ff, emissive:0xbfe6ff, emissiveIntensity:3});
      grupos.luces.push(o);
    } else if (mnom.startsWith('luz_t')) {
      o.material = new THREE.MeshStandardMaterial({color:0xff1a10, emissive:0xff1a10, emissiveIntensity:3});
      grupos.luces.push(o);
    } else if (mat) {
      mat.side = THREE.DoubleSide;
    }
    if (/^(Llanta|Rin|Cubo|Rayo|Disco|Caliper)/.test(nom)) grupos.ruedas.push(o);
    if (/^(Butaca|Respaldo|Tablero|Tunel|PisoCabina|Volante|Columna)/.test(nom)) grupos.interior.push(o);
    if (/^(Piloto|Cabeza)/.test(nom)) grupos.pilotos.push(o);
  });
  scene.add(raiz);
  document.getElementById('npiezas').textContent = n;
  document.getElementById('carga').remove();
  vista('34');
}, (e) => { document.getElementById('carga').textContent = 'error al cargar: ' + e; });

const L = COTAS.largo;
const VISTAS = {
  '34':      [centro.x - 1.15*L, 0.6*L, 1.15*L],
  '34t':     [centro.x + 1.15*L, 0.55*L, -1.1*L],
  'frontal': [centro.x - 1.6*L, 0.28*L, 0],
  'trasera': [centro.x + 1.6*L, 0.28*L, 0],
  'lateral': [centro.x, 0.25*L, 1.6*L],
  'cenital': [centro.x, 1.9*L, 0.0001],
};
function vista(k){
  const p = VISTAS[k];
  camera.position.set(p[0], p[1], p[2]);
  controls.target.copy(centro); controls.update();
  document.querySelectorAll('[data-v]').forEach(b => b.classList.toggle('on', b.dataset.v === k));
}
document.querySelectorAll('[data-v]').forEach(b => b.onclick = () => vista(b.dataset.v));

function toggle(id, grupo, fn){
  const b = document.getElementById(id);
  b.onclick = () => { b.classList.toggle('on'); const on = b.classList.contains('on');
    (fn || (o => { o.visible = on; }))(on); };
  if (!fn) { /* visible al inicio */ }
}
toggle('bRuedas', 'ruedas', on => grupos.ruedas.forEach(o => o.visible = on));
toggle('bInterior', 'interior', on => grupos.interior.forEach(o => o.visible = on));
toggle('bPilotos', 'pilotos', on => grupos.pilotos.forEach(o => o.visible = on));
toggle('bLuces', 'luces', on => grupos.luces.forEach(o => o.material.emissiveIntensity = on ? 3 : 0));
toggle('bCristal', 'cristal', on => grupos.cristal.forEach(o => o.material.opacity = on ? 0.42 : 1.0));
toggle('bMalla', 'cuerpo', on => grupos.cuerpo.forEach(o => o.material.wireframe = on));
let girando = false;
toggle('bGiro', null, on => { girando = on; controls.autoRotate = on; controls.autoRotateSpeed = 0.9; });

addEventListener('resize', () => { camera.aspect = innerWidth/innerHeight; camera.updateProjectionMatrix();
  renderer.setSize(innerWidth, innerHeight); });
(function loop(){ requestAnimationFrame(loop); controls.update(); renderer.render(scene, camera); })();
</script></body></html>
"""

html = (HTML.replace("__COTAS__", json.dumps(cotas)).replace("__GLB__", b64)
        .replace("__LARGO__", f"{cotas['largo']:.2f}").replace("__ANCHO__", f"{cotas['ancho']:.2f}")
        .replace("__ALTO__", f"{cotas['alto']:.2f}").replace("__BATALLA__", f"{cotas['batalla']:.2f}"))
out = os.path.join(RAIZ, "carro-diseno-3d.html")
with open(out, "w", encoding="utf-8") as f:
    f.write(html)
print(f"OK  {out}  ({len(html) / 1e6:.1f} MB, GLB {os.path.getsize(GLB) / 1e6:.1f} MB)")
