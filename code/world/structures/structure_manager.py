from ursina import *
import math
import random

from code.world.world_settings import *
from .skeleton_encampment import SkeletonEncampment
from .wizard_tower         import WizardTower
from .giant_tree           import GiantTree
from .graveyard            import Graveyard

# -- Biome spawn table -----------------------------------------------------
# Defines which structure types are allowed to appear in each biome
STRUCTURE_BIOME_TABLE = {
    "skeleton_encampment": [PLAINS, DESERT, TAIGA, MOUNTAIN],
    "wizard_tower":        [PLAINS, FOREST, TAIGA, MOUNTAIN],
    "giant_tree":          [FOREST, ASPEN, PLAINS],
    "graveyard":           [PLAINS, DESERT, TAIGA, FOREST],
}

# Probability that any given chunk slot will contain a structure (0.0 – 1.0)
# STRUCTURE_SPAWN_CHANCE = 0.016
STRUCTURE_SPAWN_CHANCE = 0.05


class StructureManager:
    """
    Spawns and despawns structures alongside the chunk system.
    Rules:
      - One structure maximum per chunk slot
      - Same chunk always produces the same structure (deterministic RNG)
      - Structures stay loaded well beyond the terrain detail radius
        so players can't cheese by briefly stepping away
      - Structures are only VISIBLE within NEAR_IMPOSTOR_RADIUS
        to avoid them being seen from across the map
      - Once a structure's kill cap is reached it is permanently cleared
        and will never respawn even if the chunk reloads
    """

    def __init__(self, world, entity_manager, get_player_fn):
        self.world          = world
        self.entity_manager = entity_manager
        self.get_player     = get_player_fn

        # Maps (chunk_x, chunk_z) -> active Structure instance
        self._active_structures: dict = {}

        # Chunk slots the player has permanently cleared, never respawn here
        self._cleared_chunks: set = set()

        # Occupied chunk used in world.py to determine whether the chunk has a structure or not
        self.occupied_chunks: set = set()

    def get_occupied_chunks(self):
        return self.occupied_chunks

    # ------------------------------------------------------------------ #

    def update(self, player_chunk_x: int, player_chunk_z: int,
               detail_radius: int, chunk_size: int):
        """
        Call every frame from main update.
        Handles spawning, despawning, visibility toggling,
        kill cap tracking, and ticking all active structures.
        """

        # Structures stay loaded much further than terrain chunks
        # so the player can't step just outside the detail zone to reset them
        structure_keep_radius = detail_radius + 8

        in_range = set()

        for cz in range(player_chunk_z - structure_keep_radius,
                        player_chunk_z + structure_keep_radius + 1):
            for cx in range(player_chunk_x - structure_keep_radius,
                            player_chunk_x + structure_keep_radius + 1):
                in_range.add((cx, cz))

                # Spawn a structure here if the slot is empty and not cleared
                if (cx, cz) not in self._active_structures:
                    self._try_spawn(cx, cz, chunk_size)

        # -- Visibility toggle ---------------------------------------------
        # Show structures only within NEAR_IMPOSTOR_RADIUS chunks of the player
        # Structures beyond that are still loaded but invisible
        for (cx, cz), structure in self._active_structures.items():
            chunk_dist_from_player = max(
                abs(cx - player_chunk_x),
                abs(cz - player_chunk_z)
            )
            structure.set_visible(chunk_dist_from_player <= NEAR_IMPOSTOR_RADIUS)

        # -- Permanent clear tracking --------------------------------------
        # Check for newly inactive structures WHILE they are still loaded
        # so the cleared state is saved before the chunk ever gets a chance to unload
        for k, structure in self._active_structures.items():
            if structure._inactive and k not in self._cleared_chunks:
                self._cleared_chunks.add(k)
                print(f"[StructureManager] Chunk {k} permanently cleared!")

        # -- Despawn out-of-range structures -------------------------------
        to_remove = [k for k in self._active_structures if k not in in_range]
        for k in to_remove:
            self._active_structures[k].destroy()
            del self._active_structures[k]
            self.occupied_chunks.discard(k) # unmark the chunk

        # -- Tick all active structures ------------------------------------
        # Each structure handles its own mob spawning and kill tracking
        for structure in list(self._active_structures.values()):
            structure.update(time.dt)

    # ------------------------------------------------------------------ #

    def _try_spawn(self, chunk_x: int, chunk_z: int, chunk_size: int):
        """
        Deterministically decide whether to spawn a structure in this chunk slot.
        Uses a seeded RNG so the same chunk always produces the same outcome.
        """

        # Skip chunks the player has already permanently cleared
        if (chunk_x, chunk_z) in self._cleared_chunks:
            return

        # Only spawn once the terrain chunk is actually loaded so get_ground_y works
        if (chunk_x, chunk_z) not in self.world.chunks:
            return

        # Deterministic seed, same chunk coords always rolls the same result
        chunk_rng = random.Random(
            (chunk_x * 73856093) ^ (chunk_z * 19349663) ^ 4242
        )

        # Roll to decide if a structure spawns here at all
        if chunk_rng.random() > STRUCTURE_SPAWN_CHANCE:
            return

        # Sample biome at the centre of this chunk slot
        centre_wx = chunk_x * chunk_size + chunk_size // 2
        centre_wz = chunk_z * chunk_size + chunk_size // 2
        biome     = self.world.get_biome(centre_wx, centre_wz)

        # Structures don't spawn in ocean chunks
        if biome == OCEAN:
            return

        # Use get_ground_y to get the ACTUAL surface height, get_height alone
        # misses the roughness variation added in generate_chunk
        avg_h = self.world.get_ground_y(centre_wx, centre_wz)

        height = self.world.get_height(centre_wx, centre_wz, biome)
        if biome == MOUNTAIN and height >= MOUNTAIN_PEAK_HEIGHT:
            return

        # Find which structure types are valid for this biome
        valid_structure_types = [
            s_type for s_type, allowed_biomes in STRUCTURE_BIOME_TABLE.items()
            if biome in allowed_biomes
        ]
        if not valid_structure_types:
            return

        # Pick one structure type from the valid options
        structure_type = chunk_rng.choice(valid_structure_types)
        spawn_pos      = Vec3(centre_wx, avg_h, centre_wz)
        structure_size = chunk_size * 0.9

        structure = self._build_structure(
            structure_type, spawn_pos, structure_size, chunk_rng
        )
        if structure:
            self._active_structures[(chunk_x, chunk_z)] = structure
            self.occupied_chunks.add((chunk_x, chunk_z)) # Mark the chunk

    # ------------------------------------------------------------------ #

    def will_have_structure(self, chunk_x: int, chunk_z: int) -> bool:
        """
        Deterministically checks if a chunk slot would spawn a structure,
        using the same RNG logic as _try_spawn but without actually spawning.
        Safe to call from background threads.
        """
        if (chunk_x, chunk_z) in self._cleared_chunks:
            return False

        chunk_rng = random.Random(
            (chunk_x * 73856093) ^ (chunk_z * 19349663) ^ 4242
        )

        # Same roll as _try_spawn
        if chunk_rng.random() > STRUCTURE_SPAWN_CHANCE:
            return False

        # Sample biome to check if it supports structures
        centre_wx = chunk_x * CHUNK_SIZE + CHUNK_SIZE // 2
        centre_wz = chunk_z * CHUNK_SIZE + CHUNK_SIZE // 2
        biome     = self.world.get_biome(centre_wx, centre_wz)

        if biome == OCEAN:
            return False

        height = self.world.get_height(centre_wx, centre_wz, biome)
        if biome == MOUNTAIN and height >= MOUNTAIN_PEAK_HEIGHT:
            return False

        valid = [
            s for s, biomes in STRUCTURE_BIOME_TABLE.items()
            if biome in biomes
        ]
        return len(valid) > 0

    # ------------------------------------------------------------------ #

    def _build_structure(self, structure_type: str, position: Vec3,
                          size: float, rng: random.Random):
        """Instantiate and return the correct Structure subclass."""
        kwargs = dict(
            position       = position,
            size           = size,
            rng            = rng,
            entity_manager = self.entity_manager,
            get_player_fn  = self.get_player,
        )
        mapping = {
            "skeleton_encampment": SkeletonEncampment,
            "wizard_tower":        WizardTower,
            "giant_tree":          GiantTree,
            "graveyard":           Graveyard,
        }
        cls = mapping.get(structure_type)
        return cls(**kwargs) if cls else None