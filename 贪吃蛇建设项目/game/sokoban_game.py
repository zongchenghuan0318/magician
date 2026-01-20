import pygame
import json
import math
import random
from .constants import *

# 自定义颜色
COLORS = {
    'background': (245, 247, 250),
    'primary': (57, 138, 247),
    'primary_light': (102, 163, 255),
    'secondary': (255, 102, 102),
    'wall': (70, 70, 180),
    'wall_border': (40, 40, 140),
    'wall_texture': (55, 55, 165),
    'box': (150, 150, 150),
    'box_on_target': (0, 200, 0),
    'box_border': (100, 100, 100),
    'player': (255, 0, 0),
    'player_head': (220, 0, 0),
    'player_border': (200, 0, 0),
    'target': (255, 215, 0),
    'text': (66, 165, 245),
    'text_small': (100, 100, 100),
    'button_bg': (255, 255, 255),
    'button_border': (66, 165, 245),
    'star': (255, 215, 0),
    'star_empty': (200, 200, 200),
    'overlay': (255, 255, 255, 180)
}

class SnowParticle:
    def __init__(self):
        self.x = random.randint(0, WINDOW_WIDTH)
        self.y = random.randint(-50, 0)
        self.speed = random.uniform(0.5, 2)
        self.size = random.randint(1, 3)

    def update(self):
        self.y += self.speed
        if self.y > WINDOW_HEIGHT:
            self.y = random.randint(-50, 0)
            self.x = random.randint(0, WINDOW_WIDTH)

    def draw(self, surface):
        pygame.draw.circle(surface, (255, 255, 255), (int(self.x), int(self.y)), self.size)

class SokobanGame:
    def __init__(self, surface):
        self.surface = surface
        self.active = True
        self.state = "level_select"
        self.levels = self.load_levels()
        self.current_level = 1
        self.grid = []
        self.player_pos = [0, 0]
        self.box_positions = []
        self.target_positions = []
        self.moves = 0
        self.stars = 0
        self.best_moves = {}
        self.load_best_moves()
        self.cell_size = 40
        self.offset_x = 0
        self.offset_y = 0
        self.font = pygame.font.Font(FONT_NAME, 36)
        self.small_font = pygame.font.Font(FONT_NAME, 24)
        self.very_small_font = pygame.font.Font(FONT_NAME, 18)
        self.level_buttons = []
        self.initialized = False
        self.move_history = []  # 用于存储移动历史，实现撤销功能
        self.return_to_activity = False  # 标记是否返回活动页面
        # 分页相关属性
        self.current_page = 1
        self.levels_per_page = 15  # 每页显示15个关卡
        self.total_pages = (len(self.levels) + self.levels_per_page - 1) // self.levels_per_page
        # 雪花粒子系统
        self.snow_particles = [SnowParticle() for _ in range(50)]
        # 添加时间属性用于动画效果
        self.time_passed = 0

    def load_levels(self):
        """根据提供的图片设计的关卡，使用数字表示：0=墙,1=箱子,2=目标点,3=玩家,4=箱子+目标点,5=空白"""
        levels = {
            1: [
                [5,5,5,5,5,5],
                [5,5,5,5,5,5],
                [5,5,0,5,5,5],
                [5,5,1,4,5,5],
                [5,5,2,4,5,5],
                [5,5,5,5,5,5],
                [5,5,5,5,5,5]
            ],
            2: [
                [0,0,0,0,0,0],
                [0,5,2,0,0,0],
                [0,5,5,0,0,0],
                [0,4,3,5,5,0],
                [0,5,5,1,5,0],
                [0,5,5,0,0,0],
                [0,0,0,0,0,0]
            ],
            3: [
                [0,0,0,0,0,0,0],
                [0,5,5,5,5,5,0],
                [0,5,0,5,0,5,0],
                [0,2,5,1,4,3,0],
                [0,5,5,5,0,0,0],
                [0,0,0,0,0,5,5]
            ],
            4: [
                [0,0,0,0,0,0,0],
                [0,5,5,5,0,0,0],
                [0,5,5,1,5,5,0],
                [0,0,4,5,2,5,0],
                [0,0,5,5,5,3,0],
                [0,0,0,0,0,0,0]
            ],
            5: [
                [0,0,0,0,0,0,0],
                [0,5,5,0,0,0,0],
                [0,5,2,5,2,5,0],
                [0,5,1,1,0,3,0],
                [0,0,5,5,5,5,0],
                [0,0,0,0,0,0,0]
            ],
             6: [
                [0,0,0,0,0,0],
                [0,5,3,5,0,0],
                [0,2,2,2,0,0],
                [0,1,1,1,0,0],
                [0,5,5,5,5,0],
                [0,5,5,5,5,0],
                [0,0,0,0,0,0]
            ],
            7: [
                [0,0,0,0,0,0],
                [0,5,5,0,0,0],
                [0,5,1,1,5,0],
                [0,2,2,2,5,0],
                [0,5,3,1,5,0],
                [0,5,5,5,0,0],
                [0,0,0,0,0,0]
            ],
            8: [
                [0,0,0,0,0,0,0],
                [0,0,5,5,5,0,0],
                [0,0,5,5,5,0,0],
                [0,5,1,1,1,5,0],
                [0,5,2,2,2,3,0],
                [0,0,0,0,0,0,0]
            ],
          9: [
                [0,0,0,0,0,0],
                [0,2,5,5,0,0],
                [0,3,1,1,5,0],
                [0,0,5,5,5,0],
                [0,0,0,5,5,0],
                [0,0,0,0,2,0],
                [0,0,0,0,0,0]
            ],
         10: [
                [0,0,0,0,0,0],
                [0,2,2,2,5,0],
                [0,5,5,1,5,0],
                [0,5,0,1,5,0],
                [0,5,5,1,5,0],
                [0,5,5,3,5,0],
                [0,0,0,0,0,0]
            ],
           11: [
                [0,0,0,0,0,0,0,0],
                [0,5,5,5,5,5,5,0],
                [0,5,2,4,4,1,3,0],
                [0,0,0,0,0,0,0,0],
                [0,0,0,0,0,0,0,0]
            ],
            12: [
                [0,0,0,0,0,0],
                [0,0,0,5,3,0],
                [0,5,5,1,5,0],
                [0,5,5,4,2,0],
                [0,5,5,4,2,0],
                [0,5,5,1,5,0],
                [0,0,0,5,5,0],
                [0,0,0,0,0,0]
            ],
            13: [
                [0,0,0,0,0,0],
                [0,0,5,3,5,0],
                [0,0,5,5,5,0],
                [0,0,0,1,5,0],
                [0,5,2,2,2,0],
                [0,5,1,1,5,0],
                [0,0,0,5,5,0],
                [0,0,0,0,0,0]
            ],
            14: [
                [0,0,0,0,0,0,0],
                [0,0,0,5,5,5,0],
                [0,0,0,1,1,3,0],
                [0,5,5,5,0,0,0],
                [0,5,5,5,5,5,0],
                [0,5,2,5,2,5,0],
                [0,0,0,0,0,0,0]
            ],
            15: [
                [0,0,0,0,0,0,0],
                [0,5,5,5,2,0,0],
                [0,5,0,0,5,0,0],
                [0,5,5,1,1,3,0],
                [0,5,0,5,5,5,0],
                [0,2,5,5,0,0,0],
                [0,0,0,0,0,0,0]
            ],
            16: [
                [0,0,0,0,0,0,0],
                [0,5,5,5,0,0,0],
                [0,5,3,5,0,0,0],
                [0,5,1,1,0,0,0],
                [0,0,2,5,2,5,0],
                [0,0,5,5,5,5,0],
                [0,0,0,0,0,0,0]
            ],
            17: [
                [0,0,0,0,0,0,0],
                [0,0,2,5,2,0,0],
                [0,5,4,5,4,5,0],
                [0,5,5,0,5,5,0],
                [0,5,1,5,1,5,0],
                [0,0,5,3,5,0,0],
                [0,0,0,0,0,0,0]
            ],
            18: [
                [0,0,0,0,0,0,0],
                [0,5,5,0,0,0,0],
                [0,2,4,1,5,5,0],
                [0,5,2,1,0,5,0],
                [0,0,5,3,5,5,0],
                [0,0,5,5,5,0,0],
                [0,0,0,0,0,0,0]
            ],
            19: [
                [0,0,0,0,0,0,0],
                [0,5,5,0,0,0,0],
                [0,2,4,1,5,5,0],
                [0,5,2,1,0,5,0],
                [0,0,5,3,5,5,0],
                [0,0,5,5,5,0,0],
                [0,0,0,0,0,0,0]
            ],
            20: [
                [0,0,0,0,0,0,0],
                [0,0,5,5,0,0,0],
                [0,0,5,1,1,5,0],
                [0,0,2,2,2,5,0],
                [0,5,5,3,1,5,0],
                [0,5,5,5,0,0,0],
                [0,0,0,0,0,0,0]
            ],
            21: [
                [0,0,0,0,0,0,0],
                [0,0,0,5,5,0,0],
                [0,0,3,1,2,0,0],
                [0,5,1,1,5,5,0],
                [0,5,2,5,2,5,0],
                [0,0,0,5,5,5,0],
                [0,0,0,0,0,0,0]
            ],
            22: [
                [0,0,0,0,0,0,0],
                [0,2,5,0,5,5,0],
                [0,5,5,1,5,5,0],
                [0,2,5,1,0,3,0],
                [0,5,5,1,5,5,0],
                [0,2,5,0,5,5,0],
                [0,0,0,0,0,0,0]
            ],
            23: [
                [0,0,0,0,0,0,0,0,0,0,0],
                [0,5,5,5,5,2,0,0,5,5,0],
                [0,5,1,1,3,2,2,1,1,5,0],
                [0,5,5,5,0,0,2,5,5,5,0],
                [0,0,0,0,0,0,0,0,0,0,0]
            ],
            24: [
                [0,0,0,0,0,0,0],
                [0,0,5,5,5,5,0],
                [0,5,5,0,0,5,0],
                [0,5,0,5,1,5,0],
                [0,5,5,4,5,2,0],
                [0,0,5,0,3,0,0],
                [0,0,5,5,5,0,0],
                [0,0,0,0,0,0,0]  
            ],
            25: [
                [0,0,0,0,0,0,0,0],
                [0,5,5,0,0,0,0,0],
                [0,5,5,5,5,0,0,0],
                [0,5,5,1,4,3,5,0],
                [0,0,0,5,2,0,5,0],
                [0,0,0,5,5,5,5,0],
                [0,0,0,0,0,0,0,0]
            ],
            26: [
                [0,0,0,0,0,0,0],
                [0,5,5,5,0,0,0],
                [0,5,0,5,5,0,0],
                [0,3,1,4,2,0,0],
                [0,0,5,5,2,5,0],
                [0,0,5,1,0,5,0],
                [0,0,0,5,5,5,0],
                [0,0,0,0,0,0,0]  
            ],
            27: [
                [0,0,0,0,0,0,0],
                [0,0,0,0,5,5,0],
                [0,0,0,0,3,5,0],
                [0,0,0,0,1,2,0],
                [0,5,5,5,1,2,0],
                [0,5,0,5,1,2,0],
                [0,5,5,5,5,0,0],
                [0,0,0,0,0,0,0]
            ],
            28: [
                [0,0,0,0,0,0,0,0],
                [0,0,5,5,5,5,5,0],
                [0,0,5,2,1,2,5,0],
                [0,0,5,1,3,1,5,0],
                [0,5,5,2,1,2,5,0],
                [0,5,5,5,5,5,5,0],
                [0,0,0,0,0,0,0,0]
            ],
            29: [
                [0,0,0,0,0,0,0],
                [0,5,5,5,5,5,0],
                [0,5,2,1,6,5,0],
                [0,5,1,2,1,5,0],
                [0,5,2,1,2,5,0],
                [0,5,1,2,1,5,0],
                [0,5,5,5,5,5,0],
                [0,0,0,0,0,0,0]
            ],
            30: [
                [0,0,0,0,0,0,0,0,0,0],
                [0,0,5,5,5,5,0,5,5,0],
                [0,0,5,1,0,1,0,5,5,0],
                [0,5,5,2,1,2,3,5,5,0],
                [0,5,5,2,0,5,5,5,5,0],
                [0,0,0,0,0,0,0,0,0,0]
            ],
            31: [
                [0,0,0,0,0,0],
                [0,0,5,5,0,0],
                [0,2,5,1,0,0],
                [0,2,1,5,0,0],
                [0,2,1,5,0,0],
                [0,2,1,5,0,0],
                [0,2,5,1,0,0],
                [0,5,5,5,3,0],
                [0,0,5,5,5,0],
                [0,0,0,0,0,0]
            ],
            32: [
                [0,0,0,0,0,0,0,0,0],
                [0,0,0,0,0,0,3,0,0],
                [0,5,5,5,5,2,4,5,0],
                [0,5,5,5,0,5,5,5,0],
                [0,0,0,0,0,1,0,5,0],
                [0,0,0,0,0,5,5,5,0],
                [0,0,0,0,0,0,0,0,0]
            ],
            33: [
                [0,0,0,0,0,0,0],
                [0,5,5,5,5,5,0],
                [0,2,5,2,5,5,0],
                [0,5,0,0,5,0,0],
                [0,5,5,1,5,0,0],
                [0,0,0,1,5,0,0],
                [0,0,0,3,5,0,0],
                [0,0,0,5,5,0,0],
                [0,0,0,0,0,0,0]
            ],
            34: [
                [0,0,0,0,0,0,0],
                [0,5,5,5,0,0,0],
                [0,2,5,2,5,5,0],
                [0,5,5,5,0,5,0],
                [0,0,5,0,5,5,0],
                [0,0,3,1,1,5,0],
                [0,0,5,5,5,5,0],
                [0,0,5,5,0,0,0],
                [0,0,0,0,0,0,0]
            ],
            35: [
                [0,0,0,0,0,0,0],
                [0,2,5,0,0,0,0],
                [0,2,3,5,0,0,0],
                [0,2,5,1,0,0,0],
                [0,0,1,5,0,0,0],
                [0,0,5,1,5,5,0],
                [0,0,5,5,5,5,0],
                [0,0,5,5,0,0,0],
                [0,0,0,0,0,0,0]
            ],
            36: [
                [0,0,0,0,0,0,0,0],
                [0,5,5,5,2,2,5,0],
                [0,5,5,3,1,1,5,0],
                [0,0,0,0,0,5,0,0],
                [0,0,0,0,5,5,0,0],
                [0,0,0,0,5,5,0,0],
                [0,0,0,0,5,5,0,0],
                [0,0,0,0,0,0,0,0]
            ],
            37: [
                [0,0,0,0,0,0,0,0],
                [0,5,5,5,0,0,0,0],
                [0,5,2,5,5,5,0,0],
                [0,0,4,0,1,5,5,0],
                [0,5,2,0,5,1,5,0],
                [0,5,3,0,0,5,0,0],
                [0,5,5,5,5,5,0,0],
                [0,0,0,0,0,0,0,0]
            ],
            38: [
                [0,0,0,0,0,0,0,0],
                [0,5,5,3,5,0,0,0],
                [0,5,5,0,5,0,0,0],
                [0,5,2,0,5,5,0,0],
                [0,5,2,1,1,1,5,0],
                [0,5,2,0,5,5,5,0],
                [0,0,0,0,5,5,5,0],
                [0,0,0,0,0,0,0,0]
            ],
            39: [
                [0,0,0,0,0,0,0,0],
                [0,5,3,0,5,5,0,0],
                [0,2,1,5,5,5,0,0],
                [0,2,5,0,5,1,0,0],
                [0,2,1,0,5,5,5,0],
                [0,2,5,0,5,1,5,0],
                [0,5,5,0,5,5,5,0],
                [0,0,0,0,0,0,0,0]
            ],
            40: [
                [0,0,0,0,0,0,0,0],
                [0,0,0,5,2,5,0,0],
                [0,0,0,5,1,5,5,0],
                [0,5,2,5,1,0,3,0],
                [0,5,0,1,5,2,5,0],
                [0,5,5,1,5,0,0,0],
                [0,0,5,2,5,0,0,0],
                [0,0,0,0,0,0,0,0]
            ],
            41: [
                [0,0,0,0,0,0,0,0],
                [0,3,5,5,5,5,5,0],
                [0,5,2,1,1,2,5,0],
                [0,5,1,2,2,1,5,0],
                [0,5,1,2,2,1,5,0],
                [0,5,2,1,1,2,5,0],
                [0,5,5,5,5,5,5,0],
                [0,0,0,0,0,0,0,0]
            ],
            42: [
                [0,0,0,0,0,0,0,0,0,0],
                [0,0,0,0,0,0,5,0,0,0],
                [0,0,5,5,5,5,5,5,5,0],
                [0,2,4,4,4,4,4,1,5,0],
                [0,0,5,5,5,5,5,3,0,0],
                [0,0,0,0,0,5,5,0,0,0],
                [0,0,0,0,0,0,0,0,0,0]
            ],
            43: [
                [0,0,0,0,0,0,0,0,0,0],
                [0,0,0,5,5,0,0,0,0,0],
                [0,5,5,1,5,5,3,2,2,0],
                [0,5,1,5,5,5,5,0,5,0],
                [0,0,0,5,0,0,0,0,5,0],
                [0,0,0,5,5,5,5,5,5,0],
                [0,0,0,0,0,0,0,0,0,0],
            ],
            44: [
                [0,0,0,0,0,0,0,0,0,0],
                [0,5,5,5,5,5,5,5,5,0],
                [0,5,0,0,2,0,0,0,5,0],
                [0,5,0,5,1,1,5,2,5,0],
                [0,5,2,5,3,1,0,0,5,0],
                [0,0,0,0,0,5,5,5,5,0],
                [0,0,0,0,0,0,0,0,0,0],
            ],
            45: [
                [0,0,0,0,0,0,0,0,0,0],
                [0,0,5,5,0,0,0,0,0,0],
                [0,0,5,5,5,5,1,5,5,0],
                [0,5,2,0,5,1,5,5,5,0],
                [0,5,2,0,1,0,0,0,0,0],
                [0,5,2,3,5,0,0,0,0,0],
                [0,0,0,0,0,0,0,0,0,0],
            ],
            46: [
                [0,0,0,0,0,0,0,0,0,0],
                [0,0,5,2,2,2,2,0,0,0],
                [0,5,5,5,0,0,0,0,0,0],
                [0,5,5,5,1,5,1,5,3,0],
                [0,0,0,5,5,1,5,1,5,0],
                [0,0,0,0,0,5,5,5,5,0],
                [0,0,0,0,0,0,0,0,0,0],
            ],
            47: [
                [0,0,0,0,0,0,0,0,0,0],
                [0,0,5,5,3,5,5,5,0,0],
                [0,0,5,1,5,5,1,5,0,0],
                [0,0,0,5,0,0,5,0,0,0],
                [0,5,5,1,2,2,1,5,5,0],
                [0,5,5,5,2,2,5,5,5,0],
                [0,0,0,0,0,0,0,0,0,0],
            ],
            48: [
                [0,0,0,0,0,0,0,0,0,0],
                [0,0,0,0,0,0,5,5,5,0],
                [0,0,0,0,2,2,2,2,2,0],
                [0,5,3,1,1,1,1,1,5,0],
                [0,5,5,5,5,5,0,5,0,0],
                [0,0,0,0,0,5,5,5,0,0],
                [0,0,0,0,0,0,0,0,0,0],
            ],
            49: [
                [0,0,0,0,0,0,0,0],
                [0,5,1,5,5,5,2,0],
                [0,5,1,5,1,5,0,0],
                [0,5,4,5,4,5,0,0],
                [0,5,2,5,2,1,2,0],
                [0,0,1,5,0,0,0,0],
                [0,5,2,5,4,5,2,0],
                [0,5,0,5,1,1,0,0],
                [0,5,1,3,5,2,0,0],
                [0,0,0,0,0,0,0,0]
            ],
            50: [
                [0,0,0,0,0,0,0,0,0,0,0],
                [0,0,0,0,5,5,0,0,0,0,0],
                [0,0,0,0,2,1,2,0,0,0,0],
                [0,0,5,5,1,2,1,5,5,0,0],
                [0,5,2,1,2,1,2,1,2,5,0],
                [0,5,1,2,1,6,1,2,1,5,0],
                [0,5,2,1,2,1,2,1,2,5,0],
                [0,0,5,5,1,2,1,1,5,0,0],
                [0,0,5,5,2,1,2,5,5,0,0],
                [0,0,0,0,5,5,0,0,0,0,0],
                [0,0,0,0,0,0,0,0,0,0,0]
            ]
                        
            
        }
        return levels

    def load_best_moves(self):
        """加载最佳步数记录"""
        try:
            with open('player_data.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.best_moves = data.get('sokoban_best_moves', {})
        except:
            self.best_moves = {}

    def save_best_move(self, level, moves):
        """保存最佳步数"""
        if str(level) not in self.best_moves or moves < int(self.best_moves[str(level)]):
            self.best_moves[str(level)] = moves
            try:
                with open('player_data.json', 'r', encoding='utf-8') as f:
                    data = json.load(f)
                data['sokoban_best_moves'] = self.best_moves
                with open('player_data.json', 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=4)
            except Exception as e:
                print(f"保存最佳步数失败: {e}")

    def init_level(self, level):
        """初始化关卡"""
        if level not in self.levels:
            level = 1
        self.current_level = level
        self.grid = []
        self.box_positions = []
        self.target_positions = []
        self.moves = 0
        self.stars = 0
        self.move_history = []

        # 解析关卡数据
        level_data = self.levels[level]
        for y, row in enumerate(level_data):
            grid_row = []
            for x, cell in enumerate(row):
                grid_row.append(cell)
                if cell == 3:
                    self.player_pos = [x, y]
                elif cell == 1:
                    self.box_positions.append([x, y])
                elif cell == 2:
                    self.target_positions.append([x, y])
                elif cell == 4:
                    self.box_positions.append([x, y])
                    self.target_positions.append([x, y])
                elif cell == 6:
                    self.player_pos = [x, y]
                    self.target_positions.append([x, y])
            self.grid.append(grid_row)

        # 计算偏移量使游戏居中
        self.calculate_offset()
        self.initialized = True

    def calculate_offset(self):
        """计算游戏居中的偏移量"""
        grid_width = len(self.grid[0]) * self.cell_size
        grid_height = len(self.grid) * self.cell_size
        self.offset_x = (WINDOW_WIDTH - grid_width) // 2
        self.offset_y = (WINDOW_HEIGHT - grid_height) // 2 + 50

    def move_player(self, dx, dy):
        """移动玩家并记录历史"""
        # 记录移动前的状态
        prev_state = {
            'player_pos': self.player_pos.copy(),
            'box_positions': [pos.copy() for pos in self.box_positions],
            'moves': self.moves
        }

        new_x = self.player_pos[0] + dx
        new_y = self.player_pos[1] + dy

        # 检查是否超出边界
        if new_x < 0 or new_x >= len(self.grid[0]) or new_y < 0 or new_y >= len(self.grid):
            return False

        # 检查是否是墙
        if self.grid[new_y][new_x] == 0:
            return False

        # 检查是否有箱子
        box_index = -1
        for i, (bx, by) in enumerate(self.box_positions):
            if bx == new_x and by == new_y:
                box_index = i
                break

        if box_index != -1:
            # 推动箱子
            new_box_x = new_x + dx
            new_box_y = new_y + dy

            # 检查箱子是否可以移动
            if (new_box_x < 0 or new_box_x >= len(self.grid[0]) or new_box_y < 0 or new_box_y >= len(self.grid) or
                self.grid[new_box_y][new_box_x] == 0 or
                [new_box_x, new_box_y] in self.box_positions):
                return False

            # 移动箱子
            self.box_positions[box_index] = [new_box_x, new_box_y]

        # 移动玩家
        self.player_pos = [new_x, new_y]
        self.moves += 1

        # 保存移动历史
        self.move_history.append(prev_state)
        return True

    def undo_move(self):
        """撤销上一步移动"""
        if not self.move_history:
            return False

        prev_state = self.move_history.pop()
        self.player_pos = prev_state['player_pos']
        self.box_positions = prev_state['box_positions']
        self.moves = prev_state['moves']
        return True

    def check_win(self):
        """检查是否胜利"""
        for box in self.box_positions:
            if box not in self.target_positions:
                return False
        # 保存最佳步数
        self.save_best_move(self.current_level, self.moves)
        return True

    def handle_event(self, event):
        """处理事件"""
        if self.state == "level_select":
            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                # 检查关卡按钮点击
                start_level = (self.current_page - 1) * self.levels_per_page
                for i, rect in enumerate(self.level_buttons):
                    if rect.collidepoint(mx, my):
                        self.init_level(start_level + i + 1)
                        self.state = "playing"
                        break
                # 检查返回活动页面按钮点击
                if hasattr(self, 'activity_back_rect') and self.activity_back_rect.collidepoint(mx, my):
                    self.return_to_activity = True
                # 检查选择关卡按钮点击
                if hasattr(self, 'level_select_button_rect') and self.level_select_button_rect.collidepoint(mx, my):
                    self.state = "level_select"
                # 检查分页按钮点击
                if hasattr(self, 'prev_page_rect') and self.prev_page_rect.collidepoint(mx, my) and self.current_page > 1:
                    self.current_page -= 1
                if hasattr(self, 'next_page_rect') and self.next_page_rect.collidepoint(mx, my) and self.current_page < self.total_pages:
                    self.current_page += 1
        elif self.state == "playing":
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP or event.key == pygame.K_w:
                    self.move_player(0, -1)
                elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                    self.move_player(0, 1)
                elif event.key == pygame.K_LEFT or event.key == pygame.K_a:
                    self.move_player(-1, 0)
                elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                    self.move_player(1, 0)
                elif event.key == pygame.K_r:
                    self.init_level(self.current_level)
                elif event.key == pygame.K_ESCAPE:
                    self.state = "level_select"
                elif event.key == pygame.K_z and pygame.key.get_mods() & pygame.KMOD_CTRL:
                    self.undo_move()

            # 检查鼠标点击事件
            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                # 检查撤销按钮点击
                if hasattr(self, 'undo_button_rect') and self.undo_button_rect.collidepoint(mx, my):
                    self.undo_move()
                # 检查返回活动页面按钮点击
                if hasattr(self, 'activity_back_rect') and self.activity_back_rect.collidepoint(mx, my):
                    self.return_to_activity = True
                # 检查选择关卡按钮点击
                if hasattr(self, 'level_select_button_rect') and self.level_select_button_rect.collidepoint(mx, my):
                    self.state = "level_select"

            # 检查是否胜利
            if self.check_win():
                self.state = "win"
        elif self.state == "win":
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    next_level = self.current_level + 1
                    if next_level in self.levels:
                        self.init_level(next_level)
                        self.state = "playing"
                    else:
                        self.state = "level_select"
                elif event.key == pygame.K_ESCAPE:
                    self.state = "level_select"

            # 检查鼠标点击事件
            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                # 检查下一关按钮点击
                if hasattr(self, 'next_level_rect') and self.next_level_rect.collidepoint(mx, my):
                    next_level = self.current_level + 1
                    if next_level in self.levels:
                        self.init_level(next_level)
                        self.state = "playing"
                    else:
                        self.state = "level_select"
                # 检查返回关卡选择按钮点击
                if hasattr(self, 'back_to_level_rect') and self.back_to_level_rect.collidepoint(mx, my):
                    self.state = "level_select"
                # 检查返回活动页面按钮点击
                if hasattr(self, 'activity_back_rect') and self.activity_back_rect.collidepoint(mx, my):
                    self.return_to_activity = True

    def draw_level_select(self):
        """绘制关卡选择界面"""
        # 绘制糖果马卡龙风格渐变背景：浅粉-浅紫-浅青
        for y in range(WINDOW_HEIGHT):
            # 主渐变 - 从顶部到底部
            progress = y / WINDOW_HEIGHT
            
            # 三段式渐变：浅粉 -> 浅紫 -> 浅青
            if progress < 0.33:  # 上部分：浅粉
                sub_progress = progress / 0.33
                r = int(255 - sub_progress * 30)
                g = int(200 - sub_progress * 20)
                b = int(220 + sub_progress * 35)
            elif progress < 0.66:  # 中部分：浅紫
                sub_progress = (progress - 0.33) / 0.33
                r = int(225 - sub_progress * 45)
                g = int(180 + sub_progress * 20)
                b = int(255 - sub_progress * 25)
            else:  # 下部分：浅青
                sub_progress = (progress - 0.66) / 0.34
                r = int(180 - sub_progress * 30)
                g = int(200 + sub_progress * 55)
                b = int(230 + sub_progress * 25)
                
            color = (r, g, b)
            pygame.draw.line(self.surface, color, (0, y), (WINDOW_WIDTH, y))
        
        # 添加糖果马卡龙风格的波浪图案
        wave_colors = [
            (255, 182, 193, 40),  # 浅粉
            (230, 190, 255, 35),  # 浅紫
            (180, 230, 250, 30),  # 浅青
            (255, 223, 180, 25),  # 浅橙
            (190, 255, 200, 20)   # 浅绿
        ]
        
        for i in range(5):  # 绘制5条波浪
            wave_height = 150 + i * 30
            wave_width = WINDOW_WIDTH
            wave_amplitude = 25 - i * 3
            wave_frequency = 0.015 + i * 0.004
            wave_phase = pygame.time.get_ticks() * 0.0002 + i * 0.5
            wave_y_offset = 80 + i * 120
            wave_color = wave_colors[i]
            
            points = []
            for x in range(0, wave_width, 4):  # 更平滑的曲线
                y = wave_y_offset + math.sin(x * wave_frequency + wave_phase) * wave_amplitude
                points.append((x, y))
            
            if len(points) > 1:
                # 使用平滑曲线
                pygame.draw.aalines(self.surface, wave_color, False, points)
        
        # 添加糖果马卡龙风格的光晕效果
        glow_colors = [
            (255, 182, 193),  # 浅粉
            (230, 190, 255),  # 浅紫
            (180, 230, 250),  # 浅青
            (255, 223, 180)   # 浅橙
        ]
        
        # 添加装饰性圆形光晕
        for i in range(4):  # 添加4个光晕
            glow_radius = 180 + i * 40
            glow_x = WINDOW_WIDTH * (0.15 + i * 0.25)
            glow_y = WINDOW_HEIGHT * (0.25 + i * 0.18)
            base_color = glow_colors[i]
            
            # 创建一个带有alpha通道的surface来绘制光晕
            glow_surface = pygame.Surface((glow_radius*2, glow_radius*2), pygame.SRCALPHA)
            
            # 从外到内绘制同心圆，渐变效果
            for r in range(glow_radius, 0, -2):  
                ratio = r / glow_radius
                alpha = max(0, min(255, int(15 - (glow_radius - r) * 0.08)))
                color = (base_color[0], base_color[1], base_color[2], alpha)
                pygame.draw.circle(glow_surface, color, (glow_radius, glow_radius), r)
            
            # 添加一些装饰性的小圆点
            for j in range(8):
                angle = j * (math.pi / 4)
                dot_distance = glow_radius * 0.8
                dot_x = glow_radius + math.cos(angle) * dot_distance
                dot_y = glow_radius + math.sin(angle) * dot_distance
                dot_size = 5 + (i % 3) * 2
                dot_color = (255, 255, 255, 40)
                pygame.draw.circle(glow_surface, dot_color, (int(dot_x), int(dot_y)), dot_size)
            
            self.surface.blit(glow_surface, (glow_x - glow_radius, glow_y - glow_radius))
        
        # 更新和绘制雪花粒子
        for particle in self.snow_particles:
            particle.update()
            particle.draw(self.surface)

        # 绘制糖果马卡龙风格的标题
        title_font = pygame.font.Font(FONT_NAME, 60)  # 更大的字体
        title_text = title_font.render("推箱子游戏", True, (255, 105, 180))  # 粉色标题
        title_rect = title_text.get_rect(center=(WINDOW_WIDTH // 2, 100))
        
        # 添加多层次的标题光晕
        glow_colors = [
            (255, 182, 193, 60),  # 浅粉
            (230, 190, 255, 50),  # 浅紫
            (180, 230, 250, 40),  # 浅青
        ]
        
        # 创建一个带有alpha通道的surface来绘制光晕
        title_glow_surface = pygame.Surface((title_rect.width + 60, title_rect.height + 60), pygame.SRCALPHA)
        
        # 多层次光晕效果
        for i, color in enumerate(glow_colors):
            for r in range(25 - i*5, 5 - i*2, -1):
                alpha = max(0, min(255, int(80 - r * 3)))
                glow_color = (color[0], color[1], color[2], alpha)
                pygame.draw.rect(title_glow_surface, glow_color, 
                               (30-r, 30-r, title_rect.width+r*2, title_rect.height+r*2), 
                               border_radius=r+10)
        
        self.surface.blit(title_glow_surface, (title_rect.x - 30, title_rect.y - 30))
        
        # 多层次标题阴影，创造立体感
        shadow_colors = [
            (180, 120, 160, 100),  # 深粉
            (150, 100, 180, 80),   # 深紫
            (120, 160, 200, 60)    # 深青
        ]
        
        for i, color in enumerate(shadow_colors):
            offset = (i + 1) * 2
            shadow_rect = title_rect.copy()
            shadow_rect.move_ip(offset, offset)
            shadow_text = title_font.render("推箱子游戏", True, color)
            self.surface.blit(shadow_text, shadow_rect)
        
        # 标题文本
        self.surface.blit(title_text, title_rect)
        
        # 添加装饰性元素
        # 小星星装饰
        for i in range(6):
            star_x = title_rect.x + title_rect.width * (0.1 + i * 0.18)
            star_y = title_rect.y - 15 + (i % 2) * 10
            star_size = 8 + (i % 3) * 2
            star_color = glow_colors[i % 3][:3] + (200,)
            
            # 绘制五角星
            points = []
            for j in range(5):
                angle = math.pi/2 + j * 2*math.pi/5
                points.append((star_x + math.cos(angle) * star_size, 
                              star_y + math.sin(angle) * star_size))
                angle += math.pi/5
                points.append((star_x + math.cos(angle) * star_size/2, 
                              star_y + math.sin(angle) * star_size/2))
            
            pygame.draw.polygon(self.surface, star_color, points)

        # 绘制关卡按钮
        self.level_buttons = []
        level_count = len(self.levels)
        
        # 定义按钮尺寸和间距
        button_width = 130
        button_height = 140
        horizontal_spacing = 20
        vertical_spacing = 30
        
        # 计算每行显示的关卡数，尽量多放
        max_buttons_per_row = 5
        # 动态调整每行显示的关卡数，确保不超出窗口宽度
        while True:
            total_width = max_buttons_per_row * button_width + (max_buttons_per_row - 1) * horizontal_spacing
            if total_width <= WINDOW_WIDTH - 40 or max_buttons_per_row == 1:
                break
            max_buttons_per_row -= 1
        
        level_per_row = max_buttons_per_row
        
        # 计算总宽度和起始位置，使按钮居中显示
        total_width = level_per_row * button_width + (level_per_row - 1) * horizontal_spacing
        start_x = (WINDOW_WIDTH - total_width) // 2
        start_y = 150

        # 获取鼠标位置用于悬停效果
        mouse_pos = pygame.mouse.get_pos()

        # 计算当前页显示的关卡范围
        start_level = (self.current_page - 1) * self.levels_per_page
        end_level = min(start_level + self.levels_per_page, level_count)

        # 绘制当前页的关卡按钮
        for i in range(start_level, end_level):
            # 计算在当前页中的索引
            page_index = i - start_level
            row = page_index // level_per_row
            col = page_index % level_per_row
            x = start_x + col * (button_width + horizontal_spacing)
            y = start_y + row * (button_height + vertical_spacing)
            rect = pygame.Rect(x, y, button_width, button_height)
            self.level_buttons.append(rect)

            # 检查鼠标是否悬停在按钮上
            is_hovered = rect.collidepoint(mouse_pos)
            
            # 糖果马卡龙风格的按钮颜色
            candy_colors = [
                (255, 182, 193),  # 浅粉
                (230, 190, 255),  # 浅紫
                (180, 230, 250),  # 浅青
                (255, 223, 180)   # 浅橙
            ]
            
            # 根据关卡索引选择颜色
            color_index = i % len(candy_colors)
            button_color = candy_colors[color_index]
            
            # 绘制按钮背景、阴影和装饰
            if is_hovered:
                # 悬停效果 - 轻微放大、高亮和发光
                hover_rect = rect.inflate(8, 8)
                
                # 发光效果
                glow_surface = pygame.Surface((hover_rect.width + 20, hover_rect.height + 20), pygame.SRCALPHA)
                for r in range(10, 0, -1):
                    alpha = max(0, min(255, int(40 - r * 3)))
                    glow_color = (button_color[0], button_color[1], button_color[2], alpha)
                    pygame.draw.rect(glow_surface, glow_color, 
                                   (10-r, 10-r, hover_rect.width+r*2, hover_rect.height+r*2), 
                                   border_radius=15)
                self.surface.blit(glow_surface, (hover_rect.x - 10, hover_rect.y - 10))
                
                # 亮色背景
                lighter_color = tuple(min(255, c + 20) for c in button_color)
                pygame.draw.rect(self.surface, lighter_color, hover_rect, border_radius=15)
                pygame.draw.rect(self.surface, (255, 255, 255), hover_rect, 3, border_radius=15)
            else:
                # 正常状态 - 糖果色背景
                pygame.draw.rect(self.surface, button_color, rect, border_radius=12)
                pygame.draw.rect(self.surface, (255, 255, 255, 150), rect, 2, border_radius=12)
                
                # 添加装饰性小点
                dot_size = 3
                dot_color = (255, 255, 255, 100)
                dot_positions = [
                    (rect.x + 10, rect.y + 10),
                    (rect.right - 10, rect.y + 10),
                    (rect.x + 10, rect.bottom - 10),
                    (rect.right - 10, rect.bottom - 10)
                ]
                for dot_pos in dot_positions:
                    pygame.draw.circle(self.surface, dot_color, dot_pos, dot_size)

            # 绘制糖果马卡龙风格的关卡缩略图
            thumbnail_size = 100
            thumbnail_offset_x = (button_width - thumbnail_size) // 2
            thumbnail_offset_y = 10
            thumbnail_rect = pygame.Rect(x + thumbnail_offset_x, y + thumbnail_offset_y, thumbnail_size, thumbnail_size)
            
            # 缩略图背景 - 浅色渐变
            thumbnail_surface = pygame.Surface((thumbnail_size, thumbnail_size), pygame.SRCALPHA)
            for ty in range(thumbnail_size):
                progress = ty / thumbnail_size
                # 根据按钮颜色创建更浅的渐变
                r = min(255, button_color[0] + 30 - int(progress * 20))
                g = min(255, button_color[1] + 30 - int(progress * 20))
                b = min(255, button_color[2] + 30 - int(progress * 20))
                pygame.draw.line(thumbnail_surface, (r, g, b), (0, ty), (thumbnail_size, ty))
            
            # 添加装饰性边框
            pygame.draw.rect(thumbnail_surface, (255, 255, 255, 180), (0, 0, thumbnail_size, thumbnail_size), 3, border_radius=8)
            
            # 添加小装饰
            for j in range(4):
                angle = j * (math.pi / 2)
                dot_x = thumbnail_size/2 + math.cos(angle) * (thumbnail_size/2 - 8)
                dot_y = thumbnail_size/2 + math.sin(angle) * (thumbnail_size/2 - 8)
                pygame.draw.circle(thumbnail_surface, (255, 255, 255, 100), (int(dot_x), int(dot_y)), 4)
            
            self.surface.blit(thumbnail_surface, (x + thumbnail_offset_x, y + thumbnail_offset_y))

            # 获取关卡数据
            level_data = self.levels[i + 1]
            cell_size = min(thumbnail_size // len(level_data[0]), thumbnail_size // len(level_data))
            t_start_x = x + thumbnail_offset_x + (thumbnail_size - len(level_data[0]) * cell_size) // 2
            t_start_y = y + thumbnail_offset_y + (thumbnail_size - len(level_data) * cell_size) // 2

            # 绘制缩略图中的关卡元素
            for ty, trow in enumerate(level_data):
                for tx, tcell in enumerate(trow):
                    tpx = t_start_x + tx * cell_size
                    tpy = t_start_y + ty * cell_size
                    trect = pygame.Rect(tpx, tpy, cell_size, cell_size)

                    if tcell == 0:  # 墙
                        pygame.draw.rect(self.surface, COLORS['wall'], trect)
                        pygame.draw.rect(self.surface, COLORS['wall_border'], trect, 1)
                    elif tcell == 1:  # 箱子
                        # 箱子主体
                        pygame.draw.rect(self.surface, COLORS['box'], trect)
                        # 箱子边框
                        pygame.draw.rect(self.surface, COLORS['box_border'], trect, 1)
                        # 箱子高光效果
                        highlight_rect = pygame.Rect(tpx, tpy, cell_size, cell_size//2)
                        highlight_color = (min(COLORS['box'][0] + 30, 255), min(COLORS['box'][1] + 30, 255), min(COLORS['box'][2] + 30, 255))
                        pygame.draw.rect(self.surface, highlight_color, highlight_rect)
                    elif tcell == 2:  # 目标点
                        pygame.draw.circle(self.surface, COLORS['target'], (tpx + cell_size//2, tpy + cell_size//2), cell_size//4)
                        # 高光效果
                        pygame.draw.circle(self.surface, (255, 255, 255), (tpx + cell_size//3, tpy + cell_size//3), cell_size//8)
                    elif tcell == 3:  # 玩家
                        # 玩家主体
                        pygame.draw.circle(self.surface, COLORS['player'], (tpx + cell_size//2, tpy + cell_size//2), cell_size//3)
                        # 玩家边框
                        pygame.draw.circle(self.surface, COLORS['player_border'], (tpx + cell_size//2, tpy + cell_size//2), cell_size//3, 1)
                        # 玩家高光
                        pygame.draw.circle(self.surface, (255, 255, 255), (tpx + cell_size//2 - cell_size//6, tpy + cell_size//2 - cell_size//6), cell_size//8)
                    elif tcell == 4:  # 箱子+目标点
                        # 箱子主体
                        pygame.draw.rect(self.surface, COLORS['box_on_target'], trect)
                        # 箱子边框
                        pygame.draw.rect(self.surface, COLORS['box_border'], trect, 1)
                        # 箱子高光效果
                        highlight_rect = pygame.Rect(tpx, tpy, cell_size, cell_size//2)
                        highlight_color = (min(COLORS['box_on_target'][0] + 30, 255), min(COLORS['box_on_target'][1] + 30, 255), min(COLORS['box_on_target'][2] + 30, 255))
                        pygame.draw.rect(self.surface, highlight_color, highlight_rect)

            # 绘制关卡号带阴影（放在缩略图正上方）
            level_text = self.font.render(str(i + 1), True, COLORS['text'])
            level_rect = level_text.get_rect(center=(rect.centerx, y + thumbnail_offset_y - 20))
            shadow_level_rect = level_rect.copy()
            shadow_level_rect.move_ip(1, 1)
            shadow_level_text = self.font.render(str(i + 1), True, (200, 200, 200))
            self.surface.blit(shadow_level_text, shadow_level_rect)
            self.surface.blit(level_text, level_rect)

        # 绘制糖果马卡龙风格的分页按钮
        self.total_pages = (level_count + self.levels_per_page - 1) // self.levels_per_page
        
        # 分页按钮的糖果马卡龙颜色
        pagination_colors = [
            (255, 182, 193),  # 浅粉
            (230, 190, 255),  # 浅紫
            (180, 230, 250)   # 浅青
        ]
        
        # 创建分页区域背景
        pagination_bg_rect = pygame.Rect(WINDOW_WIDTH // 2 - 180, WINDOW_HEIGHT - 120, 360, 80)
        pagination_bg_surface = pygame.Surface((pagination_bg_rect.width, pagination_bg_rect.height), pygame.SRCALPHA)
        
        # 绘制半透明背景
        pygame.draw.rect(pagination_bg_surface, (255, 255, 255, 40), 
                        (0, 0, pagination_bg_rect.width, pagination_bg_rect.height), 
                        border_radius=20)
        pygame.draw.rect(pagination_bg_surface, (255, 255, 255, 80), 
                        (0, 0, pagination_bg_rect.width, pagination_bg_rect.height), 2, 
                        border_radius=20)
        
        # 添加装饰
        for i in range(4):
            x = pagination_bg_rect.width * (0.2 + i * 0.2)
            y = pagination_bg_rect.height * 0.2
            pygame.draw.circle(pagination_bg_surface, (255, 255, 255, 60), (int(x), int(y)), 5)
        
        self.surface.blit(pagination_bg_surface, pagination_bg_rect)
        
        # 上一页按钮 - 圆形糖果风格
        prev_button_size = 50
        self.prev_page_rect = pygame.Rect(
            WINDOW_WIDTH // 2 - 120, 
            WINDOW_HEIGHT - 90, 
            prev_button_size, 
            prev_button_size
        )
        prev_hovered = self.prev_page_rect.collidepoint(mouse_pos)
        prev_color = pagination_colors[0]
        
        if prev_hovered or (self.current_page > 1):
            # 绘制圆形按钮
            if prev_hovered:
                # 悬停效果
                glow_surface = pygame.Surface((prev_button_size + 20, prev_button_size + 20), pygame.SRCALPHA)
                for r in range(10, 0, -1):
                    alpha = max(0, min(255, int(40 - r * 3)))
                    pygame.draw.circle(glow_surface, prev_color + (alpha,), 
                                     (prev_button_size//2 + 10, prev_button_size//2 + 10), 
                                     prev_button_size//2 + r)
                self.surface.blit(glow_surface, 
                                (self.prev_page_rect.x - 10, self.prev_page_rect.y - 10))
                
                # 亮色按钮
                lighter_color = tuple(min(255, c + 20) for c in prev_color)
                pygame.draw.circle(self.surface, lighter_color, 
                                 self.prev_page_rect.center, prev_button_size//2)
                pygame.draw.circle(self.surface, (255, 255, 255), 
                                 self.prev_page_rect.center, prev_button_size//2, 2)
            else:
                # 正常状态
                pygame.draw.circle(self.surface, prev_color, 
                                 self.prev_page_rect.center, prev_button_size//2)
                pygame.draw.circle(self.surface, (255, 255, 255, 150), 
                                 self.prev_page_rect.center, prev_button_size//2, 2)
            
            # 绘制三角形图标
            arrow_points = [
                (self.prev_page_rect.centerx - 8, self.prev_page_rect.centery),
                (self.prev_page_rect.centerx + 4, self.prev_page_rect.centery - 12),
                (self.prev_page_rect.centerx + 4, self.prev_page_rect.centery + 12)
            ]
            pygame.draw.polygon(self.surface, (255, 255, 255), arrow_points)
        
        # 页码显示 - 糖果风格
        page_font = pygame.font.Font(FONT_NAME, 24)
        page_text = page_font.render(f"{self.current_page}/{self.total_pages}", True, (255, 105, 180))
        page_rect = page_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT - 80))
        
        # 页码阴影
        shadow_text = page_font.render(f"{self.current_page}/{self.total_pages}", True, (150, 100, 150))
        shadow_rect = page_rect.copy()
        shadow_rect.move_ip(2, 2)
        self.surface.blit(shadow_text, shadow_rect)
        self.surface.blit(page_text, page_rect)
        
        # 下一页按钮 - 圆形糖果风格
        next_button_size = 50
        self.next_page_rect = pygame.Rect(
            WINDOW_WIDTH // 2 + 70, 
            WINDOW_HEIGHT - 90, 
            next_button_size, 
            next_button_size
        )
        next_hovered = self.next_page_rect.collidepoint(mouse_pos)
        next_color = pagination_colors[2]
        
        if next_hovered or (self.current_page < self.total_pages):
            # 绘制圆形按钮
            if next_hovered:
                # 悬停效果
                glow_surface = pygame.Surface((next_button_size + 20, next_button_size + 20), pygame.SRCALPHA)
                for r in range(10, 0, -1):
                    alpha = max(0, min(255, int(40 - r * 3)))
                    pygame.draw.circle(glow_surface, next_color + (alpha,), 
                                     (next_button_size//2 + 10, next_button_size//2 + 10), 
                                     next_button_size//2 + r)
                self.surface.blit(glow_surface, 
                                (self.next_page_rect.x - 10, self.next_page_rect.y - 10))
                
                # 亮色按钮
                lighter_color = tuple(min(255, c + 20) for c in next_color)
                pygame.draw.circle(self.surface, lighter_color, 
                                 self.next_page_rect.center, next_button_size//2)
                pygame.draw.circle(self.surface, (255, 255, 255), 
                                 self.next_page_rect.center, next_button_size//2, 2)
            else:
                # 正常状态
                pygame.draw.circle(self.surface, next_color, 
                                 self.next_page_rect.center, next_button_size//2)
                pygame.draw.circle(self.surface, (255, 255, 255, 150), 
                                 self.next_page_rect.center, next_button_size//2, 2)
            
            # 绘制三角形图标
            arrow_points = [
                (self.next_page_rect.centerx + 8, self.next_page_rect.centery),
                (self.next_page_rect.centerx - 4, self.next_page_rect.centery - 12),
                (self.next_page_rect.centerx - 4, self.next_page_rect.centery + 12)
            ]
            pygame.draw.polygon(self.surface, (255, 255, 255), arrow_points)

        # 绘制糖果马卡龙风格的返回活动页面按钮
        back_button_size = 60
        self.activity_back_rect = pygame.Rect(
            WINDOW_WIDTH - 80, 
            30, 
            back_button_size, 
            back_button_size
        )
        activity_back_hovered = self.activity_back_rect.collidepoint(mouse_pos)
        
        # 使用浅紫色作为返回按钮的颜色
        back_color = (230, 190, 255)  # 浅紫
        
        # 绘制圆形按钮
        if activity_back_hovered:
            # 悬停效果
            glow_surface = pygame.Surface((back_button_size + 20, back_button_size + 20), pygame.SRCALPHA)
            for r in range(10, 0, -1):
                alpha = max(0, min(255, int(40 - r * 3)))
                pygame.draw.circle(glow_surface, back_color + (alpha,), 
                                 (back_button_size//2 + 10, back_button_size//2 + 10), 
                                 back_button_size//2 + r)
            self.surface.blit(glow_surface, 
                            (self.activity_back_rect.x - 10, self.activity_back_rect.y - 10))
            
            # 亮色按钮
            lighter_color = tuple(min(255, c + 20) for c in back_color)
            pygame.draw.circle(self.surface, lighter_color, 
                             self.activity_back_rect.center, back_button_size//2)
            pygame.draw.circle(self.surface, (255, 255, 255), 
                             self.activity_back_rect.center, back_button_size//2, 2)
        else:
            # 正常状态
            pygame.draw.circle(self.surface, back_color, 
                             self.activity_back_rect.center, back_button_size//2)
            pygame.draw.circle(self.surface, (255, 255, 255, 150), 
                             self.activity_back_rect.center, back_button_size//2, 2)
            
            # 添加装饰性小点
            for i in range(4):
                angle = i * math.pi / 2
                dot_x = self.activity_back_rect.centerx + int(math.cos(angle) * (back_button_size//2 - 5))
                dot_y = self.activity_back_rect.centery + int(math.sin(angle) * (back_button_size//2 - 5))
                pygame.draw.circle(self.surface, (255, 255, 255, 150), (dot_x, dot_y), 2)
        
        # 绘制返回图标（房子图标）
        icon_size = back_button_size // 2
        icon_rect = pygame.Rect(
            self.activity_back_rect.centerx - icon_size // 2,
            self.activity_back_rect.centery - icon_size // 2,
            icon_size,
            icon_size
        )
        
        # 绘制房子图标
        # 屋顶
        roof_points = [
            (icon_rect.centerx, icon_rect.y),
            (icon_rect.x, icon_rect.y + icon_size * 0.4),
            (icon_rect.right, icon_rect.y + icon_size * 0.4)
        ]
        pygame.draw.polygon(self.surface, (255, 255, 255), roof_points)
        
        # 房子主体
        house_rect = pygame.Rect(
            icon_rect.x + icon_size * 0.2,
            icon_rect.y + icon_size * 0.4,
            icon_size * 0.6,
            icon_size * 0.6
        )
        pygame.draw.rect(self.surface, (255, 255, 255), house_rect)
        
        # 门
        door_rect = pygame.Rect(
            icon_rect.centerx - icon_size * 0.15,
            icon_rect.y + icon_size * 0.6,
            icon_size * 0.3,
            icon_size * 0.4
        )
        pygame.draw.rect(self.surface, back_color, door_rect)

    def draw_playing(self):
        """绘制游戏界面"""
        # 绘制现代化渐变背景
        # 创建从浅蓝到深蓝的多层次渐变背景
        for y in range(WINDOW_HEIGHT):
            # 主渐变 - 从顶部到底部
            progress = y / WINDOW_HEIGHT
            r = int(240 - progress * 20)
            g = int(245 - progress * 15)
            b = int(255 - progress * 5)
            color = (r, g, b)
            pygame.draw.line(self.surface, color, (0, y), (WINDOW_WIDTH, y))
        
        # 添加网格图案
        grid_size = 40
        grid_color = (230, 240, 255, 30)  # 非常淡的蓝色
        for x in range(0, WINDOW_WIDTH, grid_size):
            pygame.draw.line(self.surface, grid_color, (x, 0), (x, WINDOW_HEIGHT))
        for y in range(0, WINDOW_HEIGHT, grid_size):
            pygame.draw.line(self.surface, grid_color, (0, y), (WINDOW_WIDTH, y))
        
        # 添加装饰性圆形
        for i in range(5):  # 添加5个装饰圆
            circle_radius = 100 + i * 30
            circle_x = WINDOW_WIDTH * (0.1 + i * 0.2)
            circle_y = WINDOW_HEIGHT * (0.8 - i * 0.1)
            circle_color = (200, 220, 255, 10)  # 非常淡的蓝色
            
            # 创建一个带有alpha通道的surface来绘制圆形
            circle_surface = pygame.Surface((circle_radius*2, circle_radius*2), pygame.SRCALPHA)
            pygame.draw.circle(circle_surface, circle_color, (circle_radius, circle_radius), circle_radius)
            self.surface.blit(circle_surface, (circle_x - circle_radius, circle_y - circle_radius))
        
        # 添加顶部光晕
        glow_radius = 300
        glow_x = WINDOW_WIDTH // 2
        glow_y = 0
        
        # 创建一个带有alpha通道的surface来绘制光晕
        glow_surface = pygame.Surface((glow_radius*2, glow_radius), pygame.SRCALPHA)
        for r in range(glow_radius, 0, -2):  # 从外到内绘制同心半圆
            alpha = max(0, min(255, int(20 - (glow_radius - r) * 0.1)))
            pygame.draw.circle(glow_surface, (255, 255, 255, alpha), (glow_radius, 0), r)
        self.surface.blit(glow_surface, (glow_x - glow_radius, glow_y))

        # 绘制标题和关卡信息带阴影和光晕
        title_text = self.font.render(f"推箱子 - 关卡 {self.current_level}", True, COLORS['text'])
        title_rect = title_text.get_rect(center=(WINDOW_WIDTH // 2, 50))
        
        # 添加标题光晕
        title_glow_surface = pygame.Surface((title_rect.width + 40, title_rect.height + 40), pygame.SRCALPHA)
        for r in range(20, 0, -1):
            alpha = max(0, min(255, int(100 - r * 5)))
            pygame.draw.rect(title_glow_surface, (100, 150, 255, alpha), 
                            (20-r, 20-r, title_rect.width+r*2, title_rect.height+r*2), 
                            border_radius=r)
        self.surface.blit(title_glow_surface, (title_rect.x - 20, title_rect.y - 20))
        
        # 标题阴影
        shadow_title_rect = title_rect.copy()
        shadow_title_rect.move_ip(2, 2)
        shadow_title_text = self.font.render(f"推箱子 - 关卡 {self.current_level}", True, (150, 150, 180))
        self.surface.blit(shadow_title_text, shadow_title_rect)
        
        # 标题文本
        self.surface.blit(title_text, title_rect)

        # 绘制步数卡片
        stats_bg = pygame.Rect(40, 40, 150, 80)
        pygame.draw.rect(self.surface, (255, 255, 255, 180), stats_bg, border_radius=10)
        pygame.draw.rect(self.surface, COLORS['primary_light'], stats_bg, 2, border_radius=10)

        # 绘制步数
        moves_text = self.small_font.render(f"步数: {self.moves}", True, COLORS['text_small'])
        self.surface.blit(moves_text, (50, 50))

        # 绘制最佳步数
        best_move = self.best_moves.get(str(self.current_level), "--")
        best_text = self.small_font.render(f"最佳: {best_move}", True, COLORS['text_small'])
        self.surface.blit(best_text, (50, 80))

        # 绘制撤销按钮
        mouse_pos = pygame.mouse.get_pos()
        self.undo_button_rect = pygame.Rect(WINDOW_WIDTH - 120, 40, 100, 40)
        undo_hovered = self.undo_button_rect.collidepoint(mouse_pos)
        if undo_hovered:
            pygame.draw.rect(self.surface, (230, 240, 255), self.undo_button_rect, border_radius=5)
            pygame.draw.rect(self.surface, COLORS['primary_light'], self.undo_button_rect, 2, border_radius=5)
        else:
            pygame.draw.rect(self.surface, COLORS['button_bg'], self.undo_button_rect, border_radius=5)
            pygame.draw.rect(self.surface, COLORS['button_border'], self.undo_button_rect, 2, border_radius=5)
        undo_text = self.small_font.render("撤销", True, COLORS['text'])
        undo_rect_text = undo_text.get_rect(center=self.undo_button_rect.center)
        self.surface.blit(undo_text, undo_rect_text)

        # 绘制返回活动页面按钮
        self.activity_back_rect = pygame.Rect(WINDOW_WIDTH - 120, 90, 100, 40)
        activity_back_hovered = self.activity_back_rect.collidepoint(mouse_pos)
        if activity_back_hovered:
            pygame.draw.rect(self.surface, (230, 240, 255), self.activity_back_rect, border_radius=5)
            pygame.draw.rect(self.surface, COLORS['primary_light'], self.activity_back_rect, 2, border_radius=5)
        else:
            pygame.draw.rect(self.surface, COLORS['button_bg'], self.activity_back_rect, border_radius=5)
            pygame.draw.rect(self.surface, COLORS['button_border'], self.activity_back_rect, 2, border_radius=5)
        activity_back_text = self.small_font.render("活动页面", True, COLORS['text'])
        activity_back_rect_text = activity_back_text.get_rect(center=self.activity_back_rect.center)
        self.surface.blit(activity_back_text, activity_back_rect_text)

        # 绘制选择关卡按钮
        self.level_select_button_rect = pygame.Rect(WINDOW_WIDTH - 120, 140, 100, 40)
        level_select_hovered = self.level_select_button_rect.collidepoint(mouse_pos)
        if level_select_hovered:
            pygame.draw.rect(self.surface, (230, 240, 255), self.level_select_button_rect, border_radius=5)
            pygame.draw.rect(self.surface, COLORS['primary_light'], self.level_select_button_rect, 2, border_radius=5)
        else:
            pygame.draw.rect(self.surface, COLORS['button_bg'], self.level_select_button_rect, border_radius=5)
            pygame.draw.rect(self.surface, COLORS['button_border'], self.level_select_button_rect, 2, border_radius=5)
        level_select_text = self.small_font.render("选择关卡", True, COLORS['text'])
        level_select_rect_text = level_select_text.get_rect(center=self.level_select_button_rect.center)
        self.surface.blit(level_select_text, level_select_rect_text)

        # 绘制游戏网格区域阴影
        grid_width = len(self.grid[0]) * self.cell_size
        grid_height = len(self.grid) * self.cell_size
        grid_shadow_rect = pygame.Rect(
            self.offset_x - 5, 
            self.offset_y - 5, 
            grid_width + 10, 
            grid_height + 10
        )
        pygame.draw.rect(self.surface, (0, 0, 0, 30), grid_shadow_rect, border_radius=5)

        # 绘制游戏网格
        for y, row in enumerate(self.grid):
            for x, cell in enumerate(row):
                # 计算单元格位置
                px = self.offset_x + x * self.cell_size
                py = self.offset_y + y * self.cell_size
                rect = pygame.Rect(px, py, self.cell_size, self.cell_size)

                # 绘制地面（轻微渐变）
                ground_color = (250, 250, 250)
                if (x + y) % 2 == 0:
                    ground_color = (252, 252, 252)
                pygame.draw.rect(self.surface, ground_color, rect)
                pygame.draw.rect(self.surface, (200, 200, 200), rect, 1)

                # 绘制墙 - 增强3D效果
                if cell == 0:
                    # 墙的阴影
                    shadow_rect = rect.copy()
                    shadow_rect.move_ip(4, 4)
                    pygame.draw.rect(self.surface, (30, 30, 100, 100), shadow_rect, border_radius=5)
                    
                    # 墙的主体 - 渐变填充
                    wall_rect = pygame.Rect(px + 2, py + 2, self.cell_size - 4, self.cell_size - 4)
                    for i in range(wall_rect.height):
                        # 垂直渐变，顶部更亮
                        gradient_factor = 1 - (i / wall_rect.height) * 0.5
                        gradient_color = (
                            int(COLORS['wall'][0] * gradient_factor),
                            int(COLORS['wall'][1] * gradient_factor),
                            int(COLORS['wall'][2] * gradient_factor)
                        )
                        pygame.draw.line(self.surface, gradient_color, 
                                        (wall_rect.left, wall_rect.top + i), 
                                        (wall_rect.right, wall_rect.top + i), 1)
                    
                    # 墙的边框 - 圆角
                    pygame.draw.rect(self.surface, COLORS['wall_border'], wall_rect, 2, border_radius=5)
                    
                    # 墙的纹理效果 - 砖块图案
                    brick_height = self.cell_size // 4
                    brick_offset = self.cell_size // 8
                    for row in range(3):
                        y_pos = py + 4 + row * brick_height
                        # 偶数行偏移
                        offset = brick_offset if row % 2 == 0 else 0
                        
                        # 绘制水平砖缝
                        if row > 0:
                            pygame.draw.line(self.surface, COLORS['wall_border'], 
                                            (px + 4, y_pos), 
                                            (px + self.cell_size - 4, y_pos), 1)
                        
                        # 绘制垂直砖缝
                        for col in range(2):
                            x_pos = px + 4 + offset + col * (self.cell_size // 2)
                            if x_pos < px + self.cell_size - 4:
                                pygame.draw.line(self.surface, COLORS['wall_border'], 
                                                (x_pos, y_pos), 
                                                (x_pos, y_pos + brick_height), 1)
                    
                    # 墙的高光效果 - 顶部和左侧边缘
                    highlight_color = (100, 100, 220)
                    pygame.draw.line(self.surface, highlight_color, 
                                    (px + 4, py + 4), 
                                    (px + self.cell_size - 4, py + 4), 2)
                    pygame.draw.line(self.surface, highlight_color, 
                                    (px + 4, py + 4), 
                                    (px + 4, py + self.cell_size - 4), 2)

                # 绘制目标点 - 糖果马卡龙风格（浅粉-浅紫-浅青）
                if [x, y] in self.target_positions:
                    center = (px + self.cell_size//2, py + self.cell_size//2)
                    base_radius = self.cell_size//3
                    
                    # 计算脉动效果（基于游戏时间）
                    pulse = math.sin(self.time_passed * 0.005) * 0.2 + 0.8
                    pulse_radius = int(base_radius * pulse)
                    
                    # 马卡龙糖果风格 - 三层渐变光环
                    # 外层 - 浅青色
                    outer_color = (180, 230, 230, 180)
                    outer_surface = pygame.Surface((pulse_radius*2 + 8, pulse_radius*2 + 8), pygame.SRCALPHA)
                    pygame.draw.circle(outer_surface, outer_color, (pulse_radius + 4, pulse_radius + 4), pulse_radius + 4)
                    self.surface.blit(outer_surface, (center[0] - pulse_radius - 4, center[1] - pulse_radius - 4))
                    
                    # 中层 - 浅紫色
                    middle_color = (220, 180, 230, 200)
                    middle_surface = pygame.Surface((pulse_radius*2 + 4, pulse_radius*2 + 4), pygame.SRCALPHA)
                    pygame.draw.circle(middle_surface, middle_color, (pulse_radius + 2, pulse_radius + 2), pulse_radius + 2)
                    self.surface.blit(middle_surface, (center[0] - pulse_radius - 2, center[1] - pulse_radius - 2))
                    
                    # 内层 - 浅粉色
                    inner_color = (255, 200, 220)
                    pygame.draw.circle(self.surface, inner_color, center, pulse_radius)
                    
                    # 添加糖果质感 - 白色高光
                    gloss_pos = (center[0] - pulse_radius//3, center[1] - pulse_radius//3)
                    pygame.draw.circle(self.surface, (255, 255, 255, 200), gloss_pos, pulse_radius//3)
                    
                    # 添加小装饰点 - 糖果粒
                    for i in range(6):
                        angle = i * 60
                        rad = math.radians(angle)
                        sprinkle_x = center[0] + math.cos(rad) * (pulse_radius * 0.7)
                        sprinkle_y = center[1] + math.sin(rad) * (pulse_radius * 0.7)
                        sprinkle_color = (255, 255, 255) if i % 3 == 0 else \
                                        (180, 230, 230) if i % 3 == 1 else (220, 180, 230)
                        pygame.draw.circle(self.surface, sprinkle_color, (int(sprinkle_x), int(sprinkle_y)), 2)

        # 绘制箱子 - 现代化3D木箱效果
        for bx, by in self.box_positions:
            px = self.offset_x + bx * self.cell_size
            py = self.offset_y + by * self.cell_size
            
            # 如果箱子在目标点上，使用不同颜色
            if [bx, by] in self.target_positions:
                box_color = COLORS['box_on_target']
                glow_color = (220, 180, 255, 100)  # 紫色光晕
            else:
                box_color = COLORS['box']
                glow_color = None
            
            # 箱子阴影
            shadow_offset = 4
            shadow_rect = pygame.Rect(px + 5 + shadow_offset, py + 5 + shadow_offset, 
                                    self.cell_size - 10, self.cell_size - 10)
            shadow_surface = pygame.Surface((shadow_rect.width, shadow_rect.height), pygame.SRCALPHA)
            pygame.draw.rect(shadow_surface, (0, 0, 0, 100), 
                            pygame.Rect(0, 0, shadow_rect.width, shadow_rect.height), 
                            border_radius=5)
            self.surface.blit(shadow_surface, (shadow_rect.left, shadow_rect.top))
            
            # 如果在目标点上，添加光晕效果
            if glow_color:
                glow_size = self.cell_size + 10
                glow_surface = pygame.Surface((glow_size, glow_size), pygame.SRCALPHA)
                pygame.draw.circle(glow_surface, glow_color, (glow_size//2, glow_size//2), glow_size//2)
                self.surface.blit(glow_surface, (px + self.cell_size//2 - glow_size//2, 
                                                py + self.cell_size//2 - glow_size//2))
            
            # 箱子主体 - 圆角矩形
            box_rect = pygame.Rect(px + 5, py + 5, self.cell_size - 10, self.cell_size - 10)
            box_surface = pygame.Surface((box_rect.width, box_rect.height), pygame.SRCALPHA)
            
            # 箱子主体 - 立体渐变填充
            for i in range(box_rect.height):
                # 垂直渐变，顶部更亮
                gradient_factor = 1 - (i / box_rect.height) * 0.5
                gradient_color = (
                    int(box_color[0] * gradient_factor),
                    int(box_color[1] * gradient_factor),
                    int(box_color[2] * gradient_factor)
                )
                pygame.draw.line(box_surface, gradient_color, 
                                (0, i), (box_rect.width, i), 1)
            
            # 应用圆角
            pygame.draw.rect(box_surface, (0, 0, 0, 0), 
                            pygame.Rect(0, 0, box_rect.width, box_rect.height), 
                            border_radius=8)
            
            # 木箱纹理 - 木板条纹
            plank_height = box_rect.height // 4
            for i in range(4):
                y_pos = i * plank_height
                # 木板颜色变化
                plank_color = (
                    max(box_color[0]-20+i*10, 0),
                    max(box_color[1]-20+i*10, 0),
                    max(box_color[2]-20+i*10, 0)
                )
                pygame.draw.rect(box_surface, plank_color, 
                                pygame.Rect(0, y_pos, box_rect.width, plank_height), 0)
                # 木板间隙
                if i < 3:
                    gap_y = y_pos + plank_height - 1
                    pygame.draw.line(box_surface, (max(box_color[0]-50, 0), 
                                                max(box_color[1]-50, 0), 
                                                max(box_color[2]-50, 0)), 
                                    (0, gap_y), (box_rect.width, gap_y), 2)
            
            # 应用到主表面
            self.surface.blit(box_surface, (box_rect.left, box_rect.top))
            
            # 箱子边框 - 增强立体感
            pygame.draw.rect(self.surface, (max(box_color[0]-70, 0), 
                                        max(box_color[1]-70, 0), 
                                        max(box_color[2]-70, 0)), 
                            box_rect, 2, border_radius=8)
            
            # 箱子高光效果 - 左上角和顶部边缘
            highlight_color = (min(box_color[0] + 70, 255), 
                            min(box_color[1] + 70, 255), 
                            min(box_color[2] + 70, 255))
            
            # 顶部高光
            pygame.draw.line(self.surface, highlight_color, 
                            (box_rect.left + 2, box_rect.top + 2), 
                            (box_rect.right - 2, box_rect.top + 2), 2)
            # 左侧高光
            pygame.draw.line(self.surface, highlight_color, 
                            (box_rect.left + 2, box_rect.top + 2), 
                            (box_rect.left + 2, box_rect.bottom - 2), 2)
            
            # 金属装饰 - 箱子角落
            corner_size = max(4, self.cell_size // 12)
            for corner in [(0, 0), (1, 0), (0, 1), (1, 1)]:
                corner_x = box_rect.left if corner[0] == 0 else box_rect.right - corner_size
                corner_y = box_rect.top if corner[1] == 0 else box_rect.bottom - corner_size
                
                # 金属角装饰
                metal_color = (180, 180, 200)
                pygame.draw.rect(self.surface, metal_color, 
                                pygame.Rect(corner_x, corner_y, corner_size, corner_size), 
                                border_radius=2)
                # 金属高光
                pygame.draw.line(self.surface, (230, 230, 250), 
                                (corner_x + 1, corner_y + 1), 
                                (corner_x + corner_size - 1, corner_y + 1), 1)
                pygame.draw.line(self.surface, (230, 230, 250), 
                                (corner_x + 1, corner_y + 1), 
                                (corner_x + 1, corner_y + corner_size - 1), 1)


        # 绘制玩家 - 现代卡通风格角色
        px = self.offset_x + self.player_pos[0] * self.cell_size
        py = self.offset_y + self.player_pos[1] * self.cell_size
        center_x, center_y = px + self.cell_size//2, py + self.cell_size//2
        
        # 角色阴影
        shadow_radius = self.cell_size//3
        shadow_surface = pygame.Surface((shadow_radius*2, shadow_radius), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow_surface, (0, 0, 0, 80), pygame.Rect(0, 0, shadow_radius*2, shadow_radius))
        self.surface.blit(shadow_surface, (center_x - shadow_radius, center_y + self.cell_size//3))
        
        # 角色动画效果 - 轻微上下浮动
        float_offset = math.sin(self.time_passed * 0.01) * 2
        
        # 玩家身体 - 圆形主体
        body_radius = self.cell_size//2.5
        body_center_y = center_y - float_offset
        
        # 创建身体表面
        body_size = int(body_radius * 2)
        body_surface = pygame.Surface((body_size, body_size), pygame.SRCALPHA)
        
        # 身体渐变填充
        main_color = COLORS['player']
        highlight_color = (min(main_color[0] + 50, 255), min(main_color[1] + 50, 255), min(main_color[2] + 50, 255))
        shadow_color = (max(main_color[0] - 50, 0), max(main_color[1] - 50, 0), max(main_color[2] - 50, 0))
        
        # 绘制圆形身体
        pygame.draw.circle(body_surface, main_color, (body_radius, body_radius), body_radius)
        
        # 添加高光
        highlight_radius = body_radius * 0.8
        highlight_offset = body_radius * 0.3
        pygame.draw.circle(body_surface, highlight_color, 
                          (body_radius - highlight_offset, body_radius - highlight_offset), 
                          highlight_radius, 0, draw_top_left=True, draw_top_right=False, 
                          draw_bottom_left=False, draw_bottom_right=False)
        
        # 添加阴影
        pygame.draw.circle(body_surface, shadow_color, 
                          (body_radius, body_radius), 
                          body_radius, 3)
        
        # 应用到主表面
        self.surface.blit(body_surface, (center_x - body_radius, body_center_y - body_radius))
        
        # 玩家头部 - 更大更可爱的圆形
        head_radius = self.cell_size//3
        head_center_y = body_center_y - body_radius * 0.6
        
        # 创建头部表面
        head_size = int(head_radius * 2.2)
        head_surface = pygame.Surface((head_size, head_size), pygame.SRCALPHA)
        
        # 头部颜色
        head_color = COLORS['player_head']
        head_highlight = (min(head_color[0] + 50, 255), min(head_color[1] + 50, 255), min(head_color[2] + 50, 255))
        head_shadow = (max(head_color[0] - 30, 0), max(head_color[1] - 30, 0), max(head_color[2] - 30, 0))
        
        # 绘制头部
        pygame.draw.circle(head_surface, head_color, (head_radius, head_radius), head_radius)
        
        # 头部高光
        pygame.draw.circle(head_surface, head_highlight, 
                          (head_radius - head_radius*0.3, head_radius - head_radius*0.3), 
                          head_radius*0.7, 0, draw_top_left=True, draw_top_right=False, 
                          draw_bottom_left=False, draw_bottom_right=False)
        
        # 头部轮廓
        pygame.draw.circle(head_surface, head_shadow, (head_radius, head_radius), head_radius, 2)
        
        # 应用到主表面
        self.surface.blit(head_surface, (center_x - head_radius, head_center_y - head_radius))
        
        # 眼睛 - 更大更有表现力
        eye_size = head_radius // 2.5
        eye_offset = head_radius // 2
        eye_y = head_center_y - head_radius // 6
        
        # 眼白
        pygame.draw.circle(self.surface, (255, 255, 255), (center_x - eye_offset, eye_y), eye_size)
        pygame.draw.circle(self.surface, (255, 255, 255), (center_x + eye_offset, eye_y), eye_size)
        
        # 眼球 - 随时间轻微移动
        pupil_offset_x = math.sin(self.time_passed * 0.003) * (eye_size / 4)
        pupil_offset_y = math.cos(self.time_passed * 0.005) * (eye_size / 4)
        pupil_size = eye_size // 2
        
        pygame.draw.circle(self.surface, (0, 0, 0), 
                          (center_x - eye_offset + pupil_offset_x, eye_y + pupil_offset_y), 
                          pupil_size)
        pygame.draw.circle(self.surface, (0, 0, 0), 
                          (center_x + eye_offset + pupil_offset_x, eye_y + pupil_offset_y), 
                          pupil_size)
        
        # 眼睛高光
        highlight_size = pupil_size // 2
        pygame.draw.circle(self.surface, (255, 255, 255), 
                          (center_x - eye_offset + pupil_offset_x - pupil_size//3, 
                           eye_y + pupil_offset_y - pupil_size//3), 
                          highlight_size)
        pygame.draw.circle(self.surface, (255, 255, 255), 
                          (center_x + eye_offset + pupil_offset_x - pupil_size//3, 
                           eye_y + pupil_offset_y - pupil_size//3), 
                          highlight_size)

        # 手臂 - 更圆润的卡通风格
        arm_width = body_radius//2
        arm_height = body_radius//3
        arm_offset_y = float_offset * 0.5  # 随浮动效果轻微摆动
        
        # 左手臂
        left_arm_angle = math.sin(self.time_passed * 0.008) * 15  # 轻微摆动
        left_arm_surface = pygame.Surface((arm_width, arm_height), pygame.SRCALPHA)
        pygame.draw.ellipse(left_arm_surface, main_color, pygame.Rect(0, 0, arm_width, arm_height))
        pygame.draw.ellipse(left_arm_surface, shadow_color, pygame.Rect(0, 0, arm_width, arm_height), 2)
        
        # 旋转左手臂
        rotated_left_arm = pygame.transform.rotate(left_arm_surface, left_arm_angle)
        left_arm_pos = (center_x - body_radius - rotated_left_arm.get_width()//2, 
                        body_center_y + arm_offset_y)
        self.surface.blit(rotated_left_arm, left_arm_pos)
        
        # 右手臂
        right_arm_angle = math.sin(self.time_passed * 0.008 + math.pi) * 15  # 反向摆动
        right_arm_surface = pygame.Surface((arm_width, arm_height), pygame.SRCALPHA)
        pygame.draw.ellipse(right_arm_surface, main_color, pygame.Rect(0, 0, arm_width, arm_height))
        pygame.draw.ellipse(right_arm_surface, shadow_color, pygame.Rect(0, 0, arm_width, arm_height), 2)
        
        # 旋转右手臂
        rotated_right_arm = pygame.transform.rotate(right_arm_surface, -right_arm_angle)
        right_arm_pos = (center_x + body_radius - rotated_right_arm.get_width()//2, 
                         body_center_y + arm_offset_y)
        self.surface.blit(rotated_right_arm, right_arm_pos)
        
        # 腿部 - 更可爱的圆形
        leg_radius = body_radius//3
        leg_offset = body_radius * 0.4
        leg_y = body_center_y + body_radius * 0.7
        
        # 左腿
        left_leg_offset_x = math.sin(self.time_passed * 0.008 + math.pi/2) * 2  # 轻微左右移动
        pygame.draw.circle(self.surface, main_color, 
                          (center_x - leg_offset + left_leg_offset_x, leg_y), 
                          leg_radius)
        pygame.draw.circle(self.surface, shadow_color, 
                          (center_x - leg_offset + left_leg_offset_x, leg_y), 
                          leg_radius, 2)
        
        # 右腿
        right_leg_offset_x = math.sin(self.time_passed * 0.008 + math.pi*1.5) * 2  # 反向移动
        pygame.draw.circle(self.surface, main_color, 
                          (center_x + leg_offset + right_leg_offset_x, leg_y), 
                          leg_radius)
        pygame.draw.circle(self.surface, shadow_color, 
                          (center_x + leg_offset + right_leg_offset_x, leg_y), 
                          leg_radius, 2)
        
        # 表情 - 微笑
        smile_width = head_radius * 0.8
        smile_height = head_radius * 0.4
        smile_y = head_center_y + head_radius * 0.2
        
        # 根据游戏状态调整表情
        if self.check_win():
            # 胜利表情 - 大笑
            pygame.draw.arc(self.surface, (0, 0, 0), 
                           pygame.Rect(center_x - smile_width//2, smile_y - smile_height//2, 
                                      smile_width, smile_height), 
                           0, math.pi, 3)
        else:
            # 普通表情 - 微笑
            pygame.draw.arc(self.surface, (0, 0, 0), 
                           pygame.Rect(center_x - smile_width//2, smile_y - smile_height//2, 
                                      smile_width, smile_height), 
                           0, math.pi, 2)

        # 绘制操作提示 - 半透明背景
        hint_bg = pygame.Rect(WINDOW_WIDTH//2 - 250, WINDOW_HEIGHT - 40, 500, 30)
        pygame.draw.rect(self.surface, (255, 255, 255, 150), hint_bg, border_radius=15)
        hint_text = self.very_small_font.render("方向键移动, R键重置, Ctrl+Z撤销, ESC返回关卡选择", True, COLORS['text_small'])
        hint_rect = hint_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT - 25))
        self.surface.blit(hint_text, hint_rect)

    def draw_win(self):
        """绘制胜利界面"""
        # 绘制半透明覆盖层
        s = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        s.fill(COLORS['overlay'])
        self.surface.blit(s, (0, 0))

        # 绘制胜利信息带阴影
        win_text = self.font.render("恭喜过关!", True, COLORS['text'])
        win_rect = win_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 100))
        shadow_win_rect = win_rect.copy()
        shadow_win_rect.move_ip(3, 3)
        shadow_win_text = self.font.render("恭喜过关!", True, (200, 200, 200))
        self.surface.blit(shadow_win_text, shadow_win_rect)
        self.surface.blit(win_text, win_rect)

        # 绘制步数信息
        moves_text = self.small_font.render(f"您用了 {self.moves} 步", True, COLORS['text_small'])
        moves_rect = moves_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 40))
        self.surface.blit(moves_text, moves_rect)

        # 获取鼠标位置用于悬停效果
        mouse_pos = pygame.mouse.get_pos()

        # 绘制下一关按钮
        self.next_level_rect = pygame.Rect(WINDOW_WIDTH // 2 - 160, WINDOW_HEIGHT // 2 + 20, 140, 50)
        next_level_hovered = self.next_level_rect.collidepoint(mouse_pos)
        if next_level_hovered:
            pygame.draw.rect(self.surface, (230, 240, 255), self.next_level_rect, border_radius=10)
            pygame.draw.rect(self.surface, COLORS['primary_light'], self.next_level_rect, 3, border_radius=10)
        else:
            pygame.draw.rect(self.surface, COLORS['button_bg'], self.next_level_rect, border_radius=10)
            pygame.draw.rect(self.surface, COLORS['button_border'], self.next_level_rect, 2, border_radius=10)
        next_level_text = self.small_font.render("下一关", True, COLORS['text'])
        next_level_rect_text = next_level_text.get_rect(center=self.next_level_rect.center)
        self.surface.blit(next_level_text, next_level_rect_text)

        # 绘制返回关卡选择按钮
        self.back_to_level_rect = pygame.Rect(WINDOW_WIDTH // 2 + 20, WINDOW_HEIGHT // 2 + 20, 140, 50)
        back_to_level_hovered = self.back_to_level_rect.collidepoint(mouse_pos)
        if back_to_level_hovered:
            pygame.draw.rect(self.surface, (230, 240, 255), self.back_to_level_rect, border_radius=10)
            pygame.draw.rect(self.surface, COLORS['primary_light'], self.back_to_level_rect, 3, border_radius=10)
        else:
            pygame.draw.rect(self.surface, COLORS['button_bg'], self.back_to_level_rect, border_radius=10)
            pygame.draw.rect(self.surface, COLORS['button_border'], self.back_to_level_rect, 2, border_radius=10)
        back_to_level_text = self.small_font.render("关卡选择", True, COLORS['text'])
        back_to_level_rect_text = back_to_level_text.get_rect(center=self.back_to_level_rect.center)
        self.surface.blit(back_to_level_text, back_to_level_rect_text)

        # 绘制返回活动页面按钮
        self.activity_back_rect = pygame.Rect(WINDOW_WIDTH - 120, 20, 100, 40)
        activity_back_hovered = self.activity_back_rect.collidepoint(mouse_pos)
        if activity_back_hovered:
            pygame.draw.rect(self.surface, (230, 240, 255), self.activity_back_rect, border_radius=5)
            pygame.draw.rect(self.surface, COLORS['primary_light'], self.activity_back_rect, 2, border_radius=5)
        else:
            pygame.draw.rect(self.surface, COLORS['button_bg'], self.activity_back_rect, border_radius=5)
            pygame.draw.rect(self.surface, COLORS['button_border'], self.activity_back_rect, 2, border_radius=5)
        activity_back_text = self.small_font.render("活动页面", True, COLORS['text'])
        activity_back_rect_text = activity_back_text.get_rect(center=self.activity_back_rect.center)
        self.surface.blit(activity_back_text, activity_back_rect_text)

        # 添加庆祝效果 - 随机生成彩色圆点
        if not hasattr(self, 'particles'):
            self.particles = []
            for _ in range(50):
                angle = math.radians(pygame.time.get_ticks() % 360 + _ * 7.2)
                speed = 1 + random.random() * 2
                size = 2 + random.random() * 3
                self.particles.append({
                    'x': WINDOW_WIDTH // 2,
                    'y': WINDOW_HEIGHT // 2,
                    'vx': math.cos(angle) * speed,
                    'vy': math.sin(angle) * speed,
                    'size': size,
                    'color': (random.randint(50, 255), random.randint(50, 255), random.randint(50, 255)),
                    'life': 100 + random.randint(0, 50)
                })
        else:
            # 更新并绘制粒子
            for p in self.particles[:]:
                p['x'] += p['vx']
                p['y'] += p['vy']
                p['life'] -= 1
                if p['life'] <= 0:
                    self.particles.remove(p)
                    continue
                # 绘制粒子
                alpha = int(255 * (p['life'] / 150))
                s = pygame.Surface((p['size']*2, p['size']*2), pygame.SRCALPHA)
                pygame.draw.circle(s, (*p['color'], alpha), (p['size'], p['size']), p['size'])
                self.surface.blit(s, (p['x'] - p['size'], p['y'] - p['size']))

    def draw(self):
        """绘制游戏"""
        # 更新时间，用于动画效果
        self.time_passed += 1
        
        if self.state == "level_select":
            self.draw_level_select()
        elif self.state == "playing" and self.initialized:
            self.draw_playing()
        elif self.state == "win":
            self.draw_win()

    def update(self):
        """更新游戏状态"""
        # 检查是否需要返回活动页面
        if self.return_to_activity:
            self.active = False
            self.return_to_activity = False

        # 清除粒子效果（如果不在胜利界面）
        if self.state != "win" and hasattr(self, 'particles'):
            delattr(self, 'particles')

        pass