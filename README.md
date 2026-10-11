# CyberHack Academy

A desktop hacking game for learning computer security, built with **PySide6 / Qt6**.

You play as a recruit at a hacking guild. Each mission drops you into a simulated
shell where you type real commands (`ls`, `cat`, `nmap`, `crack`, `inject`, `disasm`...)
against virtual targets. Solve the challenge, capture the flag, unlock the next mission.

> **v1.1** adds 4 new missions (Tutorial + Linux priv-esc + Wi-Fi cracking + Social
> engineering), achievements, a stats dashboard, three themes, CRT scanlines, a boot
> animation, an in-mission timer with speedrun tracking, file-name Tab completion, and
> pipe support (`cat foo | grep bar`).

---

## Missions

The game ships with **11 missions** across 7 security domains:

| # | Mission | Category | Difficulty | Concepts |
|---|---------|----------|------------|----------|
| 0 | Boot Camp | Tutorial | Intro | Terminal mechanics (ls, cat, man, hint, submit) |
| 1 | The Caesar's Whisper | Cryptography | Easy | Caesar cipher, brute-forcing shifts |
| 2 | Hash on the Wire | Cryptography | Medium | MD5, wordlist attacks, unsalted hashes |
| 3 | Reconnaissance | Network Security | Easy | Port scanning, simulated `nmap`, service identification |
| 4 | Packet Sniff | Network Security | Medium | Cleartext protocols (FTP), packet capture analysis, pipes |
| 5 | Login Bypass | Web Security | Medium | SQL injection, authentication bypass |
| 6 | Cookie Theft | Web Security | Hard | Stored XSS, cookie exfiltration, session hijacking |
| 7 | Binary Secrets | Reverse Engineering | Hard | Reading pseudo-assembly, constant reconstruction |
| 8 | Root Juice | Linux Privilege Escalation | Hard | SUID binaries, PATH hijacking, `sudo -l` enumeration |
| 9 | Airwave Snatch | Wi-Fi Security | Hard | Monitor mode, WPA handshake capture, deauth, aircrack-ng |
| 10 | The Long Con | Social Engineering | Medium | Pretexting, phishing, OSINT, choice-based conversation |

---

## Features

### Gameplay
- **11 hand-authored missions** with briefings, simulated filesystems, simulated
  network targets, and conversation state machines.
- **Hacker-terminal UI** — dark background, neon green mono font, classic `$` prompt.
- **Hints system** — request progressively more revealing hints; each tier costs points.
- **Scoring** — base score per mission minus hint penalty, plus a time bonus for fast solves.
- **Pipes** — `cat capture.log | grep USER`, `| head`, `| tail`, `| wc`, `| sort`, `| uniq`.
- **Tab completion** — complete command names AND file names (like a real shell).
- **Command history** (Up/Down arrows) and **inline help** (`help`, `man <cmd>`).

### Meta-game
- **Achievements** — 16 unlockable badges (first blood, no-hint solve, speed demon,
  flawless, category masters, halfway, completionist, scholar, high scorer, boot camp grad).
  Badges pop in the terminal when earned; first badge also shows a celebratory dialog.
- **Stats dashboard** (Ctrl+D) — missions completed, total score, achievements, codex
  count, per-category progress bars, and a per-mission table with best times.
- **In-mission timer** — visible in the header during play; turns red after 5 minutes.
- **Speedrun tracking** — best time per mission is recorded separately from best score.
- **Codex / glossary** — 40+ security terms unlock as you progress. Locked terms are
  redacted until you earn them.
- **Local leaderboard** — submit your handle and total score; stored in
  `~/.cyberhack/save.json`.
- **Progress save** — completed missions, unlocks, achievements, and settings persist
  between sessions.

### Visual polish
- **Boot animation** — typing-style kernel boot sequence on launch.
- **ASCII art banner** — CYBERHACK banner in the mission panel.
- **Theme switcher** (View → Theme) — switch between:
  - **Green Terminal** (default) — classic phosphor green
  - **Amber Retro** — warm amber CRT
  - **Cyberpunk Neon** — magenta/cyan on deep purple
- **CRT scanlines** (View → CRT Scanlines) — toggle a translucent scanline overlay
  across the terminal for retro immersion.

### Audio
- **Sound effects** — chiptune-style effects generated at runtime via Qt Multimedia
  (typing clicks, success chimes, victory sweep). Falls back to silence if no audio device.

---

## Installation

### 1. Install Python dependencies

```bash
pip install -r requirements.txt
```

(Requires Python 3.10+ and PySide6 >= 6.5.)

### 2. Linux system dependencies (Qt6)

PySide6 needs a few system libraries. On Debian/Ubuntu:

```bash
sudo apt-get install -y libegl1 libgl1 libxkbcommon0 libdbus-1-3 libfontconfig1
```

On Fedora / RHEL:

```bash
sudo dnf install -y libegl libgl libxkbcommon dbus-libs fontconfig
```

On Arch:

```bash
sudo pacman -S libegl libgl libxkbcommon dbus fontconfig
```

> `main.py` will try to locate a working `libEGL.so.1` in Playwright/Chrome caches
> (and `~/.local/lib`) if your system doesn't have one — useful for headless /
> sandboxed environments. On a normal desktop this isn't needed.

### 3. Run the game

```bash
python3 main.py
```

That's it — no shell launcher required.

---

## How to play

1. The **MISSIONS** panel on the left lists all 11 missions. Double-click one
   (or click **Start Mission**) to begin. **First-time players should start with
   mission 0 (Boot Camp) — it teaches the terminal mechanics.**
2. The terminal on the right shows the briefing. Type `help` to see the commands
   available in the current mission.
3. Common commands always available:
   - `ls` — list files
   - `cat <file>` — read a file (try `cat README.txt` first!)
   - `man <cmd>` — manual for a mission-specific command
   - `hint` — request a hint (costs points; each tier is more revealing)
   - `submit <flag>` — submit a captured flag (format: `flag{...}`)
   - `clear` — clear the terminal
   - `| grep <pat>` — pipe output through grep (also: `head`, `tail`, `wc`, `sort`, `uniq`)
4. **Tips**:
   - Press **Up/Down** to recall command history.
   - Press **Tab** to complete command names AND file names.
   - Use the **Codex** (Ctrl+G) to look up security terms you've unlocked.
   - Use the **Stats Dashboard** (Ctrl+D) to see per-category progress.
   - Use the **Achievements** (Ctrl+A) to browse badge collection.
   - Use the **Leaderboard** (Ctrl+L) to submit your total score.
   - Switch **Themes** via the View menu (Green / Amber / Cyberpunk).
   - Toggle **CRT Scanlines** via the View menu for retro vibes.
   - Each completed mission unlocks the next one and adds new glossary entries.

---

## Keyboard shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+L` | Open Leaderboard |
| `Ctrl+G` | Open Codex / Glossary |
| `Ctrl+D` | Open Stats Dashboard |
| `Ctrl+A` | Open Achievements |
| `Ctrl+Q` | Quit |
| `Up/Down` (in terminal) | Recall command history |
| `Tab` (in terminal) | Autocomplete commands and file names |

---

## Project structure

```
hacking_game/
├── main.py                       # Entry point - bootstraps Qt + main window
├── requirements.txt              # PySide6
├── smoke_test.py                 # Headless test: solves all 11 missions
├── README.md                     # This file
└── game/
    ├── __init__.py
    ├── styles.py                 # 3 themes (green/amber/cyberpunk) + QSS
    ├── sounds.py                 # Runtime-generated chiptune effects
    ├── save_manager.py           # JSON save + migrations + achievements API
    ├── codex.py                  # Glossary data (40+ terms)
    ├── codex_dialog.py           # Codex UI dialog
    ├── leaderboard.py            # Leaderboard UI dialog
    ├── stats_dialog.py           # Stats dashboard UI
    ├── achievements.py           # 16 achievement definitions + unlock logic
    ├── achievements_dialog.py    # Badge grid UI
    ├── scanlines.py              # CRT scanline paintable overlay
    ├── ascii.py                  # ASCII art banner + boot animation lines
    ├── terminal.py               # Terminal widget (history, autocomplete, pipes)
    ├── main_window.py            # Main window - ties everything together
    └── missions/
        ├── __init__.py
        ├── base.py               # Mission base class + pipe support + CommandSpec
        ├── tutorial.py           # Mission 0: Boot Camp (terminal mechanics)
        ├── crypto.py             # Missions 1-2: Caesar cipher, MD5 cracking
        ├── network.py            # Missions 3-4: nmap recon, packet sniffing
        ├── web.py                # Missions 5-6: SQLi, XSS cookie theft
        ├── reverse.py            # Mission 7: pseudo-assembly reverse engineering
        ├── linux.py              # Mission 8: SUID + PATH hijacking privesc
        ├── wifi.py               # Mission 9: WPA handshake capture + crack
        └── social.py             # Mission 10: choice-based phishing conversation
```

---

## Extending the game

### Add a new mission

1. Create a class in `game/missions/<your_file>.py` that inherits from `Mission`
   (see `tutorial.py` for the simplest template, or `social.py` for a complex one).
2. Override:
   - Class attributes: `id`, `title`, `category`, `difficulty`, `max_score`,
     `briefing`, `objective`, `unlocks_codex`, `unlocks_mission`.
   - `setup()` — populate `self.fs` (virtual files), `self.commands`
     (mission-specific commands via `CommandSpec`), `self.hints` (list of `HintTier`),
     and `self.flag` (the string the player must `submit`).
3. Register it in `game/missions/__init__.py` by adding it to `ALL_MISSIONS`.
4. Set the previous mission's `unlocks_mission` to your new mission's `id`.

### Add an achievement

Add an entry to `ACHIEVEMENTS` in `game/achievements.py`, then add the unlock
condition to `check_unlocks()`.

### Add a codex term

Add a tuple to `CODEX` in `game/codex.py`, then reference it in a mission's
`unlocks_codex` list.

### Add a theme

Add a palette dict to `THEMES` in `game/styles.py`. It will automatically appear
in the View → Theme menu.

---

## Educational notes

This game is a **teaching tool**, not a hacking toolkit. All "targets" are
simulated inside the game process — no real network traffic is generated, no
real binaries are analyzed, no real Wi-Fi adapters are touched. The missions
teach the **concepts** (what is a Caesar cipher? how does SQLi work? what does
an nmap scan tell you? what's a SUID binary?) by having you perform simplified
versions of the attacks against fake systems.

**Ethics**: Only test systems you own or have explicit written permission to
test. Real-world unauthorized access is illegal and harms real people.

---

## Troubleshooting

**`libEGL.so.1: cannot open shared object file`** — Install the Qt6 system
libraries (see Installation step 2). `main.py` will also try to fall back to a
bundled libEGL from Playwright/Chrome caches if available.

**No audio** — `SoundManager` falls back to silence if Qt Multimedia can't find
an audio device. The game still plays normally. Toggle sound off/on via
**Game → Toggle Sound**.

**Save file location** — `~/.cyberhack/save.json`. Delete it (or use
**Game → Reset Progress**) to start over. Old v1.0 save files are auto-migrated
to the v1.1 schema on first launch (tutorial is unlocked, best-time fields are
backfilled, achievements list is initialized).

**Smoke test** — Run `python3 smoke_test.py` to verify all 11 missions solve
correctly without launching the GUI. Useful for catching regressions.

---

## License

MIT — built for educational use.
