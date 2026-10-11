"""Linux privilege escalation mission: find SUID binary + sudoers misconfig."""

from .base import Mission, MissionResult, CommandSpec, HintTier


class _PrivescMission(Mission):
    id = "m_linux_privesc"
    title = "Root Juice"
    category = "Linux Privilege Escalation"
    difficulty = "Hard"
    max_score = 180
    unlocks_codex = ["suid", "sudoers", "privilege_escalation", "linpeas"]
    unlocks_mission = "m_wifi_wpa"

    briefing = (
        "INCOMING TRANSMISSION - source: guild handler\n"
        "\n"
        "  You have a low-privilege shell on a target Linux box as user\n"
        "  'guest'. The box holds a flag file readable only by root.\n"
        "\n"
        "  Your job: enumerate the system, find a privilege escalation\n"
        "  vector, become root, and read /root/flag.txt.\n"
        "\n"
        "  Common privesc paths to consider:\n"
        "    - SUID binaries (find unusual ones)\n"
        "    - sudo misconfigurations (sudo -l)\n"
        "    - world-writable scripts called by root cron jobs\n"
        "\n"
        "  Tools available:\n"
        "    whoami               show current user\n"
        "    id                   show user id + groups\n"
        "    sudo -l              list sudo permissions\n"
        "    find_suid            find SUID binaries on the system\n"
        "    cat <file>           read file (only if you have permission)\n"
        "    su <user>            switch user (needs password)\n"
        "    /opt/syscheck        a SUID root binary - investigate\n"
    )

    objective = (
        "1. Confirm your identity: whoami  and  id\n"
        "2. Find what you can sudo: sudo -l\n"
        "3. Hunt for SUID binaries: find_suid\n"
        "4. Investigate /opt/syscheck (a SUID root script)\n"
        "5. Read /root/flag.txt - but you'll need root first.\n"
        "6. Submit the flag."
    )

    def setup(self):
        self.flag = "flag{sudoers_suid_and_shell_breakouts}"

        # The trick: /opt/syscheck is a SUID root shell script that
        # calls 'ps' without an absolute path. The player can prepend
        # a fake 'ps' to PATH that spawns /bin/sh as root.
        # We simulate this with: /opt/syscheck runs /bin/ps with euid=0.
        # Player puts a fake 'ps' script in /tmp/ and runs syscheck with
        # PATH=/tmp:$PATH - the fake ps runs as root and prints the flag.

        self.fs = {
            "README.txt": (
                "You are: guest (uid=1000)\n"
                "Goal: read /root/flag.txt (mode 0600, owned by root)\n"
                "\n"
                "Hints:\n"
                "  - 'find_suid' lists all SUID binaries\n"
                "  - 'sudo -l' shows what guest can run as root\n"
                "  - pay attention to /opt/syscheck - it's SUID root\n"
            ),
            "/etc/sudoers.d/guest": (
                "# guest may run /usr/bin/ls as root (no password)\n"
                "guest ALL=(root) NOPASSWD: /usr/bin/ls\n"
                "# NOTE: that's only ls - not cat. Useless for reading.\n"
            ),
            "/opt/syscheck": (
                "#!/bin/bash\n"
                "# SUID root - runs system health check\n"
                "# NOTE: calls 'ps' without absolute path - bug!\n"
                "echo '[*] system health check'\n"
                "ps aux | head -3\n"
                "echo '[*] ok'\n"
            ),
            "/root/flag.txt": f"<mode 0600, owned by root>\n{self.flag}\n",
            "/home/guest/.bash_history": (
                "ls\n"
                "whoami\n"
                "sudo -l\n"
                "find_suid\n"
                "cat /opt/syscheck\n"
            ),
        }

        # Track whether player has written a fake 'ps' script
        self._fake_ps_in_tmp = False

        def _whoami_handler(args, mission):
            return MissionResult(output="guest", sound="click")

        def _id_handler(args, mission):
            return MissionResult(
                output="uid=1000(guest) gid=1000(guest) groups=1000(guest)",
                sound="click",
            )

        def _sudo_handler(args, mission):
            if not args or args[0] != "-l":
                return MissionResult(
                    output=(
                        "[sudo] password for guest: \n"
                        "Sorry, try again."
                    ),
                    error=True, sound="error",
                )
            return MissionResult(
                output=(
                    "Matching Defaults entries for guest on this host:\n"
                    "    env_reset, mail_badpass, secure_path=/usr/local/sbin\\:/usr/local/bin\\:/usr/sbin\\:/usr/bin\\:/sbin\\:/bin\n"
                    "\n"
                    "User guest may run the following commands on this host:\n"
                    "    (root) NOPASSWD: /usr/bin/ls\n"
                ),
                sound="click",
            )

        def _find_suid_handler(args, mission):
            return MissionResult(
                output=(
                    "/usr/bin/sudo\n"
                    "/usr/bin/passwd\n"
                    "/usr/bin/su\n"
                    "/usr/bin/mount\n"
                    "/usr/bin/umount\n"
                    "/usr/bin/chsh\n"
                    "/usr/bin/chfn\n"
                    "/usr/bin/newgrp\n"
                    "/usr/bin/gpasswd\n"
                    "/opt/syscheck            <-- UNUSUAL: custom SUID binary\n"
                ),
                sound="click",
            )

        def _su_handler(args, mission):
            if not args:
                return MissionResult(output="usage: su <user>", error=True, sound="error")
            target = args[0]
            if target == "root":
                return MissionResult(
                    output="Password: \nsu: Authentication failure",
                    error=True, sound="error",
                )
            return MissionResult(
                output=f"su: user {target} does not exist",
                error=True, sound="error",
            )

        def _syscheck_handler(args, mission):
            # If player has placed a fake 'ps' in /tmp AND set PATH, our
            # simulation runs the fake ps as root.
            path = mission.fs.get("__PATH__", "/usr/bin:/bin")
            if "/tmp" in path.split(":") and mission._fake_ps_in_tmp:
                # Run the fake ps - it prints the flag
                fake_ps = mission.fs.get("/tmp/ps", "")
                return MissionResult(
                    output=(
                        "[*] system health check\n"
                        + fake_ps
                        + "\n[*] ok"
                    ),
                    sound="ok",
                )
            # Otherwise run the real /bin/ps
            return MissionResult(
                output=(
                    "[*] system health check\n"
                    "  PID TTY          TIME CMD\n"
                    " 1234 pts/0    00:00:00 bash\n"
                    " 1242 pts/0    00:00:00 syscheck\n"
                    "[*] ok"
                ),
                sound="click",
            )

        def _cat_handler_default(args, mission):
            # Intercept cat for /root/flag.txt to require euid=0
            # The base class already handles most cat calls; we override
            # by exposing the file as /root/flag.txt with a 'permission denied'
            # marker that we replace when syscheck gives us the flag.
            return None  # not used

        def _echo_handler(args, mission):
            # echo > file   => write file (for creating the fake ps)
            # We support: echo '<text>' > /tmp/ps
            if not args:
                return MissionResult(output="", sound="click")
            # Re-join, then check for redirect
            joined = " ".join(args)
            if ">" in joined:
                parts = joined.split(">", 1)
                content_part = parts[0].strip()
                target_part = parts[1].strip()
                # Strip surrounding quotes
                if (content_part.startswith("'") and content_part.endswith("'")) or \
                   (content_part.startswith('"') and content_part.endswith('"')):
                    content = content_part[1:-1]
                else:
                    content = content_part
                # Only allow /tmp/ path
                if target_part.startswith("/tmp/"):
                    mission.fs[target_part] = content + "\n"
                    if target_part.endswith("/ps"):
                        mission._fake_ps_in_tmp = True
                    return MissionResult(output="", sound="click")
                return MissionResult(
                    output=f"bash: {target_part}: Permission denied",
                    error=True, sound="error",
                )
            # Plain echo
            text = joined.strip().strip("'\"")
            return MissionResult(output=text, sound="click")

        def _cat_override(args, mission):
            if not args:
                return MissionResult(output="usage: cat <file>", error=True, sound="error")
            path = args[0]
            # Special: /root/flag.txt is only readable as root
            if path == "/root/flag.txt":
                # Did we already run syscheck with the fake ps? Then the flag
                # was already printed by syscheck. We still deny cat here
                # (the player must read it from the syscheck output).
                return MissionResult(
                    output="cat: /root/flag.txt: Permission denied",
                    error=True, sound="error",
                )
            content = mission.fs.get(path)
            if content is None:
                return MissionResult(
                    output=f"cat: {path}: No such file or directory",
                    error=True, sound="error",
                )
            return MissionResult(output=content, sound="click")

        # env / export support
        def _env_handler(args, mission):
            path = mission.fs.get("__PATH__", "/usr/bin:/bin")
            return MissionResult(
                output=(
                    f"PATH={path}\n"
                    f"USER=guest\n"
                    f"HOME=/home/guest\n"
                ),
                sound="click",
            )

        def _export_handler(args, mission):
            # Only support PATH=/tmp:...
            joined = " ".join(args)
            if "PATH=" in joined:
                new_path = joined.split("PATH=", 1)[1].strip().strip("'\"")
                mission.fs["__PATH__"] = new_path
                return MissionResult(output="", sound="click")
            return MissionResult(output="", sound="click")

        # The 'export' and 'env' commands; and override cat and echo
        self.commands = {
            "whoami":      CommandSpec("whoami", "whoami", "Show current user.", _whoami_handler),
            "id":          CommandSpec("id", "id", "Show uid/gid/groups.", _id_handler),
            "sudo":        CommandSpec("sudo", "sudo -l | sudo <cmd>", "Run a command as root (limited).", _sudo_handler),
            "find_suid":   CommandSpec("find_suid", "find_suid", "Find SUID binaries on the system.", _find_suid_handler),
            "su":          CommandSpec("su", "su <user>", "Switch user (needs password).", _su_handler),
            "/opt/syscheck": CommandSpec("/opt/syscheck", "/opt/syscheck", "Run the SUID root system-check script.", _syscheck_handler),
            "echo":        CommandSpec("echo", "echo <text> > <file>", "Print text or write to a file.", _echo_handler),
            "env":         CommandSpec("env", "env", "Show environment variables.", _env_handler),
            "export":      CommandSpec("export", "export PATH=<value>", "Set an environment variable.", _export_handler),
        }
        # Override cat with our permission-aware version
        # We do this by monkey-patching the _cmd_cat method via a custom command
        self._cat_override = _cat_override

        self.hints = [
            HintTier(
                text="'sudo -l' shows guest can only run /usr/bin/ls as root - not helpful for reading files.\n"
                     "Look at SUID binaries instead. 'find_suid' will list them - watch for /opt/syscheck (a custom one).",
                cost=20,
            ),
            HintTier(
                text="Read /opt/syscheck: cat /opt/syscheck\n"
                     "It's a bash script that calls 'ps' WITHOUT a full path. Since it runs with euid=0 (SUID root),\n"
                     "any 'ps' found in PATH runs as root. If you put a fake 'ps' in /tmp and prepend /tmp to PATH,\n"
                     "your fake 'ps' executes as root.",
                cost=30,
            ),
            HintTier(
                text="The full exploit:\n"
                     "  echo 'cat /root/flag.txt' > /tmp/ps\n"
                     "  export PATH=/tmp:/usr/bin:/bin\n"
                     "  /opt/syscheck\n"
                     "The fake 'ps' (which is now 'cat /root/flag.txt') runs as root and prints the flag.",
                cost=40,
            ),
        ]

    # Override _cmd_cat to use our permission-aware version
    def _cmd_cat(self, args):
        return self._cat_override(args, self)


MISSION_LINUX_PRIVESC = _PrivescMission()
