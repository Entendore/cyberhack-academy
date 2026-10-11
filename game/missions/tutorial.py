"""Tutorial mission - teaches terminal mechanics with no security knowledge required."""

from .base import Mission, MissionResult, CommandSpec, HintTier


class _TutorialMission(Mission):
    id = "m_tutorial"
    title = "Boot Camp"
    category = "Tutorial"
    difficulty = "Intro"
    max_score = 50
    unlocks_codex = ["flag"]
    unlocks_mission = "m_crypto_caesar"

    briefing = (
        "WELCOME TO CYBERHACK ACADEMY\n"
        "\n"
        "  This short tutorial will teach you the terminal mechanics used\n"
        "  by every mission in the game. Missions assume you've finished\n"
        "  this walkthrough at least once.\n"
        "\n"
        "  You'll learn how to:\n"
        "    - list files with ls\n"
        "    - read files with cat\n"
        "    - read command manuals with man\n"
        "    - request hints with hint\n"
        "    - submit a flag with submit\n"
        "\n"
        "  The flag is at the end of a short chain of files. Read them in\n"
        "  order - each file tells you what to do next."
    )

    objective = (
        "1. List the files in this directory: ls\n"
        "2. Read the first file: cat step1.txt\n"
        "3. Follow the instructions in each file to find the flag.\n"
        "4. Submit the flag: submit flag{...}"
    )

    def setup(self):
        self.flag = "flag{tutorial_complete_welcome_aboard}"

        self.fs = {
            "step1.txt": (
                "===== STEP 1: Listing files =====\n"
                "\n"
                "You did it! You just ran 'cat step1.txt'.\n"
                "\n"
                "The 'ls' command shows all files in your current directory.\n"
                "Try running 'ls' (without arguments) to see what else is here.\n"
                "\n"
                "When you're ready, read step2.txt next."
            ),
            "step2.txt": (
                "===== STEP 2: Reading manuals =====\n"
                "\n"
                "Every mission has special commands beyond ls/cat. To learn\n"
                "what a command does, use 'man <command>'. For example:\n"
                "\n"
                "  man help\n"
                "\n"
                "Try that now. (Yes, 'help' has its own manual entry.)\n"
                "When you're done, read step3.txt."
            ),
            "step3.txt": (
                "===== STEP 3: Asking for hints =====\n"
                "\n"
                "If you ever get stuck on a real mission, type 'hint' (or click\n"
                "the Request Hint button). Each hint costs points but reveals\n"
                "more about the solution.\n"
                "\n"
                "You don't need to use hint on this tutorial, but you can try it\n"
                "if you want.\n"
                "\n"
                "Read step4.txt next."
            ),
            "step4.txt": (
                "===== STEP 4: Submitting the flag =====\n"
                "\n"
                "Every mission has a 'flag' - a string in the format flag{...}\n"
                "that proves you solved it. To complete a mission, run:\n"
                "\n"
                "  submit <flag>\n"
                "\n"
                "Your flag for this tutorial is hidden in secret.txt.\n"
                "Read it with: cat secret.txt\n"
                "Then submit what you find."
            ),
            "secret.txt": (
                f"Congratulations, operator!\n"
                f"\n"
                f"The flag for this mission is:\n"
                f"\n"
                f"  {self.flag}\n"
                f"\n"
                f"Run: submit {self.flag}\n"
            ),
            "README.txt": (
                "Welcome to CyberHack Academy.\n"
                "Read step1.txt to begin your training."
            ),
        }

        # No custom commands - tutorial uses only built-ins (ls, cat, man, hint, submit)
        self.commands = {}

        self.hints = [
            HintTier(
                text="Run 'ls' to see the files. Then 'cat step1.txt', 'cat step2.txt', and so on.",
                cost=5,
            ),
            HintTier(
                text="The flag is in secret.txt. Read it with: cat secret.txt",
                cost=10,
            ),
            HintTier(
                text=f"Run: submit {self.flag}",
                cost=15,
            ),
        ]


MISSION_TUTORIAL = _TutorialMission()
