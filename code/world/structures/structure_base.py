from ursina import *
import math
import random

from code.world.meshbuilders.shared import darken
from ursina.shaders import lit_with_shadows_shader
from code.world.world_settings import NEAR_IMPOSTOR_RADIUS, CHUNK_SIZE


class Structure:
    """
    Base class for all world structures.
    Each structure owns:
      - A merged visual mesh (one draw call)
      - An invisible collider so the player can walk on/in it
      - A mob spawner that respawns mobs if they are all killed
      - An inactive state once enough total mobs have been killed
    """

    # -- Override these per subclass ---------------------------------------
    KILL_CAP         = 10    # total mob kills before structure stops spawning forever
    RESPAWN_INTERVAL = 15.0  # seconds between each mob respawn attempt
    MAX_ALIVE        = 4     # max mobs from this structure alive at once

    def __init__(self, position: Vec3, size: float, rng: random.Random,
                 entity_manager, get_player_fn):
        self.position       = position   # world position of the structure centre
        self.size           = size       # footprint size in world units
        self.rng            = rng        # deterministic RNG for this chunk slot
        self.entity_manager = entity_manager
        self.get_player     = get_player_fn

        self.dead           = False      # set True -> StructureManager removes it

        # Total mobs killed at this structure across all respawn waves
        self._total_kills   = 0

        # Once True, structure never spawns mobs again (until chunk reloads)
        self._inactive      = False

        # Start timer at full interval so first spawn fires immediately
        self._respawn_timer = self.RESPAWN_INTERVAL

        # Mobs currently alive that belong to this structure
        self._alive_mobs: list = []

        # Visual and collider entities, created in _finalize_mesh
        self._visual_entity   = None
        self._collider_entity = None

        # Build geometry, implemented by each subclass
        self._build(position, size, rng)

    # ------------------------------------------------------------------ #
    #  Subclass interface, must be overridden                             #
    # ------------------------------------------------------------------ #

    def _build(self, position: Vec3, size: float, rng: random.Random):
        """Build the visual mesh and collider for this structure."""
        raise NotImplementedError

    def _spawn_mobs(self):
        """Spawn the mob type specific to this structure."""
        raise NotImplementedError

    # ------------------------------------------------------------------ #
    #  Shared mesh builder                                                 #
    # ------------------------------------------------------------------ #

    def _make_mesh_builder(self):
        """
        Returns (verts, tris, cols, add_box) so subclasses can
        bake all geometry into a single merged mesh, one draw call.
        """
        verts = []; tris = []; cols = []; idx = [0]

        def add_box(cx, cy, cz, sx, sy, sz, col):
            """Add a shaded box to the mesh at world position (cx, cy, cz)."""
            hx, hy, hz = sx/2, sy/2, sz/2
            r, g, b, a = col

            # Top face is brightest, sides are dimmed, bottom is darkest
            top_col  = color.rgba(r,        g,        b,        a)
            side_col = color.rgba(r , g , b , a)
            bot_col  = color.rgba(r , g , b , a)

            faces = [
                [(-hx, hy,-hz),(-hx, hy, hz),( hx, hy, hz),( hx, hy,-hz)], darken(top_col,1.2),   # top
                [(-hx,-hy,-hz),( hx,-hy,-hz),( hx,-hy, hz),(-hx,-hy, hz)], darken(bot_col,0.50),   # bottom
                [(-hx,-hy, hz),( hx,-hy, hz),( hx, hy, hz),(-hx, hy, hz)], darken(side_col,0.90),  # south
                [( hx,-hy,-hz),(-hx,-hy,-hz),(-hx, hy,-hz),( hx, hy,-hz)], side_col,  # north
                [(-hx,-hy,-hz),(-hx,-hy, hz),(-hx, hy, hz),(-hx, hy,-hz)], darken(side_col,0.85),  # west
                [( hx,-hy, hz),( hx,-hy,-hz),( hx, hy,-hz),( hx, hy, hz)], darken(side_col,0.87),  # east
            ]

            i = 0
            while i < len(faces):
                face_verts = faces[i]
                face_col   = faces[i + 1]
                i += 2
                for (fx, fy, fz) in face_verts:
                    verts.append((cx+fx, cy+fy, cz+fz))
                    cols.append(face_col)
                tris.append((idx[0], idx[0]+1, idx[0]+2, idx[0]+3))
                idx[0] += 4

        return verts, tris, cols, add_box

    def _finalize_mesh(self, verts, tris, cols, position: Vec3):
        """
        Bake the mesh arrays into:
          - A visible rendered Entity (no collision)
          - An invisible Entity with a mesh collider (player walks on it)
        Both start hidden, set_visible() controls whether they show.
        """
        self._visual_entity = Entity(
            model       = Mesh(vertices=verts, triangles=tris,
                               colors=cols, mode='triangle'),
            position    = position,
            double_sided= True,
            visible     = False,   # hidden until player is close enough
            shader=lit_with_shadows_shader
        )

        # Collider is always invisible, it just gives the structure solid geometry
        self._collider_entity = Entity(
            model    = Mesh(vertices=verts, triangles=tris,
                            colors=cols, mode='triangle'),
            position = position,
            collider = 'mesh',
            visible  = False,
            shader=lit_with_shadows_shader
        )

    def set_visible(self, is_visible: bool):
        """
        Show or hide the structure visual mesh.
        The collider stays active regardless so the player
        doesn't fall through a hidden structure.
        """
        if self._visual_entity:
            self._visual_entity.visible = is_visible

    # ------------------------------------------------------------------ #
    #  Update                                                              #
    # ------------------------------------------------------------------ #

    def update(self, dt: float):
        if self.dead:
            return

        # -- Distance gate, skip all mob logic if player is too far away --
        # This prevents lag from structures outside the visible radius
        # still trying to spawn and track mobs every frame
        player = self.get_player()
        if player is not None:
            dx = player.x - self.position.x
            dz = player.z - self.position.z
            distance_sq_to_player   = dx*dx + dz*dz
            mob_activation_radius_sq = (NEAR_IMPOSTOR_RADIUS * CHUNK_SIZE) ** 2

            if distance_sq_to_player > mob_activation_radius_sq:
                # Player is too far, freeze all mob logic until they return
                return

        # -- Kill tracking -------------------------------------------------
        # Compare alive mob count before and after purging dead ones
        mobs_alive_before = len(self._alive_mobs)
        self._alive_mobs  = [
            mob for mob in self._alive_mobs
            if not mob.dead and mob in self.entity_manager.entities
        ]
        mobs_killed_this_frame = mobs_alive_before - len(self._alive_mobs)

        if mobs_killed_this_frame > 0:
            self._total_kills += mobs_killed_this_frame
            print(f"[{self.__class__.__name__}] "
                  f"Kills: {self._total_kills}/{self.KILL_CAP}")

        # -- Kill cap check, go permanently inactive if cap is reached ----
        if self._total_kills >= self.KILL_CAP and not self._inactive:
            self._inactive = True
            print(f"[{self.__class__.__name__}] Kill cap reached, now inactive.")

        # Inactive structures do nothing further
        if self._inactive:
            return

        # -- Mob respawn ---------------------------------------------------
        # Only respawn if we have room for more mobs
        self._respawn_timer += dt
        if (self._respawn_timer >= self.RESPAWN_INTERVAL and
                len(self._alive_mobs) < self.MAX_ALIVE):
            self._respawn_timer = 0.0
            self._spawn_mobs()

    # ------------------------------------------------------------------ #
    #  Player Damage                                                       #
    # ------------------------------------------------------------------ #

    def _damage_player(self, amount: float):
        """Deal damage to the player via player_stats."""
        from code.entity.player.playerdata import player_stats
        if player_stats is not None:
            player_stats.take_damage(amount)

    # ------------------------------------------------------------------ #
    #  Cleanup                                                             #
    # ------------------------------------------------------------------ #

    def destroy(self):
        mobs_to_kill = list(self._alive_mobs)
        self._alive_mobs.clear()

        for mob in mobs_to_kill:
            if not mob.dead and mob.root is not None:  # <- guard here
                mob.dead = True
                mob.destroy()

        if self._visual_entity:
            destroy(self._visual_entity)
            self._visual_entity = None

        if self._collider_entity:
            destroy(self._collider_entity)
            self._collider_entity = None

        self.dead = True