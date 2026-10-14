"""Optional final-only translation. No imports or changes to the ASR engine.

A spawn process owns the CPU translator so a stuck native call can be terminated.
The ASR dispatcher only calls nonblocking submit(); callbacks run separately.
"""

from collections import deque
from dataclasses import dataclass
import logging
import multiprocessing
import pickle
from pathlib import Path
import queue
import threading
import time

from translation import TranslationOptions, create_translator
from app_paths import translation_model_path

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RealtimeTranslationConfig:
    enabled: bool = False
    target_language: str = "zh-Hans"
    backend: str = "marian_local"
    model_path: Path = translation_model_path()
    queue_size: int = 8
    event_queue_size: int = 64
    request_timeout: float = 60.0  # Includes cold model loading for first request.
    shutdown_timeout: float = 15.0
    prewarm: bool = False

    def __post_init__(self):
        if min(self.queue_size, self.event_queue_size, self.request_timeout, self.shutdown_timeout) <= 0:
            raise ValueError("Translation queue sizes and timeouts must be positive")


@dataclass(frozen=True)
class TranslationEvent:
    kind: str
    session_id: str
    utterance_id: int
    original_text: str
    translated_text: str
    start: float
    end: float
    source_language: str
    target_language: str
    translation_latency_seconds: float | None = None
    end_to_end_latency_seconds: float | None = None
    inference_seconds: float | None = None
    reason: str = ""


def _translator_process(connection, options, factory):
    """Only one request in flight; the model is loaded once, including on errors."""
    translator = None
    unavailable = None
    try:
        while True:
            request = connection.recv()
            if request is None:
                return
            text, source = request
            started = time.monotonic()
            try:
                if not text.strip():
                    translated = ""
                else:
                    if translator is None and unavailable is None:
                        try:
                            translator = factory(options)
                        except Exception as error:
                            unavailable = f"translator_unavailable:{type(error).__name__}"
                    if unavailable:
                        connection.send((False, unavailable, time.monotonic() - started))
                        continue
                    translated = translator.translate(text, source, options.target_language)
                    if not isinstance(translated, str) or not translated.strip():
                        raise ValueError("Empty translation")
                connection.send((True, translated, time.monotonic() - started))
            except Exception as error:
                connection.send((False, f"translation_exception:{type(error).__name__}",
                                 time.monotonic() - started))
    except (EOFError, BrokenPipeError, OSError):
        pass
    finally:
        connection.close()


class RealtimeTranslation:
    def __init__(self, callback, config=None, *, translator_factory=create_translator):
        self.config = config or RealtimeTranslationConfig()
        self.callback = callback
        self.factory = translator_factory
        self._threads = []
        self._lock = threading.RLock()
        self._active = False
        self._process = None
        self._counts = {}

    @property
    def running(self):
        return any(thread.is_alive() for thread in self._threads)

    def start(self, session_id):
        with self._lock:
            if self.running or self._active:
                raise RuntimeError("Previous translation session has not stopped")
            self.session_id = session_id
            self._last_id = 0  # ASR final IDs are monotonically increasing per session.
            self._accepting = self.config.enabled
            self._active = self.config.enabled
            self._jobs = deque()
            self._events = queue.Queue(self.config.event_queue_size)
            self._closing = threading.Event()
            self._done = threading.Event()
            self._deadline = float("inf")
            self._worker_failure = None
            self._counts = dict(accepted=0, completed=0, failed=0, dropped_translations=0,
                                duplicates=0, queue_high_watermark=0, callback_errors=0,
                                dropped_events=0, in_flight=0, translation_seconds_total=0.0,
                                last_translation_latency_seconds=None, last_end_to_end_latency_seconds=None)
            if not self.config.enabled:
                return self
            self._threads = [threading.Thread(target=self._work, name="translation-worker", daemon=True),
                             threading.Thread(target=self._dispatch, name="translation-events", daemon=True)]
            for thread in self._threads:
                thread.start()
        return self

    def metrics(self):
        with self._lock:
            return dict(self._counts, backlog=len(getattr(self, "_jobs", ())))

    def submit(self, event):
        if event.kind != "final_transcript":
            return False
        with self._lock:
            if not getattr(self, "_accepting", False) or event.session_id != self.session_id:
                return False
            if event.utterance_id <= self._last_id:
                self._counts["duplicates"] += 1
                return False
            self._last_id = event.utterance_id
            received = event.created_at
            if self._worker_failure:
                self._failure(event, received, self._worker_failure)
                return False
            if len(self._jobs) >= self.config.queue_size:
                self._counts["dropped_translations"] += 1
                self._failure(event, received, "translation_queue_overflow")
                return False  # Drop newest, keep already accepted final translations.
            self._jobs.append((event, received))
            self._counts["accepted"] += 1
            self._counts["queue_high_watermark"] = max(
                self._counts["queue_high_watermark"], len(self._jobs))
            return True

    def _event(self, kind, source, received, *, text="", reason="", inference=None):
        elapsed = time.monotonic() - received
        # created_at includes ASR event dispatch and translation queue delays.
        endpoint = source.endpoint_latency_seconds
        event = TranslationEvent(kind, source.session_id, source.utterance_id,
                                 source.text, text, source.start, source.end, source.language,
                                 self.config.target_language,
                                 elapsed if kind != "translation_started" else None,
                                 endpoint + elapsed if endpoint is not None and kind != "translation_started" else None,
                                 inference, reason)
        try:
            self._events.put_nowait(event)
        except queue.Full:
            with self._lock:
                self._counts["dropped_events"] += 1
            logger.warning("Translation event consumer too slow; event dropped")

    def _failure(self, source, received, reason):
        with self._lock:
            self._counts["failed"] += 1
            logger.warning("Realtime translation failed: %s", reason)
            self._event("translation_failed", source, received, reason=reason)

    def _dispose_process(self):
        process = self._process
        if process is not None:
            if process.pid is None:
                process.close()
                self._process = None
            elif process.is_alive():
                process.terminate()
                process.join(2)
            if self._process is not None:
                if process.is_alive():
                    process.kill()
                    process.join(2)
                if process.is_alive():
                    raise TimeoutError("Translation process could not be terminated")
                process.join()
                process.close()
                self._process = None
        if getattr(self, "_connection", None) is not None:
            self._connection.close()
            self._connection = None

    def _work(self):
        current = None
        unavailable = None
        try:
            if self.config.prewarm:
                self._prewarm()
            while True:
                with self._lock:
                    current = self._jobs.popleft() if self._jobs else None
                    self._counts["in_flight"] = int(current is not None)
                if current is None:
                    if self._closing.wait(0.01):
                        with self._lock:
                            if not self._jobs:
                                break
                    continue
                source, received = current
                if time.monotonic() >= self._deadline:
                    self._failure(source, received, "shutdown_timeout")
                    continue
                if unavailable:
                    self._failure(source, received, unavailable)
                    continue
                self._event("translation_started", source, received)
                if self._process is None:
                    self._start_process()
                try:
                    self._connection.send((source.text, source.language))
                except (BrokenPipeError, EOFError, OSError):
                    unavailable = "translation_worker_exited"
                    self._failure(source, received, unavailable)
                    self._dispose_process()
                    continue
                deadline = time.monotonic() + self.config.request_timeout
                while not self._connection.poll(0.02):
                    if time.monotonic() >= min(deadline, self._deadline):
                        unavailable = "shutdown_timeout" if self._closing.is_set() else "translation_timeout"
                        break
                    if not self._process.is_alive():
                        unavailable = "translation_worker_exited"
                        break
                if unavailable:
                    self._failure(source, received, unavailable)
                    self._dispose_process()
                    continue
                try:
                    success, value, seconds = self._connection.recv()
                except (BrokenPipeError, EOFError, OSError):
                    unavailable = "translation_worker_exited"
                    self._failure(source, received, unavailable)
                    self._dispose_process()
                    continue
                if success:
                    with self._lock:
                        self._counts["completed"] += 1
                        self._counts["translation_seconds_total"] += time.monotonic() - received
                        self._counts["last_translation_latency_seconds"] = time.monotonic() - received
                        self._counts["last_end_to_end_latency_seconds"] = (
                            source.endpoint_latency_seconds + time.monotonic() - received
                            if source.endpoint_latency_seconds is not None else None)
                    self._event("translation_completed", source, received, text=value, inference=seconds)
                    metrics = self.metrics()
                    logger.info("Realtime translation latency=%.3fs inference=%.3fs end_to_end=%s backlog=%d",
                                time.monotonic() - received, seconds,
                                metrics["last_end_to_end_latency_seconds"], metrics["backlog"])
                else:
                    self._failure(source, received, value)
                current = None
        except Exception as error:
            reason = f"translation_worker_exception:{type(error).__name__}"
            self._worker_failure = reason
            if current is not None:
                self._failure(*current, reason)
            logger.error("Realtime translation worker failed: %s", type(error).__name__)
        finally:
            with self._lock:
                while self._jobs:
                    self._failure(*self._jobs.popleft(), "translation_worker_unavailable")
                self._counts["in_flight"] = 0
            try:
                if self._process is not None and self._process.is_alive():
                    try:
                        self._connection.send(None)
                        self._process.join(0.2)
                    except (BrokenPipeError, EOFError, OSError):
                        pass
                self._dispose_process()
            finally:
                self._done.set()

    def _start_process(self):
        pickle.dumps(self.factory)
        context = multiprocessing.get_context("spawn")
        self._connection, child = context.Pipe()
        options = TranslationOptions(True, "en", self.config.target_language,
                                     self.config.backend, self.config.model_path)
        self._process = context.Process(target=_translator_process,
            args=(child, options, self.factory), name="asr-local-translator", daemon=True)
        try:
            self._process.start()
        finally:
            child.close()

    def _prewarm(self):
        """Worker-only warmup: no fake document segment or translation event."""
        started = time.monotonic()
        try:
            self._start_process()
            self._connection.send(("Ready.", "en"))
            while not self._connection.poll(.02):
                if self._closing.is_set() or time.monotonic() - started > self.config.request_timeout:
                    raise TimeoutError("Translation prewarm interrupted")
                if not self._process.is_alive():
                    raise RuntimeError("Translation prewarm process exited")
            success, value, inference = self._connection.recv()
            if not success:
                raise RuntimeError(value)
            with self._lock:
                self._counts["prewarm_seconds"] = time.monotonic() - started
            logger.info("Translation prewarm completed in %.3fs", time.monotonic() - started)
        except Exception:
            logger.warning("Translation prewarm unavailable; English ASR continues", exc_info=True)
            self._dispose_process()

    def _dispatch(self):
        while not (self._done.is_set() and self._closing.is_set()) or not self._events.empty():
            try:
                event = self._events.get(timeout=0.02)
            except queue.Empty:
                continue
            try:
                self.callback(event)
            except Exception as error:
                with self._lock:
                    self._counts["callback_errors"] += 1
                logger.warning("Translation callback failed: %s", type(error).__name__)

    def stop(self, timeout=None):
        if not self._active:
            return True
        timeout = self.config.shutdown_timeout if timeout is None else timeout
        with self._lock:
            self._accepting = False
            self._deadline = min(self._deadline, time.monotonic() + max(0, timeout))
            self._closing.set()
        if threading.current_thread() in self._threads:
            return False
        # Up to 4 seconds extra for process terminate/kill + dispatcher drain.
        deadline = self._deadline + 5
        for thread in self._threads:
            thread.join(max(0, deadline - time.monotonic()))
        if self.running:
            raise TimeoutError("Translation callback/worker has not stopped; restart refused")
        self._active = False
        return True


class TranslatedRealtimeSession:
    """Composition only. Disabled mode uses the original ASR callback unchanged."""

    def __init__(self, callback, asr_config=None, translation_config=None,
                 *, translation_callback=None, translator_factory=create_translator, **asr_factories):
        from realtime import RealtimeSession
        self.translation = RealtimeTranslation(translation_callback or callback, translation_config,
                                               translator_factory=translator_factory)
        self._callback = callback
        self.asr = RealtimeSession(self._on_asr if self.translation.config.enabled else callback,
                                   asr_config, **asr_factories)

    def _on_asr(self, event):
        with self.translation._lock:
            if not self.translation.session_id:
                self.translation.session_id = event.session_id
        self.translation.submit(event)
        self._callback(event)

    def start(self):
        if self.asr.running:
            raise RuntimeError("Previous ASR session has not stopped")
        self.translation.start("")
        try:
            self.asr.start()
        except BaseException:
            self.stop()
            raise
        return self

    @property
    def running(self):
        return self.asr.running

    @property
    def failure_reason(self):
        return self.asr.failure_reason

    def request_stop(self):
        self.asr.request_stop()

    def metrics(self):
        return dict(self.asr.metrics(), translation=self.translation.metrics())

    def stop(self):
        try:
            stopped = self.asr.stop()
        except BaseException:
            self.translation.stop()
            raise
        if not stopped:
            return False  # ASR callback requested stop; owner must finish the join.
        return self.translation.stop()
