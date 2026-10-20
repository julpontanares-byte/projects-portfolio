import pytest
from PySide6.QtWidgets import QApplication
from PySide6.QtTest import QTest
from PySide6.QtCore import Qt


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


class _QtBot:
    def __init__(self, app):
        self.app = app
        self._widgets = []

    def addWidget(self, widget):
        self._widgets.append(widget)
        widget.show()
        self.app.processEvents()

    def mouseClick(self, widget, button, *, pos=None, delay=-1):
        if pos is None:
            QTest.mouseClick(widget, button, Qt.KeyboardModifier.NoModifier, delay=delay)
        else:
            QTest.mouseClick(widget, button, Qt.KeyboardModifier.NoModifier, pos, delay)
        self.app.processEvents()

    def keyClicks(self, widget, text, delay=-1):
        QTest.keyClicks(widget, text, delay=delay)
        self.app.processEvents()

    def keyClick(self, widget, key, modifier=Qt.KeyboardModifier.NoModifier, delay=-1):
        QTest.keyClick(widget, key, modifier, delay=delay)
        self.app.processEvents()


@pytest.fixture
def qtbot(qapp):
    return _QtBot(qapp)
