"""Real hardware + visible Tk smoke, optional short real file ASR. No mic test."""
import argparse
from dataclasses import asdict
from datetime import datetime
import json
import logging
from pathlib import Path
import sys
import time
import tkinter as tk

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from gui import DesktopApp
from gui_controller import ROOT


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-file", action="store_true")
    parser.add_argument("--auto-close", action="store_true")
    args = parser.parse_args()
    directory = ROOT / "validation/phase8" / datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    directory.mkdir(parents=True)
    logging.basicConfig(filename=directory / "smoke.log", level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s %(message)s")
    root = tk.Tk()
    app = DesktopApp(root, settings_path=directory / "preferences.json")
    app.output_dir.set(str(directory / "output"))
    ticks, report = [], {}
    phase = "hardware"
    def tick():
        nonlocal phase
        ticks.append(time.monotonic())
        if phase == "hardware" and app.runtime_ready and not app.documents.busy and app.controller.events.empty():
            info, registry, policy = app.controller.runtime
            report.update(hardware=asdict(info), registry=[asdict(m) for m in registry], recommendation=asdict(policy),
                          microphone_test=False, file_test=False)
            if args.run_file:
                app.add_files([ROOT / "validation/phase4-realtime/authored-sapi-fixture.wav"])
                app.start_files()
                phase = "file"
            else:
                phase = "done"
        elif phase == "file" and not app.controller.busy and not app.documents.busy and app.controller.events.empty():
            rows = [app.files.item(i, "values") for i in app.paths.values()]
            report.update(file_test=True, file_rows=rows, error=app.error.get(),
                          outputs=[str(p) for p in (directory / "output").glob("*")])
            phase = "done"
        if phase == "done":
            report.update(ui_tick_count=len(ticks), max_ui_tick_gap_seconds=max(b-a for a,b in zip(ticks,ticks[1:])),
                          file_page_exists=bool(app.file_page.winfo_exists()), realtime_page_exists=bool(app.live_page.winfo_exists()))
            (directory / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
            print(str(directory / "report.json"), flush=True)
            if args.auto_close:
                app.close()
            return
        root.after(50, tick)
    root.after(50, tick)
    root.mainloop()


if __name__ == "__main__":
    main()
