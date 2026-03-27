from ursina import *
import math
import random
from ursina.ursinastuff import *
from .projectile import Projectile
from .specs import *
from code.world.world_settings import *
from ursina.shaders import lit_with_shadows_shader
from code.sound import play_sound

# ============================================================
#  TASK BASE + BUILT-IN TASKS
# ============================================================

class Task:
    """Abstract base class for all entity behaviours."""

    # Priority: higher = runs first in the selector.
    priority: int = 0

    def can_run(self, entity) -> bool:
        """Return True if this task should become active."""
        return False

    def on_start(self, entity):
        """Called once when this task becomes active."""
        pass

    def on_stop(self, entity):
        """Called once when this task is deactivated."""
        pass

    def update(self, entity, dt):
        """Called every frame while this task is active."""
        pass


# ------------------------------------------------------------------ #

class TaskWander(Task):
    """Wander aimlessly, periodically picking a new random direction."""

    priority = 0   # lowest, fallback behaviour

    def __init__(self, speed: float = 3.0,
                 change_interval: float = 3.5,
                 idle_chance: float = 0.25):
        self.speed           = speed
        self.change_interval = change_interval
        self.idle_chance     = idle_chance

    def can_run(self, entity) -> bool:
        return True   # always willing to run as a fallback

    def on_start(self, entity):
        entity._wander_timer = 0.0
        entity._wander_dir   = self._random_dir()

    def on_stop(self, entity):
        entity._wander_dir = Vec3(0, 0, 0)

    def update(self, entity, dt):
        entity._wander_timer += dt
        if entity._wander_timer >= self.change_interval:
            entity._wander_timer = 0.0
            if random.random() < self.idle_chance:
                entity._wander_dir = Vec3(0, 0, 0)
            else:
                entity._wander_dir = self._random_dir()

        entity._move_in_dir(entity._wander_dir, self.speed, dt)

    @staticmethod
    def _random_dir():
        angle = random.uniform(0, math.pi * 2)
        return Vec3(math.cos(angle), 0, math.sin(angle))


# ------------------------------------------------------------------ #

class TaskChaseTarget(Task):
    """Move towards a target Entity or Vec3.  Activate within trigger_range."""

    priority = 10

    def __init__(self, get_target,
                 speed: float = 6.0,
                 trigger_range: float = 20.0,
                 stop_range: float = 2.5,
                 airborne: bool = False):
        """
        get_target : callable() -> Entity|Vec3|None
        airborne   : if True, tracks target on Y axis too (flying entities)
        """
        self.get_target    = get_target
        self.speed         = speed
        self.trigger_range = trigger_range
        self.stop_range    = stop_range
        self.airborne      = airborne

    def _target_pos(self) -> Vec3 | None:
        t = self.get_target()
        if t is None:
            return None
        return t.position if hasattr(t, 'position') else t

    def can_run(self, entity) -> bool:
        tp = self._target_pos()
        if tp is None:
            return False
        return distance(entity.root.position, tp) <= self.trigger_range

    def on_start(self, entity):
        pass

    def on_stop(self, entity):
        pass

    def update(self, entity, dt):
        tp = self._target_pos()
        if tp is None:
            return
        diff = tp - entity.root.position
        if not self.airborne:
            diff.y = 0
        dist = diff.length()
        if dist > self.stop_range:
            entity._move_in_dir(diff.normalized(), self.speed, dt, use_y=self.airborne)


# ------------------------------------------------------------------ #

class TaskRangedAttack(Task):
    """Fire a projectile at the player (or any target) when in range."""

    priority = 15

    def __init__(self, get_target,
                 attack_range: float = 14.0,
                 cooldown: float = 2.5,
                 projectile_speed: float = 18.0,
                 projectile_damage: float = 10.0,
                 projectile_color=None,
                 arc_height: float = 0.0,
                 on_projectile_spawn=None,
                 projectile_scale: float = 0.45,
                 damages_player: bool = True,   
                 get_player_fn = None,
                 on_terrain_hit=None
                 ):
        """
        on_projectile_spawn : optional callback(projectile) so the manager
                              can track projectiles for cleanup.
        projectile_scale    : visual radius of the projectile sphere
        """
        self.get_target          = get_target
        self.attack_range        = attack_range
        self.cooldown            = cooldown
        self.projectile_speed    = projectile_speed
        self.projectile_damage   = projectile_damage
        self.projectile_color    = projectile_color
        self.arc_height          = arc_height
        self.on_projectile_spawn = on_projectile_spawn
        self.projectile_scale    = projectile_scale
        self.damages_player      = damages_player
        self.get_player_fn       = get_player_fn
        self.on_terrain_hit      = on_terrain_hit
        self._cooldown_timer     = 0.0

    def _target_pos(self) -> Vec3 | None:
        t = self.get_target()
        if t is None:
            return None
        return t.position if hasattr(t, 'position') else t

    def can_run(self, entity) -> bool:
        tp = self._target_pos()
        if tp is None:
            return False
        return distance(entity.root.position, tp) <= self.attack_range

    def on_start(self, entity):
        self._cooldown_timer = self.cooldown   # fire immediately on entry

    def update(self, entity, dt):
        self._cooldown_timer += dt
        if self._cooldown_timer < self.cooldown:
            return

        tp = self._target_pos()
        if tp is None:
            return

        self._cooldown_timer = 0.0

        # - Face the target before attacking ---------------
        diff = tp - entity.root.position
        diff.y = 0
        if diff.length() > 0.01:
            target_angle = math.degrees(math.atan2(diff.x, diff.z))
            entity.root.rotation_y = target_angle

        # Trigger attack animation
        entity._trigger_attack()

        # Spawn projectile from entity's "mouth" position
        origin    = entity.root.position + Vec3(0, 1.0, 0)
        direction = (tp + Vec3(0, 0.5, 0) - origin).normalized()

        if self.arc_height != 0.0:
            direction.y += self.arc_height

        proj = Projectile(
            origin         = origin,
            direction      = direction,
            speed          = self.projectile_speed,
            damage         = self.projectile_damage,
            color_rgba     = self.projectile_color,
            scale          = self.projectile_scale,
            damages_player = self.damages_player,
            target         = self.get_player_fn() if self.get_player_fn else None,
            on_hit         = lambda p: self._on_hit_player(p),
            on_terrain_hit = self.on_terrain_hit,
        )
        if self.on_projectile_spawn:
            self.on_projectile_spawn(proj)

    def _on_hit_player(self, target):
        """Called when projectile hits the player."""
        from code.entity.player.playerdata import player_stats
        if player_stats is not None:
            player_stats.take_damage(self.projectile_damage)


# ------------------------------------------------------------------ #

class TaskMeleeAttack(Task):
    """Trigger an attack animation + deal damage when close to target."""

    priority = 20

    def __init__(self, get_target,
                 attack_range: float = 2.0,
                 cooldown: float = 1.2,
                 damage: float = 15.0,
                 on_hit=None,
                 die_on_hit: bool = False):
        """
        on_hit     : optional callback(target_entity)
        die_on_hit : if True, the entity that owns this task destroys itself
                     immediately after landing a hit (e.g. kamikaze bee sting)
        """
        self.get_target   = get_target
        self.attack_range = attack_range
        self.cooldown     = cooldown
        self.damage       = damage
        self.on_hit       = on_hit
        self.die_on_hit   = die_on_hit
        self._cooldown_timer = 0.0

    def _target_pos(self) -> Vec3 | None:
        t = self.get_target()
        if t is None:
            return None
        return t.position if hasattr(t, 'position') else t

    def can_run(self, entity) -> bool:
        tp = self._target_pos()
        if tp is None:
            return False
        return distance(entity.root.position, tp) <= self.attack_range

    def on_start(self, entity):
        self._cooldown_timer = self.cooldown

    def update(self, entity, dt):
        self._cooldown_timer += dt
        if self._cooldown_timer < self.cooldown:
            return

        tp = self._target_pos()
        if tp is None or distance(entity.root.position, tp) > self.attack_range:
            return

        self._cooldown_timer = 0.0
        entity._trigger_attack()

        t = self.get_target()
        if self.on_hit and t is not None:
            self.on_hit(t)

        # Deal damage with visual feedback if target is an EntityAI
        if hasattr(t, 'take_damage'):
            t.take_damage(self.damage)
        
        if self.die_on_hit:
            entity.dead = True


# ------------------------------------------------------------------ #

class TaskSpawnMinions(Task):
    """
    Periodically spawns minion entities around the owner.
    Respects a max_alive cap so the hive can never flood the world.

    Usage (beehive example):
        hive.add_task(TaskSpawnMinions(
            entity_manager = entity_manager,
            spec_fn        = spec_bee,
            setup_fn       = _setup_bee,   # adds tasks to the freshly spawned minion
            spawn_interval = 8.0,
            max_alive      = 5,
            spawn_radius   = 2.0,
            spawn_height   = 0.5,
            minion_gravity = 0.0,
            minion_lifetime= 30.0,
        ))
    """

    priority = 1   # runs as background, never blocks other tasks

    def __init__(self,
                 entity_manager,
                 spec_fn,
                 setup_fn,
                 spawn_interval: float = 8.0,
                 max_alive:      int   = 5,
                 spawn_radius:   float = 2.0,
                 spawn_height:   float = 0.5,
                 minion_gravity: float = 0.0,
                 minion_lifetime:float = 30.0):
        """
        entity_manager  : the EntityManager instance
        spec_fn         : callable() -> dict , returns the minion spec
        setup_fn        : callable(minion: EntityAI), adds tasks to the minion
        spawn_interval  : seconds between spawns
        max_alive       : hard cap on living minions owned by this hive
        spawn_radius    : XZ scatter radius around the hive
        spawn_height    : Y offset above the hive root for spawn point
        minion_gravity  : gravity for spawned minions (0 = flying)
        minion_lifetime : seconds until minion auto-expires (0 = forever)
        """
        self.entity_manager  = entity_manager
        self.spec_fn         = spec_fn
        self.setup_fn        = setup_fn
        self.spawn_interval  = spawn_interval
        self.max_alive       = max_alive
        self.spawn_radius    = spawn_radius
        self.spawn_height    = spawn_height
        self.minion_gravity  = minion_gravity
        self.minion_lifetime = minion_lifetime

        self._timer   = spawn_interval   # fire immediately on first tick
        self._minions : list = []        # weak tracking list

    def can_run(self, entity) -> bool:
        return True   # always ticks in background

    def update(self, entity, dt):
        # Purge expired / dead minions from tracking list
        self._minions = [m for m in self._minions if not m.dead]

        self._timer += dt
        if self._timer < self.spawn_interval:
            return
        if len(self._minions) >= self.max_alive:
            return

        self._timer = 0.0

        # Scatter spawn position around hive
        angle  = random.uniform(0, math.pi * 2)
        radius = random.uniform(0.5, self.spawn_radius)
        offset = Vec3(math.cos(angle) * radius,
                      self.spawn_height,
                      math.sin(angle) * radius)
        pos = entity.root.position + offset

        minion = self.entity_manager.spawn(
            pos,
            spec        = self.spec_fn(),
            gravity     = self.minion_gravity,
            max_lifetime= self.minion_lifetime,
        )
        self.setup_fn(minion)
        self._minions.append(minion)


# ============================================================
#  ANIMATED MODEL BUILDER
# ============================================================

class AnimatedModel:
    """
    Builds a creature model from a spec dict.

    OPTIMISED: animated parts become lightweight pivot Entities (no mesh).
    All static (non-animated) parts are baked into a SINGLE merged Mesh Entity
    parented to the root, reducing scene entity count.

    Only parts that appear in ANY animation slot get their own pivot Entity.
    Everything else is one draw call.

    spec format identical to before, see EntityAI docstring.
    """

    def __init__(self, root_entity: Entity, spec: dict):
        self.root       = root_entity
        self.parts      = {}    # name -> Entity (pivot, only for animated parts)
        self._base_rot  = {}    # name -> Vec3
        self._base_pos  = {}    # name -> Vec3

        part_list  = spec.get("parts", [])
        anim_data  = spec.get("animations", {})

        # Collect names of every part that appears in any animation
        animated_names = set()
        for anim_frames in anim_data.values():
            animated_names.update(anim_frames.keys())

        # Also mark any part whose PARENT is animated (so it moves with it)
        # We do a transitive closure so grandchildren work too
        parent_map = {p["name"]: p.get("parent") for p in part_list}
        changed = True
        while changed:
            changed = False
            for name, parent in parent_map.items():
                if parent in animated_names and name not in animated_names:
                    animated_names.add(name)
                    changed = True

        # Build a pivot Entity for every animated part (no mesh, just a transform)
        # and accumulate static parts into a single merged mesh.
        static_verts = []
        static_cols  = []
        static_tris  = []
        s_idx        = 0

        # We need world-space positions for static parts.
        # Compute them by walking the parent chain of resolved pivot entities.
        def _world_pos_rot(p_def):
            """Return (world_pos Vec3, world_rot_euler Vec3) for a part def
               by composing parent transforms.  Works only for static parts
               whose parents are also static (non-animated)."""
            pos = Vec3(*p_def.get("position", (0,0,0)))
            # For static parts we flatten the hierarchy into object space
            # relative to root, we simply accumulate position offsets
            # (rotation composition would need quaternions; for creature bodies
            # that are mostly axis-aligned this is accurate enough).
            parent_name = p_def.get("parent")
            visited = set()
            while parent_name and parent_name not in visited:
                visited.add(parent_name)
                par_def = next((x for x in part_list if x["name"] == parent_name), None)
                if par_def is None:
                    break
                pos += Vec3(*par_def.get("position", (0,0,0)))
                parent_name = par_def.get("parent")
            return pos

        def _add_box_static(cx, cy, cz, sx, sy, sz, col_rgba):
            nonlocal s_idx
            hx, hy, hz = sx/2, sy/2, sz/2
            r, g, b, a = col_rgba
            fc = color.rgba(r, g, b, a)
            ds, db = 0.78, 0.48
            sc = color.rgba(r*ds, g*ds, b*ds, a)
            bc = color.rgba(r*db, g*db, b*db, a)
            faces = [
                [(-hx,hy,-hz),(-hx,hy,hz),(hx,hy,hz),(hx,hy,-hz)],   fc,
                [(-hx,-hy,-hz),(hx,-hy,-hz),(hx,-hy,hz),(-hx,-hy,hz)],bc,
                [(-hx,-hy,hz),(hx,-hy,hz),(hx,hy,hz),(-hx,hy,hz)],   sc,
                [(hx,-hy,-hz),(-hx,-hy,-hz),(-hx,hy,-hz),(hx,hy,-hz)],sc,
                [(-hx,-hy,-hz),(-hx,-hy,hz),(-hx,hy,hz),(-hx,hy,-hz)],sc,
                [(hx,-hy,hz),(hx,-hy,-hz),(hx,hy,-hz),(hx,hy,hz)],    sc,
            ]
            i = 0
            while i < len(faces):
                fv, fc2 = faces[i], faces[i+1]; i += 2
                for (fx,fy,fz) in fv:
                    static_verts.append((cx+fx, cy+fy, cz+fz))
                    static_cols.append(fc2)
                static_tris.append((s_idx, s_idx+1, s_idx+2, s_idx+3))
                s_idx += 4

        def _add_pyramid_static(cx, cy, cz, sx, sy, sz, col_rgba):
            """Four-sided pyramid: base at cy-sy/2, apex at cy+sy/2.
               sx/sz are the base half-extents.  Uses triangular faces."""
            nonlocal s_idx
            hx, hz = sx/2, sz/2
            base_y = cy - sy/2
            apex_y = cy + sy/2
            apex   = (cx, apex_y, cz)
            r, g, b, a = col_rgba
            fc = color.rgba(r, g, b, a)
            ds = 0.72
            sc = color.rgba(r*ds, g*ds, b*ds, a)
            bc = color.rgba(r*0.45, g*0.45, b*0.45, a)
            # Base corners (CCW from above)
            bl = (cx-hx, base_y, cz-hz)
            br = (cx+hx, base_y, cz-hz)
            fr = (cx+hx, base_y, cz+hz)
            fl = (cx-hx, base_y, cz+hz)
            # Base quad
            for v in (bl, br, fr, fl):
                static_verts.append(v); static_cols.append(bc)
            static_tris.append((s_idx, s_idx+1, s_idx+2, s_idx+3)); s_idx += 4
            # Four triangular sides, each emitted as a degenerate quad
            # (v0, v1, apex, apex) so we stay in the quad-only path
            sides = [
                (br, bl, fc),   # south face (toward -z)
                (fl, fr, sc),   # north face
                (bl, fl, sc),   # west face
                (fr, br, sc),   # east face
            ]
            for (v0, v1, col) in sides:
                static_verts.extend([v0, v1, apex, apex])
                static_cols.extend([col, col, col, col])
                static_tris.append((s_idx, s_idx+1, s_idx+2, s_idx+3))
                s_idx += 4

        for p_def in part_list:
            name   = p_def["name"]
            parent = p_def.get("parent")
            col    = p_def.get("color", (1,1,1,1))
            scl    = p_def.get("scale", (1,1,1))
            pos    = p_def.get("position", (0,0,0))
            rot    = p_def.get("rotation", (0,0,0))

            if name in animated_names:
                # Single Entity per animated part, model, scale, position
                # and rotation all on the same object.  Children of this
                # part (e.g. staff child of arm_r) parent to this entity
                # and inherit scale correctly via Ursina's transform chain.
                parent_ent = self.parts.get(parent) if parent else self.root
                ent = Entity(
                    parent      = parent_ent,
                    model       = p_def.get("shape", "cube"),
                    color       = color.rgba(*col),
                    scale       = scl,
                    position    = pos,
                    rotation    = rot,
                    double_sided= True,
                    shader      = lit_with_shadows_shader,
                )
                self.parts[name]    = ent
                self._base_rot[name] = Vec3(*rot)
                self._base_pos[name] = Vec3(*pos)
            else:
                # Bake into the static merged mesh
                world_pos = _world_pos_rot(p_def)
                sx2, sy2, sz2 = scl
                shape = p_def.get("shape", "cube")
                if shape == "pyramid":
                    _add_pyramid_static(world_pos.x, world_pos.y, world_pos.z,
                                        sx2, sy2, sz2, col)
                else:
                    _add_box_static(world_pos.x, world_pos.y, world_pos.z,
                                    sx2, sy2, sz2, col)

        # Spawn the single static mesh entity (if anything is static)
        if static_verts:
            self._static_entity = Entity(
                parent      = self.root,
                model       = Mesh(vertices=static_verts, triangles=static_tris,
                                   colors=static_cols, mode='triangle'),
                double_sided= True,
                shader      = lit_with_shadows_shader,
            )
        else:
            self._static_entity = None

        self.animations = spec.get("animations", {})
        self._anim_timer  = 0.0
        self._anim_blend  = 0.0   # 0 = rest pose, 1 = full anim
        self._active_anim = None  # "walk" | "attack" | None

        # Attack one-shot state
        self._attack_timer    = 0.0
        self._attack_duration = spec.get("attack_duration", 0.45)

    # ---------------------------------------------------------------- #

    def trigger_attack(self):
        """Fire a one-shot attack animation."""
        self._active_anim  = "attack"
        self._attack_timer = 0.0

    def update(self, dt, is_moving: bool):
        # --- If attacking, freeze in rest pose and wait ---
        if self._active_anim == "attack":
            self._attack_timer += dt
            self._anim_blend = max(0.0, self._anim_blend - dt * 8.0)  # fade out walk
            if self._attack_timer >= self._attack_duration:
                self._active_anim  = "walk" if is_moving else None
                self._attack_timer = 0.0

        elif is_moving:
            if self._active_anim != "walk":
                self._active_anim = "walk"
            self._anim_blend = min(1.0, self._anim_blend + dt * 6.0)

        else:
            self._anim_blend = max(0.0, self._anim_blend - dt * 6.0)
            if self._anim_blend == 0.0:
                self._active_anim = None

        # --- Apply walk animation frame — blends to rest pose during attack ---
        anim_data = self.animations.get("walk", {}) if self._active_anim == "walk" else {}
        self._anim_timer += dt

        for name, ent in self.parts.items():
            base_r    = self._base_rot[name]
            base_p    = self._base_pos[name]
            part_anim = anim_data.get(name, {})

            rot_off = Vec3(0, 0, 0)
            if "rotation_offset" in part_anim:
                ro = part_anim["rotation_offset"]
                rv = ro(self._anim_timer) if callable(ro) else ro
                rot_off = Vec3(*rv) * self._anim_blend

            pos_off = Vec3(0, 0, 0)
            if "position_offset" in part_anim:
                po = part_anim["position_offset"]
                pv = po(self._anim_timer) if callable(po) else po
                pos_off = Vec3(*pv) * self._anim_blend

            ent.rotation = base_r + rot_off
            ent.position = base_p + pos_off


# ============================================================
#  ENTITY AI  (the main creature class)
# ============================================================

class EntityAI:
    """
    A modular AI entity.

    Usage:
        entity = EntityAI(world, position=Vec3(5,10,5), spec=MY_SPEC)
        entity.add_task(TaskWander(speed=3))
        entity.add_task(TaskChaseTarget(lambda: player, speed=6, trigger_range=20))
    """

    def __init__(self, world, position: Vec3, spec: dict = None,
                 gravity: float = -20.0, max_lifetime: float = 0.0):
        self.world    = world
        self.entity_manager = None
        self.GRAVITY  = gravity       # instance-level: 0.0 for flying entities
        self._vel_y   = 0.0
        self._is_moving = False
        self._wander_dir   = Vec3(0, 0, 0)
        self._wander_timer = 0.0
        self.dead          = False    # set True -> EntityManager removes + destroys
        self._lifetime     = 0.0
        self.max_lifetime  = max_lifetime  # 0 = live forever
        # Health system, pulled from spec so each enemy type can differ
        self.max_health     = spec.get("health", 100.0)
        self.current_health = self.max_health
        self.world          = world
        self.entity_manager = None
        self.xp_value       = spec.get("xp_value", 20) if spec else 20 

        # Root (invisible pivot, carries the whole creature)
        self.root = Entity(position=position)

        # Build animated model
        spec = spec
        self._anim_model = AnimatedModel(self.root, spec)

        # Task list, sorted descending by priority
        self._tasks: list[Task]    = []
        self._active_task: Task | None = None

    # ---------------------------------------------------------------- #
    #  Public API                                                        #
    # ---------------------------------------------------------------- #

    def add_task(self, task: Task):
        self._tasks.append(task)
        self._tasks.sort(key=lambda t: t.priority, reverse=True)

    def remove_task(self, task: Task):
        if task in self._tasks:
            self._tasks.remove(task)

    # ---------------------------------------------------------------- #
    #  Internal helpers called by Tasks                                  #
    # ---------------------------------------------------------------- #

    def _move_in_dir(self, direction: Vec3, speed: float, dt: float, use_y: bool = False):
        """Translate root in XZ (and Y if use_y) and rotate to face direction."""
        self.root.x += direction.x * speed * dt
        self.root.z += direction.z * speed * dt
        if use_y:
            self.root.y += direction.y * speed * dt
        self._is_moving = True

        # Rotate only on XZ plane regardless of Y movement
        flat = Vec3(direction.x, 0, direction.z)
        if flat.length() > 0.01:
            target_angle = math.degrees(math.atan2(flat.x, flat.z))
            diff = (target_angle - self.root.rotation_y + 180) % 360 - 180
            self.root.rotation_y += diff * min(1.0, dt * 12.0)

    def _trigger_attack(self):
        self._anim_model.trigger_attack()

    def set_player_stats(self, player_stats):
        """Call once after player_stats is created."""
        self._player_stats = player_stats

    def _damage_player(self, amount: float):
        """Deal damage to the player if player_stats is set."""
        if self._player_stats is not None:
            self._player_stats.take_damage(amount)

    # ---------------------------------------------------------------- #
    #  Gravity + ground snap                                             #
    # ---------------------------------------------------------------- #

    def _apply_gravity(self, dt: float):
        ignore_list = list(self._anim_model.parts.values()) + [self.root]

        self._vel_y += self.GRAVITY * dt
        self.root.y += self._vel_y * dt

        hit = raycast(
            origin=Vec3(self.root.x, self.root.y + 50, self.root.z),
            direction=Vec3(0, -1, 0),
            distance=200,
            ignore=ignore_list,
        )

        if hit.hit:
            ground_y = hit.world_point.y
            if self.root.y <= ground_y + 0.05:
                self.root.y  = ground_y
                self._vel_y  = 0.0
        else:
            ground_y = self.world.get_ground_y(self.root.x, self.root.z)
            if self.root.y <= ground_y + 0.05:
                self.root.y  = ground_y
                self._vel_y  = 0.0

    def take_damage(self, amount: float):
        """Apply damage, flash red, show number, and die if health hits zero."""
        if self.dead:
            return

        self.current_health -= amount
        self._flash_red()
        self._spawn_damage_number(amount)

        
        

        if self.current_health <= 0:
            # Spawn a soul orb at this entity's position before dying
            self.entity_manager.spawn_soul_orb(
                position      = self.root.position,
                xp_value      = self.xp_value,
                get_player_fn = self.entity_manager._get_player_fn,
            )
            play_sound("entity/death", volume=1.0)
            self.dead = True
        else:
            play_sound("entity/hurt", volume=1.0)



    def _flash_red(self):
        """Briefly tint all animated parts red then restore their original color."""
        # Collect all visible entities in the model
        parts_to_flash = list(self._anim_model.parts.values())
        if self._anim_model._static_entity:
            parts_to_flash.append(self._anim_model._static_entity)

        # Save original colors, apply red tint
        original_colors = {}
        for part in parts_to_flash:
            original_colors[part] = part.color
            part.color = color.rgba(1.0, 0.15, 0.15, 1)

        # Restore after 0.15 seconds
        def restore():
            for part, col in original_colors.items():
                if part and part.enabled:
                    part.color = col
        invoke(restore, delay=0.15)

    def _spawn_damage_number(self, amount: float):
        """Spawn a floating damage number above the entity that rises and fades."""
        import random

        dmg_text = Text(
            text   = f"-{int(amount)}",
            scale  = 2,
            color  = color.rgba(1.0, 0.25, 0.25, 1.0),
            parent = camera.ui,
            x      = random.uniform(-0.05, 0.05),
            y      = random.uniform(0.0, 0.10),
            origin = (0, 0),
        )

        # Float up over time
        dmg_text.animate_y(dmg_text.y + 0.12, duration=0.85, curve=curve.linear)

        # Fade out
        dmg_text.animate_color(color.rgba(1.0, 0.25, 0.25, 0.0), duration=0.85)

        # Destroy after animation finishes
        invoke(destroy, dmg_text, delay=0.85)
        
    # ---------------------------------------------------------------- #
    #  Main update                                                       #
    # ---------------------------------------------------------------- #

    def update(self, dt: float):
        self._is_moving = False

        # --- Lifetime expiry ---
        if self.max_lifetime > 0.0:
            self._lifetime += dt
            if self._lifetime >= self.max_lifetime:
                self.dead = True
                return   # skip everything else, manager will destroy next frame

        # --- Task selector (priority-based) ---
        best_task = None
        for task in self._tasks:   # already sorted by priority desc
            if task.can_run(self):
                best_task = task
                break

        if best_task is not self._active_task:
            if self._active_task is not None:
                self._active_task.on_stop(self)
            self._active_task = best_task
            if self._active_task is not None:
                self._active_task.on_start(self)

        if self._active_task is not None:
            self._active_task.update(self, dt)

        # --- Physics ---
        self._apply_gravity(dt)

        # --- Animation ---
        self._anim_model.update(dt, self._is_moving)

    def destroy(self):
        if self.root is None:
            return   # already destroyed, nothing to do

        # Destroy every entity in the animated model parts dict
        for part in self._anim_model.parts.values():
            destroy(part)
        self._anim_model.parts.clear()

        # Destroy the static baked mesh
        if self._anim_model._static_entity is not None:
            destroy(self._anim_model._static_entity)
            self._anim_model._static_entity = None

        # Destroy all children of root
        for child in list(self.root.children):
            destroy(child)

        # Destroy the root
        destroy(self.root)

        if self.root in scene.entities:
            scene.entities.remove(self.root)

        self.root = None


# ============================================================
#  ENTITY MANAGER
# ============================================================

class EntityManager:
    """Manages a pool of EntityAI instances and loose Projectiles."""

    def __init__(self, world):
        self.world       = world
        self.entities    : list[EntityAI]   = []
        self.projectiles : list[Projectile] = []
        self.soul_orbs   : list             = []
        self.explosions  : list             = []
        self._get_player_fn = None # PLAYER REFERENCE

    # ---------------------------------------------------------------- #

    def set_player(self, get_player_fn):
        """Call this once after the player exists."""
        self._get_player_fn = get_player_fn

    def spawn(self, position: Vec3, spec: dict = None,
              gravity: float = -20.0, max_lifetime: float = 0.0) -> EntityAI:
        e = EntityAI(self.world, position, spec,
                     gravity=gravity, max_lifetime=max_lifetime)
        e.entity_manager = self   # <- give the entity a reference back to the manager
        self.entities.append(e)
        return e

    def spawn_soul_orb(self, position: Vec3, xp_value: float, get_player_fn):
        """Spawn a soul orb at the given position."""
        from code.entity.soul_orb import SoulOrb
        orb = SoulOrb(position, xp_value, get_player_fn)
        self.soul_orbs.append(orb)
        return orb

    def despawn(self, entity: EntityAI):
        if entity in self.entities:
            self.entities.remove(entity)
        entity.destroy()

    def despawn_all(self):
        for e in self.entities:
            e.destroy()
        self.entities.clear()
        for p in self.projectiles:
            p.destroy()
        self.projectiles.clear()

    def register_projectile(self, proj: Projectile):
        self.projectiles.append(proj)

    def spawn_explosion(self, position: Vec3, damage: float, color_rgba=None, damages_player=True):
        """Spawn an explosion at the given position."""
        from code.entity.explosion import Explosion
        from code.sound import play_sound
        play_sound("entity/explosion", volume=0.9)
        exp = Explosion(position, damage, self, color_rgba, damages_player)
        self.explosions.append(exp)
        return exp

    # ---------------------------------------------------------------- #

    def update(self, dt: float, player_pos: Vec3 = None):
        if player_pos is not None:
            cull_dist_sq = (DETAIL_RADIUS * CHUNK_SIZE * 2.5) ** 2
            alive_ents = []
            for e in self.entities:
                # Skip entities that have already been destroyed
                if e.root is None:
                    continue

                dx = e.root.x - player_pos.x
                dz = e.root.z - player_pos.z
                if (dx*dx + dz*dz) > cull_dist_sq:
                    e.dead = True
                    e.destroy()
                else:
                    alive_ents.append(e)
            self.entities = alive_ents

        # Tick entities
        for e in self.entities:
            if e.root is None:
                continue
            e.update(dt)

        # Cull dead entities
        alive_ents = []
        for e in self.entities:
            if e.dead or e.root is None:
                if e.root is not None:
                    e.destroy()
            else:
                alive_ents.append(e)
        self.entities = alive_ents

        # Update projectiles
        alive = []
        for p in self.projectiles:
            p.update(dt)
            if not p.dead:
                alive.append(p)
        self.projectiles = alive

        # -- Tick and cull dead soul orbs ----------------------------------
        alive_orbs = []
        for orb in self.soul_orbs:
            orb.update(dt)
            if not orb.dead:
                alive_orbs.append(orb)
        self.soul_orbs = alive_orbs

        # -- Tick and cull dead explosions ---------------------------------
        alive_explosions = []
        for exp in self.explosions:
            exp.update(dt)
            if not exp.dead:
                alive_explosions.append(exp)
        self.explosions = alive_explosions


class EntitySpawner:
    """
    Handles random and manual entity spawning around the world.
    Call set_player(player) after the player is created.
    """

    def __init__(self, entity_manager, world):
        self.entity_manager  = entity_manager
        self.world           = world
        self._player         = None
        self._player_stats   = None 

        # -- Spawn interval, seconds between each automatic spawn attempt --
        self.spawn_interval  = 10.0
        self._spawn_timer    = 0.0

        # -- Max entities that this spawner is allowed to have alive at once -
        self.max_spawned_entities = 5

        # -- Track only entities spawned by THIS spawner (not manual summons) -
        self._spawned_entities: list[EntityAI] = []

        # -- Spawn just outside DETAIL_RADIUS * CHUNK_SIZE * 1.75 --
        # so entities never appear right next to the player
        self.spawn_distance = DETAIL_RADIUS * CHUNK_SIZE * 1.75

        # -- Weighted spawn table -------------------------------------------
        # Each entry: (entity_type, weight)
        # Higher weight = picked more often during random spawns
        self._spawn_table = [
            ("skeleton", 4),
            ("slime",    4),
            ("zombie",   2),
            ("beehive",  1),
            ("wizard",   1),
        ]

    def set_player(self, player):
        """Call this once after the player is created."""
        self._player = player

    def get_player(self):
        return self._player

    def set_player_stats(self, player_stats):
        """Call once after player_stats is created."""
        self._player_stats = player_stats

    def _damage_player(self, amount: float):
        """Deal damage to the player if player_stats is set."""
        if self._player_stats is not None:
            self._player_stats.take_damage(amount)
    
    # ------------------------------------------------------------------ #

    def summon(self, entity_type: str, position: Vec3 = None,
               gravity: float = -20.0, max_lifetime: float = 0.0) -> EntityAI:
        """
        Manually summon a specific entity type at a given position.
        If no position is given, spawns near the player.

        entity_type options:
            "skeleton", "zombie", "slime", "deer", "wizard", "bee", "beehive"
        """
        if position is None:
            position = self._random_position_near_player()
        return self._spawn_entity(entity_type, position,
                                  gravity=gravity, max_lifetime=max_lifetime)

    # ------------------------------------------------------------------ #

    def update(self, dt):
        """Call every frame to handle automatic world spawning."""
        if self._player is None:
            return

        # Purge entities that are either dead OR no longer tracked by the manager
        # This catches entities culled by EntityManager's distance check
        self._spawned_entities = [
            e for e in self._spawned_entities
            if not e.dead and e in self.entity_manager.entities
        ]

        # Don't spawn if we've already hit our personal cap
        if len(self._spawned_entities) >= self.max_spawned_entities:
            return

        self._spawn_timer += dt
        if self._spawn_timer < self.spawn_interval:
            return

        self._spawn_timer = 0.0

        entity_type = self._weighted_random()
        position    = self._random_position_near_player()

        if position is not None:
            spawned = self._spawn_entity(entity_type, position)
            self._spawned_entities.append(spawned)

    # ------------------------------------------------------------------ #

    def _weighted_random(self) -> str:
        total      = sum(w for _, w in self._spawn_table)
        roll       = random.uniform(0, total)
        cumulative = 0
        for entity_type, weight in self._spawn_table:
            cumulative += weight
            if roll <= cumulative:
                return entity_type
        return self._spawn_table[0][0]

    def _random_position_near_player(self) -> Vec3 | None:
        if self._player is None:
            return None

        p = self._player


        # Small random variance so they don't all spawn at the exact same radius
        distance_min = self.spawn_distance * 0.90
        distance_max = self.spawn_distance * 1.10

        for _ in range(8):
            angle          = random.uniform(0, math.pi * 2)
            dist           = random.uniform(distance_min, distance_max)
            spawn_x        = p.x + math.cos(angle) * dist
            spawn_z        = p.z + math.sin(angle) * dist
            biome          = self.world.get_biome(spawn_x, spawn_z)
            terrain_height = self.world.get_height(spawn_x, spawn_z, biome)

            if biome == OCEAN:
                continue

            return Vec3(spawn_x, terrain_height + 1.0, spawn_z)

        return None
    
    def _setup_bee(self, bee):
        bee.add_task(TaskMeleeAttack(self.get_player, attack_range=1.2,
                                     cooldown=0.8, damage=5.0,
                                     on_hit=lambda t: self._damage_player(5.0),
                                     die_on_hit=True))
        bee.add_task(TaskChaseTarget(self.get_player, speed=8.0,
                                     trigger_range=30.0, stop_range=1.0,
                                     airborne=True))
        bee.add_task(TaskWander(speed=3.0, change_interval=2.0))

    def _spawn_entity(self, entity_type: str, position: Vec3,
                      gravity: float = -20.0, max_lifetime: float = 0.0) -> EntityAI:

        gp = self.get_player   # shorthand, pass the method, not the result

        if entity_type == "skeleton":
            e = self.entity_manager.spawn(position, spec=spec_skeleton(),
                                          gravity=gravity, max_lifetime=max_lifetime)
            e.add_task(TaskMeleeAttack(gp, attack_range=2.0, cooldown=1.2, damage=15.0,on_hit=lambda t: self._damage_player(15.0)))
            e.add_task(TaskChaseTarget(gp, speed=5.0, trigger_range=40.0))
            e.add_task(TaskWander(speed=2.0))

        elif entity_type == "zombie":
            e = self.entity_manager.spawn(position, spec=spec_zombie(),
                                          gravity=gravity, max_lifetime=max_lifetime)
            e.add_task(TaskMeleeAttack(gp, attack_range=2.8, cooldown=1.8, damage=20.0,on_hit=lambda t: self._damage_player(15.0)))
            e.add_task(TaskChaseTarget(gp, speed=2.2, trigger_range=40.0))
            e.add_task(TaskWander(speed=1.2, change_interval=5.0))

        elif entity_type == "slime":
            e = self.entity_manager.spawn(position, spec=spec_slime(),
                                          gravity=gravity, max_lifetime=max_lifetime)
            e.add_task(TaskRangedAttack(gp, attack_range=14.0, cooldown=2.5,
                                        projectile_speed=16.0, projectile_damage=8.0,
                                        projectile_color=color.rgba(0.2, 0.9, 0.3, 1),
                                        arc_height=0.15,
                                        on_projectile_spawn=self.entity_manager.register_projectile,
                                        damages_player      = True,
                                        get_player_fn       = gp, ))
            e.add_task(TaskChaseTarget(gp, speed=4.0, trigger_range=16.0, stop_range=10.0))
            e.add_task(TaskWander(speed=1.5))

        elif entity_type == "wizard":
            e = self.entity_manager.spawn(position, spec=spec_wizard(),
                                          gravity=gravity, max_lifetime=max_lifetime)
            e.add_task(TaskRangedAttack(gp, attack_range=22.0, cooldown=3.0,
                                        projectile_speed=16.0, projectile_damage=12.0,
                                        projectile_color=color.rgba(1.0, 0.25, 0.02, 1),
                                        projectile_scale=1.2, arc_height=0.005,
                                        on_projectile_spawn=self.entity_manager.register_projectile,
                                        damages_player      = True,
                                        get_player_fn       = gp, 
                                        # Wizard fireballs also explode on impact
                                        on_terrain_hit      = lambda pos: self.entity_manager.spawn_explosion(
                                            pos, 8.0, color_rgba=color.rgba(0.8, 0.15, 0.80, 1.0),
                                            damages_player = True,
                                        ),
                                        ))
            e.add_task(TaskWander(speed=0.0, change_interval=999))

        elif entity_type == "beehive":
            e = self.entity_manager.spawn(position, spec=spec_beehive(),
                                          gravity=gravity, max_lifetime=max_lifetime)
            e.add_task(TaskWander(speed=0.0, change_interval=999))
            e.add_task(TaskSpawnMinions(
                entity_manager  = self.entity_manager,
                spec_fn         = spec_bee,
                setup_fn        = self._setup_bee,
                spawn_interval  = 6.0,
                max_alive       = 6,
                spawn_radius    = 1.5,
                spawn_height    = 1.0,
                minion_gravity  = 0.0,
                minion_lifetime = 45.0,
            ))

        elif entity_type == "bee":
            e = self.entity_manager.spawn(position, spec=spec_bee(),
                                          gravity=0.0, max_lifetime=max_lifetime)
            self._setup_bee(e)

        else:
            print(f"EntitySpawner: unknown entity type '{entity_type}'")

        return e