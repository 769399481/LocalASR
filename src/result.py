"""Local ASR data shared by transcription and export callers."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Segment:
    start: float
    end: float
    text: str


@dataclass(frozen=True)
class TranscriptionResult:
    text: str
    language: str
    duration: float
    segments: tuple[Segment, ...]
