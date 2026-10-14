"""Compare V1 aliases and V2 retained DLLs byte-for-byte via SHA256."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
from build_support import CUDA_NAMES


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


if __name__ == "__main__":
    if Path(sys.prefix).name.lower() != "asr": raise SystemExit("Run in Conda asr")
    parser = argparse.ArgumentParser()
    for name in ("v1", "v2", "manifest", "report"): parser.add_argument(name, type=Path)
    args = parser.parse_args()
    rows = []
    for target, source, kind in json.loads(args.manifest.read_text(encoding="utf-8")):
        name = Path(target).name
        canonical = Path("cuda" if name in CUDA_NAMES else "torch/lib") / name
        old_copy = args.v1 / "_internal" / target
        old_kept = args.v1 / "_internal" / canonical
        new_kept = args.v2 / "_internal" / canonical
        hashes = [digest(p) for p in (old_copy, old_kept, new_kept)]
        assert len(set(hashes)) == 1, f"DLL contents differ: {target}"
        assert not (args.v2 / "_internal" / target).exists(), f"Duplicate remains: {target}"
        rows.append({"removed": target, "retained": canonical.as_posix(), "bytes": old_copy.stat().st_size, "sha256": hashes[0]})
    result = {"removed_bytes": sum(r["bytes"] for r in rows), "count": len(rows), "all_identical": True, "dlls": rows}
    args.report.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({k:v for k,v in result.items() if k != "dlls"}, indent=2))
