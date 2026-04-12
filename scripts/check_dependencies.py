#!/usr/bin/env python3
"""
Sanhum Robot Dependency Checker
Checks if all required dependencies are installed for Windows and Raspberry Pi
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

class DependencyChecker:
    def __init__(self):
        self.platform = platform.system().lower()
        self.errors = []
        self.warnings = []
        
    def print_header(self):
        print("=" * 50)
        print("Sanhum Robot Dependency Checker")
        print(f"Platform: {platform.system()} {platform.release()}")
        print("=" * 50)
        print()
        
    def print_results(self):
        print("\n" + "=" * 50)
        print("Check Results:")
        print("=" * 50)
        
        if self.errors:
            print(f"\n{len(self.errors)} Errors found:")
            for error in self.errors:
                print(f"  [ERROR] {error}")
                
        if self.warnings:
            print(f"\n{len(self.warnings)} Warnings:")
            for warning in self.warnings:
                print(f"  [WARN] {warning}")
                
        if not self.errors and not self.warnings:
            print("\n[SUCCESS] All dependencies are satisfied!")
        else:
            print(f"\nStatus: {len(self.errors)} errors, {len(self.warnings)} warnings")
            
    def check_command_exists(self, command, description):
        """Check if a command exists in PATH"""
        try:
            result = subprocess.run(['which' if self.platform != 'windows' else 'where', command], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print(f"[OK] {description}")
                return True
            else:
                self.errors.append(f"{description} - command '{command}' not found")
                return False
        except Exception as e:
            self.errors.append(f"{description} - failed to check: {e}")
            return False
            
    def check_python_package(self, package, description):
        """Check if a Python package is installed"""
        try:
            __import__(package)
            print(f"[OK] {description}")
            return True
        except ImportError:
            self.errors.append(f"{description} - Python package '{package}' not installed")
            return False
            
    def check_file_exists(self, filepath, description):
        """Check if a file exists"""
        if os.path.exists(filepath):
            print(f"[OK] {description}")
            return True
        else:
            self.errors.append(f"{description} - file not found: {filepath}")
            return False
            
    def check_directory_exists(self, dirpath, description):
        """Check if a directory exists"""
        if os.path.isdir(dirpath):
            print(f"[OK] {description}")
            return True
        else:
            self.errors.append(f"{description} - directory not found: {dirpath}")
            return False
            
    def check_ros2_windows(self):
        """Check ROS2 installation on Windows"""
        print("\n--- ROS2 Windows Check ---")
        
        # Check ROS2 installation directory
        ros2_paths = [
            r"C:\dev\ros2\jazzy\setup.bat",
            r"C:\ros2\jazzy\setup.bat",
            r"C:\opt\ros\jazzy\setup.bat"
        ]
        
        ros2_found = False
        for path in ros2_paths:
            if os.path.exists(path):
                print(f"[OK] ROS2 Jazzy found at {path}")
                ros2_found = True
                break
                
        if not ros2_found:
            self.errors.append("ROS2 Jazzy installation not found")
            return
            
        # Check ROS2 commands
        self.check_command_exists("ros2", "ROS2 CLI")
        self.check_command_exists("ros2daemon", "ROS2 Daemon")
        self.check_command_exists("ros2run", "ROS2 Run")
        
    def check_ros2_linux(self):
        """Check ROS2 installation on Linux"""
        print("\n--- ROS2 Linux Check ---")
        
        # Check ROS2 installation
        if not os.path.exists("/opt/ros/jazzy"):
            self.errors.append("ROS2 Jazzy not found in /opt/ros/jazzy")
            return
            
        print("[OK] ROS2 Jazzy found in /opt/ros/jazzy")
        
        # Check ROS2 commands
        self.check_command_exists("ros2", "ROS2 CLI")
        self.check_command_exists("ros2daemon", "ROS2 Daemon")
        self.check_command_exists("ros2run", "ROS2 Run")
        self.check_command_exists("colcon", "Colcon build tool")
        
    def check_windows_dependencies(self):
        """Check Windows-specific dependencies"""
        print("\n--- Windows Dependencies ---")
        
        # Check Visual Studio
        self.check_command_exists("cl", "Visual Studio C++ compiler")
        
        # Check CMake
        self.check_command_exists("cmake", "CMake")
        
        # Check vcpkg
        vcpkg_paths = [
            r"C:\vcpkg\vcpkg.exe",
            r"C:\tools\vcpkg\vcpkg.exe"
        ]
        
        vcpkg_found = False
        for path in vcpkg_paths:
            if os.path.exists(path):
                print(f"[OK] vcpkg found at {path}")
                vcpkg_found = True
                break
                
        if not vcpkg_found:
            self.warnings.append("vcpkg not found - may be installed elsewhere")
            
        # Check Qt6
        try:
            import PyQt6
            print("[OK] PyQt6 found")
        except ImportError:
            try:
                import PySide6
                print("[OK] PySide6 found")
            except ImportError:
                self.warnings.append("Qt6 Python bindings not found")
                
        # Check OpenCV
        self.check_python_package("cv2", "OpenCV Python bindings")
        
    def check_linux_dependencies(self):
        """Check Linux/Raspberry Pi dependencies"""
        print("\n--- Linux Dependencies ---")
        
        # Check build tools
        self.check_command_exists("gcc", "GCC compiler")
        self.check_command_exists("g++", "G++ compiler")
        self.check_command_exists("cmake", "CMake")
        self.check_command_exists("make", "Make")
        
        # Check Python
        self.check_command_exists("python3", "Python 3")
        self.check_command_exists("pip3", "pip3")
        
        # Check Python packages
        self.check_python_package("serial", "PySerial")
        
        # Check serial port access
        if os.path.exists("/dev/ttyUSB0") or os.path.exists("/dev/ttyACM0"):
            print("[OK] Serial ports available")
        else:
            self.warnings.append("No serial ports found - ESP32/Arduino may not be connected")
            
        # Check GPIO access (Raspberry Pi specific)
        if os.path.exists("/usr/bin/vcgencmd"):
            print("[OK] Raspberry Pi tools available")
        else:
            self.warnings.append("Not running on Raspberry Pi or vcgencmd not available")
            
    def check_project_structure(self):
        """Check project files and structure"""
        print("\n--- Project Structure Check ---")
        
        # Get project root
        script_dir = Path(__file__).parent
        project_root = script_dir.parent
        
        # Check essential files
        essential_files = [
            "CMakeLists.txt",
            "package.xml",
            "src/gui_main.cpp",
            "src/robot_main.cpp",
            "src/main_window.cpp",
            "src/motor_driver.cpp",
            "src/esp32_driver.cpp",
            "src/arduino_sensors.cpp"
        ]
        
        for file_path in essential_files:
            full_path = project_root / file_path
            self.check_file_exists(str(full_path), f"Project file: {file_path}")
            
        # Check directories
        essential_dirs = [
            "src",
            "include",
            "launch",
            "config"
        ]
        
        for dir_path in essential_dirs:
            full_path = project_root / dir_path
            self.check_directory_exists(str(full_path), f"Project directory: {dir_path}")
            
        # Check config files
        config_files = [
            "config/raspberry_pi_config.yaml",
            "config/robot_params.yaml"
        ]
        
        for file_path in config_files:
            full_path = project_root / file_path
            self.check_file_exists(str(full_path), f"Config file: {file_path}")
            
    def check_build_artifacts(self):
        """Check if project has been built"""
        print("\n--- Build Artifacts Check ---")
        
        script_dir = Path(__file__).parent
        project_root = script_dir.parent
        
        if self.platform == "windows":
            build_dir = project_root / "build" / "Release"
            exe_name = "sanhum_gui.exe"
        else:
            build_dir = project_root / "build" / "sanhum"
            exe_name = "sanhum_robot"
            
        exe_path = build_dir / exe_name
        
        if exe_path.exists():
            print(f"[OK] Build artifact found: {exe_path}")
        else:
            self.warnings.append(f"Build artifact not found: {exe_path}")
            
    def run_checks(self):
        """Run all dependency checks"""
        self.print_header()
        
        # Check project structure
        self.check_project_structure()
        
        # Platform-specific checks
        if self.platform == "windows":
            self.check_ros2_windows()
            self.check_windows_dependencies()
        elif self.platform == "linux":
            self.check_ros2_linux()
            self.check_linux_dependencies()
        else:
            self.errors.append(f"Unsupported platform: {self.platform}")
            
        # Check build artifacts
        self.check_build_artifacts()
        
        # Print results
        self.print_results()
        
        # Return exit code
        return 1 if self.errors else 0

def main():
    checker = DependencyChecker()
    exit_code = checker.run_checks()
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
