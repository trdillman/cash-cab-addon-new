"""
Blender Test Script Generator

Creates Python scripts that run inside Blender to test the car import workflow
and validate parent-child relationships.
"""

import json
from typing import Dict, Any, List
from pathlib import Path

class BlenderTestScriptGenerator:
    """Generates Blender Python scripts for testing car import workflows"""

    def __init__(self):
        self.template = self.get_base_template()

    def generate_test_script(self, test_name: str, test_config: Dict[str, Any], debug_level: str = "verbose") -> str:
        """Generate a complete Blender test script"""

        # Core test logic
        test_logic = self.generate_test_logic(test_name, test_config)

        # Combine template with test-specific logic
        script = self.template.format(
            test_name=test_name,
            test_config=json.dumps(test_config, indent=4),
            debug_level=debug_level,
            test_logic=test_logic
        )

        return script

    def get_base_template(self) -> str:
        """Base Blender script template"""

        return '''
import bpy
import bmesh
import json
import traceback
import mathutils
from typing import Dict, Any, List, Optional

# Test Configuration
TEST_NAME = "{test_name}"
TEST_CONFIG = {test_config}
DEBUG_LEVEL = "{debug_level}"

class CarImportTester:
    """Test car import parenting in Blender environment"""

    def __init__(self):
        self.test_objects = {}
        self.hierarchy_before = {}
        self.hierarchy_after = {}
        self.transforms_before = {}
        self.transforms_after = {}
        self.debug_messages = []

    def log_debug(self, message: str, level: str = "INFO"):
        """Log debug message"""
        if DEBUG_LEVEL in ["verbose", level]:
            print(f"[CAR_TEST] [{level}] {{message}}")
        self.debug_messages.append(f"{{level}}: {{message}}")

    def create_test_car_asset(self) -> str:
        """Create a test car asset with parent-child hierarchy"""
        self.log_debug("Creating test car asset...")

        # Clear existing objects
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete(use_global=False)

        # Create car body (main parent)
        bpy.ops.mesh.primitive_cube_add(location=(0, 0, 1), size=(2, 4, 1))
        car_body = bpy.context.active_object
        car_body.name = "CAR_BODY"
        self.test_objects["car_body"] = car_body

        # Create taxi sign (child of car body)
        bpy.ops.mesh.primitive_cube_add(location=(0, 0, 2.5), size=(1.5, 0.2, 0.3))
        taxi_sign = bpy.context.active_object
        taxi_sign.name = "TAXI_SIGN"
        taxi_sign.parent = car_body
        self.test_objects["taxi_sign"] = taxi_sign

        # Create taxi light (child of taxi sign)
        bpy.ops.mesh.primitive_uv_sphere_add(location=(0, 0, 2.7), radius=0.15)
        taxi_light = bpy.context.active_object
        taxi_light.name = "TAXI_LIGHT"
        taxi_light.parent = taxi_sign
        self.test_objects["taxi_light"] = taxi_light

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
                rotation=(1.5708, 0, 0)  # 90 degrees on X axis
            )
            wheel = bpy.context.active_object
            wheel.name = f"WHEEL_{{['FRONT_LEFT', 'FRONT_RIGHT', 'REAR_LEFT', 'REAR_RIGHT'][i]}}"
            wheel.parent = car_body
            self.test_objects[f"wheel_{{i}}"] = wheel

        self.log_debug(f"Created {{len(self.test_objects)}} test objects")
        return car_body.name

    def capture_hierarchy_state(self) -> Dict[str, Any]:
        """Capture current parent-child hierarchy"""
        hierarchy = {{}}

        for obj in bpy.data.objects:
            if obj.name.startswith(('CAR_', 'TAXI_', 'WHEEL_')):
                hierarchy[obj.name] = {{
                    'parent': obj.parent.name if obj.parent else None,
                    'children': [child.name for child in obj.children if child.name.startswith(('CAR_', 'TAXI_', 'WHEEL_'))],
                    'type': obj.type
                }}

        return hierarchy

    def capture_transforms(self) -> Dict[str, Any]:
        """Capture transform data for all test objects"""
        transforms = {{}}

        for obj in bpy.data.objects:
            if obj.name.startswith(('CAR_', 'TAXI_', 'WHEEL_')):
                transforms[obj.name] = {{
                    'location': list(obj.location),
                    'rotation_euler': list(obj.rotation_euler),
                    'scale': list(obj.scale),
                    'matrix_world': [list(row) for row in obj.matrix_world],
                    'matrix_parent_inverse': [list(row) for row in obj.matrix_parent_inverse] if obj.parent else None
                }}

        return transforms

    def simulate_broken_workflow(self):
        """Simulate current broken workflow that clears parents"""
        self.log_debug("Simulating BROKEN workflow...")

        # This mimics the problematic code from route/anim.py:617
        car_obj = self.test_objects.get("car_body")
        if car_obj:
            self.log_debug(f"Clearing parent for {{car_obj.name}} (mimicking route/anim.py:617)")
            car_obj.parent = None
            car_obj.matrix_parent_inverse = mathutils.Matrix.Identity(4)

        # Clear parents for all children too (mimicking fetch_operator behavior)
        for name, obj in self.test_objects.items():
            if name != "car_body" and obj.parent:
                self.log_debug(f"Clearing parent for {{obj.name}}")
                obj.parent = None
                obj.matrix_parent_inverse = mathutils.Matrix.Identity(4)

    def simulate_fixed_workflow(self):
        """Simulate proposed fix that preserves parent relationships"""
        self.log_debug("Simulating FIXED workflow...")

        # Only transform the root object, preserve hierarchy
        car_obj = self.test_objects.get("car_body")
        if car_obj:
            self.log_debug("Preserving parent relationships, only transforming root")
            # Move car to new position but keep hierarchy intact
            car_obj.location = (5, 5, 1)  # New location
            car_obj.rotation_euler = (0, 0, 0.785)  # 45 degree rotation

    def validate_parenting(self) -> Dict[str, Any]:
        """Validate that parenting relationships are correct"""
        validation = {{
            'passed': True,
            'issues': [],
            'hierarchy_correct': True
        }}

        expected_hierarchy = {{
            'CAR_BODY': {{'parent': None, 'children': ['TAXI_SIGN']}},
            'TAXI_SIGN': {{'parent': 'CAR_BODY', 'children': ['TAXI_LIGHT']}},
            'TAXI_LIGHT': {{'parent': 'TAXI_SIGN', 'children': []}},
            # Wheels should also be children of CAR_BODY
        }}

        for obj_name, expected in expected_hierarchy.items():
            if obj_name in bpy.data.objects:
                obj = bpy.data.objects[obj_name]
                actual_parent = obj.parent.name if obj.parent else None

                if actual_parent != expected['parent']:
                    validation['passed'] = False
                    validation['hierarchy_correct'] = False
                    validation['issues'].append(
                        f"{{obj_name}}: expected parent {{expected['parent']}, got {{actual_parent}}"
                    )

        return validation

    def run_test(self) -> Dict[str, Any]:
        """Run the complete test"""
        result = {{
            'success': False,
            'error_message': None,
            'hierarchy_before': None,
            'hierarchy_after': None,
            'transforms_before': None,
            'transforms_after': None,
            'validation': None,
            'debug_messages': self.debug_messages
        }}

        try:
            # Step 1: Create test asset
            car_name = self.create_test_car_asset()
            self.log_debug(f"Created test car: {{car_name}}")

            # Step 2: Capture initial state
            self.hierarchy_before = self.capture_hierarchy_state()
            self.transforms_before = self.capture_transforms()
            self.log_debug("Captured initial state")

            # Step 3: Apply test workflow
            if TEST_CONFIG.get('parent_clearing', False):
                self.simulate_broken_workflow()
            else:
                self.simulate_fixed_workflow()

            # Step 4: Capture final state
            self.hierarchy_after = self.capture_hierarchy_state()
            self.transforms_after = self.capture_transforms()
            self.log_debug("Captured final state")

            # Step 5: Validate results
            validation = self.validate_parenting()
            self.log_debug(f"Validation result: {{validation}}")

            # Step 6: Determine success
            expected_result = TEST_CONFIG.get('expected_result', '')

            if expected_result.startswith('PASS'):
                result['success'] = validation['passed']
            elif expected_result.startswith('FAIL'):
                result['success'] = not validation['passed']
            else:
                result['success'] = validation['passed']

            if not result['success']:
                result['error_message'] = f"Test validation failed: {{validation.get('issues', [])}}"

            # Add captured data
            result['hierarchy_before'] = self.hierarchy_before
            result['hierarchy_after'] = self.hierarchy_after
            result['transforms_before'] = self.transforms_before
            result['transforms_after'] = self.transforms_after
            result['validation'] = validation

            self.log_debug(f"Test completed. Success: {{result['success']}}")

        except Exception as e:
            result['success'] = False
            result['error_message'] = f"Exception during test: {{str(e)}}\\n{{traceback.format_exc()}}"
            self.log_debug(f"Test failed with exception: {{e}}", "ERROR")

        return result

def main():
    """Main test execution"""
    print(f"Starting Blender test: {{TEST_NAME}}")
    print(f"Test config: {{TEST_CONFIG}}")

    tester = CarImportTester()
    result = tester.run_test()

    # Output results as JSON for parsing by test runner
    print("TEST_RESULT_JSON_START")
    print(json.dumps(result, indent=2))
    print("TEST_RESULT_JSON_END")

    return result['success']

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)

{test_logic}
'''

    def generate_test_logic(self, test_name: str, test_config: Dict[str, Any]) -> str:
        """Generate test-specific logic"""

        if "broken" in test_name:
            return '''
# Broken workflow test - expects parenting to be broken
print("Running BROKEN workflow test...")
# The main test logic is already in the template
# This test should show parent relationships are cleared
'''
        elif "fixed" in test_name:
            return '''
# Fixed workflow test - expects parenting to be preserved
print("Running FIXED workflow test...")
# The main test logic is already in the template
# This test should show parent relationships are maintained
'''
        elif "edge_case" in test_name:
            if "no_parent" in test_name:
                return '''
# Edge case: no parent relationships to break
print("Running NO_PARENT edge case test...")
'''
            elif "nested" in test_name:
                return '''
# Edge case: deeply nested hierarchies
print("Running NESTED edge case test...")
# Create additional nested objects
'''

        return '''
# Standard test logic
print("Running standard test...")
'''


def main():
    """Generate all test scripts"""
    generator = BlenderTestScriptGenerator()

    test_cases = {
        "broken_workflow": {
            "description": "Current workflow that breaks parenting",
            "parent_clearing": True,
            "expected_result": "FAIL_PARENTING_BROKEN"
        },
        "fixed_workflow": {
            "description": "Proposed fix that preserves parenting",
            "parent_clearing": False,
            "expected_result": "PASS_PARENTING_PRESERVED"
        },
        "edge_case_no_parent": {
            "description": "Asset with no parent relationships",
            "parent_clearing": True,
            "expected_result": "PASS_NO_CHANGE"
        },
        "edge_case_nested": {
            "description": "Deeply nested parent-child hierarchies",
            "parent_clearing": True,
            "expected_result": "FAIL_NESTED_BROKEN"
        }
    }

    output_dir = Path("asset-car-fix/scripts")
    output_dir.mkdir(exist_ok=True)

    for test_name, test_config in test_cases.items():
        script_content = generator.generate_test_script(test_name, test_config)
        script_path = output_dir / f"{test_name}_test.py"

        with open(script_path, 'w') as f:
            f.write(script_content)

        print(f"Generated: {script_path}")

if __name__ == "__main__":
    main()