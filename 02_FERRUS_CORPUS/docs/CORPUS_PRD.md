# CORPUS_PRD.md — Bible Technique
# FREGATE 02 : FERRUS CORPUS
# Version : 2.0 | Date : 2026-04-26 | Statut : REFONTE VALIDEE

---

## I. VISION IMPERIALE

Convertir tout fichier `.fbx` ou `.glb` produit par la Flotte en fichier `.blend`
natif Blender, pret pour EXODUS et les outils de production aval.

**Objectif mesurable :** N FBX/GLB dans IN/ → N fichiers corpus_P*.blend dans OUT/
en moins de 2 minutes, cout zero, sans intervention technique de l'Empereur.

---

## II. CONTRAT D'ETANCHEITE

```
Drive/FLOTTE-FERRUS/02_FERRUS_CORPUS/
  IN/    <- Entree : ferrus_P*.fbx ou *.glb (depuis 01_FERRUS_ANIMUS/OUT/ ou autre)
  OUT/   <- Sortie : corpus_P*.blend + rapport_corpus.json
```

Rien ne traverse la coque sans passer par ces deux portes.

---

## III. ARCHITECTURE — CONVERSION PURE

### Pipeline de Conversion

```
┌────────────────────────────────────────────────────────┐
│                 CORPUS PIPELINE                        │
├────────────────────────────────────────────────────────┤
│                                                        │
│  GLOB ferrus_P*.fbx / ferrus_P*.glb dans IN/          │
│         │                                              │
│         ▼  (pour chaque fichier)                       │
│                                                        │
│  1. bpy.ops.wm.read_factory_settings(use_empty=True)  │
│  2. Import FBX → bpy.ops.import_scene.fbx()           │
│     Import GLB → bpy.ops.import_scene.gltf()          │
│  3. bpy.ops.wm.save_as_mainfile(filepath=output_blend)│
│  4. Logger dans rapport_corpus.json                   │
│                                                        │
│  FIN boucle → rapport_corpus.json finalise            │
└────────────────────────────────────────────────────────┘
```

---

## IV. MODULES

### convert_to_blend.py — Coeur du Systeme

Execute via : `blender --background --python convert_to_blend.py -- [args]`

**Arguments :**

| Argument | Description |
|---|---|
| `--input` | Chemin absolu du fichier FBX ou GLB |
| `--output-blend` | Chemin de sortie .blend |
| `--report-json` | Chemin du rapport JSON (optionnel) |

**Logique interne :**
1. `bpy.ops.wm.read_factory_settings(use_empty=True)` — scene vide
2. Detection format : `.fbx` → `import_scene.fbx` / `.glb` → `import_scene.gltf`
3. `bpy.ops.wm.save_as_mainfile(filepath=output_blend)` — export .blend
4. Logger : nom fichier, format source, statut, taille output

### corpus_main.ipynb — Notebook Colab

**Cellules :**

| # | Nom | Role |
|---|---|---|
| 1 | SETUP | Monte Drive, definit chemins, verifie Blender |
| 2 | CONFIG | Liste les FBX/GLB disponibles dans IN/ |
| 3 | CONVERSION | Boucle sur N fichiers, appelle convert_to_blend.py |
| 4 | RAPPORT | Charge et affiche rapport_corpus.json |

---

## V. INPUTS REQUIS

### ferrus_P*.fbx ou ferrus_P*.glb (depuis Fregate 01 ou autre source)

| Propriete | Valeur attendue |
|---|---|
| Format | FBX Binary ou GLB (glTF 2.0) |
| Contenu | Mesh, armature, animation — tout est accepte |
| Naming | ferrus_P*.fbx / ferrus_P*.glb (convention Flotte) |

---

## VI. OUTPUTS PRODUITS

### corpus_PN.blend (MASTER)

- Contenu intact du fichier source (mesh, armature, animation)
- Format Blender natif 4.x
- Pret pour import dans EXODUS

### rapport_corpus.json

```json
{
  "generated_at": "2026-04-26T00:00:00",
  "blender_version": "4.x",
  "total_files": 2,
  "files": [
    {
      "id": "P1",
      "source": "ferrus_P1.fbx",
      "format": "FBX",
      "output_blend": "corpus_P1.blend",
      "size_bytes": 1024000,
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
| Temps par fichier | < 30 secondes (CPU) |

---

## VIII. LIMITES DE LA FREGATE

- Fregate 02 NE fait PAS de retargeting ou manipulation d'animation
- Fregate 02 NE fait PAS de mapping de bones
- Fregate 02 NE fait PAS de rendu
- Fregate 02 NE valide PAS le contenu du fichier source — elle convertit, c'est tout

---

*EXODUS SYSTEM — Fregate 02_FERRUS_CORPUS v2.0.0*
