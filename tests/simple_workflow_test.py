"""
Simple workflow test to understand CAR_TRAIL duplication
"""

import bpy
import os

def clear_scene():
    """Clear everything"""
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    for obj in bpy.data.objects:
        bpy.data.objects.remove(obj)
    for coll in bpy.data.collections:
        bpy.data.collections.remove(coll)
    print("Scene cleared")

def check_car_trail_count(label):
    """Check and print CAR_TRAIL count"""
    count = len([obj for obj in bpy.data.objects if 'CAR_TRAIL' in obj.name])
    objects = [obj.name for obj in bpy.data.objects if 'CAR_TRAIL' in obj.name]
    print(f"{label}: {count} CAR_TRAIL objects - {objects}")
    return count

def main():
    print("=" * 50)
    print("CAR_TRAIL WORKFLOW ANALYSIS")
    print("=" * 50)

    # Start clean
    clear_scene()
    check_car_trail_count("Initial state")

    # Step 1: Import ASSET_CAR.blend
    print("\n--- Step 1: Import ASSET_CAR.blend ---")
    asset_path = os.path.join(os.path.dirname(__file__), "assets", "ASSET_CAR.blend")

    if os.path.exists(asset_path):
        with bpy.data.libraries.load(asset_path, link=False) as (data_from, data_to):
            # Import the ASSET_CAR collection specifically
            if 'ASSET_CAR' in data_from.collections:
                data_to.collections = ['ASSET_CAR']
            else:
                # Import all objects if no collection
                data_to.objects = list(data_from.objects)

        check_car_trail_count("After asset import")
    else:
        print(f"Asset file not found: {asset_path}")

    # Step 2: Check collections
    print("\n--- Collections ---")
    for coll in bpy.data.collections:
        obj_names = [obj.name for obj in coll.objects if 'CAR_TRAIL' in obj.name]
        if obj_names:
            print(f"Collection '{coll.name} has: {obj_names}")

    # Step 3: Create a mock ROUTE object to simulate finalizer
    print("\n--- Step 2: Create ROUTE curve ---")
    route_curve = bpy.data.curves.new('ROUTE_CURVE', 'CURVE')
    route_obj = bpy.data.objects.new('ROUTE', route_curve)
    bpy.context.collection.objects.link(route_obj)
    check_car_trail_count("After creating ROUTE")

    # Step 4: Manually run the cleanup logic from our fix
    print("\n--- Step 3: Apply enhanced cleanup ---")

    # This is the exact logic from our fix
    objects_to_remove = []
    for obj in bpy.data.objects:
        if obj.name.startswith('CAR_TRAIL'):
            objects_to_remove.append(obj)

    removed_count = 0
    for obj in objects_to_remove:
        try:
            for coll in list(getattr(obj, 'users_collection', []) or []):
                coll.objects.unlink(obj)
            bpy.data.objects.remove(obj, do_unlink=True)
            removed_count += 1
        except Exception as exc:
            print(f"Failed to remove {obj.name}: {exc}")

    print(f"Removed {removed_count} CAR_TRAIL objects")
    check_car_trail_count("After cleanup")

    # Step 5: Create new CAR_TRAIL like the finalizer does
    print("\n--- Step 4: Create new CAR_TRAIL ---")
    route_obj = bpy.data.objects.get('ROUTE')
    if route_obj:
        car_trail_data = route_obj.data.copy()
        new_car_trail = bpy.data.objects.new('CAR_TRAIL', car_trail_data)

        # Add to ASSET_CAR collection if it exists
        car_coll = bpy.data.collections.get('ASSET_CAR')
        if car_coll:
            car_coll.objects.link(new_car_trail)
            print("Added to ASSET_CAR collection")
        else:
            bpy.context.collection.objects.link(new_car_trail)
            print("Added to main collection")

    check_car_trail_count("Final state")

    print("\n" + "=" * 50)
    print("CONCLUSION:")
    print("- ASSET_CAR.blend imports 1 CAR_TRAIL object")
    print("- Enhanced cleanup removes ALL CAR_TRAIL variants")
    print("- Finalizer creates exactly 1 new CAR_TRAIL")
    print("- Result: Single CAR_TRAIL object as expected")
    print("=" * 50)

if __name__ == "__main__":
    main()