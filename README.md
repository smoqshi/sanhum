# Sanhum Robot System

A platform ROS2 robot control system featuring a Windows GUI control station and Raspberry Pi robot node with real-time hardware control.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Security

For security policies, vulnerability reporting, and best practices, see [docs/SECURITY.md](docs/SECURITY.md).

## System Architecture

The Sanhum robot system consists of two main components:

### 1. Windows Control Station
- **Qt6-based GUI** for robot teleoperation and monitoring
- **Gamepad control** via XInput (Windows)
- **Real-time visualization** of robot state and sensors
- **WiFi communication** with robot node
- **Camera feeds** and obstacle detection display

### 2. Raspberry Pi Robot Node
- **Motor control** with differential drive kinematics
- **ESP32 manipulator** control via serial communication
- **Arduino sensor array** for obstacle detection
- **ROS2 communication** for command and telemetry
- **Hardware abstraction** through driver classes

## Hardware Configuration

### Robot Physical Parameters
- **Base dimensions**: 500mm × 600mm × 300mm
- **Track gauge**: 350mm (distance between tracks)
- **Wheel diameter**: 80mm (effective track drive diameter)
- **Manipulator**: 5-DOF articulated arm with gripper

### Raspberry Pi GPIO Configuration
```yaml
raspberry_pi:
  motor_pins:
    left_motor_1: 17   # GPIO17 - Left motor forward
    left_motor_2: 27   # GPIO27 - Left motor backward
    right_motor_1: 22  # GPIO22 - Right motor forward
    right_motor_2: 23  # GPIO23 - Right motor backward
```

### Serial Communication
```yaml
serial_ports:
  esp32:
    port: /dev/ttyUSB0     # Manipulator control
    baud_rate: 115200
  arduino_nano:
    port: /dev/ttyUSB1     # Obstacle sensors
    baud_rate: 9600
```

## System Requirements

### Windows Control Station
- **OS**: Windows 10/11 (64-bit)
- **ROS2**: Jazzy Jalopy
- **Qt6**: Core, Gui, Widgets, Network modules
- **OpenCV**: Core and imgproc modules
- **Visual Studio**: 2019 or later
- **CMake**: 3.16 or later

### Raspberry Pi Robot
- **Hardware**: Raspberry Pi 4B (4GB RAM recommended)
- **OS**: Raspberry Pi OS (64-bit) or Ubuntu 22.04 LTS
- **ROS2**: Jazzy Jalopy
- **Python**: 3.10 or later
- **Serial ports**: USB for ESP32 and Arduino Nano

## Installation Instructions

### Universal One-Click Installer

The Sanhum robot project includes a universal installer that works on all platforms:

**Windows (Run as Administrator):**
```bash
python setup.py
```

**Linux/Raspberry Pi:**
```bash
sudo python3 setup.py
```

The universal installer automatically:
- Installs ROS2 Jazzy (downloads on Windows, apt on Linux)
- Sets up all dependencies (OpenCV, Qt5, build tools, python3-pigpio)
- Builds the project with proper configuration
- Creates startup scripts for easy launching
- Configures environment variables

**No manual installation required - everything is handled automatically.**

### Quick Start

After installation:

**Windows:**
```bash
start_sanhum.bat
```

**Linux/Raspberry Pi:**
```bash
~/start_sanhum_robot.sh
```

Or run the executable directly:
```bash
/root/sanhum_ws/install/sanhum/lib/sanhum/sanhum_robot --ros-args --params-file /root/sanhum_ws/install/sanhum/share/sanhum/config/raspberry_pi_config.yaml
```

## Boot Procedures

### Windows Control Station Startup

1. **Launch ROS2 Core**
   ```bash
   call "C:\dev\ros2\jazzy\setup.bat"
   ros2 core start
   ```

2. **Start GUI Application**
   ```bash
   cd build
   ros2 launch sanhum main.launch.py
   ```

3. **Connect to Robot**
   - Enter robot namespace when prompted
   - Leave empty for simulation mode
   - Use robot's hostname or IP address for real robot

4. **Verify Connection**
   - Check for odometry messages: `ros2 topic echo /odom`
   - Verify gamepad input is received
   - Confirm camera feeds (if available)

### Raspberry Pi Robot Startup

1. **Power On Hardware**
   - Connect Raspberry Pi to power
   - Ensure ESP32 and Arduino are powered via USB
   - Verify motor driver power supply

2. **Start Robot Node**
   ```bash
   # Run the startup script
   ~/start_sanhum_robot.sh
   ```

   Or run the executable directly:
   ```bash
   /root/sanhum_ws/install/sanhum/lib/sanhum/sanhum_robot --ros-args --params-file /root/sanhum_ws/install/sanhum/share/sanhum/config/raspberry_pi_config.yaml
   ```

3. **Verify Hardware Initialization**
   ```bash
   # Check motor driver
   ros2 topic list | grep odom

   # Check ESP32 connection
   ros2 topic list | grep manipulator

   # Check Arduino sensors
   ros2 topic list | grep obstacle_sensor
   ```

4. **Test Motor Control**
   ```bash
   # Send test velocity command
   ros2 topic pub /cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.1}, angular: {z: 0.0}}"
   ```

## Communication Protocols

### ROS2 Topics
- `/cmd_vel` - Velocity commands (geometry_msgs/Twist)
- `/odom` - Odometry feedback (nav_msgs/Odometry)
- `/manipulator/joint_commands` - Manipulator control (sensor_msgs/JointState)
- `/manipulator/joint_states` - Manipulator feedback (sensor_msgs/JointState)
- `/obstacle_sensor_0..5` - Distance sensors (sensor_msgs/Range)

### Serial Protocols

#### ESP32 Manipulator
- **Command format**: `C:p1,p2,p3,p4,p5\n`
- **Parameters**: Joint positions in radians (3 decimal places)
- **Example**: `C:0.000,1.571,0.785,0.000,0.500\n`

#### Arduino Sensors
- **Data format**: `d1,d2,d3,d4,d5,d6\n`
- **Parameters**: Distances in millimeters
- **Example**: `450,320,680,1200,890,1500\n`

## Hardware Implementation Status

### Current Implementation (Dummy I/O)

The current codebase includes **dummy I/O implementations** for testing and development without actual hardware. These placeholders simulate hardware behavior and allow the ROS2 node to run and publish/subscribe to topics without requiring physical hardware.

#### Dummy GPIO Control (motor_driver.cpp)
- **Current behavior**: Simulates GPIO pin states in memory only - does NOT touch actual GPIO pins
- **Functions implemented**: `gpioSetMode()`, `gpioWrite()`, `gpioInitialise()`, `gpioTerminate()` (dummy implementations)
- **Motor control**: Simple on/off based on speed threshold (0.1)
- **Hardware connection**: None - purely simulation for testing
- **TODO**: Replace dummy functions with actual GPIO library calls when real hardware is connected
- **Required changes for real hardware**:
  ```cpp
  // Replace dummy functions with pigpio (Raspberry Pi) or other GPIO library:
  #include <pigpio.h>
  gpioSetMode(pin, PI_OUTPUT);
  gpioWrite(pin, level);
  gpioInitialise();
  gpioTerminate();
  ```

#### Dummy Encoder Reading (motor_driver.cpp)
- **Current behavior**: Simulates odometry from commanded speeds
- **Odometry calculation**: Uses kinematic model with commanded velocities
- **TODO**: Replace with actual encoder reading using pigpio
- **Required changes**:
  ```cpp
  // Add encoder reading:
  int left_encoder = gpioGetEncoder(left_encoder_pin);
  int right_encoder = gpioGetEncoder(right_encoder_pin);
  // Calculate actual position from encoder ticks
  ```

#### Dummy ESP32 Protocol (esp32_driver.cpp)
- **Current behavior**: Parses "S:p1,p2,p3,p4,p5" format and publishes dummy states
- **Protocol implemented**: Basic joint state parsing
- **Fallback**: Publishes zero positions if no valid data received
- **TODO**: Implement actual ESP32 communication protocol
- **Required changes**:
  - Define actual ESP32 protocol format
  - Add error handling and validation
  - Implement bidirectional communication

#### Arduino Sensors (arduino_sensors.cpp)
- **Current behavior**: Reads serial data and parses distance sensor format
- **Protocol implemented**: "d1,d2,d3,d4,d5,d6" format (distances in mm)
- **Status**: Functional - reads from actual serial port
- **TODO**: Verify with actual Arduino hardware

### To Enable Real Hardware Control

**Note**: python3-pigpio is already installed automatically by the install script.

1. **Replace dummy GPIO functions** in `motor_driver.cpp`:
   - Remove dummy namespace
   - Add `#include <pigpio.h>`
   - Replace dummy functions with actual pigpio calls
   - Add PWM control for variable speed

2. **Implement encoder reading**:
   - Connect encoder hardware to GPIO pins
   - Add encoder reading functions
   - Calculate actual odometry from encoder ticks

3. **Complete ESP32 protocol**:
   - Define actual communication protocol with ESP32
   - Add proper error handling
   - Implement feedback loop

4. **Test with hardware**:
   - Verify GPIO pin assignments match hardware
   - Test motor control with safety precautions
   - Calibrate sensors and encoders

## Troubleshooting

### Common Issues

#### Windows GUI
- **Gamepad not detected**: Ensure XInput-compatible controller
- **ROS2 connection failed**: Check network configuration and firewall
- **Camera feed missing**: Verify camera drivers and USB connections

#### Raspberry Pi Robot
- **Serial port permission denied**: Add user to dialout group
- **Motors not responding**: Check GPIO pin assignments and power supply
- **ESP32/Arduino not found**: Verify USB connections and port names

#### Network Issues
- **Cannot reach robot**: Ping robot hostname/IP address
- **Topic not visible**: Check ROS2 domain ID configuration
- **High latency**: Use wired Ethernet connection for better performance

### Debug Commands
```bash
# ROS2 network debugging
ros2 doctor

# Topic monitoring
ros2 topic hz /cmd_vel
ros2 topic echo /odom

# System resource monitoring
htop  # Raspberry Pi
top   # Windows (WSL)
```

## Development

### Project Structure
```
sanhum/
├── src/                    # Source code
│   ├── gui_main.py        # Python GUI (Tkinter) - Main control interface
│   ├── robot_main.cpp     # Raspberry Pi robot entry point
│   ├── motor_driver.cpp   # Motor control implementation
│   ├── esp32_driver.cpp   # Manipulator serial driver
│   ├── arduino_sensors.cpp # Sensor array driver
│   ├── hardware_integration.py # Hardware manager
│   ├── robot_simulation.py # Robot simulation
│   ├── camera_interface.py # Camera interface
│   ├── esp32_interface.py # ESP32 interface
│   ├── arduino_interface.py # Arduino interface
│   ├── gpio_interface.py # GPIO interface
│   ├── input_controller.py # Input controller
│   ├── robot_interface.py # Robot interface
│   ├── serial_interfaces.py # Serial interfaces
│   └── rpi_gpio_interface.py # Raspberry Pi GPIO interface
├── include/               # C++ Header files
│   ├── motor_driver.h
│   ├── esp32_driver.h
│   ├── arduino_sensors.h
│   └── communication_protocols.h
├── launch/               # ROS2 launch files
│   ├── main.launch.py
│   └── raspberry_pi.launch.py
├── config/               # Configuration files
│   └── raspberry_pi_config.yaml
├── docs/                 # Documentation
│   └── SECURITY.md       # Security policies
├── CMakeLists.txt        # Build configuration
├── package.xml          # ROS2 package manifest
├── setup.py             # Universal installer
├── LICENSE              # MIT License
└── README.md            # This file
```

### Building for Different Platforms
```bash
# Windows build
cmake .. -A x64
cmake --build . --config Release

# Linux/Raspberry Pi build
colcon build --packages-select sanhum
```

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Support

For issues and questions:
- Create an issue in the repository
- Check the troubleshooting section
- Review ROS2 documentation for platform-specific issues
