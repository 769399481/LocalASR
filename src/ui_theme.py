"""Shared presentation tokens and native ttk styling; no Core dependencies."""
from tkinter import ttk, font
from ui_shapes import install_round_element, replace_element, switch_image

COLORS = dict(background='#F8FBFF', surface='#FFFFFF', surface_alt='#F2F7FC',
              primary='#4D86C6', primary_hover='#4177B5', primary_pressed='#37679E',
              primary_soft='#EEF6FF', text_primary='#1F2937', text_secondary='#6B7280',
              border='#DDE7F0', focus='#91B6DD', success='#377D62', warning='#94702C',
              error='#AD4149', disabled='#A6B0BD', overlay='#20262E', overlay_text='#FFFFFF')
SPACE = dict(xs=4, s=8, m=12, l=16, xl=24, xxl=32)
TYPE = dict(title=17, section=11, body=10, helper=9, transcript=11)
CONTROL = dict(border=1, button_padding=(12, 4), input_padding=(8, 4),
               tab_padding=(16, 8), row_height=32)
RADIUS = dict(control=8, button=12, surface=16)
FORM = dict(label_width=10)
SHADOW = dict(edge='#E6EBF2', depth=1)

def apply_theme(root):
    family = 'Microsoft YaHei UI' if 'Microsoft YaHei UI' in font.families(root) else 'Segoe UI'
    root.configure(background=COLORS['background'])
    for name in ('TkDefaultFont', 'TkTextFont', 'TkMenuFont', 'TkHeadingFont'):
        font.nametofont(name, root=root).configure(family=family, size=TYPE['body'])
    style = ttk.Style(root)
    style.theme_use('clam')
    style.configure('.', background=COLORS['background'], foreground=COLORS['text_primary'],
                    font=(family, TYPE['body']), borderwidth=CONTROL['border'])
    style.configure('TFrame', borderwidth=0)
    style.configure('TLabel', padding=0)
    style.configure('Form.TLabel', anchor='w', width=FORM['label_width'])
    style.configure('Section.TLabel', font=(family, TYPE['section']), foreground=COLORS['text_primary'])
    style.configure('Muted.TLabel', foreground=COLORS['text_secondary'])
    style.configure('Empty.TLabel', background=COLORS['primary_soft'], foreground=COLORS['text_secondary'],
                    padding=SPACE['l'], anchor='center')
    style.configure('TButton', padding=CONTROL['button_padding'], background=COLORS['surface'],
                    bordercolor=COLORS['border'], lightcolor=COLORS['surface'], darkcolor=COLORS['surface'],
                    relief='flat', shiftrelief=0, focusthickness=1, focuscolor=COLORS['focus'])
    for name, normal, hover, pressed, foreground in (
        ('TButton', 'surface', 'primary_soft', 'border', 'text_primary'),
        ('Primary.TButton', 'primary', 'primary_hover', 'primary_pressed', 'surface'),
        ('Tertiary.TButton', 'background', 'primary_soft', 'border', 'text_secondary')):
        style.configure(name, background=COLORS[normal], foreground=COLORS[foreground])
        style.map(name, background=[('disabled', COLORS['surface_alt']), ('pressed', COLORS[pressed]), ('active', COLORS[hover])],
                  foreground=[('disabled', COLORS['disabled'])], bordercolor=[('focus', COLORS['focus']), ('active', COLORS['focus'])])
    style.configure('TNotebook', borderwidth=0, tabmargins=0, bordercolor=COLORS['background'],
                    lightcolor=COLORS['background'], darkcolor=COLORS['background'])
    style.configure('TNotebook.Tab', padding=CONTROL['tab_padding'], borderwidth=1,
                    background=COLORS['background'], bordercolor=COLORS['border'],
                    lightcolor=COLORS['border'], darkcolor=COLORS['border'])
    # clam expands selected tabs by default. Keep every state's allocation fixed.
    style.map('TNotebook.Tab', expand=[('selected', (0, 0, 0, 0)), ('!selected', (0, 0, 0, 0))],
              padding=[('selected', CONTROL['tab_padding']), ('!selected', CONTROL['tab_padding'])],
              background=[('selected', COLORS['primary_soft']), ('active', COLORS['surface_alt'])],
              foreground=[('selected', COLORS['primary_pressed']), ('disabled', COLORS['disabled'])])
    # The clam indicator draws an X. Borrow Windows' actual checkbox renderer,
    # not a Unicode glyph (which depends on font fallback).
    source = 'vista' if 'vista' in style.theme_names() else 'alt'
    if 'NativeCheck.indicator' not in style.element_names():
        style.element_create('NativeCheck.indicator', 'from', source, 'Checkbutton.indicator')
    layout = [('Checkbutton.padding', {'sticky': 'nswe', 'children': [
        ('NativeCheck.indicator', {'side': 'left', 'sticky': ''}),
        ('Checkbutton.focus', {'side': 'left', 'sticky': 'w', 'children': [
            ('Checkbutton.label', {'sticky': 'nswe'})]})]})]
    for name in ('TCheckbutton', 'Toggle.TCheckbutton'):
        style.layout(name, layout)
        style.configure(name, padding=(SPACE['xs'], SPACE['xs']), indicatorrelief='flat')
        style.map(name, foreground=[('disabled', COLORS['disabled'])],
                  background=[('active', COLORS['primary_soft'])])
    root.checkbox_indicator_source = source
    for name in ('TCombobox', 'TEntry'):
        style.configure(name, padding=CONTROL['input_padding'], fieldbackground=COLORS['surface'],
                        background=COLORS['surface_alt'], bordercolor=COLORS['border'],
                        lightcolor=COLORS['border'], darkcolor=COLORS['border'], arrowsize=12)
        style.map(name, fieldbackground=[('readonly', COLORS['surface']), ('disabled', COLORS['surface_alt'])],
                  foreground=[('disabled', COLORS['disabled'])], bordercolor=[('focus', COLORS['focus'])])
    style.configure('Treeview', rowheight=CONTROL['row_height'], background=COLORS['surface'],
                    fieldbackground=COLORS['surface'], borderwidth=0)
    style.map('Treeview', background=[('selected', COLORS['primary_soft'])], foreground=[('selected', COLORS['text_primary'])])
    style.configure('Treeview.Heading', padding=SPACE['xs'], background=COLORS['surface_alt'],
                    borderwidth=0, relief='flat', foreground=COLORS['text_secondary'])
    style.configure('TLabelframe', borderwidth=0, relief='flat')
    style.configure('TLabelframe.Label', foreground=COLORS['text_secondary'])
    style.configure('TSeparator', background=COLORS['border'])
    style.configure('Horizontal.TProgressbar', background=COLORS['primary'], troughcolor=COLORS['primary_soft'], borderwidth=0)
    # Native ttk widgets retain keyboard, focus, command and disabled handling.
    # All state images have identical dimensions and identical nine-slice borders.
    for name, normal, hover, pressed in (
            ('TButton', 'surface', 'primary_soft', 'border'),
            ('Primary.TButton', 'primary', 'primary_hover', 'primary_pressed'),
            ('Tertiary.TButton', 'background', 'primary_soft', 'border')):
        element = name.replace('.', '') + '.round'
        fills = (normal, 'surface_alt', pressed, normal, hover, normal)
        colors = [(COLORS[key], COLORS['focus'] if i == 5 else COLORS[key]) for i,key in enumerate(fills)]
        install_round_element(root, style, element, colors, RADIUS['button'])
        base = [('Button.border', {'sticky':'nswe', 'children':[
            ('Button.padding', {'sticky':'nswe', 'children':[
                ('Button.label', {'sticky':'nswe'})]})]})]
        style.layout(name, replace_element(base, 'Button.border', element))
    install_round_element(root, style, 'Segment.round', [
        (COLORS[key], SHADOW['edge'] if i == 3 else COLORS[key])
        for i,key in enumerate(('surface_alt','surface_alt','primary_soft','primary_soft','surface','surface'))], RADIUS['control'])
    style.layout('TNotebook.Tab', [('Segment.round', {'sticky':'nswe', 'children':[
        ('Notebook.padding', {'sticky':'nswe', 'children':[
            ('Notebook.focus', {'sticky':'nswe', 'children':[
                ('Notebook.label', {'sticky':'nswe'})]})]})]})])
    if 'Switch.indicator' not in style.element_names():
        images = [switch_image(root, COLORS[color], COLORS['surface'], selected)
                  for color,selected in (('border',False),('primary',True),('disabled',False),('disabled',True))]
        root._rounded_images.extend(images)
        style.element_create('Switch.indicator', 'image', images[0],
                             ('disabled','selected',images[3]), ('disabled',images[2]), ('selected',images[1]), sticky='w')
    style.layout('Toggle.TCheckbutton', replace_element(layout, 'NativeCheck.indicator', 'Switch.indicator'))
    install_round_element(root, style, 'Drop.round', [(COLORS['primary_soft'],COLORS['primary_soft'])]*6, RADIUS['surface']-1)
    style.layout('Drop.TFrame', [('Drop.round', {'sticky':'nswe'})])
    style.configure('Drop.TFrame', background=COLORS['primary_soft'])
    install_round_element(root, style, 'Input.round', [
        (COLORS['surface_alt'] if i == 1 else COLORS['surface'], COLORS['focus'] if i == 5 else COLORS['border'])
        for i in range(6)], RADIUS['control'])
    for name, element in (('TEntry','Entry.field'), ('TCombobox','Combobox.field')):
        style.layout(name, replace_element(style.layout(name), element, 'Input.round'))
    install_round_element(root, style, 'Reading.round', [(COLORS['surface'],SHADOW['edge'])]*6, RADIUS['surface']-1)
    style.layout('Reading.TLabelframe', [('Reading.round', {'sticky':'nswe'})])
    style.configure('Reading.TLabelframe', background=COLORS['surface'])
    return style
