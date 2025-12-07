"""
Realistic Car Import Parenting Test

More accurately simulates the actual car import workflow from the cash-cab-addon.
"""

import bpy
import sys
from mathutils import Matrix

def create_realistic_car_hierarchy():
    """Create a car hierarchy that matches the actual ASSET_CAR structure"""

    # Clear existing objects
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()

    # Create collection like ASSET_CAR
    car_collection = bpy.data.collections.new("ASSET_CAR")
    bpy.context.scene.collection.children.link(car_collection)

    # Create car body (main object that gets selected and moved)
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 1))
    car_body = bpy.context.active_object
    car_body.name = "ASSET_CAR"
    # Move to collection directly
    try:
        bpy.context.scene.collection.objects.unlink(car_body)
    except RuntimeError:
        pass  # Object might not be in scene collection
    car_collection.objects.link(car_body)

    # Create taxi sign as separate object that should be child of car
    bpy.ops.mesh.primitive_plane_add(size=0.5, location=(0, 0, 2.5))
    taxi_sign = bpy.context.active_object
    taxi_sign.name = "taxi sign.002"
    # Move to collection directly
    try:
        bpy.context.scene.collection.objects.unlink(taxi_sign)
    except RuntimeError:
        pass  # Object might not be in scene collection
    car_collection.objects.link(taxi_sign)

    # Create the parent-child relationship as it exists in the .blend file
    taxi_sign.parent = car_body
    taxi_sign.matrix_parent_inverse = car_body.matrix_world.inverted()

    print(f"Created realistic hierarchy:")
    print(f"  Collection: ASSET_CAR")
    print(f"  Car body: {car_body.name}")
    print(f"  Taxi sign: {taxi_sign.name}")
    print(f"  Parenting: {taxi_sign.parent.name if taxi_sign.parent else None}")

    return car_collection, car_body, taxi_sign

def simulate_asset_import_workflow():
    """Simulate the actual asset import and car positioning workflow"""

    print("=== Simulating ASSET_CAR Import Workflow ===")

    # Step 1: Import car hierarchy (simulated)
    car_collection, car_body, taxi_sign = create_realistic_car_hierarchy()

    # Step 2: Check initial state
    print(f"\nInitial state:")
    print(f"  Car body location: {car_body.location}")
    print(f"  Taxi sign parent: {taxi_sign.parent.name if taxi_sign.parent else None}")
    print(f"  Taxi sign world position: {taxi_sign.matrix_world.translation}")

    initial_taxi_pos = taxi_sign.matrix_world.copy()

    # Step 3: Simulate the problematic code from route/assets.py and route/anim.py
    print(f"\nApplying PROBLEMATIC code from actual workflow:")

    # This simulates what happens in route/anim.py:617 and route/fetch_operator.py:1072
    # The code finds the car object and clears its parent to position it
    print("  Clearing parent on car object...")
    car_body.parent = None
    car_body.matrix_parent_inverse = Matrix.Identity(4)

    # Then position the car at route start
    print("  Positioning car at route start...")
    car_body.location = (10, 5, 1)  # Simulate route start position

    print(f"  Car body location after positioning: {car_body.location}")

    # Step 4: Check if taxi sign followed the car
    final_taxi_pos = taxi_sign.matrix_world.copy()
    print(f"\nFinal state:")
    print(f"  Taxi sign parent: {taxi_sign.parent.name if taxi_sign.parent else None}")
    print(f"  Taxi sign world position: {final_taxi_pos.translation}")
    print(f"  Expected taxi position (should follow car): <Vector (10.0000, 5.0000, 2.5000)>")

    # Calculate if taxi sign moved with car
    expected_x = 10.0 + 0.0  # car.x + taxi_sign.relative.x
    expected_y = 5.0 + 0.0   # car.y + taxi_sign.relative.y
    expected_z = 1.0 + 1.5   # car.z + taxi_sign.relative.z

    distance_from_expected = abs(final_taxi_pos.translation.x - expected_x) + abs(final_taxi_pos.translation.y - expected_y) + abs(final_taxi_pos.translation.z - expected_z)

    print(f"  Distance from expected position: {distance_from_expected}")

    # Check if parenting relationship was affected
    parent_changed = taxi_sign.parent != car_body
    taxi_moved = (initial_taxi_pos.translation - final_taxi_pos.translation).length > 0.01

    print(f"\nResults:")
    print(f"  Parent relationship intact: {not parent_changed}")
    print(f"  Taxi sign moved: {taxi_moved}")
    print(f"  Issue reproduced: {parent_changed or distance_from_expected > 0.1}")

    return {
        'parent_intact': not parent_changed,
        'taxi_moved_with_car': distance_from_expected < 0.1,
        'issue_reproduced': parent_changed or distance_from_expected > 0.1,
        'initial_pos': initial_taxi_pos.translation,
        'final_pos': final_taxi_pos.translation,
        'expected_pos': (expected_x, expected_y, expected_z)
    }

def test_proposed_fix():
    """Test the proposed fix that preserves hierarchy"""

    print("\n=== Testing PROPOSED FIX ===")

    # Recreate hierarchy
    car_collection, car_body, taxi_sign = create_realistic_car_hierarchy()

    initial_taxi_pos = taxi_sign.matrix_world.copy()

    # Apply proposed fix: don't clear parent, just position the car
    print("Applying FIXED code: position car without breaking hierarchy...")
    car_body.location = (10, 5, 1)

    final_taxi_pos = taxi_sign.matrix_world.copy()

    # Check if taxi sign followed car
    expected_x = 10.0 + 0.0
    expected_y = 5.0 + 0.0
    expected_z = 1.0 + 1.5

    distance_from_expected = abs(final_taxi_pos.translation.x - expected_x) + abs(final_taxi_pos.translation.y - expected_y) + abs(final_taxi_pos.translation.z - expected_z)

    parent_intact = taxi_sign.parent == car_body

    print(f"  Parent relationship intact: {parent_intact}")
    print(f"  Taxi sign position: {final_taxi_pos.translation}")
    print(f"  Distance from expected: {distance_from_expected}")

    return {
        'parent_intact': parent_intact,
        'taxi_followed_car': distance_from_expected < 0.1,
        'fix_works': parent_intact and distance_from_expected < 0.1
    }

def main():
    """Run the realistic test"""
    print("Realistic Car Import Parenting Test")
    print("=" * 50)

    # Test current workflow to reproduce issue
    current_results = simulate_asset_import_workflow()

    # Test proposed fix
    fix_results = test_proposed_fix()

    # Summary
    print("\n" + "=" * 50)
    print("COMPREHENSIVE ANALYSIS:")
    print(f"Current workflow reproduces issue: {current_results['issue_reproduced']}")
    print(f"Proposed fix works: {fix_results['fix_works']}")

    if current_results['issue_reproduced'] and fix_results['fix_works']:
        print("\nSUCCESS: Test confirms the parenting issue and validates the fix!")
        print("\nRECOMMENDATION:")
        print("1. Remove 'car_obj.parent = None' from route/anim.py:617")
        print("2. Remove 'car_obj.parent = None' from route/fetch_operator.py:1072")
        print("3. Position the car object directly without clearing parent relationships")
        return 0
    elif not current_results['issue_reproduced']:
        print("\nINFO: Issue not reproduced with this test")
        print("The parenting issue might occur in a different part of the workflow")
        print("Check route/assets.py for additional parent clearing operations")
        return 0
    else:
        print("\nFAILURE: Fix doesn't resolve the issue")
        return 1

if __name__ == "__main__":
    result = main()
    sys.exit(result)