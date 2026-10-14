"""Spawn-process translation and synthetic ASR tests; no microphone/model needed."""

from dataclasses import replace
import os
from pathlib import Path
import sys
import threading
import time
import unittest
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from realtime import RealtimeEvent
from realtime_config import RealtimeConfig
from realtime_translation import RealtimeTranslation, RealtimeTranslationConfig, TranslatedRealtimeSession
from test_realtime import FakeSource, wait_for


class TestTranslator:
    def __init__(self, options):
        self.calls = 0

    def translate(self, text, source, target):
        self.calls += 1
        if text == "fail":
            raise ValueError("private text")
        if text == "crash":
            os._exit(3)
        if text == "hang":
            time.sleep(60)
        if text == "slow":
            time.sleep(0.5)
        return f"中文{self.calls}：{text}"


def unavailable_factory(options):
    raise RuntimeError("private initialization details")


class TranslationTests(unittest.TestCase):
    def setUp(self):
        self.events = []
        self.pipelines = []

    def tearDown(self):
        for pipeline in self.pipelines:
            pipeline.stop()
            self.assertFalse(pipeline.running)
            self.assertIsNone(pipeline._process)

    def create(self, callback=None, factory=TestTranslator, **kwargs):
        pipeline = RealtimeTranslation(callback or self.events.append,
            RealtimeTranslationConfig(enabled=True, **kwargs), translator_factory=factory)
        self.pipelines.append(pipeline)
        pipeline.start("session")
        return pipeline

    def final(self, number=1, text="hello", **kwargs):
        return RealtimeEvent("final_transcript", "session", number, text, 1.25, 2.75,
                             endpoint_latency_seconds=0.7, **kwargs)

    def completed(self):
        return [e for e in self.events if e.kind == "translation_completed"]

    def test_prewarm_reuses_model_without_document_event(self):
        pipeline = self.create(prewarm=True)
        wait_for(lambda: "prewarm_seconds" in pipeline.metrics())
        self.assertEqual(self.events, [])
        pipeline.submit(self.final())
        pipeline.stop()
        self.assertEqual(len(self.completed()), 1)
        self.assertIn("中文2", self.completed()[0].translated_text)

    def test_prewarm_can_stop_without_final(self):
        pipeline = self.create(prewarm=True)
        pipeline.stop()
        self.assertFalse(pipeline.running)
        self.assertEqual(pipeline.metrics()["accepted"], 0)

    def test_final_only_alignment_unicode_latency_and_model_reuse(self):
        pipeline = self.create()
        final = self.final()
        self.assertFalse(pipeline.submit(replace(final, kind="partial_transcript")))
        self.assertTrue(pipeline.submit(final))
        self.assertFalse(pipeline.submit(final))
        self.assertFalse(pipeline.submit(replace(final, session_id="stale")))
        self.assertTrue(pipeline.submit(self.final(2)))
        pipeline.stop()
        self.assertEqual(len(self.completed()), 2)
        first, second = self.completed()
        self.assertEqual((first.start, first.end, first.original_text), (1.25, 2.75, "hello"))
        self.assertEqual((first.source_language, first.target_language), ("en", "zh-Hans"))
        self.assertEqual(first.translated_text, "中文1：hello")
        self.assertEqual(second.translated_text, "中文2：hello")
        self.assertAlmostEqual(first.end_to_end_latency_seconds, first.translation_latency_seconds + 0.7)
        self.assertEqual(pipeline.metrics()["duplicates"], 1)

    def test_disabled_has_no_workers_and_no_translation(self):
        pipeline = RealtimeTranslation(self.events.append)
        pipeline.start("session")
        self.assertFalse(pipeline.submit(self.final()))
        self.assertFalse(pipeline.running)
        pipeline.stop()
        self.assertEqual(self.events, [])

    def test_failure_isolated_next_job_succeeds(self):
        pipeline = self.create()
        pipeline.submit(self.final(text="fail"))
        pipeline.submit(self.final(2))
        pipeline.stop()
        self.assertEqual(len(self.completed()), 1)
        failed = [e for e in self.events if e.kind == "translation_failed"]
        self.assertEqual(failed[0].original_text, "fail")
        self.assertNotIn("private", failed[0].reason)

    def test_empty_text_completes_without_loading_model(self):
        pipeline = self.create(factory=unavailable_factory)
        pipeline.submit(self.final(text=""))
        pipeline.stop()
        self.assertEqual(self.completed()[0].translated_text, "")

    def test_unavailable_reports_each_failure(self):
        pipeline = self.create(factory=unavailable_factory)
        pipeline.submit(self.final())
        pipeline.submit(self.final(2))
        pipeline.stop()
        self.assertEqual(pipeline.metrics()["failed"], 2)

    def test_overflow_drops_newest_nonblocking(self):
        pipeline = self.create(queue_size=1)
        pipeline.submit(self.final(text="slow"))
        wait_for(lambda: pipeline.metrics()["in_flight"] == 1)
        pipeline.submit(self.final(2))
        before = time.monotonic()
        self.assertFalse(pipeline.submit(self.final(3)))
        self.assertLess(time.monotonic() - before, 0.1)
        pipeline.stop()
        self.assertEqual(pipeline.metrics()["dropped_translations"], 1)
        self.assertEqual([e.utterance_id for e in self.completed()], [1, 2])
        self.assertTrue(any(e.reason == "translation_queue_overflow" for e in self.events))

    def test_worker_crash_fails_pending_and_future_jobs(self):
        pipeline = self.create()
        pipeline.submit(self.final(text="crash"))
        wait_for(lambda: pipeline.metrics()["failed"] == 1, timeout=8)
        pipeline.submit(self.final(2))
        pipeline.stop()
        self.assertEqual(pipeline.metrics()["failed"], 2)

    def test_hung_translation_terminated_on_stop(self):
        pipeline = self.create(shutdown_timeout=0.15)
        pipeline.submit(self.final(text="hang"))
        wait_for(lambda: pipeline.metrics()["in_flight"] == 1)
        pipeline.submit(self.final(2))
        before = time.monotonic()
        pipeline.stop()
        self.assertLess(time.monotonic() - before, 5)
        self.assertEqual(pipeline.metrics()["failed"], 2)
        self.assertEqual(pipeline.metrics()["backlog"], 0)

    def test_request_timeout_keeps_submission_nonblocking(self):
        pipeline = self.create(request_timeout=0.2)
        pipeline.submit(self.final(text="hang"))
        wait_for(lambda: pipeline.metrics()["failed"] == 1, timeout=8)
        pipeline.submit(self.final(2))
        pipeline.stop()
        self.assertEqual(pipeline.metrics()["failed"], 2)

    def test_restart_and_stop_before_start(self):
        self.assertTrue(RealtimeTranslation(self.events.append).stop())
        pipeline = self.create()
        for _ in range(2):
            with self.assertRaises(RuntimeError):
                pipeline.start("session")
            pipeline.submit(self.final())
            pipeline.stop()
            self.assertEqual(pipeline.metrics()["completed"], 1)
            pipeline.start("session")

    def test_callback_failure_does_not_stop_translation(self):
        def fail(event):
            raise ValueError("bad UI")
        pipeline = self.create(callback=fail)
        pipeline.submit(self.final())
        pipeline.stop()
        self.assertEqual(pipeline.metrics()["completed"], 1)
        self.assertGreater(pipeline.metrics()["callback_errors"], 0)

    def test_slow_translation_does_not_block_asr_and_stop_flushes(self):
        english = []
        sources = []
        cfg = RealtimeConfig(start_frames=2, pre_roll_ms=60, end_silence_ms=90,
                             partial_interval_ms=120, max_utterance_ms=600)
        def source(config, feed, fault):
            item = FakeSource(config, feed, fault)
            sources.append(item)
            return item
        session = TranslatedRealtimeSession(english.append, cfg,
            RealtimeTranslationConfig(enabled=True, shutdown_timeout=0.2),
            translation_callback=self.events.append, translator_factory=TestTranslator,
            engine_factory=lambda: Mock(transcribe=Mock(return_value="hang")),
            vad_factory=lambda: Mock(is_speech=lambda pcm: pcm[0] != 0), source_factory=source)
        for _ in range(2):
            english.clear()
            session.start()
            for _ in range(3):
                for _ in range(6):
                    session.asr.feed(b"\x01\x00" * cfg.frame_samples)
                for _ in range(3):
                    session.asr.feed(b"\0\0" * cfg.frame_samples)
            wait_for(lambda: len([e for e in english if e.kind == "final_transcript"]) == 3)
            self.assertEqual(session.translation.metrics()["completed"], 0)
            session.stop()
            self.assertFalse(session.asr.running)
            self.assertFalse(session.translation.running)
            self.assertTrue(sources[-1].closed)
            self.assertEqual(session.translation.metrics()["accepted"], 3)

    def test_invalid_config(self):
        with self.assertRaises(ValueError):
            RealtimeTranslationConfig(queue_size=0)

    def test_unpicklable_worker_factory_fails_without_leaking_process(self):
        pipeline = self.create(factory=lambda options: TestTranslator(options))
        pipeline.submit(self.final())
        wait_for(lambda: pipeline.metrics()["failed"] == 1)
        self.assertFalse(pipeline.submit(self.final(2)))
        pipeline.stop()
        self.assertEqual(pipeline.metrics()["failed"], 2)

    def test_slow_callback_has_bounded_events_and_does_not_block_submit(self):
        gate = threading.Event()
        entered = threading.Event()
        def callback(event):
            entered.set()
            gate.wait(3)
        pipeline = self.create(callback=callback, event_queue_size=1)
        try:
            pipeline.submit(self.final())
            self.assertTrue(entered.wait(2))
            for index in range(2, 7):
                pipeline.submit(self.final(index))
            wait_for(lambda: pipeline.metrics()["completed"] == 6, timeout=8)
            self.assertGreater(pipeline.metrics()["dropped_events"], 0)
            self.assertLessEqual(pipeline._events.qsize(), 1)
        finally:
            gate.set()

    def test_disabled_wrapper_does_not_load_translator_or_replace_callback(self):
        callback = self.events.append
        session = TranslatedRealtimeSession(callback,
            translator_factory=unavailable_factory,
            engine_factory=lambda: Mock(), vad_factory=lambda: Mock(), source_factory=FakeSource)
        self.assertEqual(session.asr.callback, callback)
        session.start()
        with self.assertRaises(RuntimeError):
            session.start()
        self.assertTrue(session.asr.running)
        session.stop()
        self.assertFalse(session.translation.running)

    def test_final_creation_time_includes_dispatch_delay(self):
        pipeline = self.create()
        pipeline.submit(self.final(created_at=time.monotonic() - 2))
        pipeline.stop()
        self.assertGreaterEqual(self.completed()[0].translation_latency_seconds, 2)


if __name__ == "__main__":
    unittest.main()
