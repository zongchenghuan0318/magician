import pygame
import random
import math
import json
import os
from .constants import *
from .player import player_data

# 特殊方块类型
SPECIAL_TYPES = {
    'MULTI_BALL': 0,    # 分裂球
    'ADD_BALL': 1,      # 生成一个球
    'WIDE_PADDLE': 2,   # 扩大挡板
    'SLOW_BALL': 3,     # 减速球
    'EXTRA_LIFE': 4,    # 额外生命
    'POINTS_MULTIPLIER': 5,  # 分数加倍
    'EXPLOSION': 6      # 爆炸效果
}

# 粒子系统
class Particle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color
        self.size = random.randint(2, 3)  # 减小粒子大小
        self.life = 200  # 减少初始生命值
        self.vx = random.uniform(-1.5, 1.5)  # 减小速度范围
        self.vy = random.uniform(-1.5, 1.5)
        self.rotation = random.uniform(0, 360)
        self.rotation_speed = random.uniform(-3, 3)  # 减小旋转速度

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.life -= 8  # 加快粒子消失速度
        self.rotation += self.rotation_speed
        return self.life > 0

    def draw(self, surface):
        alpha = max(0, min(255, self.life))
        color = (*self.color[:3], alpha)
        
        # 简化粒子绘制，避免旋转计算
        draw_x = int(self.x)
        draw_y = int(self.y)
        pygame.draw.circle(surface, color, (draw_x, draw_y), self.size)

# 球类
class Ball:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = 10
        self.dx = 0  # 初始速度为0，由外部设置
        self.dy = 0
        self.color = (255, 255, 255)
        self.active = True
        self.rect = pygame.Rect(x - self.radius, y - self.radius, 
                              self.radius * 2, self.radius * 2)

    def update(self, speed_multiplier, delta_time):
        # 使用浮点数计算位置，避免累积误差
        self.x += self.dx * speed_multiplier * delta_time
        self.y += self.dy * speed_multiplier * delta_time
        # 更新碰撞矩形的位置 - 使用整数避免抖动
        self.rect.center = (int(self.x), int(self.y))

    def draw(self, surface):
        # 使用整数坐标绘制，避免抖动和残影
        draw_x = int(self.x)
        draw_y = int(self.y)
        pygame.draw.circle(surface, self.color, (draw_x, draw_y), self.radius)

# 特殊方块类
class SpecialBlock:
    def __init__(self, x, y, width, height, color, special_type=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.color = color
        self.special_type = special_type
        self.active = True
        self.hit_points = 2 if special_type is not None else 1  # 特殊方块需要击中两次

    def draw(self, surface):
        if not self.active:
            return
        pygame.draw.rect(surface, self.color, self.rect)
        border_color = (40, 40, 40)
        pygame.draw.rect(surface, border_color, self.rect, 2)
        center_x = self.rect.centerx
        center_y = self.rect.centery
        if self.special_type is not None:
            if self.special_type == SPECIAL_TYPES['MULTI_BALL']:
                self.draw_multi_ball_mark(surface, center_x, center_y)
            elif self.special_type == SPECIAL_TYPES['ADD_BALL']:
                self.draw_add_ball_mark(surface, center_x, center_y)
            elif self.special_type == SPECIAL_TYPES['WIDE_PADDLE']:
                self.draw_wide_paddle_mark(surface, center_x, center_y)
            elif self.special_type == SPECIAL_TYPES['SLOW_BALL']:
                self.draw_slow_ball_mark(surface, center_x, center_y)
            elif self.special_type == SPECIAL_TYPES['EXTRA_LIFE']:
                self.draw_extra_life_mark(surface, center_x, center_y)
            elif self.special_type == SPECIAL_TYPES['POINTS_MULTIPLIER']:
                self.draw_points_multiplier_mark(surface, center_x, center_y)
            elif self.special_type == SPECIAL_TYPES['EXPLOSION']:
                self.draw_explosion_mark(surface, center_x, center_y)
        if self.special_type is not None and self.hit_points > 1:
            font = pygame.font.Font(FONT_NAME, 14)
            hit_text = font.render(str(self.hit_points), True, (255, 255, 255))
            text_rect = hit_text.get_rect(center=(center_x, center_y + 10))
            surface.blit(hit_text, text_rect)

    def draw_multi_ball_mark(self, surface, x, y):
        # 三个黄色小球
        pygame.draw.circle(surface, (255, 255, 0), (x-6, y), 3)
        pygame.draw.circle(surface, (255, 255, 0), (x+6, y), 3)
        pygame.draw.circle(surface, (255, 255, 0), (x, y+6), 3)

    def draw_add_ball_mark(self, surface, x, y):
        # 两个蓝色小球
        pygame.draw.circle(surface, (64, 181, 255), (x-5, y+3), 3)
        pygame.draw.circle(surface, (64, 181, 255), (x+5, y+3), 3)

    def draw_wide_paddle_mark(self, surface, x, y):
        # 绿色横条
        pygame.draw.rect(surface, (0, 255, 0), (x-8, y-2, 16, 4))
        pygame.draw.line(surface, (0, 180, 0), (x-10, y), (x+10, y), 2)

    def draw_slow_ball_mark(self, surface, x, y):
        # 蓝色圆+横线
        pygame.draw.circle(surface, (0, 149, 221), (x, y), 6, 2)
        pygame.draw.line(surface, (0, 149, 221), (x-6, y), (x+6, y), 2)

    def draw_extra_life_mark(self, surface, x, y):
        # 红色十字
        pygame.draw.rect(surface, (255, 0, 0), (x-2, y-8, 4, 16))
        pygame.draw.rect(surface, (255, 0, 0), (x-8, y-2, 16, 4))

    def draw_points_multiplier_mark(self, surface, x, y):
        # 橙色X
        pygame.draw.line(surface, (255, 165, 0), (x-6, y-6), (x+6, y+6), 3)
        pygame.draw.line(surface, (255, 165, 0), (x-6, y+6), (x+6, y-6), 3)

    def draw_explosion_mark(self, surface, x, y):
        # 画一个红色爆炸图案（简单放射状线条）
        for angle in range(0, 360, 45):
            rad = math.radians(angle)
            x1 = x + 0
            y1 = y + 0
            x2 = x + 10 * math.cos(rad)
            y2 = y + 10 * math.sin(rad)
            pygame.draw.line(surface, (255, 60, 60), (x1, y1), (x2, y2), 3)
        pygame.draw.circle(surface, (255, 120, 0), (x, y), 5)

# ====== 关卡数据与颜色表 ======
# 0表示无砖块，1~6为普通可破坏砖块，7为白色可破坏方块，8为不可破坏方块
LEVELS = [
    
    [
    [7,7,7,7,7,7,7,7,7,7,7,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,7,7,7,7,7,7,7,7,7,7,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,4,4,4,4,4,4,4,4,4,4,4,4,4,0,0,0,0,0,0,4,4,4,4,4,4,4,4,4,4,4,4,4,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,6,6,6,6,6,6,6,6,6,6,6,6,6,0,0,0,0,0,0,6,6,6,6,6,6,6,6,6,6,6,6,6,0,0,0,0],
    [0,0,0,0,6,6,6,6,6,6,6,6,6,6,6,6,6,0,0,0,0,0,0,6,6,6,6,6,6,6,6,6,6,6,6,6,0,0,0,0],
    [0,0,0,0,6,6,6,6,6,6,6,6,6,6,6,6,6,0,0,0,0,0,0,6,6,6,6,6,6,6,6,6,6,6,6,6,0,0,0,0],
    [0,0,0,0,6,6,6,6,6,6,6,6,6,6,6,6,6,0,0,0,0,0,0,6,6,6,6,6,6,6,6,6,6,6,6,6,0,0,0,0],
    [0,0,0,0,6,6,6,6,6,6,6,6,6,6,6,6,6,0,0,0,0,0,0,6,6,6,6,6,6,6,6,6,6,6,6,6,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,4,4,4,4,4,4,4,4,4,4,4,4,4,0,0,0,0,0,0,4,4,4,4,4,4,4,4,4,4,4,4,4,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [7,7,7,7,7,7,7,7,7,7,7,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,7,7,7,7,7,7,7,7,7,7,0],
],
     [
    [7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,0],
    [7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,0],
    [7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,0],
    [7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,0],
    [7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,0],
    [8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,7,7,7,0],
    [8,7,6,6,6,6,6,6,6,6,7,8,7,6,6,6,6,6,6,6,6,6,7,8,7,6,7,7,7,7,7,7,7,6,7,8,7,7,7,0],
    [8,7,7,7,7,7,7,7,6,7,7,8,7,6,7,7,7,7,7,7,7,7,7,8,7,6,7,7,7,7,7,7,7,6,7,8,7,7,7,0],
    [8,7,7,7,7,7,7,6,7,7,7,8,7,6,7,7,7,7,7,7,7,7,7,8,7,6,7,7,7,7,7,7,7,6,7,8,7,7,7,0],
    [8,7,7,7,7,7,6,7,7,7,7,8,7,6,7,7,7,7,7,7,7,7,7,8,7,6,6,6,6,6,6,6,6,6,7,8,7,7,7,0],
    [8,7,7,7,7,6,7,7,7,7,7,8,7,6,7,7,7,7,7,7,7,7,7,8,7,6,7,7,7,7,7,7,7,6,7,8,7,7,7,0],
    [8,7,7,7,6,7,7,7,7,7,7,8,7,6,7,7,7,7,7,7,7,7,7,8,7,6,7,7,7,7,7,7,7,6,7,8,7,7,7,0],
    [8,7,6,6,6,6,6,6,6,6,7,7,7,6,6,6,6,6,6,6,6,6,7,8,7,6,7,7,7,7,7,7,7,6,7,8,7,7,7,0],
    [7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,0],
    [7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,0],
    [7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,0],
],

  [
        [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,0,0,0],
        [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
        [0,0,0,0,8,8,8,8,8,8,8,8,8,8,8,8,0,0,0,0,0,0,0,0,8,8,8,8,8,8,8,8,8,8,8,8,8,8,0,0],
        [0,0,0,0,0,0,8,3,3,3,3,3,3,3,3,3,3,3,3,3,8,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,8,0,0,0],
        [0,0,0,0,0,0,8,3,3,3,3,3,3,3,3,3,3,3,3,3,8,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,8,0,0,0],
        [0,0,0,0,0,0,8,3,3,3,3,3,3,3,3,3,3,3,3,3,8,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,8,0,0,0],
        [0,0,0,0,0,0,8,3,3,3,3,3,3,3,3,3,3,3,3,3,8,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,8,0,0,0],
        [0,0,0,0,0,0,8,3,3,3,3,3,3,3,3,3,3,3,3,3,8,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,8,0,0,0],
        [0,0,0,0,0,0,8,3,3,3,3,3,3,3,3,3,3,3,3,3,8,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,8,0,0,0],
        [0,0,0,0,0,0,8,3,3,3,3,3,3,3,3,3,3,3,3,3,8,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,8,0,0,0],
        [0,0,0,0,0,0,8,3,3,3,3,3,3,3,3,3,3,3,3,3,8,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,8,0,0,0],
        [0,0,0,0,0,0,8,3,3,3,3,3,3,3,3,3,3,3,3,8,8,8,3,3,3,3,3,3,3,3,3,3,3,3,3,3,8,0,0,0],
        [0,0,0,0,8,8,8,8,8,8,8,8,8,8,8,8,5,5,5,5,5,5,5,5,8,8,8,8,8,8,8,8,8,8,8,8,8,8,0,0],
        [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    ],
     [
        [8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8],
        [7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,8,0,8,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7],
        [7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,8,0,8,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7],
        [7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,8,0,8,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7],
        [7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,0,0,0,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7],
        [7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,0,0,0,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7],
        [7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,8,0,8,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7],
        [7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,8,0,8,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7],
        [7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,8,0,8,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7],
        [7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,8,0,8,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7],
        [7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,8,0,8,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7],
        [7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,8,0,8,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7],
        [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
        [7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,8,0,8,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7],
        [7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,8,0,8,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7],
        [7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,8,0,8,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7],
        [7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,8,0,8,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7],
        [7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,8,0,8,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7],
        [7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,8,0,8,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7],
        [8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,0,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8],
        
    ],
   [

    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,2,2,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,2,2,0,0,0,0,0,0,0,0],  # 眼睛（对称）
    [0,0,0,0,0,2,2,2,2,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,2,2,2,2,0,0,0,0,0,0,0],
    [0,0,0,0,0,2,2,2,2,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,2,2,2,2,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,2,2,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,2,2,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [4,4,4,4,4,4,4,4,4,4,4,4,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,4,4,4,4,4,4,4,4,4,4,4,4],  # 微笑（上沿）
    [4,4,4,4,4,4,4,4,4,4,2,2,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,2,2,4,4,4,4,4,4,4,4,4,4],
    [4,4,4,4,4,4,4,4,4,2,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,2,4,4,4,4,4,4,4,4,4],
    [4,4,4,4,4,4,4,4,2,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,2,4,4,4,4,4,4,4,4],
    [4,4,4,4,4,4,4,2,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,2,4,4,4,4,4,4,4],  # 微笑（下沿）
    [4,4,4,4,4,4,2,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,2,4,4,4,4,4,4],
    [4,4,4,4,4,2,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,2,4,4,4,4,4],
    [1,1,1,1,2,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,2,1,1,1,1],
    [1,1,1,2,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,2,1,1,1],
    [1,1,2,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,2,1,1],
    [1,2,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,2,1],
    [2,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,2],
    [3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3],
   ],
    # 关卡4：带不可破坏砖块的迷宫
    [
        [7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7],
        [7,1,1,1,0,0,0,0,1,1,1,0,0,0,0,1,1,1,1,7,7,1,1,1,0,0,0,0,1,1,1,0,0,0,0,1,1,1,1,7],
        [7,1,0,1,0,2,2,0,1,0,1,0,2,2,0,1,0,0,1,7,7,1,0,1,0,2,2,0,1,0,1,0,2,2,0,1,0,0,1,7],
        [7,1,0,1,0,2,2,0,1,0,1,0,2,2,0,1,0,0,1,7,7,1,0,1,0,2,2,0,1,0,1,0,2,2,0,1,0,0,1,7],
        [7,1,1,1,0,0,0,0,1,1,1,0,0,0,0,1,1,1,1,7,7,1,1,1,0,0,0,0,1,1,1,0,0,0,0,1,1,1,1,7],
        [7,1,1,1,0,0,0,0,1,1,1,0,0,0,0,1,1,1,1,7,7,1,1,1,0,0,0,0,1,1,1,0,0,0,0,1,1,1,1,7],
        [7,1,0,1,0,2,2,0,1,0,1,0,2,2,0,1,0,0,1,7,7,1,0,1,0,2,2,0,1,0,1,0,2,2,0,1,0,0,1,7],
    ],
    # 关卡5：通道设计
    [
        [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
        [1,7,0,0,7,7,0,0,7,0,0,7,7,0,0,7,0,0,0,1,1,7,0,0,7,7,0,0,7,0,0,7,7,0,0,7,0,0,0,1],
        [1,0,2,2,0,0,2,2,0,2,2,0,0,2,2,0,2,2,2,1,1,0,2,2,0,0,2,2,0,2,2,0,0,2,2,0,2,2,2,1],
        [1,0,2,2,0,0,2,2,0,2,2,0,0,2,2,0,2,2,2,1,1,0,2,2,0,0,2,2,0,2,2,0,0,2,2,0,2,2,2,1],
        [1,7,0,0,7,7,0,0,7,0,0,7,7,0,0,7,0,0,0,1,1,7,0,0,7,7,0,0,7,0,0,7,7,0,0,7,0,0,0,1],
        [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
        [1,7,0,0,7,7,0,0,7,0,0,7,7,0,0,7,0,0,0,1,1,7,0,0,7,7,0,0,7,0,0,7,7,0,0,7,0,0,0,1],
        [1,0,2,2,0,0,2,2,0,2,2,0,0,2,2,0,2,2,2,1,1,0,2,2,0,0,2,2,0,2,2,0,0,2,2,0,2,2,2,1],
    ],
    # 新关卡1：对称波浪
    [
        [0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0],
        [0,0,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,0,0],
        [0,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,0],
        [4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4],
        [0,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,0],
        [0,0,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,0,0],
        [0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0],
    ],
    # 新关卡3：棋盘格
    [
        [1 if (i+j)%2==0 else 2 for i in range(40)] for j in range(7)
    ],
    # 新关卡4：两侧高墙
    [
        [8 if i<5 or i>34 else 3 for i in range(40)] for j in range(7)
    ],
    # 新关卡5：V字阵
    [
        [0]*i + [4]*(40-2*i) + [0]*i if i<20 else [0]*(40-i) + [4]*(2*(i-20)) + [0]*(40-i) for i in range(7)
    ],
    # 关卡：笑脸
    [
        [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,1,1,0,0,0,0,0,0,0,0,0,0,1,1,0,0,0,0,0,0,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0],
        [0,0,0,0,1,0,0,1,0,0,0,0,0,0,0,1,0,0,1,0,0,0,0,0,1,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0],
        [0,0,0,0,1,0,0,1,0,0,0,0,0,0,0,1,0,0,1,0,0,0,0,0,1,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,2,2,0,0,0,0,0,0,0,0,0,0,2,2,0,0,0,0,0,0,2,2,0,0,0,0,0,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    ],
    # 关卡：心形
    [
        [0,0,0,0,3,3,0,0,0,0,0,0,0,0,0,0,3,3,0,0,0,0,0,0,0,0,0,0,3,3,0,0,0,0,0,0,0,0,0,0],
        [0,0,0,3,3,3,3,0,0,0,0,0,0,0,3,3,3,3,0,0,0,0,0,0,0,0,3,3,3,3,3,0,0,0,0,0,0,0,0,0],
        [0,0,3,3,3,3,3,3,0,0,0,0,0,3,3,3,3,3,3,0,0,0,0,0,3,3,3,3,3,3,3,3,0,0,0,0,0,0,0,0],
        [0,3,3,3,3,3,3,3,3,0,0,0,3,3,3,3,3,3,3,3,0,0,3,3,3,3,3,3,3,3,3,3,0,0,0,0,0,0,0,0],
        [3,3,3,3,3,3,3,3,3,3,0,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,0,0,0,0,0,0],
        [0,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,0,0,0,0,0],
        [0,0,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,0,0,0,0,0,0],
    ],
    # 关卡：字母S
    [
        [0,0,0,0,4,4,4,4,4,4,4,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
        [0,0,0,0,4,0,0,0,0,0,4,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
        [0,0,0,0,4,0,0,0,0,0,4,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
        [0,0,0,0,4,4,4,4,4,4,4,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0,0,0,4,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0,0,0,4,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
        [0,0,0,0,4,4,4,4,4,4,4,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    ],
    # 关卡：螺旋
    [
        [5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5],
        [5,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,5],
        [5,0,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,0,5],
        [5,0,5,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,5,0,5],
        [5,0,5,0,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,0,5,0,5],
        [5,0,5,0,5,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,5,0,5,0,5],
        [5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5],
    ],
    # 关卡：箭头
    [
        [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,6,6,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,6,6,6,6,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,6,6,6,6,6,6,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,6,6,6,6,6,6,6,6,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,6,6,6,6,6,6,6,6,6,6,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0,0,0,0,0,0,0,6,6,6,6,6,6,6,6,6,6,6,6,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0,0,0,0,0,0,6,6,6,6,6,6,6,6,6,6,6,6,6,6,0,0,0,0,0,0,0,0,0,0,0,0,0],
    ],
]

# ====== 关卡数据与颜色表 ======
# 0表示无砖块，1~6为普通可破坏砖块，7为白色可破坏方块，8为不可破坏方块
BLOCK_COLORS = [
    (0,0,0),         # 0:无砖块
    (255, 64, 64),   # 1:红色
    (255, 215, 0),   # 2:金色
    (64, 181, 255),  # 3:蓝色
    (0, 255, 127),   # 4:绿色
    (255, 165, 0),   # 5:橙色
    (160, 32, 240),  # 6:紫色
    (255, 255, 255), # 7:白色（可破坏）
    (128, 128, 128), # 8:不可破坏方块
    # 可继续扩展更多颜色
]
# LEVELS中的数字可用到8，后续如需更多颜色可继续扩展BLOCK_COLORS

# 在create_blocks和check_block_collision逻辑中，只有8号（灰色）为不可破坏，其余均可破坏

class PongGame:
    def __init__(self, surface):
        self.surface = surface
        self.width, self.height = surface.get_size()
        from .player import player_data
        self.player_data = player_data
        self.score = 0
        self.high_score = self.player_data.data.get('pong_high_score', 0)
        self.game_state = "level_select"  # 新增关卡选择状态
        self.selected_level = 1
        self.paddle_width = 100
        self.paddle_height = 10
        self.ball_radius = 6  # 球变小
        self.brick_rows = 5
        self.brick_cols = 40  # 增加列数，砖块缩小一半
        self.brick_width = 64  # 将在create_blocks中动态计算
        self.brick_height = 64  # 正方形高度
        self.brick_margin = 0  # 无缝隙
        self.blocks = []
        self.balls = []
        self.particles = []
        self.speed_multiplier = 1.0
        self.hit_count = 0
        self.level = 1
        self.bricks_destroyed = 0
        self.show_level_up_message = False
        self.level_up_timer = 0
        
        # 能量道具系统
        self.power_up_duration = 0.0  # 改为秒为单位
        self.power_up_active = False
        self.points_multiplier = 1
        
        # 时间控制
        self.last_time = pygame.time.get_ticks()
        self.delta_time = 0.016  # 默认16ms (60FPS)
        
        # 碰撞检测优化
        self.last_collision_time = 0
        self.collision_cooldown = 5
        self.frame_count = 0
        
        # 游戏结束状态管理
        self.game_over = False
        self.show_end_screen = False
        self.end_screen_timer = 0
        self.end_screen_delay = 60  # 1秒后显示结束页面
        
        self.explosion_active = False
        self.explosion_timer = 0.0
        
        self.reset_game()
        
        # 在PongGame.__init__中添加：
        self.level_select_scroll_offset = 0
        self.level_select_dragging = False
        self.level_select_drag_start_y = 0
        self.level_select_drag_start_offset = 0
        
    def reset_game(self):
        self.paddle_x = (self.width - self.paddle_width) // 2
        self.paddle_y = self.height - 20
        # 创建新球并设置初始速度
        new_ball = Ball(self.width // 2, self.height - 50)  # 稍微提高初始位置
        base_speed = 400  # 降低基础球速，让球更容易控制
        angle = random.uniform(-20, 20)  # 减小角度范围，让球更直
        new_ball.dx = base_speed * math.sin(math.radians(angle))
        new_ball.dy = -base_speed * math.cos(math.radians(angle))
        self.balls = [new_ball]
        self.lives = 3
        self.score = 0
        self.game_state = "ready"
        self.speed_multiplier = 1.0
        self.hit_count = 0
        # self.level = 1  # 删除这行，保留当前level
        self.bricks_destroyed = 0
        self.show_level_up_message = False
        self.level_up_timer = 0
        self.particles = []
        
        # 重置能量道具
        self.power_up_duration = 0.0  # 改为秒为单位
        self.power_up_active = False
        self.points_multiplier = 1
        self.paddle_width = 100
        
        # 重置游戏结束状态
        self.game_over = False
        self.show_end_screen = False
        self.end_screen_timer = 0
        
        self.explosion_active = False
        self.explosion_timer = 0.0
        
        self.create_blocks()
        
    def create_blocks(self):
        self.blocks = []
        # 选择当前关卡数据
        level_index = (self.level-1) % len(LEVELS)
        layout = LEVELS[level_index]
        rows = len(layout)
        cols = len(layout[0])
        
        # 动态计算砖块宽度，使其铺满整行
        # 预留左右边距各20像素
        available_width = self.width - 40
        self.brick_width = available_width // cols
        self.brick_height = self.brick_width  # 正方形
        
        # 居中排列
        start_x = 20  # 左边距20像素
        start_y = 70
        for row in range(rows):
            for col in range(cols):
                block_type = layout[row][col]
                if block_type == 0:
                    continue
                x = start_x + col * self.brick_width
                y = start_y + row * self.brick_width  # 正方形Y轴间距
                color = BLOCK_COLORS[block_type]
                if block_type == 8:
                    # 不可破坏方块永远不是特殊方块
                    block = SpecialBlock(x, y, self.brick_width, self.brick_height, color)
                    block.hit_points = 999999
                    self.blocks.append(block)
                else:
                    # 10%概率为特殊方块
                    is_special = random.random() < 0.10
                    if is_special:
                        special_type = random.choice(list(SPECIAL_TYPES.values()))
                        self.blocks.append(SpecialBlock(x, y, self.brick_width, self.brick_height, color, special_type))
                    else:
                        self.blocks.append(SpecialBlock(x, y, self.brick_width, self.brick_height, color))
    
    def update(self):
        # 检查游戏结束状态
        if self.game_over:
            # 保存最高分
            if self.score > self.high_score:
                self.high_score = self.score
                self.player_data.data['pong_high_score'] = self.high_score
                self.player_data._save_data()
            self.game_state = "game_over"
            return
        if self.game_state != "playing":
            return
        # 爆炸效果倒计时和球变色
        if self.explosion_active:
            self.explosion_timer -= self.delta_time
            for ball in self.balls:
                ball.color = (255, 60, 60)
            if self.explosion_timer <= 0:
                self.explosion_active = False
                for ball in self.balls:
                    ball.color = (255, 255, 255)
        # ...原有update内容...
        # 计算delta time
        current_time = pygame.time.get_ticks()
        self.delta_time = (current_time - self.last_time) / 1000.0  # 转换为秒
        self.delta_time = min(self.delta_time, 0.033)  # 限制最大delta time (30FPS)
        self.last_time = current_time
            
        # 更新帧计数器
        self.frame_count += 1
        
        # 更新能量道具持续时间
        if self.power_up_active:
            self.power_up_duration -= self.delta_time  # 使用实际时间差
            if self.power_up_duration <= 0:
                self.power_up_active = False
                self.paddle_width = 100  # 恢复挡板宽度
                self.speed_multiplier = 1.0  # 恢复球速
                self.points_multiplier = 1  # 恢复分数倍率
            
        # 键盘控制挡板
        keys = pygame.key.get_pressed()
        paddle_speed = 600  # 每秒600像素（加倍）
        paddle_distance = paddle_speed * self.delta_time  # 根据时间差计算移动距离
        if (keys[pygame.K_LEFT] or 
            keys[ord('a')] or 
            keys[ord('A')]) and self.paddle_x > 0:
            self.paddle_x -= paddle_distance
        if (keys[pygame.K_RIGHT] or 
            keys[ord('d')] or 
            keys[ord('D')]) and self.paddle_x < self.width - self.paddle_width:
            self.paddle_x += paddle_distance
        # 限制挡板在屏幕范围内
        self.paddle_x = max(0, min(self.width - self.paddle_width, self.paddle_x))
            
        # 更新所有球的位置
        for ball in self.balls:
            if not ball.active:
                continue
            
            # 保存球的前一位置
            prev_x = ball.x
            prev_y = ball.y
            
            ball.update(self.speed_multiplier, self.delta_time)
            
            # 连续碰撞检测：防止高速球穿过砖块
            collision_detected = False
            max_iterations = 3  # 最多检测3次
            
            for iteration in range(max_iterations):
                if self.check_block_collision(ball):
                    collision_detected = True
                    break
                # 如果球移动距离过大，进行细分检测
                if abs(ball.x - prev_x) > ball.radius or abs(ball.y - prev_y) > ball.radius:
                    # 细分移动步骤
                    step_x = (ball.x - prev_x) / 2
                    step_y = (ball.y - prev_y) / 2
                    ball.x = prev_x + step_x
                    ball.y = prev_y + step_y
                    if self.check_block_collision(ball):
                        collision_detected = True
                        break
                    ball.x = prev_x + step_x * 2
                    ball.y = prev_y + step_y * 2
                else:
                    break
            
            # 额外的安全检查：确保球不会卡在任何砖块内部
            self.check_and_fix_ball_position(ball)
            
            # 检查球是否超出屏幕边界 - 优化边界检测
            if ball.x - ball.radius <= 0:
                ball.x = ball.radius  # 防止球卡在边界外
                ball.dx = abs(ball.dx)  # 确保球向右移动
                self.add_particle_effect(ball.x, ball.y, (255, 255, 255))
            elif ball.x + ball.radius >= self.width:
                ball.x = self.width - ball.radius  # 防止球卡在边界外
                ball.dx = -abs(ball.dx)  # 确保球向左移动
                self.add_particle_effect(ball.x, ball.y, (255, 255, 255))
                
            if ball.y - ball.radius <= 0:
                ball.y = ball.radius  # 防止球卡在边界外
                ball.dy = abs(ball.dy)  # 确保球向下移动
                self.add_particle_effect(ball.x, ball.y, (255, 255, 255))
                
            # 检查与挡板的碰撞 - 优化碰撞检测
            if (ball.y + ball.radius >= self.paddle_y and 
                ball.y - ball.radius <= self.paddle_y + self.paddle_height and
                ball.x >= self.paddle_x and 
                ball.x <= self.paddle_x + self.paddle_width):
                
                # 防止球卡在挡板内
                ball.y = self.paddle_y - ball.radius
                
                # 根据击中挡板的位置改变反弹角度
                relative_intersect_x = (self.paddle_x + (self.paddle_width / 2)) - ball.x
                normalized_intersect = relative_intersect_x / (self.paddle_width / 2)
                bounce_angle = normalized_intersect * 60  # 最大60度角
                
                # 固定球速，只改变方向
                base_speed = 400  # 降低基础球速，让球更容易控制
                actual_speed = base_speed * self.speed_multiplier
                ball.dx = -actual_speed * math.sin(math.radians(bounce_angle))
                ball.dy = -actual_speed * math.cos(math.radians(bounce_angle))
                
                self.add_particle_effect(ball.x, ball.y, (0, 255, 0))
                
            if ball.y + ball.radius >= self.height:
                ball.active = False
                    
        # 检查是否所有球都丢失
        if all(not ball.active for ball in self.balls):
            self.lives -= 1
            if self.lives <= 0:
                self.game_over = True
                self.end_screen_timer = 0
                if self.score > self.high_score:
                    self.high_score = self.score
                # 奖励金币
                coins_earned = max(1, self.score // 100)
                player_data.add_coins(coins_earned)
            else:
                # 重置球的位置和速度
                new_ball = Ball(self.width // 2, self.height - 50)  # 稍微提高初始位置
                # 固定初始球速
                base_speed = 400  # 降低基础球速，让球更容易控制
                angle = random.uniform(-20, 20)  # 减小角度范围，让球更直
                new_ball.dx = base_speed * math.sin(math.radians(angle))
                new_ball.dy = -base_speed * math.cos(math.radians(angle))
                self.balls = [new_ball]
                
        # 只统计可破坏方块（hit_points < 999999）
        if all((not block.active) for block in self.blocks if block.hit_points < 999999):
            self.level += 1
            self.reset_game()  # 重置球和状态
            self.speed_multiplier += 0.1
            # 显示关卡进阶提示
            self.show_level_up_message = True
            self.level_up_timer = 120  # 120帧（约2秒）
            
        # 处理关卡进阶提示
        if self.show_level_up_message:
            self.level_up_timer -= 1
            if self.level_up_timer <= 0:
                self.show_level_up_message = False
        
        # 更新粒子
        self.update_particles()
            
    def check_block_collision(self, ball):
        for block in self.blocks:
            if not block.active:
                continue
            if ball.rect.colliderect(block.rect):
                if block.color == BLOCK_COLORS[8]:
                    self.simple_bounce(ball, block.rect)
                    self.ensure_ball_outside_block(ball, block.rect)
                    self.add_particle_effect(ball.x, ball.y, block.color)
                    return True
                # 爆炸效果
                if self.explosion_active:
                    self.trigger_explosion(block)
                block.hit_points -= 1
                if block.hit_points <= 0:
                    block.active = False
                    self.score += 10 * self.points_multiplier
                    if block.special_type is not None:
                        self.apply_special_effect(block.special_type)
                self.simple_bounce(ball, block.rect)
                self.ensure_ball_outside_block(ball, block.rect)
                self.add_particle_effect(ball.x, ball.y, block.color)
                return True
        return False
    
    def ensure_ball_outside_block(self, ball, rect):
        """确保球在砖块外部"""
        # 检查球是否在砖块内部
        if (ball.x >= rect.left and ball.x <= rect.right and 
            ball.y >= rect.top and ball.y <= rect.bottom):
            # 球在砖块内部，强制移出
            # 找到最近的边界
            dist_left = ball.x - rect.left
            dist_right = rect.right - ball.x
            dist_top = ball.y - rect.top
            dist_bottom = rect.bottom - ball.y
            
            min_dist = min(dist_left, dist_right, dist_top, dist_bottom)
            
            if min_dist == dist_left:
                ball.x = rect.left - ball.radius
            elif min_dist == dist_right:
                ball.x = rect.right + ball.radius
            elif min_dist == dist_top:
                ball.y = rect.top - ball.radius
            else:
                ball.y = rect.bottom + ball.radius
            
            # 更新球的矩形位置
            ball.rect.center = (int(ball.x), int(ball.y))
    
    def check_and_fix_ball_position(self, ball):
        """检查并修复球的位置，确保不会卡在砖块内部"""
        for block in self.blocks:
            if not block.active:
                continue
            
            # 检查球是否在砖块内部
            if (ball.x >= block.rect.left and ball.x <= block.rect.right and 
                ball.y >= block.rect.top and ball.y <= block.rect.bottom):
                # 球在砖块内部，强制移出到最近的边界
                dist_left = ball.x - block.rect.left
                dist_right = block.rect.right - ball.x
                dist_top = ball.y - block.rect.top
                dist_bottom = block.rect.bottom - ball.y
                
                min_dist = min(dist_left, dist_right, dist_top, dist_bottom)
                
                if min_dist == dist_left:
                    ball.x = block.rect.left - ball.radius
                elif min_dist == dist_right:
                    ball.x = block.rect.right + ball.radius
                elif min_dist == dist_top:
                    ball.y = block.rect.top - ball.radius
                else:
                    ball.y = block.rect.bottom + ball.radius
                
                # 更新球的矩形位置
                ball.rect.center = (int(ball.x), int(ball.y))
                break
    
    def simple_bounce(self, ball, rect):
        """简化的反弹机制 - 确保球不会进入砖块内部"""
        # 计算球与砖块的重叠量
        overlap_left = ball.rect.right - rect.left
        overlap_right = rect.right - ball.rect.left
        overlap_top = ball.rect.bottom - rect.top
        overlap_bottom = rect.bottom - ball.rect.top
        
        # 找出最小重叠方向
        min_overlap = min(overlap_left, overlap_right, overlap_top, overlap_bottom)
        
        # 根据重叠方向反弹并强制调整位置
        if min_overlap == overlap_left and ball.dx > 0:
            # 从左边界反弹
            ball.x = rect.left - ball.radius
            ball.dx = -abs(ball.dx)
        elif min_overlap == overlap_right and ball.dx < 0:
            # 从右边界反弹
            ball.x = rect.right + ball.radius
            ball.dx = abs(ball.dx)
        elif min_overlap == overlap_top and ball.dy > 0:
            # 从上边界反弹
            ball.y = rect.top - ball.radius
            ball.dy = -abs(ball.dy)
        elif min_overlap == overlap_bottom and ball.dy < 0:
            # 从下边界反弹
            ball.y = rect.bottom + ball.radius
            ball.dy = abs(ball.dy)
        else:
            # 特殊情况：强制反弹并调整位置
            if abs(ball.dx) > abs(ball.dy):
                ball.dx = -ball.dx
                # 确保球在砖块外部
                if ball.x < rect.centerx:
                    ball.x = rect.left - ball.radius
                else:
                    ball.x = rect.right + ball.radius
            else:
                ball.dy = -ball.dy
                # 确保球在砖块外部
                if ball.y < rect.centery:
                    ball.y = rect.top - ball.radius
                else:
                    ball.y = rect.bottom + ball.radius
        
        # 强制更新球的矩形位置
        ball.rect.center = (int(ball.x), int(ball.y))

    def add_particle_effect(self, x, y, color):
        # 大幅减少粒子数量以提高性能
        for _ in range(1):  # 从2个粒子减少到1个
            self.particles.append(Particle(x, y, color))

    def update_particles(self):
        # 使用列表推导式一次性过滤，而不是逐个检查
        self.particles = [p for p in self.particles if p.update()]

    def add_new_ball(self):
        self.balls.append(Ball(self.width // 2, self.height - 30))

    def apply_special_effect(self, special_type):
        if special_type == SPECIAL_TYPES['MULTI_BALL']:
            # 分裂球：每个存活球分裂成3个
            new_balls = []
            for ball in self.balls:
                if not ball.active:
                    continue
                angle0 = math.atan2(ball.dy, ball.dx)
                speed = math.hypot(ball.dx, ball.dy)
                for delta in [-0.3, 0, 0.3]:  # -17°, 0°, +17°
                    new_angle = angle0 + delta
                    dx = speed * math.cos(new_angle)
                    dy = speed * math.sin(new_angle)
                    new_ball = Ball(ball.x, ball.y)
                    new_ball.dx = dx
                    new_ball.dy = dy
                    new_balls.append(new_ball)
                ball.active = False  # 原球消失
            self.balls.extend(new_balls)
        elif special_type == SPECIAL_TYPES['ADD_BALL']:
            self.add_new_ball()
        elif special_type == SPECIAL_TYPES['WIDE_PADDLE']:
            self.paddle_width = min(150, self.paddle_width + 30)
            self.power_up_duration = 5.0  # 5秒
            self.power_up_active = True
        elif special_type == SPECIAL_TYPES['SLOW_BALL']:
            self.speed_multiplier = max(0.5, self.speed_multiplier - 0.2)
            self.power_up_duration = 5.0  # 5秒
            self.power_up_active = True
        elif special_type == SPECIAL_TYPES['EXTRA_LIFE']:
            self.lives += 1
        elif special_type == SPECIAL_TYPES['POINTS_MULTIPLIER']:
            self.points_multiplier = 2
            self.power_up_duration = 5.0  # 5秒
            self.power_up_active = True
        elif special_type == SPECIAL_TYPES['EXPLOSION']:
            self.explosion_active = True
            self.explosion_timer = 10.0  # 10秒
            
    def handle_event(self, event):
        # 关卡选择页面事件
        if self.game_state == "level_select":
            btn_w, btn_h = 160, 60
            preview_h = 60
            gap_x = 60
            gap_y = 60
            levels_per_row = max(1, (self.width-2*gap_x)//(btn_w+gap_x))
            total_rows = (len(LEVELS) + levels_per_row - 1) // levels_per_row
            content_height = total_rows * (btn_h + preview_h + gap_y) + 120
            view_height = self.height - 250
            max_scroll = max(0, content_height - view_height)
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                # 拖拽滚动条
                if max_scroll > 0:
                    bar_h = int(view_height * view_height / (content_height+1))
                    bar_y = int(160 + (-self.level_select_scroll_offset/max_scroll)*(view_height-bar_h))
                    scrollbar_rect = pygame.Rect(self.width-28, bar_y, 10, bar_h)
                    if scrollbar_rect.collidepoint(mx, my):
                        self.level_select_dragging = True
                        self.level_select_drag_start_y = my
                        self.level_select_drag_start_offset = self.level_select_scroll_offset
                        return
                # 选择关卡
                for idx, btn_rect in enumerate(getattr(self, 'level_btn_rects', [])):
                    if btn_rect.collidepoint(mx, my):
                        self.selected_level = idx+1
                        return
                # 开始游戏
                if hasattr(self, 'level_start_btn_rect') and self.level_start_btn_rect.collidepoint(mx, my):
                    self.level = self.selected_level
                    self.reset_game()
                    self.game_state = "playing"
                    return
                # 返回活动页面
                if hasattr(self, 'level_back_btn_rect') and self.level_back_btn_rect.collidepoint(mx, my):
                    self.active = False
                    return
            elif event.type == pygame.MOUSEBUTTONUP:
                self.level_select_dragging = False
            elif event.type == pygame.MOUSEMOTION:
                if self.level_select_dragging:
                    dy = event.pos[1] - self.level_select_drag_start_y
                    self.level_select_scroll_offset = min(0, max(-max_scroll, self.level_select_drag_start_offset + dy))
            elif event.type == pygame.MOUSEWHEEL:
                self.level_select_scroll_offset += event.y * 40
                self.level_select_scroll_offset = max(min(self.level_select_scroll_offset, 0), -max_scroll)
            return
        # 优先处理ready状态下的鼠标点击
        if self.game_state == "ready":
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                if hasattr(self, 'ready_btn_start') and self.ready_btn_start.collidepoint(mx, my):
                    self.game_state = "playing"
                    return
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                self.game_state = "playing"
                return
        # 处理结束页面的输入
        if self.handle_end_screen_input(event):
            return
        if self.game_state == "paused":
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                if hasattr(self, 'pause_btn_continue') and self.pause_btn_continue.collidepoint(mx, my):
                    self.game_state = "playing"
                elif hasattr(self, 'pause_btn_quit') and self.pause_btn_quit.collidepoint(mx, my):
                    self.game_state = "game_over"
                    self.show_end_screen = True
                return
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                if self.game_state == "game_over":
                    self.reset_game()
                elif self.game_state == "paused":
                    self.game_state = "playing"
                elif self.game_state == "ready":
                    self.game_state = "playing"
                else:
                    self.game_state = "paused"
            elif event.key == pygame.K_r:
                self.reset_game()
        if self.game_state == "game_over":
            self.draw_game_over_screen()  # 确保按钮rect已赋值
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                if hasattr(self, 'over_btn_restart_level') and self.over_btn_restart_level.collidepoint(mx, my):
                    self.reset_game()
                    self.game_state = "playing"
                    self.show_end_screen = False
                    self.game_over = False
                    return
                if hasattr(self, 'over_btn_restart') and self.over_btn_restart.collidepoint(mx, my):
                    self.game_state = "level_select"
                    self.show_end_screen = False
                    self.level_select_scroll_offset = 0
                    self.selected_level = self.level
                    self.game_over = False  # 关键修正
                    self.draw_level_select_screen()  # 立即赋值level_btn_rects
                    self.draw()  # 立刻刷新页面
                    return
                elif hasattr(self, 'over_btn_back') and self.over_btn_back.collidepoint(mx, my):
                    self.active = False  # 由activity_page检测active切换回活动页
                return

    def draw(self):
        if self.game_state == "level_select":
            self.draw_level_select_screen()
            return
        if self.game_state == "game_over":
            self.draw_game_over_screen()
            return
        # ...原有draw内容...
        # 优化背景绘制，避免重复创建背景表面
        if not hasattr(self, '_background_surface') or self._background_surface.get_size() != (self.width, self.height):
            # 只在第一次创建背景，或者窗口大小改变时重新创建
            self._background_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            for y in range(self.height):
                c = 180 - int(80 * y / self.height)
                pygame.draw.line(self._background_surface, (c//3, c//3, c, 255), (0, y), (self.width, y))
        self.surface.blit(self._background_surface, (0, 0))
        
        # 绘制方块
        for block in self.blocks:
            block.draw(self.surface)
        

        
        # 绘制挡板
        paddle_rect = pygame.Rect(self.paddle_x, self.paddle_y, self.paddle_width, self.paddle_height)
        pygame.draw.rect(self.surface, (0, 149, 221), paddle_rect, border_radius=10)
        pygame.draw.rect(self.surface, (255, 255, 255), paddle_rect, 3, border_radius=10)
        
        # 绘制所有球
        for ball in self.balls:
            if ball.active:
                ball.draw(self.surface)
        
        # 绘制粒子
        for particle in self.particles:
            particle.draw(self.surface)
        
        # 如果游戏结束但还没显示结束页面，显示简单提示
        if self.game_over and not self.show_end_screen:
            self.draw_game_over_hint(self.surface)
        
        # ====== 顶部红心生命值 ======
        heart_radius = 16
        heart_gap = 10
        for i in range(self.lives):
            center_x = 30 + i * (heart_radius * 2 + heart_gap)
            center_y = 30
            # 画红心（用两个圆+三角形近似）
            pygame.draw.circle(self.surface, (255, 60, 60), (center_x - 8, center_y), heart_radius)
            pygame.draw.circle(self.surface, (255, 60, 60), (center_x + 8, center_y), heart_radius)
            points = [
                (center_x - 16, center_y + 4),
                (center_x + 16, center_y + 4),
                (center_x, center_y + 28)
            ]
            pygame.draw.polygon(self.surface, (255, 60, 60), points)
        
        # 绘制分数、最高分、速度、关卡
        font = pygame.font.Font(FONT_NAME, 32)
        score_text = font.render(f"分数: {self.score}", True, (255, 255, 0))
        high_score_text = font.render(f"最高分: {self.high_score}", True, (100, 255, 100))
        speed_text = font.render(f"速度: {self.speed_multiplier:.1f}x", True, (255, 150, 255))
        level_text = font.render(f"关卡: {self.level}", True, (100, 200, 255))
        self.surface.blit(score_text, (20, 60))
        self.surface.blit(high_score_text, (self.width - 200, 20))
        self.surface.blit(speed_text, (20, 95))
        self.surface.blit(level_text, (20, 130))
        
        # 显示能量道具状态
        if self.power_up_active:
            remaining_time = max(0.0, self.power_up_duration)
            power_up_text = font.render(f"能量道具: {remaining_time:.1f}s", True, (255, 255, 0))
            self.surface.blit(power_up_text, (self.width - 250, 55))
        
        # 绘制关卡进阶提示
        if self.show_level_up_message:
            self.draw_level_up_message()
        
        # 绘制游戏状态
        if self.game_state == "ready":
            self.draw_ready_screen()
        elif self.game_state == "paused":
            self.draw_pause_screen()
            
    def draw_pause_screen(self):
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))
        self.surface.blit(overlay, (0, 0))
        font = pygame.font.Font(FONT_NAME, 48)
        text = font.render("游戏暂停", True, (255, 255, 255))
        text_rect = text.get_rect(center=(self.width // 2, self.height // 2 - 60))
        self.surface.blit(text, text_rect)
        font2 = pygame.font.Font(FONT_NAME, 28)
        # 按钮参数
        btn_w, btn_h = 220, 60
        btn_gap = 40
        btn_x = self.width // 2 - btn_w // 2
        btn_y1 = self.height // 2 + 10
        btn_y2 = btn_y1 + btn_h + btn_gap
        # 继续游戏按钮
        self.pause_btn_continue = pygame.Rect(btn_x, btn_y1, btn_w, btn_h)
        pygame.draw.rect(self.surface, (66, 165, 245), self.pause_btn_continue, border_radius=12)
        cont_text = font2.render("继续游戏", True, (255,255,255))
        cont_rect = cont_text.get_rect(center=self.pause_btn_continue.center)
        self.surface.blit(cont_text, cont_rect)
        # 结束游戏按钮
        self.pause_btn_quit = pygame.Rect(btn_x, btn_y2, btn_w, btn_h)
        pygame.draw.rect(self.surface, (255, 120, 120), self.pause_btn_quit, border_radius=12)
        quit_text = font2.render("结束本局", True, (255,255,255))
        quit_rect = quit_text.get_rect(center=self.pause_btn_quit.center)
        self.surface.blit(quit_text, quit_rect)
        
    def draw_game_over_screen(self):
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        # 渐变背景
        for y in range(self.height):
            c = 40 + int(80 * y / self.height)
            pygame.draw.line(overlay, (c, c//2, c//2, 180), (0, y), (self.width, y))
        self.surface.blit(overlay, (0, 0))
        font = pygame.font.Font(FONT_NAME, 56)
        text = font.render("游戏结束", True, (255, 255, 255))
        text_rect = text.get_rect(center=(self.width // 2, self.height // 2 - 120))
        self.surface.blit(text, text_rect)
        font2 = pygame.font.Font(FONT_NAME, 36)
        score_text = font2.render(f"最终分数: {self.score}", True, (255, 215, 0))
        score_rect = score_text.get_rect(center=(self.width // 2, self.height // 2 - 40))
        self.surface.blit(score_text, score_rect)
        level_text = font2.render(f"到达关卡: {self.level}", True, (100, 200, 255))
        level_rect = level_text.get_rect(center=(self.width // 2, self.height // 2 + 10))
        self.surface.blit(level_text, level_rect)
        if self.score > self.high_score:
            new_record_text = font2.render("新纪录！", True, (255, 80, 80))
            new_record_rect = new_record_text.get_rect(center=(self.width // 2, self.height // 2 + 60))
            self.surface.blit(new_record_text, new_record_rect)
        # 两个按钮：选择关卡、返回活动页面
        btn_w, btn_h = 220, 60
        btn_gap = 40
        btn_x = self.width // 2 - btn_w // 2
        btn_y1 = self.height // 2 + 120
        btn_y2 = btn_y1 + btn_h + btn_gap
        btn_y3 = btn_y2 + btn_h + btn_gap
        # 重新游戏按钮
        self.over_btn_restart_level = pygame.Rect(btn_x, btn_y1, btn_w, btn_h)
        pygame.draw.rect(self.surface, (255, 193, 7), self.over_btn_restart_level, border_radius=12)
        restart_level_text = font2.render("重新游戏", True, (255,255,255))
        restart_level_rect = restart_level_text.get_rect(center=self.over_btn_restart_level.center)
        self.surface.blit(restart_level_text, restart_level_rect)
        # 选择关卡按钮
        self.over_btn_restart = pygame.Rect(btn_x, btn_y2, btn_w, btn_h)
        pygame.draw.rect(self.surface, (66, 165, 245), self.over_btn_restart, border_radius=12)
        restart_text = font2.render("选择关卡", True, (255,255,255))
        restart_rect = restart_text.get_rect(center=self.over_btn_restart.center)
        self.surface.blit(restart_text, restart_rect)
        # 返回活动页面按钮
        self.over_btn_back = pygame.Rect(btn_x, btn_y3, btn_w, btn_h)
        pygame.draw.rect(self.surface, (120, 120, 120), self.over_btn_back, border_radius=12)
        back_text = font2.render("返回活动页面", True, (255,255,255))
        back_rect = back_text.get_rect(center=self.over_btn_back.center)
        self.surface.blit(back_text, back_rect)
        
    def draw_ready_screen(self):
        # 渐变背景
        grad = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        for y in range(self.height):
            c1 = (66, 165, 245)
            c2 = (156, 39, 176)
            ratio = y / self.height
            r = int(c1[0] * (1 - ratio) + c2[0] * ratio)
            g = int(c1[1] * (1 - ratio) + c2[1] * ratio)
            b = int(c1[2] * (1 - ratio) + c2[2] * ratio)
            pygame.draw.line(grad, (r, g, b, 220), (0, y), (self.width, y))
        self.surface.blit(grad, (0, 0))
        # 标题
        font_title = pygame.font.Font(FONT_NAME, 64)
        title_text = font_title.render("高级弹球游戏", True, (255, 255, 255))
        title_rect = title_text.get_rect(center=(self.width // 2, self.height // 2 - 120))
        self.surface.blit(title_text, title_rect)
        # 副标题
        font_sub = pygame.font.Font(FONT_NAME, 32)
        sub_text = font_sub.render("经典打砖块，畅享乐趣！", True, (255, 255, 255, 180))
        sub_rect = sub_text.get_rect(center=(self.width // 2, self.height // 2 - 60))
        self.surface.blit(sub_text, sub_rect)
        # 大按钮
        btn_w, btn_h = 260, 72
        btn_x = self.width // 2 - btn_w // 2
        btn_y = self.height // 2 + 10
        self.ready_btn_start = pygame.Rect(btn_x, btn_y, btn_w, btn_h)
        # 按钮阴影
        shadow = pygame.Surface((btn_w, btn_h), pygame.SRCALPHA)
        pygame.draw.rect(shadow, (0,0,0,60), (6,6,btn_w-12,btn_h-12), border_radius=24)
        self.surface.blit(shadow, (btn_x+4, btn_y+6))
        # 按钮渐变
        btn_grad = pygame.Surface((btn_w, btn_h), pygame.SRCALPHA)
        for y in range(btn_h):
            c1 = (66, 165, 245)
            c2 = (156, 39, 176)
            ratio = y / btn_h
            r = int(c1[0] * (1 - ratio) + c2[0] * ratio)
            g = int(c1[1] * (1 - ratio) + c2[1] * ratio)
            b = int(c1[2] * (1 - ratio) + c2[2] * ratio)
            pygame.draw.line(btn_grad, (r, g, b, 255), (0, y), (btn_w, y))
        pygame.draw.rect(btn_grad, (255,255,255,40), (0,0,btn_w,btn_h//2), border_radius=24)
        self.surface.blit(btn_grad, (btn_x, btn_y))
        # 按钮描边
        pygame.draw.rect(self.surface, (255,255,255), self.ready_btn_start, 3, border_radius=24)
        # 按钮文字
        font_btn = pygame.font.Font(FONT_NAME, 36)
        btn_text = font_btn.render("开始游戏", True, (255,255,255))
        btn_rect = btn_text.get_rect(center=self.ready_btn_start.center)
        self.surface.blit(btn_text, btn_rect)
        # 操作说明
        font_tip = pygame.font.Font(FONT_NAME, 22)
        tip1 = font_tip.render("A/D键或方向键控制挡板", True, (255,255,255,180))
        tip2 = font_tip.render("击碎特殊方块获得能量道具", True, (255,255,255,180))
        self.surface.blit(tip1, tip1.get_rect(center=(self.width//2, self.height//2 + 110)))
        self.surface.blit(tip2, tip2.get_rect(center=(self.width//2, self.height//2 + 140)))

    def draw_level_up_message(self):
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 100))
        self.surface.blit(overlay, (0, 0))
        
        # 使用更高效的字体渲染
        font = pygame.font.Font(FONT_NAME, 36)
        text = font.render(f"第 {self.level} 关！", True, (255, 255, 0))
        text_rect = text.get_rect(center=(self.width // 2, self.height // 2))
        self.surface.blit(text, text_rect)

    def draw_end_screen(self, surface):
        """绘制游戏结束页面"""
        # 半透明背景
        overlay = pygame.Surface((self.width, self.height))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        surface.blit(overlay, (0, 0))
        
        # 主标题
        title_font = pygame.font.Font(FONT_NAME, 48)
        title_text = title_font.render("游戏结束", True, (255, 255, 255))
        title_rect = title_text.get_rect(center=(self.width // 2, 200))
        surface.blit(title_text, title_rect)
        
        # 得分显示
        score_font = pygame.font.Font(FONT_NAME, 32)
        score_text = score_font.render(f"最终得分: {self.score}", True, (255, 215, 0))
        score_rect = score_text.get_rect(center=(self.width // 2, 280))
        surface.blit(score_text, score_rect)
        
        # 关卡显示
        level_text = score_font.render(f"到达关卡: {self.level + 1}", True, (255, 215, 0))
        level_rect = level_text.get_rect(center=(self.width // 2, 320))
        surface.blit(level_text, level_rect)
        
        # 重新开始提示
        restart_font = pygame.font.Font(FONT_NAME, 24)
        restart_text = restart_font.render("按 R 键重新开始", True, (255, 255, 255))
        restart_rect = restart_text.get_rect(center=(self.width // 2, 400))
        surface.blit(restart_text, restart_rect)
        
        # 返回主菜单提示
        menu_text = restart_font.render("按 ESC 键返回主菜单", True, (255, 255, 255))
        menu_rect = menu_text.get_rect(center=(self.width // 2, 440))
        surface.blit(menu_text, menu_rect)
        
        # 装饰性边框
        border_color = (255, 215, 0)
        border_width = 4
        pygame.draw.rect(surface, border_color, (50, 150, self.width - 100, 350), border_width)
        
        # 装饰性角落
        corner_size = 20
        for x, y in [(50, 150), (self.width - 70, 150), 
                     (50, self.height - 200), (self.width - 70, self.height - 200)]:
            pygame.draw.rect(surface, border_color, (x, y, corner_size, corner_size), 3)

    def draw_game_over_hint(self, surface):
        """绘制游戏结束提示"""
        hint_font = pygame.font.Font(FONT_NAME, 28)
        hint_text = hint_font.render("游戏结束", True, (255, 0, 0))
        hint_rect = hint_text.get_rect(center=(self.width // 2, self.height // 2))
        surface.blit(hint_text, hint_rect)

    def draw_block_dividers(self, surface):
        """绘制砖块分割线"""
        if not self.blocks:
            return
        
        # 获取砖块区域信息
        first_block = next((block for block in self.blocks if block.active), None)
        if not first_block:
            return
        
        block_height = first_block.rect.height
        block_y = first_block.rect.y
        
        # 计算分割线位置 - 更明显的分割线
        divider_color = (60, 60, 80)  # 深蓝灰色，更明显
        divider_width = 3  # 更粗的线条
        
        # 在每行砖块下方绘制分割线
        current_y = block_y + block_height
        while current_y < self.height - 200:  # 避免与UI重叠
            # 绘制主分割线
            pygame.draw.line(surface, divider_color, 
                           (0, current_y), (self.width, current_y), divider_width)
            
            # 添加装饰性小点，让分割线更有设计感
            dot_color = (100, 100, 120)  # 稍亮的点
            dot_spacing = 40  # 点之间的间距
            for x in range(20, self.width - 20, dot_spacing):
                pygame.draw.circle(surface, dot_color, (x, current_y), 2)
            
            current_y += block_height + 5  # 5像素间距

    def handle_end_screen_input(self, event):
        """处理结束页面的输入"""
        if not self.show_end_screen:
            return False
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                # 重新开始游戏
                self.reset_game()
                return True
            elif event.key == pygame.K_ESCAPE:
                # 返回主菜单
                self.active = False
                return True
        
        return False

    def trigger_explosion(self, center_block):
        cx, cy = center_block.rect.center
        for block in self.blocks:
            if not block.active or block.color == BLOCK_COLORS[8]:
                continue
            bx, by = block.rect.center
            if abs(bx - cx) <= self.brick_width * 1.5 and abs(by - cy) <= self.brick_height * 1.5:
                block.hit_points = 0
                block.active = False
                self.score += 10 * self.points_multiplier

    def draw_level_select_screen(self):
        # 渐变背景
        grad = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        for y in range(self.height):
            c1 = (66, 165, 245)
            c2 = (156, 39, 176)
            ratio = y / self.height
            r = int(c1[0] * (1 - ratio) + c2[0] * ratio)
            g = int(c1[1] * (1 - ratio) + c2[1] * ratio)
            b = int(c1[2] * (1 - ratio) + c2[2] * ratio)
            pygame.draw.line(grad, (r, g, b, 220), (0, y), (self.width, y))
        self.surface.blit(grad, (0, 0))
        # 标题
        font_title = pygame.font.Font(FONT_NAME, 54)
        title_text = font_title.render("选择关卡", True, (255, 255, 255))
        title_rect = title_text.get_rect(center=(self.width // 2, 80))
        self.surface.blit(title_text, title_rect)
        # 关卡按钮和预览
        btn_w, btn_h = 160, 60
        preview_w, preview_h = 120, 60
        gap_x = 60
        gap_y = 60
        levels_per_row = max(1, (self.width-2*gap_x)//(btn_w+gap_x))
        self.level_btn_rects = []
        # 计算关卡区高度
        total_rows = (len(LEVELS) + levels_per_row - 1) // levels_per_row
        content_height = total_rows * (btn_h + preview_h + gap_y) + 120  # 增加120像素多余区域
        view_height = self.height - 250  # 关卡区可视高度
        max_scroll = max(0, content_height - view_height)
        self.level_select_scroll_offset = max(min(self.level_select_scroll_offset, 0), -max_scroll)
        # 关卡按钮和预览
        for idx, level_data in enumerate(LEVELS):
            row = idx // levels_per_row
            col = idx % levels_per_row
            bx = gap_x + col * (btn_w + gap_x)
            by = 160 + row * (btn_h + preview_h + gap_y) + self.level_select_scroll_offset
            # 只绘制可见区域
            if by + btn_h + preview_h < 160 or by > 160 + view_height:
                continue
            btn_rect = pygame.Rect(bx, by, btn_w, btn_h)
            color = (66, 165, 245) if self.selected_level == idx+1 else (120,120,120)
            pygame.draw.rect(self.surface, color, btn_rect, border_radius=16)
            font_btn = pygame.font.Font(FONT_NAME, 32)
            btn_text = font_btn.render(f"第{idx+1}关", True, (255,255,255))
            btn_text_rect = btn_text.get_rect(center=btn_rect.center)
            self.surface.blit(btn_text, btn_text_rect)
            preview_rect = pygame.Rect(bx + (btn_w-preview_w)//2, by+btn_h+10, preview_w, preview_h)
            self.draw_level_preview(level_data, preview_rect)
            self.level_btn_rects.append(btn_rect)
        # 滚动条
        if max_scroll > 0:
            bar_h = int(view_height * view_height / (content_height+1))
            bar_y = int(160 + (-self.level_select_scroll_offset/max_scroll)*(view_height-bar_h))
            pygame.draw.rect(self.surface, (180,180,220,200), (self.width-28, bar_y, 10, bar_h), border_radius=6)
            pygame.draw.rect(self.surface, (120,120,180,120), (self.width-28, bar_y, 10, bar_h), 2, border_radius=6)
        # 右下角按钮参数
        btn_w, btn_h = 180, 56
        btn_gap = 18
        btn_x = self.width - btn_w - 40
        btn_y_start = self.height - btn_h*2 - btn_gap - 40
        btn_y_back = self.height - btn_h - 40
        # 开始游戏按钮（半透明）
        start_btn_rect = pygame.Rect(btn_x, btn_y_start, btn_w, btn_h)
        start_btn_surface = pygame.Surface((btn_w, btn_h), pygame.SRCALPHA)
        pygame.draw.rect(start_btn_surface, (255, 120, 120, 180), (0,0,btn_w,btn_h), border_radius=20)
        font_start = pygame.font.Font(FONT_NAME, 32)
        start_text = font_start.render("开始游戏", True, (255,255,255))
        start_text_rect = start_text.get_rect(center=(btn_w//2, btn_h//2))
        start_btn_surface.blit(start_text, start_text_rect)
        self.surface.blit(start_btn_surface, (btn_x, btn_y_start))
        self.level_start_btn_rect = start_btn_rect
        # 返回活动页面按钮（半透明）
        back_btn_rect = pygame.Rect(btn_x, btn_y_back, btn_w, btn_h)
        back_btn_surface = pygame.Surface((btn_w, btn_h), pygame.SRCALPHA)
        pygame.draw.rect(back_btn_surface, (120, 120, 120, 160), (0,0,btn_w,btn_h), border_radius=16)
        font_back = pygame.font.Font(FONT_NAME, 28)
        back_text = font_back.render("返回活动页面", True, (255,255,255))
        back_text_rect = back_text.get_rect(center=(btn_w//2, btn_h//2))
        back_btn_surface.blit(back_text, back_text_rect)
        self.surface.blit(back_btn_surface, (btn_x, btn_y_back))
        self.level_back_btn_rect = back_btn_rect

    def draw_level_preview(self, level_data, rect):
        rows = len(level_data)
        cols = len(level_data[0])
        cell_w = rect.width // cols
        cell_h = rect.height // rows
        for r in range(rows):
            for c in range(cols):
                v = level_data[r][c]
                if v == 0:
                    continue
                color = BLOCK_COLORS[v] if v < len(BLOCK_COLORS) else (200,200,200)
                cell_rect = pygame.Rect(rect.x + c*cell_w, rect.y + r*cell_h, cell_w-1, cell_h-1)
                pygame.draw.rect(self.surface, color, cell_rect)