# -*- coding: utf-8 -*-
"""
Carrocería desde Tripo AI por API (SDK oficial `pip install tripo3d`).

Flujo para tener vistas de todos los lados QUE CORRESPONDAN entre sí:

  1. vistas   una foto (la de tres cuartos) -> Tripo genera frente / izquierda /
              atrás / derecha del MISMO carro, consistentes entre sí
  2. editar   (opcional) corregir una vista con texto, p.ej. la trasera para que
              lleve la barra de luz y el triángulo de la lámina
  3. modelo   las 4 vistas -> modelo 3D (GLB)

    python calculos/tripo.py saldo
    python calculos/tripo.py vistas ref/tripo/1-tres_cuartos.png
    python calculos/tripo.py editar <tarea> back "a thin continuous red light bar ..."
    python calculos/tripo.py modelo <tarea>
    python calculos/tripo.py modelo ref/tripo/multivista   # las 4 vistas de la lámina alineadas
                                                             # (calculos/vistas_tripo.py)
    python calculos/tripo.py imagen ref/tripo/1-tres_cuartos.png     # atajo: una foto -> 3D

La clave NO va en el repo: se lee de la variable TRIPO_API_KEY o del archivo
%USERPROFILE%\\.tripo_key. Cada tarea queda anotada en ref/tripo/tareas.json con lo
que costó, para poder retomar sin volver a pagar.
"""
import argparse
import asyncio
import json
import os
import time

from tripo3d import TripoClient

HERE = os.path.dirname(os.path.abspath(__file__))
DIR = os.path.normpath(os.path.join(HERE, "..", "ref", "tripo"))
REGISTRO = os.path.join(DIR, "tareas.json")
VERSION = "P1-20260311"            # la más reciente que acepta el SDK 0.4.2
# Orden de `files` en multiview_to_model: frente, izquierda, atrás, derecha (doc de la
# API, docs.tripo3d.ai "Multiview to model"). OJO: el README del SDK 0.4.2 los lista
# frente, atrás, izquierda, derecha; manda la doc de la API. Una vista faltante va
# como {} (el SDK lo hace al pasar None); la frontal es obligatoria.
ORDEN_VISTAS = ("front", "left", "back", "right")


def clave():
    k = os.environ.get("TRIPO_API_KEY")
    if not k:
        ruta = os.path.join(os.path.expanduser("~"), ".tripo_key")
        if os.path.exists(ruta):
            k = open(ruta, encoding="utf-8").read().strip()
    if not k:
        raise SystemExit("Falta la clave: crea una en platform.tripo3d.ai y guárdala en "
                         "%USERPROFILE%\\.tripo_key (una sola línea).")
    return k


def anotar(tarea, tipo, entrada, archivos, saldo_antes, saldo_despues):
    reg = json.load(open(REGISTRO, encoding="utf-8")) if os.path.exists(REGISTRO) else []
    reg.append({"tarea": tarea, "tipo": tipo, "entrada": entrada, "archivos": archivos,
                "creditos": None if saldo_antes is None else round(saldo_antes - saldo_despues, 2),
                "fecha": time.strftime("%Y-%m-%d %H:%M")})
    json.dump(reg, open(REGISTRO, "w", encoding="utf-8"), indent=1, ensure_ascii=False)


async def _saldo(c):
    try:
        return float((await c.get_balance()).balance)
    except Exception:
        return None


async def correr(tipo, crear, entrada):
    os.makedirs(DIR, exist_ok=True)
    async with TripoClient(api_key=clave()) as c:
        antes = await _saldo(c)
        tid = await crear(c)
        print(f"tarea {tid} ({tipo}) enviada; esperando...")
        t = await c.wait_for_task(tid, verbose=True)
        if str(t.status).lower().split(".")[-1] != "success":
            raise SystemExit(f"la tarea terminó en {t.status}")
        sal = os.path.join(DIR, tid)
        os.makedirs(sal, exist_ok=True)
        archivos = {k: v for k, v in (await c.download_task_models(t, sal)).items() if v}
        despues = await _saldo(c)
    rel = {k: os.path.relpath(v, os.path.join(DIR, "..", "..")) for k, v in archivos.items()}
    anotar(tid, tipo, entrada, rel, antes, despues)
    for k, v in rel.items():
        print(f"   {k:12s} {v}")
    if antes is not None and despues is not None:
        print(f"   créditos usados {antes - despues:.0f}, quedan {despues:.0f}")
    return tid, archivos


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("saldo")
    p = sub.add_parser("vistas"); p.add_argument("imagen")
    p = sub.add_parser("editar"); p.add_argument("tarea"); p.add_argument("vista", choices=ORDEN_VISTAS)
    p.add_argument("prompt")
    p = sub.add_parser("modelo")
    p.add_argument("tarea", help="tarea de 'vistas'/'editar', o carpeta con front/left/back/right.png")
    p.add_argument("--rapido", action="store_true", help="calidad estándar (más barato)")
    p = sub.add_parser("imagen"); p.add_argument("imagen")
    p.add_argument("--rapido", action="store_true")
    a = ap.parse_args()

    calidad = {} if getattr(a, "rapido", False) else {"geometry_quality": "detailed",
                                                      "texture_quality": "detailed"}
    if a.cmd == "saldo":
        async def s():
            async with TripoClient(api_key=clave()) as c:
                print(f"saldo: {await _saldo(c)} créditos")
        asyncio.run(s())
    elif a.cmd == "vistas":
        asyncio.run(correr("vistas", lambda c: c.generate_multiview_image(a.imagen), a.imagen))
    elif a.cmd == "editar":
        asyncio.run(correr("editar", lambda c: c.edit_multiview_image(
            a.tarea, [{"view": a.vista, "prompt": a.prompt}]), f"{a.tarea}:{a.vista}"))
    elif a.cmd == "modelo":
        d = a.tarea if os.path.isdir(a.tarea) else os.path.join(DIR, a.tarea)
        vistas = []
        for v in ORDEN_VISTAS:
            f = [x for x in os.listdir(d) if x.split(".")[0] == v
                 or x.split(".")[0].endswith("_" + v)]
            vistas.append(os.path.join(d, f[0]) if f else None)
        print("vistas:", {v: (os.path.basename(f) if f else None) for v, f in zip(ORDEN_VISTAS, vistas)})
        if vistas[0] is None:
            raise SystemExit(f"no encuentro la vista frontal en {d}")
        asyncio.run(correr("modelo", lambda c: c.multiview_to_model(
            vistas, model_version=VERSION, **calidad), a.tarea))
    elif a.cmd == "imagen":
        asyncio.run(correr("imagen", lambda c: c.image_to_model(
            a.imagen, model_version=VERSION, **calidad), a.imagen))


if __name__ == "__main__":
    main()
