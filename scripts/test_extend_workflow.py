import bpy
import sys
import time
import traceback

ADDON_MODULE = "blosm_clean"
OUTPUT_BLEND = bpy.path.abspath("//extend_test.blend")


def ensure_addon_enabled():
    prefs = bpy.context.preferences
    if ADDON_MODULE not in prefs.addons:
        bpy.ops.preferences.addon_enable(module=ADDON_MODULE)
        print(f"Enabled addon {ADDON_MODULE}")
    else:
        print(f"Addon {ADDON_MODULE} already enabled")


def configure_route_props():
    scene = bpy.context.scene
    addon = scene.blosm
    addon.route_start_address = "1 Dundas St W, Toronto"
    addon.route_end_address = "10 Dundas St W, Toronto"
    addon.route_padding_m = 50.0
    addon.route_import_roads = True
    addon.route_import_buildings = True
    addon.route_import_water = True
    addon.route_import_separate_tiles = False
    addon.route_extend_m = 1200.0
    print("Configured route properties (short route, small padding)")


def run_fetch_route_and_map():
    print("Starting fetch route & map")
    start = time.perf_counter()
    result = bpy.ops.blosm.fetch_route_map('EXEC_DEFAULT')
    duration = time.perf_counter() - start
    print("Fetch result:", result)
    print(f"Fetch duration: {duration:.1f}s")
    if 'FINISHED' not in result:
        raise RuntimeError("Fetch route map operator did not finish")


def run_extend():
    print("Starting extend city area")
    start = time.perf_counter()
    result = bpy.ops.blosm.extend_city_area('EXEC_DEFAULT')
    duration = time.perf_counter() - start
    print("Extend result:", result)
    print(f"Extend duration: {duration:.1f}s")
    if 'FINISHED' not in result:
        raise RuntimeError("Extend city operator did not finish")


def log_state():
    scene = bpy.context.scene
    tiles = scene.get('blosm_import_tiles', [])
    bbox = scene.get('blosm_import_bbox')
    print(f"Stored bbox after extend: {bbox}")
    print(f"Stored tile count: {len(tiles)}")


def save_scene():
    try:
        bpy.ops.wm.save_mainfile(filepath=OUTPUT_BLEND)
        print(f"Saved Blender scene to {OUTPUT_BLEND}")
    except Exception as exc:
        print(f"Failed to save Blender scene: {exc}")


def main():
    try:
        ensure_addon_enabled()
        configure_route_props()
        run_fetch_route_and_map()
        run_extend()
        log_state()
        save_scene()
    except Exception:
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
