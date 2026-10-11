"""QSS stylesheet + multiple color palettes for the hacker-terminal aesthetic."""

# ---------------------------------------------------------------------------
# Themes - each is a complete color palette
# ---------------------------------------------------------------------------

THEMES: dict[str, dict[str, str]] = {
    "green": {
        "name":            "Green Terminal",
        "bg_deep":         "#050708",
        "bg_panel":        "#0a0f10",
        "bg_terminal":     "#020503",
        "bg_input":        "#08120c",
        "border":          "#1f3a26",
        "border_strong":   "#2f7a3f",
        "text_main":       "#c8f7c5",
        "text_dim":        "#5a8a63",
        "text_bright":     "#39ff14",
        "text_amber":      "#ffb000",
        "text_red":        "#ff4d4d",
        "text_cyan":       "#56d4ff",
        "text_magenta":    "#ff77ff",
        "selection":       "#1f5a2f",
    },
    "amber": {
        "name":            "Amber Retro",
        "bg_deep":         "#0a0700",
        "bg_panel":        "#120c00",
        "bg_terminal":     "#050300",
        "bg_input":        "#1a1000",
        "border":          "#3a2a00",
        "border_strong":   "#7a5500",
        "text_main":       "#ffd980",
        "text_dim":        "#8a6630",
        "text_bright":     "#ffb000",
        "text_amber":      "#ff8c1a",
        "text_red":        "#ff6040",
        "text_cyan":       "#ffe080",
        "text_magenta":    "#ffaa55",
        "selection":       "#5a3f00",
    },
    "cyberpunk": {
        "name":            "Cyberpunk Neon",
        "bg_deep":         "#0a0014",
        "bg_panel":        "#14001f",
        "bg_terminal":     "#05000d",
        "bg_input":        "#1a0028",
        "border":          "#3a0050",
        "border_strong":   "#7700b3",
        "text_main":       "#e0c0ff",
        "text_dim":        "#7a5a9a",
        "text_bright":     "#ff00ff",
        "text_amber":      "#ffea00",
        "text_red":        "#ff2266",
        "text_cyan":       "#00f0ff",
        "text_magenta":    "#ff44ff",
        "selection":       "#3a0066",
    },
}

DEFAULT_THEME = "green"


# Backwards-compat: COLORS is the active palette dict
COLORS = THEMES[DEFAULT_THEME]


def get_theme(name: str) -> dict[str, str]:
    """Return the palette for the given theme name (falls back to default)."""
    return THEMES.get(name, THEMES[DEFAULT_THEME])


def list_themes() -> list[tuple[str, str]]:
    """Return [(id, name), ...] for all available themes."""
    return [(k, v["name"]) for k, v in THEMES.items()]


def build_stylesheet(c: dict = COLORS) -> str:
    """Return the full QSS stylesheet for the given palette."""
    return f"""
    QWidget {{
        background-color: {c['bg_deep']};
        color: {c['text_main']};
        font-family: 'DejaVu Sans Mono', 'Liberation Mono', 'Courier New', monospace;
        font-size: 13px;
    }}

    QMainWindow {{
        background-color: {c['bg_deep']};
    }}

    QFrame#PanelFrame {{
        background-color: {c['bg_panel']};
        border: 1px solid {c['border']};
        border-radius: 4px;
    }}

    QFrame#TerminalFrame {{
        background-color: {c['bg_terminal']};
        border: 1px solid {c['border_strong']};
        border-radius: 4px;
    }}

    QLabel#TitleLabel {{
        color: {c['text_bright']};
        font-size: 18px;
        font-weight: bold;
        padding: 4px 0px;
        letter-spacing: 2px;
    }}

    QLabel#SubtitleLabel {{
        color: {c['text_dim']};
        font-size: 11px;
        letter-spacing: 1px;
    }}

    QLabel#SectionLabel {{
        color: {c['text_amber']};
        font-size: 12px;
        font-weight: bold;
        letter-spacing: 1px;
        padding: 2px 0px;
        border-bottom: 1px dashed {c['border']};
    }}

    QLabel#BriefingLabel {{
        color: {c['text_main']};
        font-size: 13px;
        padding: 6px;
    }}

    QLabel#StatusValue {{
        color: {c['text_bright']};
        font-weight: bold;
    }}

    QLabel#FlagLabel {{
        color: {c['text_amber']};
        font-weight: bold;
        font-size: 14px;
    }}

    QLabel#AsciiBanner {{
        color: {c['text_bright']};
        font-family: 'DejaVu Sans Mono', 'Liberation Mono', monospace;
        font-size: 11px;
        padding: 4px;
    }}

    QLabel#TimerLabel {{
        color: {c['text_amber']};
        font-weight: bold;
        font-size: 14px;
        padding: 2px 8px;
        background: {c['bg_panel']};
        border: 1px solid {c['border']};
        border-radius: 3px;
    }}

    QLabel#TimerLabelWarn {{
        color: {c['text_red']};
        font-weight: bold;
        font-size: 14px;
        padding: 2px 8px;
        background: {c['bg_panel']};
        border: 1px solid {c['text_red']};
        border-radius: 3px;
    }}

    QTextEdit, QPlainTextEdit {{
        background-color: {c['bg_terminal']};
        color: {c['text_main']};
        border: 1px solid {c['border']};
        border-radius: 3px;
        padding: 6px;
        font-family: 'DejaVu Sans Mono', 'Liberation Mono', 'Courier New', monospace;
        font-size: 13px;
        selection-background-color: {c['selection']};
    }}

    QTextEdit#TerminalOutput, QPlainTextEdit#TerminalOutput {{
        background-color: {c['bg_terminal']};
        color: {c['text_main']};
        border: none;
        border-radius: 0px;
        padding: 8px;
    }}

    QLineEdit#CommandLine {{
        background-color: {c['bg_input']};
        color: {c['text_bright']};
        border: 1px solid {c['border']};
        border-radius: 3px;
        padding: 6px 8px;
        font-family: 'DejaVu Sans Mono', 'Liberation Mono', 'Courier New', monospace;
        font-size: 14px;
    }}

    QLineEdit#CommandLine:focus {{
        border: 1px solid {c['text_bright']};
    }}

    QPushButton {{
        background-color: {c['bg_panel']};
        color: {c['text_main']};
        border: 1px solid {c['border_strong']};
        border-radius: 3px;
        padding: 6px 14px;
        font-family: 'DejaVu Sans Mono', 'Liberation Mono', 'Courier New', monospace;
    }}

    QPushButton:hover {{
        background-color: {c['selection']};
        color: {c['text_bright']};
        border: 1px solid {c['text_bright']};
    }}

    QPushButton:pressed {{
        background-color: {c['border_strong']};
    }}

    QPushButton:disabled {{
        color: {c['text_dim']};
        border: 1px solid {c['border']};
    }}

    QPushButton#PrimaryButton {{
        background-color: {c['border_strong']};
        color: {c['bg_terminal']};
        font-weight: bold;
    }}

    QPushButton#PrimaryButton:hover {{
        background-color: {c['text_bright']};
        color: {c['bg_terminal']};
    }}

    QListWidget {{
        background-color: {c['bg_panel']};
        color: {c['text_main']};
        border: 1px solid {c['border']};
        border-radius: 3px;
        padding: 4px;
        outline: 0;
    }}

    QListWidget::item {{
        padding: 6px 8px;
        border-bottom: 1px dashed {c['border']};
    }}

    QListWidget::item:selected {{
        background-color: {c['selection']};
        color: {c['text_bright']};
    }}

    QListWidget::item:hover {{
        background-color: {c['bg_input']};
    }}

    QScrollBar:vertical {{
        background: {c['bg_panel']};
        width: 10px;
        border: none;
    }}

    QScrollBar::handle:vertical {{
        background: {c['border_strong']};
        min-height: 24px;
        border-radius: 4px;
    }}

    QScrollBar::handle:vertical:hover {{
        background: {c['text_bright']};
    }}

    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}

    QScrollBar:horizontal {{
        background: {c['bg_panel']};
        height: 10px;
        border: none;
    }}

    QScrollBar::handle:horizontal {{
        background: {c['border_strong']};
        min-width: 24px;
        border-radius: 4px;
    }}

    QStatusBar {{
        background-color: {c['bg_panel']};
        color: {c['text_dim']};
        border-top: 1px solid {c['border']};
    }}

    QMenuBar {{
        background-color: {c['bg_panel']};
        color: {c['text_main']};
        border-bottom: 1px solid {c['border']};
    }}

    QMenuBar::item:selected {{
        background-color: {c['selection']};
    }}

    QMenu {{
        background-color: {c['bg_panel']};
        color: {c['text_main']};
        border: 1px solid {c['border_strong']};
    }}

    QMenu::item:selected {{
        background-color: {c['selection']};
    }}

    QDialog {{
        background-color: {c['bg_deep']};
    }}

    QTabWidget::pane {{
        border: 1px solid {c['border']};
        background: {c['bg_panel']};
    }}

    QTabBar::tab {{
        background: {c['bg_panel']};
        color: {c['text_dim']};
        padding: 6px 14px;
        border: 1px solid {c['border']};
        border-bottom: none;
    }}

    QTabBar::tab:selected {{
        background: {c['bg_terminal']};
        color: {c['text_bright']};
        border: 1px solid {c['text_bright']};
        border-bottom: none;
    }}

    QProgressBar {{
        background-color: {c['bg_input']};
        border: 1px solid {c['border']};
        border-radius: 3px;
        text-align: center;
        color: {c['text_bright']};
    }}

    QProgressBar::chunk {{
        background-color: {c['text_bright']};
        border-radius: 2px;
    }}

    QTableWidget {{
        background-color: {c['bg_panel']};
        color: {c['text_main']};
        gridline-color: {c['border']};
        border: 1px solid {c['border']};
    }}

    QHeaderView::section {{
        background-color: {c['bg_input']};
        color: {c['text_amber']};
        padding: 4px;
        border: 0px;
        border-bottom: 1px solid {c['border_strong']};
        font-weight: bold;
    }}

    QTableWidget::item:selected {{
        background-color: {c['selection']};
    }}
    """


# ANSI-like color codes used in terminal output (mapped to a subset of QSS colors)
class Ansi:
    RESET = "\x1b[0m"
    BRIGHT = "\x1b[1m"
    DIM = "\x1b[2m"
    RED = "\x1b[31m"
    GREEN = "\x1b[32m"
    YELLOW = "\x1b[33m"
    BLUE = "\x1b[34m"
    MAGENTA = "\x1b[35m"
    CYAN = "\x1b[36m"
    AMBER = "\x1b[93m"
