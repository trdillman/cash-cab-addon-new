"""
Test CAR_TRAIL fix in Blender GUI mode
Run this from Blender's Python console:
  exec(open(r"C:\Users\Tyler\AppData\Roaming\Blender Foundation\Blender\4.5\scripts\addons\cash-cab-addon\blender_gui_test.py").read())
"""

import bpy
import os
import datetime

print("=" * 60)
print("CAR_TRAIL FIX TEST - GUI Mode")
print("=" * 60)
print(f"Time: {datetime.datetime.now()}")

def check_car_trail_objects():
    """Check all CAR_TRAIL objects in the scene"""
    car_trails = []
    for obj in bpy.data.objects:
        if 'CAR_TRAIL' in obj.name:
            car_trails.append(obj)

    print(f"\nFound {len(car_trails)} CAR_TRAIL object(s):")
    for obj in car_trails:
        print(f"  - {obj.name}")
        print(f"    Type: {obj.type}")
        print(f"    Collections: {[c.name for c in obj.users_collection]}")

        # Check modifiers
        if obj.type == 'CURVE':
            for mod in obj.modifiers:
                if mod.type == 'NODES':
                    print(f"    Has GeoNodes modifier: {mod.name}")

        # Check animation
        if obj.data and obj.data.animation_data:
            drivers = obj.data.animation_data.drivers
            print(f"    Animation drivers: {len(drivers)}")
            for d in drivers[:2]:  # Show first 2
                print(f"      - {d.data_path}")

    return car_trails

def clear_scene():
    """Clear everything"""
    print("\nClearing scene...")

    # Select all objects
    bpy.ops.object.select_all(action='SELECT')

    # Delete them
    bpy.ops.object.delete()

    # Check result
    car_trails = [obj for obj in bpy.data.objects if 'CAR_TRAIL' in obj.name]
    print(f"After clear: {len(car_trails)} CAR_TRAIL objects")

def test_route_import():
    """Test the actual route import"""
    print("\n" + "=" * 40)
    print("TESTING ROUTE IMPORT")
    print("=" * 40)

    # Check initial state
    initial_count = len([obj for obj in bpy.data.objects if 'CAR_TRAIL' in obj.name])
    print(f"Initial CAR_TRAIL count: {initial_count}")

    # Instructions for manual test
    print("\n" + "-" * 40)
    print("MANUAL TEST INSTRUCTIONS:")
    print("-" * 40)
    print("1. Make sure scene is clear (use 'Clear Scene' button)")
    print("2. Open the 3D View > Sidebar > CashCab tab")
    print("3. Set Start Location: '1 Dundas St. E, Toronto'")
    print("4. Set End Location: '500 Yonge St, Toronto'")
    print("5. Click 'Fetch Route and Map' button")
    print("6. Wait for completion (30-60 seconds)")
    print("7. Run check_car_trail_objects() again")
    print("-" * 40)

    # Auto-check function for after import
    print("\ndef check_after_import():")
    print("    check_car_trail_objects()")
    print("    # Expected: Exactly 1 CAR_TRAIL object")

# Run initial check
print("\nInitial scene check:")
car_trails = check_car_trail_objects()

# Show what to expect
print("\n" + "=" * 40)
print("EXPECTED RESULTS AFTER IMPORT:")
print("=" * 40)
print("✅ Success: Exactly 1 CAR_TRAIL object")
print("❌ Failure: Multiple CAR_TRAIL objects (.001, .002, etc.)")
print("❌ Failure: No CAR_TRAIL objects")
print("=" * 40)

# Add utility functions
def analyze_duplication():
    """Analyze if duplication is happening"""
    car_trails = check_car_trail_objects()

    if len(car_trails) == 1:
        if car_trails[0].name == 'CAR_TRAIL':
            print("\n✅ NO DUPLICATION - Fix appears to be working!")
            return True
        else:
            print(f"\n⚠️  Single object but wrong name: {car_trails[0].name}")
            return False
    elif len(car_trails) > 1:
        print("\n❌ DUPLICATION DETECTED!")
        print("The enhanced cleanup fix may not be working properly.")
        return False
    else:
        print("\n❌ NO CAR_TRAIL FOUND")
        print("Trail functionality may be broken.")
        return False

def test_animation():
    """Test if animation is working"""
    print("\nTesting animation setup...")

    car_trail = bpy.data.objects.get('CAR_TRAIL')
    if not car_trail:
        print("❌ No CAR_TRAIL object to test")
        return

    scene = bpy.context.scene
    print(f"Frame range: {scene.frame_start} to {scene.frame_end}")

    # Set to frame 1
    scene.frame_set(1)
    print("Current frame set to 1")

    print("\nTo test animation:")
    print("1. Press Spacebar to play")
    print("2. Look for trail effect")
    print("3. Check for bevel animation")

# Provide quick commands
print("\n" + "=" * 40)
print("QUICK COMMANDS TO RUN:")
print("=" * 40)
print("# Check CAR_TRAIL objects:")
print("check_car_trail_objects()")
print("\n# Analyze duplication:")
print("analyze_duplication()")
print("\n# Test animation:")
print("test_animation()")
print("\n# Clear scene:")
print("clear_scene()")