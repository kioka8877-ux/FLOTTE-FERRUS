# ORBIS_ROADMAP.md — Plan de Conquete
# FREGATE 05 : FERRUS ORBIS
# Version : 1.0 | Date : 2026-04-26

---

## PHASE 0 — FONDATIONS (TERMINE)

- [x] Decision imperiale : creation Fregate 05 FERRUS ORBIS
- [x] Brainstorming architectural — framework ATOM-IC applique
- [x] Analyse forensique API Roblox (endpoints, formats, limites)
- [x] Audit reutilisation flotte (~70% code disponible en recyclage)
- [x] Depot GitHub structure et fichiers crees
- [x] Documents ORBIS rediges (STATE, PRD, ROADMAP, VALIDATION, README)

---

## PHASE 1 — EXTRACTION HTTP (A ECRIRE)

### 1.1 Recherche par keyword (mode KEYWORD)

- [ ] Appel `catalog.roblox.com/v1/search/items?keyword=...&category=Models`
- [ ] Parse JSON reponse → extraction premier asset_id pertinent
- [ ] Validation : asset public et de type Model/Place

### 1.2 Telechargement .rbxm (mode ASSET_ID et KEYWORD)

- [ ] Appel `assetdelivery.roblox.com/v1/asset/?id=<asset_id>`
- [ ] Gestion redirections HTTP (asset delivery redirige parfois)
- [ ] Sauvegarde dans `/tmp/orbis_cache/<asset_id>.rbxm`
- [ ] Validation : fichier non vide, format XML detectable

### 1.3 Parse XML .rbxm

- [ ] Lecture avec `xml.etree.ElementTree`
- [ ] Fallback `lxml` si parse echoue (encoding non-standard)
- [ ] Extraction : `<Part>`, `<MeshPart>`, `<UnionOperation>` → geometrie
- [ ] Extraction : `<Texture>`, `<Decal>` → TextureId → liste IDs textures
- [ ] Extraction : `<CFrame>`, `<Vector3>` → positions + rotations
- [ ] Filtrage : supprimer `<Script>`, `<LocalScript>`, `<Sound>`, `<Light*>`, `<ParticleEmitter>`

### 1.4 Telechargement textures CDN

- [ ] Resolution IDs textures → URLs `rbxcdn.com`
- [ ] Telechargement PNG/JPG dans `/tmp/orbis_cache/textures/`
- [ ] Retry x3 avec `time.sleep(1.0)` si erreur CDN
- [ ] Gestion textures privees → warning, pas echec fatal
- [ ] Rapport : textures_resolues / textures_privees / textures_total

---

## PHASE 2 — CONVERSION GEOMETRIE (A ECRIRE)

### 2.1 Reconstruction mesh Python → intermediaire GLB/OBJ

- [ ] Convertir CFrame Roblox → matrices Blender (repere Y-up vs Z-up)
- [ ] Ecrire vertices + faces + UV depuis donnees XML parsees
- [ ] Generer un fichier intermediaire (OBJ ou GLB minimal) dans /tmp/
- [ ] Validation : fichier non vide, au moins 1 mesh detectable

**Note :** Si des librairies Python Roblox existent sur GitHub (ex: `rbxl2gltf`, `roblox-to-blender`),
evaluer leur reutilisation avant d'ecrire la conversion from scratch.

### 2.2 Import Blender headless

- [ ] `wm.read_factory_settings(use_empty=True)` — scene vierge
- [ ] Import OBJ ou GLB intermediaire via `bpy.ops.import_scene.*`
- [ ] Detection objets importes (diff set avant/apres — recycle forge_convert.py)
- [ ] Rapport : nombre d'objets importes, vertices, faces

---

## PHASE 3 — NETTOYAGE + PREPARATION (A ECRIRE)

### 3.1 Nettoyage scene (recycle forge_convert.py)

- [ ] Suppression CAMERA, LIGHT, SPEAKER, LIGHT_PROBE
- [ ] `orphans_purge(do_recursive=True)`
- [ ] Rapport : objets supprimes

### 3.2 Unification mesh (recycle osseus_core.py)

- [ ] `join_meshes()` : N parts Roblox → 1 mesh unifie
- [ ] `transform_apply(location=True, rotation=True, scale=True)`
- [ ] Validation : 1 seul objet MESH present dans la scene

### 3.3 Application materiaux + textures

- [ ] Creer materiau Blender par texture unique
- [ ] Node graph : UVMap → ShaderNodeTexImage → BSDF → Output (recycle locus_convert.py)
- [ ] `bpy.data.images.load()` pour chaque texture CDN telechargee
- [ ] `img.pack()` pour embarquer les textures dans la scene

### 3.4 Double face (recycle locus_convert.py)

- [ ] Pour chaque materiau : `mat.use_backface_culling = False`
- [ ] Validation : backface_culling desactive sur TOUS les materiaux
- [ ] Test visuel : camera peut entrer dans le decor sans mur invisible

---

## PHASE 4 — SEAL + EXPORT (A ECRIRE — recycle locus_convert.py)

- [ ] Unpack textures avant export : `img.unpack(method="WRITE_LOCAL")` (recycle osseus_core.py)
- [ ] `op_seal_export()` : export GLB avec flags valides
- [ ] Nommage : `OUT/decor_<asset_id>.glb`
- [ ] `write_rapport()` : rapport JSON complet
- [ ] Validation : fichier GLB non vide, importable dans Blender

---

## PHASE 5 — NOTEBOOK COLAB (A ECRIRE)

- [ ] Cell 00 — Git Sync (recycle corpus_main.ipynb Cell 00)
- [ ] Cell 01 — Blender 4.2 LTS install (recycle locus_main.ipynb Cell 01)
- [ ] Cell 02 — Config : saisie KEYWORD ou ASSET_ID, scan IN/
- [ ] Cell 03 — Extraction HTTP : appel API + .rbxm + CDN textures (Python pur)
- [ ] Cell 04 — Pipeline Blender : lancement orbis_core.py headless
- [ ] Cell 05 — Rapport : lecture rapport_orbis.json + affichage bilan
- [ ] Cell 06 — Download : files.download(GLB + JSON)

---

## PHASE 6 — VALIDATION ET LIVRAISON

- [ ] Test mode ASSET_ID sur asset public connu (Brookhaven ou similaire)
- [ ] Test mode KEYWORD : "brookhaven street" → asset recupere automatiquement
- [ ] Verification : GLB importable dans Blender sans erreur
- [ ] Verification : double face confirme (camera peut entrer dans le decor)
- [ ] Verification : textures visibles sur le mesh
- [ ] Verification : duree < 3 minutes
- [ ] Verification : rapport.json genere et coherent
- [ ] Validation imperiale

---

## Dependances Critiques

```
Phase 0 (Fondations)      → TERMINE
Phase 1 (Extraction HTTP) → peut commencer maintenant (Python pur, zero Blender)
Phase 2 (Conversion)      → apres Phase 1
Phase 3 (Nettoyage)       → apres Phase 2
Phase 4 (Seal)            → apres Phase 3
Phase 5 (Notebook)        → apres Phase 4 (structure connue)
Phase 6 (Validation)      → apres Phase 5
```

---

## Librairies Python a Evaluer avant Phase 2

| Librairie | Source | Evaluer pour |
|---|---|---|
| `rbxl2gltf` | GitHub | Conversion .rbxl/.rbxm → GLTF directe |
| `rblx-unarchiver` | GitHub | Unpack .rbxm → XML propre |
| Blender addon `roblox_import` | GitHub | Import .rbxm direct dans bpy |

**Protocole ATOM-IC — T (TRIZ) :** avant d'ecrire le parser XML from scratch,
verifier si une librairie existante valide resout deja le probleme.
Si oui, l'utiliser. Si non (ou trop instable), ecrire le parser minimal.
