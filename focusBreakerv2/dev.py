#!/usr/bin/env python
"""
Development launcher with hot reload enabled.
Run this instead of main.py to enable automatic restarts on file changes.

Usage:
    python dev.py
"""
import os
import sys
import subprocess

if __name__ == "__main__":
    # Set environment variable to enable hot reload
    env = os.environ.copy()
    env['DEV_MODE'] = '1'
    
    project_root = os.path.dirname(os.path.abspath(__file__))
    main_script = os.path.join(project_root, 'main.py')
    
    print("🚀 Starting focusBreaker in DEV MODE with hot reload enabled")
    print("💡 Tip: Edit Python files in focusbreaker/ and the app will auto-restart\n")
    
    # Run with hot reload
    result = subprocess.run(
        [sys.executable, main_script],
        cwd=project_root,
        env=env
    )
    
    sys.exit(result.returncode)
