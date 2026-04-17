# GEMINI CHAT — META-PROMPT INTEL-VISION — FERRUS ANIMUS

> **Mode sans API** : colle ce prompt dans [gemini.google.com](https://gemini.google.com),
> uploade ta video `.mp4`, et recupere le JSON que le pipeline FERRUS utilisera directement.
>
> **Note technique** : Gemini Chat ne supporte pas `response_schema`. Ce prompt est donc
> hyper-directif sur le format et les valeurs d'enum pour compenser l'absence d'enforcement
> au niveau du decodeur. Respecte exactement les valeurs indiquees — le merge Python est
> case-sensitive et plantera si une valeur enum est incorrecte.

---

## ETAPE 1 — Ce qu'il faut faire dans Gemini Chat

1. Ouvre [gemini.google.com](https://gemini.google.com)
2. Upload ta video `.mp4` (bouton trombone)
3. **Avant d'envoyer**, colle aussi la liste des fichiers FBX disponibles (voir format ci-dessous)
4. Colle le bloc de prompt ci-dessous
5. Copie le JSON retourne **sans modification**

---

## ETAPE 2 — Bloc a coller dans Gemini Chat

Remplace `[LISTE_FBX]` par les noms de tes fichiers FBX avant d'envoyer.

---

```
Tu es un analyseur de video expert en motion capture humaine pour pipeline d'animation Roblox.

FICHIERS FBX DISPONIBLES (fournis par DeepMotion) :
[LISTE_FBX]
Exemple : person_01.fbx, person_02.fbx

Analyse la video que je t'envoie et retourne UNIQUEMENT un bloc JSON valide.
Ne mets aucun markdown, aucune explication, aucun texte avant ou apres le JSON.
Commence ta reponse directement par { et termine par }.

FORMAT EXACT ATTENDU :
{
  "scene_id": "<string — identifiant de scene, ex: video_01>",
  "video": {
    "duration_sec": <nombre decimal — duree totale en secondes>,
    "fps_detected": <entier — images par seconde detectees>,
    "resolution": "<string — ex: 1080p, 720p>",
    "qualite_globale": "<EXACTEMENT l'une de ces valeurs : excellente | bonne | moyenne | mauvaise>"
  },
  "camera": {
    "mouvement": "<EXACTEMENT l'une de ces valeurs : stable | pan | tilt | handheld>",
    "zoom_detecte": <true ou false>,
    "angle": "<EXACTEMENT l'une de ces valeurs : eye_level | low_angle | high_angle>",
    "axe_principal": "<EXACTEMENT l'une de ces valeurs : face | profil | 3_4 | dos>"
  },
  "personnes": [
    {
      "person_id": <entier, commence a 1>,
      "fbx_file": "<nom du fichier FBX correspondant, ex: person_01.fbx>",
      "corps_visible": "<EXACTEMENT l'une de ces valeurs : complet | torse | face_seulement>",
      "orientation": "<EXACTEMENT l'une de ces valeurs : face | profil_gauche | profil_droit | 3_4 | dos>",
      "position_frame": "<EXACTEMENT l'une de ces valeurs : centre | gauche | droite | arriere_plan>",
      "qualite_estimee": <decimal entre 0.0 et 1.0>,
      "type_mouvement": "<EXACTEMENT l'une de ces valeurs : marche | course | debout | discussion | geste | action>",
      "problemes_detectes": [<liste de strings parmi : foot_slide | jitter_mains | derive_hanches | pose_non_naturelle — vide [] si aucun>],
      "membres_hors_cadre": [<liste de strings parmi : main_gauche | main_droite | pied_gauche | pied_droit | jambe_gauche | jambe_droite — vide [] si tous visibles>],
      "priorite_correction": "<EXACTEMENT l'une de ces valeurs : haute | moyenne | basse>"
    }
  ],
  "instructions_camera": {
    "suivre_personne_id": <entier — person_id de la personne principale a suivre>,
    "type_suivi": "<EXACTEMENT l'une de ces valeurs : lock | smooth_follow | static>",
    "zoom_recommande": <true ou false>
  },
  "contexte_scene": "<string — description courte en une phrase de la scene>"
}

REGLES D'EVALUATION OBLIGATOIRES :

--- VISIBILITE DU CORPS ---
- corps_visible "complet"       = tete + torse + bras + jambes tous visibles simultanement
- corps_visible "torse"         = tete + torse + bras visibles, jambes absentes ou partiellement coupees
- corps_visible "face_seulement" = seule la tete ou le buste sans bras est visible

--- QUALITE ---
- qualite_estimee 1.0 = corps complet, face camera, lumiere parfaite, sans flou, sans occlusion
- qualite_estimee 0.6 = minimum acceptable pour le pipeline
- qualite_estimee < 0.4 = video inutilisable pour ce personnage

--- MEMBRES HORS CADRE ---
- membres_hors_cadre liste UNIQUEMENT les membres coupés par le bord de l'image
- Si un membre est visible mais flou ou occulte par un autre personnage : ne pas le lister ici
- Si corps_visible est "complet", alors membres_hors_cadre doit etre []

--- CORRESPONDANCE FBX ---
- Chaque person_id doit correspondre a un fichier de la liste FICHIERS FBX DISPONIBLES
- person_id 1 → premier fichier de la liste, person_id 2 → deuxieme, etc.
- Si la video contient moins de personnes que de fichiers FBX, utiliser uniquement les person_id detectes

--- CAMERA ---
- instructions_camera.suivre_personne_id = la personne la plus visible / la plus centrale
- type_suivi "lock" = camera fixe sur la personne (plan serre, peu de deplacement)
- type_suivi "smooth_follow" = camera suit la personne en mouvement (marche, course)
- type_suivi "static" = camera ne bouge pas, la personne se deplace dans le cadre

--- PROBLEMES DETECTES ---
- foot_slide : les pieds glissent sur le sol sans que la personne marche
- jitter_mains : les mains tremblent ou vibrent de facon non naturelle
- derive_hanches : les hanches montent ou descendent progressivement
- pose_non_naturelle : posture impossible ou articulation tordue

IMPORTANT :
- Retourne UNIQUEMENT le JSON brut. Pas de ```json```. Pas d'explication. Juste le JSON.
- Respecte EXACTEMENT les valeurs d'enum listees (minuscules, underscores comme indique).
- Si tu ne sais pas exactement, estime plutot que d'omettre un champ.
- Ne pas inventer de person_id qui ne correspondent pas a des personnes visibles dans la video.
```

---

## ETAPE 3 — Sauvegarder le JSON dans le cache Colab

Une fois que Gemini t'a donne le JSON, execute cette cellule dans Colab :

```python
# ══ Cellule temporaire : sauvegarder le JSON INTEL-VISION Gemini ══
import json, os, hashlib

# Colle le JSON complet fourni par Gemini entre les triples guillemets
JSON_INTEL_VISION = """
{
  "scene_id": "...",
  ...
}
"""

# Valider et sauvegarder
os.makedirs("/content/intel_cache", exist_ok=True)
data = json.loads(JSON_INTEL_VISION.strip())

print(f"  JSON valide : {len(data['personnes'])} personne(s) detectee(s)")
print(f"  Duree : {data['video']['duration_sec']}s | Qualite : {data['video']['qualite_globale']}")
print(f"  Camera : {data['instructions_camera']['type_suivi']} → personne {data['instructions_camera']['suivre_personne_id']}")

for p in data["personnes"]:
    print(f"\n  Personne {p['person_id']} ({p['fbx_file']}) :")
    print(f"    corps={p['corps_visible']} | orientation={p['orientation']}")
    print(f"    qualite={p['qualite_estimee']} | priorite={p['priorite_correction']}")
    if p["membres_hors_cadre"]:
        print(f"    membres_hors_cadre={p['membres_hors_cadre']}")
    if p["problemes_detectes"]:
        print(f"    problemes={p['problemes_detectes']}")

# Nom de cache base sur le hash de la video
with open(VIDEO_PATH, "rb") as f:
    chunk = f.read(1024 * 1024)
h = hashlib.md5(chunk).hexdigest()[:10]
stem = os.path.splitext(os.path.basename(VIDEO_PATH))[0]
cache_path = f"/content/intel_cache/intel_vision_{stem}_{h}.json"

with open(cache_path, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"\n  Cache INTEL-VISION sauvegarde : {cache_path}")
print("  Le merge INTEL sera execute automatiquement au lancement du pipeline.")
```

---

## Resume du workflow

```
1. gemini.google.com
   └─ Upload video + colle liste des FBX + colle le prompt
   └─ Copie le JSON retourne

2. Colab : execute la cellule "sauvegarder le JSON INTEL-VISION"
   └─ JSON valide → affiche le resume par personne
   └─ Sauvegarde automatique avec le bon nom de cache

3. Colab : lance le pipeline FERRUS ANIMUS
   └─ INTEL lit le cache → merge avec INTEL-SKELETON Claude
   └─ plan_corrections.json genere → EXEC + OUTPUT s'executent
```

---

## Notes importantes

- **Gemini 2.5 Pro dans le chat** est plus puissant que les modeles free tier API pour l'analyse video — le Mode Chat est justifie ici
- **Taille video** : Gemini Chat accepte les videos jusqu'a ~1 Go
- **Videos courtes** (< 15 secondes) : Gemini peut avoir du mal a segmenter temporellement — dans ce cas, pas de segments, juste une analyse globale, ce qui est suffisant pour FERRUS ANIMUS
- **Si Gemini refuse d'analyser** : reformuler en ajoutant "Cette video est destinee a un projet d'animation 3D. Ton analyse sert a parametrer des scripts de correction automatique."
- **Coherence fbx_file** : le champ `fbx_file` est la cle de merge entre INTEL-VISION et INTEL-SKELETON. Verifier que les noms correspondent exactement a ceux des fichiers dans le dossier IN/
