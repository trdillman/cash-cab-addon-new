"""
Simple Parenting Test - Demonstrate the Issue and Save Solutions

This test demonstrates that Blender parent-child relationships are not working
correctly in the CashCab addon environment, and provides working solutions.
"""

import bpy
import sys
from pathlib import Path
from mathutils import Vector, Matrix

def create_broken_hierarchy_test():
    """Create test showing the broken parenting behavior"""

    print("=== BROKEN PARENTING TEST ===")

    # Clear scene
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()

    # Create car body
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 1))
    car_body = bpy.context.active_object
    car_body.name = "CAR_BODY_BROKEN"

    # Create taxi sign
    bpy.ops.mesh.primitive_plane_add(size=0.5, location=(0, 0, 2.5))
    taxi_sign = bpy.context.active_object
    taxi_sign.name = "TAXI_SIGN_BROKEN"

    # Create proper parent-child relationship
    taxi_sign.parent = car_body
    taxi_sign.matrix_parent_inverse = car_body.matrix_world.inverted()

    print(f"Created hierarchy: {car_body.name} -> {taxi_sign.name}")
    print(f"Initial car position: {car_body.location}")
    print(f"Initial taxi world position: {taxi_sign.matrix_world.translation}")

    # Test movement
    car_body.location = (5, 3, 2)

    print(f"After moving car to {car_body.location}:")
    print(f"Taxi world position: {taxi_sign.matrix_world.translation}")
    print(f"Expected taxi position: {Vector((5, 3, 3.5))}")

    distance = (taxi_sign.matrix_world.translation - Vector((5, 3, 3.5))).length
    print(f"Distance from expected: {distance:.6f}")
    print(f"Result: {'BROKEN - Taxi did not follow car' if distance > 0.1 else 'WORKING - Taxi followed car'}")

    return distance > 0.1  # True if broken, False if working

def create_manual_sync_test():
    """Create test showing manual synchronization solution"""

    print("\n=== MANUAL SYNC SOLUTION TEST ===")

    # Clear scene
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()

    # Create car body
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 1))
    car_body = bpy.context.active_object
    car_body.name = "CAR_BODY_FIXED"

    # Create taxi sign
    bpy.ops.mesh.primitive_plane_add(size=0.5, location=(0, 0, 2.5))
    taxi_sign = bpy.context.active_object
    taxi_sign.name = "TAXI_SIGN_FIXED"

    # Create parent-child relationship
    taxi_sign.parent = car_body
    taxi_sign.matrix_parent_inverse = car_body.matrix_world.inverted()

    # Store relative positions
    relative_positions = {
        taxi_sign.name: taxi_sign.location.copy()
    }

    print(f"Created fixed hierarchy: {car_body.name} -> {taxi_sign.name}")
    print(f"Initial car position: {car_body.location}")
    print(f"Initial taxi world position: {taxi_sign.matrix_world.translation}")

    # Manual synchronization function
    def sync_child_objects(car_obj, child_positions):
        """Manually sync child objects with parent movement"""
        for child_name, rel_pos in child_positions.items():
            child_obj = bpy.data.objects.get(child_name)
            if child_obj:
                # Calculate world position based on parent
                child_obj.location = rel_pos
                # Re-establish parenting if broken
                if child_obj.parent != car_obj:
                    child_obj.parent = car_obj
                    child_obj.matrix_parent_inverse = car_obj.matrix_world.inverted()

    # Test movement with manual sync
    car_body.location = (5, 3, 2)

    # Apply manual synchronization
    sync_child_objects(car_body, relative_positions)

    print(f"After moving car to {car_body.location} and applying manual sync:")
    print(f"Taxi world position: {taxi_sign.matrix_world.translation}")
    print(f"Expected taxi position: {Vector((5, 3, 3.5))}")

    distance = (taxi_sign.matrix_world.translation - Vector((5, 3, 3.5))).length
    print(f"Distance from expected: {distance:.6f}")
    print(f"Result: {'WORKING - Taxi followed car' if distance < 0.1 else 'STILL BROKEN'}")

    return distance < 0.1  # True if working, False if broken

def save_test_scenes(broken_result, fixed_result):
    """Save the test scenes for analysis"""

    save_dir = Path(__file__).parent / "test_scenes"
    save_dir.mkdir(exist_ok=True)

    # Save broken test scene
    if broken_result:
        broken_path = save_dir / "broken_parenting_test.blend"
        bpy.ops.wm.save_as_mainfile(filepath=str(broken_path))
        print(f"\nBroken test scene saved to: {broken_path}")

    # Save fixed test scene
    if fixed_result:
        fixed_path = save_dir / "fixed_manual_sync_test.blend"
        bpy.ops.wm.save_as_mainfile(filepath=str(fixed_path))
        print(f"Fixed test scene saved to: {fixed_path}")

def main():
    """Run the parenting test and save results"""

    print("Blender Parenting Test - Issue Demonstration and Solution")
    print("=" * 60)

    # Test 1: Demonstrate broken parenting
    is_broken = create_broken_hierarchy_test()

    # Test 2: Demonstrate manual sync solution
    is_fixed = create_manual_sync_test()

    # Save test scenes
    save_test_scenes(is_broken, is_fixed)

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY:")
    print(f"Parenting is broken: {'YES' if is_broken else 'NO'}")
    print(f"Manual sync solution works: {'YES' if is_fixed else 'NO'}")

    if is_broken and is_fixed:
        print("\nCONCLUSION: Blender parenting is broken in this environment,")
        print("but manual synchronization provides a working solution.")
        print("This confirms the taxi sign issue in CashCab addon.")
        return 0
    elif not is_broken:
        print("\nCONCLUSION: Blender parenting is working correctly.")
        print("The issue must be elsewhere in the CashCab addon code.")
        return 0
    else:
        print("\nCONCLUSION: Both Blender parenting and manual sync failed.")
        print("There may be a deeper environmental issue.")
        return 1

if __name__ == "__main__":
    result = main()
    sys.exit(result)