"""Opt-in EXE validation on synthetic fixtures; not a clean Windows certification."""
import argparse
import json
import logging
from pathlib import Path
import sys
import threading
import time
import tkinter as tk


def downloader_check(root):
    import hashlib
    import io
    from model_download import ModelSpec, ModelDownloader, DownloadError, DownloadCancelled, validate_installed
    payload = b"controlled packaged download fixture"
    spec = ModelSpec("fixture", "Fixture", "test/fixture", "revision", (
        {"name": "fixture.bin", "size": len(payload), "sha256": hashlib.sha256(payload).hexdigest()},))
    mode = ["offline"]
    def opener(request, timeout):
        if mode[0] == "offline": raise OSError("controlled offline")
        stream = io.BytesIO(b"x" * len(payload) if mode[0] == "corrupt" else payload)
        stream.status, stream.headers = 200, {}
        return stream
    downloader = ModelDownloader(root / "models", root / "downloads", opener=opener)
    target = root / "models/fixture/revision"
    checks = {}
    for value in ("offline", "corrupt"):
        mode[0] = value
        try:
            downloader.download(spec)
            checks[value + "_rejected"] = False
        except DownloadError:
            checks[value + "_rejected"] = not validate_installed(target, spec)
    cancelled = threading.Event()
    cancelled.set()
    try:
        downloader.download(spec, cancelled)
        checks["cancelled"] = False
    except DownloadCancelled:
        checks["cancelled"] = True
    mode[0] = "valid"
    checks["retry_validated"] = validate_installed(downloader.download(spec), spec)
    mode[0] = "offline"
    checks["installed_offline"] = validate_installed(downloader.download(spec), spec)
    return checks


def realtime_check(models, audio):
    import sounddevice
    import wave
    from realtime import RealtimeSession
    from realtime_audio import RealtimeWhisper
    from realtime_config import RealtimeConfig
    from realtime_translation import TranslatedRealtimeSession, RealtimeTranslationConfig
    config = RealtimeConfig(model=str(models / "small"), device="cuda", compute_type="float16")
    result = {"audio_devices": len(sounddevice.query_devices()), "human_speech_verified": False}
    load_started = time.perf_counter()
    engine = RealtimeWhisper(config)
    result["model_load_seconds"] = time.perf_counter() - load_started
    microphone = RealtimeSession(lambda event: None, config, engine_factory=lambda: engine)
    try:
        for duration in (1, .3):
            microphone.start()
            time.sleep(duration)
            microphone.stop()
        result["microphone_start_stop_twice"] = not microphone.running
        result["microphone_metrics"] = microphone.metrics()
    except Exception as error:
        result["microphone_error"] = str(error)
    finally: microphone.stop()
    replay_done = threading.Event()
    class Replay:
        def __init__(self, config, feed, fault):
            self.stop_event = threading.Event()
            self.config, self.feed = config, feed
        def start(self):
            def run():
                try:
                    with wave.open(str(audio), "rb") as stream:
                        assert (stream.getnchannels(), stream.getframerate(), stream.getsampwidth()) == (1, 16000, 2)
                        pcm = stream.readframes(stream.getnframes()) + bytes(32000)
                    size = self.config.frame_samples * 2
                    for offset in range(0, len(pcm), size):
                        if self.stop_event.is_set(): break
                        self.feed(pcm[offset:offset+size].ljust(size, b"\0"))
                        self.stop_event.wait(self.config.frame_ms / 1000)
                finally: replay_done.set()
            self.thread = threading.Thread(target=run, name="packaged-replay")
            self.thread.start()
        def close(self):
            self.stop_event.set()
            self.thread.join(5)
    finals, translated, errors = [], [], []
    def received(event):
        if event.kind == "final_transcript":
            finals.append({"id": event.utterance_id, "start": event.start, "end": event.end,
                           "nonempty": bool(event.text), "latency": event.endpoint_latency_seconds})
        elif event.kind == "translation_completed":
            translated.append({"id": event.utterance_id, "start": event.start, "end": event.end,
                "nonempty": bool(event.translated_text), "latency": event.translation_latency_seconds,
                "end_to_end": event.end_to_end_latency_seconds})
        elif event.kind in ("error", "translation_failed"): errors.append(event.reason)
    session = TranslatedRealtimeSession(received, config, RealtimeTranslationConfig(enabled=True,
        model_path=models / "opus-mt-en-zh", request_timeout=90, shutdown_timeout=90),
        engine_factory=lambda: engine, source_factory=Replay)
    try:
        session.start()
        if not replay_done.wait(25): raise TimeoutError("Replay did not finish")
    finally: session.stop()
    result.update(replay_finals=finals, replay_translations=translated, replay_errors=errors,
                  clean_shutdown=not session.asr.running and not session.translation.running,
                  metrics=session.metrics())
    return result


def main():
    import os
    entry_time = time.time()
    parser = argparse.ArgumentParser()
    parser.add_argument("--packaged-check", action="store_true")
    parser.add_argument("--models", type=Path)
    parser.add_argument("--audio", type=Path)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--startup-only", action="store_true")
    parser.add_argument("--offline", action="store_true")
    parser.add_argument("--interactive", action="store_true", help="Manual native UI validation, no automatic input")
    args = parser.parse_args()
    if args.offline:
        import os
        import socket
        os.environ["HF_HUB_OFFLINE"] = os.environ["TRANSFORMERS_OFFLINE"] = "1"
        def blocked(*args, **kwargs): raise OSError("Packaged validation: network disabled")
        socket.socket.connect = socket.socket.connect_ex = socket.create_connection = blocked
    from app_paths import PATHS
    from gui import DesktopApp
    from gui_controller import Settings
    from diagnostics import make_diagnostics
    PATHS.logs.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(filename=PATHS.logs / "gui.log", level=logging.INFO, encoding="utf-8")
    if not args.startup_only:
        if not args.models or not args.audio: parser.error("--models and --audio required")
        Settings(language="en", formats=("txt", "docx", "json", "srt", "vtt"), file_model=str(args.models / "large-v3"), realtime_model=str(args.models / "small"),
                 output_dir=str(PATHS.output), translation=True, setup_completed=args.interactive).save(PATHS.config)
    from ui_support import create_root
    root = create_root()
    app = DesktopApp(root)
    report = {"frozen": bool(getattr(sys, "frozen", False)), "executable": sys.executable,
              "cwd": str(Path.cwd()), "data_directory": str(PATHS.data), "clean_windows": False,
              "offline": "parent sockets blocked; child HF offline/local-only" if args.offline else False}
    launch_time = float(os.environ.get("LOCALASR_LAUNCH_UNIX", entry_time))
    report["timings"] = {"entry_seconds": entry_time - launch_time, "gui_created_seconds": time.time() - launch_time}
    if args.interactive:
        interactive_check(root, app, args, report)
        return
    class ModelTiming(logging.Handler):
        def emit(self, record):
            if record.name != "transcriber": return
            if record.msg.startswith("Loading local model:"): self.began = time.perf_counter()
            elif record.msg == "Model loaded" and hasattr(self, "began"):
                report["timings"]["file_model_load_seconds"] = time.perf_counter() - self.began
    logging.getLogger().addHandler(ModelTiming())
    phase = "ready"
    started = time.monotonic()
    backend_done = threading.Event()
    def finish():
        report.update(pages=len(app.tabs.tabs()), config_exists=PATHS.config.is_file(),
                      logs_exist=(PATHS.logs / "gui.log").is_file())
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        app.close()
    def backend():
        try:
            import tempfile
            with tempfile.TemporaryDirectory(dir=PATHS.data) as temp:
                report["downloader"] = downloader_check(Path(temp))
            if not args.startup_only:
                import shutil
                from exporter import Exporter
                from docx import Document
                name = args.audio.name
                data = json.loads((PATHS.output / (name + ".json")).read_text(encoding="utf-8"))
                manifest = json.loads((PATHS.output / (name + ".complete.json")).read_text(encoding="utf-8"))
                kwargs = dict(translation_request=manifest["translation"]["request"], transcription_request=manifest["transcription"])
                report["file_exports"] = {fmt: (PATHS.output / (name + "." + fmt)).stat().st_size for fmt in ("txt", "docx", "json", "srt", "vtt")}
                report["file_translation_complete"] = data.get("translation", {}).get("complete", False)
                report["bilingual_docx"] = any("\u4e00" <= c <= "\u9fff" for p in Document(PATHS.output / (name + ".docx")).paragraphs for c in p.text)
                report["completion_valid"] = Exporter.is_complete(name, PATHS.output, ("txt", "docx", "json", "srt", "vtt"), **kwargs)
                with tempfile.TemporaryDirectory(dir=PATHS.data) as temp:
                    for fmt in ("txt", "docx", "json", "srt", "complete.json"):
                        shutil.copy2(PATHS.output / (name + "." + fmt), Path(temp) / (name + "." + fmt))
                    report["missing_vtt_incomplete"] = not Exporter.is_complete(name, temp, ("txt", "docx", "json", "srt", "vtt"), **kwargs)
                report["realtime"] = realtime_check(args.models, args.audio)
        except Exception as error:
            logging.exception("Packaged check failed")
            report["backend_error"] = type(error).__name__ + ": " + str(error)
        finally: backend_done.set()
    def tick():
        nonlocal phase
        try:
            if time.monotonic() - started > 300:
                report["timeout"] = phase
                finish()
                return
            if phase == "ready" and app.runtime_ready and not app.documents.busy and not app.controller.busy:
                report["timings"]["gui_ready_seconds"] = time.time() - launch_time
                report["diagnostics"] = make_diagnostics(app.controller.runtime)
                if app.setup_dialog is None: app.open_setup()
                report["first_run_dialog"] = bool(app.setup_dialog and app.setup_dialog.window.winfo_exists())
                from ui_audit import inspect_labels
                report['chinese_ui'] = inspect_labels(root)
                report['native_drop_registered'] = app.drop_available
                assert report['chinese_ui']['passed'], report['chinese_ui']
                assert app.drop_available, 'Native drop unavailable in frozen build'
                app.setup_dialog.close()
                from ui_visual_audit import inspect_visual
                report['visual_theme'] = inspect_visual(app)
                assert report['visual_theme']['passed'], report['visual_theme']
                if args.startup_only:
                    try:
                        app.require_model("file")
                        report["missing_model_prompt"] = False
                    except ValueError:
                        report["missing_model_prompt"] = app.setup_dialog is not None
                    if app.setup_dialog: app.setup_dialog.close()
                    app.documents.submit(backend)
                    phase = "backend"
                else:
                    app.add_files([str(args.audio)])
                    app.start_files()
                    phase = "file"
            elif phase == "file" and not app.controller.busy and not app.documents.busy and app.controller.events.empty():
                report["file_rows"] = [app.files.item(i, "values") for i in app.paths.values()]
                report["gui_error"] = app.error.get()
                app.tabs.select(app.live_page)
                app.documents.submit(backend)
                phase = "backend"
            elif phase == "backend" and backend_done.is_set() and not app.documents.busy:
                finish()
                return
        except Exception as error:
            logging.exception("Packaged GUI check failed")
            report["gui_check_error"] = str(error)
            finish()
            return
        root.after(100, tick)
    root.after(100, tick)
    root.mainloop()


def interactive_check(root, app, args, report):
    """Opt-in validation surface; drag starts only from real mouse input.

    The source uses native TkDnD DND_FILES/OLE, not event_generate or calling
    add_files. It is a harness-only source, not an Explorer certification.
    """
    from tkinter import ttk
    from tkinterdnd2 import DND_FILES, COPY
    from ui_strings import tr
    from ui_audit import inspect_labels
    report.update(drag_started=0, drag_ended=[], states=[], realtime_events=[])
    source = ttk.Label(app.file_page, text=tr('test_drag_source'), padding=8, relief='solid')
    source.pack(side='bottom', fill='x', before=app.file_footer)
    source.drag_source_register(1, DND_FILES)
    def drag(event):
        report['drag_started'] += 1
        return (COPY, DND_FILES, (str(args.audio.resolve()),))
    source.dnd_bind('<<DragInitCmd>>', drag)
    source.dnd_bind('<<DragEndCmd>>', lambda event: report['drag_ended'].append(event.action))
    original = app.on_realtime
    def receive(event):
        report['realtime_events'].append({'kind': event.kind, 'utterance': event.utterance_id})
        original(event)
    app.on_realtime = receive
    def sample():
        rows = [app.files.item(item, 'values') for item in app.files.get_children()]
        state = {'rows': rows, 'status': app.status.get(), 'error': app.error.get()}
        if not report['states'] or state != report['states'][-1]:
            report['states'].append(state)
        report['native_drop_added'] = bool(report['drag_started'] and str(args.audio.resolve()) in app.paths)
        report['chinese_ui'] = inspect_labels(root)
        if root.winfo_exists(): root.after(500, sample)
    root.after(500, sample)
    root.after(600000, app.close)
    root.mainloop()
    report['clean_shutdown'] = not app.controller.busy and not app.documents.busy
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
