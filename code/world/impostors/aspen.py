import math
from ursina import color
from .shared import add_slab, add_pyramid
from code.world.meshbuilders.shared import *
from code.world.color_settings import *
from code.world.world_settings import CHUNK_SIZE


def build_aspen_impostor(size, avg_h, rng, bot=-60.0):
    """
    Aspen: yellow-green hills with thin trunks and Y-elongated leaf blobs.
    Real aspen top canopy: 1.2 wide × 3.0 tall × 1.2 deep (tall narrow column).
    Branch blobs are taller than wide (lh > lw) matching the real tree.
    """
    verts=[]; tris=[]; cols=[]; idx=0

    # -- Colors -----------------------------------------------------------
    ground  = color.rgba(*BIOME_TOP_COLOR[ASPEN], 1)          # ground top (yellow-green)
    g_side  = darken(BIOME_TOP_COLOR[ASPEN],rng.uniform(0.45,0.65))
    leaf_c  = COLOR__ASPEN_TREE_LEAVES
    l_side  = darken(COLOR__ASPEN_TREE_LEAVES, 0.65)


    # --- SIZE-DEPENDENT VALUES ---
    # Check if the Imps_Chunk_To_Create is larger than a regular chunk 
    # (which means its 5x5)
    if size > CHUNK_SIZE:
        amount_ground_rolls = rng.randint(6, 9) 
        amount_trees = rng.randint(20, 34)
        hill_height_min = 1.5 # Hill Height MIN
        hill_height_max = 5.0 # Hill Height MAX
    else: # Regular Chunk values (1x1 sized) 
        # amount_ground_rolls = rng.randint(2, 3)
        amount_ground_rolls = 0
        amount_trees = rng.randint(2, 4) 
        g_side  = darken(BIOME_SIDE_COLOR[ASPEN],rng.uniform(0.75,0.85))

    # -- Base ground slab -------------------------------------------------
    idx = add_slab(verts,tris,cols,idx, 0,0, size,size,
                   avg_h, bot, 
                   darken(ground, rng.uniform(0.85,0.95)), 
                   darken(g_side, rng.uniform(0.75,0.85))
                   )

    # -- Rolling hills ----------------------------------------------------
    for _ in range(amount_ground_rolls):

        margin = size * 0.1
        cx = rng.uniform(margin, size-margin)   # hill centre X (local)
        cz = rng.uniform(margin, size-margin)   # hill centre Z (local)
        hw = rng.uniform(size*0.08, size*0.20)  # hill half-width (spreads with slab)
        ht = rng.uniform(hill_height_min, hill_height_max)              # hill height in world units
        idx = add_slab(verts,tris,cols,idx,
                       cx-hw, cz-hw, cx+hw, cz+hw,
                       avg_h+ht, bot, 
                       darken(BIOME_TOP_COLOR[ASPEN],rng.uniform(0.9,1.0)),  # TOP COLOR
                       darken(BIOME_TOP_COLOR[ASPEN],rng.uniform(0.8,0.87)) # SIDE COLOR
                       )

    # -- Aspen trees ------------------------------------------------------
    for _ in range(amount_trees):

        margin = size * 0.05
        cx = rng.uniform(margin, size-margin)   # tree centre X (local)
        cz = rng.uniform(margin, size-margin)   # tree centre Z (local)

        tw  = rng.uniform(0.25, 0.5)  # trunk half-width (thin — aspens are narrow)
        th  = rng.uniform(5.0, 7.0)   # trunk height in world units
        tt  = avg_h + th              # Y at the top of the trunk

        # Top canopy — tall narrow column (Y-elongated, matches real 1.2×3.0×1.2)
        top_w = rng.uniform(1.0, 1.8)  # canopy half-width (keep narrow)
        top_h = rng.uniform(4.5, 6.5)  # canopy height (taller than wide)

        
        shade = rng.uniform(1.0,1.025)
        leaf_c = darken(leaf_c, shade)
        l_side = darken(l_side, shade)

        idx = add_slab(verts,tris,cols,idx,
                       cx-top_w, cz-top_w, cx+top_w, cz+top_w,
                       tt+top_h,  # canopy top
                       tt,        # canopy bottom = trunk top
                       leaf_c, 
                       l_side,
                       True
                       )

        # Branch blobs — small leaf clusters along the upper trunk
        # Each blob is taller than wide (lh > lw) matching the real tree
        num_branches = rng.randint(0, 2)
        for i in range(num_branches):
            
            
            shade = rng.uniform(1.0,1.025)
            leaf_c = darken(leaf_c, shade)
            l_side = darken(l_side, shade)

            angle = i * (2*math.pi/num_branches) + rng.uniform(-0.4, 0.4)
            dist  = rng.uniform(0.3, 1.2)   # how far the blob sits from trunk centre
            bx    = cx + math.cos(angle) * dist   # blob centre X
            bz    = cz + math.sin(angle) * dist   # blob centre Z
            by    = tt - th * rng.uniform(0.15, 0.50)  # height along the trunk (upper half)
            lw    = rng.uniform(0.6, 1.0)   # blob half-width (narrow)
            lh    = rng.uniform(1.5, 2.5)   # blob height — always greater than lw
            # Blob is centred at by: extends lh*0.6 up and lh*0.4 down
            idx = add_slab(verts,tris,cols,idx,
                           bx-lw, bz-lw, bx+lw, bz+lw,
                           by+lh*0.6,   # blob top
                           by-lh*0.4,   # blob bottom
                           leaf_c, l_side)

        trunk_color = darken(COLOR__ASPEN_TREE_TRUNK, rng.uniform(0.65, 0.9))

        # Trunk — drawn last so it renders on top of any blobs that clip into it
        idx = add_slab(verts,tris,cols,idx,
                       cx-tw, cz-tw, cx+tw, cz+tw,
                       tt,      # trunk top
                       avg_h,   # trunk bottom (ground level)
                       trunk_color, trunk_color)

    return verts, tris, cols
