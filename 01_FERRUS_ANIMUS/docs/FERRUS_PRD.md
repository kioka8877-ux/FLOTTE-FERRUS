# FERRUS_PRD.md — Bible Technique
# FREGATE 01 : FERRUS ANIMUS
# Version : 1.0 | Date : 2026-04-17 | Statut : VALIDE

---

## I. VISION IMPERIALE

Transformer des fichiers FBX d'animation bruts issus de DeepMotion en fichiers FBX
retargetes au format Roblox R15, corriges et purifies, prets a integrer une video
de production. Pipeline 100% automatise sur Google Colab gratuit.

**Objectif mesurable :** 1 video DeepMotion (< 15s, N personnes) → N FBX R15 propres
en moins de 5 minutes, cout zero, sans intervention technique de l'Empereur.

---

## II. CONTRAT D'ETANCHEITE

```
Drive/FLOTTE-FERRUS/01_FERRUS_ANIMUS/
  IN/   <- Entree unique : FBX DeepMotion deposes par l'utilisateur
  OUT/  <- Sortie unique : FBX R15 retargetes + rapport.json global
```

Rien ne traverse la coque sans passer par ces deux portes.

---

## III. ARCHITECTURE — LES TROIS COMPARTIMENTS

### 3.1 Compartiment INTEL — L'Oracle Cogitateur

**Mission :** Analyser la scene et produire `plan_corrections.json`

**Double tete :**

| SOURCE | OUTIL | INPUT | OUTPUT |
|---|---|---|---|
| INTEL-VISION | Gemini Chat (gemini.google.com) | Video .mp4 originale | intel_vision_{hash}.json |
| INTEL-SKELETON | Claude API (claude-sonnet-4-6) | FBX pre-parse via bpy | intel_skeleton_{stem}.json |
| MERGE | Python (merge automatique) | Les deux JSON ci-dessus | plan_corrections.json |

**Modules :**
- `pre_parse_fbx.py` — charge le FBX via bpy, extrait les metadonnees en XML
- `intel_skeleton.py` — appel Claude API, retourne l'analyse structuree
- `prompts/correction_prompt.txt` — mega-prompt Gemini Chat (Mode sans API)

**Contrat de sortie :** `plan_corrections.json` (voir section VII)

### 3.2 Compartiment EXEC — La Forge Mechanicus

**Mission :** Appliquer les corrections sur les FBX via bpy headless

**5 operations modulaires, activees conditionnellement par plan_corrections.json :**

| OPERATION | CONDITION D'ACTIVATION | PARAMETRE CLE |
|---|---|---|
| smooth_fcurves.py | jitter_detecte = true | bones_cibles, intensite |
| stabilize_hips.py | derive_hanches.detectee = true | correction_verticale_cm |
| remove_foot_slide.py | foot_slide.detecte = true | seuil_cm |
| camera_follow.py | camera_follow.actif = true | cible_person_id, type_suivi |
| mask_limbs.py | mask_limbs.actif = true | membres_a_masquer |

**Contrainte :** chaque operation est independante, ne depend pas des autres.

### 3.3 Compartiment OUTPUT — Le Sanctuaire

**Mission :** Retargeter le squelette DeepMotion vers Roblox R15

**Module :** `retarget_r15.py`

**Principe :** Rig R15 construit programmatiquement (ZERO fichier GLB requis).
Principe herite de motus_forge.py v4 (ANIMA-MECHANICUS, valide).

---

## IV. MAPPING SQUELETTE — VERITE MECHANICUS

### DeepMotion → Roblox R15

| OS DEEPMOTION (_JNT) | OS R15 | NOTE |
|---|---|---|
| hips_JNT | LowerTorso | ROOT — root_position applique ici |
| spine2_JNT | UpperTorso | spine_JNT et spine1_JNT ignores |
| head_JNT | Head | neck_JNT interpole |
| l_arm_JNT | LeftUpperArm | l_shoulder_JNT ignore |
| l_forearm_JNT | LeftLowerArm | |
| l_hand_JNT | LeftHand | |
| r_arm_JNT | RightUpperArm | r_shoulder_JNT ignore |
| r_forearm_JNT | RightLowerArm | |
| r_hand_JNT | RightHand | |
| l_upleg_JNT | LeftUpperLeg | |
| l_leg_JNT | LeftLowerLeg | |
| l_foot_JNT | LeftFoot | l_toebase_JNT ignore |
| r_upleg_JNT | RightUpperLeg | |
| r_leg_JNT | RightLowerLeg | |
| r_foot_JNT | RightFoot | r_toebase_JNT ignore |

**OS IGNORES (30 doigts + 4 autres) :**
l_shoulder_JNT, r_shoulder_JNT, l_toebase_JNT, r_toebase_JNT, neck_JNT,
tous les _handIndex/_handMiddle/_handRing/_handPinky/_handThumb (1-3)

---

## V. GESTION MULTI-PERSONNES (Option C)

1. Script scanne `IN/` et detecte tous les FBX automatiquement
2. `manifest.json` auto-genere → utilisateur valide en 30 secondes
3. Traitement sequentiel P1 → P2 → ... (contrainte RAM Colab)
4. Gemini analyse TOUTES les personnes ensemble (contexte partage)
5. Sortie : `OUT/ferrus_P1.fbx`, `Out/ferrus_P2.fbx`, `OUT/rapport.json`

---

## VI. STACK TECHNIQUE IMPOSE

| COMPOSANT | VALEUR | CONTRAINTE |
|---|---|---|
| Plateforme | Google Colab gratuit | Runtime standard uniquement |
| GPU | INTERDIT | CPU uniquement |
| Blender | 4.x binaire headless (-b) | Stocke dans Drive/tools/ |
| Python | 3.10+ | venv dans Drive/tools/ |
| Claude | claude-sonnet-4-6 | Via API Anthropic |
| Gemini | Gemini Chat (gemini.google.com) | Mode sans API key |
| Temps max | < 5 min pour une video 14s | Mesure de bout en bout |
| Cout recurrent | ZERO euro | Tout gratuit |

---

## VII. CONTRATS JSON

### intel_vision_{hash}.json (sortie Gemini)
Champs cles : scene_id, video, camera, personnes[], instructions_camera, contexte_scene
Voir : FERRUS_INTEL_VISION_GEMINI_METAPROMPT.md (section FORMAT EXACT)

### intel_skeleton_{stem}.json (sortie Claude)
Champs cles : fbx_file, metadata, squelette, animation, qualite_fcurves,
corrections_requises, corrections_optionnelles
Voir : FERRUS_INTEL_SKELETON_CLAUDE_METAPROMPT.md (section SORTIE ATTENDUE)

### plan_corrections.json (sortie Merge → EXEC + OUTPUT)
Champs cles par personne : person_id, fbx_input, fbx_output, corps_visible,
membres_hors_cadre, corrections_exec{}, retargeting_r15{}
Voir : Codex Mechanicus Tome I — Section XV.3

---

## VIII. CACHE STRATEGY

| CACHE | CLE | DUREE |
|---|---|---|
| intel_vision_{stem}_{hash10}.json | Hash MD5 (1 Mo) de la video | Session Colab |
| intel_skeleton_{stem}.json | Nom du fichier FBX | Session Colab |

**Principe :** une video/FBX deja analyse ne consomme plus de tokens API.

---

## IX. RAPPORT DE SORTIE

`OUT/rapport.json` contient :
- Nombre de personnes traitees
- Score qualite input par FBX
- Corrections appliquees par FBX
- Duree de traitement par FBX
- Mapping R15 valide (true/false)
- Chemin des FBX de sortie

---

## X. CONTRAINTES INVIOLABLES

1. Aucun fichier GLB en input — rig R15 programme
2. Blender en mode headless uniquement (-b) — zero interface
3. GPU jamais utilise — CPU obligatoire
4. Chaque operation EXEC independante — pas de chaine de dependances inter-ops
5. plan_corrections.json = seul contrat entre INTEL et EXEC/OUTPUT
6. Rotations forcees en quaternion au retargeting (prevenir gimbal lock)
