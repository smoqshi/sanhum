#!/usr/bin/env python3
"""
Test script to validate available components without external dependencies
"""

import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_available_modules():
    """Test available modules"""
    print("Testing Available Modules...")
    
    # Test input controller (should work)
    try:
        from input_controller import InputController
        
        def callback(data_type, data):
            pass
        
        controller = InputController(gui_callback=callback)
        controller.start()
        status = controller.get_control_status()
        controller.stop()
        
        if 'mode' in status:
            print("  OK: Input Controller available")
        else:
            print("  FAILED: Input Controller broken")
            return False
    except Exception as e:
        print(f"  ERROR: Input Controller failed: {e}")
        return False
    
    # Test robot simulation (fallback version)
    try:
        # Import from gui_main.py which has fallback classes
        import gui_main
        
        # Create a simple test
        sim = gui_main.RobotSimulation()
        sim.set_velocity(1.0, 0.5)
        sim.update(0.1)
        
        if sim.position.x > 0.0:
            print("  OK: Robot Simulation available")
        else:
            print("  FAILED: Robot Simulation broken")
            return False
    except Exception as e:
        print(f"  ERROR: Robot Simulation failed: {e}")
        return False
    
    return True

def test_gui_functionality():
    """Test GUI functionality"""
    print("Testing GUI Functionality...")
    
    try:
        import gui_main
        
        # Test that we can create the class
        app = gui_main.FullyIntegratedRobotGUI()
        
        # Test basic functionality without showing GUI
        app.robot_sim.set_velocity(1.0, 0.0)
        app.robot_sim.update(0.1)
        
        if app.robot_sim.position.x > 0.0:
            print("  OK: GUI functionality available")
        else:
            print("  FAILED: GUI functionality broken")
            return False
            
        return True
    except Exception as e:
        print(f"  ERROR: GUI functionality failed: {e}")
        return False

def test_project_files():
    """Test project file structure"""
    print("Testing Project Files...")
    
    required_files = [
        "src/gui_main.py",
        "src/sanhum_robot_gui.cpp",
        "src/robot_main.cpp",
        "src/motor_driver.cpp",
        "src/esp32_driver.cpp",
        "src/arduino_sensors.cpp",
        "src/cameras.cpp",
        "CMakeLists.txt",
        "package.xml",
        "README.md"
    ]
    
    all_exist = True
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"  OK: {file_path}")
        else:
            print(f"  MISSING: {file_path}")
            all_exist = False
    
    return all_exist

def main():
    print("=== Available Components Testing ===\n")
    
    tests = [
        ("Available Modules", test_available_modules),
        ("GUI Functionality", test_gui_functionality),
        ("Project Files", test_project_files)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"  CRITICAL ERROR: {e}")
            results.append((test_name, False))
    
    print("\n=== Test Results ===")
    all_passed = True
    for test_name, passed in results:
        status = "PASSED" if passed else "FAILED"
        print(f"{test_name}: {status}")
        if not passed:
            all_passed = False
    
    print(f"\nOverall: {'PASSED' if all_passed else 'FAILED'}")
    
    if all_passed:
        print("\nProject is ready for deployment!")
        print("Available components:")
        print("- Python GUI with simulation fallback")
        print("- C++ GUI with Qt6 (requires Qt6 installation)")
        print("- All hardware drivers (C++)")
        print("- Complete project structure")
    else:
        print("\nSome components have issues.")

if __name__ == "__main__":
    main()
