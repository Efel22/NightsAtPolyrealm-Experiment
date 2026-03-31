from ursina import *
from ursina.shaders import lit_with_shadows_shader
import math
import random
from code.world.world_settings import CHUNK_SIZE, IMPOSTOR_RADIUS

# --- Color Definitions ---
sky_blue   = color.hex('#87CEEB')
sun_color  = color.hex('#ffff00')
moon_color = color.hex("#5D687D")

sky_night = Color(0.02, 0.02, 0.08, 1)
sky_dawn  = Color(0.85, 0.40, 0.15, 1)
sky_day   = Color(0.53, 0.81, 0.92, 1)
sky_dusk  = Color(0.80, 0.35, 0.12, 1)

def lerp_color(color_a, color_b, t):
    return Color(
        color_a.r + (color_b.r - color_a.r) * t,
        color_a.g + (color_b.g - color_a.g) * t,
        color_a.b + (color_b.b - color_a.b) * t,
        color_a.a + (color_b.a - color_a.a) * t
    )


def _build_single_cloud_mesh(verts, tris, cols, idx, ox, oz, scale_mult, rng):
    top_col  = color.rgba(1.00, 1.00, 1.00, 0.92)
    side_col = color.rgba(0.82, 0.86, 0.90, 0.87)
    bot_col  = color.rgba(0.65, 0.70, 0.78, 0.82)

    num_blocks  = rng.randint(10, 18)               # more blocks per cloud
    cloud_w     = rng.uniform(60, 120) * scale_mult  # much wider
    cloud_d     = rng.uniform(40,  80) * scale_mult  # much deeper
    cloud_h_max = rng.uniform(12,  24) * scale_mult  # much taller

    blocks = []
    bw = rng.uniform(cloud_w*0.4, cloud_w*0.7)
    bd = rng.uniform(cloud_d*0.4, cloud_d*0.7)
    bh = rng.uniform(cloud_h_max*0.5, cloud_h_max)
    blocks.append((0, bh/2, 0, bw, bh, bd))

    for _ in range(num_blocks - 1):
        bw = rng.uniform(cloud_w*0.15, cloud_w*0.5)
        bd = rng.uniform(cloud_d*0.15, cloud_d*0.5)
        bh = rng.uniform(cloud_h_max*0.3, cloud_h_max*0.8)
        bx = rng.uniform(-cloud_w*0.35, cloud_w*0.35)
        bz = rng.uniform(-cloud_d*0.35, cloud_d*0.35)
        by = rng.uniform(0, cloud_h_max*0.3)
        blocks.append((bx, bh/2 + by, bz, bw, bh, bd))

    for (bx, by, bz, sw, sh, sd) in blocks:
        hx=sw/2; hy=sh/2; hz=sd/2
        faces = [
            [(-hx,hy,-hz),(-hx,hy,hz),(hx,hy,hz),(hx,hy,-hz)],     top_col,
            [(-hx,-hy,-hz),(hx,-hy,-hz),(hx,-hy,hz),(-hx,-hy,hz)],  bot_col,
            [(-hx,-hy,hz),(hx,-hy,hz),(hx,hy,hz),(-hx,hy,hz)],      side_col,
            [(hx,-hy,-hz),(-hx,-hy,-hz),(-hx,hy,-hz),(hx,hy,-hz)],  side_col,
            [(-hx,-hy,-hz),(-hx,-hy,hz),(-hx,hy,hz),(-hx,hy,-hz)],  side_col,
            [(hx,-hy,hz),(hx,-hy,-hz),(hx,hy,-hz),(hx,hy,hz)],      side_col,
        ]
        i = 0
        while i < len(faces):
            fv = faces[i]; fc = faces[i+1]; i += 2
            for (fx, fy, fz) in fv:
                verts.append((ox + bx + fx, by + fy, oz + bz + fz))
                cols.append(fc)
            tris.append((idx, idx+1, idx+2, idx+3))
            idx += 4

    return idx


class CloudGroup:
    CLOUDS_PER_GROUP = 3

    def __init__(self, center_pos: Vec3, rng):
        verts = []; tris = []; cols = []; idx = 0
        spread = 400
        for i in range(self.CLOUDS_PER_GROUP):
            ox = rng.uniform(-spread, spread)
            oz = rng.uniform(-spread, spread)
            scale = rng.uniform(2.5, 4.5)  # much bigger scale
            idx = _build_single_cloud_mesh(verts, tris, cols, idx, ox, oz, scale, rng)

        self.entity = Entity(
            model=Mesh(vertices=verts, triangles=tris, colors=cols, mode='triangle'),
            position=center_pos,
            double_sided=False,
            shader=lit_with_shadows_shader,
        )

    def set_position(self, pos):
        self.entity.position = pos

    def set_enabled(self, val):
        self.entity.enabled = val

    def set_alpha(self, a, day_intensity):
        r = 0.25 + (1.00 - 0.25) * day_intensity
        g = 0.28 + (1.00 - 0.28) * day_intensity
        b = 0.35 + (1.00 - 0.35) * day_intensity
        self.entity.color = color.rgba(r, g, b, a)

    def destroy(self):
        destroy(self.entity)


class SkySystem:

    def __init__(self):

        self.sky = Sky(color=sky_blue)

        self.daytime_cycle_speed  = 10
        self.astral_dist          = 1000

        self.cloud_group_count     = 3
        self.cloud_height          = (CHUNK_SIZE * 5)
        self.cloud_spread          = (CHUNK_SIZE * 5) * (IMPOSTOR_RADIUS)
        self.cloud_render_distance = ((CHUNK_SIZE * 5) * IMPOSTOR_RADIUS) * 1.5
        self.cloud_speed           = Vec3(((CHUNK_SIZE / 5)), 0, 0)
        self.cloud_respawn_margin  = (CHUNK_SIZE * 5) * (IMPOSTOR_RADIUS - 2) # How far can the clouds go before they teleport "back"?

        self.Sky_Pivot = Entity(parent=scene)

        from ursina.lights import DirectionalLight, AmbientLight

        self.sun_light = DirectionalLight(
            parent=self.Sky_Pivot,
            position=(-self.astral_dist, 0, 0),
            shadows=True,
        )

        self.ambient_light = AmbientLight(
            color=color.rgba(0.15, 0.15, 0.25, 1)
        )

        self.sun_visual = Entity(
            parent=self.Sky_Pivot,
            model='cube',
            scale=60,
            color=color.rgba(sun_color.r, sun_color.g, sun_color.b, 255),
            x=-self.astral_dist,
        )

        self.moon_visual = Entity(
            parent=self.Sky_Pivot,
            model='cube',
            scale=60,
            color=color.rgba(moon_color.r, moon_color.g, moon_color.b, 0),
            x=self.astral_dist,
        )

        star_vertices = []
        rng = random.Random(42)
        for _ in range(150):
            theta  = rng.uniform(0, 2*math.pi)
            phi    = rng.uniform(0, math.pi)
            radius = self.astral_dist
            x = radius * math.sin(phi) * math.cos(theta)
            y = radius * math.sin(phi) * math.sin(theta)
            z = radius * math.cos(phi)
            star_vertices.append(Vec3(x, y, z))

        self.star_mesh_entity = Entity(
            parent=self.Sky_Pivot,
            model=Mesh(vertices=star_vertices, mode='point', thickness=rng.uniform(0, 4)),
            color=color.rgba(255, 255, 255, 0),
        )

        self.cloud_groups = []
        for i in range(self.cloud_group_count):
            rng = random.Random(i * 9999)
            pos = Vec3(
                rng.uniform(-self.cloud_spread, self.cloud_spread),
                self.cloud_height,
                rng.uniform(-self.cloud_spread, self.cloud_spread),
            )
            self.cloud_groups.append(CloudGroup(pos, rng))

    @property
    def is_night(self) -> bool:
        """Returns True when the sun is below the horizon."""
        return self.sun_visual.world_y < 0

    # ------------------------------------------------------------------ #
    #  SKY COLOR                                                           #
    # ------------------------------------------------------------------ #

    def _get_sky_color(self, sun_y_normalized):
        s = sun_y_normalized
        if s < -0.15:
            return sky_night
        elif s < 0.0:
            t = (s + 0.15) / 0.15
            return lerp_color(sky_night, sky_dawn, t)
        elif s < 0.15:
            t = s / 0.15
            return lerp_color(sky_dawn, sky_day, t)
        else:
            t = min(1.0, (s - 0.15) / 0.5)
            return lerp_color(sky_day, sky_day, t)

    # ------------------------------------------------------------------ #
    #  UPDATE                                                              #
    # ------------------------------------------------------------------ #

    def update_sky(self, world):

        self.Sky_Pivot.position = camera.world_position
        self.Sky_Pivot.rotation_z += time.dt * self.daytime_cycle_speed

        sun_height    = self.sun_visual.world_y / 100
        day_intensity = clamp(sun_height, 0, 1)
        night_intensity = 1 - day_intensity

        sun_y_norm = self.sun_visual.world_y / self.astral_dist
        self.sky.color = self._get_sky_color(sun_y_norm)

        # Horizon glow factor, peaks at dawn/dusk
        horizon_factor    = 1.0 - min(1.0, abs(sun_y_norm) / 0.2)
        effective_horizon = horizon_factor * min(day_intensity, 1.0 - day_intensity) * 4
        effective_horizon = min(1.0, effective_horizon)

        # ── Sun light, drives all chunk/terrain lighting ─────────────
        # Color shifts warm at horizon (dawn/dusk) and dims to near-zero at night.
        warm_r = day_intensity + effective_horizon * 0.5
        warm_g = day_intensity * 0.90 + effective_horizon * 0.20
        warm_b = day_intensity * 0.75 - effective_horizon * 0.25

        # Sun light, never fully off at night so terrain stays visible
        self.sun_light.color = color.rgba(
            max(0.25, min(1.0, warm_r)),
            max(0.25, min(1.0, warm_g)),
            max(0.35, min(1.0, max(0.0, warm_b))),
            1
        )

        # Ambient, high floor so night is dim but never pitch black
        # The values after 'min(1.0,... X <--- are the ones that determine brightness
        self.ambient_light.color = color.rgba(
            max(0.0, min(1.0, 0.70 + 0.45 * day_intensity + effective_horizon * 0.20)),
            max(0.0, min(1.0, 0.70 + 0.40 * day_intensity + effective_horizon * 0.05)),
            max(0.0, min(1.0, 0.80 + 0.25 * day_intensity - effective_horizon * 0.15)),
            1
        )

        self.sun_visual.alpha = day_intensity

        moon_height_factor     = clamp(self.moon_visual.world_y / 10, 0, 1)
        self.moon_visual.alpha = night_intensity * moon_height_factor
        self.star_mesh_entity.alpha_setter(self.moon_visual.alpha)

        # ── Cloud update ──────────────────────────────────────────────
        cam_pos = camera.world_position

        for group in self.cloud_groups:
            group.entity.x += self.cloud_speed.x * time.dt
            group.entity.z += self.cloud_speed.z * time.dt

            dx = group.entity.x - cam_pos.x
            dz = group.entity.z - cam_pos.z
            limit = self.cloud_spread + self.cloud_respawn_margin

            if dx >  limit: group.set_position(group.entity.position - Vec3(limit*2, 0, 0))
            elif dx < -limit: group.set_position(group.entity.position + Vec3(limit*2, 0, 0))
            if dz >  limit: group.set_position(group.entity.position - Vec3(0, 0, limit*2))
            elif dz < -limit: group.set_position(group.entity.position + Vec3(0, 0, limit*2))

            dist = math.sqrt(dx*dx + dz*dz)
            group.set_enabled(dist < self.cloud_render_distance)
            if dist < self.cloud_render_distance:
                cloud_alpha = max(0.3, 0.90 * day_intensity)
                group.set_alpha(cloud_alpha, day_intensity)

    def reset(self):
        # 1. Reset the rotation of the sky (Back to morning)
        self.Sky_Pivot.rotation_z = 0
        
        # 2. Reset cloud positions
        for i, group in enumerate(self.cloud_groups):
            rng = random.Random(i * 9999)
            group.entity.x = rng.uniform(-self.cloud_spread, self.cloud_spread)
            group.entity.z = rng.uniform(-self.cloud_spread, self.cloud_spread)
            
        # 3. Force an immediate update so the colors snap back
        self.update_sky(None)