from ursina import *
import math
from code.world.world_settings import DETAIL_RADIUS, CHUNK_SIZE
from code.sound import play_sound, stop_sound

class NightTracker:
    """
    Tracks how many nights the player has survived.
    At night, enemy spawn rates and caps increase with each night,
    capping at 15 entities max.
    """

    # -- Baseline day spawn settings ---------------------------------------
    DAY_SPAWN_INTERVAL   = 10.0
    DAY_MAX_ENTITIES     = 3
    DAY_SPAWN_DISTANCE   = DETAIL_RADIUS * CHUNK_SIZE * 1.75

    # -- Night spawn settings ----------------------------------------------
    NIGHT_SPAWN_INTERVAL_START = 8.0   # first night interval
    NIGHT_SPAWN_INTERVAL_MIN   = 0.5   # fastest possible spawn rate
    NIGHT_MAX_ENTITIES_START   = 6     # first night cap
    NIGHT_MAX_ENTITIES_CAP     = 14    # absolute maximum
    NIGHT_SPAWN_DISTANCE       = DETAIL_RADIUS * CHUNK_SIZE


    def __init__(self):
        self.nights_survived = 0
        self._is_night       = False   # updated every frame from sky system

    def notify_day_night(self, is_night: bool):
        """Call every frame with the current day/night state from SkySystem."""
        if is_night and not self._is_night:
            # Just became night, new night begins
            self.nights_survived += 0   # don't increment yet, increment at dawn
            self._show_night_notification()
            print(f"[NightTracker] Night {self.nights_survived + 1} begins!")

        elif not is_night and self._is_night:
            # Just became day, night survived
            self.nights_survived += 1
            self._show_day_notification()
            print(f"[NightTracker] Survived night {self.nights_survived}!")

        self._is_night = is_night

    @property
    def is_night(self) -> bool:
        return self._is_night

    def current_spawn_interval(self) -> float:
        """Returns the spawn interval for the current time of day."""
        if not self._is_night:
            return self.DAY_SPAWN_INTERVAL

        # Each night reduces the interval, capped at the minimum
        reduction = self.nights_survived * 0.5
        return max(self.NIGHT_SPAWN_INTERVAL_MIN,
                   self.NIGHT_SPAWN_INTERVAL_START - reduction)

    def current_max_entities(self) -> int:
        """Returns the entity cap for the current time of day."""
        if not self._is_night:
            return self.DAY_MAX_ENTITIES

        # Each night adds 2 more entities, capped at the maximum
        increase = self.nights_survived * 2
        return min(self.NIGHT_MAX_ENTITIES_CAP,
                   self.NIGHT_MAX_ENTITIES_START + increase)

    def current_spawn_distance(self) -> float:
        """Returns the entity spawning distance for the current time of day."""
        if not self._is_night:
            return self.DAY_SPAWN_DISTANCE
        
        # Base case is to return night_spawn_distance
        return self.NIGHT_SPAWN_DISTANCE

    def _show_night_notification(self):
        """Flash a 'Night X has arrived' message on screen."""
        night_num = self.nights_survived + 1

        # Switch the Music
        stop_sound("music/worldtheme")
        play_sound("music/fighttheme")
        play_sound("ambient/nighttime")

        notif = Text(
            text     = f"Night {night_num} Has Arrived",
            parent   = camera.ui,
            scale    = 3.0,
            position = (0, 0.25),
            origin   = (0, 0),
            color    = color.rgba(0.9, 0.05, 0.05, 0.0),  # start transparent
        )

        # Fade in then fade out
        notif.animate_color(color.rgba(0.9, 0.05, 0.05, 1.0),
                            duration=1.0, curve=curve.linear)

        def fade_out():
            notif.animate_color(color.rgba(0.9, 0.05, 0.05, 0.0),
                                duration=1.5, curve=curve.linear)
            invoke(destroy, notif, delay=1.6)

        invoke(fade_out, delay=2.5)

    def _show_day_notification(self):
        """Flash a 'Night X has arrived' message on screen."""
        night_num = self.nights_survived + 1

        # Switch the Music
        stop_sound("music/fighttheme")
        play_sound("music/worldtheme")
        play_sound("ambient/daytime")

        notif = Text(
            text     = f"Daytime Has Arrived",
            parent   = camera.ui,
            scale    = 3.0,
            position = (0, 0.25),
            origin   = (0, 0),
            color    = color.rgba(1.0, 0.605, 0.09, 0.0),  # start transparent
        )

        # Fade in then fade out
        notif.animate_color(color.rgba(1.0, 0.605, 0.09, 1.0),
                            duration=1.0, curve=curve.linear)

        def fade_out():
            notif.animate_color(color.rgba(1.0, 0.605, 0.09, 0.0),
                                duration=1.5, curve=curve.linear)
            invoke(destroy, notif, delay=1.6)

        invoke(fade_out, delay=2.5)

# Global singleton
night_tracker = NightTracker()