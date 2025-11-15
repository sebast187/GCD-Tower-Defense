# renderer.py
import pygame, re, math
from assets import DOG_TOWERS, GEOMETRIC_ENEMIES, MAPS, ROUND_COMPOSITIONS, UI_ICONS, UI_ASSETS, MAP_DECORATIONS
from utilities import COLOR_PALETTES, SCREEN_HEIGHT, SCREEN_WIDTH, PLAYABLE_WIDTH

class Renderer:
    def __init__(self, screen):
        self.screen = screen
        self._font_cache = {}
        self._shape_cache = {}
        self._map_previews = {}

    def get_font(self, size, bold=False):
        key = (size, bold)
        if key not in self._font_cache: self._font_cache[key] = pygame.font.SysFont("Arial", size, bold=bold)
        return self._font_cache[key]

    def draw_text(self, text, x, y, color, size, bold=False, align="center"):
        font = self.get_font(size, bold)
        text_surface = font.render(text, True, color)
        text_rect = text_surface.get_rect()
        if align == "center": text_rect.center = (x, y)
        elif align == "left": text_rect.midleft = (x, y)
        elif align == "right": text_rect.midright = (x, y)
        self.screen.blit(text_surface, text_rect)
        
    def draw_main_menu(self, ui_manager):
        self.screen.fill((20, 30, 40))
        self.draw_text("Geometric Canine Defense", SCREEN_WIDTH//2, 100, COLOR_PALETTES['default']['primary_text'], 64, True, "center")
        self.draw_text("Select a Map", SCREEN_WIDTH//2, 200, COLOR_PALETTES['default']['secondary_text'], 32, align="center")
        for button in ui_manager.buttons:
            if button.id.startswith("map_"):
                map_id = button.id.split('_', 1)[1]
                preview_surface = self._get_map_preview(map_id)
                self.screen.blit(preview_surface, button.rect.topleft)
                if button.is_selected or button.is_hovered: pygame.draw.rect(self.screen, COLOR_PALETTES['default']['success'], button.rect, 4, border_radius=5)
                self.draw_text(MAPS[map_id]['name'], button.rect.centerx, button.rect.bottom + 10, COLOR_PALETTES['default']['primary_text'], 14, True, "center")
            else: button.draw(self.screen)
            
    def draw_game_state(self, game_engine, ui_manager):
        self._draw_map(game_engine.map_data)
        if ui_manager.placing_tower_type: self._draw_placement_preview(ui_manager, game_engine)
        if ui_manager.selected_tower: self._draw_range_circle(ui_manager.selected_tower)
        
        for tower in game_engine.towers: self._draw_asset(tower, DOG_TOWERS, scale=1.2)
        for enemy in game_engine.enemies: self._draw_asset(enemy, GEOMETRIC_ENEMIES)
        for proj in game_engine.projectiles: pygame.draw.circle(self.screen, (255, 255, 0), proj.pos, 4)
        
        for effect in game_engine.visual_effects:
            if effect.type == "line_trail":
                alpha = max(0, min(255, int(255 * (effect.lifetime / 0.1)))); start, end = effect.start_pos, effect.end_pos
                line_rect = pygame.Rect(min(start.x, end.x), min(start.y, end.y), abs(start.x-end.x)+1, abs(start.y-end.y)+1)
                line_surf = pygame.Surface(line_rect.size, pygame.SRCALPHA); pygame.draw.line(line_surf, (255,255,255,alpha), (start.x-line_rect.x, start.y-line_rect.y), (end.x-line_rect.x, end.y-line_rect.y), 3); self.screen.blit(line_surf, line_rect)

        self._draw_hud(game_engine, ui_manager)
        
        side_panel_clip = pygame.Rect(1150, 50, 130, SCREEN_HEIGHT-50)
        for button in ui_manager.buttons:
            if button.id.startswith("buy_"):
                if button.rect.colliderect(side_panel_clip):
                    original_clip = self.screen.get_clip(); self.screen.set_clip(side_panel_clip); button.draw(self.screen)
                    tower_id = button.id.split('_', 1)[1]; dummy_tower = type('obj', (object,), {'tower_id': tower_id, 'upgrades': [0,0,0]})
                    self._draw_asset(dummy_tower, DOG_TOWERS, scale=0.9, pos_override=(button.rect.centerx, button.rect.y+35))
                    self.draw_text(f"${DOG_TOWERS[tower_id]['cost']}", button.rect.centerx, button.rect.bottom - 15, (255,255,255), 14, True, "center")
                    self.draw_text(DOG_TOWERS[tower_id]['name'], button.rect.centerx, button.rect.bottom - 30, (255,255,255), 10, "center")
                    self.screen.set_clip(original_clip)
            elif button.is_active or (button.id.startswith("upgrade_") and ui_manager.selected_tower): 
                button.draw(self.screen)
        
        for button in ui_manager.buttons:
            if button.id == "fast_forward" and button.is_active: self._draw_asset(type('obj',(object,),{'enemy_id':'fast_forward','upgrades':(0,0,0)})(), UI_ICONS, pos_override=button.rect.center, scale=0.8)
            elif button.id == "cancel_placement" and button.is_active: self._draw_asset(type('obj',(object,),{'enemy_id':'garbage_can','upgrades':(0,0,0)})(), UI_ICONS, pos_override=button.rect.center, scale=1.0)
                
    def draw_pause_menu(self, ui_manager):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        self.draw_text("Paused", SCREEN_WIDTH//2, 150, (255,255,255), 64, True, "center")
        for button in ui_manager.buttons: button.draw(self.screen)

    def draw_settings_menu(self, ui_manager, sound_manager):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 220))
        self.screen.blit(overlay, (0, 0))
        self.draw_text("Settings", SCREEN_WIDTH//2, 150, (255,255,255), 64, True, "center")
        for slider in ui_manager.sliders: slider.draw(self.screen, self)
        for button in ui_manager.buttons: button.draw(self.screen)
                
    def _draw_map(self, map_data):
        theme = COLOR_PALETTES['map_themes'][map_data['theme']]
        self.screen.fill(COLOR_PALETTES['default']['background'])
        pygame.draw.rect(self.screen, theme['background'], (0, 0, PLAYABLE_WIDTH, SCREEN_HEIGHT))
        for decoration_id, positions in map_data.get("decorations", {}).items():
            for pos in positions: self._draw_asset(type('obj',(object,),{'enemy_id':decoration_id,'upgrades':(0,0,0)})(), MAP_DECORATIONS, pos_override=pos)
        for area in map_data.get("water_areas", []):
            color = theme.get('lava') if area.get('is_lava') else theme['water']
            if area['shape'] == 'rect': pygame.draw.rect(self.screen, color, (area['x'], area['y'], area['width'], area['height']))
            elif area['shape'] == 'circle': pygame.draw.circle(self.screen, color, (area['cx'], area['cy']), area['r'])
        paths = [p for k, p in map_data.items() if k.startswith('path')]
        for path in paths:
            if len(path) > 1: path_color=theme['path']; border_color=tuple(max(0,c-20) for c in path_color); pygame.draw.lines(self.screen, border_color, False, path, width=84); pygame.draw.lines(self.screen, path_color, False, path, width=80)
    
    def _get_map_preview(self, map_id):
        if map_id not in self._map_previews:
            map_data, preview_surface = MAPS[map_id], pygame.Surface((200, 100)); theme = COLOR_PALETTES['map_themes'][map_data['theme']]
            preview_surface.fill(theme['background']); scale_x, scale_y = 200/PLAYABLE_WIDTH, 100/SCREEN_HEIGHT
            paths = [p for k, p in map_data.items() if k.startswith('path')]
            for path in paths:
                if len(path)>1: pygame.draw.lines(preview_surface, theme['path'], False, [(p[0]*scale_x,p[1]*scale_y) for p in path], width=8)
            self._map_previews[map_id] = preview_surface
        return self._map_previews[map_id]

    def _draw_hud(self, game_engine, ui_manager):
        self._draw_asset(type('obj',(object,),{'tower_id':'side_panel_bg','upgrades':(0,0,0)})(), UI_ASSETS, pos_override=(1150,0))
        if ui_manager.selected_tower: self._draw_asset(type('obj',(object,),{'tower_id':'upgrade_panel_bg','upgrades':(0,0,0)})(), UI_ASSETS, pos_override=(10,470))
        pygame.draw.rect(self.screen, COLOR_PALETTES['default']['panel_background'], (0,0,SCREEN_WIDTH,50))
        self._draw_asset(type('obj',(object,),{'enemy_id':'heart','upgrades':(0,0,0)})(), UI_ICONS, pos_override=(190,25), scale=0.7)
        self.draw_text(f"{game_engine.lives}", 220, 25, COLOR_PALETTES['default']['primary_text'], 24, True, "left")
        self.draw_text(f"$ {game_engine.money}", 20, 25, COLOR_PALETTES['default']['success'], 24, True, "left")
        self.draw_text(f"Round: {game_engine.current_round}", SCREEN_WIDTH-20, 25, COLOR_PALETTES['default']['primary_text'], 24, True, "right")
        if ui_manager.selected_tower:
            tower = ui_manager.selected_tower
            self.draw_text(f"{tower.name}", 115, 490, COLOR_PALETTES['default']['primary_text'], 22, True, "center")
            self.draw_text(f"Pops: {tower.pop_count}", 115, 515, COLOR_PALETTES['default']['secondary_text'], 16, align="center")
            self._draw_asset(tower, DOG_TOWERS, scale=2.0, pos_override=(115, 580))
            
    def _draw_asset(self, entity, asset_dict, scale=1.0, pos_override=None):
        entity_id=entity.tower_id if hasattr(entity,'tower_id') else entity.enemy_id; pos=pos_override or entity.pos; upgrades_tuple=tuple(entity.upgrades) if hasattr(entity,'upgrades') else (0,0,0); cache_key=(entity_id,scale,upgrades_tuple)
        if cache_key not in self._shape_cache:
            asset_data, svg_data_root = asset_dict[entity_id], asset_dict[entity_id].get('svg_params') or asset_dict[entity_id].get('svg')
            if not svg_data_root: return
            all_svg_parts = dict(svg_data_root)
            if hasattr(entity, 'upgrades'):
                for path_index, tier in enumerate(entity.upgrades):
                    for i in range(1, tier + 1):
                        if f"{path_index+1}_{i}" in asset_data.get("upgrade_svgs", {}): all_svg_parts.update(asset_data["upgrade_svgs"][f"{path_index+1}_{i}"])
            all_points_str=re.findall(r"-?\d+\.?\d*", str(all_svg_parts)); coords=[abs(float(p)) for p in all_points_str] if all_points_str else [30]
            max_dim=int(max(coords)*2.5*scale) if coords else int(60*scale); size=(max_dim, max_dim)
            asset_surface=pygame.Surface(size,pygame.SRCALPHA); center=pygame.Vector2(size[0]//2,size[1]//2)
            if 'shape' in all_svg_parts: self._draw_svg_shape(asset_surface, all_svg_parts, center, scale)
            else:
                for part_name in sorted(all_svg_parts.keys()): self._draw_svg_shape(asset_surface, all_svg_parts[part_name], center, scale)
            self._shape_cache[cache_key]=asset_surface
        cached_surface=self._shape_cache[cache_key]; draw_rect=cached_surface.get_rect(center=pos); self.screen.blit(cached_surface,draw_rect)
        
    def _draw_svg_shape(self, surface, params, offset, scale):
        color, stroke_color=params.get('fill'), params.get('stroke'); stroke_width=int(params.get('stroke_width',1)*scale) if params.get('stroke_width',1)>0 else 0
        def scale_pt(pt, off): return (pt[0]*scale + off.x, pt[1]*scale + off.y)
        shape_type = params.get('shape')
        if not shape_type: return
        if shape_type == 'polygon':
            points_list = [float(p) for p in params['points'].replace(",", " ").split()]; points=[scale_pt((points_list[i], points_list[i+1]), offset) for i in range(0,len(points_list),2)]
            if color: pygame.draw.polygon(surface, color, points)
            if stroke_color and stroke_width > 0: pygame.draw.polygon(surface, stroke_color, points, stroke_width)
        elif shape_type == 'circle':
            pos, radius = (params.get('cx',0)*scale+offset.x, params.get('cy',0)*scale+offset.y), int(params.get('r',0)*scale)
            if radius > 0:
                if color: pygame.draw.circle(surface, color, pos, radius)
                if stroke_color and stroke_width > 0: pygame.draw.circle(surface, stroke_color, pos, radius, stroke_width)
        elif shape_type == 'rect':
             rect = pygame.Rect(params['x']*scale+offset.x, params['y']*scale+offset.y, params['width']*scale, params['height']*scale)
             if color: pygame.draw.rect(surface, color, rect)
             if stroke_color and stroke_width > 0: pygame.draw.rect(surface, stroke_color, rect, stroke_width)
        elif shape_type == 'path':
            for subpath in self._parse_svg_path(params.get('d',"")):
                scaled_points = [scale_pt(p, offset) for p in subpath['points']]
                if len(scaled_points)>1:
                    is_closed = subpath['closed']
                    if len(scaled_points)>2 and is_closed and color: pygame.draw.polygon(surface, color, scaled_points)
                    if stroke_color and stroke_width > 0: pygame.draw.lines(surface, stroke_color, is_closed, scaled_points, stroke_width)
    
    def _parse_svg_path(self, path_string, steps=15):
        tokens=re.findall(r"([MmLlHhVvCcSsQqTtAaZz])|(-?\d+(?:\.\d+)?)",path_string); subpaths,current_subpath,i=[],None,0; current_pos,path_start=pygame.Vector2(0,0),pygame.Vector2(0,0)
        while i<len(tokens):
            cmd_char=tokens[i][0]; i+=1;
            if not cmd_char: continue
            is_relative=cmd_char.islower(); cmd_type=cmd_char.lower()
            def get_params(count):
                nonlocal i; params=[]
                while len(params)<count and i<len(tokens) and not tokens[i][0]:params.append(float(tokens[i][1])); i+=1
                return params
            implicit_cmd='l' if cmd_type=='m' else cmd_type
            while True:
                params=get_params({'m':2,'l':2,'h':1,'v':1,'c':6,'q':4,'s':4,'t':2,'z':0}.get(cmd_type,0))
                if not params and cmd_type not in 'z': break
                if cmd_type=='m':
                    if current_subpath:subpaths.append(current_subpath)
                    current_subpath={'points':[],'closed':False}; current_pos=current_pos+params if is_relative else pygame.Vector2(params); path_start=current_pos; current_subpath['points'].append(path_start)
                elif cmd_type=='l': current_pos=current_pos+params if is_relative else pygame.Vector2(params); current_subpath['points'].append(current_pos)
                elif cmd_type=='h': current_pos.x=current_pos.x+params[0] if is_relative else params[0]; current_subpath['points'].append(current_pos.copy())
                elif cmd_type=='v': current_pos.y=current_pos.y+params[0] if is_relative else params[0]; current_subpath['points'].append(current_pos.copy())
                elif cmd_type=='c':
                    p1,p2,p3=(current_pos+params[0:2] if is_relative else pygame.Vector2(params[0:2])),(current_pos+params[2:4] if is_relative else pygame.Vector2(params[2:4])),(current_pos+params[4:6] if is_relative else pygame.Vector2(params[4:6]))
                    for t in[i/steps for i in range(1,steps+1)]:omt=1-t;current_subpath['points'].append((omt**3*current_pos)+(3*omt**2*t*p1)+(3*omt*t**2*p2)+(t**3*p3))
                    current_pos=p3
                elif cmd_type=='q':
                    p1,p2=(current_pos+params[0:2] if is_relative else pygame.Vector2(params[0:2])),(current_pos+params[2:4] if is_relative else pygame.Vector2(params[2:4]))
                    for t in[i/steps for i in range(1,steps+1)]:omt=1-t;current_subpath['points'].append((omt**2*current_pos)+(2*omt*t*p1)+(t**2*p2))
                    current_pos=p2
                elif cmd_type=='z':
                    if current_subpath:current_subpath['closed']=True
                cmd_type=implicit_cmd
                if i>=len(tokens) or tokens[i][0]:break
        if current_subpath:subpaths.append(current_subpath)
        return subpaths
        
    def _draw_range_circle(self,tower):
        radius=int(tower.get_stat('range'));s=pygame.Surface((radius*2,radius*2),pygame.SRCALPHA);pygame.draw.circle(s,(100,100,100,80),(radius,radius),radius);pygame.draw.circle(s,(255,255,255,120),(radius,radius),radius,2);self.screen.blit(s,(tower.x-radius,tower.y-radius))
    
    def _draw_placement_preview(self,ui_manager,game_engine):
        pos,tower_id=ui_manager.mouse_pos,ui_manager.placing_tower_type;dummy_tower=type('obj',(object,),{'tower_id':tower_id,'upgrades':[0,0,0]});self._draw_asset(dummy_tower,DOG_TOWERS,scale=1.2,pos_override=pos);radius=DOG_TOWERS[tower_id]['base_stats']['range'];s=pygame.Surface((radius*2,radius*2),pygame.SRCALPHA);is_valid=game_engine.is_valid_placement(tower_id,pos);color=(100,255,100,60) if is_valid else (255,100,100,60);pygame.draw.circle(s,color,(radius,radius),radius);pygame.draw.circle(s,(255,255,255,100),(radius,radius),radius,2);self.screen.blit(s,(pos[0]-radius,pos[1]-radius))
