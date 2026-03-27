import math
import random
from ursina import color
from .shared import *
from code.world.world_settings import *


# ============================================================
# ======================== ROOTS =============================
# ============================================================
def generate_roots(verts, tris, cols, idx, wx, wy, wz, trunk_half_width, trunk_color, rng):
    """
    Generates volumetric, non-overlapping roots around a base point.
    Can be reused for any tree mesh.
    """
    num_roots = rng.randint(3, 5)
    sectors = [i for i in range(num_roots)]
    rng.shuffle(sectors)
    
    for i in sectors:
        # Sector-based rotation to prevent overlap
        base_angle = (i / num_roots) * math.pi * 2
        angle = base_angle + rng.uniform(-0.3, 0.3) 
        
        root_len = rng.uniform(0.7, 1.2)
        root_width = trunk_half_width * rng.uniform(0.5, 0.8)
        root_high_point = rng.uniform(0.4, 0.8) # How high up the trunk it starts
        
        dx, dz = math.cos(angle), math.sin(angle)
        px, pz = -dz * root_width, dx * root_width # Perpendicular vector for thickness
        
        # Points for the root prism
        spine_start = (dx * trunk_half_width, root_high_point, dz * trunk_half_width)
        spine_end = (dx * root_len, 0, dz * root_len)
        side_l = (dx * trunk_half_width + px, 0, dz * trunk_half_width + pz)
        side_r = (dx * trunk_half_width - px, 0, dz * trunk_half_width - pz)
        
        root_shade = darken(trunk_color, 0.75)

        # Build two sloped faces (Triangular Prism)
        for side in [side_l, side_r]:
            verts.extend([
                (wx + side[0], wy + side[1], wz + side[2]),
                (wx + spine_start[0], wy + spine_start[1], wz + spine_start[2]),
                (wx + spine_end[0], wy + spine_end[1], wz + spine_end[2]),
                (wx + spine_end[0], wy + spine_end[1], wz + spine_end[2])
            ])
            cols.extend([root_shade] * 4)
            tris.append((idx, idx+1, idx+2, idx+3))
            idx += 4
            
    return idx


# ============================================================
# ====================== PLAINS TREE =========================
# ============================================================

PLAINS_TREE_APPLE_CHANCE = 0.1

def build_plains_tree_mesh(verts, tris, cols, idx, wx, wy, wz, rng):
    """
    Builds a generic broadleaf tree using cubes.
    Rarely spawns apples that hang from actual leaf clusters.
    """

    # -- Colors & Dimensions from constants -----------------------------------
    trunk_col  = COLOR__PLAINS_TREE_TRUNK
    # leaf_col   = COLOR__FOREST_TREE_LEAVES
    trunk_h    = rng.uniform(2.0, 4.5)   # base trunk height in world units
    leaf_scale = rng.uniform(0.85, 1.25)   # base leaf cluster size
    ls         = leaf_scale * 3

    trunk_half_width = rng.uniform(0.45, 0.79)

    # -- Trunk -----------------------------------------------------------------
    idx = add_box(
        verts, tris, cols, idx,
        wx, wy + trunk_h / 2, wz,
        trunk_half_width, trunk_h * 1.5, trunk_half_width,
        darken(trunk_col, rng.uniform(0.7, 1.0))
    )

    # -- Roots -----------------------------------------------------------------
    idx = generate_roots(verts, tris, cols, idx, wx, wy, wz,
                         trunk_half_width / 2,
                         darken_tuple(trunk_col, rng.uniform(0.55, 0.7)), rng)

    # -- Main Canopy -----------------------------------------------------------
    canopy_y = wy + trunk_h
    idx = add_box(
        verts, tris, cols, idx,
        wx, canopy_y + ls * 0.6, wz,
        ls * 1.1, ls * 0.9, ls * 1.1,
        darken(COLOR__PLAINS_TREE_LEAVES, rng.uniform(0.9, 1.1))
    )

    # Radius around the trunk that leaf clusters can spawn
    canopy_radius = 2.50
    # How many extra leaf clusters surround the main canopy ball
    num_leaf_clusters = rng.randint(3, 4)
    # Y position of the top of the main canopy ball
    canopy_top_y = canopy_y + ls * 0.6

    # Positions at the bottom of each leaf cube, used later for apple spawning
    leaf_anchors = []

    # -- Extra Leaf Clusters ---------------------------------------------------
    # Spread clusters evenly around the canopy in a circle,
    # with a small random angle nudge so it never looks perfectly uniform
    for i in range(num_leaf_clusters):
        angle_rad  = i * (2 * math.pi / num_leaf_clusters) + rng.uniform(-0.3, 0.3)
        dist       = rng.uniform(0.6, canopy_radius)

        # Convert polar coords to world X/Z around the tree center
        cluster_x  = wx + math.cos(angle_rad) * dist
        cluster_z  = wz + math.sin(angle_rad) * dist
        # Vary height slightly so clusters don't all sit at the same level
        cluster_y  = canopy_top_y + rng.uniform(-ls * 0.3, ls * 0.3)

        # Random size variation per cluster
        cluster_size = ls * rng.uniform(0.75, 0.85)

        idx = add_box(
            verts, tris, cols, idx,
            cluster_x, cluster_y - cluster_size * 0.25, cluster_z,
            cluster_size, cluster_size * 0.8, cluster_size,
            darken(COLOR__PLAINS_TREE_LEAVES, rng.uniform(0.76, 0.85))
        )

        # Record the bottom of this cluster as a point where an apple could hang
        leaf_anchors.append((cluster_x, cluster_y - cluster_size * 0.65, cluster_z))

    # -- Rare Apples (~7.5% chance, always attached to a leaf cluster) ---------
    if rng.random() < PLAINS_TREE_APPLE_CHANCE and len(leaf_anchors) >0:
        apple_col = color.rgba(0.85, 0.10, 0.10, 1)
        stem_col  = color.rgba(0.30, 0.20, 0.10, 1)
        num_apples = rng.randint(3, min(5, len(leaf_anchors)))

        for ax, ay, az in rng.sample(leaf_anchors, num_apples):
            ax += rng.uniform(-0.12, 0.12)
            az += rng.uniform(-0.12, 0.12)

            # Stem
            idx = add_box(verts, tris, cols, idx,
                          ax, ay - 0.05, az,
                          0.05, 0.12, 0.05, stem_col)

            # Apple
            idx = add_box(verts, tris, cols, idx,
                          ax, ay - 0.18, az,
                          0.28, 0.28, 0.28, apple_col)

    return idx



# ============================================================
# ====================== FOREST TREE ========================
# ============================================================

def build_forest_tree_mesh(verts, tris, cols, idx, wx, wy, wz, rng):
    """
    Builds a generic broadleaf tree using cubes.
    Rarely spawns apples that hang from actual leaf clusters.
    """

    # -- Colors & Dimensions from constants -----------------------------------
    trunk_col  = COLOR__FOREST_TREE_TRUNK
    # leaf_col   = COLOR__FOREST_TREE_LEAVES
    trunk_h    = rng.uniform(5.0, 9.5)   # base trunk height in world units
    leaf_scale = rng.uniform(1.0, 1.5)   # base leaf cluster size
    ls         = leaf_scale * 3

    

    trunk_half_width = rng.uniform(0.65, 0.9)

    # -- Trunk -----------------------------------------------------------------
    idx = add_box(
        verts, tris, cols, idx,
        wx, wy + trunk_h / 2, wz,
        trunk_half_width, trunk_h * 1.5, trunk_half_width,
        darken(trunk_col, rng.uniform(0.7, 1.0))
    )

    # -- Roots -----------------------------------------------------------------
    idx = generate_roots(verts, tris, cols, idx, wx, wy, wz,
                         trunk_half_width / 2,
                         darken_tuple(trunk_col, rng.uniform(0.55, 0.7)), rng)

    # -- Main Canopy -----------------------------------------------------------
    canopy_y = wy + trunk_h
    idx = add_box(
        verts, tris, cols, idx,
        wx, canopy_y + ls * 0.6, wz,
        ls * 1.1, ls * 0.9, ls * 1.1,
        darken(COLOR__FOREST_TREE_LEAVES, rng.uniform(0.75, 1.0))
    )

    # Radius around the trunk that leaf clusters can spawn
    canopy_radius = 3.0
    # How many extra leaf clusters surround the main canopy ball
    num_leaf_clusters = rng.randint(2, 3)
    # Y position of the top of the main canopy ball
    canopy_top_y = canopy_y + ls * 0.6

    # Positions at the bottom of each leaf cube, used later for apple spawning
    leaf_anchors = []

    # -- Extra Leaf Clusters ---------------------------------------------------
    # Spread clusters evenly around the canopy in a circle,
    # with a small random angle nudge so it never looks perfectly uniform
    for i in range(num_leaf_clusters):
        angle_rad  = i * (2 * math.pi / num_leaf_clusters) + rng.uniform(-0.5, 0.5)
        dist       = rng.uniform(1.0, canopy_radius)

        # Convert polar coords to world X/Z around the tree center
        cluster_x  = wx + math.cos(angle_rad) * dist
        cluster_z  = wz + math.sin(angle_rad) * dist
        # Vary height slightly so clusters don't all sit at the same level
        cluster_y  = canopy_top_y + rng.uniform(-ls * 0.01, ls * 0.5)

        # Random size variation per cluster
        cluster_size = ls * rng.uniform(1.0, 1.80)

        leaf_shadowing = rng.uniform(0.75, 0.95)

        idx = add_box(
            verts, tris, cols, idx,
            cluster_x, cluster_y - cluster_size * 0.25, cluster_z,
            cluster_size, cluster_size * 0.8, cluster_size,
            darken(COLOR__FOREST_TREE_LEAVES, leaf_shadowing)
        )

        # Record the bottom of this cluster as a point where an apple could hang
        leaf_anchors.append((cluster_x, cluster_y - cluster_size * 0.65, cluster_z))

    # -- Rare Apples (~7.5% chance, always attached to a leaf cluster) ---------
    if rng.random() < 0.075 and leaf_anchors:
        apple_col = color.rgba(0.85, 0.10, 0.10, 1)
        stem_col  = color.rgba(0.30, 0.20, 0.10, 1)
        num_apples = rng.randint(2, min(5, len(leaf_anchors)))

        for ax, ay, az in rng.sample(leaf_anchors, num_apples):
            ax += rng.uniform(-0.12, 0.12)
            az += rng.uniform(-0.12, 0.12)

            # Stem
            idx = add_box(verts, tris, cols, idx,
                          ax, ay - 0.05, az,
                          0.05, 0.12, 0.05, stem_col)

            # Apple
            idx = add_box(verts, tris, cols, idx,
                          ax, ay - 0.18, az,
                          0.28, 0.28, 0.28, apple_col)

    return idx





# ============================================================
# ======================= ASPEN TREE =========================
# ============================================================

def build_aspen_mesh(verts, tris, cols, idx, wx, wy, wz, rng):
    """
    Builds a tall, thin aspen-style tree.
    Uses simple offsets instead of angles (no rotation required).
    Returns idx.
    """

    # ==================================================
    # Trunk parameters
    # ==================================================
    trunk_height = rng.uniform(4.5, 9.0)   # tall trunk
    trunk_radius = rng.uniform(0.25, 0.4)  # thin trunk

    # ==================================================
    # Trunk geometry
    # ==================================================
    idx = add_box(
        verts, tris, cols, idx,
        wx,
        wy + trunk_height / 2,
        wz,
        trunk_radius,
        trunk_height,
        trunk_radius,
        darken(COLOR__ASPEN_TREE_TRUNK, rng.uniform(0.75, 1.025))
    )

    # ==================================================
    # Roots
    # ==================================================
    idx = generate_roots(verts, tris, cols, idx, wx, wy, wz, trunk_radius/2, darken_tuple(COLOR__ASPEN_TREE_TRUNK, rng.uniform(0.55, 0.75)), rng)

    # ==================================================
    # Side leaf clusters ("branches")
    # ==================================================
    num_leaf_clusters = rng.randint(0, 4)

    for i in range(num_leaf_clusters):

        
        # Slight tone variation so trees aren't identical
        tone_variation = rng.uniform(0.75, 1.025)

        # ----------------------------------------------
        # Where on the trunk the leaves attach
        # ----------------------------------------------
        branch_base_y = wy + trunk_height * rng.uniform(0.5, 0.85)

        # ----------------------------------------------
        # Horizontal offset from trunk
        # Alternate left / right for balance
        # ----------------------------------------------
        side_direction = -1 if i % 2 == 0 else 1
        horizontal_offset = side_direction * rng.uniform(0.4, 0.9)

        branch_x = wx + horizontal_offset
        branch_z = wz  # no rotation -> keep Z aligned
        branch_y = branch_base_y + rng.uniform(0.8, 1.6)

        # ----------------------------------------------
        # Leaf cluster size
        # ----------------------------------------------
        leaf_width  = rng.uniform(1.6, 2.0)
        leaf_height = rng.uniform(2.5, 3.5)

        idx = add_box(
            verts, tris, cols, idx,
            branch_x,
            branch_y + leaf_height * 0.4,
            branch_z,
            leaf_width,
            leaf_height,
            leaf_width,
            darken(COLOR__ASPEN_TREE_LEAVES, rng.uniform(0.85, 0.9))
        )

    # ==================================================
    # Top canopy
    # ==================================================
    canopy_width  = rng.uniform(1.5, 2.5)
    canopy_height = rng.uniform(4.0, 5.5)

    idx = add_box(
        verts, tris, cols, idx,
        wx,
        wy + trunk_height + 1.5,
        wz,
        canopy_width,
        canopy_height,
        canopy_width,
        darken(COLOR__ASPEN_TREE_LEAVES, rng.uniform(0.9, 1.1))
    )

    return idx



# ============================================================
# ========================= PINE TREE ========================
# ============================================================


def build_pine_mesh(verts, tris, cols, idx, wx, wy, wz, height_tint, rng):
    # Foliage colors

    color_pine_leaves = COLOR__PINE_TREE_LEAVES
    foliage_red, foliage_green, foliage_blue = color_pine_leaves

    # Trunk Parameters
    trunk_height = rng.uniform(0.01, 3.5)
    trunk_half_width = rng.uniform(0.2, 0.55)
    trunk_color = darken(COLOR__PINE_TREE_TRUNK, rng.uniform(0.7, 1.0))

    # 1. Build Trunk Box
    for fx, fz, tx, tz in [(-1,-1,1,-1), (1,-1,1,1), (1,1,-1,1), (-1,1,-1,-1)]:
        verts.extend([
            (wx + fx*trunk_half_width, wy, wz + fz*trunk_half_width),
            (wx + tx*trunk_half_width, wy, wz + tz*trunk_half_width),
            (wx + tx*trunk_half_width, wy + trunk_height, wz + tz*trunk_half_width),
            (wx + fx*trunk_half_width, wy + trunk_height, wz + fz*trunk_half_width)
        ])
        cols.extend([trunk_color] * 4)
        tris.append((idx, idx+1, idx+2, idx+3))
        idx += 4

    # 2. Generate Roots (Reusable Function Call)
    idx = generate_roots(verts, tris, cols, idx, wx, wy, wz, trunk_half_width, trunk_color, rng)

    # 3. Foliage Parameters (Lowered base_y for visual height)
    foliage_base_y = wy + trunk_height - 1.0 
    foliage_layers = [
        (rng.uniform(2.0, 2.4), rng.uniform(3.0, 3.8), foliage_base_y),
        (rng.uniform(1.4, 1.8), rng.uniform(2.5, 3.2), foliage_base_y + rng.uniform(1.8, 2.5)),
        (rng.uniform(0.7, 1.1), rng.uniform(2.0, 3.0), foliage_base_y + rng.uniform(3.5, 4.5)),
    ]
    
    layer_light_factors = [0.65, 0.85, 1.00]
    base_light = rng.uniform(0.7, 1.0)

    for (l_width, l_height, l_base_y), l_factor in zip(foliage_layers, layer_light_factors):
        layer_shade = base_light * l_factor
        apex = (wx + rng.uniform(-0.05, 0.05), l_base_y + l_height, wz + rng.uniform(-0.05, 0.05))
        
        # Jittered corners
        j = rng.uniform(0.0,0.3) # THIS IS THE JITTERNSS
        c_nw = (-l_width + rng.uniform(-j, j), l_base_y, -l_width + rng.uniform(-j, j))
        c_ne = ( l_width + rng.uniform(-j, j), l_base_y, -l_width + rng.uniform(-j, j))
        c_se = ( l_width + rng.uniform(-j, j), l_base_y,  l_width + rng.uniform(-j, j))
        c_sw = (-l_width + rng.uniform(-j, j), l_base_y,  l_width + rng.uniform(-j, j))

        # --- Directional Side Faces ---
        # We define each face and its specific multiplier
        # (v1, v2, light_multiplier)
        directional_faces = [
            (c_sw, c_se, 1.00), # North (+Z face)
            (c_ne, c_nw, 0.97), # South (-Z face)
            (c_nw, c_sw, 0.94), # West  (-X face)
            (c_se, c_ne, 0.94)  # East  (+X face)
        ]

        for c1, c2, dir_multiplier in directional_faces:
            # Combine the layer shade with the directional light
            final_factor = layer_shade * dir_multiplier
            face_color = color.rgba(foliage_red*final_factor, foliage_green*final_factor, foliage_blue*final_factor, 1)
            
            verts.extend([(wx+c1[0], c1[1], wz+c1[2]), (wx+c2[0], c2[1], wz+c2[2]), apex, apex])
            cols.extend([face_color] * 4)
            tris.append((idx, idx+1, idx+2, idx+3))
            idx += 4

        # Bottom Cap
        bottom_cap_color = darken(face_color, 0.45)
        verts.extend([(wx+c_nw[0], c_nw[1], wz+c_nw[2]), (wx+c_ne[0], c_ne[1]+0.0, wz+c_ne[2]),
                      (wx+c_se[0], c_se[1], wz+c_se[2]), (wx+c_sw[0], c_sw[1]+0.0, wz+c_sw[2])])
        cols.extend([bottom_cap_color] * 4)
        tris.append((idx, idx+1, idx+2, idx+3))
        idx += 4

    return idx


# ============================================================
# =================== SNOWY PINE TREE ========================
# ============================================================


def build_snowy_pine_mesh(verts, tris, cols, idx, wx, wy, wz, rng):
    pine_r, pine_g, pine_b = COLOR__SNOWY_PINE_TREE_LEAVES
    snow_r, snow_g, snow_b, _ = COLOR__SNOWY_PINE_TREE_SNOW

    # -- Trunk & Roots --
    trunk_height = rng.uniform(0.01, 3.5)
    trunk_half_width = rng.uniform(0.2, 0.55)
    trunk_color = darken(COLOR__SNOWY_PINE_TREE_TRUNK, rng.uniform(0.8, 1.0))

    for fx, fz, tx, tz in [(-1,-1, 1,-1), (1,-1, 1,1), (1,1,-1,1), (-1,1,-1,-1)]:
        verts.extend([
            (wx + fx*trunk_half_width, wy, wz + fz*trunk_half_width),
            (wx + tx*trunk_half_width, wy, wz + tz*trunk_half_width),
            (wx + tx*trunk_half_width, wy + trunk_height, wz + tz*trunk_half_width),
            (wx + fx*trunk_half_width, wy + trunk_height, wz + fz*trunk_half_width),
        ])
        cols.extend([trunk_color] * 4)
        tris.append((idx, idx+1, idx+2, idx+3)); idx += 4

    idx = generate_roots(verts, tris, cols, idx, wx, wy, wz, trunk_half_width, trunk_color, rng)

    # -- Foliage Layer Setup --
    foliage_start_y = wy + trunk_height - 1.2
    foliage_layers = [
        (rng.uniform(2.1, 2.4), rng.uniform(3.0, 3.6), foliage_start_y),
        (rng.uniform(1.4, 1.7), rng.uniform(2.5, 3.1), foliage_start_y + rng.uniform(1.6, 2.1)),
        (rng.uniform(0.7, 1.0), rng.uniform(2.0, 2.5), foliage_start_y + rng.uniform(3.2, 3.7)),
    ]

    foliage_brightness = [0.65, 0.85, 1.00]
    snow_brightness = [0.75, 0.85, 1.00] # Cleaned up these values for better gradient

    for layer_idx, ((layer_hw, layer_h, layer_y), foliage_factor) in \
            enumerate(zip(foliage_layers, foliage_brightness)):

        apex = (wx + rng.uniform(-0.04, 0.04), layer_y + layer_h, wz + rng.uniform(-0.04, 0.04))

        # Jittered Corners
        j_val = rng.uniform(0.0, 0.2)
        def jit(): return rng.uniform(-j_val, j_val)
        c_nw = (-layer_hw + jit(), layer_y, -layer_hw + jit())
        c_ne = ( layer_hw + jit(), layer_y, -layer_hw + jit())
        c_se = ( layer_hw + jit(), layer_y,  layer_hw + jit())
        c_sw = (-layer_hw + jit(), layer_y,  layer_hw + jit())

        # -- Directional Faces Logic --
        # Mapping: (StartCorner, EndCorner, Multiplier)
        directional_mapping = [
            (c_sw, c_se, 1.00), # North (+Z)
            (c_ne, c_nw, 0.97), # South (-Z)
            (c_nw, c_sw, 0.94), # West  (-X)
            (c_se, c_ne, 0.94)  # East  (+X)
        ]

        for c1, c2, dir_mult in directional_mapping:
            # 1. Foliage Face
            f_final_mult = foliage_factor * dir_mult
            f_col = color.rgba(pine_r * f_final_mult, pine_g * f_final_mult, pine_b * f_final_mult, 1)
            
            verts.extend([(wx+c1[0], c1[1], wz+c1[2]), (wx+c2[0], c2[1], wz+c2[2]), apex, apex])
            cols.extend([f_col]*4)
            tris.append((idx, idx+1, idx+2, idx+3)); idx += 4

            # 2. Snow Face
            snow_shrink = rng.uniform(0.78, 0.88)
            s_final_mult = snow_brightness[layer_idx] * dir_mult
            s_col = color.rgba(snow_r * s_final_mult, snow_g * s_final_mult, snow_b * s_final_mult, 1)

            # Calculate Shrunk Snow Verts
            s_c1 = (c1[0]*snow_shrink, c1[1] + (layer_h * (1-snow_shrink)) + 0.07, c1[2]*snow_shrink)
            s_c2 = (c2[0]*snow_shrink, c2[1] + (layer_h * (1-snow_shrink)) + 0.07, c2[2]*snow_shrink)
            s_apex = (apex[0], apex[1] + 0.02, apex[2])

            verts.extend([(wx+s_c1[0], s_c1[1], wz+s_c1[2]), (wx+s_c2[0], s_c2[1], wz+s_c2[2]), s_apex, s_apex])
            cols.extend([s_col]*4)
            tris.append((idx, idx+1, idx+2, idx+3)); idx += 4

        # -- Bottom Cap (Only on the bottom layer) --
        if layer_idx == 0:
            dark_cap_color = color.rgba(pine_r*0.3, pine_g*0.3, pine_b*0.3, 1)
            verts.extend([(wx+c_nw[0], c_nw[1], wz+c_nw[2]), (wx+c_ne[0], c_ne[1], wz+c_ne[2]),
                          (wx+c_se[0], c_se[1], wz+c_se[2]), (wx+c_sw[0], c_sw[1], wz+c_sw[2])])
            cols.extend([dark_cap_color]*4)
            tris.append((idx, idx+1, idx+2, idx+3)); idx += 4

    return idx