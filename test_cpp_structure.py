#!/usr/bin/env python3
"""
Test script to validate C++ code structure and Python interfaces
"""

import os
import re

def test_cpp_structure():
    """Test C++ code structure"""
    print("Testing C++ code structure...")
    
    cpp_file = "src/sanhum_robot_gui.cpp"
    if not os.path.exists(cpp_file):
        print(f"ERROR: {cpp_file} not found")
        return False
        
    with open(cpp_file, 'r') as f:
        content = f.read()
    
    # Check for key components
    checks = [
        ("class RobotSimulation", "Robot simulation class"),
        ("class ESP32Interface", "ESP32 interface class"),
        ("class ArduinoInterface", "Arduino interface class"),
        ("class CameraInterface", "Camera interface class"),
        ("class SanhumRobotGUI", "Main GUI class"),
        ("QMainWindow", "Qt main window"),
        ("QTimer", "Qt timer"),
        ("std::atomic", "Atomic operations"),
        ("std::thread", "Threading support"),
        ("updateSimulation", "Simulation update method"),
        ("updateDisplay", "Display update method"),
        ("keyPressEvent", "Keyboard event handling"),
        ("60 Hz", "60 Hz update rate")
    ]
    
    all_passed = True
    for pattern, description in checks:
        if pattern in content:
            print(f"  OK: {description}")
        else:
            print(f"  MISSING: {description}")
            all_passed = False
    
    return all_passed

def test_python_interfaces():
    """Test Python interfaces"""
    print("\nTesting Python interfaces...")
    
    interfaces = [
        ("src/esp32_interface.py", "ESP32Interface"),
        ("src/arduino_interface.py", "ArduinoInterface"),
        ("src/camera_interface.py", "CameraInterface"),
        ("src/rpi_gpio_interface.py", "RPiGPIOInterface"),
        ("src/input_controller.py", "InputController"),
        ("src/robot_simulation.py", "RobotSimulation"),
        ("src/robot_interface.py", "RobotInterfaceManager")
    ]
    
    all_passed = True
    for file_path, class_name in interfaces:
        if os.path.exists(file_path):
            print(f"  OK: {file_path}")
            
            # Check if class exists
            with open(file_path, 'r') as f:
                content = f.read()
            
            if f"class {class_name}" in content:
                print(f"    OK: {class_name} class found")
            else:
                print(f"    MISSING: {class_name} class")
                all_passed = False
        else:
            print(f"  MISSING: {file_path}")
            all_passed = False
    
    return all_passed

def test_cmake_structure():
    """Test CMakeLists.txt structure"""
    print("\nTesting CMakeLists.txt structure...")
    
    if not os.path.exists("CMakeLists.txt"):
        print("  ERROR: CMakeLists.txt not found")
        return False
        
    with open("CMakeLists.txt", 'r') as f:
        content = f.read()
    
    checks = [
        ("Qt6", "Qt6 framework"),
        ("sanhum_robot_gui_cpp", "C++ GUI executable"),
        ("HIGH_PERFORMANCE", "High performance flag"),
        ("motor_driver.cpp", "Motor driver"),
        ("esp32_driver.cpp", "ESP32 driver"),
        ("arduino_sensors.cpp", "Arduino sensors"),
        ("cameras.cpp", "Camera system"),
        ("rclcpp", "ROS2 support")
    ]
    
    all_passed = True
    for pattern, description in checks:
        if pattern in content:
            print(f"  OK: {description}")
        else:
            print(f"  MISSING: {description}")
            all_passed = False
    
    return all_passed

def test_project_structure():
    """Test overall project structure"""
    print("\nTesting project structure...")
    
    required_dirs = [
        "src",
        "include", 
        "launch",
        "config",
        "scripts"
    ]
    
    required_files = [
        "CMakeLists.txt",
        "README.md",
        "package.xml",
        "src/robot_main.cpp",
        "src/motor_driver.cpp",
        "src/esp32_driver.cpp",
        "src/arduino_sensors.cpp",
        "src/cameras.cpp"
    ]
    
    all_passed = True
    
    # Check directories
    for dir_path in required_dirs:
        if os.path.exists(dir_path):
            print(f"  OK: {dir_path}/ directory")
        else:
            print(f"  MISSING: {dir_path}/ directory")
            all_passed = False
    
    # Check files
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"  OK: {file_path}")
        else:
            print(f"  MISSING: {file_path}")
            all_passed = False
    
    return all_passed

def main():
    print("=== Sanhum Robot Project Validation ===\n")
    
    results = []
    results.append(("C++ Structure", test_cpp_structure()))
    results.append(("Python Interfaces", test_python_interfaces()))
    results.append(("CMake Structure", test_cmake_structure()))
    results.append(("Project Structure", test_project_structure()))
    
    print("\n=== Test Results ===")
    all_passed = True
    for test_name, passed in results:
        status = "PASSED" if passed else "FAILED"
        print(f"{test_name}: {status}")
        if not passed:
            all_passed = False
    
    print(f"\nOverall: {'PASSED' if all_passed else 'FAILED'}")
    
    if all_passed:
        print("\nProject structure is valid and ready for compilation!")
        print("To build the C++ GUI:")
        print("1. Install Qt6 development tools")
        print("2. Install ROS2 (foxy/galactic/humble)")
        print("3. Run: colcon build")
        print("4. Run: . install/setup.bash")
        print("5. Run: ros2 run sanhum sanhum_robot_gui_cpp")
    else:
        print("\nSome issues found. Please fix them before building.")

if __name__ == "__main__":
    main()
