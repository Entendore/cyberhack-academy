"""Terminal widget - simulated shell with history, autocomplete, pipes."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QPlainTextEdit, QLineEdit, QLabel,
    QHBoxLayout,
)
from PySide6.QtGui import (
    QTextCursor, QFont, QKeyEvent,
)


# Mono font fallback chain
_MONO_FAMILIES = [
    "DejaVu Sans Mono",
    "Liberation Mono",
    "Courier New",
    "monospace",
]


def _pick_mono_font() -> QFont:
    f = QFont()
    for name in _MONO_FAMILIES:
        f.setFamily(name)
        if f.exactMatch():
            return f
    f.setFamily(_MONO_FAMILIES[0])
    return f


class TerminalWidget(QWidget):
    """A self-contained terminal: output area + input line.

    Emits `command_entered(str)` when the user submits a line.
    Call `append_output(text)` to print to the output area.

    File-name Tab completion: set_fs_provider(callable) to a function that
    returns the current list of files in the working directory.
    """

    command_entered = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._prompt = "operator@cyberhack:~$ "
        self._history: list[str] = []
        self._history_idx: int = -1
        self._command_words: list[str] = []
        self._fs_provider = None   # callable -> list[str]
        self._setup_ui()

    # ------------------------------------------------------------------
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.output = QPlainTextEdit()
        self.output.setObjectName("TerminalOutput")
        self.output.setReadOnly(True)
        self.output.setFont(_pick_mono_font())
        self.output.setMaximumBlockCount(10000)
        layout.addWidget(self.output, 1)

        # Input row
        input_row = QWidget()
        input_layout = QHBoxLayout(input_row)
        input_layout.setContentsMargins(6, 4, 6, 4)
        input_layout.setSpacing(6)

        self.prompt_label = QLabel(self._prompt)
        self.prompt_label.setStyleSheet(
            "color: #39ff14; font-family: 'DejaVu Sans Mono', monospace; font-size: 14px;"
        )
        self.prompt_label.setFont(_pick_mono_font())

        self.input = _CommandLine(self)
        self.input.setFont(_pick_mono_font())
        self.input.setPlaceholderText("type 'help' and press Enter...")
        self.input.returnPressed.connect(self._on_enter)
        self.input.upPressed.connect(self._history_back)
        self.input.downPressed.connect(self._history_forward)
        self.input.tabPressed.connect(self._on_tab)

        input_layout.addWidget(self.prompt_label)
        input_layout.addWidget(self.input, 1)
        layout.addWidget(input_row)

    # ------------------------------------------------------------------
    # Public API
    def set_prompt(self, prompt: str):
        self._prompt = prompt
        self.prompt_label.setText(prompt)

    def clear_output(self):
        self.output.clear()

    def append_output(self, text: str):
        if text == "__CLEAR__":
            self.clear_output()
            return
        cursor = self.output.textCursor()
        cursor.movePosition(QTextCursor.End)
        if self.output.toPlainText() and not self.output.toPlainText().endswith("\n"):
            cursor.insertText("\n")
        cursor.insertText(text)
        cursor.insertText("\n")
        self.output.setTextCursor(cursor)
        self.output.ensureCursorVisible()

    def append_prompt_with_input(self, line: str):
        self.append_output(f"{self._prompt}{line}")

    def set_completions(self, words: list[str]):
        self._command_words = list(words)

    def set_fs_provider(self, provider):
        """Set a callable that returns the current list of files for Tab completion."""
        self._fs_provider = provider

    # ------------------------------------------------------------------
    # Slots
    def _on_enter(self):
        text = self.input.text()
        if not text.strip():
            self.append_output(f"{self._prompt}")
            self.input.clear()
            return
        self._history.append(text)
        self._history_idx = len(self._history)
        self.input.clear()
        self.command_entered.emit(text)

    def _history_back(self):
        if not self._history:
            return
        if self._history_idx > 0:
            self._history_idx -= 1
        self.input.setText(self._history[self._history_idx])

    def _history_forward(self):
        if not self._history:
            return
        if self._history_idx < len(self._history) - 1:
            self._history_idx += 1
            self.input.setText(self._history[self._history_idx])
        else:
            self._history_idx = len(self._history)
            self.input.clear()

    def _on_tab(self):
        text = self.input.text()
        if not text:
            return
        parts = text.split()
        # If only one token, complete command name
        if len(parts) == 1 and not text.endswith(" "):
            prefix = parts[0]
            candidates = [w for w in self._command_words if w.startswith(prefix)]
            if len(candidates) == 1:
                self.input.setText(candidates[0] + " ")
            elif len(candidates) > 1:
                self.append_output(f"{self._prompt}{text}")
                self.append_output("  ".join(candidates))
            return
        # Otherwise, complete the last token as a filename (if we have a fs_provider)
        if self._fs_provider is None:
            return
        last_token = parts[-1] if not text.endswith(" ") else ""
        if not last_token:
            return
        files = self._fs_provider() or []
        candidates = [f for f in files if f.startswith(last_token)]
        if len(candidates) == 1:
            parts[-1] = candidates[0]
            self.input.setText(" ".join(parts) + " ")
        elif len(candidates) > 1:
            self.append_output(f"{self._prompt}{text}")
            self.append_output("  ".join(candidates))

    def focus_input(self):
        self.input.setFocus()


class _CommandLine(QLineEdit):
    """QLineEdit that emits custom signals for Up/Down/Tab."""

    upPressed = Signal()
    downPressed = Signal()
    tabPressed = Signal()

    def keyPressEvent(self, e: QKeyEvent):
        k = e.key()
        if k == Qt.Key_Up:
            self.upPressed.emit()
            return
        if k == Qt.Key_Down:
            self.downPressed.emit()
            return
        if k == Qt.Key_Tab:
            self.tabPressed.emit()
            return
        super().keyPressEvent(e)
