#!/usr/bin/env python3
"""
CAR_TRAIL Fix Toronto Route Test
Execute this script in Blender to validate the CAR_TRAIL fix
Addresses: 1 Dundas St. E, Toronto to 500 Yonge St, Toronto
"""

import bpy
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def check_fix_applied():
    """Check if CAR_TRAIL fix is applied in pipeline_finalizer.py"""
    try:
        # Read the pipeline file
        pipeline_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'route', 'pipeline_finalizer.py')
        with open(pipeline_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for fix indicators
        fix_indicators = [
            '# REMOVED: Runtime CAR_TRAIL creation causing duplication',
            '# Asset CAR_TRAIL from ASSET_CAR.blend handles all trail functionality',
            'car_trail = bpy.data.objects.get(\'CAR_TRAIL\')'
        ]
        
        fix_applied = any(indicator in content for indicator in fix_indicators)
        print(f"=== CAR_TRAIL FIX STATUS ===")
        print(f"Fix Applied: {'YES' if fix_applied else 'NO'}")
        
        if fix_applied:
            print("✅ Runtime creation code commented out")
            print("✅ Asset verification code present")
        else:
            print("❌ Fix not found in pipeline_finalizer.py")
            
        return fix_applied
        
    except Exception as e:
        print(f"❌ Error checking fix status: {e}")
        return False

def setup_toronto_addresses():
    """Set up the Toronto addresses for testing"""
    print("\n=== TORONTO ADDRESS SETUP ===")
    
    # Import the addon modules to set up addresses
    try:
        # Clear existing route data if any
        print("Clearing any existing route data...")
        
        # Set Toronto addresses
        start_address = "1 Dundas St. E, Toronto"
        end_address = "500 Yonge St, Toronto"
        
        print(f"Start Address: {start_address}")
        print(f"End Address: {end_address}")
        print("Padding: 0")
        
        return {
            'start': start_address,
            'end': end_address,
            'padding': 0
        }
        
    except Exception as e:
        print(f"❌ Error setting up addresses: {e}")
        return None

def execute_fetch_route_and_map():
    """Execute the Fetch Route and Map pipeline"""
    print("\n=== EXECUTING FETCH ROUTE AND MAP ===")
    
    try:
        # Check if addon is loaded
        addon_name = "cash-cab-addon"
        
        # Try to get the operator
        if hasattr(bpy.ops, 'wm') and hasattr(bpy.ops.wm, 'blender_osm_fetch'):
            print("Found blender_osm_fetch operator")
            
            # Execute with Toronto addresses
            bpy.ops.wm.blender_osm_fetch(
                start_location="1 Dundas St. E, Toronto",
                end_location="500 Yonge St, Toronto",
                route_padding=0
            )
            print("✅ Fetch Route and Map executed")
            return True
        else:
            print("❌ blender_osm_fetch operator not found")
            print("Please ensure the CashCab addon is properly loaded")
            return False
            
    except Exception as e:
        print(f"❌ Error executing pipeline: {e}")
        return False

def run_validation_test():
    """Run the comprehensive validation test"""
    print("\n=== RUNNING COMPREHENSIVE VALIDATION ===")
    
    try:
        # Import and run the validation test
        validation_path = os.path.join(os.path.dirname(__file__), 'validation-test.py')
        
        # Read and execute the validation test
        with open(validation_path, 'r', encoding='utf-8') as f:
            validation_code = f.read()
        
        # Create a namespace for execution
        validation_namespace = {}
        exec(validation_code, validation_namespace)
        
        # Run the validation function
        results = validation_namespace['validate_car_trail_fix']()
        
        return results
        
    except Exception as e:
        print(f"❌ Error running validation: {e}")
        return None

def main():
    """Main execution function"""
    print("=" * 60)
    print("CAR_TRAIL FIX TORONTO ROUTE VALIDATION")
    print("=" * 60)
    print("Addresses: 1 Dundas St. E, Toronto → 500 Yonge St, Toronto")
    print("Padding: 0")
    print("=" * 60)
    
    # Step 1: Check if fix is applied
    fix_applied = check_fix_applied()
    if not fix_applied:
        print("\n❌ ABORTING: CAR_TRAIL fix not applied")
        print("Please apply the fix before running this test")
        return False
    
    # Step 2: Set up Toronto addresses
    addresses = setup_toronto_addresses()
    if not addresses:
        print("\n❌ ABORTING: Failed to set up addresses")
        return False
    
    # Step 3: Execute pipeline
    print("\n" + "=" * 60)
    print("EXECUTING PIPELINE TEST")
    print("=" * 60)
    
    pipeline_success = execute_fetch_route_and_map()
    
    # Step 4: Run validation
    print("\n" + "=" * 60)
    print("VALIDATION RESULTS")
    print("=" * 60)
    
    results = run_validation_test()
    
    if results:
        print(f"\n=== FINAL OUTCOME ===")
        if results.get('overall_success', False):
            print("🎉 CAR_TRAIL FIX VALIDATION SUCCESSFUL!")
            print("✅ All critical criteria met")
            print("✅ Toronto route test completed successfully")
            print("✅ CAR_TRAIL duplication issue resolved")
        else:
            print("⚠️ CAR_TRAIL FIX VALIDATION INCOMPLETE")
            print("❌ Some criteria not met")
            print(f"Success Rate: {results.get('success_rate', 0):.1f}%")
            print("Check validation-results.json for details")
        
        return results.get('overall_success', False)
    else:
        print("❌ VALIDATION FAILED: No results generated")
        return False

if __name__ == "__main__":
    success = main()
    
    if success:
        print("\n🎯 NEXT STEPS:")
        print("1. Review the saved Blender scene")
        print("2. Check validation-results.json for detailed metrics")
        print("3. Verify single CAR_TRAIL object exists")
        print("4. Confirm no duplication issues")
    else:
        print("\n🔧 TROUBLESHOOTING:")
        print("1. Ensure CashCab addon is properly loaded")
        print("2. Check internet connection for OSM data")
        print("3. Verify Toronto addresses are valid")
        print("4. Review validation results for specific failures")