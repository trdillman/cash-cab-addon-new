#!/usr/bin/env python3
"""
Test script to verify that taxi signs follow their parent cars during route import.
This script checks for proper parent-child relationships and positioning.
"""

import bpy
from mathutils import Vector
import sys
import os

def test_taxi_sign_following():
    """Test if taxi signs are properly following their parent cars."""
    print("=" * 60)
    print("TAXI SIGN FOLLOWING TEST")
    print("=" * 60)

    # Find all car objects
    car_objects = []
    taxi_sign_objects = []

    for obj in bpy.data.objects:
        if obj.type == 'MESH':
            if any(keyword in obj.name.lower() for keyword in ['car', 'vehicle', 'body']):
                car_objects.append(obj)
            elif any(keyword in obj.name.lower() for keyword in ['taxi', 'sign']):
                taxi_sign_objects.append(obj)

    print(f"\nFound {len(car_objects)} car objects:")
    for car in car_objects:
        print(f"  - {car.name} (type: {car.type}, location: {car.location})")

    print(f"\nFound {len(taxi_sign_objects)} taxi sign objects:")
    for sign in taxi_sign_objects:
        print(f"  - {sign.name} (type: {sign.type}, location: {sign.location})")

    # Test parent-child relationships
    print("\n" + "="*60)
    print("PARENT-CHILD RELATIONSHIP TEST")
    print("="*60)

    success_count = 0
    test_count = 0

    for sign in taxi_sign_objects:
        if sign.parent and sign.parent in car_objects:
            test_count += 1
            distance = (sign.location - sign.parent.location).length

            print(f"\n✓ {sign.name} -> {sign.parent.name}")
            print(f"  Parent type: {sign.parent.type}")
            print(f"  Sign location: {sign.location}")
            print(f"  Parent location: {sign.parent.location}")
            print(f"  Distance from parent: {distance:.6f}")

            # Check if the sign is reasonably close to its parent car
            if distance < 10.0:  # Adjust this threshold based on your asset scale
                print(f"  ✅ SIGN IS FOLLOWING CAR (distance < 10.0)")
                success_count += 1
            else:
                print(f"  ❌ SIGN IS TOO FAR FROM CAR (distance >= 10.0)")

        else:
            test_count += 1
            print(f"\n❌ {sign.name} has no valid parent")
            if sign.parent:
                print(f"  Current parent: {sign.parent.name} (type: {sign.parent.type})")
            else:
                print(f"  No parent assigned")

    # Test positioning by checking if signs are at origin (bad) or with cars (good)
    print("\n" + "="*60)
    print("POSITIONING TEST")
    print("="*60)

    origin_threshold = 0.1
    for sign in taxi_sign_objects:
        distance_from_origin = sign.location.length

        if distance_from_origin < origin_threshold:
            print(f"❌ {sign.name} is at origin (should be with car)")
        else:
            print(f"✓ {sign.name} is positioned away from origin")

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    print(f"Total taxi signs tested: {test_count}")
    print(f"Signs following cars: {success_count}")
    print(f"Success rate: {(success_count/test_count*100):.1f}%" if test_count > 0 else "N/A")

    if success_count == test_count and test_count > 0:
        print("\n🎉 ALL TESTS PASSED! Taxi signs are following cars correctly.")
        return True
    else:
        print(f"\n⚠️  {test_count - success_count} taxi signs are not following their cars.")
        return False

def debug_asset_structure():
    """Debug the asset structure to understand car hierarchy."""
    print("\n" + "="*60)
    print("ASSET STRUCTURE DEBUG")
    print("="*60)

    # Find ASSET_CAR collection if it exists
    car_collection = bpy.data.collections.get('ASSET_CAR')
    if car_collection:
        print(f"\nASSET_CAR collection found with {len(car_collection.objects)} objects:")
        for obj in car_collection.objects:
            print(f"  - {obj.name} (type: {obj.type})")
            if obj.parent:
                print(f"    Parent: {obj.parent.name}")
            children = [child for child in bpy.data.objects if child.parent == obj]
            if children:
                print(f"    Children: {[child.name for child in children]}")

    # Print all parent relationships in the scene
    print("\nAll parent relationships in scene:")
    parent_relationships = {}
    for obj in bpy.data.objects:
        if obj.parent:
            if obj.parent.name not in parent_relationships:
                parent_relationships[obj.parent.name] = []
            parent_relationships[obj.parent.name].append(obj.name)

    for parent, children in parent_relationships.items():
        print(f"  {parent} -> {children}")

if __name__ == "__main__":
    try:
        # Check if we're in Blender
        if 'bpy' not in sys.modules:
            print("This script must be run within Blender")
            sys.exit(1)

        debug_asset_structure()
        success = test_taxi_sign_following()

        # Exit with appropriate code
        sys.exit(0 if success else 1)

    except Exception as e:
        print(f"Error during test execution: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)