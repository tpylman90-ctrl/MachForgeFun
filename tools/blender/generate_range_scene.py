"""Generate MachForge's modular sci-fi range hardware in Blender.

Run: blender -b --python tools/blender/generate_range_scene.py
Writes: artifacts/machforge_range.blend and artifacts/machforge_range.glb
"""
import bpy
import math
import os
from mathutils import Vector


def material(name, color, metallic=0.0, roughness=0.4, emission=None):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1.0)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    if emission:
        bsdf.inputs["Emission Color"].default_value = (*emission, 1.0)
        bsdf.inputs["Emission Strength"].default_value = 2.0
    return mat


def cube(name, loc, scale, mat, bevel=0.04):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mat)
    if bevel:
        mod = obj.modifiers.new("Machined edge radii", "BEVEL")
        mod.width = bevel
        mod.segments = 3
        obj.modifiers.new("Weighted corner normals", "WEIGHTED_NORMAL")
    return obj


def cylinder(name, loc, radius, depth, mat, axis="Z", vertices=32):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=loc)
    obj = bpy.context.object
    obj.name = name
    if axis == "X":
        obj.rotation_euler[1] = math.pi / 2
    elif axis == "Y":
        obj.rotation_euler[0] = math.pi / 2
    obj.data.materials.append(mat)
    bevel = obj.modifiers.new("Edge glint", "BEVEL")
    bevel.width = min(radius * 0.14, 0.045)
    bevel.segments = 2
    obj.modifiers.new("Weighted normals", "WEIGHTED_NORMAL")
    return obj


def make_gate(x, mat, glow):
    # A square steel arch with an inset luminous target ring.
    cube("Target gate | left upright", (x, 0, 1.25), (0.16, 0.16, 2.5), mat, 0.035)
    cube("Target gate | right upright", (x, 3.0, 1.25), (0.16, 0.16, 2.5), mat, 0.035)
    cube("Target gate | crown", (x, 1.5, 2.5), (0.16, 3.15, 0.16), mat, 0.035)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.68, minor_radius=0.025, major_segments=48,
                                     minor_segments=8, location=(x - 0.1, 1.5, 1.22),
                                     rotation=(0, math.pi / 2, 0))
    ring = bpy.context.object
    ring.name = "Target gate | emissive ring"
    ring.data.materials.append(glow)


def build():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    steel = material("Graphite ceramic steel", (0.075, 0.12, 0.15), 0.78, 0.28)
    edge = material("Titanium edge trim", (0.34, 0.46, 0.50), 0.82, 0.24)
    deck = material("Range deck", (0.027, 0.046, 0.052), 0.32, 0.62)
    cyan = material("Cyan photonic markers", (0.05, 0.42, 0.52), 0.28, 0.25, (0.13, 0.75, 0.95))
    amber = material("Amber safety emitters", (0.62, 0.24, 0.06), 0.28, 0.3, (1.0, 0.24, 0.04))

    # Modular lane deck, low side curbs and recessed guide rails.
    cube("Lane foundation", (11, 1.5, -0.22), (24, 5.4, 0.44), deck, 0.12)
    for y in (-1.0, 4.0):
        cube("Lane curb", (11, y, 0.08), (23.5, 0.28, 0.42), steel, 0.06)
        for x in range(0, 23, 3):
            cube("Curb photonic marker", (x, y, 0.31), (0.52, 0.035, 0.025), cyan, 0.01)
    for y in (0.9, 2.1):
        cube("Launcher guide rail", (2.0, y, 0.17), (5.6, 0.12, 0.24), edge, 0.025)
        cube("Rail light channel", (2.0, y, 0.30), (5.3, 0.025, 0.018), cyan, 0.007)

    # Low profile launch cradle, barrel, clamp collars, recoil cylinder and actuator.
    cube("Launcher plinth", (2.0, 1.5, 0.48), (3.0, 2.1, 0.48), steel, 0.13)
    cube("Cradle upper carriage", (2.25, 1.5, 0.82), (2.3, 1.18, 0.28), edge, 0.08)
    cylinder("Electromagnetic launch barrel", (3.25, 1.5, 1.20), 0.24, 2.5, steel, "X", 48)
    cylinder("Muzzle ceramic shroud", (4.48, 1.5, 1.20), 0.275, 0.35, edge, "X", 48)
    cylinder("Muzzle aperture", (4.68, 1.5, 1.20), 0.195, 0.04, cyan, "X", 48)
    for x in (2.25, 3.0, 3.65):
        cylinder("Barrel induction collar", (x, 1.5, 1.20), 0.29, 0.09, edge, "X", 40)
        cylinder("Induction collar light", (x, 1.5, 1.20), 0.303, 0.022, cyan, "X", 40)
    cylinder("Recoil damper", (2.1, 2.18, 0.72), 0.09, 1.55, edge, "X", 24)
    for y in (0.74, 2.26):
        cube("Cradle fork", (1.85, y, 0.76), (1.35, 0.16, 0.52), steel, 0.05)
    cube("Control pedestal", (0.65, 2.9, 0.78), (0.52, 0.5, 1.4), steel, 0.09)
    cube("Control display", (0.93, 2.89, 1.12), (0.035, 0.34, 0.42), cyan, 0.015)
    for z in (0.63, 0.77, 0.91):
        cylinder("Safety status lamp", (0.93, 2.60, z), 0.035, 0.025, amber, "X", 16)

    for km, x in enumerate((7, 12, 17, 22), 1):
        make_gate(x, edge, cyan if km == 1 else amber)
        cube("Distance marker foot", (x, 1.5, 0.12), (0.5, 4.0, 0.22), steel, 0.05)

    # Repeated calibration pylons mark the corridor edges.
    for x in range(5, 24, 4):
        for y in (-0.7, 3.7):
            cylinder("Calibration pylon", (x, y, 0.62), 0.09, 1.12, steel, vertices=16)
            cylinder("Pylon beacon", (x, y, 1.22), 0.105, 0.09, amber, vertices=20)

    # A simple studio camera/light setup for asset review in Blender.
    bpy.ops.object.camera_add(location=(8, -12, 8))
    cam = bpy.context.object
    cam.name = "MachForge range preview camera"
    target = Vector((11, 1.5, 0.7))
    cam.rotation_euler = (target - cam.location).to_track_quat("-Z", "Y").to_euler()
    cam.data.lens = 42
    bpy.context.scene.camera = cam
    bpy.ops.object.light_add(type="AREA", location=(4, -3, 10))
    key = bpy.context.object
    key.name = "Cool softbox"
    key.data.energy = 1800
    key.data.shape = "DISK"
    key.data.size = 9
    bpy.ops.object.light_add(type="AREA", location=(17, 5, 7))
    rim = bpy.context.object
    rim.name = "Warm rim light"
    rim.data.energy = 1100
    rim.data.color = (0.35, 0.72, 1.0)
    rim.data.size = 7

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE_NEXT"
    scene.render.resolution_x = 1440
    scene.render.resolution_y = 900
    scene.render.resolution_percentage = 100
    scene.world.color = (0.015, 0.026, 0.04)
    scene.render.image_settings.file_format = "PNG"

    # Keep the project organized in named collections for later level assembly.
    for coll_name in ("01 · Lane", "02 · Launcher", "03 · Targets", "04 · Preview rig"):
        if coll_name not in bpy.data.collections:
            coll = bpy.data.collections.new(coll_name)
            scene.collection.children.link(coll)
    for obj in list(scene.objects):
        if "Target gate" in obj.name or "Distance marker" in obj.name:
            target_coll = bpy.data.collections["03 · Targets"]
        elif "Launcher" in obj.name or "barrel" in obj.name.lower() or "cradle" in obj.name.lower() or "muzzle" in obj.name.lower() or "induction" in obj.name.lower() or "recoil" in obj.name.lower() or "Control" in obj.name:
            target_coll = bpy.data.collections["02 · Launcher"]
        elif obj.type in {"CAMERA", "LIGHT"}:
            target_coll = bpy.data.collections["04 · Preview rig"]
        else:
            target_coll = bpy.data.collections["01 · Lane"]
        for coll in list(obj.users_collection):
            coll.objects.unlink(obj)
        target_coll.objects.link(obj)

    bpy.ops.object.select_all(action="DESELECT")


if __name__ == "__main__":
    build()
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    out = os.path.join(root, "artifacts")
    os.makedirs(out, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out, "machforge_range.blend"))
    bpy.ops.export_scene.gltf(filepath=os.path.join(out, "machforge_range.glb"), export_format="GLB", export_apply=True)
    print("MachForge range written to", out)
