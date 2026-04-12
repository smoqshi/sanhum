# Sanhum Robot System

A dual-platform ROS2 robot control system featuring a Windows GUI control station and Raspberry Pi robot node with real-time hardware control.

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
python install_all.py
```

**Linux/Raspberry Pi:**
```bash
sudo python3 install_all.py
```

The universal installer automatically:
- Installs ROS2 Jazzy (downloads on Windows, apt on Linux)
- Sets up all dependencies (OpenCV, Qt6, build tools)
- Builds the project with proper configuration
- Creates startup scripts for easy launching
- Configures environment variables

### Manual Installation

For detailed manual installation steps, see [INSTALL.md](INSTALL.md).

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
   # Terminal 1: Start ROS2 core (if not running on network)
   ros2 daemon start
   
   # Terminal 2: Launch robot node
   cd ~/sanhum_ws
   ros2 launch sanhum raspberry_pi.launch.py
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
│   ├── gui_main.cpp       # Windows GUI entry point
│   ├── robot_main.cpp     # Raspberry Pi robot entry point
│   ├── main_window.cpp    # Main GUI window
│   ├── motor_driver.cpp   # Motor control implementation
│   ├── esp32_driver.cpp   # Manipulator serial driver
│   ├── arduino_sensors.cpp # Sensor array driver
│   └── ...
├── include/               # Header files
├── launch/               # ROS2 launch files
├── config/               # Configuration files
├── CMakeLists.txt        # Build configuration
└── package.xml          # ROS2 package manifest
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
