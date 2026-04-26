# ORBIS_VALIDATION.md — Protocole de Test
# FREGATE 05 : FERRUS ORBIS
# Version : 1.0 | Date : 2026-04-26

---

## I. ASSETS DE REFERENCE

| CHAMP | VALEUR |
|---|---|
| Asset de reference | Brookhaven (ou equivalent public connu) |
| Mode de reference | ASSET_ID (deterministe) |
| Critere de selection | Asset public, gratuit, geometrie riche, textures accessibles |
| Asset ID | A definir lors de la Phase 6 (chercher sur marketplace avant validation) |
| Taille cible | < 50 MB .rbxm |
| Parts Roblox cibles | > 20 parts (valide le join_meshes) |
| Textures cibles | > 5 textures publiques |

---

## II. CRITERES DE VALIDATION PAR PHASE

### 2.1 Phase 1 — EXTRACTION HTTP

| TEST | CRITERE DE SUCCES |
|---|---|
| Mode ASSET_ID : telechargement .rbxm | Fichier present dans /tmp/orbis_cache/, taille > 0 |
| Mode KEYWORD : resolution asset_id | asset_id numerique retourne, != None |
| Parse XML .rbxm | Aucune exception ElementTree ou lxml |
| Extraction geometrie | Au moins 1 Part ou MeshPart extrait |
| Extraction textures | Au moins 1 TextureId extrait |
| Telechargement CDN | Au moins 1 texture PNG/JPG telechargee |
| Gestion texture privee | Warning dans rapport, pas d'exception levee |
| Retry CDN | En cas d'erreur 429/503 : retry x3 execute sans planter |

### 2.2 Phase 2 — CONVERSION GEOMETRIE

| TEST | CRITERE DE SUCCES |
|---|---|
| Fichier intermediaire genere | OBJ ou GLB present dans /tmp/, taille > 0 |
| Import Blender | Aucune exception bpy, au moins 1 objet MESH importe |
| Coordonnees correctes | Mesh non aplati, Y-up → Z-up converti correctement |
| Rapport import | nombre_objets > 0, vertices > 0, faces > 0 |

### 2.3 Phase 3 — NETTOYAGE + PREPARATION

| TEST | CRITERE DE SUCCES |
|---|---|
| Suppression lights | Aucun objet de type LIGHT dans la scene apres nettoyage |
| Suppression cameras | Aucun objet de type CAMERA dans la scene |
| orphans_purge | Aucune donnee orpheline (bpy.data.meshes, .materials sans user) |
| join_meshes | 1 seul objet MESH present apres unification |
| transform_apply | Scale = (1,1,1), rotation = (0,0,0) apres apply |
| Materiaux crees | au moins 1 materiau present sur le mesh |
| Textures chargees | bpy.data.images non vide, images packees |
| Double face | mat.use_backface_culling == False sur TOUS les materiaux |

**Test double face specifique :**
- Placer une camera virtuelle a l'interieur du mesh
- Rendre une frame (meme en resolution minimale)
- Les faces interieures doivent etre visibles (pas de mur invisible)

### 2.4 Phase 4 — SEAL + EXPORT

| TEST | CRITERE DE SUCCES |
|---|---|
| Fichier GLB genere | OUT/decor_<asset_id>.glb present, taille > 0 |
| GLB importable Blender | Import sans exception dans Blender desktop |
| Mesh present | Au moins 1 objet MESH dans le GLB importe |
| Textures embeddees | Textures visibles apres import GLB (pas de chemin brise) |
| Rapport JSON genere | OUT/rapport_orbis.json present et valide (json.loads sans erreur) |
| Champs rapport | status, asset_id, output_glb, textures, mesh, double_face, duree_sec presents |

### 2.5 Notebook Colab

| TEST | CRITERE DE SUCCES |
|---|---|
| Cell 00 Git Sync | Codebase synchronisee depuis GitHub sans erreur |
| Cell 01 Blender | `blender --version` affiche 4.2.x |
| Cell 02 Config | Scan IN/ detecte le fichier keyword.txt ou asset_id.txt |
| Cell 03 Extraction | .rbxm + textures telechargees, JSON intermediaire genere |
| Cell 04 Pipeline | subprocess.returncode == 0, stdout contient [ORBIS] SUCCESS |
| Cell 05 Rapport | rapport_orbis.json affiche, status == "SUCCESS" |
| Cell 06 Download | GLB + JSON telecharges sans erreur |

---

## III. TEST DE BOUT EN BOUT

### Procedure Mode ASSET_ID (reference)

```
1. Identifier un asset ID Roblox public (marketplace.roblox.com)
2. Creer IN/asset_id.txt avec l'ID
3. Configurer ASSET_ID dans Cell 02 du notebook
4. Executer orbis_main.ipynb sur Colab gratuit (CPU)
5. Attendre fin du pipeline
6. Recuperer OUT/decor_<asset_id>.glb + OUT/rapport_orbis.json
7. Ouvrir le GLB dans Blender desktop
8. Placer la camera a l'interieur du decor
9. Verifier la visibilite des faces interieures
```

### Procedure Mode KEYWORD

```
1. Creer IN/keyword.txt avec le contenu : brookhaven street
2. Configurer MODE = "KEYWORD" dans Cell 02
3. Executer le notebook
4. Verifier que l'asset_id est resolu automatiquement
5. Verifier le GLB de sortie
```

### Criteres de Succes Global

| CRITERE | VALEUR ATTENDUE |
|---|---|
| Duree totale | < 3 minutes (asset < 50 MB) |
| Fichier sortie | OUT/decor_<asset_id>.glb present avec mesh + textures |
| Rapport | OUT/rapport_orbis.json present, status = "SUCCESS" |
| GLB importable | Import Blender sans erreur |
| Double face confirme | Camera interieure — faces visibles |
| Textures visibles | Au moins 50% des textures resolues et affichees |
| Cout | 0 euro |
| Erreurs fatales | 0 |

---

## IV. VALIDATION IMPERIALE

L'Empereur valide ORBIS quand :

1. Le test de bout en bout passe en mode ASSET_ID sur l'asset de reference
2. Le GLB contient le mesh avec textures, importable dans Blender sans erreur
3. La camera peut entrer dans le decor (double face confirme visuellement)
4. Le temps total est < 3 minutes
5. Le rapport.json est clair et lisible
6. Le mode KEYWORD fonctionne sur au moins un cas de test

---

## V. CAS D'ECHEC ET ESCALADE

| ERREUR | CAUSE PROBABLE | ACTION |
|---|---|---|
| .rbxm non telecharge | Asset prive ou ID invalide | Verifier sur marketplace.roblox.com |
| XML parse error | .rbxm binaire ou corrompu | Tester avec lxml, verifier format fichier |
| Aucun mesh extrait | Pas de Part/MeshPart dans le .rbxm | Verifier structure XML manuellement |
| Coordonnees incorrectes | Erreur conversion Y-up/Z-up | Verifier matrice de conversion dans orbis_core.py |
| Textures toutes privees | Asset avec textures verrouillee | Choisir un autre asset sur marketplace |
| GLB non importable | Flags export incorrects | Verifier op_seal_export() — comparer avec locus_convert.py |
| Double face non actif | use_backface_culling non applique | Verifier boucle materiaux dans op_prepare() |
| Timeout Colab | Asset trop lourd | Ajouter decimation ou choisir asset plus leger |
| CDN rate-limit persistant | trop de requetes textures | Augmenter sleep, reduire batch textures |

---

## VI. CHECKLIST PRE-VALIDATION

Avant de lancer le test de bout en bout, verifier :

- [ ] orbis_core.py present dans codebase/
- [ ] orbis_main.ipynb present dans codebase/
- [ ] IN/ contient soit keyword.txt soit asset_id.txt
- [ ] Drive/tools/blender executable accessible
- [ ] ANTHROPIC_API_KEY non requis (ORBIS est zero-API-key)
- [ ] Connexion internet active sur Colab (requetes HTTP)
- [ ] Espace Drive suffisant (> 200 MB libre pour cache + output)
