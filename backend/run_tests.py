#!/usr/bin/env python3
"""
AudiPy Test Runner
Convenient script to run different types of tests
"""

import sys
import subprocess
from pathlib import Path


def run_command(cmd, description):
    """Run a command and print results"""
    print(f"\n🧪 {description}")
    print("=" * 50)
    
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ PASSED")
        if result.stdout:
            print(result.stdout)
    else:
        print("❌ FAILED")
        if result.stderr:
            print(result.stderr)
        if result.stdout:
            print(result.stdout)
    
    return result.returncode == 0


def main():
    """Main test runner"""
    if len(sys.argv) > 1:
        test_type = sys.argv[1]
    else:
        test_type = "all"
    
    print("🎵 AudiPy Test Suite")
    print(f"Running: {test_type}")
    
    success = True
    
    if test_type in ["all", "unit"]:
        # Run unit tests (exclude integration tests)
        success &= run_command(
            "python -m pytest tests/ -v -m 'not integration'",
            "Unit Tests"
        )
    
    if test_type in ["all", "integration"]:
        # Run integration tests
        success &= run_command(
            "python -m pytest tests/ -v -m 'integration'",
            "Integration Tests"
        )
    
    if test_type == "coverage":
        # Run tests with coverage
        success &= run_command(
            "python -m pytest tests/ --cov=services --cov=utils --cov=api --cov-report=html --cov-report=term",
            "Coverage Report"
        )
    
    if test_type == "fast":
        # Run fast tests only
        success &= run_command(
            "python -m pytest tests/ -v -m 'not slow and not integration'",
            "Fast Tests"
        )
    
    if test_type == "api":
        # Run API tests only
        success &= run_command(
            "python -m pytest tests/test_api.py -v",
            "API Tests"
        )
    
    if test_type == "services":
        # Run service tests only
        success &= run_command(
            "python -m pytest tests/test_auth_service.py -v",
            "Service Tests"
        )
    
    if test_type == "crypto":
        # Run crypto tests only
        success &= run_command(
            "python -m pytest tests/test_crypto_utils.py -v",
            "Crypto Tests"
        )
    
    if test_type == "db":
        # Run database tests only
        success &= run_command(
            "python -m pytest tests/test_db_connection.py -v",
            "Database Tests"
        )
    
    # Summary
    print("\n" + "=" * 50)
    if success:
        print("🎉 All tests passed!")
        sys.exit(0)
    else:
        print("💥 Some tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    main() 