import pygame
import random
import time
import json
import os
from .constants import *

# 俄罗斯方块形状定义
TETROMINOS = [
    [[1, 1, 1, 1]],  # I
    [[1, 1], [1, 1]],  # O
    [[1, 1, 1], [0, 1, 0]],  # T
    [[1, 1, 1], [1, 0, 0]],  # L
    [[1, 1, 1], [0, 0, 1]],  # J
    [[1, 1, 0], [0, 1, 1]],  # S
    [[0, 1, 1], [1, 1, 0]]   # Z
]

# 方块颜色 - 简化的颜色
TETROMINO_COLORS = [
    (0, 240, 255),   # I - 亮青色
    (255, 215, 0),   # O - 金色
    (147, 112, 219), # T - 紫色
    (255, 140, 0),   # L - 深橙色
    (30, 144, 255),  # J - 道奇蓝
    (50, 205, 50),   # S - 酸橙绿
    (220, 20, 60)    # Z - 猩红色
]

# 难度设置
DIFFICULTY_LEVELS = {
    1: {"name": "简单", "drop_speed": 1000, "color": (50, 205, 50)},
    2: {"name": "普通", "drop_speed": 700, "color": (255, 215, 0)},
    3: {"name": "困难", "drop_speed": 500, "color": (255, 140, 0)},
    4: {"name": "专家", "drop_speed": 300, "color": (220, 20, 60)},
    5: {"name": "大师", "drop_speed": 150, "color": (147, 112, 219)}
}

class TetrisGame:
    def __init__(self, surface):
        self.surface = surface
        self.active = True
        self.game_state = "difficulty_select"  # difficulty_select, playing, paused, game_over
        
        # 游戏区域设置
        self.grid_width = 10
        self.grid_height = 20
        self.cell_size = 32
        self.grid_x = (WINDOW_WIDTH - self.grid_width * self.cell_size) // 2
        self.grid_y = 120
        
        # 游戏状态
        self.grid = [[0 for _ in range(self.grid_width)] for _ in range(self.grid_height)]
        self.current_piece = None
        self.current_x = 0
        self.current_y = 0
        self.current_color = None
        self.next_piece = None
        self.next_color = None
        self.score = 0
        self.selected_difficulty = 1
        self.drop_speed = DIFFICULTY_LEVELS[1]["drop_speed"]
        self.lines_cleared = 0
        self.high_score = self.load_high_score()
        
        # 时间控制
        self.last_drop = time.time()
        
        # 字体
        self.font_large = pygame.font.Font(FONT_NAME, 42)
        self.font_medium = pygame.font.Font(FONT_NAME, 28)
        self.font_small = pygame.font.Font(FONT_NAME, 20)
        
        # 按键控制
        self.key_interval = 200  # 重复间隔
        self.last_key_press = {}
        
    def load_high_score(self):
        """加载最高分"""
        try:
            with open('player_data.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('tetris_high_score', 0)
        except:
            return 0
    
    def start_game(self):
        """开始游戏"""
        self.game_state = "playing"
        self.score = 0
        self.lines_cleared = 0
        self.grid = [[0 for _ in range(self.grid_width)] for _ in range(self.grid_height)]
        self.drop_speed = DIFFICULTY_LEVELS[self.selected_difficulty]["drop_speed"]
        self.generate_next_piece()
        self.new_piece()
        self.last_drop = time.time()
    
    def generate_next_piece(self):
        """生成下一个方块"""
        piece_index = random.randint(0, len(TETROMINOS) - 1)
        self.next_piece = [row[:] for row in TETROMINOS[piece_index]]
        self.next_color = TETROMINO_COLORS[piece_index]
    
    def new_piece(self):
        """生成新的方块"""
        # 使用下一个方块作为当前方块
        self.current_piece = self.next_piece
        self.current_color = self.next_color
        self.current_x = self.grid_width // 2 - len(self.current_piece[0]) // 2
        self.current_y = 0
        
        # 生成新的下一个方块
        self.generate_next_piece()
        
        # 检查游戏是否结束
        if not self.is_valid_position(self.current_x, self.current_y):
            self.game_state = "game_over"
            # 保存最高分
            if self.score > self.high_score:
                self.high_score = self.score
                self.save_high_score()
    
    def is_valid_position(self, x, y, piece=None):
        """检查位置是否有效"""
        if piece is None:
            piece = self.current_piece
            
        for row in range(len(piece)):
            for col in range(len(piece[0])):
                if piece[row][col]:
                    new_x = x + col
                    new_y = y + row
                    if (new_x < 0 or new_x >= self.grid_width or 
                        new_y >= self.grid_height or 
                        (new_y >= 0 and self.grid[new_y][new_x])):
                        return False
        return True
    
    def rotate_piece(self):
        """旋转当前方块"""
        if not self.current_piece:
            return
            
        # 转置矩阵然后反转每一行
        rotated = list(zip(*self.current_piece[::-1]))
        rotated = [list(row) for row in rotated]
        
        if self.is_valid_position(self.current_x, self.current_y, rotated):
            self.current_piece = rotated
    
    def move_piece(self, dx, dy):
        """移动当前方块"""
        if self.is_valid_position(self.current_x + dx, self.current_y + dy):
            self.current_x += dx
            self.current_y += dy
            return True
        return False
    
    def drop_piece(self):
        """快速下落当前方块"""
        while self.move_piece(0, 1):
            pass
        self.lock_piece()
    
    def lock_piece(self):
        """锁定当前方块到网格中"""
        for row in range(len(self.current_piece)):
            for col in range(len(self.current_piece[0])):
                if self.current_piece[row][col]:
                    grid_y = self.current_y + row
                    grid_x = self.current_x + col
                    if grid_y >= 0:
                        self.grid[grid_y][grid_x] = self.current_color
        
        self.clear_lines()
        self.new_piece()
    
    def clear_lines(self):
        """清除完整的行"""
        lines_to_clear = []
        for row in range(self.grid_height):
            if all(self.grid[row]):
                lines_to_clear.append(row)
        
        if lines_to_clear:
            # 计算分数 - 多行消除奖励
            lines_count = len(lines_to_clear)
            self.lines_cleared += lines_count
            
            # 基础分数
            base_score = lines_count * 100 * self.selected_difficulty
            
            # 多行消除奖励
            if lines_count == 2:
                bonus_multiplier = 1.5  # 双行消除奖励
            elif lines_count == 3:
                bonus_multiplier = 2.0  # 三行消除奖励
            elif lines_count == 4:
                bonus_multiplier = 3.0  # 四行消除奖励（俄罗斯方块）
            else:
                bonus_multiplier = 1.0
            
            self.score += int(base_score * bonus_multiplier)
            
            # 立即清除行
            for row in lines_to_clear:
                del self.grid[row]
                self.grid.insert(0, [0 for _ in range(self.grid_width)])
    
    def update(self):
        """更新游戏状态"""
        if self.game_state != "playing":
            return
            
        current_time = time.time()
        
        # 自动下落 - 固定速度，不随等级增加
        if current_time - self.last_drop > self.drop_speed / 1000:
            if not self.move_piece(0, 1):
                self.lock_piece()
            self.last_drop = current_time
    
    def handle_event(self, event):
        """处理游戏事件"""
        if self.game_state == "difficulty_select":
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    self.selected_difficulty = max(1, self.selected_difficulty - 1)
                elif event.key == pygame.K_DOWN:
                    self.selected_difficulty = min(5, self.selected_difficulty + 1)
                elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                    self.start_game()
                elif event.key == pygame.K_ESCAPE:
                    self.active = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # 左键点击
                    mouse_x, mouse_y = event.pos
                    
                    # 马卡龙风格布局的难度卡片检测
                    panel_width = 500
                    panel_height = 620
                    panel_x = (WINDOW_WIDTH - panel_width) // 2
                    panel_y = (WINDOW_HEIGHT - panel_height) // 2
                    
                    card_start_y = panel_y + 200
                    card_width = 400
                    card_height = 55
                    card_spacing = 20
                    
                    # 检查是否点击了难度选项卡片
                    for i in range(1, 6):
                        card_y = card_start_y + (i - 1) * (card_height + card_spacing)
                        card_x = (WINDOW_WIDTH - card_width) // 2
                        card_rect = pygame.Rect(card_x, card_y, card_width, card_height)
                        
                        if card_rect.collidepoint(mouse_x, mouse_y):
                            self.selected_difficulty = i
                            self.start_game()  # 点击难度选项直接开始游戏
                            break
                    
                    # 检查是否点击了返回按钮
                    button_y = panel_y + panel_height - 80
                    button_width = 200
                    button_height = 50
                    button_x = (WINDOW_WIDTH - button_width) // 2
                    back_button_rect = pygame.Rect(button_x, button_y, button_width, button_height)
                    
                    if back_button_rect.collidepoint(mouse_x, mouse_y):
                        self.active = False  # 返回活动页面
            return
            
        if self.game_state == "game_over":
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.active = False
                elif event.key == pygame.K_r:
                    self.game_state = "difficulty_select"
            return
            
        if self.game_state == "paused":
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.active = False
                elif event.key == pygame.K_SPACE:
                    self.game_state = "playing"
            return
            
        if event.type == pygame.KEYDOWN:
            current_time = time.time()
            
            if event.key == pygame.K_LEFT or event.key == pygame.K_a:
                if self.move_piece(-1, 0):
                    # 统一使用方向键作为记录键
                    self.last_key_press[pygame.K_LEFT] = current_time
            elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                if self.move_piece(1, 0):
                    # 统一使用方向键作为记录键
                    self.last_key_press[pygame.K_RIGHT] = current_time
            elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                if self.move_piece(0, 1):
                    # 统一使用方向键作为记录键
                    self.last_key_press[pygame.K_DOWN] = current_time
            elif event.key == pygame.K_UP or event.key == pygame.K_w:
                self.rotate_piece()
            elif event.key == pygame.K_SPACE:
                self.drop_piece()
            elif event.key == pygame.K_p:
                self.game_state = "paused"
            elif event.key == pygame.K_ESCAPE:
                self.active = False
        
        elif event.type == pygame.KEYUP:
            # 处理按键释放，WASD键和方向键统一处理
            if event.key == pygame.K_LEFT or event.key == pygame.K_a:
                if pygame.K_LEFT in self.last_key_press:
                    del self.last_key_press[pygame.K_LEFT]
            elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                if pygame.K_RIGHT in self.last_key_press:
                    del self.last_key_press[pygame.K_RIGHT]
            elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                if pygame.K_DOWN in self.last_key_press:
                    del self.last_key_press[pygame.K_DOWN]
    
    def handle_key_repeat(self):
        """处理按键重复"""
        if self.game_state != "playing":
            return
            
        current_time = time.time()
        keys = pygame.key.get_pressed()
        
        # 检查方向键和WASD键的重复
        for direction, keys_list in [
            (pygame.K_LEFT, [pygame.K_LEFT, pygame.K_a]),
            (pygame.K_RIGHT, [pygame.K_RIGHT, pygame.K_d]),
            (pygame.K_DOWN, [pygame.K_DOWN, pygame.K_s])
        ]:
            # 检查是否有任何一个键被按下
            if any(keys[key] for key in keys_list):
                if direction not in self.last_key_press:
                    # 第一次按下
                    if direction == pygame.K_LEFT:
                        self.move_piece(-1, 0)
                    elif direction == pygame.K_RIGHT:
                        self.move_piece(1, 0)
                    elif direction == pygame.K_DOWN:
                        self.move_piece(0, 1)
                    self.last_key_press[direction] = current_time
                elif current_time - self.last_key_press[direction] > self.key_interval / 1000:
                    # 重复按键
                    if direction == pygame.K_LEFT:
                        self.move_piece(-1, 0)
                    elif direction == pygame.K_RIGHT:
                        self.move_piece(1, 0)
                    elif direction == pygame.K_DOWN:
                        self.move_piece(0, 1)
                    self.last_key_press[direction] = current_time
    
    def draw_background(self):
        """绘制渐变背景"""
        # 创建渐变背景
        for y in range(WINDOW_HEIGHT):
            # 从深蓝到黑色的渐变
            ratio = y / WINDOW_HEIGHT
            r = int(20 + (0 - 20) * ratio)
            g = int(40 + (0 - 40) * ratio)
            b = int(80 + (0 - 80) * ratio)
            pygame.draw.line(self.surface, (r, g, b), (0, y), (WINDOW_WIDTH, y))
    
    def draw_grid(self):
        """绘制游戏网格"""
        # 绘制网格背景
        grid_rect = pygame.Rect(self.grid_x - 4, self.grid_y - 4, 
                               self.grid_width * self.cell_size + 8, 
                               self.grid_height * self.cell_size + 8)
        
        # 主边框
        pygame.draw.rect(self.surface, (100, 100, 100), grid_rect, border_radius=8)
        
        # 内部背景
        inner_rect = pygame.Rect(self.grid_x - 2, self.grid_y - 2, 
                                self.grid_width * self.cell_size + 4, 
                                self.grid_height * self.cell_size + 4)
        pygame.draw.rect(self.surface, (20, 20, 40), inner_rect, border_radius=6)
        
        # 绘制网格线
        for x in range(self.grid_width + 1):
            pygame.draw.line(self.surface, (60, 60, 80), 
                           (self.grid_x + x * self.cell_size, self.grid_y),
                           (self.grid_x + x * self.cell_size, self.grid_y + self.grid_height * self.cell_size))
        
        for y in range(self.grid_height + 1):
            pygame.draw.line(self.surface, (60, 60, 80), 
                           (self.grid_x, self.grid_y + y * self.cell_size),
                           (self.grid_x + self.grid_width * self.cell_size, self.grid_y + y * self.cell_size))
        
        # 绘制已放置的方块
        for y in range(self.grid_height):
            for x in range(self.grid_width):
                if self.grid[y][x]:  # 确保不是0（空位置）
                    cell_rect = pygame.Rect(self.grid_x + x * self.cell_size + 1,
                                          self.grid_y + y * self.cell_size + 1,
                                          self.cell_size - 2, self.cell_size - 2)
                    
                    # 绘制主方块
                    pygame.draw.rect(self.surface, self.grid[y][x], cell_rect, border_radius=4)
                    pygame.draw.rect(self.surface, (255, 255, 255), cell_rect, 1, border_radius=4)
    
    def draw_current_piece(self):
        """绘制当前方块"""
        if not self.current_piece:
            return
            
        for row in range(len(self.current_piece)):
            for col in range(len(self.current_piece[0])):
                if self.current_piece[row][col]:
                    x = self.current_x + col
                    y = self.current_y + row
                    if y >= 0:
                        cell_rect = pygame.Rect(self.grid_x + x * self.cell_size + 1,
                                              self.grid_y + y * self.cell_size + 1,
                                              self.cell_size - 2, self.cell_size - 2)
                        
                        # 绘制主方块
                        pygame.draw.rect(self.surface, self.current_color, cell_rect, border_radius=4)
                        pygame.draw.rect(self.surface, (255, 255, 255), cell_rect, 2, border_radius=4)
    
    def draw_ui(self):
        """绘制用户界面"""
        # 左侧信息面板
        panel_x = 50
        panel_y = 120
        panel_width = 300
        panel_height = 400
        
        # 面板背景
        panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)
        panel_surface = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        pygame.draw.rect(panel_surface, (0, 0, 0, 120), (0, 0, panel_width, panel_height), border_radius=15)
        pygame.draw.rect(panel_surface, (255, 255, 255, 30), (0, 0, panel_width, panel_height), 2, border_radius=15)
        self.surface.blit(panel_surface, panel_rect)
        
        # 游戏标题
        title_text = self.font_large.render("俄罗斯方块", True, (255, 255, 255))
        self.surface.blit(title_text, (panel_x + 20, panel_y + 20))
        
        # 分数
        score_text = self.font_medium.render(f"分数: {self.score:,}", True, (255, 215, 0))
        self.surface.blit(score_text, (panel_x + 20, panel_y + 80))
        
        # 难度等级
        difficulty_text = self.font_medium.render(f"难度: {DIFFICULTY_LEVELS[self.selected_difficulty]['name']}", True, (100, 200, 255))
        self.surface.blit(difficulty_text, (panel_x + 20, panel_y + 120))
        
        # 消除行数
        lines_text = self.font_medium.render(f"消除行数: {self.lines_cleared}", True, (255, 100, 100))
        self.surface.blit(lines_text, (panel_x + 20, panel_y + 160))
        
        # 最高分
        high_score_text = self.font_medium.render(f"最高分: {self.high_score:,}", True, (255, 255, 0))
        self.surface.blit(high_score_text, (panel_x + 20, panel_y + 200))
        
        
        
        # 右侧信息面板
        right_panel_x = WINDOW_WIDTH - 350
        right_panel_y = 120
        right_panel_width = 300
        right_panel_height = 300
        
        # 右侧面板背景
        right_panel_rect = pygame.Rect(right_panel_x, right_panel_y, right_panel_width, right_panel_height)
        right_panel_surface = pygame.Surface((right_panel_width, right_panel_height), pygame.SRCALPHA)
        pygame.draw.rect(right_panel_surface, (0, 0, 0, 120), (0, 0, right_panel_width, right_panel_height), border_radius=15)
        pygame.draw.rect(right_panel_surface, (255, 255, 255, 30), (0, 0, right_panel_width, right_panel_height), 2, border_radius=15)
        self.surface.blit(right_panel_surface, right_panel_rect)
        
        # 下一个方块预览
        preview_text = self.font_medium.render("下一个方块", True, (255, 255, 255))
        self.surface.blit(preview_text, (right_panel_x + 20, right_panel_y + 20))
        
        # 绘制下一个方块预览
        if self.next_piece:
            preview_x = right_panel_x + 100
            preview_y = right_panel_y + 80
            preview_size = 20
            
            for row in range(len(self.next_piece)):
                for col in range(len(self.next_piece[0])):
                    if self.next_piece[row][col]:
                        block_rect = pygame.Rect(preview_x + col * preview_size, 
                                               preview_y + row * preview_size, 
                                               preview_size - 1, preview_size - 1)
                        pygame.draw.rect(self.surface, self.next_color, block_rect, border_radius=2)
                        pygame.draw.rect(self.surface, (255, 255, 255), block_rect, 1, border_radius=2)
    
    def draw_difficulty_select_screen(self):
        """绘制马卡龙风格的难度选择界面"""
        # 马卡龙风格渐变背景：浅粉 -> 浅紫 -> 浅青
        for y in range(WINDOW_HEIGHT):
            progress = y / WINDOW_HEIGHT
            
            # 三段式马卡龙渐变
            if progress < 0.33:  # 上部分：浅粉色
                sub_progress = progress / 0.33
                r = int(255 - sub_progress * 35)  # 255 -> 220
                g = int(182 + sub_progress * 18)  # 182 -> 200
                b = int(193 + sub_progress * 32)  # 193 -> 225
            elif progress < 0.66:  # 中部分：浅紫色
                sub_progress = (progress - 0.33) / 0.33
                r = int(220 - sub_progress * 50)  # 220 -> 170
                g = int(200 + sub_progress * 20)  # 200 -> 220
                b = int(225 + sub_progress * 30)  # 225 -> 255
            else:  # 下部分：浅青色
                sub_progress = (progress - 0.66) / 0.34
                r = int(170 - sub_progress * 35)  # 170 -> 135
                g = int(220 + sub_progress * 35)  # 220 -> 255
                b = int(255 - sub_progress * 25)  # 255 -> 230
                
            color = (max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b)))
            pygame.draw.line(self.surface, color, (0, y), (WINDOW_WIDTH, y))
        
        # 添加马卡龙风格的装饰气泡
        import math
        time_offset = pygame.time.get_ticks() / 1000.0
        bubble_colors = [
            (255, 182, 193, 60),  # 浅粉
            (230, 190, 255, 55),  # 浅紫
            (173, 216, 230, 50),  # 浅蓝
            (255, 218, 185, 45),  # 浅橙
            (144, 238, 144, 40),  # 浅绿
        ]
        
        for i in range(12):
            x = int(WINDOW_WIDTH * 0.1 + (i % 4) * WINDOW_WIDTH * 0.25)
            y = int(WINDOW_HEIGHT * 0.15 + (i // 4) * WINDOW_HEIGHT * 0.3)
            # 添加浮动动画
            float_y = y + int(math.sin(time_offset * 1.5 + i * 0.5) * 8)
            size = 25 + int(math.sin(time_offset * 0.8 + i) * 8)
            color = bubble_colors[i % len(bubble_colors)]
            
            # 绘制气泡
            bubble_surface = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
            pygame.draw.circle(bubble_surface, color, (size, size), size)
            # 添加高光效果
            pygame.draw.circle(bubble_surface, (255, 255, 255, 30), (size - size//3, size - size//3), size//3)
            self.surface.blit(bubble_surface, (x - size, float_y - size))
        
        # 主面板 - 马卡龙卡片风格
        panel_width = 500
        panel_height = 620
        panel_x = (WINDOW_WIDTH - panel_width) // 2
        panel_y = (WINDOW_HEIGHT - panel_height) // 2
        
        # 面板阴影
        shadow_surface = pygame.Surface((panel_width + 20, panel_height + 20), pygame.SRCALPHA)
        pygame.draw.rect(shadow_surface, (0, 0, 0, 30), (0, 0, panel_width + 20, panel_height + 20), border_radius=35)
        self.surface.blit(shadow_surface, (panel_x - 10, panel_y - 5))
        
        # 面板主体 - 白色马卡龙卡片
        panel_surface = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        pygame.draw.rect(panel_surface, (255, 255, 255, 245), (0, 0, panel_width, panel_height), border_radius=30)
        
        # 面板边框 - 淡淡的彩虹色
        border_colors = [(255, 182, 193), (230, 190, 255), (173, 216, 230)]
        for i, color in enumerate(border_colors):
            alpha = 80 - i * 20
            border_surface = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
            pygame.draw.rect(border_surface, (*color, alpha), (i, i, panel_width - i*2, panel_height - i*2), 2, border_radius=30-i)
            panel_surface.blit(border_surface, (0, 0))
        
        self.surface.blit(panel_surface, (panel_x, panel_y))
        
        # 标题区域 - 马卡龙风格
        title_y = panel_y + 40
        title_font = self.font_large
        
        # 标题背景装饰
        title_bg_rect = pygame.Rect(panel_x + 50, title_y - 10, panel_width - 100, 60)
        title_bg_surface = pygame.Surface((panel_width - 100, 60), pygame.SRCALPHA)
        # 渐变背景
        for y in range(60):
            ratio = y / 60
            r = int(255 - ratio * 25)
            g = int(182 + ratio * 38)
            b = int(193 + ratio * 32)
            pygame.draw.line(title_bg_surface, (r, g, b, 100), (0, y), (panel_width - 100, y))
        pygame.draw.rect(title_bg_surface, (255, 255, 255, 50), (0, 0, panel_width - 100, 60), border_radius=15)
        self.surface.blit(title_bg_surface, title_bg_rect)
        
        # 主标题
        title_text = title_font.render("俄罗斯方块", True, (120, 80, 120))
        title_rect = title_text.get_rect(center=(WINDOW_WIDTH // 2, title_y + 20))
        self.surface.blit(title_text, title_rect)
        
        # 最高分显示 - 马卡龙徽章风格
        badge_y = panel_y + 120
        badge_width = 280
        badge_height = 45
        badge_x = (WINDOW_WIDTH - badge_width) // 2
        
        # 徽章背景
        badge_surface = pygame.Surface((badge_width, badge_height), pygame.SRCALPHA)
        # 金色渐变
        for y in range(badge_height):
            ratio = y / badge_height
            r = int(255 - ratio * 40)
            g = int(215 + ratio * 25)
            b = int(0 + ratio * 60)
            pygame.draw.line(badge_surface, (r, g, b, 200), (0, y), (badge_width, y))
        pygame.draw.rect(badge_surface, (255, 230, 100, 80), (0, 0, badge_width, badge_height), 2, border_radius=20)
        self.surface.blit(badge_surface, (badge_x, badge_y))
        
        # 最高分文字
        high_score_font = self.font_small
        high_score_text = high_score_font.render(f"🏆 最高分: {self.high_score:,}", True, (180, 120, 0))
        high_score_rect = high_score_text.get_rect(center=(WINDOW_WIDTH // 2, badge_y + 22))
        self.surface.blit(high_score_text, high_score_rect)
        
        # 难度选项 - 马卡龙卡片风格
        card_start_y = panel_y + 200
        card_width = 400
        card_height = 55
        card_spacing = 20
        card_colors = [
            (144, 238, 144),  # 浅绿 - 简单
            (255, 218, 185),  # 浅橙 - 普通  
            (255, 182, 193),  # 浅粉 - 困难
            (230, 190, 255),  # 浅紫 - 专家
            (173, 216, 230),  # 浅蓝 - 大师
        ]
        
        for i in range(1, 6):
            difficulty = DIFFICULTY_LEVELS[i]
            card_y = card_start_y + (i - 1) * (card_height + card_spacing)
            card_x = (WINDOW_WIDTH - card_width) // 2
            
            # 选中状态检测
            is_selected = (i == self.selected_difficulty)
            
            # 卡片阴影
            if is_selected:
                shadow_offset = 3
                shadow_alpha = 50
            else:
                shadow_offset = 2
                shadow_alpha = 30
                
            shadow_surface = pygame.Surface((card_width + 10, card_height + 10), pygame.SRCALPHA)
            pygame.draw.rect(shadow_surface, (0, 0, 0, shadow_alpha), (0, 0, card_width + 10, card_height + 10), border_radius=15)
            self.surface.blit(shadow_surface, (card_x - 5 + shadow_offset, card_y - 5 + shadow_offset))
            
            # 卡片主体
            card_color = card_colors[i - 1]
            card_surface = pygame.Surface((card_width, card_height), pygame.SRCALPHA)
            
            if is_selected:
                # 选中状态 - 更亮的颜色和边框
                for y in range(card_height):
                    ratio = y / card_height
                    r = int(card_color[0] + (255 - card_color[0]) * 0.3 - ratio * 15)
                    g = int(card_color[1] + (255 - card_color[1]) * 0.3 - ratio * 15)
                    b = int(card_color[2] + (255 - card_color[2]) * 0.3 - ratio * 15)
                    pygame.draw.line(card_surface, (r, g, b, 240), (0, y), (card_width, y))
                
                # 选中边框
                pygame.draw.rect(card_surface, (255, 255, 255, 200), (0, 0, card_width, card_height), 3, border_radius=15)
                pygame.draw.rect(card_surface, card_color, (0, 0, card_width, card_height), 2, border_radius=15)
                
                # 选中发光效果
                glow_surface = pygame.Surface((card_width + 20, card_height + 20), pygame.SRCALPHA)
                pygame.draw.rect(glow_surface, (*card_color, 60), (0, 0, card_width + 20, card_height + 20), border_radius=20)
                self.surface.blit(glow_surface, (card_x - 10, card_y - 10))
            else:
                # 未选中状态 - 正常颜色
                for y in range(card_height):
                    ratio = y / card_height
                    r = int(card_color[0] - ratio * 10)
                    g = int(card_color[1] - ratio * 10)
                    b = int(card_color[2] - ratio * 10)
                    pygame.draw.line(card_surface, (r, g, b, 200), (0, y), (card_width, y))
                
                pygame.draw.rect(card_surface, (255, 255, 255, 150), (0, 0, card_width, card_height), 1, border_radius=15)
            
            self.surface.blit(card_surface, (card_x, card_y))
            
            # 卡片内容
            # 难度星级
            stars = "⭐" * i
            star_font = self.font_medium
            star_text = star_font.render(stars, True, (255, 200, 0))
            self.surface.blit(star_text, (card_x + 30, card_y + 16))
            
            # 难度名称 - 居中显示
            name_font = self.font_medium
            name_color = (80, 60, 80) if is_selected else (100, 80, 100)
            name_text = name_font.render(difficulty['name'], True, name_color)
            name_rect = name_text.get_rect(center=(card_x + card_width // 2, card_y + card_height // 2))
            self.surface.blit(name_text, name_rect)
            
            # 推荐标签 - 简化设计
            if i == 2:  # 普通难度推荐
                recommend_size = 16
                recommend_x = card_x + card_width - 30
                recommend_y = card_y + 8
                # 简单的小圆点标记
                pygame.draw.circle(self.surface, (255, 100, 100), (recommend_x, recommend_y), recommend_size // 2)
                pygame.draw.circle(self.surface, (255, 255, 255), (recommend_x, recommend_y), recommend_size // 2, 2)
        
        # 返回按钮 - 马卡龙风格
        button_y = panel_y + panel_height - 80
        button_width = 200
        button_height = 50
        button_x = (WINDOW_WIDTH - button_width) // 2
        
        # 按钮阴影
        button_shadow = pygame.Surface((button_width + 8, button_height + 8), pygame.SRCALPHA)
        pygame.draw.rect(button_shadow, (0, 0, 0, 40), (0, 0, button_width + 8, button_height + 8), border_radius=25)
        self.surface.blit(button_shadow, (button_x - 4 + 2, button_y - 4 + 2))
        
        # 按钮主体 - 渐变粉色
        button_surface = pygame.Surface((button_width, button_height), pygame.SRCALPHA)
        for y in range(button_height):
            ratio = y / button_height
            r = int(255 - ratio * 30)
            g = int(182 + ratio * 20)
            b = int(193 + ratio * 25)
            pygame.draw.line(button_surface, (r, g, b, 220), (0, y), (button_width, y))
        
        pygame.draw.rect(button_surface, (255, 255, 255, 100), (0, 0, button_width, button_height), 2, border_radius=25)
        self.surface.blit(button_surface, (button_x, button_y))
        
        # 按钮文字
        button_font = self.font_medium
        button_text = button_font.render("返回活动页面", True, (120, 80, 120))
        button_rect = button_text.get_rect(center=(WINDOW_WIDTH // 2, button_y + 25))
        self.surface.blit(button_text, button_rect)
    
    def draw_pause_screen(self):
        """绘制暂停界面"""
        # 半透明遮罩
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.surface.blit(overlay, (0, 0))
        
        # 暂停面板
        pause_panel = pygame.Rect(WINDOW_WIDTH // 2 - 200, WINDOW_HEIGHT // 2 - 150, 400, 300)
        pause_surface = pygame.Surface((400, 300), pygame.SRCALPHA)
        pygame.draw.rect(pause_surface, (0, 0, 0, 180), (0, 0, 400, 300), border_radius=20)
        pygame.draw.rect(pause_surface, (255, 255, 255, 50), (0, 0, 400, 300), 3, border_radius=20)
        self.surface.blit(pause_surface, pause_panel)
        
        pause_text = self.font_large.render("游戏暂停", True, (255, 255, 255))
        pause_rect = pause_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 80))
        self.surface.blit(pause_text, pause_rect)
        
        continue_text = self.font_medium.render("按空格键继续", True, (255, 255, 255))
        continue_rect = continue_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2))
        self.surface.blit(continue_text, continue_rect)
        
        exit_text = self.font_medium.render("按ESC键退出", True, (255, 255, 255))
        exit_rect = exit_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 80))
        self.surface.blit(exit_text, exit_rect)
    
    def draw_game_over_screen(self):
        """绘制游戏结束界面"""
        # 半透明遮罩
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        self.surface.blit(overlay, (0, 0))
        
        # 游戏结束面板
        game_over_panel = pygame.Rect(WINDOW_WIDTH // 2 - 250, WINDOW_HEIGHT // 2 - 200, 500, 400)
        game_over_surface = pygame.Surface((500, 400), pygame.SRCALPHA)
        pygame.draw.rect(game_over_surface, (0, 0, 0, 200), (0, 0, 500, 400), border_radius=25)
        pygame.draw.rect(game_over_surface, (255, 0, 0, 100), (0, 0, 500, 400), 4, border_radius=25)
        self.surface.blit(game_over_surface, game_over_panel)
        
        game_over_text = self.font_large.render("游戏结束", True, (255, 0, 0))
        game_over_rect = game_over_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 120))
        self.surface.blit(game_over_text, game_over_rect)
        
        final_score_text = self.font_medium.render(f"最终分数: {self.score:,}", True, (255, 215, 0))
        final_score_rect = final_score_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 80))
        self.surface.blit(final_score_text, final_score_rect)
        
        # 显示是否破纪录
        if self.score > self.high_score:
            new_record_text = self.font_medium.render("新纪录！", True, (255, 255, 0))
            new_record_rect = new_record_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 40))
            self.surface.blit(new_record_text, new_record_rect)
        
        final_difficulty_text = self.font_medium.render(f"难度: {DIFFICULTY_LEVELS[self.selected_difficulty]['name']}", True, (100, 200, 255))
        final_difficulty_rect = final_difficulty_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2))
        self.surface.blit(final_difficulty_text, final_difficulty_rect)
        
        final_lines_text = self.font_medium.render(f"消除行数: {self.lines_cleared}", True, (255, 100, 100))
        final_lines_rect = final_lines_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 40))
        self.surface.blit(final_lines_text, final_lines_rect)
        
        restart_text = self.font_medium.render("按R键重新开始", True, (255, 255, 255))
        restart_rect = restart_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 80))
        self.surface.blit(restart_text, restart_rect)
        
        exit_text = self.font_medium.render("按ESC键退出", True, (255, 255, 255))
        exit_rect = exit_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 120))
        self.surface.blit(exit_text, exit_rect)
    
    def draw(self):
        """绘制游戏"""
        # 绘制背景
        self.draw_background()
        
        # 绘制难度选择界面
        if self.game_state == "difficulty_select":
            self.draw_difficulty_select_screen()
            return
        
        # 绘制游戏网格
        self.draw_grid()
        
        # 绘制当前方块
        self.draw_current_piece()
        
        # 绘制UI
        self.draw_ui()
        
        # 绘制暂停界面
        if self.game_state == "paused":
            self.draw_pause_screen()
        
        # 绘制游戏结束界面
        elif self.game_state == "game_over":
            self.draw_game_over_screen()