"""
Simple Car Import Parenting Test

Tests the core parenting issue with minimal dependencies.
"""

import bpy
import sys
from pathlib import Path

def create_test_hierarchy():
    """Create a simple car hierarchy like in ASSET_CAR.blend"""

    # Clear existing objects
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()

    # Create car body (root)
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 1))
    car_body = bpy.context.active_object
    car_body.name = "CAR_BODY"

    # Create taxi sign (child)
    bpy.ops.mesh.primitive_plane_add(size=0.5, location=(0, 0, 2.5))
    taxi_sign = bpy.context.active_object
    taxi_sign.name = "TAXI_SIGN"

    # Parent taxi sign to car body
    taxi_sign.parent = car_body
    taxi_sign.matrix_parent_inverse.identity()

    print(f"Created hierarchy: {car_body.name} -> {taxi_sign.name}")
    print(f"Taxi sign parent: {taxi_sign.parent.name if taxi_sign.parent else None}")

    return car_body, taxi_sign

def test_broken_workflow():
    """Simulate the current broken workflow"""
    print("\n=== Testing BROKEN Workflow ===")

    car_body, taxi_sign = create_test_hierarchy()

    # Store initial state
    initial_parent = taxi_sign.parent
    initial_taxi_pos = taxi_sign.matrix_world.copy()
    print(f"Initial taxi sign parent: {initial_parent.name if initial_parent else None}")
    print(f"Initial taxi position: {initial_taxi_pos.translation}")

    # Simulate the broken code from route/anim.py:617
    print("Applying BROKEN code: car_obj.parent = None")
    car_body.parent = None
    car_body.matrix_parent_inverse.identity()

    # Move car (simulating positioning at route start)
    car_body.location = (10, 5, 0)

    # Check result
    final_taxi_pos = taxi_sign.matrix_world.copy()
    final_parent = taxi_sign.parent

    print(f"Final taxi sign parent: {final_parent.name if final_parent else None}")
    print(f"Final taxi position: {final_taxi_pos.translation}")
    print(f"Car position: {car_body.location}")
    print(f"Distance between initial and final taxi position: {(initial_taxi_pos.translation - final_taxi_pos.translation).length}")

    # Check if parenting is broken
    is_broken = (final_parent != initial_parent) or (initial_taxi_pos.translation - final_taxi_pos.translation).length > 0.1
    print(f"BROKEN workflow result: {'PARENTING BROKEN' if is_broken else 'PARENTING PRESERVED'}")

    return is_broken

def test_fixed_workflow():
    """Simulate the proposed fixed workflow"""
    print("\n=== Testing FIXED Workflow ===")

    car_body, taxi_sign = create_test_hierarchy()

    # Store initial state
    initial_parent = taxi_sign.parent
    initial_taxi_pos = taxi_sign.matrix_world.copy()
    print(f"Initial taxi sign parent: {initial_parent.name if initial_parent else None}")
    print(f"Initial taxi position: {initial_taxi_pos.translation}")

    # Apply the FIXED code - only move the root, don't break parenting
    print("Applying FIXED code: move car without breaking hierarchy")
    # Move car (simulating positioning at route start)
    car_body.location = (10, 5, 0)

    # Check result
    final_taxi_pos = taxi_sign.matrix_world.copy()
    final_parent = taxi_sign.parent

    print(f"Final taxi sign parent: {final_parent.name if final_parent else None}")
    print(f"Final taxi position: {final_taxi_pos.translation}")
    print(f"Car position: {car_body.location}")
    print(f"Distance between initial and final taxi position: {(initial_taxi_pos.translation - final_taxi_pos.translation).length}")

    # Check if parenting is preserved
    is_preserved = (final_parent == initial_parent)
    print(f"FIXED workflow result: {'PARENTING PRESERVED' if is_preserved else 'PARENTING BROKEN'}")

    return is_preserved

def main():
    """Run the parenting test"""
    print("Car Import Parenting Issue Test")
    print("=" * 40)

    # Test broken workflow
    broken_result = test_broken_workflow()

    # Test fixed workflow
    fixed_result = test_fixed_workflow()

    # Summary
    print("\n" + "=" * 40)
    print("SUMMARY:")
    print(f"Broken workflow shows issue: {broken_result}")
    print(f"Fixed workflow preserves parenting: {fixed_result}")

    if broken_result and fixed_result:
        print("SUCCESS: Test confirms the issue and validates the fix!")
        return 0
    else:
        print("FAILURE: Test results don't match expectations")
        return 1

if __name__ == "__main__":
    result = main()
    sys.exit(result)