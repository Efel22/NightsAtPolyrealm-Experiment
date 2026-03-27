from ursina import color
from .shared import add_slab


def build_ocean_impostor(size, avg_h, rng, bot=-60.0):
    verts=[]; tris=[]; cols=[]; idx=0
    # top_c  = (0.055, 0.220, 0.420, 1)
    # side_c = (0.020, 0.080, 0.180, 1)
    # from ursina import color as uc
    # top_col  = uc.rgba(*top_c)
    # side_col = uc.rgba(*side_c)
    # idx = add_slab(verts,tris,cols,idx, 0,0, size,size,
    #                avg_h, bot, top_col, side_col)
    return verts, tris, cols