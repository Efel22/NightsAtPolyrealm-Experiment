from ursina import *
import math
import random 
from code.entity.player.playerdata import *


class Explosion:
    """
    A growing sphere that deals splash damage to nearby enemies
    then disappears. Used by magic staff fireballs and wizard projectiles.
    """

    # -- Tuning ------------------------------------------------------------
    EXPAND_DURATION = 0.20   # how long the explosion grows
    FADE_DURATION   = 0.25   # how long it fades after reaching full size
    MAX_SCALE       = 10.0   # maximum radius of the explosion sphere

    def __init__(self, position: Vec3, damage: float,
                 entity_manager, color_rgba=None, damages_player=True):
        self.damage            = damage
        self.entity_manager    = entity_manager
        self.dead              = False
        self._timer            = 0.0
        self.damages_player    = damages_player

        print_warning("damages_player: ")
        print_warning(damages_player)

        self._has_dealt_damage = False   # damage is dealt once at peak size

        col = color_rgba or color.rgba(1.0, 0.45, 0.05, 1.0)

        # -- Visual ,unlit glowing sphere that expands then fades ----------
        self.entity = Entity(
            model    = 'sphere',
            color    = col,
            scale    = 0.1,
            position = position,
            unlit    = True,   # always glows regardless of lighting
        )

    # ------------------------------------------------------------------ #

    def update(self, dt: float):
        if self.dead:
            return

        self._timer += dt
        total_duration = self.EXPAND_DURATION + self.FADE_DURATION

        if self._timer <= self.EXPAND_DURATION:
            # -- Expansion phase ,grow from tiny to full size --------------
            grow_progress     = self._timer / self.EXPAND_DURATION
            self.entity.scale = self.MAX_SCALE * grow_progress

            # Color shifts from orange -> red -> dark as it expands
            r = 1.0
            g = max(0.0, 0.45 - grow_progress * 0.45)
            b = 0.0
            self.entity.color = color.rgba(r, g, b, 1.0)

        elif self._timer <= total_duration:
            # -- Fade phase ,shrink alpha to zero -------------------------
            fade_progress     = (self._timer - self.EXPAND_DURATION) / self.FADE_DURATION
            self.entity.color = color.rgba(0.8, 0.2, 0.0, 1.0 - fade_progress)

            # Deal splash damage once at the start of the fade phase
            if not self._has_dealt_damage:
                self._has_dealt_damage = True
                self._deal_splash_damage()

        else:
            # -- Done ,destroy ---------------------------------------------
            self.destroy()

    def _deal_splash_damage(self):
        """Damage all entities within the explosion radius."""
        from code.entity.player.playerdata import player_stats  # <- import at call site
        explosion_pos = self.entity.position
        radius        = self.MAX_SCALE / 2.0 + 1   # world-space radius

        # -- Check player separately ,they're not in entity_manager.entities --
        if self.damages_player and player_stats is not None:
            player = player_stats.player
            dist   = (player.position - explosion_pos).length()
            if dist <= radius:
                falloff        = max(0.0, 1.0 - (dist / radius))
                damage_to_deal = min(45.0, self.damage * falloff) + random.randint(-3, 3)
                # Wizard's explosion ,damage the player
                player_stats.take_damage(damage_to_deal)

        # -- Check enemies ,only when explosion is from the player ------------
        if not self.damages_player:
            for entity in self.entity_manager.entities:
                if entity.root is None or entity.dead:
                    continue

                dist = (entity.root.position - explosion_pos).length()
                if dist > radius:
                    continue

                # Damage falls off with distance, full damage at centre
                falloff        = max(10.0, 1.0 - (dist / radius))

                # Adjusted damage
                damage_to_deal = min(10.0, self.damage * falloff) + random.randint(-3, 3)

                # Player's explosion, damage enemies
                entity.take_damage(damage_to_deal)

    def destroy(self):
        if not self.dead:
            self.dead = True
            destroy(self.entity)