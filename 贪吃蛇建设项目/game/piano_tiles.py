# -*- coding: utf-8 -*-
import pygame
import random
import time
import math
from .constants import *

class PianoTilesGame:
    def __init__(self, surface):
        self.surface = surface
        self.active = True
        self.state = "menu"  # menu, playing, game_over, achievements
        
        # 游戏参数
        self.cols = 4
        surface_width, surface_height = self.surface.get_size()
        self.tile_width = surface_width // self.cols
        self.tile_height = 120
        self.judge_line_y = surface_height - 150
        self.judge_range = 40
        self.feedback_duration = 8
        
        # 按键配置
        self.keys = [pygame.K_d, pygame.K_f, pygame.K_j, pygame.K_k]
        self.key_names = ['D', 'F', 'J', 'K']
        
        # 游戏模式
        self.game_modes = {
            'classic': {'name': '经典模式', 'desc': '标准的钢琴块游戏'},
            'crazy': {'name': '疯狂模式', 'desc': '随机变速和特殊方块'},
            'zen': {'name': '禅境模式', 'desc': '无限模式，放松心情'},
            'challenge': {'name': '挑战模式', 'desc': '限时挑战，考验极限'}
        }
        self.current_mode = 'classic'
        
        # 游戏状态
        self.tiles = []
        self.score = 0
        self.high_scores = self.load_high_scores()
        self.speed = 4
        self.base_speed = 4
        self.col_feedback = [0] * self.cols
        self.error_col = None
        self.error_timer = 0
        
        # 连击系统
        self.combo = 0
        self.max_combo = 0
        self.combo_multiplier = 1.0
        self.combo_effects = []
        
        # 挑战模式参数
        self.time_limit = 60
        self.start_time = None
        self.remaining_time = 0
        
        # 疯狂模式参数
        self.speed_change_timer = 0
        self.speed_change_interval = 180
        
        # 成就系统
        self.achievements = self.load_achievements()
        self.session_stats = {
            'total_hits': 0,
            'perfect_hits': 0,
            'max_combo': 0,
            'games_played': 0
        }
        
        # 视觉效果
        self.animation_time = 0
        self.particle_effects = []
        self.screen_shake = 0
        self.rainbow_mode = False
        self.game_over_reason = ""
        
        # UI元素
        self.menu_buttons = []
        self.init_ui_elements()

    def load_high_scores(self):
        """加载最高分"""
        return {'classic': 0, 'crazy': 0, 'zen': 0, 'challenge': 0}

    def load_achievements(self):
        """加载成就数据"""
        return {
            'first_100': {'name': '初出茅庐', 'desc': '得分达到100', 'unlocked': False},
            'combo_master': {'name': '连击大师', 'desc': '达成100连击', 'unlocked': False},
            'speed_demon': {'name': '速度恶魔', 'desc': '在疯狂模式达到20速度', 'unlocked': False},
            'zen_master': {'name': '禅境大师', 'desc': '在禅境模式坚持10分钟', 'unlocked': False},
            'perfect_game': {'name': '完美游戏', 'desc': '连续击中500个方块', 'unlocked': False}
        }

    def save_high_score(self):
        """保存最高分"""
        if self.score > self.high_scores[self.current_mode]:
            self.high_scores[self.current_mode] = self.score
            
    def check_achievements(self):
        """检查成就"""
        if self.score >= 100 and not self.achievements['first_100']['unlocked']:
            self.achievements['first_100']['unlocked'] = True
            
        if self.combo >= 100 and not self.achievements['combo_master']['unlocked']:
            self.achievements['combo_master']['unlocked'] = True

    def init_ui_elements(self):
        """初始化UI元素"""
        surface_width, surface_height = self.surface.get_size()
        button_width = 200
        button_height = 50
        start_y = surface_height // 2 - 100
        
        self.menu_buttons = [
            {'text': '开始游戏', 'rect': pygame.Rect((surface_width - button_width) // 2, start_y, button_width, button_height), 'action': 'start'},
            {'text': '游戏模式', 'rect': pygame.Rect((surface_width - button_width) // 2, start_y + 60, button_width, button_height), 'action': 'modes'},
            {'text': '成就系统', 'rect': pygame.Rect((surface_width - button_width) // 2, start_y + 120, button_width, button_height), 'action': 'achievements'},
            {'text': '返回活动', 'rect': pygame.Rect((surface_width - button_width) // 2, start_y + 180, button_width, button_height), 'action': 'back'}
        ]

    def get_speed(self):
        """根据分数和模式计算速度"""
        if self.current_mode == 'classic':
            return self.base_speed + self.score // 10
        elif self.current_mode == 'crazy':
            if self.speed_change_timer <= 0:
                self.speed_change_timer = self.speed_change_interval
                return self.base_speed + random.randint(-2, 8) + self.score // 15
            return self.speed
        elif self.current_mode == 'zen':
            return max(3, self.base_speed + self.score // 20)
        elif self.current_mode == 'challenge':
            return self.base_speed + self.score // 5
        return self.base_speed

    def spawn_tile(self):
        """生成新的方块"""
        col = random.randint(0, self.cols - 1)
        tile_type = 'normal'
        if self.current_mode == 'crazy' and random.random() < 0.1:
            tile_type = random.choice(['bonus', 'speed', 'rainbow'])
        
        tile = {
            'col': col,
            'y': -self.tile_height,
            'hit': False,
            'type': tile_type,
            'color': self.get_tile_color(tile_type),
            'bonus_score': 1 if tile_type == 'normal' else random.randint(2, 5)
        }
        self.tiles.append(tile)
        
    def get_tile_color(self, tile_type):
        """获取方块颜色"""
        if tile_type == 'bonus':
            return (255, 215, 0)
        elif tile_type == 'speed':
            return (255, 0, 255)
        elif tile_type == 'rainbow':
            return (255, 100, 100)
        else:
            return (30, 30, 30)

    def hsv_to_rgb(self, h, s, v):
        """HSV转RGB"""
        h = h / 60.0
        i = int(h)
        f = h - i
        p = v * (1 - s)
        q = v * (1 - s * f)
        t = v * (1 - s * (1 - f))
        
        if i == 0:
            r, g, b = v, t, p
        elif i == 1:
            r, g, b = q, v, p
        elif i == 2:
            r, g, b = p, v, t
        elif i == 3:
            r, g, b = p, q, v
        elif i == 4:
            r, g, b = t, p, v
        else:
            r, g, b = v, p, q
            
        return (int(r * 255), int(g * 255), int(b * 255))

    def update(self):
        """更新游戏状态"""
        self.animation_time += 0.1
        
        if self.screen_shake > 0:
            self.screen_shake -= 1
            
        for i in range(self.cols):
            if self.col_feedback[i] > 0:
                self.col_feedback[i] -= 1
        
        if self.error_timer > 0:
            self.error_timer -= 1
        
        self.combo_effects = [e for e in self.combo_effects if e['life'] > 0]
        for effect in self.combo_effects:
            effect['y'] -= 2
            effect['life'] -= 1
        
        self.particle_effects = [p for p in self.particle_effects if p['life'] > 0]
        for particle in self.particle_effects:
            particle['x'] += particle['vx']
            particle['y'] += particle['vy']
            particle['life'] -= 1
            particle['vy'] += 0.2
        
        if self.current_mode == 'crazy':
            self.speed_change_timer -= 1
            if self.speed_change_timer <= 0:
                self.speed = self.get_speed()
        else:
            self.speed = self.get_speed()
        
        if self.state == "playing":
            if self.current_mode == 'challenge':
                if self.start_time:
                    elapsed = time.time() - self.start_time
                    self.remaining_time = max(0, self.time_limit - elapsed)
                    if self.remaining_time <= 0:
                        self.game_over(None, "时间到！")
                        return
            
            for tile in self.tiles:
                tile['y'] += self.speed
                
                if tile['type'] == 'rainbow':
                    hue = (self.animation_time * 50) % 360
                    tile['color'] = self.hsv_to_rgb(hue, 1, 1)
            
            surface_width, surface_height = self.surface.get_size()
            for tile in self.tiles[:]:
                if tile['y'] > surface_height and not tile['hit']:
                    if self.current_mode != 'zen':
                        self.game_over(tile['col'])
                        break
                    else:
                        self.combo = 0
                        self.tiles.remove(tile)
                elif tile['y'] > surface_height:
                    self.tiles.remove(tile)
            
            if not self.tiles or self.tiles[-1]['y'] > self.tile_height:
                self.spawn_tile()

    def draw(self):
        """绘制游戏"""
        if self.state == "menu":
            self.draw_menu()
        elif self.state == "achievements":
            self.draw_achievements()
        else:
            self.draw_game()
            
    def draw_menu(self):
        """绘制主菜单"""
        surface_width, surface_height = self.surface.get_size()
        
        # 动态渐变背景
        for y in range(surface_height):
            color_ratio = y / surface_height
            wave = math.sin(self.animation_time + y * 0.01) * 10
            r = int(230 + 25 * color_ratio + wave)
            g = int(240 + 15 * color_ratio + wave)
            b = int(255 + 5 * color_ratio + wave)
            r = max(0, min(255, r))
            g = max(0, min(255, g))
            b = max(0, min(255, b))
            pygame.draw.line(self.surface, (r, g, b), (0, y), (surface_width, y))
        
        # 标题区域背景
        title_bg = pygame.Rect(0, 20, surface_width, 120)
        pygame.draw.rect(self.surface, (255, 255, 255, 180), title_bg)
        pygame.draw.rect(self.surface, (100, 150, 255), title_bg, 3)
        
        # 标题
        title_font = pygame.font.Font(FONT_NAME, 52)
        title_text = title_font.render("♫ 手残大师 ♫", True, (50, 50, 150))
        title_rect = title_text.get_rect(center=(surface_width // 2, 80))
        self.surface.blit(title_text, title_rect)
        
        # 副标题
        subtitle_font = pygame.font.Font(FONT_NAME, 18)
        subtitle_text = subtitle_font.render("节奏感挑战游戏", True, (100, 100, 100))
        subtitle_rect = subtitle_text.get_rect(center=(surface_width // 2, 115))
        self.surface.blit(subtitle_text, subtitle_rect)
        
        # 模式选择区域
        mode_area_y = 160
        self.draw_mode_selection(mode_area_y)
        
        # 统计信息面板
        self.draw_stats_panel(mode_area_y + 180)
        
        # 操作按钮
        self.draw_menu_buttons(surface_height - 150)
        
        # 操作提示
        self.draw_controls_hint()

    def draw_mode_selection(self, start_y):
        """绘制模式选择区域"""
        surface_width = self.surface.get_size()[0]
        
        # 模式选择标题
        title_font = pygame.font.Font(FONT_NAME, 28)
        title_text = title_font.render("选择游戏模式", True, (50, 50, 150))
        title_rect = title_text.get_rect(center=(surface_width // 2, start_y))
        self.surface.blit(title_text, title_rect)
        
        # 模式卡片
        modes = list(self.game_modes.keys())
        card_width = 160
        card_height = 120
        total_width = len(modes) * card_width + (len(modes) - 1) * 20
        start_x = (surface_width - total_width) // 2
        
        mouse_pos = pygame.mouse.get_pos()
        
        for i, mode in enumerate(modes):
            x = start_x + i * (card_width + 20)
            y = start_y + 40
            
            card_rect = pygame.Rect(x, y, card_width, card_height)
            
            # 卡片选中状态
            is_selected = mode == self.current_mode
            is_hovered = card_rect.collidepoint(mouse_pos)
            
            # 卡片背景
            if is_selected:
                bg_color = (100, 200, 255, 220)
                border_color = (50, 150, 255)
                border_width = 4
            elif is_hovered:
                bg_color = (200, 230, 255, 180)
                border_color = (100, 150, 255)
                border_width = 3
            else:
                bg_color = (255, 255, 255, 150)
                border_color = (150, 150, 150)
                border_width = 2
            
            # 绘制卡片阴影
            shadow_rect = pygame.Rect(x + 3, y + 3, card_width, card_height)
            pygame.draw.rect(self.surface, (0, 0, 0, 50), shadow_rect, border_radius=12)
            
            # 绘制卡片
            bg_surface = pygame.Surface((card_width, card_height), pygame.SRCALPHA)
            pygame.draw.rect(bg_surface, bg_color, (0, 0, card_width, card_height), border_radius=12)
            self.surface.blit(bg_surface, (x, y))
            pygame.draw.rect(self.surface, border_color, card_rect, border_width, border_radius=12)
            
            # 模式图标
            icon_y = y + 15
            self.draw_mode_icon(mode, x + card_width // 2, icon_y + 20)
            
            # 模式名称
            name_font = pygame.font.Font(FONT_NAME, 18)
            name_text = name_font.render(self.game_modes[mode]['name'], True, (50, 50, 50))
            name_rect = name_text.get_rect(center=(x + card_width // 2, y + 65))
            self.surface.blit(name_text, name_rect)
            
            # 最高分
            score_font = pygame.font.Font(FONT_NAME, 14)
            high_score = self.high_scores.get(mode, 0)
            score_text = score_font.render(f"最高: {high_score}", True, (100, 100, 100))
            score_rect = score_text.get_rect(center=(x + card_width // 2, y + 85))
            self.surface.blit(score_text, score_rect)
            
            # 选中指示器
            if is_selected:
                indicator_y = y + card_height + 10
                pygame.draw.circle(self.surface, (255, 215, 0), (x + card_width // 2, indicator_y), 6)
                pygame.draw.circle(self.surface, (200, 150, 0), (x + card_width // 2, indicator_y), 6, 2)
                
                # 模式描述
                desc_font = pygame.font.Font(FONT_NAME, 16)
                desc_text = desc_font.render(self.game_modes[mode]['desc'], True, (80, 80, 80))
                desc_rect = desc_text.get_rect(center=(surface_width // 2, indicator_y + 25))
                self.surface.blit(desc_text, desc_rect)
            
            # 存储卡片区域用于点击检测
            if not hasattr(self, 'mode_cards'):
                self.mode_cards = {}
            self.mode_cards[mode] = card_rect

    def draw_mode_icon(self, mode, x, y):
        """绘制模式图标"""
        if mode == 'classic':
            # 经典模式 - 音符图标
            pygame.draw.ellipse(self.surface, (50, 50, 50), (x-8, y-8, 16, 12))
            pygame.draw.rect(self.surface, (50, 50, 50), (x+6, y-8, 3, 20))
        elif mode == 'crazy':
            # 疯狂模式 - 闪电图标
            points = [(x-6, y-8), (x+2, y-2), (x-2, y-2), (x+6, y+8), (x-2, y+2), (x+2, y+2)]
            pygame.draw.polygon(self.surface, (255, 100, 100), points)
        elif mode == 'zen':
            # 禅境模式 - 莲花图标
            for i in range(8):
                angle = i * math.pi / 4
                petal_x = x + math.cos(angle) * 8
                petal_y = y + math.sin(angle) * 8
                pygame.draw.circle(self.surface, (100, 255, 100), (int(petal_x), int(petal_y)), 4)
            pygame.draw.circle(self.surface, (255, 255, 100), (x, y), 6)
        elif mode == 'challenge':
            # 挑战模式 - 时钟图标
            pygame.draw.circle(self.surface, (255, 150, 0), (x, y), 10, 2)
            pygame.draw.line(self.surface, (255, 150, 0), (x, y), (x, y-6), 2)
            pygame.draw.line(self.surface, (255, 150, 0), (x, y), (x+4, y-2), 2)

    def draw_stats_panel(self, start_y):
        """绘制统计信息面板"""
        surface_width = self.surface.get_size()[0]
        
        panel_width = 300
        panel_height = 80
        panel_x = (surface_width - panel_width) // 2
        
        # 面板背景
        panel_rect = pygame.Rect(panel_x, start_y, panel_width, panel_height)
        bg_surface = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        pygame.draw.rect(bg_surface, (255, 255, 255, 200), (0, 0, panel_width, panel_height), border_radius=15)
        self.surface.blit(bg_surface, (panel_x, start_y))
        pygame.draw.rect(self.surface, (150, 150, 150), panel_rect, 2, border_radius=15)
        
        # 统计信息
        stats_font = pygame.font.Font(FONT_NAME, 16)
        
        # 当前模式最高分
        current_high = self.high_scores.get(self.current_mode, 0)
        high_text = stats_font.render(f"当前模式最高分: {current_high}", True, (80, 80, 80))
        self.surface.blit(high_text, (panel_x + 20, start_y + 15))
        
        # 总游戏次数
        total_games = self.session_stats.get('games_played', 0)
        games_text = stats_font.render(f"本次游戏次数: {total_games}", True, (80, 80, 80))
        self.surface.blit(games_text, (panel_x + 20, start_y + 35))
        
        # 最大连击
        max_combo = self.session_stats.get('max_combo', 0)
        combo_text = stats_font.render(f"最大连击: {max_combo}", True, (80, 80, 80))
        self.surface.blit(combo_text, (panel_x + 20, start_y + 55))

    def draw_menu_buttons(self, start_y):
        """绘制菜单按钮"""
        surface_width = self.surface.get_size()[0]
        
        button_width = 120
        button_height = 40
        button_spacing = 20
        total_width = 3 * button_width + 2 * button_spacing
        start_x = (surface_width - total_width) // 2
        
        buttons = [
            {'text': '开始游戏', 'color': (100, 200, 100), 'action': 'start'},
            {'text': '成就系统', 'color': (255, 180, 100), 'action': 'achievements'},
            {'text': '返回活动', 'color': (255, 100, 100), 'action': 'back'}
        ]
        
        mouse_pos = pygame.mouse.get_pos()
        
        for i, button_info in enumerate(buttons):
            x = start_x + i * (button_width + button_spacing)
            y = start_y
            
            button_rect = pygame.Rect(x, y, button_width, button_height)
            is_hovered = button_rect.collidepoint(mouse_pos)
            
            # 按钮颜色
            base_color = button_info['color']
            if is_hovered:
                color = tuple(min(255, c + 30) for c in base_color)
                shadow_offset = 2
            else:
                color = base_color
                shadow_offset = 4
            
            # 按钮阴影
            shadow_rect = pygame.Rect(x + shadow_offset, y + shadow_offset, button_width, button_height)
            pygame.draw.rect(self.surface, (0, 0, 0, 100), shadow_rect, border_radius=8)
            
            # 按钮主体
            pygame.draw.rect(self.surface, color, button_rect, border_radius=8)
            pygame.draw.rect(self.surface, (50, 50, 50), button_rect, 2, border_radius=8)
            
            # 按钮文字
            text_font = pygame.font.Font(FONT_NAME, 18)
            text = text_font.render(button_info['text'], True, (255, 255, 255))
            text_rect = text.get_rect(center=button_rect.center)
            self.surface.blit(text, text_rect)
            
            # 更新按钮信息用于点击检测
            for button in self.menu_buttons:
                if button['action'] == button_info['action']:
                    button['rect'] = button_rect
                    break

    def draw_controls_hint(self):
        """绘制操作提示"""
        surface_width, surface_height = self.surface.get_size()
        
        hints = [
            "← → 或 A D: 切换模式",
            "回车键: 开始游戏",
            "Tab键: 查看成就",
            "ESC键: 返回活动页面"
        ]
        
        hint_font = pygame.font.Font(FONT_NAME, 14)
        start_y = surface_height - 80
        
        for i, hint in enumerate(hints):
            hint_text = hint_font.render(hint, True, (120, 120, 120))
            self.surface.blit(hint_text, (20, start_y + i * 18))

    def draw_game(self):
        """绘制游戏界面"""
        surface_width, surface_height = self.surface.get_size()
        
        # 屏幕震动效果
        shake_x = random.randint(-self.screen_shake//2, self.screen_shake//2) if self.screen_shake > 0 else 0
        shake_y = random.randint(-self.screen_shake//2, self.screen_shake//2) if self.screen_shake > 0 else 0
        
        # 渐变背景
        for y in range(surface_height):
            color_ratio = y / surface_height
            if self.rainbow_mode:
                hue = (y + self.animation_time * 10) % 360
                r, g, b = self.hsv_to_rgb(hue, 0.3, 0.9)
            else:
                r = int(240 + 15 * color_ratio)
                g = int(240 + 15 * color_ratio)
                b = int(250 + 5 * color_ratio)
            pygame.draw.line(self.surface, (r, g, b), (shake_x, y + shake_y), (surface_width + shake_x, y + shake_y))
        
        # 绘制分割线
        for i in range(1, self.cols):
            x = i * self.tile_width + shake_x
            pygame.draw.line(self.surface, (200, 200, 200), (x, shake_y), (x, surface_height + shake_y), 2)
        
        # 绘制判定区域
        self.draw_judge_zone(shake_x, shake_y)
        
        # 绘制方块
        for tile in self.tiles:
            if not tile['hit']:
                self.draw_tile(tile, shake_x, shake_y)
        
        # 绘制粒子效果
        for particle in self.particle_effects:
            pygame.draw.circle(self.surface, particle['color'], 
                             (int(particle['x'] + shake_x), int(particle['y'] + shake_y)), 3)
        
        # 绘制连击效果
        for effect in self.combo_effects:
            font_size = int(24 + effect['scale'] * 10)
            font = pygame.font.Font(FONT_NAME, font_size)
            text = font.render(f"COMBO x{effect['combo']}", True, (255, 215, 0))
            alpha = int(255 * effect['life'] / 60)
            text.set_alpha(alpha)
            self.surface.blit(text, (effect['x'] - text.get_width()//2, effect['y']))
        
        # 绘制底部按键
        self.draw_bottom_keys(shake_x, shake_y)
        
        # 绘制UI
        self.draw_ui()
        
        # 绘制游戏结束界面
        if self.state == "game_over":
            self.draw_game_over()

    def draw_judge_zone(self, shake_x=0, shake_y=0):
        """绘制判定区域"""
        surface_width, surface_height = self.surface.get_size()
        for i in range(self.judge_range * 2):
            alpha = 100 - abs(i - self.judge_range) * 2
            color = (100, 200, 255, alpha) if self.error_timer == 0 else (255, 100, 100, alpha)

            y = self.judge_line_y - self.judge_range + i + shake_y
            if 0 <= y < surface_height:
                s = pygame.Surface((surface_width, 1), pygame.SRCALPHA)
                s.fill(color)
                self.surface.blit(s, (shake_x, y))

        # 判定线
        line_color = (0, 180, 255) if self.error_timer == 0 else (255, 80, 80)
        pygame.draw.line(self.surface, line_color,
                        (shake_x, self.judge_line_y + shake_y), (surface_width + shake_x, self.judge_line_y + shake_y), 4)

    def draw_tile(self, tile, shake_x=0, shake_y=0):
        """绘制方块"""
        rect = pygame.Rect(tile['col'] * self.tile_width + shake_x, tile['y'] + shake_y, 
                          self.tile_width - 2, self.tile_height)
        
        # 方块颜色
        color = tile.get('color', (30, 30, 30))
        
        # 方块主体
        pygame.draw.rect(self.surface, color, rect)
        
        # 方块边框
        border_color = (255, 255, 255) if tile['type'] != 'normal' else (0, 0, 0)
        pygame.draw.rect(self.surface, border_color, rect, 2)
        
        # 特殊方块标识
        if tile['type'] == 'bonus':
            center = rect.center
            pygame.draw.circle(self.surface, (255, 255, 0), center, 15)
            pygame.draw.circle(self.surface, (200, 200, 0), center, 15, 2)
            font = pygame.font.Font(FONT_NAME, 20)
            text = font.render("$", True, (150, 150, 0))
            text_rect = text.get_rect(center=center)
            self.surface.blit(text, text_rect)
        elif tile['type'] == 'speed':
            center = rect.center
            points = [(center[0], center[1]-10), (center[0]+8, center[1]+5), (center[0]-8, center[1]+5)]
            pygame.draw.polygon(self.surface, (255, 255, 255), points)
        elif tile['type'] == 'rainbow':
            for i in range(5):
                inner_rect = pygame.Rect(rect.x + i*2, rect.y + i*2, rect.width - i*4, rect.height - i*4)
                hue = (self.animation_time * 100 + i * 60) % 360
                rainbow_color = self.hsv_to_rgb(hue, 1, 1)
                if inner_rect.width > 0 and inner_rect.height > 0:
                    pygame.draw.rect(self.surface, rainbow_color, inner_rect, 2)

    def draw_bottom_keys(self, shake_x=0, shake_y=0):
        """绘制底部按键"""
        surface_width, surface_height = self.surface.get_size()
        key_height = 50
        key_y = surface_height - key_height + shake_y
        
        for i in range(self.cols):
            x = i * self.tile_width + shake_x
            
            # 按键颜色
            if self.error_col == i and self.error_timer > 0:
                color = (255, 100, 100)
            elif self.col_feedback[i] > 0:
                color = (100, 255, 100)
            else:
                color = (220, 220, 220)
            
            # 按键矩形
            key_rect = pygame.Rect(x + 2, key_y, self.tile_width - 4, key_height)
            pygame.draw.rect(self.surface, color, key_rect, border_radius=8)
            pygame.draw.rect(self.surface, (100, 100, 100), key_rect, 2, border_radius=8)
            
            # 按键文字
            font = pygame.font.Font(FONT_NAME, 24)
            text = font.render(self.key_names[i], True, (0, 0, 0))
            text_rect = text.get_rect(center=key_rect.center)
            self.surface.blit(text, text_rect)

    def draw_ui(self):
        """绘制UI信息"""
        # 分数
        score_font = pygame.font.Font(FONT_NAME, 32)
        score_text = score_font.render(f"分数: {self.score}", True, (50, 50, 50))
        self.surface.blit(score_text, (20, 20))
        
        # 连击
        if self.combo > 0:
            combo_font = pygame.font.Font(FONT_NAME, 28)
            combo_color = (255, 100, 100) if self.combo >= 50 else (100, 255, 100) if self.combo >= 20 else (100, 100, 255)
            combo_text = combo_font.render(f"连击: {self.combo}", True, combo_color)
            self.surface.blit(combo_text, (20, 60))
        
        # 最高分
        high_score = self.high_scores.get(self.current_mode, 0)
        high_score_font = pygame.font.Font(FONT_NAME, 20)
        high_score_text = high_score_font.render(f"最高分: {high_score}", True, (100, 100, 100))
        self.surface.blit(high_score_text, (20, 100))
        
        # 速度
        speed_text = high_score_font.render(f"速度: {self.speed}", True, (100, 100, 100))
        self.surface.blit(speed_text, (20, 125))
        
        # 模式信息
        mode_text = high_score_font.render(f"模式: {self.game_modes[self.current_mode]['name']}", True, (100, 100, 100))
        self.surface.blit(mode_text, (20, 150))
        
        # 挑战模式倒计时
        if self.current_mode == 'challenge' and self.remaining_time > 0:
            time_font = pygame.font.Font(FONT_NAME, 36)
            time_color = (255, 50, 50) if self.remaining_time < 10 else (50, 50, 50)
            time_text = time_font.render(f"时间: {int(self.remaining_time)}", True, time_color)
            surface_width = self.surface.get_size()[0]
            time_rect = time_text.get_rect(center=(surface_width // 2, 50))
            self.surface.blit(time_text, time_rect)
        
        # 操作提示
        surface_width, surface_height = self.surface.get_size()
        hint_font = pygame.font.Font(FONT_NAME, 16)
        hint_text = hint_font.render("使用 D F J K 键击打黑块", True, (150, 150, 150))
        self.surface.blit(hint_text, (20, surface_height - 120))
        
        # ESC返回提示
        esc_text = hint_font.render("ESC - 返回菜单", True, (150, 150, 150))
        self.surface.blit(esc_text, (surface_width - 120, 20))

    def draw_game_over(self):
        """绘制游戏结束界面"""
        surface_width, surface_height = self.surface.get_size()
        # 半透明遮罩
        overlay = pygame.Surface((surface_width, surface_height), pygame.SRCALPHA)
        pygame.draw.rect(overlay, (0, 0, 0, 150), (0, 0, surface_width, surface_height))
        self.surface.blit(overlay, (0, 0))

        # 游戏结束面板
        panel_width = 400
        panel_height = 300
        panel_x = (surface_width - panel_width) // 2
        panel_y = (surface_height - panel_height) // 2
        
        panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)
        pygame.draw.rect(self.surface, (250, 250, 250), panel_rect, border_radius=15)
        pygame.draw.rect(self.surface, (200, 200, 200), panel_rect, 3, border_radius=15)
        
        # 游戏结束文字
        game_over_font = pygame.font.Font(FONT_NAME, 36)
        reason = getattr(self, 'game_over_reason', '游戏结束')
        game_over_text = game_over_font.render(reason, True, (255, 50, 50))
        game_over_rect = game_over_text.get_rect(center=(panel_x + panel_width//2, panel_y + 50))
        self.surface.blit(game_over_text, game_over_rect)
        
        # 最终分数
        final_score_font = pygame.font.Font(FONT_NAME, 24)
        final_score_text = final_score_font.render(f"最终分数: {self.score}", True, (50, 50, 50))
        final_score_rect = final_score_text.get_rect(center=(panel_x + panel_width//2, panel_y + 100))
        self.surface.blit(final_score_text, final_score_rect)
        
        # 最大连击
        max_combo_text = final_score_font.render(f"最大连击: {self.combo}", True, (50, 50, 50))
        max_combo_rect = max_combo_text.get_rect(center=(panel_x + panel_width//2, panel_y + 130))
        self.surface.blit(max_combo_text, max_combo_rect)
        
        # 模式信息
        mode_text = pygame.font.Font(FONT_NAME, 20).render(f"模式: {self.game_modes[self.current_mode]['name']}", True, (100, 100, 100))
        mode_rect = mode_text.get_rect(center=(panel_x + panel_width//2, panel_y + 160))
        self.surface.blit(mode_text, mode_rect)
        
        # 新纪录提示
        if self.score > 0 and self.score == self.high_scores[self.current_mode]:
            new_record_font = pygame.font.Font(FONT_NAME, 20)
            new_record_text = new_record_font.render("★ 新纪录! ★", True, (255, 215, 0))
            new_record_rect = new_record_text.get_rect(center=(panel_x + panel_width//2, panel_y + 190))
            self.surface.blit(new_record_text, new_record_rect)
        
        # 操作提示
        hint_font = pygame.font.Font(FONT_NAME, 18)
        hint_text = hint_font.render("空格键重新开始，ESC键返回菜单", True, (100, 100, 100))
        hint_rect = hint_text.get_rect(center=(panel_x + panel_width//2, panel_y + 240))
        self.surface.blit(hint_text, hint_rect)

    def draw_achievements(self):
        """绘制成就界面"""
        surface_width, surface_height = self.surface.get_size()
        
        # 渐变背景
        for y in range(surface_height):
            color_ratio = y / surface_height
            r = int(240 + 15 * color_ratio)
            g = int(240 + 15 * color_ratio)
            b = int(250 + 5 * color_ratio)
            pygame.draw.line(self.surface, (r, g, b), (0, y), (surface_width, y))
        
        # 标题
        title_font = pygame.font.Font(FONT_NAME, 36)
        title_text = title_font.render("成就系统", True, (50, 50, 150))
        title_rect = title_text.get_rect(center=(surface_width // 2, 50))
        self.surface.blit(title_text, title_rect)
        
        # 成就列表
        y_offset = 120
        for achievement_id, achievement in self.achievements.items():
            # 成就背景
            rect = pygame.Rect(50, y_offset, surface_width - 100, 60)
            color = (200, 255, 200) if achievement['unlocked'] else (200, 200, 200)
            pygame.draw.rect(self.surface, color, rect, border_radius=10)
            pygame.draw.rect(self.surface, (100, 100, 100), rect, 2, border_radius=10)
            
            # 成就名称
            name_font = pygame.font.Font(FONT_NAME, 24)
            name_text = name_font.render(achievement['name'], True, (50, 50, 50))
            self.surface.blit(name_text, (70, y_offset + 5))
            
            # 成就描述
            desc_font = pygame.font.Font(FONT_NAME, 16)
            desc_text = desc_font.render(achievement['desc'], True, (100, 100, 100))
            self.surface.blit(desc_text, (70, y_offset + 30))
            
            # 解锁状态
            status_text = "✓" if achievement['unlocked'] else "✗"
            status_color = (0, 150, 0) if achievement['unlocked'] else (150, 0, 0)
            status_font = pygame.font.Font(FONT_NAME, 36)
            status_render = status_font.render(status_text, True, status_color)
            self.surface.blit(status_render, (surface_width - 100, y_offset + 10))
            
            y_offset += 80
        
        # 返回按钮
        back_rect = pygame.Rect(50, surface_height - 80, 100, 40)
        mouse_pos = pygame.mouse.get_pos()
        color = (100, 150, 255) if back_rect.collidepoint(mouse_pos) else (150, 150, 150)
        pygame.draw.rect(self.surface, color, back_rect, border_radius=10)
        pygame.draw.rect(self.surface, (50, 50, 50), back_rect, 2, border_radius=10)
        
        back_text = pygame.font.Font(FONT_NAME, 20).render("返回", True, (255, 255, 255))
        back_text_rect = back_text.get_rect(center=back_rect.center)
        self.surface.blit(back_text, back_text_rect)

    def handle_event(self, event):
        """处理事件"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if self.state == "menu":
                    self.active = False
                else:
                    self.state = "menu"
            elif event.key == pygame.K_SPACE:
                if self.state == "game_over":
                    self.restart_game()
                elif self.state == "menu":
                    self.start_game()
            elif self.state == "playing":
                # 检查按键
                for i, key in enumerate(self.keys):
                    if event.key == key:
                        self.handle_key_press(i)
                        break
            elif self.state == "menu":
                # 模式切换
                if event.key == pygame.K_LEFT or event.key == pygame.K_a:
                    self.change_mode(-1)
                elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                    self.change_mode(1)
                elif event.key == pygame.K_RETURN:
                    self.start_game()
                elif event.key == pygame.K_TAB:
                    self.state = "achievements"
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # 左键
                mouse_pos = pygame.mouse.get_pos()
                if self.state == "menu":
                    # 检查模式卡片点击
                    if hasattr(self, 'mode_cards'):
                        for mode, card_rect in self.mode_cards.items():
                            if card_rect.collidepoint(mouse_pos):
                                self.current_mode = mode
                                return
                    
                    # 检查菜单按钮点击
                    for button in self.menu_buttons:
                        if button['rect'].collidepoint(mouse_pos):
                            if button['action'] == 'start':
                                self.start_game()
                            elif button['action'] == 'modes':
                                self.cycle_game_mode()
                            elif button['action'] == 'achievements':
                                self.state = "achievements"
                            elif button['action'] == 'back':
                                self.active = False
                elif self.state == "achievements":
                    # 返回按钮
                    surface_width, surface_height = self.surface.get_size()
                    back_rect = pygame.Rect(50, surface_height - 80, 100, 40)
                    if back_rect.collidepoint(mouse_pos):
                        self.state = "menu"
    
    def change_mode(self, direction):
        """切换游戏模式"""
        modes = list(self.game_modes.keys())
        current_index = modes.index(self.current_mode)
        new_index = (current_index + direction) % len(modes)
        self.current_mode = modes[new_index]
        
    def cycle_game_mode(self):
        """循环切换游戏模式"""
        modes = list(self.game_modes.keys())
        current_index = modes.index(self.current_mode)
        new_index = (current_index + 1) % len(modes)
        self.current_mode = modes[new_index]
        
    def start_game(self):
        """开始游戏"""
        self.restart_game()
        self.state = "playing"

    def game_over(self, error_col, reason="游戏结束"):
        """游戏结束"""
        self.state = "game_over"
        self.error_col = error_col
        self.error_timer = 30
        self.game_over_reason = reason
        self.save_high_score()
        
        self.session_stats['games_played'] += 1
        if self.combo > self.session_stats['max_combo']:
            self.session_stats['max_combo'] = self.combo
        if self.combo > self.max_combo:
            self.max_combo = self.combo
            
        self.check_achievements()
        self.screen_shake = 20

    def handle_key_press(self, col):
        """处理按键"""
        if self.state != "playing":
            return
            
        self.col_feedback[col] = self.feedback_duration
        
        hit = False
        perfect_hit = False
        
        for tile in self.tiles:
            if (tile['col'] == col and 
                tile['y'] + self.tile_height > self.judge_line_y - self.judge_range and
                tile['y'] < self.judge_line_y + self.judge_range and
                not tile['hit']):
                
                tile['hit'] = True
                hit = True
                
                hit_distance = abs((tile['y'] + self.tile_height // 2) - self.judge_line_y)
                if hit_distance < self.judge_range // 3:
                    perfect_hit = True
                    self.session_stats['perfect_hits'] += 1
                
                base_score = tile.get('bonus_score', 1)
                combo_bonus = min(self.combo // 10, 5)
                final_score = base_score + combo_bonus
                
                self.score += final_score
                self.combo += 1
                
                self.combo_multiplier = 1.0 + (self.combo / 100.0)
                
                if tile['type'] == 'speed':
                    self.base_speed = max(2, self.base_speed - 1)
                elif tile['type'] == 'rainbow':
                    self.rainbow_mode = True
                    self.add_rainbow_effect(col)
                
                self.add_hit_effect(col, tile['type'], perfect_hit)
                
                if self.combo > 5:
                    self.add_combo_effect(col)
                
                self.session_stats['total_hits'] += 1
                break
        
        if not hit:
            if self.current_mode != 'zen':
                self.game_over(col)
            else:
                self.combo = 0
                self.add_miss_effect(col)

    def add_hit_effect(self, col, tile_type='normal', perfect=False):
        """添加击中特效"""
        x = col * self.tile_width + self.tile_width // 2
        y = self.judge_line_y
        
        particle_count = 12 if perfect else 8
        if tile_type == 'bonus':
            particle_count *= 2
            base_color = (255, 215, 0)
        elif tile_type == 'speed':
            base_color = (255, 0, 255)
        elif tile_type == 'rainbow':
            base_color = (255, 100, 100)
        else:
            base_color = (255, 255, 100)
        
        for _ in range(particle_count):
            color = base_color if tile_type != 'rainbow' else (
                random.randint(100, 255),
                random.randint(100, 255),
                random.randint(100, 255)
            )
            
            self.particle_effects.append({
                'x': x + random.uniform(-10, 10),
                'y': y + random.uniform(-10, 10),
                'vx': random.uniform(-4, 4),
                'vy': random.uniform(-6, -2),
                'life': 25 if perfect else 20,
                'color': color
            })
            
    def add_combo_effect(self, col):
        """添加连击特效"""
        x = col * self.tile_width + self.tile_width // 2
        y = self.judge_line_y - 50
        
        self.combo_effects.append({
            'x': x,
            'y': y,
            'combo': self.combo,
            'life': 60,
            'scale': 1.0
        })
        
    def add_rainbow_effect(self, col):
        """添加彩虹特效"""
        x = col * self.tile_width + self.tile_width // 2
        y = self.judge_line_y
        
        for _ in range(20):
            hue = random.randint(0, 360)
            color = self.hsv_to_rgb(hue, 1, 1)
            self.particle_effects.append({
                'x': x,
                'y': y,
                'vx': random.uniform(-5, 5),
                'vy': random.uniform(-8, -3),
                'life': 30,
                'color': color
            })
            
    def add_miss_effect(self, col):
        """添加错过特效"""
        x = col * self.tile_width + self.tile_width // 2
        y = self.judge_line_y
        
        for _ in range(5):
            self.particle_effects.append({
                'x': x,
                'y': y,
                'vx': random.uniform(-2, 2),
                'vy': random.uniform(-3, -1),
                'life': 15,
                'color': (150, 150, 150)
            })

    def restart_game(self):
        """重新开始游戏"""
        self.tiles = []
        self.score = 0
        self.combo = 0
        self.combo_multiplier = 1.0
        self.state = "playing"
        self.col_feedback = [0] * self.cols
        self.error_col = None
        self.error_timer = 0
        self.particle_effects = []
        self.combo_effects = []
        self.screen_shake = 0
        self.rainbow_mode = False
        self.base_speed = 4
        self.speed = 4
        self.speed_change_timer = self.speed_change_interval
        
        if self.current_mode == 'challenge':
            self.start_time = time.time()
            self.remaining_time = self.time_limit
        else:
            self.start_time = None
        
        self.spawn_tile()