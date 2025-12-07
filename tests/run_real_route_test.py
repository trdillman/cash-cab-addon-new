"""
Real Route Import Test for CAR_TRAIL Fix
This will execute the actual "Fetch Route and Map" workflow to test our fix
"""

import bpy
import sys
import os
import datetime

# Clear the console
print("\n" * 50)
print("=" * 60)
print("REAL ROUTE IMPORT TEST - CAR_TRAIL FIX VALIDATION")
print("=" * 60)
print(f"Timestamp: {datetime.datetime.now()}")
print(f"Blender Version: {bpy.app.version_string}")

# Add addon path
addon_path = r"C:\Users\Tyler\AppData\Roaming\Blender Foundation\Blender\4.5\scripts\addons\cash-cab-addon"
if addon_path not in sys.path:
    sys.path.append(addon_path)

def check_car_trail_state(label):
    """Check current CAR_TRAIL objects"""
    car_trail_objects = [obj for obj in bpy.data.objects if 'CAR_TRAIL' in obj.name]
    print(f"\n{label}:")
    print(f"  Total CAR_TRAIL objects: {len(car_trail_objects)}")

    details = []
    for obj in car_trail_objects:
        obj_info = {
            'name': obj.name,
            'type': obj.type,
            'collections': [c.name for c in obj.users_collection],
            'modifiers': len(obj.modifiers),
            'is_curve': obj.type == 'CURVE'
        }
        details.append(obj_info)
        print(f"    - {obj.name} ({obj.type})")
        print(f"      Collections: {obj_info['collections']}")

        # Check for geometry nodes
        if obj.type == 'CURVE':
            for mod in obj.modifiers:
                if mod.type == 'NODES':
                    print(f"      Has GeoNodes: {mod.name}")

        # Check for animation
        if obj.data and obj.data.animation_data:
            drivers = obj.data.animation_data.drivers
            if drivers:
                print(f"      Animation drivers: {len(drivers)}")

    return car_trail_objects, details

def clear_scene():
    """Clear the scene completely"""
    print("\n=== CLEARING SCENE ===")

    # Select and delete all objects
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()

    # Clean up orphaned data
    for mesh in bpy.data.meshes:
        if mesh.users == 0:
            bpy.data.meshes.remove(mesh)

    for curve in bpy.data.curves:
        if curve.users == 0:
            bpy.data.curves.remove(curve)

    for material in bpy.data.materials:
        if material.users == 0:
            bpy.data.materials.remove(material)

    print("✅ Scene cleared")

def check_fix_status():
    """Check if our fix is applied"""
    print("\n=== CHECKING FIX STATUS ===")

    pipeline_file = os.path.join(addon_path, "route", "pipeline_finalizer.py")

    try:
        with open(pipeline_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check for enhanced cleanup
        if "objects_to_remove = []" in content and "obj.name.startswith('CAR_TRAIL')" in content:
            print("✅ Enhanced cleanup fix is applied")
            return True
        else:
            print("❌ Enhanced cleanup fix NOT found")
            return False

    except Exception as e:
        print(f"❌ Error checking fix: {e}")
        return False

def run_route_import():
    """Execute the actual route import"""
    print("\n=== RUNNING ROUTE IMPORT ===")
    print("Importing: 1 Dundas St. E, Toronto to 500 Yonge St, Toronto")
    print("This may take 30-60 seconds...")

    try:
        # Import the addon module
        import route.fetch_operator as fetch_op

        # Execute the fetch operator
        result = bpy.ops.wm.blender_osm_fetch(
            start_location="1 Dundas St. E, Toronto",
            end_location="500 Yonge St, Toronto",
            route_padding=0
        )

        print(f"✅ Route import completed with result: {result}")
        return True

    except Exception as e:
        print(f"❌ Route import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def analyze_results(initial_objects, final_objects, initial_details, final_details):
    """Analyze the test results"""
    print("\n=== RESULTS ANALYSIS ===")

    initial_count = len(initial_objects)
    final_count = len(final_objects)

    print(f"CAR_TRAIL objects - Before: {initial_count}, After: {final_count}")

    if final_count == 0:
        print("\n❌ CRITICAL: No CAR_TRAIL objects created!")
        print("   The trail functionality may be broken.")
        return False

    elif final_count == 1:
        obj = final_objects[0]
        if obj['name'] == 'CAR_TRAIL':
            print("\n✅ SUCCESS: Exactly one CAR_TRAIL object")
            print("   Duplication issue appears to be resolved!")
            return True
        else:
            print(f"\n⚠️  UNUSUAL: Single CAR_TRAIL but named '{obj['name']}'")
            return False

    else:
        names = [obj['name'] for obj in final_objects]
        print(f"\n❌ FAILURE: {final_count} CAR_TRAIL objects found: {names}")
        print("   Duplication issue persists!")
        return False

def check_animation_setup():
    """Check if animation is properly set up"""
    print("\n=== ANIMATION CHECK ===")

    car_trail = bpy.data.objects.get('CAR_TRAIL')
    if not car_trail:
        print("❌ No CAR_TRAIL object found")
        return False

    # Check frame range
    scene = bpy.context.scene
    print(f"Frame range: {scene.frame_start} to {scene.frame_end}")

    # Check if timeline can play
    if scene.frame_end > scene.frame_start:
        print("✅ Timeline has valid frame range")
        print("\nTo test animation:")
        print("  1. Press Spacebar to play animation")
        print("  2. Look for trail effect along the route")
        print("  3. Check if bevel/wipe effect works")
    else:
        print("⚠️  Invalid frame range - animation may not work")

    return True

def save_test_results(results):
    """Save test results"""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"car-trail-fix/real_test_results_{timestamp}.json"

    os.makedirs(os.path.dirname(filename), exist_ok=True)

    import json
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\n📄 Results saved: {filename}")

def main():
    """Main test execution"""

    # Check if fix is applied
    if not check_fix_status():
        print("\n⚠️  WARNING: Fix may not be properly applied!")
        response = input("Continue anyway? (y/N): ")
        if response.lower() != 'y':
            return

    # Check initial state
    print("\nChecking initial scene state...")
    initial_objects, initial_details = check_car_trail_state("INITIAL STATE")

    # Clear scene for clean test
    if initial_objects:
        clear_scene()
        initial_objects, initial_details = check_car_trail_state("AFTER CLEAR")

    # Run route import
    if not run_route_import():
        print("\n❌ ABORT: Route import failed")
        return

    # Check final state
    final_objects, final_details = check_car_trail_state("FINAL STATE")

    # Analyze results
    success = analyze_results(initial_objects, final_objects, initial_details, final_details)

    # Check animation setup
    animation_ok = check_animation_setup()

    # Prepare results
    results = {
        'timestamp': datetime.datetime.now().isoformat(),
        'blender_version': bpy.app.version_string,
        'fix_applied': check_fix_status(),
        'initial_count': len(initial_objects),
        'final_count': len(final_objects),
        'initial_objects': initial_details,
        'final_objects': final_details,
        'success': success,
        'animation_setup': animation_ok,
        'scene_stats': {
            'total_objects': len(bpy.data.objects),
            'total_collections': len(bpy.data.collections)
        }
    }

    # Save results
    save_test_results(results)

    # Final verdict
    print("\n" + "=" * 60)
    print("TEST CONCLUSION:")

    if success:
        print("✅ CAR_TRAIL FIX VALIDATION: PASSED")
        print("   - Single CAR_TRAIL object created")
        print("   - No duplication detected")
        if animation_ok:
            print("   - Animation setup appears correct")
        print("\nRecommendation: Test animation playback to verify trail effect")
    else:
        print("💥 CAR_TRAIL FIX VALIDATION: FAILED")
        print("   - Duplication issue persists or trail missing")
        print("\nRecommendation: Review cleanup logic or check asset files")

    print("=" * 60)

if __name__ == "__main__":
    main()