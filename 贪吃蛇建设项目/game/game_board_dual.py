import pygame
import random
from .food import Food
from .constants import GRID_SIZE, WINDOW_WIDTH, WINDOW_HEIGHT

class GameBoardDual:
    def __init__(self, snake1, snake2, board_size):
        self.snake1 = snake1
        self.snake2 = snake2
        self.board_size = board_size
        self.cell_size = GRID_SIZE
        # 使用Food类
        self.food = Food()
        self.randomize_food()
        self.create_grid_surface()

    def create_grid_surface(self):
        # 创建网格背景，风格与单人一致
        self.grid_surface = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        grid_color = (180, 180, 180)
        for x in range(0, WINDOW_WIDTH, GRID_SIZE):
            pygame.draw.line(self.grid_surface, grid_color, (x, 0), (x, WINDOW_HEIGHT))
        for y in range(0, WINDOW_HEIGHT, GRID_SIZE):
            pygame.draw.line(self.grid_surface, grid_color, (0, y), (WINDOW_WIDTH, y))

    def randomize_food(self):
        all_positions = self.snake1.positions + self.snake2.positions
        self.food.randomize_position(all_positions, [])

    def update(self):
        for snake in [self.snake1, self.snake2]:
            if len(snake.positions) > 0 and snake.positions[0] == self.food.position:
                snake.grow()
                self.randomize_food()
        # 检查碰撞（可扩展：撞墙、撞自己、撞对方）
        # ...

    def draw(self, screen):
        # 绘制背景色
        screen.fill((230, 230, 230))
        # 绘制网格
        screen.blit(self.grid_surface, (0, 0))
        # 绘制食物
        self.food.draw(screen)
        # 用皮肤系统绘制两条蛇
        self.snake1.draw(screen)
        self.snake2.draw(screen) 