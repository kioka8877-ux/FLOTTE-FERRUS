# FERRUS_ROADMAP.md — Plan de Conquete
# FREGATE 01 : FERRUS ANIMUS
# Version : 2.0 | Date : 2026-04-24

---

## PHASE 0 — FONDATIONS (TERMINE)

- [x] Brainstorming de fondation (Codex Mechanicus Tome I)
- [x] Analyse forensique FBX DeepMotion (Q-01, Q-02, Q-03 fermes)
- [x] Rapport forensique squelette 52 bones + mapping R15 valide
- [x] Meta-prompts INTEL finalises (INTEL-VISION + INTEL-SKELETON)
- [x] Depot GitHub structure et pousse
- [x] Documents FERRUS rediges (STATE, PRD, ROADMAP, VALIDATION)

---

## PHASE 1 — COMPARTIMENT INTEL (TERMINE)

### 1.1 Module pre_parse_fbx.py
- [x] Extraction squelette (hierarchie bones, parent/enfant)
- [x] Detection animation (take name, frames, fps, duree)
- [x] Detection rotation mode (euler / quaternion)
- [x] Detection jitter (variance FCurves mains + tete)
- [x] Detection foot slide (delta location pieds)
- [x] Detection derive hanches (delta Y hips_JNT)
- [x] Export XML structure pour Claude

### 1.2 Module intel_skeleton.py
- [x] Appel API Claude (claude-sonnet-4-6)
- [x] Validation JSON retourne
- [x] Cache par nom de fichier FBX
- [x] Fallback si ANTHROPIC_API_KEY absent

### 1.3 Merge INTEL
- [x] Fonction merge_intel() : intel_vision + intel_skeleton → plan_corrections.json
- [x] Logique d'activation conditionnelle des corrections EXEC
- [x] Injection membres_hors_cadre → mask_limbs
- [x] Injection jitter_bones → smooth_fcurves.bones_cibles

---

## PHASE 2 — COMPARTIMENT EXEC (TERMINE sauf mask_limbs en refactorisation)

### 2.1 smooth_fcurves.py
- [x] Lecture plan_corrections.json
- [x] Lissage FCurves sur bones_cibles (Gaussian smoothing bpy)
- [x] Parametre intensite (0.0 → 1.0) — kernel 3/5/7/9/11 + sigma adapte
- [x] Sauvegarde FBX intermediaire
- [x] Mode skip si enabled=false (copie directe)
- [x] Rapport de sortie (bones_lisses, keyframes_modifies, kernel_size)

### 2.2 stabilize_hips.py
- [x] Detection derive verticale hips_JNT (moindres carres, tendance lineaire)
- [x] Correction par detrending lineaire (offset progressif, premier frame preserve)
- [x] Parametre correction_verticale_cm
- [x] Mode skip si stable ou FCurve absente
- [x] Rapport de sortie (direction, delta_detecte_cm, keyframes_corriges)

### 2.3 remove_foot_slide.py
- [x] Detection frames ou pied au sol (Y < seuil)
- [x] Blocage position pied sur ces frames
- [x] Parametres : pied_gauche, pied_droit, seuil_cm

### 2.4 camera_follow.py
- [x] Creation camera Blender
- [x] Suivi de la cible (lock / smooth_follow / static)
- [x] Export camera dans FBX de sortie

### 2.5 mask_limbs.py (EN REFACTORISATION)
- [x] Lecture membres_a_masquer
- [x] Neutralisation des FCurves des membres hors cadre (masquage global — A REMPLACER)
- [ ] Lecture plages frames : {membre, frame_debut, frame_fin}
- [ ] Freeze a la derniere position connue avant frame_debut (Option A)
- [ ] Interpolation lineaire aux transitions entree/sortie de plage
- [ ] Reprise animation normale apres frame_fin

---

## PHASE 3 — COMPARTIMENT OUTPUT (EN REFACTORISATION)

### 3.1 retarget_r15.py — mode R15
- [x] Construction du rig R15 programmatique (15 bones, zero GLB)
- [x] Hierarchie R15 : LowerTorso (root) → UpperTorso → Head / Bras / Jambes
- [x] Transfert des rotations DeepMotion → R15 (quaternion force)
- [x] Application root_position sur LowerTorso
- [x] Bones ignores : doigts, shoulder, toebase, neck
- [x] Export FBX R15 final
- [ ] Injection mesh OSSEUS si --avatar-fbx fourni

### 3.2 retarget_r15.py — mode MIXAMO
- [x] Mapping DeepMotion 52 bones → Mixamo 26 bones
- [x] Hierarchie Mixamo avec prefixe mixamorig:
- [x] Detection automatique du prefixe
- [x] Rig Mixamo programmatique
- [x] Parametre --mode MIXAMO
- [ ] Injection mesh OSSEUS si --avatar-fbx fourni
- [ ] Validation en production avec avatar rige Mixamo

### 3.3 retarget_r15.py — mode DEEPMOTION (NOUVEAU)
- [ ] Charger FBX OSSEUS (mesh + squelette T-pose 52 bones)
- [ ] Charger FBX DeepMotion corrige (animation 52 bones)
- [ ] Copier FCurves directement (memes noms de bones — trivial)
- [ ] Exporter FBX avec mesh OSSEUS anime
- [ ] Parametre --mode DEEPMOTION

---

## PHASE 4 — NOTEBOOK COLAB D'ASSEMBLAGE (EN REFACTORISATION)

- [x] main_ferrus.ipynb : notebook principal (10 cellules)
- [x] Cellule SETUP : montage Drive, installation Blender, helpers
- [x] Cellule INTEL : pre-parse FBX + analyse Claude + fallback statique
- [x] Cellule MERGE : merge_intel() → plan_corrections.json
- [x] Cellule EXEC : execution des 5 operations
- [x] Cellule OUTPUT : retargeting (R15/Mixamo)
- [x] Cellule RAPPORT : generation rapport.json
- [x] Widget injection JSON Gemini
- [x] Gestion multi-personnes (manifest.json, traitement sequentiel)
- [ ] Cell 2 SETUP : creer IN_AVATAR/ au montage
- [ ] Cell 3 CONFIG : renommer RETARGET_MODE → BONES_MODE, ajouter option "DEEPMOTION"
- [ ] Cell 4 SCAN : scanner IN_AVATAR/, matcher avatars, ajouter avatar_fbx dans manifest
- [ ] Cell 9 OUTPUT : passer --avatar-fbx et --mode BONES_MODE a retarget_r15.py

---

## PHASE 5 — VALIDATION ET LIVRAISON (EN ATTENTE)

- [ ] Test bout en bout mode DEEPMOTION (DeepMotion -> OSSEUS 52 bones)
- [ ] Test bout en bout mode R15 (regression — doit marcher comme avant)
- [ ] Test bout en bout mode MIXAMO
- [ ] Verification : FBX output contient mesh OSSEUS anime
- [ ] Verification : duree < 5 minutes
- [ ] Verification : rapport.json genere et coherent
- [ ] Validation imperiale

---

## PHASE 6 — CORPUS — ADAPTATION BONES_MODE (EN ATTENTE)

- [ ] CORPUS : ajout support bones Mixamo (noms mixamorig:*)
- [ ] CORPUS : ajout support bones DEEPMOTION 52
- [ ] CORPUS : selecteur BONES_MODE synchronise avec ANIMUS

---

## PHASE 7 — REFACTORISATION ARCHITECTURALE (EN COURS)

Declenchee le 2026-04-24 suite a detection du bug de conception.

### 7.1 Docs de suivi (TERMINE)
- [x] Brainstorming architectural — vision ANIMUS correcte definie
- [x] Inventaire des modifications necessaires etabli
- [x] FERRUS_PRD.md v2.0 mis a jour
- [x] FERRUS_STATE.md mis a jour
- [x] FERRUS_ROADMAP.md v2.0 mis a jour
- [x] FERRUS_VALIDATION.md mis a jour (Section VII)
- [x] FERRUS_INTEL_VISION_GEMINI_METAPROMPT.md mis a jour (plages frames)

### 7.2 Code — EXEC (A FAIRE)
- [ ] mask_limbs.py : per-frame freeze (Option A)

### 7.3 Code — OUTPUT (A FAIRE)
- [ ] retarget_r15.py : mode DEEPMOTION (52->52 + mesh)
- [ ] retarget_r15.py : injection mesh R15/Mixamo via --avatar-fbx

### 7.4 Code — Notebook (A FAIRE)
- [ ] main_ferrus.ipynb : Cells 2/3/4/9

### 7.5 Infrastructure (A FAIRE)
- [ ] Creer dossier IN_AVATAR/ avec .gitkeep

---

## Dependances Critiques

```
Phase 7.1 (Docs)     → TERMINE
Phase 7.2 (EXEC)     → peut commencer maintenant
Phase 7.3 (OUTPUT)   → peut commencer maintenant (independant de 7.2)
Phase 7.4 (Notebook) → apres 7.2 et 7.3
Phase 5 (Validation) → apres Phase 7 complete
```
