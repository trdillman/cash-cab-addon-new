"""
Quick Test Runner
"""

import json
import sys
from pathlib import Path

def main():
    """Quick test to validate the test suite setup"""
    print("🚗 Car Import Parenting Issue - Quick Test Runner")
    print("=" * 60)

    # Test 1: Check files exist
    current_dir = Path(__file__).parent
    required_files = [
        "test_config.py",
        "run_tests.py",
        "blender_test_generator.py",
        "car_import_simulator.py",
        "transform_validator.py",
        "headless_test_runner.py",
        "README.md",
        "scripts/broken_workflow_test.py",
        "scripts/fixed_workflow_test.py",
        "scripts/edge_case_no_parent_test.py",
        "scripts/edge_case_nested_test.py"
    ]

    print("📁 Checking required files...")
    missing_files = []
    for file_path in required_files:
        full_path = current_dir / file_path
        if full_path.exists():
            print(f"  ✅ {file_path}")
        else:
            print(f"  ❌ {file_path}")
            missing_files.append(file_path)

    if missing_files:
        print(f"\n❌ Missing {len(missing_files)} required files")
        return False

    # Test 2: Check configuration
    print("\n⚙️  Loading configuration...")
    try:
        from test_config import TEST_CONFIG, TEST_MATRIX
        print(f"  ✅ Loaded configuration with {len(TEST_CONFIG)} settings")
        print(f"  ✅ Loaded {len(TEST_MATRIX)} test cases:")
        for name, config in TEST_MATRIX.items():
            print(f"     - {name}: {config['description']}")
    except Exception as e:
        print(f"  ❌ Failed to load configuration: {e}")
        return False

    # Test 3: Create reports directory
    print("\n📊 Creating reports directory...")
    reports_dir = current_dir / "reports"
    try:
        reports_dir.mkdir(exist_ok=True)
        print(f"  ✅ Reports directory: {reports_dir}")
    except Exception as e:
        print(f"  ❌ Failed to create reports directory: {e}")
        return False

    # Test 4: Generate a mock test report
    print("\n📋 Generating mock test report...")
    try:
        mock_report = {
            "test_metadata": {
                "mode": "quick_test",
                "start_time": 0,
                "end_time": 1,
                "duration": 1.0,
                "max_retries": 4
            },
            "summary": {
                "overall_status": "READY",
                "parenting_issue_confirmed": False,
                "fix_effectiveness": 0.0,
                "test_success_rate": 0.0,
                "critical_issues_count": 0,
                "recommendations_count": 0
            },
            "analysis": {
                "parenting_issue_confirmed": False,
                "fix_effectiveness": 0.0,
                "test_coverage": {},
                "critical_issues": [],
                "success_rate": 0.0
            },
            "fix_recommendations": [
                "Run full test suite with: python run_tests.py --mode=complete",
                "Ensure Blender is installed and accessible",
                "Test with actual ASSET_CAR.blend file when available"
            ],
            "next_steps": [
                "1. Execute: python run_tests.py --mode=quick",
                "2. Review generated reports in asset-car-fix/reports/",
                "3. Apply recommended fixes to cash-cab-addon source code"
            ]
        }

        report_path = reports_dir / "quick_test_report.json"
        with open(report_path, 'w') as f:
            json.dump(mock_report, f, indent=2)

        print(f"  ✅ Mock report generated: {report_path}")

    except Exception as e:
        print(f"  ❌ Failed to generate mock report: {e}")
        return False

    # Test 5: Check Blender availability
    print("\n🔍 Checking Blender availability...")
    import shutil
    blender_path = shutil.which("blender")
    if blender_path:
        print(f"  ✅ Blender found: {blender_path}")
    else:
        print("  ⚠️  Blender not found in PATH")
        print("     You may need to specify --blender path when running tests")
        print("     Example: python run_tests.py --blender='C:\\Program Files\\Blender Foundation\\Blender\\blender.exe'")

    # Summary
    print(f"\n" + "=" * 60)
    print("🎯 QUICK TEST SUMMARY")
    print("=" * 60)
    print("✅ All required files present")
    print("✅ Configuration loaded successfully")
    print("✅ Reports directory ready")
    print("✅ Mock report generation working")
    print("⚠️  Blender status checked (may need path specification)")

    print(f"\n🚀 READY TO RUN TESTS!")
    print("Next steps:")
    print("  1. Quick validation: python run_tests.py --mode=quick")
    print("  2. Full test suite: python run_tests.py --mode=complete")
    print("  3. With Blender path: python run_tests.py --blender='your_blender_path'")

    return True

if __name__ == "__main__":
    success = main()
    if not success:
        print(f"\n❌ Quick test failed - check the issues above")
        sys.exit(1)
    else:
        print(f"\n✅ Quick test passed - test suite ready!")
        sys.exit(0)