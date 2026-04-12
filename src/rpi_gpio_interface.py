#!/usr/bin/env python3
"""
Raspberry Pi GPIO Interface for Sanhum Robot
Direct hardware control for motors and sensors
"""

import time
import math
from enum import Enum
from typing import Dict, Tuple, Optional

try:
    import RPi.GPIO as GPIO
    RPI_AVAILABLE = True
except ImportError:
    RPI_AVAILABLE = False
    print("Warning: RPi.GPIO not available, using simulation mode")

class MotorState(Enum):
    FORWARD = 1
    BACKWARD = -1
    STOP = 0

class RPiGPIOInterface:
    """Raspberry Pi GPIO interface for motor control and sensor reading"""
    
    def __init__(self, config_file: str = "raspberry_pi_config.yaml"):
        self.initialized = False
        self.motor_pins = {}
        self.sensor_pins = {}
        self.motor_states = {}
        self.pwm_instances = {}
        
        # Load configuration
        self.load_config(config_file)
        
        # Initialize GPIO if available
        if RPI_AVAILABLE:
            self.initialize_gpio()
        else:
            print("Running in GPIO simulation mode")
            
    def load_config(self, config_file: str):
        """Load GPIO configuration from YAML file"""
        try:
            import yaml
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)
                
            # Motor pins configuration
            motor_config = config.get('raspberry_pi', {}).get('motor_pins', {})
            self.motor_pins = {
                'left_motor_1': motor_config.get('left_motor_1', 17),
                'left_motor_2': motor_config.get('left_motor_2', 27),
                'right_motor_1': motor_config.get('right_motor_1', 22),
                'right_motor_2': motor_config.get('right_motor_2', 23),
                'left_pwm': motor_config.get('left_pwm', 12),
                'right_pwm': motor_config.get('right_pwm', 13)
            }
            
            # Sensor pins configuration
            sensor_config = config.get('raspberry_pi', {}).get('sensor_pins', {})
            self.sensor_pins = {
                'ultrasonic_front_trig': sensor_config.get('ultrasonic_front_trig', 24),
                'ultrasonic_front_echo': sensor_config.get('ultrasonic_front_echo', 25),
                'ultrasonic_rear_trig': sensor_config.get('ultrasonic_rear_trig', 5),
                'ultrasonic_rear_echo': sensor_config.get('ultrasonic_rear_echo', 6),
                'infrared_left': sensor_config.get('infrared_left', 16),
                'infrared_right': sensor_config.get('infrared_right', 26),
                'battery_adc': sensor_config.get('battery_adc', 0)  # SPI ADC channel
            }
            
            print(f"GPIO configuration loaded from {config_file}")
            
        except FileNotFoundError:
            print(f"Config file {config_file} not found, using defaults")
            self.set_default_config()
        except Exception as e:
            print(f"Error loading config: {e}")
            self.set_default_config()
            
    def set_default_config(self):
        """Set default GPIO pin configuration"""
        self.motor_pins = {
            'left_motor_1': 17,
            'left_motor_2': 27,
            'right_motor_1': 22,
            'right_motor_2': 23,
            'left_pwm': 12,
            'right_pwm': 13
        }
        
        self.sensor_pins = {
            'ultrasonic_front_trig': 24,
            'ultrasonic_front_echo': 25,
            'ultrasonic_rear_trig': 5,
            'ultrasonic_rear_echo': 6,
            'infrared_left': 16,
            'infrared_right': 26,
            'battery_adc': 0
        }
        
    def initialize_gpio(self):
        """Initialize GPIO pins"""
        if not RPI_AVAILABLE:
            return False
            
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            
            # Setup motor pins
            for pin_name, pin_num in self.motor_pins.items():
                if 'pwm' in pin_name:
                    GPIO.setup(pin_num, GPIO.OUT)
                    self.pwm_instances[pin_name] = GPIO.PWM(pin_num, 1000)  # 1kHz PWM
                    self.pwm_instances[pin_name].start(0)
                else:
                    GPIO.setup(pin_num, GPIO.OUT)
                    GPIO.output(pin_num, GPIO.LOW)
                    
            # Setup sensor pins
            for pin_name, pin_num in self.sensor_pins.items():
                if 'trig' in pin_name:
                    GPIO.setup(pin_num, GPIO.OUT)
                    GPIO.output(pin_num, GPIO.LOW)
                elif 'echo' in pin_name:
                    GPIO.setup(pin_num, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
                elif 'infrared' in pin_name:
                    GPIO.setup(pin_num, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
                    
            self.initialized = True
            print("GPIO initialized successfully")
            return True
            
        except Exception as e:
            print(f"GPIO initialization failed: {e}")
            return False
            
    def set_motor_speed(self, motor: str, speed: float):
        """Set motor speed (-1.0 to 1.0)"""
        if not self.initialized and not RPI_AVAILABLE:
            return  # Simulation mode
            
        try:
            speed = max(-1.0, min(1.0, speed))  # Clamp to [-1, 1]
            
            if motor == 'left':
                pin1 = self.motor_pins['left_motor_1']
                pin2 = self.motor_pins['left_motor_2']
                pwm_pin = 'left_pwm'
            elif motor == 'right':
                pin1 = self.motor_pins['right_motor_1']
                pin2 = self.motor_pins['right_motor_2']
                pwm_pin = 'right_pwm'
            else:
                print(f"Unknown motor: {motor}")
                return
                
            # Determine motor state
            if abs(speed) < 0.05:  # Dead zone
                state = MotorState.STOP
            elif speed > 0:
                state = MotorState.FORWARD
            else:
                state = MotorState.BACKWARD
                
            # Set motor direction
            if RPI_AVAILABLE:
                if state == MotorState.FORWARD:
                    GPIO.output(pin1, GPIO.HIGH)
                    GPIO.output(pin2, GPIO.LOW)
                elif state == MotorState.BACKWARD:
                    GPIO.output(pin1, GPIO.LOW)
                    GPIO.output(pin2, GPIO.HIGH)
                else:  # STOP
                    GPIO.output(pin1, GPIO.LOW)
                    GPIO.output(pin2, GPIO.LOW)
                    
                # Set PWM speed
                pwm_value = int(abs(speed) * 100)  # Convert to percentage
                self.pwm_instances[pwm_pin].ChangeDutyCycle(pwm_value)
                
            self.motor_states[motor] = {'state': state, 'speed': speed}
            
        except Exception as e:
            print(f"Error setting motor speed: {e}")
            
    def stop_all_motors(self):
        """Stop all motors"""
        self.set_motor_speed('left', 0.0)
        self.set_motor_speed('right', 0.0)
        
    def read_ultrasonic(self, sensor: str) -> float:
        """Read ultrasonic sensor distance in meters"""
        if not self.initialized and not RPI_AVAILABLE:
            return 2.5  # Simulation value
            
        try:
            if sensor == 'front':
                trig_pin = self.sensor_pins['ultrasonic_front_trig']
                echo_pin = self.sensor_pins['ultrasonic_front_echo']
            elif sensor == 'rear':
                trig_pin = self.sensor_pins['ultrasonic_rear_trig']
                echo_pin = self.sensor_pins['ultrasonic_rear_echo']
            else:
                print(f"Unknown ultrasonic sensor: {sensor}")
                return 0.0
                
            if RPI_AVAILABLE:
                # Send trigger pulse
                GPIO.output(trig_pin, GPIO.HIGH)
                time.sleep(0.00001)  # 10 microseconds
                GPIO.output(trig_pin, GPIO.LOW)
                
                # Wait for echo start
                start_time = time.time()
                while GPIO.input(echo_pin) == GPIO.LOW:
                    start_time = time.time()
                    
                # Wait for echo end
                end_time = time.time()
                while GPIO.input(echo_pin) == GPIO.HIGH:
                    end_time = time.time()
                    
                # Calculate distance
                duration = end_time - start_time
                distance = (duration * 34300) / 2  # Speed of sound in cm/s
                
                return distance / 100.0  # Convert to meters
            else:
                return 2.5  # Simulation value
                
        except Exception as e:
            print(f"Error reading ultrasonic sensor {sensor}: {e}")
            return 0.0
            
    def read_infrared(self, sensor: str) -> float:
        """Read infrared sensor distance in meters"""
        if not self.initialized and not RPI_AVAILABLE:
            return 0.8  # Simulation value
            
        try:
            if sensor == 'left':
                pin = self.sensor_pins['infrared_left']
            elif sensor == 'right':
                pin = self.sensor_pins['infrared_right']
            else:
                print(f"Unknown infrared sensor: {sensor}")
                return 0.0
                
            if RPI_AVAILABLE:
                # Simple analog reading simulation
                # In real implementation, you'd use ADC
                value = GPIO.input(pin)
                # Convert to distance (inverse relationship)
                distance = (1.0 - value) * 1.0  # 0-1 meter range
                return max(0.05, min(1.0, distance))
            else:
                return 0.8  # Simulation value
                
        except Exception as e:
            print(f"Error reading infrared sensor {sensor}: {e}")
            return 0.0
            
    def read_battery_voltage(self) -> float:
        """Read battery voltage"""
        if not self.initialized and not RPI_AVAILABLE:
            return 12.6  # Simulation value
            
        try:
            if RPI_AVAILABLE:
                # In real implementation, you'd read from ADC
                # For now, return simulated voltage
                import random
                voltage = 12.6 + random.uniform(-0.2, 0.2)  # 12.4V - 12.8V range
                return max(10.0, min(13.0, voltage))
            else:
                return 12.6  # Simulation value
                
        except Exception as e:
            print(f"Error reading battery voltage: {e}")
            return 0.0
            
    def read_imu_data(self) -> Dict[str, float]:
        """Read IMU sensor data (roll, pitch, yaw)"""
        if not RPI_AVAILABLE:
            return {'roll': 0.0, 'pitch': 0.0, 'yaw': 0.0}
            
        try:
            # In real implementation, you'd read from MPU9250 or similar
            # For now, return simulated data
            import random
            return {
                'roll': random.uniform(-5, 5),
                'pitch': random.uniform(-5, 5),
                'yaw': random.uniform(-180, 180)
            }
        except Exception as e:
            print(f"Error reading IMU data: {e}")
            return {'roll': 0.0, 'pitch': 0.0, 'yaw': 0.0}
            
    def emergency_stop(self):
        """Emergency stop - immediately stop all motors"""
        self.stop_all_motors()
        print("Emergency stop activated - all motors stopped")
        
    def get_motor_status(self) -> Dict[str, Dict]:
        """Get current motor status"""
        return self.motor_states.copy()
        
    def cleanup(self):
        """Cleanup GPIO resources"""
        if RPI_AVAILABLE and self.initialized:
            try:
                # Stop all PWM
                for pwm in self.pwm_instances.values():
                    pwm.stop()
                    
                # Cleanup GPIO
                GPIO.cleanup()
                self.initialized = False
                print("GPIO cleanup completed")
            except Exception as e:
                print(f"GPIO cleanup error: {e}")

# Example usage and testing
if __name__ == "__main__":
    gpio = RPiGPIOInterface()
    
    try:
        print("Testing GPIO interface...")
        
        # Test motor control
        print("Testing motors...")
        gpio.set_motor_speed('left', 0.5)
        time.sleep(2)
        gpio.set_motor_speed('right', 0.5)
        time.sleep(2)
        gpio.stop_all_motors()
        
        # Test sensors
        print("Testing sensors...")
        front_dist = gpio.read_ultrasonic('front')
        rear_dist = gpio.read_ultrasonic('rear')
        left_ir = gpio.read_infrared('left')
        right_ir = gpio.read_infrared('right')
        battery = gpio.read_battery_voltage()
        imu = gpio.read_imu_data()
        
        print(f"Sensors - Front US: {front_dist:.2f}m, Rear US: {rear_dist:.2f}m")
        print(f"Sensors - Left IR: {left_ir:.2f}m, Right IR: {right_ir:.2f}m")
        print(f"Battery: {battery:.1f}V")
        print(f"IMU: Roll={imu['roll']:.1f}°, Pitch={imu['pitch']:.1f}°, Yaw={imu['yaw']:.1f}°")
        
    except KeyboardInterrupt:
        print("Test interrupted")
    finally:
        gpio.cleanup()
