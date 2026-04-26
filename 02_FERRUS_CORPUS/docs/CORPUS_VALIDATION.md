# CORPUS_VALIDATION.md — Protocole de Test
# FREGATE 02 : FERRUS CORPUS
# Version : 2.0 | Date : 2026-04-26 | Statut : EN_ATTENTE_DEVELOPPEMENT

---

## Protocole de Validation Imperiale

Deux passes : unitaire (1 fichier) puis integration (N fichiers).

---

## Passe 1 — Validation Unitaire (ferrus_P1.fbx)

### V-01 : Execution sans erreur

```
Action : Lancer corpus_main.ipynb cellule CONVERSION sur P1 seul
Attendu : Aucune exception Python ou Blender
Critere : Code de retour Blender = 0
Statut : [ ] A VALIDER
```

### V-02 : Fichier output produit

```
Action : Verifier OUT/ apres execution
Attendu : corpus_P1.blend present
Critere : os.path.exists() = True
Statut : [ ] A VALIDER
```

### V-03 : Contenu .blend intact

```
Action : Ouvrir corpus_P1.blend dans Blender 4.x
Attendu : Mesh et armature presents, identiques au FBX source
Critere : Aucun objet manquant par rapport au FBX
Statut : [ ] A VALIDER
```

### V-04 : Rapport JSON valide

```
Action : Lire rapport_corpus.json
Attendu : files[0].status = "OK", size_bytes > 0
Critere : Structure JSON valide, statut OK
Statut : [ ] A VALIDER
```

---

## Passe 2 — Validation Integration (N fichiers)

### V-05 : Traitement N fichiers

```
Action : Lancer avec 2 FBX dans IN/
Attendu : corpus_P1.blend + corpus_P2.blend
Critere : 2 fichiers .blend produits
Statut : [ ] A VALIDER
```

### V-06 : Rapport global coherent

```
Action : Lire rapport_corpus.json
Attendu : total_files = 2, files = [{P1...}, {P2...}]
Critere : Structure JSON valide, 2 entrees
Statut : [ ] A VALIDER
```

### V-07 : Compatibilite EXODUS

```
Action : Importer corpus_P1.blend dans EXODUS
Attendu : Blender detecte armature + mesh
Critere : Fichier reconnu et utilisable par EXODUS
Statut : [ ] A VALIDER (necessite EXODUS operationnel)
```

---

## Grille de Qualification

| Test | Poids | Statut |
|---|---|---|
| V-01 Execution propre | Bloquant | - |
| V-02 Fichier output | Bloquant | - |
| V-03 Contenu intact | Bloquant | - |
| V-04 Rapport JSON | Important | - |
| V-05 N fichiers | Bloquant | - |
| V-06 Rapport global | Important | - |
| V-07 Compatibilite EXODUS | Optionnel | - |

**Seuil de liberation : V-01 a V-05 passes = FREGATE OPERATIONNELLE**

---

*POUR L'EMPEROR. POUR LA FLOTTE FERRUS.*
