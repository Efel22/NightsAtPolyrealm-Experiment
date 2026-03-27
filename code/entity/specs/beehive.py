import math
import random

def spec_beehive() -> dict:
    """
    Bee Hive, optimised.

    A single animated pivot ("hive_body") is the parent of all five
    band cubes and the entrance hole.  Animating only that one pivot
    swings the entire hive body together as a unit, exactly like a
    hive hanging from a branch, while the pegs remain static.

    Animated parts: 1  (was 8)
    Static mesh parts baked: 7  (pegs + all bands + hole)
    """
    honey  = (0.85, 0.58, 0.08, 1)
    dark   = (0.32, 0.18, 0.04, 1)
    hole_c = (0.06, 0.04, 0.02, 1)
    branch = (0.38, 0.24, 0.10, 1)

    # hive_body sways as a single unit, all child parts follow automatically
    hive_sway  = lambda t: (0, 0, math.sin(t * 1.8) * 4.5)
    hive_shake = lambda t: (0, 0, math.sin(t * 18.0) * 14.0)

    return {
        "health": 100.0,
        "xp_value": 100,
        "attack_duration": 0.5,
        "parts": [
            # -- Static pegs (bake into merged mesh) ------------------
            {"name": "peg_l",    "parent": None,        "shape": "cube",
             "color": branch,    "scale": (0.80, 0.22, 0.22),
             "position": (-0.55, 3.60, 0), "rotation": (0, 0, 0)},
            {"name": "peg_r",    "parent": None,        "shape": "cube",
             "color": branch,    "scale": (0.80, 0.22, 0.22),
             "position": ( 0.55, 3.60, 0), "rotation": (0, 0, 0)},

            # -- Animated pivot, invisible, swings the whole body -----
            # Positioned at the hive's visual centre of mass (y≈2.0)
            # so the sway looks like it's hanging from the pegs.
            {"name": "hive_body","parent": None,        "shape": "cube",
             "color": (0,0,0,0), "scale": (1, 1, 1),
             "position": (0, 2.00, 0), "rotation": (0, 0, 0)},

            # -- Hive bands, children of hive_body -------------------
            # Positions are LOCAL to hive_body (subtract hive_body.position)
            # band0 world y=3.14 -> local y = 3.14-2.00 = +1.14
            {"name": "band0",    "parent": "hive_body", "shape": "cube",
             "color": dark,      "scale": (0.90, 0.52, 0.80),
             "position": (0, 1.14, 0), "rotation": (0, 0, 0)},
            # band1 world y=2.56 -> local y = +0.56
            {"name": "band1",    "parent": "hive_body", "shape": "cube",
             "color": honey,     "scale": (1.20, 0.58, 1.05),
             "position": (0, 0.56, 0), "rotation": (0, 0, 0)},
            # band2 world y=1.94 -> local y = -0.06
            {"name": "band2",    "parent": "hive_body", "shape": "cube",
             "color": dark,      "scale": (1.30, 0.62, 1.12),
             "position": (0, -0.06, 0), "rotation": (0, 0, 0)},
            # band3 world y=1.33 -> local y = -0.67
            {"name": "band3",    "parent": "hive_body", "shape": "cube",
             "color": honey,     "scale": (1.18, 0.58, 1.02),
             "position": (0, -0.67, 0), "rotation": (0, 0, 0)},
            # band4 world y=0.80 -> local y = -1.20
            {"name": "band4",    "parent": "hive_body", "shape": "cube",
             "color": dark,      "scale": (0.88, 0.52, 0.78),
             "position": (0, -1.20, 0), "rotation": (0, 0, 0)},

            # Entrance hole, child of band2, local z pokes out of band2 front face
            # band2 scale.z=1.12, half=0.56 -> hole centre at local z=0.53
            {"name": "hole",     "parent": "band2",     "shape": "cube",
             "color": hole_c,    "scale": (0.38, 0.28, 0.18),
             "position": (0, -0.05, 0.53), "rotation": (0, 0, 0)},
        ],
        "animations": {
            # Only hive_body needs animating, one pivot, zero waste
            "walk": {
                "hive_body": {"rotation_offset": hive_sway},
            },
            "attack": {
                "hive_body": {"rotation_offset": hive_shake},
            },
        },
    }


# ============================================================
#  BEE ,  tiny fast creature spawned by the hive
# ============================================================

def spec_bee() -> dict:
    """
    A bee, scaled up 2x from original so it is clearly visible.
    Wings are the only animated parts; everything else bakes into
    the static mesh (double_sided=True handles any winding issues).
    die_on_hit=True in TaskMeleeAttack makes bees kamikaze.
    """
    yellow = (0.92, 0.80, 0.05, 1)
    black  = (0.08, 0.08, 0.08, 1)
    wing   = (0.88, 0.94, 1.00, 0.80)
    eye_c  = (0.05, 0.05, 0.05, 1)

    # Fast wing flap, rotate around Z axis (span axis)
    wing_flap_l = lambda t: (0, 0, math.sin(t * 18.0) * 40)
    wing_flap_r = lambda t: (0, 0, math.sin(t * 18.0 + math.pi) * 40)

    return {
        "health": 20.0,
        "xp_value": 5,
        "attack_duration": 0.20,
        "parts": [
            # All body parts at 2× original scale for visibility
            # Abdomen (rear, black)
            {"name": "abdomen",  "parent": None,      "shape": "cube",
             "color": black,      "scale": (0.60, 0.56, 0.88),
             "position": (0, 0.56, -0.56), "rotation": (0, 0, 0)},

            # Yellow stripe on abdomen
            {"name": "stripe1",  "parent": None,      "shape": "cube",
             "color": yellow,     "scale": (0.62, 0.20, 0.90),
             "position": (0, 0.62, -0.42), "rotation": (0, 0, 0)},

            # Thorax (middle, yellow), anchor for wings
            {"name": "thorax",   "parent": None,      "shape": "cube",
             "color": yellow,     "scale": (0.68, 0.60, 0.64),
             "position": (0, 0.56, 0.10), "rotation": (0, 0, 0)},

            # Black band on thorax
            {"name": "stripe2",  "parent": None,      "shape": "cube",
             "color": black,      "scale": (0.70, 0.22, 0.66),
             "position": (0, 0.56, 0.00), "rotation": (0, 0, 0)},

            # Head (yellow)
            {"name": "head",     "parent": None,      "shape": "cube",
             "color": yellow,     "scale": (0.56, 0.52, 0.52),
             "position": (0, 0.56, 0.64), "rotation": (0, 0, 0)},

            # Eyes, head front face at z = 0.64 + 0.26 = 0.90
            {"name": "eye_l",    "parent": None,      "shape": "cube",
             "color": eye_c,      "scale": (0.18, 0.18, 0.12),
             "position": (-0.22, 0.60, 0.92), "rotation": (0, 0, 0)},
            {"name": "eye_r",    "parent": None,      "shape": "cube",
             "color": eye_c,      "scale": (0.18, 0.18, 0.12),
             "position": ( 0.22, 0.60, 0.92), "rotation": (0, 0, 0)},

            # Stinger
            {"name": "stinger",  "parent": None,      "shape": "cube",
             "color": black,      "scale": (0.12, 0.12, 0.28),
             "position": (0, 0.56, -1.06), "rotation": (0, 0, 0)},

            # Wings, animated, parented to None so pivot scale = wing scale
            # Pivot position is at thorax top (y≈0.56+0.30=0.86)
            {"name": "wing_l",   "parent": None,      "shape": "cube",
             "color": wing,       "scale": (0.90, 0.06, 0.70),
             "position": (-0.70, 0.90, 0.10), "rotation": (0, 0, -15)},
            {"name": "wing_r",   "parent": None,      "shape": "cube",
             "color": wing,       "scale": (0.90, 0.06, 0.70),
             "position": ( 0.70, 0.90, 0.10), "rotation": (0, 0,  15)},
        ],
        "animations": {
            "walk": {
                "wing_l": {"rotation_offset": wing_flap_l},
                "wing_r": {"rotation_offset": wing_flap_r},
            },
            "attack": {
                "wing_l": {"rotation_offset": wing_flap_l},
                "wing_r": {"rotation_offset": wing_flap_r},
            },
        },
    }