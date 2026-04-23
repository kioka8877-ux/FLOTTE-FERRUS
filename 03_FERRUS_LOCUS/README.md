# FERRUS LOCUS — Fregate 03
# FLOTTE FERRUS

**AD MAJOREM GLORIAM IMPERATORIS**

---

## Mission

Transformer les sorties brutes de Hunyuan3D-2.1 en decors 3D textures et exploitables.
Prendre un fichier `.ply` (geometrie) et une image 360deg equirectangulaire (texture) → produire un `.glb` ferme, texture, pret a recevoir des avatars animes.

**Un input. Un decor. Zero intervention.**

---

## Le Contrat

```
IN/      <- fichier .ply (geometrie Hunyuan3D-2.1)
IN_360/  <- image equirectangulaire 360deg (jpg/png/hdr/exr)
OUT/     <- decor_locus.glb + rapport_locus.json
```

Rien n'entre ni ne sort par une autre porte.

---

## Pourquoi LOCUS

FERRUS CORPUS produit les acteurs : les avatars animes.
FERRUS LOCUS produit la scene : l'environnement, le decor, le lieu.

```
LOCUS (decor textures .glb) + CORPUS (avatars animes .glb) = scene complete
```

Le `.glb` produit par LOCUS est directement charge dans le projet central pour y placer les avatars, positionner la camera, rendre les frames et produire la video MP4 finale.

---

## Les 3 Ops Internes

| Op | Role |
|----|------|
| **MESH** | Import `.ply`, nettoyage maillage (watertight, non-manifold) |
| **BAKE** | UV Smart Project + baking texture 360deg sur le mesh |
| **SEAL** | Validation finale + export `.glb` avec materiaux |

---

## Decimation — Option C (Auto)

Le maillage `.ply` de Hunyuan peut contenir jusqu'a 10M de faces.
LOCUS applique une decimation intelligente :

| Mode | Comportement |
|------|-------------|
| `auto` | Detection automatique selon nb de faces (defaut) |
| `none` | Mesh original intact |
| `high` | Garde 25% des faces |
| `medium` | Garde 10% des faces |
| `low` | Garde 3% des faces |

En mode `auto` :
- > 5 000 000 faces → `low`
- > 1 000 000 faces → `medium`
- > 300 000 faces   → `high`
- < 300 000 faces   → `none`

---

## Sorties

| Fichier | Format | Usage |
|---------|--------|-------|
| `decor_locus.glb` | glTF Binary | MASTER — integration projet central |
| `rapport_locus.json` | JSON | Bilan (faces, decimation, bake, statut) |

---

## Lancement Rapide

```bash
# 1. Deposer le .ply dans IN/
cp mon_decor.ply 03_FERRUS_LOCUS/IN/

# 2. Deposer l'image 360 dans IN_360/
cp texture_360.jpg 03_FERRUS_LOCUS/IN_360/

# 3. Ouvrir le notebook Colab
# 03_FERRUS_LOCUS/codebase/locus_main.ipynb

# 4. Executer toutes les cellules
# Le .glb apparait dans OUT/
```

---

## Stack

| Composant | Valeur |
|-----------|--------|
| Plateforme | Google Colab gratuit |
| GPU | INTERDIT (CPU uniquement) |
| Blender | 3.6+ headless (-b) |
| Python | bpy uniquement |
| Cout recurrent | Zero |

---

## Structure Complete

```
03_FERRUS_LOCUS/
  README.md                    <- Ce fichier
  IN/                          <- fichier .ply (Hunyuan3D-2.1)
  IN_360/                      <- image equirectangulaire 360deg
  OUT/                         <- decor_locus.glb + rapport_locus.json
  codebase/
    locus_convert.py           <- Script Blender headless (coeur)
    locus_main.ipynb           <- Notebook Colab
  docs/
    LOCUS_STATE.md             <- Etat courant de la fregate
```

---

## Viewer en Ligne (PREVIEW)

Le fichier `.glb` produit est lisible directement sur :
- https://gltf-viewer.donmccurdy.com
- https://modelviewer.dev/examples/viewer/index.html

Importer `decor_locus.glb` — le decor textures apparait immediatement.

---

*Ce qui est inscrit en ces pages constitue l'ETAT VALIDE du projet.
Ce qui n'est pas ici n'existe pas.*

**POUR L'EMPEROR. POUR LA FLOTTE FERRUS.**
