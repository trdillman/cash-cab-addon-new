"""
Check if CAR_TRAIL in ASSET_CAR.blend has constraints
"""

import bpy
import os

def check_asset_car_trail():
    """Check constraints on CAR_TRAIL in ASSET_CAR.blend"""
    print("Checking CAR_TRAIL constraints in ASSET_CAR.blend...")

    # Clear current scene
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()

    # Load ASSET_CAR.blend
    asset_path = os.path.join(os.path.dirname(__file__), "assets", "ASSET_CAR.blend")

    if os.path.exists(asset_path):
        bpy.ops.wm.open_mainfile(filepath=asset_path)

        car_trail = bpy.data.objects.get('CAR_TRAIL')
        if car_trail:
            print(f"\n✅ CAR_TRAIL found")
            print(f"   Type: {car_trail.type}")
            print(f"   Collections: {[c.name for c in car_trail.users_collection]}")

            if car_trail.constraints:
                print(f"\n⚠️  CAR_TRAIL HAS {len(car_trail.constraints)} CONSTRAINT(S):")
                for c in car_trail.constraints:
                    target_name = c.target.name if c.target else "None"
                    print(f"   - {c.name} ({c.type}) -> Target: {target_name}")
                    print(f"     Influence: {c.influence}")
            else:
                print("\n✅ CAR_TRAIL has no constraints")
        else:
            print("\n❌ No CAR_TRAIL found in ASSET_CAR.blend")
    else:
        print(f"\n❌ ASSET_CAR.blend not found at: {asset_path}")

def check_runtime_car_trail():
    """Create a CAR_TRAIL like the runtime process does"""
    print("\n" + "="*50)
    print("Checking runtime-created CAR_TRAIL...")

    # Create mock objects
    route_curve = bpy.data.curves.new('ROUTE_CURVE', 'CURVE')
    route_obj = bpy.data.objects.new('ROUTE', route_curve)
    bpy.context.collection.objects.link(route_obj)

    car_collection = bpy.data.collections.new('ASSET_CAR')
    bpy.context.scene.collection.children.link(car_collection)

    # Simulate runtime creation (simplified)
    car_trail_data = route_obj.data.copy()
    new_car_trail = bpy.data.objects.new('CAR_TRAIL', car_trail_data)
    car_collection.objects.link(new_car_trail)

    print(f"\nRuntime CAR_TRAIL created")
    print(f"   Constraints: {len(new_car_trail.constraints)}")

    # Check if runtime process adds constraints elsewhere
    # Search the codebase for where constraints might be added

def search_constraint_application():
    """Search for where constraints might be applied to CAR_TRAIL"""
    print("\n" + "="*50)
    print("Searching for constraint application code...")

    # This would need manual code review
    # Look for:
    # - Functions that add constraints to objects
    # - Code that processes CAR_TRAIL after creation
    # - Generic constraint application that might include CAR_TRAIL

if __name__ == "__main__":
    check_asset_car_trail()
    check_runtime_car_trail()

    print("\n" + "="*50)
    print("RECOMMENDATION:")
    print("1. If CAR_TRAIL has constraints in ASSET_CAR.blend:")
    print("   - Remove them from the blend file")
    print("   - Or add cleanup code to remove constraints")
    print("2. If constraints are added during pipeline:")
    print("   - Find the code adding them")
    print("   - Add check to skip CAR_TRAIL")