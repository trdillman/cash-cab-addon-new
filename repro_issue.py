
import bpy
import sys
import os
from pathlib import Path

# Add addon directory to path to allow importing its modules

# Import addon as a package so relative imports inside route.* work
# We'll treat the addon dir as the package root for simplicity, or mock the package structure.
# The addon code uses specific relative imports (e.g. `from ..app`) so it expects to be in a package.

addon_dir = Path(r"c:\Users\Tyler\AppData\Roaming\Blender Foundation\Blender\4.5\scripts\addons\cash-cab-addon-new")
init_path = addon_dir / "__init__.py"

import importlib.util

# We name the package 'cash_cab_addon' to match what the test does
spec = importlib.util.spec_from_file_location("cash_cab_addon", init_path)
module = importlib.util.module_from_spec(spec)
sys.modules["cash_cab_addon"] = module
spec.loader.exec_module(module)

# Register addon (sets up app/blender, etc.)
try:
    module.register()
except Exception as e:
    print(f"Warning: Register failed: {e}")

# Now we can import the module as part of the package
from cash_cab_addon.route import pipeline_finalizer as pf

def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    for c in list(bpy.data.collections):
        if c.name not in {"Scene Collection"}:
            try: 
                bpy.data.collections.remove(c)
            except: pass
    
    # Also clear data blocks to be clean
    for c in bpy.data.curves: bpy.data.curves.remove(c)
    for m in bpy.data.meshes: bpy.data.meshes.remove(m)
    for o in bpy.data.objects: bpy.data.objects.remove(o)

def create_bad_profile_curve():
    # Create an object named "_profile_curve" that is NOT a curve (e.g. Empty or Mesh)
    # This simulates the "zombie" object the user might have
    mesh = bpy.data.meshes.new("BadProfileMesh")
    obj = bpy.data.objects.new("_profile_curve", mesh) # Name it exactly _profile_curve
    bpy.context.scene.collection.objects.link(obj)
    return obj

def create_minimal_route_and_car():
    # ROUTE curve
    curve_data = bpy.data.curves.new("ROUTE_CURVE", "CURVE")
    curve_data.dimensions = "3D"
    spline = curve_data.splines.new("BEZIER")
    route_obj = bpy.data.objects.new("ROUTE", curve_data)
    bpy.context.scene.collection.objects.link(route_obj)

    # ASSET_CAR collection
    car_coll = bpy.data.collections.new("ASSET_CAR")
    bpy.context.scene.collection.children.link(car_coll)
    return route_obj

def run_test():
    clear_scene()
    print("--- Setup: Creating bad _profile_curve ---")
    bad_obj = create_bad_profile_curve()
    print(f"Created object: {bad_obj.name} (Type: {bad_obj.type})")
    
    # Ensure it's really there
    if "_profile_curve" in bpy.data.objects:
        print("Verified _profile_curve exists in bpy.data.objects")
    
    print("--- Setup: Creating Route and Car ---")
    create_minimal_route_and_car()
    
    print("--- Running _build_car_trail_from_route ---")
    scene = bpy.context.scene
    
    # This function uses _ensure_profile_curve internally
    car_trail = pf._build_car_trail_from_route(scene)
    
    with open("results.txt", "w") as f:
        f.write("--- Results ---\n")
        if car_trail:
            bevel_obj = car_trail.data.bevel_object
            f.write(f"CAR_TRAIL formed: {car_trail.name}\n")
            f.write(f"Bevel Object: {bevel_obj}\n")
            if bevel_obj:
                f.write(f"Bevel Object Name: {bevel_obj.name}\n")
                f.write(f"Bevel Object Type: {bevel_obj.type}\n")
            else:
                f.write("FAILURE: No bevel object assigned.\n")
        else:
            f.write("FAILURE: CAR_TRAIL not created.\n")
            
        # Check what objects exist now
        f.write("\nExisting objects with 'profile' in name:\n")
        for o in bpy.data.objects:
            if "profile" in o.name:
                f.write(f"  {o.name} (Type: {o.type})\n")

if __name__ == "__main__":
    run_test()
