#!/usr/bin/env python3
"""
Sanhum Robot WiFi Server
Runs on Raspberry Pi to accept WiFi connections from the GUI
"""

import socket
import json
import threading
import time
from datetime import datetime

# Try to import hardware interfaces
try:
    from rpi_gpio_interface import RPiGPIOInterface
    from esp32_interface import get_esp32_interface
    from arduino_interface import get_arduino_interface
    HARDWARE_AVAILABLE = True
except ImportError:
    HARDWARE_AVAILABLE = False
    print("Warning: Hardware interfaces not available - running in simulation mode")


class WiFiServer:
    """WiFi socket server for robot control"""

    def __init__(self, host='0.0.0.0', port=5000):
        self.host = host
        self.port = port
        self.server_socket = None
        self.client_socket = None
        self.client_address = None
        self.running = False
        self.connected = False

        # Robot state
        self.linear_velocity = 0.0
        self.angular_velocity = 0.0
        self.joint_angles = [0.0, 0.0, 0.0, 0.0, 0.0]  # J1-J5
        self.gripper_open = 0.0
        self.emergency_stop = False

        # Hardware interfaces
        self.gpio_interface = None
        self.esp32_interface = None
        self.arduino_interface = None

        # Initialize hardware if available
        if HARDWARE_AVAILABLE:
            try:
                self.gpio_interface = RPiGPIOInterface()
                self.esp32_interface = get_esp32_interface()
                self.arduino_interface = get_arduino_interface()
                print("Hardware interfaces initialized")
            except Exception as e:
                print(f"Warning: Hardware initialization failed: {e}")

    def start(self):
        """Start the WiFi server"""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(1)
        self.running = True

        print(f"WiFi Server started on {self.host}:{self.port}")
        print("Waiting for GUI connection...")

        # Start accept thread
        accept_thread = threading.Thread(target=self._accept_connections, daemon=True)
        accept_thread.start()

    def _accept_connections(self):
        """Accept incoming connections"""
        while self.running:
            try:
                self.server_socket.settimeout(1.0)
                self.client_socket, self.client_address = self.server_socket.accept()
                self.connected = True
                print(f"Connected to GUI at {self.client_address}")

                # Start receive thread
                receive_thread = threading.Thread(target=self._receive_commands, daemon=True)
                receive_thread.start()

                # Start telemetry thread
                telemetry_thread = threading.Thread(target=self._send_telemetry, daemon=True)
                telemetry_thread.start()

            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    print(f"Accept error: {e}")
                break

    def _receive_commands(self):
        """Receive commands from GUI"""
        while self.running and self.connected:
            try:
                self.client_socket.settimeout(1.0)
                data = self.client_socket.recv(1024)
                if not data:
                    break

                # Parse JSON command
                command = json.loads(data.decode('utf-8'))
                self._process_command(command)

            except socket.timeout:
                continue
            except json.JSONDecodeError as e:
                print(f"JSON decode error: {e}")
            except Exception as e:
                print(f"Receive error: {e}")
                break

        self._disconnect()

    def _process_command(self, command):
        """Process command from GUI"""
        cmd_type = command.get('type')

        if cmd_type == 'velocity':
            # Set robot velocity
            self.linear_velocity = command.get('linear', 0.0)
            self.angular_velocity = command.get('angular', 0.0)
            self._apply_velocity()

        elif cmd_type == 'manipulator':
            # Set manipulator joints
            self.joint_angles = command.get('joints', [0.0, 0.0, 0.0, 0.0, 0.0])
            self.gripper_open = command.get('gripper', 0.0)
            self._apply_manipulator()

        elif cmd_type == 'emergency_stop':
            # Emergency stop
            self.emergency_stop = True
            self.linear_velocity = 0.0
            self.angular_velocity = 0.0
            self._emergency_stop()

        elif cmd_type == 'reset':
            # Reset emergency stop
            self.emergency_stop = False
            print("Emergency stop reset")

        elif cmd_type == 'home':
            # Home manipulator
            self.joint_angles = [0.0, 0.0, 0.0, 0.0, 0.0]
            self.gripper_open = 0.0
            self._apply_manipulator()
            print("Manipulator homed")

    def _apply_velocity(self):
        """Apply velocity to motors"""
        if self.gpio_interface and not self.emergency_stop:
            try:
                # Convert to motor speeds (left, right)
                # Differential drive kinematics
                track_gauge = 0.35  # meters
                wheel_radius = 0.04  # meters

                left_speed = (self.linear_velocity - self.angular_velocity * track_gauge / 2) / wheel_radius
                right_speed = (self.linear_velocity + self.angular_velocity * track_gauge / 2) / wheel_radius

                # Apply to GPIO (PWM)
                self.gpio_interface.set_motor_speed('left', left_speed)
                self.gpio_interface.set_motor_speed('right', right_speed)
            except Exception as e:
                print(f"Velocity application error: {e}")

    def _apply_manipulator(self):
        """Apply manipulator joint angles"""
        if self.esp32_interface:
            try:
                # Send joint commands to ESP32
                for i, angle in enumerate(self.joint_angles):
                    self.esp32_interface.send_joint_command(i + 1, angle)

                # Send gripper command
                self.esp32_interface.send_gripper_command(self.gripper_open)
            except Exception as e:
                print(f"Manipulator application error: {e}")

    def _emergency_stop(self):
        """Emergency stop all motors"""
        if self.gpio_interface:
            try:
                self.gpio_interface.emergency_stop()
            except Exception as e:
                print(f"Emergency stop error: {e}")

    def _send_telemetry(self):
        """Send telemetry data to GUI"""
        while self.running and self.connected:
            try:
                # Get sensor data
                sensor_data = self._get_sensor_data()

                # Build telemetry message
                telemetry = {
                    'type': 'telemetry',
                    'timestamp': datetime.now().isoformat(),
                    'velocity': {
                        'linear': self.linear_velocity,
                        'angular': self.angular_velocity
                    },
                    'manipulator': {
                        'joints': self.joint_angles,
                        'gripper': self.gripper_open
                    },
                    'sensors': sensor_data,
                    'emergency_stop': self.emergency_stop
                }

                # Send to GUI
                message = json.dumps(telemetry).encode('utf-8')
                self.client_socket.sendall(message)

                time.sleep(0.1)  # 10 Hz telemetry

            except Exception as e:
                print(f"Telemetry error: {e}")
                break

    def _get_sensor_data(self):
        """Get sensor data from Arduino"""
        if self.arduino_interface:
            try:
                # Simulate sensor data for now
                # In real implementation, would read from Arduino
                return {
                    'ultrasonic_front': 2.5,
                    'ultrasonic_rear': 2.5,
                    'infrared_left': 0.8,
                    'infrared_right': 0.8
                }
            except Exception as e:
                print(f"Sensor read error: {e}")
                return {}
        return {}

    def _disconnect(self):
        """Disconnect from GUI"""
        self.connected = False
        if self.client_socket:
            self.client_socket.close()
            self.client_socket = None
        print("Disconnected from GUI")

    def stop(self):
        """Stop the WiFi server"""
        self.running = False
        self._disconnect()
        if self.server_socket:
            self.server_socket.close()
        print("WiFi Server stopped")


def main():
    """Main entry point"""
    server = WiFiServer(host='0.0.0.0', port=5000)

    try:
        server.start()
        print("WiFi Server running. Press Ctrl+C to stop.")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.stop()


if __name__ == '__main__':
    main()
