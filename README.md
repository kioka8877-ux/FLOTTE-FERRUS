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
| 01 | FERRUS ANIMUS | OPERATIONNELLE - Developpement autorise |
| 02 | ??? (decret futur) | EN ATTENTE DE DECRET IMPERIAL |
| 03 | ??? (decret futur) | EN ATTENTE DE DECRET IMPERIAL |

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

*Ce qui est inscrit en ces pages constitue l'ETAT VALIDE du projet.
Ce qui n'est pas ici n'existe pas.*

**POUR L'EMPEROR. POUR LA FLOTTE FERRUS.**
