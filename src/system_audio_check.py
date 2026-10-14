"""Opt-in real output-capture/GUI test. Never injects audio into ASR directly.

Playback is the existing authored English fixture through Windows output.
External mode permits a browser/video player to supply audio instead.
"""
import argparse
from dataclasses import asdict
import json
import logging
from pathlib import Path
import threading
import time
import tkinter as tk


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--system-audio-check", action="store_true")
    parser.add_argument("--models", type=Path, required=True)
    parser.add_argument("--audio", type=Path)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--duration", type=float, default=45)
    parser.add_argument("--hotkeys", action="store_true")
    args = parser.parse_args()
    args.directory.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(filename=args.directory / "runtime.log", level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s %(message)s", encoding="utf-8")
    from gui import DesktopApp
    from gui_controller import Settings, Controller
    from windows_system_audio import default_output
    from app_paths import translation_model_path
    settings_path = args.directory / "settings.json"
    Settings(language="en", formats=("txt", "docx", "json", "srt", "vtt"), file_model=str(args.models / "large-v3"), realtime_model=str(args.models / "small"),
             output_dir=str(args.directory / "output"), translation=True, setup_completed=True,
             audio_source="system", global_hotkeys=args.hotkeys).save(settings_path)
    # Production factory uses the ordinary local translation-model resolver.
    if not translation_model_path().exists():
        raise FileNotFoundError("Configure LOCALASR_DATA_DIR with local translation model")
    report = {"capture": "actual Windows system output", "microphone_used": False,
              "headphones_verified": False, "output_device": default_output(),
              "playback": "authored synthetic English WAV via Windows output" if args.audio else "external player",
              "finals": [], "translations": [], "errors": [], "samples": []}
    report["hotkey_actions"] = []
    from ui_support import create_root
    root = create_root()
    controller = Controller()
    app = DesktopApp(root, controller=controller, settings_path=settings_path)
    app.tabs.select(app.live_page)
    app.toggle_overlay()
    original_hotkey = app.hotkey_action
    def hotkey(action):
        report["hotkey_actions"].append({"action": action, "at": time.time()})
        original_hotkey(action)
    app.hotkey_action = hotkey
    original_post = controller.post
    def post(kind, value):
        if kind == "metrics":
            report["metrics"] = value
        if kind == "error":
            report["errors"].append(value)
        original_post(kind, value)
    controller.post = post
    original_event = app.on_realtime
    def event(value):
        original_event(value)
        if value.kind == "final_transcript":
            report["finals"].append(asdict(value))
        elif value.kind == "translation_completed":
            report["translations"].append(asdict(value))
        elif value.kind in ("error", "translation_failed"):
            report["errors"].append(value.reason)
    app.on_realtime = event
    # Observe actual laid-out widgets after real events, without moving their view.
    report['transcript_visibility'] = {'english': [], 'chinese': [], 'partial': []}
    observed_text = {}
    def observe_transcript():
        for name, widget in (('english', app.english), ('chinese', app.chinese)):
            content = widget.get('1.0', 'end-1c')
            if content.strip() and observed_text.get(name) != content:
                observed_text[name] = content
                target = widget.search(r'\S', 'end-1c', backwards=True, regexp=True, stopindex='1.0')
                report['transcript_visibility'][name].append({
                    'target': target, 'visible': widget.bbox(target) is not None,
                    'height': widget.winfo_height(), 'characters': len(content)})
        partial = app.partial.get()
        if partial and observed_text.get('partial') != partial:
            observed_text['partial'] = partial
            report['transcript_visibility']['partial'].append({
                'visible': bool(app.partial_label.winfo_ismapped()), 'characters': len(partial)})
    quit_playback = threading.Event()
    started = None
    stop_at = None
    playback = None
    last_sample = 0
    report_path = args.directory / "report.json"

    def play():
        import winsound
        while not quit_playback.is_set():
            winsound.PlaySound(str(args.audio), winsound.SND_FILENAME)
            if quit_playback.wait(5):
                break

    def save():
        temporary = report_path.with_suffix(".tmp")
        temporary.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        for attempt in range(20):
            try:
                temporary.replace(report_path)
                return
            except PermissionError:
                if attempt == 19:
                    raise
                time.sleep(.1)

    def sample():
        # Optional validation-only observer, not a product/runtime dependency.
        try:
            import psutil
            process = psutil.Process()
            processes = [process, *process.children(recursive=True)]
            memory = cpu = 0
            for item in processes:
                try:
                    memory += item.memory_info().rss
                    t = item.cpu_times()
                    cpu += t.user + t.system
                except psutil.Error:
                    pass
            return {"seconds": time.monotonic() - started, "rss_bytes_tree": memory, "cpu_seconds_tree": cpu,
                    "segments": len(report["finals"]), "translations": len(report["translations"]),
                    "overlay_segments": len(app.overlay.state.finals)}
        except ImportError:
            return {"seconds": time.monotonic() - started, "observer": "psutil unavailable"}

    def tick():
        nonlocal started, stop_at, playback, last_sample
        try:
            observe_transcript()
            if started is None:
                if app.runtime_ready and not controller.busy and not app.documents.busy and controller.events.empty():
                    app.start_live()
                    started = time.monotonic()
                root.after(100, tick)
                return
            if controller.state == "Running" and stop_at is None:
                stop_at = time.monotonic() + args.duration
                if args.audio:
                    playback = threading.Thread(target=play, name="validation-playback", daemon=True)
                    playback.start()
                report["ready_seconds"] = time.monotonic() - started
            if time.monotonic() - last_sample >= 10:
                report["samples"].append(sample())
                last_sample = time.monotonic()
                save()
            if stop_at is not None and time.monotonic() >= stop_at:
                quit_playback.set()
                if playback and playback.is_alive():
                    root.after(100, tick)
                    return
                if controller.busy:
                    app.stop()
                elif not app.documents.busy and controller.events.empty():
                    doc = app.documents.snapshot()
                    report["session_segments"] = len(doc.segments) if doc else 0
                    report["capture_duration_seconds"] = time.monotonic() - (stop_at - args.duration)
                    def export():
                        if doc and doc.segments:
                            report["exports"] = [str(p) for p in doc.export(args.directory / "output",
                                ("txt", "docx", "json", "srt", "vtt"))]
                        save()
                    app.documents.submit(export)
                    app.close()
                    return
            elif not controller.busy and time.monotonic() - started > 10:
                raise RuntimeError("Realtime stopped unexpectedly")
            root.after(100, tick)
        except Exception as error:
            logging.exception("System audio validation failed")
            report["errors"].append(str(error))
            quit_playback.set()
            save()
            app.close()
    root.after(100, tick)
    root.mainloop()
    report["clean_shutdown"] = not controller.busy and not app.documents.busy
    report["hotkeys_released"] = not app.hotkeys.registered and app.hotkeys.thread is None
    report["passed"] = bool(report["finals"] and report["translations"] and not report["errors"]
                            and report["clean_shutdown"] and len(report.get("exports", [])) == 5)
    save()


if __name__ == "__main__":
    import multiprocessing
    multiprocessing.freeze_support()
    main()
