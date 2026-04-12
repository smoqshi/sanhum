# Sanhum Robot Scripts

This directory contains essential scripts for the Sanhum robot system.

## Universal Installer

### `install_all.py`
- **Purpose**: Universal one-click installer for all platforms
- **Features**: Cross-platform, automatic ROS2 installation, dependency management
- **Usage**: 
  - Windows: `python install_all.py` (run as Administrator)
  - Linux/Raspberry Pi: `sudo python3 install_all.py`
- **Installs**: ROS2 Jazzy, OpenCV, Qt6, build tools, vcpkg
- **Builds**: Project with proper configuration
- **Creates**: Startup scripts and environment setup

### Utility Scripts

#### `check_dependencies.py`
- **Purpose**: Verify all dependencies are installed
- **Checks**: ROS2, build tools, Python packages, project structure
- **Usage**: `python scripts/check_dependencies.py`
- **Helps**: Troubleshoot installation issues

#### `install_raspberry_pi.sh`
- **Purpose**: Manual installation for Raspberry Pi (if universal installer fails)
- **Usage**: `./scripts/install_raspberry_pi.sh`
- **Alternative**: Use universal installer instead

## Platform-Specific Requirements

### Windows
- **OS**: Windows 10/11 (64-bit)
- **Permissions**: Administrator for installation
- **Software**: Visual Studio 2019+, Git
- **Hardware**: XInput-compatible gamepad (recommended)

### Raspberry Pi
- **Hardware**: Raspberry Pi 4B (4GB RAM recommended)
- **OS**: Raspberry Pi OS (64-bit) or Ubuntu 22.04 LTS
- **Permissions**: User in dialout group
- **Hardware**: ESP32 + Arduino Nano via USB

## Common Workflow

### First Time Setup
1. Run dependency checker: `python scripts/check_dependencies.py`
2. Run appropriate installation script
3. Reboot (required for serial port permissions on Pi)
4. Verify installation with dependency checker

### Development Cycle
1. Make code changes
2. Build: `python scripts/build_project.py --clean`
3. Run appropriate startup script
4. Test and repeat

### Troubleshooting
1. Run dependency checker to identify issues
2. Check script output for specific error messages
3. Verify hardware connections (especially serial ports)
4. Consult main README.md for detailed troubleshooting

## Script Features

### Error Handling
- All scripts include comprehensive error checking
- Clear error messages with suggested fixes
- Graceful failure with exit codes

### Progress Reporting
- Colored output for better readability
- Step-by-step progress indicators
- Summary of completed actions

### Safety Features
- Backup checks before destructive operations
- Permission verification
- Hardware connection validation

## Advanced Usage

### Custom Installation Paths
The Windows installation script can be modified to use different paths by editing these variables:
- `ROS2_INSTALL_PATH`: ROS2 installation directory
- `VCPKG_ROOT`: vcpkg installation directory

### Build Customization
The build script supports various options:
- `--clean`: Clean build directory first
- `--platform`: Force specific platform
- Parallel builds by default

### Workspace Management
For Raspberry Pi, scripts automatically create and manage:
- `~/sanhum_ws`: ROS2 workspace
- Symbolic links to project source
- Environment sourcing in `.bashrc`

## File Permissions

On Linux/macros, make scripts executable:
```bash
chmod +x scripts/*.sh
chmod +x scripts/*.py
```

## Support

For issues with the scripts:
1. Check the dependency checker output
2. Review script error messages
3. Consult the main README.md
4. Create an issue in the repository
