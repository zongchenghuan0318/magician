import pygame
import json
import os
from .constants import WINDOW_WIDTH, WINDOW_HEIGHT, WHITE, GOLD, BLACK, FONT_NAME, BUTTON_COLOR, BUTTON_HOVER_COLOR, BUTTON_WIDTH, BUTTON_HEIGHT, BUTTON_TEXT_COLOR
from .player import player_data
from .ui_elements import CartoonButton, Button
from .image_skins import image_skin_manager

def load_skins_from_file():
    """从JSON文件中加载皮肤数据"""
    # 构建到skins.json的健壮路径
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    skins_path = os.path.join(project_root, 'skins.json')
    
    try:
        # 使用utf-8编码打开文件以支持中文字符
        with open(skins_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        # print(f"错误：无法加载 'skins.json': {e}")
        # 如果文件不存在或格式错误，返回一个默认的皮肤以避免崩溃
        return {
            "default": {"name": "经典绿", "price": 0, "colors": [[40, 180, 99], [30, 132, 73]]}
        }

# 从外部文件加载皮肤数据
SKINS = load_skins_from_file()

class CategoryToggleButton:
    """美观的分类切换按钮"""
    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)
        self.is_image_mode = False
        self.is_hovered = False
        self.animation_progress = 0.0
        self.font = pygame.font.Font(FONT_NAME, 20)
        
        # 颜色定义
        self.bg_color = (30, 50, 80)
        self.active_color = (52, 152, 219)
        self.hover_color = (41, 128, 185)
        self.text_color = WHITE
        self.border_color = (60, 100, 140)
        
    def draw(self, surface):
        # 绘制背景
        pygame.draw.rect(surface, self.bg_color, self.rect, border_radius=20)
        pygame.draw.rect(surface, self.border_color, self.rect, 2, border_radius=20)
        
        # 绘制切换滑块
        slider_width = self.rect.width // 2 - 4
        slider_x = self.rect.x + 2 + (slider_width + 4) * self.is_image_mode
        slider_rect = pygame.Rect(slider_x, self.rect.y + 2, slider_width, self.rect.height - 4)
        
        # 滑块颜色
        slider_color = self.active_color if self.is_hovered else self.hover_color
        pygame.draw.rect(surface, slider_color, slider_rect, border_radius=18)
        
        # 绘制文字
        color_text = self.font.render("颜色", True, self.text_color if not self.is_image_mode else (100, 100, 100))
        image_text = self.font.render("图片", True, self.text_color if self.is_image_mode else (100, 100, 100))
        
        # 文字位置
        color_x = self.rect.x + (self.rect.width // 2 - color_text.get_width()) // 2
        image_x = self.rect.x + self.rect.width // 2 + (self.rect.width // 2 - image_text.get_width()) // 2
        text_y = self.rect.y + (self.rect.height - color_text.get_height()) // 2
        
        surface.blit(color_text, (color_x, text_y))
        surface.blit(image_text, (image_x, text_y))
        
        # 绘制图标（简单的装饰）
        if self.is_image_mode:
            # 图片图标（简单的方块）
            icon_rect = pygame.Rect(image_x - 25, text_y, 16, 16)
            pygame.draw.rect(surface, self.text_color, icon_rect, 2, border_radius=3)
        else:
            # 颜色图标（简单的圆形）
            icon_center = (color_x - 25, text_y + 8)
            pygame.draw.circle(surface, self.text_color, icon_center, 6, 2)
    
    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.is_hovered and event.button == 1:
                self.is_image_mode = not self.is_image_mode
                return True
        return False

class ConfirmationDialog:
    """购买确认对话框"""
    def __init__(self, screen, skin_name, price):
        self.screen = screen
        self.skin_name = skin_name
        self.price = price
        self.font = pygame.font.Font(FONT_NAME, 24)
        self.title_font = pygame.font.Font(FONT_NAME, 32)
        
        # 对话框位置和大小
        self.width = 400
        self.height = 250
        self.x = (WINDOW_WIDTH - self.width) // 2
        self.y = (WINDOW_HEIGHT - self.height) // 2
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        
        # 按钮 - 调整尺寸和文字以适应内容
        button_width = 100  # 增加按钮宽度
        button_height = 35   # 稍微增加按钮高度
        button_y = self.y + self.height - 60
        
        self.confirm_button = CartoonButton(
            self.x + 50, button_y, button_width, button_height,
            "确认", color=(46, 204, 113), font_size=16  # 简化文字并设置字体大小
        )
        self.cancel_button = CartoonButton(
            self.x + self.width - 50 - button_width, button_y, button_width, button_height,
            "取消", color=(231, 76, 60), font_size=16
        )
        
        # 动画效果
        self.scale = 0.0
        self.target_scale = 1.0
        
    def update(self):
        # 弹出动画
        if self.scale < self.target_scale:
            self.scale = min(self.scale + 0.1, self.target_scale)
    
    def draw(self):
        # 半透明背景
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        overlay.set_alpha(150)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))
        
        # 缩放效果
        if self.scale < 1.0:
            scaled_width = int(self.width * self.scale)
            scaled_height = int(self.height * self.scale)
            scaled_x = self.x + (self.width - scaled_width) // 2
            scaled_y = self.y + (self.height - scaled_height) // 2
            scaled_rect = pygame.Rect(scaled_x, scaled_y, scaled_width, scaled_height)
        else:
            scaled_rect = self.rect
        
        # 对话框背景
        pygame.draw.rect(self.screen, (50, 70, 100), scaled_rect, border_radius=20)
        pygame.draw.rect(self.screen, (100, 150, 200), scaled_rect, 3, border_radius=20)
        
        if self.scale >= 1.0:  # 只有完全显示时才绘制内容
            # 标题
            title_text = self.title_font.render("购买确认", True, WHITE)
            title_rect = title_text.get_rect(center=(self.x + self.width // 2, self.y + 50))
            self.screen.blit(title_text, title_rect)
            
            # 皮肤信息
            info_text = self.font.render(f"皮肤: {self.skin_name}", True, WHITE)
            info_rect = info_text.get_rect(center=(self.x + self.width // 2, self.y + 100))
            self.screen.blit(info_text, info_rect)
            
            # 价格信息
            price_text = self.font.render(f"价格: {self.price} 金币", True, (255, 213, 79))
            price_rect = price_text.get_rect(center=(self.x + self.width // 2, self.y + 130))
            self.screen.blit(price_text, price_rect)
            
            # 绘制按钮
            self.confirm_button.draw(self.screen)
            self.cancel_button.draw(self.screen)
    
    def handle_event(self, event):
        if self.scale < 1.0:  # 动画未完成时不处理事件
            return None
            
        if self.confirm_button.handle_event(event):
            return "confirm"
        elif self.cancel_button.handle_event(event):
            return "cancel"
        return None

class SearchBox:
    """搜索框组件"""
    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = ""
        self.active = False
        self.font = pygame.font.Font(FONT_NAME, 18)  # 缩小字体
        self.cursor_visible = True
        self.cursor_timer = 0
        
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
        elif event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.unicode.isprintable():
                self.text += event.unicode
                
    def update(self):
        self.cursor_timer += 1
        if self.cursor_timer >= 30:  # 每30帧切换一次光标显示
            self.cursor_visible = not self.cursor_visible
            self.cursor_timer = 0
    
    def draw(self, surface):
        # 背景
        color = (60, 80, 120) if self.active else (40, 60, 100)
        pygame.draw.rect(surface, color, self.rect, border_radius=10)
        pygame.draw.rect(surface, (100, 150, 200), self.rect, 2, border_radius=10)
        
        # 占位符文本
        if not self.text and not self.active:
            placeholder = self.font.render("搜索皮肤...", True, (150, 150, 150))
            surface.blit(placeholder, (self.rect.x + 10, self.rect.y + 10))
        else:
            # 实际文本
            text_surface = self.font.render(self.text, True, WHITE)
            surface.blit(text_surface, (self.rect.x + 10, self.rect.y + 10))
            
            # 光标
            if self.active and self.cursor_visible:
                cursor_x = self.rect.x + 10 + text_surface.get_width()
                cursor_y = self.rect.y + 8
                pygame.draw.line(surface, WHITE, (cursor_x, cursor_y), (cursor_x, cursor_y + 24), 2)

class ShopMenu:
    def __init__(self, screen, game_controller):
        self.screen = screen
        self.game_controller = game_controller
        self.font = pygame.font.Font(FONT_NAME, 40)
        self.small_font = pygame.font.Font(FONT_NAME, 20)  # 稍微减小
        self.tiny_font = pygame.font.Font(FONT_NAME, 16)   # 稍微减小
        self.label_font = pygame.font.Font(FONT_NAME, 14)  # 新增标签字体
        self.running = True
        self.buttons = {} # skin_id -> rect
        self.scroll_offset = 0 # For scrolling
        
        # 鼠标拖拽相关变量
        self.is_dragging = False
        self.drag_start_y = 0
        self.drag_start_offset = 0
        
        # 皮肤分类相关变量
        self.category_button = CategoryToggleButton(50, 120, 200, 40)
        
        # 搜索和排序功能
        self.search_box = SearchBox(270, 120, 200, 40)
        self.sort_by_price = False  # False: 默认排序, True: 按价格排序
        self.show_owned = False  # 是否显示已拥有的皮肤
        
        # 形状筛选相关变量
        self.shape_filter = None  # 当前选中的形状（如 'rectangle'）
        self.shape_map = {
            "rectangle": "矩形",
            "circle": "圆形",
            "pentagram": "五角星",
            "fan": "扇子",
            "heart": "爱心",
            "leaf": "叶子",
            "water_drop": "水滴",
            "music_note": "音符",
            "lightning_bolt": "闪电",
            "crown": "皇冠",
            "arrow": "箭头",
            "nebula": "星云"
        }
        from .ui_elements import Dropdown
        self.shape_order = [
            "rectangle", "circle", "pentagram", "fan", "heart", "leaf", "water_drop", "music_note", "lightning_bolt", "crown", "arrow", "nebula"
        ]
        shape_options = ["不筛选"] + [self.shape_map[s] for s in self.shape_order]
        self.shape_dropdown = Dropdown(490, 120, 120, 40, shape_options, selected=None)
        
        # 排序和筛选按钮 - 调整到更合适的位置，确保文字不被覆盖
        self.price_sort_button = CartoonButton(520, 160, 70, 30, "默认", color=(52, 152, 219), font_size=14)
        self.owned_toggle_button = CartoonButton(600, 160, 70, 30, "隐藏", color=(155, 89, 182), font_size=14)
        
        # 添加状态文字显示
        self.sort_text = "默认"
        self.owned_text = "隐藏"
        
        self.back_button = CartoonButton(
            WINDOW_WIDTH // 2 - BUTTON_WIDTH // 2,
            WINDOW_HEIGHT - BUTTON_HEIGHT - 40,
            BUTTON_WIDTH,
            BUTTON_HEIGHT,
            "返回",
            color=(120, 200, 120),
            icon_type="back"
        )
        
        # 合并所有皮肤数据
        self.all_skins = {}
        self.all_skins.update(SKINS)
        self.all_skins.update(image_skin_manager.get_all_image_skins())
        # 分离图片皮肤和颜色皮肤
        self.image_skins = {}
        self.color_skins = {}
        for skin_id, skin_data in self.all_skins.items():
            if image_skin_manager.is_image_skin(skin_id):
                self.image_skins[skin_id] = skin_data
            else:
                self.color_skins[skin_id] = skin_data

        # 背景缓存表面（避免每帧重建）
        self._bg_surface = None
        # 价格图标小表面缓存
        self._coin_icon_surface = None
        # 预览图片缓存（仅商店用，避免反复从磁盘加载）
        self._preview_image_cache = {}
        
        # 确认对话框
        self.confirmation_dialog = None
        self.pending_purchase = None  # (skin_id, skin_data)
        
        # 网格布局参数
        self.grid_cols = 3  # 每行显示3个商品
        self.card_width = 200
        self.card_height = 160
        self.card_margin = 20

    def run(self):
        self.running = True
        self.buttons = {}
        clock = pygame.time.Clock()
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            clock.tick(60)  # 60 FPS
            
    def update(self):
        """更新动画和状态"""
        self.search_box.update()
        if self.confirmation_dialog:
            self.confirmation_dialog.update()

    def handle_events(self):
        for event in pygame.event.get():
            # 如果有确认对话框，优先处理对话框事件
            if self.confirmation_dialog:
                result = self.confirmation_dialog.handle_event(event)
                if result == "confirm" and self.pending_purchase:
                    skin_id, skin_data = self.pending_purchase
                    if player_data.spend_coins(skin_data['price']):
                        player_data.add_purchased_skin(skin_id)
                        # TODO: 添加购买成功动画效果
                    self.confirmation_dialog = None
                    self.pending_purchase = None
                elif result == "cancel":
                    self.confirmation_dialog = None
                    self.pending_purchase = None
                continue
            
            # 处理搜索框事件
            self.search_box.handle_event(event)
            
            # 处理排序和筛选按钮事件
            if self.price_sort_button.handle_event(event):
                self.sort_by_price = not self.sort_by_price
                self.sort_text = "价格" if self.sort_by_price else "默认"
                self.price_sort_button.text = self.sort_text
                
            if self.owned_toggle_button.handle_event(event):
                self.show_owned = not self.show_owned
                self.owned_text = "显示" if self.show_owned else "隐藏"
                self.owned_toggle_button.text = self.owned_text
                self.scroll_offset = 0  # 重置滚动位置
            
            # 处理形状筛选下拉框事件（仅颜色皮肤模式）
            if not self.category_button.is_image_mode:
                self.shape_dropdown.handle_event(event)
                
            if event.type == pygame.QUIT:
                self.running = False
                self.game_controller.running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
            
            # 处理分类按钮点击
            if self.category_button.handle_event(event):
                self.scroll_offset = 0  # 重置滚动位置
                self.shape_filter = None  # 切换分类时重置筛选
                self.shape_dropdown.selected = None  # 切换分类时重置下拉框选中项
                
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
            
            # Handle mouse wheel scrolling
            if event.type == pygame.MOUSEWHEEL:
                self.scroll_offset += event.y * 30  # 增加滚动速度

            # Handle mouse button down
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    # 检查是否点击了购买按钮
                    for skin_id, rect in self.buttons.items():
                        if rect.collidepoint(event.pos):
                            # 根据当前显示的分类获取皮肤信息
                            current_skins = self._get_filtered_skins()
                            if skin_id in current_skins:
                                skin_info = current_skins[skin_id]
                                purchased_skins = player_data.get_purchased_skins()
                                if skin_id not in purchased_skins:
                                    # 显示购买确认对话框
                                    self.confirmation_dialog = ConfirmationDialog(
                                        self.screen, skin_info['name'], skin_info['price']
                                    )
                                    self.pending_purchase = (skin_id, skin_info)
                            return  # 如果点击了按钮，不开始拖拽
                    
                    # 检查是否点击了滚动条
                    y_start = 210  # 与_draw_shop_items中的y_start保持一致
                    list_height = WINDOW_HEIGHT - y_start - 80
                    scrollbar_rect = pygame.Rect(WINDOW_WIDTH - 25, y_start, 15, list_height)
                    if scrollbar_rect.collidepoint(event.pos):
                        # 计算点击位置对应的滚动偏移
                        click_ratio = (event.pos[1] - y_start) / list_height
                        # 根据当前分类筛选皮肤
                        current_skins = self._get_filtered_skins()
                        grid_rows = (len(current_skins) + self.grid_cols - 1) // self.grid_cols
                        content_height = grid_rows * (self.card_height + self.card_margin)
                        max_scroll = content_height - list_height
                        if max_scroll > 0:
                            self.scroll_offset = -click_ratio * max_scroll
                        return  # 如果点击了滚动条，不开始拖拽
                    
                    # 如果没有点击按钮或滚动条，开始拖拽
                    self.is_dragging = True
                    self.drag_start_y = event.pos[1]
                    self.drag_start_offset = self.scroll_offset

            # Handle mouse button up
            if event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:  # Left click release
                    self.is_dragging = False

            # Handle mouse motion (dragging)
            if event.type == pygame.MOUSEMOTION:
                if self.is_dragging:
                    # 计算拖拽距离并更新滚动偏移
                    drag_distance = event.pos[1] - self.drag_start_y
                    self.scroll_offset = self.drag_start_offset + drag_distance
    
    def _get_filtered_skins(self):
        """获取筛选和排序后的皮肤列表"""
        # 根据当前分类获取皮肤
        current_skins = self.image_skins if self.category_button.is_image_mode else self.color_skins
        
        # 搜索筛选
        if self.search_box.text.strip():
            search_term = self.search_box.text.strip().lower()
            filtered_skins = {}
            for skin_id, skin_data in current_skins.items():
                if (search_term in skin_data.get('name', '').lower() or 
                    search_term in skin_id.lower()):
                    filtered_skins[skin_id] = skin_data
            current_skins = filtered_skins
        
        # 形状筛选（仅颜色皮肤）
        if not self.category_button.is_image_mode and self.shape_filter:
            filtered_skins = {}
            for skin_id, skin_data in current_skins.items():
                if skin_data.get('shape') == self.shape_filter:
                    filtered_skins[skin_id] = skin_data
            current_skins = filtered_skins
        
        # 已拥有筛选
        purchased_skins = player_data.get_purchased_skins()
        if not self.show_owned:
            # 隐藏已拥有的皮肤
            filtered_skins = {}
            for skin_id, skin_data in current_skins.items():
                if skin_id not in purchased_skins:
                    filtered_skins[skin_id] = skin_data
            current_skins = filtered_skins
        
        # 排序
        if self.sort_by_price:
            # 按价格排序
            sorted_items = sorted(current_skins.items(), key=lambda x: x[1].get('price', 0))
        else:
            # 默认排序（颜色皮肤按形状排序）
            if self.category_button.is_image_mode:
                sorted_items = sorted(current_skins.items(), key=lambda x: x[1].get('name', ''))
            else:
                def skin_sort_key(item):
                    skin = item[1]
                    shape = skin.get("shape", "")
                    try:
                        idx = self.shape_order.index(shape)
                    except ValueError:
                        idx = len(self.shape_order)
                    return (idx, skin.get("price", 0), item[0])
                sorted_items = sorted(current_skins.items(), key=skin_sort_key)
        
        return dict(sorted_items)

    def draw(self):
        # 商店专属紫粉橙渐变背景（缓存）
        if (self._bg_surface is None) or (self._bg_surface.get_size() != (WINDOW_WIDTH, WINDOW_HEIGHT)):
            bg_surface = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
            for y in range(WINDOW_HEIGHT):
                r = int(180 + (255-180)*y/WINDOW_HEIGHT)
                g = int(120 + (80-120)*y/WINDOW_HEIGHT)
                b = int(220 + (120-220)*y/WINDOW_HEIGHT)
                pygame.draw.line(bg_surface, (r,g,b,255), (0,y), (WINDOW_WIDTH,y))
            # 顶部光晕
            pygame.draw.circle(bg_surface, (255,220,180,80), (WINDOW_WIDTH//2, 100), 120)
            pygame.draw.circle(bg_surface, (255,255,255,40), (WINDOW_WIDTH//2-180, 80), 80)
            pygame.draw.circle(bg_surface, (255,255,255,40), (WINDOW_WIDTH//2+180, 80), 80)
            # 底部彩色圆环
            for i in range(5):
                color = [(255,213,79),(255,99,132),(156,39,176),(66,165,245),(255,167,38)][i]
                pygame.draw.circle(bg_surface, color+(60,), (120+180*i, WINDOW_HEIGHT-60), 36, 8)
            # 星星点缀
            import random
            random.seed(42)  # 固定随机种子，避免背景闪烁
            for _ in range(12):
                x = random.randint(40, WINDOW_WIDTH-40)
                y = random.randint(60, WINDOW_HEIGHT-80)
                pygame.draw.circle(bg_surface, (255,255,255,80), (x, y), random.randint(2,5))
            self._bg_surface = bg_surface
        self.screen.blit(self._bg_surface, (0,0))

        # --- 卡通大标题 ---
        font = pygame.font.Font(FONT_NAME, 48)  # 稍微减小字体
        text = "商店"
        for dx, dy in [(-3,3),(3,3),(-3,-3),(3,-3),(0,4)]:
            shadow = font.render(text, True, (0,0,0))
            shadow_rect = shadow.get_rect(center=(WINDOW_WIDTH//2+dx, 50+dy))
            self.screen.blit(shadow, shadow_rect)
        for dx, dy, color in [(-2,0,(66,165,245)),(2,0,(255,213,79)),(0,-2,(120,200,120)),(0,2,(255,255,255))]:
            edge = font.render(text, True, color)
            edge_rect = edge.get_rect(center=(WINDOW_WIDTH//2+dx, 50+dy))
            self.screen.blit(edge, edge_rect)
        title = font.render(text, True, (66,165,245))
        title_rect = title.get_rect(center=(WINDOW_WIDTH//2, 50))
        self.screen.blit(title, title_rect)

        # 绘制分类按钮
        self.category_button.draw(self.screen)
        
        # 绘制搜索框
        self.search_box.draw(self.screen)
        
        # 绘制形状筛选下拉框（仅颜色皮肤模式）
        if not self.category_button.is_image_mode:
            self.shape_dropdown.draw(self.screen)
            
        # 在右上角显示金币，位置调整到更高的位置
        coin_text = self.small_font.render(f"金币: {player_data.get_coins()}", True, GOLD)
        self.screen.blit(coin_text, (WINDOW_WIDTH - 150, 70))

        # 绘制排序和筛选按钮（第二行）
        self.price_sort_button.draw(self.screen)
        self.owned_toggle_button.draw(self.screen)
        
        # 注释掉状态标签，让界面更简洁
        # sort_label = self.label_font.render("排序:", True, (180, 180, 180))
        # self.screen.blit(sort_label, (50, 164))
        
        # owned_label = self.label_font.render("已拥有:", True, (180, 180, 180))
        # self.screen.blit(owned_label, (140, 164))
        
        # 注释掉商品统计信息，让界面更简洁
        # current_skins = self._get_filtered_skins()
        # if len(current_skins) > 0:
        #     count_text = self.label_font.render(f"共 {len(current_skins)} 件商品", True, (160, 160, 160))
        #     self.screen.blit(count_text, (240, 185))
        # else:
        #     count_text = self.label_font.render("暂无匹配商品", True, (200, 100, 100))
        #     self.screen.blit(count_text, (240, 185))

        self._draw_shop_items()  # 绘制商品项目
        
        # 绘制返回按钮
        self.back_button.draw(self.screen)
        
        # 最后绘制Dropdown展开选项，确保在最顶层
        if not self.category_button.is_image_mode and self.shape_dropdown.is_open:
            self._draw_dropdown_options()
        
        # 绘制确认对话框（在最顶层）
        if self.confirmation_dialog:
            self.confirmation_dialog.draw()
            
        pygame.display.flip()
        
    def _draw_dropdown_options(self):
        """绘制下拉框展开选项"""
        opt_h = self.shape_dropdown.rect.height
        visible_opts = self.shape_dropdown.options[self.shape_dropdown.scroll:self.shape_dropdown.scroll+self.shape_dropdown.max_visible]
        drop_rect = pygame.Rect(self.shape_dropdown.rect.x, self.shape_dropdown.rect.bottom, self.shape_dropdown.rect.width, opt_h*len(visible_opts))
        pygame.draw.rect(self.screen, self.shape_dropdown.color, drop_rect, border_radius=10)
        for i, opt in enumerate(visible_opts):
            opt_rect = pygame.Rect(self.shape_dropdown.rect.x, self.shape_dropdown.rect.bottom+i*opt_h, self.shape_dropdown.rect.width, opt_h)
            bg = self.shape_dropdown.hover_color if self.shape_dropdown.hovered_idx == self.shape_dropdown.scroll+i else self.shape_dropdown.color
            pygame.draw.rect(self.screen, bg, opt_rect, border_radius=8)
            txt = self.shape_dropdown.font.render(str(opt), True, BUTTON_TEXT_COLOR)
            self.screen.blit(txt, (opt_rect.x+12, opt_rect.y+8))
            
    def _draw_shop_items(self):
        """绘制商品项目的网格布局"""
        # --- 网格布局逻辑 ---
        y_start = 210  # 调整起始位置，给按钮留出足够空间
        list_height = WINDOW_HEIGHT - y_start - 80  # 列表可见区域
        
        # 获取筛选后的皮肤
        current_skins = self._get_filtered_skins()
        
        # 计算网格参数
        grid_start_x = 50
        grid_width = WINDOW_WIDTH - 100 - 30  # 留出滚动条空间
        actual_card_width = (grid_width - (self.grid_cols - 1) * self.card_margin) // self.grid_cols
        
        grid_rows = (len(current_skins) + self.grid_cols - 1) // self.grid_cols
        content_height = grid_rows * (self.card_height + self.card_margin)
        
        # 限制滚动偏移
        if content_height > list_height:
            max_scroll = content_height - list_height
            self.scroll_offset = max(min(self.scroll_offset, 0), -max_scroll)
        else:
            self.scroll_offset = 0

        # 如果没有商品，简单显示提示信息
        if not current_skins:
            empty_text = self.small_font.render("暂无商品", True, (180, 180, 180))
            empty_rect = empty_text.get_rect(center=(WINDOW_WIDTH//2, y_start + 100))
            self.screen.blit(empty_text, empty_rect)
            return

        # --- 绘制商品卡片 ---
        self.buttons = {}  # 重置按钮
        purchased_skins = player_data.get_purchased_skins()
        
        # 裁剪区域，只绘制可见的卡片
        clip_rect = pygame.Rect(0, y_start, WINDOW_WIDTH, list_height)
        self.screen.set_clip(clip_rect)
        
        skin_list = list(current_skins.items())
        for i, (skin_id, skin_data) in enumerate(skin_list):
            row = i // self.grid_cols
            col = i % self.grid_cols
            
            card_x = grid_start_x + col * (actual_card_width + self.card_margin)
            card_y = y_start + self.scroll_offset + row * (self.card_height + self.card_margin)
            
            # 只绘制可见的卡片
            if card_y + self.card_height < y_start or card_y > y_start + list_height:
                continue
                
            # 卡片背景
            card_rect = pygame.Rect(card_x, card_y, actual_card_width, self.card_height)
            
            # 阴影效果
            shadow_rect = card_rect.move(4, 4)
            pygame.draw.rect(self.screen, (0, 0, 0, 100), shadow_rect, border_radius=16)
            
            # 卡片主体
            is_owned = skin_id in purchased_skins
            card_color = (100, 150, 100) if is_owned else (60, 80, 120)
            pygame.draw.rect(self.screen, card_color, card_rect, border_radius=16)
            pygame.draw.rect(self.screen, (120, 160, 200), card_rect, 2, border_radius=16)
            
            # 皮肤预览
            self._draw_skin_preview(skin_id, skin_data, card_x, card_y, actual_card_width)
            
            # 皮肤名称（使用小字体，颜色更柔和）
            name_text = self.small_font.render(skin_data['name'], True, (240, 240, 240))
            name_rect = name_text.get_rect(center=(card_x + actual_card_width // 2, card_y + 95))
            self.screen.blit(name_text, name_rect)
            
            # 价格和按钮
            if is_owned:
                # 已拥有标识（使用更鲜明的绿色）
                owned_text = self.small_font.render("✓ 已拥有", True, (100, 255, 150))
                owned_rect = owned_text.get_rect(center=(card_x + actual_card_width // 2, card_y + 125))
                self.screen.blit(owned_text, owned_rect)
            else:
                # 价格显示（使用更鲜明的金色）
                price_text = self.small_font.render(f"{skin_data['price']} 金币", True, (255, 223, 100))
                price_rect = price_text.get_rect(center=(card_x + actual_card_width // 2, card_y + 115))
                self.screen.blit(price_text, price_rect)
                
                # 购买按钮
                button_width = 60
                button_height = 25
                button_x = card_x + (actual_card_width - button_width) // 2
                button_y = card_y + 130
                
                buy_btn = CartoonButton(
                    button_x, button_y, button_width, button_height,
                    "购买",
                    color=(46, 204, 113),
                    font_size=16
                )
                buy_btn.draw(self.screen)
                self.buttons[skin_id] = buy_btn.rect
        
        # 取消裁剪
        self.screen.set_clip(None)
        
        # --- 绘制滚动条 ---
        if content_height > list_height:
            self._draw_scrollbar(y_start, list_height, content_height)
            
    def _draw_skin_preview(self, skin_id, skin_data, card_x, card_y, card_width):
        """绘制皮肤预览"""
        preview_size = 64
        preview_x = card_x + (card_width - preview_size) // 2
        preview_y = card_y + 15
        preview_rect = pygame.Rect(preview_x, preview_y, preview_size, preview_size)
        
        if self.category_button.is_image_mode and ('head_image' in skin_data or 'image' in skin_data):
            try:
                img_key = (skin_id, preview_size, preview_size)
                if img_key not in self._preview_image_cache:
                    from .constants import get_resource_path
                    # 优先使用head_image，如果没有则使用image
                    img_path = skin_data.get('head_image') or skin_data.get('image', '')
                    if not img_path:
                        raise Exception("未找到图片路径")
                        
                    if not os.path.isabs(img_path):
                        # 尝试不同的路径解析方式
                        resolved = None
                        # 先尝试snake_images目录
                        snake_images_path = os.path.join(get_resource_path('snake_images'), img_path)
                        if os.path.exists(snake_images_path):
                            resolved = snake_images_path
                        else:
                            # 再尝试相对于项目根目录
                            root_path = get_resource_path(img_path)
                            if os.path.exists(root_path):
                                resolved = root_path
                        
                        if not resolved:
                            raise Exception(f"图片文件不存在: {img_path}")
                    else:
                        resolved = img_path
                        
                    image = pygame.image.load(resolved).convert_alpha()
                    image = pygame.transform.scale(image, (preview_size, preview_size))
                    self._preview_image_cache[img_key] = image
                self.screen.blit(self._preview_image_cache[img_key], preview_rect)
            except Exception as e:
                # 如果图片加载失败，显示默认占位符并添加调试信息
                print(f"图片加载失败 {skin_id}: {e}")
                pygame.draw.rect(self.screen, (120,120,120), preview_rect, border_radius=8)
                # 在占位符中显示“图”字
                text_surface = self.tiny_font.render("图", True, (255, 255, 255))
                text_rect = text_surface.get_rect(center=preview_rect.center)
                self.screen.blit(text_surface, text_rect)
        elif not self.category_button.is_image_mode and 'colors' in skin_data:
            color_list = skin_data['colors']
            circle_size = min(20, preview_size // len(color_list))
            for j, c in enumerate(color_list[:4]):  # 最多显示4个颜色
                circle_x = preview_x + j * (circle_size + 4)
                circle_y = preview_y + preview_size // 2
                pygame.draw.circle(self.screen, tuple(c), (circle_x + circle_size//2, circle_y), circle_size//2)
        else:
            # 默认占位符
            pygame.draw.rect(self.screen, (120,120,120), preview_rect, border_radius=8)
            # 显示默认标识
            text_surface = self.tiny_font.render("?", True, (255, 255, 255))
            text_rect = text_surface.get_rect(center=preview_rect.center)
            self.screen.blit(text_surface, text_rect)
            
    def _draw_scrollbar(self, y_start, list_height, content_height):
        """绘制滚动条"""
        max_scroll = content_height - list_height
        scrollbar_bg_rect = pygame.Rect(WINDOW_WIDTH - 25, y_start, 15, list_height)
        pygame.draw.rect(self.screen, (20, 30, 50), scrollbar_bg_rect, border_radius=7)

        handle_height = (list_height / content_height) * list_height
        handle_y_ratio = (-self.scroll_offset / max_scroll) if max_scroll else 0
        handle_y = y_start + (list_height - handle_height) * handle_y_ratio
        
        scrollbar_handle_rect = pygame.Rect(WINDOW_WIDTH - 25, handle_y, 15, handle_height)
        pygame.draw.rect(self.screen, (80, 100, 130), scrollbar_handle_rect, border_radius=7)
