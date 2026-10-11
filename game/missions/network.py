"""Network security missions: simulated nmap port scan + packet sniffing."""

from .base import Mission, MissionResult, CommandSpec, HintTier


# ======================================================================
# Mission 3 - Reconnaissance / Port Scan (Easy-Medium)
# ======================================================================
class _ReconMission(Mission):
    id = "m_net_recon"
    title = "Reconnaissance"
    category = "Network Security"
    difficulty = "Easy"
    max_score = 120
    unlocks_codex = ["port_scan", "nmap", "three_way_handshake", "ftp"]
    unlocks_mission = "m_net_sniff"

    briefing = (
        "INCOMING TRANSMISSION - source: guild handler\n"
        "\n"
        "  A rival guild is hosting an undocumented service on host\n"
        "  10.0.0.42. We don't know which port it's on. Your job: scan\n"
        "  the host, identify the open port, and connect to retrieve the\n"
        "  flag.\n"
        "\n"
        "  Tools available:\n"
        "    nmap <target>          simulated SYN scan\n"
        "    connect <ip> <port>    raw TCP connect to a port\n"
        "\n"
        "  Standard ports 22, 80, 443 are decoys. The flag service is on\n"
        "  a non-standard port."
    )

    objective = (
        "1. Run:  nmap 10.0.0.42\n"
        "2. Identify the unusual open port in the scan output\n"
        "3. Connect: connect 10.0.0.42 <port>\n"
        "4. Submit the flag the service prints."
    )

    def setup(self):
        self.flag = "flag{open_ports_open_doors}"

        self.fs = {
            "README.txt": (
                "Target: 10.0.0.42\n"
                "We've had reports that an internal flag service is running\n"
                "on a non-standard port. Run 'nmap 10.0.0.42' to enumerate.\n"
            ),
            "intel.txt": (
                "Last-known intel on the target:\n"
                "  - SSH was disabled last week\n"
                "  - A web server was set up but never used\n"
                "  - Rumor has it the sysadmin runs a custom TCP service\n"
                "    somewhere in the 30000-40000 port range\n"
            ),
        }

        # Target: 10.0.0.42
        self.target_ip = "10.0.0.42"
        # Open ports: 22 (closed actually), 80 (open, decoy), 443 (closed), 31337 (open, FLAG)
        self.open_ports = {
            80:   ("http",      "Apache httpd 2.4.41 - decoy"),
            31337: ("unknown",   "custom TCP service - prints a flag on connect"),
        }

        def _nmap_handler(args, mission):
            if not args:
                return MissionResult(
                    output="usage: nmap <target>\nexample: nmap 10.0.0.42",
                    error=True, sound="error",
                )
            target = args[0]
            if target != mission.target_ip:
                return MissionResult(
                    output=(
                        f"Starting Nmap scan of {target}...\n"
                        f"Host seems down - no response.\n"
                    ),
                    error=True, sound="error",
                )
            lines = [
                f"Starting Nmap (simulated) against {target}...",
                f"Nmap scan report for {target}",
                f"Host is up (0.041s latency).",
                "",
                "PORT      STATE    SERVICE       VERSION",
            ]
            # Show closed ports too - typical nmap output
            for port in sorted([22, 80, 443, 31337]):
                if port in mission.open_ports:
                    svc, ver = mission.open_ports[port]
                    lines.append(f"{port:<9} open     {svc:<13} {ver}")
                else:
                    lines.append(f"{port:<9} closed   -             -")
            lines.append("")
            lines.append("Nmap done: 1 IP address (1 host up) scanned in 0.41 seconds")
            return MissionResult(output="\n".join(lines), sound="ok")

        def _connect_handler(args, mission):
            if len(args) < 2:
                return MissionResult(
                    output="usage: connect <ip> <port>",
                    error=True, sound="error",
                )
            ip = args[0]
            try:
                port = int(args[1])
            except ValueError:
                return MissionResult(
                    output=f"connect: invalid port '{args[1]}'",
                    error=True, sound="error",
                )
            if ip != mission.target_ip:
                return MissionResult(
                    output=f"connect: connection to {ip}:{port} refused",
                    error=True, sound="error",
                )
            if port not in mission.open_ports:
                return MissionResult(
                    output=(
                        f"[*] dialing {ip}:{port}...\n"
                        f"[-] connection refused (port closed)"
                    ),
                    error=True, sound="error",
                )
            if port == 80:
                return MissionResult(
                    output=(
                        f"[*] dialing {ip}:{port}...\n"
                        f"[+] connected to Apache httpd 2.4.41\n"
                        "\n"
                        "<html><body>\n"
                        "<h1>It works!</h1>\n"
                        "<p>This is the default page. Nothing interesting here.</p>\n"
                        "</body></html>\n"
                        "\n"
                        "[*] connection closed by remote host"
                    ),
                    sound="click",
                )
            if port == 31337:
                return MissionResult(
                    output=(
                        f"[*] dialing {ip}:{port}...\n"
                        f"[+] connected to custom flag service\n"
                        "\n"
                        "Welcome, operator. Here is your reward:\n"
                        f"{mission.flag}\n"
                        "\n"
                        "[*] connection closed by remote host"
                    ),
                    sound="ok",
                )
            return MissionResult(output="unexpected port", error=True, sound="error")

        self.commands = {
            "nmap": CommandSpec(
                name="nmap",
                usage="nmap <target>",
                description="Simulated SYN scan against a target host.",
                handler=_nmap_handler,
            ),
            "connect": CommandSpec(
                name="connect",
                usage="connect <ip> <port>",
                description="Open a raw TCP connection to <ip>:<port>.",
                handler=_connect_handler,
            ),
        }

        self.hints = [
            HintTier(
                text="Run 'nmap 10.0.0.42' and look for ports marked 'open'. "
                     "Standard ports (22, 80, 443) are common; the flag service is on a less-obvious port.",
                cost=10,
            ),
            HintTier(
                text="The intel.txt file mentions the sysadmin runs a custom TCP service in the 30000-40000 range. "
                     "Port 31337 (aka 'eleet') is open.",
                cost=20,
            ),
            HintTier(
                text=f"Run: connect 10.0.0.42 31337",
                cost=30,
            ),
        ]


MISSION_NET_RECON = _ReconMission()


# ======================================================================
# Mission 4 - Packet Sniffing (Medium)
# ======================================================================
class _SniffMission(Mission):
    id = "m_net_sniff"
    title = "Packet Sniff"
    category = "Network Security"
    difficulty = "Medium"
    max_score = 150
    unlocks_codex = ["packet_sniffing", "pcap", "mitm"]
    unlocks_mission = "m_web_sqli"

    briefing = (
        "INCOMING TRANSMISSION - source: guild handler\n"
        "\n"
        "  We captured network traffic from a target who logged into a\n"
        "  legacy FTP server this morning. FTP sends credentials in\n"
        "  cleartext - if you can find them in the capture, you can log\n"
        "  in yourself.\n"
        "\n"
        "  Files:\n"
        "    capture.log    raw packet log (text)\n"
        "\n"
        "  Tools:\n"
        "    grep <pattern> <file>     search file for a pattern\n"
        "    ftp <user> <pass>         log into the FTP server\n"
        "\n"
        "  The flag is in a file on the FTP server."
    )

    objective = (
        "1. Look at the capture: cat capture.log\n"
        "2. Find FTP USER and PASS commands - try: grep USER capture.log\n"
        "3. Log in with the credentials: ftp <user> <pass>\n"
        "4. Submit the flag the FTP server returns."
    )

    def setup(self):
        self.flag = "flag{cleartext_is_not_a_protocol}"

        # The capture: include some HTTP, some DNS, and the FTP login + RETR
        self.fs = {
            "capture.log": (
                "=== packet capture: 14:22:01 to 14:23:47 ===\n"
                "\n"
                "14:22:01  10.0.0.5 -> 8.8.8.8     DNS  Standard query 0x1234 A example.com\n"
                "14:22:01  8.8.8.8  -> 10.0.0.5     DNS  Standard response 93.184.216.34\n"
                "14:22:08  10.0.0.5 -> 10.0.0.99    TCP  54213 -> 21 [SYN]\n"
                "14:22:08  10.0.0.99 -> 10.0.0.5    TCP  21 -> 54213 [SYN, ACK]\n"
                "14:22:08  10.0.0.5 -> 10.0.0.99    FTP  220 (vsFTPd 3.0.3)\n"
                "14:22:09  10.0.0.5 -> 10.0.0.99    FTP  USER shadowops\n"
                "14:22:09  10.0.0.99 -> 10.0.0.5    FTP  331 Please specify the password.\n"
                "14:22:10  10.0.0.5 -> 10.0.0.99    FTP  PASS n0rthP0le42!\n"
                "14:22:10  10.0.0.99 -> 10.0.0.5    FTP  230 Login successful.\n"
                "14:22:15  10.0.0.5 -> 10.0.0.99    FTP  RETR flag.txt\n"
                "14:22:15  10.0.0.99 -> 10.0.0.5    FTP  150 Opening BINARY mode data connection.\n"
                "14:22:17  10.0.0.5 -> 10.0.0.99    TCP  54213 -> 21 [FIN, ACK]\n"
                "14:22:20  10.0.0.5 -> 93.184.216.34 HTTP GET /index.html HTTP/1.1\n"
                "14:22:30  10.0.0.5 -> 8.8.8.8     DNS  Standard query 0x5678 A mail.example.com\n"
                "=== end of capture ===\n"
            ),
            "README.txt": (
                "FTP sends usernames and passwords in cleartext over port 21.\n"
                "Look for 'USER' and 'PASS' lines in the capture. Once you have\n"
                "the credentials, run: ftp <user> <pass>\n"
            ),
        }

        def _grep_handler(args, mission):
            if len(args) < 2:
                return MissionResult(
                    output="usage: grep <pattern> <file>",
                    error=True, sound="error",
                )
            pattern = args[0]
            path = args[1]
            content = mission.fs.get(path)
            if content is None:
                return MissionResult(
                    output=f"grep: {path}: No such file",
                    error=True, sound="error",
                )
            matches = [line for line in content.splitlines() if pattern in line]
            if not matches:
                return MissionResult(
                    output=f"(no matches for '{pattern}' in {path})",
                    sound="click",
                )
            return MissionResult(output="\n".join(matches), sound="click")

        def _ftp_handler(args, mission):
            if len(args) < 2:
                return MissionResult(
                    output="usage: ftp <user> <pass>",
                    error=True, sound="error",
                )
            user = args[0]
            pw = " ".join(args[1:])
            if user == "shadowops" and pw == "n0rthP0le42!":
                return MissionResult(
                    output=(
                        "[*] connecting to 10.0.0.99:21...\n"
                        "[+] 220 (vsFTPd 3.0.3)\n"
                        "[+] 230 Login successful.\n"
                        "ftp> RETR flag.txt\n"
                        "[+] 150 Opening BINARY mode data connection.\n"
                        "[+] 226 Transfer complete.\n"
                        "\n"
                        "---- flag.txt ----\n"
                        f"{mission.flag}\n"
                        "------------------\n"
                    ),
                    sound="ok",
                )
            return MissionResult(
                output=(
                    "[*] connecting to 10.0.0.99:21...\n"
                    "[+] 220 (vsFTPd 3.0.3)\n"
                    "[-] 530 Login incorrect."
                ),
                error=True, sound="error",
            )

        self.commands = {
            "grep": CommandSpec(
                name="grep",
                usage="grep <pattern> <file>",
                description="Search a file for lines containing the pattern.",
                handler=_grep_handler,
            ),
            "ftp": CommandSpec(
                name="ftp",
                usage="ftp <user> <pass>",
                description="Log into the captured FTP server with the given credentials.",
                handler=_ftp_handler,
            ),
        }

        self.hints = [
            HintTier(
                text="FTP sends credentials as 'USER <name>' and 'PASS <password>' over the wire. "
                     "Use grep to search the capture file for these commands.",
                cost=15,
            ),
            HintTier(
                text="Run: grep USER capture.log  and  grep PASS capture.log\n"
                     "That gives you the username and password in cleartext.",
                cost=20,
            ),
            HintTier(
                text=f"Credentials are: user='shadowops' password='n0rthP0le42!'\n"
                     f"Run: ftp shadowops n0rthP0le42!",
                cost=30,
            ),
        ]


MISSION_NET_SNIFF = _SniffMission()
