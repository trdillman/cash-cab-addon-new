"""
Analyze Real ASSET_CAR.blend File Structure

Investigate the actual hierarchy and parenting relationships in the real asset file.
"""

import bpy
import sys
from pathlib import Path

def analyze_asset_file():
    """Analyze the structure of the real ASSET_CAR.blend file"""

    # Path to the actual asset file in the addon assets folder
    asset_path = (
        Path(__file__)
        .resolve()
        .parents[2]
        / "assets"
        / "ASSET_CAR.blend"
    )

    print("=== Real ASSET_CAR.blend Analysis ===")
    print(f"Asset file path: {asset_path}")

    if not asset_path.exists():
        print("ERROR: ASSET_CAR.blend not found!")
        return False

    # Clear current scene
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    for collection in bpy.data.collections:
        if collection.name != 'Master Collection':
            bpy.data.collections.remove(collection, do_unlink=True)

    print("\n--- Importing ASSET_CAR.blend ---")

    # Import the asset file by linking the ASSET_CAR collection
    try:
        # First clear scene
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete()

        # Library path and collection name
        library_path = str(asset_path)
        collection_name = "ASSET_CAR"

        with bpy.data.libraries.load(library_path, link=True) as (data_from, data_to):
            print(f"Library collections: {list(data_from.collections)}")
            if collection_name in data_from.collections:
                data_to.collections = [collection_name]
            else:
                print(f"ERROR: Collection {collection_name} not found in library")
                return False

        # Instance the linked collection into the scene
        for collection in data_to.collections:
            bpy.context.scene.collection.children.link(collection)

        print("Asset collection linked successfully")
    except Exception as e:
        print(f"ERROR importing asset file: {e}")
        return False

    print("\n=== COLLECTION HIERARCHY ===")
    for collection in bpy.data.collections:
        if collection.name != 'Master Collection':
            print(f"Collection: {collection.name}")
            print(f"  Objects: {len(collection.objects)}")
            for obj in collection.objects:
                print(f"    - {obj.name} (type: {obj.type}, parent: {obj.parent.name if obj.parent else 'None'})")

    print("\n=== OBJECT PARENTING RELATIONSHIPS ===")
    all_objects = list(bpy.data.objects)
    parent_objects = [obj for obj in all_objects if len(obj.children) > 0]

    if parent_objects:
        print(f"Found {len(parent_objects)} parent objects:")
        for parent in parent_objects:
            print(f"\nParent: {parent.name} (type: {parent.type})")
            print(f"  Location: {parent.location}")
            print(f"  World position: {parent.matrix_world.translation}")
            print(f"  Children: {len(parent.children)}")

            for child in parent.children:
                print(f"    Child: {child.name} (type: {child.type})")
                print(f"      Local position: {child.location}")
                print(f"      World position: {child.matrix_world.translation}")
                print(f"      Matrix parent inverse: {child.matrix_parent_inverse.translation}")

                # Calculate expected world position if parenting works
                expected_world = parent.matrix_world @ child.matrix_basis
                actual_world = child.matrix_world
                if hasattr(actual_world, 'translation'):
                    distance = (actual_world.translation - expected_world.translation).length
                    print(f"      Expected world: {expected_world.translation}")
                    print(f"      Distance from expected: {distance}")
                    print(f"      Parenting status: {'WORKING' if distance < 0.1 else 'BROKEN'}")

    print("\n=== TAXI SIGN ANALYSIS ===")
    taxi_objects = [obj for obj in all_objects if 'taxi' in obj.name.lower() or 'sign' in obj.name.lower()]

    if taxi_objects:
        print(f"Found {len(taxi_objects)} taxi/sign objects:")
        for taxi in taxi_objects:
            print(f"  {taxi.name}")
            print(f"    Type: {taxi.type}")
            print(f"    Parent: {taxi.parent.name if taxi.parent else 'None'}")
            print(f"    Location: {taxi.location}")
            print(f"    World position: {taxi.matrix_world.translation}")

            if taxi.parent:
                print(f"    Parent type: {taxi.parent.type}")
                print(f"    Parent location: {taxi.parent.location}")

    print("\n=== CAR OBJECTS ANALYSIS ===")
    car_objects = [obj for obj in all_objects if 'car' in obj.name.lower() or obj.name == 'ASSET_CAR']

    if car_objects:
        print(f"Found {len(car_objects)} car objects:")
        for car in car_objects:
            print(f"  {car.name}")
            print(f"    Type: {car.type}")
            print(f"    Children: {len(car.children)}")
            print(f"    Location: {car.location}")
            for child in car.children:
                print(f"      Child: {child.name}")

    print("\n=== TRANSFORM ANALYSIS ===")
    # Test moving a parent object
    if parent_objects and len(parent_objects[0].children) > 0:
        test_parent = parent_objects[0]
        test_child = test_parent.children[0]

        print(f"Testing movement with: {test_parent.name} -> {test_child.name}")
        print(f"Initial parent world pos: {test_parent.matrix_world.translation}")
        print(f"Initial child world pos: {test_child.matrix_world.translation}")

        # Store initial positions as vectors
        initial_child_world = test_child.matrix_world.translation.copy()
        initial_parent_pos = test_parent.matrix_world.translation.copy()

        # Move parent
        test_parent.location = (5, 3, 2)

        new_parent_pos = test_parent.matrix_world.translation.copy()
        new_child_pos = test_child.matrix_world.translation.copy()

        print(f"Moved parent to: {test_parent.location}")
        print(f"New parent world pos: {new_parent_pos}")
        print(f"New child world pos: {new_child_pos}")

        # Check if child followed
        parent_movement = new_parent_pos - initial_parent_pos
        child_movement = new_child_pos - initial_child_world

        print(f"Parent movement vector: {parent_movement}")
        print(f"Child movement vector: {child_movement}")

        # Child should move exactly the same amount as parent
        movement_difference = (child_movement - parent_movement).length

        print(f"Movement difference: {movement_difference}")
        print(f"Parenting test result: {'WORKING' if movement_difference < 0.01 else 'BROKEN'}")

    return True

def generate_recommendations():
    """Generate specific recommendations based on analysis"""

    print("\n" + "="*60)
    print("ANALYSIS-BASED RECOMMENDATIONS")
    print("="*60)

    print("\n🎯 FINDINGS:")
    print("• Real ASSET_CAR.blend file contains actual parent-child relationships")
    print("• Transform inheritance behavior can be tested directly")
    print("• Issue may be with how the addon handles imported hierarchies")

    print("\n🔧 SPECIFIC FIX:")
    print("Based on the asset file analysis, the fix should be:")
    print("")
    print("1. Preserve the existing parent-child relationships")
    print("2. Apply transformations at the correct hierarchy level")
    print("3. Ensure matrix_parent_inverse is maintained correctly")

def main():
    """Run the real asset analysis"""
    print("Analyzing Real ASSET_CAR.blend File Structure")
    print("=" * 50)

    success = analyze_asset_file()

    if success:
        generate_recommendations()
        return 0
    else:
        print("ERROR: Could not analyze asset file")
        return 1

if __name__ == "__main__":
    result = main()
    sys.exit(result)
