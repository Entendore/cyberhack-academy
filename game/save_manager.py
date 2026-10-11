"""Save-file manager - persists progress, scores, hints used, leaderboard,
achievements, best times, and settings."""

import json
import os
import time
from pathlib import Path
from PySide6.QtCore import QObject, Signal


DEFAULT_SAVE_DIR = Path.home() / ".cyberhack"
DEFAULT_SAVE_FILE = DEFAULT_SAVE_DIR / "save.json"


class SaveManager(QObject):
    """Manage a JSON save file.

    Schema:
    {
        "player_name": str,
        "completed": {
            mission_id: {
                "score": int,           # best score
                "hints_used": int,
                "time_s": float,        # time of best-scoring run
                "ts": float,            # wall clock
                "best_time_s": float,   # fastest run ever (for speedrun)
            }
        },
        "unlocked": [mission_id, ...],
        "codex_unlocked": [term_id, ...],
        "achievements": [achievement_id, ...],
        "leaderboard": [ {"name": str, "total": int, "ts": float}, ... ],
        "settings": { "sound": bool, "theme": str, "scanlines": bool }
    }
    """

    progress_changed = Signal()
    achievement_unlocked = Signal(str)   # emits achievement id

    def __init__(self, path: Path = DEFAULT_SAVE_FILE, parent=None):
        super().__init__(parent)
        self.path = Path(path)
        self._data: dict = {}
        self.load()

    # ------------------------------------------------------------------
    def load(self):
        if self.path.exists():
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    self._data = json.load(f)
            except Exception:
                self._data = {}
        if not self._data:
            self._data = self._default()
        # Migrations: ensure required keys exist + tutorial always unlocked
        self._migrate()

    def _migrate(self):
        """Apply schema migrations to old save files."""
        changed = False
        if "achievements" not in self._data:
            self._data["achievements"] = []
            changed = True
        if "settings" not in self._data:
            self._data["settings"] = {"sound": True, "theme": "green", "scanlines": False}
            changed = True
        else:
            s = self._data["settings"]
            if "theme" not in s:
                s["theme"] = "green"
                changed = True
            if "scanlines" not in s:
                s["scanlines"] = False
                changed = True
        # Ensure tutorial is always unlocked (added in v1.1)
        unlocked = self._data.setdefault("unlocked", [])
        if "m_tutorial" not in unlocked:
            unlocked.insert(0, "m_tutorial")
            changed = True
        # Best-time field on existing completed records
        for mid, rec in self._data.get("completed", {}).items():
            if "best_time_s" not in rec:
                rec["best_time_s"] = rec.get("time_s")
                changed = True
        if changed:
            self.save()

    def _default(self) -> dict:
        return {
            "player_name": "Operator",
            "completed": {},
            "unlocked": ["m_tutorial"],   # tutorial always unlocked on first run
            "codex_unlocked": [],
            "achievements": [],
            "leaderboard": [],
            "settings": {"sound": True, "theme": "green", "scanlines": False},
        }

    def save(self):
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=2)
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Accessors
    @property
    def player_name(self) -> str:
        return self._data.get("player_name", "Operator")

    def set_player_name(self, name: str):
        self._data["player_name"] = name[:24] or "Operator"
        self.save()

    def is_completed(self, mission_id: str) -> bool:
        return mission_id in self._data.get("completed", {})

    def is_unlocked(self, mission_id: str) -> bool:
        return mission_id in self._data.get("unlocked", [])

    def get_score(self, mission_id: str) -> int:
        rec = self._data.get("completed", {}).get(mission_id)
        return rec.get("score", 0) if rec else 0

    def total_score(self) -> int:
        return sum(rec.get("score", 0) for rec in self._data.get("completed", {}).values())

    def get_hints_used(self, mission_id: str) -> int:
        rec = self._data.get("completed", {}).get(mission_id)
        return rec.get("hints_used", 0) if rec else 0

    def get_best_time(self, mission_id: str) -> float | None:
        rec = self._data.get("completed", {}).get(mission_id)
        if not rec:
            return None
        return rec.get("best_time_s")

    # ------------------------------------------------------------------
    # Mutators
    def record_completion(self, mission_id: str, score: int,
                          hints_used: int, time_s: float):
        prev = self._data["completed"].get(mission_id, {})
        prev_score = prev.get("score", 0)
        prev_best_time = prev.get("best_time_s")

        # Update best score (keep if previous was higher)
        new_rec = dict(prev)
        if score > prev_score:
            new_rec["score"] = score
            new_rec["hints_used"] = hints_used
            new_rec["time_s"] = round(time_s, 1)
            new_rec["ts"] = time.time()
        # Always update best time
        if prev_best_time is None or time_s < prev_best_time:
            new_rec["best_time_s"] = round(time_s, 1)

        self._data["completed"][mission_id] = new_rec
        self.save()
        self.progress_changed.emit()

    def record_hints_used(self, mission_id: str, hints_used: int):
        """Track in-progress hint usage even before completion."""
        rec = self._data["completed"].get(mission_id, {})
        rec["hints_used"] = hints_used
        self._data["completed"][mission_id] = rec
        self.save()

    def unlock(self, mission_id: str):
        if mission_id not in self._data["unlocked"]:
            self._data["unlocked"].append(mission_id)
            self.save()
            self.progress_changed.emit()

    def unlock_codex(self, term_id: str):
        if term_id not in self._data["codex_unlocked"]:
            self._data["codex_unlocked"].append(term_id)
            self.save()

    def is_codex_unlocked(self, term_id: str) -> bool:
        return term_id in self._data.get("codex_unlocked", [])

    # ------------------------------------------------------------------
    # Achievements
    def get_achievements(self) -> list[str]:
        return list(self._data.get("achievements", []))

    def has_achievement(self, aid: str) -> bool:
        return aid in self._data.get("achievements", [])

    def unlock_achievement(self, aid: str) -> bool:
        """Returns True if this is a new unlock (caller should show a toast)."""
        if aid in self._data["achievements"]:
            return False
        self._data["achievements"].append(aid)
        self.save()
        self.achievement_unlocked.emit(aid)
        return True

    def check_achievements(self, mission_meta: dict) -> list[str]:
        """Check all achievements against current state. Returns list of newly unlocked.

        `mission_meta` is built by the caller and contains:
          - all_mission_ids
          - mission_topics
          - category_missions
        """
        from .achievements import check_unlocks
        state = {
            "completed":       self._data.get("completed", {}),
            "codex_unlocked":  self._data.get("codex_unlocked", []),
            "total_score":     self.total_score(),
            "achievements":    self._data.get("achievements", []),
            "all_mission_ids": mission_meta.get("all_mission_ids", []),
            "mission_topics":  mission_meta.get("mission_topics", {}),
            "category_missions": mission_meta.get("category_missions", {}),
        }
        newly = check_unlocks(state)
        for aid in newly:
            self.unlock_achievement(aid)
        return newly

    # ------------------------------------------------------------------
    # Settings
    def get_settings(self) -> dict:
        return self._data.get("settings", {"sound": True, "theme": "green", "scanlines": False})

    def set_setting(self, key: str, value):
        self._data.setdefault("settings", {})[key] = value
        self.save()

    def get_theme(self) -> str:
        return self.get_settings().get("theme", "green")

    def set_theme(self, theme: str):
        self.set_setting("theme", theme)

    # ------------------------------------------------------------------
    # Leaderboard
    def add_leaderboard_entry(self, name: str, total: int):
        self._data.setdefault("leaderboard", []).append({
            "name": name,
            "total": total,
            "ts": time.time(),
        })
        self._data["leaderboard"].sort(key=lambda e: e["total"], reverse=True)
        self._data["leaderboard"] = self._data["leaderboard"][:20]
        self.save()

    def get_leaderboard(self) -> list[dict]:
        return list(self._data.get("leaderboard", []))

    # ------------------------------------------------------------------
    def reset_progress(self):
        name = self.player_name
        settings = self.get_settings()
        leaderboard = self._data.get("leaderboard", [])
        self._data = self._default()
        self._data["player_name"] = name
        self._data["settings"] = settings
        self._data["leaderboard"] = leaderboard
        self.save()
        self.progress_changed.emit()

    # ------------------------------------------------------------------
    # Stats helpers
    def stats_summary(self) -> dict:
        """Return a stats dict for the dashboard."""
        completed = self._data.get("completed", {})
        times = [rec.get("time_s", 0) for rec in completed.values()]
        total_hints = sum(rec.get("hints_used", 0) for rec in completed.values())
        return {
            "missions_completed": len(completed),
            "total_score":        self.total_score(),
            "total_time_s":       round(sum(times), 1),
            "avg_time_s":         round(sum(times) / len(times), 1) if times else 0,
            "total_hints":        total_hints,
            "achievements":       len(self._data.get("achievements", [])),
            "codex_unlocked":     len(self._data.get("codex_unlocked", [])),
        }
