import math
import random

def spec_skeleton(get_player=None) -> dict:
    """
    Skeleton biped.

    Geometry (root y=0, all world-y):
      legs:  centre y=0.70, h=1.40  -> top=1.40
      torso: centre y=2.10, h=1.10  -> bottom=1.55 (clear gap), top=2.65
      arms:  shoulder at torso y=+0.05 -> world y=2.15
      head:  local y=+0.95 on torso  -> world y=3.05
      eyes:  local to head, z proud of front face

    Torso is added to the walk animation with a zero offset so it
    becomes an animated pivot, this ensures arm_l/arm_r (parented to
    torso) resolve to the correct pivot entity rather than falling back
    to root.  Pelvis and eyes bake into the static mesh as usual.
    """
    arm_swing     = lambda t: (math.sin(t * 7.0) * 30, 0, 0)
    arm_swing_inv = lambda t: (math.sin(t * 7.0 + math.pi) * 30, 0, 0)
    leg_swing     = lambda t: (math.sin(t * 7.0) * 28, 0, 0)
    leg_swing_inv = lambda t: (math.sin(t * 7.0 + math.pi) * 28, 0, 0)
    attack_arm    = lambda t: (math.sin(min(t, 0.4) * math.pi / 0.4) * -80, 0, 0)
    zero          = lambda t: (0, 0, 0)   # keeps torso as a pivot with no motion

    bone   = (0.42, 0.40, 0.34, 1)
    torso  = (0.28, 0.26, 0.22, 1)
    red    = (0.90, 0.08, 0.08, 1)


    return {
        "health": 60.0,
        "xp_value": 18,
        "attack_duration": 0.4,
        "parts": [
            # Torso, raised to y=2.10 so it sits clear above the legs
            {"name": "torso",  "parent": None,    "shape": "cube",
             "color": torso,   "scale": (0.90, 1.10, 0.50),
             "position": (0, 2.10, 0), "rotation": (0, 0, 0)},

            # Head, local to torso
            {"name": "head",   "parent": "torso", "shape": "cube",
             "color": bone,    "scale": (0.75, 0.75, 0.75),
             "position": (0, 0.95, 0), "rotation": (0, 0, 0)},

            # Red eyes, z=0.44 clears the head front face (scale.z/2=0.375)
            {"name": "eye_l",  "parent": "head",  "shape": "cube",
             "color": red,     "scale": (0.22, 0.20, 0.14),
             "position": (-0.18, 0.06, 0.44), "rotation": (0, 0, 0)},
            {"name": "eye_r",  "parent": "head",  "shape": "cube",
             "color": red,     "scale": (0.22, 0.20, 0.14),
             "position": ( 0.18, 0.06, 0.44), "rotation": (0, 0, 0)},

            # Arms, parented to torso; torso is animated so these resolve correctly
            {"name": "arm_l",  "parent": "torso", "shape": "cube",
             "color": bone,    "scale": (0.25, 0.95, 0.25),
             "position": (-0.60, 0.05, 0), "rotation": (0, 0, 0)},
            {"name": "arm_r",  "parent": "torso", "shape": "cube",
             "color": bone,    "scale": (0.25, 0.95, 0.25),
             "position": ( 0.60, 0.05, 0), "rotation": (0, 0, 0)},

            # Legs, parented to root for clean independent animation
            # centre y=0.70, h=1.40 -> bottom=0.00, top=1.40
            {"name": "leg_l",  "parent": None,    "shape": "cube",
             "color": bone,    "scale": (0.28, 1.40, 0.28),
             "position": (-0.22, 0.70, 0), "rotation": (0, 0, 0)},
            {"name": "leg_r",  "parent": None,    "shape": "cube",
             "color": bone,    "scale": (0.28, 1.40, 0.28),
             "position": ( 0.22, 0.70, 0), "rotation": (0, 0, 0)},
        ],
        "animations": {
            "walk": {
                # torso zero-offset keeps it as a pivot so children (arms) work
                "torso": {"rotation_offset": zero},
                "arm_l": {"rotation_offset": arm_swing_inv},
                "arm_r": {"rotation_offset": arm_swing},
                "leg_l": {"rotation_offset": leg_swing},
                "leg_r": {"rotation_offset": leg_swing_inv},
            },
            "attack": {
                "torso": {"rotation_offset": zero},
                "arm_r": {"rotation_offset": attack_arm},
            },
        },
    }