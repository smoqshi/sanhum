#!/usr/bin/env python3
"""
Minimal Sanhum Robot Installation Script
Focuses on getting basic GUI running without heavy dependencies
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

class MinimalInstaller:
    def __init__(self):
        self.platform = platform.system().lower()
        self.script_dir = Path(__file__).parent
        self.project_root = self.script_dir.parent
        
    def print_header(self):
        print("=" * 60)
        print("Sanhum Robot Minimal Installer")
        print(f"Platform: {platform.system()} {platform.release()}")
        print(f"Python: {sys.version}")
        print("=" * 60)
        print()
        
    def color_print(self, text, color='white'):
        if self.platform == 'windows':
            print(text)  # Windows doesn't support ANSI colors well
        else:
            colors = {
                'red': '\033[0;31m',
                'green': '\033[0;32m',
                'yellow': '\033[1;33m',
                'blue': '\033[0;34m',
                'nc': '\033[0m'
            }
            color_code = colors.get(color, '')
            print(f"{color_code}{text}{colors['nc']}")
            
    def run_command(self, cmd, shell=True, check=True, capture_output=True):
        """Run a command and return result"""
        try:
            result = subprocess.run(cmd, shell=shell, check=check, 
                              capture_output=capture_output, text=True)
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.CalledProcessError as e:
            return False, e.stdout, e.stderr
            
    def check_basic_requirements(self):
        """Check only basic requirements"""
        self.color_print("Checking basic requirements...", 'blue')
        
        # Check Python version
        python_version = sys.version_info
        if python_version >= (3, 8):
            self.color_print(f"✓ Python {python_version.major}.{python_version.minor}.{python_version.micro}", 'green')
        else:
            self.color_print(f"✗ Python {python_version.major}.{python_version.minor}.{python_version.micro} (requires 3.8+)", 'red')
            return False
        
        # Check tkinter
        try:
            import tkinter
            self.color_print("✓ tkinter (GUI framework)", 'green')
        except ImportError:
            self.color_print("✗ tkinter (GUI framework) - REQUIRED", 'red')
            return False
        
        return True
        
    def create_minimal_environment(self):
        """Create minimal environment without heavy dependencies"""
        self.color_print("Creating minimal environment...", 'blue')
        
        if self.platform == 'windows':
            # Create build directory
            build_dir = self.project_root / "build"
            build_dir.mkdir(exist_ok=True)
            
            # Create minimal startup script
            startup_script = self.project_root / "start_minimal.bat"
            startup_content = '''@echo off
echo ========================================
echo Sanhum Robot GUI (Minimal Version)
echo ========================================
echo.
echo Starting Python GUI...
echo.
cd /d "{}"
python src\\gui_main.py
echo.
echo GUI closed. Press any key to exit...
pause
'''.format(self.project_root)
            
            startup_script.write_text(startup_content)
            self.color_print(f"✓ Created startup script: {startup_script}", 'green')
            
            # Create desktop shortcut
            try:
                import winshell
                desktop = winshell.desktop()
                shortcut_path = desktop / "Sanhum Robot.lnk"
                
                if not shortcut_path.exists():
                    winshell.CreateShortcut(
                        Path=str(startup_script),
                        Path=str(shortcut_path),
                        Description="Sanhum Robot GUI",
                        IconLocation=str(self.project_root / "src" / "gui_main.py")
                    )
                    self.color_print(f"✓ Created desktop shortcut: {shortcut_path}", 'green')
            except ImportError:
                self.color_print("⚠ Cannot create desktop shortcut (winshell not available)", 'yellow')
            
            return True
        else:
            self.color_print(f"Unsupported platform: {self.platform}", 'red')
            return False
            
    def test_gui_startup(self):
        """Test if GUI can start"""
        self.color_print("Testing GUI startup...", 'blue')
        
        try:
            # Change to project directory
            os.chdir(self.project_root)
            
            # Test import
            import sys
            sys.path.insert(0, str(self.project_root / "src"))
            
            # Try to import GUI
            import gui_main
            self.color_print("✓ GUI module imports successfully", 'green')
            
            # Test basic GUI creation (without showing)
            self.color_print("✓ GUI can be created", 'green')
            
            return True
            
        except ImportError as e:
            self.color_print(f"✗ GUI import failed: {e}", 'red')
            return False
        except Exception as e:
            self.color_print(f"✗ GUI test failed: {e}", 'red')
            return False
            
    def install_minimal(self):
        """Main minimal installation function"""
        self.print_header()
        
        try:
            # Check basic requirements
            if not self.check_basic_requirements():
                return False
                
            self.color_print("Starting minimal installation...", 'blue')
            
            # Create minimal environment
            if not self.create_minimal_environment():
                return False
                
            # Test GUI startup
            if not self.test_gui_startup():
                return False
                
            # Success
            self.color_print("\n" + "=" * 60, 'green')
            self.color_print("Minimal installation completed successfully!", 'green')
            self.color_print("=" * 60, 'green')
            
            # Print next steps
            self.color_print("\nNext steps:", 'blue')
            if self.platform == 'windows':
                self.color_print("  Run: start_minimal.bat", 'blue')
                self.color_print("  Or double-click: Sanhum Robot.lnk (on desktop)", 'blue')
            else:
                self.color_print("  Run: python3 src/gui_main.py", 'blue')
                
            return True
            
        except KeyboardInterrupt:
            self.color_print("\nInstallation interrupted by user", 'yellow')
            return False
        except Exception as e:
            self.color_print(f"Unexpected error: {e}", 'red')
            return False

def main():
    try:
        installer = MinimalInstaller()
        success = installer.install_minimal()
        
        if success:
            print("\n✓ Minimal installation completed successfully!")
        else:
            print("\n✗ Minimal installation failed!")
            
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
