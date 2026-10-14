from ui_theme import COLORS, SPACE, TYPE, CONTROL
from ui_strings import tr
"""Bounded display projection only. The realtime document owns all saved content."""
from collections import OrderedDict
from dataclasses import dataclass
import sys
import tkinter as tk
from tkinter import ttk
from desktop_platform import DesktopPlatform, monitor_rect

@dataclass
class OverlayPreferences:
    mode: str = 'Bilingual'
    font_size: int = 22
    opacity: float = 0.85
    transparent: bool = False
    position: str = 'Bottom'
    x: int | None = None
    y: int | None = None
    width: int = 850

    def validate(self):
        if self.mode not in ('English', tr('ui_041'), 'Bilingual') or self.position not in ('Top', 'Bottom', 'Custom'):
            raise ValueError(tr('overlay_invalid'))
        if not 12 <= self.font_size <= 48 or not 0.2 <= self.opacity <= 1 or (not 350 <= self.width <= 1800):
            raise ValueError(tr('overlay_invalid'))

class SubtitleState:

    def __init__(self):
        self.reset()

    def reset(self):
        self.session_id = None
        self.finals = OrderedDict()
        self.partial = ''
        self.last_final = 0
        self.early = {}

    def update(self, event):
        if self.session_id is None:
            self.session_id = event.session_id
        if event.session_id != self.session_id:
            return
        if event.kind == 'partial_transcript' and event.utterance_id > self.last_final:
            self.partial = event.text
        elif event.kind == 'final_transcript' and event.utterance_id > self.last_final:
            self.last_final = event.utterance_id
            self.finals[event.utterance_id] = [event.text, self.early.pop(event.utterance_id, '')]
            self.partial = ''
            while len(self.finals) > 2:
                self.finals.popitem(last=False)
        elif event.kind == 'translation_completed' and event.utterance_id in self.finals:
            self.finals[event.utterance_id][1] = event.translated_text
        elif event.kind == 'translation_completed' and event.utterance_id > self.last_final:
            if len(self.early) < 8:
                self.early[event.utterance_id] = event.translated_text
        elif event.kind == 'stopped':
            self.partial = ''

    def text(self, mode):
        lines = []
        history = list(self.finals.values())
        if self.partial and mode != tr('ui_041'):
            history = history[-1:]
        for original, translated in history:
            if mode != tr('ui_041'):
                lines.append(original)
            if mode != 'English' and translated:
                lines.append(translated)
        if self.partial and mode != tr('ui_041'):
            lines.append(self.partial)
        return '\n'.join(lines)

class SubtitleOverlay:

    def __init__(self, root, preferences=None, on_change=None):
        self.preferences = preferences or OverlayPreferences()
        self.preferences.validate()
        self.on_change = on_change or (lambda: None)
        self.state = SubtitleState()
        self.native = DesktopPlatform()
        self.translation_enabled = True
        self.visible = False
        self.watch = False
        self.window = tk.Toplevel(root)
        self.window.title(tr('overlay_title'))
        self.window.withdraw()
        self.window.overrideredirect(True)
        self.window.attributes('-topmost', True)
        self.window.configure(bg=COLORS['overlay'])
        self.bar = ttk.Frame(self.window)
        self.bar.pack(fill='x')
        self.buttons = []
        for label, command in ((tr('ui_161'), self.cycle), (tr('ui_162'), lambda: self.font(-2)), (tr('ui_163'), lambda: self.font(2)), (tr('ui_164'), self.transparency), (tr('ui_165'), lambda: self.place('Top')), (tr('ui_166'), lambda: self.place('Bottom')), (tr('ui_167'), lambda: self.set_watch(True)), (tr('ui_168'), self.hide)):
            button = ttk.Button(self.bar, text=label, command=command, width=6, padding=2)
            self.buttons.append(button)
        self.opacity = tk.DoubleVar(value=self.preferences.opacity)
        self.opacity_scale = ttk.Scale(self.bar, from_=0.2, to=1, variable=self.opacity, command=self.set_opacity)
        self.opacity_label = ttk.Label(self.bar, text=tr('opacity'))
        self.label = tk.Label(self.window, fg=COLORS['overlay_text'], bg=COLORS['overlay'], justify='center', padx=SPACE['m'], pady=SPACE['s'])
        self.label.pack(fill='both', expand=True)
        self.grip = tk.Label(self.window, text=tr('ui_169'), bg=COLORS['overlay'], fg=COLORS['disabled'])
        self.grip.pack(fill='x')
        self.label.bind('<ButtonPress-1>', self.drag_start)
        self.label.bind('<B1-Motion>', self.drag)
        self.label.bind('<ButtonRelease-1>', lambda e: self.on_change())
        self.grip.bind('<ButtonPress-1>', self.resize_start)
        self.grip.bind('<B1-Motion>', self.resize)
        self.grip.bind('<ButtonRelease-1>', lambda e: self.on_change())
        self.window.update_idletasks()
        self.render()

    def render(self):
        p = self.preferences
        columns = 8 if p.width >= 650 else 4
        for i, button in enumerate(self.buttons):
            button.grid(row=i // columns, column=i % columns, sticky='ew')
        for i in range(8):
            self.bar.columnconfigure(i, weight=1 if i < columns else 0)
        self.opacity_label.grid(row=(len(self.buttons) - 1) // columns + 1, column=0)
        self.opacity_scale.grid(row=(len(self.buttons) - 1) // columns + 1, column=1, columnspan=columns - 1, sticky='ew', padx=SPACE['s'])
        self.buttons[0].configure(text={'English': tr('ui_042'), tr('ui_041'): tr('ui_041'), 'Bilingual': tr('ui_043')}[p.mode])
        self.label.configure(text=self.state.text(p.mode) or (tr('ui_170') if not self.watch else ''), font=('Microsoft YaHei UI', p.font_size), wraplength=p.width - 30)
        self.window.attributes('-alpha', p.opacity)
        if sys.platform == 'win32':
            self.window.attributes('-transparentcolor', COLORS['overlay'] if p.transparent else '')
        if self.visible:
            self.window.update_idletasks()
            if p.position in ('Top', 'Bottom'):
                self.place(p.position)
            else:
                self.geometry(self.window.winfo_x(), self.window.winfo_y())

    def update(self, event):
        self.state.update(event)
        self.render()

    def show(self):
        self.visible = True
        self.window.deiconify()
        self.window.update_idletasks()
        if self.preferences.position == 'Custom' and self.preferences.x is not None:
            self.geometry(self.preferences.x, self.preferences.y or 0)
        else:
            self.place(self.preferences.position)
        self.window.lift()

    def hide(self):
        self.visible = False
        self.window.withdraw()

    def geometry(self, x, y):
        left, top, right, bottom = monitor_rect(self.window)
        height = min(self.window.winfo_reqheight(), max(120, bottom - top - 20))
        y = max(top, min(y, bottom - height))
        x = max(left, min(x, right - min(self.preferences.width, right - left)))
        self.window.geometry(f'{self.preferences.width}x{height}+{int(x)}+{int(y)}')

    def place(self, position):
        self.preferences.position = position
        left, top, right, bottom = monitor_rect(self.window if self.visible else self.window.master)
        x = left + max(0, (right - left - self.preferences.width) // 2)
        y = top + 40 if position == 'Top' else bottom - self.window.winfo_reqheight() - 50
        self.geometry(x, y)
        self.on_change()

    def set_watch(self, enabled):
        if enabled and (not self.native.supports_click_through):
            return False
        self.native.click_through(self.window, enabled)
        self.watch = enabled
        if enabled:
            self.bar.pack_forget()
            self.grip.pack_forget()
        else:
            self.bar.pack(before=self.label, fill='x')
            self.grip.pack(fill='x')
        self.render()
        self.window.update_idletasks()
        self.geometry(self.window.winfo_x(), self.window.winfo_y())
        return True

    def cycle(self):
        modes = ('English', tr('ui_041'), 'Bilingual') if self.translation_enabled else ('English',)
        if self.preferences.mode not in modes:
            self.preferences.mode = modes[0]
        self.preferences.mode = modes[(modes.index(self.preferences.mode) + 1) % len(modes)]
        self.render()
        self.on_change()

    def font(self, delta):
        self.preferences.font_size = min(48, max(12, self.preferences.font_size + delta))
        self.render()
        self.window.update_idletasks()
        self.geometry(self.window.winfo_x(), self.window.winfo_y())
        self.on_change()

    def transparency(self):
        self.preferences.transparent = not self.preferences.transparent
        self.render()
        self.on_change()

    def set_opacity(self, value):
        self.preferences.opacity = float(value)
        self.render()
        self.on_change()

    def drag_start(self, event):
        self.origin = (event.x_root - self.window.winfo_x(), event.y_root - self.window.winfo_y())

    def drag(self, event):
        if self.watch:
            return
        p = self.preferences
        p.position = 'Custom'
        p.x, p.y = (event.x_root - self.origin[0], event.y_root - self.origin[1])
        self.geometry(p.x, p.y)

    def resize_start(self, event):
        self.resize_origin = (event.x_root, self.preferences.width)

    def resize(self, event):
        if self.watch:
            return
        self.preferences.width = min(1800, max(350, self.resize_origin[1] + event.x_root - self.resize_origin[0]))
        self.render()
        self.geometry(self.window.winfo_x(), self.window.winfo_y())

    def close(self):
        self.native.close()
        self.window.destroy()
