# CORPUS_ROADMAP.md — Plan de Conquete
# FREGATE 02 : FERRUS CORPUS
# Version : 2.0 | Date : 2026-04-26 | Statut : ACTIF (REFONTE)

---

## Phases de Conquete

```
Phase 1 : ANALYSE FORENSIQUE      [TERMINE]
Phase 2 : PHYLACTERE               [TERMINE]
Phase 3 : BIBLE TECHNIQUE          [TERMINE - REFONTE v2.0]
Phase 4 : PLAN DE CONQUETE         [TERMINE]
Phase 5 : DEVELOPPEMENT DIVIN      [A VENIR]
```

---

## PHASE 5 — DEVELOPPEMENT DIVIN

### Checkpoint 1 — convert_to_blend.py (CORE)

- [ ] Scaffolding du script (args parsing, logging)
- [ ] Detection format source (FBX vs GLB)
- [ ] Import FBX via bpy.ops.import_scene.fbx()
- [ ] Import GLB via bpy.ops.import_scene.gltf()
- [ ] Export .blend via bpy.ops.wm.save_as_mainfile()
- [ ] Rapport JSON par fichier (format, taille, statut)
- [ ] Test unitaire sur ferrus_P1.fbx

### Checkpoint 2 — corpus_main.ipynb (NOTEBOOK)

- [ ] Cellule SETUP (Drive, chemins, Blender path)
- [ ] Cellule CONFIG (liste FBX/GLB dans IN/)
- [ ] Cellule CONVERSION (boucle N fichiers, appel Blender headless)
- [ ] Cellule RAPPORT (lecture + affichage rapport_corpus.json)

### Checkpoint 3 — NETTOYAGE

- [ ] Supprimer inject_animation.py (remplace par convert_to_blend.py)
- [ ] Supprimer dossier IN_AVATAR/ (plus requis)
- [ ] Mise a jour CORPUS_STATE.md → OPERATIONNELLE

### Checkpoint 4 — LIVRAISON

- [ ] Push GitHub (codebase/ + docs/ mis a jour)
- [ ] CORPUS_STATE.md : statut → OPERATIONNELLE
- [ ] README.md principal FLOTTE-FERRUS mis a jour

---

## Tableau de Bord

| Checkpoint | Statut | Date |
|---|---|---|
| Fondation + Docs v1 | TERMINE | 2026-04-18 |
| Refonte docs v2.0 | TERMINE | 2026-04-26 |
| convert_to_blend.py | A FAIRE | - |
| corpus_main.ipynb | A FAIRE | - |
| Nettoyage anciens fichiers | A FAIRE | - |
| Livraison | A FAIRE | - |

---

## Complexite Estimee

| Module | Complexite | Justification |
|---|---|---|
| convert_to_blend.py | TRES FAIBLE | Import Blender + save — 3 appels bpy |
| corpus_main.ipynb | TRES FAIBLE | 4 cellules, logique lineaire |
| Nettoyage | TRES FAIBLE | Suppression de fichiers obsoletes |

**Temps total estime : 1 session courte**

---

*POUR L'EMPEROR. POUR LA FLOTTE FERRUS.*
