"""Manual microphone smoke test: python src/realtime_demo.py --seconds 15."""

import argparse
import json
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import time

from realtime import RealtimeSession
from realtime_config import RealtimeConfig
from realtime_translation import RealtimeTranslationConfig, TranslatedRealtimeSession


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--list-devices", action="store_true")
    parser.add_argument("--input-device", help="sounddevice device index or name")
    parser.add_argument("--model", default="small", help="Local model path or cached model name")
    parser.add_argument("--device", choices=("auto", "cuda", "cpu"), default="auto")
    parser.add_argument("--seconds", type=float, help="Auto-stop after this many seconds")
    parser.add_argument("--translate", action="store_true", help="Translate English finals locally on CPU")
    parser.add_argument("--translation-target", default="zh-Hans")
    parser.add_argument("--translation-backend", default="marian_local")
    args = parser.parse_args()
    if args.list_devices:
        import sounddevice as sd
        print(sd.query_devices())
        return 0
    if args.seconds is not None and args.seconds <= 0:
        parser.error("--seconds must be positive")
    device = int(args.input_device) if args.input_device and args.input_device.isdecimal() else args.input_device
    log_dir = Path(__file__).resolve().parents[1] / "logs"
    log_dir.mkdir(exist_ok=True)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s",
                        handlers=[logging.StreamHandler(), RotatingFileHandler(
                            log_dir / "realtime.log", maxBytes=2_000_000,
                            backupCount=3, encoding="utf-8")], force=True)

    def callback(event):
        if event.kind == "translation_completed":
            print(f"[ZH #{event.utterance_id}] {event.translated_text}", flush=True)
        elif event.kind == "translation_started":
            pass
        elif event.kind == "stopped" and args.translate:
            print("[ASR stopped] Finishing accepted translations...", flush=True)
        elif event.kind == "final_transcript" and args.translate:
            print(f"[EN FINAL #{event.utterance_id}] {event.text}", flush=True)
        elif event.kind in ("partial_transcript", "final_transcript"):
            print(f"[{event.kind} #{event.utterance_id} {event.start:.2f}-{event.end:.2f}] {event.text}", flush=True)
        else:
            print(f"[{event.kind}] {event.reason}", flush=True)

    config = RealtimeConfig(model=args.model, device=args.device, microphone_device=device)
    session = (TranslatedRealtimeSession(callback, config, RealtimeTranslationConfig(
        enabled=True, target_language=args.translation_target, backend=args.translation_backend))
        if args.translate else RealtimeSession(callback, config))
    failed = False
    try:
        session.start()
        print("Microphone is live. Speak English; Ctrl+C stops and flushes the last utterance.", flush=True)
        started = last_report = time.monotonic()
        while session.running:
            now = time.monotonic()
            if args.seconds is not None and now - started >= args.seconds:
                break
            if now - last_report >= 5:
                print("[metrics] " + json.dumps(session.metrics()), flush=True)
                last_report = now
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("Stopping microphone and finishing pending utterances...", flush=True)
    except Exception:
        logging.exception("Realtime demo failed")
        failed = True
    finally:
        try:
            session.stop()
        except TimeoutError:
            logging.exception("Shutdown not yet complete")
            failed = True
        print("[metrics] " + json.dumps(session.metrics()), flush=True)
    return 1 if failed or session.failure_reason is not None else 0


if __name__ == "__main__":
    raise SystemExit(main())
