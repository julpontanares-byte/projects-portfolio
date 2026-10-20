import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

from focusbreaker.data.db import DBManager
from focusbreaker.core.session_manager import SessionManager
from focusbreaker.core.streak_manager import StreakManager

@pytest.fixture
def test_db():
    db = DBManager(db_path=":memory:")
    db.connect()
    yield db
    db.close()

@pytest.fixture
def session_manager(test_db):
    with patch('focusbreaker.core.session_manager.QTimer') as MockTimer:
        mock_timer_instance = MockTimer.return_value
        sm = SessionManager(test_db)
        
        # Override the timer instance to allow checking if it was started/stopped
        sm._work_timer = mock_timer_instance
        
        yield sm, mock_timer_instance

def test_system_integration_session_lifecycle(test_db, session_manager):
    sm, mock_timer = session_manager
    streak_mgr = sm.streak_mgr

    # Verify initial DB state
    sessions = test_db.get_all_sessions()
    assert len(sessions) == 0

    # 1. Start a session
    task_name = "Integration Test Task"
    duration_minutes = 25
    mode = "normal"
    
    # We patch ModeController interactions implicitly through natural flow,
    # or just let it initialize (since mode_controller doesn't do heavy dependencies without setup).
    sm.start_session(task_name=task_name, duration_minutes=duration_minutes, mode=mode)
    
    # Verify timer was started
    mock_timer.start.assert_called()
    assert sm.session is not None
    assert sm.session.task_name == task_name
    assert not sm.is_paused

    # Verify that session is written to the DB
    sessions_after_start = test_db.get_all_sessions()
    assert len(sessions_after_start) == 1
    db_session = sessions_after_start[0]
    assert db_session.task_name == task_name
    assert db_session.status == "in_progress"
    assert db_session.mode == mode

    # 2. Simulate tick (Time passing)
    # Fast forward elapsed time manually
    sm._elapsed = 25 * 60 - 1  # 1 second before finish
    
    # 3. Stop the session manually as 'completed' or 'abandoned'
    sm.stop_session(status="completed")
    
    # Verify timer was stopped
    mock_timer.stop.assert_called()
    assert sm.session is None

    # Verify DB was updated
    sessions_after_stop = test_db.get_all_sessions()
    assert len(sessions_after_stop) == 1
    updated_session = sessions_after_stop[0]
    assert updated_session.status == "completed"
    assert updated_session.end_time is not None

def test_system_integration_streak_update(test_db, session_manager):
    sm, mock_timer = session_manager
    
    # Start and complete a session naturally through complete_session
    sm.start_session(task_name="Streak Task", duration_minutes=25, mode="strict")
    session_id = sm.session.id
    
    # Mark it as complete
    sm.complete_session()
    
    # Verify streak manager was utilized and DB is updated
    streaks = test_db.get_streaks()
    session_streak = streaks.get("session_streak")
    assert session_streak is not None
    assert session_streak.current_count == 1
    assert session_streak.last_updated is not None

    perfect_streak = streaks.get("perfect_session")
    assert perfect_streak is not None
    assert perfect_streak.current_count == 1
    
    # Session is marked completed in DB
    updated_session = test_db.getSession(session_id)
    assert updated_session.status == "completed"
