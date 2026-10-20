import pytest
import os
from focusbreaker.data.db import DBManager
from focusbreaker.data.models import Task, WorkSession, Settings

@pytest.fixture
def db():
    # Use in-memory database for testing
    manager = DBManager(db_path=":memory:")
    manager.connect()
    yield manager
    manager.close()

def test_db_settings(db):
    # Test default settings
    settings = db.get_settings()
    assert settings.username == "User"
    
    # Test update settings
    settings.username = "TestUser"
    db.save_settings(settings)
    
    updated = db.get_settings()
    assert updated.username == "TestUser"

def test_db_tasks(db):
    task = Task(name="Test Task", allocated_time_minutes=30, mode="normal")
    task_id = db.create_task(task)
    assert task_id is not None
    
    tasks = db.get_all_tasks()
    assert len(tasks) == 1
    assert tasks[0].name == "Test Task"

def test_db_sessions(db):
    session = WorkSession(
        task_id=1,
        task_name="Test Session",
        planned_duration_minutes=25,
        mode="normal",
        start_time="2023-10-01T10:00:00"
    )
    # create_session returns the id
    session_id = db.createSession(session)
    assert session_id is not None
    
    db_session = db.getSession(session_id)
    assert db_session.task_name == "Test Session"
    
    # Update session
    db_session.status = "completed"
    db.updateSession(db_session)
    
    updated = db.getSession(session_id)
    assert updated.status == "completed"

def test_db_streaks(db):
    streaks = db.get_streaks()
    assert "session_streak" in streaks
    assert streaks["session_streak"].current_count == 0
    
    db.update_streak("session_streak", 5, 10)
    updated = db.get_streaks()
    assert updated["session_streak"].current_count == 5
    assert updated["session_streak"].best_count == 10
