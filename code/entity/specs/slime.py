import math
import random

# ============================================================
#  SLIME SPECS
# ============================================================

def spec_slime() -> dict:
    """A bouncy blob slime."""
    squish = lambda t: (0, 0, 0)  # body handled via position bob
    attack_squish = lambda t: (math.sin(min(t, 0.3) * math.pi / 0.3) * 20, 0, 0)

    return {
        "health": 25.0,
        "xp_value": 15,
        "attack_duration": 0.3,
        "parts": [
            {"name": "body",    "parent": None,   "shape": "cube",
             "color": (0.18, 0.72, 0.28, 0.9), "scale": (1.4, 1.0, 1.4),
             "position": (0, 0.7, 0), "rotation": (0, 0, 0)},
            {"name": "eye_l",   "parent": "body", "shape": "cube",
             "color": (0.05, 0.05, 0.05, 1), "scale": (0.22, 0.22, 0.14),
             "position": (-0.30, 0.18, 0.62), "rotation": (0, 0, 0)},
            {"name": "eye_r",   "parent": "body", "shape": "cube",
             "color": (0.05, 0.05, 0.05, 1), "scale": (0.22, 0.22, 0.14),
             "position": (0.30, 0.18, 0.62), "rotation": (0, 0, 0)},
        ],
        "animations": {
            "walk": {
                "body": {
                    "position_offset": lambda t: (0, abs(math.sin(t * 5.0)) * 0.25, 0),
                },
            },
            "attack": {
                "body": {"rotation_offset": attack_squish},
            },
        },
    }
