"""
Shared geometry helpers for impostor chunk meshes.
All functions append into (verts, tris, cols, idx) and return updated idx.
Coordinates are LOCAL to the impostor entity (origin = impostor world pos).
"""
from ursina import color
from code.world.meshbuilders.shared import *

def shade(col_rgba, factor):
    r,g,b,a = col_rgba
    return (r*factor, g*factor, b*factor, a)

def add_quad(verts, tris, cols, idx, p0, p1, p2, p3, col):
    verts.extend([p0, p1, p2, p3])
    cols.extend([col, col, col, col])
    tris.append((idx, idx+1, idx+2, idx+3))
    return idx + 4



def add_slab(verts, tris, cols, idx, x0, z0, x1, z1, top, bot, top_col, side_col, include_bottom=False):
    tc = top_col
    sc = side_col

    # Top (+y)
    idx = add_quad(verts, tris, cols, idx,
        (x0, top, z0),
        (x1, top, z0),
        (x1, top, z1),
        (x0, top, z1),
        tc)

    # South (−z)
    idx = add_quad(verts, tris, cols, idx,
        (x1, top, z0),
        (x0, top, z0),
        (x0, bot, z0),
        (x1, bot, z0),
        sc)

    # North (+z)
    idx = add_quad(verts, tris, cols, idx,
        (x0, top, z1),
        (x1, top, z1),
        (x1, bot, z1),
        (x0, bot, z1),
        sc)

    # West (−x)
    idx = add_quad(verts, tris, cols, idx,
        (x0, top, z0),
        (x0, top, z1),
        (x0, bot, z1),
        (x0, bot, z0),
        shade(sc, 0.93))

    # East (+x)
    idx = add_quad(verts, tris, cols, idx,
        (x1, top, z1),
        (x1, top, z0),
        (x1, bot, z0),
        (x1, bot, z1),
        shade(sc, 0.93))

    if include_bottom:
        # Bottom (−y) FIX
        idx = add_quad(verts, tris, cols, idx,
            (x0, bot, z1),
            (x1, bot, z1),
            (x1, bot, z0),
            (x0, bot, z0),
            shade(sc, 0.75))

    return idx



def add_pyramid(verts, tris, cols, idx, cx, cz, base_hw, base_hz, base_y, apex_y,
                face_col, base_col):
    """Four-sided pyramid with directional brightness shading."""
    ax, az = cx, cz
    ap = (ax, apex_y, az)
    
    # Define corners
    bl = (cx - base_hw, base_y, cz - base_hz) # Back Left
    br = (cx + base_hw, base_y, cz - base_hz) # Back Right
    fr = (cx + base_hw, base_y, cz + base_hz) # Front Right
    fl = (cx - base_hw, base_y, cz + base_hz) # Front Left

    # 1. Base (bottom)
    idx = add_quad(verts, tris, cols, idx, bl, br, fr, fl, darken(base_col, 0.75))

    # 2. Define the faces and their specific brightness multipliers
    # Format: (v0, v1, brightness_multiplier)
    faces = [
        (fl, fr, 1.00), # North (+Z)
        (br, bl, 0.97), # South (-Z)
        (bl, fl, 0.95), # West  (-X)
        (fr, br, 0.95)  # East  (+X)
    ]

    for (v0, v1, brightness) in faces:
        # Calculate the shaded color for this specific face
        shaded_col = darken(face_col, brightness)
        
        verts.extend([v0, v1, ap, ap])
        cols.extend([shaded_col] * 4)
        tris.append((idx, idx + 1, idx + 2, idx + 3))
        idx += 4

    return idx

