"""Dependency-boundary probe only; this is NOT a no-torch full application."""
import argparse
import importlib.abc
import importlib.util
import json
import os
from pathlib import Path
import sys


if __name__ == "__main__":
    if Path(sys.prefix).name.lower() != "asr": raise SystemExit("Run in Conda asr")
    parser = argparse.ArgumentParser()
    parser.add_argument("model")
    parser.add_argument("audio")
    parser.add_argument("report", type=Path)
    args = parser.parse_args()
    # Keep CT2's native runtime available, but prohibit importing torch Python.
    runtime = Path(importlib.util.find_spec("torch").origin).parent / "lib"
    dll_handle = os.add_dll_directory(str(runtime))
    os.environ["PATH"] = str(runtime) + os.pathsep + os.environ.get("PATH", "")
    class NoTorch(importlib.abc.MetaPathFinder):
        def find_spec(self, fullname, path=None, target=None):
            if fullname == "torch" or fullname.startswith("torch."):
                raise ModuleNotFoundError("Torch intentionally unavailable in ASR audit")
    sys.meta_path.insert(0, NoTorch())
    from faster_whisper import WhisperModel
    model = WhisperModel(args.model, device="cuda", compute_type="float16", local_files_only=True)
    segments, info = model.transcribe(args.audio, language="en", vad_filter=True)
    result = {"torch_imported": any(n == "torch" or n.startswith("torch.") for n in sys.modules),
        "device": "cuda", "language": info.language, "text": " ".join(s.text.strip() for s in segments)}
    args.report.write_text(json.dumps(result, indent=2), encoding="utf-8")
    assert not result["torch_imported"] and result["text"]
    print("CT2 GPU ASR completed with torch Python imports blocked")
