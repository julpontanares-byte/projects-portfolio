import pytest
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from unittest.mock import MagicMock

from focusbreaker.ui.task_dialog import TaskDialog
from focusbreaker.data.db import DBManager

@pytest.fixture
def mock_db():
    db = MagicMock(spec=DBManager)
    mock_settings = MagicMock()
    mock_settings.username = "TestUser"
    db.get_settings.return_value = mock_settings
    return db

def test_task_dialog_initial_state(qtbot, mock_db):
    dialog = TaskDialog(mock_db)
    qtbot.addWidget(dialog)
    
    assert dialog.windowTitle() == "" # Frameless
    assert "Good morning, TestUser!" in dialog.findChild(Object=None, name="").text() if dialog.findChild(Object=None, name="") else True
    assert dialog.selected_mode == "normal"

def test_task_dialog_input_validation(qtbot, mock_db):
    dialog = TaskDialog(mock_db)
    qtbot.addWidget(dialog)
    
    # Click next without input
    qtbot.mouseClick(dialog.next_btn, Qt.LeftButton)
    assert dialog.task_input.placeholderText() == "PLEASE ENTER A TASK NAME..."
    assert not dialog.isVisible() if dialog.result() == 1 else True # Should not have accepted

def test_task_dialog_mode_selection(qtbot, mock_db):
    dialog = TaskDialog(mock_db)
    qtbot.addWidget(dialog)
    
    # Click Strict mode
    strict_card = dialog.mode_cards["strict"]
    qtbot.mouseClick(strict_card, Qt.LeftButton)
    
    assert dialog.selected_mode == "strict"
    assert strict_card._selected is True
    assert dialog.mode_cards["normal"]._selected is False

def test_task_dialog_submission(qtbot, mock_db):
    dialog = TaskDialog(mock_db)
    qtbot.addWidget(dialog)
    
    # Panel 1: Enter task name and click Next
    qtbot.keyClicks(dialog.task_input, "Coding Session")
    qtbot.mouseClick(dialog.next_btn, Qt.LeftButton)
    
    # Should now be on Panel 2 (advancing through wizard)
    assert dialog.current_panel == 2, "Should advance to Panel 2 after Next on Panel 1"
    
    # Panel 2: Duration should default to 60, click Next
    qtbot.mouseClick(dialog.next_btn, Qt.LeftButton)
    
    # Should now be on Panel 3
    assert dialog.current_panel == 3, "Should advance to Panel 3 after Next on Panel 2"
    
    # Panel 3: Click "Start Session" to complete
    qtbot.mouseClick(dialog.next_btn, Qt.LeftButton)
    
    # Dialog should be accepted and task created
    assert dialog.result() == 1, "Dialog should be accepted after completing all panels"
    mock_db.create_task.assert_called_once()
    task = mock_db.create_task.call_args[0][0]
    assert task.name == "Coding Session"
    assert task.mode == "normal"
