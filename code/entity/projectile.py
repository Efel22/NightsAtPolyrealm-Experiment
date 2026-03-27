from ursina import *
import math
import random
from code.sound import play_sound
from ursina.shaders import lit_with_shadows_shader

class Projectile:
    """
    A physics-driven projectile fired by an entity or the player.
    
    damages_player : if True  -> checks collision with the player and damages them
                     if False -> checks collision with EntityManager entities and kills them
    """

    def __init__(self, origin: Vec3, direction: Vec3,
                speed: float = 18.0,
                damage: float = 10.0,
                gravity: float = -9.8,
                max_lifetime: float = 4.0,
                visual_entity: Entity = None,
                color_rgba = None,
                scale: float = 0.45,
                damages_player: bool = True,    # True = hurts player, False = hurts enemies
                target = None,                  # player Entity OR EntityManager instance
                on_hit = None,                  # optional callback(target) when something is hit
                on_terrain_hit=None
                ):                 

        self.speed          = speed
        self.damage         = damage
        self.velocity       = direction.normalized() * speed
        self.gravity        = gravity
        self.lifetime       = 0.0
        self.max_lifetime   = max_lifetime
        self.dead           = False
        self.damages_player = damages_player
        self.target         = target      # player or entity_manager
        self.on_hit         = on_hit      # optional callback
        self.on_terrain_hit = on_terrain_hit

        if visual_entity is not None:
            # Caller supplied their own fully-built Entity
            self.entity          = visual_entity
            self.entity.position = origin
        else:
            # Fallback: plain sphere
            col = color_rgba or color.rgba(1.0, 0.4, 0.05, 1)
            self.entity = Entity(
                model    = 'sphere',
                color    = col,
                scale    = scale,
                position = origin,
                shader=lit_with_shadows_shader
            )

    def update(self, dt):
        if self.dead:
            return

        # -- Lifetime expiry -----------------------------------------------
        self.lifetime += dt
        if self.lifetime >= self.max_lifetime:
            self.destroy()
            return

        # -- Physics -------------------------------------------------------
        self.velocity.y      += self.gravity * dt
        self.entity.position += self.velocity * dt

        # Rotate entity to face direction of travel so arrows arc naturally
        if self.velocity.length() > 0.01:
            self.entity.look_at(self.entity.position + self.velocity)

        # -- Terrain collision ---------------------------------------------
        terrain_hit = raycast(
            origin    = self.entity.world_position + Vec3(0, 0.2, 0),
            direction = Vec3(0, -1, 0),
            distance  = 0.4,
            ignore    = [self.entity]
        )

        if terrain_hit.hit:
            play_sound("entity/projectile_hit_ground")
            if self.on_terrain_hit:
                self.on_terrain_hit(self.entity.world_position)
            self.destroy()
            return

        # -- Target collision ----------------------------------------------
        if self.target is not None:
            self._check_target_hit()

    def _check_target_hit(self):
        """Check if the projectile has hit its intended target."""

        if self.damages_player:
            # -- Enemy projectile -> check if we hit the player -------------
            # self.target should be the player Entity
            player = self.target
            dist   = distance(self.entity.world_position, player.position)

            if dist < 1.2:   # hit radius around the player
                if self.on_hit:
                    self.on_hit(player)
                print(f"Player hit for {self.damage} damage!")
                self.destroy()

        else:
            # -- Player projectile -> check if we hit any enemy entity -------
            # self.target should be the EntityManager instance
            entity_manager = self.target
            for entity in entity_manager.entities:
                dist = distance(self.entity.world_position, entity.root.position)
                if dist < 1.5:   # hit radius around an enemy
                    if self.on_hit:
                        self.on_hit(entity)
                    print(f"Enemy hit for {self.damage} damage!")
                    entity.take_damage(self.damage)

                    if self.on_terrain_hit:
                        self.on_terrain_hit(self.entity.world_position)

                    self.destroy()
                    return       # stop after first hit

    def destroy(self):
        if not self.dead:
            self.dead = True
            destroy(self.entity)