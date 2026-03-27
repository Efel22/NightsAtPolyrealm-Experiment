import math

def fade(t):
    """
    Smooths the transition between points (6t^5 - 15t^4 + 10t^3).
    This is what makes Perlin noise look like clouds/hills instead of jagged squares.
    """
    return t * t * t * (t * (t * 6 - 15) + 10)

def lerp(t, start, end):
    """Linear interpolation: blends two values based on a percentage (t)."""
    return start + t * (end - start)

def grad(hash_value, x, z):
    """
    Determines the 'slope' of the noise at a specific grid corner.
    It uses the hash_value to pick one of 8 directions.
    """
    h = hash_value & 15
    # Pick x or z based on the hash
    u = x if h < 8 else z
    
    # Complex bitwise logic to pick the second coordinate (v)
    if h < 4:
        v = z
    elif h == 12 or h == 14:
        v = x
    else:
        v = 0
        
    return (u if (h & 1) == 0 else -u) + (v if (h & 2) == 0 else -v)

def get_noise(perm_table, x, z):
    """
    The main 2D Perlin Noise generator.
    perm_table: A list of 512 shuffled numbers used for pseudo-randomness.
    """
    # 1. Identify which 'cell' in the 255x255 grid we are in
    grid_x = int(math.floor(x)) & 255
    grid_z = int(math.floor(z)) & 255
    
    # 2. Find the decimal position (0.0 to 1.0) inside that cell
    rel_x = x - math.floor(x)
    rel_z = z - math.floor(z)
    
    # 3. Calculate smooth curves for the x and z positions
    u = fade(rel_x)
    v = fade(rel_z)
    
    # 4. Use the permutation table to find 'random' values for the corners
    # A and B represent the hashed coordinates of the grid cell
    corner_a = perm_table[grid_x] + grid_z
    corner_b = perm_table[grid_x + 1] + grid_z
    
    # 5. Blend the four corners together using LERP
    # This creates a continuous, smooth surface
    return lerp(v,
        lerp(u, 
            grad(perm_table[corner_a],     rel_x,   rel_z),   
            grad(perm_table[corner_b],     rel_x-1, rel_z)
        ),
        lerp(u, 
            grad(perm_table[corner_a + 1], rel_x,   rel_z-1), 
            grad(perm_table[corner_b + 1], rel_x-1, rel_z-1)
        )
    )

def octave_noise(perm_table, x, z, octaves=3, persistence=0.75, scale=1.0):
    """
    Adds layers of noise (octaves) together to create detail.
    perm_table: The same shuffled list used in get_noise.
    persistence: Controls how 'rough' the terrain is (0.5 is standard). Higher value = rougher terrain!
    scale: Controls the zoom level (1/800.0 is very zoomed out).
    """
    total_value = 0.0
    amplitude = 1.0
    frequency = scale
    max_value = 0.0

    for _ in range(octaves):
        # We pass the perm_table into get_noise for each layer
        total_value += get_noise(perm_table, x * frequency, z * frequency) * amplitude
        
        # Keep track of the maximum possible height to normalize the result later
        max_value += amplitude
        amplitude *= persistence
        frequency *= 2.0
        
    # Return a value typically between -1.0 and 1.0 (or 0.0 to 1.0 depending on your grad)
    return total_value / max_value