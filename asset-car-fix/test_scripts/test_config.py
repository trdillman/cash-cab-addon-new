"""
Car Import Parenting Issue Test Suite

This test suite validates the car import workflow and identifies parenting issues
where the taxi sign loses its parent relationship to the car during import.

Test Approach:
1. Create test car assets with parent-child hierarchies
2. Simulate current broken workflow (with parent = None calls)
3. Test proposed fix that preserves hierarchies
4. Compare transforms and parent-child relationships
5. Generate validation reports
"""

import os
import sys
import json
import time
import traceback
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional

# Test Configuration
TEST_CONFIG = {
    "retry_attempts": 4,
    "debug_level": "verbose",
    "blender_executable": None,  # Will auto-detect
    "test_assets_dir": "test_assets",
    "reports_dir": "reports",
    "headless_mode": True,
    "timeout_seconds": 300,
}

# Expected Hierarchy Configuration
EXPECTED_HIERARCHY = {
    "car_body": {
        "children": ["taxi_sign", "wheels", "interior"],
        "parent": None
    },
    "taxi_sign": {
        "children": ["taxi_light", "sign_text"],
        "parent": "car_body"
    },
    "wheels": {
        "children": ["wheel_front_left", "wheel_front_right", "wheel_rear_left", "wheel_rear_right"],
        "parent": "car_body"
    },
    "interior": {
        "children": ["dashboard", "seats"],
        "parent": "car_body"
    }
}

# Test Matrix
TEST_MATRIX = {
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

class TestResult:
    """Container for individual test results"""

    def __init__(self, test_name: str):
        self.test_name = test_name
        self.start_time = time.time()
        self.end_time = None
        self.success = False
        self.error_message = None
        self.hierarchy_before = None
        self.hierarchy_after = None
        self.transforms_before = None
        self.transforms_after = None
        self.debug_output = []
        self.assertions = []

    def mark_complete(self, success: bool, error_message: str = None):
        self.end_time = time.time()
        self.success = success
        self.error_message = error_message

    def add_debug(self, message: str):
        timestamp = time.strftime("%H:%M:%S", time.localtime())
        self.debug_output.append(f"[{timestamp}] {message}")

    def add_assertion(self, assertion: str, passed: bool, details: str = None):
        self.assertions.append({
            "assertion": assertion,
            "passed": passed,
            "details": details
        })

    def to_dict(self) -> Dict[str, Any]:
        return {
            "test_name": self.test_name,
            "duration": (self.end_time or time.time()) - self.start_time,
            "success": self.success,
            "error_message": self.error_message,
            "hierarchy_before": self.hierarchy_before,
            "hierarchy_after": self.hierarchy_after,
            "transforms_before": self.transforms_before,
            "transforms_after": self.transforms_after,
            "debug_output": self.debug_output,
            "assertions": self.assertions
        }

class TestSuite:
    """Main test suite runner"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = {**TEST_CONFIG, **(config or {})}
        self.results = []
        self.base_path = Path(__file__).parent

    def setup(self):
        """Setup test environment"""
        os.makedirs(self.base_path / self.config["test_assets_dir"], exist_ok=True)
        os.makedirs(self.base_path / self.config["reports_dir"], exist_ok=True)

    def run_all_tests(self) -> Dict[str, Any]:
        """Run complete test suite with retries"""
        print("🚗 Starting Car Import Parenting Test Suite")
        print("=" * 60)

        self.setup()

        for test_name, test_config in TEST_MATRIX.items():
            print(f"\n🧪 Running: {test_name}")
            print(f"   Description: {test_config['description']}")

            # Run with retries
            final_result = None
            for attempt in range(self.config["retry_attempts"]):
                print(f"   Attempt {attempt + 1}/{self.config['retry_attempts']}")

                try:
                    result = self.run_single_test(test_name, test_config, attempt)
                    if result.success:
                        print(f"   ✅ PASSED on attempt {attempt + 1}")
                        final_result = result
                        break
                    else:
                        print(f"   ❌ FAILED on attempt {attempt + 1}: {result.error_message}")
                        if attempt < self.config["retry_attempts"] - 1:
                            print(f"   🔧 Retrying with enhanced debugging...")
                            time.sleep(1)  # Brief pause between attempts
                except Exception as exc:
                    print(f"   💥 EXCEPTION on attempt {attempt + 1}: {exc}")
                    if attempt == self.config["retry_attempts"] - 1:
                        result = TestResult(test_name)
                        result.mark_complete(False, str(exc))
                        result.add_debug(f"Exception: {traceback.format_exc()}")
                        final_result = result

            if final_result:
                self.results.append(final_result)

        return self.generate_report()

    def run_single_test(self, test_name: str, test_config: Dict[str, Any], attempt: int) -> TestResult:
        """Run a single test with the given configuration"""
        result = TestResult(f"{test_name}_attempt_{attempt + 1}")
        result.add_debug(f"Starting test: {test_name}")
        result.add_debug(f"Config: {test_config}")

        try:
            # This will be implemented by calling Blender scripts
            result = self.execute_blender_test(test_name, test_config, result)
        except Exception as exc:
            result.mark_complete(False, f"Test execution failed: {exc}")
            result.add_debug(f"Exception traceback: {traceback.format_exc()}")

        return result

    def execute_blender_test(self, test_name: str, test_config: Dict[str, Any], result: TestResult) -> TestResult:
        """Execute test in Blender environment"""
        # This will create and run the Blender test script
        script_path = self.base_path / "scripts" / f"{test_name}_test.py"

        # Generate the test script
        script_content = self.generate_blender_test_script(test_name, test_config, result)

        with open(script_path, 'w') as f:
            f.write(script_content)

        # Execute Blender headlessly
        blender_cmd = self.get_blender_command(script_path)
        result.add_debug(f"Executing: {' '.join(blender_cmd)}")

        # Run and capture output
        import subprocess
        process = subprocess.run(
            blender_cmd,
            capture_output=True,
            text=True,
            timeout=self.config["timeout_seconds"]
        )

        result.add_debug("STDOUT:\n" + process.stdout)
        if process.stderr:
            result.add_debug("STDERR:\n" + process.stderr)

        # Parse results from Blender output
        self.parse_blender_output(process.stdout, result)

        return result

    def generate_blender_test_script(self, test_name: str, test_config: Dict[str, Any], result: TestResult) -> str:
        """Generate Blender Python script for the test"""
        # This will be implemented in the script generation module
        pass

    def get_blender_command(self, script_path: Path) -> List[str]:
        """Get Blender command for headless execution"""
        blender_exe = self.config.get("blender_executable")
        if not blender_exe:
            # Try to auto-detect Blender
            blender_exe = self.find_blender_executable()

        return [
            blender_exe,
            "--background",
            "--python", str(script_path)
        ]

    def find_blender_executable(self) -> str:
        """Auto-detect Blender executable"""
        # Common Blender paths
        possible_paths = [
            "blender",
            "/usr/bin/blender",
            "/Applications/Blender.app/Contents/MacOS/Blender",
            "C:\\Program Files\\Blender Foundation\\Blender\\blender.exe"
        ]

        import shutil
        for path in possible_paths:
            if shutil.which(path):
                return path

        raise RuntimeError("Blender executable not found. Please set blender_executable in config.")

    def parse_blender_output(self, output: str, result: TestResult):
        """Parse test results from Blender output"""
        try:
            # Look for JSON result block in output
            json_start = output.find("TEST_RESULT_JSON_START")
            json_end = output.find("TEST_RESULT_JSON_END")

            if json_start != -1 and json_end != -1:
                json_data = output[json_start + len("TEST_RESULT_JSON_START"):json_end].strip()
                test_data = json.loads(json_data)

                result.hierarchy_before = test_data.get("hierarchy_before")
                result.hierarchy_after = test_data.get("hierarchy_after")
                result.transforms_before = test_data.get("transforms_before")
                result.transforms_after = test_data.get("transforms_after")
                result.success = test_data.get("success", False)
                result.error_message = test_data.get("error_message")

        except Exception as exc:
            result.add_debug(f"Failed to parse Blender output: {exc}")
            result.mark_complete(False, f"Output parsing failed: {exc}")

    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        report = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "config": self.config,
            "summary": {
                "total_tests": len(self.results),
                "passed": sum(1 for r in self.results if r.success),
                "failed": sum(1 for r in self.results if not r.success),
                "total_duration": sum(r.duration for r in self.results if hasattr(r, 'duration'))
            },
            "results": [r.to_dict() for r in self.results],
            "analysis": self.analyze_results()
        }

        # Save report
        report_path = self.base_path / self.config["reports_dir"] / f"test_report_{int(time.time())}.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"\n📊 Report saved to: {report_path}")
        self.print_summary(report)

        return report

    def analyze_results(self) -> Dict[str, Any]:
        """Analyze test results and provide insights"""
        analysis = {
            "parenting_issue_confirmed": False,
            "fix_effectiveness": {},
            "recommendations": []
        }

        # Look for broken vs fixed workflow patterns
        broken_results = [r for r in self.results if "broken" in r.test_name and not r.success]
        fixed_results = [r for r in self.results if "fixed" in r.test_name and r.success]

        if broken_results and fixed_results:
            analysis["parenting_issue_confirmed"] = True
            analysis["fix_effectiveness"] = {
                "broken_workflow_failures": len(broken_results),
                "fixed_workflow_successes": len(fixed_results),
                "improvement_rate": len(fixed_results) / (len(broken_results) + len(fixed_results)) * 100
            }
            analysis["recommendations"].append("Parenting issue confirmed: fix preserves hierarchies")
        else:
            analysis["recommendations"].append("Inconclusive results - more testing needed")

        return analysis

    def print_summary(self, report: Dict[str, Any]):
        """Print test summary to console"""
        summary = report["summary"]
        analysis = report["analysis"]

        print("\n" + "=" * 60)
        print("🏁 TEST SUITE SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {summary['total_tests']}")
        print(f"Passed: {summary['passed']} ✅")
        print(f"Failed: {summary['failed']} ❌")
        print(f"Duration: {summary['total_duration']:.2f}s")

        if analysis["parenting_issue_confirmed"]:
            print(f"\n🎯 PARENTING ISSUE CONFIRMED")
            print(f"   Fix effectiveness: {analysis['fix_effectiveness']['improvement_rate']:.1f}%")

        print(f"\n📝 RECOMMENDATIONS:")
        for rec in analysis["recommendations"]:
            print(f"   • {rec}")

if __name__ == "__main__":
    suite = TestSuite()
    report = suite.run_all_tests()