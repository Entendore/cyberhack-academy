"""Base Mission class - defines the contract every mission must implement.

A Mission is a self-contained challenge: it owns a 'virtual filesystem' the
player can poke at via simulated shell commands, validates their actions,
and produces a flag when solved.

Subclasses override:
  - setup()           to populate self.fs and define self.commands
  - handle_command()  to execute non-standard commands

The base class provides:
  - The standard command set (help, ls, cat, clear, hint, submit)
  - Hint tiers (each tier costs more points)
  - Flag submission + scoring
  - Codex unlock on completion
"""

from __future__ import annotations
import time
from dataclasses import dataclass, field
from typing import Callable


@dataclass
class MissionResult:
    """Returned by Mission.handle_command."""
    output: str = ""
    solved: bool = False          # did this command just solve the mission?
    flag: str | None = None       # flag string (only set when solved)
    error: bool = False           # was this an invalid/error command?
    sound: str | None = None      # which sound to play


@dataclass
class HintTier:
    text: str
    cost: int                     # points subtracted from mission max score


@dataclass
class CommandSpec:
    name: str
    usage: str
    description: str
    handler: Callable[[list[str], "Mission"], MissionResult]


class Mission:
    """Base class for all missions."""

    # --- Metadata (overridden by subclasses as class attributes) ---
    id: str = ""
    title: str = ""
    category: str = ""
    difficulty: str = "Easy"
    max_score: int = 100
    briefing: str = ""
    objective: str = ""
    unlocks_codex: list[str] = []   # subclasses override with their own list
    unlocks_mission: str | None = None

    def __init__(self):
        # Virtual filesystem: path -> str (text content)
        self.fs: dict[str, str] = {}
        # Custom commands added by this mission (name -> CommandSpec)
        self.commands: dict[str, CommandSpec] = {}
        # Hints, easiest/cheapest first
        self.hints: list[HintTier] = []
        # The flag the player must submit (set during setup)
        self.flag: str = ""
        # How many hints have been revealed so far this run
        self._hints_revealed: int = 0
        # Track solved state
        self.solved: bool = False
        # Build content
        self.setup()

    # ------------------------------------------------------------------
    # Subclass hook
    def setup(self):
        """Override to populate self.fs, self.commands, self.hints, self.flag."""
        pass

    # ------------------------------------------------------------------
    # Filesystem helpers
    def fs_lines(self) -> list[str]:
        return sorted(self.fs.keys())

    def cat(self, path: str) -> str | None:
        return self.fs.get(path)

    # ------------------------------------------------------------------
    # Hint API
    def next_hint(self) -> HintTier | None:
        if self._hints_revealed >= len(self.hints):
            return None
        h = self.hints[self._hints_revealed]
        self._hints_revealed += 1
        return h

    def hints_used(self) -> int:
        return self._hints_revealed

    def hint_penalty(self) -> int:
        """Total point penalty for hints revealed so far."""
        return sum(h.cost for h in self.hints[:self._hints_revealed])

    # ------------------------------------------------------------------
    # Command dispatch
    def execute(self, raw: str) -> MissionResult:
        """Parse and run a command line. Returns MissionResult.

        Supports a single pipe '|': the LHS command's output is fed as the
        'stdin' kwarg to the RHS command's handler (only grep-style commands
        consume stdin in practice; built-ins like cat ignore it).
        """
        raw = raw.strip()
        if not raw:
            return MissionResult(output="")

        # strip leading $ or > if user re-typed the prompt
        if raw[0] in "$>":
            raw = raw.lstrip("$> ").strip()

        # Pipe handling: split on the first unquoted '|'
        pipe_parts = self._split_pipe(raw)
        if len(pipe_parts) > 1:
            return self._execute_pipe(pipe_parts)

        return self._execute_single(raw)

    # ------------------------------------------------------------------
    @staticmethod
    def _split_pipe(line: str) -> list[str]:
        """Split a command line on '|' respecting single/double quotes."""
        out = []
        buf = []
        in_str = False
        quote = ""
        for ch in line:
            if in_str:
                buf.append(ch)
                if ch == quote:
                    in_str = False
                continue
            if ch in ("'", '"'):
                in_str = True
                quote = ch
                buf.append(ch)
                continue
            if ch == "|":
                out.append("".join(buf).strip())
                buf = []
                continue
            buf.append(ch)
        if buf:
            out.append("".join(buf).strip())
        return out

    def _execute_pipe(self, parts: list[str]) -> MissionResult:
        """Execute a piped command. Only one '|' is supported (a | b)."""
        # Left side
        left = self._execute_single(parts[0])
        if left.error and left.output == "":
            return left
        stdin_text = left.output

        # Right side - we only support grep/head/tail/wc as pipe consumers
        right_line = parts[1]
        right_parts = right_line.split()
        right_cmd = right_parts[0] if right_parts else ""
        right_args = right_parts[1:]

        if right_cmd == "grep":
            return self._pipe_grep(right_args, stdin_text)
        if right_cmd == "head":
            return self._pipe_head(right_args, stdin_text)
        if right_cmd == "tail":
            return self._pipe_tail(right_args, stdin_text)
        if right_cmd == "wc":
            return self._pipe_wc(right_args, stdin_text)
        if right_cmd == "sort":
            return self._pipe_sort(right_args, stdin_text)
        if right_cmd == "uniq":
            return self._pipe_uniq(right_args, stdin_text)
        # Fall back: just run right side as if it's a normal command (ignore stdin)
        # but if there's a mission command, it might still want the input
        return self._execute_single(right_line)

    def _pipe_grep(self, args, stdin: str) -> MissionResult:
        if not args:
            return MissionResult(output="usage: grep <pattern>", error=True, sound="error")
        pattern = args[0]
        lines = stdin.splitlines()
        matches = [l for l in lines if pattern in l]
        if not matches:
            return MissionResult(output="", sound="click")
        return MissionResult(output="\n".join(matches), sound="click")

    def _pipe_head(self, args, stdin: str) -> MissionResult:
        n = 10
        if args:
            try:
                n = int(args[-1])
            except ValueError:
                pass
        lines = stdin.splitlines()
        return MissionResult(output="\n".join(lines[:n]), sound="click")

    def _pipe_tail(self, args, stdin: str) -> MissionResult:
        n = 10
        if args:
            try:
                n = int(args[-1])
            except ValueError:
                pass
        lines = stdin.splitlines()
        return MissionResult(output="\n".join(lines[-n:]), sound="click")

    def _pipe_wc(self, args, stdin: str) -> MissionResult:
        lines = stdin.splitlines()
        words = sum(len(l.split()) for l in lines)
        chars = sum(len(l) for l in lines)
        return MissionResult(output=f"{len(lines):>5} {words:>5} {chars:>5}", sound="click")

    def _pipe_sort(self, args, stdin: str) -> MissionResult:
        lines = sorted(stdin.splitlines())
        return MissionResult(output="\n".join(lines), sound="click")

    def _pipe_uniq(self, args, stdin: str) -> MissionResult:
        seen: list[str] = []
        for l in stdin.splitlines():
            if not seen or seen[-1] != l:
                seen.append(l)
        return MissionResult(output="\n".join(seen), sound="click")

    def _execute_single(self, raw: str) -> MissionResult:
        parts = raw.split()
        if not parts:
            return MissionResult(output="")
        cmd = parts[0]
        args = parts[1:]

        # Standard commands always available
        if cmd == "help":
            return self._cmd_help()
        if cmd == "ls":
            return self._cmd_ls(args)
        if cmd == "cat":
            return self._cmd_cat(args)
        if cmd == "clear":
            return MissionResult(output="__CLEAR__")
        if cmd == "hint":
            return self._cmd_hint()
        if cmd == "submit":
            return self._cmd_submit(args)
        if cmd == "man":
            return self._cmd_man(args)
        # Pipe consumers as standalone commands (no stdin) - behave like no input
        if cmd in ("grep", "head", "tail", "wc", "sort", "uniq"):
            return MissionResult(
                output=f"{cmd}: this command needs to be used in a pipe (e.g. cat file | {cmd} ...)",
                error=True, sound="error",
            )

        # Mission-specific commands
        spec = self.commands.get(cmd)
        if spec is None:
            return MissionResult(
                output=f"command not found: {cmd}\nType 'help' for available commands.",
                error=True, sound="error",
            )
        try:
            return spec.handler(args, self)
        except Exception as e:
            return MissionResult(
                output=f"error executing '{cmd}': {e}",
                error=True, sound="error",
            )

    # ------------------------------------------------------------------
    # Built-in commands
    def _cmd_help(self) -> MissionResult:
        lines = ["Available commands:", ""]
        builtin = [
            ("help",            "show this help"),
            ("ls",              "list files in the working directory"),
            ("cat <file>",      "print file contents"),
            ("man <cmd>",       "show manual for a mission command"),
            ("hint",            "request a hint (costs points)"),
            ("submit <flag>",   "submit a flag to complete the mission"),
            ("clear",           "clear the terminal"),
            ("| grep <pat>",    "pipe output through grep (also: head, tail, wc, sort, uniq)"),
        ]
        for name, desc in builtin:
            lines.append(f"  {name:<22} {desc}")
        if self.commands:
            lines.append("")
            lines.append("Mission-specific commands:")
            for spec in self.commands.values():
                lines.append(f"  {spec.usage:<22} {spec.description}")
        lines.append("")
        lines.append("Tip: press Up/Down for history, Tab to autocomplete commands & files.")
        lines.append("")
        return MissionResult(output="\n".join(lines), sound="ok")

    def _cmd_ls(self, args) -> MissionResult:
        if not self.fs:
            return MissionResult(output="(empty directory)")
        files = self.fs_lines()
        return MissionResult(output="  ".join(files), sound="click")

    def _cmd_cat(self, args) -> MissionResult:
        if not args:
            return MissionResult(output="usage: cat <file>", error=True, sound="error")
        path = args[0]
        content = self.fs.get(path)
        if content is None:
            return MissionResult(output=f"cat: {path}: No such file", error=True, sound="error")
        return MissionResult(output=content, sound="click")

    def _cmd_man(self, args) -> MissionResult:
        if not args:
            return MissionResult(output="usage: man <command>", error=True, sound="error")
        name = args[0]
        spec = self.commands.get(name)
        if spec is None:
            return MissionResult(output=f"man: no manual for '{name}'", error=True, sound="error")
        lines = [
            f"NAME",
            f"    {spec.name} - {spec.description}",
            f"",
            f"SYNOPSIS",
            f"    {spec.usage}",
            f"",
            f"DESCRIPTION",
            f"    {spec.description}",
        ]
        return MissionResult(output="\n".join(lines), sound="click")

    def _cmd_hint(self) -> MissionResult:
        hint = self.next_hint()
        if hint is None:
            return MissionResult(
                output="No more hints available. Think carefully, operator.",
                sound="error",
            )
        return MissionResult(
            output=(f"--- HINT #{self._hints_revealed} (-{hint.cost} pts on completion) ---\n"
                    f"{hint.text}"),
            sound="hint",
        )

    def _cmd_submit(self, args) -> MissionResult:
        if not args:
            return MissionResult(output="usage: submit <flag>", error=True, sound="error")
        candidate = " ".join(args).strip()
        if self.flag and candidate == self.flag:
            self.solved = True
            return MissionResult(
                output=self._victory_text(),
                solved=True,
                flag=self.flag,
                sound="flag",
            )
        return MissionResult(
            output=f"Invalid flag: '{candidate}'. Try again.",
            error=True, sound="error",
        )

    # ------------------------------------------------------------------
    def _victory_text(self) -> str:
        return (
            "\n"
            "+========================================================+\n"
            "||                                                      ||\n"
            "||   MISSION COMPLETE - FLAG CAPTURED                    ||\n"
            f"||   {self.flag:<50} ||\n"
            "||                                                      ||\n"
            "+========================================================+\n"
        )

    # ------------------------------------------------------------------
    def available_commands(self) -> list[str]:
        """List of all command names for autocomplete."""
        return ["help", "ls", "cat", "man", "hint", "submit", "clear",
                "grep", "head", "tail", "wc", "sort", "uniq"] + list(self.commands.keys())

    def available_files(self) -> list[str]:
        """List of files in the working directory for Tab completion."""
        return list(self.fs.keys())

    def base_score(self) -> int:
        return self.max_score - self.hint_penalty()
