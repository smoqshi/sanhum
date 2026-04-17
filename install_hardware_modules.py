#!/usr/bin/env python3
"""
Hardware Module Installation Script for Sanhum Robot
Installs required modules for Raspberry Pi 5 GPIO and hardware integration
"""

import subprocess
import sys
import platform
from pathlib import Path

class HardwareModuleInstaller:
    def __init__(self):
        self.platform = platform.system().lower()
        self.python_version = sys.version_info
        
    def print_header(self):
        print("=" * 60)
        print("Sanhum Robot - Hardware Module Installation")
        print(f"Platform: {platform.system()} {platform.release()}")
        print(f"Python: {sys.version}")
        print("=" * 60)
        print()
        
    def run_command(self, cmd, description=""):
        """Run a command and handle errors"""
        print(f"Installing {description}...")
        try:
            result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
            print(f"  {description} installed successfully")
            return True
        except subprocess.CalledProcessError as e:
            print(f"  Failed to install {description}: {e}")
            print(f"  Error: {e.stderr}")
            return False
            
    def install_pip_packages(self):
        """Install required pip packages"""
        packages = [
            ('RPi.GPIO', 'Raspberry Pi GPIO library'),
            ('pigpio', 'Advanced GPIO control'),
            ('pyserial', 'Serial communication'),
            ('opencv-python', 'OpenCV computer vision'),
            ('numpy', 'Numerical computing'),
            ('rclpy', 'ROS2 Python client'),
            ('geometry-msgs', 'ROS2 geometry messages'),
            ('sensor-msgs', 'ROS2 sensor messages'),
            ('std-msgs', 'ROS2 standard messages'),
            ('pygame', 'Gamepad support'),
            ('Pillow', 'Image processing')
        ]
        
        print("Installing Python packages...")
        success_count = 0
        
        for package, description in packages:
            if self.run_command(f"pip install {package}", description):
                success_count += 1
        
        print(f"Successfully installed {success_count}/{len(packages)} packages")
        return success_count == len(packages)
        
    def setup_pigpio_daemon(self):
        """Setup pigpio daemon for Raspberry Pi"""
        if self.platform != 'linux':
            print("Skipping pigpio daemon setup (not on Linux)")
            return True
            
        print("Setting up pigpio daemon...")
        
        # Check if pigpio daemon is running
        try:
            result = subprocess.run("pgrep pigpiod", shell=True, capture_output=True)
            if result.returncode == 0:
                print("  pigpio daemon is already running")
                return True
        except:
            pass
        
        # Try to start pigpio daemon
        try:
            subprocess.run("sudo pigpiod", shell=True, check=True)
            print("  pigpio daemon started successfully")
            return True
        except subprocess.CalledProcessError:
            print("  Failed to start pigpio daemon")
            print("  Try running: sudo pigpiod")
            return False
            
    def setup_gpio_permissions(self):
        """Setup GPIO permissions for Raspberry Pi"""
        if self.platform != 'linux':
            print("Skipping GPIO permissions setup (not on Linux)")
            return True
            
        print("Setting up GPIO permissions...")
        
        # Add user to gpio group
        try:
            import getpass
            username = getpass.getuser()
            
            # Check if user is in gpio group
            result = subprocess.run(f"groups {username}", shell=True, capture_output=True, text=True)
            if 'gpio' not in result.stdout:
                print(f"  Adding {username} to gpio group...")
                subprocess.run(f"sudo usermod -a -G gpio {username}", shell=True, check=True)
                print(f"  Added {username} to gpio group")
                print("  Please log out and log back in for group changes to take effect")
            else:
                print(f"  User {username} is already in gpio group")
                
            return True
        except subprocess.CalledProcessError as e:
            print(f"  Failed to setup GPIO permissions: {e}")
            return False
            
    def setup_udev_rules(self):
        """Setup udev rules for serial devices"""
        if self.platform != 'linux':
            print("Skipping udev rules setup (not on Linux)")
            return True
            
        print("Setting up udev rules for serial devices...")
        
        udev_rule = """# Sanhum Robot USB Serial Devices
SUBSYSTEM=="tty", ATTRS{idVendor}=="1a86", ATTRS{idProduct}=="7523", MODE="0666", GROUP="dialout", SYMLINK+="sanhum_arduino%n"
SUBSYSTEM=="tty", ATTRS{idVendor}=="10c4", ATTRS{idProduct}=="ea60", MODE="0666", GROUP="dialout", SYMLINK+="sanhum_esp32%n"
SUBSYSTEM=="tty", ATTRS{idVendor}=="0403", ATTRS{idProduct}=="6001", MODE="0666", GROUP="dialout", SYMLINK+="sanhum_ftdi%n"
"""
        
        try:
            udev_file = Path("/etc/udev/rules.d/99-sanhum-robot.rules")
            
            # Check if file already exists
            if not udev_file.exists():
                # Write udev rules
                subprocess.run(f"echo '{udev_rule}' | sudo tee {udev_file}", shell=True, check=True)
                subprocess.run("sudo udevadm control --reload-rules", shell=True, check=True)
                print("  Udev rules created and reloaded")
            else:
                print("  Udev rules already exist")
                
            return True
        except subprocess.CalledProcessError as e:
            print(f"  Failed to setup udev rules: {e}")
            return False
            
    def install_system_dependencies(self):
        """Install system dependencies"""
        if self.platform != 'linux':
            print("Skipping system dependencies (not on Linux)")
            return True
            
        print("Installing system dependencies...")
        
        # Update package list
        try:
            subprocess.run("sudo apt update", shell=True, check=True)
            print("  Package list updated")
        except subprocess.CalledProcessError:
            print("  Failed to update package list")
            return False
            
        # Install required packages
        packages = [
            ('python3-pip', 'Python package manager'),
            ('python3-dev', 'Python development headers'),
            ('python3-venv', 'Python virtual environment'),
            ('i2c-tools', 'I2C tools'),
            ('python3-smbus', 'SMBus for I2C'),
            ('build-essential', 'Build tools'),
            ('cmake', 'Build system'),
            ('git', 'Version control')
        ]
        
        success_count = 0
        for package, description in packages:
            if self.run_command(f"sudo apt install -y {package}", description):
                success_count += 1
                
        print(f"Successfully installed {success_count}/{len(packages)} system packages")
        return success_count == len(packages)
        
    def test_installation(self):
        """Test if modules are properly installed"""
        print("Testing installation...")
        
        test_modules = [
            ('RPi.GPIO', 'import RPi.GPIO'),
            ('pigpio', 'import pigpio'),
            ('serial', 'import serial'),
            ('cv2', 'import cv2'),
            ('numpy', 'import numpy'),
            ('rclpy', 'import rclpy'),
            ('pygame', 'import pygame'),
            ('PIL', 'from PIL import Image')
        ]
        
        success_count = 0
        for module_name, import_statement in test_modules:
            try:
                exec(import_statement)
                print(f"  {module_name}: OK")
                success_count += 1
            except ImportError as e:
                print(f"  {module_name}: FAILED - {e}")
                
        print(f"Successfully tested {success_count}/{len(test_modules)} modules")
        return success_count >= len(test_modules) * 0.8  # 80% success rate
        
    def run_installation(self):
        """Run complete installation process"""
        self.print_header()
        
        if self.platform != 'linux':
            print("WARNING: This script is designed for Linux/Raspberry Pi")
            print("Some features may not work on other platforms")
            
        # Installation steps
        steps = [
            ("System Dependencies", self.install_system_dependencies),
            ("Python Packages", self.install_pip_packages),
            ("GPIO Permissions", self.setup_gpio_permissions),
            ("Pigpio Daemon", self.setup_pigpio_daemon),
            ("Udev Rules", self.setup_udev_rules),
            ("Test Installation", self.test_installation)
        ]
        
        results = {}
        for step_name, step_func in steps:
            print(f"\n{step_name}:")
            print("-" * len(step_name))
            results[step_name] = step_func()
            
        # Summary
        print("\n" + "=" * 60)
        print("Installation Summary:")
        print("=" * 60)
        
        for step_name, success in results.items():
            status = "SUCCESS" if success else "FAILED"
            print(f"{step_name}: {status}")
            
        overall_success = all(results.values())
        
        if overall_success:
            print("\nAll installation steps completed successfully!")
            print("You can now run the Sanhum Robot with full hardware support.")
        else:
            print("\nSome installation steps failed.")
            print("Please check the errors above and try to resolve them.")
            
        return overall_success

def main():
    """Main installation function"""
    installer = HardwareModuleInstaller()
    
    try:
        success = installer.run_installation()
        
        if success:
            print("\nInstallation completed successfully!")
            print("You may need to log out and log back in for group permissions to take effect.")
        else:
            print("\nInstallation completed with some errors.")
            print("Please resolve the errors and try again.")
            
        input("\nPress Enter to exit...")
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\nInstallation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
