import os
import sys

# Ensure project root is on sys.path so top-level packages (e.g., `storage`, `state`, `components`) can
# be imported from modules under `app.*` when the package is loaded.
_APP_DIR = os.path.dirname(__file__)
if _APP_DIR not in sys.path:
	sys.path.insert(0, _APP_DIR)
