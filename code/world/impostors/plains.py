import math
from ursina import color
from .shared import *
from code.world.world_settings import CHUNK_SIZE



def build_plains_impostor(size, avg_h, rng, bot=-60.0):
    """
    Gently rolling hills with sparse trees.
    Trees match the real plains tree: trunk + nearly-cubic canopy (ls*1.1 x ls*0.9).
    """
    verts=[]; tris=[]; cols=[]; idx=0

    # -- Colors -----------------------------------------------------------
    base_col  = color.rgba(*BIOME_TOP_COLOR[PLAINS], 1)   # ground top
    side_col  = darken(BIOME_TOP_COLOR[PLAINS],rng.uniform(0.75,0.85))
    
    # --- SIZE-DEPENDENT VALUES ---
    # Check if the Imps_Chunk_To_Create is larger than a regular chunk 
    # (which means its 5x5)
    if size > CHUNK_SIZE:
        amount_ground_rolls = rng.randint(5, 8) 
        amount_trees = rng.randint(5, 9)
        hill_height_min = 1.5 # Hill Height MIN
        hill_height_max = 4.0 # Hill Height MAX
    else: # Regular Chunk values (1x1 sized) 
        amount_ground_rolls = 0
        amount_trees = rng.randint(1, 3)
        side_col  = darken(BIOME_SIDE_COLOR[PLAINS],rng.uniform(0.75,0.85))
 
    # -- Base ground slab -------------------------------------------------
    # Covers the entire impostor footprint from avg_h down to bot
    idx = add_slab(verts,tris,cols,idx, 0,0, size,size,
                   avg_h, bot,  
                   darken(base_col, rng.uniform(0.85,0.95)), 
                   darken(side_col, rng.uniform(0.75,0.85))
                   )

    # -- Scattered low mounds (rolling hills) -----------------------------
    for _ in range(amount_ground_rolls):
        margin = size * 0.15          # keep mounds away from the slab edges
        cx = rng.uniform(margin, size-margin)   # mound centre X (local)
        cz = rng.uniform(margin, size-margin)   # mound centre Z (local)
        hw = rng.uniform(size*0.08, size*0.18)  # mound half-width in X
        hz = rng.uniform(size*0.08, size*0.18)  # mound half-width in Z
        ht = rng.uniform(hill_height_min, hill_height_max)   # how many units the mound rises above avg_h
        idx = add_slab(verts,tris,cols,idx,
                       cx-hw, cz-hz, cx+hw, cz+hz,
                       avg_h+ht, bot, 
                       darken(BIOME_TOP_COLOR[PLAINS],rng.uniform(0.9,1.0)),  # TOP COLOR
                       darken(BIOME_TOP_COLOR[PLAINS],rng.uniform(0.83,0.87)) # SIDE COLOR
                       )

    # -- Sparse trees -----------------------------------------------------
    for _ in range(amount_trees):
        margin = size * 0.08
        cx = rng.uniform(margin, size-margin)   # tree centre X (local)
        cz = rng.uniform(margin, size-margin)   # tree centre Z (local)

        tw  = rng.uniform(0.3, 0.6)    # trunk half-width (X and Z, trunk is square)
        th  = rng.uniform(2.5, 4.5)    # trunk height in world units
        ls  = rng.uniform(2.0, 3.0)    # leaf scale — controls canopy size
        cw  = ls * 1.1                 # canopy half-width  (real tree uses ls*1.1)
        ch  = ls * 1.9                 # canopy height      (real tree uses ls*0.9, nearly cubic)
        tt  = avg_h + th               # Y position of the top of the trunk

        # Trunk — thin vertical slab from ground up to tt
        idx = add_slab(verts,tris,cols,idx,
                       cx-tw, cz-tw, cx+tw, cz+tw,
                       tt + 2, avg_h, 
                       darken_tuple(COLOR__PLAINS_TREE_TRUNK, rng.uniform(0.8, 1.1)), # Top (the top color doesn't really matter )
                       darken_tuple(COLOR__PLAINS_TREE_TRUNK, rng.uniform(0.8, 1.1))) # Sides ()

        # Canopy — wide flat box sitting on top of the trunk
        # bottom of canopy = tt + ch*0.6 - ch*0.4 = tt + ch*0.2
        # top   of canopy = tt + ch*0.6 + ch*0.4 = tt + ch*1.0
        idx = add_slab(verts,tris,cols,idx,
                       cx-cw, cz-cw, cx+cw, cz+cw,
                       tt+ch*0.6+ch*0.4, tt+ch*0.6-ch*0.4,
                       darken_tuple(COLOR__PLAINS_TREE_LEAVES, rng.uniform(0.8, 1.1)), # Top Color (doesnt really matter?, unless viewed from above)
                       darken_tuple(COLOR__PLAINS_TREE_LEAVES, rng.uniform(0.55, 0.8)), # Side Color
                       True)

    return verts, tris, cols
