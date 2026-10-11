"""Mission package - all gameplay content lives here."""

from .base import Mission, MissionResult
from .tutorial import MISSION_TUTORIAL
from .crypto import MISSION_CRYPTO_CAESAR, MISSION_CRYPTO_HASH
from .network import MISSION_NET_RECON, MISSION_NET_SNIFF
from .web import MISSION_WEB_SQLI, MISSION_WEB_XSS
from .reverse import MISSION_RE_BINARY
from .linux import MISSION_LINUX_PRIVESC
from .wifi import MISSION_WIFI_WPA
from .social import MISSION_SOCIAL_PHISHING


# Mission order = unlock chain (each mission's unlocks_mission points to the next)
ALL_MISSIONS = [
    MISSION_TUTORIAL,
    MISSION_CRYPTO_CAESAR,
    MISSION_CRYPTO_HASH,
    MISSION_NET_RECON,
    MISSION_NET_SNIFF,
    MISSION_WEB_SQLI,
    MISSION_WEB_XSS,
    MISSION_RE_BINARY,
    MISSION_LINUX_PRIVESC,
    MISSION_WIFI_WPA,
    MISSION_SOCIAL_PHISHING,
]

# Mission topic map (used by stats dashboard + achievements)
MISSION_TOPICS = {m.id: m.category for m in ALL_MISSIONS}
CATEGORY_MISSIONS: dict[str, list[str]] = {}
for m in ALL_MISSIONS:
    CATEGORY_MISSIONS.setdefault(m.category, []).append(m.id)


__all__ = [
    "Mission",
    "MissionResult",
    "ALL_MISSIONS",
    "MISSION_TOPICS",
    "CATEGORY_MISSIONS",
]
