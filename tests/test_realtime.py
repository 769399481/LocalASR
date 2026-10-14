"""Deterministic synthetic PCM + injected VAD/ASR/source; NOT microphone tests."""

from dataclasses import FrozenInstanceError, replace
import importlib.util
from pathlib import Path
import sys
import threading
import time
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from realtime import RealtimeSession
from realtime_config import RealtimeConfig


def wait_for(predicate, timeout=3):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(0.005)
    raise AssertionError("Timed out waiting for realtime test state")


class FakeSource:
    def __init__(self, config, feed, fault):
        self.feed, self.fault = feed, fault
        self.started = False
        self.closed = False

    def start(self):
        self.started = True

    def close(self):
        self.closed = True


class RealtimeTests(unittest.TestCase):
    def setUp(self):
        self.events = []
        self.sources = []
        self.sessions = []
        self.cfg = RealtimeConfig(start_frames=2, pre_roll_ms=60, end_silence_ms=90,
                                  partial_interval_ms=120, max_utterance_ms=600,
                                  audio_queue_frames=100, shutdown_timeout=3)
        self.voice = b"\x01\x00" * self.cfg.frame_samples
        self.silence = b"\x00\x00" * self.cfg.frame_samples

    def tearDown(self):
        for session in self.sessions:
            session.stop(timeout=3)
            self.assertFalse(session.running)

    def create(self, engine=None, vad=None, callback=None, config=None, source_factory=None):
        def source(config, feed, fault):
            item = FakeSource(config, feed, fault)
            self.sources.append(item)
            return item

        session = RealtimeSession(
            callback or self.events.append, config or self.cfg,
            engine_factory=lambda: engine or Mock(transcribe=Mock(return_value="hello world")),
            vad_factory=lambda: vad or Mock(is_speech=lambda pcm: pcm[0] != 0),
            source_factory=source_factory or source)
        self.sessions.append(session)
        session.start()
        return session

    def feed(self, session, voice=6, silence=3):
        for _ in range(voice):
            session.feed(self.voice)
        for _ in range(silence):
            session.feed(self.silence)

    def finals(self):
        return [event for event in self.events if event.kind == "final_transcript"]

    def test_start_stop_repeated_restart_and_release(self):
        session = self.create()
        ids = []
        for _ in range(3):
            ids.append(session.session_id)
            session.stop()
            self.assertTrue(self.sources[-1].closed)
            self.assertEqual(self.events[-1].kind, "stopped")
            self.assertFalse(session.running)
            session.stop()
            if len(ids) < 3:
                session.start()
        self.assertEqual(len(set(ids)), 3)

    def test_repeated_start_is_rejected(self):
        session = self.create()
        with self.assertRaises(RuntimeError):
            session.start()

    def test_stop_before_start(self):
        self.assertTrue(RealtimeSession(self.events.append).stop())

    def test_silence_and_empty_audio_never_call_asr(self):
        engine = Mock()
        session = self.create(engine=engine)
        self.assertFalse(session.feed(b""))
        self.feed(session, voice=0, silence=20)
        session.stop()
        engine.transcribe.assert_not_called()
        self.assertEqual([event.kind for event in self.events], ["stopped"])

    def test_state_transition_and_final_fields(self):
        session = self.create()
        self.feed(session)
        wait_for(lambda: len(self.finals()) == 1)
        session.stop()
        kinds = [event.kind for event in self.events]
        self.assertLess(kinds.index("speech_started"), kinds.index("speech_ended"))
        self.assertLess(kinds.index("speech_ended"), kinds.index("final_transcript"))
        event = self.finals()[0]
        self.assertEqual((event.text, event.language, event.start), ("hello world", "en", 0.0))
        self.assertAlmostEqual(event.end, 0.18)
        self.assertGreaterEqual(event.endpoint_latency_seconds, 0)
        with self.assertRaises(FrozenInstanceError):
            event.text = "modified"

    def test_partial_during_speech_then_final_never_overwritten(self):
        session = self.create()
        self.feed(session, voice=5, silence=0)
        wait_for(lambda: any(e.kind == "partial_transcript" for e in self.events))
        self.feed(session, voice=2)
        wait_for(lambda: len(self.finals()) == 1)
        final_index = next(i for i, e in enumerate(self.events) if e.kind == "final_transcript")
        session.stop()
        self.assertFalse(any(e.kind == "partial_transcript" and e.utterance_id == 1
                             for e in self.events[final_index + 1:]))

    def test_inflight_partial_is_suppressed_after_endpoint(self):
        entered, release = threading.Event(), threading.Event()
        calls = []

        def infer(pcm):
            calls.append(pcm)
            if len(calls) == 1:
                entered.set()
                release.wait(2)
            return "stable final"

        session = self.create(engine=Mock(transcribe=infer))
        self.feed(session, voice=5, silence=0)
        self.assertTrue(entered.wait(2))
        self.feed(session, voice=1)
        wait_for(lambda: any(e.kind == "speech_ended" for e in self.events))
        release.set()
        wait_for(lambda: len(self.finals()) == 1)
        self.assertFalse(any(e.kind == "partial_transcript" for e in self.events))
        self.assertGreater(session.metrics()["partials_dropped"], 0)

    def test_stop_flushes_active_speech(self):
        session = self.create()
        self.feed(session, voice=5, silence=0)
        session.stop()
        self.assertEqual(len(self.finals()), 1)
        self.assertEqual(self.finals()[0].reason, "stop")
        self.assertTrue(any(e.kind == "speech_ended" and e.reason == "stop" for e in self.events))

    def test_continuous_speech_is_bounded_and_split(self):
        session = self.create()
        self.feed(session, voice=50)
        session.stop()
        self.assertEqual(len(self.finals()), 3)
        self.assertTrue(all(e.end - e.start <= 0.601 for e in self.finals()))
        self.assertEqual(self.finals()[1].start, self.finals()[0].end)

    def test_audio_queue_overflow_drops_oldest_and_reports_gap(self):
        entered, release = threading.Event(), threading.Event()

        def vad(pcm):
            entered.set()
            release.wait(2)
            return True

        session = self.create(vad=Mock(is_speech=vad), config=replace(self.cfg, audio_queue_frames=3))
        session.feed(self.voice)
        self.assertTrue(entered.wait(2))
        for _ in range(12):
            session.feed(self.voice)
        self.assertEqual(session.metrics()["audio_backlog"], 3)
        self.assertEqual(session.metrics()["dropped_audio_frames"], 9)
        release.set()
        session.stop()
        self.assertTrue(any(e.reason == "audio_gap" for e in self.events))
        self.assertLessEqual(session.metrics()["audio_high_watermark"], 3)

    def test_portaudio_overflow_is_distinct_from_known_drops(self):
        session = self.create()
        session.feed(self.voice, overflow=True)
        session.stop()
        self.assertEqual(session.metrics()["portaudio_overflows"], 1)
        self.assertEqual(session.metrics()["dropped_audio_frames"], 0)
        self.assertTrue(any(e.reason == "audio_gap" for e in self.events))

    def test_invalid_frame_reports_error_and_closes(self):
        session = self.create()
        self.assertFalse(session.feed(b"wrong size"))
        session.stop()
        self.assertTrue(any(e.reason == "invalid_audio_frame_size" for e in self.events))

    def test_inference_exception_is_fatal_but_releases_capture(self):
        session = self.create(engine=Mock(transcribe=Mock(side_effect=RuntimeError("inference failed"))))
        self.feed(session)
        wait_for(lambda: any("inference_exception" in e.reason for e in self.events))
        session.stop()
        self.assertTrue(self.sources[0].closed)
        self.assertEqual(self.events[-1].kind, "stopped")

    def test_vad_exception_is_fatal_and_clean(self):
        session = self.create(vad=Mock(is_speech=Mock(side_effect=ValueError("bad VAD"))))
        session.feed(self.voice)
        wait_for(lambda: any("vad_exception" in e.reason for e in self.events))
        session.stop()

    def test_callback_exception_does_not_kill_worker(self):
        threads = []

        def callback(event):
            threads.append(threading.current_thread().name)
            self.events.append(event)
            if event.kind != "error":
                raise ValueError("callback error")

        session = self.create(callback=callback)
        self.feed(session)
        session.stop()
        self.assertEqual(set(threads), {"asr-events"})
        self.assertTrue(any(e.reason == "callback_exception" for e in self.events))
        self.assertGreater(session.metrics()["callback_errors"], 0)

    def test_stop_from_callback_requests_shutdown_without_deadlock(self):
        holder = {}

        def callback(event):
            self.events.append(event)
            if event.kind == "speech_started":
                self.assertFalse(holder["session"].stop())

        session = self.create(callback=callback)
        holder["session"] = session
        self.feed(session)
        wait_for(lambda: any(e.kind == "stopped" for e in self.events))
        session.stop()

    def test_slow_native_inference_stop_timeout_refuses_restart(self):
        entered, release = threading.Event(), threading.Event()

        def infer(pcm):
            entered.set()
            release.wait(2)
            return "finished"

        session = self.create(engine=Mock(transcribe=infer))
        self.feed(session)
        self.assertTrue(entered.wait(2))
        try:
            with self.assertRaises(TimeoutError):
                session.stop(timeout=0.05)
            with self.assertRaises(RuntimeError):
                session.start()
            self.assertTrue(self.sources[-1].closed)
        finally:
            release.set()
        session.stop()

    def test_startup_failure_produces_error_and_stopped(self):
        session = RealtimeSession(self.events.append, self.cfg,
                                  engine_factory=Mock(side_effect=RuntimeError("no model")))
        self.sessions.append(session)
        with self.assertRaises(RuntimeError):
            session.start()
        self.assertEqual([e.kind for e in self.events], ["error", "stopped"])

    def test_source_start_failure_closes_source(self):
        class BrokenSource(FakeSource):
            def start(self):
                raise RuntimeError("device unavailable")

        def factory(config, feed, fault):
            item = BrokenSource(config, feed, fault)
            self.sources.append(item)
            return item

        with self.assertRaises(RuntimeError):
            self.create(source_factory=factory)
        self.assertTrue(self.sources[-1].closed)

    def test_disconnect_produces_error_and_stops(self):
        session = self.create()
        self.sources[-1].fault("microphone_disconnected")
        session.stop()
        self.assertTrue(any(e.reason == "microphone_disconnected" for e in self.events))

    def test_final_queue_overflow_stops_instead_of_growing(self):
        entered, release = threading.Event(), threading.Event()

        def infer(pcm):
            entered.set()
            release.wait(2)
            return "final"

        cfg = replace(self.cfg, partial_interval_ms=570, final_queue_size=1)
        session = self.create(engine=Mock(transcribe=infer), config=cfg)
        self.feed(session)
        self.assertTrue(entered.wait(2))
        self.feed(session)
        wait_for(lambda: session.metrics()["final_backlog"] == 1)
        self.feed(session)
        wait_for(lambda: any(e.reason == "final_queue_overflow" for e in self.events))
        release.set()
        session.stop()
        self.assertEqual(session.metrics()["dropped_utterances"], 1)
        self.assertLessEqual(session.metrics()["final_high_watermark"], 1)

    def test_blocked_callback_bounds_events_and_retains_confirmed_finals(self):
        entered, release = threading.Event(), threading.Event()

        def callback(event):
            self.events.append(event)
            if event.kind == "speech_started" and not entered.is_set():
                entered.set()
                release.wait(2)

        session = self.create(callback=callback, config=replace(self.cfg, event_queue_size=2))
        self.feed(session)
        self.assertTrue(entered.wait(2))
        self.feed(session)
        wait_for(lambda: session.metrics()["event_backpressure"] > 0)
        release.set()
        session.stop()
        self.assertLessEqual(session.metrics()["event_high_watermark"], 2)
        self.assertTrue(any(e.reason == "event_consumer_too_slow" for e in self.events))
        self.assertGreaterEqual(len(self.finals()), 1)

    def test_invalid_config(self):
        for kwargs in ({"sample_rate": 44100}, {"frame_ms": 15}, {"audio_queue_frames": 0},
                       {"pre_roll_ms": 0}, {"partial_interval_ms": 9000}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                RealtimeConfig(**kwargs)

    @unittest.skipUnless(importlib.util.find_spec("webrtcvad"), "Optional VAD dependency not installed")
    def test_real_webrtc_vad_digital_silence(self):
        from realtime_audio import WebRtcVad
        engine = Mock()
        session = self.create(engine=engine, vad=WebRtcVad(self.cfg))
        self.feed(session, voice=0, silence=60)
        session.stop()
        engine.transcribe.assert_not_called()
        self.assertEqual([event.kind for event in self.events], ["stopped"])

    def test_audio_adapter_closes_stream_even_when_stop_raises(self):
        from realtime_audio import Microphone
        sd = Mock()
        sd.RawInputStream.return_value.stop.side_effect = RuntimeError("driver stop failed")
        with patch.dict(sys.modules, {"sounddevice": sd}):
            source = Microphone(self.cfg, Mock(), Mock())
            source.start()
            with self.assertRaises(RuntimeError):
                source.close()
        sd.RawInputStream.return_value.close.assert_called_once()

    def test_capture_callback_only_feeds_and_flags_overflow(self):
        from realtime_audio import Microphone
        sd, feed, fault = Mock(), Mock(), Mock()
        with patch.dict(sys.modules, {"sounddevice": sd}):
            source = Microphone(self.cfg, feed, fault)
            callback = sd.RawInputStream.call_args.kwargs["callback"]
            callback(memoryview(self.voice), self.cfg.frame_samples, Mock(), Mock(input_overflow=True))
            feed.assert_called_once_with(self.voice, overflow=True)
            fault.assert_not_called()
            source.close()

    def test_late_job_after_worker_failure_is_rejected(self):
        from realtime import InferenceJob
        session = self.create()
        session._abort_assembly.set()
        session._submit(InferenceJob(1, self.voice, 0, 0.03, time.monotonic(), True))
        self.assertEqual(session.metrics()["final_backlog"], 0)
        self.assertEqual(session.metrics()["dropped_utterances"], 1)
        session.stop()


if __name__ == "__main__":
    unittest.main()
