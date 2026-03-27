import math
from ursina import color
from .shared import *
from code.world.meshbuilders.shared import *
from code.world.color_settings import *
from code.world.world_settings import *
from code.world.meshbuilders.terrain import build_peak_mesh
from code.world.meshbuilders.trees import build_snowy_pine_mesh


def build_mountain_impostor(size, avg_h, rng, bot=-60.0):
    """
    Mountain impostor mesh.

    avg_h from get_height() can be very large for mountains,
    so we clamp the base to avoid floating geometry.
    The peaks give the real mountain silhouette.
    """
    # CHUNK SIZE: --- 5x5 ---
    if size > CHUNK_SIZE:
        verts = []
        tris  = []
        cols  = []
        idx   = 0

        # Base colors
        ground_color = color.rgba(*BIOME_TOP_COLOR[MOUNTAIN], 1)
        chunk_side_color = color.rgba(*BIOME_SIDE_COLOR[MOUNTAIN], 1)
        peak_stone_color = color.rgba(*BIOME_SIDE_COLOR[MOUNTAIN], 1)

        # Clamp base height — mountains return very large values
        base_y = min(avg_h, 12.0) + rng.uniform(1.0, 4.0)

        # Generic Shading
        shade = rng.uniform(0.75, 0.99)

        # Main ground slab
        idx = add_slab(
            verts, tris, cols, idx,
            0, 0, size, size,
            base_y, bot,
            darken(ground_color, shade), darken(chunk_side_color,shade)
        )

        # -------------------------
        # Main mountain peaks
        # -------------------------
        for _ in range(rng.randint(2, 4)):
            margin  = size * 0.15
            cx      = rng.uniform(margin, size - margin)
            cz      = rng.uniform(margin, size - margin)
            base_hw = rng.uniform(size * 0.12, size * 0.22)
            base_hz = rng.uniform(size * 0.10, size * 0.18)
            peak_h  = rng.uniform(18.0, 38.0)
            apex_y  = base_y + peak_h

            # Random darker tone for this peak
            shade = rng.uniform(0.55, 0.99)
            rock_top_color_d  = darken(peak_stone_color, shade)
            rock_base_color_d = darken(peak_stone_color, shade)

            # Rock peak
            idx = add_pyramid(
                verts, tris, cols, idx,
                cx, cz, base_hw, base_hz,
                base_y, apex_y,
                rock_top_color_d, rock_base_color_d
            )

            # Snow cap (upper part of peak)
            snow_base_y = base_y + peak_h * 0.75

            # Slight snow color variation
            snow_shade = rng.uniform(0.85, 1.0)
            snow_top_color_d  = darken(COLOR__SNOW, snow_shade)
            snow_side_color_d = darken(COLOR__SNOW, snow_shade)

            idx = add_pyramid(
                verts, tris, cols, idx,
                cx, cz,
                base_hw * 0.30, base_hz * 0.30,
                snow_base_y,
                apex_y + rng.uniform(1.0, 3.0),
                snow_top_color_d, snow_side_color_d
            )

        # -------------------------
        # Smaller rock spires
        # -------------------------
        for _ in range(rng.randint(3, 6)):
            margin = size * 0.05
            cx = rng.uniform(margin, size - margin)
            cz = rng.uniform(margin, size - margin)
            hw = rng.uniform(size * 0.04, size * 0.10)
            hz = rng.uniform(size * 0.04, size * 0.08)
            h  = rng.uniform(8.0, 20.0)
            apex_y = base_y + h

            # Darker tone per spire
            shade = rng.uniform(0.70, 0.90)
            rock_top_color_d  = darken(peak_stone_color, shade)
            rock_base_color_d = darken(peak_stone_color, shade)

            # Rock spire
            idx = add_pyramid(
                verts, tris, cols, idx,
                cx, cz, hw, hz,
                base_y, apex_y,
                rock_top_color_d, rock_base_color_d
            )

            # Small snow tip
            snow_base_y = base_y + h * 0.80
            snow_shade  = rng.uniform(0.85, 1.0)

            idx = add_pyramid(
                verts, tris, cols, idx,
                cx, cz,
                hw * 0.25, hz * 0.25,
                snow_base_y,
                apex_y + 1.0,
                darken(COLOR__SNOW, snow_shade),
                darken(COLOR__SNOW, snow_shade)
            )


        
        """
        Ground rolls
        """
        # -- Ground rolls -----------------------------------------------------
        # Low hills — width is slab-relative so they spread, height is fixed units
        for _ in range(rng.randint(4, 8)):
            margin = size * 0.1
            cx = rng.uniform(margin, size-margin)   # hill centre X (local)
            cz = rng.uniform(margin, size-margin)   # hill centre Z (local)
            hw = rng.uniform(size*0.08, size*0.18)  # hill half-width (spreads with slab)
            ht = rng.uniform(2.5, 7.0)              # hill height in world units
            idx = add_slab(verts,tris,cols,idx,
                        cx-hw, cz-hw, cx+hw, cz+hw,
                        avg_h+ht, bot, darken(ground_color, rng.uniform(0.75,1.0)),
                            darken(chunk_side_color, rng.uniform(0.75,1.0)))

        """
        Pine Trees
        """
        # -- Colors -----------------------------------------------------------
        pine_foliage_low = darken(COLOR__PINE_TREE_LEAVES, rng.uniform(0.55,0.65)) # pine foliage (dark green) (BOTTOM)
        pine_foliage_top = darken(COLOR__PINE_TREE_LEAVES, rng.uniform(0.70,0.8)) # pine foliage sides (TOP)

        # -- Pine silhouettes --------------------------------------------------
        # Two stacked pyramids per tree: lower wide base + upper narrow tip
        for _ in range(rng.randint(8, 12)):
            margin = size * 0.05
            cx = rng.uniform(margin, size-margin)   # pine centre X (local)
            cz = rng.uniform(margin, size-margin)   # pine centre Z (local)
            base_hw = rng.uniform(3.0, 6.0)   # half-width of the lower (widest) layer
            total_h = rng.uniform(8.0, 15.0) # total tree height in world units
            base_y  = avg_h                   # tree starts at ground level

            # Lower layer — wider, covers bottom 55% of total height
            idx = add_pyramid(verts,tris,cols,idx,
                            cx, cz,
                            base_hw, base_hw,          # half-width X and Z
                            base_y,                    # base Y (ground)
                            base_y + total_h * 0.55,   # apex Y
                            pine_foliage_low, pine_foliage_low)

            # Upper layer — narrower (55% of base), overlaps lower at 40% height
            upper_hw = base_hw * 0.55   # narrower than the lower layer
            idx = add_pyramid(verts,tris,cols,idx,
                            cx, cz,
                            upper_hw, upper_hw,
                            base_y + total_h * 0.40,   # starts partway up the lower layer
                            base_y + total_h,           # reaches the full tree top
                            pine_foliage_top, pine_foliage_top)

        return verts, tris, cols

    # CHUNK SIZE: --- 1x1 ---
    else:

        verts = []
        tris  = []
        cols  = []
        idx   = 0

        # Base colors
        ground_color  = BIOME_TOP_COLOR[MOUNTAIN]
        chunk_side_color = BIOME_SIDE_COLOR[MOUNTAIN] 
        

        # Clamp base height — mountains return very large values
        # base_y = min(avg_h, 12.0) + rng.uniform(1.0, 4.0)
        base_y = avg_h

        # Darken the rock_top_color
        shade = rng.uniform(0.75, 0.99)

        if (avg_h >= MOUNTAIN_SNOW_HEIGHT):
            ground_color_to_apply = BIOME_TOP_COLOR[MOUNTAIN_SNOW]
            side_color_to_apply = BIOME_SIDE_COLOR[MOUNTAIN_SNOW]
        else:
            ground_color_to_apply = ground_color
            side_color_to_apply = chunk_side_color

        if avg_h >= MOUNTAIN_PEAK_HEIGHT:
            ground_color_to_apply = darken(BIOME_SIDE_COLOR[MOUNTAIN_SNOW], rng.uniform(0.85,1.0))
            side_color_to_apply = darken(BIOME_SIDE_COLOR[MOUNTAIN_SNOW], rng.uniform(0.75,0.8))


        # Main ground slab
        idx = add_slab(
            verts, tris, cols, idx,
            0, 0, size, size,
            base_y, bot,
            darken(ground_color_to_apply, shade), 
            darken(side_color_to_apply, shade)
        )
        
        # Determine whether to generate MOUNTAIN PEAK 
        # or Pine Trees
        if avg_h >= MOUNTAIN_PEAK_HEIGHT:
            """
            Mountain Peak
            """
            idx = build_peak_mesh(verts, tris, cols, idx, 0, 0, base_y, CHUNK_SIZE, rng)

        else:
            """
            Pine Trees
            """
            # -- Colors -----------------------------------------------------------
            pine_foliage_low = darken(COLOR__PINE_TREE_LEAVES, rng.uniform(0.65,0.7)) # pine foliage (dark green) (BOTTOM)
            pine_foliage_top = darken(COLOR__PINE_TREE_LEAVES, rng.uniform(0.75,0.9)) # pine foliage sides (TOP)

            # Change colors if snow height
            if avg_h >= MOUNTAIN_SNOW_HEIGHT:
                # snow_color_low = darken(COLOR__SNOWY_PINE_TREE_SNOW, rng.uniform(0.8, 0.85))
                # snow_color_top = darken(COLOR__SNOWY_PINE_TREE_SNOW, rng.uniform(0.95, 1.05))
                pine_foliage_low = darken(COLOR__SNOWY_PINE_TREE_SNOW, rng.uniform(0.8, 0.85))
                pine_foliage_top = darken(COLOR__SNOWY_PINE_TREE_SNOW, rng.uniform(0.95, 1.05))

            # -- Pine silhouettes --------------------------------------------------
            # Two stacked pyramids per tree: lower wide base + upper narrow tip
            for _ in range(rng.randint(2, 3)):
                margin = size * 0.1
                cx = rng.uniform(margin, size-margin)   # pine centre X (local)
                cz = rng.uniform(margin, size-margin)   # pine centre Z (local)
                base_hw = rng.uniform(1.5, 3.5)   # half-width of the lower (widest) layer
                total_h = rng.uniform(4.0, 6.0) # total tree height in world units
                base_y  = avg_h                   # tree starts at ground level

                # This COULD be used but, for now, i wont
                # idx = build_snowy_pine_mesh(verts, tris, cols, idx, cx, base_y, cz, rng)

                # Switch up the colors (why? i coulnt get this to work properly, just switch up the colors for the lower part)
                # Lower layer — wider, covers bottom 55% of total height
                idx = add_pyramid(verts,tris,cols,idx,
                                cx, cz,
                                base_hw, base_hw,          # half-width X and Z
                                base_y,                    # base Y (ground)
                                base_y + total_h * 0.55,   # apex Y
                                pine_foliage_low, pine_foliage_low)

                # Upper layer — narrower (55% of base), overlaps lower at 40% height
                upper_hw = base_hw * 0.55   # narrower than the lower layer
                idx = add_pyramid(verts,tris,cols,idx,
                                cx, cz,
                                upper_hw, upper_hw,
                                base_y + total_h * 0.40,   # starts partway up the lower layer
                                base_y + total_h,           # reaches the full tree top
                                pine_foliage_top, pine_foliage_top)

        return verts, tris, cols