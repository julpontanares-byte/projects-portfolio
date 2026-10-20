import pytest
from unittest.mock import MagicMock

from focusbreaker.ui.achievements_modal import AchievementsModal
from focusbreaker.data.db import DBManager


@pytest.fixture
def mock_db():
    db = MagicMock(spec=DBManager)
    db.get_achievement_stats.return_value = {
        "sessions": 0,
        "daily_streak": 0,
        "perfect_sessions": 0,
        "consecutive_perfect": 0,
        "strict_sessions": 0,
        "focused_sessions": 0,
        "modes_used": 0,
        "hours": 0,
        "total_breaks": 0,
        "no_exit_sessions": 0,
    }
    return db


def test_achievement_modal_column_breakpoint(qtbot, mock_db):
    modal = AchievementsModal(mock_db)
    qtbot.addWidget(modal)

    # Narrow window -> compact single-column layout
    modal.setFixedSize(760, 620)
    modal._refresh_grid()
    assert modal._column_count_for_width(modal.width()) == 1
    assert modal.grid.getItemPosition(0)[:2] == (0, 0)
    assert modal.grid.getItemPosition(1)[:2] == (1, 0)

    # Wider window -> two-column layout
    modal.setFixedSize(1100, 760)
    modal._refresh_grid()
    assert modal._column_count_for_width(modal.width()) == 2
    assert modal.grid.getItemPosition(0)[:2] == (0, 0)
    assert modal.grid.getItemPosition(1)[:2] == (0, 1)
