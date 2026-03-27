from ursina import *
import math
from ursina.shaders import lit_with_shadows_shader
import threading
import queue
import random
from .impostors import *
from .meshbuilders import *
from .meshbuilders.shared import *
from .world_settings import *
from .noise import  *
from code.world.structures.structure_manager import StructureManager

class World():

    def __init__(self):
        # This is the Permutation Table for the Perlin Noise, its an image (256x256)
        _rng = random.Random(1234)      # <- local instance, not random.seed()
        self.p = list(range(256))
        _rng.shuffle(self.p)            # <- shuffle with local instance
        self.p += self.p

        self.chunks          = {}
        self.chunks_pending  = set()
        self.near_impostors  = None
        self.impostors       = {}

        self.build_queue    = queue.Queue()
        self.max_threads    = 4
        self._last_p_chunk  = (None, None)

        self._water_entity       = None
        self._water_floor_entity = None

        self._biome_cache = {}
        self.structure_manager = None # Set the Structure Manager HERE instead :D

    # ------------------------------------------------------------------ #
    #  STRUCTURES                                                         #
    # ------------------------------------------------------------------ #

    def set_struct_manager(self, world, entity_manager, get_player_fn):

        self.structure_manager = StructureManager(world, entity_manager, get_player_fn)



    # ------------------------------------------------------------------ #
    #  BIOME + HEIGHT                                                      #
    # ------------------------------------------------------------------ #

    def get_biome(self, x, z):
        key = (int(x), int(z))
        if key in self._biome_cache:
            return self._biome_cache[key]

        temp         = octave_noise(self.p, x, z,         octaves=2, scale=1/800.0)
        humidity     = octave_noise(self.p, x+500, z+500, octaves=2, scale=1/800.0)
        mountain_val = octave_noise(self.p, x+999, z+999, octaves=2, scale=1/1200.0)
        ocean_val    = octave_noise(self.p, x+1500, z+1500, octaves=2, scale=1/1000.0) 

        OCEAN_THRESHOLD = -0.25   # below this -> ocean
        BEACH_THRESHOLD = -0.20   # narrow band just outside ocean -> beach

        if ocean_val < OCEAN_THRESHOLD:
            base = OCEAN
        elif ocean_val < BEACH_THRESHOLD:
            # Narrow strip bordering the ocean -> always beach
            base = BEACH
        elif temp < -0.3:
            base = TAIGA
        elif mountain_val > 0.32 and temp > 0.0 and humidity >= 0.05:
            base = MOUNTAIN
        elif temp > 0.2:
            base = DESERT if humidity < -0.1 else PLAINS
        elif humidity > 0.25:
            base = ASPEN
        elif humidity > 0.10:
            base = FOREST
        elif humidity < 0.05:
            base = OCEAN
        else:
            base = PLAINS

        if len(self._biome_cache) > 8:
            self._biome_cache.clear()
        self._biome_cache[key] = base
        return base

    def get_height(self, x, z, biome):
        # Standard low-altitude water noise (4 units high, shifted 8 units down)
        if biome==OCEAN:    return octave_noise(self.p, x,z,octaves=2,scale=1/60.0)*4-8
        
        # Beach, low flat strip just above water, micro variation only
        if biome == BEACH:
            micro = get_noise(self.p, x / 8.0 + 777, z / 8.0 + 777)
            return max(WATER_LEVEL + 3, WATER_LEVEL + 1 + micro * 6.0)

        # Simple rolling hills with different scales and heights per biome
        if biome==DESERT:   return max(WATER_LEVEL + 2, octave_noise(self.p, x,z,octaves=2,scale=1/50.0)*6)
        if biome==TAIGA:    return max(WATER_LEVEL + 2, octave_noise(self.p, x,z,octaves=2,scale=1/55.0)*8)
        if biome==PLAINS:   return max(WATER_LEVEL + 2, octave_noise(self.p, x,z,octaves=2,scale=1/70.0)*5)
        if biome==FOREST:   return max(WATER_LEVEL + 2, octave_noise(self.p, x,z,octaves=3,scale=1/45.0)*20)
        if biome==ASPEN:    return max(WATER_LEVEL + 2, octave_noise(self.p, x,z,octaves=2,scale=1/60.0)*7)

        if biome == MOUNTAIN:
            # -------------------------------------------------
            # CONSTANTS
            # -------------------------------------------------
            MOUNTAIN_MAX_HEIGHT = 35.0

            # How fast the alpine zone shoots upward
            ALPINE_RAMP_HEIGHT = 10.0   # smaller = faster rise
            ALPINE_POWER = 6.0         # higher = sharper peaks

            # -------------------------------------------------
            # 1. BIOME MASK (controls where mountains exist)
            # -------------------------------------------------
            m_val = octave_noise(
                self.p,
                x + 999,
                z + 999,
                octaves=2,
                scale=1 / 1200.0
            )

            # -------------------------------------------------
            # 2. BIOME INTENSITY (smooth edge -> center)
            # -------------------------------------------------
            raw_dist = max(0.0, m_val - 0.32)
            intensity = min(1.0, (raw_dist * 3.0) ** 0.7)

            # -------------------------------------------------
            # 3. BASE MOUNTAIN SHAPE (normal slopes)
            # -------------------------------------------------
            base = octave_noise(
                self.p,
                x,
                z,
                octaves=4,
                scale=1 / 60.0,
                persistence=0.5
            )

            peak_detail = (
                octave_noise(self.p, x + 333, z + 333, octaves=3, scale=1 / 20.0)
                * 8.0
            )

            mountain_shape = (base * 30.0) + 50.0 + peak_detail

            # -------------------------------------------------
            # 4. NORMAL HEIGHT BLENDING (pre‑snow)
            # -------------------------------------------------
            base_height = (
                (5.0 * (1.0 - intensity)) +
                (mountain_shape * intensity)
            )

            # -------------------------------------------------
            # 5. ALPINE ACCELERATION ZONE (POST‑SNOW)
            # -------------------------------------------------
            if base_height > MOUNTAIN_SNOW_HEIGHT:
                # Local ramp above snow height (NOT global)
                t = (base_height - MOUNTAIN_SNOW_HEIGHT) / ALPINE_RAMP_HEIGHT
                t = max(0.0, min(t, 1.0))

                # Aggressive curve -> fast vertical growth
                alpine_curve = t ** ALPINE_POWER

                # Extra height added ON TOP of the slope
                alpine_extra = alpine_curve * (
                    MOUNTAIN_MAX_HEIGHT - MOUNTAIN_SNOW_HEIGHT
                )

                base_height += alpine_extra

                # Extra crunchy detail near the peaks only
                alpine_noise = (
                    octave_noise(self.p, x + 777, z + 777, octaves=2, scale=1 / 15.0)
                    * 4.0
                )
                base_height += alpine_noise * alpine_curve

            # -------------------------------------------------
            # 6. HARD SAFETY CAP + FLOOR
            # -------------------------------------------------
            base_height = min(base_height, MOUNTAIN_MAX_HEIGHT)

            return max(base_height, random.uniform(0.5, 2.5))
   
        return 0.0

    def top_color(self, biome, height):
        # MOUNTAIN: Mixes Gray Rock with White Snow
        if biome == MOUNTAIN:
            # 1. Simple Threshold Check
            if height >= MOUNTAIN_SNOW_HEIGHT:
                # It's Snow! (Crisp White)
                return BIOME_TOP_COLOR[MOUNTAIN_SNOW]
            else:
                # It's Grass! (The Green/Teal you wanted)
                return BIOME_TOP_COLOR[MOUNTAIN]
        
        # DEFAULT
        return BIOME_TOP_COLOR[biome] 

    def get_ground_y(self, x, z):
        hit = raycast(
            origin    = Vec3(x, 100, z),
            direction = Vec3(0, -1, 0),
            distance  = 200,
            ignore    = []
        )
        if hit.hit:
            return hit.world_point.y
        biome = self.get_biome(x, z)
        return max(math.floor(self.get_height(x, z, biome)), WATER_LEVEL)

    # ------------------------------------------------------------------ #
    #  CHUNK GENERATION  (background thread)                              #
    # ------------------------------------------------------------------ #

    def generate_chunk(self, start_x, start_z):
        """Full-detail chunk: terrain + vegetation + grass (3×3 only)."""
        chunk_seed = (start_x * 73856093) ^ (start_z * 19349663) ^ 1234
        rng = random.Random(chunk_seed)

        cs  = CHUNK_SIZE
        bot = float(SLAB_BOTTOM)

        cx    = start_x + cs//2
        cz    = start_z + cs//2
        biome = self.get_biome(cx, cz)
        height = math.floor(self.get_height(cx, cz, biome))

        # Determine if the chunk has a structure
        _has_structure = False
        chunk_x = start_x // CHUNK_SIZE
        chunk_z = start_z // CHUNK_SIZE
        _has_structure = self.structure_manager.will_have_structure(chunk_x, chunk_z)


        # Do not generate Ocean 'chunks' (they're not needed)
        if biome == OCEAN:
            return None

        # Only apply roughness variation to land biomes, beach height is
        # already controlled precisely in get_height()
        if biome not in (OCEAN, BEACH):
            roughness = (get_noise(self.p, cx/400.0+333, cz/400.0+333) + 1.0) * 0.5
            max_vary  = 3.0 + roughness * 10.0
            micro     = get_noise(self.p, cx/8.0+777, cz/8.0+777)
            height   += math.floor(micro * max_vary)

        # Beach is already at the right height, only clamp other land biomes
        if biome not in (OCEAN, BEACH):
            height = max(height, WATER_LEVEL + 3)

        top=float(height); 
        tc=self.top_color(biome,height) # CHUNK_TOP COLOR

        # DETERMINE SIDE COLORS
        base_sc = darken_tuple(BIOME_SIDE_COLOR[biome], rng.uniform(0.85,1.0))
        if biome == MOUNTAIN and height >= MOUNTAIN_SNOW_HEIGHT:
            base_sc = darken_tuple(BIOME_SIDE_COLOR[MOUNTAIN_SNOW], rng.uniform(0.75,1.0))
            if height >= MOUNTAIN_PEAK_HEIGHT:
                tc = darken_tuple(base_sc, rng.uniform(1.2,1.35))

        # Shades depending on whether they're facing north or west!
        def shade(c,f): return (c[0]*f,c[1]*f,c[2]*f)
        sc_south=shade(base_sc,0.90); sc_north=shade(base_sc,0.60)
        sc_west=shade(base_sc,0.85);  sc_east=shade(base_sc,0.65)

        # Add a Random Tint to the TOP_COLOR (ONLY APPLIES TO 'NO_TOP_COLOR_VARIATION_BIOMES')
        tc = darken_tuple(tc, rng.uniform(0.8,1.0)) 

        verts=[]; tris=[]; vcols=[]; idx=0

        def add_quad(p0,p1,p2,p3,c):
            nonlocal idx
            verts.extend([p0,p1,p2,p3])
            col=color.rgba(c[0],c[1],c[2],1)
            vcols.extend([col,col,col,col])
            tris.append((idx,idx+1,idx+2,idx+3))
            idx+=4

        def add_quad_top(c, ao=0.22):
            nonlocal idx
            corners=[(start_x,start_z),(start_x+cs,start_z),
                     (start_x+cs,start_z+cs),(start_x,start_z+cs)]
            verts.extend([(0,top,0),(cs,top,0),(cs,top,cs),(0,top,cs)])
            for (wx2,wz2) in corners:
                nb_cols=[]
                for dx,dz in [(0,0),(-cs,0),(0,-cs),(-cs,-cs)]:
                    nb=self.get_biome(wx2+dx,wz2+dz)
                    nh=self.get_height(wx2+dx,wz2+dz,nb)
                    if nb in NO_BLEND_BIOMES:
                        nb_cols.append(c); continue
                    if biome==MOUNTAIN and nb!=MOUNTAIN:
                        nb_cols.append(c); continue
                    if biome in NO_BLEND_BIOMES:
                        nb_cols.append(c); continue
                    nb_cols.append(self.top_color(nb,nh))
                r=sum(n[0] for n in nb_cols)/4
                g=sum(n[1] for n in nb_cols)/4
                b=sum(n[2] for n in nb_cols)/4
                ex=1.0-abs(((wx2-start_x)/cs)-0.5)*2
                ez=1.0-abs(((wz2-start_z)/cs)-0.5)*2
                f=1.0-ao*(1.0-ex*ez)
                vcols.append(color.rgba(r*f,g*f,b*f,1))
            tris.append((idx,idx+1,idx+2,idx+3))
            idx+=4

        add_quad_top(tc)
        add_quad((cs,top,0),(0,top,0),(0,bot,0),(cs,bot,0),    sc_south)
        add_quad((0,top,cs),(cs,top,cs),(cs,bot,cs),(0,bot,cs), sc_north)
        add_quad((0,top,0),(0,top,cs),(0,bot,cs),(0,bot,0),    sc_west)
        add_quad((cs,top,cs),(cs,top,0),(cs,bot,0),(cs,bot,cs), sc_east)
        add_quad((0,bot,0),(cs,bot,0),(cs,bot,cs),(0,bot,cs),  BIOME_SIDE_COLOR[biome]) # Bottom Color btw, just make it so its the same as side's

        # Does the CHUNK have a Peak Mesh? (Used for Mountains ONLY)
        _is_peak_chunk = (biome == MOUNTAIN and height >= MOUNTAIN_PEAK_HEIGHT)

        if height >= WATER_LEVEL and not _is_peak_chunk and not _has_structure:
            for _ in range(3):
                vx=rng.randint(2,cs-3); vz=rng.randint(2,cs-3)
                wx=start_x+vx+0.5; wz=start_z+vz+0.5
                lx=vx+0.5;         lz=vz+0.5
                hh=(self.p[int(wx)&255]+self.p[int(wz)&255])&255
                t=hh/255.0; ht=max(0.0,min(1.0,height/20.0))

                if biome==BEACH:      effective_boulder=BOULDER_DENSITY*10.0
                elif biome==DESERT:   effective_boulder=BOULDER_DENSITY*4.0
                elif biome==MOUNTAIN: effective_boulder=BOULDER_DENSITY*5.0
                elif biome==TAIGA:    effective_boulder=BOULDER_DENSITY*2.0
                else:                 effective_boulder=BOULDER_DENSITY

                # ── Decoration Spawning ───────────────────────────────────────────────────
                # Each cell rolls a random number t (0.0–1.0).
                # High t  -> spawn a boulder (boulders are rare, controlled by effective_boulder)
                # Low t   -> spawn a tree/cactus (controlled by BIOME_TREE_DENS per biome)

                if t > (1.0 - effective_boulder):
                    # Boulder, spawns when t is in the top % (rare)
                    idx = build_boulder_mesh(verts, tris, vcols, idx, lx, height, lz, rng)

                elif biome == DESERT and t < BIOME_TREE_DENS[biome]:
                    # Cactus, spawns in desert when t is low enough
                    idx = build_cactus_mesh(verts, tris, vcols, idx, lx, height, lz, rng)

                elif biome == PLAINS and t < BIOME_TREE_DENS[biome]:
                    # Generic tree for plains
                    idx = build_plains_tree_mesh(verts, tris, vcols, idx, lx, height, lz, rng)

                elif biome == FOREST and t < BIOME_TREE_DENS[biome]:
                    # Generic tree for forest (slightly taller/denser than plains)
                    idx = build_forest_tree_mesh(verts, tris, vcols, idx, lx, height, lz, rng)

                elif biome == TAIGA and t < BIOME_TREE_DENS[biome]:
                    # Pine tree for taiga
                    idx = build_pine_mesh(verts, tris, vcols, idx, lx, height, lz, ht, rng)

                elif biome == MOUNTAIN and t < BIOME_TREE_DENS[biome]:
                    if height >= MOUNTAIN_SNOW_HEIGHT:
                        # Snowy pine above the snow line
                        idx = build_snowy_pine_mesh(verts, tris, vcols, idx, lx, height, lz, rng)
                    else:
                        # Regular pine below the snow line
                        idx = build_pine_mesh(verts, tris, vcols, idx, lx, height, lz, ht, rng)

                elif biome == ASPEN and t < BIOME_TREE_DENS[biome]:
                    # Aspen tree
                    idx = build_aspen_mesh(verts, tris, vcols, idx, lx, height, lz, rng)

        # Peak Chunk logic: Create the Peak Mesh
        if _is_peak_chunk:
            pv=[]; pt=[]; pc=[]; pi=0
            pi=build_peak_mesh(pv,pt,pc,pi, start_x,start_z, top, cs, rng)
            base_vi=len(verts)
            for (px,py,pz) in pv: verts.append((px-start_x,py,pz-start_z))
            for pfc in pc: vcols.append(pfc)
            for (i0,i1,i2,i3) in pt: tris.append((base_vi+i0,base_vi+i1,base_vi+i2,base_vi+i3))

        # --- SET GRASS COLOR (not GROUND) ---  
        # Which biome and what color?
        base_grass = BIOME_GRASS_COLOR[biome]
        if biome == MOUNTAIN and height >= MOUNTAIN_SNOW_HEIGHT: base_grass = BIOME_GRASS_COLOR[MOUNTAIN_SNOW]

        # Skip grass too if a structure owns this chunk
        if not _has_structure and not _is_peak_chunk:
            # How much grass? (Depends on the biome)
            num_grass=int(cs*cs*BIOME_GRASS_DENS[biome]* 0.3)
            
            # Generate the grass 
            for _ in range(num_grass):
                vx=rng.uniform(0.5,cs-0.5); vz=rng.uniform(0.5,cs-0.5)
                gc_col=vary_col(base_grass[0],base_grass[1],base_grass[2],amount=0.1)

                if not _is_peak_chunk:
                    idx=build_grass_mesh(verts,tris,vcols,idx, vx,height,vz, gc_col, biome, rng)

        return verts,tris,vcols, start_x,start_z, biome

    # ------------------------------------------------------------------ #
    #  IMPOSTOR GENERATION                                                #
    # ------------------------------------------------------------------ #

    def _rebuild_near_impostors(self, p_x, p_z):
        """
        Builds a single merged entity covering the near-ring chunk slots
        (Chebyshev distance DETAIL_RADIUS+1 to NEAR_IMPOSTOR_RADIUS).
        Each slot uses the same biome impostor builder as the large 5x5 grid,
        just at chunk_size scale instead of 5*chunk_size scale.
        """
        # Destroy the old near-ring entity before rebuilding
        if self.near_impostors is not None:
            destroy(self.near_impostors)
            self.near_impostors = None
 
        cs         = CHUNK_SIZE
        slab_bot   = float(SLAB_BOTTOM)
        margin     = 0.065   # tiny inset to avoid z-fighting with detail chunks
 
        

        # One chunk slot size after inset
        slot_size  = cs - margin * 2
 
        # Accumulated geometry for the single merged entity
        all_verts = []; all_tris = []; all_cols = []
 
        for chunk_z in range(p_z - NEAR_IMPOSTOR_RADIUS, p_z + NEAR_IMPOSTOR_RADIUS + 1):
            for chunk_x in range(p_x - NEAR_IMPOSTOR_RADIUS, p_x + NEAR_IMPOSTOR_RADIUS + 1):
 
                # Skip slots that are inside the real detail chunk zone
                if max(abs(chunk_x - p_x), abs(chunk_z - p_z)) <= DETAIL_RADIUS:
                    continue
 
                # Use a deterministic rng per slot so it looks the same every rebuild
                slot_rng = random.Random(
                    (chunk_x * 73856093) ^ (chunk_z * 19349663) ^ 9999
                )

                # World-space origin of this chunk slot
                slot_wx = chunk_x * cs
                slot_wz = chunk_z * cs
 
                _has_structure = False
                _has_structure = self.structure_manager.will_have_structure(chunk_x, chunk_z)

                # Sample biome and height at the slot centre
                centre_wx = slot_wx + cs // 2
                centre_wz = slot_wz + cs // 2

                # Get the biome correctly (now includes the beoch) and the average height
                biome = self.get_biome(centre_wx, centre_wz)
                # avg_h = self.get_height(centre_wx, centre_wz, biome)
                avg_h = math.floor(self.get_height(centre_wx, centre_wz, biome))

                # With:
                if biome not in (OCEAN, BEACH):
                    avg_h = max(avg_h, WATER_LEVEL + 1)
 
                # Call the same biome impostor builder used by the large 5x5 grid,
                # but pass slot_size (one chunk) instead of full (five chunks).                
                if biome == OCEAN:
                    v, t, c = build_ocean_impostor(slot_size, float(avg_h), slot_rng, slab_bot)
                elif biome == MOUNTAIN:
                    v, t, c = build_mountain_impostor(slot_size, float(avg_h), slot_rng, slab_bot)
                elif biome == DESERT:
                    v, t, c = build_desert_impostor(slot_size, float(avg_h), slot_rng, slab_bot)
                elif biome == FOREST:
                    v, t, c = build_forest_impostor(slot_size, float(avg_h), slot_rng, slab_bot)
                elif biome == TAIGA:
                    v, t, c = build_taiga_impostor(slot_size, float(avg_h), slot_rng, slab_bot)
                elif biome == ASPEN:
                    v, t, c = build_aspen_impostor(slot_size, float(avg_h), slot_rng, slab_bot)
                elif biome == BEACH:
                    v, t, c = build_beach_impostor(slot_size, float(avg_h), slot_rng, slab_bot)
                elif biome == PLAINS:
                    v, t, c = build_plains_impostor(slot_size, float(avg_h), slot_rng, slab_bot)
 
                # The impostor builder uses local coords (origin = 0,0).
                # Offset verts into world space so they land in the right slot.
                offset_x = slot_wx + margin
                offset_z = slot_wz + margin
                base_idx = len(all_verts)
 
                for (vx, vy, vz) in v:
                    all_verts.append((vx + offset_x, vy, vz + offset_z))
                for col in c:
                    all_cols.append(col)
                for face in t:
                    all_tris.append(tuple(fi + base_idx for fi in face))
 
                # --- SET GRASS COLOR (not GROUND) ---  
                # Which biome and what color?
                base_grass = BIOME_GRASS_COLOR[biome]
                if biome == MOUNTAIN and avg_h >= MOUNTAIN_SNOW_HEIGHT: base_grass = BIOME_GRASS_COLOR[MOUNTAIN_SNOW]

                # grass_idx tracks the running vertex index into all_verts
                # it must start at the CURRENT length, not base_idx from before
                grass_idx = len(all_verts)

                # How much grass? (Depends on the biome)
                num_grass=int(cs*cs*BIOME_GRASS_DENS[biome] * 0.025)

                if avg_h >= MOUNTAIN_PEAK_HEIGHT or _has_structure:
                    continue

                # Generate the grass 
                for _ in range(num_grass):
                    vx = slot_rng.uniform(0.5, cs - 0.5)
                    vz = slot_rng.uniform(0.5, cs - 0.5)
                    gc_col = vary_col(base_grass[0], base_grass[1], base_grass[2], amount=0.1)

                    # build_grass_mesh appends directly to all_verts/all_tris/all_cols
                    # and returns the updated idx, we must keep updating grass_idx
                    grass_idx = build_grass_mesh(
                        all_verts, all_tris, all_cols, grass_idx,
                        vx + offset_x, float(avg_h), vz + offset_z,
                        gc_col, biome, slot_rng, 1 # Detail level is 1 (JUST grass)
                    )

                if biome not in NO_GRASS_BIOMES or biome == BEACH:
                    bx = slot_rng.uniform(0.5, cs - 0.5)
                    bz = slot_rng.uniform(0.5, cs - 0.5)
                    grass_idx = build_boulder_mesh(
                        all_verts, all_tris, all_cols,
                        grass_idx, bx + offset_x, float(avg_h), bz + offset_z,
                        slot_rng, 0 # Detail value ('0') is 0 so its less detailed 
                    )

        if not all_verts:
            return
 
        # Merge everything into one entity, one draw call for the whole ring
        self.near_impostors = Entity(
            model        = Mesh(vertices=all_verts, triangles=all_tris,
                                colors=all_cols, mode='triangle'),
            double_sided = True,
            shader       = lit_with_shadows_shader,
        )

    # Generates the Large Impostor Chunks (5x5)
    def generate_impostor(self, ix, iz):
        
        cs     = CHUNK_SIZE
        full   = cs * 5
        margin = 0.05
        size   = full - margin * 2

        rng = random.Random((ix * 73856093) ^ (iz * 19349663) ^ 5555)

        total_h = 0.0
        land_h  = 0.0
        land_samples  = 0
        ocean_samples = 0
        has_mountain  = False
        biome_votes   = {}

        for dz in range(5):
            for dx in range(5):
                sx = ix * full + (dx + 0.5) * cs
                sz = iz * full + (dz + 0.5) * cs
                biome = self.get_biome(sx, sz)
                h     = self.get_height(sx, sz, biome)
                biome_votes[biome] = biome_votes.get(biome, 0) + 1
                if biome == MOUNTAIN:
                    has_mountain = True
                if biome == OCEAN:
                    ocean_samples += 1
                    total_h += h
                else:
                    land_h  += h
                    total_h += h
                    land_samples += 1

        all_ocean = (land_samples == 0)
        avg_h = (total_h / 25) if all_ocean else (land_h / land_samples)

        if has_mountain:
            non_mtn_h = []
            for dz in range(5):
                for dx in range(5):
                    sx = ix * full + (dx + 0.5) * cs
                    sz = iz * full + (dz + 0.5) * cs
                    b  = self.get_biome(sx, sz)
                    if b not in (MOUNTAIN, OCEAN):
                        non_mtn_h.append(self.get_height(sx, sz, b))
            ground_h = (sum(non_mtn_h) / len(non_mtn_h)) if non_mtn_h else 2.0
            avg_h = min(ground_h, 8.0)

        dominant = max(
            (b for b in biome_votes if b != OCEAN),
            key=lambda b: biome_votes[b],
            default=OCEAN
        )


        if all_ocean:
            verts,tris,cols = build_ocean_impostor(size, float(avg_h), rng, float(SLAB_BOTTOM))
        elif dominant == MOUNTAIN:
            verts,tris,cols = build_mountain_impostor(size, float(avg_h), rng, float(SLAB_BOTTOM))
        elif dominant == DESERT:
            verts,tris,cols = build_desert_impostor(size, float(avg_h), rng, float(SLAB_BOTTOM))
        elif dominant == FOREST:
            verts,tris,cols = build_forest_impostor(size, float(avg_h), rng, float(SLAB_BOTTOM))
        elif dominant == TAIGA:
            verts,tris,cols = build_taiga_impostor(size, float(avg_h), rng, float(SLAB_BOTTOM))
        elif dominant == ASPEN:
            verts,tris,cols = build_aspen_impostor(size, float(avg_h), rng, float(SLAB_BOTTOM))
        elif dominant == BEACH:
            verts,tris,cols = build_beach_impostor(size, float(avg_h), rng, float(SLAB_BOTTOM))
        else:
            verts,tris,cols = build_plains_impostor(size, float(avg_h), rng, float(SLAB_BOTTOM))

        wx = ix * full + margin
        wz = iz * full + margin

        return Entity(
            model        = Mesh(vertices=verts, triangles=tris,
                                colors=cols, mode='triangle'),
            position     = (wx, 0, wz),
            double_sided = True,
            shader       = lit_with_shadows_shader,
            
        )

    # ------------------------------------------------------------------ #
    #  THREAD WORKER                                                       #
    # ------------------------------------------------------------------ #

    def _generate_chunk_thread(self, chunk_x, chunk_z):
        data = self.generate_chunk(chunk_x*CHUNK_SIZE, chunk_z*CHUNK_SIZE)
        self.build_queue.put((chunk_x, chunk_z, data))

    # ------------------------------------------------------------------ #
    #  WATER PLANE                                                         #
    # ------------------------------------------------------------------ #

    def _rebuild_water(self, p_x, p_z):
        """
        Always-present water surface + floor.
        15 chunks half-width in each direction. No ocean check needed.
        """
        if self._water_entity:
            destroy(self._water_entity)
            self._water_entity = None
        if self._water_floor_entity:
            destroy(self._water_floor_entity)
            self._water_floor_entity = None

        cs   = CHUNK_SIZE
        half = 25 * cs
        wl   = float(WATER_LEVEL + 0.05)
        ox   = p_x * cs - half
        oz   = p_z * cs - half
        size = half * 2

        # Surface, less transparent than before
        self._water_entity = Entity(
            model=Mesh(
                vertices=[(ox,wl,oz),(ox+size,wl,oz),
                          (ox+size,wl,oz+size),(ox,wl,oz+size)],
                triangles=[(0,1,2,3)], mode='triangle'),
            color=color.rgba(0.055, 0.220, 0.420, 0.96),
            double_sided=True,
            shader=lit_with_shadows_shader,
            
        )

        # Floor, same footprint as surface, shallow depth
        floor_depth = 20.0   # not too deep
        floor_y     = wl - floor_depth
        self._water_floor_entity = Entity(
            model='cube',
            color=color.rgba(0.020, 0.060, 0.130, 1),
            scale=(size, floor_depth, size),
            position=(ox + size/2, floor_y - floor_depth/2, oz + size/2),
            
        )

    # ------------------------------------------------------------------ #
    #  WORLD UPDATE                                                        #
    # ------------------------------------------------------------------ #

    def update_world(self, player):

        

        p_x = math.floor(player.x / CHUNK_SIZE)
        p_z = math.floor(player.z / CHUNK_SIZE)

        self.structure_manager.update(p_x, p_z, DETAIL_RADIUS, CHUNK_SIZE)

        if (p_x, p_z) != self._last_p_chunk:
            self._last_p_chunk = (p_x, p_z)
            self._rebuild_water(p_x, p_z)

            # ── Real chunks, only the inner 3×3 ─────────────────────
            needed = []
            for z in range(p_z - DETAIL_RADIUS, p_z + DETAIL_RADIUS + 1):
                for x in range(p_x - DETAIL_RADIUS, p_x + DETAIL_RADIUS + 1):
                    if (x,z) not in self.chunks and (x,z) not in self.chunks_pending:
                        needed.append((abs(x-p_x)+abs(z-p_z), x, z))

            needed = sorted(needed)
            for _, x, z in needed:
                if threading.active_count() >= self.max_threads + 1: break
                self.chunks_pending.add((x, z))
                threading.Thread(
                    target=self._generate_chunk_thread,
                    args=(x, z),
                    daemon=True
                ).start()

            cs   = CHUNK_SIZE
            full = cs * 5

            # ── Near impostors ────────────────────────────────────────
            self._rebuild_near_impostors(p_x, p_z)

            # ── Large 5×5 impostor grid ───────────────────────────────
            imp_px = int(math.floor(p_x / 5))
            imp_pz = int(math.floor(p_z / 5))

            def _large_imp_overlaps(ix, iz):
                """True if this 5×5 cell overlaps the near-impostor zone."""
                cell_x0 = ix * 5; cell_x1 = ix * 5 + 4
                cell_z0 = iz * 5; cell_z1 = iz * 5 + 4
                near_x = max(cell_x0, min(cell_x1, p_x))
                near_z = max(cell_z0, min(cell_z1, p_z))
                return (abs(near_x - p_x) <= NEAR_IMPOSTOR_RADIUS - 1  and
                    abs(near_z - p_z) <= NEAR_IMPOSTOR_RADIUS - 1 )

            def _is_corner(ix, iz):
                dx = abs(ix - imp_px); dz = abs(iz - imp_pz)
                if dx == IMPOSTOR_RADIUS and dz == IMPOSTOR_RADIUS:
                    return True
                if dx == IMPOSTOR_RADIUS and dz == IMPOSTOR_RADIUS - 1:
                    return True
                if dx == IMPOSTOR_RADIUS - 1 and dz == IMPOSTOR_RADIUS:
                    return True
                return False

            def _is_ocean_cell(ix, iz):
                """Sample the centre of this impostor cell to check if ocean."""
                cx = ix * full + full // 2
                cz = iz * full + full // 2
                return self.get_biome(cx, cz) == OCEAN

            for iz in range(imp_pz - IMPOSTOR_RADIUS, imp_pz + IMPOSTOR_RADIUS + 1):
                for ix in range(imp_px - IMPOSTOR_RADIUS, imp_px + IMPOSTOR_RADIUS + 1):
                    if _is_corner(ix, iz):
                        continue
                    if _large_imp_overlaps(ix, iz):
                        continue
                    # Skip all ocean impostor cells, covered by the water entity
                    if _is_ocean_cell(ix, iz):
                        continue
                    if (ix, iz) not in self.impostors:
                        self.impostors[(ix, iz)] = self.generate_impostor(ix, iz)

            to_remove = [
                (ix2, iz2) for (ix2, iz2) in list(self.impostors)
                if (abs(ix2 - imp_px) > IMPOSTOR_RADIUS
                    or abs(iz2 - imp_pz) > IMPOSTOR_RADIUS
                    or _large_imp_overlaps(ix2, iz2)
                    or _is_corner(ix2, iz2)
                    or _is_ocean_cell(ix2, iz2))
            ]
            for k in to_remove:
                ent = self.impostors.pop(k)
                if ent is not None:
                    destroy(ent)

        # ── Consume chunk build queue ─────────────────────────────────
        chunks_consumed = 0
        while not self.build_queue.empty() and chunks_consumed < 2:
            chunk_x, chunk_z, data = self.build_queue.get()
            self.chunks_pending.discard((chunk_x, chunk_z))
            chunks_consumed += 1

            if data is None:
                self.chunks[(chunk_x,chunk_z)] = {'terrain':None,'biome':OCEAN}
            else:
                verts,tris,vcols,sx,sz,chunk_biome = data

                TERRAIN_VERTS = 24
                col_verts = verts[:TERRAIN_VERTS]
                col_tris  = tris[:6]

                terrain = Entity(
                    model=Mesh(vertices=col_verts, triangles=col_tris, mode='triangle'),
                    collider='mesh',
                    color=color.rgba(0, 0, 0, 0),
                    position=(sx, 0, sz),
                    
                )
                Entity(
                    parent=terrain,
                    model=Mesh(vertices=verts, triangles=tris, colors=vcols, mode='triangle'),
                    double_sided=True,
                    shader=lit_with_shadows_shader,
                    
                )

                self.chunks[(chunk_x,chunk_z)] = {
                    'terrain': terrain, 'biome': chunk_biome}

        # ── Despawn real chunks outside 3×3 ──────────────────────────
        to_remove = [
            coords for coords in self.chunks
            if (abs(coords[0]-p_x) > DETAIL_RADIUS or
                abs(coords[1]-p_z) > DETAIL_RADIUS)
        ]
        for coords in to_remove:
            c = self.chunks.pop(coords)
            if c['terrain']:
                for child in list(c['terrain'].children):
                    destroy(child)
                destroy(c['terrain'])

        for z in range(p_z - DETAIL_RADIUS, p_z + DETAIL_RADIUS + 1):
            for x in range(p_x - DETAIL_RADIUS, p_x + DETAIL_RADIUS + 1):
                if (x,z) in self.chunks_pending:
                    continue
                if (x,z) not in self.chunks:
                    continue


# --- World Creation ---
world = World()
from code.sound import play_sound
play_sound("music/worldtheme", volume=0.4, loop=True)