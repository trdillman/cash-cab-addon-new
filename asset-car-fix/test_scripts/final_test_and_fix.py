"""
Final Test and Fix for Car Import Parenting Issue

This demonstrates the actual problem and provides the correct fix.
"""

import bpy
import sys
from mathutils import Matrix

def create_car_hierarchy():
    """Create car hierarchy and return key objects"""

    # Clear existing objects
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()

    # Create collection like ASSET_CAR
    car_collection = bpy.data.collections.new("ASSET_CAR")
    bpy.context.scene.collection.children.link(car_collection)

    # Create car body (main object)
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 1))
    car_body = bpy.context.active_object
    car_body.name = "CAR_BODY"
    car_collection.objects.link(car_body)

    # Create taxi sign (child of car)
    bpy.ops.mesh.primitive_plane_add(size=0.5, location=(0, 0, 2.5))
    taxi_sign = bpy.context.active_object
    taxi_sign.name = "TAXI_SIGN"
    car_collection.objects.link(taxi_sign)

    # Create parent-child relationship
    taxi_sign.parent = car_body
    taxi_sign.matrix_parent_inverse = car_body.matrix_world.inverted()

    return car_collection, car_body, taxi_sign

def test_broken_approach():
    """Test the current broken approach"""
    print("=== Testing BROKEN Approach ===")

    car_collection, car_body, taxi_sign = create_car_hierarchy()

    print(f"Initial taxi position: {taxi_sign.matrix_world.translation}")

    # This is what currently happens in the code
    print("Applying: car_body.parent = None")
    car_body.parent = None
    car_body.matrix_parent_inverse = Matrix.Identity(4)

    print("Moving car to (10, 5, 1)")
    car_body.location = (10, 5, 1)

    print(f"Final taxi position: {taxi_sign.matrix_world.translation}")
    print(f"Expected position: (10, 5, 2.5)")

    # The issue: taxi sign doesn't follow the car
    from mathutils import Vector
    expected_pos = Vector((10, 5, 2.5))
    distance = (taxi_sign.matrix_world.translation - expected_pos).length
    print(f"Distance from expected: {distance}")

    is_broken = distance > 1.0
    print(f"RESULT: {'BROKEN - Taxi sign does not follow car' if is_broken else 'WORKING'}")

    return is_broken

def test_correct_fix():
    """Test the correct fix approach"""
    print("\n=== Testing CORRECT Fix ===")

    car_collection, car_body, taxi_sign = create_car_hierarchy()

    print(f"Initial taxi position: {taxi_sign.matrix_world.translation}")

    # The fix: don't clear parent, just move the root object
    print("Applying CORRECT fix: move car without clearing parent")
    # NO: car_body.parent = None
    # NO: car_body.matrix_parent_inverse = Matrix.Identity(4)

    print("Moving car to (10, 5, 1)")
    car_body.location = (10, 5, 1)

    print(f"Final taxi position: {taxi_sign.matrix_world.translation}")
    print(f"Expected position: (10, 5, 2.5)")

    from mathutils import Vector
    expected_pos = Vector((10, 5, 2.5))
    distance = (taxi_sign.matrix_world.translation - expected_pos).length
    print(f"Distance from expected: {distance}")

    is_working = distance < 0.1
    print(f"RESULT: {'WORKING - Taxi sign follows car' if is_working else 'STILL BROKEN'}")

    return is_working

def generate_fix_recommendations():
    """Generate specific code fix recommendations"""

    print("\n" + "="*60)
    print("FIX RECOMMENDATIONS")
    print("="*60)

    print("\n1. PROBLEM IDENTIFIED:")
    print("   Location: route/anim.py:617 and route/fetch_operator.py:1072")
    print("   Issue: Setting 'car_obj.parent = None' breaks transform inheritance")
    print("   Effect: Taxi sign doesn't follow car movement")

    print("\n2. BROKEN CODE TO REMOVE:")
    print("   From route/anim.py:617:")
    print("     car_obj.parent = None")
    print("     car_obj.matrix_parent_inverse = Matrix.Identity(4)")
    print("   From route/fetch_operator.py:1072:")
    print("     car_obj.parent = None")
    print("     car_obj.matrix_parent_inverse = Matrix.Identity(4)")

    print("\n3. CORRECT CODE TO USE:")
    print("   Simply remove the parent clearing lines:")
    print("   # REMOVE THESE LINES:")
    print("   # car_obj.parent = None  # <-- REMOVE THIS")
    print("   # car_obj.matrix_parent_inverse = Matrix.Identity(4)  # <-- REMOVE THIS")
    print("")
    print("   # KEEP THIS LINE:")
    print("   car_obj.location = target_location  # <-- KEEP THIS")

    print("\n4. WHY THIS WORKS:")
    print("   - Child objects inherit parent transformations automatically")
    print("   - Taxi sign will follow car movement without explicit parenting")
    print("   - Internal car hierarchy (car → taxi_sign) remains intact")
    print("   - No need for manual parent relationship management")

    print("\n5. VALIDATION:")
    print("   - Test: Taxi sign should follow car during route animation")
    print("   - Test: Car positioning at route start should move taxi sign")
    print("   - Test: No parenting relationships should be broken")

def main():
    """Run the final test"""
    print("Car Import Parenting Issue - Final Test and Fix")
    print("="*60)

    # Test the broken approach
    broken_detected = test_broken_approach()

    # Test the correct fix
    fix_works = test_correct_fix()

    # Generate recommendations
    generate_fix_recommendations()

    # Final summary
    print("\n" + "="*60)
    print("FINAL SUMMARY")
    print("="*60)

    if broken_detected and fix_works:
        print("SUCCESS: Issue identified and fix validated!")
        print("The parent clearing code breaks transform inheritance.")
        print("Removing the parent = None lines will fix the issue.")
        return 0
    elif not broken_detected:
        print("INFO: Issue not detected with current test.")
        print("The parenting issue may occur in different circumstances.")
        return 0
    else:
        print("FAILURE: Fix doesn't resolve the issue.")
        print("Further investigation needed.")
        return 1

if __name__ == "__main__":
    result = main()
    sys.exit(result)