"""
One-time asset fix for assets/ASSET_CAR.blend

This script is meant to be run with:

  blender assets/ASSET_CAR.blend --background --python asset-car-fix/test_scripts/fix_asset_car_asset_file.py

It performs a minimal, conservative cleanup:
- Finds the ASSET_CAR object.
- Identifies taxi/sign children.
- Repairs their parenting and basic transforms so they are positioned
  above the car, instead of effectively pinned at the origin.

The runtime pipeline still contains its own safety repair, but this
gives the asset a saner default state.
"""

import bpy
from mathutils import Matrix, Vector


def fix_asset_car_scene():
    car = bpy.data.objects.get("ASSET_CAR")
    if car is None:
        print("[ASSET_FIX] ASSET_CAR object not found; nothing to do.")
        return

    sign_children = []
    for obj in bpy.data.objects:
        if obj.parent == car and any(k in obj.name.lower() for k in ["taxi", "sign"]):
            sign_children.append(obj)

    if not sign_children:
        print("[ASSET_FIX] No taxi/sign children found under ASSET_CAR; nothing to do.")
        return

    print(f"[ASSET_FIX] Found {len(sign_children)} taxi/sign children under ASSET_CAR:")
    for s in sign_children:
        print(f"  - {s.name}")

    # Normalize ASSET_CAR transform (keep as-is; we only tweak children)
    for sign in sign_children:
        try:
            print(f"[ASSET_FIX] Repairing {sign.name} in asset file")
            # Ensure parent is ASSET_CAR
            sign.parent = car
            # Reset parent inverse so local location is meaningful
            sign.matrix_parent_inverse = Matrix.Identity(4)
            # Place sign slightly above car in local Z
            sign.location = Vector((0.0, 0.0, 1.5))
        except Exception as exc:
            print(f"[ASSET_FIX] Warning while fixing {sign.name}: {exc}")

    # Optionally, leave stray unparented taxi signs alone (they will be ignored at runtime)
    print("[ASSET_FIX] Asset fix complete; saving file.")
    bpy.ops.wm.save_mainfile()


def main():
    fix_asset_car_scene()


if __name__ == "__main__":
    main()

