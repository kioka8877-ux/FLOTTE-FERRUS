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
| 02 | FERRUS CORPUS | OPERATIONNELLE - Pipeline complet livre |
| 03 | ??? (decret futur) | EN ATTENTE DE DECRET IMPERIAL |

---

## Fregate 00 - FERRUS FORGE

**Mission :** Convertir tout avatar brut (`.glb`, `.obj`, `.fbx`) en fichier `.blend`
propre et exploitable par FERRUS CORPUS.

```
avatar_P1.glb  ┐
avatar_P2.obj  │  →  [FORGE]  →  avatar_P1.blend
avatar_P3.fbx  ┘                  avatar_P2.blend
                                   avatar_P3.blend
                                         ↓
                                  FERRUS CORPUS IN_AVATAR/
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
en fichiers FBX retargetes au format Roblox R15, corriges et purifies.

```
DeepMotion FBX
     |
  [INTEL] - Gemini (video) + Claude (FBX) -> plan_corrections.json
     |
  [EXEC]  - 5 operations bpy headless (smooth, hips, foot_slide, camera, mask)
     |
 [OUTPUT] - Retargeting DeepMotion 52 bones -> R15 15 bones (programme, zero GLB)
     |
  FBX R15 propre
```

### Structure

```
01_FERRUS_ANIMUS/
  codebase/
    INTEL/prompts/correction_prompt.txt
    EXEC/operations/
      smooth_fcurves.py
      stabilize_hips.py
      remove_foot_slide.py
      camera_follow.py
      mask_limbs.py
    OUTPUT/retarget_r15.py
  IN/    <- Deposer les FBX DeepMotion ici
  OUT/   <- Recuperer les FBX R15 ici
  docs/
    FERRUS_STATE.md      <- Phylactere de Resurrection
    FERRUS_PRD.md        <- Bible Technique
    FERRUS_ROADMAP.md    <- Plan de Conquete
    FERRUS_VALIDATION.md <- Protocole de Test
```

---

## Fregate 02 - FERRUS CORPUS

**Mission :** Incarner les animations R15 de FERRUS ANIMUS dans un avatar Roblox.
Transformer un squelette invisible en acteur visible, exportable en .blend (MASTER) et .glb (PREVIEW).

```
ferrus_P*.fbx (squelette R15 anime)
     +
avatar_r15.blend (mesh Roblox)
     |
  [INJECT] - Transfert direct R15->R15 (noms identiques, zero mapping)
     |
 corpus_P*.blend  <- MASTER pour EXODUS U01
 corpus_P*.glb    <- PREVIEW viewer en ligne
```

### Structure

```
02_FERRUS_CORPUS/
  codebase/
    inject_animation.py  <- Script Blender headless (coeur)
    corpus_main.ipynb    <- Notebook Colab
  IN/          <- ferrus_P*.fbx depuis 01_FERRUS_ANIMUS/OUT/
  IN_AVATAR/   <- avatar_r15.blend (fourni une fois)
  OUT/         <- corpus_P*.blend + corpus_P*.glb + rapport_corpus.json
  docs/
    CORPUS_STATE.md      <- Phylactere de Resurrection
    CORPUS_PRD.md        <- Bible Technique
    CORPUS_ROADMAP.md    <- Plan de Conquete
    CORPUS_VALIDATION.md <- Protocole de Test
```

---

*Ce qui est inscrit en ces pages constitue l'ETAT VALIDE du projet.
Ce qui n'est pas ici n'existe pas.*

**POUR L'EMPEROR. POUR LA FLOTTE FERRUS.**
