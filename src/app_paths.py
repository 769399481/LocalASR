"""Separate immutable application resources from per-user writable data."""
from dataclasses import dataclass
import os
from pathlib import Path
import sys


@dataclass(frozen=True)
class AppPaths:
    application: Path
    data: Path
    output: Path

    @property
    def config(self): return self.data / "gui_settings.json"
    @property
    def logs(self): return self.data / "logs"
    @property
    def recovery(self): return self.data / "recovery"
    @property
    def models(self): return self.data / "models"
    @property
    def downloads(self): return self.data / "downloads"
    @property
    def cache(self): return self.data / "cache"


def resolve_paths(*, frozen=None, environment=None, home=None, application=None):
    env = os.environ if environment is None else environment
    home = Path(home or Path.home())
    frozen = getattr(sys, "frozen", False) if frozen is None else frozen
    app = Path(application or (Path(sys.executable).parent if frozen else Path(__file__).resolve().parents[1]))
    data = Path(env["LOCALASR_DATA_DIR"]) if env.get("LOCALASR_DATA_DIR") else (
        Path(env.get("LOCALAPPDATA", home / "AppData/Local")) / "LocalASR" if frozen else app)
    return AppPaths(app, data, data / "output")


PATHS = resolve_paths()


def translation_model_path():
    # Import lazily so path setup itself never probes the network or loads ML.
    from model_download import CATALOG, validate_installed
    spec = CATALOG["opus-mt-en-zh"]
    managed = PATHS.models / spec.id / spec.revision
    if validate_installed(managed, spec):
        return managed
    legacy = PATHS.models / spec.id
    required = ("config.json", "pytorch_model.bin", "source.spm", "target.spm", "vocab.json")
    if all((legacy / f).is_file() for f in required):
        return legacy
    return managed


def translation_model_available():
    path = translation_model_path()
    from model_download import CATALOG, validate_installed
    if path.name == CATALOG["opus-mt-en-zh"].revision:
        return validate_installed(path, CATALOG["opus-mt-en-zh"])
    return all((path / name).is_file() and (path / name).stat().st_size > 0 for name in
               ("config.json", "pytorch_model.bin", "source.spm", "target.spm", "vocab.json"))
