"""
Implementation-Ready Solution for Car Import Parenting Issue

ISSUE: Blender parent-child transform inheritance is broken in CashCab addon environment
SOLUTION: Constraint-based child object synchronization that bypasses broken parenting

INSTRUCTIONS:
1. Add this function to route/assets.py
2. Replace parent-clearing code in route/anim.py:617 and route/fetch_operator.py:1072
3. Test with real route import
"""

import bpy
from mathutils import Vector, Matrix
from typing import Dict, List, Optional

def sync_child_objects_with_parent(parent_obj: bpy.types.Object, collection_name: str = "ASSET_CAR") -> None:
    """
    Synchronize child objects with parent using constraints instead of parenting.

    This bypasses the broken parent-child transform inheritance in the CashCab
    addon environment by using Copy Transform constraints for child following.

    Args:
        parent_obj: The main parent object (car body)
        collection_name: Name of the collection containing child objects
    """
    if not parent_obj:
        return

    # Get the asset collection
    collection = bpy.data.collections.get(collection_name)
    if not collection:
        return

    # Store initial child positions and relationships
    child_data = {}

    for obj in collection.objects:
        if obj != parent_obj and (obj.parent == parent_obj or obj.name.lower().find('taxi') != -1 or obj.name.lower().find('sign') != -1):
            # Store the initial relative position
            if hasattr(obj, 'location'):
                relative_location = obj.location.copy()
            else:
                relative_location = Vector((0, 0, 0))

            child_data[obj.name] = {
                'object': obj,
                'relative_location': relative_location,
                'was_parented': obj.parent == parent_obj
            }

    # Apply constraint-based following to each child
    for child_name, data in child_data.items():
        child_obj = data['object']
        relative_loc = data['relative_location']

        # Remove existing parenting relationship (it's broken anyway)
        if child_obj.parent:
            child_obj.parent = None
            child_obj.matrix_parent_inverse = Matrix.Identity(4)

        # Clear existing constraints on child object
        child_obj.constraints.clear()

        # Add Copy Transform constraint to follow parent
        constraint = child_obj.constraints.new(type='COPY_TRANSFORMS')
        constraint.name = "Follow_Parent_Constraint"
        constraint.target = parent_obj
        constraint.use_location = True
        constraint.use_rotation = False
        constraint.use_scale = False

        # Apply relative offset using an empty intermediate object
        # Create empty for offset if it doesn't exist
        offset_empty_name = f"{child_name}_OFFSET_EMPTY"
        offset_empty = bpy.data.objects.get(offset_empty_name)

        if not offset_empty:
            bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, 0))
            offset_empty = bpy.context.active_object
            offset_empty.name = offset_empty_name
            offset_empty.hide_viewport = True  # Hide in viewport

        # Position offset empty relative to parent
        offset_empty.parent = parent_obj
        offset_empty.matrix_parent_inverse = parent_obj.matrix_world.inverted()
        offset_empty.location = relative_loc

        # Update constraint to use offset empty as target
        constraint.target = offset_empty

        print(f"Configured constraint-based following for {child_name}")

# INTEGRATION POINTS - Replace existing code with these calls

def integration_point_1_route_anim():
    """
    Integration for route/anim.py around line 617
    Replace the parent-clearing code with this:
    """
    # REMOVE THESE LINES:
    # car_obj.parent = None
    # car_obj.matrix_parent_inverse = Matrix.Identity(4)

    # REPLACE WITH:
    car_obj.location = target_location  # Keep existing positioning
    sync_child_objects_with_parent(car_obj, "ASSET_CAR")

def integration_point_2_fetch_operator():
    """
    Integration for route/fetch_operator.py around line 1072
    Replace the parent-clearing code with this:
    """
    # REMOVE THESE LINES:
    # car_obj.parent = None
    # car_obj.matrix_parent_inverse = Matrix.Identity(4)

    # REPLACE WITH:
    car_obj.location = target_location  # Keep existing positioning
    sync_child_objects_with_parent(car_obj, "ASSET_CAR")

def integration_point_3_assets_py():
    """
    Integration for route/assets.py after CAR_TRAIL configuration (around line 254)
    Add this after _configure_car_trail_modifier call:
    """
    # ADD after existing CAR_TRAIL configuration:
    sync_child_objects_with_parent(car_obj, "ASSET_CAR")

# TESTING FUNCTION
def test_constraint_solution():
    """
    Test the constraint-based solution in a clean environment
    """
    print("Testing constraint-based child object synchronization...")

    # Clear scene
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()

    # Create test collection
    test_collection = bpy.data.collections.new("TEST_ASSET_CAR")
    bpy.context.scene.collection.children.link(test_collection)

    # Create car body
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 1))
    car_body = bpy.context.active_object
    car_body.name = "TEST_CAR_BODY"
    test_collection.objects.link(car_body)

    # Create taxi sign
    bpy.ops.mesh.primitive_plane_add(size=0.5, location=(0, 0, 2.5))
    taxi_sign = bpy.context.active_object
    taxi_sign.name = "TEST_TAXI_SIGN"
    test_collection.objects.link(taxi_sign)

    # Apply constraint-based solution
    sync_child_objects_with_parent(car_body, "TEST_ASSET_CAR")

    # Test movement
    initial_taxi_pos = taxi_sign.matrix_world.translation.copy()
    print(f"Initial taxi position: {initial_taxi_pos}")

    # Move parent
    car_body.location = (5, 3, 2)
    bpy.context.view_layer.update()

    final_taxi_pos = taxi_sign.matrix_world.translation.copy()
    print(f"Final taxi position: {final_taxi_pos}")
    print(f"Expected position: {Vector((5, 3, 3.5))}")

    distance = (final_taxi_pos - Vector((5, 3, 3.5))).length
    success = distance < 0.1

    print(f"Distance from expected: {distance:.6f}")
    print(f"Test result: {'PASS' if success else 'FAIL'}")

    return success

if __name__ == "__main__":
    # Run the test
    success = test_constraint_solution()
    if success:
        print("✅ Constraint-based solution works!")
        print("Ready for implementation in CashCab addon.")
    else:
        print("❌ Constraint-based solution failed.")
        print("Further investigation required.")