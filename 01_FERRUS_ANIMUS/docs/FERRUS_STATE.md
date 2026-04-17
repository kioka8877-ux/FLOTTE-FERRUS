# FERRUS_STATE.md — Phylactere de Resurrection
# FREGATE 01 : FERRUS ANIMUS
# Derniere mise a jour : 2026-04-17 (session architecture INTEL validee)

---

[STATUS] : EN_COURS — Phase 5 Developpement Divin

[LAST_WORK] :
- Brainstorming de fondation complete (Codex Mechanicus Tome I valide)
- Analyse forensique executee (Q-01, Q-02, Q-03 — FERMES)
- Meta-prompts INTEL finalises (INTEL-VISION Gemini + INTEL-SKELETON Claude)
- Depot GitHub kioka8877-ux/FLOTTE-FERRUS cree et structure
- Documents FERRUS (STATE, PRD, ROADMAP, VALIDATION) rediges
- Module INTEL developpe : pre_parse_fbx.py + intel_skeleton.py
- Session architecture INTEL : modes Chat valides, contrats JSON confirmes

[NEXT_TASK] : Developpement EXEC — remove_foot_slide.py (Operation 3)

[BLOCKERS] : Aucun

[SOLUTIONS] : -

[LINKS] :
- Depot GitHub : https://github.com/kioka8877-ux/FLOTTE-FERRUS
- Meta-prompt INTEL-VISION (Gemini) : FERRUS_INTEL_VISION_GEMINI_METAPROMPT.md
- Meta-prompt INTEL-SKELETON (Claude) : FERRUS_INTEL_SKELETON_CLAUDE_METAPROMPT.md
- FBX de reference : WhatsApp_Video_2026-04-12...(includeTPose).fbx | 2.9 MB | FBX 7.7 Binary

---

## Etat des Compartiments

| COMPARTIMENT | MODULE | STATUT |
|---|---|---|
| INTEL | pre_parse_fbx.py | TERMINE |
| INTEL | intel_skeleton.py | TERMINE |
| INTEL | prompts/correction_prompt.txt | PLACEHOLDER |
| EXEC | smooth_fcurves.py | TERMINE |
| EXEC | stabilize_hips.py | TERMINE |
| EXEC | remove_foot_slide.py | EN ATTENTE |
| EXEC | camera_follow.py | EN ATTENTE |
| EXEC | mask_limbs.py | EN ATTENTE |
| OUTPUT | retarget_r15.py | EN ATTENTE |
| PIPELINE | main_ferrus.ipynb | EN ATTENTE |

---

## Decisions Imperiales Actives

- DeepMotion produit 1 FBX par personne (Option C : traitement sequentiel)
- Rig R15 construit programmatiquement — ZERO fichier GLB requis
- INTEL double tete : Gemini (video) + Claude API (FBX) → merge → plan_corrections.json
- Rotations en quaternion forces au retargeting (prevenir gimbal lock)
- Cache JSON par fichier FBX (zero retokenisation si deja analyse)

## Decisions Validees — Session 2026-04-17

- MODE INTEL CHAT VALIDE : Gemini Chat + video.mp4 → intel_vision.json (copie manuelle Colab)
- MODE INTEL CHAT VALIDE : Claude Chat + FBX brut (≤ 20 Mo) → intel_skeleton.json (copie manuelle Colab)
- VERROU JSON = qualite du metaprompt (FORMAT EXACT ATTENDU + enums + champs requis)
- Les deux metaprompts (INTEL-VISION + INTEL-SKELETON) constituent le double verrou JSON de la flotte
- intel_skeleton.py reste valide pour le mode API (chemin alternatif automatise)
- Deux modes d'entree pour Claude : FBX brut (chat) ou XML pre-parse (API via intel_skeleton.py) — meme contrat de sortie
