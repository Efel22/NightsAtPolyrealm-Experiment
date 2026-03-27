import math
import random

def spec_wizard() -> dict:
    """
    A stationary wizard. Never walks, idle animation gently bobs the
    staff up and down. Attack swings arm_r forward.

    Anatomy (world-y from root=0):
      robe_low   centre y = 0.70   top = 1.40
      robe_high  centre y = 1.95   top = 2.50
      head       world  y = 3.10   top = 3.475  (parented to robe_high, local y=1.00)
      hat_brim   local to head, y = 0.46
      hat_cone   local to head, y = 1.20  (tall pyramid)

    Staff: parented to root at world position so it is never affected by
    arm_r's scale transform.  Rotated/positioned to sit in the wizard's
    right hand naturally.
    """
    purple      = (0.45, 0.10, 0.65, 1)
    dark_purple = (0.28, 0.05, 0.42, 1)
    skin        = (0.88, 0.76, 0.60, 1)
    staff_wood  = (0.45, 0.30, 0.15, 1)
    orb_red     = (0.95, 0.08, 0.08, 1)
    eye_col     = (0.05, 0.05, 0.05, 1)

    # Idle: staff bobs gently
    staff_idle = lambda t: (0, math.sin(t * 2.0) * 0.15, 0)
    # Attack: staff sweeps forward
    staff_atk  = lambda t: (math.sin(min(t, 0.4) * math.pi / 0.4) * -50, 0, 0)

    return {
        "health": 70.0,
        "xp_value": 50,
        "attack_duration": 0.4,
        "parts": [
            # --- Robe lower half ---
            {"name": "robe_low",  "parent": None,        "shape": "cube",
             "color": purple,      "scale": (1.20, 1.40, 0.90),
             "position": (0, 0.70, 0), "rotation": (0, 0, 0)},

            # --- Robe upper half ---
            {"name": "robe_high", "parent": None,        "shape": "cube",
             "color": dark_purple, "scale": (0.95, 1.10, 0.75),
             "position": (0, 1.95, 0), "rotation": (0, 0, 0)},

            # --- Head ---
            {"name": "head",      "parent": "robe_high", "shape": "cube",
             "color": skin,        "scale": (0.80, 0.75, 0.75),
             "position": (0, 1.00, 0), "rotation": (0, 0, 0)},

            # Eyes, z proud of head front face (head.scale.z/2 = 0.375)
            {"name": "eye_l",     "parent": "head",      "shape": "cube",
             "color": eye_col,     "scale": (0.18, 0.16, 0.12),
             "position": (-0.20, 0.06, 0.44), "rotation": (0, 0, 0)},
            {"name": "eye_r",     "parent": "head",      "shape": "cube",
             "color": eye_col,     "scale": (0.18, 0.16, 0.12),
             "position": ( 0.20, 0.06, 0.44), "rotation": (0, 0, 0)},

            # --- Hat brim (wide flat slab, parented to head) ---
            # head half-height = 0.375 -> brim sits at local y = 0.375 + 0.08 = 0.455
            {"name": "hat_brim",  "parent": "head",      "shape": "cube",
             "color": purple,      "scale": (1.40, 0.18, 1.25),
             "position": (0, 0.46, 0), "rotation": (0, 0, 0)},

            # --- Hat cone, tall pyramid sitting on brim ---
            # brim top local = 0.46 + 0.09 = 0.55
            # cone centre at local y = 0.55 + 1.10 = 1.65  (height 2.20)
            {"name": "hat_cone",  "parent": "head",      "shape": "pyramid",
             "color": dark_purple, "scale": (1.10, 2.20, 1.00),
             "position": (0, 1.65, 0), "rotation": (0, 0, 0)},

            # --- Staff, parented to ROOT so scale issues from arm_r are avoided.
            #     Positioned at world x=0.75, y=1.80 to sit in the right hand.
            #     Tilted slightly outward (z=-8 deg) to look natural.
            #     scale y=3.20 -> half=1.60 -> tip at y = 1.80+1.60 = 3.40
            {"name": "staff",     "parent": None,        "shape": "cube",
             "color": staff_wood,  "scale": (0.18, 3.20, 0.18),
             "position": (1.0, 1.80, 0.10), "rotation": (0, 0, 12)},

            # --- Orb at tip of staff ---
            # staff world top ≈ 1.80 + 1.60 = 3.40
            {"name": "orb",       "parent": "staff",     "shape": "sphere",
             "color": orb_red,     "scale": (4, 0.25, 4),
             "position": (0, 0.65, 0), "rotation": (0, 0, 0)},
        ],
        "animations": {
            # Wizard idle: staff gently floats
            "walk": {
                "staff": {"position_offset": staff_idle},
            },
            "attack": {
                "arm_r": {"rotation_offset": staff_atk},
                "staff": {"rotation_offset": staff_atk},
            },
        },
    }
