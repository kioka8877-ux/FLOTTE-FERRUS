"""
stabilize_hips.py — FERRUS ANIMUS / Compartiment EXEC — Operation 2
Correction de la derive verticale progressive des hanches (hips_JNT).

Consomme : plan_corrections.json -> corrections_exec.stabilize_hips
  {
    "enabled": true,
    "correction_verticale_cm": 5.2,
    "direction": "descente_progressive"
  }

Principe :
  DeepMotion produit parfois une derive verticale lineaire sur hips_JNT.location.Y :
  le personnage s'enfonce lentement dans le sol (descente) ou flotte vers le haut (montee).
  Ce module calcule la tendance lineaire de l'axe Y et l'annule progressivement,
  en preservant la position de depart du premier frame.

Usage standalone (bpy headless) :
    blender --background --python stabilize_hips.py -- \\
        --fbx-in  path/to/input.fbx \\
        --plan    path/to/plan_corrections.json \\
        --fbx-out path/to/output.fbx

Usage module :
    from stabilize_hips import run
    result = run(fbx_in, plan_path, fbx_out)
"""

import sys
import os
import json
import argparse


# ══ Constantes ════════════════════════════════════════════════════════════════

HIP_BONE      = "hips_JNT"
AXIS_VERTICAL = 1  # array_index 1 = Y dans les FBX DeepMotion (Y-up convention)


# ══ Detection et correction de derive ════════════════════════════════════════

def _linear_trend(values: list) -> list:
    """
    Calcule la tendance lineaire d'une serie de valeurs (moindres carres).
    Retourne une liste de la meme taille representant la tendance.
    """
    n = len(values)
    if n < 2:
        return [0.0] * n

    indices = list(range(n))
    mean_x  = sum(indices) / n
    mean_y  = sum(values)  / n
    mean_xy = sum(i * v for i, v in zip(indices, values)) / n
    mean_x2 = sum(i * i for i in indices) / n

    denom = mean_x2 - mean_x ** 2
    if abs(denom) < 1e-10:
        return [mean_y] * n

    a = (mean_xy - mean_x * mean_y) / denom
    b = mean_y - a * mean_x

    return [a * i + b for i in indices]


def _detect_drift(fc_y) -> dict:
    """
    Analyse la FCurve Y des hanches et calcule l'amplitude de la derive.

    Returns:
        dict avec delta_total, delta_cm, direction, trend, frame_times, values
    """
    kps = fc_y.keyframe_points
    if len(kps) < 2:
        return {"delta_total": 0.0, "delta_cm": 0.0, "direction": "stable",
                "trend": [], "frame_times": [], "values": []}

    frame_times = [kp.co[0] for kp in kps]
    values      = [kp.co[1] for kp in kps]
    trend       = _linear_trend(values)

    delta    = trend[-1] - trend[0]
    delta_cm = abs(delta) * 100  # 1 unite Blender ~ 1 m ~ 100 cm

    if abs(delta) < 0.001:
        direction = "stable"
    elif delta < 0:
        direction = "descente_progressive"
    else:
        direction = "montee_progressive"

    return {
        "delta_total": delta,
        "delta_cm":    round(delta_cm, 2),
        "direction":   direction,
        "trend":       trend,
        "frame_times": frame_times,
        "values":      values,
    }


def _apply_correction(fc_y, trend: list) -> int:
    """
    Annule la derive en soustrayant la tendance lineaire de chaque keyframe.
    Le premier frame reste intact, les suivants sont ramenes progressivement.

    Returns: nombre de keyframes modifies
    """
    kps = fc_y.keyframe_points
    n   = len(kps)
    if n < 2 or not trend:
        return 0

    baseline    = trend[0]
    corrections = [-(t - baseline) for t in trend]

    for i, kp in enumerate(kps):
        kp.co[1]           += corrections[i]
        kp.handle_left[1]  += corrections[i]
        kp.handle_right[1] += corrections[i]

    fc_y.update()
    return n


# ══ Chargement du plan ════════════════════════════════════════════════════════

def _load_hips_params(plan_path: str) -> dict | None:
    """
    Charge plan_corrections.json et extrait les params stabilize_hips.
    Retourne None si l'operation est desactivee.
    """
    with open(plan_path, "r", encoding="utf-8") as f:
        plan = json.load(f)

    hips = plan.get("corrections_exec", {}).get("stabilize_hips", {})

    if not hips.get("enabled", False):
        return None

    return {
        "correction_verticale_cm": float(hips.get("correction_verticale_cm", 0.0)),
        "direction":               hips.get("direction", "descente_progressive"),
    }


# ══ Fonction principale ═══════════════════════════════════════════════════════

def run(fbx_in: str, plan_path: str, fbx_out: str) -> dict:
    """
    Corrige la derive verticale des hanches sur le FBX d'entree.

    Args:
        fbx_in    : chemin vers le FBX source
        plan_path : chemin vers plan_corrections.json
        fbx_out   : chemin vers le FBX de sortie

    Returns:
        dict de rapport {status, direction, delta_detecte_cm, keyframes_corriges}
    """
    import bpy

    # Charger les parametres
    params = _load_hips_params(plan_path)
    if params is None:
        print("[stabilize_hips] Operation desactivee — copie directe du FBX")
        import shutil
        shutil.copy2(fbx_in, fbx_out)
        return {"status": "skipped", "raison": "enabled=false"}

    correction_cm  = params["correction_verticale_cm"]
    direction_plan = params["direction"]

    print(f"[stabilize_hips] Correction attendue : {correction_cm} cm | direction : {direction_plan}")

    # Charger le FBX
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=os.path.abspath(fbx_in))

    armature = next((o for o in bpy.context.scene.objects if o.type == "ARMATURE"), None)
    if not armature:
        raise RuntimeError(f"[stabilize_hips] Aucune armature dans {fbx_in}")

    action = armature.animation_data.action if armature.animation_data else None
    if not action:
        raise RuntimeError("[stabilize_hips] Aucune animation dans l'armature")

    # Trouver la FCurve Y des hanches
    fc_y = next(
        (fc for fc in action.fcurves
         if HIP_BONE in fc.data_path
         and "location" in fc.data_path
         and fc.array_index == AXIS_VERTICAL),
        None
    )

    if fc_y is None:
        print(f"[stabilize_hips] FCurve Y de {HIP_BONE} introuvable — skip")
        import shutil
        shutil.copy2(fbx_in, fbx_out)
        return {"status": "skipped", "raison": f"FCurve Y de {HIP_BONE} introuvable"}

    # Analyser la derive reelle dans les donnees
    drift = _detect_drift(fc_y)
    print(f"[stabilize_hips] Derive detectee dans les donnees : {drift['delta_cm']} cm | {drift['direction']}")

    if drift["direction"] == "stable":
        print("[stabilize_hips] Derive stable — copie directe du FBX")
        import shutil
        shutil.copy2(fbx_in, fbx_out)
        return {
            "status":           "skipped",
            "raison":           "derive stable dans les donnees",
            "delta_detecte_cm": drift["delta_cm"],
        }

    # Appliquer la correction par detrending lineaire
    nb_corriges = _apply_correction(fc_y, drift["trend"])
    print(f"[stabilize_hips] {nb_corriges} keyframes corriges sur {HIP_BONE}.location.Y")

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

    print(f"[stabilize_hips] FBX exporte : {fbx_out}")

    return {
        "status":             "ok",
        "direction":          drift["direction"],
        "delta_detecte_cm":   drift["delta_cm"],
        "correction_cm":      correction_cm,
        "keyframes_corriges": nb_corriges,
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
        description="FERRUS ANIMUS — EXEC Op.2 : Stabilisation hanches"
    )
    parser.add_argument("--fbx-in",  required=True, help="FBX source")
    parser.add_argument("--plan",    required=True, help="plan_corrections.json")
    parser.add_argument("--fbx-out", required=True, help="FBX sortie")

    args = parser.parse_args(argv)

    result = run(args.fbx_in, args.plan, args.fbx_out)
    print("\n[stabilize_hips] Rapport final :")
    print(json.dumps(result, indent=2, ensure_ascii=False))
