"""Realtime settings are intentionally separate from file-ASR configuration."""

from dataclasses import dataclass


@dataclass(frozen=True)
class RealtimeConfig:
    model: str = "small"  # Reuse the local HF cache; never download implicitly.
    device: str = "auto"
    sample_rate: int = 16000
    frame_ms: int = 30
    vad_mode: int = 2
    start_frames: int = 3
    pre_roll_ms: int = 210
    end_silence_ms: int = 600
    partial_interval_ms: int = 1000
    max_utterance_ms: int = 8000
    audio_queue_frames: int = 100
    final_queue_size: int = 4
    event_queue_size: int = 128
    microphone_device: int | str | None = None
    startup_timeout: float = 60.0
    shutdown_timeout: float = 30.0
    compute_type: str | None = None
    allow_cpu_fallback: bool = False
    audio_source: str = "microphone"

    def __post_init__(self):
        if self.audio_source not in ("microphone", "system"):
            raise ValueError("Unsupported audio source")
        if self.sample_rate != 16000 or self.frame_ms not in (10, 20, 30):
            raise ValueError("Realtime supports 16 kHz mono PCM16 and 10/20/30 ms frames")
        if self.device not in ("auto", "cpu", "cuda") or self.vad_mode not in range(4):
            raise ValueError("Invalid device or VAD mode")
        if min(self.start_frames, self.audio_queue_frames, self.final_queue_size,
               self.event_queue_size, self.startup_timeout, self.shutdown_timeout) <= 0:
            raise ValueError("Queue sizes, start frames and timeouts must be positive")
        if self.pre_roll_ms < self.start_frames * self.frame_ms:
            raise ValueError("Pre-roll must hold the speech onset frames")
        if not (self.frame_ms <= self.end_silence_ms < self.max_utterance_ms
                and self.frame_ms <= self.partial_interval_ms < self.max_utterance_ms
                and self.pre_roll_ms < self.max_utterance_ms):
            raise ValueError("Invalid endpoint/partial/chunk durations")

    @property
    def frame_samples(self):
        return self.sample_rate * self.frame_ms // 1000
