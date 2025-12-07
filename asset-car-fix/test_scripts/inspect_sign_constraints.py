"""
Inspect taxi sign constraints and drivers in the current scene.

Usage (for saved diagnostic scene):
  blender path/to/headless_route_import_diagnostics.blend --background --python asset-car-fix/test_scripts/inspect_sign_constraints.py
"""

import bpy


def main():
    scene = bpy.context.scene
    print(f"Scene: {scene.name}")

    car = bpy.data.objects.get("ASSET_CAR")
    if not car:
        print("ASSET_CAR not found.")
        return

    print(f"ASSET_CAR world: {tuple(car.matrix_world.translation)}")

    for obj in bpy.data.objects:
        name_l = obj.name.lower()
        if "taxi" in name_l or "sign" in name_l:
            print("\n=== SIGN OBJECT ===")
            print(f"Name: {obj.name}")
            print(f"  Parent: {obj.parent.name if obj.parent else 'None'}")
            print(f"  Local location: {tuple(obj.location)}")
            print(f"  World location: {tuple(obj.matrix_world.translation)}")
            print(f"  matrix_parent_inverse: {tuple(obj.matrix_parent_inverse.translation)}")

            print("  Constraints:")
            for c in obj.constraints:
                print(f"    - {c.name} ({c.type}), mute={getattr(c, 'mute', False)}, inf={getattr(c, 'influence', 1.0)}")

            anim = getattr(obj, "animation_data", None)
            if anim and anim.action:
                print("  FCurves:")
                for fc in anim.action.fcurves:
                    print(f"    - {fc.data_path} [{fc.array_index}]")

            if anim and anim.drivers:
                print("  Drivers:")
                for d in anim.drivers:
                    print(f"    - {d.data_path} [{d.array_index}]")


if __name__ == "__main__":
    main()

