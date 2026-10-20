from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, Property, QRectF
from PySide6.QtGui import QPainter, QColor, QPen, QBrush

class ProgressRing(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._value = 0.0
        self._ring_color = QColor("#1D8A88")
        self._bg_ring_color = QColor("rgba(224, 234, 234, 0.5)")
        self._thickness = 12
        self.setMinimumSize(240, 240)

    @Property(float)
    def value(self):
        return self._value

    @value.setter
    def value(self, val):
        self._value = max(0.0, min(1.0, val))
        self.update()

    def set_colors(self, ring: str, background: str):
        self._ring_color = QColor(ring)
        self._bg_ring_color = QColor(background)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        width = self.width()
        height = self.height()
        size = min(width, height) - self._thickness
        rect = QRectF((width - size) / 2, (height - size) / 2, size, size)

        # Draw Background Ring
        bg_pen = QPen(self._bg_ring_color)
        bg_pen.setWidth(self._thickness)
        bg_pen.setCapStyle(Qt.RoundCap)
        painter.setPen(bg_pen)
        painter.drawEllipse(rect)

        # Draw Progress Arc
        if self._value > 0:
            prog_pen = QPen(self._ring_color)
            prog_pen.setWidth(self._thickness)
            prog_pen.setCapStyle(Qt.RoundCap)
            painter.setPen(prog_pen)
            
            # Start at 90 degrees (top), go counter-clockwise
            start_angle = 90 * 16
            span_angle = -self._value * 360 * 16
            painter.drawArc(rect, start_angle, span_angle)
