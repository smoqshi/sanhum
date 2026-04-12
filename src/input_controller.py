#!/usr/bin/env python3
"""
Input Controller for Sanhum Robot
Handles keyboard and gamepad input for real robot control
"""

import threading
import time
import math
from enum import Enum

try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False
    print("Warning: pygame not available, gamepad control disabled")

class ControlMode(Enum):
    KEYBOARD = "keyboard"
    GAMEPAD = "gamepad"

class InputController:
    def __init__(self, gui_callback=None):
        self.gui_callback = gui_callback
        self.running = False
        self.control_mode = ControlMode.KEYBOARD
        
        # Control state
        self.linear_velocity = 0.0
        self.angular_velocity = 0.0
        self.max_linear_vel = 2.0
        self.max_angular_vel = 3.14
        
        # Keyboard state
        self.keys_pressed = set()
        
        # Gamepad state
        self.gamepad_connected = False
        self.gamepad = None
        self.gamepad_deadzone = 0.1
        
        # Control mappings
        self.key_mappings = {
            # Movement
            'w': 'forward',
            's': 'backward', 
            'a': 'left',
            'd': 'right',
            'space': 'stop',
            
            # Manipulator
            'q': 'joint1_ccw',
            'e': 'joint1_cw',
            'r': 'joint2_up',
            'f': 'joint2_down',
            't': 'joint3_up',
            'g': 'joint3_down',
            'z': 'gripper_open',
            'x': 'gripper_close',
            'c': 'gripper_home',
            
            # Emergency
            'escape': 'emergency_stop',
            'enter': 'reset'
        }
        
        # Initialize pygame if available
        if PYGAME_AVAILABLE:
            pygame.init()
            pygame.joystick.init()
            self._init_gamepad()
            
    def _init_gamepad(self):
        """Initialize gamepad controller"""
        if pygame.joystick.get_count() > 0:
            self.gamepad = pygame.joystick.Joystick(0)
            self.gamepad.init()
            self.gamepad_connected = True
            self.control_mode = ControlMode.GAMEPAD
            print(f"Gamepad connected: {self.gamepad.get_name()}")
        else:
            self.gamepad_connected = False
            print("No gamepad detected")
            
    def start(self):
        """Start input controller"""
        if self.running:
            return
            
        self.running = True
        self.input_thread = threading.Thread(target=self._input_loop, daemon=True)
        self.input_thread.start()
        
    def stop(self):
        """Stop input controller"""
        self.running = False
        
    def _input_loop(self):
        """Main input processing loop"""
        while self.running:
            try:
                if PYGAME_AVAILABLE:
                    pygame.event.pump()
                    
                    if self.gamepad_connected:
                        self._process_gamepad()
                    else:
                        self._process_keyboard()
                else:
                    self._process_keyboard_simple()
                    
                time.sleep(0.016)  # ~60 Hz
                
            except Exception as e:
                print(f"Input controller error: {e}")
                time.sleep(0.1)
                
    def _process_keyboard(self):
        """Process pygame keyboard input"""
        keys = pygame.key.get_pressed()
        
        # Movement controls
        linear = 0.0
        angular = 0.0
        
        if keys[pygame.K_w]:
            linear = self.max_linear_vel
        elif keys[pygame.K_s]:
            linear = -self.max_linear_vel
            
        if keys[pygame.K_a]:
            angular = self.max_angular_vel
        elif keys[pygame.K_d]:
            angular = -self.max_angular_vel
            
        # Emergency stop
        if keys[pygame.K_ESCAPE]:
            self._emergency_stop()
            
        # Update velocities
        self.linear_velocity = linear
        self.angular_velocity = angular
        
        # Send to GUI
        if self.gui_callback:
            self.gui_callback('velocity', {
                'linear': self.linear_velocity,
                'angular': self.angular_velocity
            })
            
    def _process_keyboard_simple(self):
        """Process simple keyboard input without pygame"""
        # This would need to be implemented with a different library
        # For now, using placeholder
        pass
        
    def _process_gamepad(self):
        """Process gamepad input"""
        if not self.gamepad:
            return
            
        # Left stick for movement
        left_x = self.gamepad.get_axis(0)
        left_y = self.gamepad.get_axis(1)
        
        # Right stick for camera/manipulator
        right_x = self.gamepad.get_axis(2)
        right_y = self.gamepad.get_axis(3)
        
        # Apply deadzone
        left_x = self._apply_deadzone(left_x)
        left_y = self._apply_deadzone(left_y)
        right_x = self._apply_deadzone(right_x)
        right_y = self._apply_deadzone(right_y)
        
        # Convert to robot velocities
        # Invert Y axis (gamepad Y is inverted)
        linear = -left_y * self.max_linear_vel
        angular = -left_x * self.max_angular_vel
        
        # Emergency stop (Start button)
        if self.gamepad.get_button(7):  # Start button
            self._emergency_stop()
            
        # Update velocities
        self.linear_velocity = linear
        self.angular_velocity = angular
        
        # Manipulator controls with right stick
        if abs(right_x) > 0.1 or abs(right_y) > 0.1:
            if self.gui_callback:
                self.gui_callback('manipulator_stick', {
                    'x': right_x,
                    'y': right_y
                })
                
        # Gripper controls
        if self.gamepad.get_button(0):  # A button
            if self.gui_callback:
                self.gui_callback('gripper', 'close')
        elif self.gamepad.get_button(1):  # B button
            if self.gui_callback:
                self.gui_callback('gripper', 'open')
                
        # Send velocity to GUI
        if self.gui_callback:
            self.gui_callback('velocity', {
                'linear': self.linear_velocity,
                'angular': self.angular_velocity
            })
            
    def _apply_deadzone(self, value):
        """Apply deadzone to analog input"""
        if abs(value) < self.gamepad_deadzone:
            return 0.0
        return value
        
    def _emergency_stop(self):
        """Emergency stop action"""
        self.linear_velocity = 0.0
        self.angular_velocity = 0.0
        
        if self.gui_callback:
            self.gui_callback('emergency_stop', True)
            
    def get_control_status(self):
        """Get current control status"""
        return {
            'mode': self.control_mode.value,
            'gamepad_connected': self.gamepad_connected,
            'linear_velocity': self.linear_velocity,
            'angular_velocity': self.angular_velocity
        }
        
    def set_velocity_limits(self, linear_max, angular_max):
        """Set velocity limits"""
        self.max_linear_vel = linear_max
        self.max_angular_vel = angular_max
