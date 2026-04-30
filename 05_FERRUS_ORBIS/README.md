# FERRUS ORBIS — Fregate 05
# FLOTTE FERRUS
# Statut : OPERATIONNELLE — Validation imperiale 2026-04-30

**AD MAJOREM GLORIAM IMPERATORIS**

---

## Mission

Extraire ou importer un decor 3D Roblox et l'exporter en `.glb`
pret a accueillir les personnages ANIMUS et le rendu EXODUS.

**Un input. Un decor GLB. Zero clic manuel.**

---

## Le Contrat

```
IN/    <- map.glb / map.obj / map.fbx (export Roblox Studio)
         OU keyword.txt / asset_id.txt (API Roblox)
OUT/   <- decor_<nom>.glb + rapport_orbis.json
```

Rien n'entre ni ne sort par une autre porte.

---

## Pourquoi ORBIS

FERRUS ANIMUS produit les personnages animes.
FERRUS ORBIS produit le decor dans lequel ils evoluent.

Sans ORBIS : construire les decors manuellement dans Blender (heures de travail).
Avec ORBIS : deposer un export Studio ou saisir un asset ID → GLB en moins de 5 minutes.

```
map.glb (export Roblox Studio)
          |
    [FERRUS ORBIS]
          |
    decor_map.glb (mesh + double face)
          |
    FERRUS EXODUS — rendu final
```

---

## Les Trois Modes

| MODE | INPUT | DESCRIPTION |
|---|---|---|
| `STUDIO_OBJ` | `.glb` / `.obj` / `.fbx` dans `IN/` | Export direct Roblox Studio — **mode principal** |
| `ASSET_ID` | `asset_id.txt` dans `IN/` | Telechargement API Roblox, deterministe |
| `KEYWORD` | `keyword.txt` dans `IN/` | Recherche marketplace, premier resultat |

**Mode STUDIO_OBJ recommande en production** — geometrie complete avec interieurs et textures natives.

---

## Les Quatre Operations

| OP | NOM | DESCRIPTION |
|---|---|---|
| 1 | IMPORT | Fichier Studio (.glb/.obj/.fbx) OU reconstruction depuis metadata API |
| 2 | NETTOYAGE | Suppression cameras / lights / orphans |
| 3 | JOIN + DOUBLE FACE | N parts → 1 mesh unifie, backface culling OFF |
| 4 | SEAL | Export GLB + rapport JSON |

---

## Sorties

| Fichier | Format | Usage |
|---|---|---|
| `decor_<nom>.glb` | GLB | Decor 3D double face, pret pour EXODUS |
| `rapport_orbis.json` | JSON | Bilan (mesh, materiaux, taille, duree, warnings) |

---

## Lancement Rapide

### Mode STUDIO_OBJ (recommande)

```
1. Exporter la map depuis Roblox Studio : File > Export > .glb ou .obj
2. Deposer le fichier dans IN/
3. Ouvrir orbis_main.ipynb sur Colab
4. Executer Cell 00 → Cell 01 → PATCH → Cell 04 → Cell 05 → Cell 06
   (Cell 02 et 03 sont auto-skippes en mode STUDIO_OBJ)
5. decor_<nom>.glb apparait dans OUT/
```

### Mode ASSET_ID

```
1. Deposer asset_id.txt dans IN/ (contenu : l'ID numerique Roblox)
2. Executer toutes les cellules dans l'ordre
3. decor_<asset_id>.glb apparait dans OUT/
```

---

## Stack

| Composant | Valeur |
|---|---|
| Plateforme | Google Colab gratuit |
| GPU | INTERDIT (CPU uniquement) |
| Import Studio | bpy.ops.import_scene.gltf / wm.obj_import / import_scene.fbx |
| HTTP | Python requests (API Roblox + CDN textures) |
| XML | xml.etree.ElementTree (parse .rbxm) |
| Blender | 4.2 LTS headless (-b) |
| Cout recurrent | Zero |

---

## Integration dans la Flotte

```
FERRUS FORGE   (00) — Avatar brut -> .blend
FERRUS ANIMUS  (01) — FBX mocap -> FBX animes (personnages)
FERRUS CORPUS  (02) — FBX/GLB -> .blend
FERRUS LOCUS   (03) — PLY + 360 -> decor .glb (scans physiques)
FERRUS OSSEUS  (04) — Mesh T-pose -> FBX rige
FERRUS ORBIS   (05) — Decor Roblox -> .glb  <- ICI
```

ORBIS se place en parallele d'ANIMUS :

```
FERRUS ANIMUS  (01) ─── personnages FBX ───┐
                                            ├──> FERRUS EXODUS — rendu final
FERRUS ORBIS   (05) ─── decor GLB ─────────┘
```

---

## Structure Complete

```
05_FERRUS_ORBIS/
  README.md                    <- Ce fichier
  IN/                          <- map.glb / map.obj / asset_id.txt / keyword.txt
  OUT/                         <- decor_<nom>.glb + rapport_orbis.json
  codebase/
    orbis_fetch.py             <- Extraction HTTP API Roblox (mode METADATA)
    orbis_core.py              <- Script Blender headless (coeur)
    orbis_main.ipynb           <- Notebook Colab (7 cellules)
    docs/
      ORBIS_STATE.md           <- Phylactere de Resurrection
      ORBIS_PRD.md             <- Bible Technique
      ORBIS_ROADMAP.md         <- Plan de Conquete
      ORBIS_VALIDATION.md      <- Protocole de Test
```

---

*Ce qui est inscrit en ces pages constitue l'ETAT VALIDE du projet.
Ce qui n'est pas ici n'existe pas.*

**POUR L'EMPEROR. POUR LA FLOTTE FERRUS.**
