# Juguete de gaviota 1:20 — listo para la Ender 3 V3 SE

Generado con `python calculos/tripo_gaviota.py --impresora ender3v3se`, que toma los
ajustes de `impresion/impresoras/ender3v3se.json` (sacados de `impresora3d.md`). El
diseño no cambia: si un día usas otra impresora se crea otro perfil y estos archivos
se quedan aquí, sin mezclarse.

**Qué cambia respecto al diseño, sólo para esta impresora:**
- Holgura puerta–carrocería de **0.4 mm** (el diseño usa 0.3), por los bordes
  abultados que todavía no se han resuelto.
- Agujeros **medidos con tu regla de prueba** (2026-10-09: 2.0 no entra, 2.1 firme,
  2.2 con roce leve): ajuste a presión **2.1 mm** (cubo de rueda y pasador en la
  carrocería) y ajuste libre **2.3 mm** (eje de rueda en la carrocería y pasador en la
  puerta).
- Cada pieza cabe en 206 mm, para que quepa el brim automático de 5 mm.

## Orden de impresión

| # | Archivo | Tamaño | PLA | Para qué |
|---|---|---|---|---|
| 0 | `prueba-tolerancias-ejes.stl` | 62 × 16 × 10 mm | 5 g | ya impresa: de aquí salieron 2.1 / 2.3 |
| 1 | `gaviota-1a20-placa1-carroceria.stl` | 198 × 89 × 52 mm | ~142 g | carrocería, apoyada en su piso |
| 2 | `gaviota-1a20-placa2-puertas-y-ruedas.stl` | 191 × 63 × 41 mm | ~41 g | 2 puertas paradas sobre su canto y 4 ruedas acostadas |

Si al armar algo queda muy duro o muy flojo, se cambia `agujeros_mm` en
`impresion/impresoras/ender3v3se.json` y se regenera; el diseño no se toca.

## Laminar en la PC con Linux (con tus perfiles corregidos)

Esta pieza necesita soportes y `process_fixed2.json` no los tiene: la cabina va hueca
bajo el techo (los soportes salen por el hueco de las puertas) y están los pozos de
rueda. Crea una sola vez una copia del proceso con soportes de árbol:

```bash
cd <carpeta donde está perfiles_orcaslicer>
python3 - <<'PY'
import json
p = json.load(open("perfiles_orcaslicer/process_fixed2.json"))
p.update({"name": "process_fixed2_soportes", "enable_support": "1",
          "support_type": "tree(auto)", "support_on_build_plate_only": "0"})
json.dump(p, open("perfiles_orcaslicer/process_fixed2_soportes.json", "w"), indent=2)
PY
```

Y lamina cada placa (renombra el `plate_1.gcode` antes de copiarlo a la microSD):

```bash
for f in prueba-tolerancias-ejes gaviota-1a20-placa1-carroceria gaviota-1a20-placa2-puertas-y-ruedas; do
  proc=process_fixed2_soportes.json; [ "$f" = prueba-tolerancias-ejes ] && proc=process_fixed2.json
  flatpak run com.orcaslicer.OrcaSlicer --slice 0 --outputdir salida_gcode \
    --load-settings "perfiles_orcaslicer/machine_fixed.json;perfiles_orcaslicer/$proc" \
    --load-filaments "perfiles_orcaslicer/filament_fixed.json" "$f.stl"
  mv salida_gcode/plate_1.gcode "salida_gcode/$f.gcode"
done
```

Después: microSD en FAT32 → `sync && sudo udisksctl unmount -b /dev/mmcblk0p1` →
ranura de la **pantalla** → apagar y encender la impresora. Nunca por USB.

## Armado

1. Ruedas: dos tramos de filamento 1.75 de **87 mm** (libres en la carrocería, a presión en las ruedas).
2. Puertas: ciérralas en su lugar y mete por el agujerito de la cabecera del parabrisas
   un tramo de **24 mm** hasta que tope (uno por lado). Tapa el agujerito con pintura.
   Abren hasta ~65° sin rozar.
