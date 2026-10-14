"""Bounded near-realtime ASR pipeline. All user events run on one dispatch thread."""

from collections import deque
from dataclasses import dataclass, field
import logging
import queue
import threading
import time
import uuid

from realtime_config import RealtimeConfig

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RealtimeEvent:
    kind: str
    session_id: str
    utterance_id: int | None = None
    text: str = ""
    start: float | None = None
    end: float | None = None
    language: str = "en"
    reason: str = ""
    inference_seconds: float | None = None
    endpoint_latency_seconds: float | None = None
    created_at: float = field(default_factory=time.monotonic)


@dataclass(frozen=True)
class AudioFrame:
    pcm: bytes
    sample: int
    received_at: float
    gap: bool = False


@dataclass(frozen=True)
class InferenceJob:
    utterance_id: int
    pcm: bytes
    start: float
    end: float
    speech_end_wall: float
    final: bool
    reason: str = ""


class RealtimeSession:
    """start()/stop() are owner-thread operations; callbacks may request_stop().

    stop() from a worker only requests shutdown (returns False), avoiding self-join.
    A timed-out native inference/callback cannot be killed safely; restart is refused
    until the previous workers really exit. A 'stopped' event means producers exited.
    """

    def __init__(self, callback, config=None, *, engine_factory=None,
                 vad_factory=None, source_factory=None):
        from realtime_audio import Microphone, RealtimeWhisper, WebRtcVad
        self.config = config or RealtimeConfig()
        self.callback = callback
        self.engine_factory = engine_factory or (lambda: RealtimeWhisper(self.config))
        self.vad_factory = vad_factory or (lambda: WebRtcVad(self.config))
        from audio_sources import create_source
        self.source_factory = source_factory or create_source
        self._lifecycle = threading.RLock()
        self._threads = []
        self._stats_lock = threading.Lock()
        self.session_id = ""

    @property
    def running(self):
        return any(thread.is_alive() for thread in self._threads)

    @property
    def failure_reason(self):
        return getattr(self, "_fatal_code", None)

    def start(self):
        with self._lifecycle:
            if self.running:
                raise RuntimeError("Previous realtime session has not stopped")
            self.session_id = uuid.uuid4().hex
            self._audio = queue.Queue(self.config.audio_queue_frames)
            self._events = deque()
            self._event_cv = threading.Condition()
            self._jobs = deque()
            self._job_cv = threading.Condition()
            self._partial = None
            self._closed_through = 0
            self._next_sample = 0
            self._stop = threading.Event()
            self._capture_closed = threading.Event()
            self._assembly_done = threading.Event()
            self._producers_done = threading.Event()
            self._ready = threading.Event()
            self._abort_assembly = threading.Event()
            self._fatal_code = None
            self._startup_error = None
            self._engine = None
            self._counts = dict.fromkeys((
                "captured_frames", "dropped_audio_frames", "dropped_audio_samples",
                "portaudio_overflows", "invalid_audio_frames", "dropped_utterances",
                "partials_coalesced", "partials_dropped", "callback_errors",
                "audio_high_watermark", "final_high_watermark", "event_high_watermark",
                "event_backpressure", "inference_count", "final_count"), 0)
            self._counts.update(inference_seconds_total=0.0, last_endpoint_latency_seconds=0.0)
            dispatcher = threading.Thread(target=self._dispatch, name="asr-events", daemon=True)
            supervisor = threading.Thread(target=self._supervise, name="asr-capture-owner", daemon=True)
            self._threads = [dispatcher, supervisor]
            dispatcher.start()
            supervisor.start()
        if not self._ready.wait(self.config.startup_timeout):
            self.request_stop()
            raise TimeoutError("Realtime startup timed out; call stop() before restarting")
        if self._startup_error is not None:
            self.stop()
            raise RuntimeError(f"Realtime startup failed: {type(self._startup_error).__name__}") from self._startup_error
        return self

    def request_stop(self):
        if hasattr(self, "_stop"):
            self._stop.set()

    def stop(self, timeout=None):
        self.request_stop()
        if threading.current_thread() in self._threads:
            return False
        deadline = time.monotonic() + (self.config.shutdown_timeout if timeout is None else timeout)
        for thread in tuple(self._threads):
            thread.join(max(0, deadline - time.monotonic()))
        if self.running:
            raise TimeoutError("Realtime workers still running; microphone stop requested; restart refused")
        return True

    def _inc(self, name, value=1):
        with self._stats_lock:
            self._counts[name] += value

    def _high(self, name, value):
        with self._stats_lock:
            self._counts[name] = max(self._counts[name], value)

    def metrics(self):
        if not hasattr(self, "_counts"):
            return {}
        with self._stats_lock:
            result = dict(self._counts)
        result["audio_backlog"] = self._audio.qsize()
        with self._job_cv:
            result["final_backlog"] = len(self._jobs)
            result["partial_pending"] = self._partial is not None
        return result

    def _fail(self, reason):
        # Single reserved error slot avoids recursion/deadlock in a full event queue.
        with self._event_cv:
            if self._fatal_code is None:
                self._fatal_code = reason
                logger.error("Realtime error: %s", reason)
            self._stop.set()
            self._event_cv.notify_all()

    def feed(self, pcm, *, overflow=False):
        """Nonblocking capture ingress; one producer; PCM16 mono fixed-size frames."""
        if self._stop.is_set():
            return False
        if not pcm:
            return False
        if len(pcm) != self.config.frame_samples * 2:
            self._inc("invalid_audio_frames")
            self._fail("invalid_audio_frame_size")
            return False
        sample = self._next_sample
        self._next_sample += self.config.frame_samples
        self._inc("captured_frames")
        if overflow:
            self._inc("portaudio_overflows")
        frame = AudioFrame(bytes(pcm), sample, time.monotonic(), overflow)
        try:
            self._audio.put_nowait(frame)
        except queue.Full:
            try:
                dropped = self._audio.get_nowait()
                self._inc("dropped_audio_frames")
                self._inc("dropped_audio_samples", len(dropped.pcm) // 2)
            except queue.Empty:
                pass
            self._audio.put_nowait(frame)
        self._high("audio_high_watermark", self._audio.qsize())
        return True

    def _emit(self, event):
        with self._event_cv:
            if event.kind == "partial_transcript":
                for index, old in enumerate(self._events):
                    if old.kind == "partial_transcript" and old.utterance_id == event.utterance_id:
                        self._events[index] = event
                        self._inc("partials_coalesced")
                        return
                if len(self._events) >= self.config.event_queue_size:
                    self._inc("partials_dropped")
                    return
            warned = False
            while len(self._events) >= self.config.event_queue_size:
                partial = next((item for item in self._events if item.kind == "partial_transcript"), None)
                if partial is not None:
                    self._events.remove(partial)
                    self._inc("partials_dropped")
                    break
                if not warned:
                    self._inc("event_backpressure")
                    self._fail("event_consumer_too_slow")
                    warned = True
                # Critical/final events are not dropped. Only workers wait here;
                # capture remains separate and is stopped by the supervisor.
                self._event_cv.wait(0.05)
            self._events.append(event)
            self._high("event_high_watermark", len(self._events))
            self._event_cv.notify_all()

    def _supervise(self):
        source = None
        workers = []
        try:
            self._engine = self.engine_factory()
            vad = self.vad_factory()
            if not self._stop.is_set():
                workers = [threading.Thread(target=self._infer, name="asr-inference", daemon=True),
                           threading.Thread(target=self._assemble, args=(vad,), name="asr-vad", daemon=True)]
                self._threads.extend(workers)
                for worker in workers:
                    worker.start()
                source = self.source_factory(self.config, self.feed, self._fail)
                if not self._stop.is_set():
                    source.start()
            self._ready.set()
            self._stop.wait()
        except Exception as error:
            self._startup_error = error
            self._fail(f"startup_exception:{type(error).__name__}")
        finally:
            self._ready.set()
            if source is not None:
                try:
                    source.close()
                except Exception as error:
                    self._fail(f"microphone_close_exception:{type(error).__name__}")
            self._capture_closed.set()
            for worker in reversed(workers):  # assembler flushes before inference exits
                worker.join()
            # A fatal VAD/ASR error may leave captured frames without a consumer.
            # Account for those explicitly instead of reporting a stopped backlog.
            while True:
                try:
                    discarded = self._audio.get_nowait()
                except queue.Empty:
                    break
                self._inc("dropped_audio_frames")
                self._inc("dropped_audio_samples", len(discarded.pcm) // 2)
            self._engine = None
            self._producers_done.set()
            with self._event_cv:
                self._event_cv.notify_all()

    def _submit(self, job):
        with self._job_cv:
            if self._abort_assembly.is_set():
                self._inc("dropped_utterances" if job.final else "partials_dropped")
                return
            if job.final:
                self._closed_through = job.utterance_id
                self._partial = None
                if len(self._jobs) >= self.config.final_queue_size:
                    self._inc("dropped_utterances")
                    self._abort_assembly.set()
                    self._fail("final_queue_overflow")
                    return
                self._jobs.append(job)
                self._high("final_high_watermark", len(self._jobs))
            else:
                if self._partial is not None:
                    self._inc("partials_coalesced")
                self._partial = job
            self._job_cv.notify_all()

    def _assemble(self, vad):
        cfg = self.config
        pre_roll = deque(maxlen=max(cfg.start_frames, cfg.pre_roll_ms // cfg.frame_ms))
        utterance = []
        utterance_id = 0
        voiced_run = silence = last_voice = last_partial_sample = 0
        expected_sample = 0

        def job(final, reason=""):
            frames = utterance[:last_voice + 1] if final else utterance
            return InferenceJob(utterance_id, b"".join(f.pcm for f in frames),
                                frames[0].sample / cfg.sample_rate,
                                (frames[-1].sample + cfg.frame_samples) / cfg.sample_rate,
                                utterance[last_voice].received_at, final, reason)

        def finish(reason):
            if utterance:
                final = job(True, reason)
                self._emit(RealtimeEvent("speech_ended", self.session_id, utterance_id,
                                         start=final.start, end=final.end, reason=reason))
                self._submit(final)
                utterance.clear()
            pre_roll.clear()

        try:
            while not self._abort_assembly.is_set():
                try:
                    frame = self._audio.get(timeout=0.03)
                except queue.Empty:
                    if self._capture_closed.is_set():
                        break
                    continue
                if frame.sample != expected_sample or frame.gap:
                    logger.warning("Realtime audio gap: dropped/overflowed capture frames")
                    finish("audio_gap")
                    voiced_run = silence = 0
                    self._emit(RealtimeEvent("error", self.session_id, reason="audio_gap"))
                expected_sample = frame.sample + cfg.frame_samples
                voiced = vad.is_speech(frame.pcm)
                if not utterance:
                    pre_roll.append(frame)
                    voiced_run = voiced_run + 1 if voiced else 0
                    if voiced_run < cfg.start_frames:
                        continue
                    utterance_id += 1
                    utterance.extend(pre_roll)
                    last_voice = len(utterance) - 1
                    last_partial_sample = utterance[0].sample
                    silence = 0
                    self._emit(RealtimeEvent("speech_started", self.session_id, utterance_id,
                                             start=utterance[0].sample / cfg.sample_rate))
                else:
                    utterance.append(frame)
                    if voiced:
                        last_voice = len(utterance) - 1
                        silence = 0
                    else:
                        silence += cfg.frame_ms
                length_ms = len(utterance) * cfg.frame_ms
                if silence >= cfg.end_silence_ms or length_ms >= cfg.max_utterance_ms:
                    finish("silence" if silence >= cfg.end_silence_ms else "max_duration")
                    voiced_run = silence = 0
                elif (frame.sample + cfg.frame_samples - last_partial_sample) * 1000 / cfg.sample_rate >= cfg.partial_interval_ms:
                    self._submit(job(False))
                    last_partial_sample = frame.sample + cfg.frame_samples
            if not self._abort_assembly.is_set():
                finish("stop")
        except Exception as error:
            if utterance:
                self._inc("dropped_utterances")
            self._abort_assembly.set()
            self._fail(f"vad_exception:{type(error).__name__}")
        finally:
            self._assembly_done.set()
            with self._job_cv:
                self._job_cv.notify_all()

    def _infer(self):
        try:
            while True:
                with self._job_cv:
                    while not self._jobs and self._partial is None:
                        if self._assembly_done.is_set():
                            return
                        self._job_cv.wait(0.05)
                    if self._jobs:
                        job = self._jobs.popleft()
                    else:
                        job, self._partial = self._partial, None
                started = time.monotonic()
                text = self._engine.transcribe(job.pcm)
                seconds = time.monotonic() - started
                self._inc("inference_count")
                self._inc("inference_seconds_total", seconds)
                with self._job_cv:
                    stale = not job.final and job.utterance_id <= self._closed_through
                if stale:
                    self._inc("partials_dropped")
                    continue
                latency = max(0.0, time.monotonic() - job.speech_end_wall) if job.final else None
                if job.final:
                    self._inc("final_count")
                    with self._stats_lock:
                        self._counts["last_endpoint_latency_seconds"] = latency
                self._emit(RealtimeEvent("final_transcript" if job.final else "partial_transcript",
                                         self.session_id, job.utterance_id, text,
                                         job.start, job.end, reason=job.reason, inference_seconds=seconds,
                                         endpoint_latency_seconds=latency))
                logger.info("Realtime inference final=%s duration=%.3fs endpoint_latency=%s backlog=%d",
                            job.final, seconds, latency, self._audio.qsize())
        except Exception as error:
            self._abort_assembly.set()
            with self._job_cv:
                self._inc("dropped_utterances", len(self._jobs) + 1)
                self._jobs.clear()
                self._partial = None
            self._fail(f"inference_exception:{type(error).__name__}")

    def _dispatch(self):
        last_final = 0
        reported_error = None
        while True:
            with self._event_cv:
                if self._fatal_code is not None and self._fatal_code != reported_error:
                    reported_error = self._fatal_code
                    event = RealtimeEvent("error", self.session_id, reason=reported_error)
                elif self._events:
                    event = self._events.popleft()
                    self._event_cv.notify_all()
                elif self._producers_done.is_set():
                    event = RealtimeEvent("stopped", self.session_id)
                else:
                    self._event_cv.wait(0.05)
                    continue
            if event.kind == "partial_transcript" and event.utterance_id <= last_final:
                continue
            if event.kind == "final_transcript":
                last_final = event.utterance_id
            try:
                self.callback(event)
            except Exception as error:
                self._inc("callback_errors")
                logger.error("Realtime callback exception: %s", type(error).__name__)
                if event.kind not in ("error", "stopped"):
                    try:
                        self.callback(RealtimeEvent("error", self.session_id, reason="callback_exception"))
                    except Exception:
                        logger.error("Realtime error callback also failed")
            if event.kind == "stopped":
                return
