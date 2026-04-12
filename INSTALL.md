# Universal Installation Guide

## One-Click Installation

The Sanhum robot project now includes a universal installer that works on all platforms with a single command.

### Quick Start

**Windows (Recommended - No Dependencies Required):**
```bash
python install_simple.py
```

**Windows (Full Production - Requires Visual Studio):**
```bash
python install_all_production.py
```

**Linux/Raspberry Pi:**
```bash
sudo python3 install_all.py
```

### Development/Debug Version
For testing and debugging:
```bash
python install_all_debug.py
```

## What the Universal Installer Does

### Windows Features
- ✅ **Automatic ROS2 Jazzy installation** (downloads and extracts)
- ✅ **vcpkg package manager setup** (downloads and bootstraps)
- ✅ **All dependencies** (OpenCV, Qt6, Visual Studio integration)
- ✅ **Project compilation** (CMake configuration and build)
- ✅ **Environment setup** (creates startup scripts)
- ✅ **Error handling** with detailed troubleshooting

### Linux/Raspberry Pi Features
- ✅ **ROS2 Jazzy installation** (apt package manager)
- ✅ **Development tools** (build-essential, cmake, git)
- ✅ **Python dependencies** (pyserial, colcon)
- ✅ **Workspace setup** (creates ROS2 workspace)
- ✅ **Project compilation** (colcon build)
- ✅ **Environment configuration** (bashrc updates)

## Manual Installation Options

If the universal installer fails, you can use platform-specific scripts:

### Windows
```bash
# Complete installation (requires ROS2 pre-installed)
scripts\install_windows_no_admin.bat

# vcpkg and dependencies only
scripts\setup_vcpkg.bat

# OpenCV only
scripts\install_opencv_only.bat
```

### Linux/Raspberry Pi
```bash
chmod +x scripts/install_raspberry_pi.sh
./scripts/install_raspberry_pi.sh
```

## System Requirements

### Windows
- **OS**: Windows 10/11 (64-bit)
- **Admin**: Required for ROS2 and Visual Studio installation
- **Software**: Git, Visual Studio 2019+ (auto-detected)
- **Hardware**: 8GB RAM, 10GB free disk space

### Linux/Raspberry Pi
- **OS**: Ubuntu 22.04 LTS or Raspberry Pi OS (64-bit)
- **Hardware**: Raspberry Pi 4B (4GB RAM recommended)
- **Storage**: 8GB free disk space
- **Network**: Internet connection for package downloads

## Installation Process

### Step 1: Download and Run
```bash
# Clone or download the project
git clone <repository-url>
cd sanhum

# Run universal installer
python install_all.py
```

### Step 2: Follow Prompts
The installer will:
1. Detect your platform
2. Check system requirements
3. Install missing dependencies
4. Build the project
5. Create startup scripts

### Step 3: Launch Application
After successful installation:

**Windows:**
```bash
start_sanhum.bat
```

**Linux/Raspberry Pi:**
```bash
~/start_sanhum_robot.sh
```

## Troubleshooting

### Common Issues

**"Administrator privileges required" (Windows)**
- Right-click Command Prompt → "Run as administrator"
- Or run PowerShell as administrator

**"sudo privileges required" (Linux)**
- Run with `sudo python3 install_all.py`
- Or add user to sudoers file

**"Network connection failed"**
- Check internet connection
- Verify firewall allows downloads
- Try running from different network

**"Build failed"**
- Check dependency installation
- Verify Visual Studio/Build tools
- Run dependency checker: `python scripts/check_dependencies.py`

**"vcpkg not found"**
- The installer will automatically install vcpkg
- If it fails, run: `scripts/setup_vcpkg.bat`

**"ROS2 not found"**
- Windows: Installer downloads and installs automatically
- Linux: Installer installs via apt package manager

### Manual Recovery

If universal installer fails completely:

1. **Check system**: `python scripts/check_dependencies.py`
2. **Install ROS2 manually** (see platform-specific guides)
3. **Run platform-specific script**
4. **Build manually** with provided CMake/colcon commands

## Verification

### Check Installation
```bash
# Run dependency checker
python scripts/check_dependencies.py

# Should show:
# - ROS2: OK
# - Build tools: OK  
# - Dependencies: OK
# - Project structure: OK
```

### Test Application
```bash
# Windows
start_sanhum.bat

# Linux
~/start_sanhum_robot.sh

# Should see:
# - ROS2 environment sourced
# - Application launches
# - No error messages
```

## Advanced Options

### Custom Installation Paths
Edit `install_all.py` to change default paths:
- Windows: `C:/dev/ros2`, `C:/vcpkg`
- Linux: `/opt/ros/jazzy`, `~/sanhum_ws`

### Selective Installation
Comment out sections in `install_all.py`:
- Skip ROS2 installation (if already installed)
- Skip dependency installation (if using system packages)
- Skip build step (manual compilation)

### Development Mode
For development without full installation:
```bash
# Install dependencies only
python install_all.py --deps-only

# Build only
python install_all.py --build-only
```

## Support

### Getting Help
1. **Run dependency checker** for system analysis
2. **Check installer output** for specific error messages
3. **Consult platform-specific guides** in `scripts/README.md`
4. **Create an issue** in the repository with installer output

### Debug Mode
Enable verbose logging:
```bash
python install_all.py --debug
```

This provides detailed output for troubleshooting.

---

**The universal installer `install_all.py` provides the simplest way to get Sanhum robot running on any platform.**
