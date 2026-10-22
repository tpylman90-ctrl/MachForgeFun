"""Build MachForge's stylized hard-surface rail cannon and test range."""
import bpy
import math
import os
from mathutils import Vector


OUT = os.path.abspath("artifacts")
os.makedirs(OUT, exist_ok=True)


def mat(name, color, metallic=0.0, roughness=0.35, emission=None, strength=0.0):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1)
    m.use_nodes = True
    p = m.node_tree.nodes.get("Principled BSDF")
    p.inputs["Base Color"].default_value = (*color, 1)
    p.inputs["Metallic"].default_value = metallic
    p.inputs["Roughness"].default_value = roughness
    if emission:
        key = "Emission Color" if "Emission Color" in p.inputs else "Emission"
        p.inputs[key].default_value = (*emission, 1)
        p.inputs["Emission Strength"].default_value = strength
    return m


blue = mat("Armor | cobalt ceramic", (.035, .19, .39), .62, .27)
blue_hi = mat("Armor | edge panels", (.08, .34, .62), .48, .25)
dark = mat("Graphite | structural steel", (.025, .045, .065), .78, .3)
steel = mat("Titanium | machined", (.38, .49, .53), .84, .22)
copper = mat("Copper | induction coils", (.72, .23, .085), .78, .24)
ceramic = mat("Barrel | ceramic composite", (.34, .43, .49), .48, .25)
cyan = mat("Cyan | energized", (.035, .62, .82), .35, .2, (.02, .7, 1), 3.0)
amber = mat("Amber | warning lights", (1, .34, .055), .25, .23, (1, .13, .015), 1.8)
glass = mat("Display | dark glass", (.008, .045, .065), .25, .12, (.01, .12, .18), .45)
ground = mat("Range deck | basalt", (.055, .075, .09), .32, .48)
paint = mat("Range markings", (.42, .68, .65), .15, .43, (.1, .35, .3), .3)


def finish(obj, material, bevel=0):
    if material:
        obj.data.materials.append(material)
    if bevel:
        mod = obj.modifiers.new("Machined radii", "BEVEL")
        mod.width, mod.segments = bevel, 3
        obj.modifiers.new("Corner normals", "WEIGHTED_NORMAL")
    return obj


def cube(name, loc, scale, material, bevel=.05):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.object
    o.name = name
    o.dimensions = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return finish(o, material, bevel)


def cyl(name, loc, radius, depth, material, axis="X", vertices=48, bevel=.015):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=loc)
    o = bpy.context.object
    o.name = name
    if axis == "X": o.rotation_euler[1] = math.pi / 2
    elif axis == "Y": o.rotation_euler[0] = math.pi / 2
    return finish(o, material, bevel)


def torus(name, loc, major, minor, material, axis="X"):
    bpy.ops.mesh.primitive_torus_add(major_radius=major, minor_radius=minor, major_segments=64, minor_segments=12, location=loc)
    o = bpy.context.object
    o.name = name
    if axis == "X": o.rotation_euler[1] = math.pi / 2
    elif axis == "Y": o.rotation_euler[0] = math.pi / 2
    return finish(o, material)


def hose(name, points, material, radius=.045):
    curve = bpy.data.curves.new(name, "CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = 16
    curve.bevel_depth = radius
    curve.bevel_resolution = 4
    spline = curve.splines.new("BEZIER")
    spline.bezier_points.add(len(points)-1)
    for p, co in zip(spline.bezier_points, points):
        p.co = co
        p.handle_left_type = p.handle_right_type = "AUTO"
    obj = bpy.data.objects.new(name, curve)
    bpy.context.collection.objects.link(obj)
    curve.materials.append(material)
    return obj


def text(name, body, loc, size, material, rotation=(0, 0, 0)):
    bpy.ops.object.text_add(location=loc, rotation=rotation)
    o = bpy.context.object
    o.name = name
    o.data.body = body
    o.data.size = size
    o.data.extrude = .001
    o.data.align_x = "CENTER"
    o.data.align_y = "CENTER"
    o.data.materials.append(material)
    bpy.ops.object.convert(target="MESH")
    return o


def build():
    # Deck and long, instrumented range lane (X is downrange).
    cube("Range foundation", (11, 0, -.42), (38, 12, .8), ground, .22)
    cube("Launch plinth", (0, 0, .12), (8.2, 4.3, .55), dark, .18)
    for y in (-4.8, 4.8):
        cube("Lane edge light channel", (11, y, .02), (37, .12, .09), cyan, .035)
    for x in range(2, 31, 2):
        cube("Range distance stripe", (x, 0, .015), (.035, 7.5, .025), paint, .005)
    for x in range(3, 34, 3):
        cube("Lane center dash", (x, 0, .035), (.72, .075, .025), amber if x == 3 else paint, .01)

    # Rear chassis, recoil frame, and visible track bed.
    cube("Twin recoil rails", (1.1, 0, .8), (8.8, 2.25, .28), steel, .09)
    for y in (-.78, .78):
        cube("Linear accelerator rail", (2.1, y, 1.06), (7.4, .16, .28), blue_hi, .045)
        cube("Rail cyan inlay", (2.1, y, 1.21), (7.0, .045, .025), cyan, .01)
    for x in (-2, 1, 4, 6):
        for y in (-.9, .9):
            cube("Recoil frame foot", (x, y, .52), (.36, .34, .7), dark, .07)
            cube("Recoil frame brace", (x+.38, y, .55), (.9, .12, .12), blue, .035).rotation_euler[1] = -.28

    # Main armored breech block and articulated armor plates.
    cube("Breech armor core", (-.55, 0, 1.62), (3.25, 2.65, 2.05), blue, .24)
    cube("Top service deck", (-.62, 0, 2.7), (2.55, 2.25, .18), blue_hi, .09)
    for y in (-.82, .82):
        side = cube("Angled side armor", (-.65, y, 1.62), (2.75, .14, 1.42), blue_hi, .10)
        side.rotation_euler[1] = -.13
        for x in (-1.65, -1.15, -.65, -.15, .35):
            cyl("Armor fastener", (x, y*1.095, 1.2), .065, .06, steel, "Y", 16, .008)
    cube("Front armor brow", (-2.03, 0, 2.35), (.24, 2.35, .36), dark, .08)
    for y in (-.8, -.4, 0, .4, .8):
        cube("Breech vent", (-2.17, y, 2.37), (.035, .18, .15), steel, .018)

    # Copper induction stack with insulating rings and cable feeds.
    for i, x in enumerate((-2.35, -1.95, -1.55, -1.15, -.75)):
        torus("Copper induction coil", (x, 0, 1.57), .79, .12, copper)
        torus("Coil ceramic separator", (x+.17, 0, 1.57), .80, .035, steel)
    cyl("Induction core", (-1.55, 0, 1.57), .48, 2.15, dark)
    for y in (-.7, .7):
        hose("Cyan bus conduit", [(-2.4,y,1.28),(-2.1,y*1.15,2.08),(-1.65,y*1.2,2.3),(-1.2,y,2.12),(-.8,y,1.75)], cyan, .065)
        hose("Copper power lead", [(-2.3,y,1.05),(-1.9,y*1.25,.87),(-1.35,y*1.3,.9),(-.9,y,1.18)], copper, .045)

    # Long ceramic barrel, collars, muzzle brake and energized bore.
    cyl("Barrel root collar", (1.28, 0, 1.9), .72, .48, steel)
    torus("Breech locking ring", (1.03, 0, 1.9), .69, .085, dark)
    cyl("Main ceramic barrel", (7.15, 0, 2.08), .34, 11.5, ceramic)
    for x, r in ((2.1,.48),(2.35,.42),(5.3,.38),(5.48,.4),(11.9,.43),(12.16,.48),(12.42,.53)):
        cyl("Barrel reinforcement collar", (x,0,2.08), r, .18, blue if x < 5 else steel)
    cyl("Muzzle crown", (12.65,0,2.08), .61, .34, dark)
    torus("Muzzle cyan emitter", (12.84,0,2.08), .47, .075, cyan)
    cyl("Bore opening", (12.855,0,2.08), .36, .025, glass)
    for y in (-.29, .29):
        cube("Barrel heat fin", (8.4,y,2.42), (4.7,.055,.13), steel, .025)
    # Muzzle halo rings on a plane facing the camera.
    for rad, material in ((.78,cyan),(.94,blue_hi),(1.1,amber)):
        torus("Muzzle field halo", (12.92,0,2.08), rad, .027, material)

    # Hydraulic reservoirs, pressure hardware, pipes, and gauge pods.
    for y in (-.92, .92):
        cyl("Recoil hydraulic ram", (-.25,y,.76), .17, 2.45, steel)
        cyl("Ram piston", (.35,y,.76), .085, 1.2, blue_hi)
        cyl("Capacitor pressure vessel", (-.45,y*1.38,.75), .32, 1.85, blue, "Y")
        torus("Pressure vessel end cap", (-.45,y*1.38-.95,.75), .29,.035, steel, "Y")
    for x, y, z, radius in ((-2.1,-1.32,1.08,.24),(-1.25,-1.35,.77,.19),(.35,-1.34,1.1,.25)):
        cyl("Analog pressure gauge bezel", (x,y,z), radius, .12, steel, "Y")
        cyl("Gauge black dial", (x,y-.07,z), radius*.78, .025, glass, "Y")
        cyl("Gauge center pin", (x,y-.09,z), .035, .025, amber, "Y", 20)
        # face index marks
        for a in range(7):
            angle = math.radians(-65+a*22)
            bx=x+math.sin(angle)*radius*.57; bz=z+math.cos(angle)*radius*.57
            cube("Gauge tick", (bx,y-.105,bz), (.018,.012,.07), steel, .004).rotation_euler[1] = -angle
    hose("Coolant loop A", [(-2.35,-1.1,1.35),(-2.0,-1.48,1.8),(-1.25,-1.52,1.82),(-.72,-1.15,1.25)], cyan, .06)
    hose("Coolant loop B", [(-2.25,-1.05,1.12),(-1.9,-1.55,.98),(-1.15,-1.5,1.16),(-.55,-1.2,1.55)], steel, .045)
    hose("Hydraulic return line", [(-.75,-1.3,.75),(-.25,-1.58,.52),(.55,-1.55,.58),(1.1,-1.16,.92)], copper, .05)

    # Hatch windows, status lamps, serial plate, and legible instrument panel.
    cube("Top inspection glass", (-.85,-.36,2.81), (1.04,.62,.035), dark, .06)
    cube("Top inspection window", (-.85,-.36,2.835), (.76,.39,.025), glass, .025)
    for x in (-1.6, -.1):
        cube("Top latch", (x,.55,2.83), (.48,.16,.11), steel, .045)
    cube("Side status screen", (-.38,-1.405,1.9), (1.05,.035,.55), dark, .05)
    cube("Side display glass", (-.38,-1.43,1.9), (.91,.025,.39), glass, .03)
    text("Launcher insignia", "MACHFORGE", (-.38,-1.453,2.02), .115, cyan, (math.pi/2,0,0))
    text("Serial identifier", "MF-07 / RANGE SYSTEM", (-.38,-1.454,1.83), .07, steel, (math.pi/2,0,0))
    for x in (-1.75,-1.45,-1.15):
        cyl("Status indicator", (x,-1.42,2.55), .055,.045, cyan if x != -1.45 else amber,"Y",24,.006)
    for y in (-.92, .92):
        for x in (-1.85,-1.25,-.65,-.05,.45):
            cyl("Armor bolt", (x,y*1.09,2.32), .045,.045, steel,"Y",16,.004)

    # Range targets: ring gates at 5, 10 and 15 km calibration stations.
    for i, x in enumerate((17, 24, 31)):
        z=2.4
        cyl("Target gate left upright", (x,-1.9,z/2), .11, z, dark, "Z")
        cyl("Target gate right upright", (x,1.9,z/2), .11, z, dark, "Z")
        # Arch using segmented ring, opening toward launcher.
        for a in range(13):
            angle=math.pi*a/12
            y=1.9*math.cos(angle); zz=z+1.9*math.sin(angle)
            cyl("Range gate luminous segment", (x,y,zz), .055,.32, cyan if a%3 else amber, "X", 16,.005)
        cube("Target gate base", (x,0,.12), (.7,4.4,.22), blue, .06)
        text("Distance marker", f"{(i+1)*5} KM", (x,-2.03,2.95), .25, cyan, (math.pi/2,0,0))
        for side in (-1,1):
            cube("Range sensor mast", (x+.55,side*2.3,.75), (.18,.18,1.5), steel,.04)
            cyl("Range sensor beacon", (x+.55,side*2.3,1.55), .16,.12, amber,"Z",24)

    # Soft atmospheric background cyclorama.
    cube("Horizon backdrop", (16, 0, 5), (48, 30, .2), dark, .05)


def aim(obj, point):
    obj.rotation_euler = (Vector(point)-obj.location).to_track_quat("-Z", "Y").to_euler()


def main():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    build()
    world=bpy.context.scene.world
    world.color=(.12,.15,.19)
    world.use_nodes=True
    world.node_tree.nodes["Background"].inputs["Color"].default_value=(.18,.21,.26,1)
    world.node_tree.nodes["Background"].inputs["Strength"].default_value=.42
    bpy.ops.object.light_add(type="AREA", location=(1,-9,15))
    key=bpy.context.object; key.name="Large softbox"; key.data.energy=2600; key.data.shape="DISK"; key.data.size=10; aim(key,(5,0,1))
    bpy.ops.object.light_add(type="AREA", location=(14,5,9))
    rim=bpy.context.object; rim.name="Cyan rim softbox"; rim.data.energy=1800; rim.data.color=(.24,.63,1); rim.data.size=8; aim(rim,(4,0,1.6))
    bpy.ops.object.light_add(type="AREA", location=(-5,3,6))
    fill=bpy.context.object; fill.name="Warm coil fill"; fill.data.energy=1000; fill.data.color=(1,.42,.2); fill.data.size=5; aim(fill,(-1,0,1.5))
    bpy.ops.object.camera_add(location=(-8,-13,7.2))
    camera=bpy.context.object; camera.name="Range hero camera"; camera.data.lens=48; aim(camera,(9,0,1.6))
    scene=bpy.context.scene; scene.camera=camera
    scene.render.engine="CYCLES"
    scene.cycles.samples=16
    scene.cycles.use_denoising=True
    scene.render.resolution_x=1440; scene.render.resolution_y=900; scene.render.resolution_percentage=100
    scene.view_settings.view_transform="AgX"
    scene.render.image_settings.file_format="PNG"
    scene.render.filepath=os.path.join(OUT,"machforge_range_preview.png")
    scene.world.color=(.18,.21,.26)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,"machforge_range.blend"))
    bpy.ops.render.render(write_still=True)
    bpy.ops.export_scene.gltf(filepath=os.path.join(OUT,"machforge_range.glb"),export_format="GLB",export_apply=True)


if __name__ == "__main__":
    main()
