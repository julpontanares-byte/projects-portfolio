from unittest.mock import Mock, patch
from datetime import date, timedelta
from focusbreaker.core.streak_manager import StreakManager
from focusbreaker.data.models import Streak, WorkSession

def test_process_session_completion_perfect():
    mock_db = Mock()
    mock_db.get_streaks.return_value = {}
    manager = StreakManager(mock_db)
    
    session = WorkSession(task_id=1, task_name="Test", planned_duration_minutes=25, mode="normal", start_time="2023-10-01T10:00:00")
    session.created_at = date.today().isoformat()
    session.breaks_skipped = 0
    session.emergency_exits = 0
    session.breaks_snoozed = 0
    
    milestones = manager.process_session_completion(session)
    
    assert mock_db.update_streak.call_count == 3  # session_streak, perfect_session, daily_consistency

def test_process_session_completion_broken_perfect():
    mock_db = Mock()
    
    # Pre-existing perfect streak
    perf_streak = Streak("perfect_session")
    perf_streak.current_count = 5
    perf_streak.best_count = 5
    
    mock_db.get_streaks.return_value = {"perfect_session": perf_streak}
    manager = StreakManager(mock_db)
    
    session = WorkSession(task_id=1, task_name="Test", planned_duration_minutes=25, mode="normal", start_time="2023-10-01T10:00:00")
    session.created_at = date.today().isoformat()
    session.breaks_snoozed = 1  # Breaks perfect streak, but not valid
    
    manager.process_session_completion(session)
    
    assert perf_streak.current_count == 0
    assert perf_streak.best_count == 5

def test_daily_consistency_increment():
    mock_db = Mock()
    
    daily_streak = Streak("daily_consistency")
    yesterday = date.today() - timedelta(days=1)
    daily_streak.last_updated = yesterday.isoformat()
    daily_streak.current_count = 9
    daily_streak.best_count = 9
    
    mock_db.get_streaks.return_value = {"daily_consistency": daily_streak}
    manager = StreakManager(mock_db)
    
    session = WorkSession(task_id=1, task_name="Test", planned_duration_minutes=25, mode="normal", start_time="2023-10-01T10:00:00")
    session.created_at = date.today().isoformat()
    
    milestones = manager.process_session_completion(session)
    
    assert daily_streak.current_count == 10
    assert len(milestones) >= 1
    assert milestones[0]["count"] == 10

def test_can_recover_streak():
    manager = StreakManager(Mock())
    assert manager.can_recover_streak("session_streak") is True
    assert manager.can_recover_streak("perfect_session") is True
    assert manager.can_recover_streak("daily_consistency") is False