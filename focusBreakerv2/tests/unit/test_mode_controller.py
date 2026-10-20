from unittest.mock import Mock
from focusbreaker.core.mode_controller import ModeController

def test_mode_controller_init():
    # Should default to normal if invalid
    ctrl = ModeController("invalid_mode")
    assert ctrl.mode_key == "normal"
    
    ctrl_strict = ModeController("strict")
    assert ctrl_strict.mode_key == "strict"

def test_mode_controller_properties():
    ctrl = ModeController("normal")
    rules = ctrl.get_mode_rules(Mock())
    
    assert rules["can_snooze"] is True
    assert rules["can_skip"] is True
    assert rules["can_extend"] is True
    assert rules["window_type"] == "small"
    assert rules["has_breaks"] is True
    assert rules["requires_cooldown"] is False

    ctrl_focused = ModeController("focused")
    rules_focused = ctrl_focused.get_mode_rules(Mock())
    
    assert rules_focused["can_snooze"] is False
    assert rules_focused["can_skip"] is False
    assert rules_focused["can_extend"] is False
    assert rules_focused["window_type"] == "full_screen"
    assert rules_focused["has_breaks"] is False
    assert rules_focused["requires_cooldown"] is True

def test_mode_controller_cooldown(monkeypatch):
    mock_settings = Mock()
    mock_settings.strict_cooldown = 15
    mock_settings.focused_mandatory_break = 20
    
    ctrl_normal = ModeController("normal")
    assert ctrl_normal.get_cooldown_duration(60, mock_settings) == 0
    
    ctrl_strict = ModeController("strict")
    assert ctrl_strict.get_cooldown_duration(60, mock_settings) == 15
    
    ctrl_focused = ModeController("focused")
    assert ctrl_focused.get_cooldown_duration(60, mock_settings) == 20
    assert ctrl_focused.get_cooldown_duration(130, mock_settings) == 45
    assert ctrl_focused.get_cooldown_duration(250, mock_settings) == 60

def test_is_escape_hatch_available():
    ctrl_normal = ModeController("normal")
    assert not ctrl_normal.is_escape_hatch_available(True, True)

    ctrl_strict = ModeController("strict")
    assert ctrl_strict.is_escape_hatch_available(is_break_time=True) is True
    assert ctrl_strict.is_escape_hatch_available(is_break_time=False, is_cooldown=True) is True
    assert ctrl_strict.is_escape_hatch_available(is_break_time=False, is_cooldown=False) is False

    ctrl_focused = ModeController("focused")
    assert ctrl_focused.is_escape_hatch_available(is_break_time=True) is False
    assert ctrl_focused.is_escape_hatch_available(is_cooldown=True) is True