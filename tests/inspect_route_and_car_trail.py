"""
Inspect ROUTE modifiers and CAR_TRAIL constraints in the current .blend.

Intended to be run with:
  blender -b <file>.blend -P inspect_route_and_car_trail.py
"""

import bpy


def inspect_route():
    route_obj = bpy.data.objects.get("ROUTE") or bpy.data.objects.get("Route")
    print("\n=== ROUTE OBJECT INSPECTION ===")
    if not route_obj:
        print("ROUTE object not found")
        return

    print(f"ROUTE object: {route_obj.name} (type={route_obj.type})")
    if not route_obj.modifiers:
        print("ROUTE has no modifiers")
        return

    print("Modifier stack:")
    for idx, mod in enumerate(route_obj.modifiers):
        print(f"  [{idx}] {mod.name} ({mod.type})")

    subsurf = route_obj.modifiers.get("RouteSubsurf")
    if subsurf and subsurf.type == "SUBSURF":
        print(
            "RouteSubsurf levels: viewport="
            f"{getattr(subsurf, 'levels', None)}, "
            f"render={getattr(subsurf, 'render_levels', None)}"
        )
    else:
        print("RouteSubsurf modifier not found or wrong type")


def inspect_car_trail():
    print("\n=== CAR_TRAIL INSPECTION ===")
    car_trail = bpy.data.objects.get("CAR_TRAIL")
    if not car_trail:
        print("CAR_TRAIL object not found")
        return

    print(f"CAR_TRAIL object: {car_trail.name} (type={car_trail.type})")
    print(f"  Collections: {[c.name for c in getattr(car_trail, 'users_collection', []) or []]}")

    constraints = getattr(car_trail, "constraints", None) or []
    print(f"  Constraints: {len(constraints)}")
    for c in constraints:
        target_name = getattr(getattr(c, 'target', None), 'name', None)
        print(f"    - {c.name} ({c.type}) -> target={target_name}")

    print("  Modifiers:")
    for idx, mod in enumerate(car_trail.modifiers):
        print(f"    [{idx}] {mod.name} ({mod.type})")

    curve_data = getattr(car_trail, "data", None)
    if hasattr(curve_data, "animation_data") and curve_data.animation_data:
        drivers = curve_data.animation_data.drivers
        print(f"  Curve data drivers: {len(drivers)}")
        for d in drivers:
            expr = getattr(getattr(d, "driver", None), "expression", "")
            print(f"    - {d.data_path} (expr='{expr}')")
    else:
        print("  Curve data has no animation_data/drivers")


def main():
    inspect_route()
    inspect_car_trail()


if __name__ == "__main__":
    main()

