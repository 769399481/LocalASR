"""Opt-in source/frozen visual acceptance; never imported by ordinary GUI flow."""
from tkinter import ttk, TclError
from ui_theme import COLORS, apply_theme

def inspect_visual(app):
    root, tabs = app.root, app.tabs
    selected = tabs.select()
    def geometry(widget):
        root.update_idletasks()
        return (widget.winfo_x(), widget.winfo_y(), widget.winfo_width(), widget.winfo_height(),
                widget.winfo_reqwidth(), widget.winfo_reqheight())
    def spans():
        result = {}
        for x in range(tabs.winfo_width()):
            try:
                index = tabs.index(f'@{x},10')
                result.setdefault(index, []).append(x)
            except TclError:
                pass
        return {str(k): (min(v), max(v)) for k,v in result.items()}
    tabs.select(app.file_page)
    root.update_idletasks()
    first = spans()
    tabs.select(app.live_page)
    root.update_idletasks()
    second = spans()
    tabs.select(app.file_page)
    def walk(widget):
        yield widget
        for child in widget.winfo_children():
            yield from walk(child)
    checked, failures = 0, []
    for widget in walk(app.file_page):
        if isinstance(widget, (ttk.Button, ttk.Checkbutton, ttk.Combobox)):
            original = widget.state()
            baseline = geometry(widget)
            for state in ('active', 'pressed', 'disabled', 'selected', 'focus'):
                widget.state(('!active','!pressed','!disabled','!selected','!focus',state))
                if geometry(widget) != baseline:
                    failures.append((str(widget),state))
            widget.state(('!active','!pressed','!disabled','!selected','!focus',*original))
            checked += 1
    tabs.select(selected)
    style = ttk.Style(root)
    geometry_before = root.geometry()
    maxsize_before = root.maxsize()
    scaling_before = float(root.tk.call('tk','scaling'))
    layouts = []
    try:
        # Permit off-screen controlled geometry on a smaller physical display.
        root.maxsize(max(1920,maxsize_before[0]),max(1080,maxsize_before[1]))
        for scale in (1,1.25,1.5):
            root.tk.call('tk','scaling',scale*96/72)
            apply_theme(root)
            for size in ('880x600','1366x768','1920x1080'):
                root.geometry(size)
                tabs.select(app.file_page)
                root.update()
                footer_ok = app.file_footer.winfo_rooty()+app.file_footer.winfo_height() <= app.footer.winfo_rooty()
                labels = [row.winfo_children()[0] for row in app.file_settings.winfo_children()]
                aligned = len({label.winfo_rootx() for label in labels}) == 1
                tabs.select(app.live_page)
                root.update_idletasks()
                layouts.append(dict(scale=scale,size=size,actual_width=root.winfo_width(),actual_height=root.winfo_height(),footer_visible=footer_ok,
                                    labels_aligned=aligned,transcript_height=app.panes.winfo_height()))
    finally:
        root.tk.call('tk','scaling',scaling_before)
        apply_theme(root)
        root.maxsize(*maxsize_before)
        root.geometry(geometry_before)
        tabs.select(selected)
        root.update_idletasks()
    layout_passed = all(x['footer_visible'] and x['labels_aligned'] and x['transcript_height'] > 100 for x in layouts)
    return {'navigation_geometry_equal': first == second and len(first) == 2,
            'tab_spans': first, 'controls_checked': checked, 'geometry_failures': failures,
            'checkbox_renderer': root.checkbox_indicator_source,
            'checkbox_native_element': 'NativeCheck.indicator' in str(style.layout('TCheckbutton')),
            'primary_soft': style.lookup('TNotebook.Tab','background',('selected',)),
            'controlled_layouts':layouts, 'layout_passed':layout_passed,
            'rounded_elements': 'Segment.round' in style.element_names(),
            'toggle_element': 'Switch.indicator' in str(style.layout('Toggle.TCheckbutton')),
            'passed': first == second and len(first) == 2 and not failures and layout_passed
                      and style.lookup('TNotebook.Tab','background',('selected',)) == COLORS['primary_soft']}
