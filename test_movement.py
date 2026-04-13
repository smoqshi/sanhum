#!/usr/bin/env python3
"""
Test script to verify robot movement functionality
"""

import sys
import os
import time

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_movement():
    """Test robot movement functionality"""
    print("Testing Robot Movement...")
    
    try:
        import gui_main
        
        # Create GUI instance
        app = gui_main.FullyIntegratedRobotGUI()
        
        print("  GUI created successfully")
        
        # Test keyboard input simulation
        print("  Testing keyboard input simulation...")
        
        # Simulate W key press (forward)
        app.on_key_press('w')
        print("    W key pressed")
        
        # Wait for input processing - give it more time
        time.sleep(0.5)  # Increased delay
        
        # Check if target velocity is set
        print(f"    Target velocity after 0.5s: Linear={app.target_velocity['linear']:.2f}, Angular={app.target_velocity['angular']:.2f}")
        
        if app.target_velocity['linear'] > 0.1:  # Increased threshold
            print(f"    OK: Forward velocity set: {app.target_velocity['linear']:.2f} m/s")
        else:
            print(f"    FAILED: No forward velocity: {app.target_velocity['linear']:.2f} m/s")
            
            # Debug: check key state and emergency stop
            print(f"    Debug: key_pressed['w'] = {app.key_pressed['w']}")
            print(f"    Debug: emergency_stop = {app.emergency_stop}")
            print(f"    Debug: input_thread_running = {app.input_thread_running}")
            return False
        
        # Simulate W key release
        app.on_key_release('w')
        print("    W key released")
        
        # Wait for input processing
        time.sleep(0.1)
        
        # Check if velocity returns to zero (with smoothing)
        if app.target_velocity['linear'] < 0.5:  # Should be smoothing down
            print(f"    OK: Velocity smoothing: {app.target_velocity['linear']:.2f} m/s")
        else:
            print(f"    WARNING: Velocity not smoothing: {app.target_velocity['linear']:.2f} m/s")
        
        # Test simulation update
        print("  Testing simulation update...")
        
        # Set velocity directly
        app.target_velocity['linear'] = 1.0
        app.target_velocity['angular'] = 0.5
        
        # Update simulation
        app.robot_sim.set_velocity(app.target_velocity['linear'], app.target_velocity['angular'])
        app.robot_sim.update(0.1)
        
        # Check if robot moved
        if app.robot_sim.position.x > 0:
            print(f"    OK: Robot moved to X: {app.robot_sim.position.x:.3f}m")
        else:
            print(f"    FAILED: Robot didn't move: X: {app.robot_sim.position.x:.3f}m")
            return False
        
        # Test angular movement
        print("  Testing angular movement...")
        
        app.target_velocity['linear'] = 0.0
        app.target_velocity['angular'] = 1.0
        
        initial_orientation = app.robot_sim.orientation
        app.robot_sim.set_velocity(app.target_velocity['linear'], app.target_velocity['angular'])
        app.robot_sim.update(0.1)
        
        if app.robot_sim.orientation != initial_orientation:
            print(f"    OK: Robot rotated from {initial_orientation:.3f} to {app.robot_sim.orientation:.3f} rad")
        else:
            print(f"    FAILED: Robot didn't rotate: {app.robot_sim.orientation:.3f} rad")
            return False
        
        print("  All movement tests passed!")
        return True
        
    except Exception as e:
        print(f"  ERROR: {e}")
        return False

def test_keyboard_binding():
    """Test keyboard binding"""
    print("Testing Keyboard Binding...")
    
    try:
        import gui_main
        
        app = gui_main.FullyIntegratedRobotGUI()
        
        # Test key states
        print("  Testing key states...")
        
        # Press W key
        app.on_key_press('w')
        if app.key_pressed['w']:
            print("    OK: W key registered as pressed")
        else:
            print("    FAILED: W key not registered")
            return False
        
        # Release W key
        app.on_key_release('w')
        if not app.key_pressed['w']:
            print("    OK: W key registered as released")
        else:
            print("    FAILED: W key still registered as pressed")
            return False
        
        # Test multiple keys
        app.on_key_press('w')
        app.on_key_press('a')
        app.on_key_press('q')
        
        if app.key_pressed['w'] and app.key_pressed['a'] and app.key_pressed['q']:
            print("    OK: Multiple keys registered")
        else:
            print("    FAILED: Multiple keys not registered")
            return False
        
        # Clear all keys
        app.key_pressed.clear()
        app.key_pressed = defaultdict(bool)
        
        print("  Keyboard binding tests passed!")
        return True
        
    except Exception as e:
        print(f"  ERROR: {e}")
        return False

def main():
    print("=== Robot Movement Testing ===\n")
    
    tests = [
        ("Keyboard Binding", test_keyboard_binding),
        ("Movement Functionality", test_movement)
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
        print("\nRobot movement system is working correctly!")
        print("Try running the GUI and pressing W/A/S/D keys to move the robot.")
    else:
        print("\nSome movement tests failed.")
        print("Please check the failed components.")

if __name__ == "__main__":
    from collections import defaultdict
    main()
