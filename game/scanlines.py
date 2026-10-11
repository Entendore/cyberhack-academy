"""CRT scanline overlay - paint scanlines on top of the terminal output.

A QWidget that paints semi-transparent horizontal lines across its parent,
giving the terminal a retro CRT look. Toggleable via the View menu.
"""

from PySide6.QtCore import Qt, QRect
from PySide6.QtGui import QPainter, QColor, QPaintEvent
from PySide6.QtWidgets import QWidget


class ScanlineOverlay(QWidget):
    """Transparent overlay that paints CRT-style scanlines."""

    def __init__(self, parent=None, line_spacing: int = 3, line_alpha: int = 28):
        super().__init__(parent)
        self.line_spacing = line_spacing
        self.line_alpha = line_alpha
        # Make this widget transparent and ignore mouse events
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WA_NoSystemBackground, True)
        self.setAttribute(Qt.WA_TranslucentBackground, True)

    def paintEvent(self, _e: QPaintEvent):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, False)
        c = QColor(0, 0, 0, self.line_alpha)
        p.setPen(c)
        # Draw horizontal lines every `line_spacing` pixels
        h = self.height()
        w = self.width()
        for y in range(0, h, self.line_spacing):
            p.drawLine(0, y, w, y)
        # Subtle vignette via 4 corner darkening
        # (kept lightweight to not slow down redraws)
        p.end()

    def resizeEvent(self, _e):
        self.update()
