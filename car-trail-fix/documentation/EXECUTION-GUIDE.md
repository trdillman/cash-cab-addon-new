# CAR_TRAIL Fix Toronto Route Test - Execution Guide

## 🎯 OBJECTIVE

Validate the CAR_TRAIL duplication fix using the specified Toronto addresses:
- **Start**: 1 Dundas St. E, Toronto
- **End**: 500 Yonge St, Toronto
- **Padding**: 0

## 📋 FILES CREATED

All testing files are located in the `/car-trail-fix/` directory:

### Core Test Files:
1. **`execute-toronto-test.py`** - Main Toronto route test execution
2. **`validation-test.py`** - Comprehensive CAR_TRAIL validation framework
3. **`blender-test-runner.py`** - Blender execution orchestrator
4. **`EXECUTION-GUIDE.md`** - This file

### Previous Analysis Files:
- **`findings-and-implementation-plan.md`** - Root cause analysis and solution
- **`expected-outcomes.md`** - Success criteria definitions
- **`agent-execution-summary.md`** - Previous execution attempt summary

## 🚀 EXECUTION INSTRUCTIONS

### Method 1: Blender Scripting Console (Recommended)

1. **Open Blender**
2. **Load the CashCab addon** if not already loaded
3. **Open Scripting workspace** (top tabs)
4. **Copy and paste this code** into the Python console:

```python
exec(open(r"C:\Users\Tyler\AppData\Roaming\Blender Foundation\Blender\4.5\scripts\addons\cash-cab-addon\car-trail-fix\blender-test-runner.py").read())
```

5. **Press Enter** to execute

### Method 2: Blender Command Line

1. **Open Command Prompt** or PowerShell
2. **Navigate to Blender directory**
3. **Execute with script**:

```bash
blender.exe --python "C:\Users\Tyler\AppData\Roaming\Blender Foundation\Blender\4.5\scripts\addons\cash-cab-addon\car-trail-fix\blender-test-runner.py"
```

### Method 3: Manual Execution (Debug Mode)

1. **Open Blender**
2. **Load CashCab addon**
3. **Run these commands in Python console**:

```python
# Step 1: Check environment
import bpy
print(f"Objects in scene: {len(bpy.data.objects)}")

# Step 2: Execute Toronto route test
bpy.ops.wm.blender_osm_fetch(
    start_location="1 Dundas St. E, Toronto",
    end_location="500 Yonge St, Toronto", 
    route_padding=0
)

# Step 3: Run validation
exec(open(r"C:\Users\Tyler\AppData\Roaming\Blender Foundation\Blender\4.5\scripts\addons\cash-cab-addon\car-trail-fix\validation-test.py").read())
results = validate_car_trail_fix()

# Step 4: Save scene
bpy.ops.wm.save_as_mainfile(filepath="car-trail-fix/toronto-route-test-result.blend")
```

## ✅ SUCCESS METRICS

### Critical Success Criteria (6 total):

1. **Object Count/Naming** ✅
   - Exactly 1 CAR_TRAIL object
   - Named exactly "CAR_TRAIL" (no .001 suffix)

2. **Route Objects Exist** ✅
   - ROUTE objects present from Fetch Route and Map

3. **Asset Collections** ✅
   - ASSET_CAR collection present
   - ASSET_BUILDINGS collection present

4. **Geometry Nodes** ✅
   - CAR_TRAIL has geometry nodes modifier
   - From ASSET_CAR.blend asset

5. **No Track Modifier** ✅
   - No track-to modifier on CAR_TRAIL

6. **Animation Drivers** ✅
   - Bevel factor drivers present
   - Reference scene car asset

## 📊 EXPECTED RESULTS

### Successful Test:
- **Success Rate**: ≥80% (5/6 criteria met)
- **CAR_TRAIL objects**: 1 (named "CAR_TRAIL")
- **Scene objects**: Multiple (route, assets, collections)
- **No duplication**: CAR_TRAIL.001 not created
- **Files saved**: Validation results, Blender scene

### Failed Test:
- **Success Rate**: <80%
- **Multiple CAR_TRAIL objects** or wrong naming
- **Missing asset collections**
- **No geometry nodes**
- **Track modifier present**

## 🔧 TROUBLESHOOTING

### Common Issues:

1. **Addon Not Loaded**
   ```
   Solution: Enable CashCab addon in Blender preferences
   ```

2. **Internet Connection**
   ```
   Solution: Check internet connection for OSM data fetching
   ```

3. **Invalid Addresses**
   ```
   Solution: Verify Toronto addresses are correct
   ```

4. **Missing Assets**
   ```
   Solution: Ensure ASSET_CAR.blend and ASSET_BUILDINGS.blend exist
   ```

5. **Script Permission**
   ```
   Solution: Run Blender as administrator if needed
   ```

## 📁 OUTPUT FILES

After execution, expect these files in `/car-trail-fix/`:

1. **`validation-results.json`** - Detailed test metrics
2. **`test-summary-report.json`** - Executive summary
3. **`toronto-route-test-SUCCESS.blend`** - Blender scene (if successful)
4. **`toronto-route-test-FAILED.blend`** - Blender scene (if failed)

## 🎯 VALIDATION CHECKLIST

After test execution, verify:

- [ ] Single CAR_TRAIL object exists
- [ ] Named exactly "CAR_TRAIL" (no .001)
- [ ] Has geometry nodes modifier
- [ ] No track-to modifier
- [ ] Animation drivers present
- [ ] Route objects created
- [ ] Asset collections present
- [ ] Success rate ≥80%
- [ ] Scene file saved
- [ ] Validation JSON created

## 📞 NEXT STEPS

### If Test Passes:
1. Review validation-results.json for detailed metrics
2. Open saved Blender scene to verify CAR_TRAIL
3. Test with different addresses for regression
4. Deploy fix to production

### If Test Fails:
1. Review validation-results.json for specific failures
2. Check console logs for error messages
3. Verify fix is applied in pipeline_finalizer.py
4. Re-run with manual debugging enabled

## 🚨 IMPORTANT NOTES

- **Internet Required**: For OSM data fetching
- **Clean Scene**: Test clears existing objects
- **Time**: Allow 2-5 minutes for route fetching
- **Memory**: Large route data may require sufficient RAM
- **Addons**: CashCab addon must be loaded and enabled

## 🎉 SUCCESS INDICATORS

When the fix works correctly, you should see:

```
🎉 CAR_TRAIL FIX VALIDATION PASSED!
✅ Toronto route test completed successfully  
✅ All critical success criteria met
✅ CAR_TRAIL duplication issue resolved
✅ Ready for production use
```

This indicates the CAR_TRAIL duplication fix has been successfully implemented and validated.