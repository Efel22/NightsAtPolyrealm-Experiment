from ursina import *
import math
import random

from code.entity.projectile import Projectile
from code.sound import play_sound
from ursina.shaders import lit_with_shadows_shader
from code.world.color_settings import hex_to_rgb
from code.world.meshbuilders.shared import darken


# ============================================================
#  WEAPON BASE CLASSES
# ============================================================

class MeleeWeapon:
    """Base class for all melee weapons."""

    name           = "Unknown"
    damage_min     = 10
    damage_max     = 20
    reach          = 5.0
    stamina_cost   = 15
    cooldown       = 0.25
    swing_duration = 0.25

    def __init__(self, player, entity_manager):
        self.player         = player
        self.entity_manager = entity_manager
        self._cooldown_timer = 0.0
        self._swing_timer    = 0.0
        self._swinging       = False
        self.weapon_entity   = None   # built by subclass
        self._air_time       = 0
        self._build()

    def _build(self):
        """Override, build the weapon mesh."""
        pass

    def try_swing(self):
        """Attempt a swing, checks cooldown and stamina."""
        from code.entity.player.playerdata import player_stats
        if self._cooldown_timer > 0 or self._swinging or player_stats.health <= 0:
            return
        if not player_stats.use_stamina(self.stamina_cost):
            return
        self._swinging    = True
        self._swing_timer = 0.0
        if self.weapon_entity:
            self.weapon_entity.enabled = True
        self._apply_damage()
        self._play_swing_sound()

    def _play_swing_sound(self):
        play_sound("entity/sword_use")

    def _apply_damage(self):
        """Deal damage to enemies in range and in front of the player."""
        player_pos = self.player.position
        forward = Vec3(
            math.sin(math.radians(self.player.rotation_y)),
            0,
            math.cos(math.radians(self.player.rotation_y))
        )
        for entity in self.entity_manager.entities:
            if entity.root is None:
                continue
            diff = entity.root.position - player_pos
            dist = diff.length()
            if dist > self.reach:
                continue
            diff_flat = Vec3(diff.x, 0, diff.z)
            if diff_flat.length() > 0:
                dot = diff_flat.normalized().dot(forward)
                if dot < 0.2:
                    continue
            entity.take_damage(self._roll_damage())

    def _roll_damage(self) -> float:
        """Roll a random damage value between min and max."""
        return random.randint(self.damage_min, self.damage_max)

    def update(self, dt):
        if self.player.grounded:
            self._air_time = 0
        else:
            self._air_time += dt

        if self._cooldown_timer > 0:
            self._cooldown_timer = max(0.0, self._cooldown_timer - dt)
        if not self._swinging:
            return
        self._swing_timer += dt
        swing_progress = min(1.0, self._swing_timer / self.swing_duration)
        self._animate_swing(swing_progress)
        if self._swing_timer >= self.swing_duration:
            self._swinging = False
            self._cooldown_timer = self.cooldown
            if self.weapon_entity:
                self.weapon_entity.enabled  = False
                self.weapon_entity.rotation = (0, 0, -10)

    def _animate_swing(self, progress: float):
        """Override to customize swing animation."""
        if self.weapon_entity:
            self.weapon_entity.rotation = (
                90 * progress,
                70 * progress,
                -80 + (30 * progress)
            )

    def destroy(self):
        if self.weapon_entity:
            destroy(self.weapon_entity)
            self.weapon_entity = None


class RangedWeapon:
    """Base class for all ranged weapons."""

    name           = "Unknown"
    projectile_speed  = 28.0
    projectile_damage = 10.0
    stamina_cost      = 20
    cooldown          = 0.5
    show_duration     = 0.5
    gravity           = -12.0

    def __init__(self, player, entity_manager, projectile_registry):
        self.player              = player
        self.entity_manager      = entity_manager
        self.projectile_registry = projectile_registry
        self._cooldown_timer     = 0.0
        self._show_timer         = 0.0
        self._showing            = False
        self.weapon_entity       = None
        self._base_pos           = (0, 0, 0)
        self._build()

    def _build(self):
        """Override, build the weapon mesh."""
        pass

    def try_shoot(self):
        from code.entity.player.playerdata import player_stats
        if self._cooldown_timer > 0 or self._showing or player_stats.health <= 0:
            return
        if not player_stats.use_stamina(self.stamina_cost):
            return
        self._showing    = True
        self._show_timer = 0.0
        if self.weapon_entity:
            self.weapon_entity.enabled = True
        self._fire()
        self._cooldown_timer = self.cooldown
        self._play_fire_sound()

    def _play_fire_sound(self):
        play_sound("entity/shoot_bow")

    def _get_fire_direction(self) -> Vec3:
        """Returns the direction the camera is pointing."""
        pitch = camera.world_rotation_x
        yaw   = camera.world_rotation_y
        return Vec3(
            math.sin(math.radians(yaw))   * math.cos(math.radians(pitch)),
           -math.sin(math.radians(pitch)),
            math.cos(math.radians(yaw))   * math.cos(math.radians(pitch)),
        ).normalized()

    def _fire(self):
        """Override, spawn the projectile."""
        pass

    def _make_arrow_entity(self, origin: Vec3) -> Entity:
        """Builds the standard arrow mesh entity."""
        av = []; at = []; ac = []; ai = 0

        def add_box(cx, cy, cz, sx, sy, sz, col):
            nonlocal ai
            hx, hy, hz = sx/2, sy/2, sz/2
            r, g, b, a = col
            tc = color.rgba(r, g, b, a)
            sc = color.rgba(r*.78, g*.78, b*.78, a)
            bc = color.rgba(r*.48, g*.48, b*.48, a)
            faces = [
                [(-hx,hy,-hz),(-hx,hy,hz),(hx,hy,hz),(hx,hy,-hz)], tc,
                [(-hx,-hy,-hz),(hx,-hy,-hz),(hx,-hy,hz),(-hx,-hy,hz)], bc,
                [(-hx,-hy,hz),(hx,-hy,hz),(hx,hy,hz),(-hx,hy,hz)], sc,
                [(hx,-hy,-hz),(-hx,-hy,-hz),(-hx,hy,-hz),(hx,hy,-hz)], sc,
                [(-hx,-hy,-hz),(-hx,-hy,hz),(-hx,hy,hz),(-hx,hy,-hz)], sc,
                [(hx,-hy,hz),(hx,-hy,-hz),(hx,hy,-hz),(hx,hy,hz)], sc,
            ]
            i = 0
            while i < len(faces):
                fv = faces[i]; fc = faces[i+1]; i += 2
                for (fx, fy, fz) in fv:
                    av.append((cx+fx, cy+fy, cz+fz))
                    ac.append(fc)
                at.append((ai, ai+1, ai+2, ai+3))
                ai += 4

        add_box(0, 0, 0,     0.04, 0.04, 0.55, (0.60, 0.42, 0.18, 1))
        add_box(0, 0, 0.32,  0.06, 0.06, 0.10, (0.72, 0.74, 0.78, 1))
        add_box(0, 0, -0.24, 0.12, 0.02, 0.10, (0.75, 0.18, 0.18, 1))
        add_box(0, 0, -0.24, 0.02, 0.12, 0.10, (0.75, 0.18, 0.18, 1))

        return Entity(
            model        = Mesh(vertices=av, triangles=at, colors=ac, mode='triangle'),
            position     = origin,
            double_sided = True,
            scale        = 3,
            shader       = lit_with_shadows_shader,
        )

    def update(self, dt):
        if self._cooldown_timer > 0:
            self._cooldown_timer = max(0.0, self._cooldown_timer - dt)
        if not self._showing:
            return
        self._show_timer += dt
        pull = min(1.0, self._show_timer / self.show_duration)
        if self.weapon_entity:
            self.weapon_entity.position = (
                self._base_pos[0] - 0.2 * pull,
                self._base_pos[1],
                self._base_pos[2] - 0.2 * pull,
            )
        if self._show_timer >= self.show_duration:
            self._showing = False
            if self.weapon_entity:
                self.weapon_entity.enabled  = False
                self.weapon_entity.position = self._base_pos

    def destroy(self):
        if self.weapon_entity:
            destroy(self.weapon_entity)
            self.weapon_entity = None


# ============================================================
#  MELEE WEAPONS
# ============================================================

def _build_merged_mesh(boxes, camera_parent=True):
    """Helper, bakes a list of (cx,cy,cz,sx,sy,sz,col) into one Entity."""
    sv = []; st = []; sc = []; si = 0

    def add_box(cx, cy, cz, sx, sy, sz, col):
        nonlocal si
        hx, hy, hz = sx/2, sy/2, sz/2
        r, g, b, a = col
        tc = color.rgba(r, g, b, a)
        sdc = color.rgba(r*.78, g*.78, b*.78, a)
        bc = color.rgba(r*.48, g*.48, b*.48, a)
        faces = [
            [(-hx,hy,-hz),(-hx,hy,hz),(hx,hy,hz),(hx,hy,-hz)], tc,
            [(-hx,-hy,-hz),(hx,-hy,-hz),(hx,-hy,hz),(-hx,-hy,hz)], bc,
            [(-hx,-hy,hz),(hx,-hy,hz),(hx,hy,hz),(-hx,hy,hz)], sdc,
            [(hx,-hy,-hz),(-hx,-hy,-hz),(-hx,hy,-hz),(hx,hy,-hz)], sdc,
            [(-hx,-hy,-hz),(-hx,-hy,hz),(-hx,hy,hz),(-hx,hy,-hz)], sdc,
            [(hx,-hy,hz),(hx,-hy,-hz),(hx,hy,-hz),(hx,hy,hz)], sdc,
        ]
        i = 0
        while i < len(faces):
            fv = faces[i]; fc = faces[i+1]; i += 2
            for (fx, fy, fz) in fv:
                sv.append((cx+fx, cy+fy, cz+fz))
                sc.append(fc)
            st.append((si, si+1, si+2, si+3))
            si += 4

    for box in boxes:
        add_box(*box)

    return Mesh(vertices=sv, triangles=st, colors=sc, mode='triangle')


# -- Sword (default) -------------------------------------------------------
class Sword(MeleeWeapon):
    name         = "Sword"
    damage_min   = 15
    damage_max   = 25
    reach        = 6.5
    stamina_cost = 15
    cooldown     = 0.25

    def _build(self):
        mesh = _build_merged_mesh([
            (0,      0.30,  0,  0.045, 0.55,  0.045, (0.82, 0.85, 0.90, 1)),
            (0.018,  0.30,  0,  0.010, 0.52,  0.010, (0.95, 0.97, 1.00, 1)),
            (0,      0.605, 0,  0.025, 0.07,  0.025, (0.82, 0.85, 0.90, 1)),
            (0,      0.022, 0,  0.22,  0.045, 0.055, (0.72, 0.55, 0.18, 1)),
            (-0.125, 0.022, 0,  0.03,  0.065, 0.065, (0.60, 0.44, 0.12, 1)),
            ( 0.125, 0.022, 0,  0.03,  0.065, 0.065, (0.60, 0.44, 0.12, 1)),
            (0,     -0.105, 0,  0.048, 0.18,  0.048, (0.28, 0.16, 0.08, 1)),
            (0,     -0.072, 0,  0.055, 0.022, 0.055, (0.45, 0.28, 0.12, 1)),
            (0,     -0.135, 0,  0.055, 0.022, 0.055, (0.45, 0.28, 0.12, 1)),
            (0,     -0.215, 0,  0.075, 0.055, 0.075, (0.72, 0.55, 0.18, 1)),
        ])
        self.weapon_entity = Entity(
            parent=camera, model=mesh,
            position=(0.3, -0.15, 0.5), rotation=(0, 0, -10),
            enabled=False, double_sided=True,
            shader=lit_with_shadows_shader,
        )


# -- Spear -----------------------------------------------------------------
class Spear(MeleeWeapon):
    name         = "Spear"
    damage_min   = 10
    damage_max   = 20
    reach        = 10.0   # longer range than sword
    stamina_cost = 18
    cooldown     = 0.4

    def _build(self):
        mesh = _build_merged_mesh([
            # Long thin shaft
            (0, 0.30, 0,  0.03, 0.90, 0.03, (0.45, 0.28, 0.12, 1)),
            # Metal tip
            (0, 0.80, 0,  0.04, 0.20, 0.04, (0.72, 0.74, 0.78, 1)),
            # Crossguard
            (0, 0.05, 0,  0.18, 0.03, 0.03, (0.55, 0.42, 0.15, 1)),
            # Handle
            (0, -0.15, 0, 0.04, 0.35, 0.04, (0.28, 0.16, 0.08, 1)),
            # Pommel
            (0, -0.35, 0, 0.06, 0.06, 0.06, (0.60, 0.44, 0.12, 1)),
        ])
        self.weapon_entity = Entity(
            parent=camera, model=mesh,
            position=(0.3, -0.15, 0.5), rotation=(0, 0, -10),
            enabled=False, double_sided=True,
            shader=lit_with_shadows_shader,
        )


# -- Mace ------------------------------------------------------------------
class Mace(MeleeWeapon):
    name         = "Mace"
    damage_min   = 25
    damage_max   = 35
    reach        = 5.5
    stamina_cost = 25
    cooldown     = 0.5

    def _build(self):
        mesh = _build_merged_mesh([
            # Handle
            (0,  0.10, 0,  0.045, 0.55, 0.045, (0.28, 0.16, 0.08, 1)),
            # Head, heavy block
            (0,  0.50, 0,  0.18,  0.18, 0.18,  (0.45, 0.45, 0.48, 1)),
            # Spikes on the head
            (0,      0.62, 0,  0.04, 0.06, 0.04, (0.60, 0.60, 0.65, 1)),
            (0.09,   0.55, 0,  0.06, 0.04, 0.04, (0.60, 0.60, 0.65, 1)),
            (-0.09,  0.55, 0,  0.06, 0.04, 0.04, (0.60, 0.60, 0.65, 1)),
            (0,  0.55,  0.09, 0.04, 0.04, 0.06, (0.60, 0.60, 0.65, 1)),
            (0,  0.55, -0.09, 0.04, 0.04, 0.06, (0.60, 0.60, 0.65, 1)),
            # Pommel
            (0, -0.22, 0,  0.07, 0.06, 0.07, (0.55, 0.42, 0.15, 1)),
        ])
        self.weapon_entity = Entity(
            parent=camera, model=mesh,
            position=(0.3, -0.15, 0.5), rotation=(0, 0, -10),
            enabled=False, double_sided=True,
            shader=lit_with_shadows_shader,
        )

    def _roll_damage(self) -> float:
        """Mace deals more damage the longer the player has been airborne."""
        from code.entity.player.playerdata import player
        
        airborne_bonus = 0
        if not player.grounded:
            # Use air time tracked by the mace itself
            airborne_bonus = min(40, self._air_time * 12)

        return random.randint(self.damage_min, self.damage_max) + airborne_bonus

    def update(self, dt):
        # THIS ISNT WORKING FOR SOME REASON, using the MeleeWeapon.update() to get airtime instead
        # Track how long the player has been in the air
        # if not self.player.grounded:
        #     self._air_time += dt
        # else:
        #     self._air_time = 0.0   # reset when they land
        super().update(dt)


# -- Knife -----------------------------------------------------------------
class Knife(MeleeWeapon):
    name         = "Knife"
    damage_min   = 10
    damage_max   = 18
    reach        = 6.0   # shorter range
    stamina_cost = 8     # cheaper
    cooldown     = 0.15  # faster

    def _build(self):
        mesh = _build_merged_mesh([
            # Short thin blade
            (0,  0.20, 0,  0.025, 0.32, 0.025, (0.82, 0.85, 0.90, 1)),
            # Blade gleam
            (0.01, 0.20, 0, 0.008, 0.30, 0.008, (0.95, 0.97, 1.00, 1)),
            # Small guard
            (0,  0.02, 0,  0.10, 0.025, 0.035, (0.55, 0.42, 0.15, 1)),
            # Handle
            (0, -0.09, 0,  0.035, 0.14, 0.035, (0.22, 0.12, 0.06, 1)),
            # Pommel
            (0, -0.17, 0,  0.045, 0.04, 0.045, (0.55, 0.42, 0.15, 1)),
        ])
        self.weapon_entity = Entity(
            parent=camera, model=mesh,
            position=(0.3, -0.15, 0.5), rotation=(0, 0, -10),
            enabled=False, double_sided=True,
            shader=lit_with_shadows_shader,
        )


# ============================================================
#  RANGED WEAPONS
# ============================================================

# -- Bow (default) ---------------------------------------------------------
class Bow(RangedWeapon):
    name              = "Bow"
    projectile_speed  = 28.0
    projectile_damage = 12.0
    stamina_cost      = 20
    cooldown          = 0.5

    def _build(self):
        # (reuse the bow mesh from bowshot.py, same boxes)
        bv = []; bt = []; bc = []; bi = 0

        def add_bow_box(cx, cy, cz, sx, sy, sz, col):
            nonlocal bi
            hx, hy, hz = sx/2, sy/2, sz/2
            r, g, b, a = col
            tc  = color.rgba(r, g, b, a)
            sdc = color.rgba(r*.78, g*.78, b*.78, a)
            boc = color.rgba(r*.48, g*.48, b*.48, a)
            faces = [
                [(-hx,hy,-hz),(-hx,hy,hz),(hx,hy,hz),(hx,hy,-hz)], tc,
                [(-hx,-hy,-hz),(hx,-hy,-hz),(hx,-hy,hz),(-hx,-hy,hz)], boc,
                [(-hx,-hy,hz),(hx,-hy,hz),(hx,hy,hz),(-hx,hy,hz)], sdc,
                [(hx,-hy,-hz),(-hx,-hy,-hz),(-hx,hy,-hz),(hx,hy,-hz)], sdc,
                [(-hx,-hy,-hz),(-hx,-hy,hz),(-hx,hy,hz),(-hx,hy,-hz)], sdc,
                [(hx,-hy,hz),(hx,-hy,-hz),(hx,hy,-hz),(hx,hy,hz)], sdc,
            ]
            i = 0
            while i < len(faces):
                fv = faces[i]; fc = faces[i+1]; i += 2
                for (fx, fy, fz) in fv:
                    bv.append((cx+fx, cy+fy, cz+fz))
                    bc.append(fc)
                bt.append((bi, bi+1, bi+2, bi+3))
                bi += 4

        wood = (0.42, 0.28, 0.12, 1); wl = (0.55, 0.38, 0.18, 1); st = (0.85, 0.82, 0.72, 1)
        add_bow_box(0, 0.00, 0,  0.06, 0.20, 0.05, wl)
        for y, xo, sw, sh, sd in [(0.18,0.000,0.058,0.16,0.048),(0.34,0.008,0.054,0.16,0.044),
                                    (0.50,0.020,0.048,0.16,0.038),(0.65,0.035,0.038,0.14,0.030),
                                    (0.75,0.050,0.026,0.06,0.022)]:
            add_bow_box(xo, y, 0, sw, sh, sd, wood)
        add_bow_box(0.058, 0.785, 0, 0.010, 0.020, 0.010, wl)
        for y, xo, sw, sh, sd in [(-0.18,0.000,0.058,0.16,0.048),(-0.34,0.008,0.054,0.16,0.044),
                                    (-0.50,0.020,0.048,0.16,0.038),(-0.65,0.035,0.038,0.14,0.030),
                                    (-0.75,0.050,0.026,0.06,0.022)]:
            add_bow_box(xo, y, 0, sw, sh, sd, wood)
        add_bow_box(0.058, -0.785, 0, 0.010, 0.020, 0.010, wl)
        add_bow_box(0.063, 0.0, 0, 0.006, 1.57, 0.006, st)

        self._base_pos = (-1.20, -0.30, 2.4)
        self.weapon_entity = Entity(
            parent=camera, model=Mesh(vertices=bv, triangles=bt, colors=bc, mode='triangle'),
            position=self._base_pos, rotation=(10, 110, 15),
            scale=(7.5, 1.5, 3.5), enabled=False, double_sided=True,
            shader=lit_with_shadows_shader,
        )

    def _fire(self):
        origin    = self.player.position + Vec3(0, 1.6, 0)
        direction = self._get_fire_direction()
        arrow     = self._make_arrow_entity(origin)
        proj = Projectile(
            origin=origin, direction=direction,
            speed=self.projectile_speed,
            damage=self.projectile_damage + random.randint(-3, 3),
            gravity=-12.0, visual_entity=arrow,
            damages_player=False, target=self.entity_manager,
        )
        self.projectile_registry(proj)


# -- Crossbow --------------------------------------------------------------
class Crossbow(RangedWeapon):
    name              = "Crossbow"
    projectile_speed  = 45.0   # much faster bolt
    projectile_damage = 40.0   # hits harder
    stamina_cost      = 35     # costs more stamina
    cooldown          = 1.2    # slower to reload

    def _build(self):
        # Hex Color Palette - Red, Brown, Dark Grays
        COLOR_IRON    = hex_to_rgb("#2e2e2e") # Dark Gray
        COLOR_WOOD    = hex_to_rgb("#4a2e1d") # Rich Brown
        COLOR_RED     = hex_to_rgb("#a80000") # Blood Red
        COLOR_STEEL   = hex_to_rgb("#5c5c5c") # Lighter Gray

        mesh = _build_merged_mesh([
            # 1. THE MAIN STOCK (Aligning along Z for "forward")
            # x, y, z, width, height, depth
            (0, 0, 0, 0.1, 0.1, 0.8, (*COLOR_WOOD, 1)),
            
            # 2. THE BOW LIMBS (Crossing the front of the stock)
            # Positioned at the front (z=0.35)
            (0, 0, 0.35, 0.6, 0.08, 0.1, (*COLOR_IRON, 1)),
            
            # 3. THE STRING (Red cord)
            # Positioned slightly behind the limbs
            (0, 0.04, 0.1, 0.58, 0.02, 0.02, (*COLOR_RED, 1)),
            
            # 4. HANDLE / GRIP
            # Angled down at the back (z=-0.25)
            (0, -0.15, -0.25, 0.1, 0.3, 0.1, (*COLOR_WOOD, 1)),
            
            # 5. SIDE REINFORCEMENTS
            (0.06, 0, 0, 0.02, 0.12, 0.4, (*COLOR_STEEL, 1)),
            (-0.06, 0, 0, 0.02, 0.12, 0.4, (*COLOR_STEEL, 1)),

            # 6. TRIGGER
            (0, -0.08, -0.1, 0.04, 0.08, 0.08, (*COLOR_RED, 1)),
        ])

        # Positioned for a right-handed FPS view
        # x: right/left, y: up/down, z: forward/back
        self._base_pos = (0.6, -0.5, 1.2) 
        
        self.weapon_entity = Entity(
            parent=camera, 
            model=mesh,
            position=self._base_pos, 
            rotation=(0, 0, 0), # 0,0,0 should now point it forward
            scale=(1, 1, 1),      
            enabled=False, 
            double_sided=True,
            shader=lit_with_shadows_shader,
        )

    def _fire(self):
        origin    = self.player.position + Vec3(0, 1.6, 0)
        direction = self._get_fire_direction()
        bolt      = self._make_arrow_entity(origin)
        proj = Projectile(
            origin=origin, direction=direction,
            speed=self.projectile_speed,
            damage=self.projectile_damage + random.randint(-2, 2),
            gravity=-6.0,   # flatter trajectory than arrow
            visual_entity=bolt,
            damages_player=False, target=self.entity_manager,
        )
        self.projectile_registry(proj)


# -- Magic Staff -----------------------------------------------------------
class MagicStaff(RangedWeapon):
    name              = "Magic Staff"
    projectile_speed  = 22.0
    projectile_damage = 25.0
    stamina_cost      = 40
    cooldown          = 1.0
    gravity           = -3.0   # fireballs arc gently

    def _build(self):
        mesh = _build_merged_mesh([
            # Staff shaft
            (0,  0.10, 0,  0.045, 0.75, 0.045, (0.30, 0.18, 0.40, 1)),
            # Orb housing
            (0,  0.55, 0,  0.12,  0.12, 0.12,  (0.55, 0.10, 0.75, 1)),
            # Orb glow core
            (0,  0.55, 0,  0.08,  0.08, 0.08,  (0.90, 0.40, 1.00, 1)),
            # Decorative rings
            (0,  0.38, 0,  0.06,  0.025, 0.06, (0.70, 0.55, 0.20, 1)),
            (0,  0.22, 0,  0.055, 0.025, 0.055,(0.70, 0.55, 0.20, 1)),
            # Handle
            (0, -0.22, 0,  0.05,  0.30, 0.05,  (0.25, 0.14, 0.35, 1)),
            # Pommel crystal
            (0, -0.38, 0,  0.07,  0.07, 0.07,  (0.55, 0.10, 0.75, 1)),
        ])
        self._base_pos = (-1.20, -0.30, 2.4)
        self.weapon_entity = Entity(
            parent=camera, model=mesh,
            position=self._base_pos, rotation=(10, 110, 15),
            scale=(7.5, 1.5, 3.5), enabled=False, double_sided=True,
            shader=lit_with_shadows_shader,
        )

    def _fire(self):
        origin    = self.player.position + Vec3(0, 1.6, 0)
        direction = self._get_fire_direction()

        # -- Fireball visual, unlit glowing orb, no shader ----------------
        fireball = Entity(
            model    = 'sphere',
            color    = color.rgba(1.0, 0.15, 0.05, 1.0),
            scale    = 1.0,
            position = origin,
            unlit    = True,   # glows regardless of lighting
        )

        # Inner bright core, smaller brighter sphere inside the fireball
        Entity(
            parent   = fireball,
            model    = 'sphere',
            color    = color.rgba(0.85, 0.85, 0.10, 0.35),
            scale    = 1.5,
            unlit    = True,
        )

        entity_manager = self.entity_manager

        proj = Projectile(
            origin          = origin,
            direction       = direction,
            speed           = self.projectile_speed,
            damage          = self.projectile_damage + random.randint(-4, 4),
            gravity         = self.gravity,
            visual_entity   = fireball,
            damages_player  = False,
            target          = self.entity_manager,
            # Spawn explosion wherever the fireball hits
            on_terrain_hit  = lambda pos: entity_manager.spawn_explosion(
                pos, self.projectile_damage * 0.6,
                color_rgba=color.rgba(1.0, 0.35, 0.05, 1.0),
                damages_player = False # Player's explosion shouldn't hurt the player!
            ),
        )
        self.projectile_registry(proj)

    def _play_fire_sound(self):
        play_sound("entity/cast_spell")