# ORBIS_STATE.md — Phylactere de Resurrection
# FREGATE 05 : FERRUS ORBIS
# Derniere mise a jour : 2026-04-26 (FONDATION — docs rediges)

---

[STATUS] : FONDATION — Docs valides, code a ecrire

[LAST_WORK] :
- Decision imperiale : creation Fregate 05 FERRUS ORBIS
- Contexte : FERRUS LOCUS conserve sa mission PLY/360. ORBIS prend en charge l'extraction Roblox.
- Brainstorming architectural complet execute (framework ATOM-IC applique)
- Audit de reutilisation flotte execute : ~70% du code disponible en recyclage
- Documents fondateurs rediges (STATE, PRD, ROADMAP, VALIDATION, README)
- Structure dossiers creee : IN/ OUT/ codebase/ docs/

[NEXT_TASK] : Ecrire orbis_core.py (Phase 1 — EXTRACTION + NETTOYAGE)

[STATUS] : PRET_POUR_DEVELOPPEMENT

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
| EXTRACTION | orbis_fetch.py ou orbis_core.py | A ECRIRE |
| NETTOYAGE | orbis_core.py — op_clean() | A ECRIRE |
| PREPARATION | orbis_core.py — op_prepare() | A ECRIRE |
| SEAL | orbis_core.py — op_seal_export() | A ECRIRE (recycle locus_convert.py) |
| PIPELINE | orbis_main.ipynb | A ECRIRE |
| DOCS | ORBIS_STATE.md | TERMINE |
| DOCS | ORBIS_PRD.md | TERMINE |
| DOCS | ORBIS_ROADMAP.md | TERMINE |
| DOCS | ORBIS_VALIDATION.md | TERMINE |
| INFRA | IN/ OUT/ | TERMINE |

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
| parse_args() CLI headless | locus_convert.py:50 | A RECYCLER |
| wm.read_factory_settings(use_empty=True) | Toutes fregates | A RECYCLER |
| mat.use_backface_culling = False + node graph | locus_convert.py:194 | A RECYCLER |
| op_seal_export() — flags GLB | locus_convert.py:222 | A RECYCLER |
| write_rapport() + main() try/finally | locus_convert.py:250 | A RECYCLER |
| CAMERA/LIGHT removal loop | forge_convert.py:132 | A RECYCLER |
| orphans_purge(do_recursive=True) | forge_convert.py:137 | A RECYCLER |
| join_meshes() select+join+apply | osseus_core.py:130 | A RECYCLER |
| warnings = [] accumulation | forge_convert.py:91 | A RECYCLER |
| Cell 00 Git Sync | corpus_main.ipynb | A RECYCLER |
| Cell 01 Blender install | locus_main.ipynb | A RECYCLER |
| Cell 04 subprocess launch | locus_main.ipynb | A RECYCLER |
| Cell 05 Rapport + validation | locus_main.ipynb | A RECYCLER |

---

## Historique des Sessions

| Date | Evenement |
|---|---|
| 2026-04-26 | Decision imperiale — creation Fregate 05 FERRUS ORBIS |
| 2026-04-26 | Brainstorming ATOM-IC + audit reutilisation flotte |
| 2026-04-26 | Fondation : docs rediges, structure deployee |
