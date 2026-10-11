"""Stats dashboard dialog - shows progress breakdown by topic + global stats."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QTableWidget,
    QTableWidgetItem, QHeaderView, QPushButton, QProgressBar,
)

from .save_manager import SaveManager
from .missions import ALL_MISSIONS, CATEGORY_MISSIONS
from .achievements import ACHIEVEMENTS
from .styles import COLORS


class StatsDialog(QDialog):
    def __init__(self, save: SaveManager, parent=None):
        super().__init__(parent)
        self.save = save
        self.setWindowTitle("STATS - Operator Dashboard")
        self.resize(720, 620)
        self._build_ui()
        self._refresh()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        title = QLabel("OPERATOR DASHBOARD")
        title.setObjectName("TitleLabel")
        layout.addWidget(title)

        sub = QLabel("Your training progress at a glance.")
        sub.setObjectName("SubtitleLabel")
        layout.addWidget(sub)

        # ---- Top: 4 stat tiles ----
        tiles_row = QHBoxLayout()
        tiles_row.setSpacing(6)
        stats = self.save.stats_summary()
        n_ach = stats["achievements"]
        n_total_ach = len(ACHIEVEMENTS)
        self._tiles = []
        for label, value, color in [
            ("Missions",    f"{stats['missions_completed']}/{len(ALL_MISSIONS)}", COLORS["text_bright"]),
            ("Total score", f"{stats['total_score']}",                            COLORS["text_amber"]),
            ("Achievements",f"{n_ach}/{n_total_ach}",                             COLORS["text_cyan"]),
            ("Codex",       f"{stats['codex_unlocked']}",                         COLORS["text_magenta"]),
        ]:
            tile = QFrame()
            tile.setObjectName("PanelFrame")
            tl = QVBoxLayout(tile)
            tl.setContentsMargins(8, 6, 8, 6)
            lbl_top = QLabel(label.upper())
            lbl_top.setObjectName("SubtitleLabel")
            lbl_val = QLabel(value)
            lbl_val.setStyleSheet(f"color: {color}; font-size: 22px; font-weight: bold;")
            tl.addWidget(lbl_top)
            tl.addWidget(lbl_val)
            tiles_row.addWidget(tile)
            self._tiles.append((label, lbl_val))
        layout.addLayout(tiles_row)

        # ---- Per-category progress bars ----
        cat_frame = QFrame()
        cat_frame.setObjectName("PanelFrame")
        cat_l = QVBoxLayout(cat_frame)
        cat_l.setContentsMargins(8, 6, 8, 6)
        cat_title = QLabel("PROGRESS BY CATEGORY")
        cat_title.setObjectName("SectionLabel")
        cat_l.addWidget(cat_title)
        self._cat_bars: list[tuple[str, QProgressBar, QLabel]] = []
        for cat, mids in CATEGORY_MISSIONS.items():
            row = QHBoxLayout()
            row.setSpacing(8)
            lbl = QLabel(cat)
            lbl.setMinimumWidth(220)
            row.addWidget(lbl)
            bar = QProgressBar()
            bar.setRange(0, len(mids))
            row.addWidget(bar, 1)
            val_lbl = QLabel("0/0")
            val_lbl.setMinimumWidth(50)
            val_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            row.addWidget(val_lbl)
            cat_l.addLayout(row)
            self._cat_bars.append((cat, bar, val_lbl))
        layout.addWidget(cat_frame)

        # ---- Mission table ----
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Mission", "Category", "Difficulty", "Score", "Best Time"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(self.table, 1)

        # ---- Global stats line ----
        self.summary_lbl = QLabel("")
        self.summary_lbl.setObjectName("BriefingLabel")
        self.summary_lbl.setWordWrap(True)
        layout.addWidget(self.summary_lbl)

        # Close
        btn_row = QHBoxLayout()
        btn_row.addStretch(1)
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        btn_row.addWidget(close_btn)
        layout.addLayout(btn_row)

    def _refresh(self):
        stats = self.save.stats_summary()
        # Update tiles
        self._tiles[0][1].setText(f"{stats['missions_completed']}/{len(ALL_MISSIONS)}")
        self._tiles[1][1].setText(f"{stats['total_score']}")
        self._tiles[2][1].setText(f"{stats['achievements']}/{len(ACHIEVEMENTS)}")
        self._tiles[3][1].setText(f"{stats['codex_unlocked']}")

        # Category progress
        for cat, bar, val_lbl in self._cat_bars:
            mids = CATEGORY_MISSIONS.get(cat, [])
            done = sum(1 for m in mids if self.save.is_completed(m))
            bar.setValue(done)
            val_lbl.setText(f"{done}/{len(mids)}")

        # Mission table
        self.table.setRowCount(len(ALL_MISSIONS))
        for i, m in enumerate(ALL_MISSIONS):
            completed = self.save.is_completed(m)
            unlocked = self.save.is_unlocked(m.id)
            score = self.save.get_score(m.id)
            best = self.save.get_best_time(m.id)

            if completed:
                status = m.title
            elif unlocked:
                status = m.title + "  (in progress)"
            else:
                status = "??? (locked)"
            self.table.setItem(i, 0, QTableWidgetItem(status))
            self.table.setItem(i, 1, QTableWidgetItem(m.category))
            self.table.setItem(i, 2, QTableWidgetItem(m.difficulty))
            self.table.setItem(i, 3, QTableWidgetItem(str(score) if completed else "-"))
            self.table.setItem(i, 4, QTableWidgetItem(
                f"{best:.1f}s" if best is not None else "-"
            ))

        # Summary line
        self.summary_lbl.setText(
            f"<b>Overall:</b> {stats['missions_completed']} missions completed &middot; "
            f"<b>{stats['total_score']}</b> total points &middot; "
            f"<b>{stats['total_time_s']:.0f}s</b> total playtime &middot; "
            f"<b>{stats['avg_time_s']:.1f}s</b> average per mission &middot; "
            f"<b>{stats['total_hints']}</b> hints used &middot; "
            f"<b>{stats['codex_unlocked']}</b> codex entries unlocked."
        )
