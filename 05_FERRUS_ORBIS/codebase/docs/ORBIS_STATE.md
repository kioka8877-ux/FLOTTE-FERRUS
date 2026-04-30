# ORBIS_STATE.md — Phylactere de Resurrection
# FREGATE 05 : FERRUS ORBIS
# Derniere mise a jour : 2026-04-30 (VALIDATION IMPERIALE MODE STUDIO_OBJ)

---

[STATUS] : OPERATIONNELLE — Validation imperiale 2026-04-30

[LAST_WORK] :
- Decision imperiale : creation Fregate 05 FERRUS ORBIS (2026-04-26)
- orbis_fetch.py livre : extraction HTTP API Roblox (mode METADATA)
- orbis_core.py livre : pipeline Blender headless (mode METADATA)
- orbis_main.ipynb livre : 7 cellules completes
- Decision architecturale : ajout MODE STUDIO_OBJ (2026-04-30)
  → Contexte : API Roblox assetdelivery retourne uniquement geometrie primitive
  → Roblox Studio exporte la map complete avec interieurs + textures natives
  → ORBIS reprend en aval : import → nettoyage → join → double face → GLB
- orbis_core.py mis a jour : mode STUDIO_OBJ + support .glb/.gltf/.obj/.fbx
- orbis_main.ipynb mis a jour : Cell 02 detection auto .glb/.obj/.fbx dans IN/, Cell 03 skip, Cell 04 branching
- VALIDATION IMPERIALE mode STUDIO_OBJ (2026-04-30) :
  → map.glb importe : 604 objets, 174 mesh
  → Mesh unifie : 258,064 vertices | 397,110 faces
  → 41 materiaux double face
  → GLB produit : 16.47 Mo en 4.1 secondes
  → Pipeline complet bout-en-bout confirme

[NEXT_TASK] : Aucun — Fregate operationnelle

[STATUS] : OPERATIONNELLE

[BLOCKERS] : Aucun

[SOLUTIONS] : -

[LINKS] :
- Depot GitHub : https://github.com/kioka8877-ux/FLOTTE-FERRUS
- Fregate aval (personnages) : 01_FERRUS_ANIMUS/OUT/
- Fregate aval (rendu) : FERRUS EXODUS (futur)

---

## Etat des Compartiments

| COMPARTIMENT | MODULE | STATUT |
|---|---|---|
| EXTRACTION HTTP | orbis_fetch.py | LIVRE |
| IMPORT STUDIO | orbis_core.py — op_import_studio_file() | LIVRE |
| NETTOYAGE | orbis_core.py — op_clean_scene() | LIVRE |
| JOIN + DOUBLE FACE | orbis_core.py — op_join_and_double_face() | LIVRE |
| SEAL | orbis_core.py — op_seal_export() | LIVRE |
| PIPELINE | orbis_main.ipynb | LIVRE |
| DOCS | ORBIS_STATE.md | A JOUR |
| DOCS | ORBIS_PRD.md | TERMINE |
| DOCS | ORBIS_ROADMAP.md | TERMINE |
| DOCS | ORBIS_VALIDATION.md | TERMINE |
| INFRA | IN/ OUT/ | TERMINE |
| VALIDATION | Test bout-en-bout STUDIO_OBJ | VALIDE 2026-04-30 |

---

## Decisions Imperiales Actives

- ORBIS est agnostique a la source : keyword OU asset ID direct, les deux valides
- Input unique : string (keyword ou asset ID Roblox)
- Output unique : decor_XXXX.glb + rapport_orbis.json
- Double face ON obligatoire (mat.use_backface_culling = False) — accessible de l'interieur
- Scripts / Colliders / Lights Roblox supprimes avant export
- Stack : Python requests + xml.etree.ElementTree + bpy headless, CPU, Colab gratuit, cout zero
- Textures privees → warning dans rapport, pipeline continue sans planter
- Retard CDN Roblox → time.sleep(0.5) + retry x3 par texture
- Recyclage flotte : ~70% du code provient de LOCUS + CORPUS + FORGE + OSSEUS (valides)
- orbis_core.py = script unique, CLI headless via Blender -b --python orbis_core.py -- [args]

---

## Analyse ATOM-IC (fondation)

| FILTRE | VERITÉ ATOMIQUE POUR ORBIS |
|---|---|
| A — First Principles | Un decor Roblox = matrices de transformation + UV maps + IDs d'assets. Studio n'est pas necessaire. Tout est accessible via HTTP. |
| T — TRIZ | Contradiction : "geometrie 3D complexe" VS "zero ressource". Inversion : on ne telecharge pas la scene entiere → on interroge l'API et on reconstruit uniquement ce dont on a besoin (geometrie + textures diffuse). |
| O — Pareto | 20% qui font 80% du visuel : geometrie mesh + textures diffuse. Scripts Roblox, colliders, lights, effets particulaires → poubelle. |
| M — N.U.K.E | Un orbis_main.ipynb, un orbis_core.py, zero clic. Input = keyword ou asset ID. Output = .glb. |

---

## Recyclage Flotte Confirme

| BLOC | SOURCE | STATUT |
|---|---|---|
| parse_args() CLI headless | locus_convert.py:50 | RECYCLE |
| wm.read_factory_settings(use_empty=True) | Toutes fregates | RECYCLE |
| mat.use_backface_culling = False + node graph | locus_convert.py:194 | RECYCLE |
| op_seal_export() — flags GLB | locus_convert.py:222 | RECYCLE |
| write_rapport() + main() try/finally | locus_convert.py:250 | RECYCLE |
| CAMERA/LIGHT removal loop | forge_convert.py:132 | RECYCLE |
| orphans_purge(do_recursive=True) | forge_convert.py:137 | RECYCLE |
| join_meshes() select+join+apply | osseus_core.py:130 | RECYCLE |
| warnings = [] accumulation | forge_convert.py:91 | RECYCLE |
| Cell 00 Git Sync | corpus_main.ipynb | RECYCLE |
| Cell 01 Blender install | locus_main.ipynb | RECYCLE |
| Cell 04 subprocess launch | locus_main.ipynb | RECYCLE |
| Cell 05 Rapport + validation | locus_main.ipynb | RECYCLE |

---

## Historique des Sessions

| Date | Evenement |
|---|---|
| 2026-04-26 | Decision imperiale — creation Fregate 05 FERRUS ORBIS |
| 2026-04-26 | Brainstorming ATOM-IC + audit reutilisation flotte |
| 2026-04-26 | Fondation : docs rediges, structure deployee |
| 2026-04-26 | orbis_fetch.py + orbis_core.py + orbis_main.ipynb livres (mode METADATA) |
| 2026-04-30 | Decision : ajout mode STUDIO_OBJ — export Roblox Studio direct |
| 2026-04-30 | orbis_core.py + orbis_main.ipynb mis a jour — mode STUDIO_OBJ operationnel |
| 2026-04-30 | VALIDATION IMPERIALE — mode STUDIO_OBJ : map.glb → decor_map.glb (16.47 Mo, 4.1s) |
