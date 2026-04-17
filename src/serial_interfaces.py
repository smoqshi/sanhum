#!/usr/bin/env python3
"""
Serial Interfaces for Sanhum Robot Hardware
ESP32 (Manipulator) and Arduino (Sensors) communication
"""

import serial
import serial.tools.list_ports
import time
import json
import logging
from typing import Dict, List, Optional, Tuple
from threading import Thread, Lock
from queue import Queue, Empty
import re

class ESP32Interface:
    """ESP32 Serial Interface for Manipulator Control"""
    
    def __init__(self, port: str = None, baudrate: int = 115200):
        self.logger = logging.getLogger(__name__)
        self.port = port or self._find_esp32_port()
        self.baudrate = baudrate
        self.serial_conn = None
        self.connected = False
        self.lock = Lock()
        
        # Command queues
        self.command_queue = Queue()
        self.response_queue = Queue()
        
        # Thread for communication
        self.comm_thread = None
        self.running = False
        
        # Joint positions (5 joints + gripper)
        self.joint_positions = [0.0, 0.0, 0.0, 0.0, 0.0]
        self.gripper_position = 0.0
        
        # Joint limits (degrees)
        self.joint_limits = [
            (-180, 180),  # Joint 1 (base rotation)
            (-90, 90),    # Joint 2 (shoulder)
            (-90, 90),    # Joint 3 (elbow)
            (-90, 90),    # Joint 4 (wrist)
            (-90, 90)     # Joint 5 (end effector)
        ]
        
        if self.port:
            self.connect()
    
    def _find_esp32_port(self) -> Optional[str]:
        """Find ESP32 serial port"""
        ports = serial.tools.list_ports.comports()
        
        # Common ESP32 identifiers
        esp32_identifiers = ['CP210', 'CH340', 'USB-SERIAL', 'ESP32']
        
        for port in ports:
            for identifier in esp32_identifiers:
                if identifier.upper() in port.description.upper():
                    self.logger.info(f"Found ESP32 on port {port.device}")
                    return port.device
        
        # Try first available port if no specific identifier found
        if ports:
            self.logger.info(f"Using first available port: {ports[0].device}")
            return ports[0].device
        
        return None
    
    def connect(self) -> bool:
        """Connect to ESP32"""
        try:
            self.serial_conn = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=1.0,
                write_timeout=1.0
            )
            
            # Wait for connection to stabilize
            time.sleep(2)
            
            # Test connection
            if self._test_connection():
                self.connected = True
                self.running = True
                self.comm_thread = Thread(target=self._communication_loop, daemon=True)
                self.comm_thread.start()
                
                self.logger.info(f"Connected to ESP32 on {self.port}")
                return True
            else:
                self.serial_conn.close()
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to connect to ESP32: {e}")
            return False
    
    def _test_connection(self) -> bool:
        """Test ESP32 connection"""
        try:
            # Send test command
            self.serial_conn.write(b'PING\n')
            time.sleep(0.5)
            
            # Check for response
            if self.serial_conn.in_waiting > 0:
                response = self.serial_conn.readline().decode().strip()
                return 'PONG' in response or 'OK' in response
            
            return False
            
        except Exception:
            return False
    
    def _communication_loop(self):
        """Background communication thread"""
        while self.running:
            try:
                # Send queued commands
                try:
                    command = self.command_queue.get(timeout=0.1)
                    with self.lock:
                        if self.serial_conn and self.serial_conn.is_open:
                            self.serial_conn.write(command.encode() + b'\n')
                            self.logger.debug(f"Sent: {command.strip()}")
                except Empty:
                    pass
                
                # Read responses
                with self.lock:
                    if self.serial_conn and self.serial_conn.is_open:
                        if self.serial_conn.in_waiting > 0:
                            line = self.serial_conn.readline().decode().strip()
                            if line:
                                self._process_response(line)
                
                time.sleep(0.01)  # Small delay to prevent CPU overload
                
            except Exception as e:
                self.logger.error(f"Communication error: {e}")
                time.sleep(0.1)
    
    def _process_response(self, response: str):
        """Process ESP32 response"""
        self.logger.debug(f"Received: {response}")
        
        # Parse joint state response
        if response.startswith('JOINTS:'):
            try:
                parts = response.split(':')[1].split(',')
                if len(parts) >= 5:
                    self.joint_positions = [float(p) for p in parts[:5]]
                    if len(parts) >= 6:
                        self.gripper_position = float(parts[5])
            except ValueError:
                pass
        
        # Parse status response
        elif response.startswith('STATUS:'):
            self.response_queue.put(response)
        
        # Parse error response
        elif response.startswith('ERROR:'):
            self.logger.error(f"ESP32 Error: {response}")
    
    def send_joint_command(self, positions: List[float]) -> bool:
        """Send joint positions to ESP32"""
        if not self.connected:
            return False
        
        # Validate positions
        if len(positions) != 5:
            self.logger.error("Requires 5 joint positions")
            return False
        
        # Check joint limits
        for i, pos in enumerate(positions):
            min_angle, max_angle = self.joint_limits[i]
            if pos < min_angle or pos > max_angle:
                self.logger.warning(f"Joint {i+1} position {pos} out of range [{min_angle}, {max_angle}]")
                return False
        
        # Format command
        command = f"JOINTS:{','.join([f'{p:.2f}' for p in positions])}"
        self.command_queue.put(command)
        
        # Update local positions
        self.joint_positions = positions.copy()
        
        return True
    
    def send_gripper_command(self, position: float) -> bool:
        """Send gripper position to ESP32 (0-100)"""
        if not self.connected:
            return False
        
        # Clamp position
        position = max(0.0, min(100.0, position))
        
        command = f"GRIPPER:{position:.2f}"
        self.command_queue.put(command)
        
        self.gripper_position = position
        
        return True
    
    def get_joint_positions(self) -> List[float]:
        """Get current joint positions"""
        return self.joint_positions.copy()
    
    def get_gripper_position(self) -> float:
        """Get current gripper position"""
        return self.gripper_position
    
    def home_manipulator(self) -> bool:
        """Send home command to manipulator"""
        if not self.connected:
            return False
        
        home_positions = [0.0, 0.0, 0.0, 0.0, 0.0]
        return self.send_joint_command(home_positions)
    
    def disconnect(self):
        """Disconnect from ESP32"""
        self.running = False
        
        if self.comm_thread:
            self.comm_thread.join(timeout=1.0)
        
        with self.lock:
            if self.serial_conn and self.serial_conn.is_open:
                self.serial_conn.close()
        
        self.connected = False
        self.logger.info("Disconnected from ESP32")

class ArduinoInterface:
    """Arduino Serial Interface for Sensor Data"""
    
    def __init__(self, port: str = None, baudrate: int = 9600):
        self.logger = logging.getLogger(__name__)
        self.port = port or self._find_arduino_port()
        self.baudrate = baudrate
        self.serial_conn = None
        self.connected = False
        self.lock = Lock()
        
        # Sensor data
        self.sensor_data = {
            'ultrasonic_front': 0.0,
            'ultrasonic_left': 0.0,
            'ultrasonic_right': 0.0,
            'ir_front_left': 0.0,
            'ir_front_right': 0.0,
            'ir_rear': 0.0
        }
        
        # Thread for data collection
        self.data_thread = None
        self.running = False
        
        if self.port:
            self.connect()
    
    def _find_arduino_port(self) -> Optional[str]:
        """Find Arduino serial port"""
        ports = serial.tools.list_ports.comports()
        
        # Common Arduino identifiers
        arduino_identifiers = ['Arduino', 'CH340', 'USB-SERIAL', 'FTDI']
        
        for port in ports:
            for identifier in arduino_identifiers:
                if identifier.upper() in port.description.upper():
                    self.logger.info(f"Found Arduino on port {port.device}")
                    return port.device
        
        return None
    
    def connect(self) -> bool:
        """Connect to Arduino"""
        try:
            self.serial_conn = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=1.0
            )
            
            time.sleep(2)  # Wait for Arduino to reset
            
            if self._test_connection():
                self.connected = True
                self.running = True
                self.data_thread = Thread(target=self._data_collection_loop, daemon=True)
                self.data_thread.start()
                
                self.logger.info(f"Connected to Arduino on {self.port}")
                return True
            else:
                self.serial_conn.close()
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to connect to Arduino: {e}")
            return False
    
    def _test_connection(self) -> bool:
        """Test Arduino connection"""
        try:
            # Send test command
            self.serial_conn.write(b'STATUS\n')
            time.sleep(0.5)
            
            # Check for response
            if self.serial_conn.in_waiting > 0:
                response = self.serial_conn.readline().decode().strip()
                return 'OK' in response or 'READY' in response
            
            return False
            
        except Exception:
            return False
    
    def _data_collection_loop(self):
        """Background data collection thread"""
        while self.running:
            try:
                with self.lock:
                    if self.serial_conn and self.serial_conn.is_open:
                        if self.serial_conn.in_waiting > 0:
                            line = self.serial_conn.readline().decode().strip()
                            if line:
                                self._parse_sensor_data(line)
                
                time.sleep(0.05)  # 20Hz data collection
                
            except Exception as e:
                self.logger.error(f"Data collection error: {e}")
                time.sleep(0.1)
    
    def _parse_sensor_data(self, data: str):
        """Parse sensor data from Arduino"""
        try:
            # Expected format: SENSORS:ultra_front,ultra_left,ultra_right,ir_fl,ir_fr,ir_rear
            if data.startswith('SENSORS:'):
                values = data.split(':')[1].split(',')
                if len(values) >= 6:
                    self.sensor_data = {
                        'ultrasonic_front': float(values[0]),
                        'ultrasonic_left': float(values[1]),
                        'ultrasonic_right': float(values[2]),
                        'ir_front_left': float(values[3]),
                        'ir_front_right': float(values[4]),
                        'ir_rear': float(values[5])
                    }
        except (ValueError, IndexError):
            self.logger.warning(f"Invalid sensor data: {data}")
    
    def get_sensor_data(self) -> Dict[str, float]:
        """Get current sensor readings"""
        return self.sensor_data.copy()
    
    def disconnect(self):
        """Disconnect from Arduino"""
        self.running = False
        
        if self.data_thread:
            self.data_thread.join(timeout=1.0)
        
        with self.lock:
            if self.serial_conn and self.serial_conn.is_open:
                self.serial_conn.close()
        
        self.connected = False
        self.logger.info("Disconnected from Arduino")

class SerialManager:
    """Manager for all serial interfaces"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.esp32 = None
        self.arduino = None
        self.connected = False
        
        self._initialize_interfaces()
    
    def _initialize_interfaces(self):
        """Initialize serial interfaces"""
        try:
            self.esp32 = ESP32Interface()
            self.arduino = ArduinoInterface()
            
            self.connected = self.esp32.connected or self.arduino.connected
            
            self.logger.info(f"Serial interfaces initialized - ESP32: {self.esp32.connected}, Arduino: {self.arduino.connected}")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize serial interfaces: {e}")
    
    def send_joint_command(self, positions: List[float]) -> bool:
        """Send joint command to manipulator"""
        if self.esp32 and self.esp32.connected:
            return self.esp32.send_joint_command(positions)
        return False
    
    def send_gripper_command(self, position: float) -> bool:
        """Send gripper command to manipulator"""
        if self.esp32 and self.esp32.connected:
            return self.esp32.send_gripper_command(position)
        return False
    
    def home_manipulator(self) -> bool:
        """Home the manipulator"""
        if self.esp32 and self.esp32.connected:
            return self.esp32.home_manipulator()
        return False
    
    def get_sensor_data(self) -> Dict[str, float]:
        """Get sensor data"""
        if self.arduino and self.arduino.connected:
            return self.arduino.get_sensor_data()
        return {}
    
    def get_joint_positions(self) -> List[float]:
        """Get joint positions"""
        if self.esp32 and self.esp32.connected:
            return self.esp32.get_joint_positions()
        return [0.0, 0.0, 0.0, 0.0, 0.0]
    
    def get_status(self) -> Dict:
        """Get status of all interfaces"""
        return {
            'esp32_connected': self.esp32.connected if self.esp32 else False,
            'arduino_connected': self.arduino.connected if self.arduino else False,
            'joint_positions': self.get_joint_positions(),
            'sensor_data': self.get_sensor_data()
        }
    
    def disconnect_all(self):
        """Disconnect all interfaces"""
        if self.esp32:
            self.esp32.disconnect()
        if self.arduino:
            self.arduino.disconnect()
        
        self.connected = False
        self.logger.info("All serial interfaces disconnected")

# Test function
def test_serial_interfaces():
    """Test serial interfaces"""
    print("Testing Serial Interfaces...")
    
    manager = SerialManager()
    print(f"Status: {manager.get_status()}")
    
    # Test manipulator control
    if manager.esp32 and manager.esp32.connected:
        print("Testing manipulator control...")
        manager.send_joint_command([0, 45, -45, 0, 0])
        time.sleep(2)
        manager.home_manipulator()
        print("Manipulator test completed")
    
    # Test sensor data
    if manager.arduino and manager.arduino.connected:
        print("Testing sensor data...")
        for i in range(5):
            data = manager.get_sensor_data()
            print(f"Sensor data: {data}")
            time.sleep(1)
        print("Sensor test completed")
    
    manager.disconnect_all()
    print("Serial interfaces test completed")

if __name__ == "__main__":
    test_serial_interfaces()
