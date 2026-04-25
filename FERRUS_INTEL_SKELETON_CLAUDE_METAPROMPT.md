# CLAUDE API — META-PROMPT INTEL-SKELETON — FERRUS ANIMUS

> **Mode API** : ce prompt est execute via l'API Anthropic (claude-sonnet-4-6) directement
> dans le notebook Colab, cellule INTEL. Il analyse les fichiers FBX DeepMotion et produit
> le contrat technique `intel_skeleton_{fbx_stem}.json` par fichier.
>
> **Architecture** : les donnees FBX sont pre-parsees par bpy en XML avant d'etre envoyees
> a Claude. Claude ne recoit jamais de binaire brut — seulement des metadonnees structurees.

---

## CONFIGURATION API (cellule Colab)

```python
import anthropic
import json

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """Tu es un validateur de pipeline d'animation 3D specialise dans les fichiers FBX DeepMotion.
Tu analyses des metadonnees de squelette et d'animation pour parametrer un pipeline de correction automatique.
Base chaque conclusion directement sur les donnees fournies dans les balises XML.
Si un champ est absent des donnees, indique-le explicitement — ne l'invente pas.
Reponds directement sans preambule. Le JSON doit commencer par { et terminer par }."""
```

---

## PRE-PARSING bpy — Extracteur de metadonnees FBX

Ce script Python est execute **avant** l'appel Claude pour extraire les metadonnees du FBX.

```python
# ══ pre_parse_fbx.py — extrait les metadonnees en XML pour Claude ══
import bpy
import sys
import json
import math

def extract_fbx_metadata(fbx_path: str) -> str:
    """Charge le FBX via bpy et retourne un bloc XML de metadonnees."""

    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=fbx_path)

    scene = bpy.context.scene
    armature = next((o for o in scene.objects if o.type == 'ARMATURE'), None)

    if not armature:
        return "<error>Aucune armature trouvee dans le fichier FBX</error>"

    # --- Squelette ---
    bones = list(armature.data.bones)
    bone_lines = []
    for bone in bones:
        parent_name = bone.parent.name if bone.parent else "ROOT"
        bone_lines.append(f'    <bone name="{bone.name}" parent="{parent_name}"/>')

    # --- Animations ---
    action = armature.animation_data.action if armature.animation_data else None
    anim_info = ""
    jitter_info = ""
    foot_slide_info = ""
    derive_info = ""

    if action:
        frame_start = int(action.frame_range[0])
        frame_end = int(action.frame_range[1])
        fps = scene.render.fps
        duration_sec = round((frame_end - frame_start) / fps, 2)
        total_keyframes = sum(len(fc.keyframe_points) for fc in action.fcurves)

        # Detection de la convention de rotation
        rot_modes = set()
        for fc in action.fcurves:
            if 'rotation_euler' in fc.data_path:
                rot_modes.add('euler')
            elif 'rotation_quaternion' in fc.data_path:
                rot_modes.add('quaternion')

        # Detection jitter (variance des FCurves mains et tete)
        jitter_bones = []
        jitter_scores = {}
        JITTER_BONES_CIBLES = ['l_hand_JNT', 'r_hand_JNT', 'head_JNT', 'l_forearm_JNT', 'r_forearm_JNT']

        for bone_name in JITTER_BONES_CIBLES:
            bone_fcurves = [fc for fc in action.fcurves if bone_name in fc.data_path]
            if not bone_fcurves:
                continue
            # Calcul de la variance des derivees (jitter = changements brusques)
            for fc in bone_fcurves:
                values = [kp.co[1] for kp in fc.keyframe_points]
                if len(values) < 3:
                    continue
                diffs = [abs(values[i+1] - values[i]) for i in range(len(values)-1)]
                variance = sum(d**2 for d in diffs) / len(diffs)
                if variance > 0.001:  # Seuil empirique
                    if bone_name not in jitter_bones:
                        jitter_bones.append(bone_name)
                    jitter_scores[bone_name] = round(min(variance * 100, 1.0), 3)

        global_jitter_score = round(sum(jitter_scores.values()) / max(len(jitter_scores), 1), 3) if jitter_scores else 0.0

        # Detection foot slide (mouvement des pieds quand ils devraient etre statiques)
        foot_bones = {'l_foot_JNT': 'pied_gauche', 'r_foot_JNT': 'pied_droit'}
        foot_slide_data = {}
        for bone_name, label in foot_bones.items():
            bone_loc = [fc for fc in action.fcurves
                        if bone_name in fc.data_path and 'location' in fc.data_path]
            if bone_loc:
                all_values = []
                for fc in bone_loc:
                    all_values.extend([kp.co[1] for kp in fc.keyframe_points])
                if all_values:
                    delta = round((max(all_values) - min(all_values)) * 100, 2)  # en cm approx
                    if delta > 0.5:
                        foot_slide_data[bone_name] = delta

        # Detection derive hanches
        hip_fc = [fc for fc in action.fcurves
                  if 'hips_JNT' in fc.data_path and 'location' in fc.data_path and fc.array_index == 1]
        hip_derive = 0.0
        hip_direction = "stable"
        if hip_fc:
            vals = [kp.co[1] for kp in hip_fc[0].keyframe_points]
            if len(vals) >= 2:
                hip_derive = round(abs(vals[-1] - vals[0]) * 100, 2)
                hip_direction = "descente_progressive" if vals[-1] < vals[0] else "montee_progressive"

        # Assemblage XML
        jitter_xml = ""
        if jitter_bones:
            jitter_bones_xml = "\n".join(f'      <bone name="{b}" score="{jitter_scores.get(b, 0.0)}"/>'
                                          for b in jitter_bones)
            jitter_xml = f"""
    <jitter_detecte>true</jitter_detecte>
    <jitter_global_score>{global_jitter_score}</jitter_global_score>
    <jitter_bones>
{jitter_bones_xml}
    </jitter_bones>"""
        else:
            jitter_xml = "\n    <jitter_detecte>false</jitter_detecte>"

        foot_slide_xml = ""
        if foot_slide_data:
            fs_parts = "\n".join(f'      <foot bone="{k}" delta_cm="{v}"/>'
                                  for k, v in foot_slide_data.items())
            foot_slide_xml = f"\n    <foot_slide_detecte>true</foot_slide_detecte>\n    <foot_slide>\n{fs_parts}\n    </foot_slide>"
        else:
            foot_slide_xml = "\n    <foot_slide_detecte>false</foot_slide_detecte>"

        derive_xml = f"""
    <derive_hanches_detectee>{"true" if hip_derive > 2.0 else "false"}</derive_hanches_detectee>
    <derive_hanches delta_vertical_cm="{hip_derive}" direction="{hip_direction}"/>"""

        anim_info = f"""
  <animation>
    <take_name>{action.name}</take_name>
    <frame_start>{frame_start}</frame_start>
    <frame_end>{frame_end}</frame_end>
    <fps>{fps}</fps>
    <duree_sec>{duration_sec}</duree_sec>
    <total_keyframes>{total_keyframes}</total_keyframes>
    <rotation_modes>{", ".join(rot_modes) if rot_modes else "inconnu"}</rotation_modes>
    <quaternion_disponible>{"true" if "quaternion" in rot_modes else "false"}</quaternion_disponible>
  </animation>
  <qualite_fcurves>{jitter_xml}{foot_slide_xml}{derive_xml}
  </qualite_fcurves>"""

    # Assemblage final
    import os
    file_size_kb = round(os.path.getsize(fbx_path) / 1024, 0)

    xml = f"""<fbx_asset>
  <source>{os.path.basename(fbx_path)}</source>
  <fbx_version>7.7</fbx_version>
  <taille_kb>{file_size_kb}</taille_kb>
  <convention_naming>deepmotion_jnt</convention_naming>
  <squelette>
    <root_bone>hips_JNT</root_bone>
    <total_bones>{len(bones)}</total_bones>
    <bones>
{chr(10).join(bone_lines)}
    </bones>
  </squelette>{anim_info}
</fbx_asset>"""

    return xml
```

---

## PROMPT UTILISATEUR — Template par fichier FBX

Ce template est injecte dans l'appel API Claude pour chaque FBX a analyser.

```python
USER_PROMPT_TEMPLATE = """
{fbx_xml}

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
Le mapping DeepMotion → Roblox R15 attendu est :
  Hip           → LowerTorso (root)
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
```

---

## APPEL API — Fonction principale

```python
def analyze_fbx_with_claude(fbx_path: str, fbx_xml: str) -> dict:
    """
    Envoie les metadonnees FBX a Claude et retourne l'analyse structuree.

    Args:
        fbx_path: chemin vers le fichier FBX (pour le nom de fichier)
        fbx_xml: metadonnees pre-parsees par bpy (sortie de extract_fbx_metadata)

    Returns:
        dict conforme au contrat INTEL-SKELETON
    """
    import os

    user_message = USER_PROMPT_TEMPLATE.format(fbx_xml=fbx_xml)

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        thinking={"type": "adaptive"},
        messages=[
            {"role": "user", "content": user_message}
        ]
    )

    # Extraire le texte de la reponse
    response_text = ""
    for block in response.content:
        if block.type == "text":
            response_text = block.text.strip()
            break

    # Nettoyer les backticks eventuels (fallback)
    if response_text.startswith("```"):
        lines = response_text.split("\n")
        response_text = "\n".join(lines[1:-1])

    # Parser et valider
    result = json.loads(response_text)

    # Injection du nom de fichier si absent
    if "fbx_file" not in result:
        result["fbx_file"] = os.path.basename(fbx_path)

    return result


def run_intel_skeleton(fbx_files: list[str], output_dir: str) -> list[dict]:
    """
    Execute l'analyse INTEL-SKELETON sur tous les fichiers FBX.

    Args:
        fbx_files: liste des chemins vers les fichiers FBX dans IN/
        output_dir: dossier ou sauvegarder les JSON d'analyse

    Returns:
        liste des analyses, une par FBX
    """
    import os

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

        # Appel Claude
        analysis = analyze_fbx_with_claude(fbx_path, fbx_xml)

        # Sauvegarde cache
        os.makedirs(output_dir, exist_ok=True)
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(analysis, f, ensure_ascii=False, indent=2)

        print(f"  [INTEL-SKELETON] {stem} → score={analysis['qualite_fcurves']['score_global']} "
              f"| corrections={analysis['corrections_requises']}")

        results.append(analysis)

    return results
```

---

## SORTIE ATTENDUE — Exemple pour person_01.fbx

```json
{
  "fbx_file": "person_01.fbx",
  "metadata": {
    "fbx_version": "7.7",
    "taille_kb": 2959,
    "convention_naming": "custom",
    "t_pose_incluse": true,
    "base_model": "female-normal"
  },
  "squelette": {
    "root_bone": "hips_JNT",
    "total_bones": 52,
    "bones_core": 22,
    "bones_doigts": 30,
    "bones_manquants": [],
    "mapping_r15_valide": true
  },
  "animation": {
    "take_name": "Take 001",
    "duree_frames": 282,
    "duree_sec": 9.4,
    "fps": 30,
    "total_keyframes": 8460,
    "rotation_order": "EulerXYZ",
    "quaternion_disponible": true
  },
  "qualite_fcurves": {
    "score_global": 0.78,
    "jitter_detecte": true,
    "jitter_bones": ["l_hand_JNT", "r_hand_JNT", "head_JNT"],
    "jitter_score": 0.42,
    "foot_slide": {
      "detecte": true,
      "pied_gauche_delta_max_cm": 3.2,
      "pied_droit_delta_max_cm": 1.8
    },
    "derive_hanches": {
      "detectee": true,
      "delta_vertical_cm": 5.1,
      "direction": "descente_progressive"
    },
    "gimbal_lock_risque": false
  },
  "corrections_requises": ["smooth_fcurves", "stabilize_hips", "remove_foot_slide"],
  "corrections_optionnelles": ["mask_limbs", "camera_follow"]
}
```

---

## Notes importantes

- **Prefill deprecie** : ne pas utiliser `{"role": "assistant", "content": "{"}` — incompatible avec claude-sonnet-4-6. Le prompt utilisateur demande explicitement de commencer par `{`
- **thinking adaptive** : active sur cet appel pour permettre a Claude de valider la hierarchie osseuse correctement
- **Cache obligatoire** : chaque analyse est mise en cache par nom de fichier FBX. Une video traitee deux fois ne consomme pas de tokens Claude
- **Fallback sans API key** : si `ANTHROPIC_API_KEY` est absent, le pipeline peut utiliser une analyse statique basee uniquement sur le pre-parsing bpy (sans scoring semantique)
- **Cout estime** : ~500 tokens d'input + ~600 tokens d'output par FBX analysé avec claude-sonnet-4-6 — negligeable
