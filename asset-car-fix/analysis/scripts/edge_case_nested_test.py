
import bpy
import json
import mathutils
import traceback

"""
Test: edge_case_nested
Description: Deeply nested parent-child hierarchies
Expected Result: FAIL_NESTED_BROKEN
Parent Clearing: True
"""

def log_debug(message: str, level: str = "INFO"):
    print(f"[EDGE_CASE_NESTED] [{level}] {message}")

def create_test_objects():
    """Create test objects with parent-child hierarchy"""
    log_debug("Creating test objects...")

    # Clear existing objects
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)

    objects = {}

    # Create car body (root)
    bpy.ops.mesh.primitive_cube_add(location=(0, 0, 1), size=(2, 4, 1))
    car_body = bpy.context.active_object
    car_body.name = "CAR_BODY"
    objects["car_body"] = car_body

    # Create taxi sign (child of car body)
    bpy.ops.mesh.primitive_cube_add(location=(0, 0, 2.5), size=(1.5, 0.2, 0.3))
    taxi_sign = bpy.context.active_object
    taxi_sign.name = "TAXI_SIGN"
    taxi_sign.parent = car_body
    objects["taxi_sign"] = taxi_sign

    # Create taxi light (child of taxi sign)
    bpy.ops.mesh.primitive_uv_sphere_add(location=(0, 0, 2.7), radius=0.15)
    taxi_light = bpy.context.active_object
    taxi_light.name = "TAXI_LIGHT"
    taxi_light.parent = taxi_sign
    objects["taxi_light"] = taxi_light

    # Create wheels (children of car body)
    wheel_positions = [
        (0.8, 1.5, 0.3),   # front left
        (-0.8, 1.5, 0.3),  # front right
        (0.8, -1.5, 0.3),  # rear left
        (-0.8, -1.5, 0.3)  # rear right
    ]

    for i, pos in enumerate(wheel_positions):
        bpy.ops.mesh.primitive_cylinder_add(
            location=pos,
            radius=0.3,
            depth=0.2,
            rotation=(1.5708, 0, 0)
        )
        wheel = bpy.context.active_object
        wheel.name = f"WHEEL_{i}"
        wheel.parent = car_body
        objects[f"wheel_{i}"] = wheel

    log_debug(f"Created {len(objects)} test objects")
    return objects

def capture_hierarchy(objects):
    """Capture current hierarchy state"""
    hierarchy = {}
    for name, obj in objects.items():
        hierarchy[name] = {
            'parent': obj.parent.name if obj.parent else None,
            'children': [child.name for child in obj.children if child.name in [o.name for o in objects.values()]]
        }
    return hierarchy

def capture_transforms(objects):
    """Capture current transforms"""
    transforms = {}
    for name, obj in objects.items():
        transforms[name] = {
            'location': list(obj.location),
            'rotation_euler': list(obj.rotation_euler),
            'scale': list(obj.scale)
        }
    return transforms

def apply_workflow(objects, parent_clearing):
    """Apply the specified workflow"""
    log_debug(f"Applying workflow with parent_clearing={parent_clearing}")

    if parent_clearing:
        # Simulate broken workflow that clears parents
        log_debug("Applying BROKEN workflow (clearing parents)")
        for name, obj in objects.items():
            if obj.parent:
                log_debug(f"Clearing parent for {obj.name}")
                obj.parent = None
                obj.matrix_parent_inverse = mathutils.Matrix.Identity(4)

        # Move car independently
        car_body = objects["car_body"]
        car_body.location = (5, 5, 1)
        car_body.rotation_euler = (0, 0, 0.785)  # 45 degrees
    else:
        # Simulate fixed workflow that preserves hierarchy
        log_debug("Applying FIXED workflow (preserving parents)")
        car_body = objects["car_body"]
        car_body.location = (5, 5, 1)
        car_body.rotation_euler = (0, 0, 0.785)  # 45 degrees
        # Children follow automatically

def validate_results(hierarchy_before, hierarchy_after, expected_result):
    """Validate test results"""
    log_debug("Validating results...")

    validation = {
        'parenting_preserved': True,
        'issues': []
    }

    # Check if parenting is preserved
    for name, before_data in hierarchy_before.items():
        if name in hierarchy_after:
            after_data = hierarchy_after[name]
            if before_data['parent'] != after_data['parent']:
                validation['parenting_preserved'] = False
                validation['issues'].append(
                    f"{name} parent changed from {before_data['parent']} to {after_data['parent']}"
                )

    # Determine if test passed based on expected result
    if expected_result.startswith('PASS'):
        if expected_result == 'PASS_PARENTING_PRESERVED':
            test_passed = validation['parenting_preserved']
        else:
            test_passed = True  # PASS_NO_CHANGE
    elif expected_result.startswith('FAIL'):
        test_passed = not validation['parenting_preserved']
    else:
        test_passed = validation['parenting_preserved']

    validation['test_passed'] = test_passed
    return validation

def main():
    """Main test execution"""
    log_debug("Starting test execution...")

    result = {
        'success': False,
        'error_message': None,
        'hierarchy_before': None,
        'hierarchy_after': None,
        'transforms_before': None,
        'transforms_after': None,
        'validation': None,
        'test_config': {'description': 'Deeply nested parent-child hierarchies', 'parent_clearing': True, 'expected_result': 'FAIL_NESTED_BROKEN'}
    }

    try:
        # Create test objects
        objects = create_test_objects()

        # Capture initial state
        hierarchy_before = capture_hierarchy(objects)
        transforms_before = capture_transforms(objects)
        result['hierarchy_before'] = hierarchy_before
        result['transforms_before'] = transforms_before

        # Apply workflow
        apply_workflow(objects, True)

        # Capture final state
        hierarchy_after = capture_hierarchy(objects)
        transforms_after = capture_transforms(objects)
        result['hierarchy_after'] = hierarchy_after
        result['transforms_after'] = transforms_after

        # Validate results
        validation = validate_results(
            hierarchy_before, hierarchy_after,
            "FAIL_NESTED_BROKEN"
        )
        result['validation'] = validation
        result['success'] = validation['test_passed']

        log_debug(f"Test completed. Success: {result['success']}")
        if validation['issues']:
            for issue in validation['issues']:
                log_debug(f"Issue: {issue}", "WARNING")

    except Exception as e:
        result['success'] = False
        result['error_message'] = f"Exception: {str(e)}\n{traceback.format_exc()}"
        log_debug(f"Test failed: {e}", "ERROR")

    # Output results
    print("TEST_RESULT_JSON_START")
    print(json.dumps(result, indent=2))
    print("TEST_RESULT_JSON_END")

    return result['success']

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
