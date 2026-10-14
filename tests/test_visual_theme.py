"""Geometry/state regressions for presentation only; no screenshot matching."""
import unittest
import tkinter as tk
from tkinter import ttk
from unittest.mock import patch
import test_gui
from ui_theme import COLORS, SPACE, CONTROL, TYPE, apply_theme
from ui_strings import tr
from realtime import RealtimeEvent


class VisualTests(unittest.TestCase):
    setUp = test_gui.GuiTests.setUp
    tearDown = test_gui.GuiTests.tearDown
    pump = test_gui.GuiTests.pump
    file = test_gui.GuiTests.file

    def expose(self, page=None):
        self.root.deiconify()
        if page is not None:
            self.app.tabs.select(page)
        self.root.update()

    def geometry(self, widget):
        self.root.update_idletasks()
        return (widget.winfo_x(), widget.winfo_y(), widget.winfo_width(), widget.winfo_height(),
                widget.winfo_reqwidth(), widget.winfo_reqheight())

    def test_navigation_selected_geometry(self):
        self.expose(self.app.file_page)
        def spans():
            result = {}
            for x in range(self.app.tabs.winfo_width()):
                try:
                    i = self.app.tabs.index(f'@{x},10')
                    result.setdefault(i, []).append(x)
                except tk.TclError:
                    pass
            return {k: (min(v), max(v)) for k,v in result.items()}
        before = spans()
        self.assertEqual(len(before), 2)
        self.app.tabs.select(self.app.live_page)
        self.root.update_idletasks()
        self.assertEqual(spans(), before)
        self.app.tabs.select(self.app.file_page)
        self.assertEqual(spans(), before)

    def test_button_hover_pressed_disabled_geometry(self):
        self.expose()
        for widget in (self.app.add_button, self.app.file_start, self.app.file_stop):
            baseline = self.geometry(widget)
            for state in ('active', 'pressed', 'disabled', 'focus'):
                widget.state(('!disabled', '!pressed', '!active', '!focus', state))
                self.assertEqual(self.geometry(widget), baseline, state)

    def test_checkbox_native_indicator(self):
        style = ttk.Style(self.root)
        self.assertIn('NativeCheck.indicator', str(style.layout('TCheckbutton')))
        self.assertIn(self.root.checkbox_indicator_source, ('vista', 'alt'))
        if 'vista' in style.theme_names():
            self.assertEqual(self.root.checkbox_indicator_source, 'vista')
        self.assertNotIn('×', str(style.layout('TCheckbutton')))

    def test_checkbox_states_fixed(self):
        self.expose()
        window = tk.Toplevel(self.root)
        value = tk.BooleanVar(value=False)
        box = ttk.Checkbutton(window, text='TXT', variable=value)
        box.pack()
        baseline = self.geometry(box)
        box.invoke()
        self.assertTrue(value.get())
        self.assertTrue(box.instate(('selected',)))
        for state in ('active', 'pressed', 'disabled'):
            box.state((state,))
            self.assertEqual(self.geometry(box), baseline)
        window.destroy()

    def test_spacing_tokens(self):
        self.assertEqual(tuple(SPACE.values()), (4,8,12,16,24,32))
        self.assertEqual(CONTROL['border'], 1)
        self.assertLessEqual(len(set(TYPE.values())), 5)

    def test_theme_tokens_consistent(self):
        style = ttk.Style(self.root)
        self.assertEqual(style.lookup('TFrame','background'), COLORS['background'])
        self.assertEqual(style.lookup('Treeview','fieldbackground'), COLORS['surface'])
        self.assertEqual(style.lookup('TNotebook.Tab','background',('selected',)), COLORS['primary_soft'])

    def test_button_hierarchy(self):
        style = ttk.Style(self.root)
        self.assertEqual(self.app.file_start.cget('style'), 'Primary.TButton')
        self.assertEqual(self.app.clear_button.cget('style'), 'Tertiary.TButton')
        for state in ((), ('active',), ('pressed',), ('disabled',)):
            self.assertEqual(style.lookup('Primary.TButton','padding',state), style.lookup('TButton','padding',state))

    def test_file_empty_state(self):
        self.expose()
        self.assertTrue(self.app.drop_area.winfo_ismapped())
        self.assertEqual(self.app.drop_choose.cget('text'), tr('choose_file'))
        self.file()
        self.pump(lambda: not self.app.documents.busy)
        self.assertFalse(self.app.drop_area.winfo_ismapped())

    def test_realtime_empty_state(self):
        self.expose(self.app.live_page)
        self.app.refresh_empty()
        self.assertTrue(self.app.live_empty.winfo_ismapped())
        self.assertEqual(self.app.english.get('1.0','end').strip(), '')
        self.app.on_realtime(RealtimeEvent('partial_transcript','theme',1,text='Visible partial'))
        self.app.refresh_empty()
        self.assertFalse(self.app.live_empty.winfo_ismapped())

    def test_toggle_available(self):
        self.expose(self.app.file_page)
        with patch('gui.translation_model_available', return_value=True):
            self.app.translation.set(True)
            self.assertEqual(self.app.translation_status.get(), tr('translation_ready'))
            self.app.translation.set(False)
            self.assertEqual(self.app.translation_status.get(), tr('ui_004'))
        self.assertIn('Switch.indicator', str(ttk.Style(self.root).layout('Toggle.TCheckbutton')))

    def test_combobox_states_fixed(self):
        self.expose()
        widget = self.app.file_quality_box
        baseline = self.geometry(widget)
        for state in ('readonly', 'disabled', 'active', 'focus'):
            widget.state((state,))
            self.assertEqual(self.geometry(widget), baseline)

    def test_light_chinese_theme(self):
        from ui_audit import inspect_labels
        self.assertTrue(inspect_labels(self.root)['passed'])
        self.assertEqual(COLORS['surface'], '#FFFFFF')
        self.assertIn('等待开始', tr('live_empty'))

    def test_small_and_scaled_geometry(self):
        self.expose()
        for scale in (1.25, 1.5):
            self.root.tk.call('tk', 'scaling', scale*96/72)
            apply_theme(self.root)
            for size in ('880x600','1366x768','1920x1080'):
                self.root.geometry(size)
                self.app.tabs.select(self.app.file_page)
                self.root.update()
                self.assertTrue(self.app.progress.winfo_ismapped())
                self.assertLessEqual(self.app.file_footer.winfo_rooty()+self.app.file_footer.winfo_height(), self.app.footer.winfo_rooty())

