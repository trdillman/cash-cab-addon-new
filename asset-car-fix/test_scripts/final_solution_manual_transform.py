"""
Final Solution - Manual Transform Updates for Car Import Parenting Issue

Since both parenting and constraints are broken in this environment,
use direct manual transform updates to synchronize child objects.

This is the most robust approach that should work regardless of
environmental interference with Blender's core systems.
"""

import bpy
from mathutils import Vector, Matrix
from typing import Dict, List, Optional

def sync_child_objects_manual_transform(parent_obj: bpy.types.Object, collection_name: str = "ASSET_CAR") -> Dict[str, Vector]:
    """
    Manually synchronize child objects with parent by direct transform updates.

    This completely bypasses Blender's parenting and constraint systems
    which are both broken in the CashCab addon environment.

    Args:
        parent_obj: The main parent object (car body)
        collection_name: Name of the collection containing child objects

    Returns:
        Dictionary mapping child object names to their relative positions
    """
    if not parent_obj:
        return {}

    # Get the asset collection
    collection = bpy.data.collections.get(collection_name)
    if not collection:
        return {}

    # Store initial child positions and relationships
    child_data = {}

    for obj in collection.objects:
        if obj != parent_obj and (obj.parent == parent_obj or
                                 obj.name.lower().find('taxi') != -1 or
                                 obj.name.lower().find('sign') != -1):
            # Store the initial relative position from parent
            relative_location = obj.location.copy()

            child_data[obj.name] = {
                'object': obj,
                'relative_location': relative_location,
                'was_parented': obj.parent == parent_obj
            }

    return child_data

def update_child_positions(parent_obj: bpy.types.Object, child_data: Dict[str, Dict]) -> None:
    """
    Update child object positions based on parent movement.

    Call this function whenever the parent object moves.
    """
    if not parent_obj or not child_data:
        return

    parent_matrix = parent_obj.matrix_world

    for child_name, data in child_data.items():
        child_obj = data['object']
        relative_loc = data['relative_location']

        # Calculate world position for child object
        # This simulates proper parent-child transform inheritance
        child_world_matrix = parent_matrix @ Matrix.Translation(relative_loc)

        # Update child object's world position directly
        child_obj.matrix_world = child_world_matrix

        print(f"Updated {child_name} position to follow parent")

# INTEGRATION CODE - Add this to the relevant files

class ChildObjectManager:
    """Manages child object synchronization for car assets"""

    def __init__(self):
        self.child_data = {}

    def initialize_children(self, parent_obj: bpy.types.Object, collection_name: str = "ASSET_CAR"):
        """Initialize child object relationships"""
        self.child_data = sync_child_objects_manual_transform(parent_obj, collection_name)
        print(f"Initialized {len(self.child_data)} child objects for tracking")

    def update_children(self, parent_obj: bpy.types.Object):
        """Update all child positions to follow parent"""
        update_child_positions(parent_obj, self.child_data)

# Global instance for use across the addon
_child_manager = ChildObjectManager()

def integration_car_positioning(car_obj: bpy.types.Object, target_location: Vector):
    """
    Integration function to replace existing car positioning code.

    Use this instead of the current car positioning code in route/anim.py and route/fetch_operator.py
    """
    # Position the car object
    car_obj.location = target_location

    # Update child objects to follow
    _child_manager.update_children(car_obj)

def integration_car_import(car_collection, car_obj):
    """
    Integration function for car import in route/assets.py.
    Call this after the car is imported and positioned.
    """
    # Initialize child object tracking
    _child_manager.initialize_children(car_obj, "ASSET_CAR")

    # Apply initial positioning
    _child_manager.update_children(car_obj)

# TESTING FUNCTION
def test_manual_transform_solution():
    """Test the manual transform approach"""
    print("Testing manual transform child object synchronization...")

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

    # Establish initial parenting relationship (for data purposes)
    taxi_sign.parent = car_body
    taxi_sign.location = Vector((0, 0, 1.5))  # Relative to car

    # Initialize child tracking
    child_data = sync_child_objects_manual_transform(car_body, "TEST_ASSET_CAR")
    print(f"Tracking {len(child_data)} child objects")

    # Test movement
    print(f"Initial car position: {car_body.location}")
    print(f"Initial taxi world position: {taxi_sign.matrix_world.translation}")

    # Move parent to test position
    car_body.location = Vector((5, 3, 2))

    # Update child positions manually
    update_child_positions(car_body, child_data)

    print(f"Moved car to: {car_body.location}")
    print(f"Updated taxi world position: {taxi_sign.matrix_world.translation}")
    print(f"Expected taxi position: {Vector((5, 3, 3.5))}")

    # Check results
    final_taxi_pos = taxi_sign.matrix_world.translation
    expected_pos = Vector((5, 3, 3.5))
    distance = (final_taxi_pos - expected_pos).length
    success = distance < 0.1

    print(f"Distance from expected: {distance:.6f}")
    print(f"Test result: {'PASS' if success else 'FAIL'}")

    return success

if __name__ == "__main__":
    # Run the test
    success = test_manual_transform_solution()

    if success:
        print("\n✅ MANUAL TRANSFORM SOLUTION WORKS!")
        print("This approach bypasses broken Blender systems entirely.")
        print("Ready for implementation in CashCab addon.")
    else:
        print("\n❌ Manual transform solution failed.")
        print("Environmental interference is more severe than expected.")

    print(f"\nFinal result: {success}")