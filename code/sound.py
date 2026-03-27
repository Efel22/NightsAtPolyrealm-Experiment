from ursina import *

# Cache so each sound file is only loaded once
_sound_cache: dict = {}

def play_sound(path: str, volume: float = 1.0, loop: bool = False):
    """
    Play a sound by its path relative to the assets folder.
    
    Examples:
        play_sound("entity/hurt")
        play_sound("entity/shoot_bow")
        play_sound("entity/collect_soul", volume=0.9)
        play_sound("music/worldtheme", loop=True, volume=0.4)
    """
    full_path = f"assets/sounds/{path}.wav"

    # Try mp3 if wav not found
    if not os.path.exists(full_path):
        full_path = f"assets/sounds/{path}.mp3"
    if not os.path.exists(full_path):
        full_path = f"assets/music/{path}.mp3"

    # Load and cache the sound if not already loaded
    if full_path not in _sound_cache:
        _sound_cache[full_path] = Audio(
            full_path,
            loop     = loop,
            autoplay = False,
            volume   = volume,
        )

    _sound_cache[full_path].volume = volume
    _sound_cache[full_path].play()


def stop_sound(path: str):
    """Stop a currently playing sound."""
    for key in _sound_cache:
        if path in key:
            _sound_cache[key].stop()
            return