"""Achievements dialog - shows all badges (unlocked + locked)."""

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGridLayout,
    QPushButton, QScrollArea, QWidget,
)

from .save_manager import SaveManager
from .achievements import ACHIEVEMENTS
from .styles import COLORS


class AchievementsDialog(QDialog):
    def __init__(self, save: SaveManager, parent=None):
        super().__init__(parent)
        self.save = save
        self.setWindowTitle("ACHIEVEMENTS - Badge Collection")
        self.resize(720, 600)
        self._build_ui()
        self._refresh()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        title = QLabel("ACHIEVEMENTS")
        title.setObjectName("TitleLabel")
        layout.addWidget(title)

        unlocked = sum(1 for a in ACHIEVEMENTS if self.save.has_achievement(a.id))
        sub = QLabel(f"{unlocked}/{len(ACHIEVEMENTS)} badges unlocked")
        sub.setObjectName("SubtitleLabel")
        layout.addWidget(sub)

        # Scrollable grid of badges
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"QScrollArea {{ border: none; }}")

        container = QWidget()
        grid = QGridLayout(container)
        grid.setContentsMargins(4, 4, 4, 4)
        grid.setSpacing(8)

        cols = 3
        for i, ach in enumerate(ACHIEVEMENTS):
            row, col = i // cols, i % cols
            tile = self._make_tile(ach)
            grid.addWidget(tile, row, col)

        scroll.setWidget(container)
        layout.addWidget(scroll, 1)

        btn_row = QHBoxLayout()
        btn_row.addStretch(1)
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        btn_row.addWidget(close_btn)
        layout.addLayout(btn_row)

    def _make_tile(self, ach):
        tile = QFrame()
        tile.setObjectName("PanelFrame")
        tile.setMinimumHeight(120)
        tl = QVBoxLayout(tile)
        tl.setContentsMargins(10, 8, 10, 8)
        tl.setSpacing(4)

        unlocked = self.save.has_achievement(ach.id)

        # Icon row
        icon_lbl = QLabel(ach.icon if unlocked else "?")
        if unlocked:
            icon_lbl.setStyleSheet(
                f"color: {COLORS['text_bright']}; font-size: 32px; font-weight: bold; "
                f"font-family: 'DejaVu Sans Mono', monospace;"
            )
        else:
            icon_lbl.setStyleSheet(
                f"color: {COLORS['text_dim']}; font-size: 32px; font-weight: bold; "
                f"font-family: 'DejaVu Sans Mono', monospace;"
            )
        icon_lbl.setAlignment(Qt.AlignCenter)
        tl.addWidget(icon_lbl)

        # Name
        name_lbl = QLabel(ach.name if unlocked else "???")
        if unlocked:
            name_lbl.setStyleSheet(
                f"color: {COLORS['text_amber']}; font-weight: bold; font-size: 13px;"
            )
        else:
            name_lbl.setStyleSheet(
                f"color: {COLORS['text_dim']}; font-weight: bold; font-size: 13px;"
            )
        name_lbl.setAlignment(Qt.AlignCenter)
        name_lbl.setWordWrap(True)
        tl.addWidget(name_lbl)

        # Description
        desc_lbl = QLabel(ach.description if unlocked else "Locked - keep playing to unlock.")
        desc_lbl.setStyleSheet(
            f"color: {COLORS['text_main'] if unlocked else COLORS['text_dim']}; "
            f"font-size: 11px;"
        )
        desc_lbl.setWordWrap(True)
        desc_lbl.setAlignment(Qt.AlignCenter)
        tl.addWidget(desc_lbl)

        return tile

    def _refresh(self):
        # Tiles are built once in _build_ui using live save state - no refresh needed
        pass
