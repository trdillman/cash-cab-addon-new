"""
Headless Route Import + Car/Sign Diagnostics

Runs the current CashCab addon end-to-end:
- Enables the addon if needed.
- Configures a short test route.
- Calls bpy.ops.blosm.fetch_route_map in EXEC_DEFAULT mode.
- Runs car/sign diagnostics:
  - pipeline_taxi_sign_diagnostics.inspect_pipeline_state()
  - animation_follow_diagnostics.analyze_follow_behavior()

This script is intended to be run with:
  blender --background --python asset-car-fix/test_scripts/headless_route_import_and_diagnostics.py
"""

import bpy
import sys
import time
import traceback
from pathlib import Path

ADDON_MODULE = "cash-cab-addon"


def ensure_addon_enabled():
    prefs = bpy.context.preferences
    if ADDON_MODULE not in prefs.addons:
        try:
            bpy.ops.preferences.addon_enable(module=ADDON_MODULE)
            print(f"[HEADLESS] Enabled addon {ADDON_MODULE}")
        except Exception as exc:
            print(f"[HEADLESS] ERROR enabling addon {ADDON_MODULE}: {exc}")
    else:
        print(f"[HEADLESS] Addon {ADDON_MODULE} already enabled")


def configure_route_props():
    scene = bpy.context.scene
    addon = getattr(scene, "blosm", None)
    if addon is None:
        print("[HEADLESS] ERROR: scene.blosm properties not found; GUI registration may have failed.")
        return

    # Use a short downtown Toronto route (similar to legacy tests)
    addon.route_start_address = "1 Dundas St W, Toronto"
    addon.route_end_address = "10 Dundas St W, Toronto"
    addon.route_padding_m = 50.0
    addon.route_import_roads = True
    addon.route_import_buildings = True
    addon.route_import_water = False
    addon.route_import_separate_tiles = False

    print("[HEADLESS] Configured route properties for short downtown route")


def run_fetch_route_and_map():
    print("[HEADLESS] Starting Fetch Route & Map")
    start = time.perf_counter()
    result = bpy.ops.blosm.fetch_route_map("EXEC_DEFAULT")
    duration = time.perf_counter() - start
    print("[HEADLESS] Fetch result:", result)
    print(f"[HEADLESS] Fetch duration: {duration:.1f}s")
    if "FINISHED" not in result:
        raise RuntimeError("Fetch Route & Map did not finish successfully")


def run_diagnostics():
    """
    Run pipeline and animation diagnostics on the current scene.
    """
    base_dir = Path(__file__).parent
    sys.path.insert(0, str(base_dir))

    try:
        import pipeline_taxi_sign_diagnostics as pipeline_diag
    except Exception as exc:
        print(f"[HEADLESS] ERROR importing pipeline_taxi_sign_diagnostics: {exc}")
        pipeline_diag = None

    try:
        import animation_follow_diagnostics as anim_diag
    except Exception as exc:
        print(f"[HEADLESS] ERROR importing animation_follow_diagnostics: {exc}")
        anim_diag = None

    if pipeline_diag:
        try:
            pipeline_diag.inspect_pipeline_state()
        except Exception as exc:
            print(f"[HEADLESS] ERROR running pipeline diagnostics: {exc}")
            traceback.print_exc()

    if anim_diag:
        try:
            anim_diag.analyze_follow_behavior()
        except Exception as exc:
            print(f"[HEADLESS] ERROR running animation diagnostics: {exc}")
            traceback.print_exc()


def save_scene_snapshot():
    """
    Save a lightweight snapshot of the current scene for offline inspection.
    """
    try:
        out_dir = (
            Path(__file__).parent.parent
            / "test_results"
            / "test_scenes"
            / "blender_test_results"
        )
        out_dir.mkdir(parents=True, exist_ok=True)
        filepath = out_dir / "headless_route_import_diagnostics.blend"
        bpy.ops.wm.save_mainfile(filepath=str(filepath))
        print(f"[HEADLESS] Saved scene snapshot to {filepath}")
    except Exception as exc:
        print(f"[HEADLESS] WARN: Failed to save scene snapshot: {exc}")


def main():
    try:
        ensure_addon_enabled()
        configure_route_props()
        run_fetch_route_and_map()
        run_diagnostics()
        save_scene_snapshot()
    except Exception:
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

