"""Read-only hardware probes. Import/invoke on a worker, never on the Tk thread."""
from dataclasses import asdict, dataclass
import ctypes
import logging
import platform
import subprocess

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class HardwareInfo:
    windows_version: str = ""
    cpu: str = ""
    ram_gb: float = 0
    nvidia_present: bool = False
    gpu_name: str = ""
    vram_gb: float = 0
    torch_cuda: bool | None = None  # Legacy diagnostic field; no longer probed.
    ct2_cuda_devices: int = 0
    cuda_compute_types: tuple = ()
    cpu_compute_types: tuple = ()
    errors: tuple = ()


def system_memory_gb():
    class MemoryStatus(ctypes.Structure):
        _fields_ = [("length", ctypes.c_ulong), ("load", ctypes.c_ulong)] + [
            (name, ctypes.c_ulonglong) for name in
            ("total", "available", "page_total", "page_available", "virtual_total", "virtual_available", "extended")]
    status = MemoryStatus()
    status.length = ctypes.sizeof(status)
    if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
        raise OSError("GlobalMemoryStatusEx failed")
    return status.total / 1024**3


def detect_hardware():
    values = dict(windows_version=platform.platform(), cpu=platform.processor())
    errors = []
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DESCRIPTION\System\CentralProcessor\0") as key:
            values["cpu"] = winreg.QueryValueEx(key, "ProcessorNameString")[0].strip()
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion") as key:
            build = winreg.QueryValueEx(key, "CurrentBuildNumber")[0]
            values["windows_version"] = f"Windows {'11' if int(build) >= 22000 else '10'} (build {build})"
    except (ImportError, OSError, ValueError):
        pass
    try:
        values["ram_gb"] = round(system_memory_gb(), 2)
    except Exception as error:
        errors.append(f"RAM: {error}")
    # nvidia-smi also detects a GPU when the Python CUDA runtime cannot initialize.
    try:
        result = subprocess.run(["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=5, check=True,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        name, memory = result.stdout.splitlines()[0].rsplit(",", 1)
        values.update(nvidia_present=True, gpu_name=name.strip(), vram_gb=round(float(memory) / 1024, 2))
    except Exception as error:
        errors.append(f"NVIDIA probe: {error}")
    try:
        import ctranslate2
        values["cpu_compute_types"] = tuple(sorted(ctranslate2.get_supported_compute_types("cpu")))
        values["ct2_cuda_devices"] = ctranslate2.get_cuda_device_count()
        if values["ct2_cuda_devices"]:
            values["cuda_compute_types"] = tuple(sorted(ctranslate2.get_supported_compute_types("cuda", 0)))
    except Exception as error:
        errors.append(f"CTranslate2: {error}")
    info = HardwareInfo(**values, errors=tuple(errors))
    logger.info("Hardware detected: %s", asdict(info))
    return info
