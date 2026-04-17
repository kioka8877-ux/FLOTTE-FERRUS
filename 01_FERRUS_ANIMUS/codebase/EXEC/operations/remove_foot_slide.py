"""
remove_foot_slide.py — FERRUS ANIMUS / Compartiment EXEC — Operation 3
Correction du glissement des pieds (foot slide) pendant les phases de contact au sol.

Consomme : plan_corrections.json -> corrections_exec.remove_foot_slide
  {
    "enabled": true,
    "seuil_cm": 5.0
  }

Principe :
  DeepMotion produit parfois un glissement lateral des pieds lorsqu'ils sont
  au contact du sol. Ce module detecte les phases de contact (Y < seuil) sur
  les bones l_foot_JNT et r_foot_JNT, puis gele les axes horizontaux (X et Z)
  a la valeur moyenne de chaque phase, eliminant ainsi le glissement apparent.

  Coordonnees : convention Y-up (FBX DeepMotion)
    array_index 0 = X  (lateral)
    array_index 1 = Y  (vertical — utilise pour detecter le contact)
    array_index 2 = Z  (profondeur)

Usage standalone (bpy headless) :
    blender --background --python remove_foot_slide.py -- \\
        --fbx-in  path/to/input.fbx \\
        --plan    path/to/plan_corrections.json \\
        --fbx-out path/to/output.fbx

Usage module (appele par le notebook Colab) :
    from remove_foot_slide import run
    result = run(fbx_in, plan_path, fbx_out)
"""

import sys
import os
import json
import argparse


# ══ Constantes ════════════════════════════════════════════════════════════════

FOOT_BONES    = ["l_foot_JNT", "r_foot_JNT"]
AXIS_VERTICAL = 1   # array_index Y — detecte le contact au sol
AXIS_HORIZ    = [0, 2]  # array_index X et Z — axes a geler


# ══ Detection des phases de contact ══════════════════════════════════════════

def _find_contact_phases(values_y: list, seuil: float) -> list:
    """
    Detecte les phases de contact au sol a partir des valeurs Y d'un pied.
    Une phase est une sequence continue de keyframes ou Y < seuil.

    Args:
        values_y : liste de valeurs Y (une valeur par keyframe, dans l'ordre)
        seuil    : valeur Y en unites Blender en-dessous de laquelle le pied est plante

    Returns:
        liste de tuples (start_idx, end_idx) — indices inclusifs dans values_y
    """
    phases = []
    in_contact = False
    start = 0

    for i, y in enumerate(values_y):
        if y < seuil:
            if not in_contact:
                start = i
                in_contact = True
        else:
            if in_contact:
                phases.append((start, i - 1))
                in_contact = False

    if in_contact:
        phases.append((start, len(values_y) - 1))

    return phases


# ══ Gel des axes horizontaux sur une phase ════════════════════════════════════

def _freeze_axis(fc, phases: list) -> int:
    """
    Gele les valeurs d'une FCurve (X ou Z) sur les phases de contact.
    Pour chaque phase, remplace toutes les valeurs par la moyenne de la phase.
    La moyenne garantit la stabilite numerique meme si le premier frame est bruit.

    Args:
        fc     : bpy.types.FCurve a modifier
        phases : liste de (start_idx, end_idx) issue de _find_contact_phases

    Returns:
        nombre total de keyframes modifies
    """
    kps = fc.keyframe_points
    n   = len(kps)

    if n == 0 or not phases:
        return 0

    total_modifies = 0

    for (start, end) in phases:
        s = max(0, start)
        e = min(n - 1, end)

        if s > e:
            continue

        # Valeur cible = moyenne de la phase
        values_phase = [kps[i].co[1] for i in range(s, e + 1)]
        moyenne = sum(values_phase) / len(values_phase)

        for i in range(s, e + 1):
            kps[i].co[1]           = moyenne
            kps[i].handle_left[1]  = moyenne
            kps[i].handle_right[1] = moyenne

        total_modifies += (e - s + 1)

    fc.update()
    return total_modifies


# ══ Traitement d'un pied ══════════════════════════════════════════════════════

def _process_foot(action, bone_name: str, seuil: float) -> dict:
    """
    Detecte les phases de contact et gele X/Z pour un pied donne.

    Args:
        action    : bpy.types.Action de l'armature
        bone_name : nom du bone (ex: "l_foot_JNT")
        seuil     : seuil de contact en unites Blender

    Returns:
        dict {phases_detectees, keyframes_modifies_x, keyframes_modifies_z}
    """
    vide = {"phases_detectees": 0, "keyframes_modifies_x": 0, "keyframes_modifies_z": 0}

    # FCurve Y — sert uniquement a la detection du contact
    fc_y = next(
        (fc for fc in action.fcurves
         if bone_name in fc.data_path
         and "location" in fc.data_path
         and fc.array_index == AXIS_VERTICAL),
        None
    )

    if fc_y is None or len(fc_y.keyframe_points) < 2:
        return vide

    values_y = [kp.co[1] for kp in fc_y.keyframe_points]
    phases   = _find_contact_phases(values_y, seuil)

    if not phases:
        return vide

    stats = {"phases_detectees": len(phases), "keyframes_modifies_x": 0, "keyframes_modifies_z": 0}

    # Geler X et Z sur chaque phase de contact
    for axis_idx, stat_key in [(0, "keyframes_modifies_x"), (2, "keyframes_modifies_z")]:
        fc_axis = next(
            (fc for fc in action.fcurves
             if bone_name in fc.data_path
             and "location" in fc.data_path
             and fc.array_index == axis_idx),
            None
        )
        if fc_axis:
            stats[stat_key] = _freeze_axis(fc_axis, phases)

    return stats


# ══ Chargement du plan ════════════════════════════════════════════════════════

def _load_foot_slide_params(plan_path: str) -> dict | None:
    """
    Charge plan_corrections.json et extrait les params remove_foot_slide.
    Retourne None si l'operation est desactivee ou absente.
    """
    with open(plan_path, "r", encoding="utf-8") as f:
        plan = json.load(f)

    foot = plan.get("corrections_exec", {}).get("remove_foot_slide", {})

    if not foot.get("enabled", False):
        return None

    return {
        "seuil_cm": float(foot.get("seuil_cm", 5.0)),
    }


# ══ Fonction principale ═══════════════════════════════════════════════════════

def run(fbx_in: str, plan_path: str, fbx_out: str) -> dict:
    """
    Corrige le glissement des pieds sur le FBX d'entree selon plan_corrections.json.

    Args:
        fbx_in    : chemin vers le FBX source
        plan_path : chemin vers plan_corrections.json
        fbx_out   : chemin vers le FBX de sortie

    Returns:
        dict de rapport {status, seuil_cm, pieds_traites, phases_totales,
                         keyframes_modifies, detail_pieds, fbx_out}
    """
    import bpy

    # Charger les parametres
    params = _load_foot_slide_params(plan_path)
    if params is None:
        print("[remove_foot_slide] Operation desactivee — copie directe du FBX")
        import shutil
        shutil.copy2(fbx_in, fbx_out)
        return {"status": "skipped", "raison": "enabled=false"}

    seuil_cm = params["seuil_cm"]
    seuil    = seuil_cm / 100.0  # cm -> unites Blender (1 unite ~ 1 m)

    print(f"[remove_foot_slide] Seuil de contact : {seuil_cm} cm ({seuil:.4f} unites Blender)")

    # Charger le FBX
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=os.path.abspath(fbx_in))

    armature = next((o for o in bpy.context.scene.objects if o.type == "ARMATURE"), None)
    if not armature:
        raise RuntimeError(f"[remove_foot_slide] Aucune armature dans {fbx_in}")

    action = armature.animation_data.action if armature.animation_data else None
    if not action:
        raise RuntimeError("[remove_foot_slide] Aucune animation dans l'armature")

    # Traiter chaque pied
    rapport_pieds     = {}
    phases_totales    = 0
    keyframes_totales = 0

    for bone in FOOT_BONES:
        stats = _process_foot(action, bone, seuil)
        rapport_pieds[bone] = stats
        phases_totales    += stats["phases_detectees"]
        keyframes_totales += stats["keyframes_modifies_x"] + stats["keyframes_modifies_z"]

        print(
            f"[remove_foot_slide] {bone:20s} : "
            f"{stats['phases_detectees']} phases | "
            f"X:{stats['keyframes_modifies_x']} kf | "
            f"Z:{stats['keyframes_modifies_z']} kf"
        )

    if phases_totales == 0:
        print("[remove_foot_slide] Aucune phase de contact detectee — copie directe du FBX")
        import shutil
        shutil.copy2(fbx_in, fbx_out)
        return {
            "status":   "skipped",
            "raison":   "aucune phase de contact detectee",
            "seuil_cm": seuil_cm,
        }

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

    print(f"[remove_foot_slide] FBX exporte : {fbx_out}")

    return {
        "status":             "ok",
        "seuil_cm":           seuil_cm,
        "pieds_traites":      list(rapport_pieds.keys()),
        "phases_totales":     phases_totales,
        "keyframes_modifies": keyframes_totales,
        "detail_pieds":       rapport_pieds,
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
        description="FERRUS ANIMUS — EXEC Op.3 : Suppression foot slide"
    )
    parser.add_argument("--fbx-in",  required=True, help="FBX source")
    parser.add_argument("--plan",    required=True, help="plan_corrections.json")
    parser.add_argument("--fbx-out", required=True, help="FBX sortie")

    args = parser.parse_args(argv)

    result = run(args.fbx_in, args.plan, args.fbx_out)
    print("\n[remove_foot_slide] Rapport final :")
    print(json.dumps(result, indent=2, ensure_ascii=False))
