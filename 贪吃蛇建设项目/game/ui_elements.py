class Dropdown:
    def __init__(self, x, y, width, height, options, selected=None, font_size=20, color=(80,120,180), hover_color=(255,213,79)):
        self.rect = pygame.Rect(x, y, width, height)
        self.options = options
        self.selected = selected if selected is not None else (options[0] if options else None)
        self.is_open = False
        self.hovered_idx = None
        self.font = pygame.font.Font(FONT_NAME, font_size)
        self.color = color
        self.hover_color = hover_color
        self.max_visible = 30
        self.scroll = 0
        self.dragging_scrollbar = False
        self.scrollbar_offset = 0

    def draw(self, surface):
        # 主框
        pygame.draw.rect(surface, self.color, self.rect, border_radius=10)
        sel_text = self.font.render(str(self.selected) if self.selected else "请选择", True, BUTTON_TEXT_COLOR)
        surface.blit(sel_text, (self.rect.x+12, self.rect.y+8))
        # 下拉箭头
        pygame.draw.polygon(surface, BUTTON_TEXT_COLOR, [
            (self.rect.right-24, self.rect.y+18), (self.rect.right-12, self.rect.y+18), (self.rect.right-18, self.rect.y+28)
        ])
        # 展开选项
        if self.is_open:
            opt_h = self.rect.height
            visible_opts = self.options[self.scroll:self.scroll+self.max_visible]
            blank_space = opt_h * 2  # 下拉框底部留两个选项高度
            drop_rect = pygame.Rect(self.rect.x, self.rect.bottom, self.rect.width, opt_h*len(visible_opts)+blank_space)
            pygame.draw.rect(surface, self.color, drop_rect, border_radius=10)
            for i, opt in enumerate(visible_opts):
                opt_rect = pygame.Rect(self.rect.x, self.rect.bottom+i*opt_h, self.rect.width, opt_h)
                bg = self.hover_color if self.hovered_idx == self.scroll+i else self.color
                pygame.draw.rect(surface, bg, opt_rect, border_radius=8)
                txt = self.font.render(str(opt), True, BUTTON_TEXT_COLOR)
                surface.blit(txt, (opt_rect.x+12, opt_rect.y+8))
            # 底部空白区
            pygame.draw.rect(surface, self.color, (self.rect.x, self.rect.bottom+opt_h*len(visible_opts), self.rect.width, blank_space), border_radius=8)
            # 绘制滚动条（如果选项超出max_visible）
            if len(self.options) > self.max_visible:
                bar_area = pygame.Rect(self.rect.right-8, self.rect.bottom, 6, opt_h*self.max_visible)
                total = len(self.options)
                bar_h = max(20, int(bar_area.height * self.max_visible / total))
                bar_y = bar_area.y + int(bar_area.height * self.scroll / total)
                scrollbar_rect = pygame.Rect(bar_area.x, bar_y, bar_area.width, bar_h)
                pygame.draw.rect(surface, (180,180,180), bar_area, border_radius=3)
                pygame.draw.rect(surface, (120,120,120), scrollbar_rect, border_radius=3)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.is_open = not self.is_open
                return True
            if self.is_open:
                opt_h = self.rect.height
                # 优先判断是否点在滚动条上
                if len(self.options) > self.max_visible:
                    bar_area = pygame.Rect(self.rect.right-8, self.rect.bottom, 6, opt_h*self.max_visible)
                    total = len(self.options)
                    bar_h = max(20, int(bar_area.height * self.max_visible / total))
                    bar_y = bar_area.y + int(bar_area.height * self.scroll / total)
                    scrollbar_rect = pygame.Rect(bar_area.x, bar_y, bar_area.width, bar_h)
                    if scrollbar_rect.collidepoint(event.pos):
                        self.dragging_scrollbar = True
                        self.scrollbar_offset = event.pos[1] - scrollbar_rect.y
                        return True
                # 只有点在选项上才选中
                visible_count = len(self.options[self.scroll:self.scroll+self.max_visible])
                for i in range(visible_count):
                    opt_rect = pygame.Rect(self.rect.x, self.rect.bottom+i*opt_h, self.rect.width, opt_h)
                    if opt_rect.collidepoint(event.pos):
                        self.selected = self.options[self.scroll+i]
                        self.is_open = False
                        return True
                # 点击下拉区外关闭
                drop_rect = pygame.Rect(self.rect.x, self.rect.bottom, self.rect.width, opt_h*self.max_visible)
                if not drop_rect.collidepoint(event.pos):
                    self.is_open = False
        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging_scrollbar = False
        elif event.type == pygame.MOUSEMOTION:
            if self.is_open:
                opt_h = self.rect.height
                self.hovered_idx = None
                visible_count = len(self.options[self.scroll:self.scroll+self.max_visible])
                for i in range(visible_count):
                    opt_rect = pygame.Rect(self.rect.x, self.rect.bottom+i*opt_h, self.rect.width, opt_h)
                    if opt_rect.collidepoint(event.pos):
                        self.hovered_idx = self.scroll+i
                # 拖拽滚动条
                if self.dragging_scrollbar and len(self.options) > self.max_visible:
                    bar_area = pygame.Rect(self.rect.right-8, self.rect.bottom, 6, opt_h*self.max_visible)
                    total = len(self.options)
                    rel_y = event.pos[1] - bar_area.y - self.scrollbar_offset
                    max_scroll = total - self.max_visible
                    scroll = int(rel_y / (bar_area.height - max(20, int(bar_area.height * self.max_visible / total))) * max_scroll)
                    self.scroll = max(0, min(scroll, max_scroll))
        elif event.type == pygame.MOUSEWHEEL:
            if self.is_open:
                self.scroll = max(0, min(self.scroll - event.y, len(self.options)-self.max_visible))
                return True
        return False
import pygame
import math
from .constants import *
import threading
import win32gui
import win32con
import win32api
import win32process
import ctypes
import queue

class Button:
    def __init__(self, x, y, width, height, text, color=BUTTON_COLOR, hover_color=BUTTON_HOVER_COLOR, font_size=FONT_SIZE):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.is_hovered = False
        self.is_pressed = False
        self.font = pygame.font.Font(FONT_NAME, font_size)
        self.animation_offset = 0
        self.animation_direction = 1
        self.scale = 1.0  # 添加缩放属性
        self.target_scale = 1.0  # 添加目标缩放属性
        self.pulse_animation = 0  # 添加脉冲动画计数器

    def draw(self, surface):
        # 更新悬停动画
        if self.is_hovered:
            self.animation_offset += BUTTON_ANIMATION_SPEED * self.animation_direction
            if abs(self.animation_offset) > 5:
                self.animation_direction *= -1
            
            # 添加脉冲效果
            self.pulse_animation += 1
            pulse_scale = 1.0 + 0.03 * math.sin(self.pulse_animation * 0.1)
            self.scale = pulse_scale
        else:
            self.animation_offset = 0
            self.pulse_animation = 0
            self.scale = 1.0

        # 处理按下效果
        if self.is_pressed:
            self.scale = 0.95  # 按下时缩小
            rect = self.rect.copy()
            rect.y += 2
        else:
            rect = self.rect.copy()
            rect.y += self.animation_offset
            
        # 应用缩放变换
        scaled_width = int(rect.width * self.scale)
        scaled_height = int(rect.height * self.scale)
        scaled_rect = pygame.Rect(rect.x + (rect.width - scaled_width) // 2, 
                                 rect.y + (rect.height - scaled_height) // 2, 
                                 scaled_width, scaled_height)
        
        color = self.hover_color if self.is_hovered else self.color
        
        # 绘制带有圆角的按钮
        pygame.draw.rect(surface, color, scaled_rect, border_radius=10)
        
        # 添加文字阴影效果
        if self.text:
            text_surface = self.font.render(self.text, True, BUTTON_TEXT_COLOR)
            text_rect = text_surface.get_rect(center=scaled_rect.center)
            
            # 添加文字阴影
            shadow_surface = pygame.Surface((text_surface.get_width() + 4, text_surface.get_height() + 4), pygame.SRCALPHA)
            shadow_text = self.font.render(self.text, True, (0, 0, 0, 100))
            shadow_rect = shadow_text.get_rect(center=(shadow_surface.get_width()//2, shadow_surface.get_height()//2))
            shadow_surface.blit(shadow_text, shadow_rect)
            
            # 绘制阴影
            surface.blit(shadow_surface, (text_rect.x - 2, text_rect.y - 2))
            # 绘制文字
            surface.blit(text_surface, text_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.is_hovered and event.button == 1:
                self.is_pressed = True
                return True
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self.is_pressed = False
        return False

def draw_rounded_rect(surface, rect, color, corner_radius):
    """
    Draw a rectangle with rounded corners.
    We are using a workaround because pygame.draw.rect does not support alpha.
    """
    if not isinstance(rect, pygame.Rect):
        rect = pygame.Rect(rect)
        
    if rect.width < 2 * corner_radius or rect.height < 2 * corner_radius:
        raise ValueError("Rectangle is too small for the given corner radius.")

    # Create a new surface with a per-pixel alpha channel.
    shape_surf = pygame.Surface(rect.size, pygame.SRCALPHA)

    # draw the straight edges
    pygame.draw.rect(shape_surf, color, (rect.left + corner_radius, rect.top, rect.width - 2 * corner_radius, rect.height))
    pygame.draw.rect(shape_surf, color, (rect.left, rect.top + corner_radius, rect.width, rect.height - 2 * corner_radius))

    # draw the rounded corners
    pygame.draw.circle(shape_surf, color, (rect.left + corner_radius, rect.top + corner_radius), corner_radius)
    pygame.draw.circle(shape_surf, color, (rect.right - corner_radius, rect.top + corner_radius), corner_radius)
    pygame.draw.circle(shape_surf, color, (rect.left + corner_radius, rect.bottom - corner_radius), corner_radius)
    pygame.draw.circle(shape_surf, color, (rect.right - corner_radius, rect.bottom - corner_radius), corner_radius)

    surface.blit(shape_surf, rect)

class CircularButton(Button):
    def __init__(self, x, y, size, text):
        super().__init__(x, y, size, size, text)
        self.rect = pygame.Rect(x, y, size, size)
        self.rotation = 0
        self.pulse_animation = 0
        self.hover_scale = 1.0
        self.target_scale = 1.0
        
        # 现代化颜色方案
        self.gradient_colors = [
            (52, 152, 219),   # 主色调：蓝色
            (41, 128, 185),   # 深蓝色
            (155, 89, 182),   # 紫色
            (142, 68, 173),   # 深紫色
        ]
        self.current_color_index = 0
        self.color_transition = 0.0

    def draw(self, surface, next_bg_image=None, show_tip=False):
        # 更新动画
        self.pulse_animation += 0.1
        if self.is_hovered:
            self.target_scale = 1.15
            self.color_transition += 0.05
        else:
            self.target_scale = 1.0
            self.color_transition -= 0.05
            
        self.color_transition = max(0, min(1, self.color_transition))
        self.hover_scale += (self.target_scale - self.hover_scale) * 0.2
        
        # 计算当前颜色（渐变过渡）
        color1 = self.gradient_colors[self.current_color_index]
        color2 = self.gradient_colors[(self.current_color_index + 1) % len(self.gradient_colors)]
        current_color = tuple(int(c1 + (c2 - c1) * self.color_transition) for c1, c2 in zip(color1, color2))
        
        # 绘制外发光效果
        glow_radius = int(self.rect.width // 2 * self.hover_scale + 8)
        glow_surf = pygame.Surface((glow_radius * 2 + 20, glow_radius * 2 + 20), pygame.SRCALPHA)
        for i in range(3):
            alpha = 60 - i * 20 if self.is_hovered else 20 - i * 5
            pygame.draw.circle(glow_surf, (*current_color, alpha), 
                             (glow_radius + 10, glow_radius + 10), glow_radius - i * 3)
        surface.blit(glow_surf, (self.rect.centerx - glow_radius - 10, self.rect.centery - glow_radius - 10))
        
        # 绘制主体圆形（带渐变效果）
        scaled_rect = self.rect.copy()
        scaled_rect.inflate_ip(int(self.rect.width * (self.hover_scale - 1)), 
                              int(self.rect.height * (self.hover_scale - 1)))
        scaled_rect.center = self.rect.center
        
        # 创建渐变表面
        gradient_surf = pygame.Surface((scaled_rect.width, scaled_rect.height), pygame.SRCALPHA)
        center_x, center_y = scaled_rect.width // 2, scaled_rect.height // 2
        radius = scaled_rect.width // 2
        
        for r in range(radius, 0, -1):
            alpha = 255 - (radius - r) * 2
            alpha = max(100, alpha)
            color_with_alpha = (*current_color, alpha)
            pygame.draw.circle(gradient_surf, color_with_alpha, (center_x, center_y), r)
        
        surface.blit(gradient_surf, scaled_rect.topleft)
        
        # 绘制内圈高光
        highlight_radius = int(radius * 0.6)
        highlight_surf = pygame.Surface((highlight_radius * 2, highlight_radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(highlight_surf, (255, 255, 255, 80), (highlight_radius, highlight_radius), highlight_radius)
        surface.blit(highlight_surf, (scaled_rect.centerx - highlight_radius, scaled_rect.centery - highlight_radius))
        
        # 绘制现代化图标
        self._draw_modern_icon(surface, scaled_rect)
        
        # 文字提示（改进样式）
        if show_tip and self.is_hovered:
            self._draw_tooltip(surface)

        # 背景预览（改进样式）
        if self.is_hovered and next_bg_image is not None:
            self._draw_preview(surface, next_bg_image)
    
    def _draw_modern_icon(self, surface, rect):
        """绘制多彩三段式回收标志风格循环箭头"""
        import pygame.gfxdraw
        center_x, center_y = rect.centerx, rect.centery
        outer_r = int(rect.width * 0.39)
        inner_r = int(rect.width * 0.22)
        arrow_width = outer_r - inner_r
        self.rotation = (getattr(self, 'rotation', 0) + 2) % 360
        base_angle = math.radians(self.rotation)
        # 三段主色
        color_list = [
            ((60, 200, 120), (120, 255, 180)),   # 绿色渐变
            ((255, 180, 60), (255, 120, 0)),     # 橙色渐变
            ((160, 100, 255), (90, 60, 200)),    # 紫色渐变
        ]
        highlight = (255, 255, 255)
        segs = 3
        seg_angle = 2 * math.pi / segs
        gap_angle = 0.32
        for i in range(segs):
            color1, color2 = color_list[i % len(color_list)]
            # 每段起止角度，留白
            start_a = base_angle + i * seg_angle + gap_angle/2
            end_a = base_angle + (i+1) * seg_angle - gap_angle/2
            # 画弧形环段
            points = []
            steps = 18
            for j in range(steps+1):
                t = start_a + (end_a - start_a) * j / steps
                blend = j / steps
                color = tuple(int(color1[k] * (1-blend) + color2[k] * blend) for k in range(3))
                x = center_x + outer_r * math.cos(t)
                y = center_y + outer_r * math.sin(t)
                points.append((x, y))
            for j in range(steps, -1, -1):
                t = start_a + (end_a - start_a) * j / steps
                blend = j / steps
                color = tuple(int(color1[k] * (1-blend) + color2[k] * blend) for k in range(3))
                x = center_x + inner_r * math.cos(t)
                y = center_y + inner_r * math.sin(t)
                points.append((x, y))
            # 用首段颜色填充
            pygame.gfxdraw.filled_polygon(surface, points, color1)
            pygame.gfxdraw.aapolygon(surface, points, color1)
            # 高光
            if i == 0:
                for j in range(steps//2, steps):
                    t = start_a + (end_a - start_a) * j / steps
                    x = center_x + (outer_r-2) * math.cos(t)
                    y = center_y + (outer_r-2) * math.sin(t)
                    pygame.gfxdraw.pixel(surface, int(x), int(y), highlight)
            # 箭头头部
            arrow_angle = end_a
            tip_len = arrow_width * 1.45
            tip = (
                center_x + outer_r * math.cos(arrow_angle),
                center_y + outer_r * math.sin(arrow_angle)
            )
            left = (
                center_x + (outer_r-tip_len) * math.cos(arrow_angle - 0.32),
                center_y + (outer_r-tip_len) * math.sin(arrow_angle - 0.32)
            )
            right = (
                center_x + (outer_r-tip_len) * math.cos(arrow_angle + 0.32),
                center_y + (outer_r-tip_len) * math.sin(arrow_angle + 0.32)
            )
            # 先画白色描边
            pygame.gfxdraw.filled_trigon(surface, int(tip[0]), int(tip[1]), int(left[0]), int(left[1]), int(right[0]), int(right[1]), (255,255,255))
            pygame.gfxdraw.aatrigon(surface, int(tip[0]), int(tip[1]), int(left[0]), int(left[1]), int(right[0]), int(right[1]), (255,255,255))
            # 再画主色
            arrow_color = tuple(int((color1[k]+color2[k])/2) for k in range(3))
            shrink = 0.82
            tip2 = (
                center_x + outer_r * math.cos(arrow_angle),
                center_y + outer_r * math.sin(arrow_angle)
            )
            left2 = (
                center_x + (outer_r-tip_len*shrink) * math.cos(arrow_angle - 0.32),
                center_y + (outer_r-tip_len*shrink) * math.sin(arrow_angle - 0.32)
            )
            right2 = (
                center_x + (outer_r-tip_len*shrink) * math.cos(arrow_angle + 0.32),
                center_y + (outer_r-tip_len*shrink) * math.sin(arrow_angle + 0.32)
            )
            pygame.gfxdraw.filled_trigon(surface, int(tip2[0]), int(tip2[1]), int(left2[0]), int(left2[1]), int(right2[0]), int(right2[1]), arrow_color)
            pygame.gfxdraw.aatrigon(surface, int(tip2[0]), int(tip2[1]), int(left2[0]), int(left2[1]), int(right2[0]), int(right2[1]), arrow_color)

    def _draw_tooltip(self, surface):
        """绘制美观的提示框"""
        tip_font = pygame.font.Font(FONT_NAME, 20)
        tip_text = "切换背景"
        tip_surf = tip_font.render(tip_text, True, (255, 255, 255))
        
        # 创建带圆角的提示框背景
        padding = 12
        tip_rect = tip_surf.get_rect()
        tip_rect.width += padding * 2
        tip_rect.height += padding * 2
        tip_rect.midleft = (self.rect.right + 15, self.rect.centery)
        
        # 绘制提示框背景
        tip_bg_surf = pygame.Surface((tip_rect.width, tip_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(tip_bg_surf, (0, 0, 0, 180), tip_bg_surf.get_rect(), border_radius=8)
        surface.blit(tip_bg_surf, tip_rect.topleft)
        
        # 绘制文字
        text_rect = tip_surf.get_rect(center=tip_rect.center)
        surface.blit(tip_surf, text_rect)
        
        # 绘制连接线
        pygame.draw.line(surface, (0, 0, 0, 180), 
                        (self.rect.right + 5, self.rect.centery), 
                        (tip_rect.left - 5, tip_rect.centery), 3)
    
    def _draw_preview(self, surface, next_bg_image):
        """绘制背景预览"""
        preview_size = int(self.rect.width * 0.8)
        preview_img = pygame.transform.scale(next_bg_image, (preview_size, preview_size))
        preview_rect = preview_img.get_rect(midbottom=(self.rect.centerx, self.rect.top - 15))
        # 绘制预览框背景和边框
        border_rect = preview_rect.inflate(10, 10)
        pygame.draw.rect(surface, (255, 255, 255, 200), border_rect, border_radius=12)
        pygame.draw.rect(surface, (0, 0, 0, 100), border_rect, 3, border_radius=12)
        # 绘制预览图片
        surface.blit(preview_img, preview_rect)
        # 添加"下一个"标签
        label_font = pygame.font.Font(FONT_NAME, 16)
        label_surf = label_font.render("下一个", True, (255, 255, 255))
        label_rect = label_surf.get_rect(midtop=(preview_rect.centerx, preview_rect.bottom + 5))
        # 标签背景
        label_bg_rect = label_rect.inflate(8, 4)
        pygame.draw.rect(surface, (0, 0, 0, 150), label_bg_rect, border_radius=4)
        surface.blit(label_surf, label_rect)

class TextInput:
    def __init__(self, x, y, width, height, font_size=24, text_color=BLACK, bg_color=WHITE, border_color=BLACK, max_length=20):
        self.rect = pygame.Rect(x, y, width, height)
        self.font = pygame.font.Font(FONT_NAME, font_size)
        self.text = ''
        self.text_color = text_color
        self.bg_color = bg_color
        self.border_color = border_color
        self.active = False
        self.max_length = max_length
        self.cursor_visible = True
        self.cursor_counter = 0

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
        if self.active and event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.key == pygame.K_RETURN:
                pass  # 可扩展为回车确认
            elif event.key == pygame.K_ESCAPE:
                self.active = False
            elif len(self.text) < self.max_length:
                if event.unicode.isprintable():
                    self.text += event.unicode

    def draw(self, surface):
        pygame.draw.rect(surface, self.bg_color, self.rect, border_radius=6)
        pygame.draw.rect(surface, self.border_color, self.rect, 2, border_radius=6)
        text_surf = self.font.render(self.text, True, self.text_color)
        surface.blit(text_surf, (self.rect.x + 8, self.rect.y + (self.rect.height - text_surf.get_height()) // 2))
        # 光标闪烁
        if self.active:
            self.cursor_counter += 1
            if self.cursor_counter >= 30:
                self.cursor_visible = not self.cursor_visible
                self.cursor_counter = 0
            if self.cursor_visible:
                cursor_x = self.rect.x + 8 + text_surf.get_width() + 2
                cursor_y = self.rect.y + (self.rect.height - text_surf.get_height()) // 2
                cursor_h = text_surf.get_height()
                pygame.draw.line(surface, self.text_color, (cursor_x, cursor_y), (cursor_x, cursor_y + cursor_h), 2)
        else:
            self.cursor_visible = True
            self.cursor_counter = 0

    def get_text(self):
        return self.text

    def set_text(self, text):
        self.text = text[:self.max_length]

    def enable_chinese_input(self, hwnd):
        """
        启动线程监听中文输入法内容，将其插入到输入框。
        hwnd: pygame窗口句柄
        """
        self.chinese_queue = queue.Queue()
        self._hwnd = hwnd
        self._chinese_thread = threading.Thread(target=self._listen_chinese_input, daemon=True)
        self._chinese_thread.start()

    def _listen_chinese_input(self):
        # 监听窗口消息，捕获WM_IME_CHAR
        while True:
            msg = win32gui.GetMessage(self._hwnd, 0, 0)
            if msg[1][1] == win32con.WM_IME_CHAR:
                char = chr(msg[1][2] & 0xFFFF)
                self.chinese_queue.put(char)
            win32gui.TranslateMessage(msg[1])
            win32gui.DispatchMessage(msg[1])

    def update(self):
        # 检查中文输入队列
        if hasattr(self, 'chinese_queue'):
            while not self.chinese_queue.empty():
                char = self.chinese_queue.get()
                if len(self.text) < self.max_length:
                    self.text += char

def get_pygame_hwnd():
    # 获取pygame窗口句柄
    import pygame.display
    hwnd = pygame.display.get_wm_info()['window']
    return hwnd 

class CartoonButton(Button):
    def __init__(self, x, y, width, height, text, color, icon_type=None, font_size=FONT_SIZE):
        super().__init__(x, y, width, height, text, color=color, hover_color=color, font_size=font_size)
        self.icon_type = icon_type
        self.radius = 24
        self.shadow_offset = 6
        self.text_color = (255, 255, 255)
        self.hover_scale = 1.08

        # 新增特效属性
        self.glow_intensity = 0
        self.glow_direction = 1
        self.breath_animation = 0
        self.click_ripple_time = 0
        self.click_ripple_radius = 0
        self.click_pos = None
        self.star_particles = []
        self.particle_timer = 0

    def draw(self, surface):
        # 更新动画
        self.breath_animation += 0.08
        self.particle_timer += 1

        # 呼吸灯效果（仅对开始游戏按钮）
        if self.text == "开始游戏":
            breath_scale = 1.0 + 0.05 * math.sin(self.breath_animation)
            glow_alpha = int(80 + 40 * math.sin(self.breath_animation * 1.5))
        else:
            breath_scale = 1.0
            glow_alpha = 0

        # 发光效果更新
        if self.is_hovered:
            self.glow_intensity += self.glow_direction * 8
            if self.glow_intensity >= 100:
                self.glow_intensity = 100
                self.glow_direction = -1
            elif self.glow_intensity <= 50:
                self.glow_intensity = 50
                self.glow_direction = 1
        else:
            self.glow_intensity = max(0, self.glow_intensity - 5)

        # 点击波纹效果更新
        if self.click_ripple_time > 0:
            self.click_ripple_time -= 1
            self.click_ripple_radius += 8

        # 星星粒子效果（仅对开始游戏按钮）
        if self.text == "开始游戏" and self.particle_timer % 30 == 0:
            import random
            for _ in range(2):
                self.star_particles.append({
                    'x': self.rect.centerx + random.randint(-self.rect.width//2, self.rect.width//2),
                    'y': self.rect.centery + random.randint(-self.rect.height//2, self.rect.height//2),
                    'life': 60,
                    'vx': random.uniform(-1, 1),
                    'vy': random.uniform(-2, -0.5)
                })

        # 更新粒子
        self.star_particles = [p for p in self.star_particles if p['life'] > 0]
        for particle in self.star_particles:
            particle['x'] += particle['vx']
            particle['y'] += particle['vy']
            particle['life'] -= 1

        # 计算最终矩形
        rect = self.rect.copy()
        if self.text == "开始游戏":
            # 应用呼吸效果
            rect.inflate_ip(int(rect.width * (breath_scale-1)), int(rect.height * (breath_scale-1)))
            rect.center = self.rect.center

        if self.is_hovered:
            # 悬停时放大
            rect.inflate_ip(int(rect.width * (self.hover_scale-1)), int(rect.height * (self.hover_scale-1)))
            rect.center = self.rect.center

        # 绘制发光效果
        if self.glow_intensity > 0 or glow_alpha > 0:
            glow_surface = pygame.Surface((rect.width + 40, rect.height + 40), pygame.SRCALPHA)
            glow_alpha_final = max(self.glow_intensity, glow_alpha)

            # 多层发光
            for i in range(3):
                glow_rect = pygame.Rect(20-i*5, 20-i*5, rect.width+i*10, rect.height+i*10)
                glow_color = (*self.color, glow_alpha_final // (i+1))
                pygame.draw.rect(glow_surface, glow_color, glow_rect, border_radius=self.radius+i*3)

            surface.blit(glow_surface, (rect.x-20, rect.y-20), special_flags=pygame.BLEND_ALPHA_SDL2)

        # 阴影（更柔和）
        shadow_rect = rect.copy()
        shadow_rect.x += self.shadow_offset
        shadow_rect.y += self.shadow_offset
        shadow_surface = pygame.Surface((shadow_rect.width, shadow_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(shadow_surface, (0, 0, 0, 100), (0, 0, shadow_rect.width, shadow_rect.height), border_radius=self.radius)
        surface.blit(shadow_surface, shadow_rect.topleft)

        # 渐变背景（仅对开始游戏按钮）
        if self.text == "开始游戏":
            self._draw_gradient_rect(surface, rect, self.color, (min(255, self.color[0]+30), min(255, self.color[1]+30), min(255, self.color[2]+30)))
        else:
            pygame.draw.rect(surface, self.color, rect, border_radius=self.radius)

        # 边框
        border_color = (255, 255, 255) if not self.is_hovered else (255, 255, 100)
        pygame.draw.rect(surface, border_color, rect, 4, border_radius=self.radius)

        # 点击波纹效果
        if self.click_ripple_time > 0 and self.click_pos:
            ripple_alpha = int(255 * (self.click_ripple_time / 20))
            ripple_surface = pygame.Surface((self.click_ripple_radius*2, self.click_ripple_radius*2), pygame.SRCALPHA)
            pygame.draw.circle(ripple_surface, (255, 255, 255, ripple_alpha),
                             (self.click_ripple_radius, self.click_ripple_radius),
                             self.click_ripple_radius, 3)
            surface.blit(ripple_surface, (self.click_pos[0] - self.click_ripple_radius,
                                        self.click_pos[1] - self.click_ripple_radius))

        # icon
        if self.icon_type:
            icon_center = (rect.x + 36, rect.centery)
            if self.icon_type == "smile":
                # 增强版笑脸（开始游戏按钮专用）
                if self.text == "开始游戏":
                    # 发光笑脸
                    glow_radius = 20 + int(3 * math.sin(self.breath_animation * 2))
                    glow_surface = pygame.Surface((glow_radius*2+10, glow_radius*2+10), pygame.SRCALPHA)
                    pygame.draw.circle(glow_surface, (255, 255, 0, 100), (glow_radius//2+5, glow_radius//2+5), glow_radius)
                    surface.blit(glow_surface, (icon_center[0]-glow_radius//2-5, icon_center[1]-glow_radius//2-5))

                # 主笑脸
                pygame.draw.circle(surface, (255,255,0), icon_center, 18)
                pygame.draw.circle(surface, (255,215,0), icon_center, 18, 2)  # 金色边框

                # 眼睛（更生动）
                eye_offset = 1 if self.text == "开始游戏" and int(self.breath_animation*10) % 100 < 5 else 0
                pygame.draw.circle(surface, (0,0,0), (icon_center[0]-5, icon_center[1]-2-eye_offset), 3)
                pygame.draw.circle(surface, (0,0,0), (icon_center[0]+5, icon_center[1]-2-eye_offset), 3)
                pygame.draw.circle(surface, (255,255,255), (icon_center[0]-4, icon_center[1]-3-eye_offset), 1)
                pygame.draw.circle(surface, (255,255,255), (icon_center[0]+6, icon_center[1]-3-eye_offset), 1)

                # 嘴巴（更开心的弧度）
                mouth_rect = (icon_center[0]-12, icon_center[1]-4, 24, 20)
                pygame.draw.arc(surface, (0,0,0), mouth_rect, 0.5, 2.6, 3)
            elif self.icon_type == "door":
                # 门
                pygame.draw.rect(surface, (255,140,0), (icon_center[0]-10, icon_center[1]-14, 20, 28), border_radius=6)
                pygame.draw.circle(surface, (255,255,255), (icon_center[0]+7, icon_center[1]), 2)
            elif self.icon_type == "help":
                # 问号
                pygame.draw.circle(surface, (66,165,245), icon_center, 16)
                font = pygame.font.Font(FONT_NAME, 22)
                qsurf = font.render("?", True, (255,255,255))
                qrect = qsurf.get_rect(center=icon_center)
                surface.blit(qsurf, qrect)
            elif self.icon_type == "settings":
                # 齿轮icon
                pygame.draw.circle(surface, (255,255,255), icon_center, 15, 3)
                for i in range(8):
                    angle = math.radians(i*45)
                    x1 = icon_center[0] + int(15*math.cos(angle))
                    y1 = icon_center[1] + int(15*math.sin(angle))
                    x2 = icon_center[0] + int(21*math.cos(angle))
                    y2 = icon_center[1] + int(21*math.sin(angle))
                    pygame.draw.line(surface, (255,255,255), (x1,y1), (x2,y2), 3)
                pygame.draw.circle(surface, (66,165,245), icon_center, 7)
            elif self.icon_type == "image":
                # 图片icon
                pygame.draw.rect(surface, (255,255,255), (icon_center[0]-12, icon_center[1]-10, 24, 20), 3, border_radius=5)
                pygame.draw.polygon(surface, (255,213,79), [(icon_center[0]-10,icon_center[1]+6),(icon_center[0],icon_center[1]-4),(icon_center[0]+10,icon_center[1]+6)], 0)
                pygame.draw.circle(surface, (66,165,245), (icon_center[0]-6,icon_center[1]-4), 3)
            elif self.icon_type == "back":
                # 返回箭头icon
                pygame.draw.polygon(surface, (255,255,255), [
                    (icon_center[0]-10,icon_center[1]),
                    (icon_center[0]+6,icon_center[1]-10),
                    (icon_center[0]+6,icon_center[1]-4),
                    (icon_center[0]+14,icon_center[1]-4),
                    (icon_center[0]+14,icon_center[1]+4),
                    (icon_center[0]+6,icon_center[1]+4),
                    (icon_center[0]+6,icon_center[1]+10)
                ])
            elif self.icon_type == "activity":
                # 礼物盒icon
                pygame.draw.rect(surface, (255,255,255), (icon_center[0]-10, icon_center[1]-6, 20, 14), 3, border_radius=4)
                pygame.draw.line(surface, (255,255,255), (icon_center[0], icon_center[1]-6), (icon_center[0], icon_center[1]+8), 3)
                pygame.draw.line(surface, (255,255,255), (icon_center[0]-10, icon_center[1]+2), (icon_center[0]+10, icon_center[1]+2), 3)
                # 蝴蝶结
                pygame.draw.arc(surface, (255,213,79), (icon_center[0]-10, icon_center[1]-12, 10, 10), 0.8, 2.4, 2)
                pygame.draw.arc(surface, (255,213,79), (icon_center[0], icon_center[1]-12, 10, 10), 0.8, 2.4, 2)
            elif self.icon_type == "shop":
                # 购物袋icon
                pygame.draw.rect(surface, (255,255,255), (icon_center[0]-9, icon_center[1]-8, 18, 16), 3, border_radius=4)
                pygame.draw.arc(surface, (255,255,255), (icon_center[0]-9, icon_center[1]-14, 18, 12), 3.14, 0, 2)
            elif self.icon_type == "backpack":
                # 背包icon
                pygame.draw.rect(surface, (255,255,255), (icon_center[0]-9, icon_center[1]-4, 18, 14), 3, border_radius=5)
                pygame.draw.circle(surface, (255,255,255), (icon_center[0], icon_center[1]-4), 8, 3)
            elif self.icon_type == "music":
                # 音乐符号
                # 音符本体
                pygame.draw.ellipse(surface, (255,255,255), (icon_center[0]-8, icon_center[1]+5, 12, 8))
                pygame.draw.ellipse(surface, (255,255,255), (icon_center[0]-3, icon_center[1], 12, 8))
                # 符尾
                pygame.draw.line(surface, (255,255,255), (icon_center[0]+9, icon_center[1]+4), (icon_center[0]+9, icon_center[1]-10), 3)
                pygame.draw.line(surface, (255,255,255), (icon_center[0]+4, icon_center[1]+9), (icon_center[0]+4, icon_center[1]-5), 3)
                # 音波
                for i, r in enumerate([18, 22, 26]):
                    alpha = 150 - i * 30
                    wave_surface = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
                    pygame.draw.arc(wave_surface, (255,255,255,alpha), (0, 0, r*2, r*2), -0.5, 0.5, 2)
                    surface.blit(wave_surface, (icon_center[0] + 5 - r, icon_center[1] - r))
            elif self.icon_type == "group":
                # 双人模式图标
                # 第一个人
                pygame.draw.circle(surface, (255,255,255), (icon_center[0]-6, icon_center[1]-6), 6)
                pygame.draw.rect(surface, (255,255,255), (icon_center[0]-10, icon_center[1], 8, 12), border_radius=4)
                # 第二个人
                pygame.draw.circle(surface, (255,255,255), (icon_center[0]+6, icon_center[1]-6), 6)
                pygame.draw.rect(surface, (255,255,255), (icon_center[0]+2, icon_center[1], 8, 12), border_radius=4)
            elif self.icon_type == "volume":
                # 音量图标
                # 扬声器
                pygame.draw.polygon(surface, (255,255,255), [
                    (icon_center[0]-12, icon_center[1]-6),
                    (icon_center[0]-8, icon_center[1]-6),
                    (icon_center[0]-2, icon_center[1]-12),
                    (icon_center[0]+4, icon_center[1]-12),
                    (icon_center[0]+4, icon_center[1]+12),
                    (icon_center[0]-2, icon_center[1]+12),
                    (icon_center[0]-8, icon_center[1]+6),
                    (icon_center[0]-12, icon_center[1]+6)
                ])
                # 音波
                for i, (radius, alpha) in enumerate([(16, 150), (20, 120), (24, 90)]):
                    wave_surface = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
                    pygame.draw.arc(wave_surface, (255,255,255,alpha), (0, 0, radius*2, radius*2), -0.5, 0.5, 2)
                    surface.blit(wave_surface, (icon_center[0] + 2 - radius, icon_center[1] - radius))
        # 绘制星星粒子效果
        for particle in self.star_particles:
            alpha = int(255 * (particle['life'] / 60))
            star_surface = pygame.Surface((8, 8), pygame.SRCALPHA)
            # 绘制小星星
            points = []
            for i in range(5):
                angle = math.radians(i * 72 - 90)
                x = 4 + 3 * math.cos(angle)
                y = 4 + 3 * math.sin(angle)
                points.append((x, y))
                angle = math.radians(i * 72 - 90 + 36)
                x = 4 + 1.5 * math.cos(angle)
                y = 4 + 1.5 * math.sin(angle)
                points.append((x, y))
            pygame.draw.polygon(star_surface, (255, 255, 100, alpha), points)
            surface.blit(star_surface, (particle['x']-4, particle['y']-4))

        # 文字（带阴影效果）
        if self.text:
            if self.text == "开始游戏":
                # 文字阴影
                shadow_surface = self.font.render(self.text, True, (0, 0, 0))
                shadow_rect = shadow_surface.get_rect(midleft=(rect.x + 66, rect.centery + 2))
                surface.blit(shadow_surface, shadow_rect)
                # 主文字
                text_surface = self.font.render(self.text, True, self.text_color)
                text_rect = text_surface.get_rect(midleft=(rect.x + 64, rect.centery))
                surface.blit(text_surface, text_rect)
            elif rect.width <= 80 and rect.height <= 35:  # 只对小按钮居中显示
                # 对于小按钮，文字居中显示
                text_surface = self.font.render(self.text, True, self.text_color)
                text_rect = text_surface.get_rect(center=rect.center)
                surface.blit(text_surface, text_rect)
            else:
                # 对于其他按钮，保持原有的偏左显示（为图标留空间）
                text_surface = self.font.render(self.text, True, self.text_color)
                text_rect = text_surface.get_rect(midleft=(rect.x + 64, rect.centery))
                surface.blit(text_surface, text_rect)

    def _draw_gradient_rect(self, surface, rect, color1, color2):
        """绘制垂直渐变矩形"""
        for y in range(rect.height):
            blend = y / rect.height
            color = tuple(int(color1[i] * (1-blend) + color2[i] * blend) for i in range(3))
            pygame.draw.line(surface, color, (rect.x, rect.y + y), (rect.x + rect.width, rect.y + y))

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.is_hovered and event.button == 1:
                self.is_pressed = True
                # 启动点击波纹效果
                self.click_pos = event.pos
                self.click_ripple_time = 20
                self.click_ripple_radius = 0
                return True  # 立即返回True，提升点击体验
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self.is_pressed = False
        return False