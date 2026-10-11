"""ASCII art banners and boot animation utilities."""

APP_BANNER = r"""
  ____      _    ____   _    ____ _  ______    _    ____ _____
 / ___|    / \  |  _ \ / \  / ___| |/ / ___|  / \  / ___| ____|
| |       / _ \ | |_) / _ \| |   | ' /\___ \ / _ \| |   |  _|
| |___   / ___ \|  _/ ___ \ |___| . \ ___) / ___ \ |___| |___
 \____| /_/   \_\_| /_/   \_\____|_|\_\____/_/   \_\____|_____|
"""


BOOT_LINES = [
    "[ OK ] Initializing cyberhack kernel v1.0.0",
    "[ OK ] Mounting /home/operator",
    "[ OK ] Loading terminal emulator... ok",
    "[ OK ] Loading mission modules:",
    "       - m_tutorial                    [ready]",
    "       - m_crypto_caesar               [ready]",
    "       - m_crypto_hash                 [ready]",
    "       - m_net_recon                   [ready]",
    "       - m_net_sniff                   [ready]",
    "       - m_web_sqli                    [ready]",
    "       - m_web_xss                     [ready]",
    "       - m_re_binary                   [ready]",
    "       - m_linux_privesc               [ready]",
    "       - m_wifi_wpa                    [ready]",
    "       - m_social_phishing             [ready]",
    "[ OK ] Loading codex (40+ terms)        ok",
    "[ OK ] Loading achievements (16 badges) ok",
    "[ OK ] Establishing secure channel      ok",
    "[ OK ] Welcome, operator.",
    "",
    "Type 'help' in the terminal at any time.",
    "Select a mission from the left panel to begin.",
    "",
]


def boot_lines() -> list[str]:
    return list(BOOT_LINES)


def app_banner() -> str:
    return APP_BANNER.strip("\n")
