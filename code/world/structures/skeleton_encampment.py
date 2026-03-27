from ursina import *
import math
import random

from .structure_base import Structure
from code.world.color_settings import hex_to_rgb
from code.world.meshbuilders.shared import darken


class SkeletonEncampment(Structure):
    """
    A Pillager-Outpost-style encampment with a watchtower,
    fences, and a fire pit. Spawns skeletons.
    """

    KILL_CAP         = 12
    RESPAWN_INTERVAL = 3.0
    MAX_ALIVE        = 3

    # -- Colors (Hex-to-RGB) ------------------------------------------------
    COLOR_DARK_WOOD  = (*hex_to_rgb("#3a2618"), 1)
    COLOR_LIGHT_WOOD = (*hex_to_rgb("#734d26"), 1)
    COLOR_STONE      = (*hex_to_rgb("#808085"), 1)
    COLOR_DARK_STONE = (*hex_to_rgb("#525257"), 1)
    COLOR_FIRE       = (*hex_to_rgb("#e65a0d"), 1)
    COLOR_EMBER      = (*hex_to_rgb("#cc260d"), 1)

    def _build(self, position: Vec3, size: float, rng: random.Random):
        verts, tris, cols, add_box = self._make_mesh_builder()

        ox, oz = position.x, position.z
        oy     = position.y  # <- use the actual ground height as the base

        # 1. THE WORLD-BOTTOM FOUNDATION
        world_bottom    = -64.0
        foundation_top  = oy + 0.5          # <- offset by ground height
        foundation_h    = abs(world_bottom) + (oy + 0.5)
        foundation_center_y = (world_bottom + foundation_top) / 2

        # Massive stone slab that fills the encampment footprint
        add_box(ox, foundation_center_y, oz, size, foundation_h, size, darken(self.COLOR_DARK_STONE, rng.uniform(0.8,1.1)))

        # 2. SPIKED LOG WALLS
        wall_dist   = size * 0.45
        stake_count = 14
        for i in range(stake_count):
            pos_val = -wall_dist + (i * (wall_dist * 2 / stake_count))

            for side_offset in [-wall_dist, wall_dist]:
                if not (side_offset < 0 and abs(pos_val) < 3.5):
                    h = rng.uniform(4.5, 6.5)
                    add_box(ox + pos_val, foundation_top + (h/2), oz + side_offset,
                            1.4, h, 1.4, darken(self.COLOR_DARK_WOOD, rng.uniform(0.8,1.1)))

                h2 = rng.uniform(4.5, 6.5)
                add_box(ox + side_offset, foundation_top + (h2/2), oz + pos_val,
                        1.4, h2, 1.4, darken(self.COLOR_DARK_WOOD, rng.uniform(0.8,1.1)))

        # 3. OPEN-AIR WATCHTOWER
        tw_ox, tw_oz = ox - wall_dist + 4, oz + wall_dist - 4
        tower_height  = 12.0

        for sx, sz in [(-1.5, -1.5), (1.5, -1.5), (-1.5, 1.5), (1.5, 1.5)]:
            add_box(tw_ox + sx, foundation_top + (tower_height/2), tw_oz + sz,
                    1.0, tower_height, 1.0, self.COLOR_DARK_WOOD)

        add_box(tw_ox, foundation_top + tower_height, tw_oz, 6.0, 0.6, 6.0, self.COLOR_LIGHT_WOOD)

        for rx, rz in [(-2.8, 0), (2.8, 0), (0, -2.8), (0, 2.8)]:
            rw, rd = (0.4, 6.0) if abs(rx) > 2 else (6.0, 0.4)
            add_box(tw_ox + rx, foundation_top + tower_height + 0.8, tw_oz + rz,
                    rw, 1.2, rd, self.COLOR_DARK_WOOD)

        # 4. CENTRAL CAMPFIRE
        fire_y = foundation_top + 0.2
        for ang in range(0, 360, 60):
            rad = math.radians(ang)
            add_box(ox + math.cos(rad)*1.8, fire_y, oz + math.sin(rad)*1.8,
                    0.8, 0.6, 0.8, self.COLOR_STONE)

        add_box(ox, fire_y + 0.3, oz, 1.4, 0.4, 1.4, self.COLOR_EMBER)
        add_box(ox, fire_y + 1.0, oz, 0.8, 1.4, 0.8, self.COLOR_FIRE)

        # 5. LOG PILES
        for _ in range(3):
            lx = ox + rng.uniform(-size*0.3, size*0.3)
            lz = oz + rng.uniform(-size*0.3, size*0.3)
            if math.sqrt((lx-ox)**2 + (lz-oz)**2) < 5.0:
                lx += 6.0

            add_box(lx, foundation_top + 0.4, lz, 3.5, 0.8, 0.8, darken(self.COLOR_LIGHT_WOOD, rng.uniform(0.8,1.1)))
            add_box(lx, foundation_top + 0.4, lz + 1.0, 3.5, 0.8, 0.8, darken(self.COLOR_LIGHT_WOOD, rng.uniform(0.8,1.1)))
            add_box(lx, foundation_top + 1.2, lz + 0.5, 3.5, 0.8, 0.8, darken(self.COLOR_LIGHT_WOOD, rng.uniform(0.8,1.1)))

        self._finalize_mesh(verts, tris, cols, Vec3(0, 0, 0))

    def _spawn_mobs(self):
        from code.entity.specs import spec_skeleton
        from code.entity.entities import TaskMeleeAttack, TaskChaseTarget, TaskWander

        for _ in range(2):
            angle    = self.rng.uniform(0, math.pi*2)
            dist     = self.rng.uniform(1.5, self.size*0.35)
            pos      = Vec3(
                self.position.x + math.cos(angle)*dist,
                self.position.y + 1.0,
                self.position.z + math.sin(angle)*dist,
            )
            mob = self.entity_manager.spawn(pos, spec=spec_skeleton())
            mob.add_task(TaskMeleeAttack(self.get_player,
                                         attack_range=2.5, cooldown=1.2, damage=15.0,
                                         on_hit=lambda t: self._damage_player(15.0)))
            mob.add_task(TaskChaseTarget(self.get_player,
                                          speed=5.0, trigger_range=25.0))
            mob.add_task(TaskWander(speed=2.0))
            self._alive_mobs.append(mob)