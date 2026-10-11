"""Reverse engineering mission: read pseudo-assembly to find the flag."""

from .base import Mission, MissionResult, CommandSpec, HintTier


# ======================================================================
# Mission 7 - Binary Secrets (Hard)
# ======================================================================
class _BinaryMission(Mission):
    id = "m_re_binary"
    title = "Binary Secrets"
    category = "Reverse Engineering"
    difficulty = "Hard"
    max_score = 200
    unlocks_codex = ["disassembly", "control_flow", "buffer_overflow"]
    unlocks_mission = None  # last mission

    briefing = (
        "INCOMING TRANSMISSION - source: guild handler\n"
        "\n"
        "  We recovered a stripped binary from a compromised embedded\n"
        "  device. It's a small CLI that asks for a 4-digit PIN, then\n"
        "  either prints 'ACCESS DENIED' or reveals a flag.\n"
        "\n"
        "  You don't have the source - but you have its disassembly.\n"
        "  Read the assembly, understand what PIN it expects, then run\n"
        "  the binary with that PIN to retrieve the flag.\n"
        "\n"
        "  Tools:\n"
        "    disasm         show the binary's disassembly\n"
        "    run <pin>      run the binary with the given PIN\n"
        "    strings        show printable strings extracted from the binary\n"
    )

    objective = (
        "1. Read the disassembly: disasm\n"
        "2. Find the comparison that validates the PIN (look for 'cmp').\n"
        "3. Reverse the math - the PIN is derived from a few constants.\n"
        "4. Run: run <pin>\n"
        "5. Submit the flag the binary prints."
    )

    def setup(self):
        # The PIN is 4815 - derived from constants in the disassembly.
        # We make it discoverable: the disasm shows MOV r1, 0x12 (18), MOV r2, 0x05 (5),
        # then MUL r3, r1, r2 (90), then MOV r4, 0x1e (30), ADD r5, r3, r4 (120),
        # then the loop multiplies by an index. The final cmp is against 0x12C5 (4805).
        # Actually let's keep it simpler: PIN == 0x12C5 == 4805, but we'll hint at the math.
        self._correct_pin = 4815
        self.flag = "flag{reverse_engineering_is_just_reading}"

        self.fs = {
            "README.txt": (
                "Binary: ./validate_pin (stripped, x86-64-ish pseudo-asm)\n"
                "Behavior: prompts for a 4-digit PIN. Prints the flag if correct,\n"
                "or 'ACCESS DENIED' if wrong.\n"
                "Read the disassembly with 'disasm', find the CMP, reverse the math.\n"
            ),
        }

        # Pseudo-assembly listing. The key comparison is at the end.
        disasm_text = """; ===== validate_pin - disassembly (pseudo-x86) =====
; entry: main
main:
    push    rbp
    mov     rbp, rsp
    sub     rsp, 0x20
    ; print prompt
    lea     rdi, [rel prompt]
    call    puts
    ; read PIN into local var [rbp-0x10]
    lea     rsi, [rbp-0x10]
    lea     rdi, [rel fmt_d]
    call    scanf
    ; compute expected PIN
    mov     r1, 0x05              ; r1 = 5
    mov     r2, 0x09              ; r2 = 9
    mul     r3, r1, r2            ; r3 = 5 * 9 = 45
    mov     r4, 0x6b              ; r4 = 107
    mul     r5, r3, r4            ; r5 = 45 * 107 = 4815
    ; compare input (rbp-0x10) with r5
    mov     rax, [rbp-0x10]
    cmp     rax, r5
    jne     .deny
    ; correct PIN -> print flag
    lea     rdi, [rel flag_str]
    call    puts
    jmp     .exit
.deny:
    lea     rdi, [rel denied_str]
    call    puts
.exit:
    mov     rax, 0
    leave
    ret

; ---- data section ----
prompt:       db "Enter PIN: ", 0
fmt_d:        db "%d", 0
denied_str:   db "ACCESS DENIED", 0
flag_str:     db "Flag will be printed here when run with correct PIN.", 0
"""

        # Override fs[disasm] - we'll serve it through the disasm command instead.
        self._disasm_text = disasm_text

        def _disasm_handler(args, mission):
            return MissionResult(output=mission._disasm_text, sound="click")

        def _strings_handler(args, mission):
            return MissionResult(
                output=(
                    "---- strings(./validate_pin) ----\n"
                    "Enter PIN: \n"
                    "%d\n"
                    "ACCESS DENIED\n"
                    "Flag will be printed here when run with correct PIN.\n"
                    "---------------------------------"
                ),
                sound="click",
            )

        def _run_handler(args, mission):
            if not args:
                return MissionResult(
                    output="usage: run <pin>",
                    error=True, sound="error",
                )
            try:
                pin = int(args[0])
            except ValueError:
                return MissionResult(
                    output=f"[*] running ./validate_pin\n[*] Enter PIN: {args[0]}\n[-] invalid input (not a number)",
                    error=True, sound="error",
                )
            lines = [
                "[*] running ./validate_pin",
                "[*] Enter PIN: " + str(pin),
            ]
            if pin == mission._correct_pin:
                lines.append("")
                lines.append("[+] ACCESS GRANTED")
                lines.append("")
                lines.append("---- flag ----")
                lines.append(mission.flag)
                lines.append("--------------")
                return MissionResult(output="\n".join(lines), sound="ok")
            else:
                lines.append("[-] ACCESS DENIED")
                return MissionResult(output="\n".join(lines), error=True, sound="error")

        self.commands = {
            "disasm": CommandSpec(
                name="disasm",
                usage="disasm",
                description="Print the binary's disassembly listing.",
                handler=_disasm_handler,
            ),
            "strings": CommandSpec(
                name="strings",
                usage="strings",
                description="Extract printable strings from the binary.",
                handler=_strings_handler,
            ),
            "run": CommandSpec(
                name="run",
                usage="run <pin>",
                description="Run the binary with the given PIN.",
                handler=_run_handler,
            ),
        }

        self.hints = [
            HintTier(
                text="The disassembly computes the expected PIN from a few constants, then CMPs the input against it. "
                     "Look for the line 'cmp rax, r5' - r5 holds the expected PIN. Trace back what r5 was set to.",
                cost=25,
            ),
            HintTier(
                text="Working backwards from r5:\n"
                     "  r5 = r3 * r4\n"
                     "  r3 = r1 * r2 = 5 * 9 = 45\n"
                     "  r4 = 0x6b (hex) = 107 (decimal)\n"
                     "  r5 = 45 * 107 = 4815",
                cost=35,
            ),
            HintTier(
                text=f"PIN = 4815. Run: run 4815",
                cost=50,
            ),
        ]

    # Override _victory_text to keep terminal feel
    # (inherits from base)


MISSION_RE_BINARY = _BinaryMission()
