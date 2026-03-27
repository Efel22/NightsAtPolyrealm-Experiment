import math
import random
from ursina import color
from .shared import *
from code.world.world_settings import *


# ============================================================
# ======================= CACTUS =============================
# ============================================================



def build_cactus_mesh(vertices, triangles, colors, current_index, x, y, z, rng):
    """
    Builds a Saguaro-style cactus. 
    Note: base_color is now pulled from the CACTUS_GREEN constant.
    """
    
    # Create natural shading variations using the darken function
    # We use the constant CACTUS_GREEN since it's no longer a parameter
    cactus_body_color = darken(COLOR__CACTUS, rng.uniform(0.9, 1.0))
    cactus_arm_shade_color = darken(COLOR__CACTUS, rng.uniform(0.7, 0.8)) 
    flower_color = darken(COLOR__CACTUS_FLOWER, rng.uniform(0.7, 1.0)) 

    # --- 1. Main Trunk ---
    trunk_h = rng.uniform(1.5, 3.8)
    trunk_w = rng.uniform(0.65, 0.9)
    
    # add_box(verts, tris, cols, idx, x, y, z, width, height, depth, color)
    current_index = add_box(
        vertices, triangles, colors, current_index,
        x, y + trunk_h / 2, z,
        trunk_w, trunk_h, trunk_w,
        cactus_body_color
    )

    # --- 2. Cactus Arms ---
    num_arms = rng.randint(1, 2)
    arm_tips = []

    for i in range(num_arms):
        # Pick a side (0, 90, 180, or 270 degrees)
        angle = rng.choice([0, math.pi/2, math.pi, 3*math.pi/2])
        
        spawn_y = y + trunk_h * rng.uniform(0.4, 0.7)
        out_dist = rng.uniform(0.6, 0.9)
        up_dist = rng.uniform(0.8, 1.4)
        
        dir_x = math.cos(angle)
        dir_z = math.sin(angle)

        # --- Horizontal "Shoulder" ---
        shoulder_x = x + (dir_x * out_dist / 2)
        shoulder_z = z + (dir_z * out_dist / 2)
        
        # Determine width based on direction so the box aligns correctly
        width_x = out_dist if abs(dir_x) > 0.1 else 0.35
        width_z = out_dist if abs(dir_z) > 0.1 else 0.35

        current_index = add_box(
            vertices, triangles, colors, current_index,
            shoulder_x, spawn_y, shoulder_z,
            width_x, 0.35, width_z,
            cactus_arm_shade_color
        )

        # --- Vertical "Arm" ---
        finger_x = x + (dir_x * out_dist)
        finger_z = z + (dir_z * out_dist)
        finger_y = spawn_y + (up_dist / 2)

        current_index = add_box(
            vertices, triangles, colors, current_index,
            finger_x, finger_y, finger_z,
            0.45, up_dist, 0.45,
            cactus_body_color
        )
        
        # Save the top of the arm for a flower
        arm_tips.append((finger_x, spawn_y + up_dist, finger_z))

    # --- 3. Flower Logic ---
    # Add flowers to the top of the trunk and some arm tips
    check_spots = arm_tips + [(x, y + trunk_h, z)]
    
    for fx, fy, fz in check_spots:
        if rng.random() < 0.35:
            f_size = 0.3
            # Simple cross-plane flower (2 quads)
            for rot in [0, math.pi/2]:
                cx = math.cos(rot) * f_size
                cz = math.sin(rot) * f_size
                
                vertices.extend([
                    (fx - cx, fy, fz - cz),
                    (fx + cx, fy, fz + cz),
                    (fx + cx, fy + 0.3, fz + cz),
                    (fx - cx, fy + 0.3, fz - cz)
                ])
                colors.extend([flower_color] * 4)
                triangles.append((current_index, current_index + 1, current_index + 2, current_index + 3))
                current_index += 4

    return current_index

# ============================================================
# ==================== FLOWER   MESH =========================
# ============================================================

def build_flower_mesh(verts, tris, cols, idx, wx, wy, wz, rng):
    """
    Builds a detailed 3D flower with a stem, varied leaves, 
    and a multi-layered 'blooming' head.
    """
    # 1. Setup Colors (Handling the Tuple vs Object issue)
    base_flower_col = rng.choice(COLORS_FLOWERS)
    flower_col = tint_variation(base_flower_col, 0.1)
    stem_col = tint_variation(COLOR__FLOWER_STEM, 0.05)
    
    # LEAVES: We manually darken the stem tuple to avoid the AttributeError
    # leaf_base = (r * 0.6, g * 0.6, b * 0.6)
    leaf_base = (COLOR__FLOWER_STEM[0] * 0.6, 
                 COLOR__FLOWER_STEM[1] * 0.6, 
                 COLOR__FLOWER_STEM[2] * 0.6)
    
    # Apply the high variation (0.2) you requested
    leaf_col = tint_variation(leaf_base, 0.2)
    center_col = color.rgba(1.0, 0.8, 0.1, 1) # Yellow pistil

    # 2. The Stem
    sh = rng.uniform(0.6, 1.0)
    sw = 0.05
    idx = add_box(verts, tris, cols, idx, wx, wy + sh/2, wz, sw, sh, sw, stem_col)

    # 3. The Leaves (Sprouting from the stem)
    num_leaves = rng.randint(1, 2)
    for _ in range(num_leaves):
        leaf_y = wy + (sh * rng.uniform(0.2, 0.5))
        angle = rng.uniform(0, math.pi * 2)
        # Small offset so leaf isn't inside the stem center
        lx = math.cos(angle) * 0.12
        lz = math.sin(angle) * 0.12
        
        idx = add_box(
            verts, tris, cols, idx, 
            wx + lx, leaf_y, wz + lz, 
            0.2, 0.03, 0.1, # Thin flat leaf
            leaf_col
        )

    # 4. The Petals (Double-Cross 'Bloom' effect)
    petal_y = wy + sh
    pw, ph = 0.4, 0.12 # Petal width and height
    
    # Cross 1
    idx = add_box(verts, tris, cols, idx, wx, petal_y, wz, pw, ph, ph, flower_col)
    # Cross 2
    idx = add_box(verts, tris, cols, idx, wx, petal_y, wz, ph, ph, pw, flower_col)
    
    # 5. The Flower Center
    idx = add_box(verts, tris, cols, idx, wx, petal_y + 0.08, wz, 0.12, 0.12, 0.12, center_col)

    return idx

def build_flower_patch(vertices, triangles, colors, current_index, x, y, z, random_gen):
    """
    Spawns a group of 1-3 flowers with a minimum distance check to prevent overlapping.
    """
    num_flowers = random_gen.randint(1, 3)
    placed_positions = []
    min_distance = 0.25  # The minimum distance between flower stems
    
    for _ in range(num_flowers):
        # We try up to 5 times to find a valid spot for each flower
        for attempt in range(5):
            ox = random_gen.uniform(-0.4, 0.4) # Slightly wider spread
            oz = random_gen.uniform(-0.4, 0.4)
            
            # Check distance against all flowers already placed in this patch
            is_too_close = False
            for px, pz in placed_positions:
                # Euclidean distance check (Pythagorean theorem)
                dist = math.sqrt((ox - px)**2 + (oz - pz)**2)
                if dist < min_distance:
                    is_too_close = True
                    break
            
            # If the spot is valid (or we ran out of attempts), place the flower
            if not is_too_close or attempt == 4:
                current_index = build_flower_mesh(
                    vertices, triangles, colors, current_index,
                    x + ox, y, z + oz,
                    random_gen
                )
                placed_positions.append((ox, oz))
                break # Move to the next flower in num_flowers
                
    return current_index

# ============================================================
# ==================== MUSHROOM MESH =========================
# ============================================================

def build_mushroom_mesh(vertices, triangles, colors, current_index, x, y, z, rng):
    """
    Builds a more organic mushroom with a tapered stem, a two-tier cap, 
    and a shadowed underside (gills).
    """
    # 1. Colors
    cap_base_color = darken(rng.choice(COLORS_MUSHROOM_CAPS), rng.uniform(0.8,1.0))
    # Use our darken function for the "Gills" (the underside)
    gill_color = darken(cap_base_color, 0.8)
    stem_color = darken(COLOR__MUSHROOM_STEM, rng.uniform(0.7,1.0))

    # 2. Tapered Stem
    # We'll use two thin boxes stacked to make the stem look slightly bent or tapered
    stem_h = rng.uniform(0.4, 0.6)
    stem_w = rng.uniform(0.12, 0.16)
    
    current_index = add_box(
        vertices, triangles, colors, current_index,
        x, y + stem_h / 2, z,
        stem_w, stem_h, stem_w,
        stem_color
    )

    # 3. The Cap - Lower Tier (The "Gills" layer)
    # This is wider but very thin
    lower_w = rng.uniform(0.6, 0.8)
    lower_h = 0.15
    lower_y = y + stem_h + (lower_h / 2)

    current_index = add_box(
        vertices, triangles, colors, current_index,
        x, lower_y, z,
        lower_w, lower_h, lower_w,
        gill_color # Darker underside makes it look 3D
    )

    # 4. The Cap - Upper Tier (The "Dome")
    # This is narrower but taller, sitting right on top of the lower tier
    upper_w = lower_w * 0.7
    upper_h = rng.uniform(0.2, 0.3)
    upper_y = lower_y + (lower_h / 2) + (upper_h / 2)
    
    # Add a tiny random offset so the "point" of the mushroom isn't perfectly centered
    off_x = rng.uniform(-0.05, 0.05)
    off_z = rng.uniform(-0.05, 0.05)

    current_index = add_box(
        vertices, triangles, colors, current_index,
        x + off_x, upper_y, z + off_z,
        upper_w, upper_h, upper_w,
        cap_base_color # The main bright color
    )

    return current_index

def build_mushroom_cluster(verts, tris, cols, idx, wx, wy, wz, rng):
    """
    Spawns a small cluster of mushrooms with a distance check to prevent overlapping caps.
    """
    # Increased variety for a more natural forest look
    cluster_size = rng.randint(1, 3)
    placed_positions = []
    min_dist = 0.3  # Enough space so the wide caps don't merge into a blob
    
    for _ in range(cluster_size):
        # Try a few times to find a clear spot
        for attempt in range(5):
            ox = rng.uniform(-0.45, 0.45)
            oz = rng.uniform(-0.45, 0.45)

            # Distance check against already placed mushrooms in this cluster
            too_crowded = False
            for px, pz in placed_positions:
                # Euclidean distance: sqrt(dx^2 + dz^2)
                d = math.sqrt((ox - px)**2 + (oz - pz)**2)
                if d < min_dist:
                    too_crowded = True
                    break
            
            # If the spot is clear or we're out of tries, build it
            if not too_crowded or attempt == 4:
                idx = build_mushroom_mesh(
                    verts, tris, cols, idx,
                    wx + ox, wy, wz + oz,
                    rng
                )
                placed_positions.append((ox, oz))
                break 

    return idx


# ============================================================
# ==================== PEBBLE CLUSTERS =======================
# ============================================================



def build_pebble_cluster(verts, tris, cols, idx, wx, wy, wz, rng):
    """
    Generates a small cluster of tiny cube pebbles.
    """

    count = rng.randint(3, 9)

    for _ in range(count):
        size = rng.uniform(0.1, 0.25)
        ox = rng.uniform(-0.35, 0.35)
        oz = rng.uniform(-0.35, 0.35)

        idx = add_box(
            verts, tris, cols, idx,
            wx + ox,
            wy + size / 2,
            wz + oz,
            size, size, size,
            tint_variation(COLOR__PEBBLES, 0.2)
        )

    return idx


# ============================================================
# ====================== GRASS MESH ==========================
# ============================================================

def build_grass_mesh(verts, tris, cols, idx, wx, wy, wz, col, biome, rng, detail = 2):
    """
    Grass clump with optional flowers, mushrooms, and pebbles.
    """

    # Detail? What is it?
    # The detail value is divided into 0->2
    # 0 = Return, do nothing
    # 1 = Generate Grass only
    # 2 = Generate everything

    base = color.rgba(col[0], col[1], col[2], 1)
    dark = color.rgba(col[0] * 0.45, col[1] * 0.45, col[2] * 0.45, 1)


    if biome not in NO_GRASS_BIOMES and detail >= 1:
        if rng.random() < 0.75:
            # 75% of the time
            grass_blades = rng.randint(1, 4)
        else:
            # 25% of the time
            grass_blades = rng.randint(5, 8)

        if detail == 1:
            grass_blades = rng.randint(2,3)


        # --- Grass blades ---
        for _ in range(grass_blades):
            h = rng.uniform(0.2, 1.0)

            height_multiplier = max(1.0, 3.0 - detail) 
            h = h * height_multiplier

            w = rng.uniform(0.08, 0.18)
            width_multiplier = max(1.0, 3.0 - detail) 
            w = w * width_multiplier

            lean_x = rng.uniform(-0.3, 0.3)
            lean_z = rng.uniform(-0.3, 0.3)
            angle = rng.uniform(0, math.pi)

            cos_a = math.cos(angle)
            sin_a = math.sin(angle)

            ox = rng.uniform(-0.3, 0.3)
            oz = rng.uniform(-0.3, 0.3)

            bx1 = -w * cos_a
            bz1 = -w * sin_a
            bx2 =  w * cos_a
            bz2 =  w * sin_a

            tx1 = bx1 + lean_x
            tz1 = bz1 + lean_z
            tx2 = bx2 + lean_x
            tz2 = bz2 + lean_z

            verts.extend([
                (wx + ox + bx1, wy,     wz + oz + bz1),
                (wx + ox + bx2, wy,     wz + oz + bz2),
                (wx + ox + tx2, wy + h, wz + oz + tz2),
                (wx + ox + tx1, wy + h, wz + oz + tz1),
            ])

            cols.extend([dark, dark, base, base])
            tris.append((idx, idx + 1, idx + 2, idx + 3))
            idx += 4

    
    # --- Pebble cluster ---
    if rng.random() < BIOME_PEBBLES_CHANCE[biome] and biome not in NO_PEBBLES_BIOMES and detail >= 2:
        idx = build_pebble_cluster(
            verts, tris, cols, idx,
            wx + rng.uniform(-0.4, 0.4),
            wy,
            wz + rng.uniform(-0.4, 0.4),
            rng
        )

    # --- Small flower ---
    if rng.random() < BIOME_FLOWERS_CHANCE[biome] and biome not in NO_FLOWERS_BIOMES and detail >= 2:
        idx = build_flower_patch(
        verts, tris, cols, idx,
        wx + rng.uniform(-0.2, 0.2), # Slight random jitter for the whole patch
        wy,
        wz + rng.uniform(-0.2, 0.2),
        rng
    )

    
# --- Sparse mushroom cluster ---
    if rng.random() < BIOME_MUSHROOM_CHANCE[biome] and biome not in NO_MUSHROOMS_BIOMES and detail >= 2:
        idx = build_mushroom_cluster(
            verts, tris, cols, idx,
            wx + rng.uniform(-0.4, 0.4),
            wy,
            wz + rng.uniform(-0.4, 0.4),
            rng
        )




    return idx