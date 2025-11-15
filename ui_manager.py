# ui_manager.py
import pygame
import os
from assets import MAPS, DOG_TOWERS
from utilities import COLOR_PALETTES, SCREEN_HEIGHT, SCREEN_WIDTH
from game_engine import SAVE_FILE

# --- BUG FIX: Moved Slider class definition to the top of the file ---
class Slider:
    def __init__(self, x, y, width, height, on_drag, get_value, id, label):
        self.rect = pygame.Rect(x, y, width, height)
        self.on_drag, self.get_value, self.id, self.label = on_drag, get_value, id, label
        self.is_dragging = False
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.rect.collidepoint(event.pos): self.is_dragging = True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1: self.is_dragging = False
        elif event.type == pygame.MOUSEMOTION and self.is_dragging:
            normalized_value = (event.pos[0] - self.rect.x) / self.rect.width
            self.on_drag(max(0, min(1, normalized_value)))
        return self.is_dragging
    def draw(self, screen, renderer):
        renderer.draw_text(self.label, self.rect.centerx, self.rect.y - 15, (255,255,255), 18, True)
        pygame.draw.rect(screen, (30,30,30), self.rect, border_radius=5)
        handle_x = self.rect.x + self.get_value() * self.rect.width
        pygame.draw.rect(screen, (100,100,100), (self.rect.x, self.rect.y, handle_x - self.rect.x, self.rect.height), border_top_left_radius=5, border_bottom_left_radius=5)
        pygame.draw.circle(screen, (200,200,200), (handle_x, self.rect.centery), 10)

class Button:
    def __init__(self, x, y, width, height, text, font, on_click, id):
        self.rect = pygame.Rect(x, y, width, height)
        self.text, self.font, self.on_click, self.id = text, font, on_click, id
        self.is_hovered, self.is_clicked, self.is_active, self.is_selected = False, False, True, False
        self.colors = {"normal":COLOR_PALETTES['default']['button_bg'], "hover":COLOR_PALETTES['default']['button_hover'], "clicked":COLOR_PALETTES['default']['button_click'], "disabled":COLOR_PALETTES['default']['button_disabled'], "selected":COLOR_PALETTES['default']['success']}
        self.text_color = COLOR_PALETTES['default']['button_text']
        self.description, self.desc_font = "", pygame.font.SysFont("Arial", 10)
    def handle_event(self, event, sound_manager):
        if not self.is_active: self.is_hovered=self.is_clicked=False; return False
        if event.type == pygame.MOUSEMOTION: self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.is_hovered: self.is_clicked = True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.is_hovered and self.is_clicked:
                sound_manager.play_sound('click'); self.on_click(self.id)
                self.is_clicked = False; return True
        return False
    def draw(self, screen):
        color = self.colors['disabled'] if not self.is_active else self.colors['selected'] if self.is_selected else self.colors['clicked'] if self.is_clicked else self.colors['hover'] if self.is_hovered else self.colors['normal']
        pygame.draw.rect(screen, color, self.rect, border_radius=5)
        if self.id.startswith("upgrade_"):
            screen.blit(self.font.render(self.text, True, self.text_color), (self.rect.x + 5, self.rect.y + 5))
            words, lines, current_line = self.description.split(' '), [], ""
            for word in words:
                if self.desc_font.size(current_line + word)[0] < self.rect.width-10: current_line += word + " "
                else: lines.append(current_line); current_line = word + " "
            lines.append(current_line)
            for i, line in enumerate(lines): screen.blit(self.desc_font.render(line, True, self.text_color), (self.rect.x + 5, self.rect.y + 22 + i*12))
        elif self.text: screen.blit(self.font.render(self.text, True, self.text_color), self.font.render(self.text, True, self.text_color).get_rect(center=self.rect.center))

class UIManager:
    def __init__(self, game):
        self.game, self.buttons, self.sliders, self.sound_manager = game, [], [], game.sound_manager
        self.selected_tower, self.placing_tower_type, self.mouse_pos, self.scroll_y = None, None, (0,0), 0
        self.create_buttons_for_state()
    def create_buttons_for_state(self):
        self.buttons.clear(); self.sliders.clear()
        state = self.game.game_state
        if state == 'main_menu': self._create_main_menu_buttons()
        elif state == 'in_game': self._create_ingame_buttons()
        elif state == 'paused': self._create_pause_menu_buttons()
        elif state == 'settings': self._create_settings_menu_buttons()
    def _create_main_menu_buttons(self):
        font,start_font=self.game.renderer.get_font(24),self.game.renderer.get_font(32,True)
        for i,map_id in enumerate(MAPS.keys()): self.buttons.append(Button(100+(i%5)*220,250+(i//5)*120,200,100,"",font,self.handle_click,f"map_{map_id}"))
        for i,diff in enumerate(['easy','medium','hard']):
            btn = Button(320+i*220,520,200,50,diff.capitalize(),font,self.handle_click,f"diff_{diff}")
            if diff == self.game.selected_difficulty: btn.is_selected = True
            self.buttons.append(btn)
        self.buttons.append(Button(310,600,200,50,"New Game",start_font,self.handle_click,"start_game"))
        if os.path.exists(SAVE_FILE): self.buttons.append(Button(770,600,200,50,"Continue",start_font,self.handle_click,"continue_game"))
        self.buttons.append(Button(SCREEN_WIDTH-120,SCREEN_HEIGHT-60,100,40,"Settings",self.game.renderer.get_font(16),self.handle_click,"settings"))
    def _create_ingame_buttons(self):
        font,play_font=self.game.renderer.get_font(12),self.game.renderer.get_font(20,True)
        for i,(tower_id,data) in enumerate(DOG_TOWERS.items()): self.buttons.append(Button(1160,70+i*100,100,90,"",font,self.handle_click,f"buy_{tower_id}"))
        self.buttons.append(Button(1080,650,70,50,"||",play_font,self.handle_click,"play_pause"))
        self.buttons.append(Button(1000,650,70,50,"▶▶",play_font,self.handle_click,"fast_forward"))
        self.buttons.append(Button(920,650,70,50,"AUTO",self.game.renderer.get_font(14,True),self.handle_click,"toggle_autostart"))
        self.buttons.append(Button(840,650,70,50,"",play_font,self.handle_click,"cancel_placement"))
        upgrade_font=self.game.renderer.get_font(12,True)
        for i in range(3): self.buttons.append(Button(220,480+i*80,250,70,"",upgrade_font,self.handle_click,f"upgrade_{i}"))
        self.buttons.append(Button(10,640,200,30,"Target: First",self.game.renderer.get_font(14,True),self.handle_click,"cycle_targeting"))
        self.buttons.append(Button(10,680,200,30,"Sell for $0",self.game.renderer.get_font(16,True),self.handle_click,"sell_tower"))
    def _create_pause_menu_buttons(self):
        font=self.game.renderer.get_font(32,True)
        self.buttons.append(Button(SCREEN_WIDTH//2-100,250,200,50,"Resume",font,self.handle_click,"resume"))
        self.buttons.append(Button(SCREEN_WIDTH//2-100,320,200,50,"Restart",font,self.handle_click,"restart"))
        self.buttons.append(Button(SCREEN_WIDTH//2-100,390,200,50,"Settings",font,self.handle_click,"settings"))
        self.buttons.append(Button(SCREEN_WIDTH//2-100,460,200,50,"Main Menu",font,self.handle_click,"menu"))
    def _create_settings_menu_buttons(self):
        self.sliders.append(Slider(SCREEN_WIDTH//2-150,300,300,20,self.sound_manager.set_music_volume,lambda:self.sound_manager.music_volume,"music_volume","Music Volume"))
        self.sliders.append(Slider(SCREEN_WIDTH//2-150,400,300,20,self.sound_manager.set_sfx_volume,lambda:self.sound_manager.sfx_volume,"sfx_volume","Sound FX Volume"))
        self.buttons.append(Button(SCREEN_WIDTH//2-100,500,200,50,"Back",self.game.renderer.get_font(32,True),self.handle_click,"back_from_settings"))
    def update(self, game_engine):
        state=self.game.game_state
        if state=='main_menu':
            start_button=next((b for b in self.buttons if b.id=="start_game"),None)
            if start_button:start_button.is_active=self.game.selected_map is not None
        elif state=='in_game':
            play_pause_button=next((b for b in self.buttons if b.id=="play_pause"),None)
            if play_pause_button:
                play_pause_button.text = "▶" if not game_engine.is_round_active else "||"
                play_pause_button.is_active = True
            cancel_button=next((b for b in self.buttons if b.id=="cancel_placement"),None)
            if cancel_button:cancel_button.is_active=self.placing_tower_type is not None
            self.update_tower_panel()
            buy_area=pygame.Rect(1150,50,130,SCREEN_HEIGHT-120);
            if buy_area.collidepoint(self.mouse_pos):
                content_height=len(DOG_TOWERS)*100; visible_height=buy_area.height; max_scroll=max(0,content_height-visible_height+10)
                self.scroll_y=max(-max_scroll,min(0,self.scroll_y))
            for btn in self.buttons:
                if btn.id.startswith("buy_"):btn.rect.y=70+list(DOG_TOWERS.keys()).index(btn.id.split('_',1)[1])*100+self.scroll_y
    def handle_events(self, events):
        self.mouse_pos=pygame.mouse.get_pos(); clicked_on_ui=False
        for event in events:
            if event.type==pygame.MOUSEWHEEL and self.game.game_state=='in_game':self.scroll_y+=event.y*20
            for slider in self.sliders:
                if slider.handle_event(event):clicked_on_ui=True
            for button in self.buttons:
                if button.handle_event(event,self.sound_manager):clicked_on_ui=True
            if event.type==pygame.MOUSEBUTTONUP and not clicked_on_ui:
                if event.button==1:self.handle_world_click()
                elif event.button==3:self.handle_right_click()
    def handle_click(self, button_id):
        if button_id.startswith("map_"):self.game.selected_map=button_id.split('_',1)[1]; [setattr(b,'is_selected',(b.id==button_id)) for b in self.buttons if b.id.startswith("map_")]
        elif button_id.startswith("diff_"):self.game.selected_difficulty=button_id.split('_',1)[1]; [setattr(b,'is_selected',(b.id==button_id)) for b in self.buttons if b.id.startswith("diff_")]
        elif button_id=="start_game":
            if self.game.selected_map:self.game.game_engine.delete_save();self.game.start_game(self.game.selected_map,self.game.selected_difficulty)
        elif button_id=="continue_game":
            if self.game.game_engine.load_game():self.game.change_state('in_game')
        elif button_id.startswith("buy_"):self.placing_tower_type,self.selected_tower=button_id.split('_',1)[1],None
        elif button_id=="play_pause":
            if self.game.game_state == 'in_game':
                if not self.game.game_engine.is_round_active: self.game.game_engine.start_next_round()
                else: self.game.change_state('paused')
        elif button_id.startswith("upgrade_"):
            if self.selected_tower:path_index=int(button_id.split('_',1)[1]);self.game.game_engine.upgrade_tower(self.selected_tower,path_index)
        elif button_id=="menu":self.game.game_engine.save_game();self.game.change_state('main_menu');self.selected_tower,self.placing_tower_type,self.game.selected_map=None,None,None
        elif button_id=="cycle_targeting":
            if self.selected_tower:self.selected_tower.cycle_targeting_priority()
        elif button_id=="sell_tower":
            if self.selected_tower:self.game.game_engine.sell_tower(self.selected_tower);self.selected_tower=None
        elif button_id=="fast_forward":
            ff_button=next((b for b in self.buttons if b.id=="fast_forward"),None)
            if self.game.game_speed==1.0:self.game.game_speed,ff_button.is_selected=2.0,True
            else:self.game.game_speed,ff_button.is_selected=1.0,False
        elif button_id=="toggle_autostart":
            self.game.game_engine.auto_start_next_round=not self.game.game_engine.auto_start_next_round
            btn=next((b for b in self.buttons if b.id==button_id),None);btn.is_selected=self.game.game_engine.auto_start_next_round
        elif button_id=="cancel_placement":self.placing_tower_type=None
        elif button_id=="resume":self.game.change_state('in_game')
        elif button_id=="restart":self.game.game_engine.delete_save();self.game.start_game(self.game.selected_map,self.game.selected_difficulty)
        elif button_id=="settings":self.game.change_state('settings')
        elif button_id=="back_from_settings":self.sound_manager.save_settings();self.game.change_state(self.game.previous_game_state)
    def handle_world_click(self):
        if self.game.game_state!='in_game':return
        if self.placing_tower_type:
            if self.game.game_engine.place_tower(self.placing_tower_type,self.mouse_pos):self.placing_tower_type=None
            return
        self.selected_tower=next((t for t in reversed(self.game.game_engine.towers) if t.rect.collidepoint(self.mouse_pos)),None)
    def handle_right_click(self):
        if self.placing_tower_type:self.placing_tower_type=None
        elif self.selected_tower:self.selected_tower=None
    def update_tower_panel(self):
        money,targeting_button,sell_button=self.game.game_engine.money,next((b for b in self.buttons if b.id=="cycle_targeting"),None),next((b for b in self.buttons if b.id=="sell_tower"),None)
        if self.selected_tower:
            if targeting_button:targeting_button.is_active=True;targeting_button.text=f"Target: {self.selected_tower.targeting_priority.capitalize()}"
            if sell_button:sell_button.is_active=True;sell_button.text=f"Sell for ${self.selected_tower.get_sell_value()}"
            tower_data,upgrades=DOG_TOWERS[self.selected_tower.tower_id],self.selected_tower.upgrades
            for i in range(3):
                btn=next((b for b in self.buttons if b.id==f"upgrade_{i}"),None);
                if not btn:continue
                current_tier=upgrades[i]
                path_is_locked = (upgrades[i] >= 2 and any(p > 2 for j, p in enumerate(upgrades) if j != i)) or \
                               (any(p > 2 for p in upgrades) and upgrades[i] < 2) or \
                               (upgrades[i] >= 2 and upgrades.count(2) > 0 and (upgrades.index(2) if 2 in upgrades else -1) != i)
                if current_tier>=5:btn.text,btn.description,btn.is_active="MAXED","",False
                elif path_is_locked:btn.text,btn.description,btn.is_active="LOCKED","",False
                else:
                    upgrade_info=tower_data['upgrades'][f'path{i+1}'][current_tier]
                    btn.text,btn.description=f"{upgrade_info['name']} (${upgrade_info['cost']})",upgrade_info['description']
                    btn.is_active=money>=upgrade_info['cost']
        else:
            if targeting_button:targeting_button.is_active=False
            if sell_button:sell_button.is_active=False
            for i in range(3):
                btn=next((b for b in self.buttons if b.id==f"upgrade_{i}"),None)
                if btn:btn.is_active=False
