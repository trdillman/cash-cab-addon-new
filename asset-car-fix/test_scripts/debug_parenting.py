"""
Debug Parenting Issue - Deep Investigation

Investigate why parent-child relationships aren't working as expected.
"""

import bpy
import sys
from mathutils import Matrix, Vector

def debug_parenting_relationship():
    """Debug the parent-child relationship in detail"""

    # Clear existing objects
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()

    # Create collection
    car_collection = bpy.data.collections.new("ASSET_CAR")
    bpy.context.scene.collection.children.link(car_collection)

    # Create car body
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 1))
    car_body = bpy.context.active_object
    car_body.name = "CAR_BODY"
    car_collection.objects.link(car_body)

    # Create taxi sign
    bpy.ops.mesh.primitive_plane_add(size=0.5, location=(0, 0, 2.5))
    taxi_sign = bpy.context.active_object
    taxi_sign.name = "TAXI_SIGN"
    car_collection.objects.link(taxi_sign)

    print("=== BEFORE PARENTING ===")
    print(f"Car body location: {car_body.location}")
    print(f"Car body world matrix: {car_body.matrix_world.translation}")
    print(f"Taxi sign location: {car_body.location}")
    print(f"Taxi sign world matrix: {taxi_sign.matrix_world.translation}")

    # Establish parent relationship
    print("\n=== ESTABLISHING PARENTING ===")
    taxi_sign.parent = car_body
    taxi_sign.matrix_parent_inverse = car_body.matrix_world.inverted()

    print(f"Taxi sign parent: {taxi_sign.parent.name if taxi_sign.parent else None}")
    print(f"Taxi sign matrix_parent_inverse: {taxi_sign.matrix_parent_inverse.translation}")
    print(f"Taxi sign world matrix after parenting: {taxi_sign.matrix_world.translation}")

    # Test 1: Move parent without clearing anything
    print("\n=== TEST 1: Move parent (normal case) ===")
    print("Moving car to (5, 3, 1)")
    car_body.location = (5, 3, 1)

    print(f"Car body location: {car_body.location}")
    print(f"Taxi sign parent: {taxi_sign.parent.name if taxi_sign.parent else None}")
    print(f"Taxi sign world matrix: {taxi_sign.matrix_world.translation}")
    print(f"Expected taxi position: (5, 3, 2.5)")

    taxi_pos_after_move = taxi_sign.matrix_world.translation.copy()
    expected_pos = Vector((5, 3, 2.5))
    distance = (taxi_pos_after_move - expected_pos).length
    print(f"Distance from expected: {distance}")
    print(f"Test 1 result: {'WORKING' if distance < 0.1 else 'BROKEN'}")

    # Test 2: Clear parent and move
    print("\n=== TEST 2: Clear parent and move (current broken behavior) ===")
    print("Resetting positions...")
    car_body.location = (0, 0, 1)
    taxi_sign.location = (0, 0, 2.5)  # Reset taxi sign relative position

    print("Clearing parent: car_body.parent = None")
    car_body.parent = None
    car_body.matrix_parent_inverse = Matrix.Identity(4)

    print("Moving car to (10, 5, 1)")
    car_body.location = (10, 5, 1)

    print(f"Car body location: {car_body.location}")
    print(f"Taxi sign parent: {taxi_sign.parent.name if taxi_sign.parent else None}")
    print(f"Taxi sign world matrix: {taxi_sign.matrix_world.translation}")
    print(f"Expected taxi position: (10, 5, 2.5)")

    taxi_pos_after_clear = taxi_sign.matrix_world.translation.copy()
    distance2 = (taxi_pos_after_clear - Vector((10, 5, 2.5))).length
    print(f"Distance from expected: {distance2}")
    print(f"Test 2 result: {'BROKEN' if distance2 > 1.0 else 'WORKING'}")

    # Test 3: Re-establish parenting and test again
    print("\n=== TEST 3: Re-establish parenting and test ===")
    print("Resetting positions...")
    car_body.location = (0, 0, 1)
    taxi_sign.location = (0, 0, 2.5)

    print("Re-establishing parenting...")
    taxi_sign.parent = car_body
    taxi_sign.matrix_parent_inverse = car_body.matrix_world.inverted()

    print("Moving car to (7, 4, 2)")
    car_body.location = (7, 4, 2)

    print(f"Car body location: {car_body.location}")
    print(f"Taxi sign parent: {taxi_sign.parent.name if taxi_sign.parent else None}")
    print(f"Taxi sign world matrix: {taxi_sign.matrix_world.translation}")
    print(f"Expected taxi position: (7, 4, 3.5)")

    taxi_pos_after_reparent = taxi_sign.matrix_world.translation.copy()
    distance3 = (taxi_pos_after_reparent - Vector((7, 4, 3.5))).length
    print(f"Distance from expected: {distance3}")
    print(f"Test 3 result: {'WORKING' if distance3 < 0.1 else 'BROKEN'}")

    return {
        'test1_working': distance < 0.1,
        'test2_broken': distance2 > 1.0,
        'test3_working': distance3 < 0.1,
        'parenting_works_normally': distance < 0.1 and distance3 < 0.1
    }

def investigate_collection_impact():
    """Test if collections affect parenting"""
    print("\n=== INVESTIGATING COLLECTION IMPACT ===")

    # Create objects outside of collection first
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()

    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 1))
    car_body = bpy.context.active_object
    car_body.name = "CAR_BODY"

    bpy.ops.mesh.primitive_plane_add(size=0.5, location=(0, 0, 2.5))
    taxi_sign = bpy.context.active_object
    taxi_sign.name = "TAXI_SIGN"

    # Parent without collection
    taxi_sign.parent = car_body
    taxi_sign.matrix_parent_inverse = car_body.matrix_world.inverted()

    print("Parenting established without collection")
    print(f"Moving car to (3, 2, 1)")
    car_body.location = (3, 2, 1)

    taxi_pos = taxi_sign.matrix_world.translation
    expected = Vector((3, 2, 2.5))
    distance = (taxi_pos - expected).length

    print(f"Taxi position: {taxi_pos}")
    print(f"Expected: {expected}")
    print(f"Distance: {distance}")
    print(f"Result: {'WORKING' if distance < 0.1 else 'BROKEN'}")

    return distance < 0.1

def main():
    """Run debugging tests"""
    print("Parenting Issue Debug Investigation")
    print("=" * 50)

    # Debug standard parenting
    results = debug_parenting_relationship()

    # Test collection impact
    collection_works = investigate_collection_impact()

    print("\n" + "=" * 50)
    print("DEBUG SUMMARY:")
    print(f"Standard parenting works: {results['parenting_works_normally']}")
    print(f"Parenting without collection works: {collection_works}")

    if not results['parenting_works_normally']:
        print("\nPROBLEM IDENTIFIED:")
        print("Parent-child relationships aren't working correctly in Blender")
        print("This suggests a deeper issue with the parenting setup")
        return 1
    elif not collection_works:
        print("\nCOLLECTION ISSUE:")
        print("Collections might be interfering with parenting")
        return 1
    else:
        print("\nPARENTING WORKS NORMALLY:")
        print("The issue must be elsewhere in the workflow")
        return 0

if __name__ == "__main__":
    result = main()
    sys.exit(result)