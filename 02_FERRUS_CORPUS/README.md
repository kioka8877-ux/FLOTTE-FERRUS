# FERRUS CORPUS — Fregate 02
# FLOTTE FERRUS

**AD MAJOREM GLORIAM IMPERATORIS**

---

## Mission

Incarner les animations R15 produites par FERRUS ANIMUS dans un avatar Roblox.
Prendre un squelette anime invisible → produire un acteur visible, exploitable en viewer et en production.

**Une commande. N personnages. Zero intervention.**

---

## Le Contrat

```
IN/              <- ferrus_P*.fbx (depuis 01_FERRUS_ANIMUS/OUT/)
IN_AVATAR/       <- avatar_r15.blend (depose une fois, reutilise pour tous)
OUT/             <- corpus_P*.blend + corpus_P*.glb + rapport_corpus.json
```

Rien n'entre ni ne sort par une autre porte.

---

## Pourquoi CORPUS

FERRUS ANIMUS produit l'ANIMUS — l'ame, l'animation, le mouvement.
FERRUS CORPUS lui donne un CORPUS — le corps, la chair, la forme visible.

```
ANIMUS (squelette R15 anime) + CORPUS (avatar Roblox mesh) = acteur complet
```

Les bones R15 de Ferrus et les bones de l'avatar Roblox ont les memes noms.
Le transfert est direct. Zero couche de mapping.

---

## Sorties

| Fichier | Format | Usage |
|---|---|---|
| `corpus_P1.blend` | Blender native | MASTER — input pour EXODUS U01 |
| `corpus_P1.glb` | glTF Binary | PREVIEW — viewer en ligne |
| `rapport_corpus.json` | JSON | Bilan global (bones, frames, statuts) |

---

## Lancement Rapide

```bash
# 1. Deposer les FBX dans IN/
cp 01_FERRUS_ANIMUS/OUT/ferrus_P*.fbx 02_FERRUS_CORPUS/IN/

# 2. Deposer l'avatar dans IN_AVATAR/ (une seule fois)
cp avatar_r15.blend 02_FERRUS_CORPUS/IN_AVATAR/

# 3. Ouvrir le notebook Colab
# 02_FERRUS_CORPUS/codebase/corpus_main.ipynb

# 4. Executer toutes les cellules
# Les outputs apparaissent dans OUT/
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
  IN/                          <- ferrus_P*.fbx (depuis Fregate 01)
  IN_AVATAR/                   <- avatar_r15.blend (fourni une fois)
  OUT/                         <- corpus_P*.blend + .glb + rapport_corpus.json
  codebase/
    inject_animation.py        <- Script Blender headless (coeur)
    corpus_main.ipynb          <- Notebook Colab
  docs/
    CORPUS_STATE.md            <- Phylactere de Resurrection
    CORPUS_PRD.md              <- Bible Technique
    CORPUS_ROADMAP.md          <- Plan de Conquete
    CORPUS_VALIDATION.md       <- Protocole de Test
```

---

## Viewer en Ligne (PREVIEW)

Le fichier `.glb` produit est lisible directement sur :
- https://gltf-viewer.donmccurdy.com
- https://modelviewer.dev/examples/viewer/index.html

Importer `corpus_P1.glb` — l'avatar anime apparait avec mesh et mouvement.

---

*Ce qui est inscrit en ces pages constitue l'ETAT VALIDE du projet.
Ce qui n'est pas ici n'existe pas.*

**POUR L'EMPEROR. POUR LA FLOTTE FERRUS.**
