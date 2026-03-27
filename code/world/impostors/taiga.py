import math
from ursina import color
from .shared import *
from code.world.world_settings import CHUNK_SIZE


def build_taiga_impostor(size, avg_h, rng, bot=-60.0):
    """
    Taiga: grey-green ground with pine silhouettes.
    Each pine is two stacked pyramids — wide base layer + narrow upper layer.
    All sizes are fixed world units so they don't stretch with slab size.
    """
    verts=[]; tris=[]; cols=[]; idx=0

    # -- Colors -----------------------------------------------------------
    ground_color  = color.rgba(*BIOME_TOP_COLOR[TAIGA], 1)   # ground top
    ground_side_color  = darken(BIOME_TOP_COLOR[TAIGA],rng.uniform(0.75,0.85))
    pine_foliage_low = darken(COLOR__PINE_TREE_LEAVES, rng.uniform(0.55,0.65)) # pine foliage (dark green) (BOTTOM)
    pine_foliage_top = darken(COLOR__PINE_TREE_LEAVES, rng.uniform(0.70,0.8)) # pine foliage sides (TOP)

    
    # --- SIZE-DEPENDENT VALUES ---
    # Check if the Imps_Chunk_To_Create is larger than a regular chunk 
    # (which means its 5x5)
    if size > CHUNK_SIZE:
        amount_ground_rolls = rng.randint(6, 9) 
        amount_trees = rng.randint(24, 32)
        hill_height_min = 1.5 # Hill Height MIN
        hill_height_max = 5.5 # Hill Height MAX
        tree_height_min = 10.0 # Hill Height MIN
        tree_height_max = 22.0 # Hill Height MAX
    else: # Regular Chunk values (1x1 sized) 
        # amount_ground_rolls = rng.randint(2, 3)
        amount_ground_rolls = 0
        amount_trees = rng.randint(2, 4)
        hill_height_min = 0.5 # Hill Height MIN
        hill_height_max = 2.25 # Hill Height MAX
        tree_height_min = 7.0 # Hill Height MIN
        tree_height_max = 12.0 # Hill Height MAX
        ground_side_color  = darken(BIOME_SIDE_COLOR[TAIGA],rng.uniform(0.75,0.85))

    # -- Base ground slab -------------------------------------------------
    idx = add_slab(verts,tris,cols,idx, 0,0, size,size,
                   avg_h, bot,  
                   darken(ground_color, rng.uniform(0.85,0.95)), 
                   darken(ground_side_color, rng.uniform(0.75,0.85))
                   )

    # -- Ground rolls -----------------------------------------------------
    # Low hills — width is slab-relative so they spread, height is fixed units
    for _ in range(amount_ground_rolls):

        margin = size * 0.1
        cx = rng.uniform(margin, size-margin)   # hill centre X (local)
        cz = rng.uniform(margin, size-margin)   # hill centre Z (local)
        hw = rng.uniform(size*0.08, size*0.18)  # hill half-width (spreads with slab)
        ht = rng.uniform(hill_height_min, hill_height_max)              # hill height in world units
        idx = add_slab(verts,tris,cols,idx,
                       cx-hw, cz-hw, cx+hw, cz+hw,
                       avg_h+ht, bot, 
                       darken(BIOME_TOP_COLOR[TAIGA],rng.uniform(0.9,1.0)),  # TOP COLOR
                       darken(BIOME_TOP_COLOR[TAIGA],rng.uniform(0.8,0.87)) # SIDE COLOR
                       )

    # -- Pine silhouettes --------------------------------------------------
    # Two stacked pyramids per tree: lower wide base + upper narrow tip
    for _ in range(amount_trees):
        margin = size * 0.05
        cx = rng.uniform(margin, size-margin)   # pine centre X (local)
        cz = rng.uniform(margin, size-margin)   # pine centre Z (local)
        base_hw = rng.uniform(2.5, 5.0)   # half-width of the lower (widest) layer
        total_h = rng.uniform(tree_height_min, tree_height_max) # total tree height in world units
        base_y  = avg_h                   # tree starts at ground level

        shade = rng.uniform(0.7, 1.0)

        # Lower layer — wider, covers bottom 55% of total height
        idx = add_pyramid(verts,tris,cols,idx,
                          cx, cz,
                          base_hw, base_hw,          # half-width X and Z
                          base_y,                    # base Y (ground)
                          base_y + total_h * 0.55,   # apex Y
                          darken(pine_foliage_low,shade), darken(pine_foliage_low,shade))

        # Upper layer — narrower (55% of base), overlaps lower at 40% height
        upper_hw = base_hw * 0.55   # narrower than the lower layer
        idx = add_pyramid(verts,tris,cols,idx,
                          cx, cz,
                          upper_hw, upper_hw,
                          base_y + total_h * 0.50,   # starts partway up the lower layer
                          base_y + total_h,           # reaches the full tree top
                          darken(pine_foliage_top,shade), darken(pine_foliage_top,shade))

    return verts, tris, cols
