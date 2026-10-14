"""Pure, conservative selection policy. See docs/development/PHASE8.md."""
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Selection:
    model_id: str
    model_path: str
    device: str
    compute_type: str
    reason: str = ""


@dataclass(frozen=True)
class Recommendations:
    file_modes: dict
    realtime_modes: dict
    file_default: str
    realtime_default: str
    message: str


def cpu_compute(types):
    return next((t for t in ("int8", "int8_float32", "float32") if t in types), "float32")


def recommend(info, registry):
    gpu_type = next((t for t in ("float16", "int8_float16", "int8")
                     if t in info.cuda_compute_types), None)
    gpu = bool(info.ct2_cuda_devices and gpu_type and info.vram_gb >= 2)
    reason = "" if gpu else "CTranslate2 CUDA unavailable or VRAM insufficient/unknown"
    device, compute = ("cuda", gpu_type) if gpu else ("cpu", cpu_compute(info.cpu_compute_types))
    files, live = {}, {}
    for model in registry:
        if not model.installed:
            continue
        # The large model benchmark is ~4.5 GB FP16. Reserve ~1 GiB headroom.
        large = model.id == "large-v3"
        if large and not (gpu and info.vram_gb >= 5.5 and info.ram_gb >= 8 and compute == "float16"):
            continue
        if not large and info.ram_gb and info.ram_gb < 4:
            continue
        selection = Selection(model.id, model.path, device, compute, reason)
        if model.file_compatible:
            files["Accurate" if large else "Fast"] = selection
        if model.realtime_compatible and not large:
            live["Balanced"] = selection
    message = "GPU acceleration enabled · GPU 加速已启用" if gpu else "Running on CPU — 实时识别可能较慢"
    if not files or not live:
        message += " · 缺少本地模型，请点击“首次设置 / 模型”下载"
    result = Recommendations(files, live, "Accurate" if "Accurate" in files else next(iter(files), ""),
        next(iter(live), ""), message)
    logger.info("Model recommendations: %s; fallback reason=%s", result, reason)
    return result


def inspect_runtime(settings=None):
    from hardware import detect_hardware
    from model_registry import discover_models
    overrides = {"large-v3": settings.file_model, "small": settings.realtime_model} if settings else None
    info = detect_hardware()
    registry = discover_models(overrides=overrides)
    return info, registry, recommend(info, registry)
