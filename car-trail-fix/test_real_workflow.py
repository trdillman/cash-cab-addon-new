#!/usr/bin/env python3
"""
Comprehensive CAR_TRAIL Fix Test - Real Workflow Validation
Tests the actual "Fetch Route and Map" workflow to verify CAR_TRAIL duplication fix
"""

import bpy
import sys
import os
import datetime

# Add addon path
addon_path = r"C:\Users\Tyler\AppData\Roaming\Blender Foundation\Blender\4.5\scripts\addons\cash-cab-addon"
if addon_path not in sys.path:
    sys.path.append(addon_path)

def clear_scene():
    """Clear the entire scene for clean test"""
    print("\n=== CLEARING SCENE ===")

    # Select all objects
    bpy.ops.object.select_all(action='SELECT')

    # Delete selected objects
    bpy.ops.object.delete()

    # Clean up orphaned data
    for mesh in bpy.data.meshes:
        if mesh.users == 0:
            bpy.data.meshes.remove(mesh)

    for curve in bpy.data.curves:
        if curve.users == 0:
            bpy.data.curves.remove(curve)

    for collection in bpy.data.collections:
        if collection.users == 0:
            bpy.data.collections.remove(collection)

    print("✅ Scene cleared")

def check_initial_state():
    """Check initial state of CAR_TRAIL objects"""
    print("\n=== INITIAL STATE CHECK ===")

    car_trail_objects = [obj for obj in bpy.data.objects if 'CAR_TRAIL' in obj.name]
    print(f"CAR_TRAIL objects initially: {len(car_trail_objects)}")

    for obj in car_trail_objects:
        print(f"  - {obj.name} (Type: {obj.type})")

    return len(car_trail_objects)

def execute_route_import():
    """Execute the actual route import workflow"""
    print("\n=== EXECUTING ROUTE IMPORT ===")

    try:
        # Import addon if not already imported
        from route import fetch_operator

        # Execute the route fetch operator
        bpy.ops.wm.blender_osm_fetch(
            start_location="1 Dundas St. E, Toronto",
            end_location="500 Yonge St, Toronto",
            route_padding=0
        )

        print("✅ Route import executed")
        return True

    except Exception as e:
        print(f"❌ Route import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_final_state():
    """Check final state after route import"""
    print("\n=== FINAL STATE CHECK ===")

    car_trail_objects = [obj for obj in bpy.data.objects if 'CAR_TRAIL' in obj.name]
    print(f"CAR_TRAIL objects after import: {len(car_trail_objects)}")

    details = []
    for obj in car_trail_objects:
        obj_info = {
            'name': obj.name,
            'type': obj.type,
            'collections': [c.name for c in obj.users_collection],
            'modifiers': len(obj.modifiers),
            'has_animation': bool(obj.data and obj.data.animation_data) if obj.data else False
        }
        details.append(obj_info)

        print(f"\n  Object: {obj.name}")
        print(f"    Type: {obj.type}")
        print(f"    Collections: {obj_info['collections']}")
        print(f"    Modifiers: {obj_info['modifiers']}")
        print(f"    Has Animation: {obj_info['has_animation']}")

        # Check for geometry nodes modifier
        if obj.type == 'CURVE':
            for mod in obj.modifiers:
                if mod.type == 'NODES':
                    print(f"    GeoNodes: {mod.name} -> {mod.node_group.name if mod.node_group else 'None'}")

        # Check animation drivers
        if obj.data and obj.data.animation_data:
            drivers = obj.data.animation_data.drivers
            print(f"    Drivers: {len(drivers)}")
            for driver in drivers[:3]:  # Show first 3
                print(f"      - {driver.data_path}")

    return car_trail_objects, details

def analyze_results(initial_count, final_objects):
    """Analyze test results"""
    print("\n=== RESULTS ANALYSIS ===")

    final_count = len(final_objects)

    print(f"Initial CAR_TRAIL count: {initial_count}")
    print(f"Final CAR_TRAIL count: {final_count}")

    if final_count == 0:
        print("\n❌ CRITICAL ISSUE: No CAR_TRAIL objects created!")
        print("   This means the trail functionality is completely broken.")
        return False

    elif final_count == 1:
        obj = final_objects[0]
        if obj.name == "CAR_TRAIL":
            print("\n✅ SUCCESS: Exactly one CAR_TRAIL object with correct name")
            print("   Duplication issue appears to be resolved.")
            return True
        else:
            print(f"\n⚠️  PARTIAL: One CAR_TRAIL object but wrong name: {obj.name}")
            print("   Renaming may fix the issue.")
            return False

    elif final_count == 2:
        names = [obj.name for obj in final_objects]
        if "CAR_TRAIL" in names and "CAR_TRAIL.001" in names:
            print("\n❌ FAILURE: Duplication still occurs!")
            print("   The fix did not resolve the issue.")
            return False
        else:
            print(f"\n⚠️  UNEXPECTED: Two objects with names: {names}")
            return False

    else:
        print(f"\n❌ CRITICAL: {final_count} CAR_TRAIL objects found!")
        print("   This is worse than the original issue.")
        return False

def save_test_results(results):
    """Save test results to file"""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"car-trail-fix/test_results/workflow_test_{timestamp}.json"

    os.makedirs(os.path.dirname(filename), exist_ok=True)

    import json
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\n📄 Results saved to: {filename}")

def main():
    """Main test execution"""
    print("=" * 60)
    print("CAR_TRAIL FIX - REAL WORKFLOW VALIDATION")
    print("=" * 60)
    print(f"Timestamp: {datetime.datetime.now().isoformat()}")
    print(f"Blender Version: {bpy.app.version_string}")

    # Clear scene for clean test
    clear_scene()

    # Check initial state
    initial_count = check_initial_state()

    # Execute route import workflow
    if not execute_route_import():
        print("\n❌ ABORT: Route import failed")
        return

    # Check final state
    final_objects, details = check_final_state()

    # Analyze results
    success = analyze_results(initial_count, final_objects)

    # Prepare results
    results = {
        'timestamp': datetime.datetime.now().isoformat(),
        'blender_version': bpy.app.version_string,
        'initial_count': initial_count,
        'final_count': len(final_objects),
        'success': success,
        'objects': details
    }

    # Save results
    save_test_results(results)

    # Final verdict
    print("\n" + "=" * 60)
    if success:
        print("🎉 CAR_TRAIL FIX VERIFICATION: PASSED")
        print("   The duplication issue has been resolved!")
    else:
        print("💥 CAR_TRAIL FIX VERIFICATION: FAILED")
        print("   Further investigation required.")
    print("=" * 60)

if __name__ == "__main__":
    main()