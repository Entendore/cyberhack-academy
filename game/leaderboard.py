"""Leaderboard dialog - shows local high scores."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QListWidget,
    QListWidgetItem, QPushButton, QLineEdit, QFrame, QTableWidget,
    QTableWidgetItem, QHeaderView, QMessageBox,
)

from .save_manager import SaveManager
from .styles import COLORS


class LeaderboardDialog(QDialog):
    """Show local high scores + allow the player to submit their total."""

    def __init__(self, save: SaveManager, parent=None):
        super().__init__(parent)
        self.save = save
        self.setWindowTitle("LEADERBOARD - Local High Scores")
        self.resize(540, 480)
        self._build_ui()
        self._refresh()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        title = QLabel("LEADERBOARD :: LOCAL")
        title.setObjectName("TitleLabel")
        layout.addWidget(title)

        sub = QLabel("Submit your current total to the leaderboard. Scores are stored locally in ~/.cyberhack/save.json")
        sub.setObjectName("SubtitleLabel")
        sub.setWordWrap(True)
        layout.addWidget(sub)

        # Current total
        total = self.save.total_score()
        total_lbl = QLabel(f"Your current total: <b style='color:{COLORS['text_bright']}'>{total}</b> points")
        total_lbl.setObjectName("BriefingLabel")
        layout.addWidget(total_lbl)

        # Submit row
        submit_row = QHBoxLayout()
        submit_row.setSpacing(6)
        self.name_edit = QLineEdit(self.save.player_name)
        self.name_edit.setPlaceholderText("your handle")
        submit_row.addWidget(QLabel("handle:"))
        submit_row.addWidget(self.name_edit, 1)
        submit_btn = QPushButton("Submit Score")
        submit_btn.setObjectName("PrimaryButton")
        submit_btn.clicked.connect(self._submit)
        submit_row.addWidget(submit_btn)
        layout.addLayout(submit_row)

        # Table
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["#", "Handle", "Score"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(self.table, 1)

        btn_row = QHBoxLayout()
        clear_btn = QPushButton("Clear Leaderboard")
        clear_btn.clicked.connect(self._clear)
        btn_row.addWidget(clear_btn)
        btn_row.addStretch(1)
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        btn_row.addWidget(close_btn)
        layout.addLayout(btn_row)

    def _refresh(self):
        entries = self.save.get_leaderboard()
        self.table.setRowCount(len(entries))
        for i, e in enumerate(entries):
            rank = QTableWidgetItem(str(i + 1))
            name = QTableWidgetItem(e.get("name", "?"))
            score = QTableWidgetItem(str(e.get("total", 0)))
            score.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(i, 0, rank)
            self.table.setItem(i, 1, name)
            self.table.setItem(i, 2, score)

    def _submit(self):
        name = self.name_edit.text().strip() or "Operator"
        self.save.set_player_name(name)
        total = self.save.total_score()
        if total <= 0:
            QMessageBox.information(self, "No score",
                                    "Complete at least one mission to submit a score.")
            return
        self.save.add_leaderboard_entry(name, total)
        self._refresh()

    def _clear(self):
        btn = QMessageBox.question(self, "Confirm",
                                   "Clear all leaderboard entries? This cannot be undone.")
        if btn == QMessageBox.Yes:
            self.save._data["leaderboard"] = []
            self.save.save()
            self._refresh()
