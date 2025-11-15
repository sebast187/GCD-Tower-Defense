# sound_manager.py
import pygame
import os
import json
from utilities import SETTINGS_FILE

class SoundManager:
    def __init__(self):
        self.is_sound_enabled = False
        self.music_volume = 0.3
        self.sfx_volume = 0.5
        self.load_settings()

        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
        except pygame.error:
            try: pygame.mixer.init()
            except pygame.error as e:
                print(f"FATAL: Could not initialize Pygame mixer: {e}. Sounds will be disabled.")
                return

        self.sounds = {}
        sound_files = {
            'click': "sounds/click.wav", 'pop': "sounds/pop.wav",
            'place_tower': "sounds/place_tower.wav", 'sell': "sounds/sell.wav",
            'shoot_bark': "sounds/shoot_bark.wav", 'shoot_cannon': "sounds/shoot_cannon.wav",
            'shoot_sniper': "sounds/shoot_sniper.wav"
        }
        all_files_loaded = True
        for name, path in sound_files.items():
            if not os.path.exists(path):
                print(f"Warning: Sound file not found at '{path}'")
                all_files_loaded = False; continue
            try: self.sounds[name] = pygame.mixer.Sound(path)
            except pygame.error as e: print(f"CRITICAL: Failed to load '{path}': {e}"); all_files_loaded = False
        
        self.set_sfx_volume(self.sfx_volume) # Apply loaded/default volume
            
        self.music_path = "sounds/music.ogg"
        if not os.path.exists(self.music_path): self.music_path = None; all_files_loaded = False
        
        if all_files_loaded: print("Sound Manager initialized successfully.")
        else: print("Some sound files failed to load. Sound effects may be missing.")
        self.is_sound_enabled = True

    def play_sound(self, name):
        if self.is_sound_enabled and name in self.sounds: self.sounds[name].play()

    def play_music(self):
        if self.is_sound_enabled and self.music_path:
            try:
                pygame.mixer.music.load(self.music_path)
                pygame.mixer.music.set_volume(self.music_volume) # Apply loaded/default volume
                pygame.mixer.music.play(-1)
            except pygame.error as e: print(f"CRITICAL: Failed to load music: {e}")

    def set_sfx_volume(self, volume):
        self.sfx_volume = max(0.0, min(1.0, volume))
        if self.is_sound_enabled:
            for sound in self.sounds.values(): sound.set_volume(self.sfx_volume)

    def set_music_volume(self, volume):
        self.music_volume = max(0.0, min(1.0, volume))
        if self.is_sound_enabled: pygame.mixer.music.set_volume(self.music_volume)

    def save_settings(self):
        settings = {"music_volume": self.music_volume, "sfx_volume": self.sfx_volume}
        with open(SETTINGS_FILE, 'w') as f: json.dump(settings, f)

    def load_settings(self):
        if not os.path.exists(SETTINGS_FILE): return
        try:
            with open(SETTINGS_FILE, 'r') as f:
                settings = json.load(f)
                self.music_volume = settings.get("music_volume", 0.3)
                self.sfx_volume = settings.get("sfx_volume", 0.5)
        except (IOError, json.JSONDecodeError):
            print(f"Could not load settings from {SETTINGS_FILE}. Using defaults.")
