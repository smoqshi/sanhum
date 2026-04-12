#!/bin/bash
# Sanhum Robot Raspberry Pi Installation Script
# This script installs dependencies and builds the robot node

set -e  # Exit on any error

echo "========================================"
echo "Sanhum Robot Raspberry Pi Installation"
echo "========================================"
echo

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
    print_error "This script should not be run as root. Run as regular user."
    exit 1
fi

# Set paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ROS2_DISTRO=jazzy
WORKSPACE="$HOME/sanhum_ws"

print_status "Installation paths:"
print_status "Project: $PROJECT_ROOT"
print_status "Workspace: $WORKSPACE"
echo

# Function to check command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# [1/8] Check system requirements
print_status "[1/8] Checking system requirements..."

# Check if Raspberry Pi
if ! command_exists vcgencmd; then
    print_warning "This script is optimized for Raspberry Pi. Continuing anyway..."
fi

# Check OS
if [[ -f /etc/os-release ]]; then
    . /etc/os-release
    print_status "OS: $PRETTY_NAME"
else
    print_warning "Cannot determine OS version"
fi

# Check architecture
ARCH=$(uname -m)
if [[ "$ARCH" != "aarch64" && "$ARCH" != "arm64" && "$ARCH" != "x86_64" ]]; then
    print_warning "Unsupported architecture: $ARCH"
fi

# [2/8] Update system packages
print_status "[2/8] Updating system packages..."
sudo apt update
sudo apt upgrade -y

# [3/8] Install ROS2 Jazzy
print_status "[3/8] Installing ROS2 Jazzy..."

# Check if ROS2 is already installed
if command_exists ros2; then
    print_status "ROS2 is already installed"
else
    print_status "Installing ROS2 Jazzy..."
    
    # Install required packages
    sudo apt install -y curl gnupg lsb-release
    
    # Add ROS2 apt repository
    curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.asc | sudo apt-key add -
    sudo sh -c "echo 'deb http://packages.ros.org/ros2/ubuntu $(lsb_release -cs) main' > /etc/apt/sources.list.d/ros2.list"
    
    # Update package list
    sudo apt update
    
    # Install ROS2 desktop
    sudo apt install -y ros-$ROS2_DISTRO-desktop python3-argcomplete
    
    # Install additional ROS2 packages
    sudo apt install -y \
        ros-$ROS2_DISTRO-geometry-msgs \
        ros-$ROS2_DISTRO-nav-msgs \
        ros-$ROS2_DISTRO-sensor-msgs \
        ros-$ROS2_DISTRO-std-msgs \
        ros-$ROS2_DISTRO-vision-msgs \
        ros-$ROS2_DISTRO-cv-bridge \
        ros-$ROS2_DISTRO-ros2launch
    
    # Initialize rosdep
    sudo apt install -y python3-rosdep
    sudo rosdep init
    rosdep update
    
    # Setup ROS2 environment
    echo "source /opt/ros/$ROS2_DISTRO/setup.bash" >> ~/.bashrc
fi

# [4/8] Install development tools
print_status "[4/8] Installing development tools..."
sudo apt install -y \
    build-essential \
    cmake \
    git \
    python3-pip \
    python3-vcstool \
    python3-colcon-common-extensions

# [5/8] Install Python dependencies
print_status "[5/8] Installing Python dependencies..."
pip3 install --user pyserial

# [6/8] Configure serial ports
print_status "[6/8] Configuring serial port access..."

# Add user to dialout group
if groups $USER | grep -q dialout; then
    print_status "User already in dialout group"
else
    print_status "Adding user to dialout group..."
    sudo usermod -a -G dialout $USER
    print_warning "You will need to reboot for serial port permissions to take effect"
fi

# [7/8] Setup workspace and build project
print_status "[7/8] Setting up workspace and building project..."

# Create workspace if it doesn't exist
if [[ ! -d "$WORKSPACE" ]]; then
    mkdir -p "$WORKSPACE/src"
    print_status "Created workspace: $WORKSPACE"
fi

# Link project to workspace
if [[ ! -L "$WORKSPACE/src/sanhum" ]]; then
    ln -sf "$PROJECT_ROOT" "$WORKSPACE/src/sanhum"
    print_status "Linked project to workspace"
fi

# Source ROS2
source /opt/ros/$ROS2_DISTRO/setup.bash

# Build the project
cd "$WORKSPACE"
print_status "Building Sanhum project..."
colcon build --packages-select sanhum

# [8/8] Setup environment
print_status "[8/8] Setting up environment..."

# Source workspace in bashrc
if ! grep -q "source $WORKSPACE/install/setup.bash" ~/.bashrc; then
    echo "source $WORKSPACE/install/setup.bash" >> ~/.bashrc
    print_status "Added workspace to bashrc"
fi

# Source environment for current session
source "$WORKSPACE/install/setup.bash"

# Create startup script
cat > "$HOME/start_sanhum_robot.sh" << 'EOF'
#!/bin/bash
# Sanhum Robot Startup Script

# Source ROS2 and workspace
source /opt/ros/jazzy/setup.bash
source ~/sanhum_ws/install/setup.bash

# Start robot node
ros2 launch sanhum raspberry_pi.launch.py
EOF

chmod +x "$HOME/start_sanhum_robot.sh"

echo
echo "========================================"
echo "Installation completed successfully!"
echo "========================================"
echo
echo "Next steps:"
echo "1. Reboot the system for serial port permissions to take effect"
echo "2. Run the robot with: ~/start_sanhum_robot.sh"
echo "3. Or manually: cd ~/sanhum_ws && ros2 launch sanhum raspberry_pi.launch.py"
echo
echo "To verify installation:"
echo "  - Check ROS2: ros2 --help"
echo "  - Check project: ros2 pkg list | grep sanhum"
echo "  - Check launch files: ros2 pkg executables sanhum"
echo
print_warning "Remember to reboot the system before running the robot!"
echo
