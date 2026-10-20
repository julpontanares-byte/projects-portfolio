from unittest.mock import MagicMock, patch

from focusbreaker.ui.settings_dialog import SettingsPage


def test_reset_all_requests_restart():
    page = SettingsPage.__new__(SettingsPage)
    page.db = MagicMock()
    page.accept = MagicMock()

    confirm_dialog = MagicMock()
    confirm_dialog.exec.return_value = True

    mock_app = MagicMock()

    with patch("focusbreaker.ui.settings_dialog.ThemedConfirmDialog", return_value=confirm_dialog), \
         patch("focusbreaker.ui.settings_dialog.QApplication.instance", return_value=mock_app), \
         patch("focusbreaker.ui.settings_dialog.QTimer.singleShot", side_effect=lambda _ms, cb: cb()):
        SettingsPage._reset_all(page)

    page.db.reset_database.assert_called_once()
    page.accept.assert_called_once()
    mock_app.exit.assert_called_once_with(1000)
