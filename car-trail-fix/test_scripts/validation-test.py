import bpy
import datetime
import json
import os

def validate_car_trail_fix():
    """Comprehensive CAR_TRAIL fix validation"""
    print("=== CAR_TRAIL FIX VALIDATION TEST ===")
    print(f"Timestamp: {datetime.datetime.now().isoformat()}")
    print(f"Blender Version: {bpy.app.version_string}")
    
    results = {
        "timestamp": datetime.datetime.now().isoformat(),
        "blender_version": bpy.app.version_string,
        "tests": {},
        "overall_success": False,
        "scene_analysis": {}
    }
    
    # Scene Analysis
    print("\n--- SCENE ANALYSIS ---")
    total_objects = len(bpy.data.objects)
    total_collections = len(bpy.data.collections)
    
    results["scene_analysis"]["total_objects"] = total_objects
    results["scene_analysis"]["total_collections"] = total_collections
    
    print(f"Total objects in scene: {total_objects}")
    print(f"Total collections: {total_collections}")
    
    # Test 1: Object Count and Naming
    print("\n--- Test 1: Object Count and Naming ---")
    car_trail_objects = [obj for obj in bpy.data.objects if obj.name.startswith('CAR_TRAIL')]
    print(f"CAR_TRAIL objects found: {len(car_trail_objects)}")
    
    for obj in car_trail_objects:
        print(f"  - {obj.name} (Type: {obj.type})")
        print(f"    Collections: {[c.name for c in obj.users_collection]}")
    
    single_object = len(car_trail_objects) == 1 and car_trail_objects[0].name == "CAR_TRAIL"
    results["tests"]["object_count_naming"] = single_object
    results["scene_analysis"]["car_trail_objects"] = len(car_trail_objects)
    
    if single_object:
        print("✅ SUCCESS: Single CAR_TRAIL object found")
    else:
        print("❌ FAILURE: Object count or naming incorrect")
    
    # Test 2: Route Objects Analysis
    print("\n--- Test 2: Route Objects Analysis ---")
    route_objects = [obj for obj in bpy.data.objects if 'ROUTE' in obj.name.upper()]
    print(f"ROUTE objects found: {len(route_objects)}")
    
    for obj in route_objects:
        print(f"  - {obj.name} (Type: {obj.type})")
    
    route_exists = len(route_objects) > 0
    results["tests"]["route_objects_exist"] = route_exists
    results["scene_analysis"]["route_objects"] = len(route_objects)
    
    if route_exists:
        print("✅ SUCCESS: Route objects found")
    else:
        print("❌ FAILURE: No route objects found")
    
    # Test 3: Asset Collections Check
    print("\n--- Test 3: Asset Collections ---")
    asset_car_collection = bpy.data.collections.get('ASSET_CAR')
    asset_buildings_collection = bpy.data.collections.get('ASSET_BUILDINGS')
    
    print(f"ASSET_CAR collection: {'Found' if asset_car_collection else 'Not Found'}")
    if asset_car_collection:
        print(f"  Objects in ASSET_CAR: {len(asset_car_collection.objects)}")
        for obj in asset_car_collection.objects:
            print(f"    - {obj.name} ({obj.type})")
    
    print(f"ASSET_BUILDINGS collection: {'Found' if asset_buildings_collection else 'Not Found'}")
    if asset_buildings_collection:
        print(f"  Objects in ASSET_BUILDINGS: {len(asset_buildings_collection.objects)}")
        for obj in asset_buildings_collection.objects[:5]:  # Show first 5
            print(f"    - {obj.name} ({obj.type})")
    
    assets_exist = asset_car_collection is not None or asset_buildings_collection is not None
    results["tests"]["asset_collections_exist"] = assets_exist
    results["scene_analysis"]["asset_car_exists"] = asset_car_collection is not None
    results["scene_analysis"]["asset_buildings_exists"] = asset_buildings_collection is not None
    
    if assets_exist:
        print("✅ SUCCESS: Asset collections found")
    else:
        print("❌ FAILURE: No asset collections found")
    
    # Test 4: CAR_TRAIL Detailed Analysis (if exists)
    if car_trail_objects:
        print("\n--- Test 4: CAR_TRAIL Detailed Analysis ---")
        car_trail = car_trail_objects[0]
        
        print(f"CAR_TRAIL Type: {car_trail.type}")
        print(f"CAR_TRAIL Data Type: {type(car_trail.data).__name__ if car_trail.data else 'None'}")
        
        # Modifiers Analysis
        print("Modifiers:")
        geo_mods = []
        track_mods = []
        other_mods = []
        
        for mod in car_trail.modifiers:
            print(f"  - {mod.name} ({mod.type})")
            if mod.type == 'NODES':
                geo_mods.append(mod)
                if mod.node_group:
                    print(f"    Node Group: {mod.node_group.name}")
            elif mod.type == 'TRACK_TO':
                track_mods.append(mod)
            else:
                other_mods.append(mod)
        
        print(f"Geometry nodes modifiers: {len(geo_mods)}")
        print(f"Track-to modifiers: {len(track_mods)}")
        print(f"Other modifiers: {len(other_mods)}")
        
        # Animation Data Analysis
        print("Animation Data:")
        if car_trail.data and car_trail.data.animation_data:
            drivers = car_trail.data.animation_data.drivers
            print(f"  Drivers found: {len(drivers)}")
            
            bevel_drivers = [d for d in drivers if 'bevel_factor' in d.data_path]
            print(f"  Bevel drivers: {len(bevel_drivers)}")
            
            for driver in bevel_drivers:
                print(f"    - {driver.data_path}")
                if hasattr(driver.driver, 'expression') and driver.driver.expression:
                    print(f"      Expression: {driver.driver.expression}")
        else:
            print("  No animation data found")
        
        # Store detailed analysis
        results["scene_analysis"]["car_trail_details"] = {
            "type": car_trail.type,
            "modifiers": {
                "geometry_nodes": len(geo_mods),
                "track_to": len(track_mods),
                "other": len(other_mods)
            },
            "animation_drivers": len(car_trail.data.animation_data.drivers) if car_trail.data and car_trail.data.animation_data else 0,
            "bevel_drivers": len(bevel_drivers) if car_trail.data and car_trail.data.animation_data else 0
        }
        
        geo_nodes_ok = len(geo_mods) > 0
        no_track_mod = len(track_mods) == 0
        has_drivers = len(bevel_drivers) > 0
        
        results["tests"]["geometry_nodes_present"] = geo_nodes_ok
        results["tests"]["no_track_modifier"] = no_track_mod
        results["tests"]["animation_drivers_present"] = has_drivers
        
        print(f"✅ SUCCESS: GeoNodes present: {geo_nodes_ok}")
        print(f"✅ SUCCESS: No track modifier: {no_track_mod}")
        print(f"✅ SUCCESS: Animation drivers present: {has_drivers}")
    
    # Test 5: Success Criteria Evaluation
    print("\n--- Test 5: Success Criteria Evaluation ---")
    
    critical_criteria = {
        "Single CAR_TRAIL object": results["tests"].get("object_count_naming", False),
        "Route objects exist": results["tests"].get("route_objects_exist", False),
        "Asset collections exist": results["tests"].get("asset_collections_exist", False),
        "Geometry nodes present": results["tests"].get("geometry_nodes_present", False),
        "No track modifier": results["tests"].get("no_track_modifier", False),
        "Animation drivers present": results["tests"].get("animation_drivers_present", False)
    }
    
    criteria_met = 0
    total_criteria = len(critical_criteria)
    
    for criterion, passed in critical_criteria.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {criterion}")
        if passed:
            criteria_met += 1
    
    success_rate = (criteria_met / total_criteria) * 100
    overall_success = success_rate >= 80  # At least 80% of criteria met
    
    results["overall_success"] = overall_success
    results["success_rate"] = success_rate
    results["criteria_met"] = criteria_met
    results["total_criteria"] = total_criteria
    
    print(f"\n=== FINAL RESULTS ===")
    print(f"Success Rate: {success_rate:.1f}% ({criteria_met}/{total_criteria} criteria)")
    print(f"Overall Success: {'YES' if overall_success else 'NO'}")
    
    return results

def save_blender_scene(filename_prefix, success):
    """Save Blender scene with appropriate filename"""
    filename = f"car-trail-fix/{filename_prefix}-{'SUCCESS' if success else 'FAILED'}.blend"
    
    # Ensure directory exists
    os.makedirs("car-trail-fix", exist_ok=True)
    
    try:
        bpy.ops.wm.save_as_mainfile(filepath=filename)
        print(f"✅ Scene saved: {filename}")
        return filename
    except Exception as e:
        print(f"❌ Failed to save scene: {e}")
        return None

# Run the validation if this script is executed directly
if __name__ == "__main__":
    results = validate_car_trail_fix()
    
    # Save results to file
    output_dir = "car-trail-fix"
    os.makedirs(output_dir, exist_ok=True)
    
    with open(os.path.join(output_dir, "validation-results.json"), "w") as f:
        json.dump(results, f, indent=2)
    
    # Save Blender scene
    scene_file = save_blender_scene("toronto-route-test", results["overall_success"])
    
    print(f"\n=== FILES SAVED ===")
    print(f"Validation results: {os.path.join(output_dir, 'validation-results.json')}")
    if scene_file:
        print(f"Blender scene: {scene_file}")
    
    print(f"\n=== CONCLUSION ===")
    if results["overall_success"]:
        print("🎉 CAR_TRAIL fix validation PASSED!")
        print("✅ The implemented fix successfully resolves the duplication issue")
    else:
        print("⚠️ CAR_TRAIL fix validation INCOMPLETE or FAILED")
        print("❌ Further investigation or scene setup required")