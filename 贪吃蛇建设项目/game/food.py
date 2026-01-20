# -*- coding: utf-8 -*-
import pygame
import random
import math
from .constants import *

class Food:
    def __init__(self, level=1):
        self.level = level
        self.position = (0, 0)
        self.animation_time = random.uniform(0, 2 * math.pi)
        self.pulse_time = 0
        self.set_properties_by_level()
        self.randomize_position()

    def set_properties_by_level(self):
        if self.level == 1:
            # 等级1：基础食物 - 红色苹果
            self.color = (255, 50, 50)  # 鲜艳的红色
            self.glow_color = (255, 100, 100)  # 发光颜色
            self.score = 1
            self.size_multiplier = 0.8  # 较小尺寸
            self.animation_speed = 0.2  # 较慢动画
            self.shape = "circle"
        elif self.level == 2:
            # 等级2：高级食物 - 金色钻石
            self.color = (255, 215, 0)  # 金色
            self.glow_color = (255, 255, 100)  # 黄色发光
            self.score = 3
            self.size_multiplier = 1.0  # 标准尺寸
            self.animation_speed = 0.4  # 中等动画速度
            self.shape = "diamond"
        else:
            # 等级3：稀有食物 - 紫色星星
            self.color = (138, 43, 226)  # 紫色
            self.glow_color = (255, 100, 255)  # 粉色发光
            self.score = 5
            self.size_multiplier = 1.2  # 较大尺寸
            self.animation_speed = 0.6  # 快速动画
            self.shape = "star"

    def randomize_position(self, snake_positions=None, obstacles=None):
        if snake_positions is None:
            snake_positions = []
        if obstacles is None:
            obstacles = []
            
        while True:
            self.position = (random.randint(0, GRID_WIDTH-1),
                           random.randint(0, GRID_HEIGHT-1))
            
            # 检查是否与蛇身重叠
            if self.position in snake_positions:
                continue
                
            # 检查是否与障碍物重叠
            if self.position in obstacles:
                continue
                
            # 检查是否在蛇头3x3范围内
            if snake_positions:
                head_x, head_y = snake_positions[0]
                if (abs(self.position[0] - head_x) <= 1 and 
                    abs(self.position[1] - head_y) <= 1):
                    continue
                    
            break

    def update(self, current_time):
        # 更新动画时间
        self.animation_time = (self.animation_time + self.animation_speed) % (2 * math.pi)
        self.pulse_time = (self.pulse_time + 0.1) % (2 * math.pi)

    def draw(self, surface):
        # 计算动画偏移
        scale = 1 + 0.15 * math.sin(self.animation_time)  # 缩放动画
        rotation = 20 * math.sin(self.animation_time * 2)  # 旋转动画
        pulse = 1 + 0.1 * math.sin(self.pulse_time * 3)  # 脉冲效果
        
        # 计算缩放后的尺寸
        base_size = int(GRID_SIZE * self.size_multiplier * scale * pulse)
        offset = (GRID_SIZE - base_size) // 2
        
        # 创建食物表面
        food_surface = pygame.Surface((GRID_SIZE, GRID_SIZE), pygame.SRCALPHA)
        
        # 绘制不同等级的外观
        if self.shape == "circle":
            # 等级1：圆形苹果
            self.draw_circle_food(food_surface, base_size, offset)
        elif self.shape == "diamond":
            # 等级2：菱形钻石
            self.draw_diamond_food(food_surface, base_size, offset)
        else:  # star
            # 等级3：星形宝石
            self.draw_star_food(food_surface, base_size, offset)
        
        # 添加高光效果
        self.add_highlight(food_surface, base_size, offset)
        
        # 旋转食物表面
        rotated_surface = pygame.transform.rotate(food_surface, rotation)
        
        # 计算绘制位置（居中）
        pos_x = self.position[0] * GRID_SIZE
        pos_y = self.position[1] * GRID_SIZE
        draw_x = pos_x + (GRID_SIZE - rotated_surface.get_width()) // 2
        draw_y = pos_y + (GRID_SIZE - rotated_surface.get_height()) // 2
        
        # 绘制发光效果
        self.draw_glow_effect(surface, pos_x, pos_y)
        
        # 绘制到主表面
        surface.blit(rotated_surface, (draw_x, draw_y))
        
        # 绘制等级指示器
        self.draw_level_indicator(surface, pos_x, pos_y)

    def draw_circle_food(self, surface, size, offset):
        """绘制圆形食物（等级1）"""
        center = (GRID_SIZE // 2, GRID_SIZE // 2)
        radius = size // 2
        
        # 绘制主体
        pygame.draw.circle(surface, self.color, center, radius)
        
        # 添加渐变效果
        for i in range(3):
            alpha = 100 - i * 30
            pygame.draw.circle(surface, (*self.color, alpha), center, radius - i * 2)

    def draw_diamond_food(self, surface, size, offset):
        """绘制菱形食物（等级2）"""
        center_x, center_y = GRID_SIZE // 2, GRID_SIZE // 2
        half_size = size // 2
        
        # 绘制主体
        points = [
            (center_x, center_y - half_size),  # 上
            (center_x + half_size, center_y),  # 右
            (center_x, center_y + half_size),  # 下
            (center_x - half_size, center_y)   # 左
        ]
        pygame.draw.polygon(surface, self.color, points)
        
        # 添加内部装饰
        inner_points = [
            (center_x, center_y - half_size // 2),
            (center_x + half_size // 2, center_y),
            (center_x, center_y + half_size // 2),
            (center_x - half_size // 2, center_y)
        ]
        pygame.draw.polygon(surface, (255, 255, 255, 128), inner_points)

    def draw_star_food(self, surface, size, offset):
        """绘制星形食物（等级3）"""
        center_x, center_y = GRID_SIZE // 2, GRID_SIZE // 2
        outer_radius = size // 2
        inner_radius = outer_radius // 2
        
        # 绘制星形
        star_points = self.get_star_points(center_x, center_y, 5, outer_radius, inner_radius)
        pygame.draw.polygon(surface, self.color, star_points)
        
        # 添加内部装饰
        inner_star_points = self.get_star_points(center_x, center_y, 5, inner_radius, inner_radius // 2)
        pygame.draw.polygon(surface, (255, 255, 255, 150), inner_star_points)

    def add_highlight(self, surface, size, offset):
        """添加高光效果"""
        highlight_color = (255, 255, 255, 180)
        highlight_size = size // 3
        highlight_x = offset + size // 4
        highlight_y = offset + size // 4
        
        # 绘制椭圆形高光
        pygame.draw.ellipse(surface, highlight_color, 
                           (highlight_x, highlight_y, highlight_size, highlight_size // 2))

    def draw_glow_effect(self, surface, pos_x, pos_y):
        """绘制发光效果"""
        glow_size = int(GRID_SIZE * 2.0)  # 更大的发光范围
        glow_surface = pygame.Surface((glow_size, glow_size), pygame.SRCALPHA)
        glow_center = glow_size // 2
        
        # 创建多层发光效果
        for i in range(5):
            radius = glow_size // 2 - i * 3
            alpha = int(80 * (1 - i / 5))
            color = (*self.glow_color, alpha)
            pygame.draw.circle(glow_surface, color, (glow_center, glow_center), radius)
        
        glow_x = pos_x + (GRID_SIZE - glow_size) // 2
        glow_y = pos_y + (GRID_SIZE - glow_size) // 2
        surface.blit(glow_surface, (glow_x, glow_y))

    def draw_level_indicator(self, surface, pos_x, pos_y):
        """绘制等级指示器"""
        # 在食物上方显示等级数字
        font = pygame.font.Font(FONT_NAME, 12)
        level_text = font.render(str(self.level), True, WHITE)
        text_rect = level_text.get_rect(center=(pos_x + GRID_SIZE // 2, pos_y - 5))
        
        # 添加背景
        bg_rect = text_rect.inflate(8, 4)
        pygame.draw.rect(surface, (0, 0, 0, 150), bg_rect, border_radius=3)
        pygame.draw.rect(surface, self.color, bg_rect, 1, border_radius=3)
        
        surface.blit(level_text, text_rect)

    def get_star_points(self, cx, cy, num_points, outer_radius, inner_radius):
        """生成星形点"""
        points = []
        angle = -math.pi / 2
        angle_step = math.pi / num_points
        for _ in range(num_points * 2):
            radius = outer_radius if len(points) % 2 == 0 else inner_radius
            points.append((cx + radius * math.cos(angle), cy + radius * math.sin(angle)))
            angle += angle_step
        return points 