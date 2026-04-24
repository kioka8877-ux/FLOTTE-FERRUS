# FERRUS_VALIDATION.md — Protocole de Test
# FREGATE 01 : FERRUS ANIMUS
# Version : 1.0 | Date : 2026-04-17

---

## I. FICHIER DE REFERENCE

| CHAMP | VALEUR |
|---|---|
| Fichier | WhatsApp_Video_2026-04-12...(includeTPose).fbx |
| Taille | 2.9 MB |
| Format | FBX 7.7 Binary |
| Source | DeepMotion server (/dmbt-e2e-cli/) |
| Base model | female-normal |
| Bones | 52 (22 core + 30 doigts) |
| Duree | 9.4s (282 frames @ 30fps) |
| Defauts connus | jitter (mains + tete), foot slide, derive hanches |

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
| Champs merge corrects | person_id, fbx_input, fbx_output, corrections_exec remplis |
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
| mask_limbs | FCurves membres masques | Scale = 0 sur bones cibles |

### 2.5 OUTPUT — retarget_r15.py

| TEST | CRITERE DE SUCCES |
|---|---|
| Rig R15 construit | 15 bones R15 presents dans l'armature |
| Root bone | LowerTorso est le parent racine |
| Hierarchie correcte | LowerTorso → UpperTorso → Head / Bras / Jambes |
| Rotations transferees | FCurves presentes sur tous les 15 bones R15 |
| Quaternion force | Mode rotation = quaternion sur tous les bones |
| FBX exportable | Fichier OUT/ferrus_P1.fbx valide (non corrompu) |

---

## III. TEST DE BOUT EN BOUT

### Procedure

```
1. Deposer le FBX de reference dans IN/
2. Executer main_ferrus.ipynb sur Colab gratuit
3. Fournir le JSON INTEL-VISION Gemini (via widget ou API)
4. Attendre la fin du pipeline
5. Recuperer les fichiers dans OUT/
```

### Criteres de Succes Global

| CRITERE | VALEUR ATTENDUE |
|---|---|
| Duree totale | < 5 minutes (video 9.4s) |
| Fichier sortie | OUT/ferrus_P1.fbx present |
| Rapport | OUT/rapport.json present et valide |
| FBX importable | Import Blender sans erreur |
| Bones R15 | 15 bones present dans l'armature exportee |
| Cout | 0 euro |
| Erreurs fatales | 0 |

---

## IV. VALIDATION IMPERIALE

L'Empereur valide le pipeline quand :

1. Le test de bout en bout passe sur le FBX de reference
2. Le FBX R15 de sortie est importable dans Roblox Studio sans manipulation
3. Les animations sont visuellement correctes (pas de jitter, pieds stables)
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


---

## VI. VALIDATION MODE MIXAMO (AJOUTE 2026-04-24)

### Procedure

```
1. Rigger l'avatar sur mixamo.com (sans doigts)
2. Telecharger en FBX "With Skin" (T-pose ou A-pose)
3. Deposer le FBX avatar dans CORPUS IN_AVATAR/ (a venir)
4. Dans main_ferrus.ipynb Cell 3 : RETARGET_MODE = "MIXAMO"
5. Deposer les FBX DeepMotion dans IN/
6. Executer les cellules 2 → 10
7. Recuperer les FBX Mixamo dans OUT/
```

### Criteres de Succes Mode MIXAMO

| CRITERE | VALEUR ATTENDUE |
|---|---|
| Bones output | 22 bones Mixamo presents dans l'armature |
| Prefixe | `mixamorig:` present sur tous les bones |
| Root bone | `mixamorig:Hips` est la racine |
| Rotations | FCurves presentes sur les 22 bones |
| Quaternion force | rotation_mode = QUATERNION sur tous les bones |
| FBX importable | Import Blender sans erreur |
| Frames | Meme nombre de frames que le FBX DeepMotion source |

### Points de Vigilance MIXAMO

| POINT | DESCRIPTION |
|---|---|
| Prefixe | Si l'avatar Mixamo exporte sans prefixe `mixamorig:`, les noms ne correspondront pas — verifier dans Blender |
| Doigts | ANIMUS ne retargete pas les doigts (pas dans DeepMotion) — bones doigts Mixamo resteront neutres |
| T-pose | Recommande T-pose pour le download Mixamo (meilleure qualite de pose repos) |
