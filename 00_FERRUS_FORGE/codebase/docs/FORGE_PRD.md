# FORGE_PRD.md — Bible Technique
# FREGATE 00 : FERRUS FORGE
# Version : 1.0 | Date : 2026-04-18 | Statut : VALIDE

---

## I. VISION IMPERIALE

Convertir tout avatar brut en format .blend propre et exploitable par FERRUS CORPUS.
Un avatar entre (n'importe quel format), un .blend sort. Rien d'autre.

**Objectif mesurable :** N avatars (formats mixtes) → N fichiers avatar_P*.blend
en moins de 2 minutes, cout zero, sans intervention technique de l'Empereur.

---

## II. CONTRAT D'ETANCHEITE

```
Drive/FLOTTE-FERRUS/00_FERRUS_FORGE/
  IN/   <- Entree : avatar_P*.glb / avatar_P*.obj / avatar_P*.fbx
  OUT/  <- Sortie : avatar_P*.blend + rapport_forge.json
```

Rien ne traverse la coque sans passer par ces deux portes.
Le OUT/ de FORGE alimente directement le IN_AVATAR/ de CORPUS.

---

## III. ARCHITECTURE — LA LOGIQUE DE CONVERSION

### Pipeline de Conversion

```
┌────────────────────────────────────────────────────────┐
│                   FORGE PIPELINE                       │
├────────────────────────────────────────────────────────┤
│                                                        │
│  GLOB avatar_P*.* dans IN/                            │
│         │                                              │
│         ▼  (pour chaque avatar)                        │
│                                                        │
│  1. Detecter le format (extension)                     │
│  2. Importer avec le bon ops.import :                  │
│       .glb / .gltf → import_scene.gltf()              │
│       .obj         → import_scene.obj()               │
│       .fbx         → import_scene.fbx()               │
│  3. Nettoyer la scene (orphans, camera, lights)        │
│  4. Valider : armature R15 presente ? (WARNING si non) │
│  5. Exporter → OUT/avatar_PN.blend                    │
│  6. Logger dans rapport individuel                     │
│                                                        │
│  FIN boucle → rapport_forge.json finalise              │
└────────────────────────────────────────────────────────┘
```

### Formats Supportes

| FORMAT | EXTENSION | IMPORTEUR BPY |
|---|---|---|
| glTF Binary | .glb | `bpy.ops.import_scene.gltf()` |
| glTF ASCII | .gltf | `bpy.ops.import_scene.gltf()` |
| Wavefront OBJ | .obj | `bpy.ops.import_scene.obj()` |
| Autodesk FBX | .fbx | `bpy.ops.import_scene.fbx()` |
| Autre | .* | ERREUR — loggue, skip |

---

## IV. MODULE PRINCIPAL

### forge_convert.py — Coeur du Systeme

Execute via : `blender --background --python forge_convert.py -- [args]`

**Arguments :**

| Argument | Description |
|---|---|
| `--input` | Chemin absolu de l'avatar source (tout format) |
| `--output-blend` | Chemin de sortie .blend |
| `--report-json` | Chemin du rapport JSON individuel (optionnel) |

**Logique interne :**
1. `bpy.ops.wm.read_factory_settings(use_empty=True)` — scene vide
2. Detecter extension → choisir le bon importeur
3. Importer l'avatar
4. Purger camera / lights / objets inutiles importes
5. Detecter armature — logger warning si aucune
6. Detecter noms bones R15 — logger warning si non conformes
7. `bpy.ops.wm.save_as_mainfile(filepath=output_blend)` — export BLEND
8. Ecrire rapport JSON individuel

### forge_main.ipynb — Notebook Colab

**Cellules :**

| # | Nom | Role |
|---|---|---|
| 0 | GIT SYNC | Monte Drive, clone/pull repo, copie codebase |
| 1 | SETUP | Detecte Blender, definit chemins |
| 2 | CONFIG | Liste avatars IN/, valide nommage P* |
| 3 | CONVERSION | Boucle sur N avatars, appelle forge_convert.py |
| 4 | RAPPORT | Charge et affiche rapport_forge.json |

---

## V. INPUTS REQUIS

### avatar_P*.* (deposes par l'utilisateur)

| Propriete | Valeur attendue |
|---|---|
| Nommage | avatar_P1.*, avatar_P2.*, ... (P = identifiant acteur) |
| Format | .glb, .gltf, .obj, ou .fbx |
| Contenu | Mesh du personnage + armature (optionnelle mais recommandee) |
| Taille | Pas de limite stricte — < 50 Mo recommande pour Colab |

**Remarque :** Un avatar sans armature est converti sans erreur.
Un warning est emis dans le rapport pour signaler l'absence de rig.

---

## VI. OUTPUTS PRODUITS

### avatar_PN.blend (sortie principale)

- Scene Blender propre : mesh + armature (si presente)
- Camera et lights supprimes
- Orphans purges
- Pret pour IN_AVATAR/ de FERRUS CORPUS

### rapport_forge.json

```json
{
  "generated_at": "2026-04-18T00:00:00",
  "blender_version": "4.x",
  "total_avatars": 3,
  "avatars": [
    {
      "id": "P1",
      "source_file": "avatar_P1.glb",
      "format_detected": "glb",
      "armature_found": true,
      "r15_bones_found": true,
      "output_blend": "avatar_P1.blend",
      "output_blend_size_ko": 1240,
      "status": "OK",
      "warnings": []
    },
    {
      "id": "P2",
      "source_file": "avatar_P2.obj",
      "format_detected": "obj",
      "armature_found": false,
      "r15_bones_found": false,
      "output_blend": "avatar_P2.blend",
      "output_blend_size_ko": 820,
      "status": "OK",
      "warnings": ["Aucune armature detectee — avatar sans rig"]
    }
  ]
}
```

---

## VII. NOMENCLATURE MIROIR

La cle de voute de la chaine FORGE → CORPUS :

```
IN/ de FORGE          OUT/ de FORGE         IN_AVATAR/ de CORPUS
avatar_P1.glb    →    avatar_P1.blend   →   avatar_P1.blend
avatar_P2.obj    →    avatar_P2.blend   →   avatar_P2.blend
avatar_P3.fbx    →    avatar_P3.blend   →   avatar_P3.blend
```

Le suffixe `_PN` est l'identifiant unique de l'acteur sur toute la chaine.
CORPUS associe `ferrus_P1.fbx` a `avatar_P1.blend` par ce suffixe.

---

## VIII. STACK TECHNIQUE IMPOSE

| COMPOSANT | VALEUR | CONTRAINTE |
|---|---|---|
| Plateforme | Google Colab gratuit | Runtime standard uniquement |
| GPU | INTERDIT | CPU uniquement |
| Blender | 4.x binaire headless (-b) | Stocke dans Drive/tools/ |
| Python | 3.10+ | bpy uniquement, zero pip |
| Formats entree | .glb / .gltf / .obj / .fbx | Importeurs natifs Blender |
| Temps max | < 30s par avatar | Conversion simple, pas de calcul lourd |
| Cout recurrent | ZERO euro | Tout gratuit |

---

## IX. CONTRAINTES INVIOLABLES

1. FORGE ne fait que convertir — zero injection, zero retargeting, zero rendu
2. Blender en mode headless uniquement (-b) — zero interface
3. GPU jamais utilise — CPU obligatoire
4. Nommage miroir obligatoire — `avatar_P*.blend` sans exception
5. En cas d'erreur sur un acteur : skip + log, les autres acteurs continuent
6. rapport_forge.json = seul contrat de sortie de FORGE

---

*EXODUS SYSTEM — Fregate 00_FERRUS_FORGE v1.0.0*
