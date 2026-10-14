"""Real Tk widgets with fake Core workers; no microphone/model claims."""
from dataclasses import replace
from pathlib import Path
import sys
import tempfile
import threading
import time
import tkinter as tk
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from gui import DesktopApp
from gui_controller import Controller, Settings
from realtime import RealtimeEvent
from realtime_translation import TranslationEvent
from hardware import HardwareInfo
from model_registry import ModelEntry
from recommendation import recommend


def fake_runtime(settings=None):
    hardware = HardwareInfo(ram_gb=16, vram_gb=6, ct2_cuda_devices=1,
                            cuda_compute_types=("float16",), cpu_compute_types=("int8",))
    models = (ModelEntry("small", "small", "mock-small", "mock", .5, "both", True),
              ModelEntry("large-v3", "large", "mock-large", "mock", 3, "file", True, realtime_compatible=False))
    return hardware, models, recommend(hardware, models)


class GuiTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.directory = Path(self.temp.name)
        self.root = tk.Tk()
        self.root.withdraw()
        self.gate = threading.Event()
        self.controller = Controller(runtime_probe=fake_runtime)
        self.app = DesktopApp(self.root, controller=self.controller,
                              settings_path=self.directory / "settings.json")
        self.app.output_dir.set(str(self.directory / "out"))
        self.pump(lambda: not self.app.documents.busy and self.controller.events.empty())

    def tearDown(self):
        self.gate.set()
        self.controller.stop()
        if self.controller.thread:
            self.controller.thread.join(5)
        self.assertFalse(self.controller.busy)
        self.app.documents.shutdown()
        try:
            self.root.after_cancel(self.app.timer)
            self.root.destroy()
        except tk.TclError:
            pass
        self.temp.cleanup()

    def pump(self, predicate, timeout=5):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            self.root.update()
            if predicate():
                return
            time.sleep(0.005)
        self.fail("GUI state timed out")

    def file(self, name="test.wav"):
        path = self.directory / name
        path.write_bytes(b"synthetic test, fake transcriber")
        self.app.add_files([path])
        return path

    def test_startup_pages_and_controls(self):
        self.assertEqual(len(self.app.tabs.tabs()), 2)
        self.assertFalse(hasattr(self.app, "settings_page"))
        for control in (self.app.files, self.app.file_start, self.app.live_start,
                        self.app.live_stop, self.app.devices, self.app.english, self.app.chinese):
            self.assertTrue(control.winfo_exists())

    def test_settings_roundtrip_unicode(self):
        self.app.output_dir.set(str(self.directory / "中文输出"))
        self.app.translation.set(True)
        self.app.save_settings()
        self.pump(lambda: not self.app.documents.busy)
        restored = Settings.load(self.app.settings_path)
        self.assertEqual(restored.output_dir, self.app.output_dir.get())
        self.assertTrue(restored.translation)

    def test_bad_settings_shows_error(self):
        self.app.formats["txt"].set(False)
        for flag in self.app.formats.values():
            flag.set(False)
        self.app.guard(self.app.start_files)
        self.assertIn("输出格式", self.app.error.get())

    def test_file_worker_does_not_block_tk_and_updates_state(self):
        path = self.file()
        main_thread = threading.get_ident()
        threads = []
        def run(path):
            threads.append(threading.get_ident())
            self.gate.wait(4)
            return "Success", ""
        self.controller.file_factory = lambda settings, post: Mock(run=run)
        self.app.start_files()
        ticks = []
        self.root.after(10, lambda: ticks.append(True))
        self.pump(lambda: ticks and self.app.files.item(self.app.paths[str(path)], "values")[1] == "处理中")
        self.assertTrue(self.controller.busy)
        self.assertNotEqual(threads[0], main_thread)
        self.gate.set()
        self.pump(lambda: self.app.files.item(self.app.paths[str(path)], "values")[1] == "已完成")
        self.assertEqual(self.app.progress_text.get(), "1 / 1")

    def test_file_failure_continues_and_skipped_visible(self):
        first, second = self.file("a.wav"), self.file("b.wav")
        def run(path):
            if path == first:
                raise PermissionError("private path")
            return "Skipped", ""
        self.controller.file_factory = lambda settings, post: Mock(run=run)
        self.app.start_files()
        self.pump(lambda: self.app.progress_text.get() == "2 / 2")
        self.assertEqual(self.app.files.item(self.app.paths[str(first)], "values")[1], "失败")
        self.assertEqual(self.app.files.item(self.app.paths[str(second)], "values")[1], "已跳过")
        self.assertIn("权限", self.app.error.get())
        self.assertNotIn("Traceback", self.app.error.get())

    def test_stop_batch_finishes_current_only(self):
        first, second = self.file("a.wav"), self.file("b.wav")
        def run(path):
            self.gate.wait(4)
            return "Success", ""
        self.controller.file_factory = lambda settings, post: Mock(run=run)
        self.app.start_files()
        self.pump(lambda: self.app.files.item(self.app.paths[str(first)], "values")[1] == "处理中")
        self.app.stop()
        self.gate.set()
        self.pump(lambda: not self.controller.busy and self.controller.events.empty())
        self.assertEqual(self.app.files.item(self.app.paths[str(second)], "values")[1], "就绪")

    def test_duplicate_names_rejected(self):
        with self.assertRaises(ValueError):
            self.controller.start_files(["a/test.wav", "b/test.wav"], Settings())

    def test_translation_requires_english_for_files(self):
        self.file()
        self.app.language.set("Chinese")
        self.app.translation.set(True)
        self.app.guard(self.app.start_files)
        self.assertIn("英语", self.app.error.get())

    def test_final_is_not_overwritten_by_partial_and_stale_session_ignored(self):
        final = RealtimeEvent("final_transcript", "one", 1, "Confirmed", 0, 2)
        self.app.on_realtime(final)
        self.app.on_realtime(replace(final, kind="partial_transcript", text="stale"))
        self.app.on_realtime(replace(final, session_id="old", utterance_id=2, text="wrong"))
        self.assertEqual(self.app.partial.get(), "")
        text = self.app.english.get("1.0", "end")
        self.assertIn("Confirmed", text)
        self.assertNotIn("wrong", text)
        self.assertNotIn("stale", text)

    def test_translation_events_and_error_display(self):
        event = TranslationEvent("translation_started", "one", 1, "hello", "你好", 0, 1,
                                 "en", "zh-Hans", 0.5, 1.2)
        self.app.on_realtime(event)
        self.assertIn("正在翻译", self.app.translation_status.get())
        self.app.on_realtime(replace(event, kind="translation_completed"))
        self.assertIn("你好", self.app.chinese.get("1.0", "end"))
        self.app.on_realtime(replace(event, kind="translation_failed", reason="timeout"))
        self.assertIn("英文识别不受影响", self.app.error.get())

    def test_realtime_repeated_start_stop(self):
        sessions = []
        class Session:
            running = False
            def start(self): self.running = True
            def stop(self): self.running = False
            def metrics(self): return {}
        def factory(*args):
            session = Session()
            sessions.append(session)
            return session
        self.controller.session_factory = factory
        for _ in range(2):
            self.app.start_live()
            self.pump(lambda: sessions[-1].running)
            self.app.stop()
            self.pump(lambda: not self.controller.busy and self.controller.events.empty())
        self.assertEqual(len(sessions), 2)
        self.assertFalse(any(s.running for s in sessions))

    def test_close_keeps_window_until_worker_clean(self):
        self.file()
        self.controller.file_factory = lambda settings, post: Mock(
            run=lambda path: (self.gate.wait(4), "")[0] and ("Success", ""))
        self.app.start_files()
        self.pump(lambda: "处理中" in str(self.app.files.item(next(iter(self.app.paths.values())), "values")))
        self.app.close()
        self.root.update()
        self.assertTrue(self.root.winfo_exists())
        self.assertIn("正在关闭", self.app.status.get())
        self.gate.set()
        self.pump(lambda: not self.controller.busy)
        self.root.update()

    def test_ui_queue_is_bounded_and_overflow_requests_stop(self):
        for _ in range(600):
            self.controller.post("status", "test")
        self.assertEqual(self.controller.events.qsize(), 512)
        self.assertTrue(self.controller.stop_requested.is_set())
        self.assertTrue(any(k == "error" for k, v in self.controller.drain()))

    def test_open_output_is_worker_operation(self):
        threads = []
        with patch("gui_controller.os.startfile", side_effect=lambda path: threads.append(threading.get_ident())):
            self.controller.open_output(self.app.output_dir.get())
            self.pump(lambda: not self.controller.busy)
        self.assertNotEqual(threads[0], threading.get_ident())

    def test_clear_unsaved_requires_confirmation(self):
        self.app.documents.new()
        self.app.documents.accept(RealtimeEvent("final_transcript", "one", 1, "Keep me", 0, 1))
        with patch("gui.messagebox.askyesno", return_value=False) as confirm:
            self.app.clear_session()
        confirm.assert_called_once()
        self.assertIsNotNone(self.app.documents.snapshot())
        with patch("gui.messagebox.askyesno", return_value=True):
            self.app.clear_session()
        self.assertIsNone(self.app.documents.snapshot())

    def test_new_session_cancel_keeps_old_content(self):
        self.app.documents.new()
        self.app.documents.accept(RealtimeEvent("final_transcript", "one", 1, "Keep me", 0, 1))
        self.pump(lambda: not self.app.documents.busy)
        original = self.app.documents.snapshot().session_id
        with patch("gui.messagebox.askokcancel", return_value=False):
            self.app.start_live()
        self.assertEqual(self.app.documents.snapshot().session_id, original)

    def test_pending_export_cancel_does_not_block_tk(self):
        self.app.documents.new(True)
        self.app.documents.accept(RealtimeEvent("final_transcript", "one", 1, "Keep me", 0, 1))
        self.app.export_waiting = True
        self.app.export_deadline = time.monotonic() - 1
        with patch("gui.messagebox.askyesno", return_value=False):
            self.app.check_export()
        self.assertFalse(self.app.export_waiting)
        self.assertTrue(self.app.documents.snapshot().pending)

    def test_realtime_export_and_clear_controls_exist(self):
        self.assertTrue(self.app.export_button.winfo_exists())
        self.assertTrue(self.app.clear_button.winfo_exists())
        self.assertEqual(len(self.app.tabs.tabs()), 2)

    def test_recovery_failure_blocks_new_session_and_clear(self):
        self.app.documents.new()
        self.app.documents.accept(RealtimeEvent("final_transcript", "one", 1, "Keep me", 0, 1))
        self.pump(lambda: not self.app.documents.busy)
        self.app.documents.io_error = "disk full"
        with self.assertRaises(ValueError):
            self.app.start_live()
        with self.assertRaises(ValueError):
            self.app.clear_session()
        self.assertEqual(self.app.documents.snapshot().segments[0].original_text, "Keep me")

    def test_compact_window_reserves_footer(self):
        self.root.geometry("880x600")
        self.root.deiconify()
        self.app.tabs.select(self.app.live_page)
        self.pump(lambda: self.app.live_page.winfo_height() > 1 and self.app.live_page.winfo_ismapped())
        self.root.update_idletasks()
        bottom = self.app.footer.winfo_rooty() + self.app.footer.winfo_height()
        self.assertLessEqual(bottom, self.root.winfo_rooty() + self.root.winfo_height())
        self.app.partial.set("Current partial text")
        self.root.update_idletasks()
        for control in (self.app.partial_label, self.app.translation_label):
            self.assertTrue(control.winfo_ismapped(), f"{control}: page height={self.app.live_page.winfo_height()}, panes={self.app.panes.winfo_height()}")
            self.assertLessEqual(control.winfo_rooty() + control.winfo_height(), self.app.footer.winfo_rooty())

    def test_export_settings_close_does_not_break_poll(self):
        self.app.live_export_settings()
        for child in self.root.winfo_children():
            if isinstance(child, tk.Toplevel) and child.title() == "实时会话导出设置":
                child.destroy()
        self.app.sync_controls()
        self.assertTrue(all(button.winfo_exists() for button in self.app.actions))

    def test_hotkey_stops_loading_realtime_not_file_job(self):
        with patch.object(self.app, "stop") as stop:
            self.controller.state = "Loading"
            with patch.object(type(self.controller), "busy", new_callable=unittest.mock.PropertyMock, return_value=True):
                self.app.live_requested = False
                self.app.hotkey_action("start_stop")
                stop.assert_not_called()
                self.app.live_requested = True
                self.app.session_id = None
                self.app.hotkey_action("start_stop")
                stop.assert_called_once()

    def test_quality_modes_and_empty_buttons(self):
        self.app.sync_controls()
        self.assertEqual(self.app.file_quality_box.cget("values"), ("自动推荐", "快速", "高精度"))
        self.assertEqual(self.app.realtime_quality_box.cget("values"), ("自动推荐", "均衡"))
        self.assertEqual(str(self.app.file_start.cget("state")), "disabled")
        self.assertEqual(str(self.app.export_button.cget("state")), "disabled")
        self.file()
        self.pump(lambda: not self.app.documents.busy and self.controller.events.empty())
        self.app.sync_controls()
        self.assertEqual(str(self.app.file_start.cget("state")), "normal")

    def test_quality_override_persists_without_runtime(self):
        self.app.file_quality.set("Fast")
        self.app.save_settings()
        self.pump(lambda: not self.app.documents.busy)
        self.assertEqual(Settings.load(self.app.settings_path).file_quality, "Fast")
        text = self.app.settings_path.read_text(encoding="utf-8")
        self.assertNotIn("compute_type", text)
        self.assertNotIn("HardwareInfo", text)

    def test_missing_models_disable_start_but_allow_restore(self):
        info, _, _ = fake_runtime()
        self.app.apply_runtime((info, (), recommend(info, ())))
        self.app.sync_controls()
        self.assertEqual(str(self.app.live_start.cget("state")), "disabled")
        self.app.guard(self.app.start_live)
        self.assertIn("本地模型", self.app.error.get())

    def test_unavailable_override_resets_to_auto(self):
        self.app.file_quality.set("Accurate")
        info, models, _ = fake_runtime()
        self.app.apply_runtime((info, models[:1], recommend(info, models[:1])))
        self.assertEqual(self.app.file_quality.get(), "Auto")
        self.assertIn("不可用", self.app.error.get())

    def test_loading_stopping_buttons_and_no_duplicate_start(self):
        entered = threading.Event()
        class Session:
            running = False
            def start(inner):
                entered.set()
                self.gate.wait(4)
                inner.running = True
            def stop(inner): inner.running = False
            def metrics(inner): return {}
        self.controller.session_factory = lambda *args: Session()
        self.app.start_live()
        self.pump(entered.is_set)
        self.app.sync_controls()
        self.assertEqual(self.controller.state, "Loading")
        self.assertEqual(str(self.app.live_start.cget("state")), "disabled")
        with self.assertRaises(ValueError):
            self.controller.start_realtime(Settings())
        self.app.stop()
        self.app.sync_controls()
        self.assertEqual(self.controller.state, "Stopping")
        self.assertEqual(str(self.app.live_stop.cget("state")), "disabled")
        self.gate.set()
        self.pump(lambda: not self.controller.busy and self.controller.events.empty())
        self.assertEqual(self.controller.state, "Stopped")

    def test_hardware_probe_runs_off_ui_thread(self):
        threads = []
        self.controller.runtime_probe = lambda settings: (threads.append(threading.get_ident()) or fake_runtime())
        self.app.documents.submit(lambda: self.controller.initialize_runtime(Settings()))
        self.pump(lambda: not self.app.documents.busy and self.controller.events.empty())
        self.assertNotEqual(threads[0], threading.get_ident())

    def test_runtime_failure_reports_finished_check(self):
        self.controller.runtime_probe = Mock(side_effect=RuntimeError("probe failed"))
        self.app.policy = None
        with self.assertLogs("gui_controller", level="ERROR"):
            self.app.documents.submit(lambda: self.controller.initialize_runtime(Settings()))
            self.pump(lambda: not self.app.documents.busy and self.controller.events.empty())
        self.assertNotIn("正在检查", self.app.acceleration.get())
        self.assertEqual(str(self.app.live_start.cget("state")), "disabled")

    def test_setup_panel_translation_is_optional(self):
        from setup_ui import SetupDialog
        info, models, _ = fake_runtime()
        missing = tuple(replace(m, installed=False) for m in models)
        self.controller.runtime = (info, missing, recommend(info, missing))
        with patch("setup_ui.translation_model_available", return_value=False):
            dialog = SetupDialog(self.app)
        self.assertTrue(dialog.choices["small"].get())
        self.assertTrue(dialog.choices["large-v3"].get())
        self.assertFalse(dialog.choices["opus-mt-en-zh"].get())
        dialog.close()

    def test_missing_translation_opens_download_prompt(self):
        self.app.translation.set(True)
        with patch("gui.translation_model_available", return_value=False), patch.object(self.app, "open_setup") as open_setup:
            with self.assertRaisesRegex(ValueError, "语言模型"):
                self.app.require_model("realtime")
            open_setup.assert_called_once_with(translation=True)

    def test_corrupt_preferences_safe_startup(self):
        path = self.directory / "broken.json"
        path.write_text("invalid {", encoding="utf-8")
        root = tk.Toplevel(self.root)
        with self.assertLogs("gui", level="ERROR"):
            other = DesktopApp(root, controller=Controller(runtime_probe=fake_runtime), settings_path=path)
        self.pump(lambda: not other.documents.busy and other.controller.events.empty())
        self.assertEqual(other.file_quality.get(), "Auto")
        self.assertIn("默认值", other.error.get())
        other.documents.shutdown()
        root.after_cancel(other.timer)
        root.destroy()


if __name__ == "__main__":
    unittest.main()
