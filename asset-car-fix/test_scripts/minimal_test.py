"""
Minimal Parenting Test - Without Addon

Test basic Blender parenting without any CashCab interference.
"""

import bpy
import sys
from mathutils import Vector

def test_basic_parenting():
    """Test parenting with minimal setup"""

    # Clear scene completely
    for obj in bpy.data.objects:
        bpy.data.objects.remove(obj, do_unlink=True)
    for coll in bpy.data.collections:
        if coll.name != 'Master Collection':
            bpy.data.collections.remove(coll, do_unlink=True)

    print("=== Minimal Parenting Test (Clean Environment) ===")

    # Create two objects
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0))
    parent_obj = bpy.context.active_object
    parent_obj.name = "PARENT"

    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.3, location=(1, 0, 0.5))
    child_obj = bpy.context.active_object
    child_obj.name = "CHILD"

    print(f"Parent location: {parent_obj.location}")
    print(f"Child location: {child_obj.location}")
    print(f"Child world position: {child_obj.matrix_world.translation}")

    # Establish parenting
    print("\nEstablishing parenting...")
    child_obj.parent = parent_obj
    child_obj.matrix_parent_inverse = parent_obj.matrix_world.inverted()

    print(f"Child parent: {child_obj.parent.name if child_obj.parent else None}")
    print(f"Child world position after parenting: {child_obj.matrix_world.translation}")

    # Test movement
    print("\nMoving parent to (3, 2, 1)...")
    parent_obj.location = (3, 2, 1)

    print(f"Parent location: {parent_obj.location}")
    print(f"Child world position: {child_obj.matrix_world.translation}")
    print(f"Expected child position: (3, 2, 1.5)")

    child_pos = child_obj.matrix_world.translation
    expected_pos = Vector((3, 2, 1.5))
    distance = (child_pos - expected_pos).length

    print(f"Distance from expected: {distance}")
    result = distance < 0.1
    print(f"Result: {'WORKING' if result else 'BROKEN'}")

    return result

def test_local_vs_world_coordinates():
    """Test if the issue is with local vs world coordinate handling"""

    print("\n=== Testing Local vs World Coordinates ===")

    # Clear scene
    for obj in bpy.data.objects:
        bpy.data.objects.remove(obj, do_unlink=True)

    # Create parent and child
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0))
    parent = bpy.context.active_object
    parent.name = "PARENT"

    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.2, location=(0, 0, 2))
    child = bpy.context.active_object
    child.name = "CHILD"

    print(f"Initial child local: {child.location}")
    print(f"Initial child world: {child.matrix_world.translation}")

    # Set up parenting with local offset
    child.location = (0, 0, 1)  # Local: 1 unit above parent
    child.parent = parent
    child.matrix_parent_inverse = parent.matrix_world.inverted()

    print(f"After parenting - child local: {child.location}")
    print(f"After parenting - child world: {child.matrix_world.translation}")

    # Move parent
    parent.location = (5, 3, 0)
    print(f"Parent moved to: {parent.location}")
    print(f"Child world after parent move: {child.matrix_world.translation}")

    # Check if child is at correct world position
    expected_world = Vector((5, 3, 1))  # Parent position + local offset
    child_world = child.matrix_world.translation
    distance = (child_world - expected_world).length

    print(f"Expected child world: {expected_world}")
    print(f"Actual child world: {child_world}")
    print(f"Distance: {distance}")
    result = distance < 0.1
    print(f"Local coordinate test: {'WORKING' if result else 'BROKEN'}")

    return result

def main():
    """Run minimal parenting tests"""
    print("Minimal Blender Parenting Test")
    print("=" * 40)

    # Test 1: Basic parenting
    basic_works = test_basic_parenting()

    # Test 2: Local coordinates
    local_works = test_local_vs_world_coordinates()

    print("\n" + "=" * 40)
    print("MINIMAL TEST RESULTS:")
    print(f"Basic parenting: {'WORKS' if basic_works else 'BROKEN'}")
    print(f"Local coordinates: {'WORKS' if local_works else 'BROKEN'}")

    if basic_works and local_works:
        print("\nCONCLUSION: Blender parenting works correctly")
        print("The issue must be in the CashCab addon code")
        return 0
    else:
        print("\nCONCLUSION: Blender parenting has issues")
        print("This could be a Blender version or environment issue")
        return 1

if __name__ == "__main__":
    result = main()
    sys.exit(result)