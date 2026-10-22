# MachForgeFun

MachForgeFun is a Godot 4 3D physics range for learning projectile motion by changing launch conditions and shaping the projectile. The current build puts the Blender-made sci-fi cannon, lane, and target gates into a real-time Godot scene, then lets you fire one simulated round and inspect its flight telemetry.

## Download the Android APK

The latest successful build is published here:

**[Download the latest MachForgeFun APK](https://github.com/tpylman90-ctrl/MachForgeFun/releases/download/android-latest/MachForgeFun.apk)**

The Android workflow exports and verifies an arm64 debug APK on every main-branch build. Pull requests also build an APK artifact for review. This is an early development build signed with a temporary debug key.

## Playable range

- Adjust muzzle velocity, elevation, crosswind, and projectile nose roundness.
- Fire a single projectile and follow its glowing flight trace.
- Read range, altitude, time of flight, peak altitude, and Mach number.
- Run the Godot project on desktop or export the landscape Android app.

The trajectory uses a numerical integration of gravity and quadratic aerodynamic drag in standard sea-level air. It is an educational approximation.

## Run with Godot

Open the repository root in Godot 4.7.2 and run `scenes/range.tscn`. The project uses the mobile-friendly Compatibility renderer.

## Blender source

`tools/blender/generate_range_scene.py` builds the launcher and test range and exports the editable `.blend`, the `.glb` imported by Godot, and a review render into `artifacts/`. The Blender workflow verifies the official Blender 4.5.14 archive checksum and stores generated assets as an Actions artifact. When generated assets change, it dispatches a fresh Android build so the public APK contains the current GLB. The Godot scene loads `assets/machforge_range.glb` directly. The editable Blender source is kept in `assets/blender_source/`, which Godot skips during runtime import.

Run the generator locally with Blender 4.5.14:

```sh
blender --background --python tools/blender/generate_range_scene.py
python3 tools/blender/validate_glb.py artifacts/machforge_range.glb
```

## Build an APK locally

Install Godot 4.7.2 with Android export templates, Java 17, and the Android SDK packages in `.github/workflows/android-apk.yml`. Then import the project and export the `Android` preset to `build/MachForgeFun.apk`.

GitHub Actions runs the same Godot import and scene smoke test on changes, checks the Blender GLB, exports and verifies the APK, and publishes each successful main build to the download link above.
