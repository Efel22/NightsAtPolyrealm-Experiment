from ursina import *

def hex_to_rgb(hex_code, normalize=True):
    hex_code = hex_code.lstrip('#')
    lv = len(hex_code)
    rgb = tuple(int(hex_code[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))
    if normalize:
        return tuple(c / 255.0 for c in rgb)
    return rgb

    

# BIOME IDS
PLAINS=0; DESERT=1; TAIGA=2; FOREST=3; MOUNTAIN=4; MOUNTAIN_SNOW=-4; OCEAN=5; ASPEN=6; BEACH=7

BIOME_TOP_COLOR = {
    PLAINS:        hex_to_rgb("#91B90D"), 
    DESERT:        hex_to_rgb("#fcd19e"), #d2b48c
    TAIGA:         hex_to_rgb("#2E9E85"), 
    FOREST:        hex_to_rgb("#229a12"),  #2D8C47 og?
    MOUNTAIN:      hex_to_rgb("#359C65"),
    MOUNTAIN_SNOW: hex_to_rgb("#D6E0ED"),
    OCEAN:         hex_to_rgb("#1A6EB5"),
    ASPEN:         hex_to_rgb("#B8C733"), 
    BEACH:         hex_to_rgb("#D2B48C"),
}

BIOME_SIDE_COLOR = {
    PLAINS:        hex_to_rgb("#5C3D2E"), 
    DESERT:        hex_to_rgb("#b8785f"), #BF9E6B
    TAIGA:         hex_to_rgb("#5C3D2E"),
    FOREST:        hex_to_rgb("#442c2e"), 
    MOUNTAIN:      hex_to_rgb("#808080"),
    MOUNTAIN_SNOW: hex_to_rgb("#666666"),
    OCEAN:         hex_to_rgb("#335999"),
    ASPEN:         hex_to_rgb("#5C3D2E"),
    BEACH:         hex_to_rgb("#B39466"), 
}

BIOME_GRASS_COLOR = {
    PLAINS:        BIOME_TOP_COLOR[PLAINS],
    DESERT:        hex_to_rgb("#d7a163"), #49350c
    TAIGA:         BIOME_TOP_COLOR[TAIGA], 
    FOREST:        BIOME_TOP_COLOR[FOREST],
    MOUNTAIN:      BIOME_TOP_COLOR[MOUNTAIN],
    MOUNTAIN_SNOW: hex_to_rgb("#BEBEFF"),
    OCEAN:         BIOME_TOP_COLOR[OCEAN],
    ASPEN:         BIOME_TOP_COLOR[ASPEN],
    BEACH:         BIOME_TOP_COLOR[BEACH],
}

# GENERIC SNOW
COLOR__SNOW = hex_to_rgb("#E7E7FF")

# CACTUS
COLOR__CACTUS        = color.rgba(*hex_to_rgb("#97a744"), 1) #6E8A35
COLOR__CACTUS_FLOWER = color.rgba(*hex_to_rgb("#F24D8C"), 1)

# FLOWERS
COLOR__FLOWER_STEM = (*hex_to_rgb("#2E7320"), 1)
COLORS_FLOWERS = [
    color.rgba(*hex_to_rgb("#0A97D5"), 1),  # Blue
    color.rgba(*hex_to_rgb("#EE667C"), 1),  # Pink
    color.rgba(*hex_to_rgb("#D82323"), 1),  # Red
    color.rgba(*hex_to_rgb("#F6A421"), 1),  # Orange
    color.rgba(*hex_to_rgb("#FF2097"), 1),  # Pink-Dark
]

# MUSHROOMS
COLOR__MUSHROOM_STEM = color.rgba(*hex_to_rgb("#8E99A8"), 1)
COLORS_MUSHROOM_CAPS = [
    color.rgba(*hex_to_rgb("#D41955"), 1),  # RED
    color.rgba(*hex_to_rgb("#6F4339"), 1),  # BROWN
]

# PEBBLES
COLOR__PEBBLES = color.rgba(*hex_to_rgb("#8C8C8C"), 1)

# BOULDER
COLOR__BOULDER = color.rgba(*hex_to_rgb("#767f83"), 1)

# PLAINS TREE
COLOR__PLAINS_TREE_LEAVES = color.rgba(*hex_to_rgb("#5FA233"), 1) # OG: #238D2E
COLOR__PLAINS_TREE_TRUNK  = color.rgba(*hex_to_rgb("#905E27"), 1) # OG: #4E3B29

# FOREST TREE
COLOR__FOREST_TREE_LEAVES = color.rgba(*hex_to_rgb("#1e8756"), 1) # OG: #238D2E
COLOR__FOREST_TREE_TRUNK  = color.rgba(*hex_to_rgb("#5d0d13"), 1) # OG: #4E3B29

# ASPEN TREE
COLOR__ASPEN_TREE_LEAVES = hex_to_rgb("#e66b0d")
COLOR__ASPEN_TREE_TRUNK  = color.rgba(*hex_to_rgb("#f2f2f2"), 1)

# PINE TREE
COLOR__PINE_TREE_LEAVES = hex_to_rgb("#2ca07b")
COLOR__PINE_TREE_TRUNK  = color.rgba(*hex_to_rgb("#4A371D"), 1)

# SNOW PINE TREE
COLOR__SNOWY_PINE_TREE_LEAVES = hex_to_rgb("#188f69")
COLOR__SNOWY_PINE_TREE_TRUNK  = color.rgba(*hex_to_rgb("#3d2e29"), 1)
COLOR__SNOWY_PINE_TREE_SNOW  = color.rgba(*hex_to_rgb("#d1e7ff"), 1)