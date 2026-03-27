from ursina import *
import math
import random

# from .specs import *
from code.world.world_settings import CHUNK_SIZE
from code.sound import play_sound


# ============================================================
#  CameraBob
# ============================================================
class CameraBob:
    """
    Bobs the camera up and down while the player is moving.
    Bobs harder and faster when sprinting.
    """
    def __init__(self, player):
        self.player      = player
        self._timer      = 0.0
        self._current_y  = 0.0
        
        # This prevents the "triple-triggering" for the sound
        self._ready_for_footstep = True 

        # Settings
        self._walk_speed = 9.0
        self._walk_amount = 0.06
        self._sprint_speed = 30.0
        self._sprint_amount = 0.33

    def update(self, dt, is_sprinting):
        is_moving = any(held_keys[k] for k in ('w', 's', 'a', 'd'))

        # Ground check
        ground_check = raycast(self.player.position, Vec3(0, -1, 0), distance=1.5, ignore=[self.player])
        is_grounded = ground_check.hit

        if is_moving and is_grounded:
            bob_speed = self._sprint_speed if is_sprinting else self._walk_speed
            bob_amount = self._sprint_amount if is_sprinting else self._walk_amount

            self._timer += dt * bob_speed
            current_sin = math.sin(self._timer)
            target_y = current_sin * bob_amount

            # --- FOOTSTEP LOGIC ---
            # 1. Trigger the sound at the bottom (-0.9 or lower)
            if current_sin < -0.9 and self._ready_for_footstep:
                if is_sprinting:
                    play_sound("entity/walk", volume=0.7)
                else:
                    play_sound("entity/walk", volume=0.5)
                
                # 2. Lock the sound so it can't play again immediately
                self._ready_for_footstep = False

            # 3. Reset the lock once the camera moves back toward the middle/top
            if current_sin > 0.0:
                self._ready_for_footstep = True

        else:
            self._timer = 0.0
            target_y = 0.0
            self._ready_for_footstep = True # Reset when stopping

        self._current_y += (target_y - self._current_y) * min(1.0, dt * 12.0)
        camera.y = self._current_y