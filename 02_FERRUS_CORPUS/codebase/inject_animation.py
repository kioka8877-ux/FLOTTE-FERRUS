"""
inject_animation.py — FERRUS CORPUS
Fregate 02 : Incarnation des animations R15 dans un avatar Roblox

Usage (Blender headless) :
    blender --background --python inject_animation.py -- \
        --fbx /path/to/ferrus_P1.fbx \
        --avatar /path/to/avatar_r15.blend \
        --output-blend /path/to/corpus_P1.blend \
        --output-glb /path/to/corpus_P1.glb \
        --report-json /path/to/report_P1.json

POUR L'EMPEROR. POUR LA FLOTTE FERRUS.
"""

import bpy
import sys
import json
import os


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

ARGS = parse_args(raw)
FBX_PATH      = ARGS.get("fbx")
AVATAR_PATH   = ARGS.get("avatar")
OUTPUT_BLEND  = ARGS.get("output-blend")
OUTPUT_GLB    = ARGS.get("output-glb")
REPORT_JSON   = ARGS.get("report-json")

for label, val in [("--fbx", FBX_PATH), ("--avatar", AVATAR_PATH),
                   ("--output-blend", OUTPUT_BLEND), ("--output-glb", OUTPUT_GLB)]:
    if not val:
        print(f"ERROR: Argument manquant : {label}")
        sys.exit(1)

print(f"[CORPUS] FBX       : {FBX_PATH}")
print(f"[CORPUS] AVATAR    : {AVATAR_PATH}")
print(f"[CORPUS] OUT BLEND : {OUTPUT_BLEND}")
print(f"[CORPUS] OUT GLB   : {OUTPUT_GLB}")


# ─────────────────────────────────────────────────────────────
# ETAPE 1 — Charger l'avatar
# ─────────────────────────────────────────────────────────────

print("[CORPUS] Chargement avatar_r15.blend...")
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.open_mainfile(filepath=AVATAR_PATH)

avatar_arm = next(
    (o for o in bpy.context.scene.objects if o.type == "ARMATURE"), None
)
if not avatar_arm:
    print("ERROR: Aucune armature trouvee dans avatar_r15.blend")
    sys.exit(1)

avatar_bones = [b.name for b in avatar_arm.data.bones]
print(f"[CORPUS] Avatar charge — armature '{avatar_arm.name}' | {len(avatar_bones)} bones")


# ─────────────────────────────────────────────────────────────
# ETAPE 2 — Importer le FBX Ferrus
# ─────────────────────────────────────────────────────────────

print("[CORPUS] Import FBX Ferrus...")
objects_before = set(bpy.context.scene.objects)
bpy.ops.import_scene.fbx(filepath=FBX_PATH)
new_objects = set(bpy.context.scene.objects) - objects_before

fbx_arm = next(
    (o for o in new_objects if o.type == "ARMATURE"), None
)
if not fbx_arm:
    print("ERROR: Aucune armature trouvee dans le FBX importe")
    sys.exit(1)

print(f"[CORPUS] FBX importe — armature '{fbx_arm.name}'")


# ─────────────────────────────────────────────────────────────
# ETAPE 3 — Extraire l'Action du FBX
# ─────────────────────────────────────────────────────────────

fbx_action = None

if fbx_arm.animation_data and fbx_arm.animation_data.action:
    fbx_action = fbx_arm.animation_data.action
else:
    # Fallback : chercher dans bpy.data.actions
    candidates = [a for a in bpy.data.actions if fbx_arm.name.split(".")[0] in a.name]
    if candidates:
        fbx_action = candidates[0]

if not fbx_action:
    print("ERROR: Aucune Action trouvee dans l'armature FBX")
    sys.exit(1)

frame_start = int(fbx_action.frame_range[0])
frame_end   = int(fbx_action.frame_range[1])
frames      = frame_end - frame_start + 1
print(f"[CORPUS] Action trouvee : '{fbx_action.name}' | {frames} frames ({frame_start}→{frame_end})")


# ─────────────────────────────────────────────────────────────
# ETAPE 4 — Transferer l'Action sur l'avatar
# ─────────────────────────────────────────────────────────────

print("[CORPUS] Transfert animation vers avatar...")

if not avatar_arm.animation_data:
    avatar_arm.animation_data_create()

avatar_arm.animation_data.action = fbx_action

bpy.context.scene.frame_start = frame_start
bpy.context.scene.frame_end   = frame_end

print(f"[CORPUS] Action assignee a '{avatar_arm.name}'")


# ─────────────────────────────────────────────────────────────
# ETAPE 5 — Supprimer l'armature FBX temporaire
# ─────────────────────────────────────────────────────────────

for obj in new_objects:
    if obj.type in ("ARMATURE", "EMPTY", "MESH") and obj != avatar_arm:
        bpy.data.objects.remove(obj, do_unlink=True)

print("[CORPUS] Armature FBX temporaire supprimee")


# ─────────────────────────────────────────────────────────────
# ETAPE 6 — Export .blend (MASTER)
# ─────────────────────────────────────────────────────────────

os.makedirs(os.path.dirname(OUTPUT_BLEND), exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=OUTPUT_BLEND)
blend_size = os.path.getsize(OUTPUT_BLEND)
print(f"[CORPUS] Export BLEND OK — {OUTPUT_BLEND} ({blend_size // 1024} Ko)")


# ─────────────────────────────────────────────────────────────
# ETAPE 7 — Export .glb (PREVIEW)
# ─────────────────────────────────────────────────────────────

os.makedirs(os.path.dirname(OUTPUT_GLB), exist_ok=True)

# Assurer extension .glb
glb_path = OUTPUT_GLB if OUTPUT_GLB.endswith(".glb") else OUTPUT_GLB + ".glb"

bpy.ops.export_scene.gltf(
    filepath=glb_path,
    export_format="GLB",
    export_animations=True,
    export_anim_single_armature=True,
    export_apply=False,
)

glb_size = os.path.getsize(glb_path)
print(f"[CORPUS] Export GLB  OK — {glb_path} ({glb_size // 1024} Ko)")


# ─────────────────────────────────────────────────────────────
# ETAPE 8 — Rapport JSON
# ─────────────────────────────────────────────────────────────

report = {
    "fbx_source":          os.path.basename(FBX_PATH),
    "avatar_source":       os.path.basename(AVATAR_PATH),
    "action_name":         fbx_action.name,
    "bones_avatar":        len(avatar_bones),
    "bones_list":          avatar_bones,
    "frames":              frames,
    "frame_start":         frame_start,
    "frame_end":           frame_end,
    "output_blend":        os.path.basename(OUTPUT_BLEND),
    "output_blend_size_ko": blend_size // 1024,
    "output_glb":          os.path.basename(glb_path),
    "output_glb_size_ko":  glb_size // 1024,
    "status":              "OK",
}

if REPORT_JSON:
    os.makedirs(os.path.dirname(REPORT_JSON), exist_ok=True)
    with open(REPORT_JSON, "w") as f:
        json.dump(report, f, indent=2)
    print(f"[CORPUS] Rapport JSON ecrit : {REPORT_JSON}")

print("[CORPUS] ─────────────────────────────────────────")
print(f"[CORPUS] INCARNATION COMPLETE — {os.path.basename(FBX_PATH)}")
print(f"[CORPUS]   Bones    : {len(avatar_bones)}")
print(f"[CORPUS]   Frames   : {frames}")
print(f"[CORPUS]   BLEND    : {blend_size // 1024} Ko")
print(f"[CORPUS]   GLB      : {glb_size // 1024} Ko")
print("[CORPUS] ─────────────────────────────────────────")
