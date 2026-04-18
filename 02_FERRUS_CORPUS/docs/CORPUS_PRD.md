# CORPUS_PRD.md — Bible Technique
# FREGATE 02 : FERRUS CORPUS
# Version : 1.0 | Date : 2026-04-18 | Statut : VALIDE

---

## I. VISION IMPERIALE

Prendre les squelettes R15 animes produits par FERRUS ANIMUS (FBX sans mesh, invisibles)
et les incarner dans un avatar Roblox R15 pour produire des acteurs complets, visibles,
exploitables en viewer 3D et en production EXODUS.

**Objectif mesurable :** N FBX R15 Ferrus + 1 avatar_r15.blend → N fichiers corpus_P*.blend + N fichiers corpus_P*.glb
en moins de 2 minutes, cout zero, sans intervention technique de l'Empereur.

---

## II. CONTRAT D'ETANCHEITE

```
Drive/FLOTTE-FERRUS/02_FERRUS_CORPUS/
  IN/          <- Entree : ferrus_P*.fbx depuis 01_FERRUS_ANIMUS/OUT/
  IN_AVATAR/   <- Entree : avatar_r15.blend (depose une fois)
  OUT/         <- Sortie : corpus_P*.blend + corpus_P*.glb + rapport_corpus.json
```

Rien ne traverse la coque sans passer par ces trois portes.

---

## III. ARCHITECTURE — LA LOGIQUE D'INCARNATION

### Pourquoi ca marche sans mapping

FERRUS ANIMUS produit des FBX avec 15 bones nommes selon la convention Roblox R15 :
`LowerTorso`, `UpperTorso`, `Head`, `LeftUpperArm`, `RightUpperArm`...

L'avatar Roblox `.blend` possede une armature avec les MEMES noms de bones.

```
FBX Ferrus        Avatar Roblox blend
──────────────    ────────────────────
LowerTorso    →   LowerTorso     ✓
UpperTorso    →   UpperTorso     ✓
Head          →   Head           ✓
LeftUpperArm  →   LeftUpperArm   ✓
...           →   ...            ✓
```

Transfert direct bone-to-bone par nom. Zero couche de mapping. Zero risque d'erreur.

### Pipeline d'Incarnation

```
┌────────────────────────────────────────────────────────┐
│                 CORPUS PIPELINE                        │
├────────────────────────────────────────────────────────┤
│                                                        │
│  GLOB ferrus_P*.fbx dans IN/                          │
│         │                                              │
│         ▼  (pour chaque FBX)                          │
│                                                        │
│  1. Charger avatar_r15.blend (armature + mesh)        │
│  2. Importer ferrus_PN.fbx → armature temporaire      │
│  3. Extraire l'Action (animation) de l'armature FBX   │
│  4. Appliquer l'Action sur l'armature avatar           │
│     (bones memes noms → affectation directe)          │
│  5. Export corpus_PN.blend (MASTER)                   │
│  6. Export corpus_PN.glb (PREVIEW)                    │
│  7. Logger dans rapport_corpus.json                   │
│                                                        │
│  FIN boucle → rapport_corpus.json finalise            │
└────────────────────────────────────────────────────────┘
```

---

## IV. MODULES

### inject_animation.py — Coeur du Systeme

Execute via : `blender --background --python inject_animation.py -- [args]`

**Arguments :**

| Argument | Description |
|---|---|
| `--fbx` | Chemin absolu du FBX Ferrus |
| `--avatar` | Chemin absolu de avatar_r15.blend |
| `--output-blend` | Chemin de sortie .blend |
| `--output-glb` | Chemin de sortie .glb |

**Logique interne :**
1. `bpy.ops.wm.read_factory_settings(use_empty=True)`
2. `bpy.ops.wm.open_mainfile(filepath=avatar_blend)` — charge le mesh + armature
3. `bpy.ops.import_scene.fbx(filepath=fbx_path)` — importe l'armature FBX
4. Recupere l'action de l'armature FBX importee
5. Assigne l'action a l'armature avatar via `animation_data.action`
6. `bpy.ops.export_scene.gltf(filepath=output_glb)` — export GLB
7. `bpy.ops.wm.save_as_mainfile(filepath=output_blend)` — export BLEND

### corpus_main.ipynb — Notebook Colab

**Cellules :**

| # | Nom | Role |
|---|---|---|
| 1 | SETUP | Monte Drive, definit chemins, verifie Blender |
| 2 | CONFIG | Liste les FBX disponibles dans IN/, valide avatar |
| 3 | INCARNATION | Boucle sur N FBX, appelle inject_animation.py |
| 4 | RAPPORT | Charge et affiche rapport_corpus.json |
| 5 | PREVIEW | Affiche taille et checksum des .glb produits |

---

## V. INPUTS REQUIS

### ferrus_P*.fbx (depuis Fregate 01)

| Propriete | Valeur attendue |
|---|---|
| Format | FBX Binary (Kaydara) |
| Bones | 15 bones R15 |
| Naming | LowerTorso, UpperTorso, Head... |
| Animation | KeyTime present, 1 AnimationStack |
| Mesh | ABSENT (squelette pur) |

### avatar_r15.blend

| Propriete | Valeur requise |
|---|---|
| Format | Blender .blend (version 4.x recommandee) |
| Armature | R15 — memes noms que Ferrus |
| Mesh | Present (corps Roblox attache a l'armature) |
| Materiau | Optionnel (si absent : sans texture dans le GLB) |
| Shape Keys | Optionnel (non utilisees en Fregate 02) |

---

## VI. OUTPUTS PRODUITS

### corpus_PN.blend (MASTER)

- Avatar complet (armature + mesh) avec animation
- Armature R15 native Blender
- Action NLA assignee
- Pret pour import dans EXODUS U01 (01_ANIMATION_ENGINE/IN_MIXAMO_BASE/)

### corpus_PN.glb (PREVIEW)

- Format glTF Binary
- Lisible dans tout viewer moderne
- Contient : mesh + armature + animation
- Viewable sur : gltf-viewer.donmccurdy.com, modelviewer.dev

### rapport_corpus.json

```json
{
  "generated_at": "2026-04-18T00:00:00",
  "blender_version": "4.x",
  "total_actors": 2,
  "actors": [
    {
      "id": "P1",
      "fbx_source": "ferrus_P1.fbx",
      "bones_transferred": 15,
      "frames": 427,
      "output_blend": "corpus_P1.blend",
      "output_glb": "corpus_P1.glb",
      "status": "OK"
    }
  ]
}
```

---

## VII. CONTRAINTES

| Contrainte | Valeur |
|---|---|
| GPU | INTERDIT |
| Plateforme | Google Colab gratuit (CPU) |
| Blender | 4.x headless uniquement |
| Dependances Python | bpy uniquement (zero pip) |
| Cout | Zero euro |
| Temps par acteur | < 1 minute (CPU, mesh simple) |

---

## VIII. LIMITES DE LA FREGATE

- Fregate 02 NE fait PAS d'animation faciale (shape keys ARKit) — c'est le role de EXODUS U01
- Fregate 02 NE fait PAS de retargeting complexe — les bones ont les memes noms
- Fregate 02 NE genere PAS l'avatar — l'utilisateur fournit avatar_r15.blend
- Fregate 02 NE produit PAS de rendu — juste le .blend et le .glb

---

*EXODUS SYSTEM — Fregate 02_FERRUS_CORPUS v1.0.0*
