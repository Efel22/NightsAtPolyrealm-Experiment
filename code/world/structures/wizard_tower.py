from ursina import *
import math
import random
from code.world.color_settings import hex_to_rgb
from code.world.meshbuilders.shared import darken

from .structure_base import Structure


class WizardTower(Structure):
    """
    A tall dark tower.
    Spawns wizards.
    """

    KILL_CAP         = 6
    RESPAWN_INTERVAL = 10.0
    MAX_ALIVE        = 3

    COLOR_BASALT      = (*hex_to_rgb("#3a4466"), 1)
    COLOR_LIGHT_STONE = (*hex_to_rgb("##3f2832"), 1)
    COLOR_CRYSTAL     = (*hex_to_rgb("#8119c6"), 1)
    COLOR_CRYSTAL_2     = (*hex_to_rgb("#b6377d"), 1)
    COLOR_PLATFORM    = (*hex_to_rgb("#5a6988"), 1)

    def _build(self, position: Vec3, size: float, rng: random.Random):
        verts, tris, cols, add_box = self._make_mesh_builder()

        ox, oz = position.x, position.z
        oy     = position.y              # <- use actual ground height as base

        buried_y = oy - 10.0            # <- offset from ground, not hardcoded -10

        # Hard-coded specs
        T_WIDTH  = 24
        T_HEIGHT = 10
        CORE_W   = 16

        # 1. THE BASALT COLUMN FIELD (Buried)
        for _ in range(2):
            for i in range(20):
                angle = (i / 20) * math.pi * 2
                dist  = rng.uniform(8, 13)
                px    = ox + math.cos(angle) * dist
                pz    = oz + math.sin(angle) * dist

                p_h_visible = (1.0 - (dist / 13)) * T_HEIGHT + rng.uniform(2, 6)
                total_p_h   = p_h_visible + abs(buried_y - oy)   # depth below ground
                p_center_y  = (total_p_h / 2) + buried_y

                color_to_use = self.COLOR_CRYSTAL if rng.random() > 0.5 else self.COLOR_CRYSTAL_2
                add_box(px, p_center_y, pz, rng.uniform(1.5, 3.5), total_p_h, rng.uniform(1.5, 3.5),
                        darken(color_to_use, rng.uniform(0.8, 1.1)))

        # 2. THE MAIN CORE (Buried Platform Base)
        core_h_visible = T_HEIGHT * 0.9
        total_core_h   = core_h_visible + abs(buried_y - oy)
        core_center_y  = (total_core_h / 2) + buried_y

        add_box(ox, core_center_y, oz, CORE_W, total_core_h, CORE_W, self.COLOR_BASALT)

        # 3. CORNER CRYSTALS (Buried Anchors)
        c_offset       = 6.5
        crystal_h_visible = 8.0
        total_c_h      = crystal_h_visible + abs(buried_y - oy)
        c_center_y     = (total_c_h / 2) + buried_y

        for cx, cz in [(-1, -1), (1, -1), (-1, 1), (1, 1)]:
            add_box(ox + (cx * c_offset), c_center_y + 2.0, oz + (cz * c_offset),
                    2.5, total_c_h, 2.5, self.COLOR_CRYSTAL)

        # 4. THE WIZARD PLATFORM (The Top)
        top_y = oy + T_HEIGHT            # <- offset from ground height

        add_box(ox, top_y, oz, CORE_W + 1, 1.0, CORE_W + 1, self.COLOR_PLATFORM)

        # Heavy Stone Teeth (Merlons) around the 16-wide top
        m_size = 2.0
        for mx, mz in [(-7, 0), (7, 0), (0, -7), (0, 7), (-7, -7), (7, 7)]:
            add_box(ox + mx, top_y + 1.2, oz + mz, m_size, 1.5, m_size, self.COLOR_BASALT)

        self._finalize_mesh(verts, tris, cols, Vec3(0, 0, 0))

    def _spawn_mobs(self):
        from code.entity.specs import spec_wizard
        from code.entity.entities import TaskRangedAttack, TaskWander

        pos = Vec3(
            self.position.x + self.rng.uniform(-1.5, 1.5),
            self.position.y + 1.0,
            self.position.z + self.rng.uniform(-1.5, 1.5),
        )
        mob = self.entity_manager.spawn(pos, spec=spec_wizard())
        mob.add_task(TaskRangedAttack(
            self.get_player,
            attack_range     = 22.0,
            cooldown         = 3.0,
            projectile_speed = 24.0,
            projectile_damage= 30.0,
            projectile_color = color.rgba(1.0, 0.25, 0.02, 1),
            projectile_scale = 1.5,
            arc_height       = 0.005,
            on_projectile_spawn= self.entity_manager.register_projectile,
            damages_player      = True,
            get_player_fn       = self.get_player,
            # Wizard fireballs also explode on impact
            on_terrain_hit      = lambda pos: self.entity_manager.spawn_explosion(
                pos, 8.0, color_rgba=color.rgba(0.8, 0.15, 0.80, 1.0), 
                damages_player = True,
            ),
        ))
        mob.add_task(TaskWander(speed=0.5, change_interval=8.0))
        self._alive_mobs.append(mob)