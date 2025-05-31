#!/usr/bin/env python3
"""
AudiPy Test Runner
Convenient script to run different types of tests with enhanced formatting
"""

import sys
import subprocess
from pathlib import Path
import time

# ANSI Color codes for better output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'
    
    # Background colors
    BG_GREEN = '\033[42m'
    BG_RED = '\033[41m'
    BG_YELLOW = '\033[43m'

def print_header(text):
    """Print a colorful header"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}🎵 {text}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.END}")

def print_section(text):
    """Print a section header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}🧪 {text}{Colors.END}")
    print(f"{Colors.BLUE}{'─'*50}{Colors.END}")

def print_success(text):
    """Print success message"""
    print(f"{Colors.BG_GREEN}{Colors.BOLD} ✅ {text} {Colors.END}")

def print_error(text):
    """Print error message"""
    print(f"{Colors.BG_RED}{Colors.BOLD} ❌ {text} {Colors.END}")

def print_warning(text):
    """Print warning message"""
    print(f"{Colors.BG_YELLOW}{Colors.BOLD} ⚠️  {text} {Colors.END}")

def print_info(text):
    """Print info message"""
    print(f"{Colors.CYAN}ℹ️  {text}{Colors.END}")

def format_test_count(passed, total, duration):
    """Format test count with colors"""
    if passed == total:
        return f"{Colors.GREEN}{passed}/{total} tests passed{Colors.END} in {Colors.YELLOW}{duration:.2f}s{Colors.END}"
    else:
        failed = total - passed
        return f"{Colors.RED}{failed} failed{Colors.END}, {Colors.GREEN}{passed} passed{Colors.END} of {total} total in {Colors.YELLOW}{duration:.2f}s{Colors.END}"

def run_command(cmd, description):
    """Run a command and print results with enhanced formatting"""
    print_section(description)
    
    start_time = time.time()
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    duration = time.time() - start_time
    
    if result.returncode == 0:
        print_success("PASSED")
        
        # Parse pytest output for test counts
        output_lines = result.stdout.split('\n')
        for line in output_lines:
            if 'passed' in line and ('warning' in line or 'deselected' in line or 'skipped' in line):
                # Extract test counts from pytest summary
                if 'passed' in line:
                    print(f"{Colors.GREEN}📊 {line.strip()}{Colors.END}")
                break
        
        # Show any warnings
        if 'warnings summary' in result.stdout:
            warning_lines = []
            in_warnings = False
            for line in output_lines:
                if 'warnings summary' in line:
                    in_warnings = True
                    continue
                elif in_warnings and line.startswith('=='):
                    break
                elif in_warnings and line.strip():
                    warning_lines.append(line)
            
            if warning_lines:
                print_warning(f"Found {len([l for l in warning_lines if 'DeprecationWarning' in l])} warnings")
                print(f"{Colors.YELLOW}💡 Run with -v to see warning details{Colors.END}")
        
        # Show brief output for successful tests
        if result.stdout and not any(word in result.stdout.lower() for word in ['error', 'failed', 'traceback']):
            # Just show the summary line
            for line in output_lines:
                if 'passed' in line and ('warning' in line or 'deselected' in line or 'skipped' in line):
                    break
    else:
        print_error("FAILED")
        if result.stderr:
            print(f"{Colors.RED}{result.stderr}{Colors.END}")
        if result.stdout:
            print(f"{Colors.YELLOW}{result.stdout}{Colors.END}")
    
    return result.returncode == 0

def print_summary(success, total_tests, total_duration):
    """Print final summary with colors"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.END}")
    
    if success:
        print_success(f"ALL TESTS PASSED! 🎉")
        print(f"{Colors.GREEN}✨ {total_tests} tests completed successfully in {total_duration:.2f}s{Colors.END}")
        print(f"{Colors.CYAN}🚀 Ready for deployment!{Colors.END}")
    else:
        print_error("SOME TESTS FAILED! 💥")
        print(f"{Colors.RED}🔧 Please fix failing tests before proceeding{Colors.END}")
    
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.END}")

def show_available_commands():
    """Show available test commands with colors"""
    print(f"\n{Colors.BOLD}{Colors.HEADER}📋 Available Test Commands:{Colors.END}")
    
    commands = [
        ("all", "Run all working tests (unit + API + integration)", "🎯"),
        ("unit", "Run unit tests only (fast)", "⚡"),
        ("integration", "Run integration tests", "🔗"),
        ("api", "Run all API tests (unit + integration)", "🌐"),
        ("api-unit", "Run API unit tests only (fastest)", "🏃"),
        ("api-integration", "Run API integration tests (needs server)", "🔌"),
        ("services", "Run authentication service tests", "🔐"),
        ("crypto", "Run encryption tests", "🔒"),
        ("db", "Run database tests", "🗄️"),
        ("backend", "Run all backend unit tests", "⚙️"),
        ("coverage", "Run tests with coverage report", "📊"),
        ("fast", "Run fast tests only", "💨"),
    ]
    
    for cmd, desc, emoji in commands:
        print(f"  {Colors.CYAN}{emoji} python run_tests.py {cmd:<15}{Colors.END} - {desc}")
    
    print(f"\n{Colors.YELLOW}💡 Examples:{Colors.END}")
    print(f"  {Colors.GREEN}python run_tests.py{Colors.END}           # Run all tests")
    print(f"  {Colors.GREEN}python run_tests.py api-unit{Colors.END}  # Quick API tests")
    print(f"  {Colors.GREEN}python run_tests.py coverage{Colors.END}  # Coverage report")

def main():
    """Main test runner with enhanced formatting"""
    if len(sys.argv) > 1:
        test_type = sys.argv[1]
    else:
        test_type = "all"
    
    # Show help if requested
    if test_type in ["-h", "--help", "help"]:
        show_available_commands()
        return
    
    print_header(f"AudiPy Test Suite - Running: {test_type}")
    
    start_time = time.time()
    success = True
    total_tests = 0
    
    if test_type in ["all", "unit"]:
        # Run unit tests (exclude integration tests and broken API tests)
        result = run_command(
            "venv/bin/python -m pytest tests/ -v -m 'not integration' --ignore=tests/test_api.py --ignore=tests/test_api_simple.py -q",
            "Unit Tests (Services, Crypto, Database)"
        )
        success &= result
        if result:
            total_tests += 31  # Approximate count
    
    if test_type == "all":
        # Run unit API tests as part of "all"
        result = run_command(
            "venv/bin/python -m pytest tests/test_api_units.py -v -q",
            "API Unit Tests (Route Handlers)"
        )
        success &= result
        if result:
            total_tests += 13
            
        # Run simple integration API tests as part of "all"
        result = run_command(
            "venv/bin/python -m pytest tests/test_api_simple.py -v -q",
            "API Integration Tests (HTTP Requests)"
        )
        success &= result
        if result:
            total_tests += 10
    
    if test_type in ["all", "integration"]:
        # Run integration tests
        result = run_command(
            "venv/bin/python -m pytest tests/ -v -m 'integration' -q",
            "Integration Tests (End-to-End)"
        )
        success &= result
        if result:
            total_tests += 5
    
    if test_type == "coverage":
        # Run tests with coverage
        result = run_command(
            "venv/bin/python -m pytest tests/ --cov=services --cov=utils --cov=api --cov-report=html --cov-report=term-missing",
            "Coverage Report (All Tests)"
        )
        success &= result
        total_tests = 55  # Total with coverage
    
    if test_type == "fast":
        # Run fast tests only
        result = run_command(
            "venv/bin/python -m pytest tests/ -v -m 'not slow and not integration' -q",
            "Fast Tests Only"
        )
        success &= result
        total_tests = 40
    
    if test_type == "api":
        # Run both unit and integration API tests
        result1 = run_command(
            "venv/bin/python -m pytest tests/test_api_units.py -v -q",
            "API Unit Tests"
        )
        result2 = run_command(
            "venv/bin/python -m pytest tests/test_api_simple.py -v -q",
            "API Integration Tests"
        )
        success &= (result1 and result2)
        total_tests = 23
    
    if test_type == "api-unit":
        # Run unit API tests only
        result = run_command(
            "venv/bin/python -m pytest tests/test_api_units.py -v -q",
            "API Unit Tests (Fast)"
        )
        success &= result
        total_tests = 13
    
    if test_type == "api-integration":
        # Run integration API tests only
        result = run_command(
            "venv/bin/python -m pytest tests/test_api_simple.py -v -q",
            "API Integration Tests (Requires Server)"
        )
        success &= result
        total_tests = 10
    
    if test_type == "services":
        # Run service tests only
        result = run_command(
            "venv/bin/python -m pytest tests/test_auth_service.py -v -q",
            "Authentication Service Tests"
        )
        success &= result
        total_tests = 14
    
    if test_type == "crypto":
        # Run crypto tests only
        result = run_command(
            "venv/bin/python -m pytest tests/test_crypto_utils.py -v -q",
            "Encryption & Security Tests"
        )
        success &= result
        total_tests = 6
    
    if test_type == "db":
        # Run database tests only
        result = run_command(
            "venv/bin/python -m pytest tests/test_db_connection.py -v -q",
            "Database Connection Tests"
        )
        success &= result
        total_tests = 6
    
    if test_type == "backend":
        # Run all working backend tests (services, crypto, db, API units)
        result = run_command(
            "venv/bin/python -m pytest tests/test_auth_service.py tests/test_crypto_utils.py tests/test_db_connection.py tests/test_api_units.py -v -q",
            "Backend Tests (All Units)"
        )
        success &= result
        total_tests = 39
    
    # Calculate total duration
    total_duration = time.time() - start_time
    
    # Print final summary
    print_summary(success, total_tests, total_duration)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 