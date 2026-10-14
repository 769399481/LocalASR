from ui_strings import tr
"""Presentation adapters; Core configuration retains its stable identifiers."""
import logging
import tkinter as tk
from tkinter import ttk, font
from ui_strings import tr
CHOICES = {'English': tr('ui_171'), 'Chinese': tr('ui_041'), 'Auto': tr('ui_172'), 'Fast': tr('ui_014'), 'Balanced': tr('ui_015'), 'Accurate': tr('ui_016'), 'Microphone': tr('ui_173'), 'System Audio': tr('ui_174'), 'Bilingual': tr('ui_043'), tr('ui_041'): tr('ui_041'), 'Default microphone': tr('ui_175')}

class ChoiceBox(ttk.Combobox):
    """Translate display labels without changing saved settings or worker APIs."""

    def __init__(self, master, *, textvariable, values=(), labels=None, **kw):
        self.code = textvariable
        self.labels = labels or CHOICES
        self.display = tk.StringVar(master)
        super().__init__(master, textvariable=self.display, **kw)
        self.configure(values=values)
        self.token = self.code.trace_add('write', self.refresh)
        self.bind('<<ComboboxSelected>>', self.select_code)
        self.bind('<Destroy>', self.dispose, add='+')
        self.refresh()

    def refresh(self, *_):
        self.display.set(self.labels.get(self.code.get(), self.code.get()))

    def select_code(self, _):
        self.code.set(next((k for k in self.codes if self.labels.get(k, k) == self.display.get()), self.display.get()))

    def configure(self, cnf=None, **kw):
        if 'values' in kw:
            self.codes = tuple(kw['values'])
            kw['values'] = tuple((self.labels.get(k, k) for k in self.codes))
        return super().configure(cnf, **kw)

    def dispose(self, event):
        if event.widget is self:
            self.code.trace_remove('write', self.token)

from ui_theme import apply_theme

def create_root():
    from desktop_platform import enable_dpi_awareness
    enable_dpi_awareness()
    try:
        from tkinterdnd2 import TkinterDnD
        return TkinterDnD.Tk()
    except (ImportError, RuntimeError, tk.TclError):
        logging.getLogger(__name__).exception('Native drop unavailable')
        return tk.Tk()

def install_drop(widget, callback):
    try:
        from tkinterdnd2 import DND_FILES, COPY
        widget.drop_target_register(DND_FILES)
        def dropped(event):
            callback(widget.tk.splitlist(event.data))
            return COPY
        widget.dnd_bind('<<Drop>>', dropped)
        return True
    except (AttributeError, ImportError, tk.TclError):
        return False

def file_state(state):
    return tr('state_' + state.lower())

def model_name(model_id):
    return tr({'small': 'model_fast', 'large-v3': 'model_accurate', 'opus-mt-en-zh': 'model_translation'}[model_id])
