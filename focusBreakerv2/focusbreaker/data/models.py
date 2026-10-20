from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Task:
    name: str
    allocated_time_minutes: int
    mode: str
    auto_calculate_breaks: bool = True
    manual_break_count: int = 0
    manual_break_duration: int = 5
    created_at: str = ""
    id: Optional[int] = None


@dataclass
class WorkSession:
    task_id: Optional[int]
    task_name: str
    planned_duration_minutes: int
    mode: str
    start_time: str
    id: Optional[int] = None
    end_time: Optional[str] = None
    status: str = "in_progress"
    breaks_taken: int = 0
    breaks_snoozed: int = 0
    breaks_skipped: int = 0
    emergency_exits: int = 0
    snooze_passes_remaining: int = 3
    extended_count: int = 0
    actual_duration_minutes: int = 0
    quality_score: float = 1.0
    created_at: str = ""


@dataclass
class Break:
    session_id: int
    scheduled_offset_minutes: int  # Minutes from session start
    duration_minutes: int
    scheduled_time: str = "" # Actual timestamp
    actual_time: Optional[str] = None
    status: str = "pending"
    snooze_count: int = 0
    snooze_duration_minutes: int = 0
    id: Optional[int] = None


@dataclass
class Streak:
    streak_type: str
    current_count: int = 0
    best_count: int = 0
    last_updated: str = ""


@dataclass
class Settings:
    username: str = "User"
    is_first_run: bool = True
    first_close_notified: bool = False
    normal_work_interval: int = 25
    normal_break_duration: int = 5
    normal_snooze_duration: int = 5
    max_snooze_passes: int = 3
    allow_skip_in_normal_mode: bool = True
    snooze_redistributes_breaks: bool = True
    strict_work_interval: int = 52
    strict_break_duration: int = 17
    strict_cooldown: int = 20
    focused_mandatory_break: int = 30
    media_volume: int = 80
    alarm_volume: int = 70
    alarm_duration: int = 5
    brightness_boost: int = 0
    image_duration: int = 15
    escape_hatch_enabled: bool = True
    escape_hatch_combo: str = "ctrl+alt+esc"
    escape_hatch_duration: int = 5
    blocklist: str = "chrome.exe, firefox.exe, edge.exe, discord.exe, slack.exe"

