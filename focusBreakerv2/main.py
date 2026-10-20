import sys
import os
import subprocess

def main():
    # Ensure project root is in path
    project_root = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, project_root)
    
    # Get the path to focusbreaker/main.py
    focusbreaker_main = os.path.join(project_root, "focusbreaker", "main.py")
    
    while True:
        # Run the app as a subprocess for clean restarts on Windows
        # We use sys.executable to ensure we use the same Python interpreter
        # and we set cwd to the project root for asset resolution.
        result = subprocess.run(
            [sys.executable, focusbreaker_main],
            cwd=project_root
        )
        
        # Check exit code: 1000 means restart, anything else means exit
        if result.returncode != 1000:
            sys.exit(result.returncode)

if __name__ == "__main__":
    main()

