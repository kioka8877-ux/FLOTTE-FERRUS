# FORGE_VALIDATION.md — Protocole de Test
# FREGATE 00 : FERRUS FORGE
# Version : 1.0 | Date : 2026-04-18 | Statut : EN ATTENTE DE DEVELOPPEMENT

---

## Protocole General

Chaque test est independant. Un test echoue ne bloque pas les autres.
Tous les tests s'executent dans Colab via forge_main.ipynb.

---

## TEST 01 — Conversion GLB

**Objectif :** Verifier la conversion d'un avatar .glb vers .blend

| Champ | Valeur |
|---|---|
| Input | `IN/avatar_P1.glb` (avatar Roblox R15 standard) |
| Attendu | `OUT/avatar_P1.blend` cree |
| Statut rapport | `status: "OK"` |
| Armature | `armature_found: true` |
| Bones R15 | `r15_bones_found: true` |
| Warnings | `[]` (aucun warning attendu) |

**Resultat :** [ ] PASS / [ ] FAIL
**Notes :**

---

## TEST 02 — Conversion OBJ

**Objectif :** Verifier la conversion d'un avatar .obj vers .blend

| Champ | Valeur |
|---|---|
| Input | `IN/avatar_P1.obj` (mesh simple sans rig) |
| Attendu | `OUT/avatar_P1.blend` cree |
| Statut rapport | `status: "OK"` |
| Armature | `armature_found: false` |
| Warnings | `["Aucune armature detectee — avatar sans rig"]` |

**Resultat :** [ ] PASS / [ ] FAIL
**Notes :**

---

## TEST 03 — Conversion FBX

**Objectif :** Verifier la conversion d'un avatar .fbx vers .blend

| Champ | Valeur |
|---|---|
| Input | `IN/avatar_P1.fbx` (avatar avec armature) |
| Attendu | `OUT/avatar_P1.blend` cree |
| Statut rapport | `status: "OK"` |
| Armature | `armature_found: true` |

**Resultat :** [x] PASS
**Notes :** Teste en production 2026-04-18 — ferrus_P1.fbx + ferrus_P2.fbx → .blend OK, Armature True, R15 15/15

---

## TEST 04 — Multi-Acteurs Formats Mixtes

**Objectif :** Verifier le traitement de N acteurs avec formats differents

| Champ | Valeur |
|---|---|
| Inputs | `avatar_P1.glb` + `avatar_P2.obj` + `avatar_P3.fbx` |
| Attendus | `avatar_P1.blend` + `avatar_P2.blend` + `avatar_P3.blend` |
| Rapport | `total_avatars: 3`, `actors: [{P1:OK}, {P2:OK}, {P3:OK}]` |

**Resultat :** [ ] PASS / [ ] FAIL
**Notes :**

---

## TEST 05 — Nommage Miroir

**Objectif :** Verifier la correspondance exacte des noms de fichiers

| Input | Sortie Attendue |
|---|---|
| `avatar_P1.glb` | `avatar_P1.blend` |
| `avatar_P2.obj` | `avatar_P2.blend` |
| `avatar_P3.fbx` | `avatar_P3.blend` |

**Resultat :** [ ] PASS / [ ] FAIL
**Notes :**

---

## TEST 06 — Compatibilite CORPUS

**Objectif :** Verifier que les .blend produits sont utilisables par FERRUS CORPUS

| Champ | Valeur |
|---|---|
| Input CORPUS | `avatar_P1.blend` produit par FORGE |
| Action | Copier dans IN_AVATAR/ de CORPUS, lancer CORPUS |
| Attendu | `corpus_P1.blend` + `corpus_P1.glb` produits sans erreur |

**Resultat :** [ ] PASS / [ ] FAIL
**Notes :**

---

## TEST 07 — Resilience Erreur Format Inconnu

**Objectif :** Verifier le comportement avec un format non supporte

| Champ | Valeur |
|---|---|
| Input | `avatar_P1.stl` (format non supporte) |
| Attendu | Skip avec `status: "ERREUR"` dans rapport |
| Comportement | Les autres acteurs continuent d'etre traites |

**Resultat :** [ ] PASS / [ ] FAIL
**Notes :**

---

## Bilan de Validation

| TEST | DESCRIPTION | STATUT |
|---|---|---|
| TEST 01 | Conversion .glb | EN ATTENTE |
| TEST 02 | Conversion .obj | EN ATTENTE |
| TEST 03 | Conversion .fbx | PASS (2026-04-18) |
| TEST 04 | Multi-acteurs formats mixtes | PASS partiel — 2 FBX OK (2026-04-18) |
| TEST 05 | Nommage miroir | EN ATTENTE |
| TEST 06 | Compatibilite CORPUS | EN ATTENTE |
| TEST 07 | Resilience format inconnu | EN ATTENTE |

**Validation imperiale requise apres : TEST 01 + TEST 04 + TEST 06**

---

*POUR L'EMPEROR. POUR LA FLOTTE FERRUS.*
