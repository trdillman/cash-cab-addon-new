#!/usr/bin/env python3
"""
Apply CAR_TRAIL fix to pipeline_finalizer.py
"""

import os

def apply_car_trail_fix():
    """Apply the CAR_TRAIL duplication fix"""
    
    # Read the current file
    with open('route/pipeline_finalizer.py', 'r') as f:
        lines = f.readlines()
    
    # Find the problematic section and replace it
    fixed_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Look for the start of the problematic try block
        if '    try:' in line and i + 1 < len(lines) and 'trace_obj = _build_car_trail_from_route(scene)' in lines[i + 1]:
            # Found the problematic section, replace it
            fixed_lines.extend([
                '    # REMOVED: Runtime CAR_TRAIL creation causing duplication\n',
                '    # Asset CAR_TRAIL from ASSET_CAR.blend handles all trail functionality\n',
                '    # try:\n',
                '    #     trace_obj = _build_car_trail_from_route(scene)\n',
                '    #     if trace_obj:\n',
                '    #         result["car_trail"] = trace_obj.name\n',
                '    # except Exception as exc:\n',
                '    #     print(f"[FP][CAR] WARN car trail build failed: {exc}")\n',
                '\n',
                '    # Verify asset CAR_TRAIL exists and is configured\n',
                '    car_trail = bpy.data.objects.get(\'CAR_TRAIL\')\n',
                '    if car_trail:\n',
                '        result["car_trail"] = car_trail.name\n',
                '        print(f"[FP][CAR] Using asset CAR_TRAIL: {car_trail.name}")\n',
                '    else:\n',
                '        print("[FP][CAR] ERROR: Asset CAR_TRAIL not found")\n',
                '\n'
            ])
            
            # Skip the original problematic lines (6 lines total)
            i += 6
            continue
            
        fixed_lines.append(line)
        i += 1
    
    # Write the fixed file
    with open('route/pipeline_finalizer.py', 'w') as f:
        f.writelines(fixed_lines)
    
    print("CAR_TRAIL fix applied successfully!")
    return True

if __name__ == "__main__":
    apply_car_trail_fix()