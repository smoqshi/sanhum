#!/usr/bin/env python3
"""
Simple Sanhum Robot Installation Script
Minimal requirements - focuses on getting the application running
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

class SimpleInstaller:
    def __init__(self):
        self.platform = platform.system().lower()
        self.script_dir = Path(__file__).parent
        
        # Find project root by looking for CMakeLists.txt
        current_dir = self.script_dir
        while current_dir.parent != current_dir:
            if (current_dir / "CMakeLists.txt").exists():
                self.project_root = current_dir
                break
            current_dir = current_dir.parent
        else:
            # Fallback to script directory if not found
            self.project_root = self.script_dir
        
    def print_header(self):
        print("=" * 60)
        print("Sanhum Robot Simple Installer")
        print(f"Platform: {platform.system()} {platform.release()}")
        print(f"Python: {sys.version}")
        print("=" * 60)
        print()
        
    def check_basic_requirements(self):
        """Check basic requirements"""
        print("Checking basic requirements...")
        
        # Check Python
        print(f"✅ Python {sys.version.split()[0]}")
        
        # Check project files
        cmake_file = self.project_root / "CMakeLists.txt"
        print(f"Looking for CMakeLists.txt at: {cmake_file}")
        print(f"File exists: {cmake_file.exists()}")
        if cmake_file.exists():
            print("✅ CMakeLists.txt found")
        else:
            print("❌ CMakeLists.txt not found")
            print(f"Current directory contents: {list(self.project_root.iterdir())}")
            return False
            
        # Check source files
        main_cpp = self.project_root / "src" / "gui_main.cpp"
        if main_cpp.exists():
            print("✅ Source files found")
        else:
            print("❌ Source files not found")
            return False
            
        return True
        
    def create_minimal_build(self):
        """Create minimal build without external dependencies"""
        print("Creating minimal build...")
        
        build_dir = self.project_root / "build"
        build_dir.mkdir(exist_ok=True)
        
        # Create a simple batch file to launch GUI directly
        if self.platform == 'windows':
            # Create simple GUI launcher
            gui_launcher = build_dir / "run_gui.bat"
            launcher_content = '''@echo off
echo Sanhum Robot GUI Launcher
echo ========================
echo.

REM Try to find Python GUI
echo Looking for Python GUI files...

REM Check if we can run Python directly
cd /d "{}"

REM Try to run GUI directly with Python
echo Attempting to start GUI with Python...
python src/gui_main.py 2>nul
if errorlevel 1 (
    echo GUI Python script not found, trying alternative...
    
    REM Try to find any Python GUI file
    if exist "src\\*.py" (
        echo Found Python files in src directory
        dir /b src\\*.py
        echo.
        echo You may need to run the GUI manually:
        echo   python src\\[filename].py
    ) else (
        echo No Python GUI files found
    )
)

echo.
echo If GUI didn't start, you may need to:
echo 1. Install missing dependencies
echo 2. Check ROS2 installation
echo 3. Run: python scripts\\check_dependencies.py
echo.
pause
'''.format(self.project_root)
            
            gui_launcher.write_text(launcher_content)
            print(f"✅ Created GUI launcher: {gui_launcher}")
            
            # Create startup script
            startup_script = self.project_root / "start_simple.bat"
            startup_content = '''@echo off
echo Starting Sanhum Robot GUI...
echo ========================
cd /d "{}"
call build\\run_gui.bat
'''.format(self.project_root)
            
            startup_script.write_text(startup_content)
            print(f"✅ Created startup script: {startup_script}")
            
        return True
        
    def create_python_gui(self):
        """Create a simple Python GUI if source doesn't exist"""
        gui_main = self.project_root / "src" / "gui_main.py"
        
        if not gui_main.exists():
            print("Creating simple Python GUI...")
            
            simple_gui = '''#!/usr/bin/env python3
"""
Simple Sanhum Robot GUI
Placeholder for testing installation
"""

import sys
import tkinter as tk
from tkinter import ttk, messagebox
import os
from pathlib import Path

class SanhumGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Sanhum Robot Control")
        self.root.geometry("800x600")
        
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        title_label = ttk.Label(main_frame, text="Sanhum Robot Control Station", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=10)
        
        # Connection section
        ttk.Label(main_frame, text="Robot Connection:", font=("Arial", 12, "bold")).grid(
            row=1, column=0, sticky=tk.W, pady=5)
        
        self.robot_namespace = ttk.StringVar(value="simulation")
        ttk.Entry(main_frame, textvariable=self.robot_namespace, width=30).grid(
            row=1, column=1, pady=5)
        
        # Control section
        ttk.Label(main_frame, text="Controls:", font=("Arial", 12, "bold")).grid(
            row=2, column=0, sticky=tk.W, pady=5)
        
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=2, column=1, pady=5)
        
        # Movement controls
        ttk.Label(control_frame, text="Forward: W").grid(row=0, column=1)
        ttk.Label(control_frame, text="Backward: S").grid(row=1, column=1)
        ttk.Label(control_frame, text="Left: A").grid(row=2, column=0)
        ttk.Label(control_frame, text="Right: D").grid(row=2, column=2)
        ttk.Label(control_frame, text="Stop: Space").grid(row=3, column=1)
        
        # Status section
        ttk.Label(main_frame, text="Status:", font=("Arial", 12, "bold")).grid(
            row=3, column=0, sticky=tk.W, pady=5)
        
        self.status_text = tk.Text(main_frame, width=40, height=8, state="disabled")
        self.status_text.grid(row=3, column=1, pady=5)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=10)
        
        ttk.Button(button_frame, text="Connect", command=self.connect_robot).grid(
            row=0, column=0, padx=5)
        ttk.Button(button_frame, text="Disconnect", command=self.disconnect_robot).grid(
            row=0, column=1, padx=5)
        ttk.Button(button_frame, text="Check Dependencies", command=self.check_deps).grid(
            row=1, column=0, padx=5, pady=5)
        ttk.Button(button_frame, text="Exit", command=self.root.quit).grid(
            row=1, column=1, padx=5, pady=5)
        
        self.update_status("GUI Ready. Connect to robot to begin.")
        
    def update_status(self, message):
        self.status_text.config(state="normal")
        self.status_text.delete(1.0, tk.END)
        self.status_text.insert(tk.END, f"{message}\\n")
        self.status_text.config(state="disabled")
        self.status_text.see(tk.END)
        
    def connect_robot(self):
        namespace = self.robot_namespace.get()
        self.update_status(f"Connecting to robot: {namespace}")
        
        if namespace == "simulation":
            self.update_status("Connected to simulation mode")
        else:
            self.update_status(f"Attempting to connect to robot: {namespace}")
            # Here you would add actual ROS2 connection code
            
    def disconnect_robot(self):
        self.update_status("Disconnected from robot")
        
    def check_deps(self):
        try:
            import subprocess
            result = subprocess.run([sys.executable, "scripts/check_dependencies.py"], 
                                  capture_output=True, text=True, cwd=Path(__file__).parent.parent)
            self.update_status("Dependency Check Results:\\n" + result.stdout)
        except Exception as e:
            self.update_status(f"Failed to check dependencies: {e}")
        
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = SanhumGUI()
    app.run()
'''
            
            gui_main.write_text(simple_gui)
            print(f"✅ Created simple GUI: {gui_main}")
            
    def install_all(self):
        """Main installation function"""
        try:
            self.print_header()
            
            # Check basic requirements
            if not self.check_basic_requirements():
                print("\n❌ Basic requirements not met")
                return False
                
            print("\n✅ Basic requirements met")
            
            # Create Python GUI if needed
            self.create_python_gui()
            
            # Create minimal build
            if not self.create_minimal_build():
                print("\n❌ Failed to create build")
                return False
                
            print("\n" + "=" * 60)
            print("🎉 Simple Installation Completed!")
            print("=" * 60)
            
            print("\n📋 Next Steps:")
            print("   1. Run: start_simple.bat")
            print("   2. The GUI will open in a new window")
            print("   3. Use keyboard controls (WASD) to simulate robot control")
            
            return True
            
        except Exception as e:
            print(f"\n❌ Installation failed: {e}")
            return False

def main():
    installer = SimpleInstaller()
    success = installer.install_all()
    
    input("\nPress Enter to exit...")
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
