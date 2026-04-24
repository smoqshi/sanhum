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
from pathlib import Path

class UniversalInstaller:
    def __init__(self):
        self.platform = platform.system().lower()
        self.script_dir = Path(__file__).parent
        self.project_root = self.script_dir.parent
        
        # Colors for output
        self.colors = {
            'red': '\033[0;31m',
            'green': '\033[0;32m',
            'yellow': '\033[1;33m',
            'blue': '\033[0;34m',
            'nc': '\033[0m'  # No Color
        }
        
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
                'cl': 'Visual Studio compiler',
                'vcpkg': 'Package manager'
            }
            
            for tool, description in system_tools.items():
                if tool == 'cl':
                    # Check for Visual Studio compiler
                    success, _, _ = self.run_command('where cl', capture_output=True)
                    if success and 'cl.exe' in _:
                        self.color_print(f"  ✓ {tool} ({description})", 'green')
                    else:
                        self.color_print(f"  ⚠ {tool} ({description}) - Visual Studio not found", 'yellow')
                        self.color_print("    Note: Will install with MinGW-w64 as alternative", 'blue')
                        self.color_print("    Or install Visual Studio 2019+ with C++ tools", 'blue')
                        # Don't fail for missing cl - we can use alternative compiler
                elif tool == 'vcpkg':
                    vcpkg_path = Path("C:/vcpkg/vcpkg.exe")
                    if vcpkg_path.exists():
                        self.color_print(f"  ✓ {tool} ({description})", 'green')
                    else:
                        self.color_print(f"  ⚠ {tool} ({description}) - Will be installed", 'yellow')
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
    
    def print_header(self):
        print("=" * 60)
        print("Sanhum Robot Universal Installer")
        print(f"Platform: {platform.system()} {platform.release()}")
        print(f"Python: {sys.version}")
        print("=" * 60)
        print()
        
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
        self.color_print("[Windows] Installing ROS2 Jazzy...", 'blue')
        
        if not self.check_admin():
            self.color_print("ERROR: Administrator privileges required for ROS2 installation", 'red')
            self.color_print("Please run this script as Administrator", 'yellow')
            return False
            
        # ROS2 download URL (adjust as needed)
        ros2_url = "https://github.com/ros2/ros2/releases/download/jazzy-20241206/ros2-jazzy-20241206-windows-x86_64.zip"
        ros2_zip = "ros2-jazzy.zip"
        ros2_dir = Path("C:/dev/ros2")
        
        # Download ROS2
        if not self.download_file(ros2_url, ros2_zip):
            return False
            
        # Extract ROS2
        try:
            self.color_print("Extracting ROS2...", 'blue')
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
            
            self.color_print("ROS2 installed successfully", 'green')
            return True
            
        except Exception as e:
            self.color_print(f"Failed to extract ROS2: {e}", 'red')
            return False
            
    def install_windows_dependencies(self):
        """Install Windows dependencies (vcpkg, Qt, OpenCV)"""
        self.color_print("[Windows] Installing dependencies...", 'blue')
        
        # Install vcpkg
        vcpkg_dir = Path("C:/vcpkg")
        if not vcpkg_dir.exists():
            self.color_print("Installing vcpkg...", 'blue')
            success, _, _ = self.run_command("git clone https://github.com/Microsoft/vcpkg.git C:/vcpkg")
            if not success:
                self.color_print("Failed to clone vcpkg", 'red')
                return False
                
            # Bootstrap vcpkg
            success, _, _ = self.run_command("cd C:/vcpkg && bootstrap-vcpkg.bat")
            if not success:
                self.color_print("Failed to bootstrap vcpkg", 'red')
                return False
                
        # Clean up any existing vcpkg locks
        self.color_print("Cleaning up vcpkg locks...", 'blue')
        lock_files = [
            "C:/vcpkg/installed/vcpkg/vcpkg-running.lock",
            "C:/vcpkg/buildtrees/vcpkg-running.lock"
        ]
        
        for lock_file in lock_files:
            lock_path = Path(lock_file)
            if lock_path.exists():
                try:
                    lock_path.unlink()
                    self.color_print(f"Removed lock: {lock_file}", 'yellow')
                except Exception as e:
                    self.color_print(f"Could not remove lock {lock_file}: {e}", 'yellow')
        
        # Install packages with vcpkg
        packages = [
            "opencv4[core,contrib]:x64-windows",
            "qt6:x64-windows"
        ]
        
        for package in packages:
            self.color_print(f"Installing {package}...", 'blue')
            success, stdout, stderr = self.run_command(f"C:/vcpkg/vcpkg.exe install {package}")
            if not success:
                if "vcpkg-running.lock" in stderr:
                    self.color_print(f"vcpkg is busy. Please wait and try again.", 'yellow')
                    self.color_print("Or close any other vcpkg processes.", 'yellow')
                    return False
                else:
                    self.color_print(f"Failed to install {package}", 'red')
                    self.color_print(f"Error: {stderr}", 'red')
                    return False
                
        # Integrate with Visual Studio
        self.color_print("Integrating vcpkg with Visual Studio...", 'blue')
        success, _, _ = self.run_command("C:/vcpkg/vcpkg.exe integrate install")
        
        self.color_print("Windows dependencies installed successfully", 'green')
        return True
        
    def install_linux_ros2(self):
        """Install ROS2 Jazzy on Linux"""
        self.color_print("[Linux] Installing ROS2 Jazzy...", 'blue')
        
        if not self.check_admin():
            self.color_print("ERROR: sudo privileges required for ROS2 installation", 'red')
            self.color_print("Please run: sudo python3 install_all.py", 'yellow')
            return False
            
        # Update package list
        self.color_print("Updating package list...", 'blue')
        success, _, _ = self.run_command("sudo apt update")
        if not success:
            self.color_print("Failed to update package list", 'red')
            return False
            
        # Install ROS2
        commands = [
            "sudo apt install -y curl gnupg lsb-release",
            "curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.asc | sudo apt-key add -",
            "sudo sh -c 'echo \"deb http://packages.ros.org/ros2/ubuntu $(lsb_release -cs) main\" > /etc/apt/sources.list.d/ros2.list'",
            "sudo apt update",
            "sudo apt install -y ros-jazzy-desktop",
            "sudo apt install -y python3-rosdep",
            "sudo rosdep init",
            "rosdep update"
        ]
        
        for cmd in commands:
            self.color_print(f"Running: {cmd}", 'blue')
            success, stdout, stderr = self.run_command(cmd)
            
            # Handle rosdep init already initialized case
            if "sudo rosdep init" in cmd and not success and ("already exists" in stderr or "already exists:" in stderr):
                self.color_print("rosdep already initialized (this is normal)", 'green')
                success = True
            elif not success:
                self.color_print(f"Failed: {cmd}", 'red')
                self.color_print(f"Error: {stderr}", 'red')
                return False
                
        self.color_print("ROS2 installed successfully", 'green')
        return True
        
    def install_linux_dependencies(self):
        """Install Linux dependencies"""
        self.color_print("[Linux] Installing dependencies...", 'blue')
        
        packages = [
            "build-essential",
            "cmake",
            "git",
            "python3-pip",
            "python3-vcstool",
            "python3-colcon-common-extensions",
            "libqt5-dev",
            "qtbase5-dev",
            "libqt5serialport5-dev",
            "libopencv-dev",
            "ros-jazzy-nav-msgs",
            "ros-jazzy-vision-msgs",
            "ros-jazzy-sensor-msgs",
            "ros-jazzy-geometry-msgs"
        ]
        
        for package in packages:
            self.color_print(f"Installing {package}...", 'blue')
            success, _, _ = self.run_command(f"sudo apt install -y {package}")
            if not success:
                self.color_print(f"Failed to install {package}", 'red')
                return False
                
        # Install Python packages
        python_packages = ["python3-serial"]
        for package in python_packages:
            self.color_print(f"Installing Python package {package}...", 'blue')
            success, _, _ = self.run_command(f"sudo apt install -y {package}")
            if not success:
                self.color_print(f"Failed to install {package}", 'red')
                return False
                
        self.color_print("Linux dependencies installed successfully", 'green')
        return True
        
    def build_project(self):
        """Build project"""
        self.color_print("Building Sanhum project...", 'blue')
        
        if self.platform == 'windows':
            # Windows build with CMake
            build_dir = self.project_root / "build"
            build_dir.mkdir(exist_ok=True)
            
            # Check for Visual Studio compiler first
            has_cl, _, _ = self.run_command('where cl', capture_output=True)
            has_cl = has_cl and 'cl.exe' in _
            
            if has_cl:
                # Use Visual Studio toolchain
                cmake_cmd = f'cmake .. -A x64 -DCMAKE_TOOLCHAIN_FILE="C:/vcpkg/scripts/buildsystems/vcpkg.cmake"'
                self.color_print("Using Visual Studio compiler...", 'blue')
            else:
                # Use MinGW-w64 as alternative
                mingw_path = Path("C:/mingw64")
                if not mingw_path.exists():
                    self.color_print("Installing MinGW-w64 compiler...", 'blue')
                    # Download and install MinGW-w64
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
                        
                        # Clean up
                        Path(mingw_archive).unlink()
                        self.color_print("MinGW-w64 installed successfully", 'green')
                    except ImportError:
                        self.color_print("py7zr not available, skipping MinGW installation", 'yellow')
                        self.color_print("Please install MinGW-w64 manually from https://www.mingw-w64.org/", 'yellow')
                
                # Use MinGW toolchain
                cmake_cmd = f'cmake .. -G "MinGW Makefiles" -DCMAKE_C_COMPILER=C:/mingw64/bin/gcc.exe -DCMAKE_CXX_COMPILER=C:/mingw64/bin/g++.exe -DCMAKE_TOOLCHAIN_FILE="C:/vcpkg/scripts/buildsystems/vcpkg.cmake"'
                self.color_print("Using MinGW-w64 compiler...", 'blue')
            
            # Configure CMake
            success, stdout, stderr = self.run_command(cmake_cmd, cwd=build_dir)
            if not success:
                self.color_print("CMake configuration failed", 'red')
                self.color_print(f"Error: {stderr}", 'red')
                return False
                
            # Build
            if has_cl:
                build_cmd = "cmake --build . --config Release"
            else:
                build_cmd = "cmake --build . --config Release -- -j4"
                
            success, stdout, stderr = self.run_command(build_cmd, cwd=build_dir)
            if not success:
                self.color_print("Build failed", 'red')
                self.color_print(f"Error: {stderr}", 'red')
                return False
                
        else:
            # Linux build with colcon
            workspace_dir = Path.home() / "sanhum_ws"
            workspace_dir.mkdir(exist_ok=True)
            src_dir = workspace_dir / "src"
            src_dir.mkdir(exist_ok=True)
            
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
                shutil.rmtree(src_dir / "sanhum")
                
            shutil.copytree(self.project_root, src_dir / "sanhum", ignore=ignore_nested_workspace)
                
            # Build with colcon (optimized for speed)
            self.color_print("Building with parallel compilation (this may take a few minutes)...", 'blue')
            self.color_print("Using symlink install for faster builds...", 'blue')
            success, stdout, stderr = self.run_command("colcon build --parallel-workers 8 --symlink-install --cmake-args -DCMAKE_BUILD_TYPE=Release", cwd=workspace_dir)
            if not success:
                self.color_print("Build failed", 'red')
                self.color_print(f"Error: {stderr}", 'red')
                return False
                
        self.color_print("Project built successfully", 'green')
        return True
        
    def setup_environment(self):
        """Setup environment variables and startup scripts"""
        self.color_print("Setting up environment...", 'blue')
        
        if self.platform == 'windows':
            # Create startup script
            startup_script = self.project_root / "start_sanhum.bat"
            startup_content = '''@echo off
call C:/dev/ros2/jazzy/setup.bat
cd /d "{}"
ros2 launch sanhum main.launch.py
'''.format(self.project_root / "build")
            
            startup_script.write_text(startup_content)
            self.color_print(f"Created startup script: {startup_script}", 'green')
            
        else:
            # Create startup script
            startup_script = Path.home() / "start_sanhum_robot.sh"
            startup_content = '''#!/bin/bash
source /opt/ros/jazzy/setup.bash
source ~/sanhum_ws/install/setup.bash
ros2 launch sanhum raspberry_pi.launch.py
'''
            startup_script.write_text(startup_content)
            startup_script.chmod(0o755)
            self.color_print(f"Created startup script: {startup_script}", 'green')
            
            # Add to bashrc
            bashrc = Path.home() / ".bashrc"
            bashrc_content = bashrc.read_text() if bashrc.exists() else ""
            
            if "source /opt/ros/jazzy/setup.bash" not in bashrc_content:
                with open(bashrc, 'a') as f:
                    f.write("\n# Sanhum Robot\nsource /opt/ros/jazzy/setup.bash\n")
                self.color_print("Added ROS2 to bashrc", 'green')
                
            if "source ~/sanhum_ws/install/setup.bash" not in bashrc_content:
                with open(bashrc, 'a') as f:
                    f.write("source ~/sanhum_ws/install/setup.bash\n")
                self.color_print("Added workspace to bashrc", 'green')
                
        self.color_print("Environment setup completed", 'green')
        return True
        
    def install_all(self):
        """Main installation function"""
        self.print_header()
        
        # Check modules and dependencies first
        if not self.check_modules():
            return False
        
        try:
            # Platform-specific installation
            if self.platform == 'windows':
                self.color_print("Starting Windows installation...", 'blue')
                
                # Check if ROS2 is already installed
                if not Path("C:/dev/ros2/jazzy/setup.bat").exists():
                    if not self.install_windows_ros2():
                        return False
                        
                if not self.install_windows_dependencies():
                    return False
                    
            elif self.platform == 'linux':
                self.color_print("Starting Linux installation...", 'blue')
                
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
            self.color_print("\n" + "=" * 60, 'green')
            self.color_print("Installation completed successfully!", 'green')
            self.color_print("=" * 60, 'green')
            
            # Print next steps
            self.color_print("\nNext steps:", 'blue')
            if self.platform == 'windows':
                self.color_print("  Run: start_sanhum.bat", 'blue')
            else:
                self.color_print("  Run: ~/start_sanhum_robot.sh", 'blue')
                self.color_print("  Or: source ~/.bashrc && ros2 launch sanhum raspberry_pi.launch.py", 'blue')
                
            return True
            
        except KeyboardInterrupt:
            self.color_print("\nInstallation interrupted by user", 'yellow')
            return False
        except Exception as e:
            self.color_print(f"Unexpected error: {e}", 'red')
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
