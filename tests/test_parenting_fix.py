"""
Test and Fix Blender Parent-Child Relationships

This script tests the actual Blender parenting behavior and fixes the regression.
"""

import bpy
from mathutils import Matrix, Vector

def test_blender_parenting():
    """Test how Blender parenting actually works"""
    print("=== Testing Blender Parent-Child Inheritance ===")

    # Create a simple parent-child test
    parent = bpy.data.objects.new("TestParent", None)
    parent.empty_display_type = 'PLAIN_AXES'
    parent.empty_display_size = 1.0
    bpy.context.scene.collection.objects.link(parent)

    child = bpy.data.objects.new("TestChild", None)
    child.empty_display_type = 'SPHERE'
    child.empty_display_size = 0.5
    bpy.context.scene.collection.objects.link(child)

    # Set initial positions
    parent.location = (5, 5, 0)
    child.location = (1, 0, 0)  # 1 unit relative to parent

    # Parent the child
    child.parent = parent
    child.matrix_parent_inverse = Matrix.Identity(4)

    print(f"Before parent move:")
    print(f"  Parent location: {parent.location}")
    print(f"  Child local location: {child.location}")
    print(f"  Child world location: {child.matrix_world.translation}")

    # Move parent
    parent.location = (10, 10, 0)

    print(f"After parent move:")
    print(f"  Parent location: {parent.location}")
    print(f"  Child local location: {child.location}")
    print(f"  Child world location: {child.matrix_world.translation}")

    # Check if child followed parent (world position should change by same amount)
    expected_child_world = Vector((10 + 1, 10 + 0, 0))
    actual_child_world = Vector(child.matrix_world.translation)
    distance = (actual_child_world - expected_child_world).length

    print(f"Expected child world: {expected_child_world}")
    print(f"Actual child world: {actual_child_world}")
    print(f"Distance from expected: {distance}")

    # Clean up
    bpy.data.objects.remove(parent, do_unlink=True)
    bpy.data.objects.remove(child, do_unlink=True)

    return distance < 0.001

def check_current_asset_structure():
    """Check the current ASSET_CAR structure"""
    print("\n=== Checking Current ASSET_CAR Structure ===")

    car_collection = bpy.data.collections.get("ASSET_CAR")
    if not car_collection:
        print("No ASSET_CAR collection found")
        return

    print(f"ASSET_CAR collection has {len(car_collection.all_objects)} objects")

    # Find parent objects
    parent_objects = []
    child_objects = []

    for obj in car_collection.all_objects:
        if obj.parent is None:
            parent_objects.append(obj)
        else:
            child_objects.append(obj)

    print(f"\nParent objects ({len(parent_objects)}):")
    for parent in parent_objects:
        print(f"  - {parent.name} (type: {parent.type})")

    print(f"\nChild objects ({len(child_objects)}):")
    for child in child_objects:
        print(f"  - {child.name} (type: {child.type})")
        print(f"    Parent: {child.parent.name if child.parent else 'None'}")
        print(f"    Local location: {child.location}")
        print(f"    World location: {child.matrix_world.translation}")

def fix_parenting_regression():
    """Fix the parenting regression"""
    print("\n=== Fixing Parenting Regression ===")

    car_collection = bpy.data.collections.get("ASSET_CAR")
    if not car_collection:
        print("No ASSET_CAR collection found")
        return

    # Find the main car body (should be the parent)
    car_body = None
    for obj in car_collection.objects:
        if obj.type == 'MESH' and ('body' in obj.name.lower() or 'car' in obj.name.lower() or 'chassis' in obj.name.lower()):
            car_body = obj
            break

    if not car_body:
        print("No car body found, trying first mesh object")
        for obj in car_collection.objects:
            if obj.type == 'MESH':
                car_body = obj
                break

    if not car_body:
        print("No mesh objects found in ASSET_CAR collection")
        return

    print(f"Using car body as parent: {car_body.name}")

    # Parent all loose objects to the car body
    fixed_count = 0
    for obj in car_collection.objects:
        if obj != car_body and obj.parent is None:
            print(f"Parenting {obj.name} to {car_body.name}")

            # Store current world position
            world_matrix = obj.matrix_world.copy()

            # Parent to car body
            obj.parent = car_body

            # Keep world position the same
            obj.matrix_world = world_matrix

            fixed_count += 1

    print(f"Fixed parenting for {fixed_count} objects")

def main():
    """Main execution"""
    print("Blender Parent-Child Relationship Fix")
    print("=" * 50)

    # Test Blender parenting behavior
    parenting_works = test_blender_parenting()
    print(f"\nBlender parenting works correctly: {parenting_works}")

    # Check current asset structure
    check_current_asset_structure()

    # Fix the regression
    if bpy.data.collections.get("ASSET_CAR"):
        fix_parenting_regression()
        print("\n=== After Fix ===")
        check_current_asset_structure()
    else:
        print("\nNo ASSET_CAR collection found to fix")

if __name__ == "__main__":
    main()