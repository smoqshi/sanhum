#!/usr/bin/env python3
"""
Raspberry Pi 5 GPIO Interface for Sanhum Robot
Controls motor drivers, sensors, and hardware interfaces
"""

import time
import math
from typing import Dict, Tuple, Optional
import logging

# Try to import GPIO libraries
try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    print("Warning: RPi.GPIO not available - using simulation")
    GPIO_AVAILABLE = False

try:
    import pigpio
    PIGPIO_AVAILABLE = True
except ImportError:
    print("Warning: pigpio not available - using basic GPIO")
    PIGPIO_AVAILABLE = False

class GPIOMotorDriver:
    """GPIO Motor Driver for Tank Robot"""
    
    def __init__(self, config: Dict = None):
        self.logger = logging.getLogger(__name__)
        self.connected = False
        self.pi = None
        
        # Default motor pin configuration for RPi5
        self.config = config or {
            'left_motor': {
                'pwm_pin': 12,    # BCM pin 12
                'dir_pin1': 5,    # BCM pin 5
                'dir_pin2': 6,    # BCM pin 6
                'enable_pin': 13  # BCM pin 13
            },
            'right_motor': {
                'pwm_pin': 19,   # BCM pin 19
                'dir_pin1': 20,  # BCM pin 20
                'dir_pin2': 21,  # BCM pin 21
                'enable_pin': 26  # BCM pin 26
            },
            'pwm_frequency': 1000,  # 1kHz PWM frequency
            'max_duty_cycle': 100
        }
        
        self.motor_speeds = {'left': 0.0, 'right': 0.0}
        self.emergency_stop = False
        
        if GPIO_AVAILABLE:
            self._initialize_gpio()
        else:
            self.logger.warning("GPIO not available - running in simulation mode")
    
    def _initialize_gpio(self):
        """Initialize GPIO pins"""
        try:
            if PIGPIO_AVAILABLE:
                self.pi = pigpio.pi()
                if not self.pi.connected:
                    raise Exception("Failed to connect to pigpio daemon")
                self._setup_pigpio()
            else:
                GPIO.setmode(GPIO.BCM)
                GPIO.setwarnings(False)
                self._setup_rpi_gpio()
            
            self.connected = True
            self.logger.info("GPIO motor driver initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize GPIO: {e}")
            self.connected = False
    
    def _setup_pigpio(self):
        """Setup GPIO using pigpio for better PWM control"""
        # Left motor pins
        left = self.config['left_motor']
        self.pi.set_mode(left['pwm_pin'], pigpio.OUTPUT)
        self.pi.set_PWM_frequency(left['pwm_pin'], self.config['pwm_frequency'])
        self.pi.set_mode(left['dir_pin1'], pigpio.OUTPUT)
        self.pi.set_mode(left['dir_pin2'], pigpio.OUTPUT)
        self.pi.set_mode(left['enable_pin'], pigpio.OUTPUT)
        
        # Right motor pins
        right = self.config['right_motor']
        self.pi.set_mode(right['pwm_pin'], pigpio.OUTPUT)
        self.pi.set_PWM_frequency(right['pwm_pin'], self.config['pwm_frequency'])
        self.pi.set_mode(right['dir_pin1'], pigpio.OUTPUT)
        self.pi.set_mode(right['dir_pin2'], pigpio.OUTPUT)
        self.pi.set_mode(right['enable_pin'], pigpio.OUTPUT)
        
        # Enable motors
        self.pi.write(left['enable_pin'], 1)
        self.pi.write(right['enable_pin'], 1)
    
    def _setup_rpi_gpio(self):
        """Setup GPIO using RPi.GPIO"""
        # Left motor pins
        left = self.config['left_motor']
        GPIO.setup(left['pwm_pin'], GPIO.PWM)
        GPIO.setup(left['dir_pin1'], GPIO.OUT)
        GPIO.setup(left['dir_pin2'], GPIO.OUT)
        GPIO.setup(left['enable_pin'], GPIO.OUT)
        
        # Right motor pins
        right = self.config['right_motor']
        GPIO.setup(right['pwm_pin'], GPIO.PWM)
        GPIO.setup(right['dir_pin1'], GPIO.OUT)
        GPIO.setup(right['dir_pin2'], GPIO.OUT)
        GPIO.setup(right['enable_pin'], GPIO.OUT)
        
        # Start PWM
        self.left_pwm = GPIO.PWM(left['pwm_pin'], self.config['pwm_frequency'])
        self.right_pwm = GPIO.PWM(right['pwm_pin'], self.config['pwm_frequency'])
        self.left_pwm.start(0)
        self.right_pwm.start(0)
        
        # Enable motors
        GPIO.output(left['enable_pin'], GPIO.HIGH)
        GPIO.output(right['enable_pin'], GPIO.HIGH)
    
    def set_motor_speed(self, motor: str, speed: float):
        """Set motor speed (-1.0 to 1.0)"""
        if not self.connected or self.emergency_stop:
            return
        
        motor = motor.lower()
        if motor not in ['left', 'right']:
            self.logger.error(f"Invalid motor: {motor}")
            return
        
        # Clamp speed to valid range
        speed = max(-1.0, min(1.0, speed))
        self.motor_speeds[motor] = speed
        
        motor_config = self.config[f'{motor}_motor']
        
        if speed > 0:
            # Forward
            self._set_motor_direction(motor_config, 'forward')
            duty_cycle = abs(speed) * self.config['max_duty_cycle']
        elif speed < 0:
            # Reverse
            self._set_motor_direction(motor_config, 'reverse')
            duty_cycle = abs(speed) * self.config['max_duty_cycle']
        else:
            # Stop
            self._set_motor_direction(motor_config, 'stop')
            duty_cycle = 0
        
        self._set_motor_pwm(motor_config, duty_cycle)
    
    def _set_motor_direction(self, motor_config: Dict, direction: str):
        """Set motor direction pins"""
        if PIGPIO_AVAILABLE and self.pi:
            dir1, dir2 = motor_config['dir_pin1'], motor_config['dir_pin2']
            if direction == 'forward':
                self.pi.write(dir1, 1)
                self.pi.write(dir2, 0)
            elif direction == 'reverse':
                self.pi.write(dir1, 0)
                self.pi.write(dir2, 1)
            else:  # stop
                self.pi.write(dir1, 0)
                self.pi.write(dir2, 0)
        elif GPIO_AVAILABLE:
            dir1, dir2 = motor_config['dir_pin1'], motor_config['dir_pin2']
            if direction == 'forward':
                GPIO.output(dir1, GPIO.HIGH)
                GPIO.output(dir2, GPIO.LOW)
            elif direction == 'reverse':
                GPIO.output(dir1, GPIO.LOW)
                GPIO.output(dir2, GPIO.HIGH)
            else:  # stop
                GPIO.output(dir1, GPIO.LOW)
                GPIO.output(dir2, GPIO.LOW)
    
    def _set_motor_pwm(self, motor_config: Dict, duty_cycle: float):
        """Set motor PWM duty cycle"""
        if PIGPIO_AVAILABLE and self.pi:
            self.pi.set_PWM_dutycycle(motor_config['pwm_pin'], duty_cycle)
        elif GPIO_AVAILABLE:
            pwm = getattr(self, f'{motor_config["pwm_pin"]}_pwm', None)
            if pwm:
                pwm.ChangeDutyCycle(duty_cycle)
    
    def stop_all_motors(self):
        """Stop all motors immediately"""
        self.set_motor_speed('left', 0.0)
        self.set_motor_speed('right', 0.0)
        self.logger.info("All motors stopped")
    
    def emergency_stop_motors(self):
        """Emergency stop - disable motors"""
        self.emergency_stop = True
        self.stop_all_motors()
        
        # Disable motor drivers
        if self.connected:
            if PIGPIO_AVAILABLE and self.pi:
                self.pi.write(self.config['left_motor']['enable_pin'], 0)
                self.pi.write(self.config['right_motor']['enable_pin'], 0)
            elif GPIO_AVAILABLE:
                GPIO.output(self.config['left_motor']['enable_pin'], GPIO.LOW)
                GPIO.output(self.config['right_motor']['enable_pin'], GPIO.LOW)
        
        self.logger.warning("Emergency stop activated - motors disabled")
    
    def reset_emergency_stop(self):
        """Reset emergency stop and re-enable motors"""
        self.emergency_stop = False
        
        if self.connected:
            if PIGPIO_AVAILABLE and self.pi:
                self.pi.write(self.config['left_motor']['enable_pin'], 1)
                self.pi.write(self.config['right_motor']['enable_pin'], 1)
            elif GPIO_AVAILABLE:
                GPIO.output(self.config['left_motor']['enable_pin'], GPIO.HIGH)
                GPIO.output(self.config['right_motor']['enable_pin'], GPIO.HIGH)
        
        self.logger.info("Emergency stop reset - motors re-enabled")
    
    def get_motor_speeds(self) -> Dict[str, float]:
        """Get current motor speeds"""
        return self.motor_speeds.copy()
    
    def cleanup(self):
        """Clean up GPIO resources"""
        if self.connected:
            self.stop_all_motors()
            
            if PIGPIO_AVAILABLE and self.pi:
                self.pi.stop()
            elif GPIO_AVAILABLE:
                GPIO.cleanup()
            
            self.connected = False
            self.logger.info("GPIO motor driver cleaned up")

class HardwareInterface:
    """Main hardware interface for Sanhum Robot"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.motor_driver = GPIOMotorDriver()
        self.connected = self.motor_driver.connected
        
        # Initialize other hardware interfaces
        self.serial_interfaces = {}
        self.camera_interfaces = {}
        
    def set_motor_speed(self, motor: str, speed: float):
        """Set motor speed"""
        self.motor_driver.set_motor_speed(motor, speed)
    
    def stop_all_motors(self):
        """Stop all motors"""
        self.motor_driver.stop_all_motors()
    
    def emergency_stop(self):
        """Emergency stop all systems"""
        self.motor_driver.emergency_stop_motors()
    
    def reset_emergency_stop(self):
        """Reset emergency stop"""
        self.motor_driver.reset_emergency_stop()
    
    def get_status(self) -> Dict:
        """Get hardware status"""
        return {
            'connected': self.connected,
            'motor_driver': self.motor_driver.connected,
            'emergency_stop': self.motor_driver.emergency_stop,
            'motor_speeds': self.motor_driver.get_motor_speeds()
        }
    
    def cleanup(self):
        """Clean up all hardware interfaces"""
        self.motor_driver.cleanup()
        
        # Clean up serial interfaces
        for interface in self.serial_interfaces.values():
            try:
                interface.close()
            except:
                pass
        
        # Clean up camera interfaces
        for interface in self.camera_interfaces.values():
            try:
                interface.release()
            except:
                pass

# Test function
def test_gpio_interface():
    """Test GPIO motor interface"""
    print("Testing GPIO Motor Interface...")
    
    interface = HardwareInterface()
    print(f"Hardware connected: {interface.connected}")
    print(f"Status: {interface.get_status()}")
    
    if interface.connected:
        print("Testing motor control...")
        interface.set_motor_speed('left', 0.5)
        time.sleep(2)
        interface.set_motor_speed('left', 0.0)
        interface.set_motor_speed('right', 0.5)
        time.sleep(2)
        interface.set_motor_speed('right', 0.0)
        print("Motor test completed")
    
    interface.cleanup()
    print("GPIO interface test completed")

if __name__ == "__main__":
    test_gpio_interface()
