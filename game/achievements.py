"""Achievement badges - unlock by hitting milestones during play."""

from dataclasses import dataclass


@dataclass
class Achievement:
    id: str
    name: str
    description: str
    icon: str   # ASCII glyph shown in the UI


# All achievements in the game. The achievements manager (in save_manager)
# checks these against the player's progress when called.
ACHIEVEMENTS: list[Achievement] = [
    Achievement(
        id="first_blood",
        name="First Blood",
        description="Complete your first mission.",
        icon="*",
    ),
    Achievement(
        id="no_hint_rookie",
        name="Self-Reliant",
        description="Complete a mission without using any hints.",
        icon="!",
    ),
    Achievement(
        id="speedrun",
        name="Speed Demon",
        description="Complete any mission in under 60 seconds.",
        icon=">",
    ),
    Achievement(
        id="perfect_run",
        name="Flawless",
        description="Complete a mission with no hints AND under 60 seconds.",
        icon="+",
    ),
    Achievement(
        id="crypto_master",
        name="Crypto Master",
        description="Complete all Cryptography missions.",
        icon="#",
    ),
    Achievement(
        id="net_master",
        name="Net Walker",
        description="Complete all Network Security missions.",
        icon="@",
    ),
    Achievement(
        id="web_master",
        name="Web Slayer",
        description="Complete all Web Security missions.",
        icon="%",
    ),
    Achievement(
        id="re_master",
        name="Binary Whisperer",
        description="Complete all Reverse Engineering missions.",
        icon="&",
    ),
    Achievement(
        id="linux_master",
        name="Root Juice",
        description="Complete all Linux Privilege Escalation missions.",
        icon="$",
    ),
    Achievement(
        id="wifi_master",
        name="Airwave Surfer",
        description="Complete all Wi-Fi Security missions.",
        icon="~",
    ),
    Achievement(
        id="social_master",
        name="Smooth Talker",
        description="Complete all Social Engineering missions.",
        icon="?",
    ),
    Achievement(
        id="halfway",
        name="Halfway There",
        description="Complete 5 missions.",
        icon="5",
    ),
    Achievement(
        id="completionist",
        name="Completionist",
        description="Complete every mission in the game.",
        icon="8",
    ),
    Achievement(
        id="codex_scholar",
        name="Scholar",
        description="Unlock 15 or more codex entries.",
        icon="?",
    ),
    Achievement(
        id="high_scorer",
        name="High Scorer",
        description="Reach a total score of 1000+.",
        icon="$",
    ),
    Achievement(
        id="tutorial_grad",
        name="Boot Camp Grad",
        description="Complete the tutorial mission.",
        icon="^",
    ),
]


ACHIEVEMENTS_BY_ID = {a.id: a for a in ACHIEVEMENTS}


def get_achievement(aid: str) -> Achievement | None:
    return ACHIEVEMENTS_BY_ID.get(aid)


def check_unlocks(state: dict) -> list[str]:
    """Given the player's state, return the list of newly-unlockable achievement ids.

    `state` should contain:
      - completed: dict[mid -> {score, hints_used, time_s}]
      - codex_unlocked: list[str]
      - total_score: int
      - mission_topics: dict[mid -> category]   (for category mastery)
      - all_mission_ids: list[str]
      - all_category_missions: dict[category -> list[mid]]
    """
    newly: list[str] = []
    completed = state.get("completed", {})
    codex_unlocked = state.get("codex_unlocked", [])
    total_score = state.get("total_score", 0)
    mission_topics = state.get("mission_topics", {})
    all_mission_ids = state.get("all_mission_ids", [])
    cat_missions = state.get("category_missions", {})

    def has(aid: str) -> bool:
        return aid in state.get("achievements", [])

    if not has("first_blood") and len(completed) >= 1:
        newly.append("first_blood")

    if not has("tutorial_grad") and any(
        mid == "m_tutorial" for mid in completed
    ):
        newly.append("tutorial_grad")

    if not has("no_hint_rookie"):
        for rec in completed.values():
            if rec.get("hints_used", 0) == 0:
                newly.append("no_hint_rookie")
                break

    if not has("speedrun"):
        for rec in completed.values():
            if rec.get("time_s", 9999) < 60:
                newly.append("speedrun")
                break

    if not has("perfect_run"):
        for rec in completed.values():
            if rec.get("hints_used", 0) == 0 and rec.get("time_s", 9999) < 60:
                newly.append("perfect_run")
                break

    # Category masters
    cat_to_achievement = {
        "Cryptography":            "crypto_master",
        "Network Security":        "net_master",
        "Web Security":            "web_master",
        "Reverse Engineering":     "re_master",
        "Linux Privilege Escalation": "linux_master",
        "Wi-Fi Security":          "wifi_master",
        "Social Engineering":      "social_master",
    }
    for cat, aid in cat_to_achievement.items():
        if has(aid):
            continue
        mids = cat_missions.get(cat, [])
        if mids and all(mid in completed for mid in mids):
            newly.append(aid)

    if not has("halfway") and len(completed) >= 5:
        newly.append("halfway")

    if not has("completionist") and all_mission_ids and all(
        mid in completed for mid in all_mission_ids
    ):
        newly.append("completionist")

    if not has("codex_scholar") and len(codex_unlocked) >= 15:
        newly.append("codex_scholar")

    if not has("high_scorer") and total_score >= 1000:
        newly.append("high_scorer")

    return newly
