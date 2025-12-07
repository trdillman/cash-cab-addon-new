#!/usr/bin/env python

# Blender Test Execution Script
# This script loads the Blender test and executes it within Blender

import bpy
import sys
import os

def run_car_trail_test():
    """Execute the CAR_TRAIL verification test"""

    # Clear existing Blender data to start fresh
    bpy.ops.wm.read_factory_settings(use_empty=True)

    # Load and execute our test script
    test_script_path = "C:\\Users\\Tyler\\AppData\\Roaming\\Blender Foundation\\Blender\\4.5\\scripts\\addons\\cash-cab-addon\\car-trail-fix\\run_blender_test.py"

    try:
        # Execute the test script
        exec(compile(open(test_script_path).read(), test_script_path, 'exec'))
        return 0
    except Exception as e:
        print(f"Error executing test script: {e}")
        print(f"Test script path: {test_script_path}")
        print(f"Current working directory: {os.getcwd()}")

        # Try to create a simple test scene and run basic checks
        print("Running fallback basic scene analysis...")

        # Basic scene analysis
        car_trail_objects = [obj for obj in bpy.data.objects if obj.name.startswith('CAR_TRAIL')]
        route_objects = [obj for obj in bpy.data.objects if obj.name in ['ROUTE', 'Route']]

        print(f"CAR_TRAIL objects found: {len(car_trail_objects)}")
        print(f"Route objects found: {len(route_objects)}")
        print(f"Total objects: {len(bpy.data.objects)}")

        for obj in car_trail_objects:
            print(f"CAR_TRAIL: {obj.name}, Type: {obj.type}")
            if obj.data and obj.data.animation_data:
                drivers = obj.data.animation_data.drivers
                print(f"  Drivers: {len(drivers)}")
                for driver in drivers:
                    print(f"    - {driver.data_path}")

        # Create minimal test results
        import json
        import datetime

        results = {
            "test_session": {
                "timestamp": datetime.datetime.now().isoformat(),
                "blender_version": bpy.app.version_string,
                "scene_name": bpy.context.scene.name,
                "python_version": sys.version
            },
            "scene_state": {
                "total_objects": len(bpy.data.objects),
                "car_trail_objects": len(car_trail_objects),
                "route_objects": len(route_objects)
            },
            "final_results": {
                "total_tests": 5,
                "passed": 0,
                "failed": 5,
                "success_rate": 0.0,
                "overall_success": False,
                "critical_blocking_issues": ["No test script executed - fallback mode"]
            }
        }

        with open("C:\\Users\\Tyler\\AppData\\Roaming\\Blender Foundation\\Blender\\4.5\\scripts\\addons\\cash-cab-addon\\car-trail-fix\\test-results.json", "w") as f:
            json.dump(results, f, indent=2, default=str)

        return 1

if __name__ == "__main__":
    exit(run_car_trail_test())