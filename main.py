# main.py
import pygame
from utilities import SCREEN_WIDTH, SCREEN_HEIGHT, GAME_TITLE, COLOR_PALETTES
from ui_manager import UIManager
from game_engine import GameEngine
from renderer import Renderer
from sound_manager import SoundManager
import traceback # Import traceback to print detailed errors

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(GAME_TITLE)
        self.clock = pygame.time.Clock()
        self.running = True

        self.game_state = 'main_menu'
        self.previous_game_state = 'main_menu'
        self.selected_map = None
        self.selected_difficulty = 'medium'
        self.game_speed = 1.0

        self.sound_manager = SoundManager()
        self.renderer = Renderer(self.screen)
        self.game_engine = GameEngine(self)
        self.ui_manager = UIManager(self)
        self.sound_manager.play_music()

    def run(self):
        while self.running:
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    self.sound_manager.save_settings(); self.running = False
                self.ui_manager.handle_events(events)

            self.ui_manager.update(self.game_engine)
            
            if self.game_state == 'in_game':
                dt = (self.clock.tick(60) / 1000.0) * self.game_speed
                self.game_engine.update(dt)
            else:
                self.clock.tick(60)

            self.screen.fill(COLOR_PALETTES['default']['background'])
            self.render()
            pygame.display.flip()

        pygame.quit()

    def render(self):
        if self.game_state == 'main_menu':
            self.renderer.draw_main_menu(self.ui_manager)
        elif self.game_state == 'in_game' or self.game_state == 'paused':
            self.renderer.draw_game_state(self.game_engine, self.ui_manager)
            if self.game_state == 'paused':
                self.renderer.draw_pause_menu(self.ui_manager)
        
        if self.game_state == 'settings':
            if self.previous_game_state == 'main_menu': self.renderer.draw_main_menu(self.ui_manager)
            elif self.previous_game_state in ['in_game', 'paused']: self.renderer.draw_game_state(self.game_engine, self.ui_manager)
            self.renderer.draw_settings_menu(self.ui_manager, self.sound_manager)

    def change_state(self, new_state):
        if new_state == "settings": self.previous_game_state = self.game_state
        self.game_state = new_state
        self.ui_manager.create_buttons_for_state()

    def start_game(self, map_id, difficulty):
        self.selected_map = map_id; self.selected_difficulty = difficulty
        self.game_engine.start_new_game(map_id, difficulty)
        self.change_state('in_game')

if __name__ == "__main__":
    try:
        game_instance = Game()
        game_instance.run()
    except Exception as e:
        print("\n--- A FATAL ERROR OCCURRED ---")
        # Print the full error traceback
        traceback.print_exc()
        print("---------------------------------")
        input("\nPlease press Enter to close the program...")
