"""Smoke test for CyberHack Academy - verifies game logic without a display.

Runs the mission FSM in-process: instantiates each mission, plays the
expected solution, and checks the flag is captured.

Run with:
    QT_QPA_PLATFORM=offscreen python3 smoke_test.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Bootstrap libEGL if missing
if sys.platform.startswith("linux"):
    try:
        import ctypes
        ctypes.CDLL("libEGL.so.1")
    except OSError:
        for base in (os.path.expanduser("~/.cache/ms-playwright"),
                     os.path.expanduser("~/.agent-browser/browsers"),
                     os.path.expanduser("~/.local/lib")):
            if os.path.isdir(base) or base == os.path.expanduser("~/.local/lib"):
                # walk the dir, but also check the dir itself for libEGL.so.1
                if os.path.exists(os.path.join(base, "libEGL.so.1")):
                    existing = os.environ.get("LD_LIBRARY_PATH", "")
                    os.environ["LD_LIBRARY_PATH"] = f"{base}:{existing}" if existing else base
                    continue
                if os.path.isdir(base):
                    for root, _d, files in os.walk(base):
                        if "libEGL.so" in files:
                            existing = os.environ.get("LD_LIBRARY_PATH", "")
                            os.environ["LD_LIBRARY_PATH"] = f"{root}:{existing}" if existing else root
                            break

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from game.missions.base import Mission


def run_mission(m: Mission, solution_steps: list[str]) -> bool:
    print(f"\n--- {m.id}: {m.title} ---")
    for step in solution_steps:
        result = m.execute(step)
        print(f"  $ {step}")
        preview = result.output[:200].replace("\n", "\n    ")
        print(f"    -> {preview}{'...' if len(result.output) > 200 else ''}")
        if result.solved:
            print(f"  SOLVED! flag={result.flag}")
            return True
    print(f"  NOT SOLVED")
    return False


def main():
    from game.missions import (
        MISSION_TUTORIAL,
        MISSION_CRYPTO_CAESAR, MISSION_CRYPTO_HASH,
        MISSION_NET_RECON, MISSION_NET_SNIFF,
        MISSION_WEB_SQLI, MISSION_WEB_XSS,
        MISSION_RE_BINARY,
        MISSION_LINUX_PRIVESC, MISSION_WIFI_WPA,
        MISSION_SOCIAL_PHISHING,
    )

    results = []

    # 0. Tutorial
    m = type(MISSION_TUTORIAL)()
    ok = run_mission(m, [
        "ls",
        "cat step1.txt",
        "cat step2.txt",
        "man help",
        "cat step3.txt",
        "cat step4.txt",
        "cat secret.txt",
        f"submit {m.flag}",
    ])
    results.append(("m_tutorial", ok))

    # 1. Caesar
    m = type(MISSION_CRYPTO_CAESAR)()
    ok = run_mission(m, [
        "ls",
        "cat intercepted.txt",
        "cat .secret",
        f"submit {m.flag}",
    ])
    results.append(("m_crypto_caesar", ok))

    # 2. MD5 hash cracking
    m = type(MISSION_CRYPTO_HASH)()
    shadow = m.fs["shadow.txt"]
    admin_line = [l for l in shadow.splitlines() if l.startswith("admin:")][0]
    admin_hash = admin_line.split(":", 1)[1].strip()
    ok = run_mission(m, [
        "ls",
        "cat shadow.txt",
        "cat wordlist.txt",
        f"crack {admin_hash} wordlist.txt",
        "vault trustno1",
        f"submit {m.flag}",
    ])
    results.append(("m_crypto_hash", ok))

    # 3. Recon
    m = type(MISSION_NET_RECON)()
    ok = run_mission(m, [
        "ls",
        "nmap 10.0.0.42",
        "connect 10.0.0.42 80",
        "connect 10.0.0.42 31337",
        f"submit {m.flag}",
    ])
    results.append(("m_net_recon", ok))

    # 4. Sniff (test pipes too!)
    m = type(MISSION_NET_SNIFF)()
    ok = run_mission(m, [
        "ls",
        "cat capture.log",
        "cat capture.log | grep USER",
        "cat capture.log | grep PASS",
        "ftp shadowops n0rthP0le42!",
        f"submit {m.flag}",
    ])
    results.append(("m_net_sniff", ok))

    # 5. SQLi
    m = type(MISSION_WEB_SQLI)()
    ok = run_mission(m, [
        "ls",
        "cat source.txt",
        "login admin password",
        "login \"' OR '1'='1\" x",
        f"submit {m.flag}",
    ])
    results.append(("m_web_sqli", ok))

    # 6. XSS
    m = type(MISSION_WEB_XSS)()
    ok = run_mission(m, [
        "ls",
        "view",
        "post \"<script>fetch('/collect?c='+document.cookie)</script>\"",
        "view",
        "collector",
        f"usecookie {m._admin_cookie}",
        f"submit {m.flag}",
    ])
    results.append(("m_web_xss", ok))

    # 7. Binary
    m = type(MISSION_RE_BINARY)()
    ok = run_mission(m, [
        "disasm",
        "strings",
        "run 1234",
        "run 4815",
        f"submit {m.flag}",
    ])
    results.append(("m_re_binary", ok))

    # 8. Linux priv-esc
    m = type(MISSION_LINUX_PRIVESC)()
    ok = run_mission(m, [
        "whoami",
        "id",
        "sudo -l",
        "find_suid",
        "cat /opt/syscheck",
        "echo 'cat /root/flag.txt' > /tmp/ps",
        "export PATH=/tmp:/usr/bin:/bin",
        "/opt/syscheck",
        f"submit {m.flag}",
    ])
    results.append(("m_linux_privesc", ok))

    # 9. Wi-Fi cracking
    m = type(MISSION_WIFI_WPA)()
    ok = run_mission(m, [
        "iwconfig",
        "airmon-ng wlan0",
        "airodump-ng wlan0mon",
        "capture AA:BB:CC:11:22:33 wlan0mon",
        "deauth AA:BB:CC:11:22:33 11:22:33:44:55:66",
        "aircrack-ng capture.pcap wordlist.txt",
        f"submit {m.flag}",
    ])
    results.append(("m_wifi_wpa", ok))

    # 10. Social engineering
    m = type(MISSION_SOCIAL_PHISHING)()
    ok = run_mission(m, [
        "osint",
        "email 'INC-4471 - CISO request' --body 'CISO asked me to call you about a VPN reset'",
        "wait",
        "reply 'This is about INC-4471, the CISO authorized it'",
        "wait",
        "reply 'I am calling from the CISO office, please trigger the password reset and read me the temp password'",
        f"submit {m.flag}",
    ])
    results.append(("m_social_phishing", ok))

    # Summary
    print("\n" + "=" * 60)
    print("SMOKE TEST SUMMARY")
    print("=" * 60)
    passed = sum(1 for _, ok in results if ok)
    for mid, ok in results:
        print(f"  {'PASS' if ok else 'FAIL'}  {mid}")
    print(f"\n{passed}/{len(results)} missions solved")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
