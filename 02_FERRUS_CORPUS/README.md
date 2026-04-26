# FERRUS CORPUS — Fregate 02
# FLOTTE FERRUS

**AD MAJOREM GLORIAM IMPERATORIS**

---

## Mission

Convertir les fichiers `.fbx` et `.glb` produits par la Flotte en fichiers `.blend`
exploitables par EXODUS et les outils de production aval.

**Une commande. N fichiers. Zero intervention.**

---

## Le Contrat

```
IN/    <- ferrus_P*.fbx (depuis 01_FERRUS_ANIMUS/OUT/) ou tout .glb / .fbx
OUT/   <- corpus_P*.blend + rapport_corpus.json
```

Rien n'entre ni ne sort par une autre porte.

---

## Pourquoi CORPUS

FERRUS ANIMUS produit des FBX animes prets a l'emploi.
FERRUS CORPUS les transforme au format `.blend` natif Blender — le seul format
accepte par EXODUS et l'outillage de production.

```
ferrus_P*.fbx  →  [CORPUS]  →  corpus_P*.blend  →  EXODUS
```

Aucune logique d'animation. Aucun mapping de bones. Conversion pure.

---

## Sorties

| Fichier | Format | Usage |
|---|---|---|
| `corpus_P1.blend` | Blender native | MASTER — input pour EXODUS |
| `rapport_corpus.json` | JSON | Bilan global (fichiers convertis, statuts) |

---

## Lancement Rapide

```bash
# 1. Deposer les FBX/GLB dans IN/
cp 01_FERRUS_ANIMUS/OUT/ferrus_P*.fbx 02_FERRUS_CORPUS/IN/

# 2. Ouvrir le notebook Colab
# 02_FERRUS_CORPUS/codebase/corpus_main.ipynb

# 3. Executer toutes les cellules
# Les .blend apparaissent dans OUT/
```

---

## Stack

| Composant | Valeur |
|---|---|
| Plateforme | Google Colab gratuit |
| GPU | INTERDIT (CPU uniquement) |
| Blender | 4.x headless (-b) |
| Python | bpy uniquement |
| Cout recurrent | Zero |

---

## Structure Complete

```
02_FERRUS_CORPUS/
  README.md                    <- Ce fichier
  IN/                          <- ferrus_P*.fbx ou *.glb (depuis Fregate 01)
  OUT/                         <- corpus_P*.blend + rapport_corpus.json
  codebase/
    convert_to_blend.py        <- Script Blender headless (coeur)
    corpus_main.ipynb          <- Notebook Colab
  docs/
    CORPUS_STATE.md            <- Phylactere de Resurrection
    CORPUS_PRD.md              <- Bible Technique
    CORPUS_ROADMAP.md          <- Plan de Conquete
    CORPUS_VALIDATION.md       <- Protocole de Test
```

---

*Ce qui est inscrit en ces pages constitue l'ETAT VALIDE du projet.
Ce qui n'est pas ici n'existe pas.*

**POUR L'EMPEROR. POUR LA FLOTTE FERRUS.**
