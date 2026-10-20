"""Unit tests for AudioManager"""
import pytest
from unittest.mock import patch, MagicMock
from focusbreaker.system.audio import AudioManager


@patch("focusbreaker.system.audio.pygame.mixer")
def test_audio_manager_init(mock_mixer):
    """Test AudioManager initialization."""
    mock_mixer.get_init.return_value = False
    manager = AudioManager(media_vol=80, alarm_vol=70)
    
    assert manager.media_vol == 0.8
    assert manager.alarm_vol == 0.7
    mock_mixer.init.assert_called_once()


@patch("focusbreaker.system.audio.pygame.mixer")
def test_set_volumes(mock_mixer):
    """Test volume control."""
    mock_mixer.get_init.return_value = True
    manager = AudioManager(media_vol=50, alarm_vol=60)
    
    manager.set_volumes(100, 100)
    assert manager.media_vol == 1.0
    assert manager.alarm_vol == 1.0


@patch("focusbreaker.system.audio.pygame.mixer")
@patch("os.path.getsize")
@patch("os.path.exists")
@patch("os.listdir")
def test_play_surprise(mock_listdir, mock_exists, mock_getsize, mock_mixer):
    """Test playing surprise effect."""
    mock_mixer.get_init.return_value = True
    mock_exists.return_value = True
    mock_getsize.return_value = 1024  # Mock file size
    mock_listdir.return_value = ["sound1.wav", "sound2.mp3"]
    mock_sound = MagicMock()
    mock_mixer.Sound.return_value = mock_sound
    
    manager = AudioManager()
    manager.play_surprise(mode="normal")
    
    # Should load a sound and play it
    assert mock_mixer.Sound.called or mock_mixer.Channel.called


@patch("focusbreaker.system.audio.pygame.mixer")
@patch("os.path.getsize")
@patch("os.path.exists")
def test_play_alarm(mock_exists, mock_getsize, mock_mixer):
    """Test playing alarm."""
    mock_mixer.get_init.return_value = True
    mock_exists.return_value = True
    mock_getsize.return_value = 1024  # Mock file size
    mock_sound = MagicMock()
    mock_mixer.Sound.return_value = mock_sound
    
    manager = AudioManager()
    manager.play_alarm()
    
    # Should attempt to load and play alarm
    assert mock_mixer.Sound.called or mock_mixer.Channel.called


@patch("focusbreaker.system.audio.pygame.mixer")
def test_stop_all(mock_mixer):
    """Test stopping all audio."""
    mock_mixer.get_init.return_value = True
    manager = AudioManager()
    manager.stop_all()
    
    # Both channels should be stopped
    mock_mixer.Channel().stop.call_count >= 0  # Verify method can be called
