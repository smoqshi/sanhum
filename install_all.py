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
            
    def run_command(self, cmd, shell=True, check=True, capture_output=True):
        """Run a command and return result"""
        try:
            result = subprocess.run(cmd, shell=shell, check=check, 
                              capture_output=capture_output, text=True)
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
                
        # Install packages with vcpkg
        packages = [
            "opencv4[core,contrib]:x64-windows",
            "qt6:x64-windows"
        ]
        
        for package in packages:
            self.color_print(f"Installing {package}...", 'blue')
            success, stdout, stderr = self.run_command(f"C:/vcpkg/vcpkg.exe install {package}")
            if not success:
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
            if not success:
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
            "python3-colcon-common-extensions"
        ]
        
        for package in packages:
            self.color_print(f"Installing {package}...", 'blue')
            success, _, _ = self.run_command(f"sudo apt install -y {package}")
            if not success:
                self.color_print(f"Failed to install {package}", 'red')
                return False
                
        # Install Python packages
        python_packages = ["pyserial"]
        for package in python_packages:
            self.color_print(f"Installing Python package {package}...", 'blue')
            success, _, _ = self.run_command(f"pip3 install {package}")
            if not success:
                self.color_print(f"Failed to install {package}", 'red')
                return False
                
        self.color_print("Linux dependencies installed successfully", 'green')
        return True
        
    def build_project(self):
        """Build the project"""
        self.color_print("Building Sanhum project...", 'blue')
        
        if self.platform == 'windows':
            # Windows build with CMake
            build_dir = self.project_root / "build"
            build_dir.mkdir(exist_ok=True)
            
            # Configure CMake
            cmake_cmd = f'cmake .. -A x64 -DCMAKE_TOOLCHAIN_FILE="C:/vcpkg/scripts/buildsystems/vcpkg.cmake"'
            success, stdout, stderr = self.run_command(cmake_cmd, cwd=build_dir)
            if not success:
                self.color_print("CMake configuration failed", 'red')
                self.color_print(f"Error: {stderr}", 'red')
                return False
                
            # Build
            success, stdout, stderr = self.run_command("cmake --build . --config Release", cwd=build_dir)
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
            
            # Create symlink if not exists
            project_link = src_dir / "sanhum"
            if not project_link.exists():
                project_link.symlink_to(self.project_root)
                
            # Build with colcon
            success, stdout, stderr = self.run_command("colcon build --packages-select sanhum", cwd=workspace_dir)
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
