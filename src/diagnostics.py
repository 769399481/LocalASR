"""Allowlisted diagnostics: never serialize user input, transcripts or raw logs."""
from app_version import APP_NAME, APP_VERSION


def make_diagnostics(runtime=None, state="Idle", error_count=0):
    report = {"app": APP_NAME, "version": APP_VERSION, "state": state,
              "recent_errors": {"count": error_count, "summary": "Errors occurred; see local logs" if error_count else "No recorded errors"}}
    from audio_sources import capability
    cap = capability("system")
    report["system_audio"] = {"available": cap.available, "permission": cap.permission.value,
        "limitation": "部分受保护内容或特殊音频路径可能无法捕获。"}
    if runtime:
        hardware, registry, policy = runtime
        report["hardware"] = {key: getattr(hardware, key) for key in
            ("windows_version", "cpu", "ram_gb", "nvidia_present", "gpu_name", "vram_gb", "ct2_cuda_devices", "cuda_compute_types", "cpu_compute_types")}
        report["models"] = [{"id": model.id, "installed": model.installed} for model in registry]
        report["recommended"] = {"file": policy.file_default, "realtime": policy.realtime_default}
        report["device_modes"] = {kind: {quality: {"device": selection.device, "compute_type": selection.compute_type}
            for quality, selection in getattr(policy, kind + "_modes").items()} for kind in ("file", "realtime")}
        from app_paths import translation_model_available
        report["models"].append({"id": "opus-mt-en-zh", "installed": translation_model_available()})
    return report
