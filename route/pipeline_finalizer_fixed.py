# Read the original file and create a fixed version
import re

with open('pipeline_finalizer.py', 'r') as f:
    content = f.read()

# Pattern to match the problematic runtime creation
pattern = r'    try:\s+trace_obj = _build_car_trail_from_route\(scene\)\s+if trace_obj:\s+result\["car_trail"\] = trace_obj\.name\s+except Exception as exc:\s+print\(f"\[FP\[CAR\] WARN car trail build failed: \{exc\}"\)'

# Replacement with the fix
replacement = '''# REMOVED: Runtime CAR_TRAIL creation causing duplication
    # Asset CAR_TRAIL from ASSET_CAR.blend handles all trail functionality
    # try:
    #     trace_obj = _build_car_trail_from_route(scene)
    #     if trace_obj:
    #         result["car_trail"] = trace_obj.name
    # except Exception as exc:
    #     print(f"[FP][CAR] WARN car trail build failed: {exc}")

    # Verify asset CAR_TRAIL exists and is configured
    car_trail = bpy.data.objects.get('CAR_TRAIL')
    if car_trail:
        result["car_trail"] = car_trail.name
        print(f"[FP][CAR] Using asset CAR_TRAIL: {car_trail.name}")
    else:
        print("[FP][CAR] ERROR: Asset CAR_TRAIL not found")'''

# Apply the fix
fixed_content = re.sub(pattern, replacement, content, flags=re.MULTILINE | re.DOTALL)

# Write the fixed file
with open('pipeline_finalizer.py', 'w') as f:
    f.write(fixed_content)

print("CAR_TRAIL fix applied successfully")