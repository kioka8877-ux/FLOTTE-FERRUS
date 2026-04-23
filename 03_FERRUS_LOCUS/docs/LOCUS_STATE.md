# LOCUS_STATE.md — Phylactere de Resurrection
# FERRUS LOCUS | Fregate 03
# FLOTTE FERRUS

---

## Etat Courant : EN_DEVELOPPEMENT

**Date derniere mise a jour :** 2026-04-23

---

## Checklist Dev

| Composant | Etat |
|-----------|------|
| Structure dossiers | TERMINE |
| `locus_convert.py` — OP MESH (import PLY + nettoyage) | TERMINE |
| `locus_convert.py` — OP BAKE (UV + projection 360) | TERMINE |
| `locus_convert.py` — OP SEAL (export GLB) | TERMINE |
| `locus_convert.py` — Decimation Option C (auto) | TERMINE |
| `locus_convert.py` — Rapport JSON | TERMINE |
| `locus_main.ipynb` — Notebook Colab 6 cellules | TERMINE |
| `README.md` | TERMINE |
| Tests en production | A_FAIRE |

---

## Prochaine Action

Fournir un fichier `.ply` + image 360deg Hunyuan3D pour validation en production.

---

## Points de Vigilance

- **Memoire Colab** : si mesh > 5M faces, forcer `DECIMATION_LEVEL = 'low'` avant de lancer
- **Bake resolution** : reduire a 1024x1024 si Colab sature (`BAKE_RESOLUTION = 1024`)
- **Orientation 360** : si la texture semble tournee, ajuster la rotation du world dans le script
- **Format PLY** : Hunyuan3D produit des PLY avec vertex colors — le bake 360 ecrase ces couleurs (comportement attendu)

---

*POUR L'EMPEROR. POUR LA FLOTTE FERRUS.*
