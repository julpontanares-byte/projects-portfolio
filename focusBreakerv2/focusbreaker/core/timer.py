from PySide6.QtCore import QTimer, Signal, QObject


class CountdownTimer(QObject):
    tick = Signal(int)
    finished = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._on_tick)
        self._remaining = 0
        self._running = False

    def start(self, seconds: int):
        self._remaining = seconds
        self._running = True
        self._timer.start()
        self.tick.emit(self._remaining)

    def pause(self):
        self._timer.stop()
        self._running = False

    def resume(self):
        if self._remaining > 0:
            self._running = True
            self._timer.start()

    def stop(self):
        self._timer.stop()
        self._running = False
        self._remaining = 0

    def add_seconds(self, seconds: int):
        self._remaining += seconds

    @property
    def remaining(self) -> int:
        return self._remaining

    @property
    def is_running(self) -> bool:
        return self._running

    def _on_tick(self):
        self._remaining -= 1
        self.tick.emit(self._remaining)
        if self._remaining <= 0:
            self._timer.stop()
            self._running = False
            self.finished.emit()


def fmt_time(seconds: int) -> str:
    seconds = max(0, seconds)
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"