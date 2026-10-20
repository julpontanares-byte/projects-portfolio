import pytest
from focusbreaker.core.scheduler import Scheduler
from focusbreaker.data.models import Settings, Task

@pytest.fixture
def default_settings():
    return Settings(
        normal_work_interval=25,
        normal_break_duration=5,
        strict_work_interval=52,
        strict_break_duration=17,
        focused_mandatory_break=30
    )

def test_schedule_breaks_normal_mode(default_settings):
    # 60 minute session in normal mode
    # 25 work + 5 break + 25 work + 5 break = 60
    # Breaks scheduled at offset 25
    breaks = Scheduler.schedule_breaks(session_id=1, duration_minutes=60, mode="normal", settings=default_settings)
    
    assert len(breaks) == 2
    assert breaks[0].scheduled_offset_minutes == 25
    assert breaks[0].duration_minutes == 5
    # Next break: 25 (offset) + 5 (brk) + 25 (work) = 55
    assert breaks[1].scheduled_offset_minutes == 55

def test_schedule_breaks_strict_mode(default_settings):
    # 120 minute session in strict mode
    # 52 work + 17 break + 52 work = 121 -> only 1 break scheduled inside 120 mins
    breaks = Scheduler.schedule_breaks(session_id=1, duration_minutes=120, mode="strict", settings=default_settings)
    
    assert len(breaks) == 1
    assert breaks[0].scheduled_offset_minutes == 52
    assert breaks[0].duration_minutes == 17

def test_schedule_breaks_focused_mode(default_settings):
    # Focused mode always schedules one break at the end
    breaks = Scheduler.schedule_breaks(session_id=1, duration_minutes=60, mode="focused", settings=default_settings)
    assert len(breaks) == 1
    assert breaks[0].scheduled_offset_minutes == 60
    assert breaks[0].duration_minutes == 30

def test_schedule_breaks_manual_task(default_settings):
    task = Task(name="Manual", allocated_time_minutes=60, mode="normal", auto_calculate_breaks=False, manual_break_count=2, manual_break_duration=10)
    # Interval = 60 // (2 + 1) = 20. Offsets at 20, 40.
    breaks = Scheduler.schedule_breaks(session_id=1, duration_minutes=60, mode="normal", settings=default_settings, task=task)
    
    assert len(breaks) == 2
    assert breaks[0].scheduled_offset_minutes == 20
    assert breaks[1].scheduled_offset_minutes == 40
    assert all(b.duration_minutes == 10 for b in breaks)
