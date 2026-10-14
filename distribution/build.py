"""Run exclusively in Conda asr; no dependency installation during builds."""
from pathlib import Path
import argparse
import importlib.util
import json
import os
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from app_version import APP_VERSION
sys.path.insert(0, str(ROOT / "distribution"))
from build_support import prepare_cpu_torch, generated_paths


def validate_artifacts(output):
    output = Path(output)
    for name in ("LocalASR.exe", "_internal/python311.dll", "_internal/model_catalog.json", "_internal/torch/lib/torch_cpu.dll"):
        if not (output / name).is_file(): raise RuntimeError(f"Missing build artifact: {name}")
    if any(output.rglob("model.bin")) or any(output.rglob("pytorch_model.bin")):
        raise RuntimeError("Model weights must not be bundled")


def main():
    if Path(sys.prefix).name.lower() != "asr":
        raise SystemExit("Build must run in Conda asr")
    parser = argparse.ArgumentParser()
    parser.add_argument("--variant", choices=("full", "optimized"), default="optimized")
    parser.add_argument("--phase11", action="store_true", help="Build an isolated Phase 11 candidate; preserve accepted Phase 10")
    parser.add_argument("--phase12", action="store_true", help="Build isolated UI candidate; preserve Phase 10 and 11")
    parser.add_argument("--phase12-5", action="store_true", help="Build isolated visual candidate; preserve Phase 12")
    parser.add_argument("--phase12-6", action="store_true", help="Build isolated refinement candidate; preserve Phase 12.5")
    parser.add_argument("--phase14", action="store_true", help="Build license/metadata-only installer payload; preserve rollback builds")
    parser.add_argument("--phase15", action="store_true", help="Build isolated 0.1.0 release candidate with final project links")
    args = parser.parse_args()
    if sum((args.phase11, args.phase12, args.phase12_5, args.phase12_6, args.phase14, args.phase15)) > 1:
        parser.error("Choose one candidate phase")
    work, output = generated_paths(ROOT, args.variant)
    if args.phase11:
        work = ROOT / "build/phase11"
        output = ROOT / "dist/LocalASR-Phase11"
    if args.phase12:
        work = ROOT / "build/phase12"
        output = ROOT / "dist/LocalASR-Phase12"
    if args.phase12_5:
        work = ROOT / "build/phase12_5"
        output = ROOT / "dist/LocalASR-Phase12.5"
    if args.phase12_6:
        work = ROOT / "build/phase12_6"
        output = ROOT / "dist/LocalASR-Phase12.6"
    if args.phase14:
        work = ROOT / "build/phase14"
        output = ROOT / "dist/LocalASR-Phase14"
    if args.phase15:
        work = ROOT / "build/phase15"
        output = ROOT / "dist/LocalASR-Phase15"
    env = dict(os.environ, LOCALASR_BUILD_VARIANT=args.variant)
    env.update(LOCALASR_BUILD_WORK=str(work), LOCALASR_BUILD_NAME=output.name)
    provenance = {"variant": args.variant, "app_version": APP_VERSION}
    if args.variant == "optimized":
        # Locate the existing CUDA DLL source before shadowing torch for this build.
        torch_lib = Path(importlib.util.find_spec("torch").origin).parent / "lib"
        stage, digest = prepare_cpu_torch(ROOT / "distribution/vendor")
        env.update(PYTHONPATH=str(stage), LOCALASR_CPU_TORCH=str(stage), LOCALASR_CUDA_SOURCE=str(torch_lib))
        provenance.update(torch="2.6.0+cpu", cpu_wheel_sha256=digest, cuda_source="existing torch 2.6.0+cu124 runtime libraries")
        subprocess.run([sys.executable, "-c", "import torch; assert torch.__version__ == '2.6.0+cpu'; assert torch.version.cuda is None; print(torch.__file__)"], env=env, check=True)
    # The original Phase 9 dist/LocalASR is deliberately never a cleanup target.
    for path in (work, output):
        if not path.resolve().is_relative_to(ROOT.resolve()) or path.resolve() == ROOT.resolve():
            raise RuntimeError("Build cleanup outside workspace refused")
        if path.exists(): shutil.rmtree(path)
    work.mkdir(parents=True)
    (work / "version-number.txt").write_text(APP_VERSION)
    version = tuple(int(n) for n in APP_VERSION.split(".")) + (0,)
    (work / "version.txt").write_text(f"VSVersionInfo(ffi=FixedFileInfo(filevers={version},prodvers={version},mask=0x3f,flags=0x0,OS=0x40004,fileType=0x1,subtype=0x0,date=(0,0)),kids=[StringFileInfo([StringTable('040904B0',[StringStruct('FileDescription','LocalASR'),StringStruct('FileVersion','{APP_VERSION}'),StringStruct('ProductName','LocalASR'),StringStruct('ProductVersion','{APP_VERSION}')])]),VarFileInfo([VarStruct('Translation',[1033,1200])])])", encoding="utf-8")
    subprocess.run([sys.executable, str(ROOT / "distribution/notices.py")], env=env, check=True)
    subprocess.run([sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", "--workpath", str(work), str(ROOT / "distribution/LocalASR.spec")], cwd=ROOT, env=env, check=True)
    validate_artifacts(output)
    (output / "build-provenance.json").write_text(json.dumps(provenance, indent=2), encoding="utf-8")
    print(f"Standalone {APP_VERSION}: {output}")


if __name__ == "__main__": main()

