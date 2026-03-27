from ursina import *
import math


class XPSystem:
    """
    Tracks the player's level and experience points.
    Called by SoulOrb when collected, and can be queried
    anywhere to check current level/xp.
    """

    def __init__(self):
        self.player_level          = 0
        self.player_xp             = 0
        self.player_xp_to_next_level = 25  # XP needed for level 1
        self.on_level_up             = None # Call back after player_stats is defined
        self.ability_manager         = None 

    def add_xp(self, amount: float):
        """Add XP and level up if the threshold is crossed."""
        self.player_xp += amount
        while self.player_xp >= self.player_xp_to_next_level:
            self.player_xp         -= self.player_xp_to_next_level
            self.player_level      += 1
            self.player_xp_to_next_level = int(self.player_xp_to_next_level + 5)
            print(f"[XP] Level up! Now level {self.player_level}. "
                  f"Next level at {self.player_xp_to_next_level} XP.")

            # Fire the level up callback so player_stats can increase max stats
            if self.on_level_up:
                self.on_level_up(self.player_level)

            # Every 5 levels offer an ability choice
            if self.player_level % 5 == 0 and self.on_ability_pick and self.player_level > 0:
                self.on_ability_pick()

    def xp_progress(self) -> float:
        """Returns 0.0 – 1.0 progress toward the next level."""
        return self.player_xp / self.player_xp_to_next_level


# Global singleton, import this anywhere you need XP data
xp_system = XPSystem()