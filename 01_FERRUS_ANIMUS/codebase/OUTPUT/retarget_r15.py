"""
retarget_r15.py — FERRUS ANIMUS / Compartiment OUTPUT
Retargeting du squelette DeepMotion (52 bones) vers Roblox R15 (15 bones).

Consomme : plan_corrections.json -> retargeting_r15
  {
    "enabled": true,
    "t_pose_disponible": true
  }

Principe :
  1. Charge le FBX corrige (sortie compartiment EXEC) contenant l'armature DeepMotion.
  2. Extrait les positions de repos (head/tail/roll) des 15 bones cartographies.
  3. Construit programmatiquement une nouvelle armature Roblox R15 avec la
     meme hierarchie et les memes positions de repos — ZERO fichier GLB requis.
  4. Transfere les rotations frame par frame via pose_bone.matrix_basis :
       - Root (hips_JNT → LowerTorso) : location + rotation_quaternion
       - Tous les autres : rotation_quaternion uniquement
  5. Force le mode QUATERNION sur tous les bones R15 (contrainte Mechanicus —
     previent le gimbal lock lors de l'import Roblox).
  6. Exporte uniquement l'armature R15 en FBX.

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

Usage standalone (bpy headless) :
    blender --background --python retarget_r15.py -- \\
        --fbx-in  path/to/input_corrige.fbx \\
        --plan    path/to/plan_corrections.json \\
        --fbx-out path/to/ferrus_R15.fbx

Usage module (appele par le notebook Colab) :
    from retarget_r15 import run
    result = run(fbx_in, plan_path, fbx_out)
"""

import sys
import os
import json
import argparse


# ══ Mapping et hierarchie R15 ══════════════════════════════════════════════════

# DeepMotion bone → Roblox R15 bone
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

R15_TO_DM = {v: k for k, v in DM_TO_R15.items()}

# Hierarchie R15 : bone → parent (None = racine)
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


# ══ Extraction de la pose repos de DeepMotion ═════════════════════════════════

def _extract_rest_pose(dm_armature) -> dict:
    """
    Extrait head/tail/roll de chaque bone DeepMotion en mode edition.
    Necessite que dm_armature soit l'objet actif dans le contexte Blender.

    Returns:
        dict {bone_name: {'head': Vector, 'tail': Vector, 'roll': float}}
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


# ══ Construction du rig R15 ═══════════════════════════════════════════════════

def _build_r15_armature(scene, rest_pose: dict) -> object:
    """
    Construit programmatiquement l'armature Roblox R15 avec 15 bones.
    Chaque bone est positionne selon la pose repos du bone DeepMotion correspondant.

    Args:
        scene     : bpy.types.Scene courant
        rest_pose : dict issu de _extract_rest_pose (positions des bones DeepMotion)

    Returns:
        bpy.types.Object armature R15
    """
    import bpy

    arm_data = bpy.data.armatures.new("R15_Rig")
    arm_obj  = bpy.data.objects.new("R15_Rig", arm_data)
    scene.collection.objects.link(arm_obj)

    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode="EDIT")

    edit_bones = arm_data.edit_bones

    # Creer les bones dans l'ordre de la hierarchie (parent avant enfant)
    for r15_name in R15_HIERARCHY:
        dm_name = R15_TO_DM[r15_name]

        if dm_name not in rest_pose:
            raise RuntimeError(
                f"[retarget_r15] Bone DeepMotion '{dm_name}' absent du FBX "
                f"(attendu pour construire '{r15_name}')"
            )

        data  = rest_pose[dm_name]
        eb    = edit_bones.new(r15_name)
        eb.head = data["head"]
        eb.tail = data["tail"]
        eb.roll = data["roll"]

    # Assigner les parents
    for r15_name, parent_name in R15_HIERARCHY.items():
        if parent_name is not None:
            edit_bones[r15_name].parent = edit_bones[parent_name]

    bpy.ops.object.mode_set(mode="OBJECT")
    return arm_obj


# ══ Transfert d'animation ════════════════════════════════════════════════════

def _set_rotation_modes(armature, mode: str = "QUATERNION"):
    """Force le mode de rotation sur tous les pose bones de l'armature."""
    for pb in armature.pose.bones:
        pb.rotation_mode = mode


def _transfer_animation(scene, dm_armature, r15_armature,
                        frame_start: int, frame_end: int) -> int:
    """
    Transfere les rotations (et la localisation du root) frame par frame.

    Methode : pose_bone.matrix_basis.to_3x3().to_quaternion()
    Fonctionne quel que soit le rotation_mode du bone source (euler ou quaternion).
    matrix_basis = contribution pure de la pose (sans rest pose) en espace bone local.

    Args:
        scene       : bpy.types.Scene
        dm_armature : armature DeepMotion source
        r15_armature: armature R15 destination
        frame_start : premiere frame a baker
        frame_end   : derniere frame a baker

    Returns:
        nombre de frames transferees
    """
    import bpy

    # Forcer QUATERNION sur tous les bones R15 avant de keyframer
    _set_rotation_modes(r15_armature, "QUATERNION")

    frames_done = 0

    for frame in range(frame_start, frame_end + 1):
        scene.frame_set(frame)
        bpy.context.view_layer.update()

        # Bone racine : location + rotation
        dm_hips  = dm_armature.pose.bones.get(ROOT_BONE_DM)
        r15_root = r15_armature.pose.bones.get(ROOT_BONE_R15)

        if dm_hips and r15_root:
            # matrix_basis.translation = decalage de pose depuis le repos
            r15_root.location            = dm_hips.matrix_basis.translation.copy()
            r15_root.rotation_quaternion = dm_hips.matrix_basis.to_3x3().to_quaternion()
            r15_root.keyframe_insert(data_path="location",            frame=frame)
            r15_root.keyframe_insert(data_path="rotation_quaternion", frame=frame)

        # Tous les autres bones : rotation uniquement
        for dm_name, r15_name in DM_TO_R15.items():
            if dm_name == ROOT_BONE_DM:
                continue

            dm_bone  = dm_armature.pose.bones.get(dm_name)
            r15_bone = r15_armature.pose.bones.get(r15_name)

            if dm_bone is None or r15_bone is None:
                continue

            r15_bone.rotation_quaternion = dm_bone.matrix_basis.to_3x3().to_quaternion()
            r15_bone.keyframe_insert(data_path="rotation_quaternion", frame=frame)

        frames_done += 1

    return frames_done


# ══ Chargement du plan ════════════════════════════════════════════════════════

def _load_retarget_params(plan_path: str) -> dict | None:
    """
    Charge plan_corrections.json et extrait les params retargeting_r15.
    Retourne None uniquement si explicitement desactive (enabled=false).
    Par defaut, le retargeting est toujours actif (compartiment OUTPUT obligatoire).
    """
    with open(plan_path, "r", encoding="utf-8") as f:
        plan = json.load(f)

    retarget = plan.get("retargeting_r15", {})

    if retarget.get("enabled", True) is False:
        return None

    return {
        "enabled":          True,
        "t_pose_disponible": retarget.get("t_pose_disponible", True),
    }


# ══ Fonction principale ═══════════════════════════════════════════════════════

def run(fbx_in: str, plan_path: str, fbx_out: str) -> dict:
    """
    Retargete le FBX DeepMotion corrige vers le format Roblox R15.

    Args:
        fbx_in    : chemin vers le FBX source (sortie compartiment EXEC)
        plan_path : chemin vers plan_corrections.json
        fbx_out   : chemin vers le FBX de sortie R15 (pret pour Roblox)

    Returns:
        dict de rapport {status, bones_retargetes, frames_transferees,
                         bones_manquants, fbx_out}
    """
    import bpy

    # Charger les parametres
    params = _load_retarget_params(plan_path)
    if params is None:
        print("[retarget_r15] Retargeting desactive dans plan_corrections.json")
        import shutil
        shutil.copy2(fbx_in, fbx_out)
        return {"status": "skipped", "raison": "enabled=false"}

    t_pose = params["t_pose_disponible"]

    print("[retarget_r15] Demarrage du retargeting DeepMotion → Roblox R15")
    if not t_pose:
        print("[retarget_r15] AVERTISSEMENT : t_pose_incluse=false")
        print("[retarget_r15] La pose repos sera extraite du bind pose DeepMotion (non calibre T-pose)")
        print("[retarget_r15] Risque de legere derive d'orientation sur certains bones R15")

    # Charger le FBX corrige
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=os.path.abspath(fbx_in))

    dm_armature = next((o for o in bpy.context.scene.objects if o.type == "ARMATURE"), None)
    if not dm_armature:
        raise RuntimeError(f"[retarget_r15] Aucune armature dans {fbx_in}")

    dm_action = dm_armature.animation_data.action if dm_armature.animation_data else None
    if not dm_action:
        raise RuntimeError("[retarget_r15] Aucune animation dans l'armature DeepMotion")

    frame_start = int(dm_action.frame_range[0])
    frame_end   = int(dm_action.frame_range[1])
    nb_frames   = frame_end - frame_start + 1

    print(f"[retarget_r15] Armature DeepMotion : {len(dm_armature.data.bones)} bones")
    print(f"[retarget_r15] Animation : frames {frame_start} → {frame_end} ({nb_frames} frames)")

    # Verifier que tous les bones du mapping sont presents dans le FBX
    dm_bone_names  = {b.name for b in dm_armature.data.bones}
    bones_presents = [k for k in DM_TO_R15 if k in dm_bone_names]
    bones_manquants = [k for k in DM_TO_R15 if k not in dm_bone_names]

    if bones_manquants:
        print(f"[retarget_r15] Attention : {len(bones_manquants)} bones absents du FBX :")
        for b in bones_manquants:
            print(f"  MANQUANT : {b} → {DM_TO_R15[b]}")

    if not bones_presents:
        raise RuntimeError("[retarget_r15] Aucun bone du mapping trouve dans le FBX")

    print(f"[retarget_r15] Bones cartographies : {len(bones_presents)}/15")

    # Extraire la pose repos depuis DeepMotion
    print("[retarget_r15] Extraction de la pose repos DeepMotion...")
    rest_pose = _extract_rest_pose(dm_armature)

    # Construire le rig R15 programmatiquement
    print("[retarget_r15] Construction du rig R15 (ZERO fichier GLB)...")
    scene       = bpy.context.scene
    r15_armature = _build_r15_armature(scene, rest_pose)

    print(f"[retarget_r15] Rig R15 construit : {len(r15_armature.data.bones)} bones")
    for r15_name in R15_HIERARCHY:
        dm_name = R15_TO_DM[r15_name]
        status = "OK" if dm_name in dm_bone_names else "MANQUANT"
        print(f"  {r15_name:20s} ← {dm_name:20s} [{status}]")

    # Creer une action pour le rig R15
    r15_action = bpy.data.actions.new(name="R15_Animation")
    r15_armature.animation_data_create()
    r15_armature.animation_data.action = r15_action

    # Transferer l'animation frame par frame
    print(f"[retarget_r15] Transfert animation : {nb_frames} frames en cours...")
    frames_done = _transfer_animation(
        scene, dm_armature, r15_armature, frame_start, frame_end
    )
    print(f"[retarget_r15] Transfert termine : {frames_done} frames")

    # Selectionner uniquement le rig R15 pour l'export
    bpy.ops.object.select_all(action="DESELECT")
    r15_armature.select_set(True)
    bpy.context.view_layer.objects.active = r15_armature
    scene.frame_set(frame_start)

    # Exporter uniquement le rig R15
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

    print(f"[retarget_r15] FBX R15 exporte : {fbx_out}")

    return {
        "status":             "ok",
        "bones_retargetes":   bones_presents,
        "bones_manquants":    bones_manquants,
        "frames_transferees": frames_done,
        "r15_bones":          list(R15_HIERARCHY.keys()),
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
        description="FERRUS ANIMUS — OUTPUT : Retargeting DeepMotion → Roblox R15"
    )
    parser.add_argument("--fbx-in",  required=True, help="FBX corrige (sortie EXEC)")
    parser.add_argument("--plan",    required=True, help="plan_corrections.json")
    parser.add_argument("--fbx-out", required=True, help="FBX R15 sortie")

    args = parser.parse_args(argv)

    result = run(args.fbx_in, args.plan, args.fbx_out)
    print("\n[retarget_r15] Rapport final :")
    print(json.dumps(result, indent=2, ensure_ascii=False))
