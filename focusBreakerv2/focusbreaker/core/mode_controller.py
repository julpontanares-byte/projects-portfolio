from typing import Dict, Any, Optional
from focusbreaker.config import MODES, TimingConfig

class ModeController:
    """
    Encapsulates the rules and constraints for different work modes.
    Aligns with user_flow.md requirements.
    """
    def __init__(self, mode: str):
        if mode not in MODES:
            mode = "normal"
        self.mode_key = mode
        self.config = MODES[mode]

    @property
    def name(self) -> str:
        return self.config["name"]

    @property
    def color(self) -> str:
        return self.config["color"]

    def get_mode_description(self) -> str:
        return self.config.get("description", "")

    def get_mode_rules(self, settings) -> Dict[str, Any]:
        """Step 11: Returns the full rule set for the mode."""
        rules = {
            "can_snooze": self.mode_key == "normal",
            "can_skip": self.mode_key == "normal",
            "can_extend": self.mode_key == "normal",
            "window_type": self.get_break_windows_type(),
            "has_breaks": self.has_breaks_during_work(),
            "requires_cooldown": self.requires_cooldown()
        }
        return rules

    def has_breaks_during_work(self) -> bool:
        """Step 13: Focused mode has no breaks during work."""
        return self.mode_key != "focused"

    def get_break_windows_type(self) -> str:
        """Step 25: Returns 'small' for normal, 'full_screen' for others."""
        return "small" if self.mode_key == "normal" else "full_screen"

    def can_snooze_break(self, snooze_passes_remaining: int) -> bool:
        """Fixed Step 38: Returns True if normal mode and passes remain."""
        if self.mode_key != "normal":
            return False
        return snooze_passes_remaining > 0

    def can_skip_break(self, settings) -> bool:
        """Step 38 (Skip): Checks settings for normal mode."""
        if self.mode_key != "normal":
            return False
        return settings.allow_skip_in_normal_mode

    def requires_cooldown(self) -> bool:
        """Step 44: Strict and Focused require cooldown."""
        return self.mode_key in ["strict", "focused"]

    def get_cooldown_duration(self, session_duration_minutes: int, settings) -> int:
        """Step 45: Returns mandatory rest duration."""
        if self.mode_key == "strict":
            return settings.strict_cooldown
        if self.mode_key == "focused":
            if session_duration_minutes >= 240: return 60
            if session_duration_minutes >= 120: return 45
            return settings.focused_mandatory_break
        return 0

    def is_escape_hatch_available(self, is_break_time: bool = False, is_cooldown: bool = False) -> bool:
        """Determines if escape hatch is active."""
        if self.mode_key == "normal": return False
        if self.mode_key == "strict": return is_break_time or is_cooldown
        if self.mode_key == "focused": return is_cooldown
        return False