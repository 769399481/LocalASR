"""Explicit build boundaries; no changes to the active Conda environment."""
import hashlib
import os
from pathlib import Path
import zipfile

CPU_WHEEL_NAME = "torch-2.6.0+cpu-cp311-cp311-win_amd64.whl"
# Keep the full existing cuDNN family: its engines are dynamically selected.
# cuBLAS is required by CTranslate2; NVRTC/JitLink are retained conservatively
# for runtime-compiled cuDNN engines. No system NVIDIA driver is redistributed.
CUDA_NAMES = (
    "cublas64_12.dll", "cublasLt64_12.dll", "cudart64_12.dll",
    "cudnn64_9.dll", "cudnn_adv64_9.dll", "cudnn_cnn64_9.dll", "cudnn_graph64_9.dll",
    "cudnn_heuristic64_9.dll", "cudnn_ops64_9.dll", "cudnn_engines_precompiled64_9.dll",
    "cudnn_engines_runtime_compiled64_9.dll", "nvrtc64_120_0.dll",
    "nvrtc-builtins64_124.dll", "nvJitLink_120_0.dll", "zlibwapi.dll",
)


def prepare_cpu_torch(vendor):
    vendor = Path(vendor)
    wheel = vendor / CPU_WHEEL_NAME
    if not wheel.is_file():
        raise RuntimeError("Download the pinned official CPU wheel first; see docs/DEVELOPMENT.md")
    digest = hashlib.sha256(wheel.read_bytes()).hexdigest()
    stage = vendor / ("torch-cpu-" + digest[:12])
    marker = stage / ".complete"
    if not marker.is_file():
        stage.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(wheel) as archive:
            for name in archive.namelist():
                if not (stage / name).resolve().is_relative_to(stage.resolve()):
                    raise ValueError("Unsafe wheel member")
            archive.extractall(stage)
        marker.write_text(digest, encoding="ascii")
    if marker.read_text(encoding="ascii") != digest:
        raise RuntimeError("CPU wheel staging marker mismatch")
    return stage, digest


def cuda_binaries(torch_lib):
    torch_lib = Path(torch_lib)
    paths = [torch_lib / name for name in CUDA_NAMES]
    missing = [p.name for p in paths if not p.is_file()]
    if missing: raise RuntimeError("Missing explicit CUDA runtime: " + ", ".join(missing))
    return [(str(p), "cuda") for p in paths]


def generated_paths(root, variant):
    if variant not in ("full", "optimized"):
        raise ValueError("Unknown build variant")
    root = Path(root).resolve()
    work = (root / "build" / variant).resolve()
    output = (root / "dist" / ("LocalASR-" + variant.title())).resolve()
    if any(not p.is_relative_to(root) or p == root for p in (work, output)):
        raise RuntimeError("Unsafe generated build path")
    return work, output


def deduplicate_runtime_binaries(entries):
    """Remove only identical-source DLL aliases with an explicit search location.

    Distinct files with the same basename (e.g. CT2's own cuDNN/OpenMP) remain.
    The runtime hook registers cuda and torch/lib before application imports.
    """
    preferred = {}
    for destination, source, kind in entries:
        target = destination.replace("\\", "/").lower()
        if target.endswith(".dll") and (target.startswith("cuda/") or target.startswith("torch/lib/")):
            key = os.path.normcase(os.path.realpath(source))
            if key not in preferred or target.startswith("cuda/"):
                preferred[key] = destination
    kept, removed = [], []
    for item in entries:
        destination, source, kind = item
        key = os.path.normcase(os.path.realpath(source))
        if destination.lower().endswith(".dll") and key in preferred and destination != preferred[key]:
            removed.append(item)
        else:
            kept.append(item)
    return kept, removed
