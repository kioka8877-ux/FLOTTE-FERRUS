# FERRUS_PRD.md — Bible Technique
# FREGATE 01 : FERRUS ANIMUS
# Version : 2.0 | Date : 2026-04-24 | Statut : REFACTORISATION ARCHITECTURALE

---

## I. VISION IMPERIALE

Transferer l'animation d'un FBX DeepMotion vers un avatar rige produit par FERRUS OSSEUS,
avec nettoyage IA, correction dynamique et choix du squelette cible.
Pipeline 100% automatise sur Google Colab gratuit.

**Objectif mesurable :** 1 video DeepMotion (< 15s, N personnes) + N avatars OSSEUS → N FBX
animes et purifies en moins de 5 minutes, cout zero, sans intervention technique de l'Empereur.

---

## II. CONTRAT D'ETANCHEITE

```
Drive/FLOTTE-FERRUS/01_FERRUS_ANIMUS/
  IN/           <- FBX DeepMotion deposes par l'utilisateur (animation source, 52 bones)
  IN_AVATAR/    <- FBX OSSEUS deposes par l'utilisateur (avatar rige T-pose, 52 bones)
  OUT/          <- FBX animes avec mesh avatar + rapport.json global
```

Matching par ordre alphabetique : person_01 animation <-> person_01 avatar.
Rien ne traverse la coque sans passer par ces trois portes.

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
- `pre_parse_fbx.py` — charge le FBX DeepMotion via bpy, extrait les metadonnees en XML
- `intel_skeleton.py` — appel Claude API, retourne l'analyse structuree
- `prompts/correction_prompt.txt` — mega-prompt Gemini Chat (Mode sans API)

**Contrat de sortie :** `plan_corrections.json` (voir section VII)

### 3.2 Compartiment EXEC — La Forge Mechanicus

**Mission :** Appliquer les corrections sur les FBX DeepMotion via bpy headless,
AVANT injection dans l'avatar OSSEUS.

**5 operations modulaires, activees conditionnellement par plan_corrections.json :**

| OPERATION | CONDITION D'ACTIVATION | PARAMETRE CLE |
|---|---|---|
| smooth_fcurves.py | jitter_detecte = true | bones_cibles, intensite |
| stabilize_hips.py | derive_hanches.detectee = true | correction_verticale_cm |
| remove_foot_slide.py | foot_slide.detecte = true | seuil_cm |
| camera_follow.py | camera_follow.actif = true | cible_person_id, type_suivi |
| mask_limbs.py | mask_limbs.actif = true | membres_a_masquer (avec plages frames) |

**Contrainte :** chaque operation est independante, ne depend pas des autres.

**mask_limbs.py — comportement per-frame (NOUVEAU) :**
Le masquage est dynamique par plage de frames, pas global. Quand un membre sort du cadre,
il se fige a sa derniere position connue (freeze). Quand il revient, l'animation reprend.
`membres_a_masquer` contient des objets `{membre, frame_debut, frame_fin}`.

### 3.3 Compartiment OUTPUT — Le Sanctuaire

**Mission :** Injecter l'animation nettoyee dans l'avatar OSSEUS selon le BONES_MODE choisi.

**Module :** `retarget_r15.py`

**Principe :**
- Charge le FBX OSSEUS (mesh + squelette T-pose 52 bones)
- Charge le FBX DeepMotion corrige (animation)
- Transfert selon BONES_MODE (voir section IV)
- Exporte le FBX avec le mesh OSSEUS anime

---

## IV. BONES_MODE — TROIS MODES DE SORTIE

| MODE | BONES | TECHNIQUE | USAGE |
|---|---|---|---|
| `DEEPMOTION` | 52 | Transfer direct FCurves (meme noms) | Blender, Unity full fingers |
| `MIXAMO` | 26 | Retargeting 52 -> 26 (prefixe mixamorig:) | Unity, UE5, Mixamo compat |
| `R15` | 15 | Retargeting 52 -> 15 | Roblox natif |

**Selecteur dans Cell 3 (CONFIG) du notebook :**
```python
BONES_MODE = "DEEPMOTION"   # ou "MIXAMO" ou "R15"
```

**Mode DEEPMOTION — cas trivial (meme squelette) :**
OSSEUS et DeepMotion utilisent le meme squelette 52 bones (memes noms de bones).
Le transfert consiste a copier les FCurves directement — pas de remapping.
Output inclut le mesh OSSEUS (pas animation-only).

---

## V. MAPPING SQUELETTES

### DeepMotion → Roblox R15 (15 bones)

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

### DeepMotion → Mixamo (26 bones)

| OS DEEPMOTION (_JNT) | OS MIXAMO |
|---|---|
| hips_JNT | mixamorig:Hips |
| spine_JNT | mixamorig:Spine |
| spine1_JNT | mixamorig:Spine1 |
| spine2_JNT | mixamorig:Spine2 |
| neck_JNT | mixamorig:Neck |
| head_JNT | mixamorig:Head |
| l_shoulder_JNT | mixamorig:LeftShoulder |
| l_arm_JNT | mixamorig:LeftArm |
| l_forearm_JNT | mixamorig:LeftForeArm |
| l_hand_JNT | mixamorig:LeftHand |
| r_shoulder_JNT | mixamorig:RightShoulder |
| r_arm_JNT | mixamorig:RightArm |
| r_forearm_JNT | mixamorig:RightForeArm |
| r_hand_JNT | mixamorig:RightHand |
| l_upleg_JNT | mixamorig:LeftUpLeg |
| l_leg_JNT | mixamorig:LeftLeg |
| l_foot_JNT | mixamorig:LeftFoot |
| l_toebase_JNT | mixamorig:LeftToeBase |
| r_upleg_JNT | mixamorig:RightUpLeg |
| r_leg_JNT | mixamorig:RightLeg |
| r_foot_JNT | mixamorig:RightFoot |
| r_toebase_JNT | mixamorig:RightToeBase |

**Prefixe Mixamo :** par defaut `mixamorig:` (standard Mixamo FBX export).

### DeepMotion → DeepMotion (52 bones — mode DEEPMOTION)

Transfer direct — pas de mapping. Les bones ont les memes noms dans OSSEUS et DeepMotion.
FCurves copiees telles quelles sur l'armature OSSEUS.

---

## VI. GESTION MULTI-PERSONNES (Option C)

1. Script scanne `IN/` et `IN_AVATAR/` automatiquement
2. Matching alphabetique : 1er FBX animation <-> 1er FBX avatar, etc.
3. `manifest.json` auto-genere avec champs `fbx_input` et `avatar_fbx`
4. Traitement sequentiel P1 → P2 → ... (contrainte RAM Colab)
5. Gemini analyse TOUTES les personnes ensemble (contexte partage)
6. Sortie : `OUT/ferrus_P1.fbx`, `OUT/ferrus_P2.fbx`, `OUT/rapport.json`

---

## VII. STACK TECHNIQUE IMPOSE

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

## VIII. CONTRATS JSON

### intel_vision_{hash}.json (sortie Gemini) — EVOLUE
Champs cles : scene_id, video, camera, personnes[], instructions_camera, contexte_scene
**Evolution :** `membres_hors_cadre` est maintenant une liste d'objets `{membre, frame_debut, frame_fin}`
au lieu d'une liste de strings. Voir : FERRUS_INTEL_VISION_GEMINI_METAPROMPT.md

### intel_skeleton_{stem}.json (sortie Claude) — INCHANGE
Champs cles : fbx_file, metadata, squelette, animation, qualite_fcurves,
corrections_requises, corrections_optionnelles
Voir : FERRUS_INTEL_SKELETON_CLAUDE_METAPROMPT.md (section SORTIE ATTENDUE)

### manifest.json (sortie SCAN) — EVOLUE
Champs par personne : person_id, fbx_input, **avatar_fbx** (NOUVEAU), fbx_output
Le champ `avatar_fbx` pointe vers le FBX OSSEUS correspondant dans IN_AVATAR/

### plan_corrections.json (sortie Merge → EXEC + OUTPUT) — EVOLUE
Champs cles par personne : person_id, fbx_input, **avatar_fbx** (NOUVEAU), fbx_output,
corps_visible, membres_hors_cadre (objets avec plages frames), corrections_exec{},
retargeting_output{bones_mode}

---

## IX. CACHE STRATEGY

| CACHE | CLE | DUREE |
|---|---|---|
| intel_vision_{stem}_{hash10}.json | Hash MD5 (1 Mo) de la video | Session Colab |
| intel_skeleton_{stem}.json | Nom du fichier FBX | Session Colab |

**Principe :** une video/FBX deja analyse ne consomme plus de tokens API.

---

## X. RAPPORT DE SORTIE

`OUT/rapport.json` contient :
- Nombre de personnes traitees
- Score qualite input par FBX
- Corrections appliquees par FBX
- Duree de traitement par FBX
- Mapping bones valide (true/false)
- BONES_MODE utilise
- Chemin des FBX de sortie

---

## XI. DEUX MODES D'UTILISATION INTEL (valides simultanement)

### Mode Chat (principal — zero API key)

| MODELE | INPUT | OUTPUT | INJECTION |
|---|---|---|---|
| Gemini Chat | video.mp4 + FERRUS_INTEL_VISION_GEMINI_METAPROMPT.md | intel_vision.json | Copie manuelle dans cellule Colab |
| Claude Chat | FBX brut (≤ 20 Mo) + FERRUS_INTEL_SKELETON_CLAUDE_METAPROMPT.md | intel_skeleton.json | Copie manuelle dans cellule Colab |

**Verrou JSON :** metaprompt (FORMAT EXACT ATTENDU + enums + champs requis)

### Mode API (alternatif — automatise)

| MODELE | MODULE | INPUT | OUTPUT |
|---|---|---|---|
| Claude API | intel_skeleton.py | XML pre-parse (pre_parse_fbx.py) | intel_skeleton.json (auto) |
| Gemini API | (futur) | video.mp4 | intel_vision.json (auto) |

Les deux modes produisent le **meme contrat JSON** — le pipeline EXEC ne fait pas la difference.

---

## XII. CONTRAINTES INVIOLABLES

1. Blender en mode headless uniquement (-b) — zero interface
2. GPU jamais utilise — CPU obligatoire
3. Chaque operation EXEC independante — pas de chaine de dependances inter-ops
4. plan_corrections.json = seul contrat entre INTEL et EXEC/OUTPUT
5. Rotations forcees en quaternion au retargeting (prevenir gimbal lock)
6. L'avatar OSSEUS (IN_AVATAR/) n'est jamais modifie — il est lu en lecture seule
7. Output toujours avec mesh (pas animation-only, sauf si IN_AVATAR/ vide)
