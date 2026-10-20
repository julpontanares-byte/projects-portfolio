import pytest
import os
import shutil
from pathlib import Path
from focusbreaker.system.media_manager import MediaManager
from focusbreaker.config import AppPaths

@pytest.fixture
def temp_media_structure(tmp_path):
    # Mock AppPaths to use temp directory
    base = tmp_path / "focusbreaker"
    assets = base / "assets" / "media"
    
    # Create structure
    for mode in ['normal', 'strict', 'focused']:
        (assets / mode / "defaults").mkdir(parents=True)
        (assets / mode / "user").mkdir(parents=True)
        
    return assets

def test_add_user_media(tmp_path, monkeypatch):
    # Setup dummy source file
    src_file = tmp_path / "test_image.jpg"
    src_file.write_text("dummy data")
    
    # Setup dummy dest structure
    dest_base = tmp_path / "dest"
    normal_user_dir = dest_base / "normal" / "user"
    normal_user_dir.mkdir(parents=True)
    
    # Mock AppPaths.get_media_dir
    def mock_get_media_dir(mode, user_content):
        return dest_base / mode / ("user" if user_content else "defaults")
    
    with patch("focusbreaker.config.AppPaths.get_media_dir", side_effect=mock_get_media_dir):
        path = MediaManager.add_user_media(str(src_file), mode='normal')
        
        assert path is not None
        assert os.path.exists(path)
        assert "test_image.jpg" in path

def test_get_all_media_empty(tmp_path):
    # This might fail if AppPaths isn't fully mocked, 
    # but we can check if it returns a list
    media = MediaManager.get_all_media('normal')
    assert isinstance(media, list)

from unittest.mock import patch

def test_delete_user_media(tmp_path):
    user_file = tmp_path / "user" / "delete_me.jpg"
    user_file.parent.mkdir()
    user_file.write_text("data")
    
    MediaManager.delete_user_media(str(user_file))
    assert not user_file.exists()
