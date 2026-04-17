"""
smooth_fcurves.py — FERRUS ANIMUS / Compartiment EXEC — Operation 1
Lissage des FCurves d'animation pour supprimer le jitter.

Consomme : plan_corrections.json -> corrections_exec.smooth_fcurves
  {
    "enabled": true,
    "bones_cibles": ["l_hand_JNT", "r_hand_JNT", "head_JNT"],
    "intensite": 0.5
  }

Usage standalone (bpy headless) :
    blender --background --python smooth_fcurves.py -- \\
        --fbx-in  path/to/input.fbx \\
        --plan    path/to/plan_corrections.json \\
        --fbx-out path/to/output.fbx

Usage module (appele par le notebook Colab) :
    from smooth_fcurves import run
    result = run(fbx_in, plan_path, fbx_out)
"""

import sys
import os
import json
import argparse
import math
from math import exp


# ══ Noyau gaussien ═══════════════════════════════════════════════════════════

def _gaussian_kernel(size: int, sigma: float) -> list:
    """Cree un noyau gaussien normalise de taille impaire `size`."""
    half = size // 2
    weights = [exp(-((i - half) ** 2) / (2 * sigma ** 2)) for i in range(size)]
    total = sum(weights)
    return [w / total for w in weights]


def _intensite_to_kernel(intensite: float):
    """
    Convertit intensite (0.0-1.0) en (kernel_size, sigma).
    0.0-0.2  -> taille 3,  sigma 0.8  (lissage leger)
    0.2-0.4  -> taille 5,  sigma 1.0
    0.4-0.6  -> taille 7,  sigma 1.5  (lissage moyen)
    0.6-0.8  -> taille 9,  sigma 2.0
    0.8-1.0  -> taille 11, sigma 2.5  (lissage fort)
    """
    intensite = max(0.0, min(1.0, intensite))
    idx = min(int(intensite * 5), 4)
    params = [
        (3,  0.8),
        (5,  1.0),
        (7,  1.5),
        (9,  2.0),
        (11, 2.5),
    ]
    return params[idx]


# ══ Euler unwrapping ══════════════════════════════════════════════════════════

def _unwrap_euler(values: list) -> list:
    """
    Corrige les discontinuites 2π dans une sequence d'angles Euler.
    Chaque saut > π est compense par ±2π pour rendre la sequence continue.
    Prerequis au lissage gaussien quand gimbal_lock_risque=True.
    """
    if len(values) < 2:
        return list(values)

    TWO_PI   = 2.0 * math.pi
    unwrapped = [values[0]]

    for i in range(1, len(values)):
        diff = values[i] - unwrapped[-1]
        # Ramener diff dans [-π, π]
        while diff >  math.pi:
            diff -= TWO_PI
        while diff < -math.pi:
            diff += TWO_PI
        unwrapped.append(unwrapped[-1] + diff)

    return unwrapped


# ══ Lissage FCurve ════════════════════════════════════════════════════════════

def _smooth_values(values: list, kernel: list) -> list:
    """
    Applique le noyau gaussien sur une liste de valeurs.
    Padding miroir aux extremites pour eviter les artefacts.
    """
    half = len(kernel) // 2
    n = len(values)
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


def _smooth_fcurve(fc, kernel: list, unwrap: bool = False) -> int:
    """
    Lisse les valeurs d'une FCurve avec le noyau fourni.
    Si unwrap=True et que la FCurve est de type rotation_euler,
    applique un Euler unwrapping avant le lissage pour eviter
    les artefacts de gimbal lock.
    Retourne le nombre de keyframes modifies.
    """
    kps = fc.keyframe_points
    if len(kps) < 3:
        return 0

    values = [kp.co[1] for kp in kps]

    # Euler unwrapping sur les courbes de rotation uniquement
    if unwrap and 'rotation_euler' in fc.data_path:
        values = _unwrap_euler(values)

    smoothed = _smooth_values(values, kernel)

    for kp, new_val in zip(kps, smoothed):
        kp.co[1] = new_val
        # Mise a jour des handles pour coherence visuelle
        kp.handle_left[1]  = new_val
        kp.handle_right[1] = new_val

    fc.update()
    return len(kps)


# ══ Application sur l'armature ════════════════════════════════════════════════

def _apply_smoothing(armature, bones_cibles: list, kernel: list, unwrap: bool = False) -> dict:
    """
    Applique le lissage gaussien sur toutes les FCurves des bones cibles.
    Si unwrap=True, applique un Euler unwrapping avant lissage sur les
    courbes rotation_euler pour corriger les artefacts de gimbal lock.

    Returns:
        dict avec les stats par bone : {bone_name: nb_keyframes_modifies}
    """
    action = armature.animation_data.action if armature.animation_data else None
    if not action:
        return {}

    stats = {}

    for fc in action.fcurves:
        # Identifier le bone concerne par cette FCurve
        # Format data_path : 'pose.bones["bone_name"].rotation_euler'
        data_path = fc.data_path
        if '"' not in data_path:
            continue

        bone_name = data_path.split('"')[1]
        if bone_name not in bones_cibles:
            continue

        nb = _smooth_fcurve(fc, kernel, unwrap=unwrap)
        if nb > 0:
            stats[bone_name] = stats.get(bone_name, 0) + nb

    return stats


# ══ Chargement du plan ════════════════════════════════════════════════════════

def _load_smooth_params(plan_path: str) -> dict | None:
    """
    Charge plan_corrections.json et extrait les params smooth_fcurves.
    Retourne None si l'operation est desactivee ou absente.
    """
    with open(plan_path, "r", encoding="utf-8") as f:
        plan = json.load(f)

    smooth = plan.get("corrections_exec", {}).get("smooth_fcurves", {})

    if not smooth.get("enabled", False):
        return None

    bones   = smooth.get("bones_cibles", [])
    intensite = float(smooth.get("intensite", 0.5))
    gimbal  = bool(smooth.get("gimbal_lock_risque", False))

    if not bones:
        print("[smooth_fcurves] Avertissement : bones_cibles vide — aucun lissage applique")
        return None

    return {"bones_cibles": bones, "intensite": intensite, "gimbal_lock_risque": gimbal}


# ══ Fonction principale ═══════════════════════════════════════════════════════

def run(fbx_in: str, plan_path: str, fbx_out: str) -> dict:
    """
    Execute le lissage FCurves sur le FBX d'entree selon plan_corrections.json.

    Args:
        fbx_in    : chemin vers le FBX source
        plan_path : chemin vers plan_corrections.json
        fbx_out   : chemin vers le FBX de sortie

    Returns:
        dict de rapport {status, bones_lisses, keyframes_modifies, kernel_size}
    """
    import bpy

    # Charger les parametres
    params = _load_smooth_params(plan_path)
    if params is None:
        print("[smooth_fcurves] Operation desactivee — copie directe du FBX")
        import shutil
        shutil.copy2(fbx_in, fbx_out)
        return {"status": "skipped", "raison": "enabled=false ou bones_cibles vide"}

    bones_cibles = params["bones_cibles"]
    intensite    = params["intensite"]
    gimbal       = params["gimbal_lock_risque"]
    kernel_size, sigma = _intensite_to_kernel(intensite)
    kernel = _gaussian_kernel(kernel_size, sigma)

    print(f"[smooth_fcurves] Parametres : intensite={intensite} | kernel={kernel_size} | sigma={sigma} | euler_unwrap={gimbal}")
    print(f"[smooth_fcurves] Bones cibles ({len(bones_cibles)}) : {', '.join(bones_cibles)}")

    # Charger le FBX
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=os.path.abspath(fbx_in))

    armature = next((o for o in bpy.context.scene.objects if o.type == "ARMATURE"), None)
    if not armature:
        raise RuntimeError(f"[smooth_fcurves] Aucune armature dans {fbx_in}")

    # Appliquer le lissage (avec unwrapping si gimbal_lock_risque)
    stats = _apply_smoothing(armature, bones_cibles, kernel, unwrap=gimbal)

    total_kf = sum(stats.values())
    print(f"[smooth_fcurves] Lissage applique sur {len(stats)} bones | {total_kf} keyframes modifies")
    for bone, nb in sorted(stats.items()):
        print(f"  {bone:30s} : {nb} keyframes")

    # Exporter le FBX
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

    print(f"[smooth_fcurves] FBX exporte : {fbx_out}")

    return {
        "status": "ok",
        "bones_lisses": list(stats.keys()),
        "keyframes_modifies": total_kf,
        "kernel_size": kernel_size,
        "sigma": sigma,
        "intensite": intensite,
        "euler_unwrap_applique": gimbal,
        "fbx_out": fbx_out,
    }


# ══ Point d'entree CLI ════════════════════════════════════════════════════════

if __name__ == "__main__":
    # Separer les args bpy des args du script (bpy passe ses propres args avant --)
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
    else:
        argv = []

    parser = argparse.ArgumentParser(
        description="FERRUS ANIMUS — EXEC Op.1 : Lissage FCurves"
    )
    parser.add_argument("--fbx-in",  required=True, help="FBX source")
    parser.add_argument("--plan",    required=True, help="plan_corrections.json")
    parser.add_argument("--fbx-out", required=True, help="FBX sortie")

    args = parser.parse_args(argv)

    result = run(args.fbx_in, args.plan, args.fbx_out)
    print("\n[smooth_fcurves] Rapport final :")
    print(json.dumps(result, indent=2, ensure_ascii=False))
