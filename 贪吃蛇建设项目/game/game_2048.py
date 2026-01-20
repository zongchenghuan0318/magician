import pygame
import random
import time
import math
from .constants import *

class Game2048:
    def __init__(self, surface):
        self.surface = surface
        self.active = True
        self.game_state = "playing"  # playing, game_over, win
        
        # 游戏区域设置
        self.grid_size = 4
        self.cell_size = 85
        self.cell_margin = 10
        self.grid_x = (WINDOW_WIDTH - self.grid_size * (self.cell_size + self.cell_margin) + self.cell_margin) // 2
        self.grid_y = 280
        
        # 游戏状态
        self.grid = [[0 for _ in range(self.grid_size)] for _ in range(self.grid_size)]
        self.score = 0
        self.best_score = 0
        self.moves = 0
        self.has_asked_continue = False  # 记录是否已经询问过继续游戏
        
        # 动画效果
        self.animation_tiles = []  # 存储动画中的方块
        self.merge_animations = []  # 合并动画
        self.new_tile_animations = []  # 新方块动画
        
        # 优化的颜色定义 - 更现代的颜色方案
        self.colors = {
            0: (238, 228, 218, 35),      # 空格子 - 半透明
            2: (238, 228, 218),          # 2 - 米色
            4: (237, 224, 200),          # 4 - 浅橙色
            8: (242, 177, 121),          # 8 - 橙色
            16: (245, 149, 99),          # 16 - 深橙色
            32: (246, 124, 95),          # 32 - 红色
            64: (246, 94, 59),           # 64 - 深红色
            128: (237, 207, 114),        # 128 - 黄色
            256: (237, 204, 97),         # 256 - 金黄色
            512: (237, 200, 80),         # 512 - 深黄色
            1024: (237, 197, 63),        # 1024 - 橙黄色
            2048: (237, 194, 46),        # 2048 - 亮黄色
            4096: (237, 191, 29),        # 4096 - 深橙黄
            8192: (237, 188, 12)         # 8192 - 最深的黄色
        }
        
        # 阴影颜色定义
        self.shadow_colors = {
            2: (119, 110, 101, 30),      # 2的阴影
            4: (119, 110, 101, 30),      # 4的阴影
            8: (119, 110, 101, 40),      # 8的阴影
            16: (119, 110, 101, 50),     # 16的阴影
            32: (119, 110, 101, 60),     # 32的阴影
            64: (119, 110, 101, 70),     # 64的阴影
            128: (119, 110, 101, 80),    # 128的阴影
            256: (119, 110, 101, 90),    # 256的阴影
            512: (119, 110, 101, 100),   # 512的阴影
            1024: (119, 110, 101, 110),  # 1024的阴影
            2048: (119, 110, 101, 120),  # 2048的阴影
            4096: (119, 110, 101, 130),  # 4096的阴影
            8192: (119, 110, 101, 140)   # 8192的阴影
        }
        
        # 字体
        self.font_large = pygame.font.Font(FONT_NAME, 56)
        self.font_medium = pygame.font.Font(FONT_NAME, 36)
        self.font_small = pygame.font.Font(FONT_NAME, 28)
        self.font_tiny = pygame.font.Font(FONT_NAME, 20)
        
        # 背景粒子效果
        self.particles = []
        self.init_particles()
        
        # 初始化游戏
        self.add_random_tile()
        self.add_random_tile()
        
    def init_particles(self):
        """初始化背景粒子"""
        for _ in range(30):  # 减少粒子数量以提高性能
            self.particles.append({
                'x': random.randint(0, WINDOW_WIDTH),
                'y': random.randint(0, WINDOW_HEIGHT),
                'vx': random.uniform(-0.3, 0.3),  # 降低速度
                'vy': random.uniform(-0.3, 0.3),
                'size': random.randint(2, 4),  # 减小粒子大小
                'alpha': random.randint(20, 60)  # 降低透明度
            })
    
    def update_particles(self):
        """更新背景粒子"""
        for particle in self.particles:
            particle['x'] += particle['vx']
            particle['y'] += particle['vy']
            
            # 边界反弹
            if particle['x'] <= 0 or particle['x'] >= WINDOW_WIDTH:
                particle['vx'] *= -1
            if particle['y'] <= 0 or particle['y'] >= WINDOW_HEIGHT:
                particle['vy'] *= -1
            
            # 确保粒子在屏幕内
            particle['x'] = max(0, min(WINDOW_WIDTH, particle['x']))
            particle['y'] = max(0, min(WINDOW_HEIGHT, particle['y']))
        
    def add_random_tile(self):
        """在随机空位置添加一个数字（2或4）"""
        empty_cells = []
        for i in range(self.grid_size):
            for j in range(self.grid_size):
                if self.grid[i][j] == 0:
                    empty_cells.append((i, j))
        
        if empty_cells:
            i, j = random.choice(empty_cells)
            value = 2 if random.random() < 0.9 else 4
            self.grid[i][j] = value
            
            # 添加新方块动画
            self.new_tile_animations.append({
                'i': i, 'j': j, 'value': value,
                'scale': 0.0, 'alpha': 0,
                'start_time': time.time()
            })
    
    def move_left(self):
        """向左移动"""
        moved = False
        for i in range(self.grid_size):
            # 合并相同的数字
            merged = [False] * self.grid_size
            for j in range(1, self.grid_size):
                if self.grid[i][j] != 0:
                    k = j
                    while k > 0 and (self.grid[i][k-1] == 0 or 
                                   (self.grid[i][k-1] == self.grid[i][k] and not merged[k-1])):
                        if self.grid[i][k-1] == 0:
                            self.grid[i][k-1] = self.grid[i][k]
                            self.grid[i][k] = 0
                            k -= 1
                            moved = True
                        elif self.grid[i][k-1] == self.grid[i][k] and not merged[k-1]:
                            self.grid[i][k-1] *= 2
                            self.grid[i][k] = 0
                            merged[k-1] = True
                            self.score += self.grid[i][k-1]
                            moved = True
                            
                            # 添加合并动画
                            self.merge_animations.append({
                                'i': i, 'j': k-1, 'value': self.grid[i][k-1],
                                'scale': 1.2, 'alpha': 255,
                                'start_time': time.time()
                            })
                            break
                        else:
                            break
        return moved
    
    def move_right(self):
        """向右移动"""
        moved = False
        for i in range(self.grid_size):
            # 合并相同的数字
            merged = [False] * self.grid_size
            for j in range(self.grid_size-2, -1, -1):
                if self.grid[i][j] != 0:
                    k = j
                    while k < self.grid_size-1 and (self.grid[i][k+1] == 0 or 
                                                  (self.grid[i][k+1] == self.grid[i][k] and not merged[k+1])):
                        if self.grid[i][k+1] == 0:
                            self.grid[i][k+1] = self.grid[i][k]
                            self.grid[i][k] = 0
                            k += 1
                            moved = True
                        elif self.grid[i][k+1] == self.grid[i][k] and not merged[k+1]:
                            self.grid[i][k+1] *= 2
                            self.grid[i][k] = 0
                            merged[k+1] = True
                            self.score += self.grid[i][k+1]
                            moved = True
                            
                            # 添加合并动画
                            self.merge_animations.append({
                                'i': i, 'j': k+1, 'value': self.grid[i][k+1],
                                'scale': 1.2, 'alpha': 255,
                                'start_time': time.time()
                            })
                            break
                        else:
                            break
        return moved
    
    def move_up(self):
        """向上移动"""
        moved = False
        for j in range(self.grid_size):
            # 合并相同的数字
            merged = [False] * self.grid_size
            for i in range(1, self.grid_size):
                if self.grid[i][j] != 0:
                    k = i
                    while k > 0 and (self.grid[k-1][j] == 0 or 
                                   (self.grid[k-1][j] == self.grid[k][j] and not merged[k-1])):
                        if self.grid[k-1][j] == 0:
                            self.grid[k-1][j] = self.grid[k][j]
                            self.grid[k][j] = 0
                            k -= 1
                            moved = True
                        elif self.grid[k-1][j] == self.grid[k][j] and not merged[k-1]:
                            self.grid[k-1][j] *= 2
                            self.grid[k][j] = 0
                            merged[k-1] = True
                            self.score += self.grid[k-1][j]
                            moved = True
                            
                            # 添加合并动画
                            self.merge_animations.append({
                                'i': k-1, 'j': j, 'value': self.grid[k-1][j],
                                'scale': 1.2, 'alpha': 255,
                                'start_time': time.time()
                            })
                            break
                        else:
                            break
        return moved
    
    def move_down(self):
        """向下移动"""
        moved = False
        for j in range(self.grid_size):
            # 合并相同的数字
            merged = [False] * self.grid_size
            for i in range(self.grid_size-2, -1, -1):
                if self.grid[i][j] != 0:
                    k = i
                    while k < self.grid_size-1 and (self.grid[k+1][j] == 0 or 
                                                  (self.grid[k+1][j] == self.grid[k][j] and not merged[k+1])):
                        if self.grid[k+1][j] == 0:
                            self.grid[k+1][j] = self.grid[k][j]
                            self.grid[k][j] = 0
                            k += 1
                            moved = True
                        elif self.grid[k+1][j] == self.grid[k][j] and not merged[k+1]:
                            self.grid[k+1][j] *= 2
                            self.grid[k][j] = 0
                            merged[k+1] = True
                            self.score += self.grid[k+1][j]
                            moved = True
                            
                            # 添加合并动画
                            self.merge_animations.append({
                                'i': k+1, 'j': j, 'value': self.grid[k+1][j],
                                'scale': 1.2, 'alpha': 255,
                                'start_time': time.time()
                            })
                            break
                        else:
                            break
        return moved
    
    def can_move(self):
        """检查是否还能移动"""
        # 检查是否有空格
        for i in range(self.grid_size):
            for j in range(self.grid_size):
                if self.grid[i][j] == 0:
                    return True
        
        # 检查是否有相邻的相同数字
        for i in range(self.grid_size):
            for j in range(self.grid_size):
                current = self.grid[i][j]
                # 检查右边
                if j < self.grid_size - 1 and self.grid[i][j+1] == current:
                    return True
                # 检查下边
                if i < self.grid_size - 1 and self.grid[i+1][j] == current:
                    return True
        
        return False
    
    def check_win(self):
        """检查是否达到2048"""
        for i in range(self.grid_size):
            for j in range(self.grid_size):
                if self.grid[i][j] >= 2048:
                    return True
        return False
    
    def reset_game(self):
        """重置游戏"""
        self.grid = [[0 for _ in range(self.grid_size)] for _ in range(self.grid_size)]
        self.score = 0
        self.moves = 0
        self.game_state = "playing"
        self.has_asked_continue = False  # 重置继续游戏询问标志
        self.animation_tiles = []
        self.merge_animations = []
        self.new_tile_animations = []
        self.add_random_tile()
        self.add_random_tile()
    
    def handle_event(self, event):
        """处理游戏事件"""
        if self.game_state == "game_over":
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.active = False
                elif event.key == pygame.K_r:
                    self.reset_game()
            return
        
        if self.game_state == "win":
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.active = False
                elif event.key == pygame.K_r:
                    self.reset_game()
                elif event.key == pygame.K_c:
                    self.game_state = "playing"  # 继续游戏
                    self.has_asked_continue = True  # 标记已经选择继续
            return
        
        # 处理鼠标点击
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # 左键点击
                mouse_x, mouse_y = event.pos
                # 检查是否点击了返回按钮
                back_button_rect = pygame.Rect(WINDOW_WIDTH - 150, WINDOW_HEIGHT - 80, 120, 50)
                if back_button_rect.collidepoint(mouse_x, mouse_y):
                    self.active = False  # 返回活动页面
                return
        
        if event.type == pygame.KEYDOWN:
            moved = False
            
            if event.key == pygame.K_LEFT:
                moved = self.move_left()
            elif event.key == pygame.K_RIGHT:
                moved = self.move_right()
            elif event.key == pygame.K_UP:
                moved = self.move_up()
            elif event.key == pygame.K_DOWN:
                moved = self.move_down()
            elif event.key == pygame.K_ESCAPE:
                self.active = False
            elif event.key == pygame.K_r:
                self.reset_game()
            
            if moved:
                self.moves += 1
                self.add_random_tile()
                
                # 更新最高分
                if self.score > self.best_score:
                    self.best_score = self.score
                
                # 检查是否获胜 - 只在第一次达到2048时询问
                if self.check_win() and self.game_state == "playing" and not self.has_asked_continue:
                    self.game_state = "win"
                
                # 检查游戏是否结束
                if not self.can_move():
                    self.game_state = "game_over"
    
    def draw_background(self):
        """绘制优化的渐变背景"""
        # 创建更美观的渐变背景 - 从温暖的米色到浅蓝
        for y in range(WINDOW_HEIGHT):
            # 从温暖的米色到浅蓝的渐变
            ratio = y / WINDOW_HEIGHT
            r = int(250 + (240 - 250) * ratio)
            g = int(245 + (248 - 245) * ratio)
            b = int(240 + (255 - 240) * ratio)
            pygame.draw.line(self.surface, (r, g, b), (0, y), (WINDOW_WIDTH, y))
        
        # 添加径向渐变效果 - 优化性能
        center_x, center_y = WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2
        max_distance = math.sqrt(center_x**2 + center_y**2)
        
        for y in range(0, WINDOW_HEIGHT, 8):  # 增加步长减少计算
            for x in range(0, WINDOW_WIDTH, 8):
                distance = math.sqrt((x - center_x)**2 + (y - center_y)**2)
                ratio = distance / max_distance
                alpha = int(15 * (1 - ratio))  # 降低透明度
                if alpha > 0:
                    overlay_surface = pygame.Surface((8, 8), pygame.SRCALPHA)
                    overlay_surface.fill((255, 255, 255, alpha))
                    self.surface.blit(overlay_surface, (x, y))
        
        # 绘制背景粒子
        self.update_particles()
        for particle in self.particles:
            particle_surface = pygame.Surface((particle['size'], particle['size']), pygame.SRCALPHA)
            pygame.draw.circle(particle_surface, (255, 255, 255, particle['alpha']), 
                             (particle['size']//2, particle['size']//2), particle['size']//2)
            self.surface.blit(particle_surface, (particle['x'], particle['y']))
    
    def draw_grid(self):
        """绘制优化的游戏网格"""
        # 绘制网格背景面板
        panel_width = self.grid_size * (self.cell_size + self.cell_margin) + self.cell_margin
        panel_height = self.grid_size * (self.cell_size + self.cell_margin) + self.cell_margin
        panel_rect = pygame.Rect(self.grid_x - 20, self.grid_y - 20, panel_width + 40, panel_height + 40)
        
        # 面板阴影
        shadow_surface = pygame.Surface((panel_width + 40, panel_height + 40), pygame.SRCALPHA)
        pygame.draw.rect(shadow_surface, (0, 0, 0, 30), (0, 0, panel_width + 40, panel_height + 40), border_radius=20)
        self.surface.blit(shadow_surface, (panel_rect.x + 5, panel_rect.y + 5))
        
        # 面板背景
        pygame.draw.rect(self.surface, (187, 173, 160), panel_rect, border_radius=20)
        
        # 绘制网格线
        for i in range(self.grid_size):
            for j in range(self.grid_size):
                x = self.grid_x + j * (self.cell_size + self.cell_margin)
                y = self.grid_y + i * (self.cell_size + self.cell_margin)
                
                # 绘制格子背景
                cell_rect = pygame.Rect(x, y, self.cell_size, self.cell_size)
                value = self.grid[i][j]
                color = self.colors.get(value, (205, 193, 180))
                
                # 如果是空格子，使用半透明效果
                if value == 0:
                    cell_surface = pygame.Surface((self.cell_size, self.cell_size), pygame.SRCALPHA)
                    pygame.draw.rect(cell_surface, color, (0, 0, self.cell_size, self.cell_size), border_radius=12)
                    self.surface.blit(cell_surface, cell_rect)
                else:
                    # 绘制阴影
                    shadow_color = self.shadow_colors.get(value, (119, 110, 101, 50))
                    shadow_surface = pygame.Surface((self.cell_size, self.cell_size), pygame.SRCALPHA)
                    pygame.draw.rect(shadow_surface, shadow_color, (3, 3, self.cell_size, self.cell_size), border_radius=12)
                    self.surface.blit(shadow_surface, (cell_rect.x + 3, cell_rect.y + 3))
                    
                    # 绘制主方块
                    pygame.draw.rect(self.surface, color, cell_rect, border_radius=12)
                    
                    # 添加高光效果
                    highlight_rect = pygame.Rect(cell_rect.x + 2, cell_rect.y + 2, cell_rect.width - 4, cell_rect.height // 3)
                    highlight_surface = pygame.Surface((highlight_rect.width, highlight_rect.height), pygame.SRCALPHA)
                    pygame.draw.rect(highlight_surface, (255, 255, 255, 30), (0, 0, highlight_rect.width, highlight_rect.height), border_radius=8)
                    self.surface.blit(highlight_surface, highlight_rect)
                
                # 绘制数字
                if value != 0:
                    # 选择字体大小
                    if value < 100:
                        font = self.font_large
                    elif value < 1000:
                        font = self.font_medium
                    else:
                        font = self.font_small
                    
                    # 选择文字颜色
                    if value <= 4:
                        text_color = (119, 110, 101)
                    else:
                        text_color = (249, 246, 242)
                    
                    text = font.render(str(value), True, text_color)
                    text_rect = text.get_rect(center=cell_rect.center)
                    self.surface.blit(text, text_rect)
        
        # 绘制动画效果
        self.draw_animations()
    
    def draw_animations(self):
        """绘制动画效果"""
        current_time = time.time()
        
        # 更新新方块动画
        for anim in self.new_tile_animations[:]:
            elapsed = current_time - anim['start_time']
            if elapsed < 0.3:  # 0.3秒动画
                progress = elapsed / 0.3
                anim['scale'] = progress
                anim['alpha'] = int(255 * progress)
                
                # 绘制动画方块
                x = self.grid_x + anim['j'] * (self.cell_size + self.cell_margin)
                y = self.grid_y + anim['i'] * (self.cell_size + self.cell_margin)
                
                # 缩放效果
                scaled_size = int(self.cell_size * anim['scale'])
                offset = (self.cell_size - scaled_size) // 2
                
                anim_surface = pygame.Surface((scaled_size, scaled_size), pygame.SRCALPHA)
                color = self.colors.get(anim['value'], (205, 193, 180))
                pygame.draw.rect(anim_surface, (*color, anim['alpha']), (0, 0, scaled_size, scaled_size), border_radius=8)
                
                # 绘制数字
                if anim['value'] < 100:
                    font = self.font_large
                elif anim['value'] < 1000:
                    font = self.font_medium
                else:
                    font = self.font_small
                
                if anim['value'] <= 4:
                    text_color = (119, 110, 101, anim['alpha'])
                else:
                    text_color = (249, 246, 242, anim['alpha'])
                
                text = font.render(str(anim['value']), True, text_color)
                text_rect = text.get_rect(center=(scaled_size//2, scaled_size//2))
                anim_surface.blit(text, text_rect)
                
                self.surface.blit(anim_surface, (x + offset, y + offset))
            else:
                self.new_tile_animations.remove(anim)
        
        # 更新合并动画
        for anim in self.merge_animations[:]:
            elapsed = current_time - anim['start_time']
            if elapsed < 0.2:  # 0.2秒动画
                progress = elapsed / 0.2
                anim['scale'] = 1.2 - 0.2 * progress
                anim['alpha'] = int(255 * (1 - progress))
                
                # 绘制合并动画
                x = self.grid_x + anim['j'] * (self.cell_size + self.cell_margin)
                y = self.grid_y + anim['i'] * (self.cell_size + self.cell_margin)
                
                scaled_size = int(self.cell_size * anim['scale'])
                offset = (self.cell_size - scaled_size) // 2
                
                anim_surface = pygame.Surface((scaled_size, scaled_size), pygame.SRCALPHA)
                color = self.colors.get(anim['value'], (205, 193, 180))
                pygame.draw.rect(anim_surface, (*color, anim['alpha']), (0, 0, scaled_size, scaled_size), border_radius=8)
                
                # 绘制数字
                if anim['value'] < 100:
                    font = self.font_large
                elif anim['value'] < 1000:
                    font = self.font_medium
                else:
                    font = self.font_small
                
                if anim['value'] <= 4:
                    text_color = (119, 110, 101, anim['alpha'])
                else:
                    text_color = (249, 246, 242, anim['alpha'])
                
                text = font.render(str(anim['value']), True, text_color)
                text_rect = text.get_rect(center=(scaled_size//2, scaled_size//2))
                anim_surface.blit(text, text_rect)
                
                self.surface.blit(anim_surface, (x + offset, y + offset))
            else:
                self.merge_animations.remove(anim)
    
    def draw_ui(self):
        """绘制优化的用户界面"""
        # 游戏标题 - 更现代的设计
        title_bg_rect = pygame.Rect(WINDOW_WIDTH // 2 - 120, 30, 240, 80)
        
        # 标题阴影
        shadow_rect = pygame.Rect(title_bg_rect.x + 5, title_bg_rect.y + 5, title_bg_rect.width, title_bg_rect.height)
        shadow_surface = pygame.Surface((title_bg_rect.width, title_bg_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(shadow_surface, (0, 0, 0, 40), (0, 0, title_bg_rect.width, title_bg_rect.height), border_radius=20)
        self.surface.blit(shadow_surface, shadow_rect)
        
        # 标题背景
        pygame.draw.rect(self.surface, (255, 255, 255, 220), title_bg_rect, border_radius=20)
        pygame.draw.rect(self.surface, (119, 110, 101), title_bg_rect, 3, border_radius=20)
        
        # 标题高光
        highlight_rect = pygame.Rect(title_bg_rect.x + 2, title_bg_rect.y + 2, title_bg_rect.width - 4, title_bg_rect.height // 3)
        highlight_surface = pygame.Surface((highlight_rect.width, highlight_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(highlight_surface, (255, 255, 255, 50), (0, 0, highlight_rect.width, highlight_rect.height), border_radius=18)
        self.surface.blit(highlight_surface, highlight_rect)
        
        # 标题文字阴影
        title_shadow = self.font_large.render("2048", True, (0, 0, 0, 60))
        title_shadow_rect = title_shadow.get_rect(center=(WINDOW_WIDTH // 2 + 2, 72))
        self.surface.blit(title_shadow, title_shadow_rect)
        
        title_text = self.font_large.render("2048", True, (119, 110, 101))
        title_rect = title_text.get_rect(center=(WINDOW_WIDTH // 2, 70))
        self.surface.blit(title_text, title_rect)
        
        # 分数面板 - 更美观的设计
        score_panel_x = WINDOW_WIDTH // 2 - 250
        score_panel_y = 130
        score_panel_width = 150
        score_panel_height = 60
        
        # 当前分数
        score_rect = pygame.Rect(score_panel_x, score_panel_y, score_panel_width, score_panel_height)
        
        # 分数面板阴影
        score_shadow_rect = pygame.Rect(score_rect.x + 3, score_rect.y + 3, score_rect.width, score_rect.height)
        score_shadow_surface = pygame.Surface((score_rect.width, score_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(score_shadow_surface, (0, 0, 0, 30), (0, 0, score_rect.width, score_rect.height), border_radius=15)
        self.surface.blit(score_shadow_surface, score_shadow_rect)
        
        # 分数面板背景
        pygame.draw.rect(self.surface, (255, 255, 255, 220), score_rect, border_radius=15)
        pygame.draw.rect(self.surface, (119, 110, 101), score_rect, 2, border_radius=15)
        
        # 分数面板高光
        score_highlight_rect = pygame.Rect(score_rect.x + 1, score_rect.y + 1, score_rect.width - 2, score_rect.height // 3)
        score_highlight_surface = pygame.Surface((score_highlight_rect.width, score_highlight_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(score_highlight_surface, (255, 255, 255, 40), (0, 0, score_highlight_rect.width, score_highlight_rect.height), border_radius=13)
        self.surface.blit(score_highlight_surface, score_highlight_rect)
        
        score_label = self.font_tiny.render("分数", True, (119, 110, 101))
        score_label_rect = score_label.get_rect(center=(score_panel_x + score_panel_width // 2, score_panel_y + 12))
        self.surface.blit(score_label, score_label_rect)
        
        score_value = self.font_medium.render(str(self.score), True, (119, 110, 101))
        score_value_rect = score_value.get_rect(center=(score_panel_x + score_panel_width // 2, score_panel_y + 35))
        self.surface.blit(score_value, score_value_rect)
        
        # 最高分数
        best_score_rect = pygame.Rect(score_panel_x + score_panel_width + 15, score_panel_y, score_panel_width, score_panel_height)
        
        # 最高分面板阴影
        best_shadow_rect = pygame.Rect(best_score_rect.x + 3, best_score_rect.y + 3, best_score_rect.width, best_score_rect.height)
        best_shadow_surface = pygame.Surface((best_score_rect.width, best_score_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(best_shadow_surface, (0, 0, 0, 30), (0, 0, best_score_rect.width, best_score_rect.height), border_radius=15)
        self.surface.blit(best_shadow_surface, best_shadow_rect)
        
        # 最高分面板背景
        pygame.draw.rect(self.surface, (255, 255, 255, 220), best_score_rect, border_radius=15)
        pygame.draw.rect(self.surface, (119, 110, 101), best_score_rect, 2, border_radius=15)
        
        # 最高分面板高光
        best_highlight_rect = pygame.Rect(best_score_rect.x + 1, best_score_rect.y + 1, best_score_rect.width - 2, best_score_rect.height // 3)
        best_highlight_surface = pygame.Surface((best_highlight_rect.width, best_highlight_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(best_highlight_surface, (255, 255, 255, 40), (0, 0, best_highlight_rect.width, best_highlight_rect.height), border_radius=13)
        self.surface.blit(best_highlight_surface, best_highlight_rect)
        
        best_score_label = self.font_tiny.render("最高分", True, (119, 110, 101))
        best_score_label_rect = best_score_label.get_rect(center=(best_score_rect.centerx, best_score_rect.centery - 12))
        self.surface.blit(best_score_label, best_score_label_rect)
        
        best_score_value = self.font_medium.render(str(self.best_score), True, (119, 110, 101))
        best_score_value_rect = best_score_value.get_rect(center=(best_score_rect.centerx, best_score_rect.centery + 8))
        self.surface.blit(best_score_value, best_score_value_rect)
        
        # 移动次数
        moves_rect = pygame.Rect(score_panel_x + (score_panel_width + 15) * 2, score_panel_y, score_panel_width, score_panel_height)
        
        # 移动次数面板阴影
        moves_shadow_rect = pygame.Rect(moves_rect.x + 3, moves_rect.y + 3, moves_rect.width, moves_rect.height)
        moves_shadow_surface = pygame.Surface((moves_rect.width, moves_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(moves_shadow_surface, (0, 0, 0, 30), (0, 0, moves_rect.width, moves_rect.height), border_radius=15)
        self.surface.blit(moves_shadow_surface, moves_shadow_rect)
        
        # 移动次数面板背景
        pygame.draw.rect(self.surface, (255, 255, 255, 220), moves_rect, border_radius=15)
        pygame.draw.rect(self.surface, (119, 110, 101), moves_rect, 2, border_radius=15)
        
        # 移动次数面板高光
        moves_highlight_rect = pygame.Rect(moves_rect.x + 1, moves_rect.y + 1, moves_rect.width - 2, moves_rect.height // 3)
        moves_highlight_surface = pygame.Surface((moves_highlight_rect.width, moves_highlight_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(moves_highlight_surface, (255, 255, 255, 40), (0, 0, moves_highlight_rect.width, moves_highlight_rect.height), border_radius=13)
        self.surface.blit(moves_highlight_surface, moves_highlight_rect)
        
        moves_label = self.font_tiny.render("移动", True, (119, 110, 101))
        moves_label_rect = moves_label.get_rect(center=(moves_rect.centerx, moves_rect.centery - 12))
        self.surface.blit(moves_label, moves_label_rect)
        
        moves_value = self.font_medium.render(str(self.moves), True, (119, 110, 101))
        moves_value_rect = moves_value.get_rect(center=(moves_rect.centerx, moves_rect.centery + 8))
        self.surface.blit(moves_value, moves_value_rect)
        
        # 返回按钮 - 放在右下角
        back_button_rect = pygame.Rect(WINDOW_WIDTH - 150, WINDOW_HEIGHT - 80, 120, 50)
        
        # 返回按钮阴影
        back_shadow_rect = pygame.Rect(back_button_rect.x + 3, back_button_rect.y + 3, back_button_rect.width, back_button_rect.height)
        back_shadow_surface = pygame.Surface((back_button_rect.width, back_button_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(back_shadow_surface, (0, 0, 0, 30), (0, 0, back_button_rect.width, back_button_rect.height), border_radius=10)
        self.surface.blit(back_shadow_surface, back_shadow_rect)
        
        # 返回按钮背景
        pygame.draw.rect(self.surface, (255, 255, 255, 220), back_button_rect, border_radius=10)
        pygame.draw.rect(self.surface, (119, 110, 101), back_button_rect, 2, border_radius=10)
        
        # 返回按钮高光
        back_highlight_rect = pygame.Rect(back_button_rect.x + 1, back_button_rect.y + 1, back_button_rect.width - 2, back_button_rect.height // 3)
        back_highlight_surface = pygame.Surface((back_highlight_rect.width, back_highlight_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(back_highlight_surface, (255, 255, 255, 40), (0, 0, back_highlight_rect.width, back_highlight_rect.height), border_radius=8)
        self.surface.blit(back_highlight_surface, back_highlight_rect)
        
        back_text = self.font_small.render("返回", True, (119, 110, 101))
        back_rect = back_text.get_rect(center=(back_button_rect.centerx, back_button_rect.centery))
        self.surface.blit(back_text, back_rect)
    
    def draw_win_screen(self):
        """绘制优化的获胜界面"""
        # 半透明遮罩
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((255, 255, 255, 180))
        self.surface.blit(overlay, (0, 0))
        
        # 获胜面板 - 更现代的设计
        win_panel = pygame.Rect(WINDOW_WIDTH // 2 - 200, WINDOW_HEIGHT // 2 - 150, 400, 300)
        
        # 面板阴影
        shadow_surface = pygame.Surface((400, 300), pygame.SRCALPHA)
        pygame.draw.rect(shadow_surface, (0, 0, 0, 50), (0, 0, 400, 300), border_radius=20)
        self.surface.blit(shadow_surface, (win_panel.x + 8, win_panel.y + 8))
        
        # 面板背景
        pygame.draw.rect(self.surface, (237, 194, 46), win_panel, border_radius=20)
        pygame.draw.rect(self.surface, (255, 255, 255), win_panel, 3, border_radius=20)
        
        # 胜利图标
        icon_rect = pygame.Rect(win_panel.centerx - 30, win_panel.y + 25, 60, 60)
        pygame.draw.circle(self.surface, (255, 255, 255), icon_rect.center, 30)
        pygame.draw.circle(self.surface, (237, 194, 46), icon_rect.center, 25)
        
        # 绘制胜利标志
        pygame.draw.polygon(self.surface, (255, 255, 255), 
                          [(win_panel.centerx - 10, win_panel.y + 35), 
                           (win_panel.centerx - 3, win_panel.y + 42),
                           (win_panel.centerx + 12, win_panel.y + 28)], 0)
        
        win_text = self.font_large.render("恭喜获胜！", True, (255, 255, 255))
        win_rect = win_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 30))
        self.surface.blit(win_text, win_rect)
        
        continue_text = self.font_medium.render("按C继续游戏", True, (255, 255, 255))
        continue_rect = continue_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 15))
        self.surface.blit(continue_text, continue_rect)
        
        restart_text = self.font_medium.render("按R重新开始", True, (255, 255, 255))
        restart_rect = restart_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 50))
        self.surface.blit(restart_text, restart_rect)
        
        exit_text = self.font_medium.render("按ESC退出", True, (255, 255, 255))
        exit_rect = exit_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 85))
        self.surface.blit(exit_text, exit_rect)
    
    def draw_game_over_screen(self):
        """绘制优化的游戏结束界面"""
        # 半透明遮罩
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.surface.blit(overlay, (0, 0))
        
        # 游戏结束面板 - 更现代的设计
        game_over_panel = pygame.Rect(WINDOW_WIDTH // 2 - 200, WINDOW_HEIGHT // 2 - 150, 400, 300)
        
        # 面板阴影
        shadow_surface = pygame.Surface((400, 300), pygame.SRCALPHA)
        pygame.draw.rect(shadow_surface, (0, 0, 0, 50), (0, 0, 400, 300), border_radius=20)
        self.surface.blit(shadow_surface, (game_over_panel.x + 8, game_over_panel.y + 8))
        
        # 面板背景
        pygame.draw.rect(self.surface, (119, 110, 101), game_over_panel, border_radius=20)
        pygame.draw.rect(self.surface, (255, 255, 255), game_over_panel, 3, border_radius=20)
        
        # 游戏结束图标
        icon_rect = pygame.Rect(game_over_panel.centerx - 30, game_over_panel.y + 25, 60, 60)
        pygame.draw.circle(self.surface, (255, 255, 255), icon_rect.center, 30)
        pygame.draw.circle(self.surface, (119, 110, 101), icon_rect.center, 25)
        
        # 绘制X标志
        pygame.draw.line(self.surface, (255, 255, 255), 
                        (icon_rect.centerx - 15, icon_rect.centery - 15),
                        (icon_rect.centerx + 15, icon_rect.centery + 15), 3)
        pygame.draw.line(self.surface, (255, 255, 255), 
                        (icon_rect.centerx + 15, icon_rect.centery - 15),
                        (icon_rect.centerx - 15, icon_rect.centery + 15), 3)
        
        game_over_text = self.font_large.render("游戏结束", True, (255, 255, 255))
        game_over_rect = game_over_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 30))
        self.surface.blit(game_over_text, game_over_rect)
        
        final_score_text = self.font_medium.render(f"最终分数: {self.score}", True, (255, 255, 255))
        final_score_rect = final_score_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 15))
        self.surface.blit(final_score_text, final_score_rect)
        
        restart_text = self.font_medium.render("按R重新开始", True, (255, 255, 255))
        restart_rect = restart_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 50))
        self.surface.blit(restart_text, restart_rect)
        
        exit_text = self.font_medium.render("按ESC退出", True, (255, 255, 255))
        exit_rect = exit_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 85))
        self.surface.blit(exit_text, exit_rect)
    
    def draw(self):
        """绘制游戏"""
        # 绘制背景
        self.draw_background()
        
        # 绘制UI
        self.draw_ui()
        
        # 绘制游戏网格
        self.draw_grid()
        
        # 绘制获胜界面
        if self.game_state == "win":
            self.draw_win_screen()
        
        # 绘制游戏结束界面
        elif self.game_state == "game_over":
            self.draw_game_over_screen() 