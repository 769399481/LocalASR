"""Repeatable size/import/PE audit; run in Conda asr, never modify the build."""
import argparse
import ast
import importlib.metadata as metadata
import json
from pathlib import Path
import sys


def audit(build):
    build = Path(build).resolve()
    files = [(p.relative_to(build).as_posix(), p.stat().st_size) for p in build.rglob("*") if p.is_file()]
    groups = {}
    for name, size in files:
        parts = name.split("/")
        key = "/".join(parts[:2]) if parts[0] == "_internal" else parts[0]
        groups[key] = groups.get(key, 0) + size
    cuda_prefixes = ("cublas", "cudnn", "cudart", "cufft", "curand", "cusolver", "cusparse", "cupti", "nvrtc", "nvjit", "nvtools")
    cuda = [(n, s) for n, s in files if Path(n).name.lower().startswith(cuda_prefixes) and n.endswith(".dll")]
    root = Path(__file__).resolve().parents[1]
    imports = {}
    for source in (root / "src").glob("*.py"):
        imports[source.name] = sorted({n.module or "" for n in ast.walk(ast.parse(source.read_text(encoding="utf-8-sig"))) if isinstance(n, ast.ImportFrom)} |
            {a.name for n in ast.walk(ast.parse(source.read_text(encoding="utf-8-sig"))) if isinstance(n, ast.Import) for a in n.names})
    dependencies = {}
    for name in ("torch", "transformers", "faster-whisper", "ctranslate2", "sentencepiece", "opencc-python-reimplemented"):
        dist = metadata.distribution(name)
        dependencies[name] = {"version": dist.version, "requires": dist.requires}
    import pefile
    native = {}
    for directory in (build / "_internal/torch/lib", build / "_internal/ctranslate2", build / "_internal/cuda"):
        for path in directory.glob("*.dll"):
            with pefile.PE(str(path), fast_load=True) as pe:
                pe.parse_data_directories(directories=[pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_IMPORT"], pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_DELAY_IMPORT"]])
                native[path.relative_to(build).as_posix()] = sorted({entry.dll.decode() for table in ("DIRECTORY_ENTRY_IMPORT", "DIRECTORY_ENTRY_DELAY_IMPORT") for entry in getattr(pe, table, [])})
    return {"build": str(build), "bytes": sum(s for _, s in files), "file_count": len(files),
        "exe_bytes": (build / "LocalASR.exe").stat().st_size,
        "torch_bytes": sum(s for n, s in files if n.startswith("_internal/torch/")),
        "cuda_dll_bytes": sum(s for _, s in cuda), "cuda_dlls": sorted(cuda, key=lambda p:p[1], reverse=True),
        "tk_tcl_bytes": sum(s for n, s in files if any(t in n.lower() for t in ("_tcl_data/", "_tk_data/", "tcl86", "tk86", "_tkinter"))),
        "top20_files": sorted(files, key=lambda p:p[1], reverse=True)[:20],
        "top20_components": sorted(groups.items(), key=lambda p:p[1], reverse=True)[:20],
        "source_import_graph": imports, "build_environment_dependencies": dependencies, "pe_imports": native}


if __name__ == "__main__":
    if Path(sys.prefix).name.lower() != "asr": raise SystemExit("Run in Conda asr")
    parser = argparse.ArgumentParser()
    parser.add_argument("build", type=Path)
    parser.add_argument("report", type=Path)
    args = parser.parse_args()
    args.report.parent.mkdir(parents=True, exist_ok=True)
    result = audit(args.build)
    args.report.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k:result[k] for k in ("bytes", "exe_bytes", "torch_bytes", "cuda_dll_bytes", "tk_tcl_bytes", "top20_components")}, indent=2))
