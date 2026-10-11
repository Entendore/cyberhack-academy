"""Cryptography missions: Caesar cipher + MD5 hash cracking."""

from .base import Mission, MissionResult, CommandSpec, HintTier


# ======================================================================
# Mission 1 - Caesar Cipher (Easy intro)
# ======================================================================
class _CaesarMission(Mission):
    id = "m_crypto_caesar"
    title = "The Caesar's Whisper"
    category = "Cryptography"
    difficulty = "Easy"
    max_score = 100
    unlocks_codex = ["caesar_cipher", "frequency_analysis", "flag"]
    unlocks_mission = "m_crypto_hash"

    briefing = (
        "INCOMING TRANSMISSION - source: anonymous relay node\n"
        "\n"
        "  Operator, we intercepted a hand-written note from a low-level courier.\n"
        "  The note is gibberish at first glance - but our analysts believe it is\n"
        "  a Caesar cipher, the oldest trick in the book. Each letter has been\n"
        "  shifted forward by a fixed number of positions.\n"
        "\n"
        "  Decrypt the message to reveal a passphrase, then locate the hidden\n"
        "  flag file in the courier's home directory and submit it.\n"
        "\n"
        "  Files have been synced to your local working directory. Use 'ls' to\n"
        "  see what's there."
    )

    objective = (
        "1. Read the intercepted message: cat intercepted.txt\n"
        "2. Try decrypting it with different shifts using: caesar <text> <shift>\n"
        "3. Find the hidden flag file and submit it: submit <flag>"
    )

    def setup(self):
        # The encrypted message + flag
        self.flag = "flag{caesar_lives_in_rome}"

        # Build Caesar ciphertext (shift 3 forward) of the hint message
        plaintext_hint = (
            "PASSPHRASE: the eagle flies at midnight. "
            "Look in the file named .secret for the flag."
        )
        ciphertext = self._caesar_encrypt(plaintext_hint, 3)

        self.fs = {
            "intercepted.txt": (
                "----- INTERCEPTED NOTE -----\n"
                f"{ciphertext}\n"
                "----------------------------\n"
            ),
            ".secret": f"Congratulations. The flag is: {self.flag}\n",
            "README.txt": (
                "You are in /home/courier.\n"
                "Type 'help' to see available commands.\n"
                "Tip: 'ls' will not show hidden files (those starting with a dot).\n"
            ),
        }

        # Custom command: caesar <text> <shift>
        def _caesar_handler(args, mission):
            if len(args) < 2:
                return MissionResult(
                    output="usage: caesar <text> <shift>\nexample: caesar KHOOR 3",
                    error=True, sound="error",
                )
            try:
                shift = int(args[-1])
                text = " ".join(args[:-1])
            except ValueError:
                return MissionResult(
                    output="shift must be an integer. example: caesar KHOOR 3",
                    error=True, sound="error",
                )
            result = _CaesarMission._caesar_decrypt(text, shift)
            return MissionResult(output=result, sound="click")

        self.commands = {
            "caesar": CommandSpec(
                name="caesar",
                usage="caesar <text> <shift>",
                description="Decrypt text using a Caesar cipher with the given shift (0-25).",
                handler=_caesar_handler,
            ),
        }

        self.hints = [
            HintTier(
                text="Caesar cipher with shift N replaces each letter with the letter N positions later in the alphabet. "
                     "To decrypt, shift BACKWARD by N. Try shift=3 first - it's the classic Roman value.",
                cost=10,
            ),
            HintTier(
                text="The note says: 'Look in the file named .secret for the flag.' "
                     "Hidden files (starting with .) are not shown by 'ls' but 'cat .secret' works.",
                cost=15,
            ),
            HintTier(
                text=f"The decrypted message reveals a passphrase, but the flag itself is in the .secret file. "
                     f"Run: cat .secret",
                cost=20,
            ),
        ]

    # ------------------------------------------------------------------
    @staticmethod
    def _caesar_encrypt(text: str, shift: int) -> str:
        out = []
        for ch in text:
            if ch.isalpha():
                base = ord('A') if ch.isupper() else ord('a')
                out.append(chr((ord(ch) - base + shift) % 26 + base))
            else:
                out.append(ch)
        return "".join(out)

    @staticmethod
    def _caesar_decrypt(text: str, shift: int) -> str:
        return _CaesarMission._caesar_encrypt(text, -shift)


MISSION_CRYPTO_CAESAR = _CaesarMission()


# ======================================================================
# Mission 2 - MD5 Hash Cracking (Medium)
# ======================================================================
class _HashMission(Mission):
    id = "m_crypto_hash"
    title = "Hash on the Wire"
    category = "Cryptography"
    difficulty = "Medium"
    max_score = 150
    unlocks_codex = ["hash_function", "md5", "rainbow_table", "salt", "wordlist"]
    unlocks_mission = "m_net_recon"

    briefing = (
        "INCOMING TRANSMISSION - source: guild handler\n"
        "\n"
        "  We pulled a credentials file off a compromised FTP server. The\n"
        "  passwords are MD5-hashed. Your job: reverse them.\n"
        "\n"
        "  You have:\n"
        "    - shadow.txt      the leaked hash dump\n"
        "    - wordlist.txt    a small dictionary of common passwords\n"
        "\n"
        "  Use the 'crack' command to brute-force each hash against the wordlist.\n"
        "  The admin's password unlocks a vault message containing the flag."
    )

    objective = (
        "1. Inspect the files: cat shadow.txt  and  cat wordlist.txt\n"
        "2. Crack a hash:      crack <hash> wordlist.txt\n"
        "3. Find the admin entry, crack it, then run: vault <password>\n"
        "4. Submit the revealed flag."
    )

    def setup(self):
        import hashlib

        # Pre-compute MD5s for a small wordlist
        words = [
            "123456", "password", "qwerty", "letmein", "admin",
            "welcome", "monkey", "dragon", "sunshine", "master",
            "superman", "trustno1", "iloveyou", "shadow", "freedom",
        ]
        hashes = {hashlib.md5(w.encode()).hexdigest(): w for w in words}

        # Admin password - the one that unlocks the flag
        admin_pw = "trustno1"
        admin_hash = hashlib.md5(admin_pw.encode()).hexdigest()

        # The flag
        self.flag = "flag{rainbow_tables_still_work}"

        self.fs = {
            "shadow.txt": (
                "# /etc/shadow-style dump (MD5, unsalted)\n"
                f"alice:{hashes[hashlib.md5('123456'.encode()).hexdigest()]}\n"
                f"bob:{hashes[hashlib.md5('password'.encode()).hexdigest()]}\n"
                f"carol:{hashes[hashlib.md5('qwerty'.encode()).hexdigest()]}\n"
                f"dave:{hashes[hashlib.md5('monkey'.encode()).hexdigest()]}\n"
                f"admin:{admin_hash}\n"
            ),
            "wordlist.txt": "\n".join(words) + "\n",
            "vault.lock": "<encrypted - requires vault <password> to open>",
            "README.txt": (
                "The vault.lock file is sealed. Only the admin password opens it.\n"
                "Identify the admin entry in shadow.txt, crack it, then run: vault <password>\n"
            ),
        }

        # crack <hash> <wordlist_file>
        def _crack_handler(args, mission):
            if len(args) < 2:
                return MissionResult(
                    output="usage: crack <hash> <wordlist_file>",
                    error=True, sound="error",
                )
            target_hash = args[0]
            wl_path = args[1]
            wl_text = mission.fs.get(wl_path)
            if wl_text is None:
                return MissionResult(
                    output=f"crack: cannot open wordlist '{wl_path}'",
                    error=True, sound="error",
                )
            import hashlib
            candidates = [w.strip() for w in wl_text.splitlines() if w.strip()]
            for w in candidates:
                if hashlib.md5(w.encode()).hexdigest() == target_hash:
                    return MissionResult(
                        output=(
                            f"[*] hashing wordlist...\n"
                            f"[+] MATCH FOUND\n"
                            f"    hash:   {target_hash}\n"
                            f"    plain:  {w}\n"
                        ),
                        sound="ok",
                    )
            return MissionResult(
                output=(
                    f"[*] hashing wordlist...\n"
                    f"[-] no match found in '{wl_path}' for hash {target_hash}\n"
                ),
                error=True, sound="error",
            )

        # vault <password>
        def _vault_handler(args, mission):
            if not args:
                return MissionResult(
                    output="usage: vault <password>",
                    error=True, sound="error",
                )
            pw = " ".join(args)
            if pw == admin_pw:
                return MissionResult(
                    output=(
                        "[*] decrypting vault.lock...\n"
                        "[+] ACCESS GRANTED\n"
                        "\n"
                        "---- vault message ----\n"
                        f"Welcome, admin. Your reward:\n"
                        f"{mission.flag}\n"
                        "------------------------\n"
                    ),
                    sound="ok",
                )
            return MissionResult(
                output=f"[*] decrypting vault.lock...\n[-] ACCESS DENIED - wrong password.",
                error=True, sound="error",
            )

        self.commands = {
            "crack": CommandSpec(
                name="crack",
                usage="crack <hash> <wordlist_file>",
                description="Brute-force an MD5 hash against a wordlist file.",
                handler=_crack_handler,
            ),
            "vault": CommandSpec(
                name="vault",
                usage="vault <password>",
                description="Attempt to open vault.lock with the given password.",
                handler=_vault_handler,
            ),
        }

        self.hints = [
            HintTier(
                text="The 'crack' command takes a hash and a wordlist file. "
                     "It hashes each word in the list and compares. Try: crack <admin_hash> wordlist.txt",
                cost=15,
            ),
            HintTier(
                text="To get the admin's hash, 'cat shadow.txt' and find the line starting with 'admin:'. "
                     "The hex string after the colon is the hash.",
                cost=20,
            ),
            HintTier(
                text=f"Try common passwords - 'trustno1' is in the wordlist. "
                     f"Run: vault trustno1",
                cost=30,
            ),
        ]


MISSION_CRYPTO_HASH = _HashMission()
