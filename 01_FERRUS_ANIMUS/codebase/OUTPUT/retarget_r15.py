"""
retarget_r15.py — FERRUS ANIMUS / Compartiment OUTPUT
Retargeting DeepMotion (52 bones) vers Roblox R15 (15 bones) OU Mixamo (22 bones).

MODES :
  R15    — retargeting vers Roblox R15 (15 bones) — DEFAULT — pipeline Roblox natif
  MIXAMO — retargeting vers Mixamo (22 bones) — pour avatars riges par Mixamo.com

Mapping DeepMotion → R15 (15 bones actifs, 37 ignores) :
    hips_JNT      → LowerTorso   (ROOT)
    spine2_JNT    → UpperTorso
    head_JNT      → Head
    l_arm_JNT     → LeftUpperArm
    l_forearm_JNT → LeftLowerArm
    l_hand_JNT    → LeftHand
    r_arm_JNT     → RightUpperArm
    r_forearm_JNT → RightLowerArm
    r_hand_JNT    → RightHand
    l_upleg_JNT   → LeftUpperLeg
    l_leg_JNT     → LeftLowerLeg
    l_foot_JNT    → LeftFoot
    r_upleg_JNT   → RightUpperLeg
    r_leg_JNT     → RightLowerLeg
    r_foot_JNT    → RightFoot

Mapping DeepMotion → Mixamo (22 bones) :
    hips_JNT       → mixamorig:Hips  (ROOT)
    spine_JNT      → mixamorig:Spine
    spine1_JNT     → mixamorig:Spine1
    spine2_JNT     → mixamorig:Spine2
    neck_JNT       → mixamorig:Neck
    head_JNT       → mixamorig:Head
    l_shoulder_JNT → mixamorig:LeftShoulder
    l_arm_JNT      → mixamorig:LeftArm
    l_forearm_JNT  → mixamorig:LeftForeArm
    l_hand_JNT     → mixamorig:LeftHand
    r_shoulder_JNT → mixamorig:RightShoulder
    r_arm_JNT      → mixamorig:RightArm
    r_forearm_JNT  → mixamorig:RightForeArm
    r_hand_JNT     → mixamorig:RightHand
    l_upleg_JNT    → mixamorig:LeftUpLeg
    l_leg_JNT      → mixamorig:LeftLeg
    l_foot_JNT     → mixamorig:LeftFoot
    l_toebase_JNT  → mixamorig:LeftToeBase
    r_upleg_JNT    → mixamorig:RightUpLeg
    r_leg_JNT      → mixamorig:RightLeg
    r_foot_JNT     → mixamorig:RightFoot
    r_toebase_JNT  → mixamorig:RightToeBase

Usage standalone (bpy headless) :
    blender --background --python retarget_r15.py -- \
        --fbx-in  path/to/input_corrige.fbx \
        --plan    path/to/plan_corrections.json \
        --fbx-out path/to/ferrus_out.fbx \
        --mode    R15   (ou MIXAMO — defaut: R15)

Usage module (appele par le notebook Colab) :
    from retarget_r15 import run
    result = run(fbx_in, plan_path, fbx_out, mode="R15")

POUR L'EMPEROR. POUR LA FLOTTE FERRUS.
"""

import sys
import os
import json
import argparse


# ══ Mapping et hierarchie R15 ══════════════════════════════════════════════════

DM_TO_R15 = {
    "hips_JNT":       "LowerTorso",
    "spine2_JNT":     "UpperTorso",
    "head_JNT":       "Head",
    "l_arm_JNT":      "LeftUpperArm",
    "l_forearm_JNT":  "LeftLowerArm",
    "l_hand_JNT":     "LeftHand",
    "r_arm_JNT":      "RightUpperArm",
    "r_forearm_JNT":  "RightLowerArm",
    "r_hand_JNT":     "RightHand",
    "l_upleg_JNT":    "LeftUpperLeg",
    "l_leg_JNT":      "LeftLowerLeg",
    "l_foot_JNT":     "LeftFoot",
    "r_upleg_JNT":    "RightUpperLeg",
    "r_leg_JNT":      "RightLowerLeg",
    "r_foot_JNT":     "RightFoot",
}

R15_HIERARCHY = {
    "LowerTorso":    None,
    "UpperTorso":    "LowerTorso",
    "Head":          "UpperTorso",
    "LeftUpperArm":  "UpperTorso",
    "LeftLowerArm":  "LeftUpperArm",
    "LeftHand":      "LeftLowerArm",
    "RightUpperArm": "UpperTorso",
    "RightLowerArm": "RightUpperArm",
    "RightHand":     "RightLowerArm",
    "LeftUpperLeg":  "LowerTorso",
    "LeftLowerLeg":  "LeftUpperLeg",
    "LeftFoot":      "LeftLowerLeg",
    "RightUpperLeg": "LowerTorso",
    "RightLowerLeg": "RightUpperLeg",
    "RightFoot":     "RightLowerLeg",
}

ROOT_BONE_R15 = "LowerTorso"
ROOT_BONE_DM  = "hips_JNT"


# ══ Mapping et hierarchie MIXAMO ═══════════════════════════════════════════════
# Prefixe standard Mixamo : "mixamorig:" (detecte automatiquement si absent)

MIXAMO_PREFIX = "mixamorig:"

DM_TO_MIXAMO_BASE = {
    "hips_JNT":       "Hips",
    "spine_JNT":      "Spine",
    "spine1_JNT":     "Spine1",
    "spine2_JNT":     "Spine2",
    "neck_JNT":       "Neck",
    "head_JNT":       "Head",
    "l_shoulder_JNT": "LeftShoulder",
    "l_arm_JNT":      "LeftArm",
    "l_forearm_JNT":  "LeftForeArm",
    "l_hand_JNT":     "LeftHand",
    "r_shoulder_JNT": "RightShoulder",
    "r_arm_JNT":      "RightArm",
    "r_forearm_JNT":  "RightForeArm",
    "r_hand_JNT":     "RightHand",
    "l_upleg_JNT":    "LeftUpLeg",
    "l_leg_JNT":      "LeftLeg",
    "l_foot_JNT":     "LeftFoot",
    "l_toebase_JNT":  "LeftToeBase",
    "r_upleg_JNT":    "RightUpLeg",
    "r_leg_JNT":      "RightLeg",
    "r_foot_JNT":     "RightFoot",
    "r_toebase_JNT":  "RightToeBase",
}

MIXAMO_HIERARCHY_BASE = {
    "Hips":          None,
    "Spine":         "Hips",
    "Spine1":        "Spine",
    "Spine2":        "Spine1",
    "Neck":          "Spine2",
    "Head":          "Neck",
    "LeftShoulder":  "Spine2",
    "LeftArm":       "LeftShoulder",
    "LeftForeArm":   "LeftArm",
    "LeftHand":      "LeftForeArm",
    "RightShoulder": "Spine2",
    "RightArm":      "RightShoulder",
    "RightForeArm":  "RightArm",
    "RightHand":     "RightForeArm",
    "LeftUpLeg":     "Hips",
    "LeftLeg":       "LeftUpLeg",
    "LeftFoot":      "LeftLeg",
    "LeftToeBase":   "LeftFoot",
    "RightUpLeg":    "Hips",
    "RightLeg":      "RightUpLeg",
    "RightFoot":     "RightLeg",
    "RightToeBase":  "RightFoot",
}

ROOT_BONE_MIXAMO_BASE = "Hips"


def _build_mixamo_mapping(prefix: str) -> tuple[dict, dict, str]:
    """
    Construit le mapping et la hierarchie Mixamo avec le prefixe detecte.
    Retourne (dm_to_mixamo, mixamo_hierarchy, root_bone_mixamo).
    """
    dm_to_mixamo = {k: prefix + v for k, v in DM_TO_MIXAMO_BASE.items()}
    mixamo_hier  = {
        prefix + k: (prefix + v if v else None)
        for k, v in MIXAMO_HIERARCHY_BASE.items()
    }
    root_mixamo  = prefix + ROOT_BONE_MIXAMO_BASE
    return dm_to_mixamo, mixamo_hier, root_mixamo


# ══ Detection du prefixe Mixamo ═══════════════════════════════════════════════

def _detect_mixamo_prefix_from_fbx(fbx_path: str) -> str:
    """
    Inspecte les noms de bones d'un FBX via bpy pour determiner
    si le prefixe 'mixamorig:' est present ou non.
    """
    import bpy

    # Charger temporairement pour detecter le prefixe
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=os.path.abspath(fbx_path))

    for obj in bpy.context.scene.objects:
        if obj.type == "ARMATURE":
            bone_names = {b.name for b in obj.data.bones}
            if f"{MIXAMO_PREFIX}Hips" in bone_names:
                return MIXAMO_PREFIX
            if "Hips" in bone_names:
                return ""
            break

    return MIXAMO_PREFIX  # fallback : prefixe standard


# ══ Extraction de la pose repos de DeepMotion ═════════════════════════════════

def _extract_rest_pose(dm_armature) -> dict:
    """
    Extrait head/tail/roll de chaque bone DeepMotion en mode edition.
    """
    import bpy

    bpy.context.view_layer.objects.active = dm_armature
    bpy.ops.object.mode_set(mode="EDIT")

    rest_pose = {}
    for eb in dm_armature.data.edit_bones:
        rest_pose[eb.name] = {
            "head": eb.head.copy(),
            "tail": eb.tail.copy(),
            "roll": eb.roll,
        }

    bpy.ops.object.mode_set(mode="OBJECT")
    return rest_pose


# ══ Construction du rig cible ═════════════════════════════════════════════════

def _build_target_armature(scene, rest_pose: dict,
                            dm_to_target: dict,
                            target_hierarchy: dict,
                            rig_name: str) -> object:
    """
    Construit programmatiquement l'armature cible a partir des positions repos DeepMotion.
    Fonctionne pour R15 (15 bones) et Mixamo (22 bones) — ZERO fichier GLB requis.
    """
    import bpy

    arm_data     = bpy.data.armatures.new(rig_name)
    arm_obj      = bpy.data.objects.new(rig_name, arm_data)
    scene.collection.objects.link(arm_obj)
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode="EDIT")

    edit_bones   = arm_data.edit_bones
    target_to_dm = {v: k for k, v in dm_to_target.items()}

    for target_name in target_hierarchy:
        dm_name = target_to_dm.get(target_name)
        if dm_name is None or dm_name not in rest_pose:
            raise RuntimeError(
                f"[retarget] Bone DeepMotion '{dm_name}' absent du FBX "
                f"(attendu pour construire '{target_name}')"
            )
        data  = rest_pose[dm_name]
        eb    = edit_bones.new(target_name)
        eb.head = data["head"]
        eb.tail = data["tail"]
        eb.roll = data["roll"]

    for target_name, parent_name in target_hierarchy.items():
        if parent_name is not None:
            edit_bones[target_name].parent = edit_bones[parent_name]

    bpy.ops.object.mode_set(mode="OBJECT")
    return arm_obj


# ══ Transfert d'animation ════════════════════════════════════════════════════

def _set_rotation_modes(armature, mode: str = "QUATERNION"):
    """Force le mode de rotation sur tous les pose bones."""
    for pb in armature.pose.bones:
        pb.rotation_mode = mode


def _transfer_animation(scene, dm_armature, target_armature,
                         dm_to_target: dict,
                         root_dm: str, root_target: str,
                         frame_start: int, frame_end: int) -> int:
    """
    Transfere les rotations (et la translation du root) frame par frame.
    Methode : pose_bone.matrix_basis — universel euler/quaternion.
    """
    import bpy

    _set_rotation_modes(target_armature, "QUATERNION")
    frames_done = 0

    for frame in range(frame_start, frame_end + 1):
        scene.frame_set(frame)
        bpy.context.view_layer.update()

        dm_root     = dm_armature.pose.bones.get(root_dm)
        target_root = target_armature.pose.bones.get(root_target)

        if dm_root and target_root:
            target_root.location            = dm_root.matrix_basis.translation.copy()
            target_root.rotation_quaternion = dm_root.matrix_basis.to_3x3().to_quaternion()
            target_root.keyframe_insert(data_path="location",            frame=frame)
            target_root.keyframe_insert(data_path="rotation_quaternion", frame=frame)

        for dm_name, target_name in dm_to_target.items():
            if dm_name == root_dm:
                continue
            dm_bone     = dm_armature.pose.bones.get(dm_name)
            target_bone = target_armature.pose.bones.get(target_name)
            if dm_bone is None or target_bone is None:
                continue
            target_bone.rotation_quaternion = dm_bone.matrix_basis.to_3x3().to_quaternion()
            target_bone.keyframe_insert(data_path="rotation_quaternion", frame=frame)

        frames_done += 1

    return frames_done


# ══ Chargement du plan ════════════════════════════════════════════════════════

def _load_retarget_params(plan_path: str) -> dict | None:
    """
    Charge plan_corrections.json et extrait les params retargeting.
    Retourne None si explicitement desactive (enabled=false).
    """
    with open(plan_path, "r", encoding="utf-8") as f:
        plan = json.load(f)
    retarget = plan.get("retargeting_r15", {})
    if retarget.get("enabled", True) is False:
        return None
    return {
        "enabled":           True,
        "t_pose_disponible": retarget.get("t_pose_disponible", True),
    }


# ══ Fonction principale ═══════════════════════════════════════════════════════

def run(fbx_in: str, plan_path: str, fbx_out: str, mode: str = "R15") -> dict:
    """
    Retargete le FBX DeepMotion corrige vers R15 ou Mixamo.

    Args:
        fbx_in    : chemin vers le FBX source (sortie compartiment EXEC)
        plan_path : chemin vers plan_corrections.json
        fbx_out   : chemin vers le FBX de sortie
        mode      : "R15" (defaut) ou "MIXAMO"

    Returns:
        dict de rapport {status, mode, bones_retargetes, frames_transferees, ...}
    """
    import bpy

    mode = mode.upper()
    if mode not in ("R15", "MIXAMO"):
        raise ValueError(f"[retarget] Mode invalide : '{mode}'. Valeurs : R15, MIXAMO")

    params = _load_retarget_params(plan_path)
    if params is None:
        print("[retarget] Retargeting desactive dans plan_corrections.json")
        import shutil
        shutil.copy2(fbx_in, fbx_out)
        return {"status": "skipped", "mode": mode, "raison": "enabled=false"}

    t_pose = params["t_pose_disponible"]

    print(f"[retarget] === FERRUS ANIMUS — MODE {mode} ===")
    if not t_pose:
        print("[retarget] AVERTISSEMENT : t_pose_incluse=false (derive possible sur certains bones)")

    # Charger le FBX corrige
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=os.path.abspath(fbx_in))

    dm_armature = next((o for o in bpy.context.scene.objects if o.type == "ARMATURE"), None)
    if not dm_armature:
        raise RuntimeError(f"[retarget] Aucune armature dans {fbx_in}")

    dm_action = dm_armature.animation_data.action if dm_armature.animation_data else None
    if not dm_action:
        raise RuntimeError("[retarget] Aucune animation dans l'armature DeepMotion")

    frame_start = int(dm_action.frame_range[0])
    frame_end   = int(dm_action.frame_range[1])
    nb_frames   = frame_end - frame_start + 1

    print(f"[retarget] Armature DeepMotion : {len(dm_armature.data.bones)} bones")
    print(f"[retarget] Animation : frames {frame_start} → {frame_end} ({nb_frames} frames)")

    # ── Choisir le mapping selon le mode ─────────────────────────────────────
    if mode == "R15":
        dm_to_target  = DM_TO_R15
        target_hier   = R15_HIERARCHY
        root_target   = ROOT_BONE_R15
        root_dm       = ROOT_BONE_DM
        rig_name      = "R15_Rig"
        nb_bones_ref  = 15

    else:  # MIXAMO
        # Detecter le prefixe (avec ou sans "mixamorig:")
        dm_bone_names_check = {b.name for b in dm_armature.data.bones}
        # L'armature DeepMotion n'a pas de prefixe mixamo.
        # Le prefixe cible est toujours MIXAMO_PREFIX pour les noms du rig output.
        # Cependant : si le FBX avatar de l'utilisateur n'a pas le prefixe, CORPUS
        # devra etre configure en consequence. Par defaut on genere avec prefixe.
        prefix        = MIXAMO_PREFIX
        dm_to_target, target_hier, root_target = _build_mixamo_mapping(prefix)
        root_dm       = ROOT_BONE_DM
        rig_name      = "Mixamo_Rig"
        nb_bones_ref  = 22
        print(f"[retarget] Prefixe Mixamo utilise : '{prefix}'")

    # ── Validation bones DeepMotion ──────────────────────────────────────────
    dm_bone_names   = {b.name for b in dm_armature.data.bones}
    bones_presents  = [k for k in dm_to_target if k in dm_bone_names]
    bones_manquants = [k for k in dm_to_target if k not in dm_bone_names]

    if bones_manquants:
        print(f"[retarget] Attention : {len(bones_manquants)} bones absents :")
        for b in bones_manquants:
            print(f"  MANQUANT : {b} → {dm_to_target[b]}")

    if not bones_presents:
        raise RuntimeError("[retarget] Aucun bone du mapping trouve dans le FBX")

    print(f"[retarget] Bones cartographies : {len(bones_presents)}/{nb_bones_ref}")

    # ── Extraction pose repos ─────────────────────────────────────────────────
    print("[retarget] Extraction de la pose repos DeepMotion...")
    rest_pose = _extract_rest_pose(dm_armature)

    # ── Construction du rig cible ─────────────────────────────────────────────
    print(f"[retarget] Construction du rig {mode} (ZERO fichier GLB)...")
    scene      = bpy.context.scene
    target_arm = _build_target_armature(scene, rest_pose, dm_to_target, target_hier, rig_name)
    print(f"[retarget] Rig {mode} construit : {len(target_arm.data.bones)} bones")

    for t_name in target_hier:
        dm_name = {v: k for k, v in dm_to_target.items()}.get(t_name, "?")
        status  = "OK" if dm_name in dm_bone_names else "MANQUANT"
        print(f"  {t_name:30s} ← {dm_name:20s} [{status}]")

    # ── Creer l'action cible ──────────────────────────────────────────────────
    target_action = bpy.data.actions.new(name=f"{mode}_Animation")
    target_arm.animation_data_create()
    target_arm.animation_data.action = target_action

    # ── Transfert animation ───────────────────────────────────────────────────
    print(f"[retarget] Transfert animation : {nb_frames} frames en cours...")
    frames_done = _transfer_animation(
        scene, dm_armature, target_arm,
        dm_to_target, root_dm, root_target,
        frame_start, frame_end
    )
    print(f"[retarget] Transfert termine : {frames_done} frames")

    # ── Export FBX ────────────────────────────────────────────────────────────
    bpy.ops.object.select_all(action="DESELECT")
    target_arm.select_set(True)
    bpy.context.view_layer.objects.active = target_arm
    scene.frame_set(frame_start)

    os.makedirs(os.path.dirname(os.path.abspath(fbx_out)), exist_ok=True)
    bpy.ops.export_scene.fbx(
        filepath=os.path.abspath(fbx_out),
        use_selection=True,
        apply_unit_scale=True,
        bake_anim=True,
        bake_anim_use_all_bones=True,
        bake_anim_force_startend_keying=True,
        add_leaf_bones=False,
    )

    print(f"[retarget] FBX {mode} exporte : {fbx_out}")
    print(f"[retarget] PIPELINE COMPLET. POUR L'EMPEROR.")

    return {
        "status":             "ok",
        "mode":               mode,
        "bones_retargetes":   bones_presents,
        "bones_manquants":    bones_manquants,
        "frames_transferees": frames_done,
        "target_bones":       list(target_hier.keys()),
        "t_pose_disponible":  t_pose,
        "fbx_out":            fbx_out,
    }


# ══ Point d'entree CLI ════════════════════════════════════════════════════════

if __name__ == "__main__":
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
    else:
        argv = []

    parser = argparse.ArgumentParser(
        description="FERRUS ANIMUS — OUTPUT : Retargeting DeepMotion → R15 ou Mixamo"
    )
    parser.add_argument("--fbx-in",  required=True, help="FBX corrige (sortie EXEC)")
    parser.add_argument("--plan",    required=True, help="plan_corrections.json")
    parser.add_argument("--fbx-out", required=True, help="FBX de sortie")
    parser.add_argument("--mode",    default="R15",  choices=["R15", "MIXAMO"],
                        help="Mode retargeting : R15 (defaut) ou MIXAMO (22 bones Mixamo.com)")

    args = parser.parse_args(argv)

    result = run(args.fbx_in, args.plan, args.fbx_out, mode=args.mode)
    print("\n[retarget] Rapport final :")
    print(json.dumps(result, indent=2, ensure_ascii=False))
