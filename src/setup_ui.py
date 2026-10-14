from ui_theme import COLORS, SPACE, TYPE, CONTROL
from ui_strings import tr
"""Short first-run panel, backed by the existing detector and recommendation policy."""
from dataclasses import replace
import json
import tkinter as tk
from tkinter import ttk, filedialog
from app_paths import PATHS, translation_model_available
from app_version import APP_NAME, APP_VERSION
from diagnostics import make_diagnostics
from model_download import CATALOG, ModelDownloader, DownloadCancelled, DownloadError
from recommendation import recommend
from ui_support import model_name
from ui_errors import error_message

class SetupDialog:

    def __init__(self, app, translation=False):
        self.app = app
        self.window = tk.Toplevel(app.root)
        self.window.title(tr('ui_007'))
        self.window.geometry('620x430')
        self.window.transient(app.root)
        self.window.protocol('WM_DELETE_WINDOW', self.close)
        body = ttk.Frame(self.window, padding=SPACE['l'])
        body.pack(fill='both', expand=True)
        ttk.Label(body, text=tr('ui_142'), font=('Segoe UI', 15, 'bold')).pack(anchor='w')
        ttk.Label(body, text=tr('ui_143'), wraplength=570).pack(anchor='w', pady=SPACE['s'])
        info, registry, policy = app.controller.runtime
        possible = recommend(info, [replace(m, installed=True) for m in registry])
        best = possible.file_default == 'Accurate'
        ttk.Label(body, text=tr('ui_144', arg0=tr('ui_016') if best else tr('ui_014'))).pack(anchor='w', pady=SPACE['xs'])
        installed = {m.id: m.installed for m in registry}
        installed['opus-mt-en-zh'] = translation_model_available()
        self.choices = {}
        self.checks = []
        for model_id, spec in CATALOG.items():
            default = model_id == 'small' or (model_id == 'large-v3' and best)
            if translation:
                default = model_id == 'opus-mt-en-zh'
            var = tk.BooleanVar(value=default and (not installed[model_id]))
            label = f'{model_name(model_id)} · {spec.size / 1000000000.0:.2f} GB' + (tr('ui_145') if installed[model_id] else '')
            check = ttk.Checkbutton(body, text=label, variable=var)
            check.pack(anchor='w', pady=SPACE['xs'])
            if installed[model_id]:
                check.state(['disabled'])
            self.choices[model_id] = var
            self.checks.append(check)
        self.status = tk.StringVar(value=tr('ui_146'))
        ttk.Label(body, textvariable=self.status, wraplength=570).pack(anchor='w', pady=SPACE['s'])
        self.progress = ttk.Progressbar(body, maximum=100)
        self.progress.pack(fill='x')
        row = ttk.Frame(body)
        row.pack(fill='x', pady=SPACE['m'])
        self.download = ttk.Button(row, text=tr('ui_147'), command=self.start)
        self.download.pack(side='left', padx=SPACE['xs'])
        ttk.Button(row, text=tr('ui_148'), command=app.controller.stop).pack(side='left', padx=SPACE['xs'])
        ttk.Button(row, text=tr('ui_149'), command=self.close).pack(side='right')

    def start(self):
        if self.app.controller.busy:
            return
        selected = [CATALOG[k] for k, v in self.choices.items() if v.get()]
        if not selected:
            self.status.set(tr('ui_150'))
            return
        self.download.state(['disabled'])
        self.status.set(tr('ui_151'))

        def work():
            try:
                downloader = ModelDownloader(PATHS.models, PATHS.downloads)
                for spec in selected:
                    downloader.download(spec, self.app.controller.stop_requested, lambda value: self.app.controller.post('download_progress', value))
            except (DownloadError, DownloadCancelled) as error:
                self.app.controller.post('download_progress', ('', 0, tr('ui_152') if isinstance(error, DownloadCancelled) else error_message(error, 'download')))
            finally:
                self.app.controller.post('download_finished', None)
        self.app.controller._launch(work)

    def update(self, value):
        model_id, percent, status = value
        prefix = model_name(model_id) + ' · ' if model_id else ''
        self.status.set(prefix + status + (f' · {CATALOG[model_id].size * percent / 100 / 1000000.0:.1f} / {CATALOG[model_id].size / 1000000.0:.1f} MB' if model_id else ''))
        self.progress.configure(value=percent)

    def close(self):
        if self.app.controller.busy:
            self.app.controller.stop()
            self.status.set(tr('ui_153'))
            return
        self.app.setup_completed = True
        self.app.save_settings()
        self.window.destroy()
        self.app.setup_dialog = None

def show_diagnostics(app):
    window = tk.Toplevel(app.root)
    window.title(tr('ui_154', arg0=APP_NAME, arg1=APP_VERSION))
    report = make_diagnostics(app.controller.runtime, app.controller.state, app.error_count)
    report['chosen_quality'] = {'file': app.file_quality.get(), 'realtime': app.realtime_quality.get()}
    content = json.dumps(report, ensure_ascii=False, indent=2)
    ttk.Label(window, text=tr('ui_155', arg0=APP_NAME, arg1=APP_VERSION), padding=SPACE['m']).pack()
    from tkinter.scrolledtext import ScrolledText
    text = ScrolledText(window, width=75, height=20)
    text.pack(fill='both', expand=True)
    text.insert('1.0', content)
    text.configure(state='disabled')

    def copy():
        window.clipboard_clear()
        window.clipboard_append(content)

    def save():
        path = filedialog.asksaveasfilename(parent=window, defaultextension='.json', initialfile='LocalASR-diagnostics.json')
        if path:
            from pathlib import Path
            app.documents.submit(lambda: Path(path).write_text(content, encoding='utf-8'))
    ttk.Button(window, text=tr('ui_156'), command=copy).pack(side='left', padx=SPACE['m'], pady=SPACE['s'])
    ttk.Button(window, text=tr('ui_157'), command=save).pack(side='left')

def show_about(app):
    window = tk.Toplevel(app.root)
    window.title(tr('ui_158'))
    window.transient(app.root)
    body = ttk.Frame(window, padding=SPACE['l'])
    body.pack(fill='both', expand=True)
    ttk.Label(body, text=f'{APP_NAME} {APP_VERSION}').pack(anchor='w')
    ttk.Label(body, text=tr('ui_159'), wraplength=480).pack(anchor='w', pady=SPACE['m'])
    ttk.Button(body, text=tr('ui_160'), command=lambda: show_diagnostics(app)).pack(side='left')
    ttk.Button(body, text=tr('ui_046'), command=app.show_shortcuts).pack(side='left', padx=SPACE['s'])
    ttk.Button(body, text=tr('ui_060'), command=window.destroy).pack(side='right')
