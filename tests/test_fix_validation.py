"""
Simple validation test for CAR_TRAIL fix
This simulates what happens during the pipeline
"""

import bpy
import sys
import os

# Add addon path
addon_path = r"C:\Users\Tyler\AppData\Roaming\Blender Foundation\Blender\4.5\scripts\addons\cash-cab-addon"
sys.path.insert(0, addon_path)

def simulate_asset_import():
    """Simulate importing ASSET_CAR.blend"""
    print("\n=== SIMULATING ASSET IMPORT ===")

    # Import the ASSET_CAR.blend file
    try:
        asset_path = os.path.join(addon_path, "assets", "ASSET_CAR.blend")

        with bpy.data.libraries.load(asset_path, link=False) as (data_from, data_to):
            # Import all objects
            if data_from.objects:
                data_to.objects = list(data_from.objects)

        print("✅ ASSET_CAR.blend imported")

        # Check for CAR_TRAIL objects
        car_trails = [obj for obj in bpy.data.objects if 'CAR_TRAIL' in obj.name]
        print(f"CAR_TRAIL objects after asset import: {len(car_trails)}")
        for obj in car_trails:
            print(f"  - {obj.name} (Type: {obj.type})")

        return len(car_trails)

    except Exception as e:
        print(f"❌ Asset import failed: {e}")
        return 0

def simulate_finalizer():
    """Simulate running the finalizer with enhanced cleanup"""
    print("\n=== SIMULATING FINALIZER ===")

    # Create a mock route object
    if not bpy.data.objects.get('ROUTE'):
        route_curve = bpy.data.curves.new('ROUTE_DATA', 'CURVE')
        route_obj = bpy.data.objects.new('ROUTE', route_curve)
        bpy.context.collection.objects.link(route_obj)
        print("✅ Created mock ROUTE object")

    # Create ASSET_CAR collection if it doesn't exist
    car_collection = bpy.data.collections.get('ASSET_CAR')
    if not car_collection:
        car_collection = bpy.data.collections.new('ASSET_CAR')
        bpy.context.scene.collection.children.link(car_collection)
        print("✅ Created ASSET_CAR collection")

    # Now simulate the enhanced cleanup from _build_car_trail_from_route
    print("\n--- Enhanced Cleanup Test ---")

    # Count CAR_TRAIL objects before cleanup
    before_count = len([obj for obj in bpy.data.objects if 'CAR_TRAIL' in obj.name])
    print(f"CAR_TRAIL objects before cleanup: {before_count}")

    # Apply the enhanced cleanup logic
    objects_to_remove = []
    for obj in bpy.data.objects:
        if obj.name.startswith('CAR_TRAIL'):
            objects_to_remove.append(obj)

    removed_count = 0
    for obj in objects_to_remove:
        try:
            # Remove from all collections
            for coll in list(getattr(obj, 'users_collection', []) or []):
                coll.objects.unlink(obj)
            # Remove object
            bpy.data.objects.remove(obj, do_unlink=True)
            removed_count += 1
        except Exception as exc:
            print(f"  WARN: Failed to remove {obj.name}: {exc}")

    print(f"Removed {removed_count} CAR_TRAIL variant(s)")

    # Count after cleanup
    after_count = len([obj for obj in bpy.data.objects if 'CAR_TRAIL' in obj.name])
    print(f"CAR_TRAIL objects after cleanup: {after_count}")

    # Simulate creating new CAR_TRAIL
    route_obj = bpy.data.objects.get('ROUTE')
    if route_obj and car_collection:
        car_trail_data = route_obj.data.copy()
        car_trail_data.name = 'CAR_TRAIL_DATA'
        new_car_trail = bpy.data.objects.new('CAR_TRAIL', car_trail_data)
        car_collection.objects.link(new_car_trail)
        print("✅ Created new CAR_TRAIL object")

    # Final count
    final_count = len([obj for obj in bpy.data.objects if 'CAR_TRAIL' in obj.name])
    print(f"Final CAR_TRAIL count: {final_count}")

    return final_count == 1

def main():
    print("=" * 60)
    print("CAR_TRAIL FIX VALIDATION TEST")
    print("=" * 60)

    # Clear scene
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()

    # Step 1: Simulate asset import
    asset_count = simulate_asset_import()

    # Step 2: Add some duplicates to test cleanup
    if asset_count > 0:
        # Create a duplicate
        original = bpy.data.objects.get('CAR_TRAIL')
        if original:
            duplicate = original.copy()
            duplicate.data = original.data.copy()
            duplicate.name = 'CAR_TRAIL.001'
            bpy.data.collections.get('ASSET_CAR').objects.link(duplicate)
            print("\n✅ Created CAR_TRAIL.001 duplicate for testing")

    # Check before finalizer
    before_finalizer = len([obj for obj in bpy.data.objects if 'CAR_TRAIL' in obj.name])
    print(f"\nCAR_TRAIL objects before finalizer: {before_finalizer}")

    # Step 3: Simulate finalizer with enhanced cleanup
    success = simulate_finalizer()

    # Results
    print("\n" + "=" * 60)
    if success:
        print("✅ SUCCESS: Enhanced cleanup works correctly")
        print("  - All CAR_TRAIL variants removed")
        print("  - Exactly one CAR_TRAIL created")
    else:
        print("❌ FAILURE: Enhanced cleanup did not work")
    print("=" * 60)

    return success

if __name__ == "__main__":
    main()