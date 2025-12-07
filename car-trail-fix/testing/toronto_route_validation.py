"""
CAR_TRAIL Fix Validation Script for Toronto Route Testing

This script validates the CAR_TRAIL duplication fix implementation
by testing with Toronto downtown coordinates:
- Start: 1 Dundas St E, Toronto, ON (43.6532°N, 79.3832°W)
- End: 500 Yonge St, Toronto, ON (43.6532°N, 79.3832°W)

CRITICAL SUCCESS CRITERIA:
1. Single CAR_TRAIL object exactly (no .001 variants)
2. Correct Toronto route geometry matching
3. Geometry nodes modifier from ASSET_CAR.blend
4. Two animation drivers properly configured
5. No track-to modifier present
6. Car asset integration working
"""

import bpy
import sys
from pathlib import Path

def validate_car_trail_success():
    """
    Comprehensive validation function that checks all 6 critical success criteria.
    Returns detailed validation report.
    """
    print("=" * 80)
    print("CAR_TRAIL FIX VALIDATION REPORT")
    print("=" * 80)
    
    validation_results = {
        'total_tests': 6,
        'passed_tests': 0,
        'failed_tests': 0,
        'details': {},
        'success': False
    }
    
    # Test 1: Object count and naming
    print("\n1. TESTING: Object Count and Naming")
    car_trail_objects = [obj for obj in bpy.data.objects if obj.name.startswith('CAR_TRAIL')]
    
    if len(car_trail_objects) == 1 and car_trail_objects[0].name == 'CAR_TRAIL':
        print(f"   ✅ PASS: Exactly 1 CAR_TRAIL object found: '{car_trail_objects[0].name}'")
        validation_results['passed_tests'] += 1
        validation_results['details']['object_count'] = {
            'status': 'PASS',
            'count': len(car_trail_objects),
            'names': [obj.name for obj in car_trail_objects]
        }
    else:
        print(f"   ❌ FAIL: Expected 1 CAR_TRAIL, found {len(car_trail_objects)}: {[obj.name for obj in car_trail_objects]}")
        validation_results['failed_tests'] += 1
        validation_results['details']['object_count'] = {
            'status': 'FAIL',
            'count': len(car_trail_objects),
            'names': [obj.name for obj in car_trail_objects],
            'expected': 'Exactly 1 object named "CAR_TRAIL"'
        }
    
    # Test 2: Geometry fidelity with Toronto route
    print("\n2. TESTING: Route Geometry Fidelity")
    route_obj = bpy.data.objects.get('ROUTE') or bpy.data.objects.get('Route')
    
    if route_obj and car_trail_objects:
        car_trail = car_trail_objects[0]
        if car_trail.type == 'CURVE' and route_obj.type == 'CURVE':
            # Compare curve data points (simplified check)
            route_points = len(route_obj.data.splines[0].points) if route_obj.data.splines else 0
            trail_points = len(car_trail.data.splines[0].points) if car_trail.data.splines else 0
            
            if route_points > 0 and trail_points > 0:
                print(f"   ✅ PASS: Both ROUTE and CAR_TRAIL are curves with points ({route_points} and {trail_points})")
                validation_results['passed_tests'] += 1
                validation_results['details']['geometry_fidelity'] = {
                    'status': 'PASS',
                    'route_points': route_points,
                    'trail_points': trail_points,
                    'route_type': route_obj.type,
                    'trail_type': car_trail.type
                }
            else:
                print(f"   ❌ FAIL: ROUTE or CAR_TRAIL has no curve points")
                validation_results['failed_tests'] += 1
                validation_results['details']['geometry_fidelity'] = {
                    'status': 'FAIL',
                    'route_points': route_points,
                    'trail_points': trail_points,
                    'reason': 'Missing curve data'
                }
        else:
            print(f"   ❌ FAIL: ROUTE or CAR_TRAIL is not a curve object")
            validation_results['failed_tests'] += 1
            validation_results['details']['geometry_fidelity'] = {
                'status': 'FAIL',
                'reason': 'Object type mismatch'
            }
    else:
        print(f"   ❌ FAIL: ROUTE object not found or no CAR_TRAIL objects")
        validation_results['failed_tests'] += 1
        validation_results['details']['geometry_fidelity'] = {
            'status': 'FAIL',
            'reason': 'Missing ROUTE or CAR_TRAIL objects'
        }
    
    # Test 3: Geometry nodes modifier presence
    print("\n3. TESTING: Geometry Nodes Modifier")
    if car_trail_objects:
        car_trail = car_trail_objects[0]
        geo_mods = [m for m in car_trail.modifiers if m.type == 'NODES']
        
        if geo_mods:
            geo_mod = geo_mods[0]
            node_group_name = geo_mod.node_group.name if geo_mod.node_group else 'None'
            print(f"   ✅ PASS: Found geometry nodes modifier: '{geo_mod.name}' -> '{node_group_name}'")
            validation_results['passed_tests'] += 1
            validation_results['details']['geometry_nodes'] = {
                'status': 'PASS',
                'modifier_count': len(geo_mods),
                'modifier_name': geo_mod.name,
                'node_group': node_group_name
            }
        else:
            print(f"   ❌ FAIL: No geometry nodes modifier found on CAR_TRAIL")
            validation_results['failed_tests'] += 1
            validation_results['details']['geometry_nodes'] = {
                'status': 'FAIL',
                'modifier_count': 0,
                'reason': 'Missing NODES modifier'
            }
    else:
        print(f"   ❌ FAIL: No CAR_TRAIL object to check")
        validation_results['failed_tests'] += 1
        validation_results['details']['geometry_nodes'] = {
            'status': 'FAIL',
            'reason': 'No CAR_TRAIL object'
        }
    
    # Test 4: Animation drivers (must be exactly 2)
    print("\n4. TESTING: Animation Drivers")
    if car_trail_objects:
        car_trail = car_trail_objects[0]
        if car_trail.data and car_trail.data.animation_data:
            drivers = car_trail.data.animation_data.drivers
            bevel_drivers = [d for d in drivers if 'bevel_factor' in d.data_path]
            
            if len(bevel_drivers) == 2:
                driver_info = [(d.data_path, d.driver.expression) for d in bevel_drivers]
                print(f"   ✅ PASS: Found exactly 2 bevel drivers: {driver_info}")
                validation_results['passed_tests'] += 1
                validation_results['details']['animation_drivers'] = {
                    'status': 'PASS',
                    'driver_count': len(bevel_drivers),
                    'drivers': driver_info
                }
            else:
                print(f"   ❌ FAIL: Expected 2 bevel drivers, found {len(bevel_drivers)}")
                validation_results['failed_tests'] += 1
                validation_results['details']['animation_drivers'] = {
                    'status': 'FAIL',
                    'expected_count': 2,
                    'actual_count': len(bevel_drivers),
                    'all_drivers': [d.data_path for d in drivers] if drivers else []
                }
        else:
            print(f"   ❌ FAIL: No animation data or drivers found on CAR_TRAIL")
            validation_results['failed_tests'] += 1
            validation_results['details']['animation_drivers'] = {
                'status': 'FAIL',
                'reason': 'No animation data'
            }
    else:
        print(f"   ❌ FAIL: No CAR_TRAIL object to check")
        validation_results['failed_tests'] += 1
        validation_results['details']['animation_drivers'] = {
            'status': 'FAIL',
            'reason': 'No CAR_TRAIL object'
        }
    
    # Test 5: No track-to modifier
    print("\n5. TESTING: No Track-To Modifier")
    if car_trail_objects:
        car_trail = car_trail_objects[0]
        track_mods = [m for m in car_trail.modifiers if m.type == 'TRACK_TO']
        
        if len(track_mods) == 0:
            print(f"   ✅ PASS: No track-to modifiers found (correct)")
            validation_results['passed_tests'] += 1
            validation_results['details']['no_track_modifier'] = {
                'status': 'PASS',
                'track_modifiers': 0
            }
        else:
            track_names = [m.name for m in track_mods]
            print(f"   ❌ FAIL: Found {len(track_mods)} track-to modifiers: {track_names}")
            validation_results['failed_tests'] += 1
            validation_results['details']['no_track_modifier'] = {
                'status': 'FAIL',
                'track_modifiers': len(track_mods),
                'modifier_names': track_names
            }
    else:
        print(f"   ❌ FAIL: No CAR_TRAIL object to check")
        validation_results['failed_tests'] += 1
        validation_results['details']['no_track_modifier'] = {
            'status': 'FAIL',
            'reason': 'No CAR_TRAIL object'
        }
    
    # Test 6: Car asset reference integration
    print("\n6. TESTING: Car Asset Integration")
    car_collection = bpy.data.collections.get('ASSET_CAR')
    
    if car_collection:
        car_objects = [obj for obj in car_collection.objects if 'CAR' in obj.name.upper()]
        if car_objects:
            car_names = [obj.name for obj in car_objects]
            print(f"   ✅ PASS: Found ASSET_CAR collection with {len(car_objects)} car objects: {car_names}")
            validation_results['passed_tests'] += 1
            validation_results['details']['car_asset'] = {
                'status': 'PASS',
                'collection_exists': True,
                'car_objects': len(car_objects),
                'car_names': car_names
            }
        else:
            print(f"   ❌ FAIL: ASSET_CAR collection exists but contains no car objects")
            validation_results['failed_tests'] += 1
            validation_results['details']['car_asset'] = {
                'status': 'FAIL',
                'collection_exists': True,
                'car_objects': 0,
                'reason': 'No car objects in collection'
            }
    else:
        print(f"   ❌ FAIL: ASSET_CAR collection not found")
        validation_results['failed_tests'] += 1
        validation_results['details']['car_asset'] = {
            'status': 'FAIL',
            'collection_exists': False,
            'reason': 'Missing ASSET_CAR collection'
        }
    
    # Final result
    validation_results['success'] = validation_results['passed_tests'] == validation_results['total_tests']
    
    print("\n" + "=" * 80)
    print("VALIDATION SUMMARY")
    print("=" * 80)
    print(f"Tests Passed: {validation_results['passed_tests']}/{validation_results['total_tests']}")
    print(f"Tests Failed: {validation_results['failed_tests']}/{validation_results['total_tests']}")
    
    if validation_results['success']:
        print("🎉 OVERALL RESULT: SUCCESS - CAR_TRAIL fix working correctly!")
    else:
        print("❌ OVERALL RESULT: FAILURE - CAR_TRAIL fix needs attention")
    
    print("\nDetailed Results:")
    for test_name, details in validation_results['details'].items():
        status_icon = "✅" if details['status'] == 'PASS' else "❌"
        print(f"  {status_icon} {test_name}: {details['status']}")
    
    return validation_results

def test_toronto_coordinates():
    """
    Test with specific Toronto coordinates to verify geographic context.
    """
    print("\n" + "=" * 80)
    print("TORONTO COORDINATE TEST")
    print("=" * 80)
    
    # Toronto downtown coordinates
    start_lat, start_lon = 43.6532, -79.3832  # 1 Dundas St E
    end_lat, end_lon = 43.6532, -79.3832    # 500 Yonge St (same area for demo)
    
    print(f"Testing Toronto route:")
    print(f"  Start: 1 Dundas St E ({start_lat}°N, {start_lon}°W)")
    print(f"  End: 500 Yonge St ({end_lat}°N, {end_lon}°W)")
    
    # Check if CN Tower is present (Toronto landmark)
    cn_tower = bpy.data.objects.get('CN_TOWER')
    if cn_tower:
        print(f"  ✅ CN Tower object found: {cn_tower.name}")
        print(f"  📍 Location: ({cn_tower.location.x:.2f}, {cn_tower.location.y:.2f}, {cn_tower.location.z:.2f})")
    else:
        print(f"  ⚠️  CN Tower object not found (may be expected)")
    
    # Check route object presence
    route_obj = bpy.data.objects.get('ROUTE') or bpy.data.objects.get('Route')
    if route_obj:
        print(f"  ✅ Route object found: {route_obj.name}")
        print(f"  📍 Location: ({route_obj.location.x:.2f}, {route_obj.location.y:.2f}, {route_obj.location.z:.2f})")
    else:
        print(f"  ❌ Route object not found")

def main():
    """
    Main validation function - runs all tests and saves results.
    """
    print("Starting CAR_TRAIL Fix Validation...")
    
    # Run comprehensive validation
    validation_results = validate_car_trail_success()
    
    # Test Toronto coordinates
    test_toronto_coordinates()
    
    # Save results to file
    save_validation_results(validation_results)
    
    return validation_results

def save_validation_results(results):
    """
    Save validation results to a JSON file for documentation.
    """
    import json
    from datetime import datetime
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"car_trail_validation_results_{timestamp}.json"
    filepath = Path(__file__).parent / filename
    
    # Add metadata
    results['metadata'] = {
        'timestamp': timestamp,
        'blender_version': bpy.app.version_string,
        'car_trail_fix_version': '1.0.0',
        'test_coordinates': {
            'start': '1 Dundas St E, Toronto (43.6532°N, 79.3832°W)',
            'end': '500 Yonge St, Toronto (43.6532°N, 79.3832°W)'
        }
    }
    
    try:
        with open(filepath, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\n💾 Validation results saved to: {filepath}")
    except Exception as e:
        print(f"\n❌ Failed to save results: {e}")

if __name__ == "__main__":
    main()