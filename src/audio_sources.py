"""Platform boundary. Sources deliver fixed 16 kHz mono PCM16 frames to Core.

Application/process selection is reserved, never silently treated as system audio.
"""
from dataclasses import dataclass
from enum import Enum
import sys
from typing import Protocol


class PermissionStatus(str, Enum):
    GRANTED = "granted"
    DENIED = "denied"
    NOT_REQUESTED = "not_requested"
    RESTRICTED = "restricted"
    UNSUPPORTED = "unsupported"


@dataclass(frozen=True)
class SourceCapability:
    kind: str
    available: bool
    permission: PermissionStatus
    reason: str = ""
    application_selection: bool = False


class AudioSource(Protocol):
    def start(self): ...
    def close(self): ...


class MacSystemAudioSource:
    """Future ScreenCaptureKit / Core Audio Tap adapter; no capture implemented."""
    def __init__(self, config, feed, fault):
        raise RuntimeError("macOS 系统音频尚未实现，需原生采集后端及权限验证。")


def capability(kind, platform=None):
    platform = platform or sys.platform
    if kind == "microphone":
        return SourceCapability(kind, True, PermissionStatus.NOT_REQUESTED)
    if kind == "system" and platform == "win32":
        import importlib.util
        available = importlib.util.find_spec("pyaudiowpatch") is not None
        return SourceCapability(kind, available, PermissionStatus.NOT_REQUESTED,
                                "" if available else "系统音频组件未安装。")
    return SourceCapability(kind, False, PermissionStatus.UNSUPPORTED,
                            "macOS backend architecture prepared but not validated."
                            if platform == "darwin" else "此音频来源尚未支持。")


def create_source(config, feed, fault):
    if config.audio_source == "microphone":
        from realtime_audio import Microphone
        return Microphone(config, feed, fault)
    if config.audio_source == "system" and sys.platform == "win32":
        from windows_system_audio import WindowsSystemAudioSource
        return WindowsSystemAudioSource(config, feed, fault)
    if config.audio_source == "system" and sys.platform == "darwin":
        return MacSystemAudioSource(config, feed, fault)
    raise ValueError("此音频来源尚未支持。")


class PCMConverter:
    """Stateful PyAV resampling, downmix then fixed framing; bounded residual."""
    def __init__(self, rate, channels, frame_samples=480):
        import av
        if rate <= 0 or channels <= 0:
            raise ValueError("Invalid capture format")
        self.rate, self.channels = int(rate), int(channels)
        self.frame_bytes = frame_samples * 2
        self.resampler = av.AudioResampler(format="s16", layout="mono", rate=16000)
        self.pending = bytearray()

    def convert(self, pcm):
        import av
        import numpy as np
        if not pcm:
            return []
        if len(pcm) % (2 * self.channels):
            raise ValueError("Incomplete PCM sample")
        samples = np.frombuffer(pcm, dtype="<i2").reshape(-1, self.channels)
        mono = np.rint(samples.astype(np.float32).mean(axis=1)).astype(np.int16)
        frame = av.AudioFrame.from_ndarray(mono.reshape(1, -1), format="s16", layout="mono")
        frame.sample_rate = self.rate
        for converted in self.resampler.resample(frame):
            self.pending.extend(converted.to_ndarray().tobytes())
        frames = []
        while len(self.pending) >= self.frame_bytes:
            frames.append(bytes(self.pending[:self.frame_bytes]))
            del self.pending[:self.frame_bytes]
        return frames
