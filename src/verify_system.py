#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════
JARVIS SYSTEM VERIFICATION TEST
═══════════════════════════════════════════════════════════════════════════

This script performs automated checks to verify your system is ready.
Run this BEFORE attempting to launch Jarvis.

Usage:
    python3 verify_system.py

Author: Nittaany (Satyam C)
Date: January 30, 2026
═══════════════════════════════════════════════════════════════════════════
"""

import os
import sys
import subprocess
from pathlib import Path

# Color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_header(text):
    """Print a formatted section header"""
    print(f"\n{BLUE}{'=' * 70}{RESET}")
    print(f"{BLUE}{text.center(70)}{RESET}")
    print(f"{BLUE}{'=' * 70}{RESET}\n")

def print_check(test_name, passed, details=""):
    """Print a test result"""
    status = f"{GREEN}✅ PASS{RESET}" if passed else f"{RED}❌ FAIL{RESET}"
    print(f"[{status}] {test_name}")
    if details:
        print(f"         {details}")

def check_python_version():
    """Verify Python version is 3.10+"""
    version = sys.version_info
    required = (3, 10)
    
    passed = version >= required
    details = f"Current: {version.major}.{version.minor}.{version.micro}"
    
    print_check("Python Version (≥3.10)", passed, details)
    return passed

def check_file_structure():
    """Verify all required files exist"""
    required_files = [
        'src/Jarvis.py',
        'src/app.py',
        'src/vision_backend.py',
        'src/controllers/__init__.py',
        'src/controllers/HCI_Controller.py',
        'src/controllers/ISL_Controller.py',
        'src/web/index.html'
    ]
    
    all_exist = True
    missing = []
    
    for filepath in required_files:
        if not os.path.exists(filepath):
            all_exist = False
            missing.append(filepath)
    
    details = ""
    if not all_exist:
        details = f"Missing: {', '.join(missing)}"
    
    print_check("File Structure", all_exist, details)
    return all_exist

def check_dependencies():
    """Verify critical Python packages are installed"""
    packages = {
        'mediapipe': '0.10.9',
        'cv2': 'opencv-python',
        'numpy': 'numpy',
        'pyautogui': 'pyautogui',
        'eel': 'eel'
    }
    
    all_installed = True
    missing = []
    
    for module_name, package_name in packages.items():
        try:
            __import__(module_name)
        except ImportError:
            all_installed = False
            missing.append(package_name)
    
    details = ""
    if not all_installed:
        details = f"Missing: {', '.join(missing)}"
        details += f"\nRun: pip install {' '.join(missing)}"
    
    print_check("Core Dependencies", all_installed, details)
    return all_installed

def check_optional_dependencies():
    """Check optional voice dependencies"""
    packages = ['pyttsx3', 'speech_recognition']
    
    all_installed = True
    missing = []
    
    for package in packages:
        try:
            __import__(package)
        except ImportError:
            all_installed = False
            missing.append(package)
    
    details = ""
    if not all_installed:
        details = f"Missing: {', '.join(missing)}"
        details += "\n(System will run in TEXT MODE without these)"
    else:
        details = "(Voice features available)"
    
    # This is a warning, not a failure
    status = all_installed
    print_check("Voice Dependencies (Optional)", status, details)
    return True  # Don't fail overall test

def check_venv():
    """Verify we're running in a virtual environment"""
    in_venv = hasattr(sys, 'real_prefix') or (
        hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
    )
    
    details = ""
    if not in_venv:
        details = "Run: source py3.10-venv/bin/activate"
    else:
        details = f"Active: {sys.prefix}"
    
    print_check("Virtual Environment", in_venv, details)
    return in_venv

def check_camera_access():
    """Attempt to open camera"""
    try:
        import cv2
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            # Try camera 1
            cap = cv2.VideoCapture(1)
        
        success = cap.isOpened()
        
        if success:
            # Read one frame to verify
            ret, frame = cap.read()
            success = ret and frame is not None
        
        cap.release()
        
        details = ""
        if not success:
            details = "Grant camera permission: System Preferences → Security & Privacy → Camera"
        
        print_check("Camera Access", success, details)
        return success
        
    except Exception as e:
        print_check("Camera Access", False, f"Error: {str(e)}")
        return False

def check_web_folder():
    """Verify web assets exist and are accessible"""
    web_path = 'src/web'
    
    if not os.path.exists(web_path):
        print_check("Web Folder", False, f"{web_path} not found")
        return False
    
    required = ['index.html', 'css', 'js']
    missing = [item for item in required if not os.path.exists(f"{web_path}/{item}")]
    
    success = len(missing) == 0
    details = f"Missing: {', '.join(missing)}" if not success else f"Located at: {os.path.abspath(web_path)}"
    
    print_check("Web Assets", success, details)
    return success

def run_syntax_check():
    """Verify Python files have no syntax errors"""
    files = [
        'src/Jarvis.py',
        'src/app.py',
        'src/vision_backend.py',
        'src/controllers/HCI_Controller.py',
        'src/controllers/ISL_Controller.py'
    ]
    
    all_valid = True
    errors = []
    
    for filepath in files:
        if not os.path.exists(filepath):
            continue
        
        try:
            with open(filepath, 'r') as f:
                compile(f.read(), filepath, 'exec')
        except SyntaxError as e:
            all_valid = False
            errors.append(f"{filepath}: Line {e.lineno}")
    
    details = ""
    if not all_valid:
        details = f"Syntax errors in: {', '.join(errors)}"
    
    print_check("Python Syntax", all_valid, details)
    return all_valid

def main():
    """Run all verification tests"""
    print_header("JARVIS SYSTEM VERIFICATION")
    
    print(f"{YELLOW}Running automated checks...{RESET}\n")
    
    # Track results
    results = {
        "Python Version": check_python_version(),
        "Virtual Environment": check_venv(),
        "File Structure": check_file_structure(),
        "Core Dependencies": check_dependencies(),
        "Voice Dependencies": check_optional_dependencies(),
        "Web Assets": check_web_folder(),
        "Python Syntax": run_syntax_check(),
        "Camera Access": check_camera_access()
    }
    
    # Summary
    print_header("VERIFICATION SUMMARY")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    critical_passed = all([
        results["Python Version"],
        results["File Structure"],
        results["Core Dependencies"],
        results["Web Assets"]
    ])
    
    print(f"Tests Passed: {passed}/{total}")
    
    if critical_passed:
        print(f"\n{GREEN}✅ SYSTEM READY{RESET}")
        print(f"{GREEN}You can now run: python3 src/Jarvis.py{RESET}\n")
        
        # Provide specific guidance
        if not results["Voice Dependencies"]:
            print(f"{YELLOW}⚠️  Note: Voice features disabled. System will run in TEXT MODE.{RESET}")
            print(f"{YELLOW}   Type your commands instead of speaking them.{RESET}\n")
        
        if not results["Camera Access"]:
            print(f"{YELLOW}⚠️  Note: Camera access denied.{RESET}")
            print(f"{YELLOW}   Grant permission before launching vision system.{RESET}\n")
        
        return 0
    else:
        print(f"\n{RED}❌ SYSTEM NOT READY{RESET}")
        print(f"{RED}Fix the failed checks above before proceeding.{RESET}\n")
        
        # Provide actionable fixes
        if not results["File Structure"]:
            print(f"{YELLOW}Fix: Ensure you're in the Major-Project directory{RESET}")
            print(f"     Run: cd /path/to/Major-Project\n")
        
        if not results["Core Dependencies"]:
            print(f"{YELLOW}Fix: Install missing packages{RESET}")
            print(f"     Run: pip install mediapipe==0.10.9 opencv-python pyautogui eel\n")
        
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Verification cancelled by user.{RESET}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{RED}Verification failed with error: {e}{RESET}")
        sys.exit(1)