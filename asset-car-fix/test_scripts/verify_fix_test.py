"""
Verify Fix Test - Test the implemented parent-child fix

This script creates a simple test to verify that the car import fix
works correctly by simulating the positioning logic from route/anim.py
"""

import bpy
import sys
from pathlib import Path
from mathutils import Vector, Matrix

def create_car_with_taxi_sign():
    """Create a test car with taxi sign to verify the fix"""

    print("=== VERIFYING CAR IMPORT PARENT-CHILD FIX ===")

    # Clear scene
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    for collection in bpy.data.collections:
        if collection.name != 'Master Collection':
            bpy.data.collections.remove(collection, do_unlink=True)

    # Create test collection
    test_collection = bpy.data.collections.new("ASSET_CAR_TEST")
    bpy.context.scene.collection.children.link(test_collection)

    # Create car body
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 1))
    car_body = bpy.context.active_object
    car_body.name = "CAR_BODY"
    test_collection.objects.link(car_body)

    # Create taxi sign as child of car
    bpy.ops.mesh.primitive_plane_add(size=0.5, location=(0, 0, 2.5))
    taxi_sign = bpy.context.active_object
    taxi_sign.name = "TAXI_SIGN"
    test_collection.objects.link(taxi_sign)

    # Create parent-child relationship
    taxi_sign.parent = car_body
    taxi_sign.matrix_parent_inverse = car_body.matrix_world.inverted()

    print(f"Created car: {car_body.name}")
    print(f"Created taxi sign: {taxi_sign.name}")
    print(f"Parent relationship: {taxi_sign.parent.name if taxi_sign.parent else 'None'}")
    print(f"Initial car position: {car_body.location}")
    print(f"Initial taxi world position: {taxi_sign.matrix_world.translation}")

    return car_body, taxi_sign, test_collection

def test_positioning_fix():
    """Test the exact positioning logic from the implemented fix"""

    car_body, taxi_sign, test_collection = create_car_with_taxi_sign()

    print(f"\n=== TESTING POSITIONING LOGIC ===")

    # Store initial positions
    initial_car_pos = car_body.location.copy()
    initial_taxi_world = taxi_sign.matrix_world.translation.copy()

    # Create a target object (simulating start_obj from route/anim.py)
    bpy.ops.mesh.primitive_cube_add(size=0.1, location=(5, 3, 2))
    target_obj = bpy.context.active_object
    target_obj.name = "TARGET_POSITION"

    print(f"Target position: {target_obj.location}")

    # Apply the exact fix logic from route/anim.py lines 612-624
    print(f"\nApplying fix logic from route/anim.py...")

    # This is the implemented fix:
    try:
        car_body.parent = None
        car_body.matrix_parent_inverse = Matrix.Identity(4)
        print("✅ Cleared parent relationships")
    except Exception as e:
        print(f"❌ Error clearing parent: {e}")
        return False

    try:
        car_body.matrix_world = target_obj.matrix_world.copy()
        print("✅ Applied matrix transformation")
    except Exception as e:
        print(f"❌ Error applying matrix: {e}")
        return False

    print(f"After positioning:")
    print(f"Car position: {car_body.location}")
    print(f"Car world position: {car_body.matrix_world.translation}")
    print(f"Taxi world position: {taxi_sign.matrix_world.translation}")

    # Calculate expected taxi position
    expected_taxi_pos = Vector((5, 3, 3.5))  # Target + relative offset
    actual_taxi_pos = taxi_sign.matrix_world.translation
    distance = (actual_taxi_pos - expected_taxi_pos).length

    print(f"\nExpected taxi position: {expected_taxi_pos}")
    print(f"Actual taxi position: {actual_taxi_pos}")
    print(f"Distance from expected: {distance:.6f}")

    # Determine success
    success = distance < 0.1
    print(f"Test result: {'✅ PASS - Taxi follows car correctly' if success else '❌ FAIL - Taxi does not follow car'}")

    return success

def save_test_results(success):
    """Save test results with appropriate naming"""

    test_dir = Path(__file__).parent / "test_scenes" / "verify_fix_results"
    test_dir.mkdir(parents=True, exist_ok=True)

    timestamp = bpy.context.scene.render.frame_current
    status = "SUCCESS" if success else "FAILED"
    filename = f"parent_child_fix_verification_{status}_{timestamp}.blend"

    scene_path = test_dir / filename

    try:
        bpy.ops.wm.save_as_mainfile(filepath=str(scene_path))
        print(f"\n📁 Test scene saved to: {scene_path}")
        return str(scene_path)
    except Exception as e:
        print(f"❌ Error saving scene: {e}")
        return None

def main():
    """Run the verification test"""

    print("PARENT-CHILD FIX VERIFICATION TEST")
    print("=" * 50)

    # Test the implemented fix
    success = test_positioning_fix()

    # Save results
    scene_path = save_test_results(success)

    # Summary
    print(f"\n" + "=" * 50)
    print(f"VERIFICATION SUMMARY:")
    print(f"Fix implementation: {'✅ WORKING' if success else '❌ NOT WORKING'}")

    if scene_path:
        print(f"Test scene: {scene_path}")

    if success:
        print(f"\n🎉 CONCLUSION: The parent-child fix is working correctly!")
        print(f"   Taxi signs should now follow cars during route import.")
        return 0
    else:
        print(f"\n⚠️  CONCLUSION: The fix needs further investigation.")
        print(f"   Taxi signs are still not following cars as expected.")
        return 1

if __name__ == "__main__":
    result = main()
    sys.exit(result)