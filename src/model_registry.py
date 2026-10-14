"""Small offline catalog. Registry discovery never invokes a downloader."""
from dataclasses import dataclass
import json
import os
from pathlib import Path
from app_paths import PATHS

ROOT = PATHS.data


@dataclass(frozen=True)
class ModelEntry:
    id: str
    display_name: str
    path: str
    source: str
    approximate_size_gb: float
    intended_use: str
    installed: bool
    file_compatible: bool = True
    realtime_compatible: bool = True
    license: str = "MIT"


def valid_model(path):
    try:
        config = json.loads((path / "config.json").read_text(encoding="utf-8"))
        return ((path / "model.bin").stat().st_size > 0 and isinstance(config, dict)
                and (path / "tokenizer.json").is_file())
    except (OSError, ValueError):
        return False


def discover_models(root=ROOT, cache=None, overrides=None):
    cache = Path(cache or os.environ.get("HF_HUB_CACHE") or os.environ.get("HUGGINGFACE_HUB_CACHE")
                 or Path(os.environ.get("HF_HOME", Path.home() / ".cache/huggingface")) / "hub")
    entries = []
    for model_id, size, live in (("small", .484, True), ("large-v3", 3.09, False)):
        source = f"Systran/faster-whisper-{model_id}"
        candidates = [Path(root) / "models" / model_id]
        from model_download import CATALOG, validate_installed
        spec = CATALOG[model_id]
        managed = Path(root) / "models" / model_id / spec.revision
        if validate_installed(managed, spec):
            candidates.insert(0, managed)
        if overrides and overrides.get(model_id):
            candidates.insert(0, Path(overrides[model_id]))
        snapshots = cache / f"models--Systran--faster-whisper-{model_id}" / "snapshots"
        candidates.extend(sorted(snapshots.glob("*"), reverse=True))
        installed = next((p for p in candidates if valid_model(p)), None)
        entries.append(ModelEntry(model_id, f"Whisper {model_id}", str(installed or candidates[0]),
            source, size, "file + realtime" if live else "file", installed is not None,
            realtime_compatible=live))
    return tuple(entries)
