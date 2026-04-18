# CORPUS_VALIDATION.md — Protocole de Test
# FREGATE 02 : FERRUS CORPUS
# Version : 1.0 | Date : 2026-04-18 | Statut : EN_ATTENTE_DEVELOPPEMENT

---

## Protocole de Validation Imperiale

La validation se fait en deux passes : unitaire (P1 seul) puis integration (P1+P2).

---

## Passe 1 — Validation Unitaire (ferrus_P1.fbx)

### V-01 : Execution sans erreur

```
Action : Lancer corpus_main.ipynb cellule INCARNATION sur P1 seul
Attendu : Aucune exception Python ou Blender
Critere : Code de retour Blender = 0
Statut : [ ] A VALIDER
```

### V-02 : Fichiers output produits

```
Action : Verifier OUT/ apres execution
Attendu : corpus_P1.blend present + corpus_P1.glb present
Critere : os.path.exists() = True pour les deux
Statut : [ ] A VALIDER
```

### V-03 : Bones transferes

```
Action : Lire rapport_corpus.json
Attendu : actors[0].bones_transferred = 15
Critere : Valeur exacte 15
Statut : [ ] A VALIDER
```

### V-04 : Frames conservees

```
Action : Lire rapport_corpus.json
Attendu : actors[0].frames = 427 (valeur Fregate 01)
Critere : Valeur >= 400
Statut : [ ] A VALIDER
```

### V-05 : GLB lisible en viewer

```
Action : Importer corpus_P1.glb sur gltf-viewer.donmccurdy.com
Attendu : Avatar visible avec mesh + animation jouable
Critere : Pas d'ecran vide, mouvement visible
Statut : [ ] A VALIDER
```

### V-06 : BLEND importable dans Blender

```
Action : Ouvrir corpus_P1.blend dans Blender 4.x
Attendu : Armature R15 presente, mesh attache, action assignee
Critere : F12 render ou timeline > 0 frames
Statut : [ ] A VALIDER
```

---

## Passe 2 — Validation Integration (ferrus_P1.fbx + ferrus_P2.fbx)

### V-07 : Traitement N acteurs

```
Action : Lancer avec 2 FBX dans IN/
Attendu : corpus_P1.blend + corpus_P1.glb + corpus_P2.blend + corpus_P2.glb
Critere : 4 fichiers output produits
Statut : [ ] A VALIDER
```

### V-08 : Rapport global coherent

```
Action : Lire rapport_corpus.json
Attendu : total_actors = 2, actors = [{P1...}, {P2...}]
Critere : Structure JSON valide, 2 entrees
Statut : [ ] A VALIDER
```

### V-09 : Independance des acteurs

```
Action : Verifier que corpus_P1 et corpus_P2 ont des animations differentes
Attendu : frame_range differente OU action differente entre P1 et P2
Critere : Les deux FBX ne produisent pas le meme output
Statut : [ ] A VALIDER
```

---

## Passe 3 — Validation Chaine EXODUS

### V-10 : Compatibilite EXODUS U01

```
Action : Importer corpus_P1.blend dans 01_ANIMATION_ENGINE/IN_MIXAMO_BASE/
Attendu : Blender detecte l'armature R15 + action
Critere : Cellule CONFIG de TRANSMUTATION liste l'acteur correctement
Statut : [ ] A VALIDER (necessite EXODUS U01 operationnel)
```

---

## Grille de Qualification

| Test | Poids | Statut |
|---|---|---|
| V-01 Execution propre | Bloquant | - |
| V-02 Fichiers output | Bloquant | - |
| V-03 Bones = 15 | Bloquant | - |
| V-04 Frames preservees | Important | - |
| V-05 GLB viewer | Bloquant | - |
| V-06 BLEND Blender | Important | - |
| V-07 N acteurs | Bloquant | - |
| V-08 Rapport global | Important | - |
| V-09 Independance | Important | - |
| V-10 Chaine EXODUS | Optionnel | - |

**Seuil de liberation : V-01 a V-07 passes = FREGATE OPERATIONNELLE**

---

*POUR L'EMPEROR. POUR LA FLOTTE FERRUS.*
