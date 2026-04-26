# FERRUS ORBIS — Fregate 05
# FLOTTE FERRUS

**AD MAJOREM GLORIAM IMPERATORIS**

---

## Mission

Extraire un decor 3D depuis le marketplace Roblox via API HTTP,
le nettoyer et l'exporter en `.glb` pret a accueillir les personnages ANIMUS et le rendu EXODUS.

**Un keyword ou un asset ID. Un decor GLB. Zero clic manuel.**

---

## Le Contrat

```
IN/    <- keyword.txt OU asset_id.txt
OUT/   <- decor_<asset_id>.glb + rapport_orbis.json
```

Rien n'entre ni ne sort par une autre porte.

---

## Pourquoi ORBIS

FERRUS ANIMUS produit les personnages animes.
FERRUS ORBIS produit le decor dans lequel ils evoluent.

Sans ORBIS : construire les decors manuellement dans Blender (heures de travail).
Avec ORBIS : saisir un asset ID Roblox → GLB en moins de 3 minutes.

```
keyword "brookhaven street"
          |
    [FERRUS ORBIS]
          |
    decor_XXXX.glb (mesh + textures + double face)
          |
    FERRUS EXODUS — rendu final
```

---

## Les Quatre Operations

| OP | NOM | DESCRIPTION |
|---|---|---|
| 1 | EXTRACTION | API Roblox → .rbxm + textures CDN |
| 2 | NETTOYAGE | Suppression scripts / colliders / lights Roblox |
| 3 | PREPARATION | Blender headless, double face ON, textures appliquees |
| 4 | SEAL | Export GLB + rapport JSON |

---

## Modes d'Entree

| MODE | INPUT | DESCRIPTION |
|---|---|---|
| `ASSET_ID` | Integer (ex: `12345678`) | Telechargement direct, deterministe |
| `KEYWORD` | String (ex: `brookhaven street`) | Recherche marketplace, premier resultat |

Mode ASSET_ID recommande en production — pas de surprise sur le resultat.

---

## Sorties

| Fichier | Format | Usage |
|---|---|---|
| `decor_<asset_id>.glb` | GLB | Decor 3D double face, pret pour EXODUS |
| `rapport_orbis.json` | JSON | Bilan (textures, mesh, duree, warnings) |

---

## Lancement Rapide

```bash
# 1. Deposer l'input dans IN/
echo "12345678" > 05_FERRUS_ORBIS/IN/asset_id.txt

# 2. Ouvrir le notebook Colab
# 05_FERRUS_ORBIS/codebase/orbis_main.ipynb

# 3. Configurer Cell 02
ASSET_ID = "12345678"   # ou MODE = "KEYWORD" + KEYWORD = "brookhaven street"

# 4. Executer toutes les cellules
# decor_12345678.glb apparait dans OUT/
```

---

## Stack

| Composant | Valeur |
|---|---|
| Plateforme | Google Colab gratuit |
| GPU | INTERDIT (CPU uniquement) |
| HTTP | Python requests (API Roblox + CDN) |
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
FERRUS ORBIS   (05) — Marketplace Roblox -> decor .glb  <- ICI
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
  IN/                          <- keyword.txt ou asset_id.txt
  OUT/                         <- decor_<asset_id>.glb + rapport_orbis.json
  codebase/
    orbis_core.py              <- Script Blender headless (coeur) [A ECRIRE]
    orbis_main.ipynb           <- Notebook Colab [A ECRIRE]
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
