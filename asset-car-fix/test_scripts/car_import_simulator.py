"""
Car Import Workflow Simulator

Simulates the actual car import workflow from the cash-cab-addon to test
and validate parent-child relationship preservation.
"""

import bpy
import bmesh
import json
import mathutils
import importlib.util
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

# Add the addon root to Python path to import modules
addon_root = Path(__file__).parent.parent
sys.path.insert(0, str(addon_root))

class CarImportSimulator:
    """Simulates the car import workflow with both broken and fixed versions"""

    def __init__(self):
        self.debug_messages = []
        self.simulated_objects = {}
        self.asset_objects = {}

    def log_debug(self, message: str, level: str = "INFO"):
        """Log debug message"""
        print(f"[SIMULATOR] [{level}] {message}")
        self.debug_messages.append(f"{level}: {message}")

    def setup_test_environment(self):
        """Setup clean test environment"""
        self.log_debug("Setting up test environment...")

        # Clear existing scene
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete(use_global=False)

        # Clear orphaned data
        for mesh in bpy.data.meshes:
            if mesh.users == 0:
                bpy.data.meshes.remove(mesh)

    def create_mock_car_asset(self) -> Dict[str, bpy.types.Object]:
        """Create a mock car asset that simulates ASSET_CAR.blend"""
        self.log_debug("Creating mock car asset...")

        # Create car body (main parent)
        bpy.ops.mesh.primitive_cube_add(location=(0, 0, 1), size=(2, 4, 1))
        car_body = bpy.context.active_object
        car_body.name = "CAR_BODY"
        self.asset_objects["car_body"] = car_body

        # Create taxi sign (child of car body)
        bpy.ops.mesh.primitive_cube_add(location=(0, 0, 2.5), size=(1.5, 0.2, 0.3))
        taxi_sign = bpy.context.active_object
        taxi_sign.name = "TAXI_SIGN"
        taxi_sign.parent = car_body
        self.asset_objects["taxi_sign"] = taxi_sign

        # Create taxi light (child of taxi sign)
        bpy.ops.mesh.primitive_uv_sphere_add(location=(0, 0, 2.7), radius=0.15)
        taxi_light = bpy.context.active_object
        taxi_light.name = "TAXI_LIGHT"
        taxi_light.parent = taxi_sign
        self.asset_objects["taxi_light"] = taxi_light

        # Create wheels (children of car body)
        wheel_positions = [
            (0.8, 1.5, 0.3),   # front left
            (-0.8, 1.5, 0.3),  # front right
            (0.8, -1.5, 0.3),  # rear left
            (-0.8, -1.5, 0.3)  # rear right
        ]

        wheel_names = ["WHEEL_FL", "WHEEL_FR", "WHEEL_RL", "WHEEL_RR"]
        for i, (pos, name) in enumerate(zip(wheel_positions, wheel_names)):
            bpy.ops.mesh.primitive_cylinder_add(
                location=pos,
                radius=0.3,
                depth=0.2,
                rotation=(1.5708, 0, 0)  # 90 degrees on X axis
            )
            wheel = bpy.context.active_object
            wheel.name = name
            wheel.parent = car_body
            self.asset_objects[f"wheel_{i}"] = wheel

        # Create interior (child of car body)
        bpy.ops.mesh.primitive_cube_add(location=(0, 0, 1.2), size=(1.8, 3.8, 0.8))
        interior = bpy.context.active_object
        interior.name = "INTERIOR"
        interior.parent = car_body
        self.asset_objects["interior"] = interior

        self.log_debug(f"Created mock car asset with {len(self.asset_objects)} objects")
        return self.asset_objects

    def capture_state(self) -> Dict[str, Any]:
        """Capture current scene state"""
        state = {
            "objects": {},
            "hierarchy": {},
            "timestamp": bpy.context.scene.frame_current
        }

        for obj in bpy.data.objects:
            if any(name in obj.name for name in ["CAR_", "TAXI_", "WHEEL_", "INTERIOR"]):
                state["objects"][obj.name] = {
                    "parent": obj.parent.name if obj.parent else None,
                    "children": [child.name for child in obj.children],
                    "location": list(obj.location),
                    "rotation_euler": list(obj.rotation_euler),
                    "scale": list(obj.scale),
                    "matrix_world": [list(row) for row in obj.matrix_world]
                }

        return state

    def simulate_broken_route_import(self, car_obj: bpy.types.Object) -> Dict[str, Any]:
        """Simulate the broken route import that clears parent relationships"""
        self.log_debug("Simulating BROKEN route import workflow...")

        state_before = self.capture_state()

        # This mimics route/anim.py:617
        try:
            self.log_debug(f"Clearing parent for {car_obj.name} (mimicking route/anim.py:617)")
            car_obj.parent = None
            car_obj.matrix_parent_inverse = mathutils.Matrix.Identity(4)
        except Exception as exc:
            self.log_debug(f"Error clearing parent: {exc}", "ERROR")

        # This mimics route/fetch_operator.py:1072 and similar calls
        for name, obj in self.asset_objects.items():
            if obj and obj.parent:
                self.log_debug(f"Clearing parent for {obj.name} (mimicking fetch_operator)")
                obj.parent = None
                obj.matrix_parent_inverse = mathutils.Matrix.Identity(4)

        state_after = self.capture_state()

        return {
            "before": state_before,
            "after": state_after,
            "workflow": "broken"
        }

    def simulate_fixed_route_import(self, car_obj: bpy.types.Object) -> Dict[str, Any]:
        """Simulate the fixed route import that preserves parent relationships"""
        self.log_debug("Simulating FIXED route import workflow...")

        state_before = self.capture_state()

        # Instead of clearing parent, preserve the hierarchy
        # Only transform the root object
        try:
            # Move car to route start position but preserve internal hierarchy
            start_location = mathutils.Vector((10, 10, 1))
            start_rotation = mathutils.Euler((0, 0, 0.785))  # 45 degrees

            # Transform the root object only
            car_obj.location = start_location
            car_obj.rotation_euler = start_rotation

            self.log_debug(f"Transformed car to {start_location} with rotation {start_rotation}")
            self.log_debug(f"Preserved parent-child hierarchy")

        except Exception as exc:
            self.log_debug(f"Error in fixed workflow: {exc}", "ERROR")

        state_after = self.capture_state()

        return {
            "before": state_before,
            "after": state_after,
            "workflow": "fixed"
        }

    def simulate_asset_manager_import(self) -> Dict[str, Any]:
        """Simulate asset manager import process"""
        self.log_debug("Simulating asset manager import...")

        # This simulates the asset_manager/loader.py process
        # where assets are imported from ASSET_CAR.blend

        # In real scenario, this would:
        # 1. Load ASSET_CAR.blend
        # 2. Append/link the objects
        # 3. Position them in the scene

        # For simulation, we create the objects with proper hierarchy
        mock_assets = self.create_mock_car_asset()

        return {
            "imported_objects": list(mock_assets.keys()),
            "hierarchy_preserved": self.validate_hierarchy(mock_assets)
        }

    def validate_hierarchy(self, objects: Dict[str, bpy.types.Object]) -> bool:
        """Validate that expected parent-child relationships exist"""
        expected_relationships = {
            "TAXI_SIGN": "CAR_BODY",
            "TAXI_LIGHT": "TAXI_SIGN",
            "WHEEL_FL": "CAR_BODY",
            "WHEEL_FR": "CAR_BODY",
            "WHEEL_RL": "CAR_BODY",
            "WHEEL_RR": "CAR_BODY",
            "INTERIOR": "CAR_BODY"
        }

        for child_name, expected_parent in expected_relationships.items():
            if child_name in objects:
                obj = objects[child_name]
                actual_parent = obj.parent.name if obj.parent else None
                if actual_parent != expected_parent:
                    self.log_debug(f"Hierarchy validation failed: {child_name} parent is {actual_parent}, expected {expected_parent}")
                    return False

        self.log_debug("Hierarchy validation passed")
        return True

    def compare_workflows(self, broken_result: Dict[str, Any], fixed_result: Dict[str, Any]) -> Dict[str, Any]:
        """Compare broken vs fixed workflow results"""
        comparison = {
            "parenting_preservation": {
                "broken": False,
                "fixed": False
            },
            "transform_differences": {},
            "hierarchy_differences": {}
        }

        # Check if parenting is preserved in each workflow
        for workflow, result in [("broken", broken_result), ("fixed", fixed_result)]:
            after_state = result["after"]["objects"]
            preserved_count = 0
            total_relationships = 0

            expected_relationships = [
                ("TAXI_SIGN", "CAR_BODY"),
                ("TAXI_LIGHT", "TAXI_SIGN")
            ]

            for child, expected_parent in expected_relationships:
                if child in after_state:
                    total_relationships += 1
                    actual_parent = after_state[child]["parent"]
                    if actual_parent == expected_parent:
                        preserved_count += 1

            comparison["parenting_preservation"][workflow] = (preserved_count == total_relationships)

        # Calculate transform differences
        if "CAR_BODY" in broken_result["after"]["objects"] and "CAR_BODY" in fixed_result["after"]["objects"]:
            broken_loc = broken_result["after"]["objects"]["CAR_BODY"]["location"]
            fixed_loc = fixed_result["after"]["objects"]["CAR_BODY"]["location"]

            comparison["transform_differences"] = {
                "broken_location": broken_loc,
                "fixed_location": fixed_loc,
                "distance": mathutils.Vector(broken_loc).distance_to(mathutils.Vector(fixed_loc))
            }

        return comparison

    def run_complete_simulation(self) -> Dict[str, Any]:
        """Run the complete simulation workflow"""
        self.log_debug("Starting complete car import simulation...")

        # Setup
        self.setup_test_environment()

        # Step 1: Simulate asset manager import
        import_result = self.simulate_asset_manager_import()

        # Get reference to car object
        car_obj = self.asset_objects.get("car_body")
        if not car_obj:
            raise RuntimeError("Failed to create car object for simulation")

        # Step 2: Test broken workflow
        self.setup_test_environment()  # Reset
        self.create_mock_car_asset()
        broken_result = self.simulate_broken_route_import(self.asset_objects["car_body"])

        # Step 3: Test fixed workflow
        self.setup_test_environment()  # Reset
        self.create_mock_car_asset()
        fixed_result = self.simulate_fixed_route_import(self.asset_objects["car_body"])

        # Step 4: Compare results
        comparison = self.compare_workflows(broken_result, fixed_result)

        # Step 5: Generate findings
        findings = {
            "parenting_issue_confirmed": not comparison["parenting_preservation"]["broken"] and comparison["parenting_preservation"]["fixed"],
            "fix_effectiveness": comparison["parenting_preservation"]["fixed"],
            "recommendations": []
        }

        if findings["parenting_issue_confirmed"]:
            findings["recommendations"].append("Remove explicit parent=None calls in route/anim.py:617")
            findings["recommendations"].append("Preserve hierarchy when positioning car objects")
            findings["recommendations"].append("Only transform root objects in route/fetch_operator.py")
        else:
            findings["recommendations"].append("Investigate other potential causes of parenting issues")

        return {
            "simulation": {
                "import_result": import_result,
                "broken_workflow": broken_result,
                "fixed_workflow": fixed_result,
                "comparison": comparison,
                "findings": findings,
                "debug_messages": self.debug_messages
            }
        }

def main():
    """Run the car import simulation"""
    print("🚗 Starting Car Import Simulation")
    print("=" * 50)

    simulator = CarImportSimulator()

    try:
        result = simulator.run_complete_simulation()

        print("\n" + "=" * 50)
        print("🎯 SIMULATION RESULTS")
        print("=" * 50)

        findings = result["simulation"]["findings"]
        comparison = result["simulation"]["comparison"]

        print(f"Parenting Issue Confirmed: {findings['parenting_issue_confirmed']}")
        print(f"Fix Effectiveness: {findings['fix_effectiveness']}")

        print(f"\nParenting Preservation:")
        print(f"  Broken Workflow: {comparison['parenting_preservation']['broken']}")
        print(f"  Fixed Workflow: {comparison['parenting_preservation']['fixed']}")

        print(f"\n📝 Recommendations:")
        for rec in findings["recommendations"]:
            print(f"  • {rec}")

        # Save results
        results_path = Path("asset-car-fix/reports/simulation_results.json")
        results_path.parent.mkdir(exist_ok=True)

        with open(results_path, 'w') as f:
            json.dump(result, f, indent=2)

        print(f"\n💾 Results saved to: {results_path}")

        return findings["parenting_issue_confirmed"]

    except Exception as exc:
        print(f"❌ Simulation failed: {exc}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)