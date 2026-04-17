#!/usr/bin/env python3
"""
Hardware Integration System for Sanhum Robot
Integrates GPIO, Serial, Camera, and ROS2 interfaces
"""

import logging
import time
import threading
from typing import Dict, List, Optional, Callable
from enum import Enum

# Import hardware interfaces
from gpio_interface import HardwareInterface as GPIOInterface
from serial_interfaces import SerialManager
from camera_interface import CameraInterface

# Try to import ROS2
try:
    import rclpy
    from rclpy.node import Node
    from geometry_msgs.msg import Twist
    from sensor_msgs.msg import Image, Range
    from std_msgs.msg import Header
    ROS2_AVAILABLE = True
except ImportError:
    ROS2_AVAILABLE = False
    # Create fallback classes
    Node = None

class RobotMode(Enum):
    """Robot operation modes"""
    SIMULATION = "simulation"
    HARDWARE = "hardware"
    HYBRID = "hybrid"

class HardwareManager:
    """Main hardware manager for Sanhum Robot"""
    
    def __init__(self, mode: RobotMode = RobotMode.HARDWARE, config: Dict = None):
        self.logger = logging.getLogger(__name__)
        self.mode = mode
        self.config = config or self._default_config()
        
        # Hardware interfaces
        self.gpio_interface = None
        self.serial_manager = None
        self.camera_interface = None
        self.ros2_node = None
        
        # Status tracking
        self.connected = False
        self.emergency_stop = False
        self.hardware_status = {}
        
        # Callbacks
        self.telemetry_callbacks = []
        
        # Initialize based on mode
        self._initialize_hardware()
        
    def _default_config(self) -> Dict:
        """Default hardware configuration"""
        return {
            'gpio': {
                'enabled': True,
                'motor_pins': {
                    'left_motor': {'pwm_pin': 12, 'dir_pin1': 5, 'dir_pin2': 6, 'enable_pin': 13},
                    'right_motor': {'pwm_pin': 19, 'dir_pin1': 20, 'dir_pin2': 21, 'enable_pin': 26}
                },
                'pwm_frequency': 1000
            },
            'serial': {
                'esp32': {'port': None, 'baudrate': 115200},
                'arduino': {'port': None, 'baudrate': 9600}
            },
            'cameras': {
                'cameras': {
                    'left': {'index': 0, 'name': 'Stereo Left', 'resolution': (640, 480), 'fps': 30},
                    'right': {'index': 1, 'name': 'Stereo Right', 'resolution': (640, 480), 'fps': 30},
                    'mono': {'index': 2, 'name': 'Monocular', 'resolution': (640, 480), 'fps': 30}
                }
            },
            'ros2': {
                'enabled': ROS2_AVAILABLE,
                'node_name': 'sanhum_robot',
                'cmd_vel_topic': '/cmd_vel',
                'odom_topic': '/odom',
                'sensor_topics': {
                    'ultrasonic_front': '/sensors/ultrasonic_front',
                    'ultrasonic_left': '/sensors/ultrasonic_left',
                    'ultrasonic_right': '/sensors/ultrasonic_right'
                }
            }
        }
    
    def _initialize_hardware(self):
        """Initialize hardware based on mode"""
        try:
            if self.mode in [RobotMode.HARDWARE, RobotMode.HYBRID]:
                self._initialize_gpio()
                self._initialize_serial()
                self._initialize_cameras()
                
            if self.config['ros2']['enabled']:
                self._initialize_ros2()
                
            self.connected = self._check_connectivity()
            self._update_status()
            
            self.logger.info(f"Hardware initialized in {self.mode.value} mode")
            self.logger.info(f"Connected: {self.connected}")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize hardware: {e}")
            self.connected = False
    
    def _initialize_gpio(self):
        """Initialize GPIO interface"""
        if self.config['gpio']['enabled']:
            self.gpio_interface = GPIOInterface()
            self.logger.info(f"GPIO interface initialized: {self.gpio_interface.connected}")
    
    def _initialize_serial(self):
        """Initialize serial interfaces"""
        self.serial_manager = SerialManager()
        self.logger.info(f"Serial interfaces - ESP32: {self.serial_manager.esp32.connected if self.serial_manager.esp32 else False}, "
                        f"Arduino: {self.serial_manager.arduino.connected if self.serial_manager.arduino else False}")
    
    def _initialize_cameras(self):
        """Initialize camera interfaces"""
        self.camera_interface = CameraInterface(self.config['cameras'])
        self.camera_interface.connect()
        self.logger.info(f"Camera interface connected: {self.camera_interface.connected}")
    
    def _initialize_ros2(self):
        """Initialize ROS2 interface"""
        if not ROS2_AVAILABLE:
            self.logger.warning("ROS2 not available")
            return
        
        try:
            rclpy.init()
            self.ros2_node = SanhumROS2Node(self.config['ros2'], self)
            self.ros2_thread = threading.Thread(target=self._ros2_spin, daemon=True)
            self.ros2_thread.start()
            self.logger.info("ROS2 interface initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize ROS2: {e}")
    
    def _ros2_spin(self):
        """ROS2 spinning thread"""
        if self.ros2_node:
            rclpy.spin(self.ros2_node)
    
    def _check_connectivity(self) -> bool:
        """Check overall hardware connectivity"""
        connectivity = False
        
        if self.mode == RobotMode.SIMULATION:
            connectivity = True
        elif self.mode == RobotMode.HARDWARE:
            connectivity = (
                (self.gpio_interface and self.gpio_interface.connected) or
                (self.serial_manager and self.serial_manager.connected) or
                (self.camera_interface and self.camera_interface.connected)
            )
        elif self.mode == RobotMode.HYBRID:
            connectivity = True  # Hybrid mode works with any available hardware
        
        return connectivity
    
    def _update_status(self):
        """Update hardware status"""
        self.hardware_status = {
            'mode': self.mode.value,
            'connected': self.connected,
            'emergency_stop': self.emergency_stop,
            'gpio': {
                'connected': self.gpio_interface.connected if self.gpio_interface else False,
                'motor_speeds': self.gpio_interface.get_motor_speeds() if self.gpio_interface else {}
            },
            'serial': {
                'esp32_connected': self.serial_manager.esp32.connected if self.serial_manager.esp32 else False,
                'arduino_connected': self.serial_manager.arduino.connected if self.serial_manager.arduino else False,
                'joint_positions': self.serial_manager.get_joint_positions() if self.serial_manager else [],
                'sensor_data': self.serial_manager.get_sensor_data() if self.serial_manager else {}
            },
            'cameras': {
                'connected': self.camera_interface.connected if self.camera_interface else False,
                'active_cameras': list(self.camera_interface.connected.keys()) if self.camera_interface else []
            },
            'ros2': {
                'connected': self.ros2_node is not None,
                'node_name': self.config['ros2']['node_name'] if self.ros2_node else None
            }
        }
    
    # Motor control methods
    def set_motor_speed(self, motor: str, speed: float):
        """Set motor speed"""
        if self.emergency_stop:
            return
        
        if self.gpio_interface and self.gpio_interface.connected:
            self.gpio_interface.set_motor_speed(motor, speed)
        
        # Send to ROS2 if available
        if self.ros2_node:
            self.ros2_node.publish_velocity(speed, speed)  # Simplified for demo
    
    def stop_all_motors(self):
        """Stop all motors"""
        if self.gpio_interface:
            self.gpio_interface.stop_all_motors()
        
        if self.ros2_node:
            self.ros2_node.publish_velocity(0, 0)
    
    def emergency_stop_all(self):
        """Emergency stop all systems"""
        self.emergency_stop = True
        
        if self.gpio_interface:
            self.gpio_interface.emergency_stop()
        
        if self.serial_manager:
            # Send emergency stop to ESP32
            if self.serial_manager.esp32 and self.serial_manager.esp32.connected:
                self.serial_manager.esp32.command_queue.put("STOP")
        
        if self.ros2_node:
            self.ros2_node.publish_velocity(0, 0)
        
        self.logger.warning("Emergency stop activated")
    
    def reset_emergency_stop(self):
        """Reset emergency stop"""
        self.emergency_stop = False
        
        if self.gpio_interface:
            self.gpio_interface.reset_emergency_stop()
        
        self.logger.info("Emergency stop reset")
    
    # Manipulator control methods
    def send_joint_command(self, positions: List[float]) -> bool:
        """Send joint command to manipulator"""
        if self.emergency_stop:
            return False
        
        if self.serial_manager:
            success = self.serial_manager.send_joint_command(positions)
            
            # Send to ROS2 if available
            if self.ros2_node and success:
                self.ros2_node.publish_joint_states(positions)
            
            return success
        
        return False
    
    def send_gripper_command(self, position: float) -> bool:
        """Send gripper command"""
        if self.emergency_stop:
            return False
        
        if self.serial_manager:
            success = self.serial_manager.send_gripper_command(position)
            
            # Send to ROS2 if available
            if self.ros2_node and success:
                self.ros2_node.publish_gripper_state(position)
            
            return success
        
        return False
    
    def home_manipulator(self) -> bool:
        """Home manipulator"""
        return self.send_joint_command([0.0, 0.0, 0.0, 0.0, 0.0])
    
    # Sensor data methods
    def get_sensor_data(self) -> Dict:
        """Get all sensor data"""
        sensor_data = {}
        
        if self.serial_manager:
            sensor_data.update(self.serial_manager.get_sensor_data())
        
        # Add camera data if available
        if self.camera_interface and self.camera_interface.connected:
            for camera_name in self.camera_interface.connected:
                frame = self.camera_interface.get_latest_frame(camera_name)
                if frame is not None:
                    sensor_data[f'camera_{camera_name}'] = frame
        
        return sensor_data
    
    def get_joint_positions(self) -> List[float]:
        """Get current joint positions"""
        if self.serial_manager:
            return self.serial_manager.get_joint_positions()
        return [0.0, 0.0, 0.0, 0.0, 0.0]
    
    def get_status(self) -> Dict:
        """Get comprehensive hardware status"""
        self._update_status()
        return self.hardware_status
    
    def add_telemetry_callback(self, callback: Callable):
        """Add telemetry callback"""
        self.telemetry_callbacks.append(callback)
    
    def _notify_telemetry_callbacks(self):
        """Notify all telemetry callbacks"""
        if self.telemetry_callbacks:
            status = self.get_status()
            for callback in self.telemetry_callbacks:
                try:
                    callback(status)
                except Exception as e:
                    self.logger.error(f"Telemetry callback error: {e}")
    
    def cleanup(self):
        """Clean up all hardware interfaces"""
        self.logger.info("Cleaning up hardware interfaces...")
        
        # Stop all motors
        self.stop_all_motors()
        
        # Clean up GPIO
        if self.gpio_interface:
            self.gpio_interface.cleanup()
        
        # Clean up serial interfaces
        if self.serial_manager:
            self.serial_manager.disconnect_all()
        
        # Clean up cameras
        if self.camera_interface:
            self.camera_interface.disconnect()
        
        # Clean up ROS2
        if self.ros2_node:
            self.ros2_node.destroy_node()
            rclpy.shutdown()
        
        self.connected = False
        self.logger.info("Hardware cleanup completed")

class SanhumROS2Node:
    """ROS2 node for Sanhum Robot"""
    
    def __init__(self, config: Dict, hardware_manager: HardwareManager):
        if not ROS2_AVAILABLE or Node is None:
            self.config = config
            self.hardware_manager = hardware_manager
            self.logger = logging.getLogger(__name__)
            self.logger.info("ROS2 node initialized (simulation mode)")
            return
            
        super().__init__(config['node_name'])
        self.config = config
        self.hardware_manager = hardware_manager
        
        # Publishers
        self.cmd_vel_pub = self.create_publisher(Twist, config['cmd_vel_topic'], 10)
        
        # Subscribers
        self.cmd_vel_sub = self.create_subscription(
            Twist, config['cmd_vel_topic'], self.cmd_vel_callback, 10
        )
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("ROS2 node initialized")
    
    def cmd_vel_callback(self, msg):
        """Velocity command callback"""
        if not ROS2_AVAILABLE:
            return
            
        # Convert to motor speeds
        linear = msg.linear.x
        angular = msg.angular.z
        
        # Simple differential drive conversion
        left_speed = linear - angular * 0.5
        right_speed = linear + angular * 0.5
        
        self.hardware_manager.set_motor_speed('left', left_speed)
        self.hardware_manager.set_motor_speed('right', right_speed)
    
    def publish_velocity(self, linear: float, angular: float):
        """Publish velocity command"""
        if not ROS2_AVAILABLE:
            return
            
        msg = Twist()
        msg.linear.x = linear
        msg.angular.z = angular
        self.cmd_vel_pub.publish(msg)
    
    def publish_joint_states(self, positions: List[float]):
        """Publish joint states (simplified)"""
        # Implementation would create proper JointState messages
        pass
    
    def publish_gripper_state(self, position: float):
        """Publish gripper state (simplified)"""
        # Implementation would create proper gripper state messages
        pass
    
    def destroy_node(self):
        """Destroy ROS2 node"""
        if ROS2_AVAILABLE and hasattr(self, 'destroy_node'):
            super().destroy_node()

# Test function
def test_hardware_integration():
    """Test hardware integration system"""
    print("Testing Hardware Integration System...")
    
    # Test different modes
    for mode in [RobotMode.SIMULATION, RobotMode.HARDWARE]:
        print(f"\nTesting {mode.value} mode...")
        
        manager = HardwareManager(mode=mode)
        status = manager.get_status()
        
        print(f"Connected: {status['connected']}")
        print(f"GPIO: {status['gpio']['connected']}")
        print(f"Serial: ESP32={status['serial']['esp32_connected']}, Arduino={status['serial']['arduino_connected']}")
        print(f"Cameras: {status['cameras']['connected']}")
        print(f"ROS2: {status['ros2']['connected']}")
        
        # Test motor control
        if mode == RobotMode.HARDWARE and status['gpio']['connected']:
            print("Testing motor control...")
            manager.set_motor_speed('left', 0.5)
            time.sleep(1)
            manager.set_motor_speed('left', 0.0)
            print("Motor test completed")
        
        manager.cleanup()
        time.sleep(1)
    
    print("\nHardware integration test completed")

if __name__ == "__main__":
    test_hardware_integration()
