from dataclasses import dataclass, field
import logging
from pathlib import Path
import time

from config import INPUT_DIR, OUTPUT_DIR, OUTPUT_FORMATS, SKIP_EXISTING, SUPPORTED_EXTENSIONS
from config import (TRANSLATION_ENABLED, TRANSLATION_SOURCE_LANGUAGE, TRANSLATION_TARGET_LANGUAGE,
                    TRANSLATION_BACKEND, TRANSLATION_MODEL_PATH)
from transcriber import Transcriber
from exporter import Exporter
from translation import TranslationOptions, TranslationService, create_translator

logger = logging.getLogger(__name__)


@dataclass
class BatchSummary:
    found: int = 0
    success: int = 0
    skipped: int = 0
    failed: int = 0
    failures: list[str] = field(default_factory=list)
    duration: float = 0.0
    translation_failed: int = 0

    @property
    def processed(self):
        return self.success + self.failed


class BatchProcessor:
    def __init__(self, input_dir=INPUT_DIR, output_dir=OUTPUT_DIR,
                 skip_existing=SKIP_EXISTING, transcriber_factory=Transcriber,
                 output_formats=OUTPUT_FORMATS, translation_options=None,
                 translator_factory=create_translator, transcription_request=None):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.skip_existing = skip_existing
        self.transcriber_factory = transcriber_factory
        self.transcriber = None
        self.transcription_request = transcription_request
        self.output_formats = Exporter.normalize_formats(output_formats)
        options = translation_options if translation_options is not None else TranslationOptions(
            TRANSLATION_ENABLED, TRANSLATION_SOURCE_LANGUAGE, TRANSLATION_TARGET_LANGUAGE,
            TRANSLATION_BACKEND, TRANSLATION_MODEL_PATH)
        self.translation_request = options.completion_key()
        self.translation_service = TranslationService(options, translator_factory) if options.enabled else None
        if options.enabled and "json" not in self.output_formats:
            # Always preserve the full original and aligned translation when enabled.
            self.output_formats += ("json",)

    def get_audio_files(self):
        if not self.input_dir.exists():
            logger.warning("Input directory does not exist: %s", self.input_dir)
            return []
        return sorted((p for p in self.input_dir.iterdir()
                       if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS),
                      key=lambda p: p.name.casefold())

    def run(self) -> BatchSummary:
        started = time.perf_counter()
        files = self.get_audio_files()
        summary = BatchSummary(found=len(files))
        pending = []
        for audio in files:
            name = Exporter.output_name(audio)
            if self.skip_existing and Exporter.is_complete(
                    name, self.output_dir, self.output_formats,
                    translation_request=self.translation_request, transcription_request=self.transcription_request):
                summary.skipped += 1
                logger.info("File skipped: %s", audio.name)
            else:
                pending.append((audio, name))
        if pending:
            try:
                if self.transcriber is None:
                    self.transcriber = self.transcriber_factory()
            except Exception:
                logger.exception("Model initialization failed")
                summary.failed = len(pending)
                summary.failures = [audio.name for audio, _ in pending]
                for audio, _ in pending:
                    logger.error("File failed (model unavailable): %s", audio.name)
            else:
                for audio, name in pending:
                    file_started = time.perf_counter()
                    translation_stage = False
                    logger.info("File started: %s", audio.name)
                    try:
                        result = self.transcriber.transcribe(audio)
                        # Commit an English checkpoint before touching the translator.
                        Exporter.export(name, result, self.output_dir, self.output_formats,
                                        translation_request=self.translation_request,
                                        transcription_request=self.transcription_request)
                        if self.translation_service is not None:
                            translation_stage = True
                            logger.info("Translation started: %s", audio.name)
                            translated = self.translation_service.translate(result, self.translation_request)
                            Exporter.export(name, result, self.output_dir, self.output_formats,
                                            translation=translated, transcription_request=self.transcription_request)
                            if not translated.complete:
                                summary.failed += 1
                                summary.translation_failed += 1
                                summary.failures.append(audio.name)
                                logger.error("Translation incomplete; original ASR preserved: %s; duration=%.2fs",
                                             audio.name, time.perf_counter() - file_started)
                                continue
                            logger.info("Translation completed: %s", audio.name)
                        summary.success += 1
                        logger.info("File completed: %s; duration=%.2fs", audio.name,
                                    time.perf_counter() - file_started)
                    except Exception:
                        summary.failed += 1
                        if translation_stage:
                            summary.translation_failed += 1
                        summary.failures.append(audio.name)
                        logger.exception("File failed: %s; duration=%.2fs", audio.name,
                                         time.perf_counter() - file_started)
        summary.duration = time.perf_counter() - started
        logger.info("Processing finished. Files found: %d; Processed: %d; Success: %d; "
                    "Skipped: %d; Failed: %d; duration=%.2fs", summary.found,
                    summary.processed, summary.success, summary.skipped, summary.failed,
                    summary.duration)
        if summary.failures:
            logger.error("Failed files: %s", ", ".join(summary.failures))
        if summary.translation_failed:
            logger.error("Translation failures with original ASR preserved: %d", summary.translation_failed)
        return summary
