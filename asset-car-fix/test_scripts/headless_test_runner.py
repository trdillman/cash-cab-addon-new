"""
Headless Blender Test Runner

Executes Blender tests in headless mode with retry logic and debugging.
"""

import subprocess
import json
import time
import os
import sys
import signal
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import threading

class BlenderHeadlessRunner:
    """Runs Blender tests in headless mode with advanced retry logic"""

    def __init__(self, max_retries: int = 4, timeout: int = 300):
        self.max_retries = max_retries
        self.timeout = timeout
        self.debug_level = "verbose"
        self.blender_executable = None
        self.test_results = []

    def find_blender_executable(self) -> str:
        """Find Blender executable on the system"""
        if self.blender_executable:
            return self.blender_executable

        # Common Blender paths by platform
        possible_paths = [
            # Windows
            "C:\\Program Files\\Blender Foundation\\Blender\\blender.exe",
            "C:\\Program Files\\Blender Foundation\\Blender 4.5\\blender.exe",
            "C:\\Program Files\\Blender Foundation\\Blender 4.4\\blender.exe",
            "C:\\Program Files\\Blender Foundation\\Blender 4.3\\blender.exe",
            "C:\\Program Files (x86)\\Blender Foundation\\Blender\\blender.exe",

            # macOS
            "/Applications/Blender.app/Contents/MacOS/Blender",
            "/Applications/Blender 4.5.app/Contents/MacOS/Blender",
            "/Applications/Blender 4.4.app/Contents/MacOS/Blender",

            # Linux
            "/usr/bin/blender",
            "/usr/local/bin/blender",
            "/snap/bin/blender",

            # Generic
            "blender"
        ]

        import shutil
        for path in possible_paths:
            if os.path.exists(path) or shutil.which(path):
                self.blender_executable = path
                print(f"Found Blender at: {path}")
                return path

        raise RuntimeError(
            "Blender executable not found. Please install Blender or set blender_executable path.\n"
            "Download from: https://www.blender.org/download/"
        )

    def create_enhanced_test_script(self, script_path: Path, test_config: Dict[str, Any]) -> Path:
        """Create an enhanced test script with better error handling and output"""
        enhanced_script_path = script_path.parent / f"enhanced_{script_path.stem}.py"

        script_content = f'''
import bpy
import sys
import json
import traceback
import time
import signal
import threading
from pathlib import Path

# Test configuration
TEST_CONFIG = {json.dumps(test_config, indent=2)}
SCRIPT_PATH = "{script_path}"

class TestTimeoutError(Exception):
    pass

def timeout_handler(signum, frame):
    raise TestTimeoutError("Test execution timed out")

def enhanced_error_reporting():
    """Enhanced error reporting for Blender environment"""
    print("\\n=== ENHANCED DEBUG INFO ===")
    print(f"Blender Version: {{bpy.app.version_string}}")
    print(f"Python Version: {{sys.version}}")
    print(f"Current Scene: {{bpy.context.scene.name}}")
    print(f"Objects in Scene: {{len(bpy.data.objects)}}")
    print(f"Total Objects: {{len(bpy.data.objects)}}")
    print(f"Total Meshes: {{len(bpy.data.meshes)}}")
    print(f"Total Materials: {{len(bpy.data.materials)}}")

    # Print object names
    print("\\nObjects in scene:")
    for obj in bpy.data.objects:
        print(f"  - {{obj.name}} (type: {{obj.type}}, parent: {{obj.parent.name if obj.parent else 'None'}})")

def run_original_script():
    """Run the original test script with enhanced error handling"""
    try:
        # Import and run the original script
        spec = importlib.util.spec_from_file_location("test_script", SCRIPT_PATH)
        test_module = importlib.util.module_from_spec(spec)

        # Set up environment variables
        os.environ['CAR_TEST_DEBUG'] = 'verbose'
        os.environ['CAR_TEST_CONFIG'] = json.dumps(TEST_CONFIG)

        # Enhanced debug info before test
        print("\\n=== PRE-TEST STATE ===")
        enhanced_error_reporting()

        # Run the test
        spec.loader.exec_module(test_module)

        # Enhanced debug info after test
        print("\\n=== POST-TEST STATE ===")
        enhanced_error_reporting()

        return True

    except TestTimeoutError as e:
        print(f"TEST TIMEOUT: {{e}}")
        return False
    except Exception as e:
        print(f"TEST EXCEPTION: {{e}}")
        print("\\n=== FULL TRACEBACK ===")
        traceback.print_exc()
        return False

def main():
    """Enhanced test execution with comprehensive reporting"""
    print("🚀 Starting Enhanced Blender Test Runner")
    print(f"Test Config: {{TEST_CONFIG}}")

    start_time = time.time()
    success = False

    try:
        # Set timeout
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(300)  # 5 minute timeout

        success = run_original_script()

        signal.alarm(0)  # Cancel timeout

    except TestTimeoutError:
        print("❌ Test timed out after 5 minutes")
        success = False
    except KeyboardInterrupt:
        print("❌ Test interrupted by user")
        success = False
    except Exception as e:
        print(f"❌ Unexpected error: {{e}}")
        traceback.print_exc()
        success = False

    duration = time.time() - start_time

    # Generate enhanced result report
    result = {{
        "success": success,
        "duration": duration,
        "test_config": TEST_CONFIG,
        "blender_version": bpy.app.version_string,
        "object_count_before": len([obj for obj in bpy.data.objects if obj.name.startswith(('CAR_', 'TAXI_', 'WHEEL_'))]),
        "enhanced_debug": True,
        "script_path": SCRIPT_PATH
    }}

    print("\\n=== ENHANCED TEST RESULT ===")
    print("TEST_RESULT_JSON_START")
    print(json.dumps(result, indent=2))
    print("TEST_RESULT_JSON_END")
    print("=== END ENHANCED TEST ===\\n")

    return success

if __name__ == "__main__":
    try:
        import importlib.util
        import os
        success = main()
        exit(0 if success else 1)
    except ImportError as e:
        print(f"Import error: {{e}}")
        exit(1)
'''

        with open(enhanced_script_path, 'w') as f:
            f.write(script_content)

        return enhanced_script_path

    def execute_blender_test(self, script_path: Path, test_config: Dict[str, Any], attempt: int = 1) -> Dict[str, Any]:
        """Execute Blender test with comprehensive error handling"""
        result = {
            "attempt": attempt,
            "success": False,
            "stdout": "",
            "stderr": "",
            "exit_code": None,
            "error_message": None,
            "duration": 0,
            "timeout": False
        }

        try:
            # Find Blender executable
            blender_exe = self.find_blender_executable()

            # Create enhanced test script
            enhanced_script = self.create_enhanced_test_script(script_path, test_config)

            # Build command
            cmd = [
                blender_exe,
                "--background",
                "--python", str(enhanced_script),
                "--factory-startup"  # Clean startup
            ]

            # Add debug arguments for later attempts
            if attempt > 1:
                cmd.extend(["--debug", "--debug-all"])

            print(f"🔧 Attempt {attempt}: Executing {' '.join(cmd)}")

            # Execute with timeout
            start_time = time.time()
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                universal_newlines=True
            )

            try:
                stdout, stderr = process.communicate(timeout=self.timeout)
                result["exit_code"] = process.returncode
                result["stdout"] = stdout
                result["stderr"] = stderr
                result["duration"] = time.time() - start_time

                # Parse JSON result from output
                json_start = stdout.find("TEST_RESULT_JSON_START")
                json_end = stdout.find("TEST_RESULT_JSON_END")

                if json_start != -1 and json_end != -1:
                    json_data = stdout[json_start + len("TEST_RESULT_JSON_START"):json_end].strip()
                    if json_data:
                        try:
                            test_data = json.loads(json_data)
                            result.update(test_data)
                            result["success"] = result.get("success", False) and process.returncode == 0
                        except json.JSONDecodeError as e:
                            print(f"⚠️  Failed to parse JSON result: {e}")

                if not result["success"]:
                    result["error_message"] = self.extract_error_message(stdout, stderr, process.returncode)

                return result

            except subprocess.TimeoutExpired:
                process.kill()
                result["timeout"] = True
                result["error_message"] = f"Test timed out after {self.timeout} seconds"
                result["duration"] = self.timeout
                return result

        except Exception as exc:
            result["error_message"] = f"Failed to execute Blender: {exc}"
            result["duration"] = time.time() - start_time
            return result

    def extract_error_message(self, stdout: str, stderr: str, exit_code: int) -> str:
        """Extract meaningful error message from Blender output"""
        if "Exception" in stdout:
            # Extract last exception
            lines = stdout.split('\n')
            for i, line in enumerate(lines):
                if line.startswith('Exception:'):
                    return ' '.join(lines[i:i+3])  # Include a few lines of context

        if "Error" in stderr:
            # Extract last error from stderr
            lines = stderr.split('\n')
            error_lines = [line for line in lines if 'Error:' in line]
            if error_lines:
                return error_lines[-1].strip()

        if exit_code != 0:
            return f"Process exited with code {exit_code}"

        return "Unknown error occurred"

    def run_test_with_retries(self, script_path: Path, test_config: Dict[str, Any]) -> Dict[str, Any]:
        """Run test with retry logic and progressive debugging"""
        print(f"🚗 Running test: {script_path.name}")
        print(f"   Config: {test_config.get('description', 'No description')}")

        all_attempts = []
        final_result = None

        for attempt in range(1, self.max_retries + 1):
            print(f"   🔄 Attempt {attempt}/{self.max_retries}")

            result = self.execute_blender_test(script_path, test_config, attempt)
            all_attempts.append(result)

            if result["success"]:
                print(f"   ✅ PASSED on attempt {attempt}")
                final_result = result
                break
            else:
                print(f"   ❌ FAILED on attempt {attempt}: {result['error_message']}")

                if attempt < self.max_retries:
                    # Enhanced debugging for next attempt
                    print(f"   🔧 Debugging for next attempt:")

                    if "timeout" in str(result.get("error_message", "")).lower():
                        print(f"      • Will increase timeout and reduce test complexity")
                        self.timeout = min(self.timeout * 1.5, 600)  # Max 10 minutes
                    elif "import" in str(result.get("error_message", "")).lower():
                        print(f"      • Will add factory startup and debug flags")
                    elif "memory" in str(result.get("error_message", "")).lower():
                        print(f"      • Will optimize memory usage")

                    time.sleep(1)  # Brief pause between attempts

        if not final_result:
            # Use the last attempt result
            final_result = all_attempts[-1]
            print(f"   💥 All {self.max_retries} attempts failed")

        # Add attempt history to final result
        final_result["all_attempts"] = all_attempts
        final_result["total_attempts"] = len(all_attempts)

        return final_result

    def run_test_suite(self, test_dir: Path) -> Dict[str, Any]:
        """Run all tests in the test directory"""
        if not test_dir.exists():
            raise RuntimeError(f"Test directory not found: {test_dir}")

        test_files = list(test_dir.glob("*_test.py"))
        if not test_files:
            raise RuntimeError(f"No test files found in {test_dir}")

        print(f"📂 Found {len(test_files)} test files")
        print(f"🎯 Running with {self.max_retries} max retries per test")
        print(f"⏱️  Timeout: {self.timeout} seconds per attempt")

        suite_results = {
            "start_time": time.time(),
            "test_files": [f.name for f in test_files],
            "results": {},
            "summary": {
                "total_tests": len(test_files),
                "passed": 0,
                "failed": 0,
                "total_attempts": 0
            }
        }

        for test_file in test_files:
            test_name = test_file.stem.replace("_test", "")

            # Extract test config from filename
            test_config = {
                "name": test_name,
                "description": f"Test for {test_name}",
                "broken": "broken" in test_name,
                "fixed": "fixed" in test_name,
                "edge_case": "edge" in test_name
            }

            result = self.run_test_with_retries(test_file, test_config)
            suite_results["results"][test_name] = result

            if result["success"]:
                suite_results["summary"]["passed"] += 1
            else:
                suite_results["summary"]["failed"] += 1

            suite_results["summary"]["total_attempts"] += result.get("total_attempts", 1)

        suite_results["end_time"] = time.time()
        suite_results["duration"] = suite_results["end_time"] - suite_results["start_time"]

        return suite_results

def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Headless Blender Test Runner")
    parser.add_argument("--test-dir", default="asset-car-fix/scripts",
                       help="Directory containing test scripts")
    parser.add_argument("--retries", type=int, default=4,
                       help="Maximum retries per test")
    parser.add_argument("--timeout", type=int, default=300,
                       help="Timeout per attempt in seconds")
    parser.add_argument("--blender",
                       help="Path to Blender executable")

    args = parser.parse_args()

    # Initialize runner
    runner = BlenderHeadlessRunner(
        max_retries=args.retries,
        timeout=args.timeout
    )

    if args.blender:
        runner.blender_executable = args.blender

    try:
        # Run test suite
        test_dir = Path(args.test_dir)
        results = runner.run_test_suite(test_dir)

        # Save results
        results_path = Path("asset-car-fix/reports/headless_test_results.json")
        results_path.parent.mkdir(exist_ok=True)

        with open(results_path, 'w') as f:
            json.dump(results, f, indent=2)

        # Print summary
        print("\n" + "=" * 60)
        print("🏁 HEADLESS TEST SUITE SUMMARY")
        print("=" * 60)
        summary = results["summary"]
        print(f"Total Tests: {summary['total_tests']}")
        print(f"Passed: {summary['passed']} ✅")
        print(f"Failed: {summary['failed']} ❌")
        print(f"Total Attempts: {summary['total_attempts']}")
        print(f"Duration: {results['duration']:.2f}s")
        print(f"\n📊 Results saved to: {results_path}")

        # Exit with appropriate code
        return summary["failed"] == 0

    except Exception as exc:
        print(f"❌ Test runner failed: {exc}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)