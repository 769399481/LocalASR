"""Synthetic format/state tests; not claims of native capture or macOS support."""
from dataclasses import replace
from pathlib import Path
import sys
import time
import types
import unittest
from unittest.mock import patch, Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from audio_sources import AudioSource, PCMConverter, PermissionStatus, capability, create_source
from realtime_config import RealtimeConfig
from realtime import RealtimeEvent
from subtitle_overlay import SubtitleState, OverlayPreferences
from realtime_document import RealtimeDocument
from gui_controller import Settings


def final(i=1, text="Hello"):
    return RealtimeEvent("final_transcript", "session", i, text, float(i), float(i+1))


def translation(i=1):
    return types.SimpleNamespace(kind="translation_completed", session_id="session", utterance_id=i,
                                 translated_text="你好", original_text="Hello", start=float(i), end=float(i+1))


class AudioSourceTests(unittest.TestCase):
    def test_microphone_default(self):
        self.assertEqual(RealtimeConfig().audio_source, "microphone")

    def test_microphone_adapter_unchanged(self):
        with patch("realtime_audio.Microphone") as microphone:
            cfg, feed, fault = RealtimeConfig(), Mock(), Mock()
            self.assertIs(create_source(cfg, feed, fault), microphone.return_value)
            microphone.assert_called_once_with(cfg, feed, fault)

    def test_system_source_dispatch(self):
        with patch("audio_sources.sys.platform", "win32"), patch("windows_system_audio.WindowsSystemAudioSource") as source:
            cfg = RealtimeConfig(audio_source="system")
            self.assertIs(create_source(cfg, Mock(), Mock()), source.return_value)

    def test_application_reserved_not_silently_system(self):
        self.assertFalse(capability("application", "win32").available)
        with self.assertRaises(ValueError):
            RealtimeConfig(audio_source="application")

    def test_mac_pending(self):
        cap = capability("system", "darwin")
        self.assertFalse(cap.available)
        self.assertEqual(cap.permission, PermissionStatus.UNSUPPORTED)
        with patch("audio_sources.sys.platform", "darwin"), self.assertRaisesRegex(RuntimeError, "macOS"):
            create_source(RealtimeConfig(audio_source="system"), Mock(), Mock())

    def test_unsupported_platform(self):
        with patch("audio_sources.sys.platform", "linux"), self.assertRaises(ValueError):
            create_source(RealtimeConfig(audio_source="system"), Mock(), Mock())

    def test_empty_audio(self):
        self.assertEqual(PCMConverter(48000, 2).convert(b""), [])

    def test_bad_format(self):
        with self.assertRaises(ValueError):
            PCMConverter(0, 2)
        with self.assertRaises(ValueError):
            PCMConverter(48000, 2).convert(b"x")

    def test_downmix(self):
        import numpy as np
        stereo = np.tile(np.array([1000, -1000], dtype="int16"), 480)
        frames = PCMConverter(16000, 2).convert(stereo.tobytes())
        self.assertEqual(len(frames), 1)
        self.assertEqual(frames[0], bytes(960))

    def test_resample_48k(self):
        self.check_rate(48000)

    def test_resample_44k(self):
        self.check_rate(44100)

    def check_rate(self, rate):
        import numpy as np
        converter = PCMConverter(rate, 2)
        frames = []
        for _ in range(100):
            frames.extend(converter.convert(np.full((rate // 100, 2), 2000, dtype="int16").tobytes()))
        self.assertTrue(all(len(frame) == 960 for frame in frames))
        self.assertEqual(len(frames), 33)
        self.assertLess(len(converter.pending), 960)
        self.assertAlmostEqual(np.frombuffer(frames[-1], dtype="int16").mean(), 2000, delta=2)

    def test_settings_source_persists(self):
        import tempfile
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/"settings.json"
            settings = replace(Settings(), audio_source="system", overlay={"mode": "中文"})
            settings.save(path)
            self.assertEqual(Settings.load(path), settings)

    def test_device_failure_is_visible(self):
        from windows_system_audio import WindowsSystemAudioSource
        fake = types.SimpleNamespace(PyAudio=Mock(side_effect=OSError("lost")))
        fault = Mock()
        source = WindowsSystemAudioSource(RealtimeConfig(), Mock(), fault)
        with patch.dict(sys.modules, pyaudiowpatch=fake):
            with self.assertRaises(RuntimeError):
                source.start()
            source.close()
        fault.assert_called_once_with("system_audio_unavailable")
        self.assertFalse(source.thread.is_alive())

    def test_source_stop_without_start(self):
        from windows_system_audio import WindowsSystemAudioSource
        WindowsSystemAudioSource(RealtimeConfig(), Mock(), Mock()).close()

    def test_route_change_stops_visibly(self):
        from windows_system_audio import WindowsSystemAudioSource
        device = dict(name="first", index=1, defaultSampleRate=48000, maxInputChannels=2)
        host = Mock()
        host.get_default_wasapi_loopback.return_value = device
        fake = types.SimpleNamespace(PyAudio=lambda: host, paInt16=8)
        source = WindowsSystemAudioSource(RealtimeConfig(), Mock(), Mock())
        with patch.dict(sys.modules, pyaudiowpatch=fake), patch("windows_system_audio.default_output", return_value={"name":"second"}), \
             patch("windows_system_audio.time.monotonic", side_effect=[0, 3]):
            source._run()
        source.fault.assert_called_once_with("system_audio_device_changed")
        host.open.return_value.close.assert_called_once()
        host.terminate.assert_called_once()
        self.assertEqual(source.state, "failed")

    def test_queue_overflow_fails_instead_of_silent_time_splice(self):
        from windows_system_audio import WindowsSystemAudioSource
        source = WindowsSystemAudioSource(RealtimeConfig(), Mock(), Mock())
        host = Mock()
        host.get_default_wasapi_loopback.return_value = dict(name="first", index=1, defaultSampleRate=48000, maxInputChannels=2)
        def opening(**kwargs):
            for _ in range(101):
                kwargs["stream_callback"](bytes(1920), 480, None, 0)
            return Mock()
        host.open.side_effect = opening
        fake = types.SimpleNamespace(PyAudio=lambda:host, paInt16=8, paContinue=0, paAbort=2, paComplete=1)
        with patch.dict(sys.modules, pyaudiowpatch=fake):
            source._run()
        source.fault.assert_called_once_with("system_audio_queue_overflow")
        self.assertEqual(source.dropped, 1)
        self.assertTrue(source.raw.empty())


class SubtitleTests(unittest.TestCase):
    def setUp(self):
        self.state = SubtitleState()

    def test_partial_english_only(self):
        self.state.update(RealtimeEvent("partial_transcript", "session", 1, "Hello"))
        self.assertEqual(self.state.text("中文"), "")
        self.assertEqual(self.state.text("Bilingual"), "Hello")

    def test_final_immutable_to_stale_partial(self):
        self.state.update(final())
        self.state.update(RealtimeEvent("partial_transcript", "session", 1, "Wrong"))
        self.assertEqual(self.state.text("English"), "Hello")

    def test_three_modes(self):
        self.state.update(final())
        self.state.update(translation())
        self.assertEqual(self.state.text("English"), "Hello")
        self.assertEqual(self.state.text("中文"), "你好")
        self.assertEqual(self.state.text("Bilingual"), "Hello\n你好")

    def test_history_bounded(self):
        for i in range(1, 101):
            self.state.update(final(i))
        self.assertEqual(list(self.state.finals), [99, 100])
        self.state.update(translation(1))
        self.assertEqual(len(self.state.finals), 2)

    def test_session_preserves_full_history(self):
        doc = RealtimeDocument(translation_enabled=True)
        for i in range(1, 6):
            for event in (final(i), translation(i)):
                doc.apply(event)
                self.state.update(event)
        self.assertEqual(len(doc.segments), 5)
        self.assertEqual(len(self.state.finals), 2)
        self.assertTrue(all(s.translated_text == "你好" for s in doc.segments))
        self.assertEqual([(s.start, s.end) for s in doc.segments], [(float(i), float(i+1)) for i in range(1,6)])

    def test_old_session_ignored(self):
        self.state.update(final())
        self.state.update(replace(final(2), session_id="old"))
        self.assertEqual(list(self.state.finals), [1])

    def test_reset(self):
        self.state.update(final())
        self.state.reset()
        self.assertEqual(self.state.text("English"), "")

    def test_translation_racing_final(self):
        self.state.update(translation())
        self.state.update(final())
        self.assertEqual(self.state.text("Bilingual"), "Hello\n你好")

    def test_preferences_validation(self):
        OverlayPreferences(x=-1200, y=10, position="Custom").validate()
        with self.assertRaises(ValueError):
            OverlayPreferences(font_size=100).validate()

    def test_hotkey_dispatch_queue(self):
        from desktop_platform import DesktopPlatform
        native = DesktopPlatform()
        native.commands.put("language")
        self.assertEqual(native.poll(), ["language"])
        self.assertEqual(native.poll(), [])
        native.close()


class OverlayWindowTests(unittest.TestCase):
    def setUp(self):
        import tkinter as tk
        from subtitle_overlay import SubtitleOverlay
        self.root = tk.Tk()
        self.root.withdraw()
        self.overlay = SubtitleOverlay(self.root)

    def tearDown(self):
        self.overlay.close()
        self.root.destroy()

    def test_real_window_topmost_modes_hide(self):
        self.overlay.show()
        self.root.update()
        self.assertTrue(self.overlay.window.attributes("-topmost"))
        self.overlay.update(final())
        self.overlay.update(translation())
        for mode in ("English", "中文", "Bilingual"):
            self.overlay.preferences.mode = mode
            self.overlay.render()
            self.assertEqual(self.overlay.label.cget("text"), self.overlay.state.text(mode))
        self.overlay.hide()
        self.assertFalse(self.overlay.visible)

    @unittest.skipUnless(sys.platform == "win32", "Windows native styles")
    def test_clickthrough_and_edit_restore(self):
        self.overlay.show()
        self.assertTrue(self.overlay.set_watch(True))
        native = self.overlay.native
        hwnd = native.user.GetAncestor(self.overlay.window.winfo_id(), 2)
        self.assertTrue(native.user.GetWindowLongW(hwnd, -20) & 0x20)
        self.overlay.set_watch(False)
        self.assertFalse(native.user.GetWindowLongW(hwnd, -20) & 0x20)
        self.root.update()
        self.assertTrue(self.overlay.bar.winfo_ismapped())

    def test_saved_negative_coordinates(self):
        self.overlay.preferences.position = "Custom"
        self.overlay.preferences.x = -1100
        self.overlay.preferences.y = 40
        with patch('subtitle_overlay.monitor_rect', return_value=(-1920, 0, 0, 1080)):
            self.overlay.show()
        self.root.update()
        self.assertEqual(self.overlay.window.winfo_x(), -1100)

    def test_font_opacity_size(self):
        self.overlay.font(2)
        self.overlay.set_opacity("0.5")
        self.overlay.transparency()
        self.assertEqual(self.overlay.preferences.font_size, 24)
        self.assertAlmostEqual(self.overlay.window.attributes("-alpha"), .5, delta=.01)

    def test_narrow_toolbar_controls_remain_accessible(self):
        self.overlay.preferences.width = 350
        self.overlay.show()
        self.overlay.render()
        self.root.update()
        self.assertGreater(self.overlay.opacity_scale.winfo_width(), 100)
        for button in self.overlay.buttons:
            self.assertLessEqual(button.winfo_x()+button.winfo_width(), self.overlay.window.winfo_width())

    def test_subtitle_growth_stays_in_work_area(self):
        from desktop_platform import monitor_rect
        self.overlay.show()
        self.overlay.preferences.position = "Custom"
        self.overlay.geometry(100, 800)
        self.overlay.update(final(text="A long subtitle. " * 30))
        self.root.update()
        left, top, right, bottom = monitor_rect(self.overlay.window)
        self.assertGreaterEqual(self.overlay.window.winfo_y(), top)
        self.assertLessEqual(self.overlay.window.winfo_y()+self.overlay.window.winfo_height(), bottom)


@unittest.skipUnless(sys.platform == "win32", "Windows hotkey registration")
class NativeHotkeyTests(unittest.TestCase):
    def test_conflict_repeat_unregister_and_worker_dispatch(self):
        from desktop_platform import DesktopPlatform
        import ctypes
        first, second = DesktopPlatform(), DesktopPlatform()
        try:
            failures = first.register()
            self.assertFalse(failures, failures)
            self.assertEqual(len(first.registered), 4)
            self.assertFalse(first.register())
            self.assertEqual(len(second.register()), 4)
            self.assertFalse(second.registered)
            # Exercise WM_HOTKEY dispatch in our own worker without global input.
            self.assertTrue(ctypes.windll.user32.PostThreadMessageW(first.thread.native_id, 0x312, 0x4A13, 0))
            deadline = time.monotonic() + 2
            while first.commands.empty() and time.monotonic() < deadline:
                time.sleep(.02)
            self.assertEqual(first.poll(), ["language"])
            first.close()
            self.assertIsNone(first.thread)
            self.assertFalse(second.register())
        finally:
            first.close()
            second.close()


if __name__ == "__main__":
    unittest.main()
