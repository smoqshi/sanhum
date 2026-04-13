#!/usr/bin/env python3
"""
Direct startup script for Sanhum Robot GUI
Bypasses installation and runs GUI directly
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    print("Sanhum Robot - Direct GUI Startup")
    print("=" * 50)
    print("Attempting to start GUI directly...")
    print()
    
    # Get project directory
    project_root = Path(__file__).parent
    
    try:
        # Change to project directory
        os.chdir(project_root)
        print(f"✓ Changed to: {project_root}")
        
        # Add src directory to Python path
        src_dir = project_root / "src"
        if src_dir.exists():
            sys.path.insert(0, str(src_dir))
            print(f"✓ Added to path: {src_dir}")
        
        # Try to import GUI
        print("Importing GUI modules...")
        try:
            import gui_main
            print("✓ GUI module imported successfully")
        except ImportError as e:
            print(f"✗ GUI import failed: {e}")
            print("Trying to run GUI anyway...")
        
        # Try to start GUI
        print("Starting GUI...")
        try:
            if 'gui_main' in globals():
                # Create GUI instance
                app = gui_main.FullyIntegratedRobotGUI()
                print("✓ GUI instance created")
                
                # Start the GUI
                print("✓ Starting GUI main loop...")
                app.root.mainloop()
            else:
                # Fallback - try to run gui_main.py directly
                gui_script = src_dir / "gui_main.py"
                if gui_script.exists():
                    print(f"✓ Running GUI script: {gui_script}")
                    subprocess.run([sys.executable, str(gui_script)], cwd=project_root)
                else:
                    print("✗ GUI script not found")
                    return False
        except Exception as e:
            print(f"✗ GUI startup failed: {e}")
            import traceback
            traceback.print_exc()
            return False
            
        return True
        
    except KeyboardInterrupt:
        print("\n✗ Startup interrupted by user")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    
    if success:
        print("\n✓ GUI started successfully!")
    else:
        print("\n✗ GUI startup failed!")
    
    input("Press Enter to exit...")
    sys.exit(0 if success else 1)
