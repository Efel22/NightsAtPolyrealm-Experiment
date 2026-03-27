from ursina import *
import math
import random

from code.entity.player.xp_system import xp_system


class SoulOrb:
    """
    A glowing rotating cube that appears when an enemy dies.
    Floats toward the player when they get close and grants XP on collection.
    Despawns automatically if the player is too far away
    (prevents structure unload kills from littering the world with orbs).
    """

    # -- Tuning constants --------------------------------------------------
    COLLECTION_RADIUS  = 8.5    # distance at which orb starts moving toward player
    COLLECTED_RADIUS   = 0.8    # distance at which orb is actually collected
    MOVE_SPEED         = 8.0    # how fast the orb flies toward the player
    DESPAWN_RADIUS     = 40.0   # despawn if player is further than this
    FLOAT_HEIGHT       = 1.2    # how high above spawn point the orb floats
    FLOAT_SPEED        = 1.8    # speed of the up/down bobbing animation
    FLOAT_AMPLITUDE    = 0.25   # how far up/down the orb bobs
    ROTATE_SPEED       = 120.0  # degrees per second rotation

    def __init__(self, position: Vec3, xp_value: float, get_player_fn):
        self.xp_value   = xp_value
        self.get_player = get_player_fn
        self.dead       = False
        self._lifetime  = 0.0
        self._spawn_pos = Vec3(position.x,
                               position.y + self.FLOAT_HEIGHT,
                               position.z)

        # Make the Orb Appear larger depending on xp_value!
        adjusted_scale = 0.1 + min(0.2, (xp_value / 50))

        # -- Build the soul orb entity --------------------------------------
        self.entity = Entity(
            model    = 'cube',
            scale    = adjusted_scale,
            position = self._spawn_pos,
            unlit    = True,   # ignore lighting, always glows
        )

        # Current hue in the RGB cycle (0.0 – 1.0)
        self._hue = random.uniform(0.0, 1.0)

    # ------------------------------------------------------------------ #

    def update(self, dt: float):
        if self.dead:
            return

        self._lifetime += dt
        player = self.get_player()
        if player is None:
            return

        # -- Despawn if player is too far away -----------------------------
        # This prevents orbs from stacking up when structures unload
        dx   = player.x - self.entity.x
        dz   = player.z - self.entity.z
        dist = math.sqrt(dx*dx + dz*dz)

        if dist > self.DESPAWN_RADIUS:
            self.destroy()
            return

        # -- Rotate constantly ---------------------------------------------
        self.entity.rotation_y += self.ROTATE_SPEED * dt
        self.entity.rotation_x += self.ROTATE_SPEED * 0.6 * dt

        # -- Cycle through RGB spectrum -------------------------------------
        self._hue = (self._hue + dt * 0.8) % 1.0
        self.entity.color = color.hsv(self._hue * 360, 1.0, 1.0, 1.0)

        # -- Bob up and down when idle -------------------------------------
        if dist > self.COLLECTION_RADIUS:
            bob_offset = math.sin(self._lifetime * self.FLOAT_SPEED) * self.FLOAT_AMPLITUDE
            self.entity.y = self._spawn_pos.y + bob_offset

        # -- Fly toward player when they get close -------------------------
        if dist <= self.COLLECTION_RADIUS:
            direction = Vec3(dx, player.y + 1.0 - self.entity.y, dz)
            if direction.length() > 0:
                self.entity.position += direction.normalized() * self.MOVE_SPEED * dt

        # -- Collect when close enough -------------------------------------
        if dist <= self.COLLECTED_RADIUS:
            self._collect()

    def _collect(self):
        """Grant XP and a small heal to the player, then destroy the orb."""
        xp_system.add_xp(self.xp_value)

        # Heal the player for X% of the orb's XP value
        heal_amount = self.xp_value * 0.30 # <- PERCENT
        stamina_amount = self.xp_value * 0.40 # <- PERCENT
        from code.entity.player.playerdata import player_stats
        if player_stats is not None:
            player_stats.health = min(
                player_stats.MAX_HEALTH,
                player_stats.health + heal_amount
            )
            player_stats.stamina = min(
                player_stats.MAX_STAMINA,
                player_stats.stamina + stamina_amount
            )
            print(f"[SoulOrb] Healed {heal_amount:.1f} HP")
            print(f"[SoulOrb] Restores {stamina_amount:.1f} SP")

        print(f"[SoulOrb] Collected! +{self.xp_value} XP  "
              f"({xp_system.player_xp}/{xp_system.player_xp_to_next_level})")

        from code.sound import play_sound
        play_sound("entity/collect_soul")

        self.destroy()



        self.destroy()

    def destroy(self):
        if not self.dead:
            self.dead = True
            destroy(self.entity)