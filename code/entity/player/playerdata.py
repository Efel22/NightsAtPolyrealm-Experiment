from ursina import *
import math
import random
from ursina.prefabs.first_person_controller import FirstPersonController

from code.world.world_settings import CHUNK_SIZE, DETAIL_RADIUS, WATER_LEVEL, BEACH, OCEAN, MOUNTAIN_PEAK_HEIGHT
from code.world.world import world
# from code.world.structures.structure_manager import StructureManager
from code.entity.entities import EntityManager, EntitySpawner
from code.world.sky import SkySystem
from code.entity.player.swordswing import SwordSwing
from code.entity.player.camerabob import CameraBob
from code.entity.player.bowshot import BowShot
from code.entity.player.player_stats import PlayerStats
from code.sound import play_sound
from code.entity.player.night_tracker import night_tracker
from code.entity.player.death_screen  import DeathScreen
from code.entity.player.xp_system import xp_system
from code.entity.player.abilities import AbilityManager
from code.entity.player.weapons import Sword, Bow


# -- Player ----------------------------------------------------------------
# player = FirstPersonController()
# player.position = (0, 10, 0)
# player.speed    = 10

# Walk and sprint speeds
WALK_SPEED   = 10
SPRINT_SPEED = 22
is_sprinting = False

def get_player():
    return player


# -- Sky & World Management ------------------------------------------------
# Imported lazily inside setup() to avoid circular imports with world.py
sky_system        = None
entity_manager    = None
entity_spawner    = None
structure_manager = None


def setup(world):
    global player, sky_system, entity_manager, entity_spawner, structure_manager

    # Player must be created AFTER app = Ursina() is called in main.py
    player = FirstPersonController()
    # player.position = (0, 10, 0)

    sky_system        = SkySystem()
    entity_manager    = EntityManager(world)
    entity_spawner    = EntitySpawner(entity_manager, world)
    entity_spawner.set_player(player)
    world.set_struct_manager(world, entity_manager, get_player)
    # structure_manager = StructureManager(world, entity_manager, get_player)

    # Spawn player on the nearest non-ocean land
    safe_pos = find_safe_spawn(world, randomize=True)
    player.position = safe_pos
    print(f"[setup] Player spawned at {safe_pos}")

# -- Player Systems -------------------------------------------------
# These are created after setup() is called from main.py

player_stats: PlayerStats = None
current_melee  = None
current_ranged = None
camera_bob  = None
death_screen: DeathScreen = None


def setup_combat():
    global sword_swing, bow_shot, camera_bob, player_stats, death_screen, ability_manager, current_melee, current_ranged

    # Start with default weapons
    current_melee  = Sword(player, entity_manager)
    current_ranged = Bow(player, entity_manager, entity_manager.register_projectile)

    # sword_swing = SwordSwing(player, entity_manager)
    # bow_shot    = BowShot(player, entity_manager, entity_manager.register_projectile)
    camera_bob  = CameraBob(player)
    entity_manager.set_player(get_player)
    player_stats = PlayerStats(player, WALK_SPEED, SPRINT_SPEED)
    entity_spawner.set_player_stats(player_stats)
    death_screen = DeathScreen(
        player        = player,
        on_play_again = _on_play_again,
        on_quit       = _on_quit,
    )
    # Give player_stats a direct reference so _on_death can find it
    player_stats.death_screen  = death_screen
    player_stats.entity_manager = entity_manager

    # Ability manager
    ability_manager = AbilityManager(player_stats, player)

    # Connect XP level up events and player stat increases
    xp_system.on_level_up      = player_stats.on_level_up
    xp_system.on_ability_pick  = lambda: ability_manager.offer_choices(None)

def _swap_melee(weapon_class):
    """Destroy the current melee weapon and replace it with a new one."""
    global current_melee
    if current_melee:
        current_melee.destroy()
    current_melee = weapon_class(player, entity_manager)

def _swap_ranged(weapon_class):
    """Destroy the current ranged weapon and replace it with a new one."""
    global current_ranged
    if current_ranged:
        current_ranged.destroy()
    current_ranged = weapon_class(player, entity_manager,
                                  entity_manager.register_projectile)

def _on_play_again():
    """Reset the game state when the player clicks Play Again."""
    from code.entity.player.xp_system import xp_system
    from code.entity.player.night_tracker import night_tracker

    # Reset player stats
    player_stats.health  = player_stats.MAX_HEALTH
    player_stats.stamina = player_stats.MAX_STAMINA

    # Reset night counter
    night_tracker.nights_survived = 0

    # Kill all entities
    entity_manager.despawn_all()

    # Respawn player
    safe_pos = find_safe_spawn(world, randomize=True)
    player.position = safe_pos
    # player.position = (0, 50, 0)

    # Reset player's gravity (if not, it will remain in the air)
    player.gravity = 1.0

    # Reset player's abilities
    ability_manager.reset_all()

    # Restart the Sky!
    sky_system.reset()

def _on_quit():
    quit()

def find_safe_spawn(world, start_x=0, start_z=0, search_radius=500, step=CHUNK_SIZE, randomize=False):
    """
    Searches outward from start_x, start_z until it finds a non-ocean position.
    If randomize=True, offsets the search origin by a large random amount first
    so the world feels fresh each run.
    """
    from code.world.world_settings import WATER_LEVEL
    import random

    if randomize:
        # Shift the search origin far away so the world feels new each time
        start_x = random.randint(-15000, 15000)
        start_z = random.randint(-15000, 15000)
        print(f"[find_safe_spawn] Randomized origin to ({start_x}, {start_z})")

    # Check the origin first
    biome = world.get_biome(start_x, start_z)
    if biome not in (OCEAN, BEACH):
        return Vec3(start_x, MOUNTAIN_PEAK_HEIGHT+2, start_z)

    # Spiral outward in chunks until we find land
    for radius in range(step, search_radius, step):
        for dx in range(-radius, radius + step, step):
            for dz in [-radius, radius]:
                biome = world.get_biome(start_x + dx, start_z + dz)
                if biome not in (OCEAN, BEACH):
                    x = start_x + dx
                    z = start_z + dz
                    return Vec3(x, MOUNTAIN_PEAK_HEIGHT+2, z)
        for dz in range(-radius, radius + step, step):
            for dx in [-radius, radius]:
                biome = world.get_biome(start_x + dx, start_z + dz)
                if biome not in (OCEAN, BEACH):
                    x = start_x + dx
                    z = start_z + dz
                    return Vec3(x, MOUNTAIN_PEAK_HEIGHT+2, z)

    # Fallback if nothing found within search radius
    print("[find_safe_spawn] No land found, defaulting to origin")
    return Vec3(start_x, WATER_LEVEL + 15, start_z)

# -- Per-frame update, call from main update() ----------------------------
def update_player(dt, world):
    sky_system.update_sky(world)
    world.update_world(player)
    entity_manager.update(dt, player)

    current_melee.update(dt) # MELEE WEAPON UPDATE
    current_ranged.update(dt) # RANGED WEAPON UPDATE

    camera_bob.update(dt, player_stats.is_sprinting)
    entity_spawner.update(dt)
    player_stats.update(dt)

    # Feed current day/night state to the night tracker
    night_tracker.notify_day_night(sky_system.is_night)

    # Dynamically adjust spawner settings based on night difficulty
    entity_spawner.spawn_interval      = night_tracker.current_spawn_interval()
    entity_spawner.max_spawned_entities = night_tracker.current_max_entities()
    entity_spawner.spawn_distance = night_tracker.current_spawn_distance()

    p_x = math.floor(player.x / CHUNK_SIZE)
    p_z = math.floor(player.z / CHUNK_SIZE)
    # structure_manager.update(p_x, p_z, DETAIL_RADIUS, CHUNK_SIZE)
    
    # Airtime calc (this is an attempt to fix mace's airtime damage):
    if player.grounded:
        player_stats.time_in_air = 0
    else:
        player_stats.time_in_air += 0.1

    # Allows for use of double jump (else it won't trigger again!)
    if player.grounded:
        player_stats.has_done_double_jump = False

    # Player can't go into the ocean!
    if player.y <= WATER_LEVEL - 1:
        player_stats.take_damage(player_stats.MAX_HEALTH)
        player.y = WATER_LEVEL
        player.gravity = 0


# -- Input handler, call from main input() --------------------------------
def handle_input(key):
    global is_sprinting

    if key == 'left shift':
        player_stats.try_start_sprint()

    if key == 'left shift up':
        player_stats.stop_sprint()

    # Weapon Usage
    if key == 'left mouse down':
        current_melee.try_swing()    
    if key == 'right mouse down':
        current_ranged.try_shoot()   

    if key == 'space' and player.grounded:
        play_sound("entity/jump")

    if key == 'space' and not player.grounded and player_stats.can_double_jump:
        player_stats.double_jump()
        play_sound("entity/jump")

    if key == 'z':
        player.y = 1500

    if key == 't':
        player_stats.take_damage(player_stats.MAX_HEALTH)

    if key == 'r':
        xp_system.add_xp(xp_system.player_xp_to_next_level)

    if key == 'x':
        if player.gravity != 0.0:
            player.position = (player.x, 50, player.z)
            player.gravity  = 0.0
            player.speed    = 500
        else:
            player.gravity = 1.0
            player.speed   = WALK_SPEED