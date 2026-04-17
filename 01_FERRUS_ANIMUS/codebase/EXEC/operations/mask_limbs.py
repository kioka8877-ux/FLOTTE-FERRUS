"""
mask_limbs.py — FERRUS ANIMUS / Compartiment EXEC — Operation 5
Neutralisation des rotations des membres non visibles dans la video originale.

Consomme : plan_corrections.json -> corrections_exec.mask_limbs
  {
    "actif": true,
    "membres_a_masquer": ["main_gauche", "pied_droit"]
  }

Valeurs acceptees dans membres_a_masquer :
    main_gauche   → l_hand_JNT
    main_droite   → r_hand_JNT
    pied_gauche   → l_foot_JNT
    pied_droit    → r_foot_JNT
    jambe_gauche  → l_leg_JNT + l_foot_JNT
    jambe_droite  → r_leg_JNT + r_foot_JNT

Principe :
  Lorsqu'un membre est hors cadre dans la video DeepMotion, les donnees de
  motion capture correspondantes sont inventees par l'algorithme (hallucination
  cinematique). Ce module les neutralise en ramenant toutes les rotations des
  bones concernes a la pose de repos (rotation identite).

  Neutralisation :
    rotation_euler      → tous les keyframes mis a 0.0
    rotation_quaternion → W=1.0, X=Y=Z=0.0 (quaternion identite)

  Les canaux de localisation (location) sont preserves — seule l'orientation
  est annulee. Le membre reste positionne dans l'espace mais ne tourne plus.

Usage standalone (bpy headless) :
    blender --background --python mask_limbs.py -- \\
        --fbx-in  path/to/input.fbx \\
        --plan    path/to/plan_corrections.json \\
        --fbx-out path/to/output.fbx

Usage module (appele par le notebook Colab) :
    from mask_limbs import run
    result = run(fbx_in, plan_path, fbx_out)
"""

import sys
import os
import json
import argparse


# ══ Mapping membres → bones DeepMotion ════════════════════════════════════════

MEMBRE_BONES = {
    "main_gauche":  ["l_hand_JNT"],
    "main_droite":  ["r_hand_JNT"],
    "pied_gauche":  ["l_foot_JNT"],
    "pied_droit":   ["r_foot_JNT"],
    "jambe_gauche": ["l_leg_JNT", "l_foot_JNT"],
    "jambe_droite": ["r_leg_JNT", "r_foot_JNT"],
}

# Valeur neutre par type de canal de rotation :
# rotation_quaternion : W=1 (index 0), X=Y=Z=0 (index 1,2,3)
# rotation_euler      : tous les axes = 0
QUATERNION_NEUTRAL = {0: 1.0, 1: 0.0, 2: 0.0, 3: 0.0}
EULER_NEUTRAL      = 0.0


# ══ Neutralisation d'un bone ══════════════════════════════════════════════════

def _neutral_value_for(data_path: str, array_index: int) -> float | None:
    """
    Retourne la valeur neutre pour un canal FCurve donne.
    Retourne None si le canal n'est pas un canal de rotation (location, scale — ignores).
    """
    if "rotation_quaternion" in data_path:
        return QUATERNION_NEUTRAL.get(array_index, 0.0)
    if "rotation_euler" in data_path:
        return EULER_NEUTRAL
    return None  # location, scale : on ne touche pas


def _neutralize_bone(action, bone_name: str) -> dict:
    """
    Met toutes les rotations du bone indique a la pose de repos (identite).

    Args:
        action    : bpy.types.Action de l'armature
        bone_name : nom exact du bone a neutraliser (ex: "l_hand_JNT")

    Returns:
        dict {canal: nb_keyframes_mis_a_zero}
        ex: {"rotation_euler[0]": 45, "rotation_euler[1]": 45, ...}
    """
    stats = {}

    for fc in action.fcurves:
        if bone_name not in fc.data_path:
            continue

        # Verifier que c'est bien ce bone (pas un bone qui contient le nom en sous-chaine)
        if f'"{bone_name}"' not in fc.data_path:
            continue

        neutral = _neutral_value_for(fc.data_path, fc.array_index)
        if neutral is None:
            continue  # location ou scale : on preserve

        kps = fc.keyframe_points
        if len(kps) == 0:
            continue

        for kp in kps:
            kp.co[1]           = neutral
            kp.handle_left[1]  = neutral
            kp.handle_right[1] = neutral

        fc.update()

        canal_key = f"{fc.data_path.split('.')[-1]}[{fc.array_index}]"
        stats[canal_key] = len(kps)

    return stats


# ══ Chargement du plan ════════════════════════════════════════════════════════

def _load_mask_params(plan_path: str) -> dict | None:
    """
    Charge plan_corrections.json et extrait les params mask_limbs.
    Retourne None si l'operation est desactivee ou si la liste est vide.
    """
    with open(plan_path, "r", encoding="utf-8") as f:
        plan = json.load(f)

    mask = plan.get("corrections_exec", {}).get("mask_limbs", {})

    if not mask.get("actif", False):
        return None

    membres = mask.get("membres_a_masquer", [])
    if not membres:
        print("[mask_limbs] Avertissement : membres_a_masquer vide — aucun masquage effectue")
        return None

    # Filtrer les valeurs inconnues
    membres_valides = [m for m in membres if m in MEMBRE_BONES]
    membres_inconnus = [m for m in membres if m not in MEMBRE_BONES]

    if membres_inconnus:
        print(f"[mask_limbs] Membres inconnus ignores : {membres_inconnus}")
        print(f"[mask_limbs] Valeurs acceptees : {list(MEMBRE_BONES.keys())}")

    if not membres_valides:
        return None

    return {"membres_a_masquer": membres_valides}


# ══ Fonction principale ═══════════════════════════════════════════════════════

def run(fbx_in: str, plan_path: str, fbx_out: str) -> dict:
    """
    Neutralise les rotations des membres hors cadre selon plan_corrections.json.

    Args:
        fbx_in    : chemin vers le FBX source
        plan_path : chemin vers plan_corrections.json
        fbx_out   : chemin vers le FBX de sortie

    Returns:
        dict de rapport {status, membres_masques, bones_traites,
                         keyframes_neutralises, detail, fbx_out}
    """
    import bpy

    # Charger les parametres
    params = _load_mask_params(plan_path)
    if params is None:
        print("[mask_limbs] Operation desactivee — copie directe du FBX")
        import shutil
        shutil.copy2(fbx_in, fbx_out)
        return {"status": "skipped", "raison": "actif=false ou membres_a_masquer vide"}

    membres = params["membres_a_masquer"]

    # Construire la liste de bones a neutraliser (sans doublons)
    bones_a_traiter = []
    for membre in membres:
        for bone in MEMBRE_BONES[membre]:
            if bone not in bones_a_traiter:
                bones_a_traiter.append(bone)

    print(f"[mask_limbs] Membres a masquer ({len(membres)}) : {', '.join(membres)}")
    print(f"[mask_limbs] Bones cibles ({len(bones_a_traiter)}) : {', '.join(bones_a_traiter)}")

    # Charger le FBX
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=os.path.abspath(fbx_in))

    armature = next((o for o in bpy.context.scene.objects if o.type == "ARMATURE"), None)
    if not armature:
        raise RuntimeError(f"[mask_limbs] Aucune armature dans {fbx_in}")

    action = armature.animation_data.action if armature.animation_data else None
    if not action:
        raise RuntimeError("[mask_limbs] Aucune animation dans l'armature")

    # Neutraliser chaque bone
    detail            = {}
    keyframes_totales = 0

    for bone in bones_a_traiter:
        stats = _neutralize_bone(action, bone)
        detail[bone] = stats
        total_bone   = sum(stats.values())
        keyframes_totales += total_bone

        if stats:
            print(f"[mask_limbs] {bone:20s} : {total_bone} keyframes neutralises "
                  f"({len(stats)} canaux)")
        else:
            print(f"[mask_limbs] {bone:20s} : aucune FCurve rotation trouvee — skip")

    if keyframes_totales == 0:
        print("[mask_limbs] Aucun keyframe neutralise — copie directe du FBX")
        import shutil
        shutil.copy2(fbx_in, fbx_out)
        return {
            "status":  "skipped",
            "raison":  "aucune FCurve de rotation trouvee pour les bones cibles",
            "membres": membres,
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

    print(f"[mask_limbs] FBX exporte : {fbx_out}")

    return {
        "status":               "ok",
        "membres_masques":      membres,
        "bones_traites":        bones_a_traiter,
        "keyframes_neutralises": keyframes_totales,
        "detail":               detail,
        "fbx_out":              fbx_out,
    }


# ══ Point d'entree CLI ════════════════════════════════════════════════════════

if __name__ == "__main__":
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
    else:
        argv = []

    parser = argparse.ArgumentParser(
        description="FERRUS ANIMUS — EXEC Op.5 : Masquage membres hors cadre"
    )
    parser.add_argument("--fbx-in",  required=True, help="FBX source")
    parser.add_argument("--plan",    required=True, help="plan_corrections.json")
    parser.add_argument("--fbx-out", required=True, help="FBX sortie")

    args = parser.parse_args(argv)

    result = run(args.fbx_in, args.plan, args.fbx_out)
    print("\n[mask_limbs] Rapport final :")
    print(json.dumps(result, indent=2, ensure_ascii=False))
