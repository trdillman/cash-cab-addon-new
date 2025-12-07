"""
Blender script to test the CashCab parent-child relationship fix.

Run this script in Blender's Script Editor after loading the addon.
It will test the complete pipeline with a real route fetch.
"""

import bpy
import os
from datetime import datetime

def clear_scene():
    """Clear the Blender scene"""
    print("\nClearing scene...")
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    print("Scene cleared")

def test_parent_child_fix():
    """Test the parent-child relationship fix"""
    print("\n" + "="*60)
    print("TESTING CASHCAB PARENT-CHILD FIX")
    print("="*60)

    # Clear scene
    clear_scene()

    try:
        # Step 1: Import a test route
        print("\nStep 1: Importing test route...")

        # Set test route (Times Square to Central Park)
        if hasattr(bpy.context.scene, 'blosm'):
            bpy.context.scene.blosm.start = "Times Square, New York, NY"
            bpy.context.scene.blosm.end = "Central Park, New York, NY"

            # Fetch route
            bpy.ops.blosm.fetch_route()
            print("✅ Route fetching initiated")
        else:
            print("⚠️  BLOSM addon not fully loaded, attempting manual test...")

        # Step 2: Import assets
        print("\nStep 2: Importing assets...")
        bpy.ops.blosm.import_assets()
        print("✅ Asset import initiated")

        # Step 3: Check results
        bpy.context.view_layer.update()

        # Find car and taxi objects
        car_collection = bpy.data.collections.get('ASSET_CAR')
        if not car_collection:
            print("❌ ERROR: ASSET_CAR collection not found")
            return False

        car_obj = None
        taxi_objects = []

        for obj in car_collection.objects:
            if 'car' in obj.name.lower() or 'body' in obj.name.lower():
                car_obj = obj
            elif 'taxi' in obj.name.lower() or 'sign' in obj.name.lower():
                taxi_objects.append(obj)

        if not car_obj:
            print("❌ ERROR: No car object found")
            return False

        print(f"✅ Found car object: {car_obj.name}")
        print(f"✅ Found {len(taxi_objects)} taxi sign objects")

        # Step 4: Test parent-child relationships
        print("\nStep 4: Testing parent-child relationships...")

        success_count = 0
        total_tests = 3  # Test 3 different positions

        for i in range(total_tests):
            # Store initial positions
            initial_car_pos = car_obj.matrix_world.translation.copy()
            initial_taxi_positions = [taxi.matrix_world.translation.copy() for taxi in taxi_objects]

            # Move car to test position
            test_location = (i * 5, i * 3, i * 2)
            car_obj.matrix_world.translation = test_location
            bpy.context.view_layer.update()

            # Check if taxi signs followed
            all_followed = True
            for j, taxi in enumerate(taxi_objects):
                expected_pos = initial_taxi_positions[j] + (test_location - initial_car_pos)
                actual_pos = taxi.matrix_world.translation
                distance = (actual_pos - expected_pos).length

                if distance < 1.0:  # Allow 1 unit tolerance
                    print(f"  ✅ Test {i+1}: Taxi '{taxi.name}' follows (error: {distance:.3f})")
                else:
                    print(f"  ❌ Test {i+1}: Taxi '{taxi.name}' doesn't follow (error: {distance:.3f})")
                    all_followed = False

            if all_followed:
                success_count += 1

        # Step 5: Test animation if available
        print("\nStep 5: Testing animation...")
        anim_objects = [obj for obj in bpy.data.objects if obj.animation_data]
        if anim_objects:
            print(f"✅ Found {len(anim_objects)} animated objects")

            # Test animation frames
            scene = bpy.context.scene
            original_frame = scene.frame_current_final

            for frame_offset in [0, 10, 20]:
                scene.frame_set(original_frame + frame_offset)
                bpy.context.view_layer.update()

                if car_obj and taxi_objects:
                    car_pos = car_obj.matrix_world.translation
                    for taxi in taxi_objects:
                        taxi_pos = taxi.matrix_world.translation
                        distance = (car_pos - taxi_pos).length

                        if distance < 10.0:  # Should be relatively close
                            print(f"  ✅ Frame {original_frame + frame_offset}: Taxi is {distance:.2f} units from car")
                        else:
                            print(f"  ❌ Frame {original_frame + frame_offset}: Taxi is {distance:.2f} units from car")
        else:
            print("⚠️  No animated objects found")

        # Calculate success
        success_rate = success_count / total_tests
        print(f"\nSuccess rate: {success_rate:.1%} ({success_count}/{total_tests})")

        if success_rate >= 0.8:  # 80% success rate
            print("\n✅ PARENT-CHILD FIX IS WORKING!")
            print("Taxi signs follow cars correctly.")
            return True
        else:
            print("\n❌ PARENT-CHILD FIX IS NOT WORKING!")
            print("Taxi signs are not following cars properly.")
            return False

    except Exception as e:
        print(f"\n❌ ERROR during testing: {e}")
        import traceback
        traceback.print_exc()
        return False

def save_test_result(success):
    """Save the test result"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    status = "SUCCESS" if success else "FAILED"
    filename = f"parent_child_test_{status}_{timestamp}.blend"

    # Create test_results directory if it doesn't exist
    test_dir = os.path.join(os.path.dirname(__file__), "test_scenes", "blender_test_results")
    os.makedirs(test_dir, exist_ok=True)

    filepath = os.path.join(test_dir, filename)
    bpy.ops.wm.save_as_mainfile(filepath=filepath, copy=True)

    print(f"\n📁 Test scene saved to: {filepath}")
    return filepath

# Main execution
if __name__ == "__main__":
    print("\nStarting CashCab parent-child fix test...")

    # Run test
    success = test_parent_child_fix()

    # Save result
    save_test_result(success)

    # Final message
    if success:
        print("\n🎉 TEST PASSED! The fix is working correctly.")
    else:
        print("\n⚠️  TEST FAILED! The fix needs further investigation.")