import math
from ursina import color
from .shared import add_slab, add_pyramid
from code.world.meshbuilders.shared import *
from code.world.color_settings import *
from code.world.world_settings import CHUNK_SIZE


def build_desert_impostor(size, avg_h, rng, bot=-60.0):
    """
    Sandy desert: a flat base, wind-blown dune ridges, and scattered cacti.
    Each cactus has a 50% chance of a tiny pink flower on top.
    """
    verts=[]; tris=[]; cols=[]; idx=0

    # -- Colors -----------------------------------------------------------
    chunk_top_color    = BIOME_TOP_COLOR[DESERT]
    chunk_side_color   = BIOME_SIDE_COLOR[DESERT]
    # cactus_top  = darken(COLOR__CACTUS, rng.uniform(0.9,1.0))   # cactus body top
    # cactus_side = darken(COLOR__CACTUS, rng.uniform(0.7,0.89))   # cactus body sides
    flower_col  = darken(COLOR__CACTUS_FLOWER, rng.uniform(0.7, 1.0)) 
    
    # --- SIZE-DEPENDENT VALUES ---
    # Check if the Imps_Chunk_To_Create is larger than a regular chunk 
    # (which means its 5x5)
    if size > CHUNK_SIZE:
        amount_cacti = rng.randint(7, 10)
        num_dunes = rng.randint(3, 6) 
        dune_height_min = 5.0 # Hill Height MIN
        dune_height_max = 13.0 # Hill Height MAX
    else: # Regular Chunk values (1x1 sized) 
        amount_cacti = rng.randint(0, 2)
        num_dunes = rng.randint(1, 3) 
        dune_height_min = 0.5 # Hill Height MIN
        dune_height_max = 2.5 # Hill Height MAX
        chunk_side_color  = darken(BIOME_SIDE_COLOR[DESERT],rng.uniform(0.75,0.85))

    # -- Base ground slab -------------------------------------------------
    idx = add_slab(verts,tris,cols,idx,
                   0, 0, size, size,
                   avg_h, bot,
                   darken(chunk_top_color, rng.uniform(0.7, 1.0)), darken(chunk_side_color, rng.uniform(0.7, 1.0)))

    # -- Dune ridges -------------------------------------------------------
    # Elongated pyramids suggesting wind-blown dunes.
    dune_margin    = size * 0.20    # keep dunes away from slab edges
    dune_width_min = size * 0.12    # minimum half-width along long axis
    dune_width_max = size * 0.28    # maximum half-width along long axis

    for _ in range(num_dunes):

        # Dune Color
        dune_color = darken(BIOME_TOP_COLOR[DESERT], rng.uniform(0.75, 0.90))

        cx = rng.uniform(dune_margin, size - dune_margin)   # dune centre X
        cz = rng.uniform(dune_margin, size - dune_margin)   # dune centre Z
        hw = rng.uniform(dune_width_min, dune_width_max)    # half-width (same on both axes)
        hz = hw                                              # Z matches X — round base
        dune_h = rng.uniform(dune_height_min, dune_height_max)  # how tall the dune is
        idx = add_pyramid(verts,tris,cols,idx,
                          cx, cz, hw, hz,
                          avg_h, avg_h + dune_h,
                          dune_color, dune_color)

    # -- Cacti -------------------------------------------------------------
    # Simple box cactus: a trunk slab + optional arm slabs.
    # 50% chance of a tiny pink flower cube on top.
    cactus_margin = size * 0.1       # allow cacti closer to edges than dunes

    for _ in range(amount_cacti):
        cx = rng.uniform(cactus_margin, size - cactus_margin)
        cz = rng.uniform(cactus_margin, size - cactus_margin)

        trunk_hw     = rng.uniform(0.46, 0.8)    # trunk half-width (square)
        trunk_height = rng.uniform(2.0, 5.0)    # how tall the trunk is
        trunk_top    = avg_h + trunk_height      # Y at top of trunk

        cactus_color = darken(COLOR__CACTUS, rng.uniform(0.83,1.0))

        # Trunk
        idx = add_slab(verts,tris,cols,idx,
                       cx - trunk_hw, cz - trunk_hw,
                       cx + trunk_hw, cz + trunk_hw,
                       trunk_top, avg_h,
                       cactus_color, cactus_color)

        # One or two arms (50% chance each side)
        for arm_side in [-1, 1]:
            if rng.random() < 0.35:
                arm_hw       = trunk_hw * 0.55        # arm is thinner than trunk
                arm_length   = rng.uniform(0.75, 1.5)  # how far the arm extends
                arm_base_y   = avg_h + trunk_height * rng.uniform(0.40, 0.65)
                arm_top_y    = arm_base_y + rng.uniform(1.5, 3.0)
                arm_offset   = trunk_hw + arm_length   # end X of arm from centre

                
                cactus_color = darken(COLOR__CACTUS, rng.uniform(0.65,0.8))

                # Horizontal segment (stub connecting trunk to arm tip)
                idx = add_slab(verts,tris,cols,idx,
                               cx + arm_side * trunk_hw,
                               cz - arm_hw,
                               cx + arm_side * arm_offset,
                               cz + arm_hw,
                               arm_base_y + arm_hw, arm_base_y - arm_hw,
                               cactus_color, cactus_color)

                
                cactus_color = darken(COLOR__CACTUS, rng.uniform(0.8,0.9))
                arm_hw       = trunk_hw * 0.45        # arm is thinner than trunk

                # Vertical segment at arm tip
                idx = add_slab(verts,tris,cols,idx,
                               cx + arm_side * arm_offset - arm_hw,
                               cz - arm_hw,
                               cx + arm_side * arm_offset + arm_hw,
                               cz + arm_hw,
                               arm_top_y, arm_base_y - arm_hw,
                               cactus_color, cactus_color)

        # 50% chance: tiny pink flower on top of the trunk
        if rng.random() < 0.50:
            flower_hw = trunk_hw * 0.55    # flower is smaller than the trunk
            flower_h  = rng.uniform(0.5, 1.2)
            idx = add_slab(verts,tris,cols,idx,
                           cx - flower_hw, cz - flower_hw,
                           cx + flower_hw, cz + flower_hw,
                           trunk_top + flower_h, trunk_top,
                           flower_col, flower_col)

    return verts, tris, cols
