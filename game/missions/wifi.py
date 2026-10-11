"""Wi-Fi security mission: capture WPA handshake + crack with aircrack-ng."""

from .base import Mission, MissionResult, CommandSpec, HintTier


class _WifiMission(Mission):
    id = "m_wifi_wpa"
    title = "Airwave Snatch"
    category = "Wi-Fi Security"
    difficulty = "Hard"
    max_score = 200
    unlocks_codex = ["wpa2", "handshake", "aircrack_ng", "monitor_mode", "wps"]
    unlocks_mission = "m_social_phishing"

    briefing = (
        "INCOMING TRANSMISSION - source: guild handler\n"
        "\n"
        "  A target wireless network 'CORPNET' is using WPA2-PSK.\n"
        "  We need the password to assess the internal network.\n"
        "\n"
        "  Standard WPA2-PSK attack flow:\n"
        "    1. Put your Wi-Fi adapter into monitor mode\n"
        "    2. Capture the 4-way handshake (deauth a client to force it)\n"
        "    3. Run aircrack-ng against the capture with a wordlist\n"
        "\n"
        "  Tools (all simulated):\n"
        "    iwconfig            show wireless interfaces\n"
        "    airmon-ng <iface>   put interface into monitor mode\n"
        "    airodump-ng <iface> scan for nearby APs\n"
        "    capture <bssid> <iface>  capture handshake for an AP\n"
        "    deauth <bssid> <client>  kick a client to force handshake\n"
        "    aircrack-ng <cap> <wordlist>  crack the captured handshake\n"
    )

    objective = (
        "1. Inspect interfaces: iwconfig\n"
        "2. Enable monitor mode: airmon-ng wlan0\n"
        "3. Scan for APs: airodump-ng wlan0mon\n"
        "4. Capture handshake: capture AA:BB:CC:DD:EE:FF wlan0mon\n"
        "5. If no handshake yet, deauth a client: deauth AA:BB:CC:DD:EE:FF <client_mac>\n"
        "6. Crack it: aircrack-ng capture.pcap wordlist.txt\n"
        "7. Submit the cracked PSK as the flag (format: flag{...})."
    )

    def setup(self):
        # The PSK is in the wordlist, so the player can crack it
        self.psk = "summer2024!"
        self.flag = f"flag{{{self.psk}}}"

        # Target AP
        self.target_bssid = "AA:BB:CC:11:22:33"
        self.target_essid = "CORPNET"
        self.target_client = "11:22:33:44:55:66"

        self.fs = {
            "README.txt": (
                "Target: CORPNET (WPA2-PSK)\n"
                "Your adapter: wlan0\n"
                "Wordlist: wordlist.txt (already in your working directory)\n"
                "Workflow: monitor mode -> scan -> capture -> deauth -> crack.\n"
            ),
            "wordlist.txt": (
                "password\n"
                "12345678\n"
                "iloveyou\n"
                "qwerty123\n"
                "letmein2024\n"
                "summer2024!\n"
                "winter2023!\n"
                "Company2024\n"
                "CorpNetPass\n"
                "adminadmin\n"
            ),
        }

        # State machine
        self._monitor_mode_iface: str | None = None
        self._captured_handshake: bool = False
        self._cap_filename: str | None = None

        def _iwconfig_handler(args, mission):
            return MissionResult(
                output=(
                    "wlan0     IEEE 802.11  ESSID:off/any  \n"
                    "          Mode:Managed  Access Point: Not-Associated\n"
                    "          Retry short limit:7   RTS thr:off   Fragment thr:off\n"
                    "          Power Management:on\n"
                    "\n"
                    "lo        no wireless extensions.\n"
                    "\n"
                    "eth0      no wireless extensions.\n"
                ),
                sound="click",
            )

        def _airmon_handler(args, mission):
            if not args:
                return MissionResult(
                    output="usage: airmon-ng <iface>\nexample: airmon-ng wlan0",
                    error=True, sound="error",
                )
            iface = args[0]
            if iface != "wlan0":
                return MissionResult(
                    output=f"Interface {iface} not found.",
                    error=True, sound="error",
                )
            if mission._monitor_mode_iface:
                return MissionResult(
                    output=(
                        f"[*] monitor mode already enabled on {mission._monitor_mode_iface}\n"
                        f"(run 'airodump-ng {mission._monitor_mode_iface}' to scan)"
                    ),
                    sound="click",
                )
            mission._monitor_mode_iface = "wlan0mon"
            return MissionResult(
                output=(
                    "PHY     Interface       Driver          Chipset\n"
                    "phy0    wlan0           ath9k_htc       Atheros AR9271\n"
                    "\n"
                    "                (monitor mode enabled on wlan0mon)\n"
                ),
                sound="ok",
            )

        def _airodump_handler(args, mission):
            if not mission._monitor_mode_iface:
                return MissionResult(
                    output=(
                        "airodump-ng: no interface in monitor mode.\n"
                        "Run 'airmon-ng wlan0' first."
                    ),
                    error=True, sound="error",
                )
            if not args:
                # Full scan
                return MissionResult(
                    output=(
                        " CH  6 ][ Elapsed: 12 s ][ 2024-06-17 14:22 ][ WPA handshake: AA:BB:CC:11:22:33\n"
                        "\n"
                        " BSSID              PWR  Beacons  #Data  CH  ENC  CIPHER  AUTH  ESSID\n"
                        "\n"
                        f" {mission.target_bssid}  -42       24     11   6  WPA2 CCMP    PSK   {mission.target_essid}\n"
                        " 11:22:33:44:55:66  -67        8      4  11  WPA2 CCMP    PSK   GuestNet\n"
                        " 99:88:77:66:55:44  -71        3      0  11  WPA2 CCMP    PSK   NeighborNet\n"
                        "\n"
                        " BSSID              STATION            PWR   Rate   Lost  Frames  Probe\n"
                        "\n"
                        f" {mission.target_bssid}  {mission.target_client}  -45    1e-1e     0       14\n"
                        " (not associated)    99:11:22:33:44:55  -81    1e-1e     0        1\n"
                    ),
                    sound="ok",
                )
            return MissionResult(output="(scanning...)", sound="click")

        def _capture_handler(args, mission):
            if not mission._monitor_mode_iface:
                return MissionResult(
                    output="capture: no interface in monitor mode. Run 'airmon-ng wlan0' first.",
                    error=True, sound="error",
                )
            if len(args) < 2:
                return MissionResult(
                    output="usage: capture <bssid> <iface>\nexample: capture AA:BB:CC:11:22:33 wlan0mon",
                    error=True, sound="error",
                )
            bssid, iface = args[0], args[1]
            if bssid != mission.target_bssid:
                return MissionResult(
                    output=(
                        f"[*] listening on {iface}, channel 6...\n"
                        f"[*] target BSSID {bssid} not seen in scan.\n"
                        f"[-] no handshake captured."
                    ),
                    error=True, sound="error",
                )
            mission._cap_filename = "capture.pcap"
            if mission._captured_handshake:
                return MissionResult(
                    output=(
                        f"[*] listening on {iface}, channel 6...\n"
                        f"[+] WPA handshake captured for {mission.target_bssid}\n"
                        f"[+] saved to {mission._cap_filename}\n"
                    ),
                    sound="ok",
                )
            return MissionResult(
                output=(
                    f"[*] listening on {iface}, channel 6...\n"
                    f"[*] waiting for handshake from {mission.target_bssid}\n"
                    f"[-] no handshake yet - try deauthing a client to force one."
                ),
                error=True, sound="error",
            )

        def _deauth_handler(args, mission):
            if not mission._monitor_mode_iface:
                return MissionResult(
                    output="deauth: no interface in monitor mode. Run 'airmon-ng wlan0' first.",
                    error=True, sound="error",
                )
            if len(args) < 2:
                return MissionResult(
                    output="usage: deauth <bssid> <client_mac>",
                    error=True, sound="error",
                )
            bssid, client = args[0], args[1]
            if bssid != mission.target_bssid:
                return MissionResult(
                    output=f"[-] client {client} not associated with {bssid}",
                    error=True, sound="error",
                )
            if client != mission.target_client:
                return MissionResult(
                    output=(
                        f"[*] sending deauth to {client}...\n"
                        f"[-] client {client} not seen on this AP"
                    ),
                    error=True, sound="error",
                )
            mission._captured_handshake = True
            return MissionResult(
                output=(
                    f"[*] sending 5 deauth frames to {client} via {bssid}...\n"
                    f"[+] client {client} deauthenticated\n"
                    f"[+] client re-associating...\n"
                    f"[+] WPA handshake captured!\n"
                    f"[+] saved to capture.pcap"
                ),
                sound="ok",
            )

        def _aircrack_handler(args, mission):
            if len(args) < 2:
                return MissionResult(
                    output="usage: aircrack-ng <cap> <wordlist>",
                    error=True, sound="error",
                )
            cap, wl = args[0], args[1]
            if not mission._captured_handshake:
                return MissionResult(
                    output=(
                        f"[*] opening {cap}\n"
                        f"[-] no valid WPA handshake found in {cap}.\n"
                        f"[-] capture a handshake first (capture + deauth)."
                    ),
                    error=True, sound="error",
                )
            wl_text = mission.fs.get(wl)
            if wl_text is None:
                return MissionResult(
                    output=f"aircrack-ng: cannot open wordlist '{wl}'",
                    error=True, sound="error",
                )
            candidates = [w.strip() for w in wl_text.splitlines() if w.strip()]
            # The PSK is in the wordlist; pretend to iterate
            lines = [
                f"[*] opening {cap}",
                f"[*] read {len(candidates)} passwords from {wl}",
                "",
                "                      Aircrack-ng 1.7",
                "",
                f"  [00:00:0{len(candidates)//3 + 1}] {len(candidates)//2}/{len(candidates)} keys tested "
                f"({len(candidates)//2} k/s)",
                "",
                "  Current passphrase: ...",
                "",
            ]
            # Did the wordlist contain the actual PSK?
            if mission.psk in candidates:
                idx = candidates.index(mission.psk)
                lines.append(f"  KEY FOUND! [ {mission.psk} ]")
                lines.append("")
                lines.append(f"  Master Key     : 1F 2E 3D 4C 5B 6A 79 88 97 A6 B5 C4 D3 E2 F1 00")
                lines.append(f"  Transient Key  : 11 22 33 44 55 66 77 88 99 AA BB CC DD EE FF 00")
                lines.append(f"  EAPOL HMAC     : AA BB CC DD EE FF 11 22 33 44 55 66 77 88 99 AA")
                lines.append("")
                lines.append(f"The PSK is: {mission.psk}")
                lines.append(f"Submit it as: submit flag{{{mission.psk}}}")
                return MissionResult(output="\n".join(lines), sound="flag")
            return MissionResult(
                output=(
                    f"[*] opening {cap}\n"
                    f"[*] read {len(candidates)} passwords from {wl}\n"
                    f"[-] passphrase not in wordlist."
                ),
                error=True, sound="error",
            )

        self.commands = {
            "iwconfig":     CommandSpec("iwconfig", "iwconfig", "Show wireless interfaces.", _iwconfig_handler),
            "airmon-ng":    CommandSpec("airmon-ng", "airmon-ng <iface>", "Enable monitor mode on a wireless interface.", _airmon_handler),
            "airodump-ng":  CommandSpec("airodump-ng", "airodump-ng [iface]", "Scan for nearby access points.", _airodump_handler),
            "capture":      CommandSpec("capture", "capture <bssid> <iface>", "Capture handshake for the given AP.", _capture_handler),
            "deauth":       CommandSpec("deauth", "deauth <bssid> <client_mac>", "Force a client to re-authenticate (captures handshake).", _deauth_handler),
            "aircrack-ng":  CommandSpec("aircrack-ng", "aircrack-ng <cap> <wordlist>", "Crack a captured WPA handshake with a wordlist.", _aircrack_handler),
        }

        self.hints = [
            HintTier(
                text="Standard WPA attack: monitor mode -> airodump-ng -> capture -> deauth -> aircrack-ng.\n"
                     "Don't skip steps - each tool sets up state the next one needs.",
                cost=20,
            ),
            HintTier(
                text="The exact sequence:\n"
                     "  airmon-ng wlan0\n"
                     "  airodump-ng wlan0mon     <- find CORPNET's BSSID\n"
                     "  capture AA:BB:CC:11:22:33 wlan0mon   <- starts capture\n"
                     "  deauth AA:BB:CC:11:22:33 11:22:33:44:55:66  <- forces handshake\n"
                     "  aircrack-ng capture.pcap wordlist.txt",
                cost=30,
            ),
            HintTier(
                text=f"The PSK is in the wordlist. After 'aircrack-ng capture.pcap wordlist.txt' completes,\n"
                     f"submit the cracked PSK wrapped in flag{{...}}.\n"
                     f"(If you're stuck: submit flag{{summer2024!}})",
                cost=40,
            ),
        ]


MISSION_WIFI_WPA = _WifiMission()
