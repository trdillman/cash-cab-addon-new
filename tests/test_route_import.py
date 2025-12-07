import bpy
import sys
import importlib.util
from pathlib import Path

print("[TEST] Starting route animation alignment test")

# Load addon package from this folder as 'cash_cab_addon'
addon_dir = Path(r"C:\Users\Tyler\AppData\Roaming\Blender Foundation\Blender\4.5\scripts\addons\cash-cab-addon")
init_path = addon_dir / "__init__.py"

spec = importlib.util.spec_from_file_location("cash_cab_addon", init_path)
if spec is None or spec.loader is None:
    print("[TEST] ERROR: could not create spec for addon")
    sys.exit(1)

module = importlib.util.module_from_spec(spec)
sys.modules["cash_cab_addon"] = module
spec.loader.exec_module(module)

print("[TEST] Addon module loaded as cash_cab_addon")

# Register addon (sets up scene animation properties etc.)
try:
    module.register()
    print("[TEST] Addon registered")
except Exception as exc:
    print("[TEST] ERROR registering addon:", exc)

from cash_cab_addon.route import anim as route_anim
from cash_cab_addon.route import pipeline_finalizer as route_pipeline_finalizer

scene = bpy.context.scene
print("[TEST] Using scene:", scene.name)

# Wipe existing objects for a clean synthetic test
bpy.ops.object.select_all(action='SELECT')
try:
    bpy.ops.object.delete(use_global=False)
except Exception as exc:
    print("[TEST] WARN delete objects:", exc)

# Create a simple straight ROUTE curve
curve_data = bpy.data.curves.new("ROUTE", type='CURVE')
curve_data.dimensions = '3D'
curve_data.use_path = True
spline = curve_data.splines.new('POLY')
spline.points.add(1)
spline.points[0].co = (0.0, 0.0, 0.0, 1.0)
spline.points[1].co = (50.0, 0.0, 0.0, 1.0)
route_obj = bpy.data.objects.new("ROUTE", curve_data)
scene.collection.objects.link(route_obj)
print("[TEST] Created route object:", route_obj.name)

# Create a simple ASSET_CAR object (cube mesh)
mesh = bpy.data.meshes.new("ASSET_CAR_MESH")
car_obj = bpy.data.objects.new("ASSET_CAR", mesh)
scene.collection.objects.link(car_obj)

car_coll = bpy.data.collections.new("ASSET_CAR")
scene.collection.children.link(car_coll)
for coll in list(getattr(car_obj, 'users_collection', []) or []):
    try:
        coll.objects.unlink(car_obj)
    except Exception:
        pass
car_coll.objects.link(car_obj)
print("[TEST] Created car object:", car_obj.name)

# Ensure animation scene properties exist and set test values
try:
    scene.blosm_anim_start = 15
    scene.blosm_anim_end = 150
    scene.blosm_lead_frames = 1
    print("[TEST] Scene animation props:", scene.blosm_anim_start, scene.blosm_anim_end, scene.blosm_lead_frames)
except Exception as exc:
    print("[TEST] WARN setting scene animation props:", exc)

# Run pipeline finalizer to mimic post-import cleanup
try:
    pf_result = route_pipeline_finalizer.run(scene)
    print("[TEST] pipeline_finalizer.run result:", pf_result)
except Exception as exc:
    print("[TEST] ERROR running pipeline_finalizer.run:", exc)

# Force keyframes using the shared helper
try:
    route_anim.force_follow_keyframes(scene)
    print("[TEST] Forced follow keyframes")
except Exception as exc:
    print("[TEST] ERROR forcing follow keyframes:", exc)

# Print keyframes for car and lead
try:
    route_anim.debug_print_follow_offset_keyframes(scene)
except Exception as exc:
    print("[TEST] ERROR in debug_print_follow_offset_keyframes:", exc)

# Save and reopen the file, then re-print to ensure persistence
output_path = addon_dir / "test_route_import_synthetic.blend"
try:
    bpy.ops.wm.save_mainfile(filepath=str(output_path))
    print(f"[TEST] Saved test file to {output_path}")
except Exception as exc:
    print("[TEST] ERROR saving blend file:", exc)

try:
    bpy.ops.wm.open_mainfile(filepath=str(output_path))
    scene2 = bpy.context.scene
    print("[TEST] Reopened saved blend file; scene:", scene2.name)
    from cash_cab_addon.route import anim as route_anim2
    route_anim2.debug_print_follow_offset_keyframes(scene2)
except Exception as exc:
    print("[TEST] ERROR reopening or re-debugging blend file:", exc)

print("[TEST] Finished route animation alignment test")
