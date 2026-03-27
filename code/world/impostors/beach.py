from ursina import color
from .shared import add_slab
from code.world.meshbuilders.shared import *
from code.world.color_settings import *
from code.world.world_settings import CHUNK_SIZE


def build_beach_impostor(size, avg_h, rng, bot=-60.0):
    """Flat sandy beach — just a plain slab."""
    verts=[]; tris=[]; cols=[]; idx=0
    ground  = BIOME_TOP_COLOR[BEACH]
    g_side = BIOME_SIDE_COLOR[BEACH]

    # --- SIZE-DEPENDENT VALUES ---
    # Check if the Imps_Chunk_To_Create is larger than a regular chunk 
    # (which means its 5x5)
    if size > CHUNK_SIZE:
        amount_ground_rolls = rng.randint(3, 4) 
        hill_height_min = 1.5 # Hill Height MIN
        hill_height_max = 5.5 # Hill Height MAX
    else: # Regular Chunk values (1x1 sized) 
        # amount_ground_rolls = rng.randint(2, 3)
        amount_ground_rolls = 0
        hill_height_min = 0.5 # Hill Height MIN
        hill_height_max = 2.25 # Hill Height MAX
        g_side  = darken(BIOME_SIDE_COLOR[BEACH],rng.uniform(0.75,0.85))

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
                       darken(BIOME_TOP_COLOR[BEACH],rng.uniform(0.85,1.0)),  # TOP COLOR
                       darken(BIOME_TOP_COLOR[BEACH],rng.uniform(0.73,0.80)) # SIDE COLOR
                       )


    return verts, tris, cols
