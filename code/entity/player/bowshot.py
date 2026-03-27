from ursina import *
import math

from code.entity.projectile import Projectile
from code.sound import play_sound
from ursina.shaders import lit_with_shadows_shader

# ============================================================
#  BowShot
# ============================================================
class BowShot:
    """
    A bow that appears in front of the player on right click,
    fires an arrow projectile, then disappears.
    Built as a single merged mesh, one draw call.
    """

    def __init__(self, player, entity_manager, projectile_registry):
        self.player              = player
        self.entity_manager      = entity_manager
        self.projectile_registry = projectile_registry

        self.cooldown        = 0.5
        self._cooldown_timer = 0.0

        self.show_duration = 0.5
        self._show_timer   = 0.0
        self._showing      = False

        self.arrow_speed  = 28.0
        self.arrow_damage = 10.0

        # -- Build bow as a single merged mesh -----------------------------
        bv = []; bt = []; bc = []; bi = 0

        def add_bow_box(cx, cy, cz, sx, sy, sz, col):
            nonlocal bi
            hx, hy, hz = sx/2, sy/2, sz/2
            r, g, b, a = col
            top_col  = color.rgba(r,        g,        b,        a)
            side_col = color.rgba(r * 0.78, g * 0.78, b * 0.78, a)
            bot_col  = color.rgba(r * 0.48, g * 0.48, b * 0.48, a)
            faces = [
                [(-hx, hy,-hz),(-hx, hy, hz),( hx, hy, hz),( hx, hy,-hz)], top_col,
                [(-hx,-hy,-hz),( hx,-hy,-hz),( hx,-hy, hz),(-hx,-hy, hz)], bot_col,
                [(-hx,-hy, hz),( hx,-hy, hz),( hx, hy, hz),(-hx, hy, hz)], side_col,
                [( hx,-hy,-hz),(-hx,-hy,-hz),(-hx, hy,-hz),( hx, hy,-hz)], side_col,
                [(-hx,-hy,-hz),(-hx,-hy, hz),(-hx, hy, hz),(-hx, hy,-hz)], side_col,
                [( hx,-hy, hz),( hx,-hy,-hz),( hx, hy,-hz),( hx, hy, hz)], side_col,
            ]
            i = 0
            while i < len(faces):
                fv = faces[i]; fc = faces[i+1]; i += 2
                for (fx, fy, fz) in fv:
                    bv.append((cx+fx, cy+fy, cz+fz))
                    bc.append(fc)
                bt.append((bi, bi+1, bi+2, bi+3))
                bi += 4

        wood       = (0.42, 0.28, 0.12, 1)
        wood_light = (0.55, 0.38, 0.18, 1)
        string_col = (0.85, 0.82, 0.72, 1)

        # -- Center grip ---------------------------------------------------
        # The grip sits at x=0, all limb segments grow outward from here
        # keeping x=0 so they butt up against each other with no gap
        add_bow_box(0, 0.00, 0,  0.06, 0.20, 0.05, wood_light)

        # -- Upper limb, each segment starts where the last one ended -----
        # seg Y centre = previous top edge + half of this seg height
        # seg 1: starts at y=0.10 (top of grip), height 0.16 -> centre 0.18
        add_bow_box(0.000, 0.18, 0,  0.058, 0.16, 0.048, wood)
        # seg 2: starts at y=0.26, height 0.16 -> centre 0.34
        add_bow_box(0.008, 0.34, 0,  0.054, 0.16, 0.044, wood)
        # seg 3: starts at y=0.42, height 0.16 -> centre 0.50
        add_bow_box(0.020, 0.50, 0,  0.048, 0.16, 0.038, wood)
        # seg 4: starts at y=0.58, height 0.14 -> centre 0.65
        add_bow_box(0.035, 0.65, 0,  0.038, 0.14, 0.030, wood)
        # tip: starts at y=0.72, height 0.06 -> centre 0.75
        add_bow_box(0.050, 0.75, 0,  0.026, 0.06, 0.022, wood_light)
        # tip notch (string anchor)
        add_bow_box(0.058, 0.785, 0, 0.010, 0.020, 0.010, wood_light)

        # -- Lower limb, exact mirror of upper on Y -----------------------
        add_bow_box(0.000, -0.18, 0,  0.058, 0.16, 0.048, wood)
        add_bow_box(0.008, -0.34, 0,  0.054, 0.16, 0.044, wood)
        add_bow_box(0.020, -0.50, 0,  0.048, 0.16, 0.038, wood)
        add_bow_box(0.035, -0.65, 0,  0.038, 0.14, 0.030, wood)
        add_bow_box(0.050, -0.75, 0,  0.026, 0.06, 0.022, wood_light)
        # tip notch (string anchor)
        add_bow_box(0.058, -0.785, 0, 0.010, 0.020, 0.010, wood_light)

        # -- Bowstring, ONE continuous piece tip to tip -------------------
        # Total height = distance between the two tip notches = 1.57
        # Centre Y = 0, so it spans from -0.785 to +0.785
        # X sits just past the tip notch X (0.058 + half notch width ~0.005 = 0.063)
        add_bow_box(0.063, 0.0, 0,  0.006, 1.57, 0.006, string_col)

        # Store base position for animation reset
        # +x -> right
        # -x -> left
        # +y -> up
        # -y -> down
        # +z -> further (front)
        # -z -> closer to camera
        self._base_pos = (-1.20, -0.30, 2.4)

        # Single entity, one draw call for the whole bow
        self.bow_root = Entity(
            parent      = camera,
            model       = Mesh(vertices=bv, triangles=bt, colors=bc, mode='triangle'),
            position    = self._base_pos, 
            rotation    = (10, 110, 15),             # rotated 90 on Y
            scale       = (7.5, 1.5, 3.5),
            enabled     = False,
            double_sided= True,
            shader=lit_with_shadows_shader,
        )


    # ------------------------------------------------------------------ #

    def try_shoot(self):
        from code.entity.player.playerdata import player_stats
        if self._cooldown_timer > 0 or self._showing or player_stats.health <= 0:
            return
        # Bow costs 30 stamina, block the shot if not enough
        if not player_stats.use_stamina(20):
            return

        self._showing    = True
        self._show_timer = 0.0
        self.bow_root.enabled = True
        self._fire_arrow()
        self._cooldown_timer = self.cooldown

        play_sound("entity/shoot_bow")

    def _fire_arrow(self):

        origin = self.player.position + Vec3(0, 1.6, 0)

        pitch = camera.world_rotation_x
        yaw   = camera.world_rotation_y
        cam_forward = Vec3(
            math.sin(math.radians(yaw))   * math.cos(math.radians(pitch)),
           -math.sin(math.radians(pitch)),
            math.cos(math.radians(yaw))   * math.cos(math.radians(pitch)),
        ).normalized()

        # -- Build arrow as a merged mesh ----------------------------------
        av = []; at = []; ac = []; ai = 0

        def add_arrow_box(cx, cy, cz, sx, sy, sz, col):
            nonlocal ai
            hx, hy, hz = sx/2, sy/2, sz/2
            r, g, b, a = col
            top_col  = color.rgba(r,        g,        b,        a)
            side_col = color.rgba(r * 0.78, g * 0.78, b * 0.78, a)
            bot_col  = color.rgba(r * 0.48, g * 0.48, b * 0.48, a)
            faces = [
                [(-hx, hy,-hz),(-hx, hy, hz),( hx, hy, hz),( hx, hy,-hz)], top_col,
                [(-hx,-hy,-hz),( hx,-hy,-hz),( hx,-hy, hz),(-hx,-hy, hz)], bot_col,
                [(-hx,-hy, hz),( hx,-hy, hz),( hx, hy, hz),(-hx, hy, hz)], side_col,
                [( hx,-hy,-hz),(-hx,-hy,-hz),(-hx, hy,-hz),( hx, hy,-hz)], side_col,
                [(-hx,-hy,-hz),(-hx,-hy, hz),(-hx, hy, hz),(-hx, hy,-hz)], side_col,
                [( hx,-hy, hz),( hx,-hy,-hz),( hx, hy,-hz),( hx, hy, hz)], side_col,
            ]
            i = 0
            while i < len(faces):
                fv = faces[i]; fc = faces[i+1]; i += 2
                for (fx, fy, fz) in fv:
                    av.append((cx+fx, cy+fy, cz+fz))
                    ac.append(fc)
                at.append((ai, ai+1, ai+2, ai+3))
                ai += 4

        # Arrow shaft, long and thin, runs along Z (forward direction)
        add_arrow_box(0, 0, 0,      0.04, 0.04, 0.55,  (0.60, 0.42, 0.18, 1))  # wood shaft
        # Arrowhead, metal tip at the front (+Z)
        add_arrow_box(0, 0, 0.32,   0.06, 0.06, 0.10,  (0.72, 0.74, 0.78, 1))  # steel tip
        # Fletching, two crossed fins at the back (-Z)
        add_arrow_box(0, 0,    -0.24,  0.12, 0.02, 0.10,  (0.75, 0.18, 0.18, 1))  # horizontal fin
        add_arrow_box(0, 0,    -0.24,  0.02, 0.12, 0.10,  (0.75, 0.18, 0.18, 1))  # vertical fin

        # Build the arrow entity from the merged mesh
        arrow_entity = Entity(
            model       = Mesh(vertices=av, triangles=at, colors=ac, mode='triangle'),
            position    = origin,
            double_sided= True,
            scale       = 3,
            shader=lit_with_shadows_shader,
        )

        arrow = Projectile(
            origin        = origin,
            direction     = cam_forward,
            speed         = self.arrow_speed,
            damage        = self.arrow_damage + random.randint(-5,5),
            gravity       = -12.0,
            visual_entity = arrow_entity,   # <- custom arrow mesh
            damages_player  = False,              # player's arrow -> hits enemies
            target          = self.entity_manager, # EntityManager to scan for hits
        )

        self.projectile_registry(arrow)

    def update(self, dt):
        if self._cooldown_timer > 0:
            self._cooldown_timer = max(0.0, self._cooldown_timer - dt)

        if not self._showing:
            return

        self._show_timer += dt
        pull_progress = min(1.0, self._show_timer / self.show_duration)

        # Pull-back animation, bow kicks back slightly when fired
        self.bow_root.position = (
            self._base_pos[0] - 0.2 * pull_progress,
            self._base_pos[1],
            self._base_pos[2] - 0.2 * pull_progress,
        )

        if self._show_timer >= self.show_duration:
            self._showing          = False
            self.bow_root.enabled  = False
            self.bow_root.position = self._base_pos