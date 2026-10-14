"""Summarize retained Phase 11 evidence; run in Conda asr."""
import csv
import json
import os
from pathlib import Path
import statistics
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from realtime_document import RealtimeDocument


def distribution(values):
    values = sorted(values)
    return {"min": min(values), "median": statistics.median(values),
            "p95": values[min(len(values)-1, int(len(values)*.95))], "max": max(values)}


def main():
    if Path(sys.prefix).name.lower() != "asr":
        raise RuntimeError("Use Conda asr")
    directory = ROOT / "validation/phase11/continuous-30min"
    report = json.loads((directory / "report.json").read_text(encoding="utf-8"))
    rows = list(csv.DictReader((directory / "process-samples.csv").open(encoding="utf-8-sig")))
    steady = [r for r in rows if int(r["processes"]) == 2]
    cpu = []
    for a, b in zip(steady, steady[1:]):
        elapsed = float(b["seconds"]) - float(a["seconds"])
        used = float(b["cpu_seconds"]) - float(a["cpu_seconds"])
        if elapsed > 0 and used >= 0:
            cpu.append(used / elapsed / os.cpu_count() * 100)
    memory = [int(r["working_set_bytes"]) for r in steady]
    private = [int(r["private_bytes"]) for r in steady]
    recovery = next((directory / "recovery").glob("*.json"))
    doc = RealtimeDocument.from_dict(json.loads(recovery.read_text(encoding="utf-8")))
    exported = json.loads(next(p for p in (directory / "output").glob("*.json")
                               if not p.name.endswith(".complete.json")).read_text(encoding="utf-8"))
    restored = RealtimeDocument.from_dict(exported)
    assert len(doc.segments) == len(restored.segments) == report["session_segments"]
    assert all(a.original_text == b.original_text and a.translated_text == b.translated_text
               and (a.start, a.end) == (b.start, b.end) for a,b in zip(doc.segments, restored.segments))
    summary = dict(runtime_seconds=report["capture_duration_seconds"], segments=len(doc.segments),
        passed=report["passed"], errors=report["errors"], metrics=report["metrics"],
        recovery_matches_export=True, sample_count=len(steady), resource_sampling_start=steady[0]["time"],
        resource_sampling_end=steady[-1]["time"], logical_cpus=os.cpu_count(),
        resource_note="Native Windows process-tree observer began about 150 seconds after capture start; excludes shutdown sample. Build and regression ran concurrently early in this test.",
        rss_bytes=dict(start=memory[0], end=memory[-1], peak=max(memory), minimum=min(memory)),
        private_bytes=dict(start=private[0], end=private[-1], peak=max(private)),
        cpu_machine_percent=distribution(cpu),
        english_latency=distribution([v["endpoint_latency_seconds"] for v in report["finals"]]),
        first_translation_seconds=report["translations"][0]["translation_latency_seconds"],
        translation_latency=distribution([v["translation_latency_seconds"] for v in report["translations"]]),
        warm_translation_latency=distribution([v["translation_latency_seconds"] for v in report["translations"][3:]]),
        end_to_end=distribution([v["end_to_end_latency_seconds"] for v in report["translations"]]))
    (ROOT / "validation/phase11/stability-summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
