# FORGE_ROADMAP.md — Plan de Conquete
# FREGATE 00 : FERRUS FORGE
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

### Checkpoint 1 — forge_convert.py (CORE)

- [ ] Scaffolding du script (args parsing, logging)
- [ ] Scene vide : `bpy.ops.wm.read_factory_settings(use_empty=True)`
- [ ] Detection format par extension (lower case)
- [ ] Importeur .glb / .gltf : `bpy.ops.import_scene.gltf()`
- [ ] Importeur .obj : `bpy.ops.import_scene.obj()`
- [ ] Importeur .fbx : `bpy.ops.import_scene.fbx()`
- [ ] Nettoyage scene : purge camera, lights, orphans
- [ ] Validation armature : detection + warning si absente
- [ ] Validation bones R15 : check noms + warning si non conformes
- [ ] Export .blend : `bpy.ops.wm.save_as_mainfile()`
- [ ] Rapport JSON individuel (format, armature, status, warnings)
- [ ] Test unitaire sur avatar_P1.glb

### Checkpoint 2 — forge_main.ipynb (NOTEBOOK)

- [ ] Cellule 0 : GIT SYNC (Drive, clone/pull, copie codebase)
- [ ] Cellule 1 : SETUP (Blender path, chemins Drive)
- [ ] Cellule 2 : CONFIG (liste avatars IN/, validation nommage)
- [ ] Cellule 3 : CONVERSION (boucle N avatars, appel Blender headless)
- [ ] Cellule 4 : RAPPORT (lecture + affichage rapport_forge.json)

### Checkpoint 3 — VALIDATION

- [ ] Test format .glb (1 avatar → 1 .blend)
- [ ] Test format .obj (1 avatar → 1 .blend)
- [ ] Test format .fbx (1 avatar → 1 .blend)
- [ ] Test multi-acteurs (P1 + P2 + P3, formats mixtes)
- [ ] Test avatar sans armature (warning attendu, pas d'echec)
- [ ] Test nommage miroir : avatar_P1.glb → avatar_P1.blend
- [ ] Verification .blend importable dans FERRUS CORPUS
- [ ] rapport_forge.json valide (structure JSON correcte)
- [ ] Mise a jour FORGE_STATE.md

### Checkpoint 4 — LIVRAISON

- [ ] Push GitHub (codebase/ + docs/ mis a jour)
- [ ] FORGE_STATE.md : statut → OPERATIONNELLE
- [ ] README.md principal FLOTTE-FERRUS mis a jour (Fregate 00 operationnelle)

---

## Tableau de Bord

| Checkpoint | Statut | Date |
|---|---|---|
| Fondation + Docs | TERMINE | 2026-04-18 |
| forge_convert.py | A FAIRE | - |
| forge_main.ipynb | A FAIRE | - |
| Validation production | A FAIRE | - |
| Livraison | A FAIRE | - |

---

## Complexite Estimee

| Module | Complexite | Justification |
|---|---|---|
| forge_convert.py | TRES FAIBLE | Conversion pure, importeurs natifs bpy |
| forge_main.ipynb | TRES FAIBLE | Pattern identique a CORPUS (copier-adapter) |
| Validation | TRES FAIBLE | Tests simples par format |

**Temps total estime : 1 session (< 2h)**

---

*POUR L'EMPEROR. POUR LA FLOTTE FERRUS.*
