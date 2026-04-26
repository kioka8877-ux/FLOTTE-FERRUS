# =============================================================================
# FERRUS ORBIS — orbis_fetch.py
# Fregate 05 | Extraction HTTP Roblox → metadata JSON + textures
# FLOTTE FERRUS | AD MAJOREM GLORIAM IMPERATORIS
#
# Ce script tourne en Python pur sur Colab (pas de bpy).
# Il interroge les API Roblox, parse le .rbxm/.rbxmx, telecharge
# les textures CDN et produit un metadata.json consomme par orbis_core.py.
#
# Usage :
#   python orbis_fetch.py --asset-id 12345678 --out-dir /tmp/orbis_cache/
#   python orbis_fetch.py --keyword "brookhaven street" --out-dir /tmp/orbis_cache/
#
# POUR L'EMPEROR. POUR LA FLOTTE FERRUS.
# =============================================================================

import os
import sys
import json
import time
import re
import argparse
import hashlib
from pathlib import Path

try:
    import requests
except ImportError:
    print("[ORBIS][FETCH] ERREUR — 'requests' manquant. Installer : pip install requests")
    sys.exit(1)

try:
    import xml.etree.ElementTree as ET
except ImportError:
    print("[ORBIS][FETCH] ERREUR — xml.etree.ElementTree manquant (Python standard)")
    sys.exit(1)

# =============================================================================
# CONFIGURATION
# =============================================================================

ROBLOX_CATALOG_SEARCH  = "https://catalog.roblox.com/v1/search/items"
ROBLOX_ASSET_DELIVERY  = "https://assetdelivery.roblox.com/v1/asset/"
ROBLOX_ASSET_DETAILS   = "https://economy.roblox.com/v2/assets/{asset_id}/details"

CDN_RETRY_COUNT  = 3
CDN_RETRY_SLEEP  = 1.0   # secondes entre retries

# Roblox Y-up → Blender Z-up (factor studs → metres : 1 stud = 0.28m)
STUD_TO_METER = 0.28

# Signature binaire du format .rbxm
RBXM_BINARY_MAGIC = b"<roblox!"

# Signature XML du format .rbxmx
RBXM_XML_PREFIX   = b"<roblox"

# Types de Part valides a extraire
ROBLOX_MESH_CLASSES = {"Part", "MeshPart", "UnionOperation", "WedgePart", "CornerWedgePart"}

# Classes a supprimer (bruit Roblox)
ROBLOX_JUNK_CLASSES = {
    "Script", "LocalScript", "ModuleScript",
    "PointLight", "SurfaceLight", "SpotLight",
    "Sound", "Beam", "ParticleEmitter",
    "SelectionBox", "Explosion",
    "Smoke", "Fire", "Sparkles",
}

# =============================================================================
# ARGUMENTS
# =============================================================================

def parse_args():
    parser = argparse.ArgumentParser(description="FERRUS ORBIS — Extraction Roblox → metadata")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--asset-id", type=str, help="Asset ID Roblox (numerique)")
    group.add_argument("--keyword",  type=str, help="Mot-cle de recherche marketplace")
    parser.add_argument("--out-dir", required=True, help="Dossier de sortie pour cache + metadata")
    return parser.parse_args()

# =============================================================================
# ETAPE 1 — RESOLUTION ASSET ID (mode KEYWORD)
# =============================================================================

def resolve_keyword_to_asset_id(keyword: str) -> str:
    """Cherche sur le marketplace Roblox et retourne le premier asset ID pertinent."""
    print(f"[ORBIS][FETCH] Recherche keyword : '{keyword}'")

    params = {
        "keyword":    keyword,
        "category":   "Models",
        "limit":      10,
        "sortType":   1,  # Relevance
    }
    resp = requests.get(ROBLOX_CATALOG_SEARCH, params=params, timeout=15)
    resp.raise_for_status()

    data  = resp.json()
    items = data.get("data", [])

    if not items:
        raise ValueError(f"Aucun resultat pour le keyword : '{keyword}'")

    # Premier resultat de type Asset (pas Bundle)
    for item in items:
        if item.get("itemType") == "Asset":
            asset_id = str(item["id"])
            name     = item.get("name", "?")
            print(f"[ORBIS][FETCH] Asset trouve : {name} (ID: {asset_id})")
            return asset_id

    raise ValueError(f"Aucun asset valide trouve pour : '{keyword}'")

# =============================================================================
# ETAPE 2 — TELECHARGEMENT .rbxm / .rbxmx
# =============================================================================

def download_rbxm(asset_id: str, out_dir: str) -> tuple[str, str]:
    """
    Telecharge le fichier .rbxm ou .rbxmx depuis assetdelivery.
    Retourne (chemin_local, format_detecte) avec format = 'xml' ou 'binary'.
    """
    print(f"[ORBIS][FETCH] Telechargement asset ID {asset_id}...")

    url  = ROBLOX_ASSET_DELIVERY
    resp = requests.get(url, params={"id": asset_id}, timeout=30, allow_redirects=True)
    resp.raise_for_status()

    content = resp.content

    if not content:
        raise ValueError(f"Asset {asset_id} vide — peut etre prive ou inexistant")

    # Detection format
    if content.startswith(RBXM_BINARY_MAGIC):
        fmt = "binary"
    elif content[:10].lstrip().startswith(RBXM_XML_PREFIX):
        fmt = "xml"
    else:
        # Tentative : peut etre du texte XML avec BOM ou whitespace
        try:
            content.decode("utf-8")
            fmt = "xml"
        except Exception:
            fmt = "binary"

    ext  = ".rbxmx" if fmt == "xml" else ".rbxm"
    path = os.path.join(out_dir, f"asset_{asset_id}{ext}")

    with open(path, "wb") as f:
        f.write(content)

    size_kb = len(content) // 1024
    print(f"[ORBIS][FETCH] Fichier sauvegarde : {path} ({size_kb} Ko) [format: {fmt}]")
    return path, fmt

# =============================================================================
# ETAPE 3A — PARSE XML (.rbxmx)
# =============================================================================

def parse_rbxmx(file_path: str) -> list[dict]:
    """
    Parse un fichier .rbxmx (XML Roblox) et retourne la liste des parts.
    Chaque part : {id, type, shape, size_x/y/z, pos_x/y/z, rot_matrix, texture_ids, color_rgb}
    """
    print(f"[ORBIS][FETCH] Parse XML : {file_path}")

    tree = ET.parse(file_path)
    root = tree.getroot()

    parts    = []
    part_idx = 0

    for item in root.iter("Item"):
        cls = item.get("class", "")

        # Supprimer les classes bruit
        if cls in ROBLOX_JUNK_CLASSES:
            continue

        # Garder uniquement les parties geometriques
        if cls not in ROBLOX_MESH_CLASSES:
            continue

        part = {
            "id":          f"part_{part_idx:04d}",
            "type":        cls,
            "shape":       "Block",
            "size":        [4.0, 1.2, 4.0],    # stud → metre converti plus bas
            "position":    [0.0, 0.0, 0.0],
            "rotation":    [1,0,0, 0,1,0, 0,0,1],
            "color":       [0.8, 0.8, 0.8],
            "texture_ids": [],
            "mesh_id":     None,
        }

        props = item.find("Properties")
        if props is None:
            continue

        # ── Taille ────────────────────────────────────────────
        size_el = props.find("./Vector3[@name='Size']")
        if size_el is not None:
            x = _float(size_el.find("X"))
            y = _float(size_el.find("Y"))
            z = _float(size_el.find("Z"))
            # Roblox Y-up → Blender Z-up + studs → metres
            part["size"] = [x * STUD_TO_METER, z * STUD_TO_METER, y * STUD_TO_METER]

        # ── CFrame / CoordinateFrame ──────────────────────────
        cf = (props.find("./CoordinateFrame[@name='CFrame']") or
              props.find("./CFrame[@name='CFrame']"))
        if cf is not None:
            px = _float(cf.find("X")); py = _float(cf.find("Y")); pz = _float(cf.find("Z"))
            # Roblox Y-up → Blender Z-up : swap Y et Z pour la position
            part["position"] = [px * STUD_TO_METER, pz * STUD_TO_METER, py * STUD_TO_METER]
            r00 = _float(cf.find("R00")); r01 = _float(cf.find("R01")); r02 = _float(cf.find("R02"))
            r10 = _float(cf.find("R10")); r11 = _float(cf.find("R11")); r12 = _float(cf.find("R12"))
            r20 = _float(cf.find("R20")); r21 = _float(cf.find("R21")); r22 = _float(cf.find("R22"))
            part["rotation"] = [r00, r01, r02, r10, r11, r12, r20, r21, r22]

        # ── Couleur ───────────────────────────────────────────
        color_el = props.find("./Color3uint8[@name='Color3uint8']")
        if color_el is not None:
            val = int(color_el.text or 0)
            r = ((val >> 16) & 0xFF) / 255.0
            g = ((val >>  8) & 0xFF) / 255.0
            b = ( val        & 0xFF) / 255.0
            part["color"] = [r, g, b]

        # ── Texture IDs (Decal, SurfaceAppearance) ────────────
        for tex_prop in props.findall("./string[@name='TextureID']"):
            tid = _extract_asset_id(tex_prop.text or "")
            if tid:
                part["texture_ids"].append(tid)

        for tex_prop in props.findall("./Content[@name='TextureID']"):
            url_el = tex_prop.find("url") or tex_prop.find("null")
            if url_el is not None and url_el.text:
                tid = _extract_asset_id(url_el.text)
                if tid:
                    part["texture_ids"].append(tid)

        # ── MeshId (MeshPart) ─────────────────────────────────
        mesh_el = props.find("./string[@name='MeshId']")
        if mesh_el is None:
            mesh_el = props.find("./Content[@name='MeshId']")
        if mesh_el is not None:
            raw = (mesh_el.find("url").text if mesh_el.find("url") is not None else mesh_el.text) or ""
            part["mesh_id"] = _extract_asset_id(raw)

        # ── Forme (Part) ──────────────────────────────────────
        shape_el = props.find("./token[@name='shape']")
        if shape_el is None:
            shape_el = props.find("./string[@name='shape']")
        if shape_el is not None:
            part["shape"] = shape_el.text or "Block"

        parts.append(part)
        part_idx += 1

    print(f"[ORBIS][FETCH] XML parse OK — {len(parts)} parts extraites")
    return parts

# =============================================================================
# ETAPE 3B — PARSE BINAIRE (.rbxm) via regex fallback
# =============================================================================

def parse_rbxm_binary(file_path: str) -> list[dict]:
    """
    Parse un .rbxm binaire par scan regex pour extraire les asset IDs.
    Produit une liste de parts minimaliste (geometrie inconnue, IDs connus).
    """
    print(f"[ORBIS][FETCH] Parse binaire (regex fallback) : {file_path}")

    with open(file_path, "rb") as f:
        content = f.read()

    # Extraire tous les rbxassetid:// references
    pattern = rb"rbxassetid://(\d+)"
    matches = re.findall(pattern, content)
    asset_ids = list(dict.fromkeys(m.decode() for m in matches))  # deduplique, ordre preserve

    print(f"[ORBIS][FETCH] Binaire — {len(asset_ids)} asset IDs detectes via regex")

    if not asset_ids:
        print("[ORBIS][FETCH] WARNING — Aucun asset ID trouve dans le binaire.")
        return []

    # Generer une part placeholder par ID detecte
    parts = []
    for i, aid in enumerate(asset_ids):
        parts.append({
            "id":          f"part_{i:04d}",
            "type":        "MeshPart",
            "shape":       "Block",
            "size":        [4.0, 4.0, 4.0],
            "position":    [i * 5.0, 0.0, 0.0],  # disposition lineaire temporaire
            "rotation":    [1,0,0, 0,1,0, 0,0,1],
            "color":       [0.8, 0.8, 0.8],
            "texture_ids": [aid],
            "mesh_id":     aid,
            "_binary_fallback": True,
        })

    print(f"[ORBIS][FETCH] WARNING — Format binaire : positions/rotations inconnues.")
    print(f"[ORBIS][FETCH]           Geometrie reconstituee comme placeholders lineaires.")
    print(f"[ORBIS][FETCH]           Utiliser un asset .rbxmx pour un resultat optimal.")
    return parts

# =============================================================================
# ETAPE 4 — TELECHARGEMENT TEXTURES CDN
# =============================================================================

def download_textures(texture_ids: list[str], tex_dir: str) -> dict[str, str]:
    """
    Telecharge les textures depuis assetdelivery Roblox.
    Retourne {asset_id: chemin_local} pour les textures resolues.
    """
    os.makedirs(tex_dir, exist_ok=True)
    resolved  = {}
    private   = []

    print(f"[ORBIS][FETCH] Telechargement {len(texture_ids)} texture(s)...")

    for tid in texture_ids:
        # Check cache local
        cached = _find_cached_texture(tex_dir, tid)
        if cached:
            resolved[tid] = cached
            continue

        success = False
        for attempt in range(1, CDN_RETRY_COUNT + 1):
            try:
                resp = requests.get(
                    ROBLOX_ASSET_DELIVERY,
                    params={"id": tid},
                    timeout=15,
                    allow_redirects=True,
                )
                if resp.status_code == 200:
                    # Detecter extension depuis content-type
                    ct  = resp.headers.get("Content-Type", "image/png")
                    ext = ".jpg" if "jpeg" in ct else ".png"
                    out = os.path.join(tex_dir, f"{tid}{ext}")
                    with open(out, "wb") as f:
                        f.write(resp.content)
                    resolved[tid] = out
                    success = True
                    break
                elif resp.status_code in (403, 401):
                    private.append(tid)
                    break
                else:
                    time.sleep(CDN_RETRY_SLEEP)
            except Exception as e:
                if attempt < CDN_RETRY_COUNT:
                    time.sleep(CDN_RETRY_SLEEP)
                else:
                    print(f"[ORBIS][FETCH] WARNING — Texture {tid} : {e}")

        if not success and tid not in private:
            print(f"[ORBIS][FETCH] WARNING — Texture {tid} non resolue apres {CDN_RETRY_COUNT} tentatives")

        # Pause anti-rate-limit
        time.sleep(0.3)

    print(f"[ORBIS][FETCH] Textures : {len(resolved)} resolues, {len(private)} privees")
    return resolved

# =============================================================================
# ETAPE 5 — ECRITURE METADATA JSON
# =============================================================================

def write_metadata(out_dir: str, asset_id: str, fmt: str,
                   parts: list[dict], textures_map: dict, warnings: list) -> str:
    """Ecrit metadata.json dans out_dir. Retourne le chemin du fichier."""

    # Collecter tous les texture_ids uniques depuis les parts
    all_tex_ids = list(dict.fromkeys(
        tid for p in parts for tid in p.get("texture_ids", [])
    ))
    all_mesh_ids = list(dict.fromkeys(
        p["mesh_id"] for p in parts if p.get("mesh_id")
    ))

    # Compter textures resolues / privees
    resolved_count = len(textures_map)
    total_count    = len(all_tex_ids)
    private_count  = total_count - resolved_count

    # Reconstruire le chemin relatif des textures
    tex_relative = {
        tid: os.path.relpath(path, out_dir)
        for tid, path in textures_map.items()
    }

    metadata = {
        "asset_id":       asset_id,
        "format":         fmt,
        "parts_count":    len(parts),
        "parts":          parts,
        "textures": {
            "total":     total_count,
            "resolues":  resolved_count,
            "privees":   private_count,
            "map":       tex_relative,
        },
        "mesh_ids":   all_mesh_ids,
        "warnings":   warnings,
    }

    path = os.path.join(out_dir, "metadata.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    print(f"[ORBIS][FETCH] metadata.json ecrit : {path}")
    return path

# =============================================================================
# UTILITAIRES
# =============================================================================

def _float(el) -> float:
    """Lit un float depuis un element XML, retourne 0.0 si absent."""
    if el is None or not el.text:
        return 0.0
    try:
        return float(el.text)
    except ValueError:
        return 0.0

def _extract_asset_id(raw: str) -> str | None:
    """Extrait l'ID numerique depuis 'rbxassetid://123456' ou 'https://...id=123456'."""
    if not raw:
        return None
    m = re.search(r"(\d{6,})", raw)
    return m.group(1) if m else None

def _find_cached_texture(tex_dir: str, tid: str) -> str | None:
    """Cherche une texture deja telechargee (png ou jpg)."""
    for ext in (".png", ".jpg", ".jpeg"):
        p = os.path.join(tex_dir, f"{tid}{ext}")
        if os.path.isfile(p):
            return p
    return None

def _collect_all_texture_ids(parts: list[dict]) -> list[str]:
    """Deduplique et collecte tous les texture_ids de toutes les parts."""
    seen = {}
    for p in parts:
        for tid in p.get("texture_ids", []):
            seen[tid] = True
    return list(seen.keys())

# =============================================================================
# MAIN
# =============================================================================

def main():
    args    = parse_args()
    out_dir = args.out_dir
    os.makedirs(out_dir, exist_ok=True)
    tex_dir = os.path.join(out_dir, "textures")
    warnings = []

    print("[ORBIS][FETCH] ══════════════════════════════════════")
    print("[ORBIS][FETCH] FERRUS ORBIS — Phase Extraction HTTP")
    print("[ORBIS][FETCH] ══════════════════════════════════════")

    # ── ETAPE 1 : Resolution asset_id ────────────────────────────
    if args.keyword:
        try:
            asset_id = resolve_keyword_to_asset_id(args.keyword)
        except Exception as e:
            print(f"[ORBIS][FETCH] ERREUR resolution keyword : {e}")
            sys.exit(1)
    else:
        asset_id = args.asset_id
        print(f"[ORBIS][FETCH] Mode ASSET_ID : {asset_id}")

    # ── ETAPE 2 : Telechargement ──────────────────────────────────
    try:
        rbxm_path, fmt = download_rbxm(asset_id, out_dir)
    except Exception as e:
        print(f"[ORBIS][FETCH] ERREUR telechargement : {e}")
        sys.exit(1)

    # ── ETAPE 3 : Parse ───────────────────────────────────────────
    try:
        if fmt == "xml":
            parts = parse_rbxmx(rbxm_path)
        else:
            parts = parse_rbxm_binary(rbxm_path)
            warnings.append(
                "Format binaire .rbxm : geometrie approchee (regex fallback). "
                "Utiliser un asset .rbxmx pour un resultat optimal."
            )
    except ET.ParseError as e:
        print(f"[ORBIS][FETCH] ERREUR parse XML : {e} — tentative fallback binaire")
        parts = parse_rbxm_binary(rbxm_path)
        warnings.append(f"Parse XML echoue ({e}) — fallback binaire utilise")
    except Exception as e:
        print(f"[ORBIS][FETCH] ERREUR parse : {e}")
        sys.exit(1)

    if not parts:
        print("[ORBIS][FETCH] ERREUR — Aucune part extraite. Asset incompatible.")
        sys.exit(1)

    # ── ETAPE 4 : Textures ───────────────────────────────────────
    all_tex_ids  = _collect_all_texture_ids(parts)
    textures_map = download_textures(all_tex_ids, tex_dir)

    for tid in all_tex_ids:
        if tid not in textures_map:
            warnings.append(f"Texture {tid} inaccessible (privee ou CDN timeout)")

    # ── ETAPE 5 : Metadata JSON ───────────────────────────────────
    metadata_path = write_metadata(out_dir, asset_id, fmt, parts, textures_map, warnings)

    # ── BILAN ────────────────────────────────────────────────────
    print()
    print("[ORBIS][FETCH] ══════════════════════════════════════")
    print(f"[ORBIS][FETCH] EXTRACTION COMPLETE")
    print(f"[ORBIS][FETCH]   Asset ID  : {asset_id}")
    print(f"[ORBIS][FETCH]   Format    : {fmt}")
    print(f"[ORBIS][FETCH]   Parts     : {len(parts)}")
    print(f"[ORBIS][FETCH]   Textures  : {len(textures_map)}/{len(all_tex_ids)} resolues")
    if warnings:
        for w in warnings:
            print(f"[ORBIS][FETCH]   WARNING   : {w}")
    print(f"[ORBIS][FETCH]   Metadata  : {metadata_path}")
    print("[ORBIS][FETCH] ══════════════════════════════════════")
    print("[ORBIS][FETCH] POUR L'EMPEROR.")

if __name__ == "__main__":
    main()
