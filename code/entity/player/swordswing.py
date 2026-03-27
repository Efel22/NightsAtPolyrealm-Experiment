from ursina import *
import math

from code.entity.specs import *
from ursina.shaders import lit_with_shadows_shader
from code.sound import play_sound


# ============================================================
#  SwordSwinging
# ============================================================
class SwordSwing:
    """
    A sword that appears in front of the player on left click,
    swings forward, damages nearby entities, then disappears.
    Built as a single merged mesh, one draw call.
    """

    def __init__(self, player, entity_manager):
        self.player         = player
        self.entity_manager = entity_manager

        # How often the player can swing (seconds)
        self.cooldown        = 0.25
        self._cooldown_timer = 0.0

        # How long the swing animation lasts
        self.swing_duration = 0.25
        self._swing_timer   = 0.0
        self._swinging      = False

        # Damage and reach
        self.damage = 20.0
        self.reach  = 6.5

        # -- Build sword as a single merged mesh ---------------------------
        sv = []; st = []; sc = []; si = 0

        def add_sword_box(cx, cy, cz, sx, sy, sz, col):
            nonlocal si
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
                    sv.append((cx+fx, cy+fy, cz+fz))
                    sc.append(fc)
                st.append((si, si+1, si+2, si+3))
                si += 4

        # Blade
        add_sword_box(0,      0.30,  0,  0.045, 0.55,  0.045, (0.82, 0.85, 0.90, 1))
        # Blade edge gleam
        add_sword_box(0.018,  0.30,  0,  0.010, 0.52,  0.010, (0.95, 0.97, 1.00, 1))
        # Blade tip
        add_sword_box(0,      0.605, 0,  0.025, 0.07,  0.025, (0.82, 0.85, 0.90, 1))
        # Crossguard
        add_sword_box(0,      0.022, 0,  0.22,  0.045, 0.055, (0.72, 0.55, 0.18, 1))
        # Guard left cap
        add_sword_box(-0.125, 0.022, 0,  0.03,  0.065, 0.065, (0.60, 0.44, 0.12, 1))
        # Guard right cap
        add_sword_box( 0.125, 0.022, 0,  0.03,  0.065, 0.065, (0.60, 0.44, 0.12, 1))
        # Handle
        add_sword_box(0,     -0.105, 0,  0.048, 0.18,  0.048, (0.28, 0.16, 0.08, 1))
        # Handle wrap band (upper)
        add_sword_box(0,     -0.072, 0,  0.055, 0.022, 0.055, (0.45, 0.28, 0.12, 1))
        # Handle wrap band (lower)
        add_sword_box(0,     -0.135, 0,  0.055, 0.022, 0.055, (0.45, 0.28, 0.12, 1))
        # Pommel
        add_sword_box(0,     -0.215, 0,  0.075, 0.055, 0.075, (0.72, 0.55, 0.18, 1))

        # Single entity, one draw call for the whole sword
        self.sword_root = Entity(
            parent      = camera,
            model       = Mesh(vertices=sv, triangles=st, colors=sc, mode='triangle'),
            position    = (0.3, -0.15, 0.5),
            rotation    = (0, 0, -10),
            enabled     = False,
            double_sided= True,
            shader      = lit_with_shadows_shader,
        )

    # ------------------------------------------------------------------ #

    def try_swing(self):
        """Called on left click, starts a swing if cooldown has elapsed."""
        from code.entity.player.playerdata import player_stats
        if self._cooldown_timer > 0 or self._swinging or player_stats.health <= 0:
            return
        # Melee costs 20 stamina, block the swing if not enough
        if not player_stats.use_stamina(15):
            return

        
        self._swinging    = True
        self._swing_timer = 0.0
        self.sword_root.enabled = True
        self._apply_damage()
        
        play_sound("entity/sword_use")

    def _apply_damage(self):
        """Deal damage to all entities within reach in front of the player."""
        player_pos = self.player.position

        forward = Vec3(
            math.sin(math.radians(self.player.rotation_y)),
            0,
            math.cos(math.radians(self.player.rotation_y))
        )

        for entity in self.entity_manager.entities:
            diff = entity.root.position - player_pos
            dist = diff.length()

            if dist > self.reach:
                continue

            diff_flat = Vec3(diff.x, 0, diff.z)
            if diff_flat.length() > 0:
                dot = diff_flat.normalized().dot(forward)
                if dot < 0.2:
                    continue

            # Use take_damage so health system and visual feedback both trigger
            entity.take_damage(self.damage + random.randint(-5,5))

    def update(self, dt):
        # Count down cooldown between swings
        if self._cooldown_timer > 0:
            self._cooldown_timer = max(0.0, self._cooldown_timer - dt)

        if not self._swinging:
            return

        self._swing_timer += dt
        swing_progress = min(1.0, self._swing_timer / self.swing_duration)

        # Animate the swing, arc the sword forward and across
        self.sword_root.rotation = (
            90 * swing_progress,         # sweeps forward (pitch)
            70 * swing_progress,         # arcs inward (yaw)
            -80 + (30 * swing_progress)  # rolls through the swing
        )

        # Swing finished, hide sword, start cooldown, reset rotation
        if self._swing_timer >= self.swing_duration:
            self._swinging           = False
            self._cooldown_timer     = self.cooldown
            self.sword_root.enabled  = False
            self.sword_root.rotation = (0, 0, -10)