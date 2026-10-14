import os
import sys
from pathlib import Path

if getattr(sys, "frozen", False):
    _dll_handles = []
    for folder in (Path(sys._MEIPASS), Path(sys._MEIPASS) / "torch/lib", Path(sys._MEIPASS) / "cuda"):
        if folder.is_dir():
            _dll_handles.append(os.add_dll_directory(str(folder)))
            os.environ["PATH"] = str(folder) + os.pathsep + os.environ.get("PATH", "")
