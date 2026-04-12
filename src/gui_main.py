#!/usr/bin/env python3
"""
Sanhum Robot Industrial Control System - WORKING VERSION
Real robot control with functional keyboard/gamepad input and button controls
"""

import sys
import tkinter as tk
from tkinter import messagebox, filedialog, Canvas, Frame, Label, Button, Text, Scrollbar, Entry, StringVar, DoubleVar, BooleanVar, IntVar, Scale
import os
from pathlib import Path
import threading
import time
import json
import math
from datetime import datetime
from collections import defaultdict

# Import our robot modules
try:
    from robot_interface import RobotInterfaceManager, RobotMode
    from robot_simulation import RobotSimulation, Vector3
    from input_controller import InputController, ControlMode
    from rpi_gpio_interface import RPiGPIOInterface
    ROS2_AVAILABLE = True
    GPIO_AVAILABLE = True
except ImportError:
    ROS2_AVAILABLE = False
    GPIO_AVAILABLE = False
    print("Warning: ROS2 modules not available, running in simulation mode only")
    
    # Create fallback classes
    class Vector3:
        def __init__(self, x, y, z):
            self.x = x
            self.y = y
            self.z = z
            
        def __add__(self, other):
            return Vector3(self.x + other.x, self.y + other.y, self.z + other.z)
            
        def __sub__(self, other):
            return Vector3(self.x - other.x, self.y - other.y, self.z - other.z)
            
        def __mul__(self, scalar):
            return Vector3(self.x * scalar, self.y * scalar, self.z * scalar)
            
        def magnitude(self):
            return math.sqrt(self.x**2 + self.y**2 + self.z**2)
            
        def normalize(self):
            mag = self.magnitude()
            if mag > 0:
                return Vector3(self.x/mag, self.y/mag, self.z/mag)
            return Vector3(0, 0, 0)
    
    class RobotSimulation:
        def __init__(self):
            self.chassis_length = 0.8
            self.chassis_width = 0.6
            self.chassis_height = 0.3
            self.track_width = 0.15
            self.wheel_radius = 0.1
            self.link1_length = 0.3
            self.link2_length = 0.25
            self.link3_length = 0.2
            self.gripper_length = 0.15
            
            self.position = Vector3(0.0, 0.0, 0.0)
            self.orientation = 0.0
            self.linear_velocity = 0.0
            self.angular_velocity = 0.0
            
            self.joint1_angle = 0.0
            self.joint2_angle = 0.0
            self.joint3_angle = 0.0
            self.gripper_open = 0.0
            
            self.left_track_position = 0.0
            self.right_track_position = 0.0
            self.max_linear_vel = 2.0
            self.max_angular_vel = 3.14
            
        def update(self, dt):
            if abs(self.linear_velocity) > 0.01 or abs(self.angular_velocity) > 0.01:
                self.position.x += self.linear_velocity * math.cos(self.orientation) * dt
                self.position.y += self.linear_velocity * math.sin(self.orientation) * dt
                self.orientation += self.angular_velocity * dt
                self.orientation = math.atan2(math.sin(self.orientation), math.cos(self.orientation))
                self.left_track_position += (self.linear_velocity - self.angular_velocity * self.chassis_width/2) * dt / self.wheel_radius
                self.right_track_position += (self.linear_velocity + self.angular_velocity * self.chassis_width/2) * dt / self.wheel_radius
                
        def set_velocity(self, linear, angular):
            self.linear_velocity = max(-self.max_linear_vel, min(self.max_linear_vel, linear))
            self.angular_velocity = max(-self.max_angular_vel, min(self.max_angular_vel, angular))
            
        def set_manipulator_joints(self, joint1, joint2, joint3, gripper):
            self.joint1_angle = joint1
            self.joint2_angle = joint2
            self.joint3_angle = joint3
            self.gripper_open = max(0.0, min(1.0, gripper))
            
        def get_chassis_vertices(self):
            half_length = self.chassis_length / 2
            half_width = self.chassis_width / 2
            vertices = [
                Vector3(-half_length, -half_width, 0),
                Vector3(half_length, -half_width, 0),
                Vector3(half_length, half_width, 0),
                Vector3(-half_length, half_width, 0),
            ]
            return vertices
            
        def get_track_vertices(self, side):
            half_length = self.chassis_length / 2
            track_offset = self.chassis_width / 2 + self.track_width / 2
            
            if side == 'left':
                offset = -track_offset
            else:
                offset = track_offset
                
            segments = []
            num_segments = 4
            segment_length = self.chassis_length / num_segments
            
            for i in range(num_segments):
                x_start = -half_length + i * segment_length
                x_end = x_start + segment_length
                
                vertices = [
                    Vector3(x_start, offset - self.track_width/2, 0),
                    Vector3(x_end, offset - self.track_width/2, 0),
                    Vector3(x_end, offset + self.track_width/2, self.track_width),
                    Vector3(x_start, offset + self.track_width/2, self.track_width),
                ]
                segments.append(vertices)
                
            return segments
            
        def get_manipulator_vertices(self):
            base_x = self.chassis_length / 2
            base_y = 0
            base_z = self.chassis_height
            
            j1_x = base_x
            j1_y = base_y
            j1_z = base_z + 0.2
            
            j2_x = j1_x + self.link1_length * math.cos(self.joint2_angle)
            j2_y = j1_y + self.link1_length * math.sin(self.joint1_angle)
            j2_z = j1_z + self.link1_length * math.sin(self.joint2_angle)
            
            j3_x = j2_x + self.link2_length * math.cos(self.joint2_angle + self.joint3_angle)
            j3_y = j2_y + self.link2_length * math.sin(self.joint1_angle)
            j3_z = j2_z + self.link2_length * math.sin(self.joint2_angle + self.joint3_angle)
            
            end_x = j3_x + self.link3_length * math.cos(self.joint2_angle + self.joint3_angle)
            end_y = j3_y + self.link3_length * math.sin(self.joint1_angle)
            end_z = j3_z + self.link3_length * math.sin(self.joint2_angle + self.joint3_angle)
            
            links = [
                [(base_x, base_y, base_z), (j1_x, j1_y, j1_z)],
                [(j1_x, j1_y, j1_z), (j2_x, j2_y, j2_z)],
                [(j2_x, j2_y, j2_z), (j3_x, j3_y, j3_z)],
                [(j3_x, j3_y, j3_z), (end_x, end_y, end_z)],
            ]
            
            transformed_links = []
            for link in links:
                transformed_link = []
                for point in link:
                    x, y, z = point
                    
                    cos_o = math.cos(self.orientation)
                    sin_o = math.sin(self.orientation)
                    rotated_x = x * cos_o - y * sin_o
                    rotated_y = x * sin_o + y * cos_o
                    
                    world_pos = Vector3(
                        rotated_x + self.position.x,
                        rotated_y + self.position.y,
                        z + self.position.z
                    )
                    transformed_link.append(world_pos)
                    
                transformed_links.append(transformed_link)
                
            return transformed_links
            
        def get_gripper_vertices(self):
            if self.gripper_open < 0.1:
                return []
                
            manipulator_links = self.get_manipulator_vertices()
            if not manipulator_links:
                return []
                
            end_pos = manipulator_links[-1][-1]
            
            gripper_width = 0.1 * self.gripper_open
            gripper_length = 0.05
            
            vertices = [
                Vector3(end_pos.x - gripper_width/2, end_pos.y, end_pos.z),
                Vector3(end_pos.x + gripper_width/2, end_pos.y, end_pos.z),
                Vector3(end_pos.x + gripper_width/2, end_pos.y, end_pos.z + gripper_length),
                Vector3(end_pos.x - gripper_width/2, end_pos.y, end_pos.z + gripper_length),
            ]
            
            return vertices
            
        def simulate_sensors(self, obstacles=None):
            sensor_readings = {
                'ultrasonic_front': 2.5,
                'ultrasonic_rear': 2.5,
                'infrared_left': 0.8,
                'infrared_right': 0.8
            }
            return sensor_readings
            
        def reset(self):
            self.position = Vector3(0.0, 0.0, 0.0)
            self.orientation = 0.0
            self.linear_velocity = 0.0
            self.angular_velocity = 0.0
            self.joint1_angle = 0.0
            self.joint2_angle = 0.0
            self.joint3_angle = 0.0
            self.gripper_open = 0.0
            self.left_track_position = 0.0
            self.right_track_position = 0.0

    class InputController:
        def __init__(self, gui_callback=None):
            self.gui_callback = gui_callback
            self.running = False
            self.linear_velocity = 0.0
            self.angular_velocity = 0.0
            self.max_linear_vel = 2.0
            self.max_angular_vel = 3.14
            
        def start(self):
            self.running = True
            
        def stop(self):
            self.running = False
            
        def get_control_status(self):
            return {'mode': 'keyboard', 'linear_velocity': self.linear_velocity, 'angular_velocity': self.angular_velocity}

class WorkingRobotGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("SANHUM ROBOT CONTROL SYSTEM v5.0 - WORKING")
        self.root.geometry("1600x1000")
        self.root.minsize(1400, 900)
        
        # Industrial color scheme
        self.colors = {
            'bg': '#0a0a0a',
            'panel_bg': '#1e1e1e',
            'accent': '#00ff41',
            'success': '#00ff41',
            'warning': '#ff9f00',
            'danger': '#ff3d00',
            'info': '#00b8d4',
            'text': '#ffffff',
            'text_secondary': '#b0b0b0',
            'grid': '#2a2a2a'
        }
        
        self.root.configure(bg=self.colors['bg'])
        
        # Robot state
        self.connected = False
        self.emergency_stop = False
        self.simulation_mode = True
        self.robot_namespace = StringVar(value="sanhum_robot")
        
        # Control state
        self.target_velocity = {'linear': 0.0, 'angular': 0.0}
        self.key_pressed = defaultdict(bool)
        
        # Telemetry data
        self.telemetry = {
            'position': {'x': 0.0, 'y': 0.0, 'theta': 0.0},
            'velocity': {'linear': 0.0, 'angular': 0.0},
            'battery': 100.0,
            'motors': {'left': 0.0, 'right': 0.0},
            'sensors': {'ultrasonic_front': 0.0, 'ultrasonic_rear': 0.0, 'infrared_left': 0.0, 'infrared_right': 0.0},
            'manipulator': {'joint1': 0.0, 'joint2': 0.0, 'joint3': 0.0, 'gripper': 0.0},
            'status': 'IDLE',
            'imu': {'roll': 0.0, 'pitch': 0.0, 'yaw': 0.0}
        }
        
        # Manipulator variables
        self.manipulator_vars = {
            'joint1': DoubleVar(value=0.0),
            'joint2': DoubleVar(value=0.0),
            'joint3': DoubleVar(value=0.0),
            'gripper': DoubleVar(value=0.0)
        }
        
        # Initialize systems
        self.robot_sim = RobotSimulation()
        self.input_controller = InputController(gui_callback=self.input_callback)
        
        # GPIO interface for real hardware
        self.gpio_interface = None
        if GPIO_AVAILABLE:
            try:
                self.gpio_interface = RPiGPIOInterface()
                print("GPIO interface initialized")
            except Exception as e:
                print(f"GPIO interface not available: {e}")
        else:
            print("GPIO interface not available: module not found")
        
        # ROS2 interface
        self.ros_manager = None
        if ROS2_AVAILABLE:
            self.ros_manager = RobotInterfaceManager(gui_callback=self.ros_callback)
            self.ros_manager.start_ros()
            
        # Start input controller
        self.input_controller.start()
        
        # Create interface
        self.create_menu()
        self.create_main_layout()
        
        # Bind keyboard events
        self.setup_keyboard_controls()
        
        # Start update loops
        self.telemetry_thread_running = True
        self.telemetry_thread = threading.Thread(target=self.update_telemetry_loop, daemon=True)
        self.telemetry_thread.start()
        
        self.input_thread_running = True
        self.input_thread = threading.Thread(target=self.input_processing_loop, daemon=True)
        self.input_thread.start()
        
        self.simulation_thread_running = True
        self.simulation_thread = threading.Thread(target=self.simulation_loop, daemon=True)
        self.simulation_thread.start()
        
    def setup_keyboard_controls(self):
        """Setup keyboard event bindings"""
        # Key press events
        self.root.bind('<KeyPress-w>', lambda e: self.on_key_press('w'))
        self.root.bind('<KeyPress-s>', lambda e: self.on_key_press('s'))
        self.root.bind('<KeyPress-a>', lambda e: self.on_key_press('a'))
        self.root.bind('<KeyPress-d>', lambda e: self.on_key_press('d'))
        self.root.bind('<KeyPress-space>', lambda e: self.on_key_press('space'))
        self.root.bind('<KeyPress-q>', lambda e: self.on_key_press('q'))
        self.root.bind('<KeyPress-e>', lambda e: self.on_key_press('e'))
        self.root.bind('<KeyPress-r>', lambda e: self.on_key_press('r'))
        self.root.bind('<KeyPress-f>', lambda e: self.on_key_press('f'))
        self.root.bind('<KeyPress-t>', lambda e: self.on_key_press('t'))
        self.root.bind('<KeyPress-g>', lambda e: self.on_key_press('g'))
        self.root.bind('<KeyPress-z>', lambda e: self.on_key_press('z'))
        self.root.bind('<KeyPress-x>', lambda e: self.on_key_press('x'))
        self.root.bind('<KeyPress-c>', lambda e: self.on_key_press('c'))
        self.root.bind('<KeyPress-Escape>', lambda e: self.on_key_press('escape'))
        
        # Key release events
        self.root.bind('<KeyRelease-w>', lambda e: self.on_key_release('w'))
        self.root.bind('<KeyRelease-s>', lambda e: self.on_key_release('s'))
        self.root.bind('<KeyRelease-a>', lambda e: self.on_key_release('a'))
        self.root.bind('<KeyRelease-d>', lambda e: self.on_key_release('d'))
        self.root.bind('<KeyRelease-space>', lambda e: self.on_key_release('space'))
        self.root.bind('<KeyRelease-q>', lambda e: self.on_key_release('q'))
        self.root.bind('<KeyRelease-e>', lambda e: self.on_key_release('e'))
        self.root.bind('<KeyRelease-r>', lambda e: self.on_key_release('r'))
        self.root.bind('<KeyRelease-f>', lambda e: self.on_key_release('f'))
        self.root.bind('<KeyRelease-t>', lambda e: self.on_key_release('t'))
        self.root.bind('<KeyRelease-g>', lambda e: self.on_key_release('g'))
        self.root.bind('<KeyRelease-z>', lambda e: self.on_key_release('z'))
        self.root.bind('<KeyRelease-x>', lambda e: self.on_key_release('x'))
        
        # Focus to receive keyboard events
        self.root.focus_set()
        
    def on_key_press(self, key):
        """Handle key press events"""
        self.key_pressed[key] = True
        
        if key == 'escape':
            self.emergency_stop_action()
        elif key == 'space':
            self.stop_robot()
        elif key == 'c':
            self.home_manipulator()
        elif key == 'z':
            self.open_gripper()
        elif key == 'x':
            self.close_gripper()
            
    def on_key_release(self, key):
        """Handle key release events"""
        self.key_pressed[key] = False
        
    def input_processing_loop(self):
        """Process keyboard input and update robot control"""
        while self.input_thread_running:
            try:
                if self.emergency_stop:
                    self.target_velocity['linear'] = 0.0
                    self.target_velocity['angular'] = 0.0
                else:
                    # Process movement keys
                    linear = 0.0
                    angular = 0.0
                    
                    if self.key_pressed['w']:
                        linear = 2.0  # Forward
                    elif self.key_pressed['s']:
                        linear = -2.0  # Backward
                        
                    if self.key_pressed['a']:
                        angular = 3.14  # Left
                    elif self.key_pressed['d']:
                        angular = -3.14  # Right
                        
                    # Smooth transitions
                    self.target_velocity['linear'] = self.target_velocity['linear'] * 0.8 + linear * 0.2
                    self.target_velocity['angular'] = self.target_velocity['angular'] * 0.8 + angular * 0.2
                    
                    # Process manipulator keys
                    if self.key_pressed['q']:
                        self.manipulator_vars['joint1'].set(
                            max(-180, self.manipulator_vars['joint1'].get() - 2))
                    elif self.key_pressed['e']:
                        self.manipulator_vars['joint1'].set(
                            min(180, self.manipulator_vars['joint1'].get() + 2))
                            
                    if self.key_pressed['r']:
                        self.manipulator_vars['joint2'].set(
                            max(-90, self.manipulator_vars['joint2'].get() - 2))
                    elif self.key_pressed['f']:
                        self.manipulator_vars['joint2'].set(
                            min(90, self.manipulator_vars['joint2'].get() + 2))
                            
                    if self.key_pressed['t']:
                        self.manipulator_vars['joint3'].set(
                            max(-180, self.manipulator_vars['joint3'].get() - 2))
                    elif self.key_pressed['g']:
                        self.manipulator_vars['joint3'].set(
                            min(180, self.manipulator_vars['joint3'].get() + 2))
                
                # Send commands to hardware
                self.send_robot_commands()
                
                time.sleep(0.05)  # 20 Hz
                
            except Exception as e:
                print(f"Input processing error: {e}")
                time.sleep(0.1)
                
    def send_robot_commands(self):
        """Send commands to robot hardware/simulation"""
        try:
            # Send velocity commands
            if self.gpio_interface and not self.simulation_mode:
                # Real hardware control
                # Convert linear/angular to left/right motor speeds
                wheel_separation = 0.35
                left_speed = self.target_velocity['linear'] - self.target_velocity['angular'] * wheel_separation / 2.0
                right_speed = self.target_velocity['linear'] + self.target_velocity['angular'] * wheel_separation / 2.0
                
                self.gpio_interface.set_motor_speed('left', left_speed / 2.0)
                self.gpio_interface.set_motor_speed('right', right_speed / 2.0)
            else:
                # Simulation control
                self.robot_sim.set_velocity(
                    self.target_velocity['linear'],
                    self.target_velocity['angular']
                )
                
            # Send manipulator commands
            if self.ros_manager and self.ros_manager.get_interface() and self.connected:
                self.ros_manager.get_interface().send_manipulator_command(
                    self.manipulator_vars['joint1'].get(),
                    self.manipulator_vars['joint2'].get(),
                    self.manipulator_vars['joint3'].get(),
                    self.manipulator_vars['gripper'].get()
                )
            else:
                # Simulation manipulator control
                self.robot_sim.set_manipulator_joints(
                    self.manipulator_vars['joint1'].get(),
                    self.manipulator_vars['joint2'].get(),
                    self.manipulator_vars['joint3'].get(),
                    self.manipulator_vars['gripper'].get()
                )
                
        except Exception as e:
            print(f"Command sending error: {e}")
            
    def stop_robot(self):
        """Stop robot movement"""
        self.target_velocity['linear'] = 0.0
        self.target_velocity['angular'] = 0.0
        
        if self.gpio_interface:
            self.gpio_interface.stop_all_motors()
            
        self.add_log("Robot stopped")
        
    def home_manipulator(self):
        """Home manipulator to zero position"""
        for var in self.manipulator_vars.values():
            var.set(0.0)
        self.add_log("Manipulator homed")
        
    def open_gripper(self):
        """Open gripper"""
        self.manipulator_vars['gripper'].set(100)
        self.add_log("Gripper opened")
        
    def close_gripper(self):
        """Close gripper"""
        self.manipulator_vars['gripper'].set(0)
        self.add_log("Gripper closed")
        
    def create_menu(self):
        """Create industrial menu bar"""
        menubar = tk.Menu(self.root, bg=self.colors['panel_bg'], fg=self.colors['text'])
        
        # System menu
        system_menu = tk.Menu(menubar, tearoff=0, bg=self.colors['panel_bg'], fg=self.colors['text'])
        menubar.add_cascade(label="SYSTEM", menu=system_menu)
        system_menu.add_command(label="Connect Robot", command=self.connect_robot)
        system_menu.add_command(label="Disconnect Robot", command=self.disconnect_robot)
        system_menu.add_separator()
        system_menu.add_command(label="Emergency Stop", command=self.emergency_stop_action)
        system_menu.add_command(label="Reset System", command=self.reset_system)
        system_menu.add_separator()
        system_menu.add_command(label="Exit", command=self.quit_app)
        
        # Control menu
        control_menu = tk.Menu(menubar, tearoff=0, bg=self.colors['panel_bg'], fg=self.colors['text'])
        menubar.add_cascade(label="CONTROL", menu=control_menu)
        control_menu.add_command(label="Keyboard Mode", command=lambda: self.set_control_mode("keyboard"))
        control_menu.add_command(label="Test Motors", command=self.test_motors)
        
        # Mode menu
        mode_menu = tk.Menu(menubar, tearoff=0, bg=self.colors['panel_bg'], fg=self.colors['text'])
        menubar.add_cascade(label="MODE", menu=mode_menu)
        mode_menu.add_command(label="Simulation Mode", command=lambda: self.set_mode("SIMULATION"))
        mode_menu.add_command(label="Real Robot Mode", command=lambda: self.set_mode("REAL"))
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0, bg=self.colors['panel_bg'], fg=self.colors['text'])
        menubar.add_cascade(label="HELP", menu=help_menu)
        help_menu.add_command(label="Control Guide", command=self.show_control_guide)
        help_menu.add_command(label="System Info", command=self.show_info)
        
        self.root.config(menu=menubar)
        
    def create_main_layout(self):
        """Create main industrial layout"""
        # Main container
        main_frame = Frame(self.root, bg=self.colors['bg'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Top status bar
        self.create_status_bar(main_frame)
        
        # Middle section with panels
        middle_frame = Frame(main_frame, bg=self.colors['bg'])
        middle_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Left panel - Telemetry and 3D View
        left_panel = Frame(middle_frame, bg=self.colors['panel_bg'], relief=tk.RIDGE, bd=2)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        self.create_telemetry_and_3d_panel(left_panel)
        
        # Center panel - Camera Views
        center_panel = Frame(middle_frame, bg=self.colors['panel_bg'], relief=tk.RIDGE, bd=2)
        center_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        self.create_camera_panel(center_panel)
        
        # Right panel - Control Status and Manipulator
        right_panel = Frame(middle_frame, bg=self.colors['panel_bg'], relief=tk.RIDGE, bd=2)
        right_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        self.create_control_and_manipulator_panel(right_panel)
        
    def create_status_bar(self, parent):
        """Create industrial status bar"""
        status_frame = Frame(parent, bg=self.colors['panel_bg'], height=40, relief=tk.RIDGE, bd=2)
        status_frame.pack(fill=tk.X, pady=(0, 5))
        status_frame.pack_propagate(False)
        
        # Connection status
        self.connection_indicator = Label(
            status_frame, text="SIMULATION MODE", bg=self.colors['info'], 
            fg=self.colors['text'], font=("Arial", 12, "bold"), width=15
        )
        self.connection_indicator.pack(side=tk.LEFT, padx=10, pady=5)
        
        # Control status
        self.control_status_label = Label(
            status_frame, text="CONTROL: KEYBOARD", bg=self.colors['panel_bg'],
            fg=self.colors['accent'], font=("Arial", 11, "bold")
        )
        self.control_status_label.pack(side=tk.LEFT, padx=20)
        
        # Robot status
        self.robot_status_label = Label(
            status_frame, text="STATUS: IDLE", bg=self.colors['panel_bg'],
            fg=self.colors['text'], font=("Arial", 11)
        )
        self.robot_status_label.pack(side=tk.LEFT, padx=20)
        
        # Emergency stop indicator
        self.emergency_indicator = Label(
            status_frame, text="EMERGENCY STOP: OFF", bg=self.colors['success'],
            fg=self.colors['text'], font=("Arial", 11, "bold"), width=20
        )
        self.emergency_indicator.pack(side=tk.LEFT, padx=20)
        
        # Battery indicator
        self.battery_label = Label(
            status_frame, text="BATTERY: 100%", bg=self.colors['panel_bg'],
            fg=self.colors['accent'], font=("Arial", 11)
        )
        self.battery_label.pack(side=tk.LEFT, padx=20)
        
        # Time
        self.time_label = Label(
            status_frame, text="", bg=self.colors['panel_bg'],
            fg=self.colors['text'], font=("Arial", 11)
        )
        self.time_label.pack(side=tk.RIGHT, padx=10)
        
        self.update_time()
        
    def create_telemetry_and_3d_panel(self, parent):
        """Create telemetry display with 3D visualization"""
        # Panel header
        header = Frame(parent, bg=self.colors['grid'], height=30)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        Label(header, text="TELEMETRY & 3D VIEW", bg=self.colors['grid'], 
               fg=self.colors['accent'], font=("Arial", 12, "bold")).pack(pady=5)
        
        # Content container
        content_frame = Frame(parent, bg=self.colors['panel_bg'])
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 3D Visualization (top half)
        viz_frame = Frame(content_frame, bg=self.colors['panel_bg'])
        viz_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        Label(viz_frame, text="3D ROBOT MODEL", bg=self.colors['panel_bg'],
               fg=self.colors['accent'], font=("Arial", 10, "bold")).pack(anchor=tk.W)
        
        self.robot_3d_canvas = Canvas(viz_frame, bg='#0a0a0a', width=400, height=250, 
                                      highlightthickness=1, highlightbackground=self.colors['grid'])
        self.robot_3d_canvas.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Telemetry data (bottom half)
        telemetry_frame = Frame(content_frame, bg=self.colors['panel_bg'])
        telemetry_frame.pack(fill=tk.BOTH, expand=True)
        
        Label(telemetry_frame, text="TELEMETRY DATA", bg=self.colors['panel_bg'],
               fg=self.colors['accent'], font=("Arial", 10, "bold")).pack(anchor=tk.W)
        
        # Position display
        pos_frame = Frame(telemetry_frame, bg=self.colors['panel_bg'])
        pos_frame.pack(fill=tk.X, pady=2)
        
        self.position_display = Label(pos_frame, text="X: 0.00m  Y: 0.00m  THETA: 0.00°",
                                     bg=self.colors['panel_bg'], fg=self.colors['text'],
                                     font=("Courier", 9))
        self.position_display.pack(anchor=tk.W, padx=10)
        
        # Velocity display
        vel_frame = Frame(telemetry_frame, bg=self.colors['panel_bg'])
        vel_frame.pack(fill=tk.X, pady=2)
        
        self.velocity_display = Label(vel_frame, text="Linear: 0.00m/s  Angular: 0.00rad/s",
                                     bg=self.colors['panel_bg'], fg=self.colors['text'],
                                     font=("Courier", 9))
        self.velocity_display.pack(anchor=tk.W, padx=10)
        
        # Motor status
        motor_frame = Frame(telemetry_frame, bg=self.colors['panel_bg'])
        motor_frame.pack(fill=tk.X, pady=2)
        
        self.motor_display = Label(motor_frame, text="Left: 0.00%  Right: 0.00%",
                                   bg=self.colors['panel_bg'], fg=self.colors['text'],
                                   font=("Courier", 9))
        self.motor_display.pack(anchor=tk.W, padx=10)
        
        # Sensor readings
        sensor_frame = Frame(telemetry_frame, bg=self.colors['panel_bg'])
        sensor_frame.pack(fill=tk.X, pady=2)
        
        self.sensor_display = Label(sensor_frame, text="US-F: 0.00m  US-R: 0.00m  IR-L: 0.00m  IR-R: 0.00m",
                                   bg=self.colors['panel_bg'], fg=self.colors['text'],
                                   font=("Courier", 9))
        self.sensor_display.pack(anchor=tk.W, padx=10)
        
        # System log (small)
        log_frame = Frame(telemetry_frame, bg=self.colors['panel_bg'])
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.system_log = Text(log_frame, height=4, bg='#0a0a0a', fg=self.colors['accent'],
                               font=("Courier", 8), wrap=tk.WORD)
        
        log_scrollbar = Scrollbar(log_frame, orient=tk.VERTICAL, command=self.system_log.yview)
        self.system_log.configure(yscrollcommand=log_scrollbar.set)
        
        self.system_log.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
    def create_camera_panel(self, parent):
        """Create camera view panel"""
        # Panel header
        header = Frame(parent, bg=self.colors['grid'], height=30)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        Label(header, text="CAMERA VIEWS", bg=self.colors['grid'],
               fg=self.colors['accent'], font=("Arial", 12, "bold")).pack(pady=5)
        
        # Camera views container
        camera_container = Frame(parent, bg=self.colors['panel_bg'])
        camera_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create 3 camera views
        cameras = ['FRONT CAMERA', 'REAR CAMERA', 'MANIPULATOR']
        self.camera_canvases = {}
        
        for i, camera_name in enumerate(cameras):
            # Camera frame
            cam_frame = Frame(camera_container, bg=self.colors['panel_bg'], relief=tk.SUNKEN, bd=2)
            if i == 0:
                cam_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
            elif i == 1:
                cam_frame.pack(fill=tk.BOTH, expand=True, pady=5)
            else:
                cam_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
            
            # Camera label
            Label(cam_frame, text=camera_name, bg=self.colors['panel_bg'],
                   fg=self.colors['text'], font=("Arial", 9, "bold")).pack(pady=2)
            
            # Camera canvas (simulated video feed)
            canvas = Canvas(cam_frame, bg='#000000', width=320, height=180)
            canvas.pack(padx=5, pady=5)
            
            self.camera_canvases[camera_name] = canvas
            
    def create_control_and_manipulator_panel(self, parent):
        """Create control status and manipulator panel"""
        # Panel header
        header = Frame(parent, bg=self.colors['grid'], height=30)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        Label(header, text="CONTROL STATUS & MANIPULATOR", bg=self.colors['grid'],
               fg=self.colors['accent'], font=("Arial", 12, "bold")).pack(pady=5)
        
        # Content container
        content_frame = Frame(parent, bg=self.colors['panel_bg'])
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Connection controls
        conn_frame = Frame(content_frame, bg=self.colors['panel_bg'])
        conn_frame.pack(fill=tk.X, pady=10)
        
        Label(conn_frame, text="ROBOT CONNECTION", bg=self.colors['panel_bg'],
               fg=self.colors['accent'], font=("Arial", 10, "bold")).pack(anchor=tk.W)
        
        # Namespace input
        ns_frame = Frame(conn_frame, bg=self.colors['panel_bg'])
        ns_frame.pack(fill=tk.X, pady=5)
        
        Label(ns_frame, text="Namespace:", bg=self.colors['panel_bg'],
               fg=self.colors['text'], font=("Arial", 9)).pack(side=tk.LEFT)
        
        Entry(ns_frame, textvariable=self.robot_namespace, bg=self.colors['grid'],
              fg=self.colors['text'], font=("Arial", 9)).pack(side=tk.LEFT, padx=5)
        
        # Control buttons
        button_frame = Frame(conn_frame, bg=self.colors['panel_bg'])
        button_frame.pack(fill=tk.X, pady=5)
        
        self.connect_btn = Button(button_frame, text="CONNECT", command=self.connect_robot,
                                 bg=self.colors['success'], fg=self.colors['text'],
                                 font=("Arial", 10, "bold"), width=12)
        self.connect_btn.pack(side=tk.LEFT, padx=2)
        
        self.disconnect_btn = Button(button_frame, text="DISCONNECT", command=self.disconnect_robot,
                                    bg=self.colors['warning'], fg=self.colors['text'],
                                    font=("Arial", 10, "bold"), width=12, state=tk.DISABLED)
        self.disconnect_btn.pack(side=tk.LEFT, padx=2)
        
        self.emergency_btn = Button(button_frame, text="E-STOP", command=self.emergency_stop_action,
                                   bg=self.colors['danger'], fg=self.colors['text'],
                                   font=("Arial", 10, "bold"), width=12)
        self.emergency_btn.pack(side=tk.LEFT, padx=2)
        
        # Control status display
        control_status_frame = Frame(content_frame, bg=self.colors['panel_bg'])
        control_status_frame.pack(fill=tk.X, pady=10)
        
        Label(control_status_frame, text="CONTROL STATUS", bg=self.colors['panel_bg'],
               fg=self.colors['accent'], font=("Arial", 10, "bold")).pack(anchor=tk.W)
        
        self.control_info_display = Label(control_status_frame, 
                                         text=f"Linear: {self.target_velocity['linear']:.2f}m/s | Angular: {self.target_velocity['angular']:.2f}rad/s",
                                         bg=self.colors['panel_bg'], fg=self.colors['text'],
                                         font=("Courier", 9))
        self.control_info_display.pack(anchor=tk.W, padx=10)
        
        # Active keys display
        active_keys_frame = Frame(content_frame, bg=self.colors['panel_bg'])
        active_keys_frame.pack(fill=tk.X, pady=10)
        
        Label(active_keys_frame, text="ACTIVE CONTROLS", bg=self.colors['panel_bg'],
               fg=self.colors['accent'], font=("Arial", 10, "bold")).pack(anchor=tk.W)
        
        self.active_keys_display = Label(active_keys_frame, text="No keys pressed",
                                         bg=self.colors['panel_bg'], fg=self.colors['text_secondary'],
                                         font=("Courier", 9))
        self.active_keys_display.pack(anchor=tk.W, padx=10)
        
        # Keyboard controls info
        keyboard_info_frame = Frame(content_frame, bg=self.colors['panel_bg'])
        keyboard_info_frame.pack(fill=tk.X, pady=10)
        
        Label(keyboard_info_frame, text="KEYBOARD CONTROLS", bg=self.colors['panel_bg'],
               fg=self.colors['accent'], font=("Arial", 10, "bold")).pack(anchor=tk.W)
        
        controls_text = """W/S: Forward/Backward | A/D: Left/Right | SPACE: Stop
Q/E: Joint1 | R/F: Joint2 | T/G: Joint3 | Z/X: Gripper | C: Home | ESC: E-Stop"""
        
        Label(keyboard_info_frame, text=controls_text, bg=self.colors['panel_bg'],
               fg=self.colors['text_secondary'], font=("Courier", 8), justify=tk.LEFT).pack(anchor=tk.W, padx=10)
        
        # Manipulator controls (single line layout)
        manip_frame = Frame(content_frame, bg=self.colors['panel_bg'])
        manip_frame.pack(fill=tk.X, pady=10)
        
        Label(manip_frame, text="MANIPULATOR CONTROL", bg=self.colors['panel_bg'],
               fg=self.colors['accent'], font=("Arial", 10, "bold")).pack(anchor=tk.W)
        
        # Single line manipulator controls
        manip_control_frame = Frame(manip_frame, bg=self.colors['panel_bg'])
        manip_control_frame.pack(fill=tk.X, pady=5)
        
        # Joint controls in single line
        joints = [
            ("J1", "joint1", -180, 180),
            ("J2", "joint2", -90, 90),
            ("J3", "joint3", -180, 180),
            ("Gripper", "gripper", 0, 100)
        ]
        
        for i, (label, var_name, min_val, max_val) in enumerate(joints):
            # Create frame for each joint
            joint_frame = Frame(manip_control_frame, bg=self.colors['panel_bg'])
            joint_frame.pack(side=tk.LEFT, padx=5)
            
            # Label
            Label(joint_frame, text=label, bg=self.colors['panel_bg'],
                   fg=self.colors['text'], font=("Arial", 8, "bold")).pack()
            
            # Scale (vertical orientation for compactness)
            Scale(joint_frame, from_=min_val, to=max_val, resolution=1,
                  orient=tk.VERTICAL, variable=self.manipulator_vars[var_name],
                  bg=self.colors['panel_bg'], fg=self.colors['text'],
                  troughcolor=self.colors['grid'], activebackground=self.colors['accent'],
                  length=80, width=8).pack()
            
            # Value display
            value_label = Label(joint_frame, text="0°", bg=self.colors['panel_bg'],
                             fg=self.colors['text_secondary'], font=("Arial", 7))
            value_label.pack()
            
            # Update value display
            def update_label(label=value_label, var=self.manipulator_vars[var_name], name=var_name):
                if name == "gripper":
                    label.config(text=f"{int(var.get())}%")
                else:
                    label.config(text=f"{int(var.get())}°")
                self.root.after(100, update_label, label, var, name)
            
            update_label()
        
        # Gripper action buttons (also in line)
        gripper_btn_frame = Frame(manip_control_frame, bg=self.colors['panel_bg'])
        gripper_btn_frame.pack(side=tk.LEFT, padx=10)
        
        Label(gripper_btn_frame, text="ACTIONS", bg=self.colors['panel_bg'],
               fg=self.colors['text'], font=("Arial", 8, "bold")).pack()
        
        Button(gripper_btn_frame, text="OPEN", command=self.open_gripper,
               bg=self.colors['success'], fg=self.colors['text'],
               font=("Arial", 8, "bold"), width=6).pack(pady=2)
        
        Button(gripper_btn_frame, text="CLOSE", command=self.close_gripper,
               bg=self.colors['danger'], fg=self.colors['text'],
               font=("Arial", 8, "bold"), width=6).pack(pady=2)
        
        Button(gripper_btn_frame, text="HOME", command=self.home_manipulator,
               bg=self.colors['info'], fg=self.colors['text'],
               font=("Arial", 8, "bold"), width=6).pack(pady=2)
        
    # Callback functions
    def input_callback(self, data_type, data):
        """Handle input controller callbacks"""
        if data_type == 'velocity':
            self.target_velocity['linear'] = data['linear']
            self.target_velocity['angular'] = data['angular']
            
        elif data_type == 'emergency_stop':
            self.emergency_stop = data
            self.update_emergency_status()
            
        elif data_type == 'gripper':
            if data == 'open':
                self.open_gripper()
            elif data == 'close':
                self.close_gripper()
                
    def ros_callback(self, data_type, data):
        """Handle ROS2 callbacks"""
        if data_type == 'log':
            self.add_log(data)
        elif data_type == 'connection':
            self.connected = data
            self.update_connection_status()
        elif data_type == 'odometry':
            self.telemetry['position'].update(data['position'])
            self.telemetry['velocity'].update(data['velocity'])
        elif data_type == 'battery':
            self.telemetry['battery'] = data['percentage']
        elif data_type == 'sensor':
            self.telemetry['sensors'][data['type']] = data['value']
        elif data_type == 'manipulator':
            self.telemetry['manipulator'].update(data)
        elif data_type == 'imu':
            self.telemetry['imu'].update(data)
        elif data_type == 'emergency_stop':
            self.emergency_stop = data
            self.update_emergency_status()
        elif data_type == 'mode':
            self.robot_mode.set(data)
            
    def update_telemetry_loop(self):
        """Update telemetry displays"""
        while self.telemetry_thread_running:
            try:
                # Update active keys display
                active_keys = [k.upper() for k, v in self.key_pressed.items() if v]
                if active_keys:
                    self.active_keys_display.config(text=f"Keys: {', '.join(active_keys)}")
                else:
                    self.active_keys_display.config(text="No keys pressed")
                
                # Update control info display
                self.control_info_display.config(
                    text=f"Linear: {self.target_velocity['linear']:.2f}m/s | Angular: {self.target_velocity['angular']:.2f}rad/s"
                )
                
                # Update displays
                pos = self.telemetry['position']
                self.position_display.config(
                    text=f"X: {pos['x']:.2f}m  Y: {pos['y']:.2f}m  THETA: {math.degrees(pos['theta']):.2f}°"
                )
                
                vel = self.telemetry['velocity']
                self.velocity_display.config(
                    text=f"Linear: {vel['linear']:.2f}m/s  Angular: {vel['angular']:.2f}rad/s"
                )
                
                motors = self.telemetry['motors']
                self.motor_display.config(
                    text=f"Left: {motors['left']:.1f}%  Right: {motors['right']:.1f}%"
                )
                
                sensors = self.telemetry['sensors']
                self.sensor_display.config(
                    text=f"US-F: {sensors['ultrasonic_front']:.2f}m  US-R: {sensors['ultrasonic_rear']:.2f}m  IR-L: {sensors['infrared_left']:.2f}m  IR-R: {sensors['infrared_right']:.2f}m"
                )
                
                self.battery_label.config(text=f"BATTERY: {self.telemetry['battery']:.1f}%")
                self.robot_status_label.config(text=f"STATUS: {self.telemetry['status']}")
                
                time.sleep(0.1)
            except:
                break
                
    def simulation_loop(self):
        """Update robot simulation"""
        last_time = time.time()
        
        while self.simulation_thread_running:
            try:
                current_time = time.time()
                dt = current_time - last_time
                last_time = current_time
                
                if self.simulation_mode and not self.emergency_stop:
                    # Update simulation
                    self.robot_sim.update(dt)
                    
                    # Update telemetry from simulation
                    self.telemetry['position']['x'] = self.robot_sim.position.x
                    self.telemetry['position']['y'] = self.robot_sim.position.y
                    self.telemetry['position']['theta'] = self.robot_sim.orientation
                    self.telemetry['velocity']['linear'] = self.robot_sim.linear_velocity
                    self.telemetry['velocity']['angular'] = self.robot_sim.angular_velocity
                    
                    # Simulate sensor readings
                    sensor_readings = self.robot_sim.simulate_sensors()
                    self.telemetry['sensors'].update(sensor_readings)
                    
                    # Update motor values
                    self.telemetry['motors']['left'] = (self.target_velocity['linear'] - 
                                                       self.target_velocity['angular'] * 0.3) * 50
                    self.telemetry['motors']['right'] = (self.target_velocity['linear'] + 
                                                        self.target_velocity['angular'] * 0.3) * 50
                    
                    # Update status
                    if abs(self.telemetry['velocity']['linear']) > 0.1 or abs(self.telemetry['velocity']['angular']) > 0.1:
                        self.telemetry['status'] = 'MOVING'
                    else:
                        self.telemetry['status'] = 'IDLE'
                        
                    # Update 3D visualization
                    self.draw_robot_3d()
                    
                # Update camera feeds
                self.update_camera_feeds()
                
                time.sleep(0.05)  # 20 Hz update rate
            except:
                break
                
    def draw_robot_3d(self):
        """Draw 3D robot visualization"""
        canvas = self.robot_3d_canvas
        canvas.delete("all")
        
        # Simple 2D projection of 3D robot
        cx, cy = 200, 125  # Canvas center
        scale = 50  # Scale factor
        
        # Draw robot chassis
        chassis_verts = self.robot_sim.get_chassis_vertices()
        if chassis_verts:
            # Project to 2D and draw
            points = []
            for v in chassis_verts[:4]:  # Bottom face only
                x = cx + v.x * scale
                y = cy - v.y * scale
                points.extend([x, y])
                
            if len(points) >= 6:
                canvas.create_polygon(points, fill='#2a2a2a', outline=self.colors['accent'], width=2)
                
        # Draw tracks
        for side in ['left', 'right']:
            track_segments = self.robot_sim.get_track_vertices(side)
            for segment in track_segments:
                points = []
                for v in segment[:4]:  # Bottom face
                    x = cx + v.x * scale
                    y = cy - v.y * scale
                    points.extend([x, y])
                    
                if len(points) >= 6:
                    canvas.create_polygon(points, fill='#1a1a1a', outline=self.colors['warning'], width=1)
                    
        # Draw manipulator
        manipulator_links = self.robot_sim.get_manipulator_vertices()
        for link in manipulator_links:
            if len(link) >= 2:
                x1 = cx + link[0].x * scale
                y1 = cy - link[0].y * scale
                x2 = cx + link[1].x * scale
                y2 = cy - link[1].y * scale
                canvas.create_line(x1, y1, x2, y2, fill=self.colors['info'], width=3)
                
        # Draw gripper
        gripper_verts = self.robot_sim.get_gripper_vertices()
        if gripper_verts:
            points = []
            for v in gripper_verts:
                x = cx + v.x * scale
                y = cy - v.y * scale
                points.extend([x, y])
                
            if len(points) >= 6:
                canvas.create_polygon(points, fill='', outline=self.colors['success'], width=2)
                
        # Draw direction indicator
        dir_x = cx + math.cos(self.robot_sim.orientation) * 30
        dir_y = cy - math.sin(self.robot_sim.orientation) * 30
        canvas.create_line(cx, cy, dir_x, dir_y, fill=self.colors['danger'], width=2, arrow=tk.LAST)
        
    def update_camera_feeds(self):
        """Update camera visualizations"""
        for camera_name, canvas in self.camera_canvases.items():
            canvas.delete("all")
            
            if self.connected or self.simulation_mode:
                # Simulate video feed
                canvas.create_rectangle(0, 0, 320, 180, fill="#001100", outline="")
                
                # Add some simulated video elements
                import random
                for _ in range(15):
                    x = random.randint(0, 320)
                    y = random.randint(0, 180)
                    canvas.create_oval(x-1, y-1, x+1, y+1, fill="#00ff00", outline="")
                    
                # Add timestamp
                timestamp = datetime.now().strftime("%H:%M:%S")
                canvas.create_text(5, 5, text=camera_name, fill="#00ff00", 
                                  font=("Arial", 8), anchor="nw")
                canvas.create_text(5, 175, text=timestamp, fill="#00ff00", 
                                  font=("Arial", 8), anchor="sw")
                                  
                # Add robot position info
                canvas.create_text(160, 90, text=f"X: {self.telemetry['position']['x']:.1f} Y: {self.telemetry['position']['y']:.1f}",
                                  fill="#00ff00", font=("Arial", 10))
            else:
                # Show "NO SIGNAL"
                canvas.create_rectangle(0, 0, 320, 180, fill="#000000", outline="")
                canvas.create_text(160, 90, text="NO SIGNAL", fill="#ff0000", 
                                  font=("Arial", 16, "bold"))
                                  
    def update_time(self):
        """Update time display"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.time_label.config(text=current_time)
        self.root.after(1000, self.update_time)
        
    def update_connection_status(self):
        """Update connection status display"""
        if self.connected:
            self.connection_indicator.config(text="CONNECTED", bg=self.colors['success'])
            self.connect_btn.config(state=tk.DISABLED)
            self.disconnect_btn.config(state=tk.NORMAL)
        else:
            self.connection_indicator.config(text="DISCONNECTED", bg=self.colors['danger'])
            self.connect_btn.config(state=tk.NORMAL)
            self.disconnect_btn.config(state=tk.DISABLED)
            
    def update_emergency_status(self):
        """Update emergency stop status"""
        if self.emergency_stop:
            self.emergency_indicator.config(text="EMERGENCY STOP: ON", bg=self.colors['danger'])
        else:
            self.emergency_indicator.config(text="EMERGENCY STOP: OFF", bg=self.colors['success'])
            
    def set_control_mode(self, mode):
        """Set control mode"""
        self.control_status_label.config(text=f"CONTROL: {mode.upper()}")
        self.add_log(f"Control mode changed to: {mode}")
        
    def set_mode(self, mode):
        """Set robot operation mode"""
        self.simulation_mode = (mode == "SIMULATION")
        
        if self.simulation_mode:
            self.connection_indicator.config(text="SIMULATION MODE", bg=self.colors['info'])
        else:
            self.connection_indicator.config(text="REAL ROBOT MODE", bg=self.colors['warning'])
            
        self.add_log(f"Mode changed to: {mode}")
        
    def test_motors(self):
        """Test motor functionality"""
        self.add_log("Testing motors...")
        
        # Test sequence
        test_sequence = [
            (0.5, 0.0),   # Forward
            (0.0, 0.5),   # Right
            (-0.5, 0.0),  # Backward
            (0.0, -0.5),  # Left
            (0.0, 0.0)    # Stop
        ]
        
        def run_test():
            for i, (linear, angular) in enumerate(test_sequence):
                self.target_velocity['linear'] = linear
                self.target_velocity['angular'] = angular
                self.add_log(f"Test {i+1}: Linear={linear:.1f}, Angular={angular:.1f}")
                time.sleep(2)
                
            self.add_log("Motor test completed")
            
        test_thread = threading.Thread(target=run_test, daemon=True)
        test_thread.start()
        
    # Control functions
    def connect_robot(self):
        """Connect to robot"""
        if self.simulation_mode:
            self.add_log("Simulation mode - no physical connection needed")
            self.connected = True
            self.update_connection_status()
            return
            
        if self.ros_manager:
            namespace = self.robot_namespace.get()
            if self.ros_manager.get_interface():
                success = self.ros_manager.get_interface().connect(namespace)
                if success:
                    self.add_log(f"Connected to robot: {namespace}")
                else:
                    self.add_log(f"Failed to connect to robot: {namespace}")
                    
    def disconnect_robot(self):
        """Disconnect from robot"""
        if self.ros_manager and self.ros_manager.get_interface():
            self.ros_manager.get_interface().disconnect()
            
        self.connected = False
        self.update_connection_status()
        self.add_log("Disconnected from robot")
        
    def emergency_stop_action(self):
        """Emergency stop action"""
        self.emergency_stop = not self.emergency_stop
        
        if self.ros_manager and self.ros_manager.get_interface():
            self.ros_manager.get_interface().emergency_stop_action(self.emergency_stop)
            
        if self.emergency_stop:
            self.target_velocity['linear'] = 0.0
            self.target_velocity['angular'] = 0.0
            if self.gpio_interface:
                self.gpio_interface.emergency_stop()
            self.add_log("EMERGENCY STOP ACTIVATED")
        else:
            self.add_log("Emergency stop deactivated")
            
        self.update_emergency_status()
        
    def reset_system(self):
        """Reset robot system"""
        self.emergency_stop = False
        self.target_velocity['linear'] = 0.0
        self.target_velocity['angular'] = 0.0
        
        for var in self.manipulator_vars.values():
            var.set(0.0)
            
        self.robot_sim.reset()
        
        if self.ros_manager and self.ros_manager.get_interface():
            self.ros_manager.get_interface().reset_system()
            
        self.add_log("System reset completed")
        self.update_emergency_status()
        
    def add_log(self, message):
        """Add message to system log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        self.system_log.insert(tk.END, log_entry)
        self.system_log.see(tk.END)
        
        # Keep only last 50 lines
        lines = self.system_log.get(1.0, tk.END).split('\n')
        if len(lines) > 50:
            self.system_log.delete(1.0, f"{len(lines)-49}.0")
            
    def show_control_guide(self):
        """Show control guide"""
        guide = """
SANHUM ROBOT CONTROL GUIDE v5.0
================================

KEYBOARD CONTROLS:
- W/S: Forward/Backward movement
- A/D: Left/Right rotation
- SPACE: Stop all movement
- Q/E: Joint1 rotation (base)
- R/F: Joint2 movement (shoulder)
- T/G: Joint3 movement (elbow)
- Z/X: Gripper open/close
- C: Home all manipulator joints
- ESC: Emergency stop

BUTTON CONTROLS:
- CONNECT: Connect to robot
- DISCONNECT: Disconnect from robot
- E-STOP: Emergency stop
- OPEN/CLOSE/HOME: Gripper controls

REAL-TIME FEEDBACK:
- Active keys display shows current input
- Velocity display shows actual robot speed
- 3D visualization updates in real-time
- Telemetry data updates continuously

SAFETY FEATURES:
- Emergency stop always available
- Real-time velocity monitoring
- System logging for diagnostics
        """
        messagebox.showinfo("Control Guide", guide)
        
    def show_info(self):
        """Show system information"""
        info = f"""
SANHUM ROBOT CONTROL SYSTEM v5.0
================================

SYSTEM:
Python: {sys.version.split()[0]}
Platform: {sys.platform}
GUI Framework: Tkinter
ROS2 Interface: {'Available' if ROS2_AVAILABLE else 'Not Available'}
GPIO Interface: {'Available' if self.gpio_interface else 'Not Available'}

STATUS:
Connection: {'Connected' if self.connected else 'Disconnected'}
Mode: {'Simulation' if self.simulation_mode else 'Real Robot'}
Emergency Stop: {'Active' if self.emergency_stop else 'Inactive'}

ROBOT:
Position: X={self.telemetry['position']['x']:.2f}m, Y={self.telemetry['position']['y']:.2f}m
Velocity: Linear={self.telemetry['velocity']['linear']:.2f}m/s, Angular={self.telemetry['velocity']['angular']:.2f}rad/s
Battery: {self.telemetry['battery']:.1f}%

© 2024 Sanhum Robot Project
Working Version - Functional Controls
        """
        messagebox.showinfo("System Information", info)
        
    def quit_app(self):
        """Quit application"""
        if messagebox.askokcancel("Exit", "Are you sure you want to exit the robot control system?"):
            self.telemetry_thread_running = False
            self.input_thread_running = False
            self.simulation_thread_running = False
            
            if self.input_controller:
                self.input_controller.stop()
                
            if self.ros_manager:
                self.ros_manager.stop_ros()
                
            if self.gpio_interface:
                self.gpio_interface.cleanup()
                
            if self.connected:
                self.disconnect_robot()
                
            self.root.quit()
            
    def run(self):
        """Start the GUI"""
        self.add_log("Sanhum Robot Control System v5.0 initialized")
        self.add_log(f"ROS2 Interface: {'Available' if ROS2_AVAILABLE else 'Not Available'}")
        self.add_log(f"GPIO Interface: {'Available' if self.gpio_interface else 'Not Available'}")
        self.add_log("Keyboard controls ready - Use W/A/S/D to move robot")
        self.add_log("System ready - Press keys to control robot")
        
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.quit_app()

if __name__ == "__main__":
    app = WorkingRobotGUI()
    app.run()
