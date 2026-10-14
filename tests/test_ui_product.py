"""Product behavior, not screenshot snapshots. Tk tests use fake Core."""
import ast
import errno
from pathlib import Path
import re
import tkinter as tk
import unittest
from unittest.mock import patch
import test_gui
from gui_controller import Settings
from ui_strings import ZH_CN, tr
from ui_errors import error_message
from ui_support import ChoiceBox, create_root, install_drop
from setup_ui import SetupDialog


class ProductTests(unittest.TestCase):
    setUp = test_gui.GuiTests.setUp
    tearDown = test_gui.GuiTests.tearDown
    pump = test_gui.GuiTests.pump
    file = test_gui.GuiTests.file

    def test_localized_choices_keep_core_codes(self):
        variable = tk.StringVar(value='Auto')
        box = ChoiceBox(self.root, textvariable=variable, values=('Auto', 'English', 'Chinese'))
        self.assertEqual(box.cget('values'), ('自动识别', '英语', '中文'))
        box.display.set('英语')
        box.select_code(None)
        self.assertEqual(variable.get(), 'English')

    def test_catalog_references_complete(self):
        for path in Path('src').glob('*.py'):
            tree = ast.parse(path.read_text(encoding='utf-8'))
            for node in ast.walk(tree):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 'tr' and isinstance(node.args[0], ast.Constant):
                    self.assertIn(node.args[0].value, ZH_CN, str(path))

    def test_widget_labels_have_no_developer_terms(self):
        forbidden = re.compile(r'\b(Whisper|CUDA|float16|CTranslate2|WASAPI|loopback|Ready|Translation|English|Microphone|Auto|Fast|Balanced|Accurate|Pending|Start|Stop)\b')
        def inspect(widget):
            for option in ('text', 'values'):
                if option in widget.keys():
                    self.assertIsNone(forbidden.search(str(widget.cget(option))), str(widget.cget(option)))
            for child in widget.winfo_children(): inspect(child)
        inspect(self.root)

    def test_defaults_are_auto_and_two_formats(self):
        self.assertEqual(Settings().language, 'auto')
        self.assertEqual(Settings().formats, ('txt', 'docx'))

    def test_empty_state_and_deduplication(self):
        self.assertFalse(self.app.paths)
        path = self.file()
        self.app.add_files((path, path))
        self.assertEqual(len(self.app.paths), 1)
        self.assertIn('重复', self.app.error.get())

    def test_unsupported_drop_rejected(self):
        path = self.directory / 'bad.exe'; path.write_bytes(b'bad')
        self.app.add_files((path,))
        self.assertFalse(self.app.paths)
        self.assertIn('不支持', self.app.error.get())

    def test_tcl_drop_paths_unicode_spaces(self):
        path = self.directory / '中文 文件.wav'; path.write_bytes(b'fixture')
        encoded = self.root.tk.call('list', str(path))
        self.app.add_files(self.root.tk.splitlist(encoded))
        self.assertIn(str(path), self.app.paths)

    def test_source_labels_and_switch(self):
        self.assertEqual(self.app.source_box.cget('values'), ('麦克风', '系统音频'))
        with patch.object(self.controller, 'system_output') as probe:
            self.app.audio_source.set('System Audio'); self.app.source_changed()
            self.pump(lambda: not self.app.documents.busy)
            probe.assert_called_once()
        self.assertEqual(self.app.settings().audio_source, 'system')

    def test_translation_off_disables_chinese_modes(self):
        self.app.translation.set(False)
        self.assertEqual(self.app.modes.cget('values'), ('英文',))
        self.app.overlay.cycle()
        self.assertEqual(self.app.overlay.preferences.mode, 'English')
        self.app.subtitle_mode.set('Bilingual'); self.app.set_subtitle_mode()
        self.assertIn('开启中文翻译', self.app.error.get())

    def test_translation_on_exposes_bilingual(self):
        self.app.translation.set(True)
        self.assertEqual(self.app.modes.cget('values'), ('英文', '中文', '双语'))

    def test_error_categories_safe(self):
        for category in ('model','gpu','microphone','system_audio','device_changed','translation','export','permission','disk','download'):
            message = error_message(RuntimeError('SECRET traceback C:/private'), category)
            self.assertNotIn('SECRET', message)
            self.assertTrue(any('\u4e00' <= c <= '\u9fff' for c in message))
        self.assertIn('磁盘空间', error_message(OSError(errno.ENOSPC, 'disk')))

    def test_cpu_fallback_nonfatal_message(self):
        self.controller.post('acceleration', 'CPU fallback')
        self.pump(lambda: self.controller.events.empty())
        self.assertIn('已自动切换到 CPU', self.app.acceleration.get())
        self.assertFalse(self.app.error.get())

    def test_microphone_event_is_not_model_error(self):
        from realtime import RealtimeEvent
        self.app.on_realtime(RealtimeEvent('error', 'microphone-fixture', reason='microphone_disconnected'))
        self.assertIn('麦克风', self.app.error.get())
        self.assertNotIn('模型加载', self.app.error.get())

    def test_initial_cpu_selection_not_reported_as_failure(self):
        self.controller.post('acceleration', 'Running on CPU')
        self.pump(lambda: self.controller.events.empty())
        self.assertIn('正在使用 CPU', self.app.acceleration.get())
        self.assertNotIn('暂不可用', self.app.acceleration.get())

    def test_first_run_download_names_and_progress(self):
        dialog = SetupDialog(self.app)
        self.assertTrue(all('large-v3' not in c.cget('text') for c in dialog.checks))
        dialog.update(('small', 50, '正在下载…'))
        self.assertIn('MB', dialog.status.get())
        self.assertEqual(float(dialog.progress.cget('value')), 50)
        dialog.close()

    def test_edit_watch_toolbar(self):
        self.app.overlay.show()
        if self.app.overlay.native.supports_click_through:
            self.assertTrue(self.app.overlay.set_watch(True))
            self.assertFalse(self.app.overlay.bar.winfo_ismapped())
            self.assertTrue(self.app.overlay.set_watch(False))
            self.assertTrue(self.app.overlay.bar.winfo_ismapped())

    def test_file_duration_off_main_thread(self):
        import threading
        main = threading.get_ident(); observed = []
        with patch('av.open', side_effect=lambda *_: (observed.append(threading.get_ident()), None)[1]):
            self.file()
            self.pump(lambda: not self.app.documents.busy)
        self.assertTrue(observed)
        self.assertNotEqual(observed[0], main)

    def test_last_transcript_visible_in_short_viewport(self):
        from gui import DesktopApp
        self.root.deiconify()
        window = tk.Toplevel(self.root)
        try:
            for language in ('Confirmed English', '已确认中文翻译'):
                for height in (1, 2):
                    short = tk.Text(window, height=height, width=35)
                    short.pack()
                    self.root.update()
                    with patch.object(short, 'see', wraps=short.see) as seen:
                        for index in range(20):
                            DesktopApp.append(short, f'{language} {index}\n\n')
                            self.root.update()
                            target = seen.call_args.args[0]
                            self.assertTrue(short.get(target, target + '+1c').strip())
                            self.assertIsNotNone(short.bbox(target), (language, height, target))
                        DesktopApp.append(short, '')
                        self.root.update()
                        self.assertEqual(seen.call_args.args[0], target)
                        self.assertIsNotNone(short.bbox(target))
                        self.assertIn(f'{language} 19', short.get('1.0', 'end'))
                    short.destroy()
        finally:
            window.destroy()

    def test_partial_keeps_confirmed_transcript_visible(self):
        from realtime import RealtimeEvent
        self.root.deiconify()
        self.app.tabs.select(self.app.live_page)
        self.root.update()
        self.app.on_realtime(RealtimeEvent('final_transcript', 'visible', 1, text='Confirmed final'))
        self.root.update()
        before = self.app.english.get('1.0', 'end')
        self.app.on_realtime(RealtimeEvent('partial_transcript', 'visible', 2, text='New partial'))
        self.root.update()
        self.assertEqual(self.app.english.get('1.0', 'end'), before)
        self.assertEqual(self.app.partial.get(), 'New partial')
        self.assertTrue(self.app.partial_label.winfo_ismapped())
        self.assertIsNotNone(self.app.english.bbox('1.0'))

    def test_translation_idle_status_matches_switch(self):
        with patch('gui.translation_model_available', return_value=True):
            self.app.translation.set(True)
            self.app.show_translation()
            self.assertEqual(self.app.translation_status.get(), tr('translation_ready'))
            self.app.translation.set(False)
            self.app.show_translation()
            self.assertEqual(self.app.translation_status.get(), tr('ui_004'))

    def test_scaled_small_layout(self):
        from ui_support import apply_theme
        self.root.deiconify()
        for scale in (1.25, 1.5):
            self.root.tk.call('tk', 'scaling', scale * 96 / 72)
            apply_theme(self.root)
            for size in ('1024x680', '1366x768', '1920x1080'):
                self.root.geometry(size)
                for page in (self.app.file_page, self.app.live_page):
                    self.app.tabs.select(page); self.root.update()
                    self.assertGreater(page.winfo_height(), 200, (scale, size))
                    self.assertLessEqual(self.app.footer.winfo_y()+self.app.footer.winfo_height(), self.root.winfo_height())
                self.assertGreater(self.app.panes.winfo_height(), 100, (scale, size))

    def test_file_progress_reserved_in_small_window(self):
        self.root.deiconify()
        self.root.geometry('880x600')
        self.app.tabs.select(self.app.file_page)
        for i in range(100):
            self.app.files.insert('', 'end', values=(f'fixture-{i}.wav', '就绪', '关闭', '', '0:11'))
        self.root.update()
        self.assertTrue(self.app.progress.winfo_ismapped())
        self.assertGreater(self.app.files.winfo_height(), 50)
        self.assertLessEqual(self.app.file_footer.winfo_rooty() + self.app.file_footer.winfo_height(), self.app.footer.winfo_rooty())
        self.app.files.yview_moveto(1)
        self.root.update()
        self.assertTrue(self.app.progress.winfo_ismapped())
        self.assertGreater(self.app.files.yview()[0], 0)


class NativeDropTests(unittest.TestCase):
    def test_native_package_loads_and_binds(self):
        root = create_root(); root.withdraw()
        try:
            label = tk.Label(root)
            self.assertTrue(install_drop(label, lambda paths: None))
            self.assertTrue(root.tk.call('package', 'present', 'tkdnd'))
        finally: root.destroy()
