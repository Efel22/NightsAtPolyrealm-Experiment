import math
import random
from ursina import color
from .shared import *

def build_boulder_mesh(vertices, triangles, colors, current_index, x, y, z, random_gen, detail=1):
    # Determine the overall scale of the main boulder
    main_scale = random_gen.uniform(1.8, 3.5)
    
    # Create a base gray color for the rock
    
    # base_gray_val = random_gen.uniform(0.4, 0.6)
    # base_rock_color = color.rgba(base_gray_val, base_gray_val, base_gray_val + 0.05, 1)
    
    base_rock_color = darken(COLOR__BOULDER, random_gen.uniform(0.7,1.0))

    # 1. THE MAIN BOULDER
    # We vary the dimensions (width, height, depth) so it's not a perfect cube
    width = main_scale * random_gen.uniform(0.8, 1.2)
    height = main_scale * random_gen.uniform(0.6, 0.9) # Boulders are usually wider than tall
    depth = main_scale * random_gen.uniform(0.8, 1.2)
    
    # Use darken to give the main stone a unique shade
    main_color = darken(base_rock_color, random_gen.uniform(0.8, 1.2))
    
    # add_box usually centers on the X/Z, so we offset Y by half height to sit on the ground
    current_index = add_box(
        vertices, triangles, colors, current_index, 
        x, y + (height * 0.5), z, 
        width, height, depth, 
        main_color
    )

    # 2. ADD FRAGMENT STONES (The "Cool" Factor)
    # We add smaller rocks leaning against the main one to make it look like a natural formation
    num_fragments = random_gen.randint(2, 4)
    
    # If the detail is 0, then just generate the main stone and maybe 1 fragment
    if detail < 1:
        num_fragments = random_gen.randint(0, 1)

    for i in range(num_fragments):
        # Pick a random angle to place the fragment around the main boulder
        angle = random_gen.uniform(0, 6.28) # 0 to 2*PI
        distance = main_scale * random_gen.uniform(0.5, 0.8)
        
        # Calculate fragment position
        frag_x = x + math.cos(angle) * distance
        frag_z = z + math.sin(angle) * distance
        
        # Fragments should be significantly smaller and flatter
        f_scale = main_scale * random_gen.uniform(0.3, 0.5)
        f_w = f_scale * random_gen.uniform(0.7, 1.3)
        f_h = f_scale * random_gen.uniform(0.4, 0.8)
        f_d = f_scale * random_gen.uniform(0.7, 1.3)
        
        # Vary the color of each fragment so they don't blend into one blob
        frag_color = darken(base_rock_color, random_gen.uniform(0.6, 0.9))
        
        current_index = add_box(
            vertices, triangles, colors, current_index,
            frag_x, y + (f_h * 0.5), frag_z,
            f_w, f_h, f_d,
            frag_color
        )

    return current_index


def build_peak_mesh(vertices, triangles, colors, current_index, start_x, start_z, top_y, cell_size, random_gen):
    """
    Builds a subtle, geometric gray pyramid with a distinct snow cap.
    """
    center_x = start_x + cell_size / 2.0
    center_z = start_z + cell_size / 2.0
    
    # 1. Colors - Clean and High Contrast
    rock_color = color.rgba(0.45, 0.45, 0.48, 1) # Solid Slate Gray
    snow_color = color.rgba(0.98, 0.98, 1.0, 1)  # Crisp White
    
    # 2. Dimensions
    # Subtle height (1.2x to 1.5x cell size)
    total_height = cell_size * random_gen.uniform(0.45, 1.75)
    base_width = cell_size * 0.45
    
    # The "Snow Line" - where the rock ends and snow begins
    snow_line_y = top_y + (total_height * 0.65) 
    # Width of the pyramid at the snow line (interpolation)
    mid_width = base_width * 0.35 

    def add_pyramid_segment(b_x, b_z, b_w, t_x, t_z, t_w, bottom_y, top_y_val, col):
        """Creates a 4-sided tapered box (frustum) or pyramid tip"""
        nonlocal current_index
        
        # Define the 4 corners at the bottom
        b_pts = [
            (b_x - b_w, bottom_y, b_z - b_w),
            (b_x + b_w, bottom_y, b_z - b_w),
            (b_x + b_w, bottom_y, b_z + b_w),
            (b_x - b_w, bottom_y, b_z + b_w)
        ]
        
        # Define the 4 corners at the top
        t_pts = [
            (t_x - t_w, top_y_val, t_z - t_w),
            (t_x + t_w, top_y_val, t_z - t_w),
            (t_x + t_w, top_y_val, t_z + t_w),
            (t_x - t_w, top_y_val, t_z + t_w)
        ]

        # Build 4 side faces
        for i in range(4):
            p1 = b_pts[i]
            p2 = b_pts[(i + 1) % 4]
            p3 = t_pts[(i + 1) % 4]
            p4 = t_pts[i]

            # Shading: Darken side faces slightly for 3D depth
            side_shade = 0.8 if i % 2 == 0 else 1.0
            final_col = darken(col, side_shade)

            vertices.extend([p1, p2, p3, p4])
            colors.extend([final_col] * 4)
            triangles.append((current_index, current_index + 1, current_index + 2, current_index + 3))
            current_index += 4

    # --- Step 1: The Rock Base (The large bottom part) ---
    # A tiny bit of "Lean" for interest
    peak_offset_x = random_gen.uniform(-0.1, 0.1)
    peak_offset_z = random_gen.uniform(-0.1, 0.1)
    
    add_pyramid_segment(
        center_x, center_z, base_width,          # Bottom base
        center_x + peak_offset_x, center_z + peak_offset_z, mid_width, # Top base
        top_y, snow_line_y, 
        rock_color
    )

    # --- Step 2: The Snow Cap (The pointy top) ---
    # We taper this down to a width of 0 (a true point)
    add_pyramid_segment(
        center_x + peak_offset_x, center_z + peak_offset_z, mid_width, # Bottom (match rock top)
        center_x + peak_offset_x * 1.2, center_z + peak_offset_z * 1.2, 0, # The Apex
        snow_line_y, top_y + total_height, 
        snow_color
    )

    return current_index