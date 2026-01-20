# -*- coding: utf-8 -*-
import pygame
import math
from .constants import GRID_SIZE, WINDOW_WIDTH, WINDOW_HEIGHT, SNAKE_SPEED
from .player import player_data
from .shop import SKINS
from .image_skins import image_skin_manager

def get_hexagon_points(center_x, center_y, radius):
    """计算六边形的顶点坐标"""
    points = []
    for i in range(6):
        # 旋转30度，让六边形平顶
        angle_deg = 60 * i + 30
        angle_rad = math.pi / 180 * angle_deg
        points.append((center_x + radius * math.cos(angle_rad),
                       center_y + radius * math.sin(angle_rad)))
    return points

def get_pentagram_points(center_x, center_y, outer_radius):
    """计算五角星的顶点坐标"""
    points = []
    inner_radius = outer_radius * 0.5  # 内外半径比例，可调整
    for i in range(10):
        if i % 2 == 0:  # 外顶点
            radius = outer_radius
            angle_deg = 36 * i - 90
        else:  # 内顶点
            radius = inner_radius
            angle_deg = 36 * i - 90
        angle_rad = math.pi / 180 * angle_deg
        points.append((center_x + radius * math.cos(angle_rad),
                       center_y + radius * math.sin(angle_rad)))
    return points

class Snake:
    def __init__(self, allow_cross_self=False):
        self.length = 1
        self.positions = [((WINDOW_WIDTH // GRID_SIZE) // 2, (WINDOW_HEIGHT // GRID_SIZE) // 2)]
        self.direction = (1, 0)
        self.next_direction = (1, 0)
        self.score = 0
        self.last_move_time = 0
        self.speed = 1000 / SNAKE_SPEED
        self.animation_time = 0
        self.allow_cross_self = allow_cross_self

    def get_head_position(self):
        return self.positions[0]

    def update(self, current_time):
        self.animation_time = current_time
        # 根据速度移动蛇
        if current_time - self.last_move_time > self.speed:
            self.last_move_time = current_time
            if not self.move():
                return False # 移动失败（撞到自己）
        return True

    def move(self):
        self.direction = self.next_direction
        cur = self.get_head_position()
        x, y = self.direction
        # 计算新位置，实现穿墙效果
        new_x = (cur[0] + x) % (WINDOW_WIDTH // GRID_SIZE)
        new_y = (cur[1] + y) % (WINDOW_HEIGHT // GRID_SIZE)
        new = (new_x, new_y)
        if not self.allow_cross_self:
            # 检查是否撞到自己
            if new in self.positions:
                if len(self.positions) > 2 and new in self.positions[1:]:
                    return False
        # 允许穿过自己，直接插入新头部
        self.positions.insert(0, new)
        if len(self.positions) > self.length:
            self.positions.pop()
        return True

    def draw(self, surface):
        skin_id = player_data.get_equipped_skin()
        t = self.animation_time / 1000.0
        direction = self.direction
        perp = (-direction[1], direction[0])
        wave_amp = GRID_SIZE * 0.09

        # 检查是否为图片皮肤
        if image_skin_manager.is_image_skin(skin_id):
            # 使用图片皮肤绘制
            for i, pos in enumerate(reversed(self.positions)):
                is_head = (i == len(self.positions) - 1)
                wave_phase = t * 12 + i * 0.6
                offset_x = perp[0] * math.sin(wave_phase) * wave_amp
                offset_y = perp[1] * math.sin(wave_phase) * wave_amp
                center_x = pos[0] * GRID_SIZE + GRID_SIZE // 2 + offset_x
                center_y = pos[1] * GRID_SIZE + GRID_SIZE // 2 + offset_y
                
                # 计算每段身体的移动方向
                if is_head:
                    # 头部使用当前方向
                    segment_direction = self.direction
                else:
                    # 身体段使用从当前位置到下一段位置的方向
                    current_index = len(self.positions) - 1 - i
                    next_index = current_index + 1
                    if next_index < len(self.positions):
                        next_pos = self.positions[next_index]
                        dx = next_pos[0] - pos[0]
                        dy = next_pos[1] - pos[1]
                        # 处理穿墙情况
                        if abs(dx) > 1:  # 穿墙
                            dx = -1 if dx > 0 else 1
                        if abs(dy) > 1:  # 穿墙
                            dy = -1 if dy > 0 else 1
                        segment_direction = (dx, dy)
                    else:
                        # 最后一段身体，使用从当前位置到前一段位置的方向（反向）
                        prev_index = current_index - 1
                        if prev_index >= 0:
                            prev_pos = self.positions[prev_index]
                            dx = pos[0] - prev_pos[0]
                            dy = pos[1] - prev_pos[1]
                            # 处理穿墙情况
                            if abs(dx) > 1:  # 穿墙
                                dx = -1 if dx > 0 else 1
                            if abs(dy) > 1:  # 穿墙
                                dy = -1 if dy > 0 else 1
                            segment_direction = (dx, dy)
                        else:
                            # 如果只有一个身体段，使用蛇头方向
                            segment_direction = self.direction
                
                # 尝试绘制图片皮肤，如果失败则回退到默认皮肤
                if not image_skin_manager.draw_image_segment(surface, (center_x, center_y), segment_direction, skin_id, is_head):
                    # 回退到默认皮肤
                    skin_info = SKINS.get("default_rectangle")
                    base_color, dark_color = skin_info["colors"]
                    shape = skin_info.get("shape", "rectangle")
                    self.draw_segment(surface, pos, i, base_color, dark_color, shape, is_head)
        else:
            # 使用原有的颜色皮肤系统
            skin_info = SKINS.get(skin_id, SKINS.get("default_rectangle"))
            base_color, dark_color = skin_info["colors"]
            shape = skin_info.get("shape", "rectangle")

            for i, pos in enumerate(reversed(self.positions)):
                is_head = (i == len(self.positions) - 1)
                self.draw_segment(surface, pos, i, base_color, dark_color, shape, is_head)
    
    def draw_segment(self, surface, pos, index, base_color, dark_color, shape, is_head):
        center_x = pos[0] * GRID_SIZE + GRID_SIZE // 2
        center_y = pos[1] * GRID_SIZE + GRID_SIZE // 2
        
        t = self.animation_time / 1000.0
        direction = self.direction
        perp = (-direction[1], direction[0])
        wave_amp = GRID_SIZE * 0.09
        wave_phase = t * 12 + index * 0.6
        offset_x = perp[0] * math.sin(wave_phase) * wave_amp
        offset_y = perp[1] * math.sin(wave_phase) * wave_amp
        center_x += offset_x
        center_y += offset_y

        radius = GRID_SIZE // 2 * 0.9

        # --- 绘制光晕 (保留) ---
        # breath = 0.5 + 0.5 * math.sin(t * 2)
        # outer_glow_surface = pygame.Surface((radius * 3.5, radius * 3.5), pygame.SRCALPHA)
        # outer_alpha = int((40 + 180 * breath) * 0.1)
        # pygame.draw.circle(outer_glow_surface, (*base_color, outer_alpha), outer_glow_surface.get_rect().center, int(radius * 1.7))
        # surface.blit(outer_glow_surface, (center_x - radius * 1.75, center_y - radius * 1.75), special_flags=pygame.BLEND_RGBA_ADD)

        # inner_glow_surface = pygame.Surface((radius * 2.2, radius * 2.2), pygame.SRCALPHA)
        # inner_alpha = int((80 + 100 * breath) * 0.1)
        # pygame.draw.circle(inner_glow_surface, (*base_color, inner_alpha), inner_glow_surface.get_rect().center, int(radius * 1.1))
        # surface.blit(inner_glow_surface, (center_x - radius * 1.1, center_y - radius * 1.1), special_flags=pygame.BLEND_RGBA_ADD)
        # --- 光晕结束 ---

        if shape == "circle":
            self.draw_circle_segment(surface, center_x, center_y, radius, base_color, dark_color)
        elif shape == "rectangle":
            self.draw_rectangle_segment(surface, center_x, center_y, radius, base_color, dark_color)
        elif shape == "hexagon":
            self.draw_hexagon_segment(surface, center_x, center_y, radius, base_color, dark_color)
        elif shape == "pentagram":
            self.draw_pentagram_segment(surface, center_x, center_y, radius, base_color, dark_color)
        elif shape == "fan":
            self.draw_fan_segment(surface, center_x, center_y, radius, base_color, dark_color, self.direction)
        elif shape == "heart":
            self.draw_heart_segment(surface, center_x, center_y, radius, base_color, dark_color)
        elif shape == "leaf":
            self.draw_leaf_segment(surface, center_x, center_y, radius, base_color, dark_color, self.direction)
        elif shape == "water_drop":
            self.draw_water_drop_segment(surface, center_x, center_y, radius, base_color, dark_color, self.direction)
        elif shape == "music_note":
            self.draw_music_note_segment(surface, center_x, center_y, radius, base_color, dark_color, self.direction)
        elif shape == "lightning_bolt":
            self.draw_lightning_bolt_segment(surface, center_x, center_y, radius, base_color, dark_color, self.direction)
        elif shape == "crown":
            self.draw_crown_segment(surface, center_x, center_y, radius, base_color, dark_color, self.direction)
        elif shape == "arrow":
            self.draw_arrow_segment(surface, center_x, center_y, radius, base_color, dark_color, self.direction)
        else: # rectangle/default
            self.draw_rectangle_segment(surface, center_x, center_y, radius, base_color, dark_color)

        if is_head:
            self.draw_eyes(surface, center_x, center_y, radius)

    def draw_circle_segment(self, surface, center_x, center_y, radius, base_color, dark_color):
        pygame.draw.circle(surface, dark_color, (center_x, center_y), radius)
        pygame.draw.circle(surface, base_color, (center_x, center_y), radius * 0.85)
        highlight_radius = radius * 0.2
        highlight_center = (center_x - radius * 0.4, center_y - radius * 0.4)
        pygame.draw.circle(surface, (255, 255, 255, 180), highlight_center, highlight_radius)

    def draw_rectangle_segment(self, surface, center_x, center_y, radius, base_color, dark_color):
        rect_size = radius * 2
        rect = pygame.Rect(center_x - radius, center_y - radius, rect_size, rect_size)
        pygame.draw.rect(surface, dark_color, rect, border_radius=int(radius * 0.2))
        pygame.draw.rect(surface, base_color, rect.inflate(-rect_size*0.15, -rect_size*0.15), border_radius=int(radius * 0.15))
        highlight_rect = pygame.Rect(0, 0, rect_size * 0.3, rect_size * 0.3)
        highlight_rect.topleft = (rect.left + rect_size * 0.1, rect.top + rect_size * 0.1)
        pygame.draw.rect(surface, (255, 255, 255, 90), highlight_rect, border_radius=int(radius * 0.05))

    def draw_hexagon_segment(self, surface, center_x, center_y, radius, base_color, dark_color):
        points = get_hexagon_points(center_x, center_y, radius)
        pygame.draw.polygon(surface, dark_color, points)
        inner_points = get_hexagon_points(center_x, center_y, radius * 0.85)
        pygame.draw.polygon(surface, base_color, inner_points)
        # Simple highlight for hexagon
        highlight_center = (center_x - radius * 0.3, center_y - radius * 0.3)
        pygame.draw.circle(surface, (255, 255, 255, 90), highlight_center, radius * 0.2)

    def draw_pentagram_segment(self, surface, center_x, center_y, radius, base_color, dark_color):
        points = get_pentagram_points(center_x, center_y, radius)
        pygame.draw.polygon(surface, dark_color, points)
        inner_points = get_pentagram_points(center_x, center_y, radius * 0.85)
        pygame.draw.polygon(surface, base_color, inner_points)
        # Simple highlight for pentagram
        highlight_center = (center_x - radius * 0.3, center_y - radius * 0.3)
        pygame.draw.circle(surface, (255, 255, 255, 90), highlight_center, radius * 0.2)

    def draw_fan_segment(self, surface, center_x, center_y, radius, base_color, dark_color, direction):
        # Determine fan orientation based on snake's direction
        angle = math.atan2(-direction[1], direction[0]) # Angle in radians
        
        # Draw the fan surface (arc)
        rect = pygame.Rect(center_x - radius, center_y - radius, radius * 2, radius * 2)
        pygame.draw.arc(surface, base_color, rect, angle - math.pi / 2.5, angle + math.pi / 2.5, int(radius))

        # Draw the fan ribs
        num_ribs = 5
        for i in range(num_ribs):
            rib_angle = angle - math.pi / 2.5 + (i * (math.pi / 2.5 * 2) / (num_ribs - 1))
            start_pos = (center_x, center_y)
            end_pos = (center_x + radius * math.cos(rib_angle), center_y - radius * math.sin(rib_angle))
            pygame.draw.line(surface, dark_color, start_pos, end_pos, 2)

    def draw_heart_segment(self, surface, center_x, center_y, radius, base_color, dark_color):
        # Scale factor to make the heart fit well within the grid
        s = radius * 0.9

        # Points for the triangle part of the heart
        p1 = (center_x - s, center_y)
        p2 = (center_x + s, center_y)
        p3 = (center_x, center_y + s)

        # Draw the main shape
        pygame.draw.circle(surface, dark_color, (center_x - s / 2, center_y - s * 0.2), s / 1.8)
        pygame.draw.circle(surface, dark_color, (center_x + s / 2, center_y - s * 0.2), s / 1.8)
        pygame.draw.polygon(surface, dark_color, [p1, p2, p3])

        # Draw the inner, lighter part
        pygame.draw.circle(surface, base_color, (center_x - s / 2, center_y - s * 0.2), s / 2.2)
        pygame.draw.circle(surface, base_color, (center_x + s / 2, center_y - s * 0.2), s / 2.2)
        inner_s = s * 0.85
        p1_inner = (center_x - inner_s, center_y)
        p2_inner = (center_x + inner_s, center_y)
        p3_inner = (center_x, center_y + inner_s)
        # We need to adjust the inner polygon to align with the circles
        adjusted_p1 = (p1[0] + s*0.1, p1[1] - s*0.2)
        adjusted_p2 = (p2[0] - s*0.1, p2[1] - s*0.2)
        adjusted_p3 = (p3[0], p3[1] - s*0.2)
        pygame.draw.polygon(surface, base_color, [adjusted_p1, adjusted_p2, adjusted_p3])

    def draw_leaf_segment(self, surface, center_x, center_y, radius, base_color, dark_color, direction):
        # Create a temporary surface to draw the leaf on, for easier rotation
        leaf_surface = pygame.Surface((radius * 2, radius * 2.5), pygame.SRCALPHA)
        w, h = leaf_surface.get_size()

        # Define points for a realistic leaf polygon
        leaf_poly = [
            (w * 0.5, h),           # Stem bottom
            (w * 0.2, h * 0.75),
            (w * 0.3, h * 0.4),
            (w * 0.5, h * 0.0),      # Tip
            (w * 0.7, h * 0.4),
            (w * 0.8, h * 0.75),
        ]
        
        # Draw the main leaf shape
        pygame.draw.polygon(leaf_surface, base_color, leaf_poly)
        
        # Draw the veins to make it more realistic
        pygame.draw.line(leaf_surface, dark_color, (w * 0.5, h), (w * 0.5, h * 0.1), 2) # Center vein
        pygame.draw.line(leaf_surface, dark_color, (w * 0.5, h * 0.7), (w * 0.3, h * 0.5), 1)
        pygame.draw.line(leaf_surface, dark_color, (w * 0.5, h * 0.7), (w * 0.7, h * 0.5), 1)
        pygame.draw.line(leaf_surface, dark_color, (w * 0.5, h * 0.4), (w * 0.35, h * 0.2), 1)
        pygame.draw.line(leaf_surface, dark_color, (w * 0.5, h * 0.4), (w * 0.65, h * 0.2), 1)

        # Rotate the leaf surface based on the snake's direction
        angle = math.degrees(math.atan2(-direction[1], direction[0])) - 90
        rotated_leaf = pygame.transform.rotate(leaf_surface, angle)
        
        # Position the rotated leaf on the main screen
        new_rect = rotated_leaf.get_rect(center=(center_x, center_y))
        surface.blit(rotated_leaf, new_rect.topleft)

    def draw_water_drop_segment(self, surface, center_x, center_y, radius, base_color, dark_color, direction):
        # Create a temporary surface for the water drop to allow for rotation
        drop_surface = pygame.Surface((radius * 2, radius * 2.5), pygame.SRCALPHA)
        w, h = drop_surface.get_size()

        # Draw the main drop shape (circle + triangle)
        pygame.draw.circle(drop_surface, base_color, (w / 2, h * 0.4), w / 2)
        poly_points = [(w / 2, h), (0, h * 0.4), (w, h * 0.4)]
        pygame.draw.polygon(drop_surface, base_color, poly_points)
        
        # Draw a simple highlight
        pygame.draw.circle(drop_surface, (255, 255, 255, 180), (w * 0.4, h * 0.3), w * 0.15)
        
        # Rotate and blit
        angle = math.degrees(math.atan2(-direction[1], direction[0])) - 90
        rotated_drop = pygame.transform.rotate(drop_surface, angle)
        new_rect = rotated_drop.get_rect(center=(center_x, center_y))
        surface.blit(rotated_drop, new_rect.topleft)

    def draw_music_note_segment(self, surface, center_x, center_y, radius, base_color, dark_color, direction):
        # Create a temporary surface to draw the note on for rotation
        note_surface = pygame.Surface((radius * 2.5, radius * 3), pygame.SRCALPHA)
        w, h = note_surface.get_size()
        
        # Center of the drawing area
        cx, cy = w / 2, h / 2

        # Note head
        head_radius = radius * 0.6
        pygame.draw.ellipse(note_surface, base_color, (cx - head_radius, cy, head_radius * 2, head_radius * 1.5))

        # Stem
        stem_height = radius * 1.8
        stem_width = radius * 0.25
        stem_x = cx + head_radius * 0.8
        stem_y = cy + head_radius * 0.75 - stem_height
        pygame.draw.rect(note_surface, dark_color, (stem_x, stem_y, stem_width, stem_height))

        # Flag (for an eighth note)
        flag_points = [
            (stem_x + stem_width, stem_y),
            (stem_x + stem_width + radius, stem_y + radius * 0.5),
            (stem_x + stem_width + radius * 0.5, stem_y + radius),
            (stem_x + stem_width, stem_y + radius * 0.2)
        ]
        pygame.draw.polygon(note_surface, dark_color, flag_points)

        # Rotate the note surface based on the snake's direction
        angle = math.degrees(math.atan2(-direction[1], direction[0])) - 90
        rotated_note = pygame.transform.rotate(note_surface, angle)
        
        # Position the rotated note on the main screen
        new_rect = rotated_note.get_rect(center=(center_x, center_y))
        surface.blit(rotated_note, new_rect.topleft)

    def draw_lightning_bolt_segment(self, surface, center_x, center_y, radius, base_color, dark_color, direction):
        # Create a temporary surface to draw the lightning bolt on for rotation
        bolt_surface = pygame.Surface((radius * 2.5, radius * 2.5), pygame.SRCALPHA)
        w, h = bolt_surface.get_size()
        
        # Define a more classic, sharp lightning bolt shape
        points = [
            (w * 0.5, 0),         # Top tip
            (w * 0.2, h * 0.5),   # Left mid
            (w * 0.4, h * 0.5),   # Inner left
            (w * 0.3, h),         # Bottom tip
            (w * 0.8, h * 0.4),   # Right mid
            (w * 0.6, h * 0.4),   # Inner right
        ]
        
        # Draw the main bolt shape with a darker border
        pygame.draw.polygon(bolt_surface, dark_color, points)
        
        # Scale the polygon toward the center to create an inner shape
        cx, cy = w / 2, h / 2
        inner_points = [(cx + (p[0] - cx) * 0.7, cy + (p[1] - cy) * 0.7) for p in points]
        pygame.draw.polygon(bolt_surface, base_color, inner_points)

        # Rotate the bolt surface based on the snake's direction
        angle = math.degrees(math.atan2(-direction[1], direction[0])) - 90
        rotated_bolt = pygame.transform.rotate(bolt_surface, angle)
        
        # Position the rotated bolt on the main screen
        new_rect = rotated_bolt.get_rect(center=(center_x, center_y))
        surface.blit(rotated_bolt, new_rect.topleft)

    def draw_crown_segment(self, surface, center_x, center_y, radius, base_color, dark_color, direction):
        # 绘制一个清晰、经典的皇冠图标，不旋转
        crown_surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        w, h = crown_surface.get_size()
        cx, cy = w / 2, h / 2

        # 1. 绘制底座
        base_y = cy + radius * 0.2
        base_rect = pygame.Rect(cx - radius * 0.9, base_y, radius * 1.8, radius * 0.6)
        pygame.draw.rect(crown_surface, dark_color, base_rect, border_radius=3)
        pygame.draw.rect(crown_surface, base_color, base_rect.inflate(-4, -4), border_radius=3)

        # 2. 绘制三个尖角
        tip_y = cy - radius
        # 中间尖角
        mid_tip_points = [(cx, tip_y), (cx - radius * 0.3, base_y), (cx + radius * 0.3, base_y)]
        pygame.draw.polygon(crown_surface, dark_color, mid_tip_points)
        pygame.draw.polygon(crown_surface, base_color, [(cx, tip_y + 4), (cx - radius * 0.2, base_y), (cx + radius * 0.2, base_y)])
        
        # 两侧尖角
        left_tip_points = [(cx - radius * 0.7, tip_y + radius*0.3), (cx - radius, base_y), (cx - radius * 0.4, base_y)]
        right_tip_points = [(cx + radius * 0.7, tip_y + radius*0.3), (cx + radius, base_y), (cx + radius * 0.4, base_y)]
        pygame.draw.polygon(crown_surface, dark_color, left_tip_points)
        pygame.draw.polygon(crown_surface, base_color, [(cx - radius * 0.7, tip_y + radius*0.3 + 3), (cx - radius*0.9, base_y), (cx - radius*0.5, base_y)])
        pygame.draw.polygon(crown_surface, dark_color, right_tip_points)
        pygame.draw.polygon(crown_surface, base_color, [(cx + radius * 0.7, tip_y + radius*0.3 + 3), (cx + radius*0.9, base_y), (cx + radius*0.5, base_y)])
        
        # 3. 绘制宝石
        # 尖角宝石
        pygame.draw.circle(crown_surface, (255, 0, 0), (cx, tip_y), radius * 0.18)
        pygame.draw.circle(crown_surface, (0, 0, 255), (cx - radius * 0.7, tip_y + radius*0.3), radius * 0.15)
        pygame.draw.circle(crown_surface, (0, 0, 255), (cx + radius * 0.7, tip_y + radius*0.3), radius * 0.15)
        # 底座宝石
        pygame.draw.circle(crown_surface, (0, 255, 0), (cx, base_y + radius * 0.3), radius * 0.2)
        pygame.draw.circle(crown_surface, (255,255,255,150), (cx-radius*0.05, base_y + radius*0.25), radius*0.08)


        # 将皇冠绘制到主屏幕，不旋转
        new_rect = crown_surface.get_rect(center=(center_x, center_y))
        surface.blit(crown_surface, new_rect.topleft)

    def draw_arrow_segment(self, surface, center_x, center_y, radius, base_color, dark_color, direction):
        # 创建一个临时表面用于旋转
        arrow_surface = pygame.Surface((radius * 2.2, radius * 2.2), pygame.SRCALPHA)
        w, h = arrow_surface.get_size()
        cx, cy = w / 2, h / 2
        # 箭头三角形
        tip = (cx, cy - radius * 0.95)
        left = (cx - radius * 0.6, cy + radius * 0.5)
        right = (cx + radius * 0.6, cy + radius * 0.5)
        pygame.draw.polygon(arrow_surface, dark_color, [tip, left, right])
        pygame.draw.polygon(arrow_surface, base_color, [ (cx, cy - radius * 0.85), (cx - radius * 0.45, cy + radius * 0.4), (cx + radius * 0.45, cy + radius * 0.4)])
        # 箭尾
        tail_rect = pygame.Rect(cx - radius * 0.18, cy + radius * 0.2, radius * 0.36, radius * 0.7)
        pygame.draw.rect(arrow_surface, dark_color, tail_rect)
        pygame.draw.rect(arrow_surface, base_color, tail_rect.inflate(-radius*0.18, -radius*0.18))
        # 高光
        pygame.draw.polygon(arrow_surface, (255,255,255,90), [ (cx, cy - radius * 0.7), (cx - radius * 0.15, cy), (cx + radius * 0.15, cy)])
        # 旋转
        angle = math.degrees(math.atan2(-direction[1], direction[0])) - 90
        rotated_arrow = pygame.transform.rotate(arrow_surface, angle)
        new_rect = rotated_arrow.get_rect(center=(center_x, center_y))
        surface.blit(rotated_arrow, new_rect.topleft)

    def draw_eyes(self, surface, center_x, center_y, radius):
        dir_x, dir_y = self.direction
        eye_size = max(2, radius * 0.15)
        eye_forward_offset = radius * 0.3
        eye_side_offset = radius * 0.35
        p_dir_x, p_dir_y = -dir_y, dir_x
        
        eye1_pos = (
            center_x + dir_x * eye_forward_offset + p_dir_x * eye_side_offset,
            center_y + dir_y * eye_forward_offset + p_dir_y * eye_side_offset
        )
        eye2_pos = (
            center_x + dir_x * eye_forward_offset - p_dir_x * eye_side_offset,
            center_y + dir_y * eye_forward_offset - p_dir_y * eye_side_offset
        )

        pygame.draw.circle(surface, (0, 0, 0), eye1_pos, eye_size)
        pygame.draw.circle(surface, (255, 255, 255), (eye1_pos[0] + 1, eye1_pos[1] + 1), eye_size * 0.3)
        pygame.draw.circle(surface, (0, 0, 0), eye2_pos, eye_size)
        pygame.draw.circle(surface, (255, 255, 255), (eye2_pos[0] + 1, eye2_pos[1] + 1), eye_size * 0.3)

    def change_direction(self, new_direction):
        # 如果上一个方向指令还未执行，则忽略新的指令
        if self.direction != self.next_direction:
            return
        # 避免180度转身
        if len(self.positions) > 1 and (new_direction[0] * -1, new_direction[1] * -1) == self.direction:
            return
        self.next_direction = new_direction

    def grow(self, score_increase=10):
        self.length += 1
        self.score += score_increase

    def move_left(self):
        self.change_direction((-1, 0))

    def move_right(self):
        self.change_direction((1, 0))

    def move_up(self):
        self.change_direction((0, -1))

    def move_down(self):
        self.change_direction((0, 1)) 