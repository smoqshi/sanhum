#!/usr/bin/env python3
"""
Test script to validate all Python interfaces work correctly
"""

import sys
import time
import threading
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_esp32_interface():
    """Test ESP32 interface"""
    print("Testing ESP32 Interface...")
    
    try:
        from esp32_interface import get_esp32_interface
        
        # Test simulation interface
        esp32 = get_esp32_interface(simulation=True)
        
        if esp32.connect():
            print("  OK: ESP32 connected")
            
            # Test joint commands
            if esp32.send_joint_command([0, 45, -45, 90, 0]):
                print("  OK: Joint command sent")
            else:
                print("  FAILED: Joint command failed")
                return False
                
            # Test gripper command
            if esp32.send_gripper_command(100):
                print("  OK: Gripper command sent")
            else:
                print("  FAILED: Gripper command failed")
                return False
                
            # Test home command
            if esp32.home_manipulator():
                print("  OK: Home command sent")
            else:
                print("  FAILED: Home command failed")
                return False
                
            esp32.disconnect()
            print("  OK: ESP32 disconnected")
            return True
        else:
            print("  FAILED: ESP32 connection failed")
            return False
            
    except Exception as e:
        print(f"  ERROR: {e}")
        return False

def test_arduino_interface():
    """Test Arduino interface"""
    print("Testing Arduino Interface...")
    
    try:
        from arduino_interface import get_arduino_interface
        
        # Test simulation interface
        arduino = get_arduino_interface(simulation=True)
        
        def sensor_callback(data):
            print(f"    Sensor data: {data}")
        
        if arduino.connect():
            print("  OK: Arduino connected")
            
            arduino.set_sensor_callback(sensor_callback)
            
            # Get sensor data
            data = arduino.get_sensor_data()
            if data and 'sensor_0' in data:
                print("  OK: Sensor data received")
                print(f"    Front ultrasonic: {data['sensor_0']:.2f}m")
                print(f"    Rear ultrasonic: {data['sensor_1']:.2f}m")
            else:
                print("  FAILED: No sensor data")
                return False
                
            arduino.disconnect()
            print("  OK: Arduino disconnected")
            return True
        else:
            print("  FAILED: Arduino connection failed")
            return False
            
    except Exception as e:
        print(f"  ERROR: {e}")
        return False

def test_camera_interface():
    """Test Camera interface"""
    print("Testing Camera Interface...")
    
    try:
        from camera_interface import get_camera_interface
        
        # Test simulation interface
        camera = get_camera_interface(simulation=True, camera_indices=[0, 1, 2])
        
        def frame_callback(frame, camera_idx):
            print(f"    Frame received from camera {camera_idx}: {frame.shape}")
        
        if camera.connect():
            print("  OK: Camera connected")
            
            camera.set_frame_callback(0, frame_callback)
            camera.set_frame_callback(1, frame_callback)
            camera.set_frame_callback(2, frame_callback)
            
            if camera.start_capture():
                print("  OK: Camera capture started")
                
                # Test for a short time
                time.sleep(0.5)
                
                # Get camera info
                info = camera.get_camera_info()
                connected_count = sum(1 for cam_info in info.values() if cam_info['connected'])
                print(f"  OK: {connected_count}/{len(info)} cameras connected")
                
                # Test snapshot
                if camera.take_snapshot(0, "test_snapshot.jpg"):
                    print("  OK: Snapshot saved")
                else:
                    print("  FAILED: Snapshot failed")
                    return False
                    
                camera.stop_capture()
                camera.disconnect()
                print("  OK: Camera disconnected")
                return True
            else:
                print("  FAILED: Camera capture failed")
                return False
        else:
            print("  FAILED: Camera connection failed")
            return False
            
    except Exception as e:
        print(f"  ERROR: {e}")
        return False

def test_robot_simulation():
    """Test Robot simulation"""
    print("Testing Robot Simulation...")
    
    try:
        from robot_simulation import RobotSimulation, Vector3
        
        robot = RobotSimulation()
        
        # Test initial state
        pos = robot.position
        if pos.x == 0.0 and pos.y == 0.0:
            print("  OK: Initial position correct")
        else:
            print("  FAILED: Initial position incorrect")
            return False
            
        # Test velocity setting
        robot.set_velocity(1.0, 0.5)
        if robot.linear_velocity == 1.0 and robot.angular_velocity == 0.5:
            print("  OK: Velocity setting works")
        else:
            print("  FAILED: Velocity setting failed")
            return False
            
        # Test manipulator
        robot.set_manipulator_joints(45, 30, -45, 90, 0, 50)
        if robot.joint1_angle == math.radians(45):
            print("  OK: Manipulator setting works")
        else:
            print("  FAILED: Manipulator setting failed")
            return False
            
        # Test update
        robot.update(0.1)
        if robot.position.x > 0.0:  # Should have moved
            print("  OK: Simulation update works")
        else:
            print("  FAILED: Simulation update failed")
            return False
            
        # Test reset
        robot.reset()
        if robot.position.x == 0.0 and robot.position.y == 0.0:
            print("  OK: Reset works")
        else:
            print("  FAILED: Reset failed")
            return False
            
        return True
        
    except Exception as e:
        print(f"  ERROR: {e}")
        return False

def test_input_controller():
    """Test Input controller"""
    print("Testing Input Controller...")
    
    try:
        from input_controller import InputController
        
        def callback(data_type, data):
            print(f"    Callback: {data_type} -> {data}")
        
        controller = InputController(gui_callback=callback)
        
        controller.start()
        print("  OK: Controller started")
        
        status = controller.get_control_status()
        if 'mode' in status and 'linear_velocity' in status:
            print("  OK: Control status available")
        else:
            print("  FAILED: Control status missing")
            return False
            
        controller.stop()
        print("  OK: Controller stopped")
        return True
        
    except Exception as e:
        print(f"  ERROR: {e}")
        return False

def main():
    print("=== Python Interface Testing ===\n")
    
    import math  # Needed for robot simulation test
    
    tests = [
        ("ESP32 Interface", test_esp32_interface),
        ("Arduino Interface", test_arduino_interface),
        ("Camera Interface", test_camera_interface),
        ("Robot Simulation", test_robot_simulation),
        ("Input Controller", test_input_controller)
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
        print("\nAll Python interfaces are working correctly!")
        print("The project is ready for both Python and C++ deployment.")
    else:
        print("\nSome interfaces have issues. Please check the failed tests.")

if __name__ == "__main__":
    main()
