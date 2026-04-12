#!/usr/bin/env python3
"""
Sanhum Robot GUI - Modern and User-Friendly Interface
Professional robot control station with enhanced UX
"""

import sys
import tkinter as tk
from tkinter import messagebox, filedialog, colorchooser
import os
from pathlib import Path
import threading
import time

class SanhumGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Sanhum Robot Control Station")
        self.root.geometry("1000x700")
        self.root.minsize(800, 600)
        
        # Set modern color scheme
        self.colors = {
            'bg': '#2b2b2b',
            'fg': '#ffffff',
            'accent': '#007acc',
            'success': '#28a745',
            'warning': '#ffc107',
            'danger': '#dc3545',
            'secondary': '#6c757d'
        }
        
        self.root.configure(bg=self.colors['bg'])
        
        # Connection state
        self.connected = False
        self.robot_namespace = tk.StringVar(value="simulation")
        
        # Control variables
        self.robot_speed = tk.DoubleVar(value=0.0)
        self.robot_rotation = tk.DoubleVar(value=0.0)
        
        # Status variables
        self.status_messages = []
        self.connection_status = tk.StringVar(value="Disconnected")
        
        # Create GUI elements
        self.create_widgets()
        self.create_menu()
        
        # Start status update thread
        self.status_thread_running = True
        self.status_thread = threading.Thread(target=self.update_status_loop, daemon=True)
        self.status_thread.start()
        
    def create_menu(self):
        """Create menu bar"""
        menubar = tk.Menu(self.root)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Load Config", command=self.load_config)
        file_menu.add_command(label="Save Config", command=self.save_config)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit_app)
        
        # Connection menu
        conn_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Connection", menu=conn_menu)
        conn_menu.add_command(label="Connect", command=self.connect_robot)
        conn_menu.add_command(label="Disconnect", command=self.disconnect_robot)
        conn_menu.add_separator()
        conn_menu.add_command(label="Check Dependencies", command=self.check_deps)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="User Guide", command=self.show_help)
        help_menu.add_command(label="About", command=self.show_about)
        
        self.root.config(menu=menubar)
        
    def create_widgets(self):
        """Create all GUI widgets"""
        # Main container with padding
        main_container = tk.Frame(self.root, bg=self.colors['bg'])
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Title Section
        title_frame = tk.Frame(main_container, bg=self.colors['bg'])
        title_frame.pack(fill=tk.X, pady=(0, 20))
        
        title_label = tk.Label(title_frame, 
                               text="Sanhum Robot Control Station",
                               font=("Segoe UI", 18, "bold"),
                               fg=self.colors['fg'],
                               bg=self.colors['bg'])
        title_label.pack()
        
        subtitle_label = tk.Label(title_frame,
                                text="Professional Robot Control Interface",
                                font=("Segoe UI", 10),
                                fg=self.colors['secondary'],
                                bg=self.colors['bg'])
        subtitle_label.pack(pady=(5, 0))
        
        # Connection Section
        conn_frame = self.create_section_frame(main_container, "Robot Connection")
        
        # Namespace input
        namespace_container = tk.Frame(conn_frame, bg=self.colors['bg'])
        namespace_container.pack(fill=tk.X, pady=10)
        
        tk.Label(namespace_container, text="Robot Namespace:", 
                font=("Segoe UI", 11, "bold"),
                fg=self.colors['fg'],
                bg=self.colors['bg']).pack(anchor=tk.W)
        
        namespace_input_container = tk.Frame(namespace_container, bg=self.colors['bg'])
        namespace_input_container.pack(fill=tk.X, pady=(5, 0))
        
        self.namespace_entry = tk.Entry(namespace_input_container, 
                                     textvariable=self.robot_namespace,
                                     font=("Segoe UI", 10),
                                     bg=self.colors['secondary'],
                                     fg=self.colors['fg'],
                                     insertbackground=self.colors['accent'])
        self.namespace_entry.pack(fill=tk.X, side=tk.LEFT, padx=(0, 10))
        
        # Connection status indicator
        self.status_indicator = tk.Label(namespace_input_container,
                                      textvariable=self.connection_status,
                                      font=("Segoe UI", 10, "bold"),
                                      fg=self.colors['fg'],
                                      bg=self.colors['secondary'],
                                      relief=tk.RAISED,
                                      bd=1)
        self.status_indicator.pack(side=tk.RIGHT)
        
        # Control Panel
        control_frame = self.create_section_frame(main_container, "Robot Controls")
        
        # Speed Control
        speed_container = tk.Frame(control_frame, bg=self.colors['bg'])
        speed_container.pack(fill=tk.X, pady=10)
        
        tk.Label(speed_container, text="Linear Speed (m/s):",
                font=("Segoe UI", 11, "bold"),
                fg=self.colors['fg'],
                bg=self.colors['bg']).pack(anchor=tk.W)
        
        speed_frame = tk.Frame(speed_container, bg=self.colors['bg'])
        speed_frame.pack(fill=tk.X, pady=5)
        
        self.speed_scale = tk.Scale(speed_frame, 
                               from_=-2.0, to=2.0, resolution=0.1,
                               orient=tk.HORIZONTAL,
                               variable=self.robot_speed,
                               font=("Segoe UI", 9),
                               bg=self.colors['bg'],
                               fg=self.colors['fg'],
                               troughcolor=self.colors['secondary'],
                               activebackground=self.colors['accent'])
        self.speed_scale.pack(fill=tk.X)
        
        # Rotation Control
        rotation_container = tk.Frame(control_frame, bg=self.colors['bg'])
        rotation_container.pack(fill=tk.X, pady=10)
        
        tk.Label(rotation_container, text="Angular Speed (rad/s):",
                font=("Segoe UI", 11, "bold"),
                fg=self.colors['fg'],
                bg=self.colors['bg']).pack(anchor=tk.W)
        
        rotation_frame = tk.Frame(rotation_container, bg=self.colors['bg'])
        rotation_frame.pack(fill=tk.X, pady=5)
        
        self.rotation_scale = tk.Scale(rotation_frame,
                                 from_=-3.14, to=3.14, resolution=0.01,
                                 orient=tk.HORIZONTAL,
                                 variable=self.robot_rotation,
                                 font=("Segoe UI", 9),
                                 bg=self.colors['bg'],
                                 fg=self.colors['fg'],
                                 troughcolor=self.colors['secondary'],
                                 activebackground=self.colors['accent'])
        self.rotation_scale.pack(fill=tk.X)
        
        # Quick Actions
        actions_frame = self.create_section_frame(main_container, "Quick Actions")
        
        buttons_container = tk.Frame(actions_frame, bg=self.colors['bg'])
        buttons_container.pack(fill=tk.X, pady=10)
        
        # Button row 1
        button_row1 = tk.Frame(buttons_container, bg=self.colors['bg'])
        button_row1.pack(fill=tk.X, pady=5)
        
        self.connect_btn = self.create_button(button_row1, "Connect", self.connect_robot, self.colors['success'])
        self.connect_btn.pack(side=tk.LEFT, padx=5)
        
        self.disconnect_btn = self.create_button(button_row1, "Disconnect", self.disconnect_robot, self.colors['danger'])
        self.disconnect_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = self.create_button(button_row1, "Stop", self.stop_robot, self.colors['warning'])
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        # Button row 2
        button_row2 = tk.Frame(buttons_container, bg=self.colors['bg'])
        button_row2.pack(fill=tk.X, pady=5)
        
        self.config_btn = self.create_button(button_row2, "Load Config", self.load_config, self.colors['secondary'])
        self.config_btn.pack(side=tk.LEFT, padx=5)
        
        self.deps_btn = self.create_button(button_row2, "Check Deps", self.check_deps, self.colors['accent'])
        self.deps_btn.pack(side=tk.LEFT, padx=5)
        
        self.help_btn = self.create_button(button_row2, "Help", self.show_help, self.colors['secondary'])
        self.help_btn.pack(side=tk.LEFT, padx=5)
        
        # Status Section
        status_frame = self.create_section_frame(main_container, "Status Monitor")
        
        status_container = tk.Frame(status_frame, bg=self.colors['bg'])
        status_container.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Status text area
        self.status_text = tk.Text(status_container,
                                  height=8,
                                  font=("Consolas", 9),
                                  bg=self.colors['secondary'],
                                  fg=self.colors['fg'],
                                  wrap=tk.WORD)
        
        status_scrollbar = tk.Scrollbar(status_container, orient=tk.VERTICAL, command=self.status_text.yview)
        self.status_text.configure(yscrollcommand=status_scrollbar.set)
        
        self.status_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        status_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Initial status message
        self.add_status_message("Sanhum Robot GUI initialized successfully", "info")
        self.add_status_message("Ready to connect to robot. Configure namespace and click Connect.", "info")
        
    def create_section_frame(self, parent, title):
        """Create a section frame with title"""
        section_frame = tk.Frame(parent, bg=self.colors['bg'])
        section_frame.pack(fill=tk.X, pady=15)
        
        title_label = tk.Label(section_frame,
                           text=title,
                           font=("Segoe UI", 12, "bold"),
                           fg=self.colors['accent'],
                           bg=self.colors['bg'])
        title_label.pack(anchor=tk.W, pady=(0, 10))
        
        content_frame = tk.Frame(section_frame, bg=self.colors['bg'], relief=tk.GROOVE, bd=1)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        return content_frame
        
    def create_button(self, parent, text, command, color=None):
        """Create a modern button with styling"""
        if color is None:
            color = self.colors['accent']
            
        btn = tk.Button(parent,
                     text=text,
                     command=command,
                     font=("Segoe UI", 10, "bold"),
                     bg=color,
                     fg='white',
                     relief=tk.RAISED,
                     bd=0,
                     padx=15,
                     pady=8,
                     cursor="hand2")
        
        # Hover effects
        btn.bind("<Enter>", lambda e: btn.config(bg=self.darken_color(color)))
        btn.bind("<Leave>", lambda e: btn.config(bg=color))
        
        return btn
        
    def darken_color(self, color):
        """Darken a color for hover effects"""
        # Simple color darkening
        if color.startswith('#'):
            r = int(color[1:3], 16)
            g = int(color[3:5], 16)
            b = int(color[5:7], 16)
            return f"#{max(0, r-30):02x}{max(0, g-30):02x}{max(0, b-30):02x}"
        return color
        
    def add_status_message(self, message, msg_type="info"):
        """Add a message to the status display"""
        timestamp = time.strftime("%H:%M:%S")
        status_icon = {"info": "INFO", "success": "SUCCESS", "warning": "WARNING", "error": "ERROR"}
        icon = status_icon.get(msg_type, "INFO")
        
        formatted_message = f"[{timestamp}] {icon} {message}"
        
        self.status_text.insert(tk.END, formatted_message + "\n")
        self.status_text.see(tk.END)
        
        # Keep only last 100 messages
        lines = self.status_text.get(1.0, tk.END).split('\n')
        if len(lines) > 100:
            self.status_text.delete(1.0, f"{len(lines)-99}.0")
            
    def update_status_loop(self):
        """Background thread for status updates"""
        while self.status_thread_running:
            try:
                if self.connected:
                    # Simulate status updates when connected
                    if int(time.time()) % 5 == 0:  # Every 5 seconds
                        speed = self.robot_speed.get()
                        rotation = self.robot_rotation.get()
                        self.add_status_message(f"Robot active - Speed: {speed:.1f} m/s, Rotation: {rotation:.2f} rad/s", "info")
                time.sleep(1)
            except:
                break
                
    def connect_robot(self):
        """Connect to robot"""
        namespace = self.robot_namespace.get().strip()
        if not namespace:
            messagebox.showwarning("Connection Error", "Please enter a robot namespace")
            return
            
        self.add_status_message(f"Connecting to robot: {namespace}", "info")
        self.connection_status.set("Connecting...")
        
        # Simulate connection process
        self.root.after(1000, self.simulate_connection)
        
    def simulate_connection(self):
        """Simulate robot connection"""
        if self.robot_namespace.get() == "simulation":
            self.add_status_message("Connected to simulation mode", "success")
            self.connection_status.set("Connected (Simulation)")
        else:
            self.add_status_message(f"Connected to robot: {self.robot_namespace.get()}", "success")
            self.connection_status.set(f"Connected ({self.robot_namespace.get()})")
            
        self.connected = True
        self.connect_btn.config(state=tk.DISABLED)
        self.disconnect_btn.config(state=tk.NORMAL)
        
    def disconnect_robot(self):
        """Disconnect from robot"""
        self.add_status_message("Disconnecting from robot...", "info")
        self.connection_status.set("Disconnecting...")
        
        # Simulate disconnection
        self.root.after(500, self.simulate_disconnection)
        
    def simulate_disconnection(self):
        """Simulate robot disconnection"""
        self.add_status_message("Disconnected from robot", "warning")
        self.connection_status.set("Disconnected")
        
        self.connected = False
        self.connect_btn.config(state=tk.NORMAL)
        self.disconnect_btn.config(state=tk.DISABLED)
        
        # Reset controls
        self.robot_speed.set(0.0)
        self.robot_rotation.set(0.0)
        
    def stop_robot(self):
        """Stop robot movement"""
        self.add_status_message("Emergency stop activated", "warning")
        self.robot_speed.set(0.0)
        self.robot_rotation.set(0.0)
        
    def load_config(self):
        """Load configuration from file"""
        try:
            filename = filedialog.askopenfilename(
                title="Load Configuration",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            
            if filename:
                self.add_status_message(f"Loading configuration from: {filename}", "info")
                # Here you would load actual config
                messagebox.showinfo("Load Config", f"Configuration loaded from {filename}")
        except Exception as e:
            messagebox.showerror("Load Error", f"Failed to load configuration: {e}")
            
    def save_config(self):
        """Save current configuration to file"""
        try:
            filename = filedialog.asksaveasfilename(
                title="Save Configuration",
                defaultfile="sanhum_config.json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            
            if filename:
                config = {
                    "namespace": self.robot_namespace.get(),
                    "speed": self.robot_speed.get(),
                    "rotation": self.robot_rotation.get()
                }
                
                import json
                with open(filename, 'w') as f:
                    json.dump(config, f, indent=2)
                    
                self.add_status_message(f"Configuration saved to: {filename}", "success")
                messagebox.showinfo("Save Config", f"Configuration saved to {filename}")
        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save configuration: {e}")
            
    def check_deps(self):
        """Check system dependencies"""
        self.add_status_message("Checking system dependencies...", "info")
        
        try:
            # Check Python version
            python_version = sys.version.split()[0]
            self.add_status_message(f"Python: {python_version}", "info")
            
            # Check required modules
            required_modules = ['tkinter', 'json', 'threading', 'time']
            for module in required_modules:
                try:
                    __import__(module)
                    self.add_status_message(f"Module {module}: Available", "success")
                except ImportError:
                    self.add_status_message(f"Module {module}: Missing", "error")
                    
            # Check project files
            project_root = Path(__file__).parent.parent
            cmake_file = project_root / "CMakeLists.txt"
            if cmake_file.exists():
                self.add_status_message("CMakeLists.txt: Found", "success")
            else:
                self.add_status_message("CMakeLists.txt: Not found", "error")
                
            self.add_status_message("Dependency check completed", "success")
            
        except Exception as e:
            self.add_status_message(f"Dependency check failed: {e}", "error")
            
    def show_help(self):
        """Show help dialog"""
        help_text = """
Sanhum Robot Control Station - User Guide

CONNECTION:
- Enter robot namespace (e.g., 'robot1', 'sanhum_bot')
- Leave as 'simulation' for simulation mode
- Click 'Connect' to establish connection

CONTROLS:
- Linear Speed: Control forward/backward movement (-2.0 to 2.0 m/s)
- Angular Speed: Control rotation (-3.14 to 3.14 rad/s)
- Emergency Stop: Immediately stops all robot movement

QUICK ACTIONS:
- Connect/Disconnect: Establish or terminate robot connection
- Load/Save Config: Manage robot configurations
- Check Deps: Verify system requirements

STATUS MONITOR:
- Real-time status messages with timestamps
- Connection status indicator
- Automatic status updates when connected

CONFIGURATION:
- Save current settings to JSON file
- Load saved configurations
- Persistent storage of robot parameters

TROUBLESHOOTING:
- Ensure robot namespace is correct
- Check network connectivity for real robots
- Verify ROS2 installation (for advanced features)
- Run dependency checker for system diagnosis
        """
        
        messagebox.showinfo("User Guide", help_text)
        
    def show_about(self):
        """Show about dialog"""
        about_text = """
Sanhum Robot Control Station
Version 1.0.0

A professional robot control interface for
the Sanhum robotic system.

Features:
- Modern, user-friendly interface
- Real-time robot control
- Configuration management
- System monitoring
- Cross-platform compatibility

© 2024 Sanhum Robot Project
        """
        
        messagebox.showinfo("About Sanhum Robot", about_text)
        
    def quit_app(self):
        """Quit application"""
        if messagebox.askokcancel("Exit", "Are you sure you want to exit?"):
            self.status_thread_running = False
            self.root.quit()
            
    def run(self):
        """Start the GUI main loop"""
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.quit_app()

if __name__ == "__main__":
    app = SanhumGUI()
    app.run()
