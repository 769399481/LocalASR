"""Visible Tk + real Whisper/translation smoke test, paced SYNTHETIC WAV (not mic).

Own-app test driver invokes the same application actions as the buttons. It does
not claim human clicking or human speech validation. Leaves the GUI open unless
--auto-close is specified, for inspection and Word opening by the tester.
"""
import argparse
import json
import logging
from pathlib import Path
import sys
import threading
import time
import tkinter as tk
import wave

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from gui import DesktopApp
from gui_controller import Controller, ROOT
from realtime_config import RealtimeConfig
from realtime_translation import RealtimeTranslationConfig, TranslatedRealtimeSession


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--translate", action="store_true")
    parser.add_argument("--auto-close", action="store_true")
    args = parser.parse_args()
    directory = ROOT / "validation/phase7-gui" / ("bilingual" if args.translate else "english")
    directory.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(filename=directory / "smoke.log", level=logging.INFO)
    ended = threading.Event()
    class Replay:
        def __init__(self, cfg, feed, fault):
            self.cfg, self.feed = cfg, feed
            self.stop = threading.Event()
            self.thread = threading.Thread(target=self.play)
        def start(self): self.thread.start()
        def play(self):
            try:
                with wave.open(str(ROOT / "validation/phase4-realtime/authored-sapi-fixture.wav"), "rb") as audio:
                    while not self.stop.is_set():
                        pcm = audio.readframes(self.cfg.frame_samples)
                        if not pcm:
                            break
                        self.feed(pcm.ljust(self.cfg.frame_samples * 2, b"\0"))
                        self.stop.wait(self.cfg.frame_ms / 1000)
                for _ in range(35):
                    self.feed(b"\0" * self.cfg.frame_samples * 2)
                    self.stop.wait(self.cfg.frame_ms / 1000)
            finally:
                ended.set()
        def close(self):
            self.stop.set()
            self.thread.join()
    def factory(settings, device, callback):
        return TranslatedRealtimeSession(callback, RealtimeConfig(device="cuda"),
            RealtimeTranslationConfig(enabled=args.translate), source_factory=Replay)
    root = tk.Tk()
    controller = Controller(session_factory=factory)
    app = DesktopApp(root, controller=controller, settings_path=directory / "preferences.json")
    app.output_dir.set(str(directory / "output"))
    app.translation.set(args.translate)
    app.tabs.select(app.live_page)
    ticks = []
    phase = "start"
    started = time.monotonic()
    def tick():
        nonlocal phase
        ticks.append(time.monotonic())
        if phase == "start" and app.runtime_ready and not app.documents.busy:
            app.start_live()
            phase = "recording"
        elif phase == "recording" and ended.is_set():
            app.stop()
            phase = "stopping"
        elif phase == "stopping" and not controller.busy and not app.documents.busy and controller.events.empty():
            doc = app.documents.snapshot()
            if not doc or not doc.segments:
                raise RuntimeError("No final transcript")
            app.export_session()
            phase = "exporting"
        elif phase == "exporting" and not app.documents.busy and controller.events.empty():
            doc = app.documents.snapshot()
            report = {"test_type": "Program-driven visible GUI, real GPU ASR, synthetic paced replay; NOT microphone",
                "translation": args.translate, "segments": len(doc.segments), "pending": doc.pending,
                "statuses": [s.translation_status for s in doc.segments],
                "export_paths": doc.export_paths, "recovery": str(app.documents.directory / f"{doc.session_id}.json"),
                "ui_tick_count": len(ticks), "max_ui_tick_gap_seconds": max(b-a for a,b in zip(ticks,ticks[1:])),
                "english_visible": bool(app.english.get("1.0", "end").strip()),
                "chinese_visible": bool(app.chinese.get("1.0", "end").strip()),
                "elapsed_seconds": time.monotonic() - started}
            (directory / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
            print(json.dumps(report, ensure_ascii=False, indent=2), flush=True)
            phase = "finished"
            if args.auto_close:
                app.close()
                return
        if phase != "finished":
            root.after(50, tick)
    root.after(100, tick)
    root.mainloop()


if __name__ == "__main__":
    main()
