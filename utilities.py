# utilities.py

# --- Screen and Display Settings ---
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
PLAYABLE_WIDTH = 1150 # NEW: The width of the map/game area
GAME_TITLE = "Geometric Canine Defense"
SETTINGS_FILE = "settings.json" # NEW
COLOR_PALETTES = {
    'default': {
        'background': (44, 62, 80), 'primary_text': (236, 240, 241),
        'secondary_text': (189, 195, 199), 'accent': (52, 152, 219),
        'success': (46, 204, 113), 'danger': (231, 76, 60),
        'panel_background': (52, 73, 94), 'button_bg': (41, 128, 185),
        'button_hover': (52, 152, 219), 'button_click': (31, 97, 141),
        'button_disabled': (127, 140, 141), 'button_text': (255, 255, 255)
    },
    # --- CORRECTED MAP THEMES ---
    'map_themes': {
        'meadow': {
            'background': (34, 139, 34),     # Was 'grass'
            'path': (139, 69, 19),
            'water': (70, 130, 180)
        },
        'desert': {
            'background': (222, 184, 135),    # Was 'sand'
            'path': (244, 164, 96),
            'water': (0, 191, 255)           # Was 'oasis'
        },
        'arctic': {
            'background': (255, 250, 250),    # Was 'snow'
            'path': (211, 211, 211),
            'water': (0, 206, 209)
        },
        'volcano': {
            'background': (105, 105, 105),    # Was 'rock'
            'path': (40, 40, 40),
            'water': (178, 34, 34),          # A dark red for generic "water" areas
            'lava': (255, 69, 0)             # A special color for actual lava
        }
    }
}
# --- (The rest of the file - Gameplay Constants, etc. - is the same) ---
STARTING_MONEY = 650; STARTING_LIVES = 100; MAX_ROUNDS = 100
TOWER_PLACEMENT_RADIUS = 30; PATH_RESTRICTION_WIDTH = 50
RENDER_LAYERS = {'map_terrain':0, 'map_path':1, 'map_water':2, 'tower_range':5, 'towers':10, 'enemies':15, 'projectiles':20, 'tower_placement_preview':25, 'hud':30, 'panels':31, 'buttons':32, 'tooltips':40}
DIFFICULTY_SETTINGS = {'easy':{'starting_money':800, 'starting_lives':150, 'enemy_speed_modifier':0.9, 'tower_cost_modifier':0.95}, 'medium':{'starting_money':650, 'starting_lives':100, 'enemy_speed_modifier':1.0, 'tower_cost_modifier':1.0}, 'hard':{'starting_money':500, 'starting_lives':75, 'enemy_speed_modifier':1.1, 'tower_cost_modifier':1.05}}
