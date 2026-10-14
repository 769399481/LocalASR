"""Opt-in real local translation check using authored text, NOT real ASR audio.

Run with Conda asr. No downloads or network requests are made by this script.
"""

import argparse
import ctypes
import json
from pathlib import Path
import sys
import tempfile
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from config import TRANSLATION_MODEL_PATH
from exporter import Exporter
from result import Segment, TranscriptionResult
from translation import TranslationOptions, TranslationService


def peak_working_set_mb():
    if sys.platform != "win32":
        return None
    from ctypes import wintypes

    class MemoryCounters(ctypes.Structure):
        _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD)] + [
            (name, ctypes.c_size_t) for name in (
                "PeakWorkingSetSize", "WorkingSetSize", "QuotaPeakPagedPoolUsage",
                "QuotaPagedPoolUsage", "QuotaPeakNonPagedPoolUsage", "QuotaNonPagedPoolUsage",
                "PagefileUsage", "PeakPagefileUsage")]

    counters = MemoryCounters()
    counters.cb = ctypes.sizeof(counters)
    current_process = ctypes.windll.kernel32.GetCurrentProcess
    current_process.restype = wintypes.HANDLE
    get_memory = ctypes.windll.psapi.GetProcessMemoryInfo
    get_memory.argtypes = [wintypes.HANDLE, ctypes.POINTER(MemoryCounters), wintypes.DWORD]
    if not get_memory(current_process(), ctypes.byref(counters), counters.cb):
        raise ctypes.WinError()
    return round(counters.PeakWorkingSetSize / 1024**2, 1)


def run(output_dir: Path, with_asr: bool):
    texts = ("Good morning, everyone.",
             "Today we are going to talk about hope and faith.",
             "Please open the document on your computer.",
             "This translation runs locally and does not upload your audio.",
             "Thank you for listening.")
    # Synthetic fixture times are used only to exercise export/alignment.
    original = TranscriptionResult("\n".join(texts), "en", 15.0,
                                   tuple(Segment(i * 3.0, (i + 1) * 3.0, text)
                                         for i, text in enumerate(texts)))
    options = TranslationOptions(enabled=True, model_path=TRANSLATION_MODEL_PATH)
    service = TranslationService(options)
    started = time.perf_counter()
    translated = service.translate(original, options.completion_key())
    elapsed = time.perf_counter() - started
    if not translated.complete:
        raise RuntimeError(f"Real translation failed: {translated.error}; "
                           f"segment errors: {[s.error for s in translated.segments]}")
    translated.validate_against(original)
    if not all(any('\u4e00' <= char <= '\u9fff' for char in seg.translated_text)
               for seg in translated.segments):
        raise AssertionError("Expected Chinese output for each English sample")
    Exporter.export("authored-text-sample", original, output_dir, translation=translated)
    assert Exporter.is_complete("authored-text-sample", output_dir,
                                translation_request=options.completion_key())
    assert next(service.translator.model.parameters()).device.type == "cpu"
    report = {"test_type": "real local text translation; synthetic timestamps; NOT audio ASR",
              "seconds_including_model_load": round(elapsed, 2),
              "peak_process_working_set_mb": peak_working_set_mb(),
              "translation_device": "cpu", "output_dir": str(output_dir.resolve()),
              "pairs": [{"en": segment.original_text, "zh": segment.translated_text}
                        for segment in translated.segments]}
    if with_asr:
        from transcriber import Transcriber
        engine = Transcriber()
        if engine.device != "cuda":
            raise AssertionError("Expected existing Whisper GPU configuration to remain available")
        report["whisper_model_load_with_translator_resident"] = f"{engine.device}/{engine.compute_type}"
    report_text = json.dumps(report, ensure_ascii=False, indent=2)
    (output_dir / "verification.json").write_text(report_text + "\n", encoding="utf-8")
    print(report_text)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--with-asr", action="store_true", help="Also load the existing Whisper GPU model")
    args = parser.parse_args()
    if args.output_dir:
        run(args.output_dir, args.with_asr)
    else:
        with tempfile.TemporaryDirectory(prefix="asr-real-translation-") as temporary:
            run(Path(temporary), args.with_asr)
