import pygame
import time
import math
import random
from game.constants import WINDOW_WIDTH, WINDOW_HEIGHT, FONT_NAME

class SplashScreen:
    def __init__(self, screen):
        self.screen = screen
        self.font_large = pygame.font.Font(FONT_NAME, 72)
        self.font_medium = pygame.font.Font(FONT_NAME, 28)
        self.font_small = pygame.font.Font(FONT_NAME, 18)
        self.clock = pygame.time.Clock()
        self.start_time = time.time()
        self.duration = 3.5  # 延长启动画面持续时间
        
        # 加载蛇图像
        try:
            self.snake_head = pygame.image.load("snake_images/dragonking_head.png").convert_alpha()
            self.snake_body = pygame.image.load("snake_images/dragonking_body.png").convert_alpha()
            self.snake_head = pygame.transform.scale(self.snake_head, (100, 100))
            self.snake_body = pygame.transform.scale(self.snake_body, (80, 80))
            
            # 加载更多蛇皮肤图像用于展示
            self.skin_images = []
            skin_types = ["xiyangyang", "lanyangyang", "meiyangyang", "dragon", "cat", "robot", "space"]
            for skin in skin_types:
                try:
                    head = pygame.image.load(f"snake_images/{skin}_head.png").convert_alpha()
                    head = pygame.transform.scale(head, (60, 60))
                    self.skin_images.append(head)
                except:
                    pass
        except:
            self.snake_head = None
            self.snake_body = None
            self.skin_images = []
            
        # 创建粒子效果
        self.particles = []
        for _ in range(150):  # 增加粒子数量
            self.particles.append({
                'x': random.randint(0, WINDOW_WIDTH),
                'y': random.randint(0, WINDOW_HEIGHT),
                'size': random.randint(2, 8),
                'speed': random.uniform(0.5, 3.0),
                'color': random.choice([
                    (255, 255, 255, 100),  # 白色
                    (100, 200, 255, 80),   # 蓝色
                    (255, 200, 100, 80),   # 金色
                    (200, 100, 255, 80),   # 紫色
                    (100, 255, 150, 80),   # 绿色
                    (255, 100, 100, 80),   # 红色
                ])
            })
            
        # 创建食物图标
        self.foods = []
        for _ in range(15):
            self.foods.append({
                'x': random.randint(0, WINDOW_WIDTH),
                'y': random.randint(0, WINDOW_HEIGHT),
                'size': random.randint(8, 16),
                'color': random.choice([
                    (255, 0, 0),      # 红色苹果
                    (255, 255, 0),    # 黄色香蕉
                    (255, 165, 0),    # 橙色橘子
                    (0, 255, 0),      # 绿色梨
                    (128, 0, 128),    # 紫色葡萄
                ]),
                'speed': random.uniform(0.2, 1.0),
                'angle': random.uniform(0, 2 * math.pi)
            })
            
        # 创建闪电效果
        self.lightnings = []
        
        # 创建星星效果
        self.stars = []
        for _ in range(20):
            self.stars.append({
                'x': random.randint(0, WINDOW_WIDTH),
                'y': random.randint(0, WINDOW_HEIGHT // 2),  # 主要在上半部分
                'size': random.randint(15, 30),
                'angle': random.uniform(0, 2 * math.pi),
                'speed': random.uniform(0.01, 0.05)
            })
            
        # 创建云朵效果
        self.clouds = []
        for _ in range(6):
            self.clouds.append({
                'x': random.randint(-100, WINDOW_WIDTH + 100),
                'y': random.randint(50, 200),
                'width': random.randint(100, 200),
                'height': random.randint(40, 80),
                'speed': random.uniform(0.2, 0.8),
                'alpha': random.randint(30, 80)
            })
            
    def draw_star(self, x, y, size, angle):
        # 绘制五角星
        points = []
        for i in range(10):
            # 确定半径 (内圈和外圈交替)
            radius = size if i % 2 == 0 else size * 0.4
            # 计算角度
            a = angle + math.pi * 2 * i / 10
            # 计算点坐标
            points.append((x + radius * math.cos(a), y + radius * math.sin(a)))
        
        # 绘制五角星
        pygame.draw.polygon(self.screen, (255, 255, 100), points)
        
    def create_lightning(self):
        # 随机决定是否创建新闪电
        if random.random() < 0.02:  # 2%的概率每帧创建闪电
            start_x = random.randint(0, WINDOW_WIDTH)
            start_y = 0
            segments = []
            x, y = start_x, start_y
            
            # 创建闪电路径
            for _ in range(10):
                next_x = x + random.randint(-50, 50)
                next_y = y + random.randint(20, 50)
                segments.append((x, y, next_x, next_y))
                x, y = next_x, next_y
                if y > WINDOW_HEIGHT:
                    break
                    
            self.lightnings.append({
                'segments': segments,
                'life': 5,  # 闪电持续5帧
                'width': random.randint(2, 4),
                'color': (200, 230, 255)
            })
            
    def draw_cloud(self, x, y, width, height, alpha):
        # 创建透明表面
        cloud_surface = pygame.Surface((width, height), pygame.SRCALPHA)
        
        # 绘制云朵（多个重叠的圆形）
        radius = height // 2
        pygame.draw.circle(cloud_surface, (255, 255, 255, alpha), (radius, height // 2), radius)
        pygame.draw.circle(cloud_surface, (255, 255, 255, alpha), (width - radius, height // 2), radius)
        pygame.draw.circle(cloud_surface, (255, 255, 255, alpha), (width // 3, height // 2 - 10), radius + 5)
        pygame.draw.circle(cloud_surface, (255, 255, 255, alpha), (width * 2 // 3, height // 2 - 5), radius + 3)
        
        # 绘制云朵底部
        pygame.draw.rect(cloud_surface, (255, 255, 255, alpha), 
                        (radius, height // 2, width - radius * 2, radius))
        
        # 将云朵绘制到屏幕上
        self.screen.blit(cloud_surface, (x, y))
            
    def draw(self):
        # 计算当前动画进度 (0.0 到 1.0)
        elapsed = time.time() - self.start_time
        progress = min(elapsed / self.duration, 1.0)
        
        # 绘制动态渐变背景
        for y in range(0, WINDOW_HEIGHT, 2):  # 优化性能，每2像素绘制一次
            ratio = y / WINDOW_HEIGHT
            # 使用更丰富的颜色渐变
            r = int(20 + (60 - 20) * ratio + 10 * math.sin(elapsed + ratio * 5))
            g = int(30 + (50 - 30) * ratio)
            b = int(80 + (120 - 80) * ratio + 10 * math.cos(elapsed * 0.5 + ratio * 3))
            
            pygame.draw.line(self.screen, (r, g, b), (0, y), (WINDOW_WIDTH, y), 2)
            
        # 绘制云朵
        for cloud in self.clouds:
            self.draw_cloud(cloud['x'], cloud['y'], cloud['width'], cloud['height'], cloud['alpha'])
            # 移动云朵
            cloud['x'] += cloud['speed']
            # 如果云朵移出屏幕，从另一侧重新进入
            if cloud['x'] > WINDOW_WIDTH + 100:
                cloud['x'] = -cloud['width']
                cloud['y'] = random.randint(50, 200)
        
        # 创建闪电
        self.create_lightning()
        
        # 绘制闪电
        for lightning in self.lightnings[:]:
            for segment in lightning['segments']:
                pygame.draw.line(self.screen, lightning['color'], 
                               (segment[0], segment[1]), (segment[2], segment[3]), 
                               lightning['width'])
            
            # 闪电周围的光晕
            for segment in lightning['segments']:
                mid_x = (segment[0] + segment[2]) // 2
                mid_y = (segment[1] + segment[3]) // 2
                glow_radius = lightning['width'] * 3
                glow_surf = pygame.Surface((glow_radius*2, glow_radius*2), pygame.SRCALPHA)
                pygame.draw.circle(glow_surf, (200, 230, 255, 50), (glow_radius, glow_radius), glow_radius)
                self.screen.blit(glow_surf, (mid_x - glow_radius, mid_y - glow_radius))
            
            lightning['life'] -= 1
            if lightning['life'] <= 0:
                self.lightnings.remove(lightning)
        
        # 绘制星星
        for star in self.stars:
            self.draw_star(star['x'], star['y'], star['size'], star['angle'] + elapsed)
            # 旋转星星
            star['angle'] += star['speed']
        
        # 绘制粒子效果
        for particle in self.particles:
            # 更新粒子位置
            particle['y'] -= particle['speed']
            if particle['y'] < 0:
                particle['y'] = WINDOW_HEIGHT
                particle['x'] = random.randint(0, WINDOW_WIDTH)
            
            # 绘制粒子
            size = particle['size'] + math.sin(elapsed * 2 + particle['x']) * 1.5
            if size > 0:
                color = list(particle['color'])
                # 调整透明度以产生闪烁效果
                color[3] = int(color[3] * (0.7 + 0.3 * math.sin(elapsed * 3 + particle['y'] * 0.01)))
                
                s = pygame.Surface((size*2, size*2), pygame.SRCALPHA)
                pygame.draw.circle(s, color, (size, size), size)
                self.screen.blit(s, (particle['x'] - size, particle['y'] - size))
        
        # 绘制食物图标
        for food in self.foods:
            # 更新食物位置（轻微浮动）
            food['x'] += math.sin(elapsed * 2 + food['y'] * 0.01) * 0.5
            food['y'] += math.cos(elapsed * 2 + food['x'] * 0.01) * 0.5
            
            # 绘制食物（圆形）
            pygame.draw.circle(self.screen, food['color'], (int(food['x']), int(food['y'])), food['size'])
            # 添加高光
            highlight_size = food['size'] // 3
            pygame.draw.circle(self.screen, (255, 255, 255, 150), 
                             (int(food['x'] - food['size']//3), int(food['y'] - food['size']//3)), 
                             highlight_size)
        
        # 绘制光晕效果
        glow_radius = 300 + 50 * math.sin(elapsed * 2)
        for radius in range(int(glow_radius), int(glow_radius - 100), -5):
            alpha = int(10 - (glow_radius - radius) / 10)
            if alpha > 0:
                s = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
                pygame.draw.circle(s, (100, 150, 255, alpha), (radius, radius), radius)
                self.screen.blit(s, (WINDOW_WIDTH//2 - radius, WINDOW_HEIGHT//2 - radius))
        
        # 绘制标题
        if progress > 0.1:
            # 计算标题动画效果
            title_scale = 1.0 + 0.05 * math.sin(elapsed * 3)
            title_y_offset = 5 * math.sin(elapsed * 2)
            
            alpha = min(255, int((progress - 0.1) * 255 / 0.3))
            title_text = "贪吃蛇大冒险"
            
            # 绘制发光效果
            for i in range(5, 0, -1):
                glow_surface = self.font_large.render(title_text, True, (100, 150, 255))
                glow_surface.set_alpha(alpha // (i*2))
                glow_size = int(72 * title_scale) + i*2
                glow_font = pygame.font.Font(FONT_NAME, glow_size)
                glow_surface = glow_font.render(title_text, True, (100, 150, 255))
                glow_surface.set_alpha(alpha // (i*2))
                glow_rect = glow_surface.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//2 - 120 + title_y_offset))
                self.screen.blit(glow_surface, glow_rect)
            
            # 绘制主标题
            title_font = pygame.font.Font(FONT_NAME, int(72 * title_scale))
            title_surface = title_font.render(title_text, True, (255, 255, 255))
            title_surface.set_alpha(alpha)
            title_rect = title_surface.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//2 - 120 + title_y_offset))
            self.screen.blit(title_surface, title_rect)
            
            # 绘制标题阴影
            shadow_surface = title_font.render(title_text, True, (0, 0, 0))
            shadow_surface.set_alpha(alpha // 3)
            shadow_rect = shadow_surface.get_rect(center=(WINDOW_WIDTH//2 + 4, WINDOW_HEIGHT//2 - 116 + title_y_offset))
            self.screen.blit(shadow_surface, shadow_rect)
            
            # 绘制副标题
            if progress > 0.2:
                subtitle_alpha = min(255, int((progress - 0.2) * 255 / 0.3))
                subtitle_text = "多种游戏模式 · 丰富皮肤 · 精彩挑战"
                subtitle_font = pygame.font.Font(FONT_NAME, 24)
                subtitle_surface = subtitle_font.render(subtitle_text, True, (220, 220, 255))
                subtitle_surface.set_alpha(subtitle_alpha)
                subtitle_rect = subtitle_surface.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//2 - 60 + title_y_offset))
                self.screen.blit(subtitle_surface, subtitle_rect)
        
        # 绘制蛇动画
        if progress > 0.3:
            alpha = min(255, int((progress - 0.3) * 255 / 0.3))
            
            # 创建蛇身体动画
            if self.snake_body:
                for i in range(5):
                    body_alpha = alpha - i * 20
                    if body_alpha > 0:
                        body_copy = self.snake_body.copy()
                        body_copy.set_alpha(body_alpha)
                        
                        # 计算蛇身体的位置（波浪运动）
                        offset_x = math.sin(elapsed * 3 + i * 0.5) * 15
                        offset_y = math.cos(elapsed * 2 + i * 0.5) * 10
                        
                        body_rect = body_copy.get_rect(center=(
                            WINDOW_WIDTH//2 - 60 - i * 40 + offset_x, 
                            WINDOW_HEIGHT//2 + 30 + offset_y
                        ))
                        self.screen.blit(body_copy, body_rect)
            
            # 绘制蛇头动画
            if self.snake_head:
                head_copy = self.snake_head.copy()
                head_copy.set_alpha(alpha)
                
                # 添加更复杂的动画效果
                scale = 1.0 + 0.1 * math.sin(elapsed * 3)
                rotation = math.sin(elapsed * 2) * 15  # 头部轻微摆动
                
                snake_scaled = pygame.transform.scale(head_copy, 
                                                    (int(100 * scale), int(100 * scale)))
                snake_rotated = pygame.transform.rotate(snake_scaled, rotation)
                
                snake_rect = snake_rotated.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//2 + 30))
                self.screen.blit(snake_rotated, snake_rect)
                
            # 绘制皮肤展示
            if progress > 0.5 and self.skin_images:
                skin_alpha = min(255, int((progress - 0.5) * 255 / 0.3))
                
                # 计算皮肤图标的排列位置
                num_skins = len(self.skin_images)
                radius = 180  # 环形排列的半径
                center_x, center_y = WINDOW_WIDTH//2, WINDOW_HEIGHT//2 + 30
                
                for i, skin in enumerate(self.skin_images):
                    # 计算环形位置
                    angle = 2 * math.pi * i / num_skins + elapsed * 0.5  # 旋转效果
                    x = center_x + radius * math.cos(angle)
                    y = center_y + radius * math.sin(angle)
                    
                    # 添加缩放效果
                    scale = 0.8 + 0.2 * math.sin(elapsed * 2 + i)
                    skin_scaled = pygame.transform.scale(skin, 
                                                      (int(60 * scale), int(60 * scale)))
                    
                    # 设置透明度
                    skin_scaled.set_alpha(skin_alpha)
                    
                    # 绘制皮肤图标
                    skin_rect = skin_scaled.get_rect(center=(x, y))
                    self.screen.blit(skin_scaled, skin_rect)
                    
                    # 添加连接线
                    line_alpha = skin_alpha // 3
                    pygame.draw.line(self.screen, (200, 200, 255, line_alpha), 
                                   (center_x, center_y), (x, y), 2)
        
        # 绘制高级进度条
        if progress < 0.9:
            bar_width = 400
            bar_height = 12
            bar_x = (WINDOW_WIDTH - bar_width) // 2
            bar_y = WINDOW_HEIGHT - 100
            
            # 进度条外框
            pygame.draw.rect(self.screen, (30, 30, 40), 
                           (bar_x-4, bar_y-4, bar_width+8, bar_height+8), border_radius=8)
            pygame.draw.rect(self.screen, (80, 80, 100), 
                           (bar_x-4, bar_y-4, bar_width+8, bar_height+8), 2, border_radius=8)
            
            # 进度条背景
            pygame.draw.rect(self.screen, (40, 40, 60), 
                           (bar_x, bar_y, bar_width, bar_height), border_radius=6)
            
            # 进度条填充（渐变效果）
            fill_width = int(bar_width * min(progress / 0.9, 1.0))
            if fill_width > 0:
                for i in range(fill_width):
                    ratio = i / bar_width
                    color_r = int(100 + 155 * ratio)
                    color_g = int(200 - 50 * ratio)
                    color_b = int(255 - 155 * ratio)
                    pygame.draw.line(self.screen, (color_r, color_g, color_b), 
                                   (bar_x + i, bar_y), (bar_x + i, bar_y + bar_height))
                
                # 进度条光晕
                glow_surf = pygame.Surface((20, bar_height), pygame.SRCALPHA)
                for i in range(10):
                    alpha = 150 - i * 15
                    if alpha > 0:
                        pygame.draw.rect(glow_surf, (255, 255, 255, alpha), 
                                       (i, 0, 1, bar_height))
                
                glow_pos = bar_x + fill_width - 10
                if glow_pos < bar_x + bar_width - 10:
                    self.screen.blit(glow_surf, (glow_pos, bar_y))
                    
            # 添加进度百分比显示
            percent = int(min(progress / 0.9, 1.0) * 100)
            percent_text = f"{percent}%"
            percent_font = pygame.font.Font(FONT_NAME, 16)
            percent_surface = percent_font.render(percent_text, True, (220, 220, 240))
            percent_rect = percent_surface.get_rect(midright=(bar_x + bar_width + 30, bar_y + bar_height//2))
            self.screen.blit(percent_surface, percent_rect)
        
        # 绘制加载文本和提示
        if progress < 0.9:
            # 加载文本
            loading_text = "游戏加载中..."
            loading_surface = self.font_medium.render(loading_text, True, (220, 220, 240))
            loading_rect = loading_surface.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT - 70))
            self.screen.blit(loading_surface, loading_rect)
            
            # 随机提示文本
            if hasattr(self, 'tip_timer') and hasattr(self, 'current_tip'):
                self.tip_timer -= 1
                if self.tip_timer <= 0:
                    self.update_tip()
            else:
                self.tip_timer = 120  # 约2秒更换一次提示
                self.update_tip()
                
            # 显示提示文本
            tip_alpha = 180 + 75 * math.sin(elapsed * 2)  # 闪烁效果
            tip_surface = self.font_small.render(self.current_tip, True, (180, 220, 255))
            tip_surface.set_alpha(int(tip_alpha))
            tip_rect = tip_surface.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT - 40))
            self.screen.blit(tip_surface, tip_rect)
        else:
            # 显示"按任意键继续"，带有脉动效果
            continue_text = "按任意键继续"
            pulse = 0.7 + 0.3 * math.sin(elapsed * 5)
            continue_font = pygame.font.Font(FONT_NAME, int(28 * pulse))
            continue_surface = continue_font.render(continue_text, True, (255, 255, 255))
            continue_rect = continue_surface.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT - 70))
            
            # 添加发光效果
            for i in range(3, 0, -1):
                glow = pygame.font.Font(FONT_NAME, int(28 * pulse) + i*2)
                glow_surface = glow.render(continue_text, True, (100, 150, 255))
                glow_surface.set_alpha(100 - i*30)
                glow_rect = glow_surface.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT - 70))
                self.screen.blit(glow_surface, glow_rect)
                
            self.screen.blit(continue_surface, continue_rect)
        
        # 版权信息
        if progress > 0.6:
            alpha = min(255, int((progress - 0.6) * 255 / 0.3))
            copyright_text = "© 2024 贪吃蛇大冒险团队"
            copyright_surface = self.font_small.render(copyright_text, True, (200, 200, 220))
            copyright_surface.set_alpha(alpha)
            copyright_rect = copyright_surface.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT - 30))
            self.screen.blit(copyright_surface, copyright_rect)
            
    def update_tip(self):
        # 游戏提示文本列表
        tips = [
            "提示: 按空格键可以暂停游戏",
            "提示: 收集特殊食物可以获得额外积分",
            "提示: 尝试不同的蛇皮肤，体验不同的游戏风格",
            "提示: 挑战高难度模式，提升你的反应能力",
            "提示: 双人模式可以和朋友一起游戏",
            "提示: 完成成就可以解锁特殊奖励",
            "提示: 定期查看商店，获取最新皮肤",
            "提示: 使用键盘方向键或WASD控制蛇的移动",
            "提示: 游戏中按M键可以静音背景音乐",
            "提示: 尝试突破自己的最高分记录"
        ]
        self.current_tip = random.choice(tips)
        self.tip_timer = 120  # 重置计时器
    
    def run(self):
        """运行启动画面，直到结束或用户按键"""
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return False
                elif event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                    # 如果加载进度超过90%，允许用户跳过
                    elapsed = time.time() - self.start_time
                    if elapsed / self.duration > 0.9:
                        return True
            
            # 清屏并绘制
            self.screen.fill((0, 0, 0))
            self.draw()
            pygame.display.flip()
            self.clock.tick(60)
            
            # 检查是否完成
            if time.time() - self.start_time > self.duration:
                # 等待用户按键
                waiting = True
                while waiting:
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            return False
                        elif event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                            waiting = False
                            return True
                    
                    # 继续绘制，但保持"按任意键继续"的闪烁效果
                    self.screen.fill((0, 0, 0))
                    self.draw()
                    pygame.display.flip()
                    self.clock.tick(60)
        
        return True