from dataclasses import asdict
from decimal import Decimal, ROUND_HALF_UP
import hashlib
from html import escape
import json
import logging
import math
from pathlib import Path
from tempfile import TemporaryDirectory

from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT

from config import OUTPUT_DIR, OUTPUT_FORMATS
from formatter import Formatter
from result import TranscriptionResult
from translation import TranslationResult

logger = logging.getLogger(__name__)


class Exporter:
    SUPPORTED_FORMATS = frozenset(("txt", "docx", "json", "srt", "vtt"))

    @staticmethod
    def normalize_formats(formats) -> tuple[str, ...]:
        if isinstance(formats, str):
            raise ValueError("Output formats must be a sequence, not a string")
        selected = tuple(dict.fromkeys(formats))
        if not selected or any(fmt not in Exporter.SUPPORTED_FORMATS for fmt in selected):
            raise ValueError("Select one or more of: txt, docx, json, srt, vtt")
        return selected

    @staticmethod
    def output_name(audio_path: Path) -> str:
        # The full source filename avoids collisions across media extensions.
        return Path(audio_path).name

    @staticmethod
    def is_complete(filename: str, output_dir: Path = OUTPUT_DIR,
                    formats=OUTPUT_FORMATS, *, translation_request=None, transcription_request=None) -> bool:
        selected = Exporter.normalize_formats(formats)
        directory = Path(output_dir)
        if (directory / f"{filename}.pending").exists():
            return False
        manifest_path = directory / f"{filename}.complete.json"
        if not manifest_path.is_file():
            return False
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            if manifest.get("version") != 1:
                return False
            if transcription_request is not None and manifest.get("transcription") != transcription_request:
                return False
            translated = manifest.get("translation")
            if translation_request is None:
                if translated is not None:
                    return False
            elif (not isinstance(translated, dict)
                  or translated.get("request") != translation_request
                  or translated.get("complete") is not True):
                return False
            recorded = manifest["sha256"]
            for fmt in selected:
                path = directory / f"{filename}.{fmt}"
                if fmt not in recorded or not path.is_file():
                    return False
                if Exporter._digest(path) != recorded[fmt]:
                    logger.warning("Output changed; treating as incomplete: %s", path.name)
                    return False
            return True
        except Exception:
            # Corrupt or unreadable output is incomplete and must be retried.
            logger.warning("Unreadable output; treating as incomplete: %s", filename,
                           exc_info=True)
            return False

    @staticmethod
    def export(filename: str, result: TranscriptionResult | str,
               output_dir: Path = OUTPUT_DIR, formats=OUTPUT_FORMATS, *,
               translation: TranslationResult | None = None,
               translation_request=None, session_data=None, bilingual_txt=False,
               transcription_request=None) -> tuple[Path, ...]:
        if not filename or Path(filename).name != filename or filename in (".", ".."):
            raise ValueError("Export filename must be a single filename")
        selected = Exporter.normalize_formats(formats)
        if isinstance(result, TranscriptionResult):
            Exporter._validate_result(result)
        elif not isinstance(result, str) or any(fmt in ("json", "srt", "vtt") for fmt in selected):
            raise TypeError("JSON/SRT/VTT require TranscriptionResult with real segment timestamps")
        if translation is not None:
            if not isinstance(result, TranscriptionResult):
                raise TypeError("Bilingual export requires TranscriptionResult")
            translation.validate_against(result)
            if translation_request is not None and translation_request != translation.request:
                raise ValueError("Translation request mismatch")
            translation_request = translation.request
        if translation_request is not None and "json" not in selected:
            raise ValueError("Translation exports require JSON to preserve aligned results")
        text = Formatter.clean(result.text if isinstance(result, TranscriptionResult) else result)
        directory = Path(output_dir)
        directory.mkdir(parents=True, exist_ok=True)
        paths = tuple(directory / f"{filename}.{fmt}" for fmt in selected)
        pending = directory / f"{filename}.pending"
        # Stage all requested outputs and their checksums before publishing.
        # The marker covers failures between individually atomic replacements.
        with TemporaryDirectory(prefix=".asr-export-", dir=directory) as staging:
            staged_paths = []
            for fmt in selected:
                staged = Path(staging) / f"transcript.{fmt}"
                value = text if fmt in ("txt", "docx") else result
                if fmt == "json" and (translation is not None or session_data is not None):
                    Exporter.save_json(result, staged, translation=translation, session_data=session_data)
                elif translation is not None and fmt == "txt" and bilingual_txt:
                    Exporter.save_txt(Exporter.bilingual_text(translation), staged)
                elif translation is not None and fmt == "docx":
                    Exporter.save_docx(Exporter.bilingual_text(translation), staged)
                else:
                    getattr(Exporter, f"save_{fmt}")(value, staged)
                staged_paths.append(staged)
            manifest = {"version": 1, "sha256": {
                fmt: Exporter._digest(path) for fmt, path in zip(selected, staged_paths)}}
            if transcription_request is not None:
                manifest["transcription"] = transcription_request
            if translation_request is not None:
                manifest["translation"] = {"request": translation_request,
                                           "complete": translation is not None and translation.complete}
            staged_manifest = Path(staging) / "complete.json"
            staged_manifest.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
            pending.write_text("Export in progress; rerun to recover.\n", encoding="utf-8")
            for staged, target in zip(staged_paths, paths):
                staged.replace(target)
            staged_manifest.replace(directory / f"{filename}.complete.json")
            pending.unlink()
        return paths

    @staticmethod
    def _digest(path: Path) -> str:
        with path.open("rb") as stream:
            return hashlib.file_digest(stream, "sha256").hexdigest()

    @staticmethod
    def _validate_seconds(seconds):
        if isinstance(seconds, bool) or not isinstance(seconds, (int, float)):
            raise ValueError("Timestamps and duration must be numbers")
        if not math.isfinite(seconds) or seconds < 0:
            raise ValueError("Timestamps and duration must be finite and non-negative")

    @staticmethod
    def _validate_result(result: TranscriptionResult):
        Exporter._validate_seconds(result.duration)
        if not isinstance(result.text, str) or not isinstance(result.language, str):
            raise ValueError("Result text and language must be strings")
        for segment in result.segments:
            Exporter._validate_seconds(segment.start)
            Exporter._validate_seconds(segment.end)
            if segment.end < segment.start or not isinstance(segment.text, str):
                raise ValueError("Segment must have text and end >= start")

    @staticmethod
    def timestamp(seconds: float, *, vtt: bool = False) -> str:
        Exporter._validate_seconds(seconds)
        # Round once, then divide integers so 59.9995 carries into the next minute.
        total_ms = int((Decimal(str(seconds)) * 1000).to_integral_value(rounding=ROUND_HALF_UP))
        hours, remainder = divmod(total_ms, 3_600_000)
        minutes, remainder = divmod(remainder, 60_000)
        whole_seconds, milliseconds = divmod(remainder, 1000)
        separator = "." if vtt else ","
        return f"{hours:02d}:{minutes:02d}:{whole_seconds:02d}{separator}{milliseconds:03d}"

    @staticmethod
    def save_json(result: TranscriptionResult, path: Path, *, translation=None, session_data=None):
        Exporter._validate_result(result)
        data = asdict(result)
        if session_data is not None:
            data["realtime_session"] = session_data
        if translation is not None:
            translation.validate_against(result)
            data["translation"] = {**asdict(translation), "complete": translation.complete}
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2,
                                   allow_nan=False) + "\n", encoding="utf-8")

    @staticmethod
    def bilingual_text(translation: TranslationResult) -> str:
        blocks, group = [], []

        def flush():
            original = " ".join(segment.original_text.strip() for segment in group)
            translated = " ".join(segment.translated_text if segment.error is None
                                  else f"[翻译失败：{segment.error}]" for segment in group)
            blocks.extend((Formatter.clean(original), translated.strip()))
            group.clear()

        for segment in translation.segments:
            if not segment.original_text.strip():
                continue
            group.append(segment)
            if len(group) >= 4 or sum(len(item.original_text) for item in group) >= 600:
                flush()
        if group:
            flush()
        if not blocks:
            blocks.append(Formatter.clean(translation.original_text))
            if translation.error:
                blocks.append(f"[翻译失败：{translation.error}]")
        return "\n\n".join(blocks)

    @staticmethod
    def _subtitle_text(result: TranscriptionResult, *, vtt: bool) -> str:
        Exporter._validate_result(result)
        cues = []
        previous_start = -1.0
        for index, segment in enumerate(result.segments):
            # Blank payload lines would terminate a cue; preserve nonblank lines.
            payload = "\n".join(line.strip() for line in segment.text.splitlines() if line.strip())
            if not payload:
                continue
            start = Exporter.timestamp(segment.start, vtt=vtt)
            end = Exporter.timestamp(segment.end, vtt=vtt)
            if start == end:
                # Do not invent an end time for zero/sub-millisecond segments.
                logger.warning("Subtitle segment %d omitted: no positive millisecond duration", index)
                continue
            if segment.start < previous_start:
                raise ValueError("Subtitle segments must be ordered by start time")
            previous_start = segment.start
            if vtt:
                payload = escape(payload.replace("\x00", "\ufffd"), quote=False)
            cues.append(f"{len(cues) + 1}\n{start} --> {end}\n{payload}\n\n")
        return ("WEBVTT\n\n" if vtt else "") + "".join(cues)

    @staticmethod
    def save_srt(result: TranscriptionResult, path: Path):
        path.write_text(Exporter._subtitle_text(result, vtt=False), encoding="utf-8")

    @staticmethod
    def save_vtt(result: TranscriptionResult, path: Path):
        path.write_text(Exporter._subtitle_text(result, vtt=True), encoding="utf-8")

    @staticmethod
    def save_txt(text: str, path: Path):
        path.write_text(text, encoding="utf-8")

    @staticmethod
    def save_docx(text: str, path: Path):
        doc = Document()
        style = doc.styles["Normal"]
        style.font.name = "Calibri"
        style.font.size = Pt(11)
        style.paragraph_format.line_spacing = 1.15
        style.paragraph_format.space_after = Pt(8)
        for block in text.split("\n\n"):
            paragraph = doc.add_paragraph(block)
            paragraph.alignment = WD_PARAGRAPH_ALIGNMENT.LEFT
        doc.save(path)
