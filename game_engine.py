# game_engine.py
# --- (Imports are unchanged) ---
import math, pygame, json, os
from assets import MAPS, ROUND_COMPOSITIONS, GEOMETRIC_ENEMIES, DOG_TOWERS
from utilities import STARTING_MONEY, STARTING_LIVES, DIFFICULTY_SETTINGS, PATH_RESTRICTION_WIDTH, PLAYABLE_WIDTH
from game_objects import DogTower, GeometricEnemy, Projectile, VisualEffect
SAVE_FILE = "savegame.json"

class GameEngine:
    # --- (init, reset, start_new_game, start_next_round are unchanged) ---
    def __init__(self, game): self.game,self.sound_manager=game,game.sound_manager; self.reset()
    def reset(self):
        self.towers, self.enemies, self.projectiles, self.visual_effects = [],[],[],[]
        self.current_round, self.money, self.lives = 0, STARTING_MONEY, STARTING_LIVES
        self.map_data, self.map_paths, self.difficulty_modifiers = None,[],{}
        self.is_round_active, self.spawn_queue, self.round_timer, self.win, self.lose = False,[],0,False,False
        self.auto_start_next_round = False
    def start_new_game(self, map_id, difficulty):
        self.reset(); self.map_data = MAPS[map_id]
        self.map_paths = [self.map_data.get("path",[])] + [self.map_data.get(f"path{i}",[]) for i in range(2,5)]
        self.map_paths = [p for p in self.map_paths if p]
        self.difficulty_modifiers = DIFFICULTY_SETTINGS[difficulty]
        self.money, self.lives = self.difficulty_modifiers['starting_money'], self.difficulty_modifiers['starting_lives']
    def start_next_round(self):
        if self.is_round_active or self.win or self.lose: return
        self.is_round_active, self.current_round, self.round_timer = True, self.current_round + 1, 0
        if self.current_round > len(ROUND_COMPOSITIONS): self.win, self.is_round_active = True, False; self.delete_save(); return
        self.spawn_queue = []
        for enemy_id, count, start_time, end_time in ROUND_COMPOSITIONS[self.current_round - 1]:
            spacing = (end_time-start_time)/count if count>1 else 0
            for i in range(count): self.spawn_queue.append((start_time+i*spacing, enemy_id, self.map_paths[i % len(self.map_paths)]))
        self.spawn_queue.sort(key=lambda x: x[0], reverse=True)

    def update(self, dt):
        if self.lose or self.win: return
        if self.is_round_active:
            self.round_timer += dt
            while self.spawn_queue and self.round_timer >= self.spawn_queue[-1][0]:
                _, enemy_id, path = self.spawn_queue.pop()
                new_enemy = GeometricEnemy(enemy_id, path); new_enemy.speed_base *= self.difficulty_modifiers['enemy_speed_modifier']
                self.enemies.append(new_enemy)
        for tower in self.towers:
            tower.update(dt, self.enemies)
            if tower.can_attack():
                new_projectiles, new_effects = tower.attack(self.enemies, self.sound_manager); self.projectiles.extend(new_projectiles); self.visual_effects.extend(new_effects)
        for enemy in self.enemies[:]:
            enemy.update(dt)
            if not enemy.is_active:
                if enemy in self.enemies: self.enemies.remove(enemy)
                self.lives -= enemy.get_tier()
                if self.lives <= 0: self.lives = 0; self.lose = True; self.delete_save()
        
        projectiles_to_remove = []
        for proj in self.projectiles:
            proj.update(dt)
            if not proj.is_active: projectiles_to_remove.append(proj); continue
            
            hit_something = False
            if proj.target and proj.target.is_active and proj.check_collision():
                hit_something = True
                
                if proj.is_area_of_effect:
                    # --- BUG FIX: Use named arguments for VisualEffect ---
                    self.visual_effects.append(VisualEffect(type="explosion", pos=proj.pos, radius=proj.blast_radius, lifetime=0.2))
                    for enemy in self.enemies[:]:
                        if enemy.pos.distance_to(proj.pos) <= proj.blast_radius:
                            newly_spawned = enemy.take_damage(proj.damage_tier, proj.owner, self.sound_manager)
                            self.money += enemy.money_on_hit
                            if not enemy.is_active and enemy in self.enemies: self.enemies.remove(enemy)
                            self.enemies.extend(newly_spawned)
                else:
                    newly_spawned = proj.target.take_damage(proj.damage_tier, proj.owner, self.sound_manager)
                    self.money += proj.target.money_on_hit
                    if not proj.target.is_active and proj.target in self.enemies: self.enemies.remove(proj.target)
                    self.enemies.extend(newly_spawned)

            if hit_something: proj.cleanup(); projectiles_to_remove.append(proj)

        for proj in projectiles_to_remove:
            if proj in self.projectiles: self.projectiles.remove(proj)
        self.visual_effects = [effect for effect in self.visual_effects if effect.update(dt)]
        if self.is_round_active and not self.enemies and not self.spawn_queue:
            self.is_round_active = False; self.money += 100 + self.current_round; self.save_game()
            if self.auto_start_next_round: self.start_next_round()

    # --- (The rest of the file is unchanged) ---
    def is_valid_placement(self, tower_id, pos):
        if pos[0] > PLAYABLE_WIDTH: return False
        tower_data = DOG_TOWERS[tower_id]
        in_water = any(pygame.Rect(a['x'],a['y'],a['width'],a['height']).collidepoint(pos) for a in self.map_data.get("water_areas",[]))
        if tower_data.get("is_water_only", False) and not in_water: return False
        if not tower_data.get("is_water_only", False) and in_water: return False
        for path in self.map_paths:
            if not path: continue
            for i in range(len(path)-1):
                p1,p2 = pygame.Vector2(path[i]), pygame.Vector2(path[i+1])
                line_vec, point_vec = p2-p1, pygame.Vector2(pos)-p1; line_len_sq = line_vec.length_squared()
                if line_len_sq == 0: continue
                t = max(0, min(1, point_vec.dot(line_vec)/line_len_sq)); closest_point = p1 + t*line_vec
                if closest_point.distance_to(pygame.Vector2(pos)) < PATH_RESTRICTION_WIDTH: return False
        if any(pygame.Vector2(t.x, t.y).distance_to(pygame.Vector2(pos)) < 40 for t in self.towers): return False
        return True
    def place_tower(self, tower_id, position):
        cost = int(DOG_TOWERS[tower_id]['cost'] * self.difficulty_modifiers['tower_cost_modifier'])
        if self.money >= cost and self.is_valid_placement(tower_id, position):
            self.money-=cost; self.towers.append(DogTower(tower_id, position)); self.sound_manager.play_sound('place_tower'); return True
        return False
    def upgrade_tower(self, tower, path_index):
        if not tower or path_index < 0 or path_index > 2: return
        current_tier = tower.upgrades[path_index]
        if current_tier >= 5: return
        upgrades = tower.upgrades
        if upgrades[path_index] >= 2 and any(p > 2 for i, p in enumerate(upgrades) if i != path_index): return
        if any(p > 2 for p in upgrades) and upgrades[path_index] < 2: return
        if upgrades[path_index] >= 2 and upgrades.count(2) > 0 and (upgrades.index(2) if 2 in upgrades else -1) != path_index: return
        upgrade_data = DOG_TOWERS[tower.tower_id]['upgrades'][f'path{path_index+1}'][current_tier]
        cost = upgrade_data['cost']
        if self.money >= cost:
            self.money -= cost; tower.apply_upgrade(path_index, upgrade_data); tower.upgrades[path_index] += 1
            tower.total_cost += cost; self.sound_manager.play_sound('click')
    def sell_tower(self, tower):
        if tower in self.towers: self.money += tower.get_sell_value(); self.towers.remove(tower); self.sound_manager.play_sound('sell')
    def save_game(self):
        save_data = {"map_id": self.game.selected_map, "difficulty": self.game.selected_difficulty, "money": self.money, "lives": self.lives, "current_round": self.current_round, "towers": [t.serialize() for t in self.towers]}
        with open(SAVE_FILE, 'w') as f: json.dump(save_data, f, indent=4)
    def load_game(self):
        try:
            with open(SAVE_FILE, 'r') as f: save_data = json.load(f)
            self.game.selected_map, self.game.selected_difficulty = save_data['map_id'], save_data['difficulty']
            self.start_new_game(self.game.selected_map, self.game.selected_difficulty)
            self.money, self.lives, self.current_round = save_data['money'], save_data['lives'], save_data['current_round']
            self.towers = [DogTower.deserialize(data) for data in save_data['towers']]; return True
        except (FileNotFoundError, json.JSONDecodeError): return False
    def delete_save(self):
        if os.path.exists(SAVE_FILE): os.remove(SAVE_FILE)
