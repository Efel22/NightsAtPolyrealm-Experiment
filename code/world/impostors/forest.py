import math
from ursina import color
from .shared import add_slab
from code.world.meshbuilders.shared import *
from code.world.color_settings import *
from code.world.world_settings import CHUNK_SIZE
 
def build_forest_impostor(size, avg_h, rng, bot=-60.0):
    """
    Forest: rolling ground with trees whose canopy matches the real tree —
    nearly cubic leaf blobs (ls*1.1 wide × ls*0.9 tall × ls*1.1 deep).
    Multiple shades of green across trees.
    """
    verts=[]; tris=[]; cols=[]; idx=0

    # -- Colors -----------------------------------------------------------
    ground  = color.rgba(*BIOME_TOP_COLOR[FOREST], 1)   # ground top
    g_side  = darken(BIOME_TOP_COLOR[FOREST],rng.uniform(0.75,0.85))
    
    # --- SIZE-DEPENDENT VALUES ---
    # Check if the Imps_Chunk_To_Create is larger than a regular chunk 
    # (which means its 5x5)
    if size > CHUNK_SIZE:
        amount_ground_rolls = rng.randint(6, 9) 
        amount_trees = rng.randint(10, 20)
        hill_height_min = 1.5 # Hill Height MIN
        hill_height_max = 5.5 # Hill Height MAX
    else: # Regular Chunk values (1x1 sized) 
        # amount_ground_rolls = rng.randint(2, 3)
        amount_ground_rolls = 0
        amount_trees = rng.randint(3, 5)
        hill_height_min = 0.5 # Hill Height MIN
        hill_height_max = 2.25 # Hill Height MAX
        g_side  = darken(BIOME_SIDE_COLOR[FOREST],rng.uniform(0.75,0.85))

    # build_grass_mesh(verts, tris, cols, idx, size, avg_h, size, BIOME_GRASS_COLOR[FOREST], FOREST, rng)

    # -- Base ground slab -------------------------------------------------
    idx = add_slab(verts,tris,cols,idx, 0,0, size,size,
                   avg_h, bot, 
                   darken(ground, rng.uniform(0.85,0.95)), 
                   darken(g_side, rng.uniform(0.75,0.85))
                   )

        


    # -- Ground rolls -----------------------------------------------------
    for _ in range(amount_ground_rolls):
        margin = size * 0.1
        cx = rng.uniform(margin, size-margin)   # hill centre X (local)
        cz = rng.uniform(margin, size-margin)   # hill centre Z (local)
        hw = rng.uniform(size*0.08, size*0.18)  # hill half-width (spreads with slab)
        ht = rng.uniform(hill_height_min, hill_height_max)                        # hill height in world units
        idx = add_slab(verts,tris,cols,idx,
                       cx-hw, cz-hw, cx+hw, cz+hw,
                       avg_h+ht, bot, 
                       darken(BIOME_TOP_COLOR[FOREST],rng.uniform(0.85,1.0)),  # TOP COLOR
                       darken(BIOME_TOP_COLOR[FOREST],rng.uniform(0.73,0.80)) # SIDE COLOR
                       )

    # -- Forest trees -----------------------------------------------------
    # Trunk + nearly-cubic canopy blob matching the real tree proportions:
    #   real canopy = ls*1.1 wide × ls*0.9 tall × ls*1.1 deep
    for _ in range(amount_trees):
        margin = size * 0.05
        cx = rng.uniform(margin, size-margin)   # tree centre X (local)
        cz = rng.uniform(margin, size-margin)   # tree centre Z (local)

        tw  = rng.uniform(0.4, 0.8)    # trunk half-width (square cross-section)
        th  = rng.uniform(4.0, 9.0)    # trunk height in world units
        ls  = rng.uniform(2.7, 4.5)    # leaf scale — increase for bigger canopy
        cw  = ls * 1.1                 # canopy half-width  (matches real: ls*1.1)
        ch  = ls * 1.9                 # canopy height      (matches real: ls*0.9, nearly cubic)
        tt  = avg_h + th               # Y at the top of the trunk

        # Trunk — square slab from ground up to tt
        idx = add_slab(verts,tris,cols,idx,
                       cx-tw, cz-tw, cx+tw, cz+tw,
                       tt + 2, avg_h, 
                       darken(COLOR__FOREST_TREE_TRUNK, rng.uniform(0.5, 0.8)), 
                       darken(COLOR__FOREST_TREE_TRUNK, rng.uniform(0.5, 0.8))
                       )

        # Canopy — wide flat box centred above the trunk top
        # The box centre is at tt + ch*0.5, half-height = ch*0.5
        # so it runs from tt + ch*0.1  to  tt + ch*1.1
        idx = add_slab(verts,tris,cols,idx,
                       cx-cw, cz-cw, cx+cw, cz+cw,
                       tt+ch*0.5+ch*0.6,   # canopy top    (tt + ch*1.1)
                       tt+ch*0.5-ch*0.4,   # canopy bottom (tt + ch*0.1)
                       darken(COLOR__FOREST_TREE_LEAVES, rng.uniform(0.7,1.0)), 
                       darken(COLOR__FOREST_TREE_LEAVES, rng.uniform(0.7,1.0)),
                       True
                       )

    return verts, tris, cols
