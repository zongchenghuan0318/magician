# -*- coding: utf-8 -*-
import pygame
import os
import random
import math
import sys
import json
import subprocess
import time # Added for time.time()

# 导入常量和模块
from .constants import get_resource_path, SNOW_PARTICLE_COUNT, WINDOW_WIDTH, WINDOW_HEIGHT, SNOW_PARTICLE_SPEED, SNOW_PARTICLE_SIZE, BACKGROUND_SWITCH_BUTTON_SIZE, BUTTON_WIDTH, BUTTON_HEIGHT, BUTTON_COLOR, BUTTON_HOVER_COLOR, BUTTON_TEXT_COLOR, FONT_NAME, WHITE, TITLE_FLOAT_SPEED, TITLE_FLOAT_AMPLITUDE, TITLE_FONT_SIZE, BACKGROUND_COLOR, SETTINGS_MENU_WIDTH, SETTINGS_MENU_HEIGHT, GOLD, MENU_BACKGROUND_ALPHA, FONT_SIZE
from .shop import ShopMenu
from .backpack import BackpackMenu
from .player import player_data
from .ui_elements import Button, CircularButton, draw_rounded_rect, CartoonButton
from .activity_page import ActivityPage

HELP_TEXT = [
    "游戏控制:",
    "  - 使用方向键或 WASD 移动",
    "  - 空格键暂停/继续游戏",
    "  - ESC 键返回主菜单",
    "",
    "游戏玩法:",
    "  - 吃食物增加分数和长度",
    "  - 避免撞到自己或障碍物",
    "  - 穿墙模式下可以从一边穿到另一边",
    "",
    "祝你游戏愉快!",
]

def load_help_text():
    try:
        help_path = get_resource_path('help.md')
        with open(help_path, 'r', encoding='utf-8') as f:
            # 简单处理，去除Markdown标题标记，但保留一些格式用于渲染
            lines = []
            for line in f.readlines():
                stripped_line = line.strip()
                if stripped_line:
                    lines.append(stripped_line)
            return lines
    except FileNotFoundError:
        return ["错误: help.md 文件未找到。"]

class SnowParticle:
    def __init__(self):
        self.x = random.randint(0, WINDOW_WIDTH)
        self.y = random.randint(-50, 0)
        self.speed = random.uniform(0.5, SNOW_PARTICLE_SPEED)
        self.size = random.randint(1, SNOW_PARTICLE_SIZE)

    def update(self):
        self.y += self.speed
        if self.y > WINDOW_HEIGHT:
            self.y = random.randint(-50, 0)
            self.x = random.randint(0, WINDOW_WIDTH)

    def draw(self, surface):
        pygame.draw.circle(surface, WHITE, (int(self.x), int(self.y)), self.size)

class BubbleFragment:
    def __init__(self, x, y, color, shape="circle"):
        self.x = x
        self.y = y
        self.color = color
        self.shape = shape
        self.radius = random.randint(4, 8)
        self.angle = random.uniform(0, 2*math.pi)
        self.speed = random.uniform(2.5, 5.5)  # 初速度略调慢
        self.life = 48  # 总帧数更长
        self.max_life = 90
        self.alpha = 255
        self.scale = 1.0
        self.rotation = random.uniform(0, 360)
        self.rotation_speed = random.uniform(-7, 7)  # 旋转速度略减缓

    def update(self):
        self.x += math.cos(self.angle) * self.speed
        self.y += math.sin(self.angle) * self.speed
        self.speed *= 0.97  # 衰减更慢
        self.life -= 1
        self.alpha = int(255 * (self.life / self.max_life))
        self.scale *= 0.99  # 缩小更慢
        self.rotation += self.rotation_speed

    def draw(self, surface):
        s = pygame.Surface((56, 56), pygame.SRCALPHA)
        cx, cy, r = 28, 28, int(self.radius * self.scale * 1.7)
        color = (*self.color, min(255, int(self.alpha*1.5)))
        shape_type = getattr(self, 'shape_type', self.shape)
        border_color = (255,255,255,min(255, int(self.alpha*0.9)))
        glow_color = (255,255,255,120)
        if shape_type == "circle":
            pygame.draw.circle(s, color, (cx, cy), r)
            pygame.draw.circle(s, border_color, (cx, cy), r, 4)
            pygame.draw.circle(s, glow_color, (cx, cy), r+6, 6)
        elif shape_type == "star":
            points = []
            for i in range(5):
                angle = math.radians(i * 72 - 90)
                x = cx + r * math.cos(angle)
                y = cy + r * math.sin(angle)
                points.append((x, y))
                angle = math.radians(i * 72 + 36 - 90)
                x = cx + r * 0.5 * math.cos(angle)
                y = cy + r * 0.5 * math.sin(angle)
                points.append((x, y))
            pygame.draw.polygon(s, color, points)
            pygame.draw.polygon(s, border_color, points, 4)
            pygame.draw.polygon(s, glow_color, points, 8)
        elif shape_type == "polygon":
            sides = random.randint(5,8)
            points = []
            for i in range(sides):
                angle = math.radians(i * 360 / sides)
                x = cx + r * math.cos(angle)
                y = cy + r * math.sin(angle)
                points.append((x, y))
            pygame.draw.polygon(s, color, points)
            pygame.draw.polygon(s, border_color, points, 4)
            pygame.draw.polygon(s, glow_color, points, 8)
        elif shape_type == "heart":
            heart_points = []
            for t in range(0, 360, 20):
                rad = math.radians(t)
                x = cx + r * 0.8 * math.sin(rad) ** 3
                y = cy - r * (0.6 * math.cos(rad) - 0.3 * math.cos(2*rad) - 0.2 * math.cos(3*rad) - 0.1 * math.cos(4*rad))
                heart_points.append((x, y))
            pygame.draw.polygon(s, color, heart_points)
            pygame.draw.polygon(s, border_color, heart_points, 4)
            pygame.draw.polygon(s, glow_color, heart_points, 8)
        s = pygame.transform.rotate(s, self.rotation)
        surface.blit(s, (self.x-28, self.y-28))

class Bubble:
    COLORS = [
        (180, 220, 255), # 淡蓝
        (220, 180, 255), # 淡紫
        (255, 210, 230), # 淡粉
        (200, 255, 220), # 淡绿
        (255, 245, 180)  # 淡黄
    ]
    def __init__(self, width, height):
        self.r = random.randint(18, 32)
        self.x = random.randint(self.r, width-self.r)
        self.y = height + self.r + random.randint(0, 40)
        self.speed = random.uniform(0.3, 0.8)
        self.alpha = random.randint(60, 110)
        self.color = random.choice(self.COLORS)
        self.popped = False
        self.pop_time = 0
        self.fragments = []  # 爆炸碎片
        self.flash_life = 0
    def update(self):
        if not self.popped:
            self.y -= self.speed
            if self.y < -self.r:
                self.popped = True
        else:
            # 爆炸碎片动画
            if not self.fragments:
                n = random.randint(8, 14)
                shapes = ["circle", "star", "polygon", "heart"]
                bubble_radius = self.r
                for i in range(n):
                    angle = math.radians(i * 360 / n + random.uniform(-10,10))
                    dist = bubble_radius * random.uniform(0.7, 1.1)
                    frag_x = self.x + math.cos(angle) * dist
                    frag_y = self.y + math.sin(angle) * dist
                    shape = random.choice(shapes)
                    frag_color = tuple(min(255, int(c*random.uniform(0.85,1.15))) for c in self.color)
                    frag = BubbleFragment(frag_x, frag_y, frag_color, shape)
                    frag.angle = angle
                    self.fragments.append(frag)
                self.flash_life = 14  # 闪光持续更久
            for frag in self.fragments:
                frag.update()
            self.fragments = [f for f in self.fragments if f.life > 0 and f.alpha > 0 and f.radius * f.scale > 1]
            self.r += 1
            self.alpha -= 16  # 泡泡本体消失慢一点
            if self.alpha <= 0 and not self.fragments and self.flash_life <= 0:
                self.alpha = 0
            if self.flash_life > 0:
                self.flash_life -= 1
    def draw(self, surface):
        if self.alpha > 0 and not self.popped:
            s = pygame.Surface((self.r*2, self.r*2), pygame.SRCALPHA)
            # 主体渐变+动态高光
            for i in range(self.r, 0, -1):
                ratio = i/self.r
                c = tuple(int(self.color[j]*ratio + 255*(1-ratio)) for j in range(3))
                a = int(self.alpha * ratio)
                pygame.draw.circle(s, c+(a,), (self.r, self.r), i)
            # 动态高光
            t = pygame.time.get_ticks()//8 % 360
            highlight_x = int(self.r + self.r*0.4*math.cos(math.radians(t)))
            highlight_y = int(self.r + self.r*0.4*math.sin(math.radians(t)))
            pygame.draw.circle(s, (255,255,255, min(120, self.alpha)), (highlight_x, highlight_y), int(self.r*0.22))
            # 发光边缘
            for glow in range(2, 8):
                pygame.draw.circle(s, (255,255,255,int(self.alpha*0.06)), (self.r, self.r), self.r+glow, 1)
            # 阴影
            pygame.draw.ellipse(s, (120,120,120,40), (int(self.r*0.2), int(self.r*1.3), int(self.r*1.2), int(self.r*0.4)))
            surface.blit(s, (int(self.x-self.r), int(self.y-self.r)))
            # 粒子特效
            if getattr(self, 'has_particle', False):
                for _ in range(2):
                    px = self.x + random.randint(-self.r//2, self.r//2)
                    py = self.y + random.randint(-self.r//2, self.r//2)
                    pygame.draw.circle(surface, (255,255,255,80), (int(px), int(py)), random.randint(1,3))
        # 爆炸中心闪光
        if self.popped and self.flash_life > 0:
            alpha = int(180 * (self.flash_life / 10))
            s = pygame.Surface((60, 60), pygame.SRCALPHA)
            pygame.draw.circle(s, (255, 255, 200, alpha), (30, 30), 30)
            surface.blit(s, (self.x-30, self.y-30))
        # 爆炸碎片
        for frag in self.fragments:
            frag.draw(surface)
    def is_hit(self, mx, my):
        return (self.x-mx)**2 + (self.y-my)**2 <= self.r**2 and not self.popped

class ModeSelectMenu:
    def __init__(self, surface):
        self.surface = surface
        self.buttons = []
        self.setup_buttons()
    def setup_buttons(self):
        btn_width = 220
        btn_height = 64
        gap = 36
        center_x = WINDOW_WIDTH // 2 - btn_width // 2
        center_y = WINDOW_HEIGHT // 2 - btn_height // 2
        single_btn = CartoonButton(center_x, center_y - btn_height//2 - gap//2, btn_width, btn_height, "单人模式", color=(102,204,102), icon_type="smile")
        dual_btn = CartoonButton(center_x, center_y + btn_height//2 + gap//2, btn_width, btn_height, "双人模式", color=(255,213,79), icon_type="group")
        self.buttons = [single_btn, dual_btn]
    def draw(self):
        # 半透明遮罩
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0,0,0,120))
        self.surface.blit(overlay, (0,0))
        # 圆角面板
        panel_rect = pygame.Rect(WINDOW_WIDTH//2-260, WINDOW_HEIGHT//2-120, 520, 240)
        draw_rounded_rect(self.surface, panel_rect, (255,255,255,240), 32)
        # 标题
        font = pygame.font.Font(FONT_NAME, 44)
        text = font.render("选择模式", True, (66,165,245))
        text_rect = text.get_rect(center=(WINDOW_WIDTH//2, panel_rect.top+48))
        self.surface.blit(text, text_rect)
        # 按钮
        for btn in self.buttons:
            btn.draw(self.surface)
    def handle_event(self, event):
        for btn in self.buttons:
            if btn.handle_event(event):
                if btn.text == "单人模式":
                    return "single"
                elif btn.text == "双人模式":
                    return "dual"
        return None

class Menu:
    def __init__(self, surface):
        self.surface = surface
        self.buttons = []
        self.background_images = []
        self.current_bg_index = 0
        self.snow_particles = [SnowParticle() for _ in range(SNOW_PARTICLE_COUNT)]
        self.title_offset = 0
        self.title_direction = 1
        self.hide_icons = False  # 新增：是否隐藏图标
        # self.activity_page = ActivityPage(self.surface)  # 不再主窗口弹窗
        self.load_backgrounds()
        self.load_bg_index()
        self.setup_buttons()
        self.bubbles = [Bubble(WINDOW_WIDTH, WINDOW_HEIGHT) for _ in range(random.randint(3,5))]
        # 新增：模式选择弹窗
        self.show_mode_select = False
        self.mode_select_menu = ModeSelectMenu(self.surface)

    def load_backgrounds(self):
        bg_dir = get_resource_path('backgrounds')
        if os.path.exists(bg_dir):
            for file in os.listdir(bg_dir):
                if file.lower().endswith(('.png', '.jpg', '.bmp')):
                    try:
                        image_path = os.path.join(bg_dir, file)
                        image = pygame.image.load(image_path)
                        image = pygame.transform.scale(image, (WINDOW_WIDTH, WINDOW_HEIGHT))
                        self.background_images.append(image)
                    except pygame.error as e:
                        print(f"错误：无法加载图片 {file}: {e}")
                        continue

    def load_bg_index(self):
        try:
            bg_index_path = get_resource_path('current_bg_index.json')
            with open(bg_index_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                idx = int(data.get('current_bg_index', 0))
                if 0 <= idx < len(self.background_images):
                    self.current_bg_index = idx
        except Exception:
            pass

    def save_bg_index(self):
        try:
            # 使用统一的资源路径处理函数
            bg_index_path = get_resource_path('current_bg_index.json')
            with open(bg_index_path, 'w', encoding='utf-8') as f:
                json.dump({'current_bg_index': self.current_bg_index}, f)
        except Exception:
            pass

    def setup_buttons(self):
        # 主菜单卡通风格按钮
        cartoon_btn_w = 260
        cartoon_btn_h = 70
        cartoon_gap = 36
        center_x = WINDOW_WIDTH // 2 - cartoon_btn_w // 2
        center_y = WINDOW_HEIGHT // 2 - cartoon_btn_h // 2
        start_button = CartoonButton(
            center_x,
            center_y - cartoon_btn_h - cartoon_gap,
            cartoon_btn_w,
            cartoon_btn_h,
            "开始游戏",
            color=(102, 204, 102),
            icon_type="smile"
        )
        settings_button = CartoonButton(
            center_x,
            center_y,
            cartoon_btn_w,
            cartoon_btn_h,
            "设置",
            color=(66, 165, 245),
            icon_type="settings"
        )
        exit_button = CartoonButton(
            center_x,
            center_y + cartoon_btn_h + cartoon_gap,
            cartoon_btn_w,
            cartoon_btn_h,
            "退出游戏",
            color=(255, 167, 38),
            icon_type="door"
        )
        # 背景切换按钮（左下角）
        bg_button = CircularButton(
            20,
            WINDOW_HEIGHT - BACKGROUND_SWITCH_BUTTON_SIZE - 20,
            BACKGROUND_SWITCH_BUTTON_SIZE,
            "切换背景"
        )
        btn_top = center_y - cartoon_btn_h - cartoon_gap  # 主按钮顶部y
        activity_button = CartoonButton(
            WINDOW_WIDTH - 390,
            20,
            110,
            48,
            "活动",
            color=(255, 213, 79),
            icon_type="activity",
            font_size=22
        )
        shop_button = CartoonButton(
            WINDOW_WIDTH - 130, 
            20, 
            110, 
            48, 
            "商店",
            color=(255, 99, 132),
            icon_type="shop",
            font_size=22
        )
        backpack_button = CartoonButton(
            WINDOW_WIDTH - 260,
            20,
            110,
            48,
            "背包",
            color=(120, 200, 120),
            icon_type="backpack",
            font_size=22
        )
        # 隐藏按钮
        hide_icons_button = ModernHideButton(
            WINDOW_WIDTH - 74,
            WINDOW_HEIGHT - 74,
            54,
            54,
            "隐藏所有图标"
        )
        self.buttons = [start_button, settings_button, exit_button, bg_button, activity_button, shop_button, backpack_button, hide_icons_button]

    def update_bubbles(self):
        for i, b in enumerate(self.bubbles):
            b.update()
            if b.alpha <= 0 or b.y < -b.r*2:
                self.bubbles[i] = Bubble(WINDOW_WIDTH, WINDOW_HEIGHT)

    def draw(self):
        # 绘制背景
        if self.background_images:
            self.surface.blit(self.background_images[self.current_bg_index], (0, 0))
        else:
            self.surface.fill(BACKGROUND_COLOR)
        # 左上角显示版本号和开发者（可隐藏，且字体更小）
        if not self.hide_icons:
            font_ver = pygame.font.Font(FONT_NAME, 14)
            ver_text = font_ver.render("版本 2.6.2.3  开发者：宗成焕", True, (66, 165, 245))
            self.surface.blit(ver_text, (12, 12))
        # 更新和绘制雪花
        for particle in self.snow_particles:
            particle.update()
            particle.draw(self.surface)
        # 绘制泡泡
        self.update_bubbles()
        for b in self.bubbles:
            b.draw(self.surface)
        if self.hide_icons:
            for button in self.buttons:
                if isinstance(button, ModernHideButton):
                    button.draw(self.surface, hide_state=True)
            return
        # --- 卡通风主标题 ---
        self.title_offset += TITLE_FLOAT_SPEED * self.title_direction

        # 优化切换背景按钮及预览
        for button in self.buttons:
            if isinstance(button, CircularButton):
                next_idx = (self.current_bg_index + 1) % len(self.background_images) if self.background_images else 0
                next_img = self.background_images[next_idx] if self.background_images else None
                button.draw(self.surface, next_bg_image=next_img, show_tip=True)
            else:
                button.draw(self.surface)
        # 其它UI绘制...
        if abs(self.title_offset) > TITLE_FLOAT_AMPLITUDE:
            self.title_direction *= -1
        font = pygame.font.Font(FONT_NAME, TITLE_FONT_SIZE+16)
        text = "贪吃蛇"
        center_x = WINDOW_WIDTH // 2
        center_y = WINDOW_HEIGHT // 4 + int(self.title_offset)
        # 1. 黑色阴影
        for dx, dy in [(-4,4),(4,4),(-4,-4),(4,-4),(0,6)]:
            shadow = font.render(text, True, (0,0,0))
            shadow_rect = shadow.get_rect(center=(center_x+dx, center_y+dy))
            self.surface.blit(shadow, shadow_rect)
        # 2. 彩色描边
        for dx, dy, color in [(-3,0,(0,200,0)),(3,0,(255,200,0)),(0,-3,(0,255,0)),(0,3,(255,255,0))]:
            edge = font.render(text, True, color)
            edge_rect = edge.get_rect(center=(center_x+dx, center_y+dy))
            self.surface.blit(edge, edge_rect)
        # 3. 渐变填充
        title = font.render(text, True, (255,255,255))
        title_rect = title.get_rect(center=(center_x, center_y))
        grad = pygame.Surface(title.get_size(), pygame.SRCALPHA)
        for y in range(title.get_height()):
            r = int(102 + (255-102)*y/title.get_height())
            g = int(204 + (255-204)*y/title.get_height())
            b = int(102 + (0-102)*y/title.get_height())
            pygame.draw.line(grad, (r,g,b), (0,y), (title.get_width(),y))
        title_mask = title.copy()
        title_mask.set_colorkey((0,0,0))
        grad.blit(title_mask, (0,0), special_flags=pygame.BLEND_RGBA_MULT)
        self.surface.blit(grad, title_rect)
        # 4. Q版蛇头装饰
        cx = title_rect.right + 36
        cy = title_rect.centery + 18
        pygame.draw.circle(self.surface, (102,204,102), (cx,cy), 28)
        pygame.draw.circle(self.surface, (0,150,0), (cx,cy), 28, 4)
        pygame.draw.circle(self.surface, (255,255,255), (cx-10,cy-8), 7)
        pygame.draw.circle(self.surface, (0,0,0), (cx-10,cy-8), 3)
        pygame.draw.circle(self.surface, (255,255,255), (cx+10,cy-8), 7)
        pygame.draw.circle(self.surface, (0,0,0), (cx+10,cy-8), 3)
        pygame.draw.line(self.surface, (255,0,0), (cx,cy+18), (cx,cy+32), 4)
        pygame.draw.line(self.surface, (255,0,0), (cx,cy+28), (cx-6,cy+36), 2)
        pygame.draw.line(self.surface, (255,0,0), (cx,cy+28), (cx+6,cy+36), 2)
        # --- end ---
        for button in self.buttons:
            if isinstance(button, ModernHideButton):
                button.draw(self.surface, hide_state=self.hide_icons)
            else:
                button.draw(self.surface)
        # 新增：绘制模式选择弹窗
        if self.show_mode_select:
            self.mode_select_menu.draw()

    def handle_event(self, event):
        if self.show_mode_select:
            result = self.mode_select_menu.handle_event(event)
            if result == "single":
                self.show_mode_select = False
                return "start"
            elif result == "dual":
                self.show_mode_select = False
                return "dual"
            return None
        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos
            for b in self.bubbles:
                if b.is_hit(mx, my):
                    b.popped = True
                    b.pop_time = time.time()
        # 新增：隐藏图标状态下只响应ESC和眼睛按钮
        if self.hide_icons:
            # 支持ESC恢复
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.hide_icons = False
            # 支持点击眼睛按钮恢复
            for button in self.buttons:
                if isinstance(button, ModernHideButton) and button.handle_event(event):
                    self.hide_icons = False
            return None
        for button in self.buttons:
            if button.handle_event(event):
                if button.text == "开始游戏":
                    self.show_mode_select = True
                    return None
                # 新增：双人模式
                elif button.text == "双人模式":
                    return "dual"
                elif button.text == "设置":
                    return "settings"
                elif button.text == "退出游戏":
                    return "exit"
                elif button.text == "商店":
                    return "shop"
                elif button.text == "背包":
                    return "backpack"
                elif button.text == "隐藏所有图标":
                    self.hide_icons = True
                elif button.text == "活动":
                    return "activity"
                elif isinstance(button, CircularButton):
                    if self.background_images:
                        # 渐变动画参数
                        button.fade_alpha = 0
                        self.current_bg_index = (self.current_bg_index + 1) % len(self.background_images)
                        self.save_bg_index()
        return None

class SettingsMenu:
    def __init__(self, surface):
        self.surface = surface
        self.buttons = []
        self.setup_buttons()
        # 蛇动画参数
        self.snake_length = 22
        self.snake_speed = 2.0  # 越大越快
        self.snake_radius = 10
        self.snake_color = (220, 40, 40)
        self.snake_path = []
        self._generate_snake_path()
        
        # 背景音乐相关
        self.music_list = self._load_music_list()
        self.current_music_index = self._load_current_music_index()
        self.music_preview_playing = False

    def _generate_snake_path(self):
        padding = 30  # 蛇距离屏幕边缘的距离
        r = 50  # 路径的圆角半径
        step = 5  # 路径点的步长，值越大，蛇移动越快
        path = []
        
        # 上边
        for x in range(padding + r, WINDOW_WIDTH - padding - r, step):
            path.append((x, padding))
        # 右上角
        for angle in range(270, 361, step):
            rad = math.radians(angle)
            x = WINDOW_WIDTH - padding - r + math.cos(rad) * r
            y = padding + r + math.sin(rad) * r
            path.append((x, y))
        # 右边
        for y in range(padding + r, WINDOW_HEIGHT - padding - r, step):
            path.append((WINDOW_WIDTH - padding, y))
        # 右下角
        for angle in range(0, 91, step):
            rad = math.radians(angle)
            x = WINDOW_WIDTH - padding - r + math.cos(rad) * r
            y = WINDOW_HEIGHT - padding - r + math.sin(rad) * r
            path.append((x, y))
        # 下边
        for x in range(WINDOW_WIDTH - padding - r, padding + r, -step):
            path.append((x, WINDOW_HEIGHT - padding))
        # 左下角
        for angle in range(90, 181, step):
            rad = math.radians(angle)
            x = padding + r + math.cos(rad) * r
            y = WINDOW_HEIGHT - padding - r + math.sin(rad) * r
            path.append((x, y))
        # 左边
        for y in range(WINDOW_HEIGHT - padding - r, padding + r, -step):
            path.append((padding, y))
        # 左上角
        for angle in range(180, 271, step):
            rad = math.radians(angle)
            x = padding + r + math.cos(rad) * r
            y = padding + r + math.sin(rad) * r
            path.append((x, y))

        self.snake_path = path

    def _load_music_list(self):
        """加载可用的背景音乐列表"""
        # 使用get_resource_path获取正确的audio目录路径
        audio_dir = get_resource_path("audio")
        music_files = []
        try:
            if os.path.exists(audio_dir):
                for file in os.listdir(audio_dir):
                    if file.endswith('.mp3'):
                        # 美化显示名称
                        display_name = file.replace('.mp3', '').replace('_', ' ').title()
                        music_files.append({
                            'file': file,
                            'path': os.path.join(audio_dir, file),  # 使用完整的路径
                            'name': display_name
                        })
        except Exception as e:
            # 如果加载失败，至少返回默认音乐
            default_music_path = get_resource_path('audio/wet_hands.mp3')
            if os.path.exists(default_music_path):
                music_files.append({
                    'file': 'wet_hands.mp3',
                    'path': default_music_path,
                    'name': 'Wet Hands (默认)'
                })
        
        # 按文件名排序
        music_files.sort(key=lambda x: x['file'])
        return music_files
    
    def _load_current_music_index(self):
        """加载当前选中的音乐索引"""
        try:
            music_config_path = get_resource_path('current_music_index.json')
            if os.path.exists(music_config_path):
                with open(music_config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('current_music_index', 0)
        except Exception:
            pass
        return 0  # 默认第一个音乐
    
    def _save_current_music_index(self):
        """保存当前选中的音乐索引"""
        try:
            music_config_path = get_resource_path('current_music_index.json')
            with open(music_config_path, 'w', encoding='utf-8') as f:
                json.dump({'current_music_index': self.current_music_index}, f)
        except Exception:
            pass

    def setup_buttons(self):
        # 现代化卡片式布局
        btn_width = 300
        btn_height = 70
        btn_margin = 25
        
        # 主要设置选项按钮 - 单列布局，更简洁现代
        center_x = WINDOW_WIDTH // 2 - btn_width // 2
        start_y = 180
        
        from .ui_elements import CartoonButton
        
        # 创建按钮配置
        button_configs = [
            {"text": "背景音乐", "color": (255, 99, 132), "icon": "music"},
            {"text": "音量设置", "color": (156, 39, 176), "icon": "volume"},
            {"text": "添加背景", "color": (255, 213, 79), "icon": "image"},
            {"text": "游戏帮助", "color": (66, 165, 245), "icon": "help"}
        ]
        
        # 清空按钮列表
        self.buttons = []
        
        # 创建按钮
        for i, config in enumerate(button_configs):
            button = CartoonButton(
                center_x, start_y + i * (btn_height + btn_margin),
                btn_width, btn_height,
                config["text"], color=config["color"], 
                icon_type=config["icon"], font_size=26
            )
            self.buttons.append(button)
        
        # 返回按钮 - 单独放在底部中央
        back_button = CartoonButton(
            WINDOW_WIDTH // 2 - 140, start_y + 4 * (btn_height + btn_margin) + 20, 
            280, btn_height, "返回主菜单", color=(120, 200, 120), icon_type="back", font_size=26
        )
        self.buttons.append(back_button)

    def draw(self):
        # 1. 绘制现代化渐变背景
        self._draw_modern_background()
        
        # 2. 绘制主面板
        self._draw_main_panel()
        
        # 3. 绘制标题区域
        self._draw_title_section()
        
        # 4. 绘制功能卡片
        self._draw_feature_cards()
        
        # 5. 绘制按钮
        for button in self.buttons:
            button.draw(self.surface)
            
        # 6. 绘制状态信息
        self._draw_status_info()
    
    def _draw_modern_background(self):
        """绘制现代化背景"""
        # 创建微妙的径向渐变背景
        for y in range(WINDOW_HEIGHT):
            ratio = y / WINDOW_HEIGHT
            # 从深蓝到浅紫的渐变
            r = int(50 + (80 - 50) * ratio)
            g = int(120 + (140 - 120) * ratio) 
            b = int(200 + (255 - 200) * ratio)
            alpha = int(120 + (180 - 120) * ratio)
            
            overlay = pygame.Surface((WINDOW_WIDTH, 1), pygame.SRCALPHA)
            overlay.fill((r, g, b, alpha))
            self.surface.blit(overlay, (0, y))
    
    def _draw_main_panel(self):
        """绘制主面板"""
        # 更大的面板尺寸
        panel_width = WINDOW_WIDTH - 80
        panel_height = WINDOW_HEIGHT - 120
        panel_x = (WINDOW_WIDTH - panel_width) // 2
        panel_y = (WINDOW_HEIGHT - panel_height) // 2
        
        panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)
        
        # 面板阴影 - 多层阴影效果
        for i in range(3):
            shadow_offset = 4 + i * 2
            shadow_alpha = 40 - i * 10
            shadow_surface = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
            pygame.draw.rect(shadow_surface, (0, 0, 0, shadow_alpha), 
                           (0, 0, panel_width, panel_height), border_radius=25)
            self.surface.blit(shadow_surface, (panel_x + shadow_offset, panel_y + shadow_offset))
        
        # 面板背景 - 玻璃态效果
        glass_surface = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        pygame.draw.rect(glass_surface, (255, 255, 255, 230), 
                        (0, 0, panel_width, panel_height), border_radius=25)
        self.surface.blit(glass_surface, panel_rect)
        
        # 面板边框 - 多层边框
        pygame.draw.rect(self.surface, (200, 220, 255, 180), panel_rect, 3, border_radius=25)
        pygame.draw.rect(self.surface, (255, 255, 255, 120), panel_rect, 1, border_radius=25)
    
    def _draw_title_section(self):
        """绘制标题区域"""
        title_y = 80
        
        # 主标题 - 更大更醒目
        title_font = pygame.font.Font(FONT_NAME, 52)
        title_text = "游戏设置"
        
        # 现代化标题效果 - 多层渐变阴影
        shadow_colors = [(0, 0, 0, 60), (66, 165, 245, 40), (156, 39, 176, 30)]
        for i, (r, g, b, a) in enumerate(shadow_colors):
            offset = 3 - i
            shadow = title_font.render(title_text, True, (r, g, b, a))
            shadow_rect = shadow.get_rect(center=(WINDOW_WIDTH // 2 + offset, title_y + offset))
            self.surface.blit(shadow, shadow_rect)
        
        # 主标题 - 渐变色
        title_gradient = pygame.Surface((400, 60), pygame.SRCALPHA)
        for x in range(400):
            progress = x / 400
            # 从蓝色渐变到紫色
            r = int(66 + (156 - 66) * progress)
            g = int(165 + (39 - 165) * progress)
            b = int(245 + (176 - 245) * progress)
            pygame.draw.line(title_gradient, (r, g, b), (x, 0), (x, 60), 1)
        
        # 渲染标题文本
        title_surface = title_font.render(title_text, True, (255, 255, 255))
        title_mask = pygame.mask.from_surface(title_surface)
        title_outline = title_mask.to_surface(setcolor=(255, 255, 255), unsetcolor=(0, 0, 0, 0))
        
        # 应用渐变
        title_gradient = pygame.transform.scale(title_gradient, title_surface.get_size())
        title_gradient.blit(title_outline, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        
        # 绘制标题
        title_rect = title_gradient.get_rect(center=(WINDOW_WIDTH // 2, title_y))
        self.surface.blit(title_gradient, title_rect)
        
        # 副标题 - 更现代的字体和颜色
        subtitle_font = pygame.font.Font(FONT_NAME, 22)
        subtitle_text = "个性化您的游戏体验"
        subtitle_surface = subtitle_font.render(subtitle_text, True, (100, 100, 120))
        subtitle_rect = subtitle_surface.get_rect(center=(WINDOW_WIDTH // 2, title_y + 40))
        self.surface.blit(subtitle_surface, subtitle_rect)
        
        # 装饰元素 - 现代化分隔线
        line_y = title_y + 60
        line_width = 300
        line_x = (WINDOW_WIDTH - line_width) // 2
        
        # 渐变线条
        for i in range(line_width):
            progress = i / line_width
            # 从紫色渐变到蓝色
            r = int(156 + (66 - 156) * progress)
            g = int(39 + (165 - 39) * progress)
            b = int(176 + (245 - 176) * progress)
            alpha = int(200 * (1 - abs(2*progress - 1)))  # 中间最亮
            
            line_surface = pygame.Surface((1, 3), pygame.SRCALPHA)
            line_surface.fill((r, g, b, alpha))
            self.surface.blit(line_surface, (line_x + i, line_y))
    
    def _draw_feature_cards(self):
        """绘制功能卡片背景"""
        # 单一大卡片背景，适配单列按钮布局
        card_width = 340
        card_height = 400
        card_x = WINDOW_WIDTH // 2 - card_width // 2
        card_y = 160
        
        card_rect = pygame.Rect(card_x, card_y, card_width, card_height)
        
        # 卡片阴影 - 更柔和的多层阴影
        for i in range(3):
            shadow_offset = 4 + i * 2
            shadow_alpha = 30 - i * 8
            shadow_surface = pygame.Surface((card_width, card_height), pygame.SRCALPHA)
            pygame.draw.rect(shadow_surface, (0, 0, 0, shadow_alpha), 
                           (0, 0, card_width, card_height), border_radius=20)
            self.surface.blit(shadow_surface, (card_x + shadow_offset, card_y + shadow_offset))
        
        # 卡片背景 - 半透明玻璃效果
        card_surface = pygame.Surface((card_width, card_height), pygame.SRCALPHA)
        pygame.draw.rect(card_surface, (255, 255, 255, 120), 
                       (0, 0, card_width, card_height), border_radius=20)
        self.surface.blit(card_surface, card_rect)
        
        # 卡片边框 - 渐变效果
        border_colors = [(255, 99, 132), (156, 39, 176), (66, 165, 245)]
        segments = 30
        for i in range(segments):
            progress = i / segments
            # 在颜色之间进行插值
            idx = int(progress * (len(border_colors) - 1))
            t = progress * (len(border_colors) - 1) - idx
            if idx < len(border_colors) - 1:
                r = int(border_colors[idx][0] * (1 - t) + border_colors[idx + 1][0] * t)
                g = int(border_colors[idx][1] * (1 - t) + border_colors[idx + 1][1] * t)
                b = int(border_colors[idx][2] * (1 - t) + border_colors[idx + 1][2] * t)
                color = (r, g, b, 180)
                
                # 绘制边框段
                angle_start = progress * 360
                angle_end = (progress + 1/segments) * 360
                rect = card_rect.inflate(2, 2)
                pygame.draw.arc(self.surface, color, rect, 
                              math.radians(angle_start), math.radians(angle_end), 3)
        
        # 卡片标题
        title_font = pygame.font.Font(FONT_NAME, 24)
        title_surface = title_font.render("游戏设置", True, (80, 80, 80))
        title_rect = title_surface.get_rect(center=(WINDOW_WIDTH // 2, card_y - 15))
        self.surface.blit(title_surface, title_rect)
    
    def _draw_status_info(self):
        """绘制状态信息"""
        info_y = WINDOW_HEIGHT - 60
        info_font = pygame.font.Font(FONT_NAME, 18)
        
        # 获取当前音乐名称
        try:
            current_music = self.music_list[self.current_music_index]['name'] if self.music_list else "未知"
        except:
            current_music = "未知"
        
        # 创建状态信息背景
        status_bg = pygame.Surface((WINDOW_WIDTH - 100, 30), pygame.SRCALPHA)
        pygame.draw.rect(status_bg, (255, 255, 255, 80), (0, 0, WINDOW_WIDTH - 100, 30), border_radius=15)
        status_bg_rect = status_bg.get_rect(center=(WINDOW_WIDTH // 2, info_y))
        self.surface.blit(status_bg, status_bg_rect)
        
        # 绘制状态文本
        status_text = f"当前背景音乐: {current_music}  |  版本: v2.0  |  状态: 正常运行"
        status_surface = info_font.render(status_text, True, (80, 80, 100))
        status_rect = status_surface.get_rect(center=(WINDOW_WIDTH // 2, info_y))
        self.surface.blit(status_surface, status_rect)

    def draw_animated_snake(self):
        # Q版卡通蛇动画
        current_time = pygame.time.get_ticks()
        snake_head_index = int(current_time / 1000 * self.snake_speed * 10) % len(self.snake_path)
        colors = [
            (255, 213, 79), (66, 165, 245), (120, 200, 120), (255, 167, 38), (255, 99, 132), (156, 39, 176)
        ]
        for i in range(self.snake_length):
            index = (snake_head_index - i * 5) % len(self.snake_path)
            if index < 0:
                index += len(self.snake_path)
            pos = self.snake_path[index]
            scale = 1.0 - (i / (self.snake_length+2))
            radius = int(self.snake_radius * (0.9 + 0.5*scale))
            color = colors[i % len(colors)]
            if i == 0:
                # 蛇头：大圆+大眼睛+红舌头
                pygame.draw.circle(self.surface, (102,204,102), (int(pos[0]), int(pos[1])), radius+10)
                pygame.draw.circle(self.surface, (0,150,0), (int(pos[0]), int(pos[1])), radius+10, 3)
                # 眼睛
                pygame.draw.circle(self.surface, (255,255,255), (int(pos[0])-8, int(pos[1])-6), 6)
                pygame.draw.circle(self.surface, (0,0,0), (int(pos[0])-8, int(pos[1])-6), 2)
                pygame.draw.circle(self.surface, (255,255,255), (int(pos[0])+8, int(pos[1])-6), 6)
                pygame.draw.circle(self.surface, (0,0,0), (int(pos[0])+8, int(pos[1])-6), 2)
                # 笑嘴
                pygame.draw.arc(self.surface, (0,0,0), (int(pos[0])-8, int(pos[1]), 16, 10), 3.5, 5.8, 2)
                # 舌头
                pygame.draw.line(self.surface, (255,0,0), (int(pos[0]), int(pos[1])+10), (int(pos[0]), int(pos[1])+22), 3)
                pygame.draw.line(self.surface, (255,0,0), (int(pos[0]), int(pos[1])+18), (int(pos[0])-4, int(pos[1])+26), 2)
                pygame.draw.line(self.surface, (255,0,0), (int(pos[0]), int(pos[1])+18), (int(pos[0])+4, int(pos[1])+26), 2)
            else:
                # 身体：彩色圆点
                pygame.draw.circle(self.surface, color, (int(pos[0]), int(pos[1])), radius)
                pygame.draw.circle(self.surface, (255,255,255), (int(pos[0]), int(pos[1])), radius, 2)

    def handle_event(self, event):
        for button in self.buttons:
            if button.handle_event(event):
                if button.text == "背景音乐":
                    return "background_music"
                elif button.text == "添加背景":
                    return "add_background"
                elif button.text == "游戏帮助":
                    return "help"
                elif button.text == "音量设置":
                    return "volume_settings"
                elif button.text == "返回主菜单":
                    return "back"
        return None

class MusicSelectionMenu:
    def __init__(self, surface, audio_manager, game_controller):
        self.surface = surface
        self.audio_manager = audio_manager
        self.game_controller = game_controller
        self.font = pygame.font.Font(FONT_NAME, 24)
        self.title_font = pygame.font.Font(FONT_NAME, 36)
        self.small_font = pygame.font.Font(FONT_NAME, 18)
        
        # 加载音乐列表
        self.music_list = self._load_music_list()
        self.current_music_index = self._load_current_music_index()
        self.scroll_offset = 0
        self.music_cards = []
        self.preview_playing = False
        self.preview_music_index = -1
        
        # 动画和特效相关
        self.floating_particles = []
        self.init_particles()
        self.glow_timer = 0
        self.wave_offset = 0
        
        # 创建音乐卡片
        self._create_music_cards()
        
        # 返回按钮 - 使用更美观的设计
        from .ui_elements import CartoonButton
        self.back_button = CartoonButton(
            50, WINDOW_HEIGHT - 80, 140, 50, "返回", 
            color=(255, 107, 107), icon_type="back", font_size=20
        )
        
    def init_particles(self):
        """初始化粒子系统"""
        import random
        for _ in range(50):
            self.floating_particles.append({
                'x': random.randint(0, WINDOW_WIDTH),
                'y': random.randint(0, WINDOW_HEIGHT),
                'size': random.randint(1, 3),
                'color': random.choice([(66, 165, 245), (135, 206, 235), (173, 216, 230)]),
                'speed_x': random.uniform(-0.5, 0.5),
                'speed_y': random.uniform(-1, -0.3),
                'alpha': random.randint(50, 150)
            })
        
    def _load_music_list(self):
        """加载可用的背景音乐列表"""
        # 使用get_resource_path获取正确的audio目录路径
        audio_dir = get_resource_path("audio")
        music_files = []
        try:
            if os.path.exists(audio_dir):
                for file in os.listdir(audio_dir):
                    if file.endswith('.mp3'):
                        # 美化显示名称
                        display_name = file.replace('.mp3', '').replace('_', ' ').title()
                        # 特殊名称处理
                        name_map = {
                            'Wet Hands': 'Wet Hands (默认)',
                            'Deadman': '黑神话',
                            'Huitailang': '灰太狼',
                            'Lanyangyang': '懒羊羊',
                            'Man': '男声',
                            'Meiyangyang': '美羊羊',
                            'Qijizaixian': '奇迹再现',
                            'Seeyouagain': 'See You Again',
                            'Xiyangyang': '喜羊羊',
                            'Zhangyuge': '章鱼哥'
                        }
                        display_name = name_map.get(display_name, display_name)
                        
                        music_files.append({
                            'file': file,
                            'path': os.path.join(audio_dir, file),  # 使用完整的路径
                            'name': display_name
                        })
        except Exception as e:
            # 如果加载失败，至少返回默认音乐
            default_music_path = get_resource_path('audio/wet_hands.mp3')
            if os.path.exists(default_music_path):
                music_files.append({
                    'file': 'wet_hands.mp3',
                    'path': default_music_path,
                    'name': 'Wet Hands (默认)'
                })
        
        # 按文件名排序
        music_files.sort(key=lambda x: x['file'])
        return music_files
    
    def _load_current_music_index(self):
        """加载当前选中的音乐索引"""
        try:
            music_config_path = get_resource_path('current_music_index.json')
            if os.path.exists(music_config_path):
                with open(music_config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('current_music_index', 0)
        except Exception:
            pass
        return 0  # 默认第一个音乐
    
    def _save_current_music_index(self):
        """保存当前选中的音乐索引"""
        try:
            music_config_path = get_resource_path('current_music_index.json')
            with open(music_config_path, 'w', encoding='utf-8') as f:
                json.dump({'current_music_index': self.current_music_index}, f)
        except Exception:
            pass
    
    def _create_music_cards(self):
        """创建音乐卡片"""
        self.music_cards = []
        card_width = 300
        card_height = 80
        cards_per_row = 2
        margin = 20
        start_x = (WINDOW_WIDTH - (card_width * cards_per_row + margin * (cards_per_row - 1))) // 2
        start_y = 120
        
        for i, music in enumerate(self.music_list):
            row = i // cards_per_row
            col = i % cards_per_row
            x = start_x + col * (card_width + margin)
            y = start_y + row * (card_height + margin)
            
            self.music_cards.append({
                'rect': pygame.Rect(x, y, card_width, card_height),
                'music': music,
                'index': i,
                'is_hovered': False
            })
    
    def handle_event(self, event):
        # 处理返回按钮
        if self.back_button.handle_event(event):
            self.stop_preview()
            return "back"
        
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = event.pos
            
            # 检查音乐卡片点击
            for card in self.music_cards:
                if card['rect'].collidepoint(mouse_pos):
                    # 选中这个音乐
                    self.current_music_index = card['index']
                    self._save_current_music_index()
                    
                    # 停止预览并更新背景音乐
                    self.stop_preview()
                    self.game_controller.update_menu_music()
                    return None
        
        elif event.type == pygame.MOUSEMOTION:
            mouse_pos = event.pos
            # 更新卡片悬停状态
            for card in self.music_cards:
                card['is_hovered'] = card['rect'].collidepoint(mouse_pos)
        
        elif event.type == pygame.MOUSEWHEEL:
            # 滚轮滚动
            self.scroll_offset += event.y * 30
            max_scroll = max(0, len(self.music_list) // 2 * 100 - 200)
            self.scroll_offset = max(-max_scroll, min(0, self.scroll_offset))
            self._create_music_cards()  # 重新创建卡片位置
        
        return None
    
    def preview_music(self, music_index):
        """预览音乐"""
        if music_index < len(self.music_list):
            music = self.music_list[music_index]
            self.audio_manager.stop_music()
            if self.audio_manager.play_music(music['path'], loop=False):
                self.preview_playing = True
                self.preview_music_index = music_index
    
    def stop_preview(self):
        """停止预览"""
        if self.preview_playing:
            self.preview_playing = False
            self.preview_music_index = -1
    
    def get_current_music_path(self):
        """获取当前选中的音乐路径"""
        if 0 <= self.current_music_index < len(self.music_list):
            return self.music_list[self.current_music_index]['path']
        return get_resource_path('audio/wet_hands.mp3')  # 使用get_resource_path获取默认音乐
    
    def draw(self):
        # 更新动画计时器
        import time
        self.glow_timer += 0.1
        self.wave_offset += 0.05
        
        # 更新粒子位置
        self._update_particles()
        
        # 绘制华丽的动态背景
        self._draw_dynamic_background()
        
        # 绘制粒子系统
        self._draw_particles()
        
        # 绘制主面板 - 使用玻璃态设计
        self._draw_glass_panel()
        
        # 绘制标题 - 3D立体效果
        self._draw_3d_title()
        
        # 绘制音乐卡片 - 现代化设计
        self._draw_modern_music_cards()
        
        # 绘制返回按钮
        self.back_button.draw(self.surface)
        
        # 绘制装饰元素
        self._draw_decorations()
    
    def _update_particles(self):
        """更新粒子位置"""
        import random
        for particle in self.floating_particles:
            particle['x'] += particle['speed_x']
            particle['y'] += particle['speed_y']
            
            # 重置超出屏幕的粒子
            if particle['y'] < 0:
                particle['y'] = WINDOW_HEIGHT
                particle['x'] = random.randint(0, WINDOW_WIDTH)
            if particle['x'] < 0 or particle['x'] > WINDOW_WIDTH:
                particle['x'] = random.randint(0, WINDOW_WIDTH)
    
    def _draw_dynamic_background(self):
        """绘制动态渐变背景"""
        # 创建径向渐变背景
        center_x, center_y = WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2
        max_radius = int(math.sqrt(center_x**2 + center_y**2))
        
        # 动态颜色渐变
        for radius in range(0, max_radius, 3):
            ratio = radius / max_radius
            # 使用正弦波创建动态效果
            wave = math.sin(self.wave_offset + ratio * math.pi * 2) * 0.3
            
            # 从深蓝到浅蓝的渐变
            r = int(20 + (50 + wave * 30) * ratio)
            g = int(30 + (100 + wave * 50) * ratio)
            b = int(60 + (150 + wave * 70) * ratio)
            alpha = int(255 * (1 - ratio * 0.7))
            
            color = (*[max(0, min(255, c)) for c in [r, g, b]], alpha)
            
            if radius < max_radius - 3:
                pygame.draw.circle(self.surface, color, (center_x, center_y), radius, 3)
    
    def _draw_particles(self):
        """绘制粒子系统"""
        for particle in self.floating_particles:
            # 动态透明度
            alpha_wave = math.sin(self.glow_timer + particle['x'] * 0.01) * 0.3 + 0.7
            alpha = int(particle['alpha'] * alpha_wave)
            
            # 绘制粒子及其光晕
            size = particle['size']
            color = (*particle['color'], alpha)
            
            # 主粒子
            particle_surface = pygame.Surface((size * 4, size * 4), pygame.SRCALPHA)
            pygame.draw.circle(particle_surface, color, (size * 2, size * 2), size)
            
            # 光晕效果
            for i in range(1, 4):
                glow_alpha = alpha // (i + 1)
                glow_color = (*particle['color'], glow_alpha)
                pygame.draw.circle(particle_surface, glow_color, 
                                 (size * 2, size * 2), size + i)
            
            self.surface.blit(particle_surface, 
                            (particle['x'] - size * 2, particle['y'] - size * 2))
    
    def _draw_glass_panel(self):
        """绘制玻璃态主面板"""
        panel_rect = pygame.Rect(50, 50, WINDOW_WIDTH - 100, WINDOW_HEIGHT - 100)
        
        # 多层阴影效果
        for i in range(5):
            shadow_alpha = 60 - i * 10
            shadow_surface = pygame.Surface((panel_rect.width, panel_rect.height), pygame.SRCALPHA)
            pygame.draw.rect(shadow_surface, (0, 0, 0, shadow_alpha), 
                           (0, 0, panel_rect.width, panel_rect.height), border_radius=25)
            self.surface.blit(shadow_surface, (panel_rect.x + i * 2, panel_rect.y + i * 2))
        
        # 玻璃态背景 - 渐变效果
        for y in range(panel_rect.height):
            ratio = y / panel_rect.height
            alpha = int(200 + (255 - 200) * (1 - ratio))
            
            # 动态颜色变化
            wave = math.sin(self.wave_offset + ratio * math.pi) * 0.1
            base_color = (245 + wave * 20, 248 + wave * 15, 255)
            
            line_surface = pygame.Surface((panel_rect.width, 1), pygame.SRCALPHA)
            line_surface.fill((*[int(max(245, min(255, c))) for c in base_color], alpha))
            self.surface.blit(line_surface, (panel_rect.x, panel_rect.y + y))
        
        # 多层发光边框
        glow_intensity = math.sin(self.glow_timer) * 0.3 + 0.7
        for i in range(3):
            glow_alpha = int(150 * glow_intensity / (i + 1))
            glow_color = (66, 165, 245, glow_alpha)
            pygame.draw.rect(self.surface, glow_color, panel_rect, 4 + i, border_radius=25)
    
    def _draw_3d_title(self):
        """绘制立体标题"""
        title_text = "🎵 选择背景音乐"
        title_y = 80
        
        # 立体阴影效果
        shadow_layers = [(4, 4, (0, 0, 0, 120)), (2, 2, (0, 0, 0, 80))]
        for dx, dy, color in shadow_layers:
            shadow = self.title_font.render(title_text, True, color[:3])
            shadow.set_alpha(color[3])
            shadow_rect = shadow.get_rect(center=(WINDOW_WIDTH // 2 + dx, title_y + dy))
            self.surface.blit(shadow, shadow_rect)
        
        # 发光边框
        glow_offset = math.sin(self.glow_timer * 2) * 2
        edge_colors = [(255, 100, 100), (100, 255, 100), (100, 100, 255), (255, 255, 100)]
        for i, edge_color in enumerate(edge_colors):
            dx = math.sin(self.glow_timer + i * math.pi / 2) * glow_offset
            dy = math.cos(self.glow_timer + i * math.pi / 2) * glow_offset
            edge = self.title_font.render(title_text, True, edge_color)
            edge.set_alpha(120)
            edge_rect = edge.get_rect(center=(WINDOW_WIDTH // 2 + dx, title_y + dy))
            self.surface.blit(edge, edge_rect)
        
        # 主文字
        main_title = self.title_font.render(title_text, True, (255, 255, 255))
        title_rect = main_title.get_rect(center=(WINDOW_WIDTH // 2, title_y))
        self.surface.blit(main_title, title_rect)
    
    def _draw_modern_music_cards(self):
        """绘制现代化音乐卡片"""
        for card in self.music_cards:
            rect = card['rect']
            music = card['music']
            is_selected = card['index'] == self.current_music_index
            is_hovered = card['is_hovered']
            
            # 动态效果
            hover_scale = 1.05 if is_hovered else 1.0
            scaled_rect = pygame.Rect(
                rect.centerx - rect.width * hover_scale // 2,
                rect.centery - rect.height * hover_scale // 2,
                int(rect.width * hover_scale),
                int(rect.height * hover_scale)
            )
            
            # 卡片阴影 - 多层效果
            shadow_offset = 3 if not is_hovered else 6
            for i in range(3):
                shadow_alpha = 40 - i * 10
                shadow_rect = pygame.Rect(
                    scaled_rect.x + shadow_offset + i,
                    scaled_rect.y + shadow_offset + i,
                    scaled_rect.width, scaled_rect.height
                )
                shadow_surface = pygame.Surface((scaled_rect.width, scaled_rect.height), pygame.SRCALPHA)
                pygame.draw.rect(shadow_surface, (0, 0, 0, shadow_alpha), 
                               (0, 0, scaled_rect.width, scaled_rect.height), border_radius=15)
                self.surface.blit(shadow_surface, shadow_rect)
            
            # 卡片背景颜色和效果
            if is_selected:
                # 当前选中 - 金色渐变
                self._draw_gradient_card(scaled_rect, 
                                       [(255, 215, 0), (255, 165, 0)], 
                                       (255, 255, 255))
                # 发光效果
                glow_alpha = int(100 * (math.sin(self.glow_timer * 3) * 0.3 + 0.7))
                glow_surface = pygame.Surface((scaled_rect.width + 20, scaled_rect.height + 20), pygame.SRCALPHA)
                pygame.draw.rect(glow_surface, (255, 215, 0, glow_alpha), 
                               (10, 10, scaled_rect.width, scaled_rect.height), border_radius=15)
                self.surface.blit(glow_surface, (scaled_rect.x - 10, scaled_rect.y - 10))
            
            elif is_hovered:
                # 悬停状态 - 蓝色渐变
                self._draw_gradient_card(scaled_rect, 
                                       [(100, 149, 237), (135, 206, 235)], 
                                       (255, 255, 255))
            else:
                # 默认状态 - 白色渐变
                self._draw_gradient_card(scaled_rect, 
                                       [(255, 255, 255), (248, 248, 255)], 
                                       (80, 80, 80))
            
            # 绘制卡片内容
            self._draw_card_content(scaled_rect, music, is_selected, is_hovered)
    
    def _draw_gradient_card(self, rect, colors, text_color):
        """绘制渐变卡片"""
        # 绘制渐变背景
        for y in range(rect.height):
            ratio = y / rect.height
            r = int(colors[0][0] + (colors[1][0] - colors[0][0]) * ratio)
            g = int(colors[0][1] + (colors[1][1] - colors[0][1]) * ratio)
            b = int(colors[0][2] + (colors[1][2] - colors[0][2]) * ratio)
            
            line_surface = pygame.Surface((rect.width, 1))
            line_surface.fill((r, g, b))
            self.surface.blit(line_surface, (rect.x, rect.y + y))
        
        # 绘制圆角边框
        pygame.draw.rect(self.surface, (200, 200, 200), rect, 2, border_radius=15)
    
    def _draw_card_content(self, rect, music, is_selected, is_hovered):
        """绘制卡片内容"""
        # 确定文字颜色
        if is_selected:
            text_color = (255, 255, 255)
            icon_color = (255, 255, 255)
        elif is_hovered:
            text_color = (255, 255, 255)
            icon_color = (255, 255, 255)
        else:
            text_color = (80, 80, 80)
            icon_color = (100, 100, 100)
        
        # 绘制音乐图标
        icon_text = "🎵"
        icon_surface = self.font.render(icon_text, True, icon_color)
        icon_rect = icon_surface.get_rect(center=(rect.centerx, rect.centery - 20))
        self.surface.blit(icon_surface, icon_rect)
        
        # 绘制音乐名称
        name_text = self.font.render(music['name'], True, text_color)
        name_rect = name_text.get_rect(center=(rect.centerx, rect.centery + 5))
        self.surface.blit(name_text, name_rect)
        
        # 绘制状态文本
        if is_selected:
            status_text = "✓ 正在播放"
            status_color = (144, 238, 144)
        else:
            status_text = "👆 点击选择"
            status_color = text_color
        
        status_surface = self.small_font.render(status_text, True, status_color)
        status_rect = status_surface.get_rect(center=(rect.centerx, rect.centery + 25))
        self.surface.blit(status_surface, status_rect)
    
    def _draw_decorations(self):
        """绘制装饰元素"""
        # 角落装饰
        corner_size = 50
        corner_colors = [(255, 215, 0, 100), (255, 165, 0, 80)]
        
        # 左上角
        for i, color in enumerate(corner_colors):
            offset = i * 5
            corner_surface = pygame.Surface((corner_size - offset, corner_size - offset), pygame.SRCALPHA)
            pygame.draw.arc(corner_surface, color, 
                          (0, 0, corner_size - offset, corner_size - offset), 
                          0, math.pi / 2, 3)
            self.surface.blit(corner_surface, (60 + offset, 60 + offset))
        
        # 右下角
        for i, color in enumerate(corner_colors):
            offset = i * 5
            corner_surface = pygame.Surface((corner_size - offset, corner_size - offset), pygame.SRCALPHA)
            pygame.draw.arc(corner_surface, color, 
                          (0, 0, corner_size - offset, corner_size - offset), 
                          math.pi, math.pi * 3 / 2, 3)
            self.surface.blit(corner_surface, 
                            (WINDOW_WIDTH - 110 - offset, WINDOW_HEIGHT - 110 - offset))

class HelpMenu:
    def __init__(self, surface):
        self.surface = surface
        self.font_title = pygame.font.Font(FONT_NAME, 36)
        self.font_heading = pygame.font.Font(FONT_NAME, 28)
        self.font_text = pygame.font.Font(FONT_NAME, 22)
        self.scroll_y = 0
        self.help_content = load_help_text()
        self.total_content_height = self._calculate_content_height()

        self.back_button = Button(
            WINDOW_WIDTH // 2 - BUTTON_WIDTH // 2,
            WINDOW_HEIGHT - BUTTON_HEIGHT - 30,
            BUTTON_WIDTH,
            BUTTON_HEIGHT,
            "返回"
        )
        # 删除泡泡动画相关内容，恢复原状

    def _calculate_content_height(self):
        height = 0
        for line in self.help_content:
            if line.startswith('## '):
                height += self.font_heading.get_height() + 20
            elif line.startswith('# '):
                height += self.font_title.get_height() + 25
            else:
                height += self.font_text.get_height() + 10
        return height

    def handle_event(self, event):
        if self.back_button.handle_event(event):
            return "back"
        
        if event.type == pygame.MOUSEWHEEL:
            self.scroll_y += event.y * 20
            # Clamp scroll
            max_scroll = 0
            min_scroll = min(0, (WINDOW_HEIGHT - 200) - self.total_content_height)
            if self.total_content_height < WINDOW_HEIGHT - 200:
                 min_scroll = 0
            self.scroll_y = max(min_scroll, min(max_scroll, self.scroll_y))

        return None

    def draw(self):
        # 恢复为原始的帮助页面背景样式
        # 使用深色半透明遮罩提升可读性
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 220))  # 增加透明度到220，更突出内容
        self.surface.blit(overlay, (0, 0))

        # 创建渐变背景面板
        panel_rect = pygame.Rect(50, 50, WINDOW_WIDTH - 100, WINDOW_HEIGHT - 100)
        
        # 绘制带有渐变效果的圆角矩形背景
        gradient_height = panel_rect.height
        for y in range(gradient_height):
            alpha = int(180 + 30 * math.sin(y * math.pi / gradient_height))
            color = (20, 30, 40, alpha)
            pygame.draw.line(self.surface, color, 
                           (panel_rect.left, panel_rect.top + y), 
                           (panel_rect.right, panel_rect.top + y))
        
        # 添加边框效果
        pygame.draw.rect(self.surface, (66, 165, 245, 200), panel_rect, 3, border_radius=15)  # 使用主题蓝色边框
        
        # 添加微妙的阴影效果
        shadow_rect = panel_rect.move(-5, -5)
        pygame.draw.rect(self.surface, (0, 0, 0, 80), shadow_rect, border_radius=15)
        
        y_offset = 70 + self.scroll_y
        for line in self.help_content:
            if y_offset > panel_rect.bottom - 30:
                break
            
            font = self.font_text
            color = (200, 200, 200)
            x_pos = 80
            
            if line.startswith('## '):
                font = self.font_heading
                color = GOLD
                line = line[3:]
                y_offset += 10
            elif line.startswith('# '):
                font = self.font_title
                color = WHITE
                line = line[2:]
                y_offset += 15
            
            if y_offset >= 60:
                text_surf = font.render(line, True, color)
                self.surface.blit(text_surf, (x_pos, y_offset))

            y_offset += font.get_height() + 5

        self.back_button.draw(self.surface)

class PauseMenu:
    def __init__(self, surface):
        self.surface = surface
        self.buttons = []
        self.setup_buttons()

    def setup_buttons(self):
        from .ui_elements import CartoonButton
        btn_width = 220
        btn_height = 64
        gap = 36
        center_x = WINDOW_WIDTH // 2 - btn_width // 2
        center_y = WINDOW_HEIGHT // 2 - btn_height // 2
        continue_btn = CartoonButton(center_x, center_y - btn_height//2 - gap//2, btn_width, btn_height, "继续游戏", color=(66,165,245), icon_type="smile")
        main_menu_btn = CartoonButton(center_x, center_y + btn_height//2 + gap//2, btn_width, btn_height, "返回主菜单", color=(255,213,79), icon_type="back")
        self.buttons = [continue_btn, main_menu_btn]

    def draw(self):
        # 半透明遮罩
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0,0,0,120))
        self.surface.blit(overlay, (0,0))
        # 圆角面板
        from .ui_elements import draw_rounded_rect
        panel_rect = pygame.Rect(WINDOW_WIDTH//2-260, WINDOW_HEIGHT//2-120, 520, 240)
        draw_rounded_rect(self.surface, panel_rect, (255,255,255,240), 32)
        # 标题
        font = pygame.font.Font(FONT_NAME, 44)
        text = font.render("游戏暂停", True, (66,165,245))
        text_rect = text.get_rect(center=(WINDOW_WIDTH//2, panel_rect.top+48))
        self.surface.blit(text, text_rect)
        # 优化按钮布局：标题下方留足间距，按钮整体在面板下半部分居中
        btn_h = sum([btn.rect.height for btn in self.buttons])
        gap = 32
        title_gap = 36
        total_h = btn_h + gap
        y = text_rect.bottom + title_gap
        # 保证按钮不会超出面板底部
        min_y = panel_rect.bottom - total_h - 24
        if y < min_y:
            y = min_y
        for btn in self.buttons:
            btn.rect.centerx = WINDOW_WIDTH // 2
            btn.rect.y = y
            btn.draw(self.surface)
            y += btn.rect.height + gap

    def handle_event(self, event):
        for btn in self.buttons:
            if btn.handle_event(event):
                if btn.text == "继续游戏":
                    return "continue"
                elif btn.text == "返回主菜单":
                    return "main_menu"
        return None

class GameOverMenuSingle:
    def __init__(self, surface):
        self.surface = surface
        self.buttons = []
        self.setup_buttons()

    def setup_buttons(self):
        restart_button = CartoonButton(
            0, 0,
            BUTTON_WIDTH,
            BUTTON_HEIGHT,
            "重新开始",
            color=(102, 204, 102),
            icon_type="smile"
        )
        main_menu_button = CartoonButton(
            0, 0,
            BUTTON_WIDTH,
            BUTTON_HEIGHT,
            "返回主菜单",
            color=(255, 167, 38),
            icon_type="door"
        )
        self.buttons = [restart_button, main_menu_button]

    def draw(self, score=None):
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        overlay.set_alpha(MENU_BACKGROUND_ALPHA)
        overlay.fill((0, 0, 0))
        self.surface.blit(overlay, (0, 0))
        font_title = pygame.font.Font(FONT_NAME, TITLE_FONT_SIZE + 18)
        font_score = pygame.font.Font(FONT_NAME, FONT_SIZE+16)
        font_result = pygame.font.Font(FONT_NAME, FONT_SIZE+18)
        # 计算高度
        title_h = font_title.get_height() + 16
        panel_h = 70
        btn_h = sum([btn.rect.height for btn in self.buttons]) + 24
        gap = 32
        total_h = title_h + panel_h + btn_h + gap*3
        y = (WINDOW_HEIGHT - total_h) // 2
        center_x = WINDOW_WIDTH // 2
        # 标题
        text = "游戏结束"
        for dx, dy in [(-5,5),(5,5),(-5,-5),(5,-5),(0,8)]:
            shadow = font_title.render(text, True, (0,0,0))
            shadow_rect = shadow.get_rect(center=(center_x+dx, y+title_h//2+dy))
            self.surface.blit(shadow, shadow_rect)
        for dx, dy, color in [(-3,0,(0,200,0)),(3,0,(255,200,0)),(0,-3,(0,255,0)),(0,3,(255,255,0))]:
            edge = font_title.render(text, True, color)
            edge_rect = edge.get_rect(center=(center_x+dx, y+title_h//2+dy))
            self.surface.blit(edge, edge_rect)
        title = font_title.render(text, True, (255,255,255))
        title_rect = title.get_rect(center=(center_x, y+title_h//2))
        self.surface.blit(title, title_rect)
        y += title_h + gap
        # 分数面板
        panel_w = 320
        panel_rect = pygame.Rect(center_x - panel_w//2, y, panel_w, panel_h)
        pygame.draw.rect(self.surface, (66,165,245,180), panel_rect, border_radius=22)
        pygame.draw.rect(self.surface, (255,255,255), panel_rect, 4, border_radius=22)
        txt = font_score.render(f"最终分数: {score}", True, (255,255,255))
        self.surface.blit(txt, (panel_rect.x+32, y+panel_h//2-txt.get_height()//2))
        y += panel_h + gap
        # 按钮
        for button in self.buttons:
            button.rect.centerx = center_x
            button.rect.y = y
            button.draw(self.surface)
            y += button.rect.height + 24
    def handle_event(self, event):
        for button in self.buttons:
            if button.handle_event(event):
                if button.text == "重新开始":
                    return "restart"
                elif button.text == "返回主菜单":
                    return "main_menu"
        return None

# 保留GameOverMenuDual为双人模式专用（原GameOverMenu代码）
class GameOverMenuDual:
    def __init__(self, surface):
        self.surface = surface
        self.buttons = []
        self.setup_buttons()
    def setup_buttons(self):
        restart_button = CartoonButton(
            0, 0,
            BUTTON_WIDTH,
            BUTTON_HEIGHT,
            "重新开始",
            color=(102, 204, 102),
            icon_type="smile"
        )
        main_menu_button = CartoonButton(
            0, 0,
            BUTTON_WIDTH,
            BUTTON_HEIGHT,
            "返回主菜单",
            color=(255, 167, 38),
            icon_type="door"
        )
        self.buttons = [restart_button, main_menu_button]
    def draw(self, score1=None, score2=None, winner=None):
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        overlay.set_alpha(MENU_BACKGROUND_ALPHA)
        overlay.fill((0, 0, 0))
        self.surface.blit(overlay, (0, 0))

        # 字体
        font_title = pygame.font.Font(FONT_NAME, TITLE_FONT_SIZE + 18)
        font_score = pygame.font.Font(FONT_NAME, FONT_SIZE+16)
        font_result = pygame.font.Font(FONT_NAME, FONT_SIZE+18)

        # 计算各部分高度
        title_h = font_title.get_height() + 16
        panel_h = 70
        result_h = font_result.get_height() + 20
        btn_h = sum([btn.rect.height for btn in self.buttons]) + 24  # 按钮间距
        gap = 24
        total_h = title_h + panel_h + result_h + btn_h + gap*3
        y = (WINDOW_HEIGHT - total_h) // 2
        center_x = WINDOW_WIDTH // 2

        # --- 标题 ---
        text = "游戏结束"
        for dx, dy in [(-5,5),(5,5),(-5,-5),(5,-5),(0,8)]:
            shadow = font_title.render(text, True, (0,0,0))
            shadow_rect = shadow.get_rect(center=(center_x+dx, y+title_h//2+dy))
            self.surface.blit(shadow, shadow_rect)
        for dx, dy, color in [(-3,0,(0,200,0)),(3,0,(255,200,0)),(0,-3,(0,255,0)),(0,3,(255,255,0))]:
            edge = font_title.render(text, True, color)
            edge_rect = edge.get_rect(center=(center_x+dx, y+title_h//2+dy))
            self.surface.blit(edge, edge_rect)
        title = font_title.render(text, True, (255,255,255))
        title_rect = title.get_rect(center=(center_x, y+title_h//2))
        self.surface.blit(title, title_rect)
        y += title_h + gap

        # --- 分数面板 ---
        panel_w = 240
        panel_h = 70
        gap_panel = 200  # 调整为200，分数面板左右分布更宽松
        offset = panel_w // 2 + gap_panel // 2
        x2 = center_x - offset  # 玩家2在左
        x1 = center_x + offset  # 玩家1在右
        panel2 = pygame.Rect(x2 - panel_w//2, y, panel_w, panel_h)
        panel1 = pygame.Rect(x1 - panel_w//2, y, panel_w, panel_h)
        pygame.draw.rect(self.surface, (0,120,255,180), panel2, border_radius=22)
        pygame.draw.rect(self.surface, (255,255,255), panel2, 4, border_radius=22)
        txt2 = font_score.render(f"玩家2分数: {score2}", True, (255,255,255))
        self.surface.blit(txt2, (panel2.x+32, y+panel_h//2-txt2.get_height()//2))
        pygame.draw.rect(self.surface, (0,200,0,180), panel1, border_radius=22)
        pygame.draw.rect(self.surface, (255,255,255), panel1, 4, border_radius=22)
        txt1 = font_score.render(f"玩家1分数: {score1}", True, (255,255,255))
        self.surface.blit(txt1, (panel1.x+32, y+panel_h//2-txt1.get_height()//2))
        y += panel_h + gap

        # --- 胜负信息 ---
        if winner == 1:
            result_text, color = "玩家1胜利！", (0,200,0)
        elif winner == 2:
            result_text, color = "玩家2胜利！", (0,120,255)
        else:
            result_text, color = "平局！", (255,200,0)
        for dx, dy in [(-3,3),(3,3),(-3,-3),(3,-3),(0,5)]:
            shadow = font_result.render(result_text, True, (0,0,0))
            shadow_rect = shadow.get_rect(center=(center_x+dx, y+result_h//2+dy))
            self.surface.blit(shadow, shadow_rect)
        result = font_result.render(result_text, True, color)
        result_rect = result.get_rect(center=(center_x, y+result_h//2))
        self.surface.blit(result, result_rect)
        y += result_h + gap

        # --- 按钮 ---
        for button in self.buttons:
            button.rect.centerx = center_x
            button.rect.y = y
            button.draw(self.surface)
            y += button.rect.height + 24

    def handle_event(self, event):
        for button in self.buttons:
            if button.handle_event(event):
                if button.text == "重新开始":
                    return "restart"
                elif button.text == "返回主菜单":
                    return "main_menu"
        return None

class ModernHideButton(Button):
    def __init__(self, x, y, width, height, text):
        super().__init__(x, y, width, height, text,
                         color=(187, 222, 251),        # 更淡蓝色主色
                         hover_color=(144, 202, 249),  # 更淡蓝色悬停
                         font_size=22)
        self.text_color = (255, 255, 255)
        self.radius = 16

    def draw(self, surface, hide_state=False):
        rect = self.rect.copy()
        color = self.hover_color if self.is_hovered else self.color
        pygame.draw.rect(surface, color, rect, border_radius=self.radius)
        shadow_rect = rect.move(2, 3)
        pygame.draw.rect(surface, (120, 170, 220, 40), shadow_rect, border_radius=self.radius)
        # 更明显的眼睛icon
        icon_center = rect.center
        # 眼白
        pygame.draw.ellipse(surface, (255,255,255), (icon_center[0]-16, icon_center[1]-9, 32, 18))
        # 眼球
        pygame.draw.ellipse(surface, (30, 60, 120), (icon_center[0]-8, icon_center[1]-5, 16, 10))
        # 高光
        pygame.draw.circle(surface, (220,220,255), (icon_center[0]-4, icon_center[1]-2), 3)
        # 眼睛边框
        pygame.draw.ellipse(surface, (30, 60, 120), (icon_center[0]-16, icon_center[1]-9, 32, 18), 2)
        # 隐藏状态斜杠
        if hide_state:
            pygame.draw.line(surface, (220, 0, 0), (icon_center[0]-14, icon_center[1]-8), (icon_center[0]+14, icon_center[1]+8), 4)
        # 不显示文字

class ModernIconButton(Button):
    def __init__(self, x, y, width, height, text, icon_type):
        super().__init__(x, y, width, height, text,
                         color=(66, 165, 245),
                         hover_color=(33, 150, 243),
                         font_size=22)
        self.text_color = (255, 255, 255)
        self.radius = 12
        self.icon_type = icon_type

    def draw(self, surface):
        rect = self.rect.copy()
        color = self.hover_color if self.is_hovered else self.color
        pygame.draw.rect(surface, color, rect, border_radius=self.radius)
        # icon区域
        icon_center = (rect.x + 22, rect.centery)
        if self.icon_type == "shop":
            # 简易购物袋icon
            pygame.draw.rect(surface, (255,255,255), (icon_center[0]-8, icon_center[1]-8, 16, 14), 2, border_radius=4)
            pygame.draw.arc(surface, (255,255,255), (icon_center[0]-8, icon_center[1]-14, 16, 12), 3.14, 0, 2)
        elif self.icon_type == "backpack":
            # 简易背包icon
            pygame.draw.rect(surface, (255,255,255), (icon_center[0]-8, icon_center[1]-6, 16, 12), 2, border_radius=5)
            pygame.draw.circle(surface, (255,255,255), (icon_center[0], icon_center[1]-6), 7, 2)
        elif self.icon_type == "activity":
            # 简易礼物盒icon
            pygame.draw.rect(surface, (255,255,255), (icon_center[0]-8, icon_center[1]-4, 16, 12), 2, border_radius=3)
            pygame.draw.line(surface, (255,255,255), (icon_center[0], icon_center[1]-4), (icon_center[0], icon_center[1]+8), 2)
            pygame.draw.line(surface, (255,255,255), (icon_center[0]-8, icon_center[1]+2), (icon_center[0]+8, icon_center[1]+2), 2)
            # 蝴蝶结
            pygame.draw.arc(surface, (255,255,255), (icon_center[0]-8, icon_center[1]-10, 8, 8), 0.8, 2.4, 2)
            pygame.draw.arc(surface, (255,255,255), (icon_center[0], icon_center[1]-10, 8, 8), 0.8, 2.4, 2)
        # 文字
        text_surface = self.font.render(self.text, True, self.text_color)
        text_rect = text_surface.get_rect(midleft=(rect.x + 44, rect.centery))
        surface.blit(text_surface, text_rect)

# 删除ActivityPopupMixin类和Menu.__bases__ += (ActivityPopupMixin,)