# -*- coding: utf-8 -*-
import pygame
import random
import math
from .constants import *

class GameBoard:
    def __init__(self):
        self.obstacles = []
        self.obstacle_details = [] # 存储(颜色, 动画偏移)
        self.grid_surface = None
        self.generate_obstacles()
        self.create_grid_surface()

    def create_grid_surface(self):
        # 创建网格背景
        self.grid_surface = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        grid_color = (180, 180, 180)  # 柔和的淡灰色
        
        # 绘制垂直线
        for x in range(0, WINDOW_WIDTH, GRID_SIZE):
            pygame.draw.line(self.grid_surface, grid_color, (x, 0), (x, WINDOW_HEIGHT))
        
        # 绘制水平线
        for y in range(0, WINDOW_HEIGHT, GRID_SIZE):
            pygame.draw.line(self.grid_surface, grid_color, (0, y), (WINDOW_WIDTH, y))

    def generate_obstacles(self, snake_positions=None):
        if snake_positions is None:
            snake_positions = []
            
        self.obstacles = []
        self.obstacle_details = []
        attempts = 0
        max_attempts = 200 # 增加尝试次数以确保生成足够数量
        
        # 定义新的颜色方案（红色/橙色系，更具警示性）
        obstacle_colors = [
            (255, 69, 0),    # OrangeRed
            (220, 20, 60),   # Crimson
            (255, 140, 0),   # DarkOrange
            (178, 34, 34),   # Firebrick
            (255, 0, 0)      # Red
        ]
        
        while len(self.obstacles) < OBSTACLE_COUNT and attempts < max_attempts:
            attempts += 1
            pos = (random.randint(1, GRID_WIDTH - 2), # 避免在最边缘生成
                  random.randint(1, GRID_HEIGHT - 2))
            
            # 检查是否与蛇身重叠
            if pos in snake_positions:
                continue
                
            # 检查是否与现有障碍物重叠或太近
            too_close = False
            for obs_pos in self.obstacles:
                if abs(pos[0] - obs_pos[0]) <= 1 and abs(pos[1] - obs_pos[1]) <= 1:
                    too_close = True
                    break
            if too_close:
                continue
                    
            # 检查是否在蛇头3x3范围内
            if snake_positions:
                head_x, head_y = snake_positions[0]
                if (abs(pos[0] - head_x) <= 2 and # 扩大安全区域
                    abs(pos[1] - head_y) <= 2):
                    continue
                    
            self.obstacles.append(pos)
            # 为每个障碍物添加颜色和随机动画偏移
            self.obstacle_details.append({
                'color': random.choice(obstacle_colors),
                'anim_offset': random.random() * 2 * math.pi # 随机相位
            })

    def update(self, current_time):
        # 更新动画状态
        for detail in self.obstacle_details:
            detail['anim_offset'] += 0.05 # 控制动画速度

    def draw(self, surface):
        # 绘制网格背景
        surface.blit(self.grid_surface, (0, 0))
        
        # 绘制障碍物
        for i, pos in enumerate(self.obstacles):
            center_x = pos[0] * GRID_SIZE + GRID_SIZE // 2
            center_y = pos[1] * GRID_SIZE + GRID_SIZE // 2
            size = GRID_SIZE * 0.4
            detail = self.obstacle_details[i]
            color = detail['color']
            
            # 1. 增强搏动光晕效果
            anim_offset = detail['anim_offset']
            # 更亮、范围更大的光晕
            glow_alpha = 120 + 100 * (math.sin(anim_offset) + 1) / 2 # 范围: 120 -> 220
            glow_size = size * (1.8 + 0.4 * math.sin(anim_offset)) # 范围: 1.4 -> 2.2 倍大小
            self.draw_hexagon(surface, (*color, glow_alpha), center_x, center_y, glow_size, is_filled=True)

            # 2. 绘制更清晰的六边形主体
            highlight_color = tuple(min(255, c + 100) for c in color)
            # 使用高光色作为边框颜色，并加粗边框
            self.draw_hexagon(surface, highlight_color, center_x, center_y, size, is_filled=False, border_width=2)
            
            # 3. 内部填充一个稍暗的颜色来提供对比
            inner_fill_color = tuple(c // 1.5 for c in color)
            self.draw_hexagon(surface, inner_fill_color, center_x, center_y, size, is_filled=True)
            
    def draw_hexagon(self, surface, color, center_x, center_y, size, is_filled=True, border_width=0):
        # 确保尺寸不会是负数
        if size <= 0:
            return
            
        points = []
        for i in range(6):
            # 旋转30度，使六边形尖端朝上
            angle = math.pi / 3 * i - math.pi / 6
            x = center_x + size * math.cos(angle)
            y = center_y + size * math.sin(angle)
            points.append((x, y))
            
        if is_filled:
            pygame.draw.polygon(surface, color, points)
        else:
            pygame.draw.polygon(surface, color, points, border_width)

    def check_collision(self, position):
        return position in self.obstacles 