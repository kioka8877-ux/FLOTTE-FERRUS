# FERRUS_STATE.md — Phylactere de Resurrection
# FREGATE 01 : FERRUS ANIMUS
# Derniere mise a jour : 2026-04-24 (MODE MIXAMO AJOUTE)

---

[STATUS] : OPERATIONNELLE — Mode MIXAMO ajoute, validation en production requise

[LAST_WORK] :
- Brainstorming de fondation complete (Codex Mechanicus Tome I valide)
- Analyse forensique executee (Q-01, Q-02, Q-03 — FERMES)
- Meta-prompts INTEL finalises (INTEL-VISION Gemini + INTEL-SKELETON Claude)
- Depot GitHub kioka8877-ux/FLOTTE-FERRUS cree et structure
- Documents FERRUS (STATE, PRD, ROADMAP, VALIDATION) rediges
- Module INTEL developpe : pre_parse_fbx.py + intel_skeleton.py
- Session architecture INTEL : modes Chat valides, contrats JSON confirmes
- EXEC Op.1-5 livrees et operationnelles
- OUTPUT livree : retarget_r15.py — rig R15 programmatique, matrix_basis quaternion, export selection
- PIPELINE livre : main_ferrus.ipynb — 10 cellules, orchestration complete INTEL->EXEC->OUTPUT->RAPPORT
- Validation en production reussie (2026-04-17)
- SESSION 2026-04-24 : ajout mode MIXAMO (22 bones Mixamo.com) dans retarget_r15.py
- SESSION 2026-04-24 : ajout selecteur RETARGET_MODE dans main_ferrus.ipynb (Cell 3 CONFIG)

[NEXT_TASK] : Validation MIXAMO en production avec un FBX avatar rige par Mixamo.com

[STATUS] : PRET_POUR_VALIDATION_MIXAMO

[BLOCKERS] : Aucun

[SOLUTIONS] : -

[LINKS] :
- Depot GitHub : https://github.com/kioka8877-ux/FLOTTE-FERRUS
- Meta-prompt INTEL-VISION (Gemini) : FERRUS_INTEL_VISION_GEMINI_METAPROMPT.md
- Meta-prompt INTEL-SKELETON (Claude) : FERRUS_INTEL_SKELETON_CLAUDE_METAPROMPT.md

---

## Etat des Compartiments

| COMPARTIMENT | MODULE | STATUT |
|---|---|---|
| INTEL | pre_parse_fbx.py | TERMINE |
| INTEL | intel_skeleton.py | TERMINE |
| INTEL | prompts/correction_prompt.txt | PLACEHOLDER |
| EXEC | smooth_fcurves.py | TERMINE |
| EXEC | stabilize_hips.py | TERMINE |
| EXEC | remove_foot_slide.py | TERMINE |
| EXEC | camera_follow.py | TERMINE |
| EXEC | mask_limbs.py | TERMINE |
| OUTPUT | retarget_r15.py — mode R15 | VALIDE EN PRODUCTION |
| OUTPUT | retarget_r15.py — mode MIXAMO | IMPLEMENTE — VALIDATION REQUISE |
| PIPELINE | main_ferrus.ipynb | TERMINE |

---

## Decisions Imperiales Actives

- DeepMotion produit 1 FBX par personne (Option C : traitement sequentiel)
- Rig cible construit programmatiquement — ZERO fichier GLB requis (R15 et Mixamo)
- INTEL double tete : Gemini (video) + Claude API (FBX) -> merge -> plan_corrections.json
- Rotations en quaternion forces au retargeting (prevenir gimbal lock)
- Cache JSON par fichier FBX (zero retokenisation si deja analyse)
- RETARGET_MODE = "R15" ou "MIXAMO" — choix dans Cell 3 du notebook

## Historique des Sessions

| Date | Evenement |
|---|---|
| 2026-04-17 | Pipeline complet livre et valide en production (R15) |
| 2026-04-24 | Ajout mode MIXAMO 22 bones — retarget_r15.py + notebook |
