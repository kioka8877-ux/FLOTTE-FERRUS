# CORPUS_ROADMAP.md — Plan de Conquete
# FREGATE 02 : FERRUS CORPUS
# Version : 1.0 | Date : 2026-04-18 | Statut : ACTIF

---

## Phases de Conquete

```
Phase 1 : ANALYSE FORENSIQUE      [TERMINE]
Phase 2 : PHYLACTERE               [TERMINE]
Phase 3 : BIBLE TECHNIQUE          [TERMINE]
Phase 4 : PLAN DE CONQUETE         [EN COURS]
Phase 5 : DEVELOPPEMENT DIVIN      [A VENIR]
```

---

## PHASE 5 — DEVELOPPEMENT DIVIN

### Checkpoint 1 — inject_animation.py (CORE)

- [ ] Scaffolding du script (args parsing, logging)
- [ ] Chargement avatar_r15.blend via bpy
- [ ] Import FBX Ferrus → armature temporaire
- [ ] Extraction de l'Action depuis l'armature FBX
- [ ] Assignation de l'Action a l'armature avatar
- [ ] Export .blend (save_as_mainfile)
- [ ] Export .glb (export_scene.gltf)
- [ ] Rapport JSON par acteur (bones, frames, status)
- [ ] Test unitaire sur ferrus_P1.fbx

### Checkpoint 2 — corpus_main.ipynb (NOTEBOOK)

- [ ] Cellule SETUP (Drive, chemins, Blender path)
- [ ] Cellule CONFIG (liste FBX IN/, validation avatar)
- [ ] Cellule INCARNATION (boucle N acteurs, appel Blender headless)
- [ ] Cellule RAPPORT (lecture + affichage rapport_corpus.json)
- [ ] Cellule PREVIEW (taille .glb, checksum, lien viewer)

### Checkpoint 3 — VALIDATION

- [ ] Test P1 seul (1 FBX → 1 blend + 1 glb)
- [ ] Test P1 + P2 (2 FBX → 2 blend + 2 glb, rapport global)
- [ ] Verification .glb dans viewer en ligne
- [ ] Verification .blend importable dans EXODUS U01
- [ ] Rapport corpus.json valide (structure JSON correcte)
- [ ] Mise a jour CORPUS_STATE.md

### Checkpoint 4 — LIVRAISON

- [ ] Push GitHub (codebase/ + docs/ mis a jour)
- [ ] CORPUS_STATE.md : statut → OPERATIONNELLE
- [ ] README.md principal FLOTTE-FERRUS mis a jour (Fregate 02 operationnelle)

---

## Tableau de Bord

| Checkpoint | Statut | Date |
|---|---|---|
| Fondation + Docs | TERMINE | 2026-04-18 |
| inject_animation.py | A FAIRE | - |
| corpus_main.ipynb | A FAIRE | - |
| Validation production | A FAIRE | - |
| Livraison | A FAIRE | - |

---

## Complexite Estimee

| Module | Complexite | Justification |
|---|---|---|
| inject_animation.py | FAIBLE | Transfert direct R15→R15, bpy standard |
| corpus_main.ipynb | TRES FAIBLE | 5 cellules, logique lineaire |
| Validation | FAIBLE | 2 FBX Ferrus deja valides |

**Temps total estime : 1 session Colab**

---

*POUR L'EMPEROR. POUR LA FLOTTE FERRUS.*
