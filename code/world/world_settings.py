from ursina import *
from code.world.color_settings import *

# --- Important World Settings ---
WATER_LEVEL = -7
CHUNK_SIZE = 32
SLAB_BOTTOM = -8
MOUNTAIN_SNOW_HEIGHT = 15
MOUNTAIN_PEAK_HEIGHT = 30

# Detailed Chunks' Radius: Chunks that have Grass, Colliders and use the _density values
DETAIL_RADIUS = 1 # Default = 1

# Near Impostor Chunks' Radius: Chunks without collider that use _impostor_small() functions
NEAR_IMPOSTOR_RADIUS = 3 # Default = 3

# Large Impostor Chunks' Radius: Chunks without collider that use _impostor() functions (are really big)
IMPOSTOR_RADIUS = 3 # Default = 3

# Used mostly for testing purposes, increases other density values
DENSITY_MULTIPLIER = 1.0 * CHUNK_SIZE

BIOME_TREE_DENS = {
    PLAINS:   0.55 * DENSITY_MULTIPLIER,
    DESERT:   0.70 * DENSITY_MULTIPLIER,
    TAIGA:    0.70 * DENSITY_MULTIPLIER,
    FOREST:   0.75 * DENSITY_MULTIPLIER,
    MOUNTAIN: 1.50 * DENSITY_MULTIPLIER,
    OCEAN:    0.00 * DENSITY_MULTIPLIER,
    ASPEN:    0.75 * DENSITY_MULTIPLIER,
    BEACH:    0.00 * DENSITY_MULTIPLIER,
}

# Boulder Density for ALL biomes (can't adjust it for now)
BOULDER_DENSITY         = 0.10



# Biomes' Grass DENSITY (on ground, includes flowers, pebbles, etc) 
BIOME_GRASS_DENS = {
    PLAINS:   0.4,
    DESERT:   0.1,
    TAIGA:    0.3,
    FOREST:   0.3,
    MOUNTAIN: 0.1,
    OCEAN:    0.0,
    ASPEN:    0.3,
    BEACH:    0.0,
}

# Biomes' Flowers CHANCE 
BIOME_FLOWERS_CHANCE = {
    PLAINS:   0.04,
    DESERT:   0.0,
    TAIGA:    0.001,
    FOREST:   0.02,
    MOUNTAIN: 0.00,
    OCEAN:    0.0,
    ASPEN:    0.025,
    BEACH:    0.0,
}

# Biomes' Mushroom CHANCE 
BIOME_MUSHROOM_CHANCE = {
    PLAINS:   0.0045,
    DESERT:   0.0,
    TAIGA:    0.02,
    FOREST:   0.0075,
    MOUNTAIN: 0.0,
    OCEAN:    0.0,
    ASPEN:    0.005,
    BEACH:    0.000,
}

# Biomes' Grass CHANCE 
BIOME_PEBBLES_CHANCE = {
    PLAINS:   0.10,
    DESERT:   0.90,
    TAIGA:    0.20,
    FOREST:   0.05,
    MOUNTAIN: 0.90,
    OCEAN:    0.00,
    ASPEN:    0.02,
    BEACH:    0.90,
}

# --- BIOME CATEGORIES --- 

# NO_BLEND_BIOMES: Which biomes don't blend grass (ground/top) color with neighboors? 
NO_BLEND_BIOMES = (OCEAN, BEACH, DESERT, MOUNTAIN)

# NO_BLEND_BIOMES: Which biomes don't blend grass (ground/top) color with neighboors? 
NO_TOP_COLOR_VARIATION_BIOMES = (OCEAN, BEACH, DESERT, MOUNTAIN)

# NO_GRASS_BIOMES: Which biomes don't have GRASS (does NOT include FLOWERS, PEBBLES, etc.)
NO_GRASS_BIOMES = (OCEAN, BEACH)

# NO_FLOWERS_BIOMES: Which biomes don't have FLOWERS (does NOT include GRASS, PEBBLES, etc.)
NO_FLOWERS_BIOMES = (OCEAN, BEACH, DESERT, MOUNTAIN)

# NO_FLOWERS_BIOMES: Which biomes don't have MUSHROOMS (does NOT include FLOWERS, PEBBLES, etc.)
NO_MUSHROOMS_BIOMES = (OCEAN, BEACH, DESERT, MOUNTAIN)

# NO_PEBBLES_BIOMES: Which biomes don't have PEBBLES (does NOT include GRASS, FLOWERS, etc.)
NO_PEBBLES_BIOMES = ()





