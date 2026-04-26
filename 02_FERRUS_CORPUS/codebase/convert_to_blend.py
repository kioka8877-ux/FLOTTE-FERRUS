"""
convert_to_blend.py — FERRUS CORPUS
Fregate 02 : Convertisseur FBX / GLB → .blend pour EXODUS

Usage (Blender headless) :
    blender --background --python convert_to_blend.py -- \
        --input   /path/to/ferrus_P1.fbx \
        --output  /path/to/corpus_P1.blend \
        --report  /path/to/rapport_corpus.json   (optionnel)

Formats supportes en entree : .fbx  .glb  .gltf
Format de sortie             : .blend

POUR L'EMPEROR. POUR LA FLOTTE FERRUS.
"""

import bpy
import sys
import os
import json
import time


# ─────────────────────────────────────────────────────────────
# ARGS
# ─────────────────────────────────────────────────────────────

def parse_args(argv):
    args = {}
    i = 0
    while i < len(argv):
        if argv[i].startswith("--"):
            key = argv[i][2:]
            if i + 1 < len(argv) and not argv[i + 1].startswith("--"):
                args[key] = argv[i + 1]
                i += 2
            else:
                args[key] = True
                i += 1
        else:
            i += 1
    return args


if "--" in sys.argv:
    raw = sys.argv[sys.argv.index("--") + 1:]
else:
    print("[CORPUS] ERREUR : Aucun argument fourni apres --")
    sys.exit(1)

ARGS        = parse_args(raw)
INPUT_PATH  = ARGS.get("input")
OUTPUT_PATH = ARGS.get("output")
REPORT_PATH = ARGS.get("report")

for label, val in [("--input", INPUT_PATH), ("--output", OUTPUT_PATH)]:
    if not val:
        print(f"[CORPUS] ERREUR : Argument manquant : {label}")
        sys.exit(1)

print(f"[CORPUS] INPUT  : {INPUT_PATH}")
print(f"[CORPUS] OUTPUT : {OUTPUT_PATH}")


# ─────────────────────────────────────────────────────────────
# SCENE VIDE
# ─────────────────────────────────────────────────────────────

bpy.ops.wm.read_factory_settings(use_empty=True)
print("[CORPUS] Scene Blender initialisee (vide)")


# ─────────────────────────────────────────────────────────────
# IMPORT
# ─────────────────────────────────────────────────────────────

ext = os.path.splitext(INPUT_PATH)[1].lower()
t_start = time.time()

if ext == ".fbx":
    print("[CORPUS] Format detecte : FBX")
    bpy.ops.import_scene.fbx(filepath=INPUT_PATH)
elif ext in (".glb", ".gltf"):
    print(f"[CORPUS] Format detecte : {ext.upper()}")
    bpy.ops.import_scene.gltf(filepath=INPUT_PATH)
else:
    print(f"[CORPUS] ERREUR : Format non supporte : {ext}")
    sys.exit(1)

elapsed_import = time.time() - t_start
objects = list(bpy.context.scene.objects)
print(f"[CORPUS] Import OK — {len(objects)} objet(s) charges en {elapsed_import:.1f}s")

for obj in objects:
    print(f"  • {obj.type:12s}  {obj.name}")


# ─────────────────────────────────────────────────────────────
# EXPORT .blend
# ─────────────────────────────────────────────────────────────

os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

t_save = time.time()
bpy.ops.wm.save_as_mainfile(filepath=OUTPUT_PATH)
elapsed_save = time.time() - t_save

size_bytes = os.path.getsize(OUTPUT_PATH)
print(f"[CORPUS] Export .blend OK — {size_bytes} octets en {elapsed_save:.1f}s")
print(f"[CORPUS] Fichier : {OUTPUT_PATH}")


# ─────────────────────────────────────────────────────────────
# RAPPORT JSON
# ─────────────────────────────────────────────────────────────

if REPORT_PATH:
    # Charger rapport existant ou creer un nouveau
    if os.path.exists(REPORT_PATH):
        with open(REPORT_PATH, "r") as f:
            rapport = json.load(f)
    else:
        rapport = {
            "generated_at": "",
            "blender_version": ".".join(str(v) for v in bpy.app.version),
            "total_files": 0,
            "files": []
        }

    from datetime import datetime
    rapport["generated_at"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    rapport["total_files"] = len(rapport["files"]) + 1
    rapport["files"].append({
        "source":        os.path.basename(INPUT_PATH),
        "format":        ext.upper().lstrip("."),
        "output_blend":  os.path.basename(OUTPUT_PATH),
        "size_bytes":    size_bytes,
        "objects":       len(objects),
        "elapsed_s":     round(elapsed_import + elapsed_save, 2),
        "status":        "OK"
    })

    os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
    with open(REPORT_PATH, "w") as f:
        json.dump(rapport, f, indent=2, ensure_ascii=False)
    print(f"[CORPUS] Rapport mis a jour : {REPORT_PATH}")


print("[CORPUS] Mission accomplie. POUR L'EMPEROR.")
sys.exit(0)
