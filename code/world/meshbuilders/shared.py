import random
from ursina import color

from code.world.color_settings import *

# --- VARY_COL() ---
# ?: Allows for variagion on the color (in the + AND - )
def vary_col(r, g, b, amount=0.08):
    v = random.uniform(-amount, amount)
    return (max(0.0, min(1.0, r+v)),
            max(0.0, min(1.0, g+v)),
            max(0.0, min(1.0, b+v)))

def tint_variation(color_tuple, amount=0.08):
    """
    Takes a color tuple, adds a random tint, and returns a color.rgba object.
    """
    # 1. Grab the values from the tuple by index (since tuples don't have .r, .g, .b)
    # color_tuple[0] is Red, [1] is Green, [2] is Blue
    r = color_tuple[0]
    g = color_tuple[1]
    b = color_tuple[2]
    
    # 2. Get the Alpha (A) if it exists, otherwise default to 1.0
    a = color_tuple[3] if len(color_tuple) > 3 else 1.0
    
    # 3. Generate the random offset
    variation = random.uniform(-amount, amount)
    
    # 4. Return the official color object using your engine's rgba function
    # We use max(0.0) and min(1.0) to make sure the color stays in a valid range
    return color.rgba(
        max(0.0, min(1.0, r + variation)),
        max(0.0, min(1.0, g + variation)),
        max(0.0, min(1.0, b + variation)),
        a
    )

def darken(col, factor):

    """
    Unified darken function: Accepts a color object (with .r, .g, .b) 
    OR a tuple (r, g, b, [a]). Returns a color.rgba object.
    """
    # 1. Detect if 'col' is a tuple/list or an object
    if isinstance(col, (tuple, list)):
        r = col[0]
        g = col[1]
        b = col[2]
        a = col[3] if len(col) > 3 else 1.0
    else:
        # Assume it's a color object with .r, .g, .b, .a attributes
        r, g, b, a = col.r, col.g, col.b, col.a

    # 2. Apply factor and clamp between 0.0 and 1.0
    # This prevents 'over-brightening' or negative color values
    new_r = max(0.0, min(1.0, r * factor))
    new_g = max(0.0, min(1.0, g * factor))
    new_b = max(0.0, min(1.0, b * factor))

    # 3. Return the official engine color object
    return color.rgba(new_r, new_g, new_b, a)

    # """
    # Darkens a color by multiplying RGB values.
    # factor < 1.0 = darker
    # """
    # return color.rgba(
    #     col.r * factor,
    #     col.g * factor,
    #     col.b * factor,
    #     col.a
    # )

def darken_tuple(color_tuple, factor):
    """
    Takes a color tuple, adds a random tint, and returns a color.rgba object.
    """
    # 1. Grab the values from the tuple by index (since tuples don't have .r, .g, .b)
    # color_tuple[0] is Red, [1] is Green, [2] is Blue
    r = color_tuple[0]
    g = color_tuple[1]
    b = color_tuple[2]
    
    # 2. Get the Alpha (A) if it exists, otherwise default to 1.0
    a = color_tuple[3] if len(color_tuple) > 3 else 1.0
    
    # 3. Return the official color object using your engine's rgba function
    # We use max(0.0) and min(1.0) to make sure the color stays in a valid range
    return color.rgba(
        max(0.0, min(1.0, r * factor)),
        max(0.0, min(1.0, g * factor)),
        max(0.0, min(1.0, b * factor)),
        a
    )


def add_box(verts, tris, cols, idx, cx, cy, cz, sx, sy, sz, col):
    hx = sx/2; hy = sy/2; hz = sz/2

    # Full brightness for top, darkened for sides, very dark for bottom
    top_col   = color.rgba(col[0],        col[1],        col[2],        1)
    side_col  = color.rgba(col[0] * 0.75, col[1] * 0.75, col[2] * 0.75, 1)
    bot_col   = color.rgba(col[0] * 0.45, col[1] * 0.45, col[2] * 0.45, 1)

    faces = [
        # TOP    (+Y), brightest
        [(-hx, hy,-hz), (-hx, hy, hz), ( hx, hy, hz), ( hx, hy,-hz)],  darken(top_col, 1.05),

        # BOTTOM (-Y), darkest (rarely seen)
        [(-hx,-hy,-hz), ( hx,-hy,-hz), ( hx,-hy, hz), (-hx,-hy, hz)],  darken(bot_col, 0.90),

        # SOUTH  (+Z), side
        [(-hx,-hy, hz), ( hx,-hy, hz), ( hx, hy, hz), (-hx, hy, hz)],  darken(side_col, 0.98),

        # NORTH  (-Z), side
        [( hx,-hy,-hz), (-hx,-hy,-hz), (-hx, hy,-hz), ( hx, hy,-hz)],  side_col,

        # WEST   (-X), side
        [(-hx,-hy,-hz), (-hx,-hy, hz), (-hx, hy, hz), (-hx, hy,-hz)],  darken(side_col, 0.97),

        # EAST   (+X), side
        [( hx,-hy, hz), ( hx,-hy,-hz), ( hx, hy,-hz), ( hx, hy, hz)],  darken(side_col, 0.97),
    ]

    i = 0
    while i < len(faces):
        face_verts = faces[i]
        face_col   = faces[i + 1]
        i += 2
        for (fx, fy, fz) in face_verts:
            verts.append((cx+fx, cy+fy, cz+fz))
            cols.append(face_col)
        tris.append((idx, idx+1, idx+2, idx+3))
        idx += 4

    return idx