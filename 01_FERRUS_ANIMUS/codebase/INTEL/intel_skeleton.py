"""
intel_skeleton.py — FERRUS ANIMUS / Compartiment INTEL
Analyse les fichiers FBX DeepMotion via le AI Gateway (OpenAI-compatible)
et produit les contrats intel_skeleton_{stem}.json.

Appele depuis le notebook Colab (cellule INTEL) apres pre_parse_fbx.py.

Variable d'environnement requise : AI_GATEWAY_API_KEY (Secrets Colab)

Voir : FERRUS_INTEL_SKELETON_CLAUDE_METAPROMPT.md pour le detail du prompt.
"""

import requests
import json
import os

from pre_parse_fbx import extract_fbx_metadata


# ══ Configuration AI Gateway ══════════════════════════════════════════════════

AI_GATEWAY_URL = "https://ai-gateway.happycapy.ai/api/v1/chat/completions"
AI_GATEWAY_MODEL = "anthropic/claude-sonnet-4-6"

SYSTEM_PROMPT = (
    "Tu es un validateur de pipeline d'animation 3D specialise dans les fichiers FBX DeepMotion. "
    "Tu analyses des metadonnees de squelette et d'animation pour parametrer un pipeline de correction automatique. "
    "Base chaque conclusion directement sur les donnees fournies dans les balises XML. "
    "Si un champ est absent des donnees, indique-le explicitement — ne l'invente pas. "
    "Reponds directement sans preambule. Le JSON doit commencer par { et terminer par }."
)

USER_PROMPT_TEMPLATE = """{fbx_xml}

Analyse ces metadonnees FBX et retourne UNIQUEMENT un bloc JSON valide.
Ne mets aucun markdown, aucune explication, aucun texte avant ou apres le JSON.
Le JSON doit commencer directement par {{ et se terminer par }}.

FORMAT EXACT ATTENDU :
{{
  "fbx_file": "<nom du fichier source>",
  "metadata": {{
    "fbx_version": "7.7",
    "taille_kb": <entier>,
    "convention_naming": "<EXACTEMENT l'une de ces valeurs : deepmotion_jnt | mixamo | custom>",
    "t_pose_incluse": <true ou false>,
    "base_model": "<string — ex: female-normal, male-athletic ou inconnu si absent>"
  }},
  "squelette": {{
    "root_bone": "<nom de l'os racine>",
    "total_bones": <entier>,
    "bones_core": <entier — nombre d'os du corps principal sans les doigts>,
    "bones_doigts": <entier — 0 si pas de doigts>,
    "bones_manquants": [<liste de strings — os R15 attendus mais absents, vide [] si mapping complet>],
    "mapping_r15_valide": <true ou false>
  }},
  "animation": {{
    "take_name": "<nom du take d'animation>",
    "duree_frames": <entier>,
    "duree_sec": <nombre decimal>,
    "fps": <entier>,
    "total_keyframes": <entier>,
    "rotation_order": "<EXACTEMENT l'une de ces valeurs : EulerXYZ | EulerZYX | Quaternion | Mixte>",
    "quaternion_disponible": <true ou false>
  }},
  "qualite_fcurves": {{
    "score_global": <decimal entre 0.0 et 1.0 — qualite generale de l'animation>,
    "jitter_detecte": <true ou false>,
    "jitter_bones": [<liste de strings — noms des os avec jitter detecte, vide [] si aucun>],
    "jitter_score": <decimal entre 0.0 et 1.0 — intensite du jitter, 0.0 si absent>,
    "foot_slide": {{
      "detecte": <true ou false>,
      "pied_gauche_delta_max_cm": <decimal — 0.0 si absent>,
      "pied_droit_delta_max_cm": <decimal — 0.0 si absent>
    }},
    "derive_hanches": {{
      "detectee": <true ou false>,
      "delta_vertical_cm": <decimal — 0.0 si absent>,
      "direction": "<EXACTEMENT l'une de ces valeurs : descente_progressive | montee_progressive | stable>"
    }},
    "gimbal_lock_risque": <true ou false — true si rotation euler sans quaternion disponible>
  }},
  "corrections_requises": [<liste de strings parmi : smooth_fcurves | stabilize_hips | remove_foot_slide — base uniquement sur les defauts detectes>],
  "corrections_optionnelles": [<liste de strings parmi : mask_limbs | camera_follow — a laisser au merge>]
}}

REGLES D'ANALYSE OBLIGATOIRES :

--- MAPPING R15 ---
Le mapping DeepMotion -> Roblox R15 attendu est :
  Hip           -> LowerTorso (root)
  spine1_JNT    -> UpperTorso
  Head          -> Head
  LeftUpArm     -> LeftUpperArm
  LeftLowArm    -> LeftLowerArm
  LeftHand      -> LeftHand
  RightUpArm    -> RightUpperArm
  RightLowArm   -> RightLowerArm
  RightHand     -> RightHand
  LeftUpLeg     -> LeftUpperLeg
  LeftLowLeg    -> LeftLowerLeg
  LeftFoot      -> LeftFoot
  RightUpLeg    -> RightUpperLeg
  RightLowLeg   -> RightLowerLeg
  RightFoot     -> RightFoot

Os ignores (non requis par R15) :
  LeftCollar, RightCollar, Neck,
  tous les doigts

mapping_r15_valide = true si TOUS les 15 os cibles sont presents dans le squelette.

--- QUALITE ---
- score_global 1.0 = animation parfaite, aucun defaut detecte
- score_global 0.7-0.9 = animation bonne avec defauts mineurs
- score_global 0.5-0.7 = defauts significatifs necessitant correction
- score_global < 0.5 = animation fortement degradee

--- CORRECTIONS REQUISES ---
Ajouter a corrections_requises UNIQUEMENT si le probleme est detecte dans les donnees :
- "smooth_fcurves" si jitter_detecte = true
- "stabilize_hips" si derive_hanches.detectee = true et delta_vertical_cm > 2.0
- "remove_foot_slide" si foot_slide.detecte = true

--- GIMBAL LOCK ---
gimbal_lock_risque = true si rotation_order est EulerXYZ ou EulerZYX ET quaternion_disponible = false

IMPORTANT :
- Base CHAQUE conclusion directement sur les donnees XML fournies.
- Ne pas inventer de bones_manquants si tous les os du mapping R15 sont presentes.
- Si une valeur est absente des donnees XML, utilise des valeurs par defaut conservatrices (false, 0.0, []).
- corrections_optionnelles doit toujours contenir ["mask_limbs", "camera_follow"] — ces decisions appartiennent au merge.
"""


# ══ Fonctions principales ═════════════════════════════════════════════════════

def analyze_fbx_with_gateway(fbx_path: str, fbx_xml: str, api_key: str) -> dict:
    """
    Envoie les metadonnees FBX au AI Gateway et retourne l'analyse structuree.

    Args:
        fbx_path: chemin vers le fichier FBX (pour le nom de fichier)
        fbx_xml:  metadonnees pre-parsees par bpy (sortie de extract_fbx_metadata)
        api_key:  cle AI Gateway (AI_GATEWAY_API_KEY)

    Returns:
        dict conforme au contrat INTEL-SKELETON
    """
    user_message = USER_PROMPT_TEMPLATE.format(fbx_xml=fbx_xml)

    payload = {
        "model": AI_GATEWAY_MODEL,
        "max_tokens": 4096,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    response = requests.post(AI_GATEWAY_URL, json=payload, headers=headers, timeout=60)
    response.raise_for_status()

    response_text = response.json()["choices"][0]["message"]["content"].strip()

    # Nettoyer les backticks eventuels (fallback)
    if response_text.startswith("```"):
        lines = response_text.split("\n")
        response_text = "\n".join(lines[1:-1])

    result = json.loads(response_text)

    # Injection du nom de fichier si absent
    if "fbx_file" not in result:
        result["fbx_file"] = os.path.basename(fbx_path)

    return result


def _static_fallback(fbx_path: str, fbx_xml: str) -> dict:
    """
    Analyse statique basee uniquement sur le pre-parsing bpy.
    Utilisee si ANTHROPIC_API_KEY est absent.
    Produit un JSON minimal conservateur.
    """
    import xml.etree.ElementTree as ET

    stem = os.path.splitext(os.path.basename(fbx_path))[0]
    root_el = ET.fromstring(fbx_xml)

    total_bones = len(root_el.findall(".//bone"))
    taille_kb = int(float(root_el.findtext("taille_kb", "0")))
    take_name = root_el.findtext(".//take_name", "Take 001")
    duree_sec = float(root_el.findtext(".//duree_sec", "0"))
    fps = int(root_el.findtext(".//fps", "30"))
    total_kf = int(root_el.findtext(".//total_keyframes", "0"))
    duree_frames = int(round(duree_sec * fps))
    quat = root_el.findtext(".//quaternion_disponible", "false") == "true"
    rot_order = "Quaternion" if quat else "EulerXYZ"

    jitter = root_el.findtext(".//jitter_detecte", "false") == "true"
    jitter_bones = [b.get("name", "") for b in root_el.findall(".//jitter_bones/bone")]
    jitter_score = float(root_el.findtext(".//jitter_global_score", "0.0"))

    foot_slide = root_el.findtext(".//foot_slide_detecte", "false") == "true"
    gauche = float(root_el.findtext('.//foot[@bone="LeftFoot"][@delta_cm]', "0") or
                   (root_el.find('.//foot[@bone="LeftFoot"]').get("delta_cm", "0")
                    if root_el.find('.//foot[@bone="LeftFoot"]') is not None else "0"))
    droite = float(root_el.findtext('.//foot[@bone="RightFoot"][@delta_cm]', "0") or
                   (root_el.find('.//foot[@bone="RightFoot"]').get("delta_cm", "0")
                    if root_el.find('.//foot[@bone="RightFoot"]') is not None else "0"))

    derive = root_el.findtext(".//derive_hanches_detectee", "false") == "true"
    derive_el = root_el.find(".//derive_hanches")
    derive_cm = float(derive_el.get("delta_vertical_cm", "0")) if derive_el is not None else 0.0
    derive_dir = derive_el.get("direction", "stable") if derive_el is not None else "stable"

    corrections = []
    if jitter:
        corrections.append("smooth_fcurves")
    if derive and derive_cm > 2.0:
        corrections.append("stabilize_hips")
    if foot_slide:
        corrections.append("remove_foot_slide")

    score = 1.0 - (0.2 * int(jitter) + 0.15 * int(derive) + 0.15 * int(foot_slide))

    return {
        "fbx_file": os.path.basename(fbx_path),
        "metadata": {
            "fbx_version": "7.7",
            "taille_kb": taille_kb,
            "convention_naming": "custom",
            "t_pose_incluse": True,
            "base_model": "inconnu",
        },
        "squelette": {
            "root_bone": "Hip",
            "total_bones": total_bones,
            "bones_core": max(0, total_bones - 30),
            "bones_doigts": 30 if total_bones >= 52 else 0,
            "bones_manquants": [],
            "mapping_r15_valide": total_bones >= 22,
        },
        "animation": {
            "take_name": take_name,
            "duree_frames": duree_frames,
            "duree_sec": duree_sec,
            "fps": fps,
            "total_keyframes": total_kf,
            "rotation_order": rot_order,
            "quaternion_disponible": quat,
        },
        "qualite_fcurves": {
            "score_global": round(max(0.0, score), 2),
            "jitter_detecte": jitter,
            "jitter_bones": jitter_bones,
            "jitter_score": jitter_score,
            "foot_slide": {
                "detecte": foot_slide,
                "pied_gauche_delta_max_cm": gauche,
                "pied_droit_delta_max_cm": droite,
            },
            "derive_hanches": {
                "detectee": derive,
                "delta_vertical_cm": derive_cm,
                "direction": derive_dir,
            },
            "gimbal_lock_risque": not quat and rot_order in ("EulerXYZ", "EulerZYX"),
        },
        "corrections_requises": corrections,
        "corrections_optionnelles": ["mask_limbs", "camera_follow"],
    }


def run_intel_skeleton(
    fbx_files: list,
    output_dir: str,
    api_key: str = None,
) -> list:
    """
    Execute l'analyse INTEL-SKELETON sur tous les fichiers FBX.

    Args:
        fbx_files:  liste des chemins vers les fichiers FBX dans IN/
        output_dir: dossier ou sauvegarder les JSON d'analyse
        api_key:    cle AI Gateway — AI_GATEWAY_API_KEY (None = fallback statique)

    Returns:
        liste des analyses, une par FBX
    """
    results = []

    for fbx_path in fbx_files:
        stem = os.path.splitext(os.path.basename(fbx_path))[0]
        cache_path = os.path.join(output_dir, f"intel_skeleton_{stem}.json")

        # Cache hit
        if os.path.exists(cache_path):
            print(f"  [INTEL-SKELETON] Cache hit : {stem}")
            with open(cache_path, "r") as f:
                results.append(json.load(f))
            continue

        print(f"  [INTEL-SKELETON] Analyse : {stem}...")

        # Pre-parsing bpy
        fbx_xml = extract_fbx_metadata(fbx_path)

        # Appel AI Gateway ou fallback statique
        if api_key:
            analysis = analyze_fbx_with_gateway(fbx_path, fbx_xml, api_key)
        else:
            print(f"  [INTEL-SKELETON] AI_GATEWAY_API_KEY absent — fallback statique")
            analysis = _static_fallback(fbx_path, fbx_xml)

        # Sauvegarde cache
        os.makedirs(output_dir, exist_ok=True)
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(analysis, f, ensure_ascii=False, indent=2)

        score = analysis["qualite_fcurves"]["score_global"]
        corrections = analysis["corrections_requises"]
        print(f"  [INTEL-SKELETON] {stem} → score={score} | corrections={corrections}")

        results.append(analysis)

    return results
