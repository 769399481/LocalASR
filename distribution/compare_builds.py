"""Render the recorded three-build size audit without touching any binaries."""
import json
from pathlib import Path
import sys

if __name__ == "__main__":
    if Path(sys.prefix).name.lower() != "asr": raise SystemExit("Run in Conda asr")
    root = Path(__file__).resolve().parents[1] / "validation/phase10"
    reports = [json.loads((root / name).read_text(encoding="utf-8-sig")) for name in
               ("baseline.json", "candidate-v1-size.json", "candidate-v2-size.json")]
    labels = ("Phase 9 stable", "Phase 10 v1", "Phase 10 v2")
    def component(report, key): return dict(report["top20_components"]).get("_internal/" + key, 0)
    rows = [("Total", [r["bytes"] for r in reports]),
            ("Main EXE", [r["exe_bytes"] for r in reports]),
            ("torch directory", [r["torch_bytes"] for r in reports]),
            ("CUDA DLLs across all directories", [r["cuda_dll_bytes"] for r in reports]),
            ("CTranslate2 directory", [component(r, "ctranslate2") for r in reports]),
            ("Transformers / Marian code", [component(r, "transformers") for r in reports]),
            ("Tcl/Tk", [r["tk_tcl_bytes"] for r in reports])]
    text = ["# Phase 10 size comparison", "", "Exact bytes; decimal GB = bytes / 1,000,000,000.", "",
            "CUDA DLL totals overlap the torch directory in stable/v1; do not add these rows together.", "",
            "| Component | " + " | ".join(labels) + " |", "|---|---:|---:|---:|"]
    text += ["| " + label + " | " + " | ".join(f"{n:,}" for n in values) + " |" for label, values in rows]
    saved = reports[0]["bytes"] - reports[2]["bytes"]
    text += ["", f"Stable → v2 reduction: **{saved:,} bytes ({saved / 1e9:.6f} GB, {100 * saved / reports[0]['bytes']:.2f}%)**.",
             f"V1 → v2 identical DLL copies removed: **{reports[1]['bytes'] - reports[2]['bytes']:,} bytes**.", ""]
    for label, report in zip(labels, reports):
        for field, title in (("top20_files", "largest files"), ("top20_components", "largest components/directories")):
            text += [f"## {label}: 20 {title}", "", "| Path | Bytes |", "|---|---:|"]
            text += [f"| `{name}` | {size:,} |" for name, size in report[field]]
            text.append("")
    (root / "SIZE_COMPARISON.md").write_text("\n".join(text), encoding="utf-8")
    print("Wrote", root / "SIZE_COMPARISON.md")
