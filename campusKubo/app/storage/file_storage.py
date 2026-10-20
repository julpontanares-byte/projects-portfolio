("""Simple file storage helpers for handling uploaded files.

This module provides a small, safe helper to persist user avatar images
into the application's `assets/uploads/profile_photos` directory. It
supports copying files from local paths and decoding `data:` URLs.
""")
import os
import shutil
import base64
import re
from typing import Optional


PROFILE_DIR = os.path.join(os.getenv('FILE_STORAGE_PATH', 'assets/uploads'), "profile_photos")


def ensure_profile_dir() -> str:
	os.makedirs(PROFILE_DIR, exist_ok=True)
	return PROFILE_DIR


def _is_data_url(s: str) -> bool:
	return isinstance(s, str) and s.startswith("data:")


def save_user_avatar(user_id: int, src: str) -> Optional[str]:
	"""Save an avatar for `user_id` from `src`.

	`src` may be a local filesystem path or a data URL (base64). The
	function copies/decodes the image into
	`assets/uploads/profile_photos/profile_{user_id}.png` and returns
	the stored relative path on success, or None on failure.
	"""
	if not user_id or not src:
		return None

	try:
		ensure_profile_dir()
		dest_filename = f"profile_{user_id}.png"
		dest_path = os.path.join(PROFILE_DIR, dest_filename)

		# If data URL, decode
		if _is_data_url(src):
			m = re.match(r"data:(image/\w+);base64,(.*)", src, re.DOTALL)
			if not m:
				return None
			b64 = m.group(2)
			data = base64.b64decode(b64)
			with open(dest_path, "wb") as f:
				f.write(data)
			return os.path.abspath(dest_path)

		# If src is a remote URL (http/https), we don't fetch it here.
		if src.startswith("http://") or src.startswith("https://"):
			# For external URLs, we simply do not copy; return the URL so it
			# can be stored in the DB instead.
			return src

		# Otherwise assume local file path — copy to destination
		if os.path.exists(src):
			shutil.copy2(src, dest_path)
			return os.path.abspath(dest_path)

		return None
	except Exception:
		return None

