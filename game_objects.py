# game_objects.py
import math
import pygame
from assets import DOG_TOWERS, GEOMETRIC_ENEMIES

TIER_TO_ENEMY_ID = {1:"red_triangle", 2:"blue_square", 3:"green_pentagon", 4:"yellow_hexagon", 5:"pink_octagon", 6:"white_decagon", 7:"black_dodecagon", 10:"ceramic_star", 20:"reinforced_star"}

class VisualEffect:
    # --- BUG FIX: Corrected __init__ and added radius ---
    def __init__(self, type, pos, lifetime=0.5, start_pos=None, end_pos=None, radius=0):
        self.type = type
        self.pos = pos
        self.lifetime = lifetime
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.radius = radius
        
    def update(self, dt):
        self.lifetime -= dt
        return self.lifetime > 0

class DogTower:
    # --- (Unchanged) ---
    def __init__(self, tower_id, position):
        self.tower_id, self.pos, self.x, self.y = tower_id, pygame.Vector2(position), position[0], position[1]
        self.base_data = DOG_TOWERS[self.tower_id]
        self.name, self.stats = self.base_data["name"], self.base_data["base_stats"].copy()
        self.upgrades, self.target, self.cooldown, self.total_cost = [0, 0, 0], None, 0, self.base_data["cost"]
        self.rect = pygame.Rect(self.x-25, self.y-25, 50, 50)
        self.targeting_priorities, self.targeting_priority = ["first", "last", "strong", "close"], "first"
        self.pop_count = 0
    def get_stat(self, stat_name): return self.stats.get(stat_name)
    def find_target(self, enemies):
        in_range = [e for e in enemies if self.pos.distance_to(e.pos) <= self.get_stat("range") and ("camo" not in e.properties or self.get_stat("can_see_camo")) and e.tier - e.incoming_damage_tiers > 0]
        if not in_range: self.target = None; return
        if self.targeting_priority == "first": in_range.sort(key=lambda e: e.distance_travelled, reverse=True)
        elif self.targeting_priority == "last": in_range.sort(key=lambda e: e.distance_travelled)
        elif self.targeting_priority == "strong": in_range.sort(key=lambda e: e.tier, reverse=True)
        elif self.targeting_priority == "close": in_range.sort(key=lambda e: self.pos.distance_to(e.pos))
        self.target = in_range[0]
    def update(self, dt, enemies):
        if self.cooldown > 0: self.cooldown -= dt
        self.find_target(enemies)
    def can_attack(self): return self.cooldown <= 0 and self.target and self.stats.get("attack_speed", 0) > 0
    def attack(self, enemies_list, sound_manager):
        self.cooldown = 1.0 / self.get_stat("attack_speed")
        projectiles, visual_effects = [], []
        sound_map = {"corgi_cannon": "shoot_cannon", "greyhound_sniper": "shoot_sniper"}
        sound_manager.play_sound(sound_map.get(self.tower_id, 'shoot_bark'))
        if self.get_stat("is_hitscan"):
            if self.target:
                newly_spawned = self.target.take_damage(self.get_stat("damage_tier_reduction"), self, sound_manager)
                if not self.target.is_active and self.target in enemies_list: enemies_list.remove(self.target)
                enemies_list.extend(newly_spawned)
                visual_effects.append(VisualEffect("line_trail", pos=None, start_pos=self.pos, end_pos=self.target.pos, lifetime=0.1))
        else:
            for _ in range(self.get_stat("projectile_count") or 1):
                if self.target:
                    proj = Projectile(self)
                    projectiles.append(proj); self.target.add_incoming_damage(proj.damage_tier)
        return projectiles, visual_effects
    def cycle_targeting_priority(self): self.targeting_priority = self.targeting_priorities[(self.targeting_priorities.index(self.targeting_priority) + 1) % len(self.targeting_priorities)]
    def apply_upgrade(self, path_index, upgrade_data):
        for stat, value in upgrade_data['stat_changes'].items():
            if isinstance(value,(int,float)) and stat in self.stats and isinstance(self.stats[stat],(int,float)):
                if stat in ["attack_speed","range","blast_radius"]: self.stats[stat] *= value
                else: self.stats[stat] = value
            else: self.stats[stat] = value
    def get_sell_value(self): return int(self.total_cost * 0.7)
    def serialize(self): return {"tower_id":self.tower_id,"position":[self.x,self.y],"upgrades":self.upgrades,"pop_count":self.pop_count,"targeting":self.targeting_priority}
    @staticmethod
    def deserialize(data):
        tower = DogTower(data['tower_id'], data['position'])
        tower.pop_count = data.get("pop_count", 0); tower.targeting_priority = data.get("targeting", "first")
        temp_upgrades = data['upgrades']; tower.upgrades = [0,0,0] 
        for path_index, tier in enumerate(temp_upgrades):
            if tier > 0:
                for i in range(tier):
                    upgrade_data = DOG_TOWERS[tower.tower_id]['upgrades'][f'path{path_index+1}'][i]
                    tower.apply_upgrade(path_index, upgrade_data); tower.total_cost += upgrade_data['cost']; tower.upgrades[path_index] += 1
        return tower

class GeometricEnemy:
    # --- (Unchanged) ---
    def __init__(self, enemy_id, path): self.enemy_id,self.path=enemy_id,path; self.base_data=GEOMETRIC_ENEMIES[self.enemy_id]; self.tier,self.speed_base=self.base_data["tier"],self.base_data["speed"]; self.speed_multiplier=1.0; self.money_on_hit,self.children_on_pop=self.base_data["money"],self.base_data["children"]; self.properties=self.base_data.get("properties",[]).copy(); self.pos=pygame.Vector2(self.path[0]); self.path_index,self.distance_travelled=0,0; self.is_active=True; self.rect=pygame.Rect(self.pos.x-15,self.pos.y-15,30,30); self.incoming_damage_tiers=0; self.status_effects={}
    def update(self, dt):
        self.speed_multiplier = 1.0; effects_to_remove = []
        for effect, timer in self.status_effects.items():
            timer -= dt
            if timer <= 0: effects_to_remove.append(effect)
            else: self.status_effects[effect] = timer; self.speed_multiplier *= 0.5
        for effect in effects_to_remove: del self.status_effects[effect]
        self.move(dt)
    def move(self, dt):
        if not self.is_active or self.path_index >= len(self.path)-1: self.is_active=False; return
        dist_to_move = (self.speed_base * self.speed_multiplier) * 50 * dt
        while dist_to_move > 0 and self.path_index < len(self.path)-1:
            target, seg, seg_len = pygame.Vector2(self.path[self.path_index+1]), pygame.Vector2(self.path[self.path_index+1])-self.pos, (pygame.Vector2(self.path[self.path_index+1])-self.pos).length()
            if seg_len==0: self.path_index+=1; continue
            if dist_to_move >= seg_len: dist_to_move-=seg_len; self.distance_travelled+=seg_len; self.pos,self.path_index=target,self.path_index+1
            else: self.pos+=seg.normalize()*dist_to_move; self.distance_travelled+=dist_to_move; dist_to_move=0
        self.rect.center = self.pos
    def apply_status_effect(self, effect, duration): self.status_effects[effect] = duration
    def take_damage(self, damage, owner_tower, sound_manager):
        can_pop_lead = owner_tower.get_stat("can_pop_lead")
        if "lead" in self.properties and not can_pop_lead: return []
        if "shielded" in self.properties: self.properties.remove("shielded"); return []
        actual_damage=min(self.tier,damage); owner_tower.pop_count+=actual_damage; self.tier-=damage
        sound_manager.play_sound('pop')
        if owner_tower.get_stat("adds_slow"): self.apply_status_effect('slow', owner_tower.get_stat("adds_slow")['duration'])
        if self.tier <= 0:
            self.is_active=False; new_children = []
            for child_id, count in self.children_on_pop.items():
                for _ in range(count): child=GeometricEnemy(child_id,self.path); child.pos,child.path_index,child.distance_travelled=self.pos.copy(),self.path_index,self.distance_travelled; new_children.append(child)
            return new_children
        else:
            new_id = next((TIER_TO_ENEMY_ID[t] for t in sorted(TIER_TO_ENEMY_ID.keys(), reverse=True) if t <= self.tier), None)
            if new_id and new_id != self.enemy_id: self.enemy_id=new_id; self.base_data=GEOMETRIC_ENEMIES[self.enemy_id]; self.speed_base=self.base_data["speed"]; self.money_on_hit,self.children_on_pop=self.base_data["money"],self.base_data["children"]
            return []
    def add_incoming_damage(self, amount): self.incoming_damage_tiers += amount
    def remove_incoming_damage(self, amount): self.incoming_damage_tiers = max(0, self.incoming_damage_tiers - amount)
    def get_tier(self): return GEOMETRIC_ENEMIES[self.enemy_id]['tier']

class Projectile:
    # --- (Unchanged) ---
    def __init__(self, owner_tower):
        self.owner, self.pos, self.target = owner_tower, owner_tower.pos.copy(), owner_tower.target
        self.speed = owner_tower.get_stat("projectile_speed") or 400
        self.damage_tier, self.can_pop_lead = owner_tower.get_stat("damage_tier_reduction"), owner_tower.get_stat("can_pop_lead")
        self.is_active = True; self.is_area_of_effect = owner_tower.get_stat("is_area_of_effect"); self.blast_radius = owner_tower.get_stat("blast_radius")
    def update(self, dt):
        if not self.is_active or not self.target or not self.target.is_active: self.cleanup(); return
        direction = self.target.pos-self.pos
        if direction.length() < self.speed*dt: self.pos = self.target.pos
        else: self.pos += direction.normalize() * self.speed * dt
    def check_collision(self): return self.pos.distance_to(self.target.pos) < 10
    def cleanup(self):
        if self.target and self.is_active: self.target.remove_incoming_damage(self.damage_tier)
        self.is_active, self.target = False, None
