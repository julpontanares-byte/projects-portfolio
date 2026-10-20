import pytest
from PySide6.QtCore import Qt
from unittest.mock import MagicMock, patch

from focusbreaker.ui.main_window import MainWindow
from focusbreaker.data.db import DBManager
from focusbreaker.config import Palette

@pytest.fixture
def mock_db():
    db = MagicMock(spec=DBManager)
    mock_settings = MagicMock()
    mock_settings.username = "Annuh"
    db.get_settings.return_value = mock_settings
    db.get_all_tasks.return_value = []
    db.get_stats.return_value = {}
    db.get_streaks.return_value = {}
    return db

@patch("focusbreaker.ui.main_window.SystemTrayManager")
@patch("focusbreaker.ui.main_window.FloatingSessionWindow")
def test_main_window_navigation(MockFloating, MockTray, qtbot, mock_db):
    window = MainWindow(mock_db)
    qtbot.addWidget(window)
    
    # Check initial page
    assert window.stack.currentIndex() == 0 # Home
    
    # Navigate to History
    qtbot.mouseClick(window.switcher.tabs["history"], Qt.LeftButton)
    assert window.stack.currentIndex() == 1
    
    # Navigate to Analytics
    qtbot.mouseClick(window.switcher.tabs["analytics"], Qt.LeftButton)
    assert window.stack.currentIndex() == 2
    
    # Navigate to Home again
    qtbot.mouseClick(window.switcher.tabs["home"], Qt.LeftButton)
    assert window.stack.currentIndex() == 0

@patch("focusbreaker.ui.main_window.TaskDialog")
def test_main_window_start_session_flow(MockDialog, qtbot, mock_db):
    with patch("focusbreaker.ui.main_window.SystemTrayManager"), \
         patch("focusbreaker.ui.main_window.FloatingSessionWindow"):
        window = MainWindow(mock_db)
        qtbot.addWidget(window)
        
        # Mock dialog return
        mock_dialog_instance = MockDialog.return_value
        mock_dialog_instance.exec.return_value = True
        mock_task = MagicMock()
        mock_task.name = "Test Task"
        mock_task.allocated_time_minutes = 25
        mock_task.mode = "normal"
        mock_dialog_instance.get_task.return_value = mock_task
        
        # Trigger new task from FAB
        qtbot.mouseClick(window.fab, Qt.LeftButton)
        
        MockDialog.assert_called_once()
        # Verify that start_session was called with the correct arguments
        # This checks the fix for the TypeError
        assert window.session_mgr.session is not None
        assert window.session_mgr.session.task_name == "Test Task"
