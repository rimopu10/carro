# -*- coding: utf-8 -*-
"""
Visor 3D autónomo: carrocería de Tripo (ventanas cerradas, sin las ruedas de IA) + el chasis vigente
(cad/chasis.json) + ruedas de relleno + el piloto de 1.75 m (buck_piloto.py) + las puertas de gaviota que
abren con su herraje (puertas.py). Vistas desde los ojos del piloto y del pasajero.

    python calculos/visor_tripo_chasis.py <stl_decimado_mm> [salida.html]
Salida por defecto: carro-tripo-chasis-3d.html (three.js desde CDN, abre con doble clic).
Las puertas son las piezas de cad/_gaviota-1a20 (tripo_gaviota.py) a escala real; son geometría de juguete
(piel sin panel interior), no el diseño constructivo final.
"""
import base64
import json
import os
import sys

import numpy as np
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
RAIZ = os.path.join(HERE, "..")
import buck_piloto as BK          # noqa: E402
import hueco_puerta as HP         # noqa: E402
import puertas as PU              # noqa: E402

ch = json.load(open(os.path.join(RAIZ, "cad", "chasis.json"), encoding="utf-8"))

piel = trimesh.load(sys.argv[1])
piel.apply_scale(0.001)
V = np.asarray(piel.vertices, np.float32)
F = np.asarray(piel.faces, np.uint32)
b64 = lambda a: base64.b64encode(np.ascontiguousarray(a).tobytes()).decode("ascii")

# ---- puertas: las piezas EXACTAS del juguete 1:20 (cad/_gaviota-1a20, tripo_gaviota.py) a escala real ------------
# (x20 / 1000 = metros). Se quitan de la carrocería las caras que ocupan, para que al abrir quede el hueco.
def cargar_puerta(nombre):
    m = trimesh.load(os.path.join(RAIZ, "cad", "_gaviota-1a20", nombre))
    m.apply_scale(0.02)
    return m


pz = {"izq_chasis": cargar_puerta("puerta-der.stl"),      # el juguete llama 'der' a z>0 = lado del piloto (L del chasis)
      "der_chasis": cargar_puerta("puerta-izq.stl")}
cent = V[F].mean(axis=1)
quitar = np.zeros(len(F), bool)
for m in pz.values():
    lo, hi = m.bounds[0] - 0.02, m.bounds[1] + 0.02
    cand = np.where(((cent >= lo) & (cent <= hi)).all(axis=1))[0]
    if len(cand):
        d = np.abs(trimesh.proximity.closest_point(m, cent[cand])[1])
        quitar[cand[d < 0.015]] = True
F_cuerpo = F[~quitar]
VL, FL = np.asarray(pz["izq_chasis"].vertices, np.float32), np.asarray(pz["izq_chasis"].faces, np.uint32)
VR, FR = np.asarray(pz["der_chasis"].vertices, np.float32), np.asarray(pz["der_chasis"].faces, np.uint32)

# ---- piloto y puertas ---------------------------------------------------------------------------------------
nom = BK.postura(BK.NOMINAL["hx"], BK.NOMINAL["hy"], BK.NOMINAL["recline"])
ojo = BK.metricas(nom)["ojo"]
maniqui = []
for z in (0.31, -0.31):
    for c in BK.capsulas(nom, z=z):
        maniqui.append({"a": [float(v) for v in c["a"]], "b": [float(v) for v in c["b"]], "r": c["r"], "n": c["nombre"]})
her = {k: [float(x) for x in v] for k, v in PU.herraje().items()}
puerta = {"a0L": [float(x) for x in PU.EJE_A0], "a0R": [float(PU.EJE_A0[0]), float(PU.EJE_A0[1]), -float(PU.EJE_A0[2])],
          "u": [float(x) for x in PU.EJE_U], "max": PU.THETA_MAX, "herraje": her, "fuerza": PU.FUERZA_NOMINAL}

datos = {
    "v": b64(V), "fb": b64(F_cuerpo), "vl": b64(VL), "fl": b64(FL), "vr": b64(VR), "fr": b64(FR),
    "tubos": [{"a": t["a"], "b": t["b"], "tag": t["tag"], "nom": t["nom"],
               "r": (t["sec"].get("d") or t["sec"].get("b")) / 2} for t in ch["tubos"]],
    "ruedas": ch["ruedas"], "maniqui": maniqui, "puerta": puerta, "ojo": [float(ojo[0]), float(ojo[1])],
}

HTML = r"""<!DOCTYPE html>
<html lang="es"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Chasis, piloto y puertas</title>
<style>
 html,body{margin:0;height:100%;background:#0c1016;overflow:hidden;color:#c9d1d9;
  font-family:ui-sans-serif,system-ui,"Segoe UI",sans-serif}
 #app{position:fixed;inset:0}
 #p{position:fixed;top:12px;left:12px;width:270px;background:#131820ee;border:1px solid #262d38;
  border-radius:12px;padding:12px 14px;font-size:12px;line-height:1.6;z-index:5}
 h1{font-size:14px;margin:0 0 6px} label{display:block;cursor:pointer}
 input[type=range]{width:100%} button{background:#1c2430;color:#c9d1d9;border:1px solid #2d3745;
  border-radius:8px;padding:5px 9px;margin:2px 2px 0 0;cursor:pointer;font-size:12px}
 button:hover{background:#26303f} small{color:#8b96a5}
 .sw{display:inline-block;width:10px;height:10px;border-radius:2px;margin-right:6px}
</style></head><body><div id="app"></div>
<div id="p"><h1>Chasis, piloto y puertas</h1>
 <label>Opacidad de la carrocería <span id="ov"></span><input id="op" type="range" min="0" max="100" value="30"></label>
 <label>Apertura de las puertas <span id="dv">0°</span><input id="pu" type="range" min="0" max="__MAX__" value="0"></label>
 <label><input type="checkbox" id="cb" checked> Carrocería</label>
 <label><input type="checkbox" id="cc" checked> Chasis (__NT__ tubos)</label>
 <label><input type="checkbox" id="cm" checked> Piloto 1.75 m</label>
 <label><input type="checkbox" id="ch" checked> Herraje de puertas</label>
 <label><input type="checkbox" id="cr" checked> Ruedas (relleno)</label>
 <div style="margin-top:6px">
  <button data-v="3q">3/4</button><button data-v="lat">Lado</button><button data-v="top">Arriba</button>
  <button data-v="fr">Frente</button><button data-v="ab">Debajo</button>
  <button data-v="ojo">Ojos piloto</button><button data-v="ojoP">Ojos pasajero</button>
  <button data-v="ojoA">Atrás piloto</button><button data-v="puerta">Puerta abierta</button></div>
 <div style="margin-top:8px"><span class="sw" style="background:#f2c14e"></span>seguridad (célula/pilares)
  <br><span class="sw" style="background:#59b3ff"></span>suspensión
  <br><span class="sw" style="background:#7bd88f"></span>batería
  <br><span class="sw" style="background:#ff8a4c"></span>travesaños de asientos
  <br><span class="sw" style="background:#c8ced6"></span>resto / diagonales
  <br><span class="sw" style="background:#e0a060"></span>puerta · <span class="sw" style="background:#ffd23f"></span>bisagras
  · <span class="sw" style="background:#4de1ff"></span>cierres · <span class="sw" style="background:#fff"></span>amortiguador</div>
 <div style="margin-top:8px"><small>Chasis rediseñado para el piloto real (1.75 m, asiento hundido sobre rieles) y las
 puertas de gaviota. Las puertas son las piezas del juguete 1:20 a escala real. Amortiguador de
 __FUERZA__ N. Las ruedas son de relleno.</small></div>
 <div id="hover" style="margin-top:6px;color:#f2c14e"></div></div>
<script type="importmap">{"imports":{"three":"https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js",
 "three/addons/":"https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/"}}</script>
<script type="module">
import * as THREE from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
const D = __DATOS__;
const dec = (s,T)=>{const b=atob(s),u=new Uint8Array(b.length);for(let i=0;i<b.length;i++)u[i]=b.charCodeAt(i);return new T(u.buffer)};
const app=document.getElementById('app');
const R=new THREE.WebGLRenderer({antialias:true});R.setPixelRatio(devicePixelRatio);
R.setSize(innerWidth,innerHeight);app.appendChild(R.domElement);
const S=new THREE.Scene();S.background=new THREE.Color(0x0c1016);
const C=new THREE.PerspectiveCamera(35,innerWidth/innerHeight,0.01,50);
const O=new OrbitControls(C,R.domElement);O.target.set(1.6,0.45,0);O.enableDamping=true;
S.add(new THREE.HemisphereLight(0xffffff,0x223044,1.1));
const L=new THREE.DirectionalLight(0xffffff,1.6);L.position.set(3,5,4);S.add(L);
// ejes del proyecto: x hacia atrás, y arriba, z lateral (+z = izquierda, lado del piloto): son los de three
const pos=new THREE.BufferAttribute(dec(D.v,Float32Array),3);
const geo=(idx,verts)=>{const g=new THREE.BufferGeometry();
 g.setAttribute('position',verts?new THREE.BufferAttribute(dec(verts,Float32Array),3):pos);
 g.setIndex(new THREE.BufferAttribute(dec(idx,Uint32Array),1));g.computeVertexNormals();return g};
const mk=(c)=>new THREE.MeshStandardMaterial({color:c,metalness:.35,roughness:.35,transparent:true,
 opacity:.3,side:THREE.DoubleSide,depthWrite:false});
const mat=mk(0xb8c4d6), matD=mk(0xe0a060);
const body=new THREE.Mesh(geo(D.fb),mat);S.add(body);
const grid=new THREE.GridHelper(8,32,0x2a3442,0x1a222d);grid.position.set(1.6,0,0);S.add(grid);
const col={safe:0xf2c14e,susp:0x59b3ff,batt:0x7bd88f,asiento:0xff8a4c};
const tubes=new THREE.Group();
for(const t of D.tubos){const a=new THREE.Vector3(...t.a),b=new THREE.Vector3(...t.b);
 const len=a.distanceTo(b);const m=new THREE.Mesh(new THREE.CylinderGeometry(t.r,t.r,len,10),
  new THREE.MeshStandardMaterial({color:col[t.tag]||0xc8ced6,metalness:.6,roughness:.4}));
 m.position.copy(a).add(b).multiplyScalar(.5);
 m.quaternion.setFromUnitVectors(new THREE.Vector3(0,1,0),b.clone().sub(a).normalize());
 m.userData.nom=t.nom;tubes.add(m);}
S.add(tubes);
const wh=new THREE.Group();
for(const w of D.ruedas){const m=new THREE.Mesh(new THREE.CylinderGeometry(w.R,w.R,w.W,40),
 new THREE.MeshStandardMaterial({color:0x15191f,roughness:.9}));m.rotation.x=Math.PI/2;
 m.position.set(w.x,w.R,w.z);wh.add(m);}
S.add(wh);
// piloto: cápsulas del buck
const man=new THREE.Group();
for(const c of D.maniqui){const a=new THREE.Vector3(...c.a),b=new THREE.Vector3(...c.b),d=b.clone().sub(a),len=d.length();
 const m=new THREE.Mesh(new THREE.CapsuleGeometry(c.r,Math.max(len,1e-4),6,14),
  new THREE.MeshStandardMaterial({color:0xe0b090,transparent:true,opacity:.5,roughness:.8}));
 m.position.copy(a).add(b).multiplyScalar(.5);
 if(len>1e-4)m.quaternion.setFromUnitVectors(new THREE.Vector3(0,1,0),d.normalize());man.add(m);}
S.add(man);
// puertas + herraje
const P=D.puerta, u=new THREE.Vector3(...P.u);
const sph=(p,c,r=.016)=>{const m=new THREE.Mesh(new THREE.SphereGeometry(r,14,10),new THREE.MeshBasicMaterial({color:c}));
 m.position.set(...p);return m};
const mir=p=>[p[0],p[1],-p[2]];
const door={L:new THREE.Group(),R:new THREE.Group()};
const doorMesh={L:new THREE.Mesh(geo(D.fl,D.vl),matD),R:new THREE.Mesh(geo(D.fr,D.vr),matD)};
const hw=new THREE.Group();
for(const s of ['L','R']){door[s].matrixAutoUpdate=false;door[s].add(doorMesh[s]);S.add(door[s]);
 const f=s==='L'?(p=>p):mir, H=P.herraje;
 door[s].add(sph(f(H.amortiguador_puerta),0xffffff,.018));
 for(const k of ['bisagra_1','bisagra_2'])hw.add(sph(f(H[k]),0xffd23f,.022));
 for(const k of ['cierre_techo_delantero','cierre_estribo_delantero','cierre_estribo_trasero','cierre_trasero'])hw.add(sph(f(H[k]),0x4de1ff,.018));
 hw.add(sph(f(H.amortiguador_chasis),0xffffff,.018));}
S.add(hw);
const strutGeo={L:new THREE.BufferGeometry(),R:new THREE.BufferGeometry()};
const struts=new THREE.Group();
for(const s of ['L','R']){strutGeo[s].setAttribute('position',new THREE.BufferAttribute(new Float32Array(6),3));
 struts.add(new THREE.Line(strutGeo[s],new THREE.LineBasicMaterial({color:0xffffff})));}
S.add(struts);
function setDoor(th){
 for(const s of ['L','R']){const a0=new THREE.Vector3(...(s==='L'?P.a0L:P.a0R));
  const ang=(s==='L'?-1:1)*th*Math.PI/180;      // el lado derecho es el espejo: gira al revés
  const M=new THREE.Matrix4().makeTranslation(a0.x,a0.y,a0.z)
   .multiply(new THREE.Matrix4().makeRotationAxis(u,ang)).multiply(new THREE.Matrix4().makeTranslation(-a0.x,-a0.y,-a0.z));
  door[s].matrix.copy(M);door[s].matrixWorldNeedsUpdate=true;
  const f=s==='L'?(p=>p):mir,H=P.herraje;
  const pd=new THREE.Vector3(...f(H.amortiguador_puerta)).applyMatrix4(M),sa=new THREE.Vector3(...f(H.amortiguador_chasis));
  strutGeo[s].attributes.position.set([sa.x,sa.y,sa.z,pd.x,pd.y,pd.z]);strutGeo[s].attributes.position.needsUpdate=true;}
 document.getElementById('dv').textContent=th+'°';}
setDoor(0);
const $=id=>document.getElementById(id);
const setOp=()=>{mat.opacity=$('op').value/100;matD.opacity=Math.min(1,$('op').value/100+.25);$('ov').textContent=$('op').value+'%'};
$('op').oninput=setOp;setOp();
$('pu').oninput=e=>setDoor(+e.target.value);
$('cb').onchange=e=>{body.visible=e.target.checked;doorMesh.L.visible=doorMesh.R.visible=e.target.checked};
$('cc').onchange=e=>tubes.visible=e.target.checked;
$('cm').onchange=e=>man.visible=e.target.checked;
$('ch').onchange=e=>{hw.visible=struts.visible=e.target.checked};
$('cr').onchange=e=>wh.visible=e.target.checked;
const [ex,ey]=D.ojo;
const V={'3q':[[-1.6,1.5,3.6],[1.7,.5,0]],'lat':[[1.7,.6,6.2],[1.7,.5,0]],'top':[[1.7,6.5,.01],[1.7,.4,0]],
 'fr':[[-4.5,.8,.01],[1.7,.5,0]],'ab':[[1.7,-5,.01],[1.7,.3,0]],
 'ojo':[[ex,ey,.31],[ex-1.3,ey-.09,.28],85],'ojoP':[[ex,ey,-.31],[ex-1.3,ey-.09,-.28],85],
 'ojoA':[[ex,ey,.31],[ex+1.5,ey,.31],85],'puerta':[[-0.5,1.3,3.2],[1.7,.7,.6],40]};
document.querySelectorAll('button').forEach(b=>b.onclick=()=>{const v=V[b.dataset.v];
 C.position.set(...v[0]);O.target.set(...v[1]);C.fov=v[2]||35;C.updateProjectionMatrix();
 if(b.dataset.v==='puerta'){$('pu').value=P.max;setDoor(P.max);}});
C.position.set(...V['3q'][0]);
const ray=new THREE.Raycaster(),mp=new THREE.Vector2();
R.domElement.addEventListener('pointermove',e=>{mp.set(e.clientX/innerWidth*2-1,-(e.clientY/innerHeight)*2+1);
 ray.setFromCamera(mp,C);const h=ray.intersectObjects(tubes.children)[0];
 $('hover').textContent=h?h.object.userData.nom:''});
addEventListener('resize',()=>{R.setSize(innerWidth,innerHeight);C.aspect=innerWidth/innerHeight;C.updateProjectionMatrix()});
(function loop(){O.update();R.render(S,C);requestAnimationFrame(loop)})();
</script></body></html>"""

salida = sys.argv[2] if len(sys.argv) > 2 else os.path.join(RAIZ, "carro-tripo-chasis-3d.html")
html = (HTML.replace("__DATOS__", json.dumps(datos)).replace("__NT__", str(len(ch["tubos"])))
        .replace("__MAX__", str(int(PU.THETA_MAX))).replace("__FUERZA__", f"{PU.FUERZA_NOMINAL:.0f}"))
open(salida, "w", encoding="utf-8").write(html)
print("OK", salida, f"{os.path.getsize(salida)/1e6:.1f} MB",
      f"| carrocería {len(F_cuerpo)} de {len(F)} caras (se quitaron {int(quitar.sum())} de las puertas)")
