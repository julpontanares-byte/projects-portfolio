import pytest
from unittest.mock import Mock, patch
from focusbreaker.core.session_manager import SessionManager
from focusbreaker.data.models import WorkSession, Break, Settings
from datetime import datetime

@pytest.fixture
def mock_db():
    db = Mock()
    db.get_settings.return_value = Settings(max_snooze_passes=3)
    db.createSession.return_value = 1
    db.canSnooze.return_value = True
    return db

@patch("focusbreaker.core.session_manager.QTimer")
@patch("focusbreaker.core.session_manager.Scheduler")
def test_session_manager_start(MockScheduler, MockQTimer, mock_db):
    mock_timer_instance = Mock()
    MockQTimer.return_value = mock_timer_instance

    mock_breaks = [Break(session_id=1, scheduled_offset_minutes=25, duration_minutes=5, status="pending")]
    MockScheduler.schedule_breaks.return_value = mock_breaks
    
    manager = SessionManager(mock_db)
    manager.start_session("Test Task", 50, "normal")
    
    assert manager.session is not None
    assert manager.session.id == 1
    assert manager.session.task_name == "Test Task"
    assert manager.session.mode == "normal"
    assert not manager.is_paused
    
    mock_db.log_event.assert_any_call("session_started", session_id=1)
    mock_timer_instance.start.assert_called_once()
    assert len(manager.breaks) == 1

@patch("focusbreaker.core.session_manager.QTimer")
def test_session_manager_pause_resume(MockQTimer, mock_db):
    mock_timer_instance = Mock()
    mock_timer_instance.isActive.return_value = True
    MockQTimer.return_value = mock_timer_instance

    manager = SessionManager(mock_db)
    manager.start_session("T", 10, "normal")
    
    manager.pause()
    assert manager.is_paused
    mock_timer_instance.stop.assert_called_once()
    
    manager.resume()
    assert not manager.is_paused
    # 1 for start, 1 for resume
    assert mock_timer_instance.start.call_count == 2

@patch("focusbreaker.core.session_manager.QTimer")
def test_session_manager_stop(MockQTimer, mock_db):
    manager = SessionManager(mock_db)
    manager.session = WorkSession(task_id=1, task_name="T", planned_duration_minutes=10, mode="normal", start_time=datetime.now().isoformat())
    manager.session.id = 1
    
    manager.stop_session("abandoned")
    
    assert manager.session is None
    assert manager.is_paused is False
    assert not manager.in_cooldown
    mock_db.updateSession.assert_called_once()
    mock_db.log_event.assert_called_with("session_stopped", session_id=1, description="Status: abandoned")

@patch("focusbreaker.core.session_manager.QTimer")
def test_session_manager_complete_cooldown(MockQTimer, mock_db):
    manager = SessionManager(mock_db)
    manager.session = WorkSession(task_id=1, task_name="T", planned_duration_minutes=60, mode="strict", start_time=datetime.now().isoformat())
    manager.session.id = 1
    
    manager.mode_ctrl = Mock()
    manager.mode_ctrl.get_cooldown_duration.return_value = 15
    manager.streak_mgr = Mock()
    manager.streak_mgr.process_session_completion.return_value = []
    
    manager.complete_session()
    
    assert manager.session is None
    assert manager.in_cooldown is True
    assert manager._cooldown_rem == 15 * 60

def test_session_manager_quality_calc(mock_db):
    manager = SessionManager(mock_db)
    session = WorkSession(task_id=1, task_name="T", planned_duration_minutes=60, mode="normal", start_time=datetime.now().isoformat())
    manager.session = session
    
    # 2 taken, 1 snoozed, 1 skipped, 1 emergency exit
    session.breaks_taken = 2
    session.breaks_snoozed = 1
    session.breaks_skipped = 1
    session.emergency_exits = 1
    
    manager._update_quality()
    
    # taken / total = 2 / 4 = 0.5
    # 0.5 - (1 * 0.2) = 0.3
    assert session.quality_score == 0.3