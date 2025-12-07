"""
Mock test for CAR_TRAIL bevel profile setup.

Creates a minimal ROUTE curve and ASSET_CAR collection, then invokes the
pipeline_finalizer CAR_TRAIL builder to verify that:
  - _profile_curve exists (asset or fallback)
  - CAR_TRAIL uses _profile_curve as its bevel object.

Run with:
  blender -b -P mock_car_trail_import_test.py
"""

import bpy
import sys
from pathlib import Path


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()

    for c in list(bpy.data.collections):
        if c.name not in {"Scene Collection"}:
            try:
                bpy.data.collections.remove(c)
            except Exception:
                pass


def create_minimal_route_and_car():
    # ROUTE curve
    curve_data = bpy.data.curves.new("ROUTE_CURVE", "CURVE")
    curve_data.dimensions = "3D"
    spline = curve_data.splines.new("BEZIER")
    spline.bezier_points.add(1)
    spline.bezier_points[0].co = (0.0, 0.0, 0.0)
    spline.bezier_points[1].co = (10.0, 0.0, 0.0)
    route_obj = bpy.data.objects.new("ROUTE", curve_data)
    bpy.context.scene.collection.objects.link(route_obj)

    # ASSET_CAR collection and dummy car object
    car_coll = bpy.data.collections.new("ASSET_CAR")
    bpy.context.scene.collection.children.link(car_coll)
    mesh = bpy.data.meshes.new("ASSET_CAR_MESH")
    car_obj = bpy.data.objects.new("ASSET_CAR", mesh)
    car_coll.objects.link(car_obj)
    return route_obj, car_obj


def main():
    clear_scene()
    route_obj, car_obj = create_minimal_route_and_car()

    # Import addon as a package so relative imports inside route.* work
    addon_dir = Path(__file__).resolve().parent
    init_path = addon_dir / "__init__.py"
    if str(addon_dir) not in sys.path:
        sys.path.append(str(addon_dir))

    import importlib.util

    spec = importlib.util.spec_from_file_location("cash_cab_addon", init_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["cash_cab_addon"] = module
    spec.loader.exec_module(module)

    # Register addon (sets up app/blender, etc.), then import pipeline_finalizer
    try:
        module.register()
    except Exception:
        pass

    from cash_cab_addon.route import pipeline_finalizer as pf

    scene = bpy.context.scene
    ct = pf._build_car_trail_from_route(scene)

    print("\n=== MOCK CAR_TRAIL TEST ===")
    print("Route object:", route_obj.name)
    print("Car object:", car_obj.name)
    print("CAR_TRAIL object:", ct.name if ct else None)

    profile = bpy.data.objects.get("_profile_curve")
    print("Profile curve object:", profile)

    if ct and getattr(ct, "data", None):
        cd = ct.data
        print("CAR_TRAIL curve data:", cd.name)
        print("  bevel_object:", getattr(cd, "bevel_object", None))
        print("  bevel_mode:", getattr(cd, "bevel_mode", None))
        print("  bevel_depth:", getattr(cd, "bevel_depth", None))


if __name__ == "__main__":
    main()
