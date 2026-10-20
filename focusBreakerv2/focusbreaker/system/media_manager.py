import os
import shutil
import random
from pathlib import Path
from typing import List, Optional, Dict
import logging

from focusbreaker.config import AppPaths, MediaConfig

logger = logging.getLogger("FocusBreaker")

class MediaManager:
    """
    Handles file operations for the Break Media Library.
    Manages default assets and user uploads.
    """
    
    _history = {} # Track last shown for each mode to prevent immediate repeats

    @staticmethod
    def add_user_media(source_path: str, mode: str = 'normal') -> Optional[str]:
        """
        Copies a user file to the appropriate media directory.
        Returns the new relative path if successful.
        """
        try:
            src = Path(source_path)
            if not src.exists():
                return None
                
            # Determine destination based on extension
            dest_dir = AppPaths.get_media_dir(mode, user_content=True)
            dest_dir.mkdir(parents=True, exist_ok=True)
            
            # Create a clean filename
            filename = src.name.replace(" ", "_")
            dest_path = dest_dir / filename
            
            # Handle name collisions
            counter = 1
            while dest_path.exists():
                dest_path = dest_dir / f"{src.stem}_{counter}{src.suffix}"
                counter += 1
                
            shutil.copy2(src, dest_path)
            logger.info(f"Media added: {dest_path}")
            return str(dest_path)
            
        except Exception as e:
            logger.error(f"Failed to add media: {e}")
            return None

    @staticmethod
    def get_all_media(mode: Optional[str] = None) -> List[Dict]:
        """
        Returns a list of all media files (defaults + user).
        """
        media_list = []
        modes = [mode] if mode else ['normal', 'strict', 'focused']
        
        for m in modes:
            # Defaults
            default_dir = AppPaths.get_media_dir(m, user_content=False)
            if default_dir.exists():
                for f in default_dir.iterdir():
                    if f.suffix.lower() in (MediaConfig.SUPPORTED_IMAGE_FORMATS | MediaConfig.SUPPORTED_VIDEO_FORMATS):
                        media_list.append({
                            'name': f.name,
                            'path': str(f),
                            'mode': m,
                            'is_user': False,
                            'type': 'video' if f.suffix.lower() in MediaConfig.SUPPORTED_VIDEO_FORMATS else 'image'
                        })
            
            # User
            user_dir = AppPaths.get_media_dir(m, user_content=True)
            if user_dir.exists():
                for f in user_dir.iterdir():
                    if f.suffix.lower() in (MediaConfig.SUPPORTED_IMAGE_FORMATS | MediaConfig.SUPPORTED_VIDEO_FORMATS):
                        media_list.append({
                            'name': f.name,
                            'path': str(f),
                            'mode': m,
                            'is_user': True,
                            'type': 'video' if f.suffix.lower() in MediaConfig.SUPPORTED_VIDEO_FORMATS else 'image'
                        })
                        
        return media_list

    @staticmethod
    def get_random_media(mode: str) -> Optional[Dict]:
        """
        Returns a random media item for the specified mode.
        Implements shuffle-like behavior by preventing immediate repeats.
        """
        pool = MediaManager.get_all_media(mode)
        if not pool:
            return None
        
        # Filter out the last one shown for this mode if there's more than one choice
        last = MediaManager._history.get(mode)
        if len(pool) > 1 and last:
            temp_pool = [m for m in pool if m['path'] != last]
            if temp_pool:
                pool = temp_pool
        
        selected = random.choice(pool)
        MediaManager._history[mode] = selected['path']
        return selected

    @staticmethod
    def delete_user_media(file_path: str):
        """Deletes a user-uploaded file."""
        try:
            p = Path(file_path)
            if p.exists() and "user" in str(p):
                p.unlink()
                logger.info(f"Media deleted: {file_path}")
        except Exception as e:
            logger.error(f"Delete failed: {e}")
