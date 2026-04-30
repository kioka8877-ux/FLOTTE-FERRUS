# CODEX MECHANICUS - FLOTTE FERRUS

**AD MAJOREM GLORIAM IMPERATORIS**

---

## Vision

La FLOTTE FERRUS est un pipeline automatise de traitement d'animations 3D.
Chaque **fregate** est une unite autonome, isolee, avec un contrat d'entree et de sortie strict.

**Plateforme :** Google Colab gratuit (CPU uniquement)
**Cout recurrent :** Zero euro

---

## Les Dix Lois de la Voie Royale

| LOI | DOCTRINE |
|---|---|
| LOI DU LEVIER | Effort minimum / Resultat maximum |
| LOI DU FLUX SACRE | Humain -> IA -> Code -> Resultat |
| LOI DE L'ETANCHEITE | Chaque fregate est un silo isole |
| LOI DU GOULOT | Identifier et detruire le bottleneck en premier |
| LOI DE SURQUALITE | L'output doit etre superieur a l'input en qualite |
| LOI D'AGNOSTICISME | Systeme agnostique a l'origine des donnees |
| LOI DU MIROIR | Synchronisation temporelle parfaite entre composants |
| LOI TELECOMMANDE | Calcul lourd sur Colab, l'humain appuie juste un bouton |
| LOI DU BETON | Si pas sur GitHub/Drive, cela n'existe pas |
| LOI DE L'EMPIRE | Seul ce qui sert l'objectif final est retenu |

---

## Protocole d'Ingenierie Celeste

Cinq phases sacrees. Le developpement ne commence qu'a la Phase 5.

| PHASE | NOM | DESCRIPTION |
|---|---|---|
| Phase 1 | ANALYSE FORENSIQUE | Verification de la faisabilite reelle |
| Phase 2 | PHYLACTERE DE RESURRECTION | Redaction de FERRUS_STATE.md |
| Phase 3 | PRD / BIBLE FERRUS | Specifications exhaustives dans FERRUS_PRD.md |
| Phase 4 | PLAN DE CONQUETE | FERRUS_ROADMAP.md avec checkpoints |
| Phase 5 | DEVELOPPEMENT DIVIN | Code propre, modulaire, documente |

---

## Flotte

| FREGATE | NOM | STATUT |
|---|---|---|
| 00 | FERRUS FORGE | OPERATIONNELLE - Validation imperiale 2026-04-18 |
| 01 | FERRUS ANIMUS | OPERATIONNELLE - Pipeline complet livre |
| 02 | FERRUS CORPUS | OPERATIONNELLE - Validation imperiale 2026-04-26 |
| 03 | FERRUS LOCUS | EN ATTENTE DE DECRET IMPERIAL |
| 04 | FERRUS OSSEUS | OPERATIONNELLE - Validation imperiale 2026-04-24 |
| 05 | FERRUS ORBIS | OPERATIONNELLE - Validation imperiale 2026-04-30 |

---

## Fregate 00 - FERRUS FORGE

**Mission :** Convertir tout avatar brut (`.glb`, `.obj`, `.fbx`) en fichier `.blend`
propre et exploitable par les fregates aval.

```
avatar_P1.glb  ┐
avatar_P2.obj  │  →  [FORGE]  →  avatar_P1.blend
avatar_P3.fbx  ┘                  avatar_P2.blend
                                   avatar_P3.blend
```

### Structure

```
00_FERRUS_FORGE/
  codebase/
    forge_convert.py   <- Script Blender headless (coeur)
    forge_main.ipynb   <- Notebook Colab
    docs/
      FORGE_STATE.md / FORGE_PRD.md / FORGE_ROADMAP.md / FORGE_VALIDATION.md
  IN/    <- Deposer les avatars bruts ici (.glb / .obj / .fbx)
  OUT/   <- Recuperer les .blend ici
```

---

## Fregate 01 - FERRUS ANIMUS

**Mission :** Transformer des fichiers FBX d'animation bruts issus de DeepMotion
en fichiers FBX retargetes au format Roblox R15 ou OSSEUS (52 bones), corriges et purifies.

```
DeepMotion FBX + Avatar OSSEUS
     |
  [INTEL] - Gemini (video) + Claude API (FBX) -> plan_corrections.json
     |
  [EXEC]  - 5 operations bpy headless (smooth, hips, foot_slide, camera, mask)
     |
 [OUTPUT] - Retargeting DeepMotion -> R15 / Mixamo / OSSEUS 52 bones
     |
  FBX anime propre (avec mesh si mode DEEPMOTION)
```

### Structure

```
01_FERRUS_ANIMUS/
  codebase/
    INTEL/
      pre_parse_fbx.py
      intel_skeleton.py
      prompts/correction_prompt.txt
    EXEC/operations/
      smooth_fcurves.py / stabilize_hips.py / remove_foot_slide.py
      camera_follow.py / mask_limbs.py
    OUTPUT/retarget_r15.py
  main_ferrus.ipynb
  IN/ IN_AVATAR/ OUT/ CLAUDE_IN/ GEMINI_IN/
  docs/
    FERRUS_STATE.md / FERRUS_PRD.md / FERRUS_ROADMAP.md / FERRUS_VALIDATION.md
```

---

## Fregate 02 - FERRUS CORPUS

**Mission :** Convertir les fichiers `.fbx` et `.glb` produits par la Flotte
en fichiers `.blend` natifs Blender, prets pour EXODUS.

```
ferrus_P*.fbx  ┐
ferrus_P*.glb  │  →  [CORPUS]  →  corpus_P*.blend  →  EXODUS
               ┘
```

Conversion pure. Aucune logique d'animation. Aucun mapping de bones.

### Structure

```
02_FERRUS_CORPUS/
  codebase/
    convert_to_blend.py  <- Script Blender headless (coeur)
    corpus_main.ipynb    <- Notebook Colab
  IN/    <- ferrus_P*.fbx ou *.glb (depuis 01_FERRUS_ANIMUS/OUT/)
  OUT/   <- corpus_P*.blend + rapport_corpus.json
  docs/
    CORPUS_STATE.md / CORPUS_PRD.md / CORPUS_ROADMAP.md / CORPUS_VALIDATION.md
```

---

## Fregate 04 - FERRUS OSSEUS

**Mission :** Prendre un mesh T-pose sans squelette et produire un FBX rige
pret pour ANIMUS (52 bones DeepMotion / R15 / Mixamo).

```
mesh_T-pose.glb  →  [OSSEUS]  →  osseus_avatar.fbx (mesh + squelette 52 bones)
                                        ↓
                               01_FERRUS_ANIMUS/IN_AVATAR/
```

### Structure

```
04_FERRUS_OSSEUS/
  codebase/
    osseus_core.py       <- Script Blender headless (coeur)
    osseus_main.ipynb    <- Notebook Colab
  IN/    <- mesh T-pose brut
  OUT/   <- osseus_avatar.fbx
  docs/OSSEUS_STATE.md
```

---

---

## Fregate 05 - FERRUS ORBIS

**Mission :** Extraire un decor 3D depuis le marketplace Roblox via API HTTP,
le nettoyer et l'exporter en `.glb` pret pour ANIMUS + EXODUS.

```
keyword "brookhaven street"  ┐
   OU                         │  →  [ORBIS]  →  decor_XXXX.glb (mesh + textures + double face)
asset_id 12345678            ┘
```

### Structure

```
05_FERRUS_ORBIS/
  codebase/
    orbis_core.py      <- Script Blender headless (coeur)
    orbis_main.ipynb   <- Notebook Colab
    docs/
      ORBIS_STATE.md / ORBIS_PRD.md / ORBIS_ROADMAP.md / ORBIS_VALIDATION.md
  IN/    <- keyword.txt ou asset_id.txt
  OUT/   <- decor_<asset_id>.glb + rapport_orbis.json
```

---

*Ce qui est inscrit en ces pages constitue l'ETAT VALIDE du projet.
Ce qui n'est pas ici n'existe pas.*

**POUR L'EMPEROR. POUR LA FLOTTE FERRUS.**
