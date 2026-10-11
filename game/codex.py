"""In-game codex / glossary of security terms."""

CODEX = [
    # (id, term, category, definition)
    ("caesar_cipher", "Caesar Cipher", "Cryptography",
     "A substitution cipher where each letter in the plaintext is shifted by a fixed number of positions down the alphabet. "
     "Trivially broken by brute force (only 25 possible shifts) or frequency analysis. Named after Julius Caesar, who used shift=3."),

    ("frequency_analysis", "Frequency Analysis", "Cryptography",
     "Technique for breaking substitution ciphers by comparing letter frequencies in the ciphertext against the known "
     "frequency distribution of the target language. In English, 'E' is the most common letter (~12.7%), followed by 'T', 'A', 'O'."),

    ("hash_function", "Hash Function", "Cryptography",
     "A one-way function that maps data of arbitrary size to a fixed-size digest. Good cryptographic hashes (SHA-256, BLAKE2) "
     "are collision-resistant and preimage-resistant. MD5 and SHA-1 are considered broken for crypto use but still appear in legacy systems."),

    ("md5", "MD5", "Cryptography",
     "A 128-bit hash function designed by Ron Rivest in 1991. Broken for collision resistance since the early 2000s. "
     "Still widely found in CTF challenges, file checksums, and legacy password stores. Cracked with rainbow tables or wordlists."),

    ("rainbow_table", "Rainbow Table", "Cryptography",
     "Precomputed table of hash -> plaintext mappings used to reverse hash functions quickly. Defeated by salting: "
     "appending a unique random value to each password before hashing makes precomputed tables useless."),

    ("salt", "Salt", "Cryptography",
     "A random value added to a password before hashing, stored alongside the hash. Even if two users share the same password, "
     "their salts (and therefore hashes) differ. Modern password hashing (bcrypt, argon2) embeds the salt in the output string."),

    ("wordlist", "Wordlist", "Cryptography",
     "A list of candidate passwords (often leaked databases like rockyou.txt) used in dictionary attacks against a hash. "
     "Tools like hashcat and john the ripper iterate over the list, hashing each candidate and comparing to the target."),

    ("port_scan", "Port Scan", "Network Security",
     "Probing a host for open TCP/UDP ports to identify running services. The classic tool is nmap. "
     "Common scan types: -sS (SYN scan, stealthy), -sT (connect scan, no special privileges), -sU (UDP, slow)."),

    ("nmap", "nmap", "Network Security",
     "Network mapper - the de-facto standard port scanner. Sends crafted packets and infers service versions from responses. "
     "Flags: -sV (version detection), -O (OS detection), -p- (all 65535 ports), --script (NSE scripts for vuln detection)."),

    ("three_way_handshake", "TCP 3-Way Handshake", "Network Security",
     "Connection setup between TCP client and server: SYN (client -> server, 'I want to talk'), "
     "SYN-ACK (server -> client, 'OK, me too'), ACK (client -> server, 'Confirmed'). A SYN scan sends SYN but never completes "
     "the handshake - hence the name 'half-open' scan."),

    ("ftp", "FTP", "Network Security",
     "File Transfer Protocol - sends files (and credentials!) in cleartext over port 21 for control and port 20 for data. "
     "Trivially sniffable. Modern alternatives: SFTP (over SSH) and FTPS (FTP over TLS)."),

    ("pcap", "PCAP", "Network Security",
     "Packet capture file format produced by tools like tcpdump and Wireshark. Contains raw frames as seen on the wire. "
     "Common filters: 'tcp port 80', 'host 192.168.1.5', 'tcp contains \"password\"'."),

    ("packet_sniffing", "Packet Sniffing", "Network Security",
     "Passively capturing network traffic. On wired Ethernet, requires promiscuous mode or a span port. "
     "On Wi-Fi, monitor mode captures all frames in the air. Cleartext protocols (FTP, HTTP, Telnet) leak credentials directly."),

    ("mitm", "Man-in-the-Middle", "Network Security",
     "Attack where the attacker relays (and possibly alters) traffic between two parties who believe they are talking directly. "
     "Defeated by TLS with proper certificate validation. Tools: ettercap, bettercap, mitmproxy."),

    ("sql_injection", "SQL Injection", "Web Security",
     "Vulnerability where untrusted input is concatenated into a SQL query, allowing the attacker to alter query semantics. "
     "Classic payload: ' OR '1'='1 which makes WHERE clauses always true. Defense: parameterized queries / prepared statements."),

    ("prepared_statement", "Prepared Statement", "Web Security",
     "A SQL query template with placeholders (? or :name) sent to the DB engine separately from the parameter values. "
     "The engine treats parameters strictly as data, never as SQL syntax - this makes injection impossible."),

    ("xss", "Cross-Site Scripting (XSS)", "Web Security",
     "Injection of JavaScript into a web page viewed by other users. Three flavors: stored (persisted in DB), reflected (in URL), "
     "DOM-based (client-side). Lets attackers steal cookies, log keystrokes, or perform actions as the victim."),

    ("cookie", "Cookie", "Web Security",
     "A key=value pair stored in the browser and sent with every request to the originating domain. HttpOnly flag blocks JS access "
     "(defeats XSS cookie theft); Secure flag forces HTTPS-only; SameSite=Strict/Lax blocks CSRF."),

    ("csrf", "Cross-Site Request Forgery (CSRF)", "Web Security",
     "Attack where a malicious site triggers an authenticated request to a victim site (e.g. <img src='bank.com/transfer?to=attacker'>). "
     "Defeated by anti-CSRF tokens, SameSite cookies, and re-authentication for sensitive actions."),

    ("disassembly", "Disassembly", "Reverse Engineering",
     "Converting machine code bytes back into human-readable assembly. Tools: objdump, IDA Pro, Ghidra, radare2. "
     "Assembly is architecture-specific (x86-64, ARM, RISC-V, etc.)."),

    ("control_flow", "Control Flow Graph", "Reverse Engineering",
     "A graph of basic blocks (straight-line code) connected by jumps and calls. Built by disassemblers to visualize "
     "function structure. Loops, conditionals, and calls become visible as edges in the graph."),

    ("buffer_overflow", "Buffer Overflow", "Reverse Engineering",
     "Writing past the end of a fixed-size buffer, corrupting adjacent memory. Classic exploit: overwrite the return address "
     "on the stack to redirect execution to attacker-controlled shellcode. Modern defenses: ASLR, stack canaries, NX bit, DEP."),

    ("flag", "Flag", "CTF Culture",
     "The string you must capture to prove you solved a challenge. Usually wrapped in a recognizable format like "
     "flag{...} or CTF{...}. Submit it to score the mission."),

    # ---- Linux privilege escalation ----
    ("suid", "SUID Bit", "Linux Privilege Escalation",
     "Set-User-ID bit - a file permission flag that causes the executable to run with the privileges of the file's "
     "OWNER, not the user invoking it. When a SUID binary is owned by root, it runs as root. Many SUID root binaries "
     "(passwd, sudo, su) are intentional; custom SUID root scripts are almost always a privilege escalation vector."),

    ("sudoers", "Sudoers Policy", "Linux Privilege Escalation",
     "The /etc/sudoers file (and /etc/sudoers.d/*) defines which users can run which commands as root via sudo. "
     "Misconfigurations like 'user ALL=(ALL) NOPASSWD: /usr/bin/vim' are instant root - vim can shell out with :!sh. "
     "Always run 'sudo -l' to enumerate your permissions."),

    ("privilege_escalation", "Privilege Escalation", "Linux Privilege Escalation",
     "The act of going from a low-privilege account (e.g. www-data, guest) to a higher one (root). Vectors include "
     "kernel exploits, SUID binaries, sudo misconfigurations, writable cron scripts, and credential reuse. "
     "Tools: linpeas, linenum, linuxprivchecker."),

    ("linpeas", "LinPEAS", "Linux Privilege Escalation",
     "Linux Privilege Escalation Awesome Script - an automated enumeration tool that color-codes likely privesc "
     "vectors (SUID binaries, writable paths, sudo perms, etc.). Output is large but the red/yellow highlights "
     "are usually where the answer is."),

    # ---- Wi-Fi security ----
    ("wpa2", "WPA2-PSK", "Wi-Fi Security",
     "Wi-Fi Protected Access 2 - Pre-Shared Key. The most common home/SOHO Wi-Fi security protocol. The PSK is "
     "derived from the network password via PBKDF2 with the SSID as salt. Vulnerable to offline dictionary attacks "
     "if you capture the 4-way handshake. WPA3 closes this hole with SAE."),

    ("handshake", "4-Way Handshake", "Wi-Fi Security",
     "The 4-message exchange between AP and client that proves both know the PSK without ever sending it. Messages: "
     "ANonce -> SNonce + MIC -> GTK + MIC -> ACK. Capturing all 4 frames lets you offline-brute-force the PSK."),

    ("aircrack_ng", "aircrack-ng", "Wi-Fi Security",
     "The classic Wi-Fi cracking suite. Tools: airmon-ng (monitor mode), airodump-ng (scan), aireplay-ng (deauth / "
     "inject), aircrack-ng (crack capture with wordlist). Still effective against WPA2-PSK if the password is weak."),

    ("monitor_mode", "Monitor Mode", "Wi-Fi Security",
     "Special Wi-Fi adapter mode that captures all frames in the air, not just those addressed to you. Required for "
     "handshake capture and deauth attacks. Not all chipsets support it; the Alfa AWUS036NHA is the classic choice."),

    ("wps", "WPS", "Wi-Fi Security",
     "Wi-Fi Protected Setup - a flawed 'easy connect' feature using an 8-digit PIN. Vulnerable to the Pixie-Dust "
     "attack (reaver, bully) which cracks the PIN in minutes. Once cracked, the WPA2 PSK is recovered too. "
     "Disable WPS on any router you control."),

    # ---- Social engineering ----
    ("phishing", "Phishing", "Social Engineering",
     "Fraudulent communication (usually email) impersonating a trusted entity to trick the victim into revealing "
     "credentials, opening malware, or sending money. Variants: spear-phishing (targeted), whaling (target = exec), "
     "smishing (SMS), vishing (voice)."),

    ("pretexting", "Pretexting", "Social Engineering",
     "Creating a fabricated scenario (the 'pretext') to lower a target's defenses. Examples: 'I'm calling from the "
     "CISO's office about INC-4471', 'I'm the new vendor onboarding specialist'. The pretext must match what the "
     "target expects to hear - that's what makes it believable."),

    ("osint", "OSINT", "Social Engineering",
     "Open-Source Intelligence - gathering information about a target from public sources (LinkedIn, Twitter, "
     "GitHub, SEC filings, breach databases). The more you know about a target's role, pain points, and tone, the "
     "better your pretext lands. Tools: theHarvester, Maltego, recon-ng."),

    ("vishing", "Vishing", "Social Engineering",
     "Voice phishing - social engineering over the phone. More effective than email phishing because voice carries "
     "tone, urgency, and authority that text can't. Targets IT helpdesks especially - a confident caller claiming "
     "to be a frustrated exec can sometimes bypass normal verification."),

    ("baiting", "Baiting", "Social Engineering",
     "Leaving infected physical media (USB drives, CDs) where the target will find and plug in. The classic "
     "experiment: dropping branded USBs in a target's parking lot - 50%+ get plugged in. Defended by USB lockdown "
     "policy and 'kill switches' that block unknown devices."),
]


# Build lookup by id
CODEX_BY_ID = {entry[0]: entry for entry in CODEX}


def codex_terms() -> list[tuple[str, str, str, str]]:
    return list(CODEX)


def get_term(term_id: str):
    return CODEX_BY_ID.get(term_id)
