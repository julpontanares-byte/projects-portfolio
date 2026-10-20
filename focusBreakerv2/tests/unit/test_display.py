"""Unit tests for DisplayController"""
import pytest
from unittest.mock import patch, MagicMock
from focusbreaker.system.display import DisplayController, OverlayWindow


@patch("focusbreaker.system.display.sbc.get_brightness")
def test_display_controller_init(mock_get_brightness):
    """Test DisplayController initialization."""
    mock_get_brightness.return_value = [75]
    controller = DisplayController()
    
    assert controller.original_brightness == 75
    assert controller.brightness_boost == 100


@patch("focusbreaker.system.display.sbc.get_brightness")
def test_display_controller_init_list(mock_get_brightness):
    """Test DisplayController handles list brightness return."""
    mock_get_brightness.return_value = [85]
    controller = DisplayController()
    
    assert controller.original_brightness == 85


@patch("focusbreaker.system.display.sbc.get_brightness")
def test_display_controller_init_fallback(mock_get_brightness):
    """Test DisplayController fallback when brightness reading fails."""
    mock_get_brightness.side_effect = Exception("Cannot read brightness")
    controller = DisplayController()
    
    assert controller.original_brightness == 100


@patch("focusbreaker.system.display.sbc.set_brightness")
@patch("focusbreaker.system.display.sbc.get_brightness")
def test_boost_brightness(mock_get_brightness, mock_set_brightness):
    """Test brightness boost."""
    mock_get_brightness.return_value = [75]
    controller = DisplayController()
    
    controller.boost_brightness(level=100)
    mock_set_brightness.assert_called_once_with(100)


@patch("focusbreaker.system.display.sbc.set_brightness")
@patch("focusbreaker.system.display.sbc.get_brightness")
def test_restore_brightness(mock_get_brightness, mock_set_brightness):
    """Test brightness restoration."""
    mock_get_brightness.return_value = [75]
    controller = DisplayController()
    
    controller.restore_brightness()
    mock_set_brightness.assert_called_once_with(75)


@patch("focusbreaker.system.display.sbc.set_brightness")
@patch("focusbreaker.system.display.sbc.get_brightness")
def test_restore_brightness_from_list(mock_get_brightness, mock_set_brightness):
    """Test brightness restoration when original is a list."""
    mock_get_brightness.return_value = [80]
    controller = DisplayController()
    controller.original_brightness = [80]
    
    controller.restore_brightness()
    mock_set_brightness.assert_called_once_with(80)


@patch("focusbreaker.system.display.sbc.set_brightness")
@patch("focusbreaker.system.display.sbc.get_brightness")
def test_set_brightness_error_handling(mock_get_brightness, mock_set_brightness):
    """Test that brightness errors are silently handled."""
    mock_get_brightness.return_value = [75]
    mock_set_brightness.side_effect = Exception("Cannot set brightness")
    controller = DisplayController()
    
    # Should not raise, just silently fail
    controller.boost_brightness(100)


def test_overlay_window_creation():
    """Test OverlayWindow can be created."""
    overlay = OverlayWindow(
        title="Test Break",
        message="Rest now",
        color="#FF0000"
    )
    
    assert overlay is not None
    assert overlay.windowTitle() == ""  # Title is set via label, not window title
