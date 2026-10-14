"""Small Tk image elements for ttk: decoration only, native input semantics stay intact."""
import math
import tkinter as tk
RASTER_SIZE = 128


def rounded_image(root, fill, edge, radius, size=RASTER_SIZE, background='#F8FBFF'):
    if size <= 2*(radius+1):
        raise ValueError('Rounded element must retain a nonempty tile centre')
    image = tk.PhotoImage(master=root, width=size, height=size)
    image.put(background, to=(0,0,size,size))
    # Transparent corners, one-pixel outline, stretchable centre (ttk nine-slice).
    for y in range(size):
        dy = max(radius-y-0.5, y-(size-radius)+0.5, 0)
        inset = math.ceil(radius-math.sqrt(max(0, radius*radius-dy*dy))) if dy else 0
        image.put(edge, to=(inset, y, size-inset, y+1))
        if 0 < y < size-1:
            image.put(fill, to=(inset+1, y, size-inset-1, y+1))
    return image


def install_round_element(root, style, name, colors, radius):
    if name in style.element_names():
        return
    images = [rounded_image(root, fill, edge, radius) for fill, edge in colors]
    root._rounded_images = getattr(root, '_rounded_images', []) + images
    style.element_create(name, 'image', images[0], ('disabled', images[1]),
                         ('pressed', images[2]), ('selected', images[3]),
                         ('active', images[4]), ('focus', images[5]),
                         border=radius+1, padding=0, width=32, height=32, sticky='nsew')


def replace_element(layout, old, new):
    return [(new if name == old else name,
             {key: replace_element(value, old, new) if key == 'children' else value
              for key, value in options.items()}) for name, options in layout]


def switch_image(root, track, thumb, selected):
    image = tk.PhotoImage(master=root, width=36, height=20)
    for y in range(20):
        inset = math.ceil(10-math.sqrt(max(0,100-(y-9.5)**2)))
        image.put(track, to=(inset,y,36-inset,y+1))
    center = 26 if selected else 10
    for y in range(3,17):
        half = math.sqrt(max(0,49-(y-9.5)**2))
        image.put(thumb, to=(math.ceil(center-half),y,math.floor(center+half)+1,y+1))
    return image
