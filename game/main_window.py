"""Main application window - ties missions, terminal, scoring, hints,
achievements, themes, boot animation, scanline overlay, and timer together."""

from __future__ import annotations
import time
from typing import Optional

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction, QFont, QKeySequence, QColor
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QSplitter, QFrame, QStatusBar, QMessageBox,
    QMenu, QCheckBox, QInputDialog, QApplication,
)

from .styles import build_stylesheet, get_theme, list_themes, COLORS
from .save_manager import SaveManager
from .sounds import SoundManager
from .terminal import TerminalWidget
from .missions import (
    ALL_MISSIONS, MISSION_TOPICS, CATEGORY_MISSIONS, Mission, MissionResult,
)
from .codex_dialog import CodexDialog
from .leaderboard import LeaderboardDialog
from .stats_dialog import StatsDialog
from .achievements_dialog import AchievementsDialog
from .achievements import get_achievement, ACHIEVEMENTS
from .scanlines import ScanlineOverlay
from .ascii import app_banner, boot_lines


APP_NAME = "CyberHack Academy"
APP_VERSION = "1.1.0"


class MainWindow(QMainWindow):
    """Top-level window."""

    def __init__(self):
        super().__init__()
        self.save = SaveManager()
        self.sound = SoundManager(enabled=self.save.get_settings().get("sound", True))
        self.missions: dict[str, Mission] = {m.id: m for m in ALL_MISSIONS}
        self.current_mission: Optional[Mission] = None
        self.current_mission_class = None
        self.mission_start_time: float = 0.0
        self._in_mission: bool = False

        # In-mission timer (updates status bar every second)
        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._on_timer_tick)

        # Boot animation state
        self._boot_lines_queue: list[str] = []
        self._boot_timer = QTimer(self)
        self._boot_timer.setInterval(120)
        self._boot_timer.timeout.connect(self._on_boot_tick)

        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.resize(1320, 840)
        self._build_ui()
        self._build_menu()
        self._refresh_mission_list()
        self._update_status_panel()
        self._apply_scanline_setting()
        self._start_boot_animation()

    # ------------------------------------------------------------------
    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(8)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)

        # --- LEFT: banner + mission select ---
        left = QFrame()
        left.setObjectName("PanelFrame")
        left_l = QVBoxLayout(left)
        left_l.setContentsMargins(8, 8, 8, 8)
        left_l.setSpacing(6)

        # ASCII banner
        self.banner_label = QLabel(app_banner())
        self.banner_label.setObjectName("AsciiBanner")
        left_l.addWidget(self.banner_label)

        lbl = QLabel("MISSIONS")
        lbl.setObjectName("SectionLabel")
        left_l.addWidget(lbl)

        self.mission_list = QListWidget()
        self.mission_list.itemDoubleClicked.connect(self._on_mission_double_click)
        left_l.addWidget(self.mission_list, 1)

        # Player + score
        self.player_label = QLabel("Operator: -")
        self.player_label.setObjectName("BriefingLabel")
        left_l.addWidget(self.player_label)
        self.score_label = QLabel("Total score: 0")
        self.score_label.setObjectName("BriefingLabel")
        left_l.addWidget(self.score_label)

        # Achievements summary
        self.achievement_label = QLabel("Badges: 0/" + str(len(ACHIEVEMENTS)))
        self.achievement_label.setObjectName("BriefingLabel")
        left_l.addWidget(self.achievement_label)

        # Action buttons
        self.play_btn = QPushButton("Start Mission")
        self.play_btn.setObjectName("PrimaryButton")
        self.play_btn.clicked.connect(self._on_play_clicked)
        left_l.addWidget(self.play_btn)

        self.hint_btn = QPushButton("Request Hint")
        self.hint_btn.clicked.connect(self._on_hint_clicked)
        self.hint_btn.setEnabled(False)
        left_l.addWidget(self.hint_btn)

        left_l.addStretch(0)
        splitter.addWidget(left)

        # --- RIGHT: header + briefing + terminal + scanlines overlay ---
        right_wrapper = QWidget()
        right_l_wrap = QVBoxLayout(right_wrapper)
        right_l_wrap.setContentsMargins(0, 0, 0, 0)
        right_l_wrap.setSpacing(0)

        right = QFrame()
        right.setObjectName("TerminalFrame")
        right_l = QVBoxLayout(right)
        right_l.setContentsMargins(8, 8, 8, 8)
        right_l.setSpacing(6)

        # Header row (title + category + timer)
        header_row = QHBoxLayout()
        header_row.setSpacing(8)
        self.mission_title = QLabel("Select a mission to begin")
        self.mission_title.setObjectName("TitleLabel")
        header_row.addWidget(self.mission_title, 1)

        self.cat_label = QLabel("")
        self.cat_label.setObjectName("SectionLabel")
        header_row.addWidget(self.cat_label)

        self.timer_label = QLabel("")
        self.timer_label.setObjectName("TimerLabel")
        self.timer_label.setVisible(False)
        header_row.addWidget(self.timer_label)
        right_l.addLayout(header_row)

        self.objective_label = QLabel("")
        self.objective_label.setObjectName("BriefingLabel")
        self.objective_label.setWordWrap(True)
        right_l.addWidget(self.objective_label)

        self.briefing_label = QLabel("")
        self.briefing_label.setObjectName("BriefingLabel")
        self.briefing_label.setWordWrap(True)
        self.briefing_label.setStyleSheet(
            f"background: {COLORS['bg_panel']}; padding: 8px; border-left: 3px solid {COLORS['text_amber']};"
        )
        right_l.addWidget(self.briefing_label)

        # Terminal
        self.terminal = TerminalWidget()
        self.terminal.command_entered.connect(self._on_command)
        right_l.addWidget(self.terminal, 1)

        right_l_wrap.addWidget(right, 1)

        # Scanline overlay - paints over the terminal area
        self.scanline_overlay = ScanlineOverlay(right_wrapper)
        self.scanline_overlay.setVisible(False)

        splitter.addWidget(right_wrapper)
        splitter.setSizes([360, 960])
        root.addWidget(splitter, 1)

        # Status bar
        sb = QStatusBar()
        self.setStatusBar(sb)
        sb.showMessage("Booting...")

    def _build_menu(self):
        mb = self.menuBar()

        m_game = mb.addMenu("&Game")
        a_leader = QAction("&Leaderboard...", self)
        a_leader.setShortcut(QKeySequence("Ctrl+L"))
        a_leader.triggered.connect(self._open_leaderboard)
        m_game.addAction(a_leader)

        a_codex = QAction("&Codex / Glossary...", self)
        a_codex.setShortcut(QKeySequence("Ctrl+G"))
        a_codex.triggered.connect(self._open_codex)
        m_game.addAction(a_codex)

        a_stats = QAction("Stats &Dashboard...", self)
        a_stats.setShortcut(QKeySequence("Ctrl+D"))
        a_stats.triggered.connect(self._open_stats)
        m_game.addAction(a_stats)

        a_ach = QAction("&Achievements...", self)
        a_ach.setShortcut(QKeySequence("Ctrl+A"))
        a_ach.triggered.connect(self._open_achievements)
        m_game.addAction(a_ach)

        m_game.addSeparator()
        a_name = QAction("Set &Player Name...", self)
        a_name.triggered.connect(self._set_player_name)
        m_game.addAction(a_name)

        a_sound = QAction("Toggle &Sound", self)
        a_sound.setCheckable(True)
        a_sound.setChecked(self.sound.enabled)
        a_sound.toggled.connect(self._toggle_sound)
        m_game.addAction(a_sound)

        m_game.addSeparator()
        a_reset = QAction("&Reset Progress...", self)
        a_reset.triggered.connect(self._reset_progress)
        m_game.addAction(a_reset)

        a_quit = QAction("&Quit", self)
        a_quit.setShortcut(QKeySequence("Ctrl+Q"))
        a_quit.triggered.connect(self.close)
        m_game.addAction(a_quit)

        # View menu - themes + scanlines
        m_view = mb.addMenu("&View")
        self._theme_group = []
        theme_menu = m_view.addMenu("&Theme")
        current_theme = self.save.get_theme()
        for tid, tname in list_themes():
            a = QAction(tname, self)
            a.setCheckable(True)
            a.setChecked(tid == current_theme)
            a.triggered.connect(lambda checked=False, t=tid: self._set_theme(t))
            self._theme_group.append(a)
            theme_menu.addAction(a)

        a_scan = QAction("&CRT Scanlines", self)
        a_scan.setCheckable(True)
        a_scan.setChecked(self.save.get_settings().get("scanlines", False))
        a_scan.toggled.connect(self._toggle_scanlines)
        m_view.addAction(a_scan)

        m_help = mb.addMenu("&Help")
        a_about = QAction("&About", self)
        a_about.triggered.connect(self._about)
        m_help.addAction(a_about)
        a_help = QAction("&Quick Start", self)
        a_help.triggered.connect(self._quick_start)
        m_help.addAction(a_help)

    # ------------------------------------------------------------------
    # Boot animation
    def _start_boot_animation(self):
        self._boot_lines_queue = boot_lines()
        self._boot_timer.start()
        self.sound.boot()

    def _on_boot_tick(self):
        if not self._boot_lines_queue:
            self._boot_timer.stop()
            self.statusBar().showMessage("Ready. Type 'help' in the terminal for commands.", 5000)
            return
        line = self._boot_lines_queue.pop(0)
        self.terminal.append_output(line)

    # ------------------------------------------------------------------
    # Mission list
    def _refresh_mission_list(self):
        self.mission_list.clear()
        for m in ALL_MISSIONS:
            unlocked = self.save.is_unlocked(m.id)
            completed = self.save.is_completed(m.id)
            score = self.save.get_score(m.id)
            best = self.save.get_best_time(m.id)

            tag = ""
            if completed:
                tag = f"  [DONE {score}pts"
                if best is not None:
                    tag += f" / {best:.0f}s"
                tag += "]"
            elif not unlocked:
                tag = "  [LOCKED]"
            else:
                tag = "  [NEW]"
            label = f"{m.title}  ({m.category}/{m.difficulty}){tag}"

            item = QListWidgetItem(label)
            item.setData(Qt.UserRole, m.id)
            if not unlocked:
                item.setForeground(QColor(COLORS["text_dim"]))
            elif completed:
                item.setForeground(QColor(COLORS["text_dim"]))
            else:
                item.setForeground(QColor(COLORS["text_bright"]))
            self.mission_list.addItem(item)

        # Auto-select first unlocked-but-not-completed
        for i in range(self.mission_list.count()):
            item = self.mission_list.item(i)
            mid = item.data(Qt.UserRole)
            if self.save.is_unlocked(mid) and not self.save.is_completed(mid):
                self.mission_list.setCurrentRow(i)
                self._show_mission_briefing(mid)
                return
        for i in range(self.mission_list.count()):
            item = self.mission_list.item(i)
            mid = item.data(Qt.UserRole)
            if self.save.is_unlocked(mid):
                self.mission_list.setCurrentRow(i)
                self._show_mission_briefing(mid)
                return
        if self.mission_list.count() > 0:
            self.mission_list.setCurrentRow(0)
            self._show_mission_briefing(self.mission_list.item(0).data(Qt.UserRole))

    def _show_mission_briefing(self, mission_id: str):
        m = self.missions.get(mission_id)
        if m is None:
            return
        unlocked = self.save.is_unlocked(mission_id)
        completed = self.save.is_completed(mission_id)
        score = self.save.get_score(mission_id)

        if not unlocked:
            self.mission_title.setText(f"{m.title}  [LOCKED]")
            self.briefing_label.setText(
                "This mission is locked. Complete the previous mission to unlock it."
            )
            self.objective_label.setText("")
            self.cat_label.setText("")
            self.play_btn.setEnabled(False)
            self.hint_btn.setEnabled(False)
            return

        self.mission_title.setText(m.title)
        self.cat_label.setText(f"{m.category} / {m.difficulty} / {m.max_score} pts")

        if completed:
            best = self.save.get_best_time(m.id)
            time_str = f" (best time: {best:.1f}s)" if best is not None else ""
            self.objective_label.setText(
                f"Completed with {score} points{time_str}. Replay for a higher score "
                f"(your best score is kept)."
            )
        else:
            self.objective_label.setText(f"Objective: {m.objective}")

        self.briefing_label.setText(m.briefing)
        self.play_btn.setEnabled(True)
        self.hint_btn.setEnabled(self._in_mission and self.current_mission is not None)

    # ------------------------------------------------------------------
    # Mission lifecycle
    def _on_play_clicked(self):
        item = self.mission_list.currentItem()
        if item is None:
            return
        mid = item.data(Qt.UserRole)
        if not self.save.is_unlocked(mid):
            QMessageBox.information(self, "Mission Locked",
                                    "Complete the previous mission to unlock this one.")
            return
        self._start_mission(mid)

    def _on_mission_double_click(self, item: QListWidgetItem):
        mid = item.data(Qt.UserRole)
        if not self.save.is_unlocked(mid):
            QMessageBox.information(self, "Mission Locked",
                                    "Complete the previous mission to unlock this one.")
            return
        self._start_mission(mid)

    def _start_mission(self, mission_id: str):
        # Stop boot animation if still running
        if self._boot_timer.isActive():
            self._boot_timer.stop()
            # Drain remaining boot lines silently
            self._boot_lines_queue = []

        old = self.missions[mission_id]
        cls = type(old)
        self.current_mission = cls()
        self.current_mission_class = cls
        self._in_mission = True
        self.mission_start_time = time.time()

        # Configure terminal: autocomplete + file completion
        self.terminal.set_completions(self.current_mission.available_commands())
        self.terminal.set_fs_provider(self.current_mission.available_files)
        self.terminal.set_prompt(f"op@{mission_id}:~$ ")
        self.terminal.clear_output()
        self._print_mission_banner(self.current_mission)
        self.hint_btn.setEnabled(True)

        # Start in-mission timer
        self.timer_label.setVisible(True)
        self.timer_label.setText("00:00")
        self._timer.start()

        self.statusBar().showMessage(
            f"Mission started: {self.current_mission.title}. Type 'help' for commands."
        )
        self.sound.click()
        self.terminal.focus_input()

    def _print_mission_banner(self, m: Mission):
        self.terminal.append_output(
            f"=== MISSION START: {m.title} ===\n"
            f"Category: {m.category}  |  Difficulty: {m.difficulty}  |  Max score: {m.max_score}\n"
            f"{m.objective}\n"
            "----------------------------------------"
        )

    # ------------------------------------------------------------------
    # Timer
    def _on_timer_tick(self):
        if not self._in_mission:
            return
        elapsed = int(time.time() - self.mission_start_time)
        mm, ss = divmod(elapsed, 60)
        text = f"{mm:02d}:{ss:02d}"
        # Warn color after 5 minutes
        if elapsed >= 300:
            self.timer_label.setObjectName("TimerLabelWarn")
        else:
            self.timer_label.setObjectName("TimerLabel")
        # Re-apply style by setting text (stylesheet selector picks up object name change)
        self.timer_label.setStyleSheet("")  # clear inline
        self.timer_label.setText(text)
        # Force style recompute
        self.timer_label.style().unpolish(self.timer_label)
        self.timer_label.style().polish(self.timer_label)

    # ------------------------------------------------------------------
    # Command dispatch
    def _on_command(self, line: str):
        prompt_id = self.current_mission.id if self.current_mission else "lobby"
        self.terminal.append_output(f"op@{prompt_id}:~$ {line}")
        self.sound.type()

        if not self._in_mission or self.current_mission is None:
            self._handle_lobby_command(line)
            return

        result: MissionResult = self.current_mission.execute(line)

        if result.sound:
            self.sound.play(result.sound)

        if result.output == "__CLEAR__":
            self.terminal.clear_output()
            return

        if result.output:
            self.terminal.append_output(result.output)

        if result.solved:
            self._on_mission_solved()
        else:
            self.save.record_hints_used(self.current_mission.id,
                                        self.current_mission.hints_used())

    def _handle_lobby_command(self, line: str):
        parts = line.split()
        if not parts:
            return
        cmd = parts[0]
        if cmd in ("help", "?"):
            self.terminal.append_output(
                "Lobby commands:\n"
                "  help            show this help\n"
                "  missions        list available missions\n"
                "  play <id>       start a mission by id\n"
                "  codex           open the glossary\n"
                "  leaderboard     open the leaderboard\n"
                "  stats           open the stats dashboard\n"
                "  achievements    open the badges collection\n"
                "  clear           clear the screen\n"
                "\n"
                "Or use the MISSIONS panel on the left."
            )
        elif cmd == "missions":
            lines = ["ID                          Title                                  Status"]
            for m in ALL_MISSIONS:
                unlocked = self.save.is_unlocked(m.id)
                completed = self.save.is_completed(m.id)
                status = "DONE" if completed else ("open" if unlocked else "LOCKED")
                lines.append(f"{m.id:<27} {m.title:<39} {status}")
            self.terminal.append_output("\n".join(lines))
        elif cmd == "play" and len(parts) >= 2:
            mid = parts[1]
            if mid not in self.missions:
                self.terminal.append_output(f"unknown mission id: {mid}")
                self.sound.error()
                return
            if not self.save.is_unlocked(mid):
                self.terminal.append_output(f"mission locked: {mid}")
                self.sound.error()
                return
            self._start_mission(mid)
        elif cmd == "codex":
            self._open_codex()
        elif cmd == "leaderboard":
            self._open_leaderboard()
        elif cmd == "stats":
            self._open_stats()
        elif cmd == "achievements":
            self._open_achievements()
        elif cmd == "clear":
            self.terminal.clear_output()
        else:
            self.terminal.append_output(
                f"unknown lobby command: {cmd}\nType 'help' for available commands."
            )
            self.sound.error()

    # ------------------------------------------------------------------
    def _on_mission_solved(self):
        m = self.current_mission
        elapsed = time.time() - self.mission_start_time
        score = max(0, m.base_score())
        if elapsed < 300:
            time_bonus = min(20, int((300 - elapsed) // 30))
        else:
            time_bonus = 0
        total = score + time_bonus

        self._timer.stop()
        self.timer_label.setVisible(False)

        self.terminal.append_output(
            f"\n[*] elapsed time: {elapsed:.1f}s\n"
            f"[*] base score:   {score} (after -{m.hint_penalty()} hint penalty)\n"
            f"[*] time bonus:   +{time_bonus}\n"
            f"[*] total:        {total}\n"
        )
        self.sound.flag()

        # Record completion (this updates best score AND best time)
        self.save.record_completion(m.id, total, m.hints_used(), elapsed)
        # Unlock codex entries
        for term_id in m.unlocks_codex:
            self.save.unlock_codex(term_id)
        # Unlock next mission
        if m.unlocks_mission:
            self.save.unlock(m.unlocks_mission)
            next_m = self.missions.get(m.unlocks_mission)
            if next_m:
                self.terminal.append_output(
                    f"\n[+] NEW MISSION UNLOCKED: {next_m.title}\n"
                )

        # Check achievements
        meta = {
            "all_mission_ids":   [m.id for m in ALL_MISSIONS],
            "mission_topics":    MISSION_TOPICS,
            "category_missions": CATEGORY_MISSIONS,
        }
        newly = self.save.check_achievements(meta)
        for aid in newly:
            ach = get_achievement(aid)
            if ach:
                self.terminal.append_output(
                    f"\n[+] ACHIEVEMENT UNLOCKED: {ach.name}\n"
                    f"    {ach.description}\n"
                )
                self.sound.flag()
                # Also show a popup for the first achievement
                if len(self.save.get_achievements()) == 1:
                    QMessageBox.information(
                        self, "First Achievement!",
                        f"You unlocked your first achievement:\n\n"
                        f"  {ach.icon}  {ach.name}\n"
                        f"  {ach.description}\n\n"
                        f"Keep going, operator."
                    )

        self._in_mission = False
        self.current_mission = None
        self.hint_btn.setEnabled(False)
        self.terminal.set_completions([])
        self.terminal.set_fs_provider(None)
        self.terminal.set_prompt("op@lobby:~$ ")
        self._refresh_mission_list()
        self._update_status_panel()
        self.statusBar().showMessage(f"Mission complete! Score: {total}", 5000)

    # ------------------------------------------------------------------
    def _on_hint_clicked(self):
        if not self._in_mission or self.current_mission is None:
            return
        result = self.current_mission.execute("hint")
        if result.sound:
            self.sound.play(result.sound)
        if result.output:
            self.terminal.append_output(f"op@{self.current_mission.id}:~$ hint")
            self.terminal.append_output(result.output)
        self.save.record_hints_used(self.current_mission.id,
                                    self.current_mission.hints_used())

    # ------------------------------------------------------------------
    # Menu actions
    def _open_codex(self):
        dlg = CodexDialog(self.save, self)
        dlg.exec()

    def _open_leaderboard(self):
        dlg = LeaderboardDialog(self.save, self)
        dlg.exec()
        self._update_status_panel()

    def _open_stats(self):
        dlg = StatsDialog(self.save, self)
        dlg.exec()

    def _open_achievements(self):
        dlg = AchievementsDialog(self.save, self)
        dlg.exec()
        self._update_status_panel()

    def _set_player_name(self):
        name, ok = QInputDialog.getText(self, "Player Name",
                                        "Enter your handle:",
                                        text=self.save.player_name)
        if ok and name.strip():
            self.save.set_player_name(name.strip())
            self._update_status_panel()

    def _toggle_sound(self, on: bool):
        self.sound.set_enabled(on)
        self.save.set_setting("sound", on)

    def _set_theme(self, theme_id: str):
        # Update radio-style checkmarks
        for a in self._theme_group:
            a.setChecked(False)
        for a in self._theme_group:
            if a.text() == dict(list_themes())[theme_id]:
                a.setChecked(True)
                break
        self.save.set_theme(theme_id)
        QApplication.instance().setStyleSheet(build_stylesheet(get_theme(theme_id)))
        self.statusBar().showMessage(f"Theme: {dict(list_themes())[theme_id]}", 3000)

    def _toggle_scanlines(self, on: bool):
        self.save.set_setting("scanlines", on)
        self._apply_scanline_setting()

    def _apply_scanline_setting(self):
        on = self.save.get_settings().get("scanlines", False)
        self.scanline_overlay.setVisible(on)
        # Reposition to cover terminal area
        if on:
            # The overlay is parented to right_wrapper; raise it
            self.scanline_overlay.raise_()
            self.scanline_overlay.adjustSize()
            # Resize to parent
            parent = self.scanline_overlay.parentWidget()
            if parent is not None:
                self.scanline_overlay.setGeometry(parent.rect())

    def resizeEvent(self, e):
        super().resizeEvent(e)
        if self.scanline_overlay.isVisible():
            parent = self.scanline_overlay.parentWidget()
            if parent is not None:
                self.scanline_overlay.setGeometry(parent.rect())

    def _reset_progress(self):
        btn = QMessageBox.question(
            self, "Reset Progress",
            "Reset ALL mission progress, codex unlocks, and achievements?\n"
            "Your leaderboard entries will be kept.\n"
            "This cannot be undone.",
        )
        if btn == QMessageBox.Yes:
            self.save.reset_progress()
            self._refresh_mission_list()
            self._update_status_panel()
            self.terminal.clear_output()
            self._start_boot_animation()
            self.statusBar().showMessage("Progress reset.", 3000)

    def _about(self):
        QMessageBox.about(
            self, f"About {APP_NAME}",
            f"<h3>{APP_NAME} v{APP_VERSION}</h3>"
            "<p>A hacking game for learning computer security.</p>"
            "<p>Topics: cryptography, network security, web security, "
            "reverse engineering, Linux privilege escalation, Wi-Fi security, "
            "and social engineering.</p>"
            "<p>Built with PySide6 / Qt6.</p>"
            "<p><i>For educational use only. Practice ethics - only hack systems "
            "you own or have explicit permission to test.</i></p>"
        )

    def _quick_start(self):
        self.terminal.append_output(
            "\n=== QUICK START ===\n"
            "1. MISSIONS panel on the left shows all missions. Double-click to start.\n"
            "2. Each mission drops you into a simulated terminal. Type 'help' to see commands.\n"
            "3. Common commands: ls, cat <file>, man <cmd>, hint, submit <flag>.\n"
            "4. Pipes work: cat capture.log | grep USER\n"
            "5. Press Up/Down for history. Tab completes commands AND file names.\n"
            "6. Use 'hint' (button or command) if stuck - each hint costs points.\n"
            "7. Find the flag string (format: flag{...}) and run: submit flag{...}\n"
            "8. Menus: Ctrl+G codex, Ctrl+L leaderboard, Ctrl+D stats, Ctrl+A achievements.\n"
            "9. View menu: switch themes (Green/Amber/Cyberpunk) or toggle CRT scanlines.\n"
            "===================\n"
        )

    # ------------------------------------------------------------------
    def _update_status_panel(self):
        self.player_label.setText(f"Operator: {self.save.player_name}")
        self.score_label.setText(f"Total score: {self.save.total_score()}")
        n_ach = len(self.save.get_achievements())
        self.achievement_label.setText(f"Badges: {n_ach}/{len(ACHIEVEMENTS)}")

    # ------------------------------------------------------------------
    def closeEvent(self, e):
        self.save.save()
        super().closeEvent(e)
