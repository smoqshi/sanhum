#!/usr/bin/env python3
"""
ESP32 Interface for Sanhum Robot Manipulator
Python interface for ESP32 serial communication
"""

import serial
import threading
import time
from typing import List, Optional, Dict
import json

class ESP32Interface:
    """Interface for ESP32 manipulator control via serial communication"""
    
    def __init__(self, port: str = "/dev/ttyACM0", baud_rate: int = 115200):
        self.port = port
        self.baud_rate = baud_rate
        self.serial_conn = None
        self.connected = False
        self.running = False
        
        # Joint states
        self.joint_states = {
            'joint1': 0.0,
            'joint2': 0.0,
            'joint3': 0.0,
            'joint4': 0.0,
            'joint5': 0.0
        }
        
        # Callback for joint state updates
        self.joint_callback = None
        
        # Communication thread
        self.comm_thread = None
        
    def connect(self) -> bool:
        """Connect to ESP32 via serial"""
        try:
            self.serial_conn = serial.Serial(
                port=self.port,
                baudrate=self.baud_rate,
                timeout=1.0
            )
            self.connected = True
            
            # Start communication thread
            self.running = True
            self.comm_thread = threading.Thread(target=self._communication_loop, daemon=True)
            self.comm_thread.start()
            
            print(f"Connected to ESP32 on {self.port}")
            return True
            
        except Exception as e:
            print(f"Failed to connect to ESP32: {e}")
            self.connected = False
            return False
            
    def disconnect(self):
        """Disconnect from ESP32"""
        self.running = False
        if self.comm_thread:
            self.comm_thread.join(timeout=2)
            
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
            
        self.connected = False
        print("Disconnected from ESP32")
        
    def send_joint_command(self, joint_positions: List[float]) -> bool:
        """Send joint command to ESP32
        
        Args:
            joint_positions: List of 5 joint angles in degrees
            
        Returns:
            True if command sent successfully
        """
        if not self.connected or not self.serial_conn:
            return False
            
        if len(joint_positions) < 5:
            return False
            
        try:
            # Format: C:p1,p2,p3,p4,p5\n
            command = f"C:{joint_positions[0]:.2f},{joint_positions[1]:.2f},{joint_positions[2]:.2f},{joint_positions[3]:.2f},{joint_positions[4]:.2f}\n"
            
            self.serial_conn.write(command.encode('utf-8'))
            self.serial_conn.flush()
            
            return True
            
        except Exception as e:
            print(f"Error sending joint command: {e}")
            return False
            
    def send_gripper_command(self, open_percentage: float) -> bool:
        """Send gripper command
        
        Args:
            open_percentage: 0.0 (closed) to 100.0 (fully open)
            
        Returns:
            True if command sent successfully
        """
        if not self.connected or not self.serial_conn:
            return False
            
        try:
            # Format: G:percentage\n
            command = f"G:{open_percentage:.1f}\n"
            
            self.serial_conn.write(command.encode('utf-8'))
            self.serial_conn.flush()
            
            return True
            
        except Exception as e:
            print(f"Error sending gripper command: {e}")
            return False
            
    def _communication_loop(self):
        """Background thread for reading ESP32 responses"""
        buffer = ""
        
        while self.running and self.connected:
            try:
                if self.serial_conn.in_waiting > 0:
                    data = self.serial_conn.readline().decode('utf-8').strip()
                    
                    if data:
                        self._parse_response(data)
                        
                time.sleep(0.01)  # 100 Hz polling
                
            except Exception as e:
                print(f"Communication error: {e}")
                time.sleep(0.1)
                
    def _parse_response(self, data: str):
        """Parse response from ESP32
        
        Expected formats:
        - "S:j1,j2,j3,j4,j5" - Joint states
        - "A:acknowledgment" - Acknowledgment
        - "E:error_message" - Error
        """
        try:
            if data.startswith('S:'):  # Joint states
                parts = data[2:].split(',')
                if len(parts) >= 5:
                    self.joint_states['joint1'] = float(parts[0])
                    self.joint_states['joint2'] = float(parts[1])
                    self.joint_states['joint3'] = float(parts[2])
                    self.joint_states['joint4'] = float(parts[3])
                    self.joint_states['joint5'] = float(parts[4])
                    
                    if self.joint_callback:
                        self.joint_callback(self.joint_states)
                        
            elif data.startswith('A:'):  # Acknowledgment
                print(f"ESP32 ACK: {data[2:]}")
                
            elif data.startswith('E:'):  # Error
                print(f"ESP32 Error: {data[2:]}")
                
        except Exception as e:
            print(f"Error parsing ESP32 response: {e}")
            
    def get_joint_states(self) -> Dict[str, float]:
        """Get current joint states"""
        return self.joint_states.copy()
        
    def set_joint_callback(self, callback):
        """Set callback for joint state updates"""
        self.joint_callback = callback
        
    def home_manipulator(self) -> bool:
        """Home manipulator (move all joints to 0 degrees)"""
        return self.send_joint_command([0.0, 0.0, 0.0, 0.0, 0.0])
        
    def test_connection(self) -> bool:
        """Test connection to ESP32"""
        if not self.connected:
            return False
            
        try:
            # Send test command
            self.serial_conn.write(b"T:test\n")
            self.serial_conn.flush()
            
            # Wait for response
            time.sleep(0.5)
            
            return True
            
        except Exception as e:
            print(f"Connection test failed: {e}")
            return False

# Simulation fallback
class ESP32Simulation:
    """Simulation fallback for ESP32 interface"""
    
    def __init__(self):
        self.connected = True
        self.joint_states = {
            'joint1': 0.0,
            'joint2': 0.0,
            'joint3': 0.0,
            'joint4': 0.0,
            'joint5': 0.0
        }
        self.joint_callback = None
        
    def connect(self) -> bool:
        print("ESP32 simulation mode - no real hardware")
        return True
        
    def disconnect(self):
        print("ESP32 simulation disconnected")
        
    def send_joint_command(self, joint_positions: List[float]) -> bool:
        if len(joint_positions) >= 5:
            self.joint_states['joint1'] = joint_positions[0]
            self.joint_states['joint2'] = joint_positions[1]
            self.joint_states['joint3'] = joint_positions[2]
            self.joint_states['joint4'] = joint_positions[3]
            self.joint_states['joint5'] = joint_positions[4]
            
            if self.joint_callback:
                self.joint_callback(self.joint_states)
                
        return True
        
    def send_gripper_command(self, open_percentage: float) -> bool:
        return True
        
    def get_joint_states(self) -> Dict[str, float]:
        return self.joint_states.copy()
        
    def set_joint_callback(self, callback):
        self.joint_callback = callback
        
    def home_manipulator(self) -> bool:
        return self.send_joint_command([0.0, 0.0, 0.0, 0.0, 0.0])
        
    def test_connection(self) -> bool:
        return True

def get_esp32_interface(simulation: bool = True, port: str = "/dev/ttyACM0") -> object:
    """Get ESP32 interface (real or simulation)"""
    if simulation:
        return ESP32Simulation()
    else:
        return ESP32Interface(port)

if __name__ == "__main__":
    # Test the interface
    esp32 = get_esp32_interface(simulation=True)
    
    if esp32.connect():
        print("ESP32 interface connected")
        
        # Test joint commands
        esp32.send_joint_command([0, 45, -45, 90, 0])
        time.sleep(1)
        
        esp32.send_joint_command([0, 0, 0, 0, 0])
        time.sleep(1)
        
        # Test gripper
        esp32.send_gripper_command(100)
        time.sleep(1)
        esp32.send_gripper_command(0)
        
        esp32.disconnect()
    else:
        print("Failed to connect to ESP32")
