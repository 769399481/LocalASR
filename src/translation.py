"""Segment-aligned translation, independent of Whisper and document exporters."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
import logging
from pathlib import Path
from typing import Callable

from result import TranscriptionResult

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class TranslationOptions:
    enabled: bool = False
    source_language: str = "en"
    target_language: str = "zh-Hans"
    backend: str = "marian_local"
    model_path: Path = Path("models/opus-mt-en-zh")

    def completion_key(self):
        if not self.enabled:
            return None
        revision_file = Path(self.model_path) / "REVISION"
        try:
            revision = revision_file.read_text(encoding="utf-8").strip() if revision_file.is_file() else "unversioned"
        except OSError:
            revision = "unreadable"
        return {"source_language": self.source_language,
                "target_language": self.target_language, "backend": self.backend,
                "model_path": str(Path(self.model_path).resolve()),
                "revision": revision}


@dataclass(frozen=True)
class TranslatedSegment:
    start: float
    end: float
    original_text: str
    translated_text: str | None
    error: str | None = None


@dataclass(frozen=True)
class TranslationResult:
    source_language: str
    target_language: str
    original_text: str
    translated_text: str
    segments: tuple[TranslatedSegment, ...]
    request: dict
    error: str | None = None

    @property
    def complete(self) -> bool:
        return self.error is None and all(segment.error is None for segment in self.segments)

    def validate_against(self, original: TranscriptionResult):
        if (self.original_text != original.text or self.source_language != original.language
                or len(self.segments) != len(original.segments)):
            raise ValueError("Translation does not match the original transcription")
        for source, translated in zip(original.segments, self.segments):
            if (source.start, source.end, source.text) != (
                    translated.start, translated.end, translated.original_text):
                raise ValueError("Translation segment alignment mismatch")
            if translated.error is None and source.text.strip() and not translated.translated_text:
                raise ValueError("A successful nonempty segment must have translated text")


class Translator(ABC):
    """Provider adapters implement text translation only; no audio access."""

    @abstractmethod
    def translate(self, text: str, source_language: str, target_language: str) -> str:
        raise NotImplementedError


class MarianLocalTranslator(Translator):
    """Offline CPU-only MarianMT. Dependencies load only when translation is used."""

    def __init__(self, model_path: Path):
        model_path = Path(model_path)
        required = ("config.json", "pytorch_model.bin", "source.spm", "target.spm", "vocab.json")
        if not all((model_path / name).is_file() for name in required):
            raise FileNotFoundError("Local Marian translation model is unavailable")
        import torch
        from opencc import OpenCC
        from transformers import MarianMTModel, MarianTokenizer

        self.torch = torch
        self.tokenizer = MarianTokenizer.from_pretrained(str(model_path), local_files_only=True)
        self.model = MarianMTModel.from_pretrained(str(model_path), local_files_only=True).to("cpu").eval()
        self.simplify = OpenCC("t2s")
        self.prefix_ids = self.tokenizer.encode(">>cmn_Hans<<", add_special_tokens=False)
        if ">>cmn_Hans<<" not in self.tokenizer.get_vocab():
            raise ValueError("Model does not support Simplified Mandarin target prefix")
        self.max_positions = int(self.model.config.max_position_embeddings)
        logger.info("Local translator loaded on CPU; no translation VRAM allocation")

    def translate(self, text: str, source_language: str, target_language: str) -> str:
        if (source_language, target_language) != ("en", "zh-Hans"):
            raise ValueError("This local model supports en -> zh-Hans only")
        if not text.strip():
            return ""
        tokens = self.tokenizer.encode(text, add_special_tokens=False)
        chunk_size = min(256, self.max_positions - len(self.prefix_ids) - 1)
        translated = []
        # Split long segments internally; never truncate the input or alter its
        # externally visible segment index/timestamps.
        with self.torch.inference_mode():
            for offset in range(0, len(tokens), chunk_size):
                ids = self.prefix_ids + tokens[offset:offset + chunk_size] + [self.tokenizer.eos_token_id]
                inputs = self.torch.tensor([ids], dtype=self.torch.long, device="cpu")
                output = self.model.generate(input_ids=inputs,
                                             attention_mask=self.torch.ones_like(inputs),
                                             num_beams=4, max_length=self.max_positions)
                if len(output[0]) >= self.max_positions:
                    raise RuntimeError("Translation reached the output token limit")
                decoded = self.tokenizer.decode(output[0], skip_special_tokens=True).strip()
                if not decoded:
                    raise RuntimeError("Translator returned empty output")
                translated.append(decoded)
        return self.simplify.convert("".join(translated))


def create_translator(options: TranslationOptions) -> Translator:
    if options.backend != "marian_local":
        raise ValueError("Unsupported translation backend")
    if (options.source_language, options.target_language) != ("en", "zh-Hans"):
        raise ValueError("This local backend supports en -> zh-Hans only")
    return MarianLocalTranslator(options.model_path)


class TranslationService:
    def __init__(self, options: TranslationOptions,
                 factory: Callable[[TranslationOptions], Translator] = create_translator):
        self.options = options
        self.factory = factory
        self.translator = None
        self.initialization_error = None

    def translate(self, original: TranscriptionResult, request: dict) -> TranslationResult:
        if not self.options.enabled:
            raise ValueError("Translation is disabled")
        global_error = None
        has_text = any(segment.text.strip() for segment in original.segments)
        if original.text.strip() and not has_text:
            global_error = "missing_source_segments"
        elif has_text and original.language != self.options.source_language:
            global_error = "source_language_mismatch"
        elif has_text:
            if self.translator is None and self.initialization_error is None:
                try:
                    self.translator = self.factory(self.options)
                except Exception as error:
                    self.initialization_error = f"translator_unavailable:{type(error).__name__}"
                    # Error messages from future providers can contain private text
                    # or credentials. Record the exception type, not their payload.
                    logger.error("Translator initialization failed: %s", type(error).__name__)
            global_error = self.initialization_error
        translated_segments = []
        for index, segment in enumerate(original.segments):
            error_code = global_error if segment.text.strip() else None
            translated = "" if not segment.text.strip() else None
            if segment.text.strip() and error_code is None:
                try:
                    translated = self.translator.translate(segment.text, original.language,
                                                           self.options.target_language)
                    if not isinstance(translated, str) or not translated.strip():
                        raise ValueError("Empty translation for nonempty input")
                except Exception as error:
                    error_code = f"segment_translation_failed:{type(error).__name__}"
                    translated = None
                    logger.warning("Translation segment %d failed: %s", index, type(error).__name__)
            translated_segments.append(TranslatedSegment(
                segment.start, segment.end, segment.text, translated, error_code))
        return TranslationResult(
            original.language, self.options.target_language, original.text,
            "\n".join(segment.translated_text or "" for segment in translated_segments),
            tuple(translated_segments), request, global_error)
