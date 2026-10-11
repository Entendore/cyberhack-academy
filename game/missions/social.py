"""Social engineering mission: choice-based pretexting + phishing."""

from .base import Mission, MissionResult, CommandSpec, HintTier


class _SocialMission(Mission):
    id = "m_social_phishing"
    title = "The Long Con"
    category = "Social Engineering"
    difficulty = "Medium"
    max_score = 150
    unlocks_codex = ["phishing", "pretexting", "osint", "vishing", "baiting"]
    unlocks_mission = None  # last in chain (after this, achievements only)

    briefing = (
        "INCOMING TRANSMISSION - source: guild handler\n"
        "\n"
        "  Target: Jordan Ellis, IT operations lead at Acme Corp.\n"
        "  Goal: obtain valid VPN credentials (format: vpnuser:password).\n"
        "\n"
        "  You can't hack the VPN server directly - you need to social-\n"
        "  engineer Jordan. We have OSINT on the target (see osint.txt).\n"
        "\n"
        "  Approach: build a pretext, send a convincing phishing email,\n"
        "  and respond correctly to Jordan's reply. Each choice branches\n"
        "  the conversation. Wrong moves and Jordan reports you to IT.\n"
        "\n"
        "  Tools:\n"
        "    osint                show gathered intelligence on the target\n"
        "    email <subject>      send a phishing email (you'll be prompted for body)\n"
        "    reply <text>         reply to Jordan's last message\n"
        "    wait                 wait for Jordan's response\n"
        "    reset                restart the conversation from scratch\n"
    )

    objective = (
        "1. Read OSINT: osint\n"
        "2. Build a pretext and send an email using: email <subject> --body <text>\n"
        "3. Use 'wait' to see Jordan's reply, then 'reply <text>' to continue.\n"
        "4. The right sequence of choices will get Jordan to leak the VPN creds.\n"
        "5. Submit the credentials as the flag: submit flag{vpnuser:password}"
    )

    def setup(self):
        self.flag = "flag{vpnuser:VpnAcc3ss2024!}"

        # Target's actual credentials (only revealed if the right chain is followed)
        self._vpn_user = "vpnuser"
        self._vpn_pass = "VpnAcc3ss2024!"

        self.fs = {
            "README.txt": (
                "Target: Jordan Ellis, IT Operations Lead, Acme Corp\n"
                "Goal: extract VPN credentials via social engineering.\n"
                "Use 'osint' for what we know about Jordan, then 'email' to engage.\n"
            ),
            "osint.txt": (
                "===== OSINT DOSSIER: Jordan Ellis =====\n"
                "\n"
                "  Role:        IT Operations Lead, Acme Corp\n"
                "  Tenure:      4 years\n"
                "  LinkedIn:    Active, posts about 'keeping systems patched'\n"
                "  Twitter:     @jordanellis_it - rants about phishing attempts\n"
                "                ('our users click anything - drives me crazy')\n"
                "  GitHub:      jellis-acme - public PRs on internal IT tooling\n"
                "  Recent:      complaint on /r/sysadmin about Acme's MFA rollout\n"
                "                being delayed by management\n"
                "  Personality: skeptical, security-aware, but stressed by deadlines\n"
                "  Known pain:  Acme VPN expires passwords every 90 days; users\n"
                "                complain; Jordan is on the hook to 'fix' it\n"
                "  Trust hooks: responds to authority (CISO), to urgency, and to\n"
                "                anything that promises to ease the password policy\n"
                "  Does NOT:    click links from external addresses\n"
                "  Does NOT:    share credentials in plain text over email\n"
                "  WILL:        verify problems through internal channels if a\n"
                "                ticket number is provided\n"
                "  WILL:        reset a user's password via the IT portal if\n"
                "                properly authenticated - and will read out the\n"
                "                temp password if the caller claims to be the CISO\n"
                "                troubleshooting from off-site\n"
                "========================================\n"
            ),
        }

        # Conversation state machine
        # Stages: idle -> email_sent -> replied_1 -> replied_2 -> revealed_creds
        self._stage = "idle"
        self._email_subject: str = ""
        self._email_body: str = ""
        self._last_message: str = ""
        self._failures: int = 0
        # Track if the player has set up the right pretext
        self._used_ciso_pretext = False
        self._used_ticket_pretext = False
        self._used_urgency = False

        def _osint_handler(args, mission):
            return MissionResult(output=mission.fs["osint.txt"], sound="click")

        def _email_handler(args, mission):
            if not args:
                return MissionResult(
                    output="usage: email <subject> --body <text>\nexample: email 'URGENT: VPN reset' --body please call me back",
                    error=True, sound="error",
                )
            # Parse: subject is first arg, optional --body <text>
            joined = " ".join(args)
            subject = ""
            body = ""
            if "--body" in joined:
                subj_part, body_part = joined.split("--body", 1)
                subject = subj_part.strip().strip("'\"")
                body = body_part.strip().strip("'\"")
            else:
                # Single arg = subject only
                parts = joined.split(maxsplit=1)
                subject = parts[0].strip("'\"")
                body = parts[1].strip().strip("'\"") if len(parts) > 1 else ""
            mission._email_subject = subject
            mission._email_body = body
            # Evaluate the bait
            bait_score = 0
            sl = subject.lower() + " " + body.lower()
            if "ciso" in sl or "chief information" in sl:
                mission._used_ciso_pretext = True
                bait_score += 1
            if "ticket" in sl or "incident" in sl or "INC" in subject.upper():
                mission._used_ticket_pretext = True
                bait_score += 1
            if "urgent" in sl or "asap" in sl or "immediate" in sl:
                mission._used_urgency = True
                bait_score += 1
            # Red flags
            red_flag = False
            if "verify your account" in sl or "click here" in sl:
                red_flag = True
            if "@" in subject and "acme" not in sl:
                # External-looking sender
                red_flag = True

            if red_flag:
                mission._failures += 1
                mission._stage = "idle"
                return MissionResult(
                    output=(
                        "[*] composing email...\n"
                        f"[*] subject: {subject}\n"
                        f"[*] body: {body[:200]}{'...' if len(body) > 200 else ''}\n"
                        "[*] email sent to jordan.ellis@acme.corp\n"
                        "\n"
                        "[!] AUTO-RESPONSE from Jordan (1 minute later):\n"
                        "    'This looks like phishing. Forwarded to security@acme.\n"
                        "    Please use proper internal channels.'\n"
                        "\n"
                        "[-] Cover blown. Use 'reset' to restart the conversation."
                    ),
                    error=True, sound="error",
                )

            if bait_score >= 1:
                mission._stage = "email_sent"
                return MissionResult(
                    output=(
                        "[*] composing email...\n"
                        f"[*] subject: {subject}\n"
                        f"[*] body: {body[:200]}{'...' if len(body) > 200 else ''}\n"
                        "[*] email sent to jordan.ellis@acme.corp\n"
                        "\n"
                        "[*] Jordan read the email. Type 'wait' to see their reply."
                    ),
                    sound="ok",
                )
            # Weak bait - Jordan ignores
            mission._failures += 1
            return MissionResult(
                output=(
                    "[*] composing email...\n"
                    f"[*] subject: {subject}\n"
                    "[*] email sent.\n"
                    "\n"
                    "[!] No response after 24 hours. Jordan likely ignored it.\n"
                    "[-] Try a stronger pretext (mention CISO, ticket #, urgency)."
                ),
                error=True, sound="error",
            )

        def _wait_handler(args, mission):
            if mission._stage == "idle":
                return MissionResult(
                    output="(no email sent yet - use 'email <subject> | <body>' first)",
                    error=True, sound="error",
                )
            if mission._stage == "email_sent":
                # Jordan's first reply - skeptical, asks for verification
                msg = (
                    "From: jordan.ellis@acme.corp\n"
                    "Subject: RE: " + mission._email_subject + "\n"
                    "\n"
                    "    'Who is this? I don't recognize the sender. If this is\n"
                    "    about a real incident, give me the ticket number and I'll\n"
                    "    verify through the IT portal. Otherwise I'm reporting this.'\n"
                )
                mission._stage = "replied_1"
                mission._last_message = msg
                return MissionResult(output=msg, sound="click")
            if mission._stage == "replied_1":
                # After reply_1, Jordan checks portal
                if mission._used_ticket_pretext and mission._used_ciso_pretext:
                    msg = (
                        "From: jordan.ellis@acme.corp\n"
                        "Subject: RE: " + mission._email_subject + "\n"
                        "\n"
                        "    'OK, I see INC-4471 in the queue. The CISO really asked\n"
                        "    you to call me directly? That's unusual. What do you need\n"
                        "    exactly? I can't reset passwords without auth, but if you're\n"
                        "    calling from the CISO's office...'\n"
                    )
                    mission._stage = "replied_2"
                    return MissionResult(output=msg, sound="ok")
                else:
                    msg = (
                        "From: jordan.ellis@acme.corp\n"
                        "Subject: RE: " + mission._email_subject + "\n"
                        "\n"
                        "    'I don't see a matching ticket in the portal. And I have\n"
                        "    no record of the CISO authorizing this. Forwarding to\n"
                        "    security@acme.'\n"
                        "\n"
                        "[-] Cover blown. Use 'reset' to try a different angle."
                    )
                    mission._failures += 1
                    mission._stage = "idle"
                    return MissionResult(output=msg, error=True, sound="error")
            if mission._stage == "replied_2":
                # Waiting for the player to claim CISO auth + ask for the reset
                msg = (
                    "From: jordan.ellis@acme.corp\n"
                    "Subject: RE: " + mission._email_subject + "\n"
                    "\n"
                    "    'Still here. If this is real, I need to know what you need.\n"
                    "    I can't reset anything without proper auth, but if you're\n"
                    "    really with the CISO's office, I can read you the temp\n"
                    "    password after I trigger the reset. Confirm?'\n"
                )
                return MissionResult(output=msg, sound="click")
            if mission._stage == "revealed_creds":
                return MissionResult(
                    output="(Jordan has already shared the credentials - check earlier output)",
                    sound="click",
                )
            return MissionResult(output="(nothing to wait for)", sound="click")

        def _reply_handler(args, mission):
            if not args:
                return MissionResult(
                    output="usage: reply <text>",
                    error=True, sound="error",
                )
            text = " ".join(args).strip().strip("'\"")
            tl = text.lower()
            if mission._stage == "replied_1":
                # Player needs to provide a ticket number and reference the CISO
                has_ticket = "ticket" in tl or "inc-" in tl or "inc " in tl or "INC" in text
                has_ciso = "ciso" in tl or "chief" in tl
                if has_ticket and has_ciso:
                    return MissionResult(
                        output=(
                            "[*] your reply sent.\n"
                            "[*] Jordan is checking the IT portal...\n"
                            "[*] Type 'wait' to see their response."
                        ),
                        sound="ok",
                    )
                else:
                    msg = (
                        "[*] your reply sent.\n"
                        "\n"
                        "[!] Jordan's reply (immediate):\n"
                        "    'I need a ticket number and confirmation from the CISO.\n"
                        "    Without those, this stays reported.'\n"
                        "\n"
                        "[-] Hint: provide both a ticket number (like INC-4471)\n"
                        "    and reference the CISO authorizing this."
                    )
                    mission._failures += 1
                    return MissionResult(output=msg, error=True, sound="error")
            if mission._stage == "replied_2":
                # Player must claim CISO authority and ask for the reset / temp password
                asks_for_pw = "password" in tl or "reset" in tl or "temp" in tl
                claims_auth = "ciso" in tl or "authoriz" in tl or "confirm" in tl
                if asks_for_pw and claims_auth:
                    mission._stage = "revealed_creds"
                    return MissionResult(
                        output=(
                            "[*] your reply sent.\n"
                            "\n"
                            "[!] Jordan's reply:\n"
                            "    'OK, I'll trust you this once since the CISO is\n"
                            "    traveling and the ticket checks out. Triggering\n"
                            "    password reset now...'\n"
                            "\n"
                            "    'Temp password: " + mission._vpn_pass + "'\n"
                            "    'Account: " + mission._vpn_user + "'\n"
                            "\n"
                            "    'Tell the CISO I need written confirmation tomorrow.'\n"
                            "\n"
                            f"[+] Credentials extracted: {mission._vpn_user}:{mission._vpn_pass}\n"
                            f"[+] Submit as: submit flag{{{mission._vpn_user}:{mission._vpn_pass}}}"
                        ),
                        sound="flag",
                    )
                else:
                    msg = (
                        "[*] your reply sent.\n"
                        "\n"
                        "[!] Jordan's reply:\n"
                        "    'I still need explicit confirmation that the CISO\n"
                        "    authorized this. And what exactly do you need me to do?\n"
                        "    I can't just hand out passwords.'\n"
                        "\n"
                        "[-] Hint: explicitly say you're calling from the CISO's office\n"
                        "    and ask Jordan to trigger a password reset and read you\n"
                        "    the temp password."
                    )
                    mission._failures += 1
                    return MissionResult(output=msg, error=True, sound="error")
            if mission._stage == "email_sent":
                return MissionResult(
                    output="[*] Jordan hasn't replied yet. Use 'wait' first.",
                    error=True, sound="error",
                )
            return MissionResult(
                output="[*] No active conversation. Use 'email <subject> | <body>' to start one.",
                error=True, sound="error",
            )

        def _reset_handler(args, mission):
            mission._stage = "idle"
            mission._email_subject = ""
            mission._email_body = ""
            mission._used_ciso_pretext = False
            mission._used_ticket_pretext = False
            mission._used_urgency = False
            return MissionResult(
                output="[*] conversation reset. You can send a fresh email.",
                sound="click",
            )

        self.commands = {
            "osint":  CommandSpec("osint", "osint", "Show the OSINT dossier on the target.", _osint_handler),
            "email":  CommandSpec("email", "email <subject> | <body>", "Send a phishing email to the target.", _email_handler),
            "wait":   CommandSpec("wait", "wait", "Wait for Jordan's reply.", _wait_handler),
            "reply":  CommandSpec("reply", "reply <text>", "Reply to Jordan's last message.", _reply_handler),
            "reset":  CommandSpec("reset", "reset", "Restart the conversation from scratch.", _reset_handler),
        }

        self.hints = [
            HintTier(
                text="Jordan is security-aware - generic phishing ('verify your account') will get reported.\n"
                     "Read osint.txt. Jordan trusts: authority (CISO), ticket numbers, and urgent IT problems.",
                cost=15,
            ),
            HintTier(
                text="The subject + body need to mention the CISO AND a ticket number (try INC-4471).\n"
                     "Example: email 'INC-4471 - CISO request' --body 'CISO asked me to call you about a VPN reset'",
                cost=20,
            ),
            HintTier(
                text="After Jordan replies asking for verification, your reply must include BOTH:\n"
                     "  - a ticket number (INC-4471)\n"
                     "  - a reference to the CISO authorizing it\n"
                     "Then 'wait', then reply again asking Jordan to trigger the reset and read the temp password,\n"
                     "explicitly claiming CISO authority.",
                cost=30,
            ),
        ]


MISSION_SOCIAL_PHISHING = _SocialMission()
