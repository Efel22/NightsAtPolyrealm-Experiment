from ursina import *
import math
import random

from .structure_base import Structure
from code.world.color_settings import hex_to_rgb
from code.world.meshbuilders.shared import darken


class Graveyard(Structure):
    """
    A spooky graveyard with tombstones and a dead tree.
    Spawns zombies.
    """

    KILL_CAP         = 10
    RESPAWN_INTERVAL = 14.0
    MAX_ALIVE        = 3

    # Your updated color palette
    COLOR_STONE_LIGHT = (*hex_to_rgb("#6d708d"), 1) 
    COLOR_STONE_DARK  = (*hex_to_rgb("#4a4b62"), 1)
    COLOR_DIRT_OLD    = (*hex_to_rgb("#4e3431"), 1) 
    COLOR_DIRT_FRESH  = (*hex_to_rgb("#3f2832"), 1) 
    COLOR_MOSS        = (*hex_to_rgb("#389c46"), 1)
    COLOR_GRAVE_1     = (*hex_to_rgb("#8b93af"), 1)
    COLOR_GRAVE_2     = (*hex_to_rgb("#477d85"), 1)

    def _build(self, position: Vec3, size: float, rng: random.Random):
        verts, tris, cols, add_box = self._make_mesh_builder()
        ox, oy, oz = position.x, position.y, position.z
        
        # 1. MAIN GROUND PATCH
        add_box(ox, oy, oz, size, 1, size, self.COLOR_DIRT_OLD)

        # 2. PROBABILISTIC TOMBSTONES & FRESH GRAVES
        potential_slots = [
            (-size*0.3, -size*0.25), (size*0.25, -size*0.28),
            (-size*0.28, size*0.2),  (size*0.3, size*0.25),
            (size*0.05, -size*0.32), (-size*0.1, size*0.32),
            (size*0.32, size*0.05),  (-size*0.33, -size*0.05),
        ]

        for i, (tx, tz) in enumerate(potential_slots):
            if rng.random() < 0.85:
                ts_x, ts_y, ts_z = ox + tx, oy, oz + tz
                col = self.COLOR_GRAVE_1 if i % 2 == 0 else self.COLOR_GRAVE_2
                
                # The Tombstone
                ts_w, ts_h = rng.uniform(1.3, 1.7), rng.uniform(1.8, 2.4)
                add_box(ts_x, ts_y + ts_h/2, ts_z, ts_w, ts_h, 0.5, darken(col,rng.uniform(0.8,1.0)))
                add_box(ts_x, ts_y + ts_h + 0.1, ts_z, ts_w * 1.1, 0.3, 0.6, darken(col,rng.uniform(0.8,1.0)))

                # Fresh Grave Dirt
                grave_l = 2.8
                add_box(ts_x, oy + 0.35, ts_z - (grave_l/2 + 0.4), 
                        ts_w * 0.9, 0.75, grave_l, darken(self.COLOR_DIRT_FRESH,rng.uniform(0.8,1.0)))

        # 3. PERIMETER WALLS
        wall_h = 2.2
        wall_thick = 1.0
        b = size * 0.48
        
        # Walls: North, East, West
        add_box(ox, oy + wall_h/2, oz + b, size, wall_h, wall_thick, self.COLOR_STONE_DARK) 
        add_box(ox + b, oy + wall_h/2, oz, wall_thick, wall_h, size, self.COLOR_STONE_DARK) 
        add_box(ox - b, oy + wall_h/2, oz, wall_thick, wall_h, size, self.COLOR_STONE_DARK) 
        
        # South Entrance (with gap)
        gap = 4.5
        side_len = (size - gap) / 2
        add_box(ox - (size/2 - side_len/2), oy + wall_h/2, oz - b, side_len, wall_h, wall_thick, self.COLOR_STONE_DARK)
        add_box(ox + (size/2 - side_len/2), oy + wall_h/2, oz - b, side_len, wall_h, wall_thick, self.COLOR_STONE_DARK)

        # 4. PILLARS (Corners + Entrance)
        pill_w = 1.4  # Slightly wider for a heavy feel
        pill_h = wall_h + 1.2
        
        # List of coordinates for the 4 corners
        corners = [
            (b, b),   # North-East
            (-b, b),  # North-West
            (b, -b),  # South-East
            (-b, -b), # South-West
        ]
        
        # Entrance positions
        gate_posts = [
            (gap/2 + 0.5, -b), 
            (-(gap/2 + 0.5), -b)
        ]

        # Combine and generate all pillars
        for px, pz in corners + gate_posts:
            add_box(ox + px, oy + pill_h/2, oz + pz, pill_w, pill_h, pill_w, self.COLOR_STONE_LIGHT)
            # Add a small cap on each pillar
            add_box(ox + px, oy + pill_h + 0.1, oz + pz, pill_w * 1.2, 0.3, pill_w * 1.2, self.COLOR_STONE_DARK)

        self._finalize_mesh(verts, tris, cols, Vec3(0, 0, 0))

    def _spawn_mobs(self):
        from code.entity.specs import spec_zombie
        from code.entity.entities import TaskMeleeAttack, TaskChaseTarget, TaskWander

        for _ in range(2):
            angle = self.rng.uniform(0, math.pi*2)
            dist  = self.rng.uniform(1.0, self.size*0.30)
            pos   = Vec3(
                self.position.x + math.cos(angle)*dist,
                self.position.y + 1.0,
                self.position.z + math.sin(angle)*dist,
            )
            mob = self.entity_manager.spawn(pos, spec=spec_zombie())
            mob.add_task(TaskMeleeAttack(self.get_player,
                                          attack_range=3.8, cooldown=1.8, damage=20.0,
                                          on_hit=lambda t: self._damage_player(20.0)))
            mob.add_task(TaskChaseTarget(self.get_player,
                                          speed=2.2, trigger_range=28.0))
            mob.add_task(TaskWander(speed=1.2, change_interval=5.0))
            self._alive_mobs.append(mob)