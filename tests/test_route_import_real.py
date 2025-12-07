import bpy
import sys
import importlib.util
from pathlib import Path

print("[REALTEST] Starting real route import test")

# Load addon package from this folder as 'cash_cab_addon'
addon_dir = Path(r"C:\Users\Tyler\AppData\Roaming\Blender Foundation\Blender\4.5\scripts\addons\cash-cab-addon")
init_path = addon_dir / "__init__.py"

spec = importlib.util.spec_from_file_location("cash_cab_addon", init_path)
if spec is None or spec.loader is None:
    print("[REALTEST] ERROR: could not create spec for addon")
    sys.exit(1)

module = importlib.util.module_from_spec(spec)
sys.modules["cash_cab_addon"] = module
spec.loader.exec_module(module)

print("[REALTEST] Addon module loaded as cash_cab_addon")

# Register addon (sets up operators, scene props, GUI, etc.)
try:
    module.register()
    print("[REALTEST] Addon registered")
except Exception as exc:
    print("[REALTEST] ERROR registering addon:", exc)

from cash_cab_addon.route import anim as route_anim
from cash_cab_addon.route import pipeline_finalizer as route_pipeline_finalizer

scene = bpy.context.scene
print("[REALTEST] Using scene:", scene.name)

addon = getattr(scene, "blosm", None)
if addon is None:
    print("[REALTEST] ERROR: scene.blosm not found; cannot configure route")
    sys.exit(1)

# Configure a real route in Toronto
if not getattr(addon, "route_start_address", ""):
    addon.route_start_address = "CN Tower, Toronto, Canada"
if not getattr(addon, "route_end_address", ""):
    addon.route_end_address = "Rogers Centre, Toronto, Canada"

# Ensure layers and animation are enabled
addon.route_import_roads = True
addon.route_import_buildings = True
addon.route_create_preview_animation = True

# Animation GUI values
try:
    scene.blosm_anim_start = 15
    scene.blosm_anim_end = 150
    scene.blosm_lead_frames = 1
    print("[REALTEST] Scene animation props:", scene.blosm_anim_start, scene.blosm_anim_end, scene.blosm_lead_frames)
except Exception as exc:
    print("[REALTEST] WARN setting scene animation props:", exc)

# Run the real Fetch Route & Map operator
print("[REALTEST] Invoking BLOSM_OT_FetchRouteMap (EXEC_DEFAULT)")
try:
    res = bpy.ops.blosm.fetch_route_map("EXEC_DEFAULT")
    print("[REALTEST] bpy.ops.blosm.fetch_route_map result:", res)
except Exception as exc:
    print("[REALTEST] ERROR running fetch_route_map:", exc)
    sys.exit(1)

# After real import, run the pipeline finalizer explicitly once more to be sure
try:
    pf_result = route_pipeline_finalizer.run(scene)
    print("[REALTEST] pipeline_finalizer.run result keys:", sorted(pf_result.keys()))
except Exception as exc:
    print("[REALTEST] ERROR running pipeline_finalizer.run:", exc)

# Force keyframes using the shared helper so GUI values drive car & lead
try:
    route_anim.force_follow_keyframes(scene)
    print("[REALTEST] Forced follow keyframes after real import")
except Exception as exc:
    print("[REALTEST] ERROR forcing follow keyframes:", exc)

# Print keyframes for car and lead
try:
    route_anim.debug_print_follow_offset_keyframes(scene)
except Exception as exc:
    print("[REALTEST] ERROR in debug_print_follow_offset_keyframes:", exc)

# Save and reopen the file, then re-print to ensure persistence
output_path = addon_dir / "test_route_import_real.blend"
try:
    bpy.ops.wm.save_mainfile(filepath=str(output_path))
    print(f"[REALTEST] Saved test file to {output_path}")
except Exception as exc:
    print("[REALTEST] ERROR saving blend file:", exc)

try:
    bpy.ops.wm.open_mainfile(filepath=str(output_path))
    scene2 = bpy.context.scene
    print("[REALTEST] Reopened saved blend file; scene:", scene2.name)
    from cash_cab_addon.route import anim as route_anim2
    route_anim2.debug_print_follow_offset_keyframes(scene2)
except Exception as exc:
    print("[REALTEST] ERROR reopening or re-debugging blend file:", exc)

print("[REALTEST] Finished real route import test")
