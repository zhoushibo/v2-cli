# -*- coding: utf-8 -*-
"""
V2 Learning System - Test Runner
Run all tests with coverage report
"""

import subprocess
import sys
from pathlib import Path

def run_tests():
    """Run all tests with coverage"""
    print("=" * 80)
    print("V2 Learning System - Unit Tests")
    print("=" * 80)
    print()
    
    # Change to test directory
    test_dir = Path(__file__).parent / "tests"
    
    # Run pytest with coverage
    cmd = [
        sys.executable, "-m", "pytest",
        str(test_dir),
        "-v",
        "--tb=short",
        f"--cov={Path(__file__).parent}",
        "--cov-report=term-missing",
        "--cov-report=html:coverage_report",
        "-o", "addopts="  # Override any config addopts
    ]
    
    print(f"Running: {' '.join(cmd)}")
    print()
    
    result = subprocess.run(cmd)
    
    print()
    print("=" * 80)
    if result.returncode == 0:
        print("ALL TESTS PASSED")
    else:
        print("SOME TESTS FAILED")
    print("=" * 80)
    print()
    print("Coverage report: coverage_report/index.html")
    
    return result.returncode

if __name__ == "__main__":
    sys.exit(run_tests())
