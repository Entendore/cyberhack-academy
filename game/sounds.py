"""Sound manager - generates simple chiptune-style effects via Qt Multimedia.

Falls back to no-op if Qt Multimedia is unavailable, so the game still runs
on minimal PySide6 installs.
"""

import struct
import math
import random
import tempfile
import os
from PySide6.QtCore import QObject, QUrl

try:
    from PySide6.QtMultimedia import QSoundEffect
    _HAS_AUDIO = True
except Exception:
    _HAS_AUDIO = False


# ----------------------------------------------------------------------
# WAV generation helpers
# ----------------------------------------------------------------------
def _make_wav_bytes(samples: list[float], sample_rate: int = 22050) -> bytes:
    """Build a WAV file in memory from a list of float samples in [-1, 1]."""
    n = len(samples)
    data = bytearray()
    for s in samples:
        s = max(-1.0, min(1.0, s))
        v = int(s * 32767)
        data += struct.pack("<h", v)
    header = struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF",
        36 + n * 2,
        b"WAVE",
        b"fmt ",
        16,           # PCM chunk size
        1,            # PCM format
        1,            # mono
        sample_rate,
        sample_rate * 2,
        2,            # block align
        16,           # bits per sample
        b"data",
        n * 2,
    )
    return header + bytes(data)


def _gen_tone(freq: float, duration_s: float, decay: float = 6.0,
              sample_rate: int = 22050, volume: float = 0.4) -> bytes:
    n = int(duration_s * sample_rate)
    samples = []
    for i in range(n):
        t = i / sample_rate
        env = math.exp(-decay * t)
        samples.append(volume * env * math.sin(2 * math.pi * freq * t))
    return _make_wav_bytes(samples, sample_rate)


def _gen_chirp(f0: float, f1: float, duration_s: float,
               sample_rate: int = 22050, volume: float = 0.35) -> bytes:
    n = int(duration_s * sample_rate)
    samples = []
    for i in range(n):
        t = i / sample_rate
        frac = t / duration_s
        f = f0 + (f1 - f0) * frac
        env = math.exp(-3.0 * t)
        samples.append(volume * env * math.sin(2 * math.pi * f * t))
    return _make_wav_bytes(samples, sample_rate)


def _gen_noise(duration_s: float, sample_rate: int = 22050,
               volume: float = 0.2) -> bytes:
    n = int(duration_s * sample_rate)
    samples = [volume * (random.random() * 2 - 1) for _ in range(n)]
    return _make_wav_bytes(samples, sample_rate)


# ----------------------------------------------------------------------
class SoundManager(QObject):
    """Pre-generates small WAV effects and plays them via QSoundEffect.

    If Qt Multimedia is missing, all play_* methods silently no-op.
    """

    def __init__(self, parent=None, enabled: bool = True):
        super().__init__(parent)
        self.enabled = enabled and _HAS_AUDIO
        self._effects: dict[str, QSoundEffect] = {}
        self._temp_files: list[str] = []
        if self.enabled:
            try:
                self._build_effects()
            except Exception:
                self.enabled = False

    def _build_effects(self):
        snippets = {
            "type":   _gen_tone(2200, 0.018, decay=80, volume=0.10),
            "enter":  _gen_tone(440, 0.06, decay=20, volume=0.20),
            "ok":     _gen_chirp(523, 1046, 0.18, volume=0.30),
            "flag":   _gen_chirp(440, 1760, 0.45, volume=0.30),
            "error":  _gen_tone(180, 0.18, decay=8, volume=0.30),
            "click":  _gen_tone(880, 0.03, decay=40, volume=0.18),
            "hint":   _gen_tone(660, 0.10, decay=12, volume=0.22),
            "boot":   _gen_chirp(220, 880, 0.55, volume=0.28),
        }
        tmp_dir = tempfile.mkdtemp(prefix="cyberhack_snd_")
        for name, wav_bytes in snippets.items():
            path = os.path.join(tmp_dir, f"{name}.wav")
            with open(path, "wb") as f:
                f.write(wav_bytes)
            self._temp_files.append(path)
            eff = QSoundEffect(self)
            eff.setSource(QUrl.fromLocalFile(path))
            eff.setVolume(0.6)
            self._effects[name] = eff

    # ------------------------------------------------------------------
    def play(self, name: str):
        if not self.enabled:
            return
        eff = self._effects.get(name)
        if eff is not None:
            try:
                eff.stop()
                eff.play()
            except Exception:
                pass

    def type(self):    self.play("type")
    def enter(self):   self.play("enter")
    def ok(self):      self.play("ok")
    def flag(self):    self.play("flag")
    def error(self):   self.play("error")
    def click(self):   self.play("click")
    def hint(self):    self.play("hint")
    def boot(self):    self.play("boot")

    def set_enabled(self, enabled: bool):
        self.enabled = enabled and _HAS_AUDIO
