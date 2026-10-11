"""Codex (glossary) dialog - shows unlocked security terms."""

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QListWidget,
    QListWidgetItem, QTextEdit, QPushButton, QLineEdit, QSplitter,
    QWidget, QFrame,
)

from .codex import codex_terms
from .save_manager import SaveManager
from .styles import COLORS


class CodexDialog(QDialog):
    """Modal-ish dialog showing the glossary, with unlocked/locked states."""

    def __init__(self, save: SaveManager, parent=None):
        super().__init__(parent)
        self.save = save
        self.setWindowTitle("CODEX - Security Glossary")
        self.resize(880, 560)
        self._build_ui()
        self._populate()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(8)

        title = QLabel("CODEX :: SECURITY GLOSSARY")
        title.setObjectName("TitleLabel")
        root.addWidget(title)

        sub = QLabel("Terms unlock as you complete missions. Locked terms are redacted.")
        sub.setObjectName("SubtitleLabel")
        root.addWidget(sub)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setStyleSheet(f"QSplitter::handle {{ background: {COLORS['border']}; }}")

        # Left: list of terms
        left = QFrame()
        left.setObjectName("PanelFrame")
        left_l = QVBoxLayout(left)
        left_l.setContentsMargins(6, 6, 6, 6)
        left_l.setSpacing(4)

        self.search = QLineEdit()
        self.search.setPlaceholderText("filter...")
        self.search.textChanged.connect(self._filter)
        left_l.addWidget(self.search)

        self.list_widget = QListWidget()
        self.list_widget.itemClicked.connect(self._on_select)
        left_l.addWidget(self.list_widget, 1)

        splitter.addWidget(left)

        # Right: detail
        right = QFrame()
        right.setObjectName("PanelFrame")
        right_l = QVBoxLayout(right)
        right_l.setContentsMargins(8, 8, 8, 8)
        right_l.setSpacing(6)

        self.term_title = QLabel("(select a term)")
        self.term_title.setObjectName("SectionLabel")
        right_l.addWidget(self.term_title)

        self.term_body = QTextEdit()
        self.term_body.setReadOnly(True)
        right_l.addWidget(self.term_body, 1)

        splitter.addWidget(right)
        splitter.setSizes([280, 600])
        root.addWidget(splitter, 1)

        # Close button
        btn_row = QHBoxLayout()
        btn_row.addStretch(1)
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        btn_row.addWidget(close_btn)
        root.addLayout(btn_row)

    def _populate(self):
        self.list_widget.clear()
        for term_id, term, category, definition in codex_terms():
            unlocked = self.save.is_codex_unlocked(term_id)
            label = term if unlocked else "??? (locked)"
            item = QListWidgetItem(f"[{category}] {label}")
            item.setData(Qt.UserRole, term_id)
            if not unlocked:
                f = item.foreground()
                f.setColor(QColor(COLORS["text_dim"]))
                item.setForeground(f)
            self.list_widget.addItem(item)
        if self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(0)
            self._on_select(self.list_widget.item(0))

    def _filter(self, text: str):
        text = text.lower().strip()
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            item.setHidden(text not in item.text().lower())

    def _on_select(self, item: QListWidgetItem):
        if item is None:
            return
        term_id = item.data(Qt.UserRole)
        unlocked = self.save.is_codex_unlocked(term_id)
        if not unlocked:
            self.term_title.setText("??? (locked)")
            self.term_body.setPlainText(
                "This term is locked. Complete more missions to unlock it.\n"
                "Each mission unlocks 2-5 new glossary entries."
            )
            return
        # Find the term entry
        from .codex import CODEX_BY_ID
        entry = CODEX_BY_ID.get(term_id)
        if entry is None:
            return
        _, term, category, definition = entry
        self.term_title.setText(f"{term}   [{category}]")
        self.term_body.setPlainText(definition)
