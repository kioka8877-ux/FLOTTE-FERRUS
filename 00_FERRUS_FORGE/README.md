# FERRUS FORGE — Fregate 00

**AD MAJOREM GLORIAM IMPERATORIS**

---

## Mission

Convertir tout avatar brut (`.glb`, `.gltf`, `.obj`, `.fbx`) en fichier `.blend`
propre et exploitable par FERRUS CORPUS.

Un avatar entre. Un `.blend` sort. Rien d'autre.

---

## Position dans la Flotte

```
FERRUS FORGE  (00)  →  avatar brut → .blend
FERRUS ANIMUS (01)  →  video/mocap → FBX R15 animes
FERRUS CORPUS (02)  →  FBX + .blend → output final viewable
```

FORGE est la fregate de pre-processing. Elle tourne une fois pour preparer les avatars,
puis CORPUS les utilise indefiniment.

---

## Workflow

```
IN/
  avatar_P1.glb   ┐
  avatar_P2.obj   │  →  forge_convert.py (Blender headless)
  avatar_P3.fbx   ┘
                           │
                           ▼
                       OUT/
                         avatar_P1.blend
                         avatar_P2.blend
                         avatar_P3.blend
                         rapport_forge.json
                           │
                           ▼
                  FERRUS CORPUS IN_AVATAR/
```

---

## Nomenclature Miroir

La cle de toute la chaine :

| IN/ | OUT/ | CORPUS IN_AVATAR/ |
|---|---|---|
| avatar_P1.glb | avatar_P1.blend | avatar_P1.blend |
| avatar_P2.obj | avatar_P2.blend | avatar_P2.blend |
| avatar_P3.fbx | avatar_P3.blend | avatar_P3.blend |

Le suffixe `_P*` identifie l'acteur sur toute la chaine FORGE → CORPUS.

---

## Structure

```
00_FERRUS_FORGE/
  IN/                        <- Deposer les avatars bruts ici
  OUT/                       <- Recuperer les .blend ici
  codebase/
    forge_convert.py         <- Script Blender headless (coeur)
    forge_main.ipynb         <- Notebook Colab
    docs/
      FORGE_STATE.md         <- Phylactere de Resurrection
      FORGE_PRD.md           <- Bible Technique
      FORGE_ROADMAP.md       <- Plan de Conquete
      FORGE_VALIDATION.md    <- Protocole de Test
```

---

## Utilisation

1. Deposer les avatars dans `IN/` avec le nommage `avatar_P1.*`, `avatar_P2.*`, etc.
2. Ouvrir `forge_main.ipynb` dans Google Colab
3. Executer les cellules de haut en bas
4. Recuperer les `.blend` dans `OUT/`
5. Copier les `.blend` dans `IN_AVATAR/` de FERRUS CORPUS

---

## Formats Supportes

| Format | Extension | Support |
|---|---|---|
| glTF Binary | .glb | Natif Blender |
| glTF ASCII | .gltf | Natif Blender |
| Wavefront OBJ | .obj | Natif Blender |
| Autodesk FBX | .fbx | Natif Blender |

---

## Statut

**PLANIFICATION** — Developpement a venir.

Voir `codebase/docs/FORGE_STATE.md` pour l'etat detaille.

---

*POUR L'EMPEROR. POUR LA FLOTTE FERRUS.*
