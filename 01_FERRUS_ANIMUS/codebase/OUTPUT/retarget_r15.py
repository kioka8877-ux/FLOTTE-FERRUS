"""
retarget_r15.py — FERRUS ANIMUS / Compartiment OUTPUT
Retargeting DeepMotion (52 bones) vers R15 (15 bones), Mixamo (22 bones),
ou transfert direct DeepMotion (52 bones → 52 bones avec mesh OSSEUS).

MODES :
  DEEPMOTION — transfert direct FCurves (memes noms de bones) + mesh OSSEUS obligatoire
  R15        — retargeting vers Roblox R15 (15 bones)
  MIXAMO     — retargeting vers Mixamo (22 bones)

Mapping DeepMotion → R15 (15 bones actifs, convention custom) :
    Hip           → LowerTorso   (ROOT)
    spine1_JNT    → UpperTorso
    Head          → Head
    LeftUpArm     → LeftUpperArm
    LeftLowArm    → LeftLowerArm
    LeftHand      → LeftHand
    RightUpArm    → RightUpperArm
    RightLowArm   → RightLowerArm
    RightHand     → RightHand
    LeftUpLeg     → LeftUpperLeg
    LeftLowLeg    → LeftLowerLeg
    LeftFoot      → LeftFoot
    RightUpLeg    → RightUpperLeg
    RightLowLeg   → RightLowerLeg
    RightFoot     → RightFoot

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
        --fbx-in     path/to/input_corrige.fbx \
        --plan       path/to/plan_corrections.json \
        --fbx-out    path/to/ferrus_out.fbx \
        --mode       DEEPMOTION   (ou R15 ou MIXAMO — defaut: R15) \
        --avatar-fbx path/to/osseus_avatar.fbx   (requis pour DEEPMOTION, optionnel pour R15/MIXAMO)

Usage module (appele par le notebook Colab) :
    from retarget_r15 import run
    result = run(fbx_in, plan_path, fbx_out, mode="DEEPMOTION", avatar_fbx="osseus.fbx")

POUR L'EMPEROR. POUR LA FLOTTE FERRUS.
"""

import sys
import os
import json
import argparse


# ══ Mapping et hierarchie R15 ══════════════════════════════════════════════════

DM_TO_R15 = {
    "Hip":          "LowerTorso",
    "spine1_JNT":   "UpperTorso",
    "Head":         "Head",
    "LeftUpArm":    "LeftUpperArm",
    "LeftLowArm":   "LeftLowerArm",
    "LeftHand":     "LeftHand",
    "RightUpArm":   "RightUpperArm",
    "RightLowArm":  "RightLowerArm",
    "RightHand":    "RightHand",
    "LeftUpLeg":    "LeftUpperLeg",
    "LeftLowLeg":   "LeftLowerLeg",
    "LeftFoot":     "LeftFoot",
    "RightUpLeg":   "RightUpperLeg",
    "RightLowLeg":  "RightLowerLeg",
    "RightFoot":    "RightFoot",
}

# ══ Mapping DeepMotion → OSSEUS (mode transfert direct 52 bones) ══════════════
# DeepMotion utilise une convention mixte (noms courts pour le corps, _JNT pour doigts)
# OSSEUS genere tous les bones avec le suffixe _JNT.
# Les bones deja identiques (doigts, spine_JNT, spine1_JNT, toebases) ne sont pas listes.

DM_TO_OSSEUS = {
    "Hip":         "hips_JNT",
    "Chest":       "spine2_JNT",
    "Neck":        "neck_JNT",
    "Head":        "head_JNT",
    "LeftCollar":  "l_shoulder_JNT",
    "LeftUpArm":   "l_arm_JNT",
    "LeftLowArm":  "l_forearm_JNT",
    "LeftHand":    "l_hand_JNT",
    "LeftUpLeg":   "l_upleg_JNT",
    "LeftLowLeg":  "l_leg_JNT",
    "LeftFoot":    "l_foot_JNT",
    "RightCollar": "r_shoulder_JNT",
    "RightUpArm":  "r_arm_JNT",
    "RightLowArm": "r_forearm_JNT",
    "RightHand":   "r_hand_JNT",
    "RightUpLeg":  "r_upleg_JNT",
    "RightLowLeg": "r_leg_JNT",
    "RightFoot":   "r_foot_JNT",
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
ROOT_BONE_DM  = "Hip"


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


# ══ Mode DEEPMOTION — copy directe FCurves ════════════════════════════════════

def _copy_fcurves_direct(dm_action, osseus_arm) -> int:
    """
    Copie les FCurves de l'action DeepMotion vers une nouvelle action
    sur l'armature OSSEUS. Fonctionne car les bones ont exactement les
    memes noms dans les deux squelettes (52 bones DeepMotion).

    Force les rotations en quaternion sur tous les bones OSSEUS.

    Returns:
        Nombre de FCurves copiees.
    """
    import bpy

    # Forcer quaternion sur tous les bones OSSEUS
    for pb in osseus_arm.pose.bones:
        pb.rotation_mode = "QUATERNION"

    osseus_bone_names = {b.name for b in osseus_arm.data.bones}

    new_action = bpy.data.actions.new(name="DEEPMOTION_Animation")
    osseus_arm.animation_data_create()
    osseus_arm.animation_data.action = new_action

    copied = 0
    for fc in dm_action.fcurves:
        # Trouver le bone reference dans le data_path
        # Format : 'pose.bones["bone_name"].rotation_quaternion'
        bone_name = None
        for bn in osseus_bone_names:
            if f'"{bn}"' in fc.data_path:
                bone_name = bn
                break

        if bone_name is None:
            continue  # FCurve ne correspond a aucun bone OSSEUS

        new_fc = new_action.fcurves.new(
            data_path=fc.data_path,
            index=fc.array_index,
        )
        new_fc.keyframe_points.add(len(fc.keyframe_points))
        for i, kp in enumerate(fc.keyframe_points):
            new_fc.keyframe_points[i].co           = kp.co
            new_fc.keyframe_points[i].interpolation = kp.interpolation
            new_fc.keyframe_points[i].handle_left   = kp.handle_left
            new_fc.keyframe_points[i].handle_right  = kp.handle_right
        new_fc.update()
        copied += 1

    return copied


# ══ Injection mesh OSSEUS (R15 / MIXAMO) ══════════════════════════════════════

def _import_osseus_meshes(avatar_fbx: str, scene) -> list:
    """
    Importe le FBX OSSEUS dans la scene courante et retourne la liste
    des objets MESH importes (l'armature OSSEUS n'est pas retournee).

    L'avatar OSSEUS est lu en lecture seule — il n'est jamais modifie.
    Les meshes sont lies au rig cible uniquement a l'export.
    """
    import bpy

    # Snapshot des objets existants avant import
    existing = set(bpy.context.scene.objects)

    bpy.ops.import_scene.fbx(filepath=os.path.abspath(avatar_fbx))

    # Identifier les nouveaux objets
    imported = set(bpy.context.scene.objects) - existing

    # Recuperer les armatures importees (a supprimer — on veut uniquement les meshes)
    osseus_arms  = [o for o in imported if o.type == "ARMATURE"]
    osseus_meshes = [o for o in imported if o.type == "MESH"]

    # Supprimer l'armature OSSEUS importee (on garde uniquement les meshes)
    for arm in osseus_arms:
        bpy.data.objects.remove(arm, do_unlink=True)

    print(f"[retarget] Meshes OSSEUS importes : {len(osseus_meshes)}")
    for m in osseus_meshes:
        print(f"  mesh : {m.name}")

    return osseus_meshes


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

def run(fbx_in: str, plan_path: str, fbx_out: str,
        mode: str = "R15", avatar_fbx: str | None = None) -> dict:
    """
    Retargete le FBX DeepMotion corrige vers R15, Mixamo ou DEEPMOTION.

    Args:
        fbx_in     : chemin vers le FBX source (sortie compartiment EXEC)
        plan_path  : chemin vers plan_corrections.json
        fbx_out    : chemin vers le FBX de sortie
        mode       : "R15" (defaut), "MIXAMO" ou "DEEPMOTION"
        avatar_fbx : chemin vers le FBX OSSEUS (requis pour DEEPMOTION,
                     optionnel pour R15/MIXAMO — si fourni, le mesh est inclus dans l'output)

    Returns:
        dict de rapport {status, mode, bones_retargetes, frames_transferees, ...}
    """
    import bpy

    mode = mode.upper()
    if mode not in ("R15", "MIXAMO", "DEEPMOTION"):
        raise ValueError(f"[retarget] Mode invalide : '{mode}'. Valeurs : R15, MIXAMO, DEEPMOTION")

    if mode == "DEEPMOTION" and not avatar_fbx:
        raise ValueError("[retarget] Mode DEEPMOTION : --avatar-fbx est obligatoire")

    params = _load_retarget_params(plan_path)
    if params is None:
        print("[retarget] Retargeting desactive dans plan_corrections.json")
        import shutil
        shutil.copy2(fbx_in, fbx_out)
        return {"status": "skipped", "mode": mode, "raison": "enabled=false"}

    t_pose = params["t_pose_disponible"]
    print(f"[retarget] === FERRUS ANIMUS — MODE {mode} ===")

    # ═══════════════════════════════════════════════════════════════════════════
    # MODE DEEPMOTION — transfert direct FCurves (meme squelette 52 bones)
    # ═══════════════════════════════════════════════════════════════════════════
    if mode == "DEEPMOTION":
        bpy.ops.wm.read_factory_settings(use_empty=True)
        scene = bpy.context.scene

        # Parametres d'import FBX uniformes — garantit le meme espace de coordonnees
        # pour OSSEUS et DeepMotion, evite le mismatch d'axes (bug "Superman / vole").
        # Blender 4.2 : apply_unit_scale et use_manual_orientation supprimes de l'API
        FBX_IMPORT_PARAMS = dict(
            axis_forward="-Z",
            axis_up="Y",
            global_scale=1.0,
            use_anim=True,
        )

        # 1. Charger l'avatar OSSEUS (mesh + squelette T-pose)
        print(f"[retarget] Chargement OSSEUS : {avatar_fbx}")
        bpy.ops.import_scene.fbx(filepath=os.path.abspath(avatar_fbx), **FBX_IMPORT_PARAMS)

        osseus_arm = next((o for o in scene.objects if o.type == "ARMATURE"), None)
        if not osseus_arm:
            raise RuntimeError(f"[retarget] Aucune armature dans l'avatar OSSEUS : {avatar_fbx}")

        mesh_objects = [o for o in scene.objects if o.type == "MESH"]
        print(f"[retarget] OSSEUS : armature '{osseus_arm.name}', "
              f"{len(osseus_arm.data.bones)} bones, "
              f"{len(mesh_objects)} mesh(es)")

        # Normaliser l'espace de l'armature OSSEUS (pas d'animation → safe).
        # Apres transform_apply, osseus_arm.matrix_world ≈ identite.
        # Les matrix_basis des bones DeepMotion seront directement comparables.
        bpy.context.view_layer.objects.active = osseus_arm
        bpy.ops.object.select_all(action="DESELECT")
        osseus_arm.select_set(True)
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
        print(f"[retarget] OSSEUS transform normalise : {osseus_arm.matrix_world}")

        # 2. Charger le FBX DeepMotion corrige (animation)
        print(f"[retarget] Chargement DeepMotion : {fbx_in}")
        existing_before = set(scene.objects)
        bpy.ops.import_scene.fbx(filepath=os.path.abspath(fbx_in), **FBX_IMPORT_PARAMS)

        dm_arm = next(
            (o for o in scene.objects if o.type == "ARMATURE" and o != osseus_arm),
            None
        )
        if not dm_arm:
            raise RuntimeError(
                f"[retarget] Armature DeepMotion introuvable apres import de {fbx_in}"
            )

        dm_action = dm_arm.animation_data.action if dm_arm.animation_data else None
        if not dm_action:
            raise RuntimeError("[retarget] Aucune animation dans l'armature DeepMotion")

        frame_start = int(dm_action.frame_range[0])
        frame_end   = int(dm_action.frame_range[1])
        nb_frames   = frame_end - frame_start + 1

        print(f"[retarget] DeepMotion : {len(dm_arm.data.bones)} bones, "
              f"frames {frame_start}→{frame_end} ({nb_frames} frames)")

        # 3. Verifier la correspondance des bones
        osseus_bones = {b.name for b in osseus_arm.data.bones}
        dm_bones     = {b.name for b in dm_arm.data.bones}
        communs      = osseus_bones & dm_bones
        absents_osseus = dm_bones - osseus_bones

        if absents_osseus:
            print(f"[retarget] {len(absents_osseus)} bones DeepMotion absents dans OSSEUS "
                  f"(FCurves ignorees) : {sorted(absents_osseus)[:5]}{'...' if len(absents_osseus) > 5 else ''}")

        print(f"[retarget] Bones en commun : {len(communs)}/{len(dm_bones)}")

        # 4. Bake frame-par-frame DeepMotion → OSSEUS
        # Le mapping DM_TO_OSSEUS traduit les noms courts DeepMotion vers les noms _JNT d'OSSEUS.
        # Les bones avec noms identiques (doigts, spine_JNT, etc.) sont passes directement.
        print("[retarget] Construction du mapping DM → OSSEUS...")

        # Construire la table de lookup : osseus_name → dm_name
        osseus_to_dm = {v: k for k, v in DM_TO_OSSEUS.items()}
        dm_bone_set = {b.name for b in dm_arm.data.bones}
        for bn in dm_bone_set:
            if bn not in osseus_to_dm.values() and bn not in {v for v in DM_TO_OSSEUS.keys()}:
                # Bone DM dont le nom existe tel quel dans OSSEUS (doigts, spine_JNT, etc.)
                osseus_to_dm.setdefault(bn, bn)

        print(f"[retarget] Bones mappes : {len(osseus_to_dm)}")
        print("[retarget] Bake frame-par-frame DeepMotion → OSSEUS...")

        for pb in osseus_arm.pose.bones:
            pb.rotation_mode = "QUATERNION"

        new_action = bpy.data.actions.new(name="DEEPMOTION_Baked")
        osseus_arm.animation_data_create()
        osseus_arm.animation_data.action = new_action

        # Matrice de conversion espace DM → espace OSSEUS (une seule fois, hors boucle).
        # Apres transform_apply sur OSSEUS, osseus_arm.matrix_world ≈ identite,
        # donc dm_to_osseus ≈ dm_arm.matrix_world.
        # Cela corrige le mismatch d'axes entre les deux armatures.
        dm_to_osseus = osseus_arm.matrix_world.inverted() @ dm_arm.matrix_world

        for frame in range(frame_start, frame_end + 1):
            scene.frame_set(frame)
            bpy.context.view_layer.update()

            for pb in osseus_arm.pose.bones:
                dm_name = osseus_to_dm.get(pb.name, pb.name)
                dm_pb = dm_arm.pose.bones.get(dm_name)
                if dm_pb is None:
                    continue
                # Fix #3 : decompose() gere correctement les matrices avec scale non-unitaire.
                # to_quaternion() direct sur Matrix4x4 echoue si scale != 1.
                _, rot, _ = dm_pb.matrix_basis.decompose()
                pb.rotation_quaternion = rot
                pb.keyframe_insert(data_path="rotation_quaternion", frame=frame)

                if pb.parent is None:  # Root bone : location aussi
                    # Fix #4 : lire la position en espace monde DM, convertir en espace OSSEUS.
                    # matrix_basis.translation est en espace local de l'armature DM.
                    # Si dm_arm a une rotation/scale objet, cette translation est dans
                    # un repere different de celui d'OSSEUS → personnage qui vole.
                    world_mat = dm_arm.matrix_world @ dm_pb.matrix
                    loc, _, _ = (osseus_arm.matrix_world.inverted() @ world_mat).decompose()
                    pb.location = loc
                    pb.keyframe_insert(data_path="location", frame=frame)

        fcurves_copies = len(new_action.fcurves)
        print(f"[retarget] FCurves bakees : {fcurves_copies}")

        # 5. Supprimer l'armature DeepMotion et les cameras
        bpy.data.objects.remove(dm_arm, do_unlink=True)
        for cam_obj in [o for o in scene.objects if o.type == "CAMERA"]:
            bpy.data.objects.remove(cam_obj, do_unlink=True)

        # 6. Exporter : armature OSSEUS + meshes
        scene.frame_start = frame_start
        scene.frame_end   = frame_end
        scene.frame_set(frame_start)

        bpy.ops.object.select_all(action="DESELECT")
        osseus_arm.select_set(True)
        for m in mesh_objects:
            m.select_set(True)
        bpy.context.view_layer.objects.active = osseus_arm

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

        print(f"[retarget] FBX DEEPMOTION exporte : {fbx_out}")
        print(f"[retarget] PIPELINE COMPLET. POUR L'EMPEROR.")

        return {
            "status":              "ok",
            "mode":                "DEEPMOTION",
            "fcurves_copies":      fcurves_copies,
            "bones_communs":       len(communs),
            "bones_absents_osseus": sorted(absents_osseus),
            "frames":              nb_frames,
            "mesh_present":        len(mesh_objects) > 0,
            "mesh_count":          len(mesh_objects),
            "fbx_out":             fbx_out,
        }

    # ═══════════════════════════════════════════════════════════════════════════
    # MODE R15 / MIXAMO — retargeting + injection mesh optionnelle
    # ═══════════════════════════════════════════════════════════════════════════

    if not t_pose:
        print("[retarget] AVERTISSEMENT : t_pose_incluse=false (derive possible sur certains bones)")

    # Charger le FBX corrige — memes parametres d'axes que le mode DEEPMOTION
    # Blender 4.2 : apply_unit_scale et use_manual_orientation supprimes de l'API
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(
        filepath=os.path.abspath(fbx_in),
        axis_forward="-Z",
        axis_up="Y",
        global_scale=1.0,
        use_anim=True,
    )

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

    # Choisir le mapping selon le mode
    if mode == "R15":
        dm_to_target  = DM_TO_R15
        target_hier   = R15_HIERARCHY
        root_target   = ROOT_BONE_R15
        root_dm       = ROOT_BONE_DM
        rig_name      = "R15_Rig"
        nb_bones_ref  = 15

    else:  # MIXAMO
        prefix        = MIXAMO_PREFIX
        dm_to_target, target_hier, root_target = _build_mixamo_mapping(prefix)
        root_dm       = ROOT_BONE_DM
        rig_name      = "Mixamo_Rig"
        nb_bones_ref  = 22
        print(f"[retarget] Prefixe Mixamo utilise : '{prefix}'")

    # Validation bones DeepMotion
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

    # Extraction pose repos
    print("[retarget] Extraction de la pose repos DeepMotion...")
    rest_pose = _extract_rest_pose(dm_armature)

    # Construction du rig cible
    print(f"[retarget] Construction du rig {mode} (ZERO fichier GLB)...")
    scene      = bpy.context.scene
    target_arm = _build_target_armature(scene, rest_pose, dm_to_target, target_hier, rig_name)
    print(f"[retarget] Rig {mode} construit : {len(target_arm.data.bones)} bones")

    for t_name in target_hier:
        dm_name = {v: k for k, v in dm_to_target.items()}.get(t_name, "?")
        status  = "OK" if dm_name in dm_bone_names else "MANQUANT"
        print(f"  {t_name:30s} ← {dm_name:20s} [{status}]")

    # Creer l'action cible
    target_action = bpy.data.actions.new(name=f"{mode}_Animation")
    target_arm.animation_data_create()
    target_arm.animation_data.action = target_action

    # Transfert animation
    print(f"[retarget] Transfert animation : {nb_frames} frames en cours...")
    frames_done = _transfer_animation(
        scene, dm_armature, target_arm,
        dm_to_target, root_dm, root_target,
        frame_start, frame_end
    )
    print(f"[retarget] Transfert termine : {frames_done} frames")

    # Injection mesh OSSEUS si avatar_fbx fourni
    mesh_objects  = []
    mesh_injected = False
    if avatar_fbx:
        print(f"[retarget] Injection mesh OSSEUS : {avatar_fbx}")
        mesh_objects  = _import_osseus_meshes(avatar_fbx, scene)
        mesh_injected = len(mesh_objects) > 0
        if not mesh_injected:
            print("[retarget] AVERTISSEMENT : aucun mesh trouve dans l'avatar OSSEUS")

    # Export FBX : rig cible + meshes si disponibles
    # Definir le range scene pour que bake_anim couvre toute l'animation
    scene.frame_start = frame_start
    scene.frame_end   = frame_end
    scene.frame_set(frame_start)

    bpy.ops.object.select_all(action="DESELECT")
    target_arm.select_set(True)
    for m in mesh_objects:
        m.select_set(True)
    bpy.context.view_layer.objects.active = target_arm

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
        "mesh_present":       mesh_injected,
        "mesh_count":         len(mesh_objects),
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
        description="FERRUS ANIMUS — OUTPUT : Retargeting DeepMotion → DEEPMOTION / R15 / Mixamo"
    )
    parser.add_argument("--fbx-in",     required=True,
                        help="FBX corrige (sortie EXEC)")
    parser.add_argument("--plan",       required=True,
                        help="plan_corrections.json")
    parser.add_argument("--fbx-out",    required=True,
                        help="FBX de sortie")
    parser.add_argument("--mode",       default="R15",
                        choices=["R15", "MIXAMO", "DEEPMOTION"],
                        help="Mode retargeting : R15 (defaut), MIXAMO ou DEEPMOTION")
    parser.add_argument("--avatar-fbx", default=None,
                        help="FBX OSSEUS (requis pour DEEPMOTION, optionnel pour R15/MIXAMO)")

    args = parser.parse_args(argv)

    result = run(
        fbx_in=args.fbx_in,
        plan_path=args.plan,
        fbx_out=args.fbx_out,
        mode=args.mode,
        avatar_fbx=args.avatar_fbx,
    )
    print("\n[retarget] Rapport final :")
    print(json.dumps(result, indent=2, ensure_ascii=False))
