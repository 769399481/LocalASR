"""GUI-independent final-only realtime documents and atomic recovery storage."""
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import threading
import uuid
import os
from concurrent.futures import ThreadPoolExecutor


def now():
    return datetime.now(timezone.utc).isoformat()


@dataclass
class FinalSegment:
    segment_id: int
    start: float
    end: float
    original_text: str
    translated_text: str | None = None
    translation_status: str = "disabled"
    created_at: str = field(default_factory=now)


@dataclass
class RealtimeDocument:
    session_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    started_at: str = field(default_factory=now)
    ended_at: str | None = None
    duration: float = 0.0
    source_language: str = "en"
    target_language: str = "zh-Hans"
    translation_enabled: bool = False
    segments: list[FinalSegment] = field(default_factory=list)
    revision: int = 0
    saved_revision: int = -1
    export_paths: list[str] = field(default_factory=list)

    @property
    def pending(self):
        return any(s.translation_status == "pending" for s in self.segments)

    @property
    def unsaved(self):
        return bool(self.segments) and self.revision != self.saved_revision

    def apply(self, event):
        if event.kind == "final_transcript":
            if any(s.segment_id == event.utterance_id for s in self.segments):
                return False
            self.segments.append(FinalSegment(event.utterance_id, event.start, event.end, event.text,
                translation_status="pending" if self.translation_enabled else "disabled"))
            self.duration = max(self.duration, event.end)
        elif event.kind in ("translation_completed", "translation_failed"):
            segment = next((s for s in self.segments if s.segment_id == event.utterance_id), None)
            if segment is None:
                return False
            if (segment.start, segment.end, segment.original_text) != (event.start, event.end, event.original_text):
                raise ValueError("Translation alignment mismatch")
            segment.translated_text = event.translated_text if event.kind == "translation_completed" else None
            segment.translation_status = "completed" if event.kind == "translation_completed" else "failed"
        else:
            return False
        self.revision += 1
        return True

    def finish(self):
        if self.ended_at is None:
            self.ended_at = now()
            self.duration = max(self.duration, (datetime.fromisoformat(self.ended_at) -
                                               datetime.fromisoformat(self.started_at)).total_seconds())
            self.revision += 1
        # A terminated worker/dropped notification cannot leave an eternal pending job.
        for segment in self.segments:
            if segment.translation_status == "pending":
                segment.translation_status = "failed"
                self.revision += 1

    def to_dict(self):
        return {"schema_version": 1, **asdict(self)}

    @classmethod
    def from_dict(cls, value):
        data = dict(value.get("realtime_session", value))
        if data.pop("schema_version", None) != 1:
            raise ValueError("Unsupported session schema")
        segments = [FinalSegment(**segment) for segment in data.pop("segments")]
        document = cls(**data, segments=segments)
        if not isinstance(document.session_id, str) or not document.session_id.isalnum():
            raise ValueError("Invalid session ID")
        for stamp in (document.started_at, document.ended_at):
            if stamp is not None and datetime.fromisoformat(stamp).tzinfo is None:
                raise ValueError("Session dates require timezone")
        ids = set()
        previous = -1.0
        for segment in segments:
            if (segment.segment_id in ids or not isinstance(segment.original_text, str)
                or segment.translation_status not in ("disabled", "pending", "completed", "failed")
                or not all(isinstance(t, (int, float)) and math.isfinite(t) and t >= 0 for t in (segment.start, segment.end))
                or segment.end < segment.start or segment.start < previous):
                raise ValueError("Invalid recovered segment")
            if segment.translation_status == "completed" and not isinstance(segment.translated_text, str):
                raise ValueError("Missing completed translation")
            ids.add(segment.segment_id)
            previous = segment.start
        if not isinstance(document.duration, (int, float)) or not math.isfinite(document.duration) or document.duration < 0:
            raise ValueError("Invalid duration")
        return document

    def export(self, directory, formats, *, english_only=False):
        from exporter import Exporter
        from result import Segment, TranscriptionResult
        from translation import TranslatedSegment, TranslationResult
        if self.pending and not english_only:
            raise ValueError("Waiting for translation to finish")
        result = TranscriptionResult("\n".join(s.original_text for s in self.segments),
            self.source_language, self.duration, tuple(Segment(s.start, s.end, s.original_text) for s in self.segments))
        translated = None
        if self.translation_enabled and not english_only:
            translated = TranslationResult(self.source_language, self.target_language, result.text,
                "\n".join(s.translated_text or "" for s in self.segments),
                tuple(TranslatedSegment(s.start, s.end, s.original_text, s.translated_text,
                    None if s.translation_status == "completed" else "未完成") for s in self.segments),
                {"session_id": self.session_id})
        # Full session JSON is always included, also for English-only snapshots.
        formats = tuple(dict.fromkeys((*formats, "json")))
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        stamp = datetime.fromisoformat(self.started_at).astimezone().strftime("%Y-%m-%d_%H%M%S")
        base = f"realtime_{stamp}_{self.session_id[:8]}"
        index = 0
        while True:
            name = base + (f"_{index}" if index else "")
            reservation = directory / f"{name}.reserve"
            try:
                handle = os.open(reservation, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.close(handle)
            except FileExistsError:
                index += 1
                continue
            if any(directory.glob(f"{name}.*")) and any(p != reservation for p in directory.glob(f"{name}.*")):
                reservation.unlink()
                index += 1
                continue
            break
        try:
            metadata = self.to_dict()
            metadata["saved_revision"] = self.revision
            metadata["export_paths"] = [str(directory / f"{name}.{fmt}") for fmt in formats]
            return Exporter.export(name, result, directory, formats, translation=translated,
                                   session_data=metadata, bilingual_txt=True)
        finally:
            reservation.unlink(missing_ok=True)


class DocumentStore:
    """One IO worker; autosaves coalesce by session ID, never by partial event."""
    def __init__(self, directory, notify):
        self.directory = Path(directory)
        self.notify = notify
        self.lock = threading.RLock()
        self.document = None
        self.core_id = None
        self.early = {}
        self.pending_writes = {}
        self.writer_scheduled = False
        self.executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="session-io")
        self.tasks = set()
        self.closed = False
        self.io_error = None

    @property
    def busy(self):
        with self.lock:
            return any(not task.done() for task in self.tasks)

    def submit(self, action):
        with self.lock:
            self.tasks = {task for task in self.tasks if not task.done()}
            def guarded():
                try:
                    return action()
                except Exception as error:
                    import logging
                    logging.getLogger(__name__).exception("Session IO failed")
                    self.io_error = str(error)
                    self.notify("error", "会话保存/恢复失败，内容仍保留；请检查输出权限和日志。")
            task = self.executor.submit(guarded)
            self.tasks.add(task)
            return task

    def new(self, translation=False, target="zh-Hans"):
        with self.lock:
            # Old documents keep their own recovery files. Start never deletes one.
            self.autosave()
            self.document = RealtimeDocument(translation_enabled=translation, target_language=target)
            self.core_id = None
            self.early.clear()
            return self.document.session_id

    def accept(self, event):
        if event.kind not in ("final_transcript", "translation_completed", "translation_failed"):
            return
        with self.lock:
            if self.document is None:
                return
            if self.core_id is None:
                self.core_id = event.session_id
            if self.core_id != event.session_id:
                return
            changed = self.document.apply(event)
            if not changed and event.kind.startswith("translation_"):
                # The translator can complete before the English display callback.
                if len(self.early) < 64:
                    self.early[event.utterance_id] = event
            if changed:
                early = self.early.pop(event.utterance_id, None)
                if early is not None:
                    self.document.apply(early)
                self.autosave()

    def snapshot(self):
        with self.lock:
            return RealtimeDocument.from_dict(self.document.to_dict()) if self.document else None

    def finish(self):
        with self.lock:
            if self.document:
                self.document.finish()
                self.autosave()

    def autosave(self):
        with self.lock:
            if not self.document or not self.document.segments:
                return
            self.pending_writes[self.document.session_id] = self.document.to_dict()
            if not self.writer_scheduled:
                self.writer_scheduled = True
                self.submit(self._write_pending)

    def _write_pending(self):
        while True:
            with self.lock:
                if not self.pending_writes:
                    self.writer_scheduled = False
                    return
                key, data = self.pending_writes.popitem()
            try:
                self.directory.mkdir(parents=True, exist_ok=True)
                target = self.directory / f"{key}.json"
                temporary = self.directory / f".{key}.{uuid.uuid4().hex}.tmp"
                try:
                    with temporary.open("w", encoding="utf-8") as output:
                        json.dump(data, output, ensure_ascii=False, indent=2, allow_nan=False)
                        output.flush()
                        os.fsync(output.fileno())
                    temporary.replace(target)
                    self.io_error = None
                finally:
                    temporary.unlink(missing_ok=True)
            except Exception:
                with self.lock:
                    self.writer_scheduled = False
                raise

    def restore(self, path):
        def read():
            doc = RealtimeDocument.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))
            doc.finish()  # Interrupted pending translations are explicitly failed.
            with self.lock:
                self.autosave()
                self.document, self.core_id = doc, None
                self.early.clear()
                self.autosave()
            self.notify("restored", None)
        return self.submit(read)

    def export(self, directory, formats, english_only=False):
        def write():
            doc = self.snapshot()
            if not doc or not doc.segments:
                raise ValueError("No final transcript to export")
            paths = doc.export(directory, formats, english_only=english_only)
            with self.lock:
                if self.document and self.document.session_id == doc.session_id:
                    self.document.saved_revision = doc.revision
                    self.document.export_paths = [str(path) for path in paths]
                    self.autosave()
            self.notify("exported", [str(path) for path in paths])
        return self.submit(write)

    def clear(self):
        with self.lock:
            # Clear the working view only; existing recovery stays available.
            self.autosave()
            self.document, self.core_id = None, None
            self.early.clear()

    def shutdown(self):
        self.executor.shutdown(wait=True)
        self.closed = True
