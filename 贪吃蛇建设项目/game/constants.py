# -*- coding: utf-8 -*-
import pygame
import sys
import os

# 仅初始化字体模块，避免在导入常量时初始化所有子系统
pygame.font.init() # 初始化字体模块

def get_resource_path(relative_path):
    """
    获取资源文件的绝对路径
    在开发环境中直接返回相对路径
    在PyInstaller打包后返回资源文件的真实路径
    """
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller打包后的路径
        return os.path.join(sys._MEIPASS, relative_path)
    else:
        # 开发环境中的路径
        return os.path.join(os.path.abspath('.'), relative_path)

# 窗口设置
GRID_SIZE = 30
WINDOW_WIDTH = GRID_SIZE * 40  # 40个格子
WINDOW_HEIGHT = GRID_SIZE * 30  # 30个格子
FPS = 60

# 颜色定义
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
GOLD = (255, 215, 0)
TRANSPARENT = (0, 0, 0, 0)

# 游戏设置
GRID_WIDTH = WINDOW_WIDTH // GRID_SIZE  # 40个格子
GRID_HEIGHT = WINDOW_HEIGHT // GRID_SIZE  # 30个格子

# 蛇的设置
SNAKE_SPEED = 9  # 每秒移动的格子数
SNAKE_COLOR = (0, 255, 0)
SNAKE_HEAD_COLOR = (0, 200, 0)
SNAKE_ANIMATION_SPEED = 0.2  # 蛇身动画速度

# 食物设置
FOOD_COLOR = (255, 0, 0)
FOOD_ANIMATION_SPEED = 0.3  # 食物动画速度

# 障碍物设置
OBSTACLE_COLOR = (128, 128, 128)
OBSTACLE_COUNT = 5
OBSTACLE_SAFE_DISTANCE = 3  # 障碍物与蛇头和食物的安全距离

# 字体设置
# 尝试加载中文字体
# 优先尝试SimHei（黑体），如果找不到则尝试Microsoft YaHei（微软雅黑）
FONT_NAME = pygame.font.match_font('simhei') or pygame.font.match_font('microsoftyahei')
if not FONT_NAME:
    print("警告：未找到支持中文的字体（SimHei或Microsoft YaHei），中文显示可能不正常。")
FONT_SIZE = 32
SCORE_FONT_SIZE = 24
TITLE_FONT_SIZE = 48

# 按钮设置
BUTTON_WIDTH = 200
BUTTON_HEIGHT = 50
BUTTON_COLOR = (50, 50, 50)
BUTTON_HOVER_COLOR = (70, 70, 70)
BUTTON_TEXT_COLOR = WHITE
BUTTON_ANIMATION_SPEED = 0.2  # 按钮动画速度

# 背景设置
BACKGROUND_COLOR = (230, 230, 230)
BACKGROUND_SWITCH_BUTTON_SIZE = 40
BACKGROUND_SWITCH_BUTTON_COLOR = (100, 100, 100)
BACKGROUND_SWITCH_BUTTON_HOVER_COLOR = (120, 120, 120)

# 动画设置
SNOW_PARTICLE_COUNT = 50
SNOW_PARTICLE_SPEED = 1
SNOW_PARTICLE_SIZE = 2
TITLE_FLOAT_AMPLITUDE = 10
TITLE_FLOAT_SPEED = 0.5

# 菜单设置
MENU_TITLE_COLOR = (255, 255, 255)
MENU_TITLE_SHADOW_COLOR = (100, 100, 100)
MENU_BACKGROUND_ALPHA = 128  # 半透明背景的透明度

# 设置菜单
SETTINGS_MENU_WIDTH = 400
SETTINGS_MENU_HEIGHT = 300
SETTINGS_MENU_COLOR = (50, 50, 50)
SETTINGS_MENU_ALPHA = 200 