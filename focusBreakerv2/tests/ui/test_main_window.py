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
    assert window.stack.currentIndex() == 0 # Dashboard
    
    # Navigate to History
    qtbot.mouseClick(window.switcher.tabs["history"], Qt.LeftButton)
    assert window.stack.currentIndex() == 1
    mock_db.get_all_sessions.assert_called()

    # Navigate to Analytics
    qtbot.mouseClick(window.switcher.tabs["analytics"], Qt.LeftButton)
    assert window.stack.currentIndex() == 2
    
    # Navigate to Settings (placeholder)
    qtbot.mouseClick(window.settings_btn, Qt.LeftButton)
    # Settings is a modal, not a stack page

def test_main_window_sidebar_toggle(qtbot, mock_db):
    pytest.skip("Sidebar functionality not implemented in current UI")

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
        
        # Trigger new task from FAB button
        qtbot.mouseClick(window.fab, Qt.LeftButton)
        
        MockDialog.assert_called_once()
        assert window.session_mgr.is_active is True
        assert window.stack.currentIndex() == 0 # Home view
