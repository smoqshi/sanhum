#!/usr/bin/env python3
"""
Simple Sanhum Robot GUI
Placeholder for testing installation
"""

import sys
import tkinter as tk
from tkinter import messagebox
import os
from pathlib import Path

class SanhumGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Sanhum Robot Control")
        self.root.geometry("800x600")
        
        # Main frame
        main_frame = tk.Frame(self.root, padx=10, pady=10)
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        title_label = tk.Label(main_frame, text="Sanhum Robot Control Station", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=10)
        
        # Connection section
        tk.Label(main_frame, text="Robot Connection:", font=("Arial", 12, "bold")).grid(
            row=1, column=0, sticky=tk.W, pady=5)
        
        self.robot_namespace = tk.StringVar(value="simulation")
        tk.Entry(main_frame, textvariable=self.robot_namespace, width=30).grid(
            row=1, column=1, pady=5)
        
        # Control section
        tk.Label(main_frame, text="Controls:", font=("Arial", 12, "bold")).grid(
            row=2, column=0, sticky=tk.W, pady=5)
        
        control_frame = tk.Frame(main_frame)
        control_frame.grid(row=2, column=1, pady=5)
        
        # Movement controls
        tk.Label(control_frame, text="Forward: W").grid(row=0, column=1)
        tk.Label(control_frame, text="Backward: S").grid(row=1, column=1)
        tk.Label(control_frame, text="Left: A").grid(row=2, column=0)
        tk.Label(control_frame, text="Right: D").grid(row=2, column=2)
        tk.Label(control_frame, text="Stop: Space").grid(row=3, column=1)
        
        # Status section
        tk.Label(main_frame, text="Status:", font=("Arial", 12, "bold")).grid(
            row=3, column=0, sticky=tk.W, pady=5)
        
        self.status_text = tk.Text(main_frame, width=40, height=8, state="disabled")
        self.status_text.grid(row=3, column=1, pady=5)
        
        # Buttons
        button_frame = tk.Frame(main_frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=10)
        
        tk.Button(button_frame, text="Connect", command=self.connect_robot).grid(
            row=0, column=0, padx=5)
        tk.Button(button_frame, text="Disconnect", command=self.disconnect_robot).grid(
            row=0, column=1, padx=5)
        tk.Button(button_frame, text="Check Dependencies", command=self.check_deps).grid(
            row=1, column=0, padx=5, pady=5)
        tk.Button(button_frame, text="Exit", command=self.root.quit).grid(
            row=1, column=1, padx=5, pady=5)
        
        self.update_status("GUI Ready. Connect to robot to begin.")
        
    def update_status(self, message):
        self.status_text.config(state="normal")
        self.status_text.delete(1.0, tk.END)
        self.status_text.insert(tk.END, f"{message}\n")
        self.status_text.config(state="disabled")
        self.status_text.see(tk.END)
        
    def connect_robot(self):
        namespace = self.robot_namespace.get()
        self.update_status(f"Connecting to robot: {namespace}")
        
        if namespace == "simulation":
            self.update_status("Connected to simulation mode")
        else:
            self.update_status(f"Attempting to connect to robot: {namespace}")
            # Here you would add actual ROS2 connection code
            
    def disconnect_robot(self):
        self.update_status("Disconnected from robot")
        
    def check_deps(self):
        try:
            import subprocess
            result = subprocess.run([sys.executable, "scripts/check_dependencies.py"], 
                                  capture_output=True, text=True, cwd=Path(__file__).parent.parent)
            self.update_status("Dependency Check Results:\n" + result.stdout)
        except Exception as e:
            self.update_status(f"Failed to check dependencies: {e}")
        
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = SanhumGUI()
    app.run()
