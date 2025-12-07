"""
Transform and Relationship Validation Tools

Comprehensive validation tools for analyzing parent-child relationships,
transform matrices, and hierarchy preservation in Blender car import workflows.
"""

import bpy
import mathutils
import json
import numpy as np
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass
from pathlib import Path

@dataclass
class TransformData:
    """Container for transform information"""
    location: List[float]
    rotation_euler: List[float]
    scale: List[float]
    matrix_world: List[List[float]]
    matrix_local: List[List[float]]
    matrix_parent_inverse: Optional[List[List[float]]] = None

@dataclass
class RelationshipData:
    """Container for parent-child relationship information"""
    object_name: str
    parent_name: Optional[str]
    children_names: List[str]
    depth: int
    is_root: bool
    is_leaf: bool

class TransformValidator:
    """Comprehensive transform and relationship validation"""

    def __init__(self, tolerance: float = 0.001):
        self.tolerance = tolerance
        self.validation_results = {}
        self.debug_messages = []

    def log_debug(self, message: str, level: str = "INFO"):
        """Log debug message"""
        print(f"[VALIDATOR] [{level}] {message}")
        self.debug_messages.append(f"{level}: {message}")

    def capture_object_state(self, obj: bpy.types.Object) -> Dict[str, Any]:
        """Capture complete state of an object"""
        state = {
            "name": obj.name,
            "type": obj.type,
            "parent": obj.parent.name if obj.parent else None,
            "children": [child.name for child in obj.children],
            "visible": obj.visible_get(),
            "selectable": obj.select_get(),
            "locked": obj.lock_location + obj.lock_rotation + obj.lock_scale
        }

        # Capture transforms
        state["transforms"] = {
            "location": list(obj.location),
            "rotation_euler": list(obj.rotation_euler),
            "rotation_quaternion": list(obj.rotation_quaternion),
            "scale": list(obj.scale),
            "matrix_world": [list(row) for row in obj.matrix_world],
            "matrix_local": [list(row) for row in obj.matrix_local],
        }

        if obj.parent:
            state["transforms"]["matrix_parent_inverse"] = [list(row) for row in obj.matrix_parent_inverse]

        # Additional properties
        state["properties"] = {
            "display_type": obj.display_type,
            "show_bounds": obj.show_bounds,
            "show_name": obj.show_name,
            "show_axis": obj.show_axis,
            "empty_display_type": obj.empty_display_type if obj.type == 'EMPTY' else None,
            "empty_display_size": obj.empty_display_size if obj.type == 'EMPTY' else 0
        }

        return state

    def capture_scene_state(self) -> Dict[str, Any]:
        """Capture complete scene state for car-related objects"""
        self.log_debug("Capturing scene state...")

        scene_state = {
            "timestamp": bpy.context.scene.frame_current,
            "objects": {},
            "hierarchy": {},
            "metadata": {
                "blender_version": bpy.app.version_string,
                "scene_name": bpy.context.scene.name,
                "total_objects": len(bpy.data.objects)
            }
        }

        # Filter for car-related objects
        car_objects = [obj for obj in bpy.data.objects if any(
            prefix in obj.name.upper() for prefix in ["CAR_", "TAXI_", "WHEEL_", "INTERIOR", "BODY", "SIGN", "LIGHT"]
        )]

        for obj in car_objects:
            obj_state = self.capture_object_state(obj)
            scene_state["objects"][obj.name] = obj_state

        # Build hierarchy map
        scene_state["hierarchy"] = self.build_hierarchy_map(scene_state["objects"])

        self.log_debug(f"Captured state for {len(car_objects)} car objects")
        return scene_state

    def build_hierarchy_map(self, objects: Dict[str, Any]) -> Dict[str, Any]:
        """Build hierarchical relationship map"""
        hierarchy = {
            "roots": [],
            "depths": {},
            "paths": {},
            "relationships": {}
        }

        # Find root objects
        for obj_name, obj_data in objects.items():
            if obj_data["parent"] is None:
                hierarchy["roots"].append(obj_name)

        # Calculate depths for each object
        for obj_name in objects.keys():
            depth = self.calculate_object_depth(obj_name, objects)
            hierarchy["depths"][obj_name] = depth
            path = self.get_object_path(obj_name, objects)
            hierarchy["paths"][obj_name] = path

        # Build relationship summary
        for obj_name, obj_data in objects.items():
            parent = obj_data["parent"]
            children = obj_data["children"]

            hierarchy["relationships"][obj_name] = {
                "parent": parent,
                "children": [c for c in children if c in objects],  # Filter to car objects only
                "depth": hierarchy["depths"][obj_name],
                "is_root": parent is None,
                "is_leaf": len([c for c in children if c in objects]) == 0,
                "siblings": self.get_siblings(obj_name, objects)
            }

        return hierarchy

    def calculate_object_depth(self, obj_name: str, objects: Dict[str, Any]) -> int:
        """Calculate depth of object in hierarchy"""
        if obj_name not in objects:
            return -1

        parent = objects[obj_name]["parent"]
        if parent is None:
            return 0
        else:
            return 1 + self.calculate_object_depth(parent, objects)

    def get_object_path(self, obj_name: str, objects: Dict[str, Any]) -> List[str]:
        """Get full path from root to object"""
        path = []
        current = obj_name

        while current and current in objects:
            path.append(current)
            current = objects[current]["parent"]

        return list(reversed(path))

    def get_siblings(self, obj_name: str, objects: Dict[str, Any]) -> List[str]:
        """Get sibling objects (objects with same parent)"""
        if obj_name not in objects:
            return []

        parent = objects[obj_name]["parent"]
        siblings = []

        for other_name, other_data in objects.items():
            if other_name != obj_name and other_data["parent"] == parent:
                siblings.append(other_name)

        return siblings

    def validate_hierarchy_preservation(self, before_state: Dict[str, Any], after_state: Dict[str, Any]) -> Dict[str, Any]:
        """Validate that parent-child relationships are preserved"""
        self.log_debug("Validating hierarchy preservation...")

        validation = {
            "passed": True,
            "preserved_relationships": 0,
            "broken_relationships": 0,
            "missing_objects": [],
            "extra_objects": [],
            "relationship_changes": {},
            "issues": []
        }

        before_objects = before_state.get("objects", {})
        after_objects = after_state.get("objects", {})

        # Check for missing objects
        before_names = set(before_objects.keys())
        after_names = set(after_objects.keys())

        validation["missing_objects"] = list(before_names - after_names)
        validation["extra_objects"] = list(after_names - before_names)

        # Validate relationships for common objects
        common_objects = before_names & after_names

        for obj_name in common_objects:
            before_parent = before_objects[obj_name]["parent"]
            after_parent = after_objects[obj_name]["parent"]

            if before_parent == after_parent:
                validation["preserved_relationships"] += 1
            else:
                validation["broken_relationships"] += 1
                validation["relationship_changes"][obj_name] = {
                    "before": before_parent,
                    "after": after_parent
                }

                # Check if this is an expected break
                if before_parent is not None and after_parent is None:
                    validation["issues"].append(
                        f"Object {obj_name} lost parent relationship (was {before_parent})"
                    )
                    validation["passed"] = False

        # Check hierarchy depth preservation
        before_depths = before_state.get("hierarchy", {}).get("depths", {})
        after_depths = after_state.get("hierarchy", {}).get("depths", {})

        depth_changes = {}
        for obj_name in common_objects:
            before_depth = before_depths.get(obj_name, 0)
            after_depth = after_depths.get(obj_name, 0)
            if before_depth != after_depth:
                depth_changes[obj_name] = {
                    "before": before_depth,
                    "after": after_depth
                }

        validation["depth_changes"] = depth_changes

        self.log_debug(f"Hierarchy validation: {validation['preserved_relationships']} preserved, {validation['broken_relationships']} broken")

        return validation

    def validate_transform_consistency(self, before_state: Dict[str, Any], after_state: Dict[str, Any]) -> Dict[str, Any]:
        """Validate transform consistency between states"""
        self.log_debug("Validating transform consistency...")

        validation = {
            "passed": True,
            "consistent_objects": 0,
            "inconsistent_objects": 0,
            "transform_changes": {},
            "significant_changes": [],
            "issues": []
        }

        before_objects = before_state.get("objects", {})
        after_objects = after_state.get("objects", {})
        common_objects = set(before_objects.keys()) & set(after_objects.keys())

        for obj_name in common_objects:
            before_transforms = before_objects[obj_name]["transforms"]
            after_transforms = after_objects[obj_name]["transforms"]

            changes = self.compare_transforms(before_transforms, after_transforms, obj_name)
            validation["transform_changes"][obj_name] = changes

            # Determine if changes are significant
            is_significant = any([
                changes["location_change"] > self.tolerance,
                changes["rotation_change"] > self.tolerance,
                changes["scale_change"] > self.tolerance,
                changes["matrix_change"] > self.tolerance
            ])

            if is_significant:
                validation["inconsistent_objects"] += 1
                validation["significant_changes"].append(obj_name)

                # Check if this change is expected
                if obj_name == "CAR_BODY":
                    # Car body movement is expected
                    self.log_debug(f"Expected transform change for {obj_name}")
                else:
                    # Child objects should follow parent, not have independent changes
                    if after_objects[obj_name]["parent"] is not None:
                        validation["issues"].append(
                            f"Child object {obj_name} has unexpected transform changes"
                        )
                        validation["passed"] = False
            else:
                validation["consistent_objects"] += 1

        self.log_debug(f"Transform validation: {validation['consistent_objects']} consistent, {validation['inconsistent_objects']} changed")

        return validation

    def compare_transforms(self, before: Dict[str, Any], after: Dict[str, Any], obj_name: str) -> Dict[str, Any]:
        """Compare two transform states"""
        changes = {
            "location_change": 0.0,
            "rotation_change": 0.0,
            "scale_change": 0.0,
            "matrix_change": 0.0,
            "details": {}
        }

        # Compare locations
        before_loc = mathutils.Vector(before["location"])
        after_loc = mathutils.Vector(after["location"])
        changes["location_change"] = (before_loc - after_loc).length
        changes["details"]["location_distance"] = changes["location_change"]

        # Compare rotations
        before_rot = mathutils.Euler(before["rotation_euler"])
        after_rot = mathutils.Euler(after["rotation_euler"])
        changes["rotation_change"] = sum(abs(a - b) for a, b in zip(before_rot, after_rot))
        changes["details"]["rotation_difference"] = changes["rotation_change"]

        # Compare scales
        before_scale = mathutils.Vector(before["scale"])
        after_scale = mathutils.Vector(after["scale"])
        changes["scale_change"] = (before_scale - after_scale).length
        changes["details"]["scale_difference"] = changes["scale_change"]

        # Compare world matrices
        before_matrix = mathutils.Matrix(before["matrix_world"])
        after_matrix = mathutils.Matrix(after["matrix_world"])
        changes["matrix_change"] = (before_matrix - after_matrix).length
        changes["details"]["matrix_difference"] = changes["matrix_change"]

        return changes

    def generate_validation_report(self, before_state: Dict[str, Any], after_state: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive validation report"""
        self.log_debug("Generating validation report...")

        report = {
            "timestamp": bpy.context.scene.frame_current,
            "hierarchy_validation": self.validate_hierarchy_preservation(before_state, after_state),
            "transform_validation": self.validate_transform_consistency(before_state, after_state),
            "analysis": {},
            "recommendations": []
        }

        # Analyze results
        hierarchy_result = report["hierarchy_validation"]
        transform_result = report["transform_validation"]

        # Determine overall success
        overall_success = hierarchy_result["passed"] and transform_result["passed"]

        # Generate analysis
        analysis = {
            "parenting_issue_detected": not hierarchy_result["passed"],
            "transform_issue_detected": not transform_result["passed"],
            "root_object_movement": False,
            "child_object_independence": False
        }

        # Check if root object moved (expected)
        if "CAR_BODY" in transform_result["transform_changes"]:
            car_body_changes = transform_result["transform_changes"]["CAR_BODY"]
            if car_body_changes["location_change"] > self.tolerance:
                analysis["root_object_movement"] = True

        # Check if child objects moved independently (unexpected)
        for obj_name, changes in transform_result["transform_changes"].items():
            if obj_name != "CAR_BODY" and obj_name in after_state.get("objects", {}):
                obj_parent = after_state["objects"][obj_name]["parent"]
                if obj_parent and changes["location_change"] > self.tolerance:
                    analysis["child_object_independence"] = True

        report["analysis"] = analysis

        # Generate recommendations
        if analysis["parenting_issue_detected"]:
            report["recommendations"].append("Fix parent relationship clearing in route/anim.py:617")
            report["recommendations"].append("Remove parent=None calls from fetch_operator.py")

        if analysis["transform_issue_detected"] and analysis["child_object_independence"]:
            report["recommendations"].append("Ensure child objects follow parent transforms")
            report["recommendations"].append("Use matrix_parent_inverse for proper child positioning")

        if not analysis["parenting_issue_detected"] and analysis["root_object_movement"]:
            report["recommendations"].append("Parenting preserved correctly - only root object moved")

        report["overall_success"] = overall_success

        self.log_debug(f"Validation report generated: Success={overall_success}")

        return report

    def save_report(self, report: Dict[str, Any], filename: str = None) -> str:
        """Save validation report to file"""
        if filename is None:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"validation_report_{timestamp}.json"

        report_path = Path("asset-car-fix/reports") / filename
        report_path.parent.mkdir(exist_ok=True)

        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)

        self.log_debug(f"Validation report saved to: {report_path}")
        return str(report_path)

def main():
    """Main validation function"""
    validator = TransformValidator()

    print("🔍 Starting Transform and Relationship Validation")
    print("=" * 60)

    try:
        # Capture initial state (this would be called after car import)
        before_state = validator.capture_scene_state()
        print(f"📊 Captured initial state with {len(before_state['objects'])} objects")

        # Simulate some changes (for testing)
        if "CAR_BODY" in bpy.data.objects:
            car_body = bpy.data.objects["CAR_BODY"]
            car_body.location = (5, 5, 1)  # Move the car

        # Capture final state
        after_state = validator.capture_scene_state()
        print(f"📊 Captured final state with {len(after_state['objects'])} objects")

        # Generate validation report
        report = validator.generate_validation_report(before_state, after_state)

        # Print results
        print(f"\n🎯 VALIDATION RESULTS")
        print(f"Overall Success: {report['overall_success']}")
        print(f"Hierarchy Preserved: {report['hierarchy_validation']['passed']}")
        print(f"Transforms Consistent: {report['transform_validation']['passed']}")

        print(f"\n📝 Analysis:")
        analysis = report['analysis']
        for key, value in analysis.items():
            print(f"  {key}: {value}")

        print(f"\n💡 Recommendations:")
        for rec in report['recommendations']:
            print(f"  • {rec}")

        # Save report
        report_path = validator.save_report(report)
        print(f"\n💾 Report saved to: {report_path}")

        return report['overall_success']

    except Exception as exc:
        print(f"❌ Validation failed: {exc}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)