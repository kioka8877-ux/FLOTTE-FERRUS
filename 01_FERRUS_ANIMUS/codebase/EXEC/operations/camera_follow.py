"""
camera_follow.py — FERRUS ANIMUS / Compartiment EXEC — Operation 4
Creation et animation d'une camera Blender suivant le personnage principal.

Consomme : plan_corrections.json -> corrections_exec.camera_follow
  {
    "actif": true,
    "cible_person_id": 1,
    "type_suivi": "lock" | "smooth_follow" | "static"
  }

Principe :
  Ce module cree une camera dans la scene Blender et l'anime selon le type_suivi :
    - static       : camera fixe, pointee vers la position moyenne du personnage.
                     Aucun keyframe de deplacement — ideal pour plans poses.
    - lock         : camera verrouilee sur les hanches frame-par-frame, offset fixe.
                     Parfait pour les plans serres ou le personnage reste sur place.
    - smooth_follow: camera suit les hanches avec un lissage gaussien.
                     La camera "retarde" legerement sur les mouvements brusques —
                     rendu cinematique pour les scenes de marche/course.

  Positions evaluees en espace monde Blender (Z-up) via pose_bone.head + matrix_world.
  Rotation calculee via Vector.to_track_quat('-Z', 'Y') — methode native Blender.
  L'animation camera est bakee en keyframes pour une compatibilite FBX maximale.

Usage standalone (bpy headless) :
    blender --background --python camera_follow.py -- \\
        --fbx-in  path/to/input.fbx \\
        --plan    path/to/plan_corrections.json \\
        --fbx-out path/to/output.fbx

Usage module (appele par le notebook Colab) :
    from camera_follow import run
    result = run(fbx_in, plan_path, fbx_out)
"""

import sys
import os
import json
import argparse
from math import exp


# ══ Constantes ════════════════════════════════════════════════════════════════

HIP_BONE        = "hips_JNT"
CAMERA_DISTANCE = 3.0   # unites Blender (~ metres) devant le personnage (axe Y monde)
CAMERA_HEIGHT   = 0.5   # unites au-dessus de hips_JNT.Z (cadrage torse/tete)
TARGET_HEIGHT   = 0.3   # unites au-dessus de hips_JNT.Z pour le point de vise
SMOOTH_KERNEL   = 11    # taille noyau gaussien pour smooth_follow
SMOOTH_SIGMA    = 3.0   # sigma gaussien pour smooth_follow


# ══ Extraction des positions monde de hips_JNT ════════════════════════════════

def _get_hip_world_positions(scene, armature) -> dict:
    """
    Evalue la pose a chaque frame de l'action et retourne les positions monde
    du bone hips_JNT en espace Blender Z-up.

    Utilise scene.frame_set() + matrix_world @ pose_bone.head pour obtenir
    les coordonnees monde correctes, quelle que soit la transformation de l'armature.

    Returns:
        dict {frame_int: (x, y, z)} en espace monde Blender
        Vide si hips_JNT est introuvable ou si aucune animation n'est presente.
    """
    action = armature.animation_data.action if armature.animation_data else None
    if not action:
        return {}

    if HIP_BONE not in armature.pose.bones:
        return {}

    frame_start = int(action.frame_range[0])
    frame_end   = int(action.frame_range[1])

    positions = {}
    for frame in range(frame_start, frame_end + 1):
        scene.frame_set(frame)
        bpy_module = sys.modules.get("bpy")
        if bpy_module:
            bpy_module.context.view_layer.update()

        bone      = armature.pose.bones[HIP_BONE]
        world_pos = armature.matrix_world @ bone.head
        positions[frame] = (world_pos.x, world_pos.y, world_pos.z)

    return positions


def _unpack_positions(hip_positions: dict) -> tuple:
    """Retourne (frames, xs, ys, zs) alignes dans l'ordre croissant des frames."""
    frames = sorted(hip_positions.keys())
    xs = [hip_positions[f][0] for f in frames]
    ys = [hip_positions[f][1] for f in frames]
    zs = [hip_positions[f][2] for f in frames]
    return frames, xs, ys, zs


# ══ Lissage gaussien ══════════════════════════════════════════════════════════

def _gaussian_kernel(size: int, sigma: float) -> list:
    half    = size // 2
    weights = [exp(-((i - half) ** 2) / (2 * sigma ** 2)) for i in range(size)]
    total   = sum(weights)
    return [w / total for w in weights]


def _smooth_list(values: list, kernel: list) -> list:
    """Lissage avec padding miroir aux extremites."""
    half = len(kernel) // 2
    n    = len(values)
    result = []
    for i in range(n):
        s = 0.0
        for j, w in enumerate(kernel):
            idx = i + j - half
            if idx < 0:
                idx = -idx
            elif idx >= n:
                idx = 2 * n - idx - 2
            idx = max(0, min(n - 1, idx))
            s += values[idx] * w
        result.append(s)
    return result


# ══ Strategies de trajectoire camera ══════════════════════════════════════════

def _build_static_trajectory(frames, xs, ys, zs):
    """
    Camera fixe : placee a la position moyenne du personnage + offset.
    Un seul point de vue pour toute la duree — aucun deplacement camera.

    Returns:
        (cam_xs, cam_ys, cam_zs, tgt_xs, tgt_ys, tgt_zs) — listes de longueur len(frames)
    """
    mean_x = sum(xs) / len(xs)
    mean_y = sum(ys) / len(ys)
    mean_z = sum(zs) / len(zs)

    cam_x = mean_x
    cam_y = mean_y - CAMERA_DISTANCE  # en avant du personnage (Y negatif = devant)
    cam_z = mean_z + CAMERA_HEIGHT

    tgt_x = mean_x
    tgt_y = mean_y
    tgt_z = mean_z + TARGET_HEIGHT

    n = len(frames)
    return (
        [cam_x] * n, [cam_y] * n, [cam_z] * n,
        [tgt_x] * n, [tgt_y] * n, [tgt_z] * n,
    )


def _build_lock_trajectory(frames, xs, ys, zs):
    """
    Camera verrou : suit exactement les hanches avec un offset constant.
    Le personnage reste toujours au meme endroit dans le cadre.
    """
    cam_xs = list(xs)
    cam_ys = [y - CAMERA_DISTANCE for y in ys]
    cam_zs = [z + CAMERA_HEIGHT   for z in zs]

    tgt_xs = list(xs)
    tgt_ys = list(ys)
    tgt_zs = [z + TARGET_HEIGHT for z in zs]

    return cam_xs, cam_ys, cam_zs, tgt_xs, tgt_ys, tgt_zs


def _build_smooth_follow_trajectory(frames, xs, ys, zs):
    """
    Camera cinematique : suit les hanches avec inertie gaussienne.
    Les mouvements brusques sont absorbes — la camera "retarde" legerement.
    Les petits tremblements sont effaces.
    """
    kernel = _gaussian_kernel(SMOOTH_KERNEL, SMOOTH_SIGMA)
    xs_s   = _smooth_list(xs, kernel)
    ys_s   = _smooth_list(ys, kernel)
    zs_s   = _smooth_list(zs, kernel)

    cam_xs = list(xs_s)
    cam_ys = [y - CAMERA_DISTANCE for y in ys_s]
    cam_zs = [z + CAMERA_HEIGHT   for z in zs_s]

    # La camera suit les hanches lissees, mais vise les hanches reelles
    # — cree un effet de regard "anticipe" naturel
    tgt_xs = list(xs)
    tgt_ys = list(ys)
    tgt_zs = [z + TARGET_HEIGHT for z in zs]

    return cam_xs, cam_ys, cam_zs, tgt_xs, tgt_ys, tgt_zs


# ══ Creation et animation de la camera ════════════════════════════════════════

def _create_and_animate_camera(scene, frames,
                                cam_xs, cam_ys, cam_zs,
                                tgt_xs, tgt_ys, tgt_zs) -> object:
    """
    Cree une camera Blender, la positionne et la keyframe a chaque frame.
    La rotation est calculee via to_track_quat('-Z', 'Y') — methode Blender native.

    Returns:
        bpy.types.Object camera cree
    """
    import bpy
    from mathutils import Vector

    cam_data = bpy.data.cameras.new(name="FERRUS_Camera")
    cam_obj  = bpy.data.objects.new(name="FERRUS_Camera", object_data=cam_data)
    scene.collection.objects.link(cam_obj)
    scene.camera = cam_obj

    cam_obj.rotation_mode = "XYZ"

    for i, frame in enumerate(frames):
        cam_pos = Vector((cam_xs[i], cam_ys[i], cam_zs[i]))
        tgt_pos = Vector((tgt_xs[i], tgt_ys[i], tgt_zs[i]))

        direction = (tgt_pos - cam_pos)
        if direction.length < 1e-6:
            direction = Vector((0.0, 1.0, 0.0))  # fallback : regarde vers +Y
        else:
            direction.normalize()

        # to_track_quat('-Z', 'Y') : fait pointer l'axe -Z local vers direction,
        # avec Y local comme axe haut — convention camera Blender standard
        rot = direction.to_track_quat("-Z", "Y")
        cam_obj.location       = cam_pos
        cam_obj.rotation_euler = rot.to_euler("XYZ")

        cam_obj.keyframe_insert(data_path="location",       frame=frame)
        cam_obj.keyframe_insert(data_path="rotation_euler", frame=frame)

    return cam_obj


# ══ Chargement du plan ════════════════════════════════════════════════════════

def _load_camera_params(plan_path: str) -> dict | None:
    """
    Charge plan_corrections.json et extrait les params camera_follow.
    Retourne None si l'operation est desactivee.
    """
    with open(plan_path, "r", encoding="utf-8") as f:
        plan = json.load(f)

    cam = plan.get("corrections_exec", {}).get("camera_follow", {})

    if not cam.get("actif", False):
        return None

    type_suivi = cam.get("type_suivi", "smooth_follow")
    if type_suivi not in ("lock", "smooth_follow", "static"):
        print(f"[camera_follow] type_suivi inconnu : '{type_suivi}' — fallback smooth_follow")
        type_suivi = "smooth_follow"

    return {
        "cible_person_id": int(cam.get("cible_person_id", 1)),
        "type_suivi":      type_suivi,
    }


# ══ Fonction principale ═══════════════════════════════════════════════════════

def run(fbx_in: str, plan_path: str, fbx_out: str) -> dict:
    """
    Cree et anime une camera de suivi dans le FBX d'entree selon plan_corrections.json.

    Args:
        fbx_in    : chemin vers le FBX source (animation corrigee)
        plan_path : chemin vers plan_corrections.json
        fbx_out   : chemin vers le FBX de sortie (animation + camera)

    Returns:
        dict de rapport {status, type_suivi, cible_person_id,
                         camera_name, frames_keyframed, fbx_out}
    """
    import bpy

    # Charger les parametres
    params = _load_camera_params(plan_path)
    if params is None:
        print("[camera_follow] Operation desactivee — copie directe du FBX")
        import shutil
        shutil.copy2(fbx_in, fbx_out)
        return {"status": "skipped", "raison": "actif=false"}

    type_suivi      = params["type_suivi"]
    cible_person_id = params["cible_person_id"]

    print(f"[camera_follow] Type de suivi : {type_suivi} | Cible : person_{cible_person_id}")

    # Charger le FBX
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=os.path.abspath(fbx_in))

    armature = next((o for o in bpy.context.scene.objects if o.type == "ARMATURE"), None)
    if not armature:
        raise RuntimeError(f"[camera_follow] Aucune armature dans {fbx_in}")

    if not armature.animation_data or not armature.animation_data.action:
        raise RuntimeError("[camera_follow] Aucune animation dans l'armature")

    if HIP_BONE not in armature.pose.bones:
        raise RuntimeError(f"[camera_follow] Bone '{HIP_BONE}' introuvable dans l'armature")

    scene = bpy.context.scene

    # Extraire les positions monde de hips_JNT frame par frame
    print(f"[camera_follow] Extraction des positions monde de {HIP_BONE}...")
    hip_positions = _get_hip_world_positions(scene, armature)

    if not hip_positions:
        raise RuntimeError(f"[camera_follow] Impossible d'extraire les positions de {HIP_BONE}")

    frames, xs, ys, zs = _unpack_positions(hip_positions)
    print(f"[camera_follow] {len(frames)} frames extraites "
          f"(frame {frames[0]} → {frames[-1]})")

    # Construire la trajectoire camera
    if type_suivi == "static":
        cam_xs, cam_ys, cam_zs, tgt_xs, tgt_ys, tgt_zs = \
            _build_static_trajectory(frames, xs, ys, zs)
    elif type_suivi == "lock":
        cam_xs, cam_ys, cam_zs, tgt_xs, tgt_ys, tgt_zs = \
            _build_lock_trajectory(frames, xs, ys, zs)
    else:  # smooth_follow
        cam_xs, cam_ys, cam_zs, tgt_xs, tgt_ys, tgt_zs = \
            _build_smooth_follow_trajectory(frames, xs, ys, zs)

    # Creer et animer la camera
    cam_obj = _create_and_animate_camera(
        scene, frames,
        cam_xs, cam_ys, cam_zs,
        tgt_xs, tgt_ys, tgt_zs,
    )

    print(f"[camera_follow] Camera '{cam_obj.name}' creee | "
          f"{len(frames)} keyframes | type={type_suivi}")

    # Remettre la scene sur la premiere frame avant export
    scene.frame_set(frames[0])

    # Exporter le FBX (armature + camera)
    os.makedirs(os.path.dirname(os.path.abspath(fbx_out)), exist_ok=True)
    bpy.ops.export_scene.fbx(
        filepath=os.path.abspath(fbx_out),
        use_selection=False,
        apply_unit_scale=True,
        bake_anim=True,
        bake_anim_use_all_bones=True,
        bake_anim_force_startend_keying=True,
        add_leaf_bones=False,
    )

    print(f"[camera_follow] FBX exporte avec camera : {fbx_out}")

    return {
        "status":           "ok",
        "type_suivi":       type_suivi,
        "cible_person_id":  cible_person_id,
        "camera_name":      cam_obj.name,
        "frames_keyframed": len(frames),
        "fbx_out":          fbx_out,
    }


# ══ Point d'entree CLI ════════════════════════════════════════════════════════

if __name__ == "__main__":
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
    else:
        argv = []

    parser = argparse.ArgumentParser(
        description="FERRUS ANIMUS — EXEC Op.4 : Camera follow"
    )
    parser.add_argument("--fbx-in",  required=True, help="FBX source")
    parser.add_argument("--plan",    required=True, help="plan_corrections.json")
    parser.add_argument("--fbx-out", required=True, help="FBX sortie")

    args = parser.parse_args(argv)

    result = run(args.fbx_in, args.plan, args.fbx_out)
    print("\n[camera_follow] Rapport final :")
    print(json.dumps(result, indent=2, ensure_ascii=False))
