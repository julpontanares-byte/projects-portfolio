import os
import random
from typing import Optional

# Lazy-load pygame to avoid hanging on import
_pygame = None

def _get_pygame():
    """Lazy-load pygame module on first use."""
    global _pygame
    if _pygame is None:
        try:
            import pygame
            _pygame = pygame
        except ImportError:
            raise ImportError("pygame module not installed")
    return _pygame

class AudioManager:
    """
    Handles background music, surprise sound effects, and alarms.
    Uses pygame.mixer for low-latency playback.
    """
    def __init__(self, media_vol: int | float = 80, alarm_vol: int | float = 70):
        pygame = _get_pygame()
        if not pygame.mixer.get_init():
            pygame.mixer.init()
        self.media_vol = media_vol / 100.0
        self.alarm_vol = alarm_vol / 100.0
        self.media_channel = pygame.mixer.Channel(0)
        self.alarm_channel = pygame.mixer.Channel(1)

    def set_volumes(self, media_vol: int | float, alarm_vol: int | float):
        self.media_vol = media_vol / 100.0
        self.alarm_vol = alarm_vol / 100.0
        self.media_channel.set_volume(self.media_vol)
        self.alarm_channel.set_volume(self.alarm_vol)

    def play_surprise(self, mode: str = "normal"):
        """Plays a random surprise effect for the given mode."""
        # Try to find audio files in media folders first
        audio_extensions = ('.mp3', '.wav', '.ogg')
        surprise_paths = [
            "focusbreaker/assets/media/alarm.mp3",
            "focusbreaker/assets/audio/universfield-new-notification-09-352705.mp3",
        ]
        
        # Try to find mode-specific surprise sounds if they exist
        mode_path = f"focusbreaker/assets/media/{mode}/defaults"
        if os.path.exists(mode_path):
            audio_files = [f for f in os.listdir(mode_path) if f.endswith(audio_extensions)]
            if audio_files:
                surprise_paths.insert(0, os.path.join(mode_path, random.choice(audio_files)))
        
        # Play the first valid surprise sound found
        pygame = _get_pygame()
        for sound_path in surprise_paths:
            if os.path.exists(sound_path) and os.path.getsize(sound_path) > 0:
                try:
                    sound = pygame.mixer.Sound(sound_path)
                    self.media_channel.play(sound)
                    return
                except pygame.error as e:
                    continue  # Try next file if this one fails

    def play_alarm(self):
        """Plays the break-end alarm."""
        # Try .mp3 first, then .wav
        pygame = _get_pygame()
        alarm_paths = [
            "focusbreaker/assets/media/alarm.mp3",
            "focusbreaker/assets/media/alarm.wav",
        ]
        
        for alarm_path in alarm_paths:
            if os.path.exists(alarm_path) and os.path.getsize(alarm_path) > 0:
                try:
                    sound = pygame.mixer.Sound(alarm_path)
                    self.alarm_channel.play(sound)
                    return
                except pygame.error as e:
                    continue  # Try next format if this one fails
        
        # If no valid alarm found, play a system beep using a simple tone
        try:
            import winsound
            winsound.Beep(1000, 500)  # 1000 Hz for 500ms
        except (ImportError, RuntimeError):
            pass  # If on non-Windows or winsound fails, silently skip

    def stop_all(self):
        self.media_channel.stop()
        self.alarm_channel.stop()
