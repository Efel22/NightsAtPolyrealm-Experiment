import math
import random

def spec_zombie() -> dict:
    """
    A hulking zombie. Green head and arms, blue torso and legs.
    Arms are pre-rotated forward (~35 deg) for that classic outstretched look.
    Legs are parented to root to keep animation clean.
    Walk is a slow, heavy shamble with a deep body bob.
    Attack lurches the whole torso forward.
    """
    # Slow shamble, legs only swing ~18 deg, arms sway gently
    leg_swing     = lambda t: (math.sin(t * 3.5) * 18, 0, 0)
    leg_swing_inv = lambda t: (math.sin(t * 3.5 + math.pi) * 18, 0, 0)
    arm_sway      = lambda t: (math.sin(t * 3.5) * 8, 0, 0)
    arm_sway_inv  = lambda t: (math.sin(t * 3.5 + math.pi) * 8, 0, 0)
    # Heavy bob, torso sinks and rises slowly
    body_bob      = lambda t: (0, math.sin(t * 7.0) * 0.10, 0)
    # Attack: torso lurches forward, arms slam down
    attack_torso  = lambda t: (math.sin(min(t, 0.5) * math.pi / 0.5) * -40, 0, 0)
    attack_arm_l  = lambda t: (math.sin(min(t, 0.5) * math.pi / 0.5) * -50, 0, 0)
    attack_arm_r  = lambda t: (math.sin(min(t, 0.5) * math.pi / 0.5) * -50, 0, 0)

    green  = (0.22, 0.55, 0.20, 1)   # rotting green skin
    blue   = (0.18, 0.32, 0.65, 1)   # blue torso / legs
    dark_g = (0.16, 0.42, 0.14, 1)   # darker green for hands / shading
    yellow = (0.80, 0.75, 0.10, 1)   # bloodshot yellow eyes

    return {
        "health": 160.0,
        "xp_value": 40,
        "attack_duration": 0.5,
        "parts": [
            # Torso, large and blue, sits high so legs have room below
            {"name": "torso", "parent": None,    "shape": "cube",
             "color": blue,   "scale": (1.50, 1.40, 0.80),
             "position": (0, 2.00, 0), "rotation": (0, 0, 0)},

            # Head, big green block
            {"name": "head",  "parent": "torso", "shape": "cube",
             "color": green,  "scale": (1.10, 1.00, 0.95),
             "position": (0, 1.22, 0), "rotation": (0, 0, 0)},

            # Eyes, yellow and wide-set, proud of the face
            # Head front face is at z = +0.475  (scale.z 0.95 / 2)
            {"name": "eye_l", "parent": "head",  "shape": "cube",
             "color": yellow, "scale": (0.28, 0.22, 0.14),
             "position": (-0.28, 0.10, 0.52), "rotation": (0, 0, 0)},
            {"name": "eye_r", "parent": "head",  "shape": "cube",
             "color": yellow, "scale": (0.28, 0.22, 0.14),
             "position": ( 0.28, 0.10, 0.52), "rotation": (0, 0, 0)},

            # Arms, green, pre-rotated forward 35 deg (zombie reach)
            # Positioned at shoulder edge of torso (x = ±0.75+0.30 half-arm)
            {"name": "arm_l", "parent": "torso", "shape": "cube",
             "color": green,  "scale": (0.42, 1.20, 0.40),
             "position": (-1.00, 0.10, 0.20), "rotation": (-35, 0, 0)},
            {"name": "arm_r", "parent": "torso", "shape": "cube",
             "color": green,  "scale": (0.42, 1.20, 0.40),
             "position": ( 1.00, 0.10, 0.20), "rotation": (-35, 0, 0)},

            # Legs, blue, parented to root for clean animation
            # Root y=0: legs bottom at y≈0, top at y≈1.40 -> meet torso bottom (2.00-0.70=1.30) ✓
            {"name": "leg_l", "parent": None,    "shape": "cube",
             "color": blue,   "scale": (0.52, 1.40, 0.52),
             "position": (-0.42, 0.70, 0), "rotation": (0, 0, 0)},
            {"name": "leg_r", "parent": None,    "shape": "cube",
             "color": blue,   "scale": (0.52, 1.40, 0.52),
             "position": ( 0.42, 0.70, 0), "rotation": (0, 0, 0)},
        ],
        "animations": {
            "walk": {
                "torso":  {"position_offset": body_bob},
                "leg_l":  {"rotation_offset": leg_swing},
                "leg_r":  {"rotation_offset": leg_swing_inv},
                "arm_l":  {"rotation_offset": arm_sway},
                "arm_r":  {"rotation_offset": arm_sway_inv},
            },
            "attack": {
                "torso":  {"rotation_offset": attack_torso},
                "arm_l":  {"rotation_offset": attack_arm_l},
                "arm_r":  {"rotation_offset": attack_arm_r},
            },
        },
    }
