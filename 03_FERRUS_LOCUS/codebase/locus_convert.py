# =============================================================================
# FERRUS LOCUS — locus_convert.py
# Fregate 03 | Pipeline PLY + Image 360deg -> GLB texture
# FLOTTE FERRUS | AD MAJOREM GLORIAM IMPERATORIS
# =============================================================================

import bpy
import os
import sys
import json
import argparse
import math
from pathlib import Path

# =============================================================================
# CONFIGURATION
# =============================================================================

SUPPORTED_PLY = {".ply"}
SUPPORTED_IMG = {".jpg", ".jpeg", ".png", ".hdr", ".exr"}

# Decimation Option C : auto par defaut, override manuel possible
# "auto"   = detection automatique selon nb de faces
# "none"   = mesh original intact
# "high"   = garde 25% des faces
# "medium" = garde 10% des faces
# "low"    = garde 3% des faces
DECIMATION_LEVEL = "auto"

DECIMATION_RATIO = {
    "none"  : 1.0,
    "high"  : 0.25,
    "medium": 0.10,
    "low"   : 0.03,
}

DECIMATION_AUTO_THRESHOLDS = {
    5_000_000: "low",
    1_000_000: "medium",
    300_000  : "high",
    0        : "none",
}

BAKE_RESOLUTION = 2048  # pixels (2048x2048)

# =============================================================================
# ARGUMENTS
# =============================================================================

def parse_args():
    parser = argparse.ArgumentParser(description="FERRUS LOCUS — PLY + 360 -> GLB")
    parser.add_argument("--ply",    required=True,  help="Chemin vers le fichier .ply")
    parser.add_argument("--img360", required=True,  help="Chemin vers l'image 360 (jpg/png/hdr)")
    parser.add_argument("--output", required=True,  help="Chemin de sortie .glb")
    parser.add_argument("--decim",  default="auto",
                        choices=["auto", "none", "high", "medium", "low"],
                        help="Niveau de decimation (defaut: auto)")
    parser.add_argument("--bake-res", type=int, default=2048,
                        help="Resolution de baking en pixels (defaut: 2048)")
    # Blender passe ses propres args avant "--", on ignore tout avant
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
    else:
        argv = []
    return parser.parse_args(argv)

# =============================================================================
# OP 1 — MESH : Import PLY + nettoyage
# =============================================================================

def op_mesh_import(ply_path: str) -> bpy.types.Object:
    """Importe le .ply, nettoie le mesh, retourne l'objet Blender."""
    print(f"[LOCUS][MESH] Import: {ply_path}")

    # Purger la scene par defaut
    bpy.ops.wm.read_factory_settings(use_empty=True)

    # Import PLY
    bpy.ops.wm.ply_import(filepath=ply_path)
    obj = bpy.context.selected_objects[0]
    bpy.context.view_layer.objects.active = obj

    face_count = len(obj.data.polygons)
    vert_count = len(obj.data.vertices)
    print(f"[LOCUS][MESH] Vertices: {vert_count:,} | Faces apres import: {face_count:,}")

    # Si point cloud (0 faces) — reconstruction via convex hull bmesh
    if face_count == 0 and vert_count > 0:
        print("[LOCUS][MESH] Point cloud detecte — convex hull bmesh...")
        import bmesh as _bmesh
        bm = _bmesh.new()
        bm.from_mesh(obj.data)
        result = _bmesh.ops.convex_hull(bm, input=bm.verts, use_existing_faces=False)
        interior = [g for g in result.get('geom_interior', [])
                    if isinstance(g, _bmesh.types.BMVert)]
        unused   = [g for g in result.get('geom_unused', [])
                    if isinstance(g, _bmesh.types.BMVert)]
        _bmesh.ops.delete(bm, geom=interior + unused, context='VERTS')
        bm.to_mesh(obj.data)
        bm.free()
        obj.data.update()
        face_count = len(obj.data.polygons)
        print(f"[LOCUS][MESH] Faces apres convex hull: {face_count:,}")

    return obj

# =============================================================================
# OP 1b — DECIMATION : Reduction du maillage
# =============================================================================

def resolve_decimation_level(obj: bpy.types.Object, level: str) -> str:
    """Resout le niveau effectif si mode auto."""
    if level != "auto":
        return level
    face_count = len(obj.data.polygons)
    for threshold in sorted(DECIMATION_AUTO_THRESHOLDS.keys(), reverse=True):
        if face_count >= threshold:
            resolved = DECIMATION_AUTO_THRESHOLDS[threshold]
            print(f"[LOCUS][DECIM] Auto: {face_count:,} faces -> niveau '{resolved}'")
            return resolved
    return "none"

def op_decimate(obj: bpy.types.Object, level: str):
    """Applique un modificateur Decimate selon le niveau."""
    effective_level = resolve_decimation_level(obj, level)
    ratio = DECIMATION_RATIO.get(effective_level, 1.0)

    if ratio >= 1.0:
        print("[LOCUS][DECIM] Pas de decimation appliquee.")
        return

    face_before = len(obj.data.polygons)
    mod = obj.modifiers.new(name="LOCUS_Decimate", type='DECIMATE')
    mod.ratio = ratio
    bpy.ops.object.modifier_apply(modifier=mod.name)
    face_after = len(obj.data.polygons)
    print(f"[LOCUS][DECIM] {face_before:,} -> {face_after:,} faces (ratio {ratio})")

# =============================================================================
# OP 2 — BAKE : Projection UV + baking de la texture 360
# =============================================================================

def op_bake_texture(obj: bpy.types.Object, img360_path: str, bake_res: int):
    """Projette l'image 360 sur le mesh via UV baking."""
    print(f"[LOCUS][BAKE] Image 360: {img360_path} | Resolution: {bake_res}x{bake_res}")

    # --- Scene world : charger l'image 360 comme environment ---
    world = bpy.data.worlds.new("LOCUS_World")
    bpy.context.scene.world = world
    world.use_nodes = True
    wnt = world.node_tree
    wnt.nodes.clear()

    bg_node  = wnt.nodes.new('ShaderNodeBackground')
    env_node = wnt.nodes.new('ShaderNodeTexEnvironment')
    out_node = wnt.nodes.new('ShaderNodeOutputWorld')

    img360 = bpy.data.images.load(img360_path)
    env_node.image = img360

    wnt.links.new(env_node.outputs['Color'], bg_node.inputs['Color'])
    wnt.links.new(bg_node.outputs['Background'], out_node.inputs['Surface'])

    # --- UV Map : projection spherique via bmesh (compatible headless) ---
    import bmesh
    bpy.context.view_layer.objects.active = obj
    me = obj.data
    bm = bmesh.new()
    bm.from_mesh(me)
    uv_layer = bm.loops.layers.uv.new("UVMap")
    for face in bm.faces:
        for loop in face.loops:
            co = loop.vert.co.normalized()
            u = 0.5 + math.atan2(co.x, co.y) / (2 * math.pi)
            v = 0.5 - math.asin(max(-1.0, min(1.0, co.z))) / math.pi
            loop[uv_layer].uv = (u, v)
    bm.to_mesh(me)
    bm.free()
    me.update()
    print("[LOCUS][BAKE] UV spherique appliquee.")

    # --- Image cible pour baking (NON connectee au shader) ---
    bake_img = bpy.data.images.new("LOCUS_BakeTarget", width=bake_res, height=bake_res)

    # --- Materiau : projection position → TexEnvironment → Emission ---
    # (type EMIT : pas de circular dependency, capture directe de la couleur)
    mat = bpy.data.materials.new("LOCUS_Mat")
    mat.use_nodes = True
    obj.data.materials.clear()
    obj.data.materials.append(mat)

    nt = mat.node_tree
    nt.nodes.clear()

    texcoord_node = nt.nodes.new('ShaderNodeTexCoord')
    normalize_node= nt.nodes.new('ShaderNodeVectorMath')
    normalize_node.operation = 'NORMALIZE'
    env_tex_node  = nt.nodes.new('ShaderNodeTexEnvironment')
    emission_node = nt.nodes.new('ShaderNodeEmission')
    out_mat_node  = nt.nodes.new('ShaderNodeOutputMaterial')
    # Noeud bake target — NON connecte, juste selectionne
    bake_node     = nt.nodes.new('ShaderNodeTexImage')
    bake_node.image = bake_img

    env_tex_node.image = img360

    # Position objet → normalise → direction spherique → couleur 360
    nt.links.new(texcoord_node.outputs['Object'],     normalize_node.inputs[0])
    nt.links.new(normalize_node.outputs['Vector'],    env_tex_node.inputs['Vector'])
    nt.links.new(env_tex_node.outputs['Color'],       emission_node.inputs['Color'])
    nt.links.new(emission_node.outputs['Emission'],   out_mat_node.inputs['Surface'])

    # Selectionner bake_node comme cible (deconnecte = pas de circular dependency)
    for n in nt.nodes: n.select = False
    bake_node.select = True
    nt.nodes.active = bake_node

    # --- Baking EMIT : capture la couleur emise par le shader ---
    bpy.context.scene.render.engine = 'CYCLES'
    bpy.context.scene.cycles.device = 'CPU'
    bpy.context.scene.cycles.samples = 4

    print("[LOCUS][BAKE] Baking EMIT en cours (CPU)...")
    bpy.ops.object.bake(type='EMIT')
    print("[LOCUS][BAKE] Baking termine.")

    # ── FIX : recabler le materiau pour export GLB ──────────────
    # Apres bake, remplacer le shader EMIT par PrincipledBSDF + texture bakee + UV
    # Sans ce recablage, le GLB exporte un mesh noir (bake_node deconnecte)
    nt.nodes.clear()

    uv_map_node  = nt.nodes.new('ShaderNodeUVMap')
    uv_map_node.uv_map = "UVMap"

    img_tex_node = nt.nodes.new('ShaderNodeTexImage')
    img_tex_node.image = bake_img

    bsdf_node    = nt.nodes.new('ShaderNodeBsdfPrincipled')
    out_glb_node = nt.nodes.new('ShaderNodeOutputMaterial')

    nt.links.new(uv_map_node.outputs['UV'],          img_tex_node.inputs['Vector'])
    nt.links.new(img_tex_node.outputs['Color'],      bsdf_node.inputs['Base Color'])
    nt.links.new(bsdf_node.outputs['BSDF'],          out_glb_node.inputs['Surface'])

    print("[LOCUS][BAKE] Materiau recable : PrincipledBSDF + UVMap + texture bakee.")
    # ────────────────────────────────────────────────────────────

    # Sauvegarder la texture dans le GLB (pack)
    bake_img.pack()

    return bake_img

# =============================================================================
# OP 3 — SEAL : Nettoyage final + export GLB
# =============================================================================

def op_seal_export(obj: bpy.types.Object, output_path: str):
    """Verifie le mesh, exporte en .glb."""
    print(f"[LOCUS][SEAL] Export GLB: {output_path}")

    # S'assurer que seul cet objet est selectionne
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    # Export GLB
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
    print(f"[LOCUS][SEAL] Fichier produit: {output_path} ({size_mb:.2f} Mo)")
    return size_mb

# =============================================================================
# RAPPORT JSON
# =============================================================================

def write_rapport(output_path: str, rapport: dict):
    rapport_path = str(Path(output_path).parent / "rapport_locus.json")
    with open(rapport_path, "w", encoding="utf-8") as f:
        json.dump(rapport, f, indent=2, ensure_ascii=False)
    print(f"[LOCUS][RAPPORT] {rapport_path}")

# =============================================================================
# MAIN PIPELINE
# =============================================================================

def main():
    args = parse_args()

    ply_path   = args.ply
    img360_path= args.img360
    output_path= args.output
    decim_level= args.decim
    bake_res   = args.bake_res

    # Validations
    if not os.path.exists(ply_path):
        raise FileNotFoundError(f"PLY introuvable: {ply_path}")
    if not os.path.exists(img360_path):
        raise FileNotFoundError(f"Image 360 introuvable: {img360_path}")
    if Path(ply_path).suffix.lower() not in SUPPORTED_PLY:
        raise ValueError(f"Format PLY non supporte: {Path(ply_path).suffix}")
    if Path(img360_path).suffix.lower() not in SUPPORTED_IMG:
        raise ValueError(f"Format image non supporte: {Path(img360_path).suffix}")

    rapport = {
        "status": "RUNNING",
        "input_ply": ply_path,
        "input_img360": img360_path,
        "output_glb": output_path,
        "decimation_level": decim_level,
        "bake_resolution": bake_res,
    }

    try:
        # OP 1 — MESH
        obj = op_mesh_import(ply_path)
        rapport["faces_raw"] = len(obj.data.polygons)

        # OP 1b — DECIMATION
        op_decimate(obj, decim_level)
        rapport["faces_final"] = len(obj.data.polygons)
        rapport["decimation_applied"] = decim_level

        # OP 2 — BAKE
        op_bake_texture(obj, img360_path, bake_res)

        # OP 3 — SEAL
        size_mb = op_seal_export(obj, output_path)
        rapport["output_size_mb"] = round(size_mb, 2)
        rapport["status"] = "SUCCESS"

    except Exception as e:
        rapport["status"] = "ERROR"
        rapport["error"] = str(e)
        print(f"[LOCUS][ERROR] {e}")
        raise

    finally:
        write_rapport(output_path, rapport)

    print("[LOCUS] PIPELINE COMPLET. POUR L'EMPEROR.")

if __name__ == "__main__":
    main()
