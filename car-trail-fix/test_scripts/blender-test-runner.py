"""
Blender Test Runner for CAR_TRAIL Fix
Execute this in Blender's scripting console or command line
"""

import bpy
import sys
import os
import datetime

# Ensure we're in the correct directory
script_dir = os.path.dirname(os.path.abspath(__file__))
addon_dir = os.path.dirname(script_dir)

def test_environment_setup():
    """Set up the test environment"""
    print("=== ENVIRONMENT SETUP ===")
    print(f"Script directory: {script_dir}")
    print(f"Addon directory: {addon_dir}")
    print(f"Blender version: {bpy.app.version_string}")
    
    # Clear the scene for clean testing
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    print("✅ Scene cleared")
    
    return True

def run_car_trail_test():
    """Execute the complete CAR_TRAIL test"""
    print("\n=== CAR_TRAIL FIX TORONTO TEST EXECUTION ===")
    print(f"Timestamp: {datetime.datetime.now().isoformat()}")
    
    try:
        # Import the test runner
        sys.path.insert(0, script_dir)
        import execute_toronto_test
        
        # Run the main test
        success = execute_toronto_test.main()
        
        return success
        
    except Exception as e:
        print(f"❌ Error in CAR_TRAIL test: {e}")
        import traceback
        traceback.print_exc()
        return False

def create_summary_report(success):
    """Create a comprehensive summary report"""
    print("\n=== CREATING SUMMARY REPORT ===")
    
    report = {
        "test_timestamp": datetime.datetime.now().isoformat(),
        "blender_version": bpy.app.version_string,
        "test_type": "Toronto Route CAR_TRAIL Fix Validation",
        "addresses": {
            "start": "1 Dundas St. E, Toronto",
            "end": "500 Yonge St, Toronto",
            "padding": 0
        },
        "test_result": "SUCCESS" if success else "FAILED",
        "scene_summary": {},
        "files_created": []
    }
    
    # Analyze scene
    total_objects = len(bpy.data.objects)
    car_trail_objects = [obj for obj in bpy.data.objects if obj.name.startswith('CAR_TRAIL')]
    
    report["scene_summary"] = {
        "total_objects": total_objects,
        "car_trail_objects": len(car_trail_objects),
        "car_trail_names": [obj.name for obj in car_trail_objects]
    }
    
    # Save report
    report_path = os.path.join(script_dir, "test-summary-report.json")
    
    import json
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    report["files_created"].append("test-summary-report.json")
    print(f"✅ Summary report saved: {report_path}")
    
    return report

if __name__ == "__main__":
    print("=" * 80)
    print("CAR_TRAIL FIX TORONTO ROUTE VALIDATION - BLENDER RUNNER")
    print("=" * 80)
    
    # Run the test
    test_environment_setup()
    success = run_car_trail_test()
    
    # Create summary
    summary = create_summary_report(success)
    
    # Final status
    print("\n" + "=" * 80)
    print("FINAL TEST RESULT")
    print("=" * 80)
    
    if success:
        print("🎉 CAR_TRAIL FIX VALIDATION PASSED!")
        print("✅ Toronto route test completed successfully")
        print("✅ All critical success criteria met")
        print("✅ CAR_TRAIL duplication issue resolved")
        print("✅ Ready for production use")
    else:
        print("⚠️ CAR_TRAIL FIX VALIDATION FAILED")
        print("❌ Please review the detailed logs")
        print("❌ Check scene setup and addon configuration")
    
    print(f"\nFiles created in {script_dir}:")
    for file_created in summary.get("files_created", []):
        print(f"  - {file_created}")
    
    print(f"\nTimestamp: {datetime.datetime.now().isoformat()}")
    print("=" * 80)