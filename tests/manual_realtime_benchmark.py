"""Paced WAV replay through real VAD + Whisper. NOT a microphone verification.

Input must be a short mono/16-bit/16kHz WAV. No download, playback to speakers,
or microphone recording occurs in this script. --translate adds local CPU translation.
"""

import argparse
from dataclasses import asdict
import json
from pathlib import Path
import statistics
import sys
import threading
import time
import wave

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from realtime import RealtimeSession
from realtime_audio import RealtimeWhisper
from realtime_config import RealtimeConfig
from realtime_translation import RealtimeTranslationConfig, TranslatedRealtimeSession


def run(wav_path, output_path, device, translate=False, passes=1):
    if not 1 <= passes <= 3:
        raise ValueError("Use 1 to 3 replay passes")
    with wave.open(str(wav_path), "rb") as audio:
        if (audio.getnchannels(), audio.getsampwidth(), audio.getframerate()) != (1, 2, 16000):
            raise ValueError("Expected mono PCM16 at 16 kHz")
        duration = audio.getnframes() / audio.getframerate()
        if not 0 < duration <= 60:
            raise ValueError("Use a short WAV up to 60 seconds for this smoke test")
    done = threading.Event()
    events = []
    engines = []
    config = RealtimeConfig(device=device)

    class Replay:
        def __init__(self, cfg, feed, fault):
            self.stop = threading.Event()
            self.feed = feed
            self.thread = threading.Thread(target=self.play, name="wav-replay")

        def start(self):
            self.thread.start()

        def play(self):
            try:
                for _ in range(passes):
                    deadline = time.monotonic()
                    with wave.open(str(wav_path), "rb") as audio:
                        while not self.stop.is_set():
                            pcm = audio.readframes(config.frame_samples)
                            if not pcm:
                                break
                            self.feed(pcm.ljust(config.frame_samples * 2, b"\0"))
                            deadline += config.frame_ms / 1000
                            self.stop.wait(max(0, deadline - time.monotonic()))
                    for _ in range(1000 // config.frame_ms + 1):
                        if self.stop.is_set():
                            break
                        self.feed(b"\0" * config.frame_samples * 2)
                        self.stop.wait(config.frame_ms / 1000)
            finally:
                done.set()

        def close(self):
            self.stop.set()
            self.thread.join()

    def factory():
        engine = RealtimeWhisper(config)
        engines.append(engine)
        return engine

    session = (TranslatedRealtimeSession(events.append, config,
        RealtimeTranslationConfig(enabled=True), engine_factory=factory, source_factory=Replay)
        if translate else RealtimeSession(events.append, config, engine_factory=factory, source_factory=Replay))
    try:
        session.start()
        if not done.wait((duration + 1.1) * passes + 10):
            raise TimeoutError("WAV replay did not finish")
        # stop() flushes and joins the complete pipeline, including native inference.
    finally:
        session.stop()
    finals = [event for event in events if event.kind == "final_transcript"]
    if session.failure_reason or not finals:
        raise RuntimeError(f"No successful final transcript: {session.failure_reason}")
    latencies = [event.endpoint_latency_seconds for event in finals]
    report = {
        "test_type": "Paced WAV replay, real WebRTC VAD + Whisper; NOT live microphone",
        "source_file": str(wav_path.resolve()), "audio_duration_seconds": duration,
        "replay_passes": passes,
        "model": config.model, "device": engines[0].device,
        "compute_type": engines[0].compute_type,
        "partial_count": sum(e.kind == "partial_transcript" for e in events),
        "final_count": len(finals),
        "endpoint_latency_seconds": {"min": min(latencies), "median": statistics.median(latencies),
                                      "max": max(latencies)},
        "metrics": session.metrics(), "events": [asdict(event) for event in events]}
    if translate:
        translations = [event for event in events if event.kind == "translation_completed"]
        report["translation_backend"] = "Helsinki-NLP/opus-mt-en-zh + OpenCC, CPU"
        report["translation_count"] = len(translations)
        report["translation_latency_seconds"] = [e.translation_latency_seconds for e in translations]
        report["end_to_end_latency_seconds"] = [e.end_to_end_latency_seconds for e in translations]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({key: value for key, value in report.items() if key != "events"}, indent=2))
    for event in finals:
        print(f"FINAL {event.start:.2f}-{event.end:.2f}: {event.text}")
    if translate:
        for event in translations:
            print(f"ZH {event.start:.2f}-{event.end:.2f}: {event.translated_text}")
        if len(translations) != len(finals):
            raise RuntimeError("Not all final transcripts were translated; inspect report")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("wav", type=Path)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="auto")
    parser.add_argument("--translate", action="store_true")
    parser.add_argument("--passes", type=int, default=1)
    args = parser.parse_args()
    run(args.wav, args.report, args.device, args.translate, args.passes)
