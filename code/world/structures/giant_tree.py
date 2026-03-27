from ursina import *
import math
import random

from .structure_base import Structure
from code.world.color_settings import hex_to_rgb
from code.world.meshbuilders.shared import darken


class GiantTree(Structure):
    """
    An enormous oak tree with thick trunk and wide canopy.
    Beehives hang from the branches. Spawns bees.
    """

    KILL_CAP         = 15
    RESPAWN_INTERVAL = 10.0
    MAX_ALIVE        = 3

    COLOR_BARK_DARK  = (*hex_to_rgb("#382412"), 1)
    COLOR_BARK_LIGHT = (*hex_to_rgb("#593D1F"), 1)
    COLOR_LEAF_DARK  = (*hex_to_rgb("#14471A"), 1)
    COLOR_LEAF_MID   = (*hex_to_rgb("#1A6124"), 1)
    COLOR_LEAF_LIGHT = (*hex_to_rgb("#247A2E"), 1)
    COLOR_HIVE       = (*hex_to_rgb("#EAAD20"), 1)
    COLOR_HIVE_HOLE  = (*hex_to_rgb("#4D330D"), 1)
    COLOR_VINE       = (*hex_to_rgb("#2E7320"), 1)

    def _build(self, position: Vec3, size: float, rng: random.Random):
        verts, tris, cols, add_box = self._make_mesh_builder()
        
        ox, oz = position.x, position.z
        
        # FIXED DIMENSIONS to ensure visibility
        buried_base_y = -10.0  # Start deep underground
        visible_height = 30.0  # Reach high into the air
        trunk_w = 6.0          # Very thick trunk
        
        # 1. THE TRUNK (Pillar from -10 to +30)
        # Center is (Top + Bottom) / 2 = 10.0
        # Total Height is (Top - Bottom) = 40.0
        add_box(ox, 10.0, oz, trunk_w, 40.0, trunk_w, self.COLOR_BARK_DARK)
        
        # 2. THE FLARED BASE (Extra thick at ground level)
        # Pillar from -10 to +4
        add_box(ox, -3.0, oz, trunk_w * 1.6, 14.0, trunk_w * 1.6, self.COLOR_BARK_DARK)

        # 3. MEGA CANOPY (Positioned at the top of the trunk)
        # Starting the canopy layers around Y=20
        canopy_start_y = 22.0
        
        leaf_layers = [
            (25.0, 8.0, 0.0, self.COLOR_LEAF_DARK),  # Massive bottom layer
            (18.0, 6.0, 7.0, self.COLOR_LEAF_MID),   # Middle layer
            (12.0, 5.0, 12.0, self.COLOR_LEAF_LIGHT), # Top point
        ]
        
        for lw, lh, ly_off, lcol in leaf_layers:
            # Position centered on the layer height
            layer_center_y = canopy_start_y + ly_off + (lh / 2)
            add_box(ox, layer_center_y, oz, lw, lh, lw, lcol)

        # 4. OVERSIZED VINES (Hanging from the massive canopy)
        for v in range(20):
            angle = (v / 20) * math.pi * 2
            dist = rng.uniform(trunk_w * 0.8, 12.0)
            vx, vz = ox + math.cos(angle) * dist, oz + math.sin(angle) * dist
            
            v_len = rng.uniform(15.0, 25.0)
            # Hang them from the bottom of the first leaf layer (Y=22)
            add_box(vx, 22.0 - (v_len / 2), vz, 0.4, v_len, 0.4, self.COLOR_VINE)

        # 5. TITANIC BEE NESTS
        # These are now 4.0x6.0 - roughly the size of a small building
        for i in range(3):
            h_angle = (i / 3) * math.pi * 2 + 0.8
            h_dist = 10.0 # Pushed way out from the trunk
            hx, hz = ox + math.cos(h_angle) * h_dist, oz + math.sin(h_angle) * h_dist
            
            hive_w, hive_h = 4.0, 6.0
            # Hanging centered below the canopy
            hy = 18.0 
            
            # Nest Body
            add_box(hx, hy, hz, hive_w, hive_h, hive_w, self.COLOR_HIVE)
            
            # Tapered bottom point
            add_box(hx, hy - (hive_h/2) - 0.5, hz, hive_w * 0.6, 1.5, hive_w * 0.6, self.COLOR_HIVE)
            
            # Massive Entrance Hole
            h_off = hive_w * 0.4
            add_box(hx + (math.cos(h_angle) * h_off), hy - 1.0, hz + (math.sin(h_angle) * h_off), 
                    1.5, 1.5, 1.5, self.COLOR_HIVE_HOLE)

        self._finalize_mesh(verts, tris, cols, Vec3(0, 0, 0))

    def _spawn_mobs(self):
        from code.entity.specs import spec_bee
        from code.entity.entities import TaskMeleeAttack, TaskChaseTarget, TaskWander

        # Increased spawn radius (0.8) to ensure they are around the tree, not inside it
        # Adjusted height (0.6) so they hang around the lower canopy/vines level
        spawn_radius = self.size * 0.8
        spawn_height = self.size * 0.6

        for ang in range(0, 360, 120):
            rad = math.radians(ang)
            pos = Vec3(
                self.position.x + math.cos(rad) * spawn_radius,
                self.position.y + spawn_height,
                self.position.z + math.sin(rad) * spawn_radius,
            )
            
            mob = self.entity_manager.spawn(pos, spec=spec_bee(),
                                            gravity=0.0, max_lifetime=20.0)
            
            mob.add_task(TaskMeleeAttack(self.get_player, attack_range=1.2,
                                          cooldown=0.8, damage=5.0,
                                          on_hit=lambda t: self._damage_player(5.0),
                                          die_on_hit=True))
            
            mob.add_task(TaskChaseTarget(self.get_player, speed=8.0,
                                          trigger_range=60.0, stop_range=1.0,
                                          airborne=True))
            
            mob.add_task(TaskWander(speed=3.0, change_interval=2.0))
            
            self._alive_mobs.append(mob)