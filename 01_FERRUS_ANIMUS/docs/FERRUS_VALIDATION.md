# FERRUS_VALIDATION.md — Protocole de Test
# FREGATE 01 : FERRUS ANIMUS
# Version : 2.0 | Date : 2026-04-24

---

## I. FICHIER DE REFERENCE

| CHAMP | VALEUR |
|---|---|
| Fichier animation | WhatsApp_Video_2026-04-12...(includeTPose).fbx |
| Taille | 2.9 MB |
| Format | FBX 7.7 Binary |
| Source | DeepMotion server (/dmbt-e2e-cli/) |
| Base model | female-normal |
| Bones | 52 (22 core + 30 doigts) |
| Duree | 9.4s (282 frames @ 30fps) |
| Defauts connus | jitter (mains + tete), foot slide, derive hanches |
| Fichier avatar | FBX OSSEUS T-pose 52 bones (produit par FERRUS OSSEUS) |

---

## II. CRITERES DE VALIDATION PAR COMPARTIMENT

### 2.1 INTEL — pre_parse_fbx.py

| TEST | CRITERE DE SUCCES |
|---|---|
| Lecture FBX | Aucune exception bpy, armature detectee |
| Bones extraits | total_bones = 52 |
| Root bone | hips_JNT |
| Mapping R15 | mapping_r15_valide = true |
| Animation | take_name = "Take 001", duree_sec = 9.4, fps = 30 |
| Jitter detecte | jitter_detecte = true, jitter_bones inclut l_hand_JNT et r_hand_JNT |
| Foot slide | foot_slide.detecte = true, pied_gauche_delta_max_cm > 2.0 |
| Derive hanches | derive_hanches.detectee = true, delta_vertical_cm > 2.0 |
| Format sortie | XML valide, parseable par ElementTree |

### 2.2 INTEL — intel_skeleton.py

| TEST | CRITERE DE SUCCES |
|---|---|
| Appel Claude | Reponse JSON valide (debut { fin }) |
| Champs obligatoires | Tous les champs du contrat INTEL-SKELETON presents |
| corrections_requises | Contient smooth_fcurves, stabilize_hips, remove_foot_slide |
| corrections_optionnelles | Contient mask_limbs et camera_follow |
| Cache | 2e appel sur meme FBX = lecture cache, zero appel API |

### 2.3 INTEL — Merge

| TEST | CRITERE DE SUCCES |
|---|---|
| plan_corrections.json genere | Fichier present dans intel_cache/ |
| Champs merge corrects | person_id, fbx_input, avatar_fbx, fbx_output, corrections_exec remplis |
| Activation conditions | smooth_fcurves.actif = true (jitter detecte) |
| | stabilize_hips.actif = true (derive detectee) |
| | remove_foot_slide.actif = true (foot slide detecte) |

### 2.4 EXEC — Operations

| OPERATION | TEST | CRITERE |
|---|---|---|
| smooth_fcurves | FCurves apres lissage | Variance reduite sur l_hand_JNT, r_hand_JNT |
| stabilize_hips | Hips Y apres correction | Delta vertical < 1.0 cm |
| remove_foot_slide | Pieds au sol apres correction | Delta location pied < seuil_cm |
| camera_follow | Camera presente dans FBX | Camera track sur hips_JNT visible |
| mask_limbs | FCurves membres hors cadre | Freeze a derniere position connue sur plage frames definie |

**mask_limbs — test specifique per-frame :**
- Frame avant frame_debut : animation normale presente
- Frames [frame_debut, frame_fin] : valeur constante egale a la valeur du frame frame_debut - 1
- Frame apres frame_fin : animation reprend normalement
- Pas de saut brusque aux transitions (interpolation lineaire si applicable)

### 2.5 OUTPUT — retarget_r15.py (tous modes)

#### Mode R15

| TEST | CRITERE DE SUCCES |
|---|---|
| Rig R15 construit | 15 bones R15 presents dans l'armature |
| Root bone | LowerTorso est le parent racine |
| Hierarchie correcte | LowerTorso → UpperTorso → Head / Bras / Jambes |
| Rotations transferees | FCurves presentes sur tous les 15 bones R15 |
| Quaternion force | Mode rotation = quaternion sur tous les bones |
| Mesh OSSEUS | Mesh present dans le FBX si --avatar-fbx fourni |
| FBX exportable | Fichier OUT/ferrus_P1.fbx valide (non corrompu) |

#### Mode MIXAMO

| TEST | CRITERE DE SUCCES |
|---|---|
| Bones output | 26 bones Mixamo presents dans l'armature |
| Prefixe | mixamorig: present sur tous les bones |
| Root bone | mixamorig:Hips est la racine |
| Rotations | FCurves presentes sur les 26 bones |
| Quaternion force | rotation_mode = QUATERNION sur tous les bones |
| Mesh OSSEUS | Mesh present dans le FBX si --avatar-fbx fourni |
| FBX importable | Import Blender sans erreur |

#### Mode DEEPMOTION (NOUVEAU)

| TEST | CRITERE DE SUCCES |
|---|---|
| Bones output | 52 bones DeepMotion presents (noms identiques a OSSEUS) |
| FCurves copiees | FCurves de TOUS les bones presents (pas de bone vide) |
| Mesh OSSEUS | Mesh OBLIGATOIREMENT present (pas animation-only) |
| Frames | Meme nombre de frames que le FBX DeepMotion source |
| Quaternion force | rotation_mode = QUATERNION sur tous les bones |
| FBX importable | Import Blender sans erreur |
| Aucun bone from scratch | Le squelette provient de OSSEUS, pas construit en code |

---

## III. TEST DE BOUT EN BOUT

### Procedure

```
1. Deposer le FBX DeepMotion dans IN/
2. Deposer le FBX OSSEUS correspondant dans IN_AVATAR/
3. Choisir BONES_MODE dans Cell 3 du notebook
4. Executer main_ferrus.ipynb sur Colab gratuit
5. Fournir le JSON INTEL-VISION Gemini (via widget ou API)
6. Attendre la fin du pipeline
7. Recuperer les fichiers dans OUT/
```

### Criteres de Succes Global

| CRITERE | VALEUR ATTENDUE |
|---|---|
| Duree totale | < 5 minutes (video 9.4s) |
| Fichier sortie | OUT/ferrus_P1.fbx present avec mesh |
| Rapport | OUT/rapport.json present et valide |
| FBX importable | Import Blender sans erreur |
| Mesh present | Avatar OSSEUS visible dans le FBX output |
| Animation presente | FCurves sur tous les bones du mode choisi |
| Cout | 0 euro |
| Erreurs fatales | 0 |

---

## IV. VALIDATION IMPERIALE

L'Empereur valide le pipeline quand :

1. Le test de bout en bout passe sur le FBX de reference (mode DEEPMOTION en priorite)
2. Le FBX output contient le mesh OSSEUS anime et importable dans Blender sans erreur
3. Les animations sont visuellement correctes (pas de jitter, pieds stables, membres freeze proprement)
4. Le temps total est < 5 minutes
5. Le rapport.json est clair et lisible

---

## V. CAS D'ECHEC ET ESCALADE

| ERREUR | CAUSE PROBABLE | ACTION |
|---|---|---|
| bpy : armature non trouvee | FBX corrompu ou format non supporte | Verifier FBX avec Blender desktop |
| Claude : JSON invalide | Modele a ajoute du markdown | Verifier system prompt, activer fallback |
| Merge : fbx_file mismatch | Nom FBX different entre Gemini et IN/ | Verifier noms des fichiers |
| Foot slide non corrige | Seuil trop eleve | Reduire seuil_cm dans plan_corrections.json |
| Gimbal lock visible | Quaternion non force | Verifier retarget_r15.py forcer_quaternion = true |
| Timeout Colab | Operation trop longue | Reduire intensite smooth_fcurves |
| Mesh absent dans output | --avatar-fbx non passe ou IN_AVATAR/ vide | Verifier Cell 9 notebook + presence FBX OSSEUS |
| Bones DEEPMOTION vides | FCurve copy rate | Verifier noms bones identiques OSSEUS/DeepMotion |
| Saut visuel aux transitions freeze | Pas d'interpolation aux bords de plage | Verifier logique de transition mask_limbs.py |

---

## VI. VALIDATION MODE MIXAMO (AJOUTE 2026-04-24)

### Procedure

```
1. Rigger l'avatar sur mixamo.com (sans doigts)
2. Telecharger en FBX "With Skin" (T-pose)
3. Deposer le FBX avatar dans IN_AVATAR/
4. Dans main_ferrus.ipynb Cell 3 : BONES_MODE = "MIXAMO"
5. Deposer les FBX DeepMotion dans IN/
6. Executer les cellules 2 → 10
7. Recuperer les FBX dans OUT/
```

### Points de Vigilance MIXAMO

| POINT | DESCRIPTION |
|---|---|
| Prefixe | Si l'avatar Mixamo exporte sans prefixe mixamorig:, verifier dans Blender |
| Doigts | ANIMUS ne retargete pas les doigts — bones doigts resteront neutres |
| T-pose | Recommande T-pose pour meilleure qualite de pose repos |

---

## VII. VALIDATION MODE DEEPMOTION (NOUVEAU — 2026-04-24)

### Procedure

```
1. Produire le FBX OSSEUS via FERRUS OSSEUS (squelette 52 bones, T-pose)
2. Deposer dans IN_AVATAR/
3. Deposer le FBX DeepMotion dans IN/
4. Dans main_ferrus.ipynb Cell 3 : BONES_MODE = "DEEPMOTION"
5. Executer les cellules 2 → 10
6. Verifier que le FBX output contient mesh + animation
```

### Criteres de Succes Mode DEEPMOTION

| CRITERE | VALEUR ATTENDUE |
|---|---|
| Bones output | 52 bones (identiques OSSEUS) |
| Mesh present | Avatar OSSEUS visible (pas animation-only) |
| FCurves | Presentes sur tous les 52 bones |
| Frames | Identique au FBX DeepMotion source |
| Pas de deformation | T-pose respectee au frame 0 |
| Root bone | hips_JNT est la racine |

### Points de Vigilance DEEPMOTION

| POINT | DESCRIPTION |
|---|---|
| Noms de bones | OSSEUS et DeepMotion doivent avoir EXACTEMENT les memes noms |
| Scale OSSEUS | Si l'avatar a un scale != 1.0 il faut l'appliquer avant transfert |
| T-pose offset | Si OSSEUS est en A-pose et DeepMotion en T-pose, les offsets de repos peuvent diverger |

---

## VIII. VALIDATION mask_limbs PER-FRAME (NOUVEAU — 2026-04-24)

### Procedure de test

```
1. Preparer un intel_vision.json avec membres_hors_cadre contenant des plages :
   [{"membre": "main_gauche", "frame_debut": 50, "frame_fin": 100}]
2. Executer le pipeline jusqu'a l'etape EXEC
3. Ouvrir le FBX intermediaire dans Blender
4. Inspecter les FCurves de l_hand_JNT
```

### Criteres de Succes mask_limbs per-frame

| CRITERE | VALEUR ATTENDUE |
|---|---|
| Frames [0, 49] | FCurves normales, animation DeepMotion presente |
| Frame 49 | Derniere valeur "normale" avant freeze |
| Frames [50, 100] | Valeur constante = valeur du frame 49 |
| Frame 101+ | FCurves normales, animation DeepMotion reprend |
| Transition entree (frame 50) | Pas de saut brusque |
| Transition sortie (frame 101) | Pas de saut brusque |
