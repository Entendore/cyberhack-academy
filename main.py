#!/usr/bin/env python3
"""CyberHack Academy - a PySide6 hacking game for learning computer security.

Run with:    python3 main.py

No shell launcher required - this entry point handles all the system
quirks (missing libEGL on minimal Linux installs, offscreen fallback for
headless testing) inside Python itself.
"""

import sys
import os


def _bootstrap_qt_libs():
    """Best-effort fix for missing libEGL on some Linux distros.

    If libEGL.so.1 isn't on the system, search a few well-known locations
    (Playwright/Chrome browser caches, ~/.local/lib) and re-exec ourselves
    with LD_LIBRARY_PATH set so Qt's dlopen can find it.

    No-op on Windows / macOS / systems where libEGL is already present.
    """
    if not sys.platform.startswith("linux"):
        return

    # Already loadable? Done.
    try:
        import ctypes
        ctypes.CDLL("libEGL.so.1")
        return
    except OSError:
        pass

    # Build a search list of candidate libEGL.so files.
    candidates: list[str] = []
    home = os.path.expanduser("~")

    # 1. ~/.local/lib (where the user / a previous run may have placed it)
    candidates.append(os.path.join(home, ".local", "lib", "libEGL.so.1"))
    candidates.append(os.path.join(home, ".local", "lib", "libEGL.so"))

    # 2. Playwright browser cache
    playwright_cache = os.path.join(home, ".cache", "ms-playwright")
    if os.path.isdir(playwright_cache):
        for root, _dirs, files in os.walk(playwright_cache):
            for f in files:
                if f.startswith("libEGL.so"):
                    candidates.append(os.path.join(root, f))

    # 3. agent-browser cache
    agent_browser = os.path.join(home, ".agent-browser", "browsers")
    if os.path.isdir(agent_browser):
        for root, _dirs, files in os.walk(agent_browser):
            for f in files:
                if f.startswith("libEGL.so"):
                    candidates.append(os.path.join(root, f))

    # 4. System locations
    candidates.extend([
        "/usr/lib/x86_64-linux-gnu/libEGL.so.1",
        "/usr/lib/libEGL.so.1",
        "/lib/x86_64-linux-gnu/libEGL.so.1",
    ])

    for c in candidates:
        if os.path.exists(c):
            d = os.path.dirname(c)
            existing = os.environ.get("LD_LIBRARY_PATH", "")
            os.environ["LD_LIBRARY_PATH"] = f"{d}:{existing}" if existing else d
            # Also pull in libGLESv2.so.2 from the same dir if present
            glesv2 = os.path.join(d, "libGLESv2.so.2")
            if os.path.exists(glesv2):
                # Already covered by the LD_LIBRARY_PATH above
                pass
            # Re-exec so the new env takes effect for Qt's dlopen
            os.execv(sys.executable, [sys.executable] + sys.argv)
            return  # unreachable


def main():
    _bootstrap_qt_libs()

    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import Qt
    from game.styles import build_stylesheet, get_theme
    from game.main_window import MainWindow
    from game import __app_name__, __version__

    # High DPI
    try:
        QApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )
    except Exception:
        pass

    app = QApplication(sys.argv)
    app.setApplicationName(__app_name__)
    app.setApplicationVersion(__version__)
    app.setStyle("Fusion")

    # Load persisted theme (default = green terminal)
    from game.save_manager import SaveManager
    tmp_save = SaveManager()
    theme_name = tmp_save.get_settings().get("theme", "green")
    app.setStyleSheet(build_stylesheet(get_theme(theme_name)))

    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
