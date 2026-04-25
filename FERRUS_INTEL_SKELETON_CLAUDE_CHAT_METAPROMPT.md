# CLAUDE CHAT — META-PROMPT INTEL-SKELETON — FERRUS ANIMUS
# Version : 1.0 | Date : 2026-04-25
# Mode : Upload FBX direct dans Claude Chat — sans API, sans Blender

> **Usage** : colle ce prompt dans [claude.ai](https://claude.ai),
> uploade UN fichier FBX, et recupere le JSON a deposer dans `CLAUDE_IN/` sur Drive.
>
> **Un FBX = un JSON = un fichier dans CLAUDE_IN/.**
> Repeter pour chaque FBX de la video.

---

## ETAPE 1 — Ce qu'il faut faire dans Claude Chat

1. Ouvre [claude.ai](https://claude.ai)
2. Upload **un seul fichier FBX** (bouton trombone)
3. Colle le bloc de prompt ci-dessous **sans rien modifier**
4. Copie le JSON retourne **sans modification**
5. Sauvegarde le fichier sous le nom exact indique dans `fbx_file`
6. Depose le fichier dans `CLAUDE_IN/` sur ton Google Drive

---

## ETAPE 2 — Bloc a coller dans Claude Chat

---

```
Tu es un validateur de pipeline d'animation 3D specialise dans les fichiers FBX DeepMotion.
Analyse le fichier FBX que je t'envoie et retourne UNIQUEMENT un bloc JSON valide.
Ne mets aucun markdown, aucune explication, aucun texte avant ou apres le JSON.
Commence ta reponse directement par { et termine par }.

FORMAT EXACT ATTENDU :
{
  "fbx_file": "<nom exact du fichier FBX uploade, ex: personne_01.fbx>",
  "metadata": {
    "fbx_version": "<string — version FBX detectee, ex: 7.7>",
    "taille_kb": <entier — taille du fichier en Ko>,
    "convention_naming": "custom",
    "t_pose_incluse": <true ou false>,
    "base_model": "<string — ex: female-normal, male-athletic ou inconnu si absent>"
  },
  "squelette": {
    "root_bone": "<nom de l'os racine — generalement Hip>",
    "total_bones": <entier — nombre total d'os dans le squelette>,
    "bones_core": <entier — nombre d'os du corps principal sans les doigts>,
    "bones_doigts": <entier — 0 si pas de doigts>,
    "bones_manquants": [<liste de strings — os R15 attendus mais absents du FBX, vide [] si tous presents>],
    "mapping_r15_valide": <true ou false>
  },
  "animation": {
    "take_name": "<nom du take d'animation>",
    "duree_frames": <entier>,
    "duree_sec": <nombre decimal>,
    "fps": <entier>,
    "total_keyframes": <entier>,
    "rotation_order": "<EXACTEMENT l'une de ces valeurs : EulerXYZ | EulerZYX | Quaternion | Mixte>",
    "quaternion_disponible": <true ou false>
  },
  "qualite_fcurves": {
    "score_global": <decimal entre 0.0 et 1.0>,
    "jitter_detecte": <true ou false>,
    "jitter_bones": [<liste de strings — noms des os avec jitter, vide [] si aucun>],
    "jitter_score": <decimal entre 0.0 et 1.0 — 0.0 si absent>,
    "foot_slide": {
      "detecte": <true ou false>,
      "pied_gauche_delta_max_cm": <decimal — 0.0 si absent>,
      "pied_droit_delta_max_cm": <decimal — 0.0 si absent>
    },
    "derive_hanches": {
      "detectee": <true ou false>,
      "delta_vertical_cm": <decimal — 0.0 si absent>,
      "direction": "<EXACTEMENT l'une de ces valeurs : descente_progressive | montee_progressive | stable>"
    },
    "gimbal_lock_risque": <true ou false>
  },
  "corrections_requises": [<liste parmi : smooth_fcurves | stabilize_hips | remove_foot_slide — uniquement si detecte>],
  "corrections_optionnelles": ["mask_limbs", "camera_follow"]
}

REGLES D'ANALYSE OBLIGATOIRES :

--- MAPPING R15 (convention custom DeepMotion) ---
Os R15 attendus dans ce FBX :
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

mapping_r15_valide = true si les 15 os ci-dessus sont tous presents dans le squelette.
bones_manquants = liste des os du tableau ci-dessus absents du FBX (vide [] si mapping complet).

Os ignores (non requis par R15) :
  LeftCollar, RightCollar, l_toebase_JNT, r_toebase_JNT, Neck,
  tous les doigts (Index, Middle, Ring, Pinky, Thumb et leurs phalanges)

--- QUALITE ---
- score_global 1.0 = animation parfaite, aucun defaut
- score_global 0.7-0.9 = defauts mineurs
- score_global 0.5-0.7 = defauts significatifs
- score_global < 0.5 = animation fortement degradee

--- CORRECTIONS REQUISES ---
Ajouter a corrections_requises UNIQUEMENT si detecte :
- "smooth_fcurves"     si jitter_detecte = true
- "stabilize_hips"     si derive_hanches.detectee = true et delta_vertical_cm > 2.0
- "remove_foot_slide"  si foot_slide.detecte = true

--- GIMBAL LOCK ---
gimbal_lock_risque = true si rotation_order est EulerXYZ ou EulerZYX ET quaternion_disponible = false

--- CHAMPS FIXES ---
convention_naming = toujours "custom" pour ces FBX
corrections_optionnelles = toujours ["mask_limbs", "camera_follow"] sans exception

IMPORTANT :
- Retourne UNIQUEMENT le JSON brut. Pas de ```json```. Pas d'explication. Juste le JSON.
- Respecte EXACTEMENT les valeurs d'enum (minuscules, underscores).
- Si une valeur est incertaine, utilise des valeurs conservatrices (false, 0.0, []).
- Ne pas inventer de bones_manquants si tous les 15 os du mapping sont presents.
```

---

## ETAPE 3 — Nommer et deposer le fichier

Le JSON retourne par Claude doit etre sauvegarde sous ce nom exact :

```
intel_skeleton_<nom_du_fbx_sans_extension>.json

Exemples :
  personne_01.fbx  →  intel_skeleton_personne_01.json
  personne_02.fbx  →  intel_skeleton_personne_02.json
```

Deposer dans :
```
Google Drive / tools / 01_FERRUS_ANIMUS / CLAUDE_IN /
  intel_skeleton_personne_01.json
  intel_skeleton_personne_02.json
```

---

## ETAPE 4 — Repeter pour chaque FBX

Un nouveau message Claude Chat par FBX. Meme prompt, FBX different.

---

## ETAPE 5 — Lancer le pipeline Colab

Une fois tous les JSON deposes dans `CLAUDE_IN/` :

1. **Cell 4 (SCAN)** — verifie le manifest
2. **Cell 5 (INTEL)** — detecte les fichiers dans `CLAUDE_IN/` → les copie en cache → skip l'appel API
3. **Cell 6 (GEMINI)** — injecte `intel_vision.json`
4. **Cell 7 (MERGE)** — fusionne tout → `plan_corrections.json`

---

## Resume du workflow

```
Pour chaque FBX :
  claude.ai
  └─ Upload FBX + colle le prompt
  └─ Copie le JSON retourne
  └─ Sauvegarde sous intel_skeleton_{stem}.json
  └─ Depose dans CLAUDE_IN/ sur Drive

Colab :
  Cell 5 → detecte CLAUDE_IN/ → cache hit → skip API
  Cell 6 → charge intel_vision.json (Gemini)
  Cell 7 → merge → plan_corrections.json
```

---

## Notes importantes

- **Claude.ai** : utiliser Claude Sonnet ou Opus pour une meilleure lecture des FBX binaires
- **Taille FBX** : Claude Chat accepte les fichiers jusqu'a ~30 Mo — suffisant pour des FBX DeepMotion standards
- **Cache prioritaire** : si `intel_skeleton_{stem}.json` existe dans `CLAUDE_IN/`, Cell 5 l'utilise directement et ne fait aucun appel API
- **Verification rapide** : apres avoir obtenu le JSON, verifier que `mapping_r15_valide` est `true` et `bones_manquants` est `[]` avant de deposer
