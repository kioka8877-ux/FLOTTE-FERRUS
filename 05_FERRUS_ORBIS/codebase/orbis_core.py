# =============================================================================
# FERRUS ORBIS — orbis_core.py
# Fregate 05 | Pipeline Blender headless : source → GLB
# FLOTTE FERRUS | AD MAJOREM GLORIAM IMPERATORIS
#
# Deux modes :
#
#   MODE METADATA (API Roblox via orbis_fetch.py) :
#     blender --background --python orbis_core.py -- \
#       --mode METADATA \
#       --metadata /tmp/orbis_cache/metadata.json \
#       --asset-id 12345678 \
#       --output   /content/drive/.../OUT/decor_12345678.glb
#
#   MODE STUDIO_OBJ (export direct Roblox Studio) :
#     blender --background --python orbis_core.py -- \
#       --mode STUDIO_OBJ \
#       --input-file /content/drive/.../IN/map.obj \
#       --output     /content/drive/.../OUT/decor_map.glb
#
# Recyclage flotte :
#   - parse_args()        <- locus_convert.py:50
#   - factory_settings    <- forge_convert.py:83
#   - CAMERA/LIGHT purge  <- forge_convert.py:132
#   - orphans_purge       <- forge_convert.py:137
#   - join_meshes()       <- osseus_core.py:130
#   - double face         <- locus_convert.py:194
#   - op_seal_export()    <- locus_convert.py:222
#   - write_rapport()     <- locus_convert.py:250
#   - main() try/finally  <- locus_convert.py:260
#
# POUR L'EMPEROR. POUR LA FLOTTE FERRUS.
# =============================================================================

import bpy
import os
import sys
import json
import argparse
import math
import mathutils
from pathlib import Path

# =============================================================================
# ARGUMENTS
# =============================================================================

def parse_args():
    """Parse les arguments CLI Blender headless (apres --)."""
    parser = argparse.ArgumentParser(description="FERRUS ORBIS — source → GLB")
    parser.add_argument("--mode",       required=True,
                        choices=["METADATA", "STUDIO_OBJ"],
                        help="Mode pipeline : METADATA (API Roblox) ou STUDIO_OBJ (export Studio)")
    parser.add_argument("--output",     required=True, help="Chemin de sortie .glb")

    # Mode METADATA
    parser.add_argument("--metadata",   help="[METADATA] Chemin vers metadata.json (orbis_fetch)")
    parser.add_argument("--asset-id",   help="[METADATA] Asset ID Roblox (pour nommage rapport)")

    # Mode STUDIO_OBJ
    parser.add_argument("--input-file", help="[STUDIO_OBJ] Chemin vers .obj ou .fbx exporte depuis Studio")

    # Blender injecte ses propres args avant "--", on ignore tout avant
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
    else:
        argv = []
    return parser.parse_args(argv)

# =============================================================================
# OP 1 — SCENE INIT
# =============================================================================

def op_scene_init():
    """Scene Blender vierge. Recycle forge_convert.py:83."""
    print("[ORBIS][CORE] Initialisation scene vide...")
    bpy.ops.wm.read_factory_settings(use_empty=True)
    print("[ORBIS][CORE] Scene vide OK.")

# =============================================================================
# OP 2A — IMPORT STUDIO FILE (mode STUDIO_OBJ)
# =============================================================================

def op_import_studio_file(input_file: str) -> int:
    """
    Importe un fichier .obj ou .fbx exporte depuis Roblox Studio.
    Retourne le nombre d'objets MESH importes.
    """
    ext = Path(input_file).suffix.lower()
    print(f"[ORBIS][CORE] Import fichier Studio : {input_file} (format: {ext})")

    objects_before = set(bpy.context.scene.objects)

    if ext == ".obj":
        bpy.ops.wm.obj_import(filepath=input_file)
    elif ext == ".fbx":
        bpy.ops.import_scene.fbx(filepath=input_file)
    elif ext == ".glb" or ext == ".gltf":
        bpy.ops.import_scene.gltf(filepath=input_file)
    else:
        raise ValueError(f"Format non supporte : {ext}. Utiliser .glb, .obj ou .fbx depuis Roblox Studio.")

    objects_after  = set(bpy.context.scene.objects)
    new_objects    = objects_after - objects_before
    mesh_count     = sum(1 for o in new_objects if o.type == 'MESH')

    print(f"[ORBIS][CORE] Import OK : {len(new_objects)} objets ({mesh_count} MESH)")

    if mesh_count == 0:
        raise RuntimeError("Aucun objet MESH importe — verifier le fichier d'entree")

    return mesh_count

# =============================================================================
# OP 2B — RECONSTRUCTION GEOMETRIE depuis metadata (mode METADATA)
# =============================================================================

def op_build_geometry(parts: list) -> list:
    """
    Reconstruit la geometrie Roblox dans Blender depuis la liste des parts.
    - Part / WedgePart / CornerWedgePart → primitives bpy
    - MeshPart / UnionOperation → cubes placeholder (mesh binaire non charge)
    Retourne la liste des objets Blender crees.
    """
    print(f"[ORBIS][CORE] Reconstruction geometrie : {len(parts)} parts...")

    created = []
    binary_fallback_count = 0

    for part in parts:
        ptype = part.get("type", "Part")
        size  = part.get("size",     [1.0, 1.0, 1.0])
        pos   = part.get("position", [0.0, 0.0, 0.0])
        rot9  = part.get("rotation", [1,0,0, 0,1,0, 0,0,1])
        color = part.get("color",    [0.8, 0.8, 0.8])
        pid   = part.get("id", "part")

        if part.get("_binary_fallback"):
            binary_fallback_count += 1

        # ── Creer la primitive ────────────────────────────────────
        if ptype == "WedgePart":
            _add_wedge(pid, size, pos, rot9, color)
        else:
            # Block (Part, MeshPart placeholder, UnionOperation placeholder)
            bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 0))
            obj = bpy.context.active_object
            obj.name = pid
            obj.scale = (size[0], size[1], size[2])

        obj = bpy.context.active_object

        # ── Position ─────────────────────────────────────────────
        obj.location = mathutils.Vector(pos)

        # ── Rotation depuis matrice 3x3 ─────────────────────────
        m = rot9
        rot_mat = mathutils.Matrix((
            (m[0], m[1], m[2]),
            (m[3], m[4], m[5]),
            (m[6], m[7], m[8]),
        ))
        obj.rotation_euler = rot_mat.to_euler('XYZ')

        # ── Couleur de base (sera ecrasee par texture si disponible) ──
        _assign_color_material(obj, color, pid)

        created.append(obj)

    print(f"[ORBIS][CORE] {len(created)} objets crees ({binary_fallback_count} placeholders binaires)")
    return created

def _add_wedge(name: str, size: list, pos: list, rot9: list, color: list):
    """Cree un WedgePart via bmesh (triangle + rectangle = coin)."""
    import bmesh
    mesh = bpy.data.meshes.new(name)
    obj  = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)

    bm = bmesh.new()
    sx, sy, sz = size[0] / 2, size[1] / 2, size[2] / 2

    verts = [
        bm.verts.new((-sx, -sy, -sz)),
        bm.verts.new(( sx, -sy, -sz)),
        bm.verts.new(( sx,  sy, -sz)),
        bm.verts.new((-sx,  sy, -sz)),
        bm.verts.new((-sx, -sy,  sz)),
        bm.verts.new(( sx, -sy,  sz)),
    ]
    bm.faces.new([verts[0], verts[1], verts[2], verts[3]])  # fond
    bm.faces.new([verts[0], verts[1], verts[5], verts[4]])  # face avant
    bm.faces.new([verts[1], verts[2], verts[5]])             # triangle droit
    bm.faces.new([verts[0], verts[3], verts[4]])             # triangle gauche
    bm.faces.new([verts[2], verts[3], verts[4], verts[5]])   # hypotenuse

    bm.to_mesh(mesh)
    bm.free()
    mesh.update()

def _assign_color_material(obj, color: list, name: str):
    """Cree un materiau couleur uni sans texture, double face force."""
    mat = bpy.data.materials.new(f"orbis_mat_{name}")
    mat.use_nodes = True
    mat.use_backface_culling = False  # double face — accessible de l'interieur

    nt = mat.node_tree
    nt.nodes.clear()

    bsdf = nt.nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.inputs['Base Color'].default_value = (color[0], color[1], color[2], 1.0)
    bsdf.inputs['Roughness'].default_value  = 0.7

    out = nt.nodes.new('ShaderNodeOutputMaterial')
    nt.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])

    obj.data.materials.clear()
    obj.data.materials.append(mat)

# =============================================================================
# OP 3 — APPLICATION TEXTURES (mode METADATA uniquement)
# =============================================================================

def op_apply_textures(parts: list, tex_map_abs: dict):
    """
    Remplace les materiaux couleur par des materiaux texture pour les parts
    qui ont des textures resolues. Recycle le node graph de locus_convert.py:198.
    """
    print(f"[ORBIS][CORE] Application textures : {len(tex_map_abs)} textures disponibles...")

    applied = 0

    for part in parts:
        pid      = part.get("id", "")
        tex_ids  = part.get("texture_ids", [])

        if not tex_ids:
            continue

        # Trouver la premiere texture resolue pour cette part
        tex_path = None
        for tid in tex_ids:
            if tid in tex_map_abs and os.path.isfile(tex_map_abs[tid]):
                tex_path = tex_map_abs[tid]
                break

        if not tex_path:
            continue

        # Trouver l'objet Blender correspondant
        obj = bpy.data.objects.get(pid)
        if obj is None or obj.type != 'MESH':
            continue

        # Creer le materiau texture (recycle locus_convert.py:191-215)
        mat = bpy.data.materials.new(f"orbis_tex_{pid}")
        mat.use_nodes = True
        mat.use_backface_culling = False  # double face obligatoire

        # Charger et embarquer l'image
        img = bpy.data.images.load(tex_path)
        img.pack()

        nt = mat.node_tree
        nt.nodes.clear()

        uv_node   = nt.nodes.new('ShaderNodeUVMap')
        uv_node.uv_map = "UVMap"

        img_node  = nt.nodes.new('ShaderNodeTexImage')
        img_node.image       = img
        img_node.interpolation = 'Linear'

        bsdf_node = nt.nodes.new('ShaderNodeBsdfPrincipled')
        bsdf_node.inputs['Roughness'].default_value = 0.7

        out_node  = nt.nodes.new('ShaderNodeOutputMaterial')

        nt.links.new(uv_node.outputs['UV'],      img_node.inputs['Vector'])
        nt.links.new(img_node.outputs['Color'],  bsdf_node.inputs['Base Color'])
        nt.links.new(bsdf_node.outputs['BSDF'],  out_node.inputs['Surface'])

        # Smart UV Project pour les primitives (pas d'UV generees a la creation)
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.uv.smart_project(angle_limit=66.0, island_margin=0.02)
        bpy.ops.object.mode_set(mode='OBJECT')

        obj.data.materials.clear()
        obj.data.materials.append(mat)
        applied += 1

    print(f"[ORBIS][CORE] {applied} parts texturees")

# =============================================================================
# OP 4 — NETTOYAGE SCENE
# =============================================================================

def op_clean_scene() -> int:
    """
    Supprime cameras, lights et objets parasites.
    Recycle forge_convert.py:132-137.
    """
    print("[ORBIS][CORE] Nettoyage scene...")

    removed = 0
    for obj in list(bpy.context.scene.objects):
        if obj.type in ("CAMERA", "LIGHT", "SPEAKER", "LIGHT_PROBE"):
            bpy.data.objects.remove(obj, do_unlink=True)
            removed += 1

    bpy.ops.outliner.orphans_purge(do_recursive=True)
    print(f"[ORBIS][CORE] {removed} objet(s) supprimes + orphans purges")
    return removed

# =============================================================================
# OP 5 — JOIN MESHES + DOUBLE FACE GLOBAL
# =============================================================================

def op_join_and_double_face() -> bpy.types.Object:
    """
    Rejoint tous les meshes en un seul objet.
    Force double face sur tous les materiaux.
    Recycle osseus_core.py:130 + locus_convert.py:194.
    """
    mesh_objects = [o for o in bpy.context.scene.objects if o.type == 'MESH']

    if not mesh_objects:
        raise RuntimeError("Aucun objet MESH dans la scene apres reconstruction")

    print(f"[ORBIS][CORE] Join {len(mesh_objects)} mesh(es) en un objet unifie...")

    bpy.ops.object.select_all(action='DESELECT')
    for obj in mesh_objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = mesh_objects[0]

    if len(mesh_objects) > 1:
        bpy.ops.object.join()

    merged = bpy.context.active_object
    merged.name = "ORBIS_Decor"

    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

    # Double face sur TOUS les materiaux (recycle locus_convert.py:194)
    mats_patched = 0
    for slot in merged.material_slots:
        if slot.material:
            slot.material.use_backface_culling = False
            mats_patched += 1

    vc = len(merged.data.vertices)
    fc = len(merged.data.polygons)
    print(f"[ORBIS][CORE] Mesh unifie : {vc:,} vertices | {fc:,} faces")
    print(f"[ORBIS][CORE] Double face ON sur {mats_patched} materiau(x)")
    return merged

# =============================================================================
# OP 6 — SEAL : UNPACK TEXTURES + EXPORT GLB
# =============================================================================

def op_seal_export(obj: bpy.types.Object, output_path: str) -> float:
    """
    Unpack textures + export GLB.
    Recycle locus_convert.py:222 + osseus_core.py:530.
    """
    print(f"[ORBIS][CORE] Export GLB : {output_path}")

    # Unpack images embeddees avant export (recycle osseus_core.py:530)
    unpack_dir = os.path.join(os.path.dirname(output_path), "_tex_unpack")
    os.makedirs(unpack_dir, exist_ok=True)

    for img in bpy.data.images:
        if img.packed_file:
            stem = Path(img.filepath_raw or img.name).stem or img.name
            ext  = img.file_format.lower() if img.file_format else "png"
            img.filepath_raw = os.path.join(unpack_dir, f"{stem}.{ext}")
            try:
                img.unpack(method="WRITE_LOCAL")
            except Exception:
                pass  # image non packee ou deja sur disque

    # Selection unique de l'objet cible
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    # Export GLB (recycle locus_convert.py:233-240)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    bpy.ops.export_scene.gltf(
        filepath=output_path,
        export_format='GLB',
        use_selection=True,
        export_texcoords=True,
        export_normals=True,
        export_materials='EXPORT',
    )

    size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"[ORBIS][CORE] GLB produit : {output_path} ({size_mb:.2f} Mo)")
    return size_mb

# =============================================================================
# RAPPORT JSON (recycle locus_convert.py:250)
# =============================================================================

def write_rapport(output_path: str, rapport: dict):
    rapport_path = str(Path(output_path).parent / "rapport_orbis.json")
    with open(rapport_path, "w", encoding="utf-8") as f:
        json.dump(rapport, f, indent=2, ensure_ascii=False)
    print(f"[ORBIS][CORE] rapport_orbis.json : {rapport_path}")

# =============================================================================
# MAIN PIPELINE
# =============================================================================

def main():
    args = parse_args()
    mode        = args.mode
    output_path = args.output

    rapport = {
        "status":      "RUNNING",
        "mode":        mode,
        "output_glb":  output_path,
        "mesh":        {},
        "double_face": True,
        "warnings":    [],
    }

    try:
        # ── MODE STUDIO_OBJ ──────────────────────────────────────────────
        if mode == "STUDIO_OBJ":
            if not args.input_file:
                raise ValueError("--input-file requis en mode STUDIO_OBJ")

            input_file = args.input_file
            if not os.path.exists(input_file):
                raise FileNotFoundError(f"Fichier introuvable : {input_file}")

            rapport["input_file"] = input_file
            rapport["source"]     = Path(input_file).name

            # OP 1 — SCENE INIT
            op_scene_init()

            # OP 2A — IMPORT STUDIO FILE
            mesh_count = op_import_studio_file(input_file)
            rapport["mesh"]["objects_importes"] = mesh_count

            # OP 4 — NETTOYAGE (cameras, lights, orphans)
            removed = op_clean_scene()
            rapport["mesh"]["objects_supprimes"] = removed

            # OP 5 — JOIN + DOUBLE FACE
            merged = op_join_and_double_face()
            rapport["mesh"]["vertices"]    = len(merged.data.vertices)
            rapport["mesh"]["faces"]       = len(merged.data.polygons)
            rapport["mesh"]["mesh_unifie"] = True

            # OP 6 — SEAL
            size_mb = op_seal_export(merged, output_path)
            rapport["output_size_mb"] = round(size_mb, 2)
            rapport["status"] = "SUCCESS"

            label = Path(input_file).stem

        # ── MODE METADATA (API Roblox) ───────────────────────────────────
        elif mode == "METADATA":
            if not args.metadata:
                raise ValueError("--metadata requis en mode METADATA")
            if not args.asset_id:
                raise ValueError("--asset-id requis en mode METADATA")

            metadata_path = args.metadata
            asset_id      = args.asset_id

            if not os.path.exists(metadata_path):
                raise FileNotFoundError(f"metadata.json introuvable : {metadata_path}")

            with open(metadata_path, "r", encoding="utf-8") as f:
                meta = json.load(f)

            parts = meta.get("parts", [])
            if not parts:
                raise ValueError("metadata.json ne contient aucune part — orbis_fetch a echoue ?")

            meta_dir    = os.path.dirname(metadata_path)
            tex_map_rel = meta.get("textures", {}).get("map", {})
            tex_map_abs = {
                tid: os.path.join(meta_dir, rel_path)
                for tid, rel_path in tex_map_rel.items()
            }

            rapport["asset_id"]  = asset_id
            rapport["format"]    = meta.get("format", "?")
            rapport["textures"]  = {
                "total":   meta.get("textures", {}).get("total", 0),
                "resolues": meta.get("textures", {}).get("resolues", 0),
                "privees": meta.get("textures", {}).get("privees", 0),
            }
            rapport["warnings"] = meta.get("warnings", [])

            # OP 1 — SCENE INIT
            op_scene_init()

            # OP 2B — RECONSTRUCTION GEOMETRIE
            created = op_build_geometry(parts)
            rapport["mesh"]["parts_roblox"]   = len(parts)
            rapport["mesh"]["objects_crees"]  = len(created)

            # OP 3 — APPLICATION TEXTURES
            op_apply_textures(parts, tex_map_abs)

            # OP 4 — NETTOYAGE
            removed = op_clean_scene()
            rapport["mesh"]["objects_supprimes"] = removed

            # OP 5 — JOIN + DOUBLE FACE
            merged = op_join_and_double_face()
            rapport["mesh"]["vertices"]    = len(merged.data.vertices)
            rapport["mesh"]["faces"]       = len(merged.data.polygons)
            rapport["mesh"]["mesh_unifie"] = True

            # OP 6 — SEAL
            size_mb = op_seal_export(merged, output_path)
            rapport["output_size_mb"] = round(size_mb, 2)
            rapport["status"] = "SUCCESS"

            label = f"Asset {asset_id}"

    except Exception as e:
        rapport["status"] = "ERROR"
        rapport["error"]  = str(e)
        print(f"[ORBIS][CORE] ERREUR : {e}")
        import traceback
        traceback.print_exc()
        raise

    finally:
        write_rapport(output_path, rapport)

    print()
    print("[ORBIS][CORE] ══════════════════════════════════════")
    print(f"[ORBIS][CORE] PIPELINE COMPLET — {label}")
    print(f"[ORBIS][CORE]   Mode     : {mode}")
    print(f"[ORBIS][CORE]   Vertices : {rapport['mesh'].get('vertices', '?'):,}" if isinstance(rapport['mesh'].get('vertices'), int) else f"[ORBIS][CORE]   Vertices : ?")
    print(f"[ORBIS][CORE]   Faces    : {rapport['mesh'].get('faces', '?'):,}" if isinstance(rapport['mesh'].get('faces'), int) else f"[ORBIS][CORE]   Faces    : ?")
    print(f"[ORBIS][CORE]   GLB      : {rapport.get('output_size_mb', '?')} Mo")
    print("[ORBIS][CORE] POUR L'EMPEROR.")
    print("[ORBIS][CORE] ══════════════════════════════════════")

if __name__ == "__main__":
    main()
