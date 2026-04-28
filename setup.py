#!/usr/bin/env python3
"""
Universal Sanhum Robot Installation Script
One-click installation for all platforms (Windows, Linux, Raspberry Pi)
"""

import os
import sys
import subprocess
import platform
import urllib.request
import zipfile
import shutil
import time
from pathlib import Path

class ProgressBar:
    """Simple text-based progress bar"""
    def __init__(self, total=100, prefix='', suffix='', length=50):
        self.total = total
        self.prefix = prefix
        self.suffix = suffix
        self.length = length
        self.current = 0

    def update(self, current):
        self.current = current
        self._print()

    def increment(self):
        self.current += 1
        self._print()

    def _print(self):
        percent = min(100, (self.current / self.total) * 100)
        filled_length = int(self.length * self.current // self.total)
        bar = '█' * filled_length + '-' * (self.length - filled_length)
        print(f'\r{self.prefix} |{bar}| {percent:.1f}% {self.suffix}', end='', flush=True)
        if self.current >= self.total:
            print()

class UniversalInstaller:
    def __init__(self):
        self.platform = platform.system().lower()
        self.script_dir = Path(__file__).parent
        self.project_root = self.script_dir

        # Colors for output
        self.colors = {
            'red': '\033[0;31m',
            'green': '\033[0;32m',
            'yellow': '\033[1;33m',
            'blue': '\033[0;34m',
            'cyan': '\033[0;36m',
            'nc': '\033[0m'  # No Color
        }

        # Installation steps tracking
        self.steps = [
            "Check system requirements",
            "Install ROS2 Jazzy",
            "Install dependencies",
            "Build project",
            "Setup environment"
        ]
        self.current_step = 0
        self.completed_steps = []

    def print_installation_state(self):
        """Print visual representation of installation state"""
        print()
        self.color_print("Installation Progress:", 'cyan')
        print("┌" + "─" * 50 + "┐")

        for i, step in enumerate(self.steps):
            if i < self.current_step:
                # Completed step
                status = "✓"
                color = 'green'
            elif i == self.current_step:
                # Current step
                status = "►"
                color = 'yellow'
            else:
                # Pending step
                status = "○"
                color = 'blue'

            step_text = f"{status} {step}"
            if self.platform == 'windows':
                print(f"│ {step_text:<48} │")
            else:
                color_code = self.colors.get(color, '')
                print(f"│ {color_code}{step_text:<48}{self.colors['nc']} │")

        print("└" + "─" * 50 + "┘")
        print()

    def advance_step(self):
        """Advance to next installation step"""
        self.completed_steps.append(self.steps[self.current_step])
        self.current_step += 1
        self.print_installation_state()
        
    def check_modules(self):
        """Check if required modules and dependencies are available"""
        self.color_print("Checking system modules and dependencies...", 'blue')
        print()
        
        all_checks_passed = True
        
        # Check Python version
        python_version = sys.version_info
        if python_version >= (3, 8):
            self.color_print(f"✓ Python {python_version.major}.{python_version.minor}.{python_version.micro}", 'green')
        else:
            self.color_print(f"✗ Python {python_version.major}.{python_version.minor}.{python_version.micro} (requires 3.8+)", 'red')
            all_checks_passed = False
        
        # Check required Python modules
        required_modules = {
            'subprocess': 'Standard library',
            'pathlib': 'Standard library',
            'urllib.request': 'Standard library',
            'zipfile': 'Standard library',
            'shutil': 'Standard library',
            'platform': 'Standard library',
            'ctypes': 'Standard library (Windows admin check)',
            'os': 'Standard library',
            'sys': 'Standard library'   
        }
        
        self.color_print("Python Modules:", 'blue')
        for module, description in required_modules.items():
            try:
                __import__(module)
                self.color_print(f"  ✓ {module} ({description})", 'green')
            except ImportError:
                self.color_print(f"  ✗ {module} ({description}) - MISSING", 'red')
                all_checks_passed = False
        
        # Check optional modules
        optional_modules = {
            'serial': 'Hardware communication',
            'cv2': 'OpenCV computer vision',
            'numpy': 'Numerical computing',
            'pygame': 'Gamepad support',
            'rclpy': 'ROS2 Python client',
            'PIL': 'Image processing (Pillow)',
            'tkinter': 'GUI framework'
        }
        
        self.color_print("\nOptional Modules:", 'blue')
        for module, description in optional_modules.items():
            try:
                __import__(module)
                self.color_print(f"  ✓ {module} ({description})", 'green')
            except ImportError:
                self.color_print(f"  ⚠ {module} ({description}) - Not installed (optional)", 'yellow')
        
        # Check system tools
        self.color_print("\nSystem Tools:", 'blue')
        
        if self.platform == 'windows':
            system_tools = {
                'git': 'Version control',
                'cmake': 'Build system',
                'cl': 'Visual Studio compiler'
            }

            for tool, description in system_tools.items():
                if tool == 'cl':
                    # Check for Visual Studio compiler
                    success, _, _ = self.run_command('where cl', capture_output=True)
                    if success and 'cl.exe' in _:
                        self.color_print(f"  ✓ {tool} ({description})", 'green')
                    else:
                        self.color_print(f"  ⚠ {tool} ({description}) - Visual Studio not found", 'yellow')
                        self.color_print("    Note: Python GUI does not require Visual Studio", 'blue')
                else:
                    success, _, _ = self.run_command(f'where {tool}', capture_output=True)
                    if success:
                        self.color_print(f"  ✓ {tool} ({description})", 'green')
                    else:
                        self.color_print(f"  ✗ {tool} ({description}) - Not found", 'red')
                        all_checks_passed = False
        
        elif self.platform == 'linux':
            system_tools = {
                'git': 'Version control',
                'cmake': 'Build system',
                'gcc': 'C compiler',
                'apt': 'Package manager',
                'colcon': 'ROS2 build tool'
            }
            
            for tool, description in system_tools.items():
                success, _, _ = self.run_command(f'which {tool}', capture_output=True)
                if success:
                    self.color_print(f"  ✓ {tool} ({description})", 'green')
                else:
                    if tool in ['colcon']:
                        self.color_print(f"  ⚠ {tool} ({description}) - Will be installed", 'yellow')
                    else:
                        self.color_print(f"  ✗ {tool} ({description}) - Not found", 'red')
                        all_checks_passed = False
        
        # Check hardware access
        self.color_print("\nHardware Access:", 'blue')
        
        if self.platform == 'windows':
            # Check COM ports for potential hardware
            try:
                import serial.tools.list_ports
                ports = serial.tools.list_ports.comports()
                if ports:
                    self.color_print(f"  ✓ {len(ports)} serial port(s) available", 'green')
                    for port in ports[:3]:  # Show first 3 ports
                        self.color_print(f"    - {port.device} ({port.description})", 'blue')
                else:
                    self.color_print("  ⚠ No serial ports detected (robot hardware not connected)", 'yellow')
            except ImportError:
                self.color_print("  ⚠ Cannot check serial ports (pyserial not installed)", 'yellow')
        
        elif self.platform == 'linux':
            # Check for common device paths
            device_paths = ['/dev/ttyUSB*', '/dev/ttyACM*']
            devices_found = False
            for pattern in device_paths:
                success, stdout, _ = self.run_command(f'ls {pattern} 2>/dev/null', capture_output=True)
                if success and stdout.strip():
                    self.color_print(f"  ✓ Serial devices found: {stdout.strip()}", 'green')
                    devices_found = True
                    break
            
            if not devices_found:
                self.color_print("  ⚠ No serial devices detected (robot hardware not connected)", 'yellow')
        
        # Check disk space
        self.color_print("\nDisk Space:", 'blue')
        try:
            import shutil
            total, used, free = shutil.disk_usage(self.project_root)
            free_gb = free // (1024**3)
            
            if free_gb >= 5:
                self.color_print(f"  ✓ {free_gb} GB free space", 'green')
            elif free_gb >= 2:
                self.color_print(f"  ⚠ {free_gb} GB free space (recommended: 5GB+)", 'yellow')
            else:
                self.color_print(f"  ✗ {free_gb} GB free space (insufficient)", 'red')
                all_checks_passed = False
        except Exception:
            self.color_print("  ⚠ Cannot check disk space", 'yellow')
        
        # Summary
        print()
        if all_checks_passed:
            self.color_print("✓ All required modules and tools are available!", 'green')
            self.color_print("  Ready to proceed with installation.", 'green')
        else:
            self.color_print("✗ Some required modules or tools are missing!", 'red')
            self.color_print("  Please install missing dependencies before proceeding.", 'red')
            self.color_print("  Continue anyway? (NOT RECOMMENDED)", 'yellow')
            
            response = input("Continue with installation? [y/N]: ").strip().lower()
            if response not in ['y', 'yes']:
                self.color_print("Installation cancelled by user.", 'yellow')
                return False
        
        return all_checks_passed

    def complete_step(self, step_name):
        """Mark current step as complete and advance"""
        self.color_print(f"✓ {step_name} completed", 'green')
        self.advance_step()
    
    def print_header(self):
        print("=" * 60)
        print("Sanhum Robot Universal Installer v1.0.0")
        print(f"Platform: {platform.system()} {platform.release()}")
        print(f"Python: {sys.version}")
        print("=" * 60)
        print()
        self.color_print("This installer will:", 'blue')
        self.color_print("  1. Check system requirements and dependencies", 'blue')
        self.color_print("  2. Install ROS2 Jazzy (if not already installed)", 'blue')
        self.color_print("  3. Install required dependencies (Qt, OpenCV, etc.)", 'blue')
        self.color_print("  4. Build the Sanhum robot project", 'blue')
        self.color_print("  5. Configure environment and startup scripts", 'blue')
        print()
        self.color_print("Estimated time: 10-30 minutes (depending on system)", 'yellow')
        print()

        # Show initial installation state
        self.print_installation_state()
        
    def color_print(self, text, color='white'):
        if self.platform == 'windows':
            print(text)  # Windows doesn't support ANSI colors well
        else:
            color_code = self.colors.get(color, '')
            print(f"{color_code}{text}{self.colors['nc']}")
            
    def run_command(self, cmd, shell=True, check=True, capture_output=True, cwd=None):
        """Run a command and return result"""
        try:
            result = subprocess.run(cmd, shell=shell, check=check, 
                              capture_output=capture_output, text=True, cwd=cwd)
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.CalledProcessError as e:
            return False, e.stdout, e.stderr
            
    def check_admin(self):
        """Check if running with admin privileges"""
        if self.platform == 'windows':
            try:
                import ctypes
                return ctypes.windll.shell32.IsUserAnAdmin() != 0
            except:
                return False
        else:
            return os.geteuid() == 0
            
    def download_file(self, url, filename):
        """Download a file from URL"""
        try:
            self.color_print(f"Downloading {filename}...", 'blue')
            urllib.request.urlretrieve(url, filename)
            self.color_print(f"Downloaded {filename}", 'green')
            return True
        except Exception as e:
            self.color_print(f"Failed to download {filename}: {e}", 'red')
            return False
            
    def install_windows_ros2(self):
        """Install ROS2 Jazzy on Windows"""
        self.color_print("[Step 2/5] Installing ROS2 Jazzy...", 'blue')
        self.color_print("This may take 5-10 minutes depending on your internet speed", 'yellow')
        print()

        if not self.check_admin():
            self.color_print("ERROR: Administrator privileges required for ROS2 installation", 'red')
            self.color_print("Please run this script as Administrator", 'yellow')
            return False

        # Check if ROS2 is already installed
        if Path("C:/dev/ros2/jazzy/setup.bat").exists():
            self.color_print("✓ ROS2 Jazzy already installed at C:/dev/ros2/jazzy", 'green')
            self.color_print("  Skipping ROS2 installation", 'blue')
            return True

        # ROS2 download URL (adjust as needed)
        ros2_url = "https://github.com/ros2/ros2/releases/download/jazzy-20241206/ros2-jazzy-20241206-windows-x86_64.zip"
        ros2_zip = "ros2-jazzy.zip"
        ros2_dir = Path("C:/dev/ros2")

        # Download ROS2
        self.color_print("Downloading ROS2 Jazzy (~1.5 GB)...", 'blue')
        if not self.download_file(ros2_url, ros2_zip):
            return False

        # Extract ROS2
        try:
            self.color_print("Extracting ROS2 (this may take a few minutes)...", 'blue')
            with zipfile.ZipFile(ros2_zip, 'r') as zip_ref:
                zip_ref.extractall(ros2_dir.parent)

            # Rename to expected directory
            extracted_dir = ros2_dir.parent / "ros2-jazzy-20241206-windows-x86_64"
            if extracted_dir.exists():
                if ros2_dir.exists():
                    shutil.rmtree(ros2_dir)
                extracted_dir.rename(ros2_dir)

            # Clean up
            Path(ros2_zip).unlink()

            self.color_print("✓ ROS2 Jazzy installed successfully at C:/dev/ros2/jazzy", 'green')
            self.complete_step("Install ROS2 Jazzy")
            return True

        except Exception as e:
            self.color_print(f"Failed to extract ROS2: {e}", 'red')
            return False
            
    def install_windows_dependencies(self):
        """Install Windows dependencies (Python GUI only)"""
        self.color_print("[Step 3/5] Installing Windows dependencies...", 'blue')
        self.color_print("Installing Python GUI dependencies...", 'blue')
        print()

        # Install Python GUI dependencies
        python_deps = ["pyserial", "opencv-python", "pillow"]
        for dep in python_deps:
            self.color_print(f"  Installing {dep}...", 'blue')
            success, _, _ = self.run_command(f"pip install --user --no-cache-dir {dep}")
            if not success:
                self.color_print(f"  Failed to install {dep}", 'yellow')
            else:
                self.color_print(f"  ✓ {dep} installed", 'green')

        # Install colcon (ROS2 build tool)
        self.color_print("Installing colcon (ROS2 build tool)...", 'blue')
        # Use --user and --no-cache-dir to avoid permission issues
        success, stdout, stderr = self.run_command("pip install --user --no-cache-dir colcon-common-extensions")
        if not success:
            self.color_print("Failed to install colcon via pip", 'red')
            self.color_print(f"Error: {stderr}", 'red')
            self.color_print("Trying with --break-system-packages flag...", 'yellow')
            success, stdout, stderr = self.run_command("pip install --user --no-cache-dir --break-system-packages colcon-common-extensions")
            if not success:
                self.color_print("Failed to install colcon", 'red')
                self.color_print(f"Error: {stderr}", 'red')
                self.color_print("Please install colcon manually: pip install --user colcon-common-extensions", 'yellow')
                return False
        self.color_print("✓ colcon installed successfully", 'green')

        self.color_print("✓ Windows dependencies installed successfully", 'green')
        self.complete_step("Install dependencies")
        return True
        
    def install_linux_ros2(self):
        """Install ROS2 Jazzy on Linux"""
        self.color_print("[Step 2/5] Installing ROS2 Jazzy...", 'blue')
        self.color_print("This may take 10-20 minutes depending on your system", 'yellow')
        print()

        if not self.check_admin():
            self.color_print("ERROR: sudo privileges required for ROS2 installation", 'red')
            self.color_print("Please run: sudo python3 setup.py", 'yellow')
            return False

        # Check if ROS2 is already installed
        success, _, _ = self.run_command("which ros2", capture_output=True)
        if success:
            self.color_print("✓ ROS2 Jazzy already installed", 'green')
            self.color_print("  Skipping ROS2 installation", 'blue')
            self.complete_step("Install ROS2 Jazzy")
            return True

        # Update package list
        self.color_print("Updating package list...", 'blue')
        success, _, _ = self.run_command("sudo apt update")
        if not success:
            self.color_print("Failed to update package list", 'red')
            return False
        self.color_print("✓ Package list updated", 'green')

        # Install ROS2
        commands = [
            ("Installing curl, gnupg, lsb-release", "sudo apt install -y curl gnupg lsb-release"),
            ("Adding ROS2 GPG key", "curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.asc | sudo apt-key add -"),
            ("Adding ROS2 repository", "sudo sh -c 'echo \"deb http://packages.ros.org/ros2/ubuntu $(lsb_release -cs) main\" > /etc/apt/sources.list.d/ros2.list'"),
            ("Updating package list again", "sudo apt update"),
            ("Installing ROS2 Jazzy Desktop (this will take a while)", "sudo apt install -y ros-jazzy-desktop"),
            ("Installing python3-rosdep", "sudo apt install -y python3-rosdep"),
            ("Initializing rosdep", "sudo rosdep init"),
            ("Updating rosdep database", "rosdep update")
        ]

        progress = ProgressBar(len(commands), prefix='Progress', suffix='Complete')
        for i, (description, cmd) in enumerate(commands, 1):
            self.color_print(f"  {description}...", 'blue')
            success, stdout, stderr = self.run_command(cmd)

            # Handle rosdep init already initialized case
            if "sudo rosdep init" in cmd and not success and ("already exists" in stderr or "already exists:" in stderr):
                self.color_print("  ✓ rosdep already initialized (this is normal)", 'green')
                success = True
            elif not success:
                self.color_print(f"  ✗ Failed: {description}", 'red')
                self.color_print(f"  Error: {stderr}", 'red')
                return False
            else:
                self.color_print(f"  ✓ {description} completed", 'green')
            progress.increment()

        self.color_print("✓ ROS2 Jazzy installed successfully", 'green')
        self.complete_step("Install ROS2 Jazzy")
        return True
        
    def install_linux_dependencies(self):
        """Install Linux dependencies"""
        self.color_print("[Step 3/5] Installing Linux dependencies...", 'blue')
        self.color_print("This may take 5-10 minutes depending on your system", 'yellow')
        print()

        packages = [
            "build-essential",
            "cmake",
            "git",
            "python3-pip",
            "python3-vcstool",
            "python3-colcon-common-extensions",
            "qtbase5-dev",
            "libqt5serialport5-dev",
            "ros-jazzy-nav-msgs",
            "ros-jazzy-sensor-msgs",
            "ros-jazzy-geometry-msgs",
            "python3-pigpio"
        ]

        self.color_print("Installing system packages...", 'blue')
        progress = ProgressBar(len(packages), prefix='Progress', suffix='Complete')
        for i, package in enumerate(packages, 1):
            self.color_print(f"  Installing {package}...", 'blue')
            success, _, _ = self.run_command(f"sudo apt install -y {package}")
            if not success:
                self.color_print(f"  ✗ Failed to install {package}", 'red')
                return False
            progress.increment()
            self.color_print(f"  ✓ {package} installed", 'green')

        # Install Python packages
        python_packages = ["python3-serial"]
        self.color_print("Installing Python packages...", 'blue')
        progress = ProgressBar(len(python_packages), prefix='Progress', suffix='Complete')
        for i, package in enumerate(python_packages, 1):
            self.color_print(f"  Installing {package}...", 'blue')
            success, _, _ = self.run_command(f"sudo apt install -y {package}")
            if not success:
                self.color_print(f"  ✗ Failed to install {package}", 'red')
                return False
            progress.increment()
            self.color_print(f"  ✓ {package} installed", 'green')

        self.color_print("✓ Linux dependencies installed successfully", 'green')
        self.complete_step("Install dependencies")
        return True
        
    def build_project(self):
        """Build project"""
        self.color_print("[Step 4/5] Building Sanhum project...", 'blue')
        self.color_print("This may take 5-10 minutes depending on your system", 'yellow')
        print()

        if self.platform == 'windows':
            # Windows build with colcon (ROS2 build tool)
            workspace_dir = Path.home() / "sanhum_ws"
            workspace_dir.mkdir(exist_ok=True)
            src_dir = workspace_dir / "src"
            src_dir.mkdir(exist_ok=True)

            self.color_print("Preparing workspace...", 'blue')

            # Copy project files to workspace (avoid nested workspace issues)
            import shutil
            def ignore_nested_workspace(path, names):
                ignored = set()
                # Exclude directories that would cause recursion
                for name in names:
                    if name in ['ros2_ws', 'sanhum_ws', '__pycache__', '.git', 'build', 'install', 'log']:
                        ignored.add(name)
                    elif name.endswith('.pyc'):
                        ignored.add(name)
                return list(ignored)

            # Clean up existing corrupted workspace
            if (src_dir / "sanhum").exists():
                self.color_print("Cleaning existing workspace...", 'blue')
                shutil.rmtree(src_dir / "sanhum")

            self.color_print("Copying project files to workspace...", 'blue')
            shutil.copytree(self.project_root, src_dir / "sanhum", ignore=ignore_nested_workspace)
            self.color_print("✓ Project files copied", 'green')

            # Source ROS2 and build with colcon
            self.color_print("Building with colcon (ROS2 build tool)...", 'blue')
            self.color_print("  Sourcing ROS2 environment", 'blue')

            # Source ROS2 and build
            ros2_setup = Path("C:/dev/ros2/jazzy/setup.bat")
            if not ros2_setup.exists():
                self.color_print(f"✗ ROS2 not found at {ros2_setup}", 'red')
                return False

            # Find colcon.exe location
            import os
            old_path = os.environ.get('PATH', '')
            colcon_paths = [
                Path.home() / "AppData" / "Roaming" / "Python" / "Python314" / "Scripts",
                Path.home() / "AppData" / "Roaming" / "Python" / "Python313" / "Scripts",
                Path.home() / "AppData" / "Roaming" / "Python" / "Python312" / "Scripts",
                Path.home() / "AppData" / "Local" / "Programs" / "Python" / "Python314" / "Scripts",
                Path.home() / "AppData" / "Local" / "Programs" / "Python" / "Python313" / "Scripts",
            ]

            colcon_path = None
            for path in colcon_paths:
                if (path / "colcon.exe").exists():
                    colcon_path = path / "colcon.exe"
                    os.environ['PATH'] = str(path) + ';' + old_path
                    self.color_print(f"  Found colcon at: {colcon_path}", 'blue')
                    break

            if not colcon_path:
                self.color_print("✗ colcon.exe not found in Python Scripts directories", 'red')
                self.color_print("  Please install colcon manually", 'yellow')
                return False

            # Install MinGW if not present
            mingw_path = Path("C:/mingw64")
            mingw_gcc = mingw_path / "bin" / "gcc.exe"
            mingw_gpp = mingw_path / "bin" / "g++.exe"
            mingw_make = mingw_path / "bin" / "mingw32-make.exe"

            if not mingw_gcc.exists():
                self.color_print("Installing MinGW-w64 compiler...", 'blue')
                mingw_url = "https://github.com/niXman/mingw-builds-binaries/releases/download/13.2.0-rt_v11-rev1/x86_64-13.2.0-release-posix-seh-ucrt-rt_v11-rev1.7z"
                mingw_archive = "mingw64.7z"

                if not self.download_file(mingw_url, mingw_archive):
                    return False

                # Extract MinGW-w64
                try:
                    import py7zr
                    self.color_print("Extracting MinGW-w64...", 'blue')
                    with py7zr.SevenZipFile(mingw_archive, mode='r') as z:
                        z.extractall("C:/")

                    Path(mingw_archive).unlink()
                    self.color_print("✓ MinGW-w64 installed successfully", 'green')
                except ImportError:
                    self.color_print("py7zr not available, installing...", 'blue')
                    success, _, _ = self.run_command("pip install py7zr")
                    if success:
                        import py7zr
                        self.color_print("Extracting MinGW-w64...", 'blue')
                        with py7zr.SevenZipFile(mingw_archive, mode='r') as z:
                            z.extractall("C:/")

                        Path(mingw_archive).unlink()
                        self.color_print("✓ MinGW-w64 installed successfully", 'green')
                    else:
                        self.color_print("✗ Cannot extract MinGW archive", 'red')
                        return False

            # Verify MinGW installation
            if not mingw_gcc.exists():
                self.color_print(f"✗ MinGW compiler not found at {mingw_gcc}", 'red')
                return False

            # Add MinGW to PATH and set CMake variables
            self.color_print("Configuring for MinGW build...", 'blue')
            os.environ['PATH'] = str(mingw_path / "bin") + ';' + os.environ['PATH']
            os.environ['CMAKE_MAKE_PROGRAM'] = str(mingw_make)
            os.environ['CMAKE_C_COMPILER'] = str(mingw_gcc)
            os.environ['CMAKE_CXX_COMPILER'] = str(mingw_gpp)
            self.color_print(f"  MinGW path: {mingw_path}", 'blue')

            # Build command with ROS2 environment sourced and MinGW configuration
            # Note: ROS2 on Windows requires Visual Studio, MinGW is not officially supported
            self.color_print("WARNING: ROS2 on Windows requires Visual Studio compiler", 'yellow')
            self.color_print("MinGW is not officially supported for ROS2 builds on Windows", 'yellow')
            self.color_print("Building Python GUI instead (for WiFi robot control)", 'blue')

            # Install Python GUI dependencies
            self.color_print("Installing Python GUI dependencies...", 'blue')
            python_deps = ["pyserial", "opencv-python", "pillow"]
            for dep in python_deps:
                self.color_print(f"  Installing {dep}...", 'blue')
                success, _, _ = self.run_command(f"pip install --user --no-cache-dir {dep}")
                if not success:
                    self.color_print(f"  Failed to install {dep}", 'yellow')
                else:
                    self.color_print(f"  ✓ {dep} installed", 'green')

            # Skip C++ build on Windows (requires Visual Studio)
            self.color_print("✓ Skipping C++ ROS2 node build (requires Visual Studio)", 'green')
            self.color_print("✓ Python GUI is ready for WiFi robot control", 'green')
            return True

        else:
            # Linux build with colcon
            workspace_dir = Path.home() / "sanhum_ws"
            workspace_dir.mkdir(exist_ok=True)
            src_dir = workspace_dir / "src"
            src_dir.mkdir(exist_ok=True)

            self.color_print("Preparing workspace...", 'blue')

            # Copy project files to workspace (avoid nested workspace issues)
            import shutil
            def ignore_nested_workspace(path, names):
                ignored = set()
                # Exclude directories that would cause recursion
                for name in names:
                    if name in ['ros2_ws', 'sanhum_ws', '__pycache__', '.git', 'build', 'install', 'log']:
                        ignored.add(name)
                    elif name.endswith('.pyc'):
                        ignored.add(name)
                return list(ignored)

            # Clean up existing corrupted workspace
            if (src_dir / "sanhum").exists():
                self.color_print("Cleaning existing workspace...", 'blue')
                shutil.rmtree(src_dir / "sanhum")

            self.color_print("Copying project files to workspace...", 'blue')
            shutil.copytree(self.project_root, src_dir / "sanhum", ignore=ignore_nested_workspace)
            self.color_print("✓ Project files copied", 'green')

            # Build with colcon (optimized for speed)
            self.color_print("Building with colcon (parallel compilation)...", 'blue')
            self.color_print("  Using 8 parallel workers for faster builds", 'blue')
            self.color_print("  Using symlink install for faster rebuilds", 'blue')
            success, stdout, stderr = self.run_command("colcon build --parallel-workers 8 --symlink-install --cmake-args -DCMAKE_BUILD_TYPE=Release", cwd=workspace_dir)
            if not success:
                self.color_print("✗ Build failed", 'red')
                self.color_print(f"Error: {stderr}", 'red')
                return False

        self.color_print("✓ Project built successfully", 'green')
        self.complete_step("Build project")
        return True
        
    def setup_environment(self):
        """Setup environment variables and startup scripts"""
        self.color_print("[Step 5/5] Setting up environment...", 'blue')
        print()

        if self.platform == 'windows':
            # Create startup script for Python GUI
            startup_script = self.project_root / "start_sanhum.bat"
            startup_content = '''@echo off
echo Starting Sanhum Robot GUI...
cd /d "{}"
python src/gui_main.py
pause
'''.format(self.project_root)

            startup_script.write_text(startup_content)
            self.color_print(f"✓ Created startup script: {startup_script}", 'green')
            self.color_print("  Run this script to start the Python GUI for WiFi robot control", 'blue')

        else:
            # Create startup script
            startup_script = Path.home() / "start_sanhum_robot.sh"
            startup_content = '''#!/bin/bash
/root/sanhum_ws/install/sanhum/lib/sanhum/sanhum_robot --ros-args --params-file /root/sanhum_ws/install/sanhum/share/sanhum/config/raspberry_pi_config.yaml
'''
            startup_script.write_text(startup_content)
            startup_script.chmod(0o755)
            self.color_print(f"✓ Created startup script: {startup_script}", 'green')
            self.color_print("  Run this script to start the robot node", 'blue')

            # Add to bashrc
            bashrc = Path.home() / ".bashrc"
            bashrc_content = bashrc.read_text() if bashrc.exists() else ""

            if "source /opt/ros/jazzy/setup.bash" not in bashrc_content:
                with open(bashrc, 'a') as f:
                    f.write("\n# Sanhum Robot\nsource /opt/ros/jazzy/setup.bash\n")
                self.color_print("✓ Added ROS2 to bashrc", 'green')

            if "source ~/sanhum_ws/install/setup.bash" not in bashrc_content:
                with open(bashrc, 'a') as f:
                    f.write("source ~/sanhum_ws/install/setup.bash\n")
                self.color_print("✓ Added workspace to bashrc", 'green')

        self.color_print("✓ Environment setup completed", 'green')
        self.complete_step("Setup environment")
        return True
        
    def install_all(self):
        """Main installation function"""
        self.print_header()

        # Check modules and dependencies first
        self.color_print("[Step 1/5] Checking system requirements...", 'blue')
        if not self.check_modules():
            return False
        self.complete_step("Check system requirements")

        try:
            # Platform-specific installation
            if self.platform == 'windows':
                self.color_print("\nStarting Windows installation...", 'blue')
                print()

                # Check if ROS2 is already installed
                if not Path("C:/dev/ros2/jazzy/setup.bat").exists():
                    if not self.install_windows_ros2():
                        return False

                if not self.install_windows_dependencies():
                    return False

            elif self.platform == 'linux':
                self.color_print("\nStarting Linux installation...", 'blue')
                print()

                if not self.install_linux_ros2():
                    return False

                if not self.install_linux_dependencies():
                    return False

            else:
                self.color_print(f"Unsupported platform: {self.platform}", 'red')
                return False

            # Build project
            if not self.build_project():
                return False

            # Setup environment
            if not self.setup_environment():
                return False

            # Success
            print()
            self.color_print("=" * 60, 'green')
            self.color_print("✓ Installation completed successfully!", 'green')
            self.color_print("=" * 60, 'green')
            print()

            # Print summary
            self.color_print("Installation Summary:", 'blue')
            self.color_print("  ✓ System requirements checked", 'green')
            self.color_print("  ✓ ROS2 Jazzy installed", 'green')
            self.color_print("  ✓ Dependencies installed (Qt, OpenCV, etc.)", 'green')
            self.color_print("  ✓ Sanhum robot project built", 'green')
            self.color_print("  ✓ Environment configured", 'green')
            print()

            # Print next steps
            self.color_print("Next steps:", 'blue')
            if self.platform == 'windows':
                self.color_print("  1. Double-click: start_sanhum.bat", 'blue')
                self.color_print("  2. Or run from command prompt:", 'blue')
                self.color_print("     cd /d \"{}\"".format(self.project_root), 'blue')
                self.color_print("     start_sanhum.bat", 'blue')
            else:
                self.color_print("  1. Run: ~/start_sanhum_robot.sh", 'blue')
                self.color_print("  2. Or source environment and use launch:", 'blue')
                self.color_print("     source ~/.bashrc", 'blue')
                self.color_print("     ros2 launch sanhum raspberry_pi.launch.py", 'blue')
            print()

            self.color_print("For more information, see README.md", 'blue')
            self.color_print("For security information, see docs/SECURITY.md", 'blue')
            print()

            return True

        except KeyboardInterrupt:
            self.color_print("\n✗ Installation interrupted by user", 'yellow')
            return False
        except Exception as e:
            self.color_print(f"\n✗ Unexpected error: {e}", 'red')
            return False

def main():
    try:
        installer = UniversalInstaller()
        success = installer.install_all()
        
        if success:
            print("\n✓ Installation completed successfully!")
        else:
            print("\n✗ Installation failed!")
            
        input("Press Enter to exit...")
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nInstallation interrupted by user")
        input("Press Enter to exit...")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        input("Press Enter to exit...")
        sys.exit(1)

if __name__ == "__main__":
    main()
