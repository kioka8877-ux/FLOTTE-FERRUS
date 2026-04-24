# FERRUS OSSEUS — Fregate 04
# FLOTTE FERRUS

**AD MAJOREM GLORIAM IMPERATORIS**

---

## Mission

Transformer un avatar brut en **T-pose sans squelette** en un **FBX rige pret a recevoir des animations**.

Un mesh entre. Un FBX rige sort. Aucune intervention humaine.

**Un input. Un rig. Zero intervention.**

---

## Le Contrat

```
IN/      <- avatar brut .glb / .gltf / .obj / .fbx (T-pose, sans squelette)
OUT/     <- avatar_rigged_*.fbx + rapport_osseus.json
```

Rien n'entre ni ne sort par une autre porte.

---

## Prerequis

- Avatar en **T-pose** (bras horizontaux, jambes droites)
- **Sans squelette existant** (ou squelette ignore/supprime)
- Formats supportes : `.glb`, `.gltf`, `.obj`, `.fbx`

---

## Pourquoi OSSEUS

FERRUS ANIMUS prend des FBX **deja rigues** (DeepMotion ou Mixamo) et retargete les animations.
Mais si tu as un avatar brut sans rig, ANIMUS ne peut rien faire.

OSSEUS resout ca : il **cree le squelette automatiquement** depuis la geometrie du mesh.

```
Avatar brut .glb (T-pose, sans rig)
        |
[FERRUS OSSEUS] — detection bbox + placement squelette + auto-weights
        |
Avatar rige .fbx (R15 / Mixamo / DeepMotion)
        |
[FERRUS ANIMUS] — retargeting + corrections animation
        |
FBX R15 propre pour CORPUS
```

---

## Les 3 Ops Internes

| Op | Role |
|----|------|
| **SCAN** | Import mesh, join, detection T-pose via bounding box |
| **BONE** | Placement automatique du squelette (proportions anatomiques) |
| **BIND** | Parenting Automatic Weights + export FBX rige |

---

## Templates de Squelettes

| Template | Bones | Usage |
|----------|-------|-------|
| `r15` | 15 bones | Roblox R15 (defaut) — compatible FERRUS ANIMUS |
| `mixamo` | 26 bones | Adobe Mixamo + Unity |
| `deepmotion` | 52 bones | DeepMotion complet avec doigts |

---

## Algorithme de Placement

OSSEUS calcule les positions des joints depuis la **bounding box** du mesh.
Fonctionne uniquement en T-pose (bras etendus horizontalement).

```
hauteur = bbox_max_Y - bbox_min_Y

hips_Y       = sol + hauteur * 0.52
epaules_Y    = sol + hauteur * 0.76
tete_top_Y   = sol + hauteur * 0.97

bras_gauche_X = centre - demi_largeur * 0.42  (coude)
bras_gauche_X = centre - demi_largeur * 0.82  (poignet)
```

Puis **Automatic Weights** (heat map Blender) assigne les influences.

---

## Sorties

| Fichier | Format | Usage |
|---------|--------|-------|
| `avatar_rigged_{nom}_{template}.fbx` | FBX | Input pour FERRUS ANIMUS IN/ |
| `rapport_osseus_{nom}.json` | JSON | Bilan (vertices, bones, weights, statut) |

---

## Lancement Rapide

```bash
# 1. Deposer le mesh dans IN/
cp mon_avatar.glb 04_FERRUS_OSSEUS/IN/

# 2. Ouvrir le notebook Colab
# 04_FERRUS_OSSEUS/codebase/osseus_main.ipynb

# 3. Configurer CELLULE 1
INPUT_FILE = "mon_avatar.glb"
TEMPLATE   = "r15"     # ou mixamo ou deepmotion

# 4. Executer toutes les cellules
# Le FBX rige apparait dans OUT/
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
04_FERRUS_OSSEUS/
  README.md                    <- Ce fichier
  IN/                          <- mesh brut T-pose
  OUT/                         <- avatar_rigged_*.fbx + rapport_osseus.json
  codebase/
    osseus_core.py             <- Script Blender headless (coeur)
    osseus_main.ipynb          <- Notebook Colab
  docs/
    OSSEUS_STATE.md            <- Etat courant de la fregate
```

---

## Integration dans la Flotte

```
FERRUS FORGE  (00) — Avatar brut -> .blend
FERRUS ANIMUS (01) — FBX mocap -> FBX R15 animes
FERRUS CORPUS (02) — FBX + avatar -> scene animee
FERRUS LOCUS  (03) — PLY + 360 -> decor .glb
FERRUS OSSEUS (04) — Mesh T-pose sans rig -> FBX rige  ← ICI
```

OSSEUS se place **avant ANIMUS** dans le workflow :

```
Avatar brut sans rig
  → [OSSEUS] → FBX rige
  → [ANIMUS] → FBX R15 + animations
  → [CORPUS] → Scene finale
```

---

*Ce qui est inscrit en ces pages constitue l'ETAT VALIDE du projet.
Ce qui n'est pas ici n'existe pas.*

**POUR L'EMPEROR. POUR LA FLOTTE FERRUS.**
