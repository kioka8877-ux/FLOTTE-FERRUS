# ORBIS_PRD.md — Bible Technique
# FREGATE 05 : FERRUS ORBIS
# Version : 1.0 | Date : 2026-04-26 | Statut : FONDATION

---

## I. VISION IMPERIALE

Extraire un decor 3D depuis le marketplace Roblox via API HTTP,
le nettoyer, le preparer pour l'occupation humaine et l'exporter en GLB
pret a recevoir les personnages ANIMUS et le rendu EXODUS.

**Objectif mesurable :** 1 keyword OU 1 asset ID → 1 decor_XXXX.glb exploitable
en moins de 3 minutes, cout zero, sans ouvrir Roblox Studio ni le navigateur.

---

## II. CONTRAT D'ETANCHEITE

```
Drive/FLOTTE-FERRUS/05_FERRUS_ORBIS/
  IN/       <- keyword.txt OU asset_id.txt (un fichier = une recherche)
  OUT/      <- decor_XXXX.glb + rapport_orbis.json
```

Rien n'entre ni ne sort par une autre porte.

**Format IN/ :**
- Fichier `keyword.txt` : contient un mot-cle (ex: `brookhaven street`)
- Fichier `asset_id.txt` : contient un asset ID numerique (ex: `12345678`)
- Les deux modes sont valides et auto-detectes

---

## III. ARCHITECTURE — LES QUATRE OPERATIONS

### 3.1 Operation EXTRACTION

**Mission :** Interroger le marketplace Roblox et telecharger le contenu brut.

**Etapes :**
1. Si keyword → appel API catalog pour recuperer l'asset ID du premier resultat pertinent
2. Appel API assetdelivery pour telecharger le fichier `.rbxm`
3. Parse XML du `.rbxm` → extraction des mesh refs + texture IDs
4. Telechargement textures via CDN Roblox (`rbxcdn.com`)

**Endpoints Roblox utilises :**

| Endpoint | Usage |
|---|---|
| `catalog.roblox.com/v1/search/items?keyword=...&category=Models` | Recherche par keyword |
| `assetdelivery.roblox.com/v1/asset/?id=<asset_id>` | Telechargement .rbxm |
| `t{1-7}.rbxcdn.com/<hash>` | Textures CDN |

**Sortie :** fichiers `.rbxm` + textures PNG/JPG dans `/tmp/orbis_cache/`

### 3.2 Operation NETTOYAGE

**Mission :** Extraire la geometrie pure et supprimer le bruit Roblox.

**Suppressions obligatoires :**

| Element | Raison |
|---|---|
| `<Script>`, `<LocalScript>`, `<ModuleScript>` | Code Lua non executable en dehors Roblox |
| `BasePart` de type Collider (non visible) | Inutile, alourdit la scene |
| Lights (PointLight, SurfaceLight, SpotLight) | Remplacees par l'eclairage EXODUS |
| `<Sound>`, `<Beam>`, `<ParticleEmitter>` | Effets Roblox incompatibles |

**Conservation :**
- `<Part>`, `<MeshPart>`, `<UnionOperation>` → geometrie
- `<Texture>`, `<Decal>` avec TextureId → materiaux
- Hierarchie de groupes `<Model>`, `<Folder>` → preservee pour lisibilite

**Sortie :** scene Python bpy propre, prete pour import Blender

### 3.3 Operation PREPARATION

**Mission :** Configurer la scene pour l'occupation humaine.

**Etapes Blender headless :**
1. `wm.read_factory_settings(use_empty=True)` — scene vierge
2. Import geometrie extraite (via intermediaire GLB ou OBJ)
3. `join_meshes()` — N parts Roblox → 1 mesh unifie (recycle osseus_core.py)
4. Double face ON : `mat.use_backface_culling = False` sur tous les materiaux
5. Application textures CDN sur les materiaux (nodes : UVMap → Image → BSDF)
6. Suppression objets residuels : CAMERA, LIGHT, SPEAKER (recycle forge_convert.py)
7. `orphans_purge(do_recursive=True)` — nettoyage donnees orphelines
8. Centrage scene (optionnel) : origine au centroid du decor

**Resultat :** scene Blender avec mesh double face, textures appliquees, accessible de l'interieur

### 3.4 Operation SEAL

**Mission :** Exporter le decor en GLB propre et generer le rapport.

**Export GLB (recycle locus_convert.py) :**
```python
bpy.ops.export_scene.gltf(
    filepath=output_path,
    export_format='GLB',
    use_selection=True,
    export_texcoords=True,
    export_normals=True,
    export_materials='EXPORT',
)
```

**Nommage sortie :** `decor_<asset_id>.glb`

---

## IV. MODES D'ENTREE

| MODE | INPUT | DESCRIPTION |
|---|---|---|
| `KEYWORD` | String texte | Recherche marketplace → premier resultat |
| `ASSET_ID` | Integer | Telechargement direct, zero recherche |

**Mode ASSET_ID recommande** pour la production — deterministe, pas de surprise sur le resultat.
**Mode KEYWORD** utile pour l'exploration.

---

## V. STACK TECHNIQUE IMPOSE

| COMPOSANT | VALEUR | CONTRAINTE |
|---|---|---|
| Plateforme | Google Colab gratuit | Runtime standard uniquement |
| GPU | INTERDIT | CPU uniquement |
| Blender | 4.2 LTS binaire headless (-b) | Stocke dans Drive/tools/ |
| Python | 3.10+ | requests + xml.etree.ElementTree + bpy |
| HTTP | requests | Telechargement .rbxm + textures CDN |
| XML | xml.etree.ElementTree | Parse .rbxm (fallback : lxml) |
| Temps max | < 3 min pour un asset standard | Mesure bout en bout |
| Cout recurrent | ZERO euro | Tout gratuit |

---

## VI. CONTRAT JSON DE SORTIE

### rapport_orbis.json

```json
{
  "status": "SUCCESS",
  "asset_id": 12345678,
  "asset_name": "Brookhaven Street Block",
  "mode": "ASSET_ID",
  "keyword": null,
  "output_glb": "OUT/decor_12345678.glb",
  "textures": {
    "total": 12,
    "resolues": 10,
    "privees": 2
  },
  "mesh": {
    "parts_roblox": 47,
    "mesh_unifie": true,
    "vertices": 18432,
    "faces": 9216
  },
  "double_face": true,
  "duree_sec": 87.4,
  "warnings": [
    "Texture ID 987654321 inaccessible (privee) — geometrie conservee sans texture"
  ],
  "erreur": null
}
```

---

## VII. GESTION DES ERREURS ET CAS LIMITES

| CAS | COMPORTEMENT |
|---|---|
| Asset ID inexistant | Rapport erreur + sys.exit(1) |
| Asset prive (achat requis) | Rapport erreur + sys.exit(1) |
| Texture CDN inaccessible | Warning dans rapport, pipeline continue |
| .rbxm malformed XML | Fallback lxml, si echec → erreur fatale |
| Asset trop lourd (> 500MB) | Warning memoire + decimation automatique si > 500K faces |
| Keyword sans resultat | Rapport erreur + suggestion d'utiliser ASSET_ID |
| CDN rate-limit | Retry x3 avec time.sleep(1.0), echec gracieux si x3 rate |

---

## VIII. CONTRAINTES INVIOLABLES

1. Blender en mode headless uniquement (-b) — zero interface
2. GPU jamais utilise — CPU obligatoire
3. `mat.use_backface_culling = False` sur TOUS les materiaux — sans exception
4. L'asset source n'est jamais modifie — cache en lecture seule dans /tmp/
5. Le rapport JSON est toujours genere, meme en cas d'erreur (try/finally)
6. Textures privees → warning, pas erreur fatale
7. Sortie toujours nommee `decor_<asset_id>.glb` — pas de nom custom

---

## IX. INTEGRATION DANS LA FLOTTE

```
FERRUS ANIMUS  (01) — personnages FBX animes
       +
FERRUS ORBIS   (05) — decor Roblox .glb
       |
       v
FERRUS EXODUS  (futur) — rendu final scene complete
```

ORBIS produit le **decor**. ANIMUS produit les **personnages**. EXODUS les assemble et rend.

---

## X. ANALYSE ATOM-IC (REFERENCE)

| FILTRE | APPLICATION DANS ORBIS |
|---|---|
| A — First Principles | Roblox = base de donnees publique de geometrie 3D. Pas besoin de Studio. L'atome = (vertices, UV, texture_id). Tout accessible via HTTP. |
| T — TRIZ Inversion | Au lieu de telecharger et ouvrir une scene entiere (lourd), on interroge l'API et on reconstruit uniquement la geometrie utile. |
| O — Pareto 80/20 | Geometrie + textures diffuse = 80% du visuel. Scripts Lua, colliders, lights, sons = effort sans valeur visuelle. |
| M — N.U.K.E | orbis_core.py + orbis_main.ipynb. Un appel. Une pression sur Run. Un GLB sort. |
