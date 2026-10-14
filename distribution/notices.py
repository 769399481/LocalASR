"""Preserve installed dependency license files verbatim alongside an inventory."""
import importlib.metadata as metadata
import json
from pathlib import Path
import shutil
import sys

root = Path(__file__).resolve().parents[1]
destination = root / "distribution/third_party_licenses"
if destination.exists():
    if destination.resolve() != (root / "distribution/third_party_licenses").resolve() or not destination.resolve().is_relative_to(root):
        raise RuntimeError("Unsafe generated notices path")
    shutil.rmtree(destination)
destination.mkdir(parents=True, exist_ok=True)
python_license = Path(sys.prefix) / "LICENSE_PYTHON.txt"
if python_license.is_file():
    shutil.copy2(python_license, destination / python_license.name)
inventory = []
for dist in metadata.distributions():
    name = dist.metadata.get("Name", "unknown")
    copied = []
    for file in dist.files or ():
        # Basename matching avoids copying unrelated code such as
        # license_plate_detection_pipeline.py into legal notices.
        basename = Path(str(file)).name.lower()
        if basename.startswith(("license", "licence", "copying", "notice")) and not basename.endswith((".py", ".pyc", ".pyd", ".so", ".dll")) and dist.locate_file(file).is_file():
            if "test" in str(file).lower(): continue
            target = destination / name / Path(str(file)).name
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists(): target = target.with_name(str(len(copied)) + "-" + target.name)
            shutil.copy2(dist.locate_file(file), target)
            copied.append(str(target.relative_to(destination)))
    inventory.append({"component": name, "version": dist.version,
        "license": dist.metadata.get("License-Expression") or dist.metadata.get("License") or "See bundled license / upstream",
        "source": dist.metadata.get("Home-page") or dist.metadata.get("Project-URL") or "See distribution metadata",
        "license_files": copied})
(destination / "inventory.json").write_text(json.dumps(inventory, ensure_ascii=False, indent=2), encoding="utf-8")
