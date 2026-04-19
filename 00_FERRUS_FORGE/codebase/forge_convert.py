"""
forge_convert.py — FERRUS FORGE
Fregate 00 : Conversion d'avatars bruts en .blend Blender

Usage (Blender headless) :
    blender --background --python forge_convert.py -- \
        --input   /path/to/avatar_P1.glb \
        --output-blend /path/to/avatar_P1.blend \
        --report-json  /path/to/report_P1.json

Formats supportes : .glb / .gltf / .obj / .fbx / .blend

POUR L'EMPEROR. POUR LA FLOTTE FERRUS.
"""

import bpy
import sys
import json
import os


# ─────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────

R15_BONES = {
    "LowerTorso", "UpperTorso", "Head",
    "LeftUpperArm", "LeftLowerArm", "LeftHand",
    "RightUpperArm", "RightLowerArm", "RightHand",
    "LeftUpperLeg", "LeftLowerLeg", "LeftFoot",
    "RightUpperLeg", "RightLowerLeg", "RightFoot",
}

SUPPORTED_FORMATS = {".glb", ".gltf", ".obj", ".fbx", ".blend"}


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
    print("ERROR: Aucun argument fourni apres --")
    sys.exit(1)

ARGS         = parse_args(raw)
INPUT_PATH   = ARGS.get("input")
OUTPUT_BLEND = ARGS.get("output-blend")
REPORT_JSON  = ARGS.get("report-json")

for label, val in [("--input", INPUT_PATH), ("--output-blend", OUTPUT_BLEND)]:
    if not val:
        print(f"ERROR: Argument manquant : {label}")
        sys.exit(1)

print(f"[FORGE] INPUT        : {INPUT_PATH}")
print(f"[FORGE] OUTPUT BLEND : {OUTPUT_BLEND}")


# ─────────────────────────────────────────────────────────────
# ETAPE 1 — Scene vide
# ─────────────────────────────────────────────────────────────

print("[FORGE] Preparation scene vide...")
bpy.ops.wm.read_factory_settings(use_empty=True)


# ─────────────────────────────────────────────────────────────
# ETAPE 2 — Detection format + Import
# ─────────────────────────────────────────────────────────────

ext = os.path.splitext(INPUT_PATH)[1].lower()
warnings = []

print(f"[FORGE] Format detecte : {ext}")

if ext not in SUPPORTED_FORMATS:
    msg = f"Format non supporte : {ext}"
    print(f"[FORGE] ERREUR — {msg}")
    if REPORT_JSON:
        os.makedirs(os.path.dirname(REPORT_JSON), exist_ok=True)
        with open(REPORT_JSON, "w") as f:
            json.dump({
                "source_file":       os.path.basename(INPUT_PATH),
                "format_detected":   ext,
                "status":            "ERREUR",
                "warnings":          [msg],
            }, f, indent=2)
    sys.exit(1)

print(f"[FORGE] Import en cours...")
objects_before = set(bpy.context.scene.objects)

if ext in (".glb", ".gltf"):
    bpy.ops.import_scene.gltf(filepath=INPUT_PATH)
elif ext == ".obj":
    bpy.ops.import_scene.obj(filepath=INPUT_PATH)
elif ext == ".fbx":
    bpy.ops.import_scene.fbx(filepath=INPUT_PATH)
elif ext == ".blend":
    bpy.ops.wm.open_mainfile(filepath=INPUT_PATH)

new_objects = set(bpy.context.scene.objects) - objects_before
print(f"[FORGE] Import OK — {len(new_objects)} objet(s) importe(s)")


# ─────────────────────────────────────────────────────────────
# ETAPE 3 — Nettoyage scene
# ─────────────────────────────────────────────────────────────

print("[FORGE] Nettoyage scene...")

removed = 0
for obj in list(bpy.context.scene.objects):
    if obj.type in ("CAMERA", "LIGHT", "SPEAKER", "LIGHT_PROBE"):
        bpy.data.objects.remove(obj, do_unlink=True)
        removed += 1

bpy.ops.outliner.orphans_purge(do_recursive=True)
print(f"[FORGE] Nettoyage OK — {removed} objet(s) supprime(s)")


# ─────────────────────────────────────────────────────────────
# ETAPE 4 — Validation armature
# ─────────────────────────────────────────────────────────────

armature_found  = False
r15_bones_found = False
bones_list      = []

armature_obj = next(
    (o for o in bpy.context.scene.objects if o.type == "ARMATURE"), None
)

if armature_obj:
    armature_found = True
    bones_list = [b.name for b in armature_obj.data.bones]
    matching   = R15_BONES & set(bones_list)
    r15_bones_found = len(matching) >= 10  # au moins 10/15 bones R15 presents

    print(f"[FORGE] Armature : '{armature_obj.name}' | {len(bones_list)} bones")
    print(f"[FORGE] Bones R15 detectes : {len(matching)}/15")

    if not r15_bones_found:
        msg = f"Bones R15 insuffisants : {len(matching)}/15 ({', '.join(sorted(matching)[:5])}...)"
        warnings.append(msg)
        print(f"[FORGE] WARNING — {msg}")
else:
    msg = "Aucune armature detectee — avatar sans rig"
    warnings.append(msg)
    print(f"[FORGE] WARNING — {msg}")


# ─────────────────────────────────────────────────────────────
# ETAPE 5 — Export .blend
# ─────────────────────────────────────────────────────────────

os.makedirs(os.path.dirname(OUTPUT_BLEND), exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=OUTPUT_BLEND)
blend_size = os.path.getsize(OUTPUT_BLEND)
print(f"[FORGE] Export BLEND OK — {OUTPUT_BLEND} ({blend_size // 1024} Ko)")


# ─────────────────────────────────────────────────────────────
# ETAPE 6 — Rapport JSON
# ─────────────────────────────────────────────────────────────

actor_id = os.path.splitext(os.path.basename(INPUT_PATH))[0]  # ex: avatar_P1
report = {
    "source_file":           os.path.basename(INPUT_PATH),
    "format_detected":       ext.lstrip("."),
    "armature_found":        armature_found,
    "r15_bones_found":       r15_bones_found,
    "bones_count":           len(bones_list),
    "output_blend":          os.path.basename(OUTPUT_BLEND),
    "output_blend_size_ko":  blend_size // 1024,
    "status":                "OK",
    "warnings":              warnings,
}

if REPORT_JSON:
    os.makedirs(os.path.dirname(REPORT_JSON), exist_ok=True)
    with open(REPORT_JSON, "w") as f:
        json.dump(report, f, indent=2)
    print(f"[FORGE] Rapport JSON ecrit : {REPORT_JSON}")


# ─────────────────────────────────────────────────────────────
# BILAN
# ─────────────────────────────────────────────────────────────

print("[FORGE] ─────────────────────────────────────────")
print(f"[FORGE] CONVERSION COMPLETE — {os.path.basename(INPUT_PATH)}")
print(f"[FORGE]   Format   : {ext}")
print(f"[FORGE]   Armature : {'OUI' if armature_found else 'NON'}")
print(f"[FORGE]   R15      : {'OUI' if r15_bones_found else 'NON / WARNING'}")
print(f"[FORGE]   BLEND    : {blend_size // 1024} Ko")
if warnings:
    for w in warnings:
        print(f"[FORGE]   WARNING  : {w}")
print("[FORGE] ─────────────────────────────────────────")
