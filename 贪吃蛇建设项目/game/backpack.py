import pygame
import math
from .constants import WINDOW_WIDTH, WINDOW_HEIGHT, WHITE, GOLD, BLACK, FONT_NAME, BUTTON_COLOR, GRID_SIZE
from .player import player_data
from .shop import SKINS, CategoryToggleButton # 导入分类切换按钮
from .ui_elements import CartoonButton, Button, Dropdown
from .snake import get_hexagon_points, get_pentagram_points
from .image_skins import image_skin_manager

class BackpackMenu:
    def __init__(self, screen, game_controller):
        self.screen = screen
        self.game_controller = game_controller
        self.font = pygame.font.Font(FONT_NAME, 40)
        self.small_font = pygame.font.Font(FONT_NAME, 20)
        self.running = True
        self.scroll_y = 0
        self.skin_rects = {}
        # 鼠标拖拽相关变量
        self.is_dragging = False
        self.drag_start_y = 0
        self.drag_start_offset = 0
        # 分类切换按钮
        self.category_button = CategoryToggleButton(50, 50, 200, 40)
        self.back_button = CartoonButton(
            WINDOW_WIDTH // 2 - 100,
            WINDOW_HEIGHT - 70,
            200, 50, "返回", color=(120, 200, 120), icon_type="back", font_size=30
        )
        # 动态生成形状筛选Dropdown（只包含玩家已拥有的皮肤类型）
        all_shapes = set()
        for skin_id in player_data.get_purchased_skins():
            if skin_id in SKINS and 'shape' in SKINS[skin_id]:
                all_shapes.add(SKINS[skin_id]['shape'])
        # shape_map可补充中文名
        default_shape_map = {
            "rectangle": "方形",
            "circle": "圆形",
            "pentagram": "五角星",
            "fan": "扇形",
            "heart": "爱心",
            "leaf": "叶子",
            "water_drop": "水滴",
            "music_note": "音符",
            "lightning_bolt": "闪电",
            "crown": "皇冠",
            "arrow": "箭头",
            "nebula": "星云"
        }
        self.shape_order = sorted(all_shapes)
        self.shape_map = {k: default_shape_map.get(k, k) for k in self.shape_order}
        shape_options = ["不筛选"] + [self.shape_map[s] for s in self.shape_order]
        self.shape_dropdown = Dropdown(270, 50, 180, 40, shape_options, selected=None)
        self.shape_filter = None

    def run(self):
        self.running = True
        self.skin_rects = {}
        while self.running:
            self.handle_events()
            self.draw()

    def handle_events(self):
        for event in pygame.event.get():
            # 优先处理下拉框滚动：只有下拉框展开时才传递滚轮事件
            if not self.category_button.is_image_mode:
                if event.type == pygame.MOUSEWHEEL and self.shape_dropdown.is_open:
                    if self.shape_dropdown.handle_event(event):
                        continue  # 已处理，不再下滑背包
                else:
                    self.shape_dropdown.handle_event(event)
            if event.type == pygame.QUIT:
                self.running = False
                self.game_controller.running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False # Go back to main menu
            # 处理分类按钮点击
            if self.category_button.handle_event(event):
                self.scroll_y = 0  # 重置滚动位置
                self.skin_rects.clear()  # 清空皮肤矩形，强制重新生成
                self.shape_filter = None
                self.shape_dropdown.selected = None
            # 处理形状筛选下拉框选择（仅颜色皮肤模式）
            if not self.category_button.is_image_mode:
                if self.shape_dropdown.selected == "不筛选" or not self.shape_dropdown.selected:
                    self.shape_filter = None
                else:
                    try:
                        idx = [self.shape_map[s] for s in self.shape_order].index(self.shape_dropdown.selected)
                        self.shape_filter = self.shape_order[idx]
                    except ValueError:
                        self.shape_filter = None
            if self.back_button.handle_event(event):
                self.running = False
                return
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1: # Left click
                    # 检查是否点击了皮肤
                    for skin_id, rect in self.skin_rects.items():
                        if rect.collidepoint(event.pos):
                            player_data.equip_skin(skin_id)
                            self.game_controller.reload_skin_audio()
                            return
                    # 检查是否点击了滚动条
                    purchased_skins = self.get_filtered_purchased_skins()
                    cols = 4
                    padding = 40
                    cell_size = (WINDOW_WIDTH - padding * (cols + 1)) // cols
                    item_height = cell_size + 40
                    content_height = math.ceil(len(purchased_skins) / cols) * (item_height + padding)
                    max_scroll = content_height - (WINDOW_HEIGHT - 200)
                    if max_scroll > 0:
                        scrollbar_rect = pygame.Rect(WINDOW_WIDTH - 25, 100, 15, WINDOW_HEIGHT - 200)
                        if scrollbar_rect.collidepoint(event.pos):
                            click_ratio = (event.pos[1] - 100) / (WINDOW_HEIGHT - 200)
                            self.scroll_y = -click_ratio * max_scroll
                            return
                    # 如果没有点击皮肤或滚动条，开始拖拽
                    self.is_dragging = True
                    self.drag_start_y = event.pos[1]
                    self.drag_start_offset = self.scroll_y
                elif event.button == 4: # Scroll up
                    self.scroll_y = min(self.scroll_y + 40, 0)
                elif event.button == 5: # Scroll down
                    purchased_skins = self.get_filtered_purchased_skins()
                    cols = 4
                    padding = 40
                    cell_size = (WINDOW_WIDTH - padding * (cols + 1)) // cols
                    item_height = cell_size + 40
                    content_height = math.ceil(len(purchased_skins) / cols) * (item_height + padding)
                    max_scroll = content_height - (WINDOW_HEIGHT - 200)
                    if max_scroll < 0:
                        max_scroll = 0
                    self.scroll_y = max(self.scroll_y - 40, -max_scroll)
            if event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    self.is_dragging = False
            if event.type == pygame.MOUSEMOTION:
                if self.is_dragging:
                    drag_distance = event.pos[1] - self.drag_start_y
                    self.scroll_y = self.drag_start_offset + drag_distance
                    purchased_skins = self.get_filtered_purchased_skins()
                    cols = 4
                    padding = 40
                    cell_size = (WINDOW_WIDTH - padding * (cols + 1)) // cols
                    item_height = cell_size + 40
                    content_height = math.ceil(len(purchased_skins) / cols) * (item_height + padding)
                    max_scroll = content_height - (WINDOW_HEIGHT - 200)
                    if max_scroll < 0:
                        max_scroll = 0
                    self.scroll_y = max(min(self.scroll_y, 0), -max_scroll)

    def get_filtered_purchased_skins(self):
        """根据当前分类和形状筛选已购买的皮肤"""
        all_purchased_skins = player_data.get_purchased_skins()
        filtered_skins = []
        # 按形状筛选
        if not self.category_button.is_image_mode and self.shape_filter:
            return [k for k in all_purchased_skins if not image_skin_manager.is_image_skin(k) and SKINS.get(k, {}).get("shape") == self.shape_filter]
        for skin_id in all_purchased_skins:
            # 根据当前分类筛选
            if self.category_button.is_image_mode:
                # 显示图片皮肤
                if image_skin_manager.is_image_skin(skin_id):
                    filtered_skins.append(skin_id)
            else:
                # 显示颜色皮肤
                if not image_skin_manager.is_image_skin(skin_id):
                    filtered_skins.append(skin_id)
        return filtered_skins

    def draw_skin_preview(self, surface, rect, skin_id):
        if image_skin_manager.is_image_skin(skin_id):
            self.draw_image_skin_preview(surface, rect, skin_id)
        else:
            skin_info = SKINS.get(skin_id, SKINS.get("default_rectangle"))
            shape = skin_info.get("shape", "rectangle")
            base_color, dark_color = skin_info["colors"]
            preview_surface = pygame.Surface(rect.size, pygame.SRCALPHA)
            center_x, center_y = rect.width // 2, rect.height // 2
            radius = min(rect.width, rect.height) // 2 * 0.8
            if shape == "rectangle":
                r_rect = pygame.Rect(center_x - radius, center_y - radius, radius * 2, radius * 2)
                pygame.draw.rect(preview_surface, dark_color, r_rect, border_radius=int(radius * 0.2))
                pygame.draw.rect(preview_surface, base_color, r_rect.inflate(-radius*0.3, -radius*0.3), border_radius=int(radius * 0.15))
            elif shape == "circle":
                pygame.draw.circle(preview_surface, dark_color, (center_x, center_y), radius)
                pygame.draw.circle(preview_surface, base_color, (center_x, center_y), radius * 0.85)
            elif shape == "hexagon":
                points = get_hexagon_points(center_x, center_y, radius)
                pygame.draw.polygon(preview_surface, dark_color, points)
                inner_points = get_hexagon_points(center_x, center_y, radius * 0.85)
                pygame.draw.polygon(preview_surface, base_color, inner_points)
            elif shape == "pentagram":
                points = get_pentagram_points(center_x, center_y, radius)
                pygame.draw.polygon(preview_surface, dark_color, points)
                inner_points = get_pentagram_points(center_x, center_y, radius * 0.85)
                pygame.draw.polygon(preview_surface, base_color, inner_points)
            elif shape == "fan":
                direction = (1, 0)
                angle = math.atan2(-direction[1], direction[0])
                arc_rect = pygame.Rect(center_x - radius, center_y - radius, radius * 2, radius * 2)
                pygame.draw.arc(preview_surface, base_color, arc_rect, angle - math.pi / 2.5, angle + math.pi / 2.5, int(radius))
                num_ribs = 5
                for i in range(num_ribs):
                    rib_angle = angle - math.pi / 2.5 + (i * (math.pi / 2.5 * 2) / (num_ribs - 1))
                    start_pos = (center_x, center_y)
                    end_pos = (center_x + radius * math.cos(rib_angle), center_y - radius * math.sin(rib_angle))
                    pygame.draw.line(preview_surface, dark_color, start_pos, end_pos, 2)
            elif shape == "heart":
                s = radius * 0.9
                p1 = (center_x - s, center_y)
                p2 = (center_x + s, center_y)
                p3 = (center_x, center_y + s)
                pygame.draw.circle(preview_surface, dark_color, (center_x - s / 2, center_y - s * 0.2), s / 1.8)
                pygame.draw.circle(preview_surface, dark_color, (center_x + s / 2, center_y - s * 0.2), s / 1.8)
                pygame.draw.polygon(preview_surface, dark_color, [p1, p2, p3])
                pygame.draw.circle(preview_surface, base_color, (center_x - s / 2, center_y - s * 0.2), s / 2.2)
                pygame.draw.circle(preview_surface, base_color, (center_x + s / 2, center_y - s * 0.2), s / 2.2)
                adjusted_p1 = (p1[0] + s*0.1, p1[1] - s*0.2)
                adjusted_p2 = (p2[0] - s*0.1, p2[1] - s*0.2)
                adjusted_p3 = (p3[0], p3[1] - s*0.2)
                pygame.draw.polygon(preview_surface, base_color, [adjusted_p1, adjusted_p2, adjusted_p3])
            elif shape == "leaf":
                pygame.draw.polygon(preview_surface, base_color, [(center_x, center_y - radius), (center_x - radius*0.5, center_y + radius*0.5), (center_x + radius*0.5, center_y + radius*0.5)])
                pygame.draw.line(preview_surface, dark_color, (center_x, center_y - radius), (center_x, center_y + radius*0.5), 1)
            elif shape == "water_drop":
                pygame.draw.circle(preview_surface, base_color, (center_x, center_y + radius*0.2), radius * 0.8)
                pygame.draw.polygon(preview_surface, base_color, [(center_x, center_y - radius), (center_x - radius*0.8, center_y + radius*0.2), (center_x + radius*0.8, center_y + radius*0.2)])
                pygame.draw.circle(preview_surface, (255, 255, 255, 150), (center_x + radius*0.2, center_y), radius * 0.3)
            elif shape == "music_note":
                head_radius = radius * 0.5
                pygame.draw.ellipse(preview_surface, base_color, (center_x - head_radius, center_y + radius*0.3, head_radius * 2, head_radius * 1.5))
                stem_height = radius * 1.8
                stem_width = radius * 0.25
                stem_x = center_x + head_radius * 0.8
                stem_y = center_y + radius*0.6 - stem_height
                pygame.draw.rect(preview_surface, dark_color, (stem_x, stem_y, stem_width, stem_height))
                flag_points = [
                    (stem_x + stem_width, stem_y),
                    (stem_x + stem_width + radius, stem_y + radius * 0.5),
                    (stem_x + stem_width + radius*0.5, stem_y + radius),
                    (stem_x + stem_width, stem_y + radius*0.2) ]
                pygame.draw.polygon(preview_surface, dark_color, flag_points)
            elif shape == "lightning_bolt":
                w, h = preview_surface.get_size()
                cx, cy = w / 2, h / 2
                r = min(w, h) / 2 * 0.9
                bolt_surface = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
                bw, bh = bolt_surface.get_size()
                points = [
                    (bw * 0.5, 0),
                    (bw * 0.2, bh * 0.5),
                    (bw * 0.4, bh * 0.5),
                    (bw * 0.3, bh),
                    (bw * 0.8, bh * 0.4),
                    (bw * 0.6, bh * 0.4),
                ]
                pygame.draw.polygon(bolt_surface, dark_color, points)
                bcx, bcy = bw / 2, bh / 2
                inner_points = [(bcx + (p[0] - bcx) * 0.7, bcy + (p[1] - bcy) * 0.7) for p in points]
                pygame.draw.polygon(bolt_surface, base_color, inner_points)
                bolt_rect = bolt_surface.get_rect(center=(cx, cy))
                preview_surface.blit(bolt_surface, bolt_rect.topleft)
            elif shape == "crown":
                dark_color = tuple(max(0, c - 50) for c in base_color)
                w, h = preview_surface.get_size()
                cx, cy = w / 2, h / 2
                radius = min(w,h) / 2 * 0.9
                base_y = cy + radius * 0.2
                base_rect = pygame.Rect(cx - radius * 0.9, base_y, radius * 1.8, radius * 0.6)
                pygame.draw.rect(preview_surface, dark_color, base_rect, border_radius=3)
                pygame.draw.rect(preview_surface, base_color, base_rect.inflate(-4, -4), border_radius=3)
                tip_y = cy - radius
                mid_tip_points = [(cx, tip_y), (cx - radius * 0.3, base_y), (cx + radius * 0.3, base_y)]
                pygame.draw.polygon(preview_surface, dark_color, mid_tip_points)
                pygame.draw.polygon(preview_surface, base_color, [(cx, tip_y + 4), (cx - radius * 0.2, base_y), (cx + radius * 0.2, base_y)])
                left_tip_points = [(cx - radius * 0.7, tip_y + radius*0.3), (cx - radius, base_y), (cx - radius * 0.4, base_y)]
                right_tip_points = [(cx + radius * 0.7, tip_y + radius*0.3), (cx + radius, base_y), (cx + radius * 0.4, base_y)]
                pygame.draw.polygon(preview_surface, dark_color, left_tip_points)
                pygame.draw.polygon(preview_surface, base_color, [(cx - radius * 0.7, tip_y + radius*0.3 + 3), (cx - radius*0.9, base_y), (cx - radius*0.5, base_y)])
                pygame.draw.polygon(preview_surface, dark_color, right_tip_points)
                pygame.draw.polygon(preview_surface, base_color, [(cx + radius * 0.7, tip_y + radius*0.3 + 3), (cx + radius*0.9, base_y), (cx + radius*0.5, base_y)])
                pygame.draw.circle(preview_surface, (255, 0, 0), (cx, tip_y), radius * 0.18)
                pygame.draw.circle(preview_surface, (0, 0, 255), (cx - radius * 0.7, tip_y + radius*0.3), radius * 0.15)
                pygame.draw.circle(preview_surface, (0, 0, 255), (cx + radius * 0.7, tip_y + radius*0.3), radius * 0.15)
                pygame.draw.circle(preview_surface, (0, 255, 0), (cx, base_y + radius * 0.3), radius * 0.2)
                pygame.draw.circle(preview_surface, (255,255,255,150), (cx-radius*0.05, base_y + radius*0.25), radius*0.08)
            elif shape == "arrow":
                w, h = preview_surface.get_size()
                cx, cy = w / 2, h / 2
                r = min(w, h) / 2 * 0.9
                arrow_points = [
                    (cx, cy - r),
                    (cx - r * 0.6, cy + r * 0.3),
                    (cx + r * 0.6, cy + r * 0.3)
                ]
                pygame.draw.polygon(preview_surface, dark_color, arrow_points)
                stem_rect = pygame.Rect(cx - r * 0.15, cy + r * 0.3, r * 0.3, r * 0.7)
                pygame.draw.rect(preview_surface, dark_color, stem_rect)
                inner_arrow_points = [
                    (cx, cy - r * 0.8),
                    (cx - r * 0.4, cy + r * 0.1),
                    (cx + r * 0.4, cy + r * 0.1)
                ]
                pygame.draw.polygon(preview_surface, base_color, inner_arrow_points)
                inner_stem_rect = pygame.Rect(cx - r * 0.1, cy + r * 0.1, r * 0.2, r * 0.5)
                pygame.draw.rect(preview_surface, base_color, inner_stem_rect)
            else:
                r_rect = pygame.Rect(center_x - radius, center_y - radius, radius * 2, radius * 2)
                pygame.draw.rect(preview_surface, dark_color, r_rect, border_radius=int(radius * 0.2))
                pygame.draw.rect(preview_surface, base_color, r_rect.inflate(-radius*0.3, -radius*0.3), border_radius=int(radius * 0.15))
            surface.blit(preview_surface, rect.topleft)

    def draw_image_skin_preview(self, surface, rect, skin_id):
        skin_data = image_skin_manager.get_skin_data(skin_id)
        if not skin_data:
            return
        head_image_name = skin_data.get("head_image")
        body_image_name = skin_data.get("body_image")
        if not head_image_name or not body_image_name:
            return
        segment_size = int(min(rect.width, rect.height) * 0.4)
        head_image = image_skin_manager.get_image(head_image_name, (segment_size, segment_size))
        body_image = image_skin_manager.get_image(body_image_name, (segment_size, segment_size))
        if not head_image or not body_image:
            preview_surface = pygame.Surface(rect.size, pygame.SRCALPHA)
            center_x, center_y = rect.width // 2, rect.height // 2
            radius = min(rect.width, rect.height) // 2 * 0.8
            pygame.draw.rect(preview_surface, (100, 100, 100), (center_x - radius, center_y - radius, radius * 2, radius * 2), border_radius=int(radius * 0.2))
            pygame.draw.rect(preview_surface, (150, 150, 150), (center_x - radius, center_y - radius, radius * 2, radius * 2), border_radius=int(radius * 0.2), width=2)
            text = self.small_font.render("图片", True, WHITE)
            text_rect = text.get_rect(center=(center_x, center_y))
            preview_surface.blit(text, text_rect)
            surface.blit(preview_surface, rect.topleft)
        else:
            center_x = rect.centerx
            center_y = rect.centery
            head_rect = head_image.get_rect(center=(center_x, center_y - segment_size))
            surface.blit(head_image, head_rect)
            body_rect = body_image.get_rect(center=(center_x, center_y))
            surface.blit(body_image, body_rect)

    def draw(self):
        bg_surface = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        for y in range(WINDOW_HEIGHT):
            r = int(120 + (40-120)*y/WINDOW_HEIGHT)
            g = int(180 + (60-180)*y/WINDOW_HEIGHT)
            b = int(255 + (120-255)*y/WINDOW_HEIGHT)
            pygame.draw.line(bg_surface, (r,g,b,255), (0,y), (WINDOW_WIDTH,y))
        for i in range(2):
            pygame.draw.circle(bg_surface, (255,255,255,60), (WINDOW_WIDTH//2 + 220*i - 220, 120), 100)
        wave_surface = pygame.Surface((WINDOW_WIDTH, 120), pygame.SRCALPHA)
        for x in range(WINDOW_WIDTH):
            y = int(30*math.sin(x/80.0) + 60)
            pygame.draw.circle(wave_surface, (66,165,245,80), (x, y), 24)
        bg_surface.blit(wave_surface, (0, WINDOW_HEIGHT-120))
        self.screen.blit(bg_surface, (0,0))
        font = pygame.font.Font(FONT_NAME, 56)
        text = "我的皮肤"
        for dx, dy in [(-4,4),(4,4),(-4,-4),(4,-4),(0,6)]:
            shadow = font.render(text, True, (0,0,0))
            shadow_rect = shadow.get_rect(center=(WINDOW_WIDTH//2+dx, 80+dy))
            self.screen.blit(shadow, shadow_rect)
        for dx, dy, color in [(-3,0,(66,165,245)),(3,0,(255,213,79)),(0,-3,(120,200,120)),(0,3,(255,255,255))]:
            edge = font.render(text, True, color)
            edge_rect = edge.get_rect(center=(WINDOW_WIDTH//2+dx, 80+dy))
            self.screen.blit(edge, edge_rect)
        title = font.render(text, True, (66,165,245))
        title_rect = title.get_rect(center=(WINDOW_WIDTH//2, 80))
        self.screen.blit(title, title_rect)
        self.category_button.draw(self.screen)
        # 形状筛选下拉框（仅颜色皮肤模式）
        if not self.category_button.is_image_mode:
            self.shape_dropdown.draw(self.screen)
        purchased_skins = self.get_filtered_purchased_skins()
        equipped_skin = player_data.get_equipped_skin()
        cols = 4
        padding = 40
        cell_size = (WINDOW_WIDTH - padding * (cols + 1)) // cols
        item_height = cell_size + 40
        content_height = math.ceil(len(purchased_skins) / cols) * (item_height + padding)
        max_scroll = content_height - (WINDOW_HEIGHT - 200)
        if max_scroll < 0: max_scroll = 0
        self.scroll_y = max(self.scroll_y, -max_scroll)
        grid_area = pygame.Rect(0, 100, WINDOW_WIDTH, WINDOW_HEIGHT - 200)
        for i, skin_id in enumerate(purchased_skins):
            row = i // cols
            col = i % cols
            x = padding + col * (cell_size + padding)
            y = grid_area.top + self.scroll_y + row * (item_height + padding)
            if y + item_height < grid_area.top or y > grid_area.bottom:
                continue
            container_rect = pygame.Rect(x, y, cell_size, item_height)
            self.skin_rects[skin_id] = container_rect
            preview_rect = pygame.Rect(x, y, cell_size, cell_size)
            if equipped_skin == skin_id:
                pygame.draw.rect(self.screen, GOLD, preview_rect.inflate(8, 8), border_radius=15)
            pygame.draw.rect(self.screen, (40, 60, 90), preview_rect, border_radius=10)
            self.draw_skin_preview(self.screen, preview_rect.inflate(-20, -20), skin_id)
            skin_data = SKINS.get(skin_id)
            if not skin_data:
                if image_skin_manager.is_image_skin(skin_id):
                    skin_data = image_skin_manager.get_skin_data(skin_id)
                    if skin_data:
                        name_text = self.small_font.render(skin_data['name'], True, WHITE)
                        text_rect = name_text.get_rect(center=(container_rect.centerx, preview_rect.bottom + 20))
                        self.screen.blit(name_text, text_rect)
                continue
            name_text = self.small_font.render(skin_data['name'], True, WHITE)
            text_rect = name_text.get_rect(center=(container_rect.centerx, preview_rect.bottom + 20))
            self.screen.blit(name_text, text_rect)
        if content_height > (WINDOW_HEIGHT - 200):
            scrollbar_bg_rect = pygame.Rect(WINDOW_WIDTH - 25, 100, 15, WINDOW_HEIGHT - 200)
            pygame.draw.rect(self.screen, (20, 30, 50), scrollbar_bg_rect, border_radius=7)
            handle_height = ((WINDOW_HEIGHT - 200) / content_height) * (WINDOW_HEIGHT - 200)
            handle_y_ratio = (-self.scroll_y / max_scroll) if max_scroll else 0
            handle_y = 100 + ((WINDOW_HEIGHT - 200) - handle_height) * handle_y_ratio
            scrollbar_handle_rect = pygame.Rect(WINDOW_WIDTH - 25, handle_y, 15, handle_height)
            pygame.draw.rect(self.screen, (80, 100, 130), scrollbar_handle_rect, border_radius=7)
        self.back_button.draw(self.screen)
        # 最后绘制Dropdown展开选项，确保在最顶层
        if not self.category_button.is_image_mode and self.shape_dropdown.is_open:
            opt_h = self.shape_dropdown.rect.height
            visible_opts = self.shape_dropdown.options[self.shape_dropdown.scroll:self.shape_dropdown.scroll+self.shape_dropdown.max_visible]
            drop_rect = pygame.Rect(self.shape_dropdown.rect.x, self.shape_dropdown.rect.bottom, self.shape_dropdown.rect.width, opt_h*len(visible_opts))
            pygame.draw.rect(self.screen, self.shape_dropdown.color, drop_rect, border_radius=10)
            for i, opt in enumerate(visible_opts):
                opt_rect = pygame.Rect(self.shape_dropdown.rect.x, self.shape_dropdown.rect.bottom+i*opt_h, self.shape_dropdown.rect.width, opt_h)
                bg = self.shape_dropdown.hover_color if self.shape_dropdown.hovered_idx == self.shape_dropdown.scroll+i else self.shape_dropdown.color
                pygame.draw.rect(self.screen, bg, opt_rect, border_radius=8)
                txt = self.shape_dropdown.font.render(str(opt), True, WHITE)
                self.screen.blit(txt, (opt_rect.x+12, opt_rect.y+8))
        pygame.display.flip()