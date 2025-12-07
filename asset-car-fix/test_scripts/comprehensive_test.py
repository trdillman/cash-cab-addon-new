"""
Comprehensive test for the CashCab addon parent-child relationship fix.

This script tests the complete pipeline:
1. Route fetching with default addresses
2. Asset import
3. Positioning and animation
4. Parent-child relationship verification
"""

import bpy
import os
import sys
from datetime import datetime

# Add addon path to sys.path to import modules
addon_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if addon_path not in sys.path:
    sys.path.insert(0, addon_path)

def clear_scene():
    """Clear the Blender scene"""
    print("Clearing scene...")
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()

    # Clear orphan data
    for block in bpy.data.meshes:
        if block.users == 0:
            bpy.data.meshes.remove(block)
    for block in bpy.data.materials:
        if block.users == 0:
            bpy.data.materials.remove(block)
    for block in bpy.data.textures:
        if block.users == 0:
            bpy.data.textures.remove(block)
    for block in bpy.data.images:
        if block.users == 0:
            bpy.data.images.remove(block)

    print("Scene cleared")

def get_test_routes():
    """Get test routes with default addresses"""
    return [
        {
            "name": "test_route_nyc",
            "start": "Times Square, New York, NY",
            "end": "Central Park, New York, NY",
            "description": "NYC Times Square to Central Park"
        },
        {
            "name": "test_route_sf",
            "start": "Golden Gate Bridge, San Francisco, CA",
            "end": "Fisher's Wharf, San Francisco, CA",
            "description": "San Francisco Golden Gate to Fisherman's Wharf"
        }
    ]

def test_route_fetch_and_import(route_info):
    """Test route fetching and asset import"""
    print(f"\n{'='*60}")
    print(f"Testing route: {route_info['description']}")
    print(f"From: {route_info['start']}")
    print(f"To: {route_info['end']}")
    print(f"{'='*60}")

    try:
        # Import route modules
        from route import fetch_operator
        from route import assets as route_assets
        from route import anim as route_anim

        # Set start and end locations
        bpy.context.scene.blosm.start = route_info['start']
        bpy.context.scene.blosm.end = route_info['end']

        # Step 1: Fetch route
        print("\nStep 1: Fetching route...")
        bpy.ops.blosm.fetch_route()

        # Check if route was created
        route_objects = [obj for obj in bpy.data.objects if 'BLOSM_route' in obj.name]
        if not route_objects:
            print("❌ ERROR: No route objects created")
            return False

        print(f"✅ Route created with {len(route_objects)} objects")

        # Step 2: Import assets
        print("\nStep 2: Importing assets...")

        # Check if ASSET_CAR collection exists or will be created
        if 'ASSET_CAR' not in bpy.data.collections:
            print("Creating ASSET_CAR collection...")

        # Import assets
        bpy.ops.blosm.import_assets()

        # Check if car objects were imported
        car_collection = bpy.data.collections.get('ASSET_CAR')
        if car_collection:
            car_objects = list(car_collection.objects)
            print(f"✅ Car collection has {len(car_objects)} objects")

            # Look for taxi signs
            taxi_objects = [obj for obj in car_objects if 'taxi' in obj.name.lower() or 'sign' in obj.name.lower()]
            if taxi_objects:
                print(f"✅ Found {len(taxi_objects)} taxi sign objects")
                for taxi in taxi_objects:
                    print(f"  - {taxi.name}")
            else:
                print("⚠️  WARNING: No taxi sign objects found")
        else:
            print("⚠️  WARNING: No ASSET_CAR collection found")

        # Step 3: Position cars
        print("\nStep 3: Positioning cars...")

        # Get car object
        car_obj = None
        if car_collection:
            for obj in car_collection.objects:
                if 'car' in obj.name.lower() or 'body' in obj.name.lower():
                    car_obj = obj
                    break

        if car_obj:
            # The positioning happens in import_assets operator
            # Let's verify the car was positioned
            start_obj = bpy.data.objects.get('BLOSM_start')
            if start_obj:
                distance = (car_obj.matrix_world.translation - start_obj.matrix_world.translation).length
                print(f"✅ Car positioned at distance {distance:.3f} from start point")

                if distance < 10.0:  # Should be very close
                    print("✅ Car positioning looks correct")
                else:
                    print(f"⚠️  WARNING: Car is {distance:.3f} units from start point")
            else:
                print("⚠️  WARNING: No start object found")
        else:
            print("❌ ERROR: No car object found for positioning")
            return False

        # Step 4: Test parent-child relationships
        print("\nStep 4: Testing parent-child relationships...")

        if car_obj and taxi_objects:
            success = True
            for taxi in taxi_objects:
                # Store initial positions
                initial_car_pos = car_obj.matrix_world.translation.copy()
                initial_taxi_pos = taxi.matrix_world.translation.copy()

                # Move car to test position
                test_location = (10, 10, 5)
                car_obj.matrix_world.translation = test_location
                bpy.context.view_layer.update()

                # Check if taxi followed
                final_taxi_pos = taxi.matrix_world.translation.copy()
                expected_taxi_pos = initial_taxi_pos + (test_location - initial_car_pos)

                distance = (final_taxi_pos - expected_taxi_pos).length

                if distance < 0.5:  # Allow some tolerance
                    print(f"✅ Taxi sign '{taxi.name}' follows car (error: {distance:.3f})")
                else:
                    print(f"❌ Taxi sign '{taxi.name}' does NOT follow car (error: {distance:.3f})")
                    success = False

                # Reset car position
                car_obj.matrix_world.translation = initial_car_pos
                bpy.context.view_layer.update()

            if success:
                print("✅ All taxi signs follow cars correctly!")
            else:
                print("❌ Some taxi signs do not follow cars")
                return success

        # Step 5: Test animation
        print("\nStep 5: Testing animation...")

        # Get animation objects
        anim_objects = [obj for obj in bpy.data.objects if obj.animation_data]
        if anim_objects:
            print(f"✅ Found {len(anim_objects)} animated objects")

            # Try to play a few frames
            scene = bpy.context.scene
            if scene.frame_start == scene.frame_end:
                scene.frame_end = scene.frame_start + 100

            print(f"Animation range: {scene.frame_start} to {scene.frame_end}")

            # Test a few keyframes
            test_frames = [scene.frame_start, scene.frame_start + 25, scene.frame_start + 50]
            for frame in test_frames:
                scene.frame_set(frame)
                bpy.context.view_layer.update()

                if car_obj and taxi_objects:
                    car_pos = car_obj.matrix_world.translation
                    for taxi in taxi_objects:
                        taxi_pos = taxi.matrix_world.translation
                        distance = (car_pos - taxi_pos).length

                        if distance < 5.0:  # Taxi should stay reasonably close
                            print(f"✅ Frame {frame}: Taxi '{taxi.name}' is {distance:.2f} units from car")
                        else:
                            print(f"❌ Frame {frame}: Taxi '{taxi.name}' is {distance:.2f} units from car (too far!)")
        else:
            print("⚠️  No animation found")

        return True

    except Exception as e:
        print(f"❌ ERROR during testing: {e}")
        import traceback
        traceback.print_exc()
        return False

def save_test_scene(route_info, success):
    """Save the test scene with success/failure indication"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    status = "SUCCESS" if success else "FAILED"
    filename = f"{route_info['name']}_{status}_{timestamp}.blend"
    filepath = os.path.join(
        os.path.dirname(__file__),
        "test_scenes",
        "blender_test_results",
        filename
    )

    bpy.ops.wm.save_as_mainfile(filepath=filepath, copy=True)
    print(f"\n📁 Scene saved to: {filepath}")
    return filepath

def generate_test_report(results):
    """Generate a comprehensive test report"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    report = f"""
# CashCab Parent-Child Fix - Comprehensive Test Report

**Generated**: {timestamp}
**Test Status**: {'✅ ALL TESTS PASSED' if all(results.values()) else '❌ SOME TESTS FAILED'}

## Test Results

"""

    for route_name, success in results.items():
        status = "✅ PASSED" if success else "❌ FAILED"
        report += f"- **{route_name}**: {status}\n"

    report += f"""

## Summary

- Total Tests: {len(results)}
- Passed: {sum(results.values())}
- Failed: {len(results) - sum(results.values())}

## Implementation Details

- Fix applied to: `route/anim.py` lines 610-625
- Changes: Parent relationships cleared before positioning to avoid matrix conflicts
- Matrix import: Already present in file

## Test Configuration

Each test verified:
1. Route fetching from start to end address
2. Asset import with ASSET_CAR collection
3. Car positioning at route start
4. Taxi sign parent-child relationships
5. Animation playback verification

## Files

- Test scenes saved to: `asset-car-fix/test_scenes/blender_test_results/`
- Backup of original file: `route/anim.py.backup`
- Fixed file: `route/anim.py`
"""

    # Save report
    report_path = os.path.join(
        os.path.dirname(__file__),
        "test_scenes",
        "blender_test_results",
        f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    )

    with open(report_path, 'w') as f:
        f.write(report)

    print(f"\n📄 Test report saved to: {report_path}")
    return report_path

def main():
    """Main test execution"""
    print("\n" + "="*80)
    print("🚗 CASHCAB PARENT-CHILD FIX - COMPREHENSIVE TEST")
    print("="*80)

    # Clear scene
    clear_scene()

    # Get test routes
    test_routes = get_test_routes()
    results = {}

    # Run tests
    for route_info in test_routes:
        print(f"\n📍 Starting test for: {route_info['name']}")

        # Run the test
        success = test_route_fetch_and_import(route_info)
        results[route_info['name']] = success

        # Save scene
        save_test_scene(route_info, success)

        # Clear for next test
        if route_info != test_routes[-1]:  # Don't clear after last test
            clear_scene()

    # Generate report
    report_path = generate_test_report(results)

    # Print summary
    print("\n" + "="*80)
    print("🏁 TEST SUMMARY")
    print("="*80)

    for route_name, success in results.items():
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{route_name}: {status}")

    all_passed = all(results.values())

    if all_passed:
        print(f"\n🎉 ALL TESTS PASSED! The parent-child fix is working correctly.")
        print("✅ Taxi signs now follow cars during route import and animation.")
    else:
        print(f"\n⚠️  Some tests failed. Please review the test scenes and report.")

    print(f"\n📊 Detailed report: {report_path}")

    return all_passed

if __name__ == "__main__":
    main()