import pytest
from unittest.mock import patch, MagicMock
from focusbreaker.core.escape_hatch import EscapeHatch

@patch("focusbreaker.core.escape_hatch.keyboard")
def test_escape_hatch_trigger(mock_keyboard):
    hatch = EscapeHatch(hold_duration=1.0)
    
    # Mock keyboard pressed
    mock_keyboard.is_pressed.return_value = True
    
    # Manually trigger check_state twice to simulate holding
    with patch("focusbreaker.core.escape_hatch.time.time") as mock_time:
        mock_time.side_effect = [100.0, 101.1] # 1.1s elapsed
        
        trigger_spy = MagicMock()
        hatch.triggered.connect(trigger_spy)
        
        hatch._check_state() # First press detection
        hatch._check_state() # Trigger threshold reached
        
        trigger_spy.assert_called_once()
        assert hatch._is_pressed is False # Resets after trigger

@patch("focusbreaker.core.escape_hatch.keyboard")
def test_escape_hatch_cancel(mock_keyboard):
    hatch = EscapeHatch(hold_duration=3.0)
    
    cancel_spy = MagicMock()
    hatch.cancelled.connect(cancel_spy)
    
    # Press
    mock_keyboard.is_pressed.return_value = True
    hatch._check_state()
    assert hatch._is_pressed is True
    
    # Release
    mock_keyboard.is_pressed.return_value = False
    hatch._check_state()
    
    assert hatch._is_pressed is False
    cancel_spy.assert_called_once()
