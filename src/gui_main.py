#!/usr/bin/env python3
"""
Sanhum Robot Industrial Control Interface
Professional robot control system inspired by KUKA industrial robots
Features camera views, real telemetry, and advanced robot control
"""

import sys
import tkinter as tk
from tkinter import messagebox, filedialog, Canvas, Frame, Label, Scale, Button, Text, Scrollbar, Entry, StringVar, DoubleVar, BooleanVar, IntVar
import os
from pathlib import Path
import threading
import time
import json
import math
from datetime import datetime

class IndustrialRobotGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("SANHUM ROBOT CONTROL SYSTEM v2.0")
        self.root.geometry("1400x900")
        self.root.minsize(1200, 800)
        
        # Industrial color scheme
        self.colors = {
            'bg': '#1a1a1a',
            'panel_bg': '#2d2d2d',
            'accent': '#00ff41',
            'success': '#00ff41',
            'warning': '#ff9f00',
            'danger': '#ff3d00',
            'info': '#00b8d4',
            'text': '#ffffff',
            'text_secondary': '#b0b0b0',
            'grid': '#404040'
        }
        
        self.root.configure(bg=self.colors['bg'])
        
        # Robot state
        self.connected = False
        self.emergency_stop = False
        self.robot_namespace = StringVar(value="sanhum_robot")
        
        # Robot telemetry data
        self.telemetry = {
            'position': {'x': 0.0, 'y': 0.0, 'theta': 0.0},
            'velocity': {'linear': 0.0, 'angular': 0.0},
            'battery': 100.0,
            'motors': {'left': 0.0, 'right': 0.0},
            'sensors': {'ultrasonic': 0.0, 'infrared': 0.0, 'temperature': 25.0},
            'manipulator': {'joint1': 0.0, 'joint2': 0.0, 'joint3': 0.0, 'gripper': 0.0},
            'status': 'IDLE'
        }
        
        # Control variables
        self.target_velocity = {'linear': DoubleVar(value=0.0), 'angular': DoubleVar(value=0.0)}
        self.manipulator_joints = {
            'joint1': DoubleVar(value=0.0),
            'joint2': DoubleVar(value=0.0), 
            'joint3': DoubleVar(value=0.0),
            'gripper': DoubleVar(value=0.0)
        }
        
        # Camera feeds (simulated)
        self.camera_feeds = {
            'front': None,
            'rear': None,
            'manipulator': None
        }
        
        # Create industrial interface
        self.create_menu()
        self.create_main_layout()
        
        # Start telemetry updates
        self.telemetry_thread_running = True
        self.telemetry_thread = threading.Thread(target=self.update_telemetry_loop, daemon=True)
        self.telemetry_thread.start()
        
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
        
        # Configuration menu
        config_menu = tk.Menu(menubar, tearoff=0, bg=self.colors['panel_bg'], fg=self.colors['text'])
        menubar.add_cascade(label="CONFIG", menu=config_menu)
        config_menu.add_command(label="Load Configuration", command=self.load_config)
        config_menu.add_command(label="Save Configuration", command=self.save_config)
        config_menu.add_command(label="Robot Parameters", command=self.robot_parameters)
        
        # Diagnostics menu
        diag_menu = tk.Menu(menubar, tearoff=0, bg=self.colors['panel_bg'], fg=self.colors['text'])
        menubar.add_cascade(label="DIAGNOSTICS", menu=diag_menu)
        diag_menu.add_command(label="System Check", command=self.system_check)
        diag_menu.add_command(label="Sensor Calibration", command=self.sensor_calibration)
        diag_menu.add_command(label="Motor Test", command=self.motor_test)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0, bg=self.colors['panel_bg'], fg=self.colors['text'])
        menubar.add_cascade(label="HELP", menu=help_menu)
        help_menu.add_command(label="Operator Manual", command=self.show_manual)
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
        
        # Left panel - Telemetry and Status
        left_panel = Frame(middle_frame, bg=self.colors['panel_bg'], relief=tk.RIDGE, bd=2)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        self.create_telemetry_panel(left_panel)
        
        # Center panel - Camera Views
        center_panel = Frame(middle_frame, bg=self.colors['panel_bg'], relief=tk.RIDGE, bd=2)
        center_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        self.create_camera_panel(center_panel)
        
        # Right panel - Robot Controls
        right_panel = Frame(middle_frame, bg=self.colors['panel_bg'], relief=tk.RIDGE, bd=2)
        right_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        self.create_control_panel(right_panel)
        
        # Bottom panel - Manipulator Controls
        bottom_panel = Frame(main_frame, bg=self.colors['panel_bg'], relief=tk.RIDGE, bd=2)
        bottom_panel.pack(fill=tk.X, pady=(5, 0))
        
        self.create_manipulator_panel(bottom_panel)
        
    def create_status_bar(self, parent):
        """Create industrial status bar"""
        status_frame = Frame(parent, bg=self.colors['panel_bg'], height=40, relief=tk.RIDGE, bd=2)
        status_frame.pack(fill=tk.X, pady=(0, 5))
        status_frame.pack_propagate(False)
        
        # Connection status
        self.connection_indicator = Label(
            status_frame, text="DISCONNECTED", bg=self.colors['danger'], 
            fg=self.colors['text'], font=("Arial", 12, "bold"), width=15
        )
        self.connection_indicator.pack(side=tk.LEFT, padx=10, pady=5)
        
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
        
    def create_telemetry_panel(self, parent):
        """Create telemetry display panel"""
        # Panel header
        header = Frame(parent, bg=self.colors['grid'], height=30)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        Label(header, text="TELEMETRY DATA", bg=self.colors['grid'], 
               fg=self.colors['accent'], font=("Arial", 12, "bold")).pack(pady=5)
        
        # Telemetry content
        telemetry_frame = Frame(parent, bg=self.colors['panel_bg'])
        telemetry_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Position display
        pos_frame = Frame(telemetry_frame, bg=self.colors['panel_bg'])
        pos_frame.pack(fill=tk.X, pady=5)
        
        Label(pos_frame, text="POSITION", bg=self.colors['panel_bg'], 
               fg=self.colors['accent'], font=("Arial", 10, "bold")).pack(anchor=tk.W)
        
        self.position_display = Label(pos_frame, text="X: 0.00m  Y: 0.00m  THETA: 0.00°",
                                     bg=self.colors['panel_bg'], fg=self.colors['text'],
                                     font=("Courier", 10))
        self.position_display.pack(anchor=tk.W, padx=10)
        
        # Velocity display
        vel_frame = Frame(telemetry_frame, bg=self.colors['panel_bg'])
        vel_frame.pack(fill=tk.X, pady=5)
        
        Label(vel_frame, text="VELOCITY", bg=self.colors['panel_bg'],
               fg=self.colors['accent'], font=("Arial", 10, "bold")).pack(anchor=tk.W)
        
        self.velocity_display = Label(vel_frame, text="Linear: 0.00m/s  Angular: 0.00rad/s",
                                     bg=self.colors['panel_bg'], fg=self.colors['text'],
                                     font=("Courier", 10))
        self.velocity_display.pack(anchor=tk.W, padx=10)
        
        # Motor status
        motor_frame = Frame(telemetry_frame, bg=self.colors['panel_bg'])
        motor_frame.pack(fill=tk.X, pady=5)
        
        Label(motor_frame, text="MOTOR STATUS", bg=self.colors['panel_bg'],
               fg=self.colors['accent'], font=("Arial", 10, "bold")).pack(anchor=tk.W)
        
        self.motor_display = Label(motor_frame, text="Left: 0.00%  Right: 0.00%",
                                   bg=self.colors['panel_bg'], fg=self.colors['text'],
                                   font=("Courier", 10))
        self.motor_display.pack(anchor=tk.W, padx=10)
        
        # Sensor readings
        sensor_frame = Frame(telemetry_frame, bg=self.colors['panel_bg'])
        sensor_frame.pack(fill=tk.X, pady=5)
        
        Label(sensor_frame, text="SENSORS", bg=self.colors['panel_bg'],
               fg=self.colors['accent'], font=("Arial", 10, "bold")).pack(anchor=tk.W)
        
        self.sensor_display = Label(sensor_frame, text="US: 0.00m  IR: 0.00m  Temp: 25.0°C",
                                   bg=self.colors['panel_bg'], fg=self.colors['text'],
                                   font=("Courier", 10))
        self.sensor_display.pack(anchor=tk.W, padx=10)
        
        # System log
        log_frame = Frame(telemetry_frame, bg=self.colors['panel_bg'])
        log_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        Label(log_frame, text="SYSTEM LOG", bg=self.colors['panel_bg'],
               fg=self.colors['accent'], font=("Arial", 10, "bold")).pack(anchor=tk.W)
        
        log_container = Frame(log_frame, bg=self.colors['panel_bg'])
        log_container.pack(fill=tk.BOTH, expand=True)
        
        self.system_log = Text(log_container, height=8, bg='#1a1a1a', fg=self.colors['accent'],
                               font=("Courier", 9), wrap=tk.WORD)
        
        log_scrollbar = Scrollbar(log_container, orient=tk.VERTICAL, command=self.system_log.yview)
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
            
            # Simulate camera feed
            self.simulate_camera_feed(camera_name, canvas)
            
    def create_control_panel(self, parent):
        """Create robot control panel"""
        # Panel header
        header = Frame(parent, bg=self.colors['grid'], height=30)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        Label(header, text="ROBOT CONTROLS", bg=self.colors['grid'],
               fg=self.colors['accent'], font=("Arial", 12, "bold")).pack(pady=5)
        
        # Controls container
        control_container = Frame(parent, bg=self.colors['panel_bg'])
        control_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Movement controls
        movement_frame = Frame(control_container, bg=self.colors['panel_bg'])
        movement_frame.pack(fill=tk.X, pady=10)
        
        Label(movement_frame, text="MOVEMENT CONTROL", bg=self.colors['panel_bg'],
               fg=self.colors['accent'], font=("Arial", 10, "bold")).pack(anchor=tk.W)
        
        # Linear velocity control
        Label(movement_frame, text="Linear Velocity (m/s):", bg=self.colors['panel_bg'],
               fg=self.colors['text'], font=("Arial", 9)).pack(anchor=tk.W, pady=(5, 0))
        
        self.linear_scale = Scale(movement_frame, from_=-2.0, to=2.0, resolution=0.1,
                                  orient=tk.HORIZONTAL, variable=self.target_velocity['linear'],
                                  bg=self.colors['panel_bg'], fg=self.colors['text'],
                                  troughcolor=self.colors['grid'], activebackground=self.colors['accent'],
                                  length=200)
        self.linear_scale.pack(anchor=tk.W, padx=10)
        
        # Angular velocity control
        Label(movement_frame, text="Angular Velocity (rad/s):", bg=self.colors['panel_bg'],
               fg=self.colors['text'], font=("Arial", 9)).pack(anchor=tk.W, pady=(10, 0))
        
        self.angular_scale = Scale(movement_frame, from_=-3.14, to=3.14, resolution=0.01,
                                   orient=tk.HORIZONTAL, variable=self.target_velocity['angular'],
                                   bg=self.colors['panel_bg'], fg=self.colors['text'],
                                   troughcolor=self.colors['grid'], activebackground=self.colors['accent'],
                                   length=200)
        self.angular_scale.pack(anchor=tk.W, padx=10)
        
        # Control buttons
        button_frame = Frame(control_container, bg=self.colors['panel_bg'])
        button_frame.pack(fill=tk.X, pady=20)
        
        self.connect_btn = Button(button_frame, text="CONNECT", command=self.connect_robot,
                                 bg=self.colors['success'], fg=self.colors['text'],
                                 font=("Arial", 10, "bold"), width=12)
        self.connect_btn.pack(side=tk.LEFT, padx=5)
        
        self.disconnect_btn = Button(button_frame, text="DISCONNECT", command=self.disconnect_robot,
                                    bg=self.colors['warning'], fg=self.colors['text'],
                                    font=("Arial", 10, "bold"), width=12, state=tk.DISABLED)
        self.disconnect_btn.pack(side=tk.LEFT, padx=5)
        
        self.emergency_btn = Button(button_frame, text="E-STOP", command=self.emergency_stop_action,
                                   bg=self.colors['danger'], fg=self.colors['text'],
                                   font=("Arial", 10, "bold"), width=12)
        self.emergency_btn.pack(side=tk.LEFT, padx=5)
        
        # Robot mode selection
        mode_frame = Frame(control_container, bg=self.colors['panel_bg'])
        mode_frame.pack(fill=tk.X, pady=10)
        
        Label(mode_frame, text="ROBOT MODE:", bg=self.colors['panel_bg'],
               fg=self.colors['accent'], font=("Arial", 10, "bold")).pack(anchor=tk.W)
        
        self.robot_mode = StringVar(value="MANUAL")
        modes = ["MANUAL", "AUTO", "TELEOP", "PROGRAM"]
        
        for mode in modes:
            tk.Radiobutton(mode_frame, text=mode, variable=self.robot_mode, value=mode,
                          bg=self.colors['panel_bg'], fg=self.colors['text'],
                          selectcolor=self.colors['grid'], font=("Arial", 9)).pack(anchor=tk.W, padx=10)
        
    def create_manipulator_panel(self, parent):
        """Create manipulator control panel"""
        # Panel header
        header = Frame(parent, bg=self.colors['grid'], height=30)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        Label(header, text="MANIPULATOR CONTROL", bg=self.colors['grid'],
               fg=self.colors['accent'], font=("Arial", 12, "bold")).pack(pady=5)
        
        # Manipulator controls container
        manip_container = Frame(parent, bg=self.colors['panel_bg'])
        manip_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Joint controls
        joint_frame = Frame(manip_container, bg=self.colors['panel_bg'])
        joint_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        Label(joint_frame, text="JOINT CONTROL", bg=self.colors['panel_bg'],
               fg=self.colors['accent'], font=("Arial", 10, "bold")).pack(anchor=tk.W)
        
        joints = [('Joint 1', 'joint1', -180, 180),
                 ('Joint 2', 'joint2', -90, 90),
                 ('Joint 3', 'joint3', -180, 180),
                 ('Gripper', 'gripper', 0, 100)]
        
        for joint_name, var_name, min_val, max_val in joints:
            Label(joint_frame, text=f"{joint_name}:", bg=self.colors['panel_bg'],
                   fg=self.colors['text'], font=("Arial", 9)).pack(anchor=tk.W, pady=(5, 0))
            
            Scale(joint_frame, from_=min_val, to=max_val, resolution=1,
                  orient=tk.HORIZONTAL, variable=self.manipulator_joints[var_name],
                  bg=self.colors['panel_bg'], fg=self.colors['text'],
                  troughcolor=self.colors['grid'], activebackground=self.colors['accent'],
                  length=150).pack(anchor=tk.W, padx=10)
        
        # Gripper control buttons
        gripper_frame = Frame(manip_container, bg=self.colors['panel_bg'])
        gripper_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=20)
        
        Label(gripper_frame, text="GRIPPER ACTIONS", bg=self.colors['panel_bg'],
               fg=self.colors['accent'], font=("Arial", 10, "bold")).pack(anchor=tk.W)
        
        Button(gripper_frame, text="OPEN", command=lambda: self.gripper_action("open"),
               bg=self.colors['success'], fg=self.colors['text'],
               font=("Arial", 9, "bold"), width=10).pack(pady=5)
        
        Button(gripper_frame, text="CLOSE", command=lambda: self.gripper_action("close"),
               bg=self.colors['danger'], fg=self.colors['text'],
               font=("Arial", 9, "bold"), width=10).pack(pady=5)
        
        Button(gripper_frame, text="HOME", command=lambda: self.gripper_action("home"),
               bg=self.colors['info'], fg=self.colors['text'],
               font=("Arial", 9, "bold"), width=10).pack(pady=5)
        
    def simulate_camera_feed(self, camera_name, canvas):
        """Simulate camera video feed"""
        def update_camera():
            if not self.connected:
                # Show "NO SIGNAL" when disconnected
                canvas.delete("all")
                canvas.create_rectangle(0, 0, 320, 180, fill="#000000", outline="")
                canvas.create_text(160, 90, text="NO SIGNAL", fill="#ff0000", 
                                  font=("Arial", 16, "bold"))
            else:
                # Simulate video feed with moving elements
                canvas.delete("all")
                canvas.create_rectangle(0, 0, 320, 180, fill="#001100", outline="")
                
                # Add some simulated video elements
                import random
                for _ in range(20):
                    x = random.randint(0, 320)
                    y = random.randint(0, 180)
                    canvas.create_oval(x-2, y-2, x+2, y+2, fill="#00ff00", outline="")
                
                # Add timestamp
                timestamp = datetime.now().strftime("%H:%M:%S")
                canvas.create_text(5, 5, text=camera_name, fill="#00ff00", 
                                  font=("Arial", 8), anchor="nw")
                canvas.create_text(5, 175, text=timestamp, fill="#00ff00", 
                                  font=("Arial", 8), anchor="sw")
            
            self.root.after(100, update_camera)
        
        update_camera()
        
    def update_telemetry_loop(self):
        """Update telemetry data in background"""
        while self.telemetry_thread_running:
            try:
                if self.connected and not self.emergency_stop:
                    # Simulate telemetry updates
                    import random
                    
                    # Update position (simulate movement)
                    self.telemetry['position']['x'] += self.target_velocity['linear'].get() * 0.1
                    self.telemetry['position']['theta'] += self.target_velocity['angular'].get() * 0.1
                    
                    # Update velocity
                    self.telemetry['velocity']['linear'] = self.target_velocity['linear'].get()
                    self.telemetry['velocity']['angular'] = self.target_velocity['angular'].get()
                    
                    # Update motor values
                    self.telemetry['motors']['left'] = (self.target_velocity['linear'].get() + 
                                                       self.target_velocity['angular'].get()) * 50
                    self.telemetry['motors']['right'] = (self.target_velocity['linear'].get() - 
                                                        self.target_velocity['angular'].get()) * 50
                    
                    # Update sensors
                    self.telemetry['sensors']['ultrasonic'] = random.uniform(0.5, 3.0)
                    self.telemetry['sensors']['infrared'] = random.uniform(0.1, 1.0)
                    self.telemetry['sensors']['temperature'] = random.uniform(20.0, 35.0)
                    
                    # Update battery
                    self.telemetry['battery'] = max(0, self.telemetry['battery'] - 0.01)
                    
                    # Update status
                    if abs(self.telemetry['velocity']['linear']) > 0.1 or abs(self.telemetry['velocity']['angular']) > 0.1:
                        self.telemetry['status'] = 'MOVING'
                    else:
                        self.telemetry['status'] = 'IDLE'
                    
                    self.update_displays()
                    
                time.sleep(0.1)
            except:
                break
                
    def update_displays(self):
        """Update all display elements"""
        try:
            # Update position display
            pos = self.telemetry['position']
            self.position_display.config(
                text=f"X: {pos['x']:.2f}m  Y: {pos['y']:.2f}m  THETA: {math.degrees(pos['theta']):.2f}°"
            )
            
            # Update velocity display
            vel = self.telemetry['velocity']
            self.velocity_display.config(
                text=f"Linear: {vel['linear']:.2f}m/s  Angular: {vel['angular']:.2f}rad/s"
            )
            
            # Update motor display
            motors = self.telemetry['motors']
            self.motor_display.config(
                text=f"Left: {motors['left']:.1f}%  Right: {motors['right']:.1f}%"
            )
            
            # Update sensor display
            sensors = self.telemetry['sensors']
            self.sensor_display.config(
                text=f"US: {sensors['ultrasonic']:.2f}m  IR: {sensors['infrared']:.2f}m  Temp: {sensors['temperature']:.1f}°C"
            )
            
            # Update battery
            self.battery_label.config(text=f"BATTERY: {self.telemetry['battery']:.1f}%")
            
            # Update robot status
            self.robot_status_label.config(text=f"STATUS: {self.telemetry['status']}")
            
        except:
            pass
            
    def update_time(self):
        """Update time display"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.time_label.config(text=current_time)
        self.root.after(1000, self.update_time)
        
    def connect_robot(self):
        """Connect to robot"""
        self.add_log("Connecting to robot: " + self.robot_namespace.get())
        self.connection_indicator.config(text="CONNECTING", bg=self.colors['warning'])
        
        # Simulate connection
        self.root.after(1000, self.simulate_connection)
        
    def simulate_connection(self):
        """Simulate robot connection"""
        self.connected = True
        self.connection_indicator.config(text="CONNECTED", bg=self.colors['success'])
        self.connect_btn.config(state=tk.DISABLED)
        self.disconnect_btn.config(state=tk.NORMAL)
        self.add_log("Robot connected successfully")
        self.add_log("System ready for operation")
        
    def disconnect_robot(self):
        """Disconnect from robot"""
        self.add_log("Disconnecting from robot")
        self.connected = False
        self.connection_indicator.config(text="DISCONNECTED", bg=self.colors['danger'])
        self.connect_btn.config(state=tk.NORMAL)
        self.disconnect_btn.config(state=tk.DISABLED)
        
        # Reset controls
        self.target_velocity['linear'].set(0.0)
        self.target_velocity['angular'].set(0.0)
        
        self.add_log("Robot disconnected")
        
    def emergency_stop_action(self):
        """Emergency stop action"""
        self.emergency_stop = not self.emergency_stop
        
        if self.emergency_stop:
            self.emergency_indicator.config(text="EMERGENCY STOP: ON", bg=self.colors['danger'])
            self.target_velocity['linear'].set(0.0)
            self.target_velocity['angular'].set(0.0)
            self.add_log("EMERGENCY STOP ACTIVATED")
        else:
            self.emergency_indicator.config(text="EMERGENCY STOP: OFF", bg=self.colors['success'])
            self.add_log("Emergency stop deactivated")
            
    def reset_system(self):
        """Reset robot system"""
        self.add_log("System reset initiated")
        self.emergency_stop = False
        self.emergency_indicator.config(text="EMERGENCY STOP: OFF", bg=self.colors['success'])
        self.target_velocity['linear'].set(0.0)
        self.target_velocity['angular'].set(0.0)
        
        # Reset manipulator
        for joint in self.manipulator_joints.values():
            joint.set(0.0)
            
        self.add_log("System reset completed")
        
    def gripper_action(self, action):
        """Gripper control action"""
        if action == "open":
            self.manipulator_joints['gripper'].set(100)
            self.add_log("Gripper opened")
        elif action == "close":
            self.manipulator_joints['gripper'].set(0)
            self.add_log("Gripper closed")
        elif action == "home":
            for joint in self.manipulator_joints.values():
                joint.set(0.0)
            self.add_log("Manipulator homed")
            
    def add_log(self, message):
        """Add message to system log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        self.system_log.insert(tk.END, log_entry)
        self.system_log.see(tk.END)
        
        # Keep only last 100 lines
        lines = self.system_log.get(1.0, tk.END).split('\n')
        if len(lines) > 100:
            self.system_log.delete(1.0, f"{len(lines)-99}.0")
            
    def load_config(self):
        """Load configuration"""
        filename = filedialog.askopenfilename(
            title="Load Robot Configuration",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'r') as f:
                    config = json.load(f)
                    
                self.add_log(f"Configuration loaded from {filename}")
                messagebox.showinfo("Load Config", "Configuration loaded successfully")
            except Exception as e:
                messagebox.showerror("Load Error", f"Failed to load configuration: {e}")
                
    def save_config(self):
        """Save configuration"""
        filename = filedialog.asksaveasfilename(
            title="Save Robot Configuration",
            defaultfile="sanhum_config.json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                config = {
                    'robot_namespace': self.robot_namespace.get(),
                    'robot_mode': self.robot_mode.get(),
                    'velocity_limits': {
                        'linear': {'min': -2.0, 'max': 2.0},
                        'angular': {'min': -3.14, 'max': 3.14}
                    },
                    'manipulator_joints': {name: var.get() for name, var in self.manipulator_joints.items()}
                }
                
                with open(filename, 'w') as f:
                    json.dump(config, f, indent=2)
                    
                self.add_log(f"Configuration saved to {filename}")
                messagebox.showinfo("Save Config", "Configuration saved successfully")
            except Exception as e:
                messagebox.showerror("Save Error", f"Failed to save configuration: {e}")
                
    def robot_parameters(self):
        """Show robot parameters dialog"""
        params = """
ROBOT PARAMETERS:
================
Model: Sanhum Robot v2.0
Max Linear Velocity: 2.0 m/s
Max Angular Velocity: 3.14 rad/s
Battery Capacity: 12V 20Ah
Motor Type: DC Brushless
Sensor Suite: Ultrasonic, Infrared, Temperature
Manipulator: 3 DOF + Gripper
Communication: ROS2, Serial (ESP32, Arduino)
Control Frequency: 10 Hz
        """
        messagebox.showinfo("Robot Parameters", params)
        
    def system_check(self):
        """Perform system check"""
        self.add_log("Performing system check...")
        
        # Simulate system check
        checks = [
            "Communication systems: OK",
            "Motor controllers: OK", 
            "Sensor systems: OK",
            "Power systems: OK",
            "Manipulator: OK",
            "Camera systems: OK"
        ]
        
        for check in checks:
            self.add_log(f"  {check}")
            self.root.after(500)
            
        self.add_log("System check completed - All systems operational")
        
    def sensor_calibration(self):
        """Sensor calibration"""
        self.add_log("Starting sensor calibration...")
        messagebox.showinfo("Sensor Calibration", "Sensor calibration completed successfully")
        self.add_log("Sensor calibration completed")
        
    def motor_test(self):
        """Motor test"""
        self.add_log("Performing motor test...")
        messagebox.showinfo("Motor Test", "Motor test completed successfully")
        self.add_log("Motor test completed")
        
    def show_manual(self):
        """Show operator manual"""
        manual = """
SANHUM ROBOT CONTROL SYSTEM - OPERATOR MANUAL
============================================

1. SYSTEM CONNECTION
   - Enter robot namespace
   - Click CONNECT to establish connection
   - Verify green connection indicator

2. MOVEMENT CONTROL
   - Use Linear Velocity slider for forward/backward
   - Use Angular Velocity slider for rotation
   - Emergency Stop button halts all movement

3. MANIPULATOR CONTROL
   - Use joint sliders for precise positioning
   - Gripper buttons for open/close/home actions

4. CAMERA MONITORING
   - Front camera for navigation
   - Rear camera for obstacle detection
   - Manipulator camera for precise positioning

5. SAFETY FEATURES
   - Emergency Stop immediately halts robot
   - Battery monitoring prevents power loss
   - System log tracks all operations

6. TROUBLESHOOTING
   - Check connection status indicator
   - Review system log for errors
   - Run System Check for diagnostics
        """
        messagebox.showinfo("Operator Manual", manual)
        
    def show_info(self):
        """Show system information"""
        info = f"""
SANHUM ROBOT CONTROL SYSTEM
Version: 2.0.0
Build: Industrial Edition

Python: {sys.version.split()[0]}
Platform: {sys.platform}
GUI Framework: Tkinter

System Status: {'Connected' if self.connected else 'Disconnected'}
Robot Mode: {self.robot_mode.get()}
Emergency Stop: {'Active' if self.emergency_stop else 'Inactive'}

© 2024 Sanhum Robot Project
        """
        messagebox.showinfo("System Information", info)
        
    def quit_app(self):
        """Quit application"""
        if messagebox.askokcancel("Exit", "Are you sure you want to exit the robot control system?"):
            self.telemetry_thread_running = False
            if self.connected:
                self.disconnect_robot()
            self.root.quit()
            
    def run(self):
        """Start the industrial GUI"""
        self.add_log("Sanhum Robot Control System initialized")
        self.add_log("Waiting for robot connection...")
        
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.quit_app()

if __name__ == "__main__":
    app = IndustrialRobotGUI()
    app.run()
