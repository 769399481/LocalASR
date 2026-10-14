from pathlib import Path
import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs, copy_metadata

root = Path(SPECPATH).parent
variant = os.environ.get("LOCALASR_BUILD_VARIANT", "full")
work = Path(os.environ.get("LOCALASR_BUILD_WORK", str(root / "build" / variant)))
optimized = variant == "optimized"
if optimized:
    sys.path.insert(0, os.environ["LOCALASR_CPU_TORCH"])
sys.path.insert(0, str(root / "src"))
sys.path.insert(0, str(root / "distribution"))
from app_version import APP_VERSION
datas = [(str(root / "src/model_catalog.json"), "."), (str(root / "THIRD_PARTY_NOTICES.md"), ".")]
binaries = []
if optimized:
    from build_support import cuda_binaries
    binaries += cuda_binaries(os.environ["LOCALASR_CUDA_SOURCE"])
for package in ("faster_whisper", "ctranslate2", "opencc", "sacremoses", "sentencepiece", "pyaudiowpatch"):
    datas += collect_data_files(package)
    binaries += collect_dynamic_libs(package)
for package in ("faster-whisper", "ctranslate2", "sounddevice", "webrtcvad-wheels", "python-docx", "opencc-python-reimplemented", "PyAudioWPatch"):
    datas += copy_metadata(package)
datas += collect_data_files("tkinterdnd2")
datas += copy_metadata("tkinterdnd2")
licenses = root / "distribution/third_party_licenses"
if licenses.exists(): datas.append((str(licenses), "third_party_licenses"))
unused = ["librosa", "numba", "llvmlite"] if optimized else []
a = Analysis([str(root / "src/desktop_entry.py")], pathex=[str(root / "src")], binaries=binaries, datas=datas,
    hiddenimports=["packaged_check", "_sounddevice_data", "_webrtcvad", "sounddevice", "sentencepiece", "opencc", "sacremoses"],
    hookspath=[str(root / "distribution/hooks")], runtime_hooks=[str(root / "distribution/runtime_hook.py")],
    excludes=["IPython", "jupyter", "pytest", "matplotlib", "pandas", "tensorflow", "jax", "torchaudio", "torchvision", "cv2", "sklearn"] + unused,
    noarchive=False)
if optimized:
    from build_support import deduplicate_runtime_binaries
    import json
    a.binaries, duplicates = deduplicate_runtime_binaries(a.binaries)
    (work / "deduplicated-dlls.json").write_text(json.dumps(duplicates, indent=2), encoding="utf-8")
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name="LocalASR", debug=False,
          bootloader_ignore_signals=False, strip=False, upx=False, console=False,
          version=str(work / "version.txt"))
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False,
               name=os.environ.get("LOCALASR_BUILD_NAME", "LocalASR-" + variant.title()))
