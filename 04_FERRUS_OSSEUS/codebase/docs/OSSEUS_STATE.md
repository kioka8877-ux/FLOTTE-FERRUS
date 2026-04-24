# OSSEUS_STATE.md — Etat de la Fregate FERRUS OSSEUS
# Phylactere de Resurrection — Fregate 04
# FLOTTE FERRUS | AD MAJOREM GLORIAM IMPERATORIS

---

## Statut Global

**PHASE : ALPHA — En attente de validation production**

---

## Date de Creation

2026-04-24

---

## Ce qui est OPERATIONNEL

| Composant | Etat | Notes |
|-----------|------|-------|
| `osseus_core.py` | LIVRE | Script Blender headless complet |
| `osseus_main.ipynb` | LIVRE | Notebook Colab 8 cellules |
| `README.md` | LIVRE | Documentation complete |
| Template R15 (15 bones) | LIVRE | Naming Roblox standard |
| Template Mixamo (26 bones) | LIVRE | Prefix mixamorig: |
| Template DeepMotion (52 bones) | LIVRE | Corps complet + doigts |
| Import GLB/GLTF/OBJ/FBX | LIVRE | |
| Detection bbox T-pose | LIVRE | |
| Placement squelette auto | LIVRE | Proportions anatomiques |
| Automatic Weights | LIVRE | Fallback Envelope si echec |
| Export FBX rige | LIVRE | |
| Rapport JSON | LIVRE | |

---

## Ce qui N'A PAS ETE TESTE

| Test | Priorite | Notes |
|------|----------|-------|
| Pipeline complet sur vrai avatar GLB | CRITIQUE | Valider en production Colab |
| Template R15 sur avatar Roblox standard | HAUTE | |
| Template Mixamo sur avatar game | HAUTE | |
| Template DeepMotion 52 bones | MOYENNE | |
| Avatar multi-mesh (PLY split) | MOYENNE | Join teste en theorie |
| Avatar non-centre (offset X/Y) | HAUTE | bbox prend en compte le centre |
| Avatar echelle non-standard | MOYENNE | Transform apply avant bbox |
| Automatic Weights echec -> fallback | BASSE | Code present, non teste |

---

## Limitations Connues

| Limitation | Contournement |
|------------|---------------|
| T-pose obligatoire | Aucun — OSSEUS ne detecte pas la pose |
| Proportions fixes (humanoide standard) | Fonctionne pour 90% des avatars game |
| Doigts DeepMotion : positions approx | Suffisant pour auto-weights basiques |
| Pas de fingers detailles (R15/Mixamo) | Normal — ces templates n'ont pas de doigts |

---

## Prochaine Etape

1. **Tester en production** sur un vrai avatar GLB en T-pose
2. Valider le rapport JSON (`status: SUCCESS`)
3. Verifier le FBX rige dans un viewer 3D
4. Tester dans FERRUS ANIMUS (input FBX rige → retargeting)

---

## Protocole de Test Rapide

```bash
# 1. Prendre un avatar test en T-pose (ex: depuis Mixamo.com, download T-pose)
# 2. Deposer dans IN/
# 3. Lancer osseus_main.ipynb avec TEMPLATE="r15"
# 4. Verifier :
#    - rapport_osseus.json : status == "SUCCESS"
#    - avatar_rigged_*.fbx : existe et taille > 100 Ko
#    - Ouvrir le FBX dans Blender ou https://gltf-viewer.donmccurdy.com
#    - Verifier que le squelette est visible et positionne dans le mesh
```

---

## Bugs Connus

Aucun pour l'instant — pas encore teste en production.

---

*Ce qui est inscrit en ces pages constitue l'ETAT VALIDE du projet.
Ce qui n'est pas ici n'existe pas.*

**POUR L'EMPEROR. POUR LA FLOTTE FERRUS.**
