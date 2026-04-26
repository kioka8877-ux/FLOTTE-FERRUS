# =============================================================================
# FERRUS OSSEUS — osseus_core.py
# Fregate 04 | Pipeline Mesh T-pose (sans rig) -> FBX rige
# FLOTTE FERRUS | AD MAJOREM GLORIAM IMPERATORIS
# =============================================================================
#
# Usage (Blender headless) :
#   blender --background --python osseus_core.py -- \
#       --input   avatar.glb \
#       --output  avatar_rigged.fbx \
#       --template r15 \
#       --report  rapport_osseus.json
#
# Templates : r15 | mixamo | deepmotion
# Formats   : .glb .gltf .obj .fbx
#
# POUR L'EMPEROR. POUR LA FLOTTE FERRUS.
# =============================================================================

import sys
import subprocess

# numpy requis par io_scene_gltf2 (manquant dans Blender 3.x apt)
try:
    import numpy
except ImportError:
    print("[OSSEUS] numpy absent — recherche chemin systeme...")
    # sys.executable = /usr/bin/python3.10 sans pip dans cet env.
    # On cherche numpy via pip3/pip du systeme et on ajoute son site-packages a sys.path.
    _found = False
    for _pip in ["pip3", "pip", "/usr/bin/pip3", "/usr/local/bin/pip3"]:
        _r = subprocess.run([_pip, "show", "numpy"],
                            capture_output=True, text=True)
        if _r.returncode == 0:
            for _line in _r.stdout.split("\n"):
                if _line.startswith("Location:"):
                    _site = _line.split(":", 1)[1].strip()
                    if _site not in sys.path:
                        sys.path.insert(0, _site)
                    _found = True
                    break
            if _found:
                break
    if not _found:
        # Fallback : ajouter les chemins site-packages communs sous Colab
        for _p in [
            "/usr/local/lib/python3.10/dist-packages",
            "/usr/local/lib/python3.9/dist-packages",
            "/usr/lib/python3/dist-packages",
        ]:
            if _p not in sys.path:
                sys.path.insert(0, _p)
    try:
        import numpy
        print(f"[OSSEUS] numpy trouve : {numpy.__version__}")
    except ImportError:
        raise RuntimeError(
            "numpy introuvable dans sys.path. "
            "Verifier que numpy est installe dans l'environnement Colab (pip install numpy)."
        )

import bpy
import mathutils
import os
import json
import math
from pathlib import Path

# =============================================================================
# ARGS
# =============================================================================

def parse_args():
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
    else:
        argv = []

    import argparse
    parser = argparse.ArgumentParser(description="FERRUS OSSEUS — Mesh T-pose -> FBX rige")
    parser.add_argument("--input",    required=True,
                        help="Chemin vers le mesh source (.glb/.gltf/.obj/.fbx)")
    parser.add_argument("--output",   required=True,
                        help="Chemin de sortie .fbx rige")
    parser.add_argument("--template", default="r15",
                        choices=["r15", "mixamo", "deepmotion"],
                        help="Squelette cible : r15 | mixamo | deepmotion (defaut: r15)")
    parser.add_argument("--report",   default=None,
                        help="Chemin du rapport JSON (optionnel)")
    return parser.parse_args(argv)


# =============================================================================
# STEP 1 — IMPORT MESH
# =============================================================================

SUPPORTED_FORMATS = {".glb", ".gltf", ".obj", ".fbx"}

def import_mesh(input_path: str) -> list:
    """Importe le fichier source, supprime armatures existantes, retourne liste de meshes."""
    ext = Path(input_path).suffix.lower()

    if ext not in SUPPORTED_FORMATS:
        raise ValueError(f"Format non supporte: {ext}. Formats valides: {SUPPORTED_FORMATS}")

    print(f"[OSSEUS][IMPORT] {input_path}")
    bpy.ops.wm.read_factory_settings(use_empty=True)

    if ext in (".glb", ".gltf"):
        bpy.ops.import_scene.gltf(filepath=input_path)
    elif ext == ".obj":
        bpy.ops.import_scene.obj(filepath=input_path)
    elif ext == ".fbx":
        bpy.ops.import_scene.fbx(
            filepath=input_path,
            ignore_leaf_bones=True,
            force_connect_children=False,
            automatic_bone_orientation=True,
        )

    # Supprimer armatures existantes — on cree from scratch
    for obj in list(bpy.context.scene.objects):
        if obj.type == "ARMATURE":
            bpy.data.objects.remove(obj, do_unlink=True)

    mesh_objects = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    if not mesh_objects:
        raise RuntimeError("Aucun mesh trouve dans le fichier source")

    print(f"[OSSEUS][IMPORT] {len(mesh_objects)} mesh(es) importes")
    return mesh_objects


# =============================================================================
# STEP 2 — JOIN MESHES
# =============================================================================

def join_meshes(mesh_objects: list) -> bpy.types.Object:
    """Rejoint tous les meshes en un seul objet et applique les transformations."""
    bpy.ops.object.select_all(action="DESELECT")
    for obj in mesh_objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = mesh_objects[0]

    if len(mesh_objects) > 1:
        bpy.ops.object.join()
        print(f"[OSSEUS][JOIN] {len(mesh_objects)} meshes rejoints")

    mesh_obj = bpy.context.active_object
    mesh_obj.name = "OSSEUS_Mesh"

    # Appliquer toutes les transformations (scale, rotation, location)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

    face_count = len(mesh_obj.data.polygons)
    vert_count = len(mesh_obj.data.vertices)
    print(f"[OSSEUS][JOIN] Mesh: {vert_count:,} vertices | {face_count:,} faces")
    return mesh_obj


# =============================================================================
# STEP 3 — BOUNDING BOX
# =============================================================================

def compute_bbox(obj: bpy.types.Object):
    """Calcule la bounding box world-space depuis les 8 coins de l'objet."""
    corners = [obj.matrix_world @ mathutils.Vector(v) for v in obj.bound_box]
    xs = [v.x for v in corners]
    ys = [v.y for v in corners]
    zs = [v.z for v in corners]

    bbox_min = (min(xs), min(ys), min(zs))
    bbox_max = (max(xs), max(ys), max(zs))

    h = bbox_max[1] - bbox_min[1]
    w = bbox_max[0] - bbox_min[0]
    d = bbox_max[2] - bbox_min[2]

    print(f"[OSSEUS][BBOX] Hauteur={h:.3f}  Largeur={w:.3f}  Profondeur={d:.3f}")
    print(f"[OSSEUS][BBOX] Min=({bbox_min[0]:.3f}, {bbox_min[1]:.3f}, {bbox_min[2]:.3f})")
    print(f"[OSSEUS][BBOX] Max=({bbox_max[0]:.3f}, {bbox_max[1]:.3f}, {bbox_max[2]:.3f})")
    return bbox_min, bbox_max


# =============================================================================
# STEP 4 — COMPUTE JOINTS
# =============================================================================

def compute_joints(bbox_min, bbox_max) -> dict:
    """
    Calcule les positions 3D de tous les joints anatomiques.
    Assume T-pose : bras etendus en X, Y=up, Z=profondeur.
    Proportions calibrees pour avatar humanoide standard.
    """
    min_x, min_y, min_z = bbox_min
    max_x, max_y, max_z = bbox_max

    cx  = (min_x + max_x) / 2   # centre X
    cz  = (min_z + max_z) / 2   # centre Z
    h   = max_y - min_y          # hauteur totale
    hw  = (max_x - min_x) / 2   # demi-largeur (bras etendus)

    def J(xf, yf, zf=0.0):
        """
        xf : fraction de hw (signe inclus, -1=gauche, +1=droite)
        yf : fraction de h depuis le sol
        zf : fraction de h en profondeur
        """
        return (cx + xf * hw, min_y + yf * h, cz + zf * h)

    j = {}

    # ── Colonne vertebrale ──────────────────────────────────────────────────
    j["hips"]     = J( 0,  0.52)
    j["spine"]    = J( 0,  0.57)
    j["spine1"]   = J( 0,  0.62)
    j["spine2"]   = J( 0,  0.68)
    j["chest"]    = J( 0,  0.73)
    j["neck"]     = J( 0,  0.80)
    j["head"]     = J( 0,  0.87)
    j["head_top"] = J( 0,  0.97)

    # ── Epaules ─────────────────────────────────────────────────────────────
    j["l_shoulder"] = J(-0.24,  0.76)
    j["r_shoulder"] = J(+0.24,  0.76)

    # ── Bras gauche ─────────────────────────────────────────────────────────
    j["l_arm"]      = J(-0.42,  0.74)
    j["l_forearm"]  = J(-0.63,  0.74)
    j["l_hand"]     = J(-0.82,  0.74)
    j["l_hand_tip"] = J(-0.97,  0.74)

    # ── Bras droit (miroir) ─────────────────────────────────────────────────
    j["r_arm"]      = J(+0.42,  0.74)
    j["r_forearm"]  = J(+0.63,  0.74)
    j["r_hand"]     = J(+0.82,  0.74)
    j["r_hand_tip"] = J(+0.97,  0.74)

    # ── Jambe gauche ────────────────────────────────────────────────────────
    j["l_upleg"]  = J(-0.16,  0.50)
    j["l_leg"]    = J(-0.15,  0.26)
    j["l_foot"]   = J(-0.15,  0.04)
    j["l_toe"]    = (cx - 0.15*hw, min_y,        cz + 0.06*h)
    j["l_toetip"] = (cx - 0.15*hw, min_y,        cz + 0.13*h)

    # ── Jambe droite (miroir) ───────────────────────────────────────────────
    j["r_upleg"]  = J(+0.16,  0.50)
    j["r_leg"]    = J(+0.15,  0.26)
    j["r_foot"]   = J(+0.15,  0.04)
    j["r_toe"]    = (cx + 0.15*hw, min_y,        cz + 0.06*h)
    j["r_toetip"] = (cx + 0.15*hw, min_y,        cz + 0.13*h)

    # ── Doigts gauche (clusteres autour de la main) ─────────────────────────
    # Tier 1 (proximal) : proches de l_hand
    j["l_index1"]  = J(-0.985, 0.748)
    j["l_middle1"] = J(-0.985, 0.738)
    j["l_ring1"]   = J(-0.985, 0.728)
    j["l_pinky1"]  = J(-0.985, 0.718)
    j["l_thumb1"]  = J(-0.865, 0.762)

    # Tier 2 (medial)
    j["l_index2"]  = J(-1.005, 0.748)
    j["l_middle2"] = J(-1.005, 0.738)
    j["l_ring2"]   = J(-1.005, 0.728)
    j["l_pinky2"]  = J(-1.005, 0.718)
    j["l_thumb2"]  = J(-0.925, 0.765)

    # Tier 3 (distal / fingertip)
    j["l_index3"]  = J(-1.025, 0.748)
    j["l_middle3"] = J(-1.025, 0.738)
    j["l_ring3"]   = J(-1.025, 0.728)
    j["l_pinky3"]  = J(-1.025, 0.718)
    j["l_thumb3"]  = J(-0.970, 0.767)

    # ── Doigts droit (miroir) ───────────────────────────────────────────────
    j["r_index1"]  = J(+0.985, 0.748)
    j["r_middle1"] = J(+0.985, 0.738)
    j["r_ring1"]   = J(+0.985, 0.728)
    j["r_pinky1"]  = J(+0.985, 0.718)
    j["r_thumb1"]  = J(+0.865, 0.762)

    j["r_index2"]  = J(+1.005, 0.748)
    j["r_middle2"] = J(+1.005, 0.738)
    j["r_ring2"]   = J(+1.005, 0.728)
    j["r_pinky2"]  = J(+1.005, 0.718)
    j["r_thumb2"]  = J(+0.925, 0.765)

    j["r_index3"]  = J(+1.025, 0.748)
    j["r_middle3"] = J(+1.025, 0.738)
    j["r_ring3"]   = J(+1.025, 0.728)
    j["r_pinky3"]  = J(+1.025, 0.718)
    j["r_thumb3"]  = J(+0.970, 0.767)

    return j


# =============================================================================
# TEMPLATES — Definitions des squelettes
# =============================================================================
# Format par bone : (nom, joint_head, joint_tail, parent_name | None)
# =============================================================================

def get_template_bones(template: str) -> list:
    if template == "r15":
        return _bones_r15()
    elif template == "mixamo":
        return _bones_mixamo()
    elif template == "deepmotion":
        return _bones_deepmotion()
    raise ValueError(f"Template inconnu: {template}")


def _bones_r15():
    """15 bones — Roblox R15. Naming standard Roblox."""
    return [
        # Torse
        ("LowerTorso",    "hips",      "spine1",    None),
        ("UpperTorso",    "spine2",    "neck",      "LowerTorso"),
        ("Head",          "neck",      "head_top",  "UpperTorso"),
        # Bras gauche
        ("LeftUpperArm",  "l_arm",     "l_forearm", "UpperTorso"),
        ("LeftLowerArm",  "l_forearm", "l_hand",    "LeftUpperArm"),
        ("LeftHand",      "l_hand",    "l_hand_tip","LeftLowerArm"),
        # Bras droit
        ("RightUpperArm", "r_arm",     "r_forearm", "UpperTorso"),
        ("RightLowerArm", "r_forearm", "r_hand",    "RightUpperArm"),
        ("RightHand",     "r_hand",    "r_hand_tip","RightLowerArm"),
        # Jambe gauche
        ("LeftUpperLeg",  "l_upleg",   "l_leg",     "LowerTorso"),
        ("LeftLowerLeg",  "l_leg",     "l_foot",    "LeftUpperLeg"),
        ("LeftFoot",      "l_foot",    "l_toe",     "LeftLowerLeg"),
        # Jambe droite
        ("RightUpperLeg", "r_upleg",   "r_leg",     "LowerTorso"),
        ("RightLowerLeg", "r_leg",     "r_foot",    "RightUpperLeg"),
        ("RightFoot",     "r_foot",    "r_toe",     "RightLowerLeg"),
    ]


def _bones_mixamo():
    """26 bones — Mixamo avec prefix mixamorig."""
    return [
        # Torse
        ("mixamorig:Hips",              "hips",       "spine",      None),
        ("mixamorig:Spine",             "spine",      "spine1",     "mixamorig:Hips"),
        ("mixamorig:Spine1",            "spine1",     "spine2",     "mixamorig:Spine"),
        ("mixamorig:Spine2",            "spine2",     "chest",      "mixamorig:Spine1"),
        ("mixamorig:Neck",              "neck",       "head",       "mixamorig:Spine2"),
        ("mixamorig:Head",              "head",       "head_top",   "mixamorig:Neck"),
        # Bras gauche
        ("mixamorig:LeftShoulder",      "l_shoulder", "l_arm",      "mixamorig:Spine2"),
        ("mixamorig:LeftArm",           "l_arm",      "l_forearm",  "mixamorig:LeftShoulder"),
        ("mixamorig:LeftForeArm",       "l_forearm",  "l_hand",     "mixamorig:LeftArm"),
        ("mixamorig:LeftHand",          "l_hand",     "l_hand_tip", "mixamorig:LeftForeArm"),
        # Bras droit
        ("mixamorig:RightShoulder",     "r_shoulder", "r_arm",      "mixamorig:Spine2"),
        ("mixamorig:RightArm",          "r_arm",      "r_forearm",  "mixamorig:RightShoulder"),
        ("mixamorig:RightForeArm",      "r_forearm",  "r_hand",     "mixamorig:RightArm"),
        ("mixamorig:RightHand",         "r_hand",     "r_hand_tip", "mixamorig:RightForeArm"),
        # Jambe gauche
        ("mixamorig:LeftUpLeg",         "l_upleg",    "l_leg",      "mixamorig:Hips"),
        ("mixamorig:LeftLeg",           "l_leg",      "l_foot",     "mixamorig:LeftUpLeg"),
        ("mixamorig:LeftFoot",          "l_foot",     "l_toe",      "mixamorig:LeftLeg"),
        ("mixamorig:LeftToeBase",       "l_toe",      "l_toetip",   "mixamorig:LeftFoot"),
        # Jambe droite
        ("mixamorig:RightUpLeg",        "r_upleg",    "r_leg",      "mixamorig:Hips"),
        ("mixamorig:RightLeg",          "r_leg",      "r_foot",     "mixamorig:RightUpLeg"),
        ("mixamorig:RightFoot",         "r_foot",     "r_toe",      "mixamorig:RightLeg"),
        ("mixamorig:RightToeBase",      "r_toe",      "r_toetip",   "mixamorig:RightFoot"),
        # Doigts (4 bones pour Mixamo 26)
        ("mixamorig:LeftHandIndex1",    "l_index1",   "l_index2",   "mixamorig:LeftHand"),
        ("mixamorig:LeftHandThumb1",    "l_thumb1",   "l_thumb2",   "mixamorig:LeftHand"),
        ("mixamorig:RightHandIndex1",   "r_index1",   "r_index2",   "mixamorig:RightHand"),
        ("mixamorig:RightHandThumb1",   "r_thumb1",   "r_thumb2",   "mixamorig:RightHand"),
    ]


def _bones_deepmotion():
    """52 bones — DeepMotion avec naming _JNT. Corps complet avec doigts."""
    bones = [
        # Colonne
        ("hips_JNT",          "hips",       "spine",      None),
        ("spine_JNT",         "spine",      "spine1",     "hips_JNT"),
        ("spine1_JNT",        "spine1",     "spine2",     "spine_JNT"),
        ("spine2_JNT",        "spine2",     "neck",       "spine1_JNT"),
        ("neck_JNT",          "neck",       "head",       "spine2_JNT"),
        ("head_JNT",          "head",       "head_top",   "neck_JNT"),
        # Epaule + Bras gauche
        ("l_shoulder_JNT",    "l_shoulder", "l_arm",      "spine2_JNT"),
        ("l_arm_JNT",         "l_arm",      "l_forearm",  "l_shoulder_JNT"),
        ("l_forearm_JNT",     "l_forearm",  "l_hand",     "l_arm_JNT"),
        ("l_hand_JNT",        "l_hand",     "l_hand_tip", "l_forearm_JNT"),
        # Epaule + Bras droit
        ("r_shoulder_JNT",    "r_shoulder", "r_arm",      "spine2_JNT"),
        ("r_arm_JNT",         "r_arm",      "r_forearm",  "r_shoulder_JNT"),
        ("r_forearm_JNT",     "r_forearm",  "r_hand",     "r_arm_JNT"),
        ("r_hand_JNT",        "r_hand",     "r_hand_tip", "r_forearm_JNT"),
        # Jambe gauche
        ("l_upleg_JNT",       "l_upleg",    "l_leg",      "hips_JNT"),
        ("l_leg_JNT",         "l_leg",      "l_foot",     "l_upleg_JNT"),
        ("l_foot_JNT",        "l_foot",     "l_toe",      "l_leg_JNT"),
        ("l_toebase_JNT",     "l_toe",      "l_toetip",   "l_foot_JNT"),
        # Jambe droite
        ("r_upleg_JNT",       "r_upleg",    "r_leg",      "hips_JNT"),
        ("r_leg_JNT",         "r_leg",      "r_foot",     "r_upleg_JNT"),
        ("r_foot_JNT",        "r_foot",     "r_toe",      "r_leg_JNT"),
        ("r_toebase_JNT",     "r_toe",      "r_toetip",   "r_foot_JNT"),
    ]
    # 22 bones core — ajout des 30 bones doigts (5 doigts x 3 joints x 2 mains)
    for side, hand_jnt in [("l", "l_hand_JNT"), ("r", "r_hand_JNT")]:
        for finger in ["handIndex", "handMiddle", "handRing", "handPinky", "handThumb"]:
            fname = finger.replace("hand", "").lower()  # index, middle, ring, pinky, thumb
            for i in range(1, 4):
                bone_name = f"{side}_{finger}{i}_JNT"
                head_j    = f"{side}_{fname}{i}"
                tail_j    = f"{side}_{fname}{i+1}" if i < 3 else f"{side}_{fname}3"
                if i == 3:
                    # Bone terminal : tail = meme direction, legerement au-dela
                    # On reutilise tier3 comme tail (bone de longueur minimale)
                    tail_j = f"{side}_{fname}3"
                parent = hand_jnt if i == 1 else f"{side}_{finger}{i-1}_JNT"
                bones.append((bone_name, head_j, tail_j, parent))
    return bones


# =============================================================================
# STEP 5 — CREATE ARMATURE
# =============================================================================

def create_armature(joints: dict, template: str) -> bpy.types.Object:
    """Cree et positionne l'armature selon le template et les joints calcules."""
    bones_def = get_template_bones(template)

    arm_data = bpy.data.armatures.new("OSSEUS_Armature")
    arm_obj  = bpy.data.objects.new("OSSEUS_Armature", arm_data)
    bpy.context.collection.objects.link(arm_obj)
    bpy.context.view_layer.objects.active = arm_obj

    bpy.ops.object.mode_set(mode="EDIT")
    edit_bones = arm_data.edit_bones

    created = {}
    skipped = []

    for bone_name, head_jnt, tail_jnt, parent_name in bones_def:
        if head_jnt not in joints:
            skipped.append(f"{bone_name} (joint manquant: {head_jnt})")
            continue
        if tail_jnt not in joints:
            skipped.append(f"{bone_name} (joint manquant: {tail_jnt})")
            continue

        eb = edit_bones.new(bone_name)
        head_pos = mathutils.Vector(joints[head_jnt])
        tail_pos = mathutils.Vector(joints[tail_jnt])
        # Bone terminal (head == tail) : etendre de 1 cm dans la direction du parent
        if (tail_pos - head_pos).length < 0.001:
            parent_head = mathutils.Vector(joints.get(head_jnt, head_pos))
            # direction : reprendre celle du bone precedent ou +X par defaut
            if parent_name and parent_name in created:
                pb = created[parent_name]
                direction = (pb.tail - pb.head).normalized()
            else:
                direction = mathutils.Vector((0.01, 0.0, 0.0))
            tail_pos = head_pos + direction * 0.01
        eb.head = head_pos
        eb.tail = tail_pos
        eb.use_connect = False
        created[bone_name] = eb

    # Assigner les parents apres creation de tous les bones
    for bone_name, _, _, parent_name in bones_def:
        if parent_name and parent_name in created and bone_name in created:
            created[bone_name].parent = created[parent_name]

    bpy.ops.object.mode_set(mode="OBJECT")

    if skipped:
        for s in skipped:
            print(f"[OSSEUS][ARM] WARN bone ignore: {s}")

    print(f"[OSSEUS][ARM] Template '{template}' — {len(created)} bones crees")
    return arm_obj


# =============================================================================
# STEP 6 — PARENT MESH TO ARMATURE (Automatic Weights)
# =============================================================================

def parent_with_auto_weights(mesh_obj: bpy.types.Object,
                              arm_obj:  bpy.types.Object) -> bool:
    """
    Parent le mesh a l'armature avec Automatic Weights.
    Fallback sur Envelope Weights si le heat map echoue.
    Retourne True si Automatic Weights a reussi.
    """
    bpy.ops.object.select_all(action="DESELECT")
    mesh_obj.select_set(True)
    arm_obj.select_set(True)
    bpy.context.view_layer.objects.active = arm_obj

    try:
        bpy.ops.object.parent_set(type="ARMATURE_AUTO")
        print("[OSSEUS][WEIGHT] Automatic Weights appliques")
        return True
    except Exception as e:
        print(f"[OSSEUS][WEIGHT] Automatic Weights echoue ({e}), fallback Envelope...")

    # Fallback : Envelope Weights
    try:
        bpy.ops.object.select_all(action="DESELECT")
        mesh_obj.select_set(True)
        arm_obj.select_set(True)
        bpy.context.view_layer.objects.active = arm_obj
        bpy.ops.object.parent_set(type="ARMATURE_ENVELOPE")
        print("[OSSEUS][WEIGHT] Envelope Weights appliques (fallback)")
        return False
    except Exception as e2:
        raise RuntimeError(f"Echec parenting armature: {e2}")


# =============================================================================
# STEP 7 — EXPORT FBX
# =============================================================================

def export_fbx(mesh_obj: bpy.types.Object,
               arm_obj:  bpy.types.Object,
               output_path: str) -> float:
    """Exporte le mesh rige en FBX avec textures embeddees. Retourne la taille en Mo."""
    bpy.ops.object.select_all(action="DESELECT")
    mesh_obj.select_set(True)
    arm_obj.select_set(True)
    bpy.context.view_layer.objects.active = arm_obj

    out_dir = os.path.dirname(os.path.abspath(output_path))
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    # Deballer les images packees sur disque avant export
    # (Blender importe les textures FBX/GLB en mode "packed" — memoire uniquement)
    # Sans cette etape, embed_textures ne trouve pas les fichiers source
    for img in bpy.data.images:
        if img.packed_file:
            unpack_path = os.path.join(out_dir, bpy.path.clean_name(img.name) + ".png")
            img.filepath_raw = unpack_path
            img.file_format  = "PNG"
            img.unpack(method="WRITE_LOCAL")
            print(f"[OSSEUS][EXPORT] Texture deballee : {img.name}")

    bpy.ops.export_scene.fbx(
        filepath=output_path,
        use_selection=True,
        add_leaf_bones=False,
        bake_anim=False,
        use_mesh_modifiers=True,
        mesh_smooth_type="FACE",
        use_armature_deform_only=False,
        path_mode="COPY",
        embed_textures=True,        # Textures embeddees dans le binaire FBX (self-contained)
        global_scale=1.0,
        axis_forward="-Z",
        axis_up="Y",
    )

    size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"[OSSEUS][EXPORT] {output_path} ({size_mb:.2f} Mo)")
    return size_mb


# =============================================================================
# RAPPORT JSON
# =============================================================================

def write_rapport(rapport: dict, report_path: str):
    dir_ = os.path.dirname(os.path.abspath(report_path))
    if dir_:
        os.makedirs(dir_, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(rapport, f, indent=2, ensure_ascii=False)
    print(f"[OSSEUS][RAPPORT] {report_path}")


# =============================================================================
# MAIN PIPELINE
# =============================================================================

def main():
    args = parse_args()

    input_path  = args.input
    output_path = args.output
    template    = args.template
    report_path = args.report

    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Fichier source introuvable: {input_path}")

    rapport = {
        "status":         "RUNNING",
        "input":          input_path,
        "output":         output_path,
        "template":       template,
    }

    try:
        # ── STEP 1 : Import ────────────────────────────────────────────────
        mesh_objects = import_mesh(input_path)
        rapport["mesh_count_raw"] = len(mesh_objects)

        # ── STEP 2 : Join ──────────────────────────────────────────────────
        mesh_obj = join_meshes(mesh_objects)
        rapport["vertices"] = len(mesh_obj.data.vertices)
        rapport["faces"]    = len(mesh_obj.data.polygons)

        # ── STEP 3 : Bounding box ──────────────────────────────────────────
        bbox_min, bbox_max = compute_bbox(mesh_obj)
        rapport["bbox_min"] = list(bbox_min)
        rapport["bbox_max"] = list(bbox_max)

        height = round(bbox_max[1] - bbox_min[1], 4)
        width  = round(bbox_max[0] - bbox_min[0], 4)
        rapport["height"] = height
        rapport["width"]  = width
        print(f"[OSSEUS] Avatar detecte — hauteur={height} | largeur={width}")

        # ── STEP 4 : Joints ────────────────────────────────────────────────
        joints = compute_joints(bbox_min, bbox_max)
        rapport["joints_count"] = len(joints)

        # ── STEP 5 : Armature ─────────────────────────────────────────────
        arm_obj = create_armature(joints, template)
        rapport["bones_count"] = len(arm_obj.data.bones)

        # ── STEP 6 : Auto Weights ─────────────────────────────────────────
        auto_ok = parent_with_auto_weights(mesh_obj, arm_obj)
        rapport["auto_weights"] = auto_ok

        # ── STEP 7 : Export FBX ───────────────────────────────────────────
        size_mb = export_fbx(mesh_obj, arm_obj, output_path)
        rapport["output_size_mb"] = round(size_mb, 2)
        rapport["status"]         = "SUCCESS"

    except Exception as e:
        rapport["status"] = "ERROR"
        rapport["error"]  = str(e)
        print(f"[OSSEUS][ERROR] {e}")
        if report_path:
            write_rapport(rapport, report_path)
        raise

    if report_path:
        write_rapport(rapport, report_path)

    print("=" * 65)
    print(f"[OSSEUS] PIPELINE COMPLET")
    print(f"[OSSEUS]   Template  : {template}")
    print(f"[OSSEUS]   Bones     : {rapport['bones_count']}")
    print(f"[OSSEUS]   Weights   : {'AUTO' if rapport['auto_weights'] else 'ENVELOPE (fallback)'}")
    print(f"[OSSEUS]   Sortie    : {output_path} ({rapport['output_size_mb']} Mo)")
    print("=" * 65)
    print("[OSSEUS] POUR L'EMPEROR. POUR LA FLOTTE FERRUS.")


if __name__ == "__main__":
    main()
