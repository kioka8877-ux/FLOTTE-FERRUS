# FERRUS_ROADMAP.md — Plan de Conquete
# FREGATE 01 : FERRUS ANIMUS
# Version : 1.0 | Date : 2026-04-17

---

## PHASE 0 — FONDATIONS (TERMINE)

- [x] Brainstorming de fondation (Codex Mechanicus Tome I)
- [x] Analyse forensique FBX DeepMotion (Q-01, Q-02, Q-03 fermes)
- [x] Rapport forensique squelette 52 bones + mapping R15 valide
- [x] Meta-prompts INTEL finalises (INTEL-VISION + INTEL-SKELETON)
- [x] Depot GitHub structure et pousse
- [x] Documents FERRUS rediges (STATE, PRD, ROADMAP, VALIDATION)

---

## PHASE 1 — COMPARTIMENT INTEL (EN COURS)

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
- [ ] Fonction merge_intel() : intel_vision + intel_skeleton → plan_corrections.json
- [ ] Logique d'activation conditionnelle des corrections EXEC
- [ ] Injection membres_hors_cadre → mask_limbs
- [ ] Injection jitter_bones → smooth_fcurves.bones_cibles

---

## PHASE 2 — COMPARTIMENT EXEC

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
- [ ] Detection frames ou pied au sol (Y < seuil)
- [ ] Blocage position pied sur ces frames
- [ ] Parametres : pied_gauche, pied_droit, seuil_cm

### 2.4 camera_follow.py
- [ ] Creation camera Blender
- [ ] Suivi de la cible (lock / smooth_follow / static)
- [ ] Export camera dans FBX de sortie

### 2.5 mask_limbs.py
- [ ] Lecture membres_a_masquer
- [ ] Neutralisation des FCurves des membres hors cadre
- [ ] Zero-out rotation + scale sur bones cibles

---

## PHASE 3 — COMPARTIMENT OUTPUT

### 3.1 retarget_r15.py
- [ ] Construction du rig R15 programmatique (15 bones, zero GLB)
- [ ] Hierarchie R15 : LowerTorso (root) → UpperTorso → Head / Bras / Jambes
- [ ] Transfert des rotations DeepMotion → R15 (quaternion force)
- [ ] Application root_position sur LowerTorso
- [ ] Bones ignores : doigts, shoulder, toebase, neck
- [ ] Export FBX R15 final

---

## PHASE 4 — NOTEBOOK COLAB D'ASSEMBLAGE

- [ ] main_ferrus.ipynb : notebook principal
- [ ] Cellule SETUP : montage Drive, installation Blender, venv
- [ ] Cellule INTEL : pre-parse FBX + analyse Claude + injection JSON Gemini
- [ ] Cellule EXEC : execution des 5 operations (ordre : smooth → hips → foot → mask → camera)
- [ ] Cellule OUTPUT : retargeting R15
- [ ] Cellule RAPPORT : generation rapport.json + affichage resume
- [ ] Widget injection JSON Gemini (sans API key)
- [ ] Gestion multi-personnes (scan IN/, manifest.json, traitement sequentiel)

---

## PHASE 5 — VALIDATION ET LIVRAISON

- [ ] Test bout en bout sur FBX de reference (WhatsApp_Video_2026-04-12)
- [ ] Verification : squelette R15 15 bones present dans output
- [ ] Verification : duree < 5 minutes
- [ ] Verification : rapport.json genere et coherent
- [ ] Verification : FBX R15 importable dans Roblox Studio
- [ ] Validation imperiale

---

## Dependances Critiques

```
Phase 1 (INTEL) → must be done before Phase 2 (EXEC)
Phase 2 (EXEC)  → must be done before Phase 3 (OUTPUT)
Phase 3 (OUTPUT) → must be done before Phase 4 (Notebook)
Phase 4 (Notebook) → must be done before Phase 5 (Validation)
```

## Temps Estime par Phase

| PHASE | ESTIMATION |
|---|---|
| Phase 1 — INTEL | 2-3h |
| Phase 2 — EXEC | 3-4h |
| Phase 3 — OUTPUT | 2-3h |
| Phase 4 — Notebook | 1-2h |
| Phase 5 — Validation | 1h |
