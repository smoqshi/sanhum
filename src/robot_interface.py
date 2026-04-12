#!/usr/bin/env python3
"""
Sanhum Robot Interface Module
Connects GUI to real robot hardware and simulation
"""

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile
from geometry_msgs.msg import Twist, Pose, Point, Quaternion
from sensor_msgs.msg import BatteryState, Imu, Range
from std_msgs.msg import String, Header
from nav_msgs.msg import Odometry
import threading
import time
import math
import json
from enum import Enum

class RobotMode(Enum):
    MANUAL = "MANUAL"
    AUTO = "AUTO"
    TELEOP = "TELEOP"
    PROGRAM = "PROGRAM"
    SIMULATION = "SIMULATION"

class RobotInterface(Node):
    def __init__(self, gui_callback=None):
        super().__init__('sanhum_robot_gui_node')
        
        self.gui_callback = gui_callback
        self.connected = False
        self.emergency_stop = False
        self.mode = RobotMode.SIMULATION
        
        # Robot state
        self.current_pose = Pose()
        self.current_velocity = Twist()
        self.battery_state = BatteryState()
        self.sensor_data = {
            'ultrasonic_front': 0.0,
            'ultrasonic_rear': 0.0,
            'infrared_left': 0.0,
            'infrared_right': 0.0,
            'imu': {'roll': 0.0, 'pitch': 0.0, 'yaw': 0.0}
        }
        
        # Manipulator state
        self.manipulator_joints = {
            'joint1': 0.0,
            'joint2': 0.0,
            'joint3': 0.0,
            'gripper': 0.0
        }
        
        # Setup QoS
        qos_profile = QoSProfile(depth=10)
        
        # Publishers
        self.cmd_vel_pub = self.create_publisher(Twist, 'cmd_vel', qos_profile)
        self.manipulator_cmd_pub = self.create_publisher(String, 'manipulator_cmd', qos_profile)
        self.mode_pub = self.create_publisher(String, 'robot_mode', qos_profile)
        
        # Subscribers
        self.odom_sub = self.create_subscription(
            Odometry, 'odom', self.odometry_callback, qos_profile)
        self.battery_sub = self.create_subscription(
            BatteryState, 'battery', self.battery_callback, qos_profile)
        self.imu_sub = self.create_subscription(
            Imu, 'imu', self.imu_callback, qos_profile)
        
        # Sensor subscriptions
        self.us_front_sub = self.create_subscription(
            Range, 'ultrasonic_front', self.us_front_callback, qos_profile)
        self.us_rear_sub = self.create_subscription(
            Range, 'ultrasonic_rear', self.us_rear_callback, qos_profile)
        self.ir_left_sub = self.create_subscription(
            Range, 'infrared_left', self.ir_left_callback, qos_profile)
        self.ir_right_sub = self.create_subscription(
            Range, 'infrared_right', self.ir_right_callback, qos_profile)
        
        # Manipulator feedback
        self.manipulator_sub = self.create_subscription(
            String, 'manipulator_feedback', self.manipulator_callback, qos_profile)
        
        self.get_logger().info('Robot Interface initialized')
        
    def connect(self, namespace="sanhum_robot"):
        """Connect to robot"""
        try:
            self.connected = True
            self.get_logger().info(f'Connected to robot: {namespace}')
            
            if self.gui_callback:
                self.gui_callback('log', f"Connected to robot: {namespace}")
                self.gui_callback('connection', True)
                
            return True
        except Exception as e:
            self.get_logger().error(f'Failed to connect: {e}')
            return False
            
    def disconnect(self):
        """Disconnect from robot"""
        self.connected = False
        self.stop_robot()
        self.get_logger().info('Disconnected from robot')
        
        if self.gui_callback:
            self.gui_callback('log', "Disconnected from robot")
            self.gui_callback('connection', False)
            
    def set_mode(self, mode):
        """Set robot operation mode"""
        self.mode = mode
        mode_msg = String()
        mode_msg.data = mode.value
        self.mode_pub.publish(mode_msg)
        
        self.get_logger().info(f'Robot mode set to: {mode.value}')
        
        if self.gui_callback:
            self.gui_callback('mode', mode.value)
            
    def send_velocity_command(self, linear_x, angular_z):
        """Send velocity command to robot"""
        if not self.connected or self.emergency_stop:
            return
            
        cmd = Twist()
        cmd.linear.x = linear_x
        cmd.angular.z = angular_z
        
        self.cmd_vel_pub.publish(cmd)
        self.current_velocity = cmd
        
    def send_manipulator_command(self, joint1, joint2, joint3, gripper):
        """Send manipulator command"""
        if not self.connected or self.emergency_stop:
            return
            
        cmd = {
            'joint1': joint1,
            'joint2': joint2,
            'joint3': joint3,
            'gripper': gripper
        }
        
        cmd_msg = String()
        cmd_msg.data = json.dumps(cmd)
        self.manipulator_cmd_pub.publish(cmd_msg)
        
        self.manipulator_joints = cmd
        
    def emergency_stop_action(self, stop=True):
        """Emergency stop action"""
        self.emergency_stop = stop
        
        if stop:
            self.stop_robot()
            self.get_logger().warn('Emergency stop activated')
            
            if self.gui_callback:
                self.gui_callback('emergency_stop', True)
        else:
            self.get_logger().info('Emergency stop deactivated')
            
            if self.gui_callback:
                self.gui_callback('emergency_stop', False)
                
    def stop_robot(self):
        """Stop robot movement"""
        cmd = Twist()
        cmd.linear.x = 0.0
        cmd.angular.z = 0.0
        self.cmd_vel_pub.publish(cmd)
        self.current_velocity = cmd
        
    def reset_system(self):
        """Reset robot system"""
        self.stop_robot()
        self.emergency_stop = False
        
        # Reset manipulator to home position
        self.send_manipulator_command(0.0, 0.0, 0.0, 0.0)
        
        self.get_logger().info('System reset completed')
        
        if self.gui_callback:
            self.gui_callback('log', "System reset completed")
            
    # Callback functions
    def odometry_callback(self, msg):
        """Odometry data callback"""
        self.current_pose = msg.pose.pose
        self.current_velocity = msg.twist.twist
        
        if self.gui_callback:
            self.gui_callback('odometry', {
                'position': {
                    'x': self.current_pose.position.x,
                    'y': self.current_pose.position.y,
                    'theta': self.get_yaw_from_quaternion(self.current_pose.orientation)
                },
                'velocity': {
                    'linear': self.current_velocity.linear.x,
                    'angular': self.current_velocity.angular.z
                }
            })
            
    def battery_callback(self, msg):
        """Battery state callback"""
        self.battery_state = msg
        
        if self.gui_callback:
            self.gui_callback('battery', {
                'voltage': msg.voltage,
                'percentage': msg.percentage,
                'current': msg.current
            })
            
    def imu_callback(self, msg):
        """IMU data callback"""
        # Convert quaternion to euler angles
        roll, pitch, yaw = self.euler_from_quaternion(
            msg.orientation.x, msg.orientation.y, msg.orientation.z, msg.orientation.w)
            
        self.sensor_data['imu'] = {
            'roll': roll,
            'pitch': pitch,
            'yaw': yaw
        }
        
        if self.gui_callback:
            self.gui_callback('imu', self.sensor_data['imu'])
            
    def us_front_callback(self, msg):
        """Front ultrasonic callback"""
        self.sensor_data['ultrasonic_front'] = msg.range
        
        if self.gui_callback:
            self.gui_callback('sensor', {
                'type': 'ultrasonic_front',
                'value': msg.range
            })
            
    def us_rear_callback(self, msg):
        """Rear ultrasonic callback"""
        self.sensor_data['ultrasonic_rear'] = msg.range
        
        if self.gui_callback:
            self.gui_callback('sensor', {
                'type': 'ultrasonic_rear',
                'value': msg.range
            })
            
    def ir_left_callback(self, msg):
        """Left infrared callback"""
        self.sensor_data['infrared_left'] = msg.range
        
        if self.gui_callback:
            self.gui_callback('sensor', {
                'type': 'infrared_left',
                'value': msg.range
            })
            
    def ir_right_callback(self, msg):
        """Right infrared callback"""
        self.sensor_data['infrared_right'] = msg.range
        
        if self.gui_callback:
            self.gui_callback('sensor', {
                'type': 'infrared_right',
                'value': msg.range
            })
            
    def manipulator_callback(self, msg):
        """Manipulator feedback callback"""
        try:
            feedback = json.loads(msg.data)
            self.manipulator_joints.update(feedback)
            
            if self.gui_callback:
                self.gui_callback('manipulator', self.manipulator_joints)
        except json.JSONDecodeError:
            pass
            
    # Utility functions
    def get_yaw_from_quaternion(self, quaternion):
        """Extract yaw from quaternion"""
        return math.atan2(2.0 * (quaternion.w * quaternion.z + quaternion.x * quaternion.y),
                         1.0 - 2.0 * (quaternion.y * quaternion.y + quaternion.z * quaternion.z))
                         
    def euler_from_quaternion(self, x, y, z, w):
        """Convert quaternion to euler angles"""
        t0 = +2.0 * (w * x + y * z)
        t1 = +1.0 - 2.0 * (x * x + y * y)
        roll_x = math.atan2(t0, t1)
        
        t2 = +2.0 * (w * y - z * x)
        t2 = +1.0 if t2 > +1.0 else t2
        t2 = -1.0 if t2 < -1.0 else t2
        pitch_y = math.asin(t2)
        
        t3 = +2.0 * (w * z + x * y)
        t4 = +1.0 - 2.0 * (y * y + z * z)
        yaw_z = math.atan2(t3, t4)
        
        return roll_x, pitch_y, yaw_z  # in radians

class RobotInterfaceManager:
    """Manages robot interface and ROS2 connection"""
    
    def __init__(self, gui_callback=None):
        self.gui_callback = gui_callback
        self.ros_node = None
        self.ros_thread = None
        self.running = False
        
    def start_ros(self):
        """Start ROS2 node in separate thread"""
        if self.running:
            return
            
        self.running = True
        
        def ros_spin():
            rclpy.init()
            try:
                self.ros_node = RobotInterface(self.gui_callback)
                rclpy.spin(self.ros_node)
            except Exception as e:
                if self.gui_callback:
                    self.gui_callback('log', f"ROS Error: {e}")
            finally:
                if self.ros_node:
                    self.ros_node.destroy_node()
                rclpy.shutdown()
                self.running = False
                
        self.ros_thread = threading.Thread(target=ros_spin, daemon=True)
        self.ros_thread.start()
        
        # Wait for node to initialize
        time.sleep(1)
        
    def stop_ros(self):
        """Stop ROS2 node"""
        self.running = False
        if self.ros_node:
            self.ros_node.destroy_node()
        if self.ros_thread:
            self.ros_thread.join(timeout=2)
            
    def get_interface(self):
        """Get robot interface instance"""
        return self.ros_node
