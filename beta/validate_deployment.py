#!/usr/bin/env python
"""
Pre-deployment validation script for Render deployment.
Tests all requirements are met before pushing to production.
"""

import os
import sys
import subprocess
from pathlib import Path

def print_section(title):
    """Print a formatted section header."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def check_file_exists(filepath, description):
    """Check if a file exists."""
    if Path(filepath).exists():
        print(f"✓ {description}: {filepath}")
        return True
    else:
        print(f"✗ {description}: {filepath} - NOT FOUND")
        return False

def check_python_module(module_name):
    """Check if a Python module can be imported."""
    try:
        __import__(module_name)
        print(f"✓ Python module: {module_name}")
        return True
    except ImportError:
        print(f"✗ Python module: {module_name} - NOT INSTALLED")
        return False

def run_command(cmd, description):
    """Run a command and check if it succeeds."""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f"✓ {description}")
            return True
        else:
            print(f"✗ {description}")
            print(f"  Error: {result.stderr[:200]}")
            return False
    except Exception as e:
        print(f"✗ {description}: {str(e)}")
        return False

def main():
    """Run all pre-deployment checks."""
    print_section("🚀 Pre-Deployment Validation for Render")
    
    checks_passed = 0
    checks_total = 0
    
    # Check 1: Required files
    print_section("1️⃣  Required Files")
    required_files = [
        ("api_server.py", "FastAPI app"),
        ("requirements.txt", "Python dependencies"),
        ("render.yaml", "Render config"),
        ("Procfile", "Procfile"),
        (".env.example", "Environment example"),
    ]
    
    for filepath, description in required_files:
        checks_total += 1
        if check_file_exists(filepath, description):
            checks_passed += 1
    
    # Check 2: Python version
    print_section("2️⃣  Python Environment")
    checks_total += 1
    py_version = f"{sys.version_info.major}.{sys.version_info.minor}"
    if sys.version_info >= (3, 9):
        print(f"✓ Python version: {py_version}")
        checks_passed += 1
    else:
        print(f"✗ Python version: {py_version} (need >= 3.9)")
    
    # Check 3: Core dependencies
    print_section("3️⃣  Core Python Dependencies")
    core_modules = ["fastapi", "uvicorn", "firebase_admin", "sqlalchemy", "selenium"]
    for module in core_modules:
        checks_total += 1
        if check_python_module(module):
            checks_passed += 1
    
    # Check 4: API server syntax
    print_section("4️⃣  API Server Syntax")
    checks_total += 1
    if run_command("python -m py_compile api_server.py", "api_server.py syntax check"):
        checks_passed += 1
    
    # Check 5: Git status
    print_section("5️⃣  Git Repository")
    checks_total += 1
    if run_command("git status", "Git repo check"):
        checks_passed += 1
    
    # Check 6: Environment variables
    print_section("6️⃣  Environment Variables")
    checks_total += 1
    env_vars_ok = True
    
    if os.getenv("FB_SCRAPER_API_TOKEN"):
        print("✓ FB_SCRAPER_API_TOKEN is set")
    else:
        print("⚠ FB_SCRAPER_API_TOKEN not set (add in Render dashboard)")
        env_vars_ok = False
    
    if Path("firebase_credentials.json").exists() or os.getenv("FIREBASE_CREDENTIALS"):
        print("✓ Firebase credentials available")
    else:
        print("⚠ Firebase credentials not found (add as Secret File in Render)")
        env_vars_ok = False
    
    if env_vars_ok:
        checks_passed += 1
    
    # Check 7: Requirements.txt validation
    print_section("7️⃣  Requirements Validation")
    checks_total += 1
    if run_command("python -m pip check", "No conflicting packages"):
        checks_passed += 1
    
    # Summary
    print_section("📊 Summary")
    percentage = (checks_passed / checks_total) * 100
    print(f"Checks passed: {checks_passed}/{checks_total} ({percentage:.0f}%)")
    
    if checks_passed == checks_total:
        print("\n✅ All checks passed! Ready to deploy to Render.")
        return 0
    else:
        print(f"\n⚠️  {checks_total - checks_passed} check(s) failed. See above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
