#!/usr/bin/env python3
"""
Verification script for the taxi sign following fix.
This should be run after importing a route to verify that taxi signs follow their cars.
"""

import bpy
from mathutils import Vector
import sys

def verify_taxi_sign_following():
    """Verify that taxi signs are properly following their parent cars."""
    print("=" * 60)
    print("TAXI SIGN FOLLOWING VERIFICATION")
    print("=" * 60)

    # Find all relevant objects
    car_objects = []
    taxi_sign_objects = []
    all_related_objects = []

    for obj in bpy.data.objects:
        obj_name_lower = obj.name.lower()
        if obj.type == 'MESH':
            if any(keyword in obj_name_lower for keyword in ['car', 'vehicle', 'body']):
                car_objects.append(obj)
                all_related_objects.append(obj)
            elif any(keyword in obj_name_lower for keyword in ['taxi', 'sign']):
                taxi_sign_objects.append(obj)
                all_related_objects.append(obj)

    print(f"\nFound {len(car_objects)} car objects:")
    for car in car_objects:
        print(f"  - {car.name}")
        print(f"    Location: {car.location}")
        print(f"    Parent: {car.parent.name if car.parent else 'None'}")

    print(f"\nFound {len(taxi_sign_objects)} taxi sign objects:")
    for sign in taxi_sign_objects:
        print(f"  - {sign.name}")
        print(f"    Location: {sign.location}")
        print(f"    Parent: {sign.parent.name if sign.parent else 'None'}")

    # Verification tests
    print("\n" + "="*60)
    print("VERIFICATION TESTS")
    print("="*60)

    tests_passed = 0
    total_tests = 0

    # Test 1: Check if taxi signs have valid parents
    print("\n1. TAXI SIGN PARENT RELATIONSHIP TEST:")
    total_tests += 1
    signs_with_valid_parents = 0
    for sign in taxi_sign_objects:
        if sign.parent and sign.parent in car_objects:
            signs_with_valid_parents += 1
            print(f"   ✅ {sign.name} -> {sign.parent.name}")
        else:
            print(f"   ❌ {sign.name} has no valid car parent")

    if signs_with_valid_parents == len(taxi_sign_objects) and len(taxi_sign_objects) > 0:
        print(f"   ✅ ALL {signs_with_valid_parents} taxi signs have valid car parents")
        tests_passed += 1
    else:
        print(f"   ❌ Only {signs_with_valid_parents}/{len(taxi_sign_objects)} taxi signs have valid car parents")

    # Test 2: Check if taxi signs are reasonably close to their parents
    print("\n2. TAXI SIGN PROXIMITY TEST:")
    total_tests += 1
    signs_close_to_parent = 0
    max_distance = 20.0  # Adjust based on asset scale

    for sign in taxi_sign_objects:
        if sign.parent and sign.parent in car_objects:
            distance = (sign.location - sign.parent.location).length
            if distance < max_distance:
                signs_close_to_parent += 1
                print(f"   ✅ {sign.name} is {distance:.2f} units from {sign.parent.name} (threshold: {max_distance})")
            else:
                print(f"   ❌ {sign.name} is {distance:.2f} units from {sign.parent.name} (threshold: {max_distance})")

    if signs_close_to_parent == len([s for s in taxi_sign_objects if s.parent in car_objects]):
        print(f"   ✅ All taxi signs are within {max_distance} units of their parent cars")
        tests_passed += 1
    else:
        print(f"   ❌ Some taxi signs are too far from their parent cars")

    # Test 3: Check if taxi signs are NOT at origin (unless their car is also at origin)
    print("\n3. TAXI SIGN ORIGIN TEST:")
    total_tests += 1
    origin_threshold = 0.1
    signs_not_at_origin = 0

    for sign in taxi_sign_objects:
        distance_from_origin = sign.location.length
        car_at_origin = sign.parent and sign.parent.location.length < origin_threshold if sign.parent else False

        if distance_from_origin > origin_threshold or car_at_origin:
            signs_not_at_origin += 1
            if car_at_origin:
                print(f"   ✅ {sign.name} is at origin but its car is also at origin (OK)")
            else:
                print(f"   ✅ {sign.name} is not at origin (distance: {distance_from_origin:.2f})")
        else:
            print(f"   ❌ {sign.name} is at origin while its car is not")

    if signs_not_at_origin == len(taxi_sign_objects):
        print("   ✅ No taxi signs are stranded at origin")
        tests_passed += 1
    else:
        print("   ❌ Some taxi signs are stranded at origin")

    # Test 4: Check if car objects are positioned (not at origin unless Start object is at origin)
    print("\n4. CAR POSITIONING TEST:")
    total_tests += 1
    cars_positioned = 0
    start_obj = bpy.data.objects.get('Start')
    start_at_origin = start_obj and start_obj.location.length < origin_threshold if start_obj else False

    for car in car_objects:
        distance_from_origin = car.location.length
        if distance_from_origin > origin_threshold or start_at_origin:
            cars_positioned += 1
            if start_at_origin:
                print(f"   ✅ {car.name} is at origin but Start is also at origin (OK)")
            else:
                print(f"   ✅ {car.name} is positioned (distance from origin: {distance_from_origin:.2f})")
        else:
            print(f"   ❌ {car.name} is at origin (should be positioned)")

    if cars_positioned == len(car_objects):
        print("   ✅ All car objects are properly positioned")
        tests_passed += 1
    else:
        print("   ❌ Some car objects are not properly positioned")

    # Summary
    print("\n" + "="*60)
    print("VERIFICATION SUMMARY")
    print("="*60)

    print(f"Tests passed: {tests_passed}/{total_tests}")
    print(f"Success rate: {(tests_passed/total_tests*100):.1f}%")

    if tests_passed == total_tests:
        print("\n🎉 ALL VERIFICATION TESTS PASSED!")
        print("✅ Taxi signs are following their cars correctly")
        print("✅ Internal parent-child relationships are preserved")
        print("✅ Cars are positioned at the route start")
        return True
    else:
        print(f"\n⚠️  {total_tests - tests_passed} verification tests failed")
        print("❌ The taxi sign following fix may need further adjustment")
        return False

def print_debug_info():
    """Print detailed debug information for troubleshooting."""
    print("\n" + "="*60)
    print("DEBUG INFORMATION")
    print("="*60)

    # Print ASSET_CAR collection info
    car_collection = bpy.data.collections.get('ASSET_CAR')
    if car_collection:
        print(f"\nASSET_CAR collection contains {len(car_collection.objects)} objects:")
        for obj in car_collection.objects:
            print(f"  - {obj.name} (type: {obj.type})")
            if obj.parent:
                print(f"    Parent: {obj.parent.name}")
            children = [child for child in bpy.data.objects if child.parent == obj]
            if children:
                print(f"    Children: {[child.name for child in children]}")

    # Print all parent relationships
    print("\nAll parent relationships in scene:")
    for obj in bpy.data.objects:
        if obj.parent:
            print(f"  {obj.parent.name} -> {obj.name}")

    # Print Start object info
    start_obj = bpy.data.objects.get('Start')
    if start_obj:
        print(f"\nStart object: {start_obj.name}")
        print(f"  Location: {start_obj.location}")
        print(f"  Rotation: {start_obj.rotation_euler}")

if __name__ == "__main__":
    try:
        # Check if we're in Blender
        if 'bpy' not in sys.modules:
            print("This script must be run within Blender")
            sys.exit(1)

        print_debug_info()
        success = verify_taxi_sign_following()

        print(f"\nScript completed with exit code {0 if success else 1}")
        sys.exit(0 if success else 1)

    except Exception as e:
        print(f"Error during verification: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)