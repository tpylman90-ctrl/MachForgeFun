# MachForgeFun

MachForge is a small browser-based STEM ballistics lab. Players reshape a projectile's side profile, choose material and dimensions, set launch conditions, and fire one simulated round down a sci-fi test corridor.

## Run

Open `index.html` in a modern browser. There are no package installs, services, or network assets.

## First playable loop

- Drag the cyan profile points to sculpt an organic projectile nose and body.
- Choose one of four starting silhouettes, then tune length, diameter, and core material.
- Set muzzle velocity, launch elevation, and crosswind.
- Fire and follow range, altitude, velocity, Mach number, and estimated aerodynamic drag.
- Compare the velocity and altitude traces, then alter one variable and fire again.

The model numerically integrates gravity and quadratic aerodynamic drag in standard sea-level air. It is an educational approximation, not a real-world firing tool. The current view is a lightweight procedural canvas scene so the prototype runs on desktop and mobile without a 3D engine.

## Blender source

`tools/blender/generate_range_scene.py` builds a reusable sci-fi launcher, lane hardware, and target gates in Blender, then exports a `.blend` and `.glb` into `artifacts/`. Run it from this repository with Blender installed:

```sh
blender -b --python tools/blender/generate_range_scene.py
```

The browser prototype does not import the GLB yet. Blender is not bundled in the current development environment, so the script is included as the next-step asset source and was not rendered or export-validated here.
