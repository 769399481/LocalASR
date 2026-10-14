"""Refinement contracts: real widgets, fake Core, no pixel matching."""
import time
import tkinter as tk
from tkinter import ttk
from unittest.mock import patch
import unittest
import test_gui
from ui_theme import RADIUS, SHADOW, FORM, apply_theme


class RefinementTests(unittest.TestCase):
    setUp = test_gui.GuiTests.setUp
    tearDown = test_gui.GuiTests.tearDown
    pump = test_gui.GuiTests.pump

    def show(self, page=None):
        self.root.deiconify()
        self.app.tabs.select(page or self.app.file_page)
        self.root.update()

    def test_idle_does_not_reconfigure_unchanged_actions(self):
        self.show()
        self.app.sync_controls()
        with patch.object(self.app.add_button, 'configure', wraps=self.app.add_button.configure) as call:
            for _ in range(30):
                self.app.sync_controls()
            self.assertEqual(call.call_count,0)

    def test_event_loop_heartbeat_and_bounded_timers(self):
        self.show()
        fired=[]
        self.root.after(60,lambda:fired.append(True))
        started=time.monotonic()
        self.pump(lambda:bool(fired),timeout=2)
        self.assertLess(time.monotonic()-started,2)
        self.assertLess(len(self.root.tk.call('after','info')),10)

    def test_theme_reapply_does_not_allocate_images(self):
        before=set(self.root.tk.call('image','names'))
        for _ in range(4): apply_theme(self.root)
        self.assertEqual(set(self.root.tk.call('image','names')),before)

    def test_form_labels_share_left_axis(self):
        self.show()
        labels=[row.winfo_children()[0] for row in self.app.file_settings.winfo_children()]
        self.assertGreaterEqual(len(labels),5)
        self.assertEqual(len({w.winfo_rootx() for w in labels}),1)
        self.assertEqual(len({w.winfo_width() for w in labels}),1)
        for w in labels:
            self.assertEqual(str(w.cget('style')),'Form.TLabel')
        self.assertEqual(ttk.Style(self.root).lookup('Form.TLabel','anchor'),'w')

    def test_file_headings_left_aligned(self):
        for col in self.app.files['columns']:
            self.assertEqual(str(self.app.files.heading(col,'anchor')),'w')

    def test_toggle_binding_disabled_and_geometry(self):
        self.show()
        value=tk.BooleanVar(value=False)
        box=ttk.Checkbutton(self.app.file_page,style='Toggle.TCheckbutton',variable=value,takefocus=True)
        box.pack()
        self.root.update_idletasks()
        size=(box.winfo_reqwidth(),box.winfo_reqheight())
        box.invoke(); self.assertTrue(value.get())
        box.state(('disabled',)); box.invoke(); self.assertTrue(value.get())
        self.assertEqual((box.winfo_reqwidth(),box.winfo_reqheight()),size)
        self.assertIn('Switch.indicator',str(ttk.Style(self.root).layout('Toggle.TCheckbutton')))
        box.destroy()

    def test_more_settings_keeps_binding_and_can_close(self):
        self.show(self.app.live_page)
        self.assertFalse(self.app.live_options.winfo_ismapped())
        self.app.toggle_live_options(); self.root.update_idletasks()
        self.assertTrue(self.app.realtime_quality_box.winfo_ismapped())
        self.app.toggle_live_options(); self.root.update_idletasks()
        self.assertFalse(self.app.live_options.winfo_ismapped())

    def test_transcript_has_majority_of_compact_page(self):
        self.root.geometry('880x600')
        self.show(self.app.live_page)
        self.assertGreater(self.app.panes.winfo_height()/self.app.live_page.winfo_height(),.45)

    def test_radius_and_shadow_are_centralized(self):
        self.assertLess(RADIUS['control'],RADIUS['button'])
        self.assertLess(RADIUS['button'],RADIUS['surface'])
        self.assertEqual(SHADOW['depth'],1)
        self.assertGreater(FORM['label_width'],0)

    def test_rounded_assets_have_large_nonempty_tile_centre(self):
        from ui_shapes import RASTER_SIZE, rounded_image
        self.assertGreaterEqual(RASTER_SIZE-2*(max(RADIUS.values())+1),64)
        with self.assertRaises(ValueError):
            rounded_image(self.root,'white','gray',15,size=32)

    def test_navigation_all_states_keep_allocation(self):
        self.show()
        base=(self.app.tabs.winfo_reqwidth(),self.app.tabs.winfo_reqheight())
        for state in ('active','pressed','disabled','focus'):
            self.app.tabs.state((state,))
            self.root.update_idletasks()
            self.assertEqual((self.app.tabs.winfo_reqwidth(),self.app.tabs.winfo_reqheight()),base)
            self.app.tabs.state(('!'+state,))
