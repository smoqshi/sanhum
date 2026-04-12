#!/usr/bin/env python3
"""
Arduino Interface for Sanhum Robot Sensors
Python interface for Arduino sensor data via serial communication
"""

import serial
import threading
import time
from typing import List, Optional, Dict, Callable
import json

class ArduinoInterface:
    """Interface for Arduino sensor data via serial communication"""
    
    def __init__(self, port: str = "/dev/ttyUSB0", baud_rate: int = 115200):
        self.port = port
        self.baud_rate = baud_rate
        self.serial_conn = None
        self.connected = False
        self.running = False
        
        # Sensor data
        self.sensor_data = {
            'sensor_0': 0.0,  # Front ultrasonic
            'sensor_1': 0.0,  # Rear ultrasonic
            'sensor_2': 0.0,  # Left infrared
            'sensor_3': 0.0,  # Right infrared
            'sensor_4': 0.0,  # Left side sensor
            'sensor_5': 0.0,  # Right side sensor
        }
        
        # Callback for sensor updates
        self.sensor_callback = None
        
        # Communication thread
        self.comm_thread = None
        
    def connect(self) -> bool:
        """Connect to Arduino via serial"""
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
            
            print(f"Connected to Arduino on {self.port}")
            return True
            
        except Exception as e:
            print(f"Failed to connect to Arduino: {e}")
            self.connected = False
            return False
            
    def disconnect(self):
        """Disconnect from Arduino"""
        self.running = False
        if self.comm_thread:
            self.comm_thread.join(timeout=2)
            
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
            
        self.connected = False
        print("Disconnected from Arduino")
        
    def _communication_loop(self):
        """Background thread for reading Arduino sensor data"""
        buffer = ""
        
        while self.running and self.connected:
            try:
                if self.serial_conn.in_waiting > 0:
                    data = self.serial_conn.readline().decode('utf-8').strip()
                    
                    if data:
                        self._parse_sensor_data(data)
                        
                time.sleep(0.01)  # 100 Hz polling
                
            except Exception as e:
                print(f"Arduino communication error: {e}")
                time.sleep(0.1)
                
    def _parse_sensor_data(self, data: str):
        """Parse sensor data from Arduino
        
        Expected format: "d1,d2,d3,d4,d5,d6" (distances in mm)
        """
        try:
            parts = data.split(',')
            if len(parts) >= 6:
                # Convert mm to meters
                for i in range(6):
                    try:
                        dist_mm = float(parts[i])
                        dist_m = dist_mm / 1000.0
                        self.sensor_data[f'sensor_{i}'] = dist_m
                    except ValueError:
                        continue
                        
                if self.sensor_callback:
                    self.sensor_callback(self.sensor_data)
                    
        except Exception as e:
            print(f"Error parsing Arduino sensor data: {e}")
            
    def get_sensor_data(self) -> Dict[str, float]:
        """Get current sensor data"""
        return self.sensor_data.copy()
        
    def set_sensor_callback(self, callback: Callable[[Dict[str, float]], None]):
        """Set callback for sensor data updates"""
        self.sensor_callback = callback
        
    def request_calibration(self) -> bool:
        """Request sensor calibration"""
        if not self.connected or not self.serial_conn:
            return False
            
        try:
            self.serial_conn.write(b"CAL\n")
            self.serial_conn.flush()
            return True
        except Exception as e:
            print(f"Error requesting calibration: {e}")
            return False
            
    def test_connection(self) -> bool:
        """Test connection to Arduino"""
        if not self.connected:
            return False
            
        try:
            # Send test command
            self.serial_conn.write(b"TEST\n")
            self.serial_conn.flush()
            
            # Wait for response
            time.sleep(0.5)
            
            return True
            
        except Exception as e:
            print(f"Arduino connection test failed: {e}")
            return False

# Simulation fallback
class ArduinoSimulation:
    """Simulation fallback for Arduino interface"""
    
    def __init__(self):
        self.connected = True
        self.sensor_data = {
            'sensor_0': 2.5,  # Front ultrasonic
            'sensor_1': 2.5,  # Rear ultrasonic
            'sensor_2': 0.8,  # Left infrared
            'sensor_3': 0.8,  # Right infrared
            'sensor_4': 1.2,  # Left side sensor
            'sensor_5': 1.2,  # Right side sensor
        }
        self.sensor_callback = None
        self.running = False
        
        # Start simulation thread
        self.sim_thread = threading.Thread(target=self._simulation_loop, daemon=True)
        self.sim_thread.start()
        
    def _simulation_loop(self):
        """Simulate sensor data changes"""
        while True:
            try:
                # Simulate sensor reading variations
                import random
                
                # Ultrasonic sensors (0.5m to 3.0m range)
                self.sensor_data['sensor_0'] = random.uniform(0.5, 3.0)
                self.sensor_data['sensor_1'] = random.uniform(0.5, 3.0)
                
                # Infrared sensors (0.05m to 1.5m range)
                self.sensor_data['sensor_2'] = random.uniform(0.05, 1.5)
                self.sensor_data['sensor_3'] = random.uniform(0.05, 1.5)
                
                # Side sensors (0.2m to 2.0m range)
                self.sensor_data['sensor_4'] = random.uniform(0.2, 2.0)
                self.sensor_data['sensor_5'] = random.uniform(0.2, 2.0)
                
                if self.sensor_callback:
                    self.sensor_callback(self.sensor_data)
                    
                time.sleep(0.1)  # 10 Hz update rate
                
            except Exception as e:
                print(f"Arduino simulation error: {e}")
                time.sleep(1)
                
    def connect(self) -> bool:
        print("Arduino simulation mode - no real hardware")
        return True
        
    def disconnect(self):
        print("Arduino simulation disconnected")
        
    def get_sensor_data(self) -> Dict[str, float]:
        return self.sensor_data.copy()
        
    def set_sensor_callback(self, callback: Callable[[Dict[str, float]], None]):
        self.sensor_callback = callback
        
    def request_calibration(self) -> bool:
        print("Arduino simulation calibration requested")
        return True
        
    def test_connection(self) -> bool:
        return True

def get_arduino_interface(simulation: bool = True, port: str = "/dev/ttyUSB0") -> object:
    """Get Arduino interface (real or simulation)"""
    if simulation:
        return ArduinoSimulation()
    else:
        return ArduinoInterface(port)

if __name__ == "__main__":
    # Test the interface
    arduino = get_arduino_interface(simulation=True)
    
    def sensor_callback(data):
        print(f"Sensor data: {data}")
    
    arduino.set_sensor_callback(sensor_callback)
    
    if arduino.connect():
        print("Arduino interface connected")
        
        # Test for a few seconds
        time.sleep(5)
        
        arduino.disconnect()
    else:
        print("Failed to connect to Arduino")
