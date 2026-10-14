from ui_theme import COLORS, SPACE, TYPE, CONTROL
from ui_strings import tr
"""Tk desktop UI. All Core work and model imports live outside the Tk thread."""
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import time
from tkinter.scrolledtext import ScrolledText
from gui_controller import Controller, ROOT, Settings, friendly_error
from realtime_document import DocumentStore
from app_paths import PATHS, translation_model_available
from app_version import APP_NAME, APP_VERSION
from ui_support import ChoiceBox, apply_theme, create_root, install_drop, file_state
from ui_errors import error_message
from dataclasses import asdict
from subtitle_overlay import SubtitleOverlay, OverlayPreferences
from desktop_platform import DesktopPlatform
logger = logging.getLogger(__name__)
LANGUAGES = {'English': 'en', 'Chinese': 'zh', 'Auto': 'auto'}

class DesktopApp:

    def __init__(self, root, *, controller=None, settings_path=None):
        self.root = root
        self.controller = controller or Controller()
        self.settings_path = Path(settings_path or PATHS.config)
        self.offer_setup = settings_path is None
        self.setup_dialog = None
        self.error_count = 0
        self.documents = DocumentStore(self.settings_path.parent / 'recovery', self.controller.post)
        self.controller.documents = self.documents
        self.export_waiting = False
        self.closing = False
        self.paths = {}
        self.durations = {}
        self.task_started = None
        self.session_id = None
        self.live_requested = False
        self.last_final = 0
        self.device_ids = {'Default microphone': None}
        self.runtime_ready = False
        self.policy = None
        load_error = ''
        try:
            settings = Settings.load(self.settings_path)
        except Exception:
            logger.exception('Cannot read GUI settings')
            settings = Settings()
            load_error = tr('ui_001')
        self.file_model = tk.StringVar(value=settings.file_model)
        self.setup_completed = settings.setup_completed
        self.realtime_model = tk.StringVar(value=settings.realtime_model)
        self.file_quality = tk.StringVar(value=settings.file_quality or 'Auto')
        self.realtime_quality = tk.StringVar(value=settings.realtime_quality or 'Auto')
        self.acceleration = tk.StringVar(value=tr('ui_002'))
        self.output_dir = tk.StringVar(value=settings.output_dir)
        self.language = tk.StringVar(value=next((k for k, v in LANGUAGES.items() if v == settings.language)))
        self.translation = tk.BooleanVar(value=settings.translation)
        self.formats = {fmt: tk.BooleanVar(value=fmt in settings.formats) for fmt in ('txt', 'docx', 'json', 'srt', 'vtt')}
        self.status = tk.StringVar(value=tr('ui_003'))
        self.error = tk.StringVar(value=load_error)
        self.partial = tk.StringVar()
        self.translation_status = tk.StringVar(value=tr('translation_ready') if settings.translation else tr('ui_004'))
        self.progress_text = tk.StringVar(value='0 / 0')
        self.elapsed = tk.StringVar()
        self.device = tk.StringVar(value=settings.microphone)
        if settings.microphone != 'Default microphone':
            self.device_ids[settings.microphone] = settings.microphone.split(': ', 1)[-1]
        self.actions = []
        self.audio_source = tk.StringVar(value='System Audio' if settings.audio_source == 'system' else 'Microphone')
        self.system_audio_status = tk.StringVar(value=tr('ui_005'))
        self.overlay = SubtitleOverlay(root, OverlayPreferences(**settings.overlay or {}))
        self.overlay_visible = tk.BooleanVar(value=False)
        self.subtitle_mode = tk.StringVar(value=self.overlay.preferences.mode)
        self.overlay.translation_enabled = settings.translation
        self.hotkeys = DesktopPlatform()
        self.hotkeys_enabled = tk.BooleanVar(value=settings.global_hotkeys)
        root.title(APP_NAME)
        root.geometry('1080x760')
        root.minsize(880, 600)
        root.protocol('WM_DELETE_WINDOW', self.close)
        root.report_callback_exception = self.callback_error
        apply_theme(root)
        outer = ttk.Frame(root, padding=SPACE['m'])
        outer.pack(fill='both', expand=True)
        header = ttk.Frame(outer)
        header.pack(fill='x', pady=(0, SPACE['s']))
        ttk.Label(header, text=APP_NAME, font=('Microsoft YaHei UI', TYPE['title'], 'bold')).pack(side='left')
        ttk.Button(header, text=tr('ui_006'), command=lambda: self.guard(self.diagnostics)).pack(side='right')
        self.button(header, tr('ui_007'), self.open_setup)
        footer = ttk.Frame(outer)
        self.footer = footer
        footer.pack(side='bottom', fill='x')
        self.activity = ttk.Progressbar(footer, mode='indeterminate', length=100)
        self.activity_running = False
        self.tabs = ttk.Notebook(outer)
        self.tabs.pack(fill='both', expand=True)
        self.file_page = ttk.Frame(self.tabs, padding=SPACE['m'])
        self.live_page = ttk.Frame(self.tabs, padding=SPACE['m'])
        for frame, name in ((self.file_page, tr('ui_009')), (self.live_page, tr('ui_010'))):
            self.tabs.add(frame, text=name)
        self.build_file()
        self.build_live()
        self.configure_hotkeys()
        ttk.Separator(footer).pack(fill='x', pady=SPACE['s'])
        ttk.Label(footer, textvariable=self.acceleration, wraplength=980).pack(anchor='w')
        ttk.Label(footer, textvariable=self.status, wraplength=980).pack(anchor='w')
        ttk.Label(footer, textvariable=self.error, foreground=COLORS['error'], wraplength=980).pack(anchor='w')
        self.translation.trace_add('write', lambda *_: self.show_translation())
        self.show_translation()
        self.timer = root.after(50, self.poll)

        def find_recovery():
            paths = sorted(self.documents.directory.glob('*.json'), key=lambda p: p.stat().st_mtime, reverse=True)
            if paths:
                self.controller.post('recovery_available', len(paths))
        self.documents.submit(find_recovery)
        self.documents.submit(lambda: self.controller.initialize_runtime(settings))
        self.sync_controls()

    def button(self, parent, text, command, *, track=True, style='TButton'):
        button = ttk.Button(parent, text=text, style=style, command=lambda: self.guard(command))
        button.pack(side='left', padx=(0, SPACE['s']))
        if track:
            self.actions.append(button)
        return button

    def formats_row(self, parent):
        row = ttk.Frame(parent)
        row.pack(fill='x', pady=SPACE['xs'])
        ttk.Label(row, text=tr('ui_011'), style='Form.TLabel').pack(side='left')
        for fmt, value in self.formats.items():
            ttk.Checkbutton(row, text=fmt.upper(), variable=value).pack(side='left', padx=SPACE['xs'])

    def quality_row(self, parent, variable, kind):
        row = ttk.Frame(parent)
        row.pack(fill='x', pady=SPACE['xs'])
        ttk.Label(row, text=tr('ui_012'), style='Form.TLabel').pack(side='left')
        combo = ChoiceBox(row, textvariable=variable, values=['Auto'], labels={'Auto': tr('ui_013'), 'Fast': tr('ui_014'), 'Balanced': tr('ui_015'), 'Accurate': tr('ui_016')}, state='disabled', width=15)
        combo.pack(side='left', padx=(0, SPACE['s']))
        description = tk.StringVar(value=tr('quality_auto'))
        def describe(*_):
            description.set(tr('quality_' + variable.get().lower()))
        variable.trace_add('write', describe)
        ttk.Label(row, textvariable=description, style='Muted.TLabel').pack(side='left')
        if kind == 'realtime':
            ttk.Checkbutton(row, style='Toggle.TCheckbutton', text=tr('ui_019'), variable=self.translation).pack(side='left', padx=SPACE['m'])
        combo.bind('<<ComboboxSelected>>', lambda _: self.guard(self.save_settings), add='+')
        setattr(self, kind + '_quality_box', combo)

    def build_file(self):
        bar = ttk.Frame(self.file_page)
        bar.pack(side='bottom', fill='x', pady=(SPACE['s'],0))
        self.add_button = self.button(bar, tr('ui_020'), self.choose_files)
        self.button(bar, tr('ui_021'), self.remove_files, style='Tertiary.TButton')
        self.file_start = self.button(bar, tr('start_file'), self.start_files)
        self.file_start.configure(style='Primary.TButton')
        self.file_stop = self.button(bar, tr('ui_023'), self.stop, track=False)
        self.button(bar, tr('ui_024'), lambda: self.controller.open_output(self.output_dir.get()))
        self.file_start.pack_configure(side='right', padx=0)
        self.file_stop.pack_configure(side='right')
        settings = self.file_settings = ttk.Frame(self.file_page)
        settings.pack(side='bottom', fill='x', pady=(SPACE['s'],0))
        row = ttk.Frame(settings)
        row.pack(fill='x', pady=SPACE['xs'])
        ttk.Label(row, text=tr('ui_025'), style='Form.TLabel').pack(side='left')
        ChoiceBox(row, textvariable=self.language, values=list(LANGUAGES), state='readonly', width=12).pack(side='left')
        row = ttk.Frame(settings)
        row.pack(fill='x', pady=SPACE['xs'])
        ttk.Label(row, text=tr('translation_setting'), style='Form.TLabel').pack(side='left')
        ttk.Checkbutton(row, style='Toggle.TCheckbutton', variable=self.translation, takefocus=True).pack(side='left')
        ttk.Label(row, text=tr('ui_027'), style='Muted.TLabel').pack(side='left')
        self.quality_row(settings, self.file_quality, 'file')
        self.formats_row(settings)
        self.output_row(settings)
        self.file_footer = ttk.Frame(self.file_page)
        self.file_footer.pack(side='bottom', fill='x')
        table = ttk.Frame(self.file_page)
        table.pack(fill='both', expand=True)
        self.files = ttk.Treeview(table, columns=('file', 'status', 'translation', 'error', 'duration'), show='headings', selectmode='extended')
        for name, title, width in (('file', tr('ui_029'), 300), ('status', tr('ui_030'), 95), ('translation', tr('ui_031'), 65), ('error', tr('ui_032'), 240), ('duration', tr('ui_033'), 80)):
            self.files.heading(name, text=title, anchor='w')
            self.files.column(name, width=width, minwidth=60)
        scroll = ttk.Scrollbar(table, orient='vertical', command=self.files.yview)
        self.files.configure(yscrollcommand=scroll.set)
        self.files.pack(side='left', fill='both', expand=True)
        scroll.pack(side='right', fill='y')
        self.drop_area = ttk.Frame(table, padding=SPACE['m'], style='Drop.TFrame')
        self.drop_title = ttk.Label(self.drop_area, text=tr('drop_title'), style='Empty.TLabel', anchor='center', justify='center')
        self.drop_title.pack(fill='x')
        self.drop_choose = ttk.Button(self.drop_area, text=tr('choose_file'), command=lambda: self.guard(self.choose_files))
        self.drop_choose.pack(pady=SPACE['xs'])
        self.drop_area.place(relx=0.5, rely=0.5, anchor='center', relwidth=1, relheight=1)
        self.drop_title.pack_configure(pady=(SPACE['l'],0))
        self.drop_available = install_drop(self.files, self.add_files)
        install_drop(self.drop_area, self.add_files)
        install_drop(self.drop_title, self.add_files)
        install_drop(self.drop_choose, self.add_files)
        self.progress = ttk.Progressbar(self.file_footer, mode='determinate')
        self.progress.pack(fill='x', pady=(SPACE['xs'], SPACE['xs']))
        ttk.Label(self.file_footer, textvariable=self.progress_text).pack(side='left')
        ttk.Label(self.file_footer, textvariable=self.elapsed).pack(side='right')
        self.file_hint = tk.StringVar(value=tr('ui_035'))

    def build_live(self):
        source_row = ttk.Frame(self.live_page)
        source_row.pack(fill='x', pady=(0, SPACE['xs']))
        ttk.Label(source_row, text=tr('audio_source_setting'), style='Form.TLabel').pack(side='left')
        self.source_box = ChoiceBox(source_row, textvariable=self.audio_source, values=('Microphone', 'System Audio'), state='readonly', width=18)
        self.source_box.pack(side='left')
        self.source_box.bind('<<ComboboxSelected>>', lambda e: self.source_changed(), add='+')
        self.source_status_label = ttk.Label(source_row, textvariable=self.system_audio_status)
        row = ttk.Frame(self.live_page)
        row.pack(fill='x')
        self.microphone_controls = ttk.Frame(row)
        self.microphone_controls.pack(side='left')
        ttk.Label(self.microphone_controls, text=tr('ui_037'), style='Form.TLabel').pack(side='left')
        self.devices = ChoiceBox(self.microphone_controls, textvariable=self.device, values=list(self.device_ids), state='readonly', width=42)
        self.devices.pack(side='left', padx=(0, SPACE['s']))
        self.button(self.microphone_controls, tr('ui_038'), self.controller.devices)
        self.live_start = self.button(row, tr('start_live'), self.start_live)
        self.live_stop = self.button(row, tr('ui_039'), self.stop, track=False)
        self.live_stop.pack_forget()
        self.live_start.configure(style='Primary.TButton')
        self.live_options = ttk.Frame(self.live_page)
        self.quality_row(self.live_options, self.realtime_quality, 'realtime')
        overlay_row = ttk.Frame(self.live_page)
        overlay_row.pack(side='bottom', fill='x', pady=SPACE['xs'])
        ttk.Checkbutton(overlay_row, style='Toggle.TCheckbutton', text=tr('ui_026'), variable=self.translation).pack(side='left')
        ttk.Checkbutton(overlay_row, style='Toggle.TCheckbutton', text=tr('overlay_title'), variable=self.overlay_visible, command=self.toggle_overlay).pack(side='left', padx=SPACE['s'])
        self.modes = modes = ChoiceBox(overlay_row, textvariable=self.subtitle_mode, values=('English', tr('ui_041'), 'Bilingual'), labels={'English': tr('ui_042'), tr('ui_041'): tr('ui_041'), 'Bilingual': tr('ui_043')}, state='readonly', width=8)
        modes.pack(side='left', padx=SPACE['xs'])
        modes.bind('<<ComboboxSelected>>', lambda e: self.set_subtitle_mode(), add='+')
        ttk.Button(overlay_row, text=tr('ui_044'), command=lambda: self.guard(self.toggle_edit)).pack(side='left')
        ttk.Checkbutton(self.live_options, text=tr('ui_045'), variable=self.hotkeys_enabled, command=self.configure_hotkeys).pack(side='left', padx=SPACE['s'])
        ttk.Button(self.live_options, text=tr('ui_046'), command=self.show_shortcuts).pack(side='left')
        ttk.Button(overlay_row, text=tr('more_settings'), style='Tertiary.TButton', command=self.toggle_live_options).pack(side='right')
        self.source_changed()
        tools = ttk.Frame(self.live_options)
        tools.pack(side='bottom', fill='x', pady=SPACE['xs'])
        self.clear_button = self.button(tools, tr('ui_047'), self.clear_session, style='Tertiary.TButton')
        self.export_button = self.button(tools, tr('ui_048'), self.export_session, track=False)
        self.button(tools, tr('ui_049'), self.restore_session)
        self.button(tools, tr('ui_024'), lambda: self.controller.open_output(self.output_dir.get()))
        self.button(tools, tr('ui_050'), self.live_export_settings, style='Tertiary.TButton')
        self.translation_label = ttk.Label(self.live_page, textvariable=self.translation_status, wraplength=950)
        self.translation_label.pack(side='bottom', anchor='w', pady=SPACE['xs'])
        self.panes = ttk.Panedwindow(self.live_page, orient='vertical')
        self.panes.pack(fill='both', expand=True)
        english = ttk.Labelframe(self.panes, text=tr('ui_051'), padding=SPACE['m'], style='Reading.TLabelframe')
        self.chinese_frame = ttk.Labelframe(self.panes, text=tr('ui_052'), padding=SPACE['m'], style='Reading.TLabelframe')
        self.panes.add(english, weight=1)
        self.panes.add(self.chinese_frame, weight=1)
        partial_area = ttk.Frame(english)
        partial_area.pack(side='bottom', fill='x')
        ttk.Label(partial_area, text=tr('ui_053')).pack(anchor='w', pady=(4, 0))
        self.partial_label = ttk.Label(partial_area, textvariable=self.partial, wraplength=440, foreground=COLORS['text_secondary'])
        self.partial_label.pack(anchor='w')
        self.english = ScrolledText(english, wrap='word', state='disabled', width=35, height=6, font=('Segoe UI', TYPE['transcript']), borderwidth=0, highlightthickness=0, background=COLORS['surface'], foreground=COLORS['text_primary'])
        self.english.pack(fill='both', expand=True)
        self.chinese = ScrolledText(self.chinese_frame, wrap='word', state='disabled', width=35, height=6, font=('Microsoft YaHei UI', TYPE['transcript']), borderwidth=0, highlightthickness=0, background=COLORS['surface'], foreground=COLORS['text_primary'])
        self.chinese.pack(fill='both', expand=True)
        self.live_empty = ttk.Label(self.english, text=tr('live_empty'), style='Empty.TLabel', anchor='center', justify='center', wraplength=600)
        self.refresh_empty()

    def refresh_empty(self):
        empty = self.english.compare('end-1c', '==', '1.0') and not self.partial.get()
        if empty:
            if not self.live_empty.winfo_manager():
                self.live_empty.place(relx=0.5, rely=0.5, anchor='center', relwidth=0.95)
        elif self.live_empty.winfo_manager():
            self.live_empty.place_forget()

    def toggle_live_options(self):
        if self.live_options.winfo_manager():
            self.live_options.pack_forget()
        else:
            self.live_options.pack(side='bottom', fill='x', before=self.panes)

    def output_row(self, parent):
        row = ttk.Frame(parent)
        row.pack(fill='x', pady=SPACE['xs'])
        ttk.Label(row, text=tr('ui_054'), style='Form.TLabel').pack(side='left')
        ttk.Entry(row, textvariable=self.output_dir).pack(side='left', fill='x', expand=True, padx=(0, SPACE['s']))
        self.button(row, tr('ui_055'), lambda: self.browse(self.output_dir))

    def settings(self):
        settings = Settings(self.file_model.get().strip(), self.realtime_model.get().strip(), self.output_dir.get().strip(), tuple((k for k, v in self.formats.items() if v.get())), LANGUAGES[self.language.get()], self.translation.get(), microphone=self.device.get(), file_quality='' if self.file_quality.get() == 'Auto' else self.file_quality.get(), realtime_quality='' if self.realtime_quality.get() == 'Auto' else self.realtime_quality.get(), setup_completed=self.setup_completed, audio_source='system' if self.audio_source.get() == 'System Audio' else 'microphone', overlay=asdict(self.overlay.preferences), global_hotkeys=self.hotkeys_enabled.get())
        settings.validate()
        return settings

    def guard(self, action):
        try:
            action()
        except ValueError as error:
            self.error.set(str(error))
        except Exception as error:
            logger.exception('GUI action failed')
            self.error.set(friendly_error(error))

    def callback_error(self, kind, error, traceback):
        logger.error('Tk callback failed', exc_info=(kind, error, traceback))
        self.error.set(tr('ui_056'))

    def browse(self, variable):
        selected = filedialog.askdirectory(parent=self.root)
        if selected:
            variable.set(selected)

    def choose_files(self):
        selected = filedialog.askopenfilenames(parent=self.root, filetypes=[(tr('ui_057'), '*.mp3 *.wav *.m4a *.flac *.aac *.ogg *.mp4')])
        self.add_files(selected)

    def add_files(self, selected):
        if self.controller.busy or self.closing:
            self.error.set(tr('ui_058'))
            return
        duplicate = unsupported = 0
        for raw in selected:
            path = str(Path(raw).resolve())
            if Path(path).suffix.lower() not in {'.mp3', '.wav', '.m4a', '.flac', '.aac', '.ogg', '.mp4'} or not Path(path).is_file():
                unsupported += 1
                continue
            if path.casefold() in {p.casefold() for p in self.paths}:
                duplicate += 1
                continue
            item = self.files.insert('', 'end', values=(Path(path).name, file_state('Pending'), tr('ui_059') if self.translation.get() else tr('ui_060'), '', '—'))
            self.paths[path] = item

            def probe(path=path):
                try:
                    import av
                    with av.open(path) as container:
                        seconds = container.duration / av.time_base if container.duration else None
                    self.controller.post('duration', (path, seconds))
                except Exception:
                    logger.debug('Cannot probe duration', exc_info=True)
            self.documents.submit(probe)
        self.error.set(tr('ui_061', arg0=duplicate, arg1=unsupported) if duplicate or unsupported else '')
        self.sync_controls()

    def remove_files(self):
        selected = set(self.files.selection())
        for path, item in list(self.paths.items()):
            if item in selected:
                self.files.delete(item)
                del self.paths[path]

    def save_settings(self):
        settings = self.settings()
        self.documents.submit(lambda: settings.save(self.settings_path))

    def start_files(self):
        self.require_model('file')
        settings = self.settings()
        self.error.set('')
        self.controller.start_files(tuple(self.paths), settings)
        self.live_requested = False
        self.task_started = time.monotonic()
        self.save_settings()
        for path, item in self.paths.items():
            self.files.item(item, values=(Path(path).name, file_state('Pending'), tr('ui_059') if settings.translation else tr('ui_060'), '', self.durations.get(path, '—')))
        self.progress.configure(maximum=max(1, len(self.paths)), value=0)
        self.progress_text.set(f'0 / {len(self.paths)}')
        self.status.set(tr('ui_062'))
        self.sync_controls()

    def start_live(self):
        self.require_model('realtime')
        settings = self.settings()
        if self.controller.busy or self.documents.busy:
            raise ValueError(tr('ui_063'))
        previous = self.documents.snapshot()
        if previous and previous.unsaved and self.documents.io_error:
            raise ValueError(tr('ui_064'))
        if previous and previous.segments:
            if not messagebox.askokcancel(tr('ui_065'), tr('ui_066'), parent=self.root):
                return
        self.documents.new(settings.translation, settings.target_language)
        self.overlay.state.reset()
        self.overlay.render()
        self.show_translation()
        self.controller.start_realtime(settings, self.device_ids.get(self.device.get()))
        self.live_requested = True
        self.save_settings()
        self.session_id = None
        self.last_final = 0
        self.partial.set('')
        for widget in (self.english, self.chinese):
            widget.configure(state='normal')
            widget.delete('1.0', 'end')
            widget.configure(state='disabled')
        self.error.set('')
        self.status.set(tr('ui_067'))
        self.translation_status.set(tr('ui_068') if settings.translation else tr('ui_004'))
        self.sync_controls()

    def require_model(self, kind):
        if not self.runtime_ready:
            raise ValueError(tr('ui_069'))
        if not self.policy or not getattr(self.policy, kind + '_modes'):
            self.open_setup()
            raise ValueError(tr('ui_070'))
        if self.translation.get() and (not translation_model_available()):
            self.open_setup(translation=True)
            raise ValueError(tr('ui_071'))

    def open_setup(self, translation=False):
        if not self.controller.runtime:
            raise ValueError(tr('ui_072'))
        if self.setup_dialog and self.setup_dialog.window.winfo_exists():
            self.setup_dialog.window.lift()
            return
        from setup_ui import SetupDialog
        self.setup_dialog = SetupDialog(self, translation)

    def diagnostics(self):
        from setup_ui import show_about
        show_about(self)

    def show_shortcuts(self):
        messagebox.showinfo(tr('ui_046'), tr('ui_073'), parent=self.root)

    def apply_runtime(self, value):
        self.policy = value[2]
        self.runtime_ready = True
        self.acceleration.set(tr('ui_074') if any((x.device == 'cuda' for x in (*self.policy.file_modes.values(), *self.policy.realtime_modes.values()))) else tr('ui_075'))
        for kind in ('file', 'realtime'):
            modes = getattr(self.policy, kind + '_modes')
            variable = getattr(self, kind + '_quality')
            if variable.get() != 'Auto' and variable.get() not in modes:
                variable.set('Auto')
                self.error.set(tr('ui_076'))
            getattr(self, kind + '_quality_box').configure(values=['Auto', *modes])
        self.status.set(tr('ui_003'))
        if self.offer_setup and (not self.setup_completed) and (not self.closing):
            self.root.after_idle(lambda: self.guard(self.open_setup))

    def clear_session(self):
        doc = self.documents.snapshot()
        if doc and doc.unsaved and self.documents.io_error:
            raise ValueError(tr('ui_077'))
        if doc and doc.unsaved and (not messagebox.askyesno(tr('ui_078'), tr('ui_079'), parent=self.root)):
            return
        self.documents.clear()
        self.render_document()

    def restore_session(self):
        path = filedialog.askopenfilename(parent=self.root, initialdir=self.documents.directory, title=tr('ui_080'), filetypes=[(tr('ui_081'), '*.json')])
        if path:
            self.documents.restore(path)

    def render_document(self):
        doc = self.documents.snapshot()
        for widget in (self.english, self.chinese):
            widget.configure(state='normal')
            widget.delete('1.0', 'end')
            widget.configure(state='disabled')
        self.partial.set('')
        self.last_final = 0
        if doc:
            self.translation.set(doc.translation_enabled)
            self.show_translation()
            for segment in doc.segments:
                self.append(self.english, segment.original_text)
                if doc.translation_enabled:
                    self.append(self.chinese, segment.translated_text or tr('ui_082'))
                self.last_final = max(self.last_final, segment.segment_id)

    def export_session(self):
        doc = self.documents.snapshot()
        if not doc or not doc.segments:
            raise ValueError(tr('ui_083'))
        self.settings().validate()
        self.export_waiting = True
        self.export_deadline = time.monotonic() + 10
        if self.controller.busy:
            self.controller.stop()
        self.status.set(tr('ui_082'))
        self.check_export()

    def check_export(self):
        if not self.export_waiting or self.closing:
            return
        doc = self.documents.snapshot()
        if not doc:
            self.export_waiting = False
            return
        english_only = False
        if self.controller.busy or doc.pending:
            if time.monotonic() < self.export_deadline:
                self.root.after(100, self.check_export)
                return
            english_only = messagebox.askyesno(tr('ui_084'), tr('ui_085'), parent=self.root)
            if not english_only:
                self.export_waiting = False
                return
        self.export_waiting = False
        settings = self.settings()
        self.documents.export(settings.output_dir, settings.formats, english_only)
        self.status.set(tr('ui_086'))

    def show_translation(self):
        if self.controller.busy:
            return
        self.translation_status.set(tr('translation_ready') if self.translation.get() else tr('ui_004'))
        self.overlay.translation_enabled = self.translation.get()
        self.modes.configure(values=('English', tr('ui_041'), 'Bilingual') if self.translation.get() else ('English',))
        if not self.translation.get():
            self.subtitle_mode.set('English')
            self.overlay.preferences.mode = 'English'
            self.overlay.render()
        if self.translation.get() and (not translation_model_available()) and self.runtime_ready:
            self.guard(lambda: self.open_setup(translation=True))
        visible = str(self.chinese_frame) in self.panes.panes()
        if self.translation.get() and (not visible):
            self.panes.add(self.chinese_frame, weight=1)
        elif not self.translation.get() and visible:
            self.panes.forget(self.chinese_frame)

    def stop(self):
        self.controller.stop()
        self.status.set(tr('ui_087'))

    @staticmethod
    def append(widget, text):
        widget.configure(state='normal')
        widget.insert('end', text + '\n\n')
        if int(widget.index('end-1c').split('.')[0]) > 1000:
            widget.delete('1.0', '101.0')
        # Paragraph separators (and empty results) must not hide the last text.
        last_text = widget.search(r'\S', 'end-1c', backwards=True,
                                  regexp=True, stopindex='1.0')
        if last_text:
            widget.see(last_text)
        widget.configure(state='disabled')

    def on_realtime(self, event):
        if self.session_id is None:
            self.session_id = event.session_id
        if event.session_id != self.session_id:
            return
        kind = event.kind
        self.overlay.update(event)
        if kind == 'partial_transcript' and event.utterance_id > self.last_final:
            self.partial.set(event.text)
        elif kind == 'final_transcript':
            if event.utterance_id <= self.last_final:
                return
            self.last_final = event.utterance_id
            self.partial.set('')
            self.append(self.english, event.text)
        elif kind == 'translation_completed':
            self.append(self.chinese, event.translated_text)
            self.translation_status.set(tr('ui_088'))
        elif kind == 'translation_started':
            self.translation_status.set(tr('ui_089', arg0=event.utterance_id))
        elif kind == 'translation_failed':
            self.append(self.chinese, tr('ui_090', arg0=event.utterance_id))
            logger.error('Translation failed: %s', event.reason)
            self.error.set(error_message(category='translation'))
        elif kind == 'error':
            logger.error('Realtime error: %s', event.reason)
            category = 'model' if 'inference' in event.reason or 'model' in event.reason else None
            self.error.set(error_message(event.reason, category))
        elif kind == 'speech_started':
            self.status.set(tr('ui_091'))
        elif kind == 'speech_ended':
            self.status.set(tr('ui_092'))
        elif kind == 'stopped':
            self.partial.set('')
            self.status.set(tr('ui_093'))

    def poll(self):
        for action in self.hotkeys.poll():
            self.guard(lambda action=action: self.hotkey_action(action))
        for kind, value in self.controller.drain():
            if kind == 'realtime':
                self.on_realtime(value)
            elif kind == 'status':
                self.status.set(value)
            elif kind == 'runtime':
                self.apply_runtime(value)
            elif kind == 'runtime_failed':
                self.runtime_ready = True
                self.acceleration.set(tr('ui_094'))
            elif kind == 'acceleration':
                self.acceleration.set(tr('ui_074') if tr('ui_095') in value or 'GPU acceleration enabled' in value else tr('ui_096') if 'fallback' in value.lower() or tr('ui_096') == value else tr('ui_075'))
            elif kind == 'error':
                self.error_count += 1
                self.error.set(value)
            elif kind == 'download_progress':
                if self.setup_dialog:
                    self.setup_dialog.update(value)
            elif kind == 'download_finished':
                if self.setup_dialog:
                    self.setup_dialog.download.state(['!disabled'])
                settings = self.settings()
                self.documents.submit(lambda: self.controller.initialize_runtime(settings))
            elif kind == 'file':
                path, state, error = value
                item = self.paths.get(path)
                if item:
                    old = self.files.item(item, 'values')
                    self.files.item(item, values=(old[0], file_state(state), old[2], error, self.durations.get(path, '—')))
                if error:
                    self.error.set(error)
            elif kind == 'progress':
                self.progress.configure(value=value[0], maximum=value[1])
                self.progress_text.set(f'{value[0]} / {value[1]}')
            elif kind == 'duration':
                path, seconds = value
                if path in self.paths and seconds is not None:
                    self.durations[path] = f'{int(seconds) // 60}:{int(seconds) % 60:02d}'
                    self.files.set(self.paths[path], 'duration', self.durations[path])
            elif kind == 'devices':
                self.device_ids = {'Default microphone': None, **{name: i for i, name in reversed(value)}}
                self.devices.configure(values=list(self.device_ids))
                if self.device.get() not in self.device_ids:
                    self.device.set('Default microphone')
                self.status.set(tr('ui_097'))
            elif kind == 'system_output':
                self.system_audio_status.set(value)
            elif kind == 'metrics':
                logger.info('GUI realtime metrics: %s', value)
            elif kind == 'restored':
                self.render_document()
                self.status.set(tr('ui_098'))
            elif kind == 'exported':
                self.status.set(tr('ui_099', arg0=len(value), arg1=Path(value[0]).name))
            elif kind == 'recovery_available':
                self.status.set(tr('ui_100', arg0=value))
        self.sync_controls()
        if self.closing:
            self.status.set(tr('ui_101'))
        if self.closing and (not self.controller.busy) and (not self.documents.busy) and self.controller.events.empty():
            if self.documents.io_error and (not messagebox.askyesno(tr('ui_102'), tr('ui_103'), parent=self.root)):
                self.closing = False
                return self._schedule_poll()
            self.documents.shutdown()
            self.hotkeys.close()
            self.overlay.close()
            self.root.destroy()
            return
        self._schedule_poll()

    def _schedule_poll(self):
        self.timer = self.root.after(50, self.poll)

    def sync_controls(self):
        self.refresh_empty()
        if self.overlay_visible.get() != self.overlay.visible:
            self.overlay_visible.set(self.overlay.visible)
        def set_state(widget, state):
            # Avoid invalidating every image-backed control on each 50 ms poll.
            if str(widget.cget('state')) != state:
                widget.configure(state=state)
        busy = self.controller.busy or self.documents.busy or (not self.controller.events.empty()) or self.closing or self.export_waiting
        if busy != self.activity_running:
            self.activity_running = busy
            if busy:
                self.activity.pack(fill='x')
            else:
                self.activity.pack_forget()
        if busy:
            self.activity.step(2)
        if self.task_started is not None and self.controller.busy and not self.live_requested:
            self.elapsed.set(tr('elapsed', seconds=int(time.monotonic() - self.task_started)))
        self.actions = [button for button in self.actions if button.winfo_exists()]
        for button in self.actions:
            if button not in (self.file_start, self.live_start, self.clear_button, self.export_button):
                set_state(button, 'disabled' if busy else 'normal')
        for button in (self.file_stop, self.live_stop):
            set_state(button, 'normal' if self.controller.busy and self.controller.state in ('Loading', 'Running') else 'disabled')
        for kind, button in (('file', self.file_start), ('realtime', self.live_start)):
            available = self.runtime_ready and self.policy and getattr(self.policy, kind + '_modes')
            set_state(button, 'normal' if available and (not busy) and (kind != 'file' or self.paths) else 'disabled')
            set_state(getattr(self, kind + '_quality_box'), 'readonly' if available and (not busy) else 'disabled')
        if self.paths:
            if self.drop_area.winfo_manager():
                self.drop_area.place_forget()
        elif not self.drop_area.winfo_manager():
            self.drop_area.place(relx=0.5, rely=0.5, anchor='center')
        if self.controller.busy and self.live_requested:
            if self.live_start.winfo_manager(): self.live_start.pack_forget()
            if not self.live_stop.winfo_manager(): self.live_stop.pack(side='left', padx=SPACE['s'])
        else:
            if self.live_stop.winfo_manager(): self.live_stop.pack_forget()
            if not self.live_start.winfo_manager(): self.live_start.pack(side='left', padx=SPACE['s'])
        hint = '' if self.paths else tr('ui_035')
        if self.file_hint.get() != hint: self.file_hint.set(hint)
        set_state(self.source_box, 'disabled' if busy else 'readonly')
        doc = self.documents.document
        set_state(self.clear_button, 'normal' if doc and doc.segments and (not busy) else 'disabled')
        set_state(self.export_button, 'normal' if doc and doc.segments and (not self.documents.busy) and (not self.closing) and (not self.export_waiting) else 'disabled')

    def close(self):
        self.hotkeys.close()
        self.closing = True
        self.export_waiting = False
        self.documents.autosave()
        self.guard(self.save_settings)
        self.stop()
        self.status.set(tr('ui_101'))
        self.sync_controls()

    def source_changed(self):
        system = self.audio_source.get() == 'System Audio'
        if system:
            self.microphone_controls.pack_forget()
            self.source_status_label.pack(side='left', padx=SPACE['s'])
            self.documents.submit(self.controller.system_output)
        else:
            self.source_status_label.pack_forget()
            self.microphone_controls.pack(side='left', before=self.live_start)

    def toggle_overlay(self):
        self.overlay.hide() if self.overlay.visible else self.overlay.show()

    def live_export_settings(self):
        dialog = tk.Toplevel(self.root)
        dialog.title(tr('ui_104'))
        dialog.transient(self.root)
        dialog.geometry('660x180')
        self.output_row(dialog)
        self.formats_row(dialog)
        ttk.Label(dialog, text=tr('ui_105')).pack(pady=SPACE['s'])
        ttk.Button(dialog, text=tr('ui_106'), command=dialog.destroy).pack()

    def set_subtitle_mode(self):
        if self.subtitle_mode.get() != 'English' and (not self.overlay.translation_enabled):
            self.error.set(tr('ui_107'))
            self.subtitle_mode.set('English')
        self.overlay.preferences.mode = self.subtitle_mode.get()
        self.overlay.render()

    def toggle_edit(self):
        if not self.overlay.set_watch(not self.overlay.watch):
            self.error.set(tr('ui_108'))

    def configure_hotkeys(self):
        self.hotkeys.close()
        if self.hotkeys_enabled.get():
            failures = self.hotkeys.register()
            if failures:
                logger.warning('Hotkey failures: %s', failures)
                self.error.set(tr('ui_109'))

    def hotkey_action(self, action):
        if self.closing:
            return
        if action == 'show_hide':
            self.toggle_overlay()
        elif action == 'language':
            self.overlay.cycle()
            self.subtitle_mode.set(self.overlay.preferences.mode)
        elif action == 'edit':
            self.toggle_edit()
        elif action == 'start_stop':
            if self.controller.busy:
                if self.controller.state in ('Loading', 'Running') and self.live_requested:
                    self.stop()
            else:
                self.start_live()

def main():
    PATHS.logs.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s %(message)s', handlers=[RotatingFileHandler(PATHS.logs / 'gui.log', maxBytes=2000000, backupCount=3, encoding='utf-8')])
    root = create_root()
    DesktopApp(root)
    root.mainloop()
if __name__ == '__main__':
    main()
