"""
pre_parse_fbx.py — FERRUS ANIMUS / Compartiment INTEL
Charge un fichier FBX DeepMotion via bpy et retourne un bloc XML
de metadonnees structurees pour analyse par Claude (INTEL-SKELETON).

Usage (bpy headless) :
    Appele depuis intel_skeleton.py via extract_fbx_metadata(fbx_path)

Contrat de sortie : XML string conforme au schema attendu par le prompt Claude.
Voir : FERRUS_INTEL_SKELETON_CLAUDE_METAPROMPT.md
"""

import bpy
import os
import math


def extract_fbx_metadata(fbx_path: str) -> str:
    """
    Charge le FBX via bpy et retourne un bloc XML de metadonnees.

    Args:
        fbx_path: chemin absolu vers le fichier FBX DeepMotion

    Returns:
        XML string conforme au contrat INTEL-SKELETON
        ou "<error>...</error>" en cas d'echec
    """

    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=fbx_path)

    scene = bpy.context.scene
    armature = next((o for o in scene.objects if o.type == "ARMATURE"), None)

    if not armature:
        return "<error>Aucune armature trouvee dans le fichier FBX</error>"

    # --- Squelette ---
    bones = list(armature.data.bones)
    bone_lines = []
    for bone in bones:
        parent_name = bone.parent.name if bone.parent else "ROOT"
        bone_lines.append(
            f'    <bone name="{bone.name}" parent="{parent_name}"/>'
        )

    # --- Animations ---
    action = armature.animation_data.action if armature.animation_data else None
    anim_info = ""

    if action:
        frame_start = int(action.frame_range[0])
        frame_end = int(action.frame_range[1])
        fps = scene.render.fps
        duration_sec = round((frame_end - frame_start) / fps, 2)
        total_keyframes = sum(len(fc.keyframe_points) for fc in action.fcurves)

        # Detection de la convention de rotation
        rot_modes = set()
        for fc in action.fcurves:
            if "rotation_euler" in fc.data_path:
                rot_modes.add("euler")
            elif "rotation_quaternion" in fc.data_path:
                rot_modes.add("quaternion")

        # --- Detection jitter (variance des FCurves mains et tete) ---
        jitter_bones = []
        jitter_scores = {}
        JITTER_BONES_CIBLES = [
            "l_hand_JNT", "r_hand_JNT", "head_JNT",
            "l_forearm_JNT", "r_forearm_JNT"
        ]

        for bone_name in JITTER_BONES_CIBLES:
            bone_fcurves = [
                fc for fc in action.fcurves if bone_name in fc.data_path
            ]
            if not bone_fcurves:
                continue
            for fc in bone_fcurves:
                values = [kp.co[1] for kp in fc.keyframe_points]
                if len(values) < 3:
                    continue
                diffs = [abs(values[i + 1] - values[i]) for i in range(len(values) - 1)]
                variance = sum(d ** 2 for d in diffs) / len(diffs)
                if variance > 0.001:  # Seuil empirique
                    if bone_name not in jitter_bones:
                        jitter_bones.append(bone_name)
                    jitter_scores[bone_name] = round(min(variance * 100, 1.0), 3)

        global_jitter_score = (
            round(sum(jitter_scores.values()) / max(len(jitter_scores), 1), 3)
            if jitter_scores
            else 0.0
        )

        # --- Detection foot slide ---
        foot_bones = {"l_foot_JNT": "pied_gauche", "r_foot_JNT": "pied_droit"}
        foot_slide_data = {}
        for bone_name, label in foot_bones.items():
            bone_loc = [
                fc for fc in action.fcurves
                if bone_name in fc.data_path and "location" in fc.data_path
            ]
            if bone_loc:
                all_values = []
                for fc in bone_loc:
                    all_values.extend([kp.co[1] for kp in fc.keyframe_points])
                if all_values:
                    delta = round((max(all_values) - min(all_values)) * 100, 2)
                    if delta > 0.5:
                        foot_slide_data[bone_name] = delta

        # --- Detection derive hanches ---
        hip_fc = [
            fc for fc in action.fcurves
            if "hips_JNT" in fc.data_path
            and "location" in fc.data_path
            and fc.array_index == 1
        ]
        hip_derive = 0.0
        hip_direction = "stable"
        if hip_fc:
            vals = [kp.co[1] for kp in hip_fc[0].keyframe_points]
            if len(vals) >= 2:
                hip_derive = round(abs(vals[-1] - vals[0]) * 100, 2)
                hip_direction = (
                    "descente_progressive" if vals[-1] < vals[0]
                    else "montee_progressive"
                )

        # --- Assemblage XML jitter ---
        if jitter_bones:
            jitter_bones_xml = "\n".join(
                f'      <bone name="{b}" score="{jitter_scores.get(b, 0.0)}"/>'
                for b in jitter_bones
            )
            jitter_xml = (
                f"\n    <jitter_detecte>true</jitter_detecte>"
                f"\n    <jitter_global_score>{global_jitter_score}</jitter_global_score>"
                f"\n    <jitter_bones>\n{jitter_bones_xml}\n    </jitter_bones>"
            )
        else:
            jitter_xml = "\n    <jitter_detecte>false</jitter_detecte>"

        # --- Assemblage XML foot slide ---
        if foot_slide_data:
            fs_parts = "\n".join(
                f'      <foot bone="{k}" delta_cm="{v}"/>'
                for k, v in foot_slide_data.items()
            )
            foot_slide_xml = (
                f"\n    <foot_slide_detecte>true</foot_slide_detecte>"
                f"\n    <foot_slide>\n{fs_parts}\n    </foot_slide>"
            )
        else:
            foot_slide_xml = "\n    <foot_slide_detecte>false</foot_slide_detecte>"

        # --- Assemblage XML derive hanches ---
        derive_xml = (
            f'\n    <derive_hanches_detectee>{"true" if hip_derive > 2.0 else "false"}</derive_hanches_detectee>'
            f'\n    <derive_hanches delta_vertical_cm="{hip_derive}" direction="{hip_direction}"/>'
        )

        anim_info = f"""
  <animation>
    <take_name>{action.name}</take_name>
    <frame_start>{frame_start}</frame_start>
    <frame_end>{frame_end}</frame_end>
    <fps>{fps}</fps>
    <duree_sec>{duration_sec}</duree_sec>
    <total_keyframes>{total_keyframes}</total_keyframes>
    <rotation_modes>{", ".join(rot_modes) if rot_modes else "inconnu"}</rotation_modes>
    <quaternion_disponible>{"true" if "quaternion" in rot_modes else "false"}</quaternion_disponible>
  </animation>
  <qualite_fcurves>{jitter_xml}{foot_slide_xml}{derive_xml}
  </qualite_fcurves>"""

    # --- Assemblage XML final ---
    file_size_kb = round(os.path.getsize(fbx_path) / 1024, 0)

    xml = f"""<fbx_asset>
  <source>{os.path.basename(fbx_path)}</source>
  <fbx_version>7.7</fbx_version>
  <taille_kb>{file_size_kb}</taille_kb>
  <convention_naming>deepmotion_jnt</convention_naming>
  <squelette>
    <root_bone>hips_JNT</root_bone>
    <total_bones>{len(bones)}</total_bones>
    <bones>
{chr(10).join(bone_lines)}
    </bones>
  </squelette>{anim_info}
</fbx_asset>"""

    return xml
