"""
mask_limbs.py — FERRUS ANIMUS / Compartiment EXEC — Operation 5
Freeze per-frame des membres hors cadre sur les plages de frames definies.

Consomme : plan_corrections.json -> corrections_exec.mask_limbs
  {
    "actif": true,
    "membres_a_masquer": [
      {"membre": "main_gauche", "frame_debut": 80, "frame_fin": 145},
      {"membre": "pied_droit",  "frame_debut": 0,  "frame_fin": 30}
    ]
  }

Valeurs acceptees pour "membre" :
    main_gauche   → l_hand_JNT
    main_droite   → r_hand_JNT
    pied_gauche   → l_foot_JNT
    pied_droit    → r_foot_JNT
    jambe_gauche  → l_leg_JNT + l_foot_JNT
    jambe_droite  → r_leg_JNT + r_foot_JNT

Principe — Freeze per-frame (Option A) :
  Lorsqu'un membre sort du cadre sur une plage [frame_debut, frame_fin],
  les donnees MoCap DeepMotion sont hallucinées par l'algorithme.
  Ce module les remplace par la derniere valeur connue AVANT frame_debut,
  ce que ferait un animateur a la main (freeze).

  Comportement :
    frames < frame_debut  → animation normale (inchangee)
    frames [debut, fin]   → valeur constante = valeur au frame (debut - 1)
    frames > frame_fin    → animation normale qui reprend (via interpolation LINEAR)

  Seules les rotations sont traitees. Les canaux location/scale sont preserves.

Usage standalone (bpy headless) :
    blender --background --python mask_limbs.py -- \
        --fbx-in  path/to/input.fbx \
        --plan    path/to/plan_corrections.json \
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


# ══ Helpers FCurve ════════════════════════════════════════════════════════════

def _is_rotation_channel(data_path: str) -> bool:
    """Retourne True si le canal est une rotation (quaternion ou euler)."""
    return "rotation_quaternion" in data_path or "rotation_euler" in data_path


def _freeze_bone_range(action, bone_name: str, frame_debut: int, frame_fin: int) -> dict:
    """
    Freeze un bone sur la plage [frame_debut, frame_fin].

    Principe :
      1. Evalue la valeur freeze = valeur du canal au frame (frame_debut - 1)
         Si frame_debut == 0, on prend la valeur au frame 0 (T-pose/repos).
      2. Pour tous les keyframes dans [frame_debut, frame_fin] :
         - co[1] = freeze_val
         - handles = freeze_val (plat, pas de derive)
         - interpolation = LINEAR (transition propre vers le prochain keyframe reel)
      3. Le keyframe apres frame_fin reprend la valeur MoCap normale → fondu propre.

    Args:
        action      : bpy.types.Action de l'armature
        bone_name   : nom exact du bone (ex: "l_hand_JNT")
        frame_debut : premiere frame a freezer (incluse)
        frame_fin   : derniere frame a freezer (incluse)

    Returns:
        dict {canal: nb_keyframes_freezes}
    """
    stats = {}
    freeze_eval_frame = max(0, frame_debut - 1)

    for fc in action.fcurves:
        # Verifier que c'est exactement ce bone (pas un sous-string)
        if f'"{bone_name}"' not in fc.data_path:
            continue
        # Traiter uniquement les canaux de rotation
        if not _is_rotation_channel(fc.data_path):
            continue

        kps = fc.keyframe_points
        if not kps:
            continue

        # Evaluer la valeur a conserver (derniere position connue)
        freeze_val = fc.evaluate(freeze_eval_frame)

        count = 0
        for kp in kps:
            frame = kp.co[0]
            if frame_debut <= frame <= frame_fin:
                kp.co[1]           = freeze_val
                kp.handle_left[1]  = freeze_val
                kp.handle_right[1] = freeze_val
                kp.interpolation   = "LINEAR"
                count += 1

        if count:
            fc.update()
            canal_key = f"{fc.data_path.split('.')[-1]}[{fc.array_index}]"
            stats[canal_key] = count

    return stats


# ══ Chargement du plan ════════════════════════════════════════════════════════

def _load_mask_params(plan_path: str) -> list | None:
    """
    Charge plan_corrections.json et extrait les params mask_limbs.

    Retourne une liste de dicts :
      [{"membre": "main_gauche", "frame_debut": 80, "frame_fin": 145}, ...]

    Retourne None si l'operation est desactivee ou si la liste est vide.
    Supporte le format legacy (liste de strings) pour retrocompatibilite :
      ["main_gauche", "pied_droit"] → traitement sur toute la duree de l'animation.
    """
    with open(plan_path, "r", encoding="utf-8") as f:
        plan = json.load(f)

    mask = plan.get("corrections_exec", {}).get("mask_limbs", {})

    if not mask.get("actif", False):
        return None

    raw = mask.get("membres_a_masquer", [])
    if not raw:
        print("[mask_limbs] Avertissement : membres_a_masquer vide — aucun masquage effectue")
        return None

    # Detecter le format
    if raw and isinstance(raw[0], str):
        # Format legacy : liste de strings → freeze sur toute la duree (frame 0 → frame 99999)
        print("[mask_limbs] Format legacy detecte (liste de strings) — freeze sur toute la duree")
        entries = [{"membre": m, "frame_debut": 0, "frame_fin": 99999} for m in raw]
    else:
        # Format v2 : liste d'objets {membre, frame_debut, frame_fin}
        entries = raw

    # Valider et filtrer
    valides = []
    for entry in entries:
        membre = entry.get("membre", "")
        if membre not in MEMBRE_BONES:
            print(f"[mask_limbs] Membre inconnu ignore : '{membre}' "
                  f"(valeurs acceptees : {list(MEMBRE_BONES.keys())})")
            continue
        frame_debut = int(entry.get("frame_debut", 0))
        frame_fin   = int(entry.get("frame_fin", 99999))
        if frame_debut > frame_fin:
            print(f"[mask_limbs] Plage invalide pour '{membre}' : "
                  f"frame_debut ({frame_debut}) > frame_fin ({frame_fin}) — ignore")
            continue
        valides.append({"membre": membre, "frame_debut": frame_debut, "frame_fin": frame_fin})

    return valides if valides else None


# ══ Fonction principale ═══════════════════════════════════════════════════════

def run(fbx_in: str, plan_path: str, fbx_out: str) -> dict:
    """
    Freeze les membres hors cadre sur leurs plages de frames respectives.

    Args:
        fbx_in    : chemin vers le FBX source
        plan_path : chemin vers plan_corrections.json
        fbx_out   : chemin vers le FBX de sortie

    Returns:
        dict de rapport {status, operations, keyframes_freezes, detail, fbx_out}
    """
    import bpy

    # Charger les parametres
    params = _load_mask_params(plan_path)
    if params is None:
        print("[mask_limbs] Operation desactivee — copie directe du FBX")
        import shutil
        shutil.copy2(fbx_in, fbx_out)
        return {"status": "skipped", "raison": "actif=false ou membres_a_masquer vide"}

    # Charger le FBX
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=os.path.abspath(fbx_in))

    armature = next((o for o in bpy.context.scene.objects if o.type == "ARMATURE"), None)
    if not armature:
        raise RuntimeError(f"[mask_limbs] Aucune armature dans {fbx_in}")

    action = armature.animation_data.action if armature.animation_data else None
    if not action:
        raise RuntimeError("[mask_limbs] Aucune animation dans l'armature")

    # Resume des operations planifiees
    print(f"[mask_limbs] {len(params)} plage(s) de freeze a appliquer :")
    for entry in params:
        print(f"  {entry['membre']:15s} → frames [{entry['frame_debut']} → {entry['frame_fin']}]")

    # Appliquer le freeze pour chaque entree
    detail            = []
    keyframes_totales = 0

    for entry in params:
        membre      = entry["membre"]
        frame_debut = entry["frame_debut"]
        frame_fin   = entry["frame_fin"]
        bones       = MEMBRE_BONES[membre]

        entry_detail = {
            "membre": membre,
            "frame_debut": frame_debut,
            "frame_fin": frame_fin,
            "bones": {}
        }

        for bone_name in bones:
            stats = _freeze_bone_range(action, bone_name, frame_debut, frame_fin)
            total_bone = sum(stats.values())
            entry_detail["bones"][bone_name] = {"canaux": stats, "keyframes_freezes": total_bone}
            keyframes_totales += total_bone

            if stats:
                print(f"[mask_limbs] {membre:15s} / {bone_name:20s} : "
                      f"{total_bone} kf freezes sur frames [{frame_debut}→{frame_fin}]")
            else:
                print(f"[mask_limbs] {membre:15s} / {bone_name:20s} : "
                      f"aucune FCurve rotation — skip")

        detail.append(entry_detail)

    if keyframes_totales == 0:
        print("[mask_limbs] Aucun keyframe freeze — copie directe du FBX")
        import shutil
        shutil.copy2(fbx_in, fbx_out)
        return {
            "status":  "skipped",
            "raison":  "aucune FCurve de rotation trouvee pour les bones et plages cibles",
            "detail":  detail,
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
    print(f"[mask_limbs] Total : {keyframes_totales} keyframes freezes sur {len(params)} plage(s)")

    return {
        "status":             "ok",
        "operations":         len(params),
        "keyframes_freezes":  keyframes_totales,
        "detail":             detail,
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
        description="FERRUS ANIMUS — EXEC Op.5 : Freeze per-frame des membres hors cadre"
    )
    parser.add_argument("--fbx-in",  required=True, help="FBX source")
    parser.add_argument("--plan",    required=True, help="plan_corrections.json")
    parser.add_argument("--fbx-out", required=True, help="FBX sortie")

    args = parser.parse_args(argv)

    result = run(args.fbx_in, args.plan, args.fbx_out)
    print("\n[mask_limbs] Rapport final :")
    print(json.dumps(result, indent=2, ensure_ascii=False))
