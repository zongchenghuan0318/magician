import pygame
import sys
import os
import random
import time
from .constants import *
from .player import player_data

class PintuGame:
    def __init__(self, surface, parent):
        self.surface = surface
        self.parent = parent
        self.panel_x = parent.panel_x
        self.panel_y = parent.panel_y
        self.panel_w = parent.panel_w
        self.panel_h = parent.panel_h
        self.is_running = True
        self.selected_piece = None
        self.completed = False
        self.completion_time = 0
        self.start_time = time.time()
        self.moves = 0
        self.difficulty = 3  # 默认3x3难度
        self.pieces = []
        self.original_image = None
        self.image_path = None
        self.swapping = False
        self.swap_pieces = []
        self.swap_progress = 0
        self.show_image_selector = True  # 显示图片选择界面
        self.image_files = []  # 图片文件列表
        self.selected_image_index = 0  # 选中的图片索引
        self.thumbnail_size = (100, 100)  # 缩略图大小
        self.load_image_list()  # 加载图片列表
        # 加载字体
        self.font = pygame.font.Font(FONT_NAME, 24)
        self.title_font = pygame.font.Font(FONT_NAME, 36)

    def load_image_list(self):
        """加载pintu文件夹中的所有图片文件"""
        pintu_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'pintu')
        self.image_files = [f for f in os.listdir(pintu_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))]
        if not self.image_files:
            print("错误：pintu文件夹中未找到图片文件")
            self.parent.page = 'main'
            return
        # 加载第一张图片作为默认图片
        self.load_selected_image()

    def load_selected_image(self):
        """加载选中的图片"""
        if not self.image_files:
            return
        pintu_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'pintu')
        self.image_path = os.path.join(pintu_dir, self.image_files[self.selected_image_index])
        try:
            self.original_image = pygame.image.load(self.image_path)
            # 调整图片大小以适应游戏面板
            self.original_image = pygame.transform.scale(self.original_image, (
                min(self.panel_w - 40, 600), min(self.panel_h - 120, 600)))
        except Exception as e:
            print(f"加载图片出错: {e}")
            self.parent.page = 'main'

    def load_random_image(self):
        """从pintu文件夹随机加载一张图片"""
        if not self.image_files:
            self.load_image_list()
        else:
            self.selected_image_index = random.randint(0, len(self.image_files) - 1)
            self.load_selected_image()

    def create_pieces(self):
        """将图片分割成拼图块"""
        if not self.original_image:
            return
        image_rect = self.original_image.get_rect()
        piece_width = image_rect.width // self.difficulty
        piece_height = image_rect.height // self.difficulty
        self.pieces = []
        for y in range(self.difficulty):
            for x in range(self.difficulty):
                # 创建拼图块的矩形区域
                piece_rect = pygame.Rect(x * piece_width, y * piece_height, piece_width, piece_height)
                # 切割图片
                piece_image = self.original_image.subsurface(piece_rect)
                # 记录正确位置
                correct_pos = (x, y)
                # 计算拼图块在游戏面板中的位置
                start_x = self.panel_x + (self.panel_w - image_rect.width) // 2
                start_y = self.panel_y + 80
                current_pos = (x, y)
                # 创建拼图块对象
                piece = {
                    'image': piece_image,
                    'correct_pos': correct_pos,
                    'current_pos': current_pos,
                    'rect': pygame.Rect(
                        start_x + x * piece_width,
                        start_y + y * piece_height,
                        piece_width,
                        piece_height
                    ),
                    'empty': False  # 标记是否为空块
                }
                self.pieces.append(piece)
        # 取消空块，所有块都是图片块
        pass

    def shuffle_pieces(self):
        """打乱拼图块的位置"""
        # 随机打乱所有拼图块的位置
        piece_positions = [(x, y) for y in range(self.difficulty) for x in range(self.difficulty)]
        random.shuffle(piece_positions)
        # 确保至少有一个块位置不同（避免已经完成的情况）
        original_positions = [piece['correct_pos'] for piece in self.pieces]
        while piece_positions == original_positions:
            random.shuffle(piece_positions)
        # 分配打乱后的位置
        for i, piece in enumerate(self.pieces):
            piece['current_pos'] = piece_positions[i]
        # 更新拼图块的矩形位置
        self.update_piece_rects()

    def update_piece_rects(self):
        """更新拼图块的矩形位置"""
        if not self.original_image:
            return
        image_rect = self.original_image.get_rect()
        piece_width = image_rect.width // self.difficulty
        piece_height = image_rect.height // self.difficulty
        start_x = self.panel_x + (self.panel_w - image_rect.width) // 2
        start_y = self.panel_y + 80
        for piece in self.pieces:
            x, y = piece['current_pos']
            piece['rect'].x = start_x + x * piece_width
            piece['rect'].y = start_y + y * piece_height

    def check_completion(self):
        """检查拼图是否完成"""
        for piece in self.pieces:
            if piece['current_pos'] != piece['correct_pos']:
                return False
        return True

    def handle_event(self, event):
        """处理游戏事件"""
        if self.show_image_selector:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_pos = event.pos
                # 检查是否点击了返回按钮
                back_btn_rect = pygame.Rect(self.panel_x + self.panel_w - 130, self.panel_y + self.panel_h - 60, 110, 45)
                if back_btn_rect.collidepoint(mouse_pos):
                    self.parent.page = 'main'
                    return
                # 检查是否点击了图片缩略图
                pintu_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'pintu')
                thumb_margin = 15
                cols = 5  # 与绘制时保持一致
                # 计算起始x坐标，使缩略图区域居中
                total_width = cols * (self.thumbnail_size[0] + thumb_margin) - thumb_margin
                start_x = self.panel_x + (self.panel_w - total_width) // 2
                start_y = self.panel_y + 70
                for i, image_file in enumerate(self.image_files):
                    row = i // cols
                    col = i % cols
                    x = start_x + col * (self.thumbnail_size[0] + thumb_margin)
                    y = start_y + row * (self.thumbnail_size[1] + thumb_margin)
                    # 考虑缩略图背景和边框的偏移
                    thumb_rect = pygame.Rect(x - 2, y - 2, self.thumbnail_size[0] + 4, self.thumbnail_size[1] + 4)
                    if thumb_rect.collidepoint(mouse_pos):
                        self.selected_image_index = i
                        self.load_selected_image()
                        self.create_pieces()
                        self.shuffle_pieces()
                        self.show_image_selector = False
                        self.completed = False  # 重置完成状态
                        self.start_time = time.time()
                        self.moves = 0
                        return
        else:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # 鼠标左键点击
                mouse_pos = event.pos
                # 检查是否点击了返回按钮
                back_btn_rect = pygame.Rect(self.panel_x + self.panel_w - 130, self.panel_y + self.panel_h - 60, 110, 45)
                if back_btn_rect.collidepoint(mouse_pos):
                    self.parent.page = 'main'
                    return
                # 检查是否点击了重新开始按钮
                restart_btn_rect = pygame.Rect(self.panel_x + 20, self.panel_y + self.panel_h - 60, 130, 45)
                if restart_btn_rect.collidepoint(mouse_pos):
                    self.reset_game()
                    return
                # 检查是否点击了更换图片按钮
                change_image_btn_rect = pygame.Rect(self.panel_x + 430, self.panel_y + self.panel_h - 60, 130, 45)
                if change_image_btn_rect.collidepoint(mouse_pos):
                    self.show_image_selector = True
                    return
                # 检查是否点击了难度按钮
                easy_btn_rect = pygame.Rect(self.panel_x + 160, self.panel_y + self.panel_h - 60, 80, 45)
                if easy_btn_rect.collidepoint(mouse_pos):
                    self.difficulty = 3
                    self.reset_game()
                    return
                medium_btn_rect = pygame.Rect(self.panel_x + 250, self.panel_y + self.panel_h - 60, 80, 45)
                if medium_btn_rect.collidepoint(mouse_pos):
                    self.difficulty = 4
                    self.reset_game()
                    return
                hard_btn_rect = pygame.Rect(self.panel_x + 340, self.panel_y + self.panel_h - 60, 80, 45)
                if hard_btn_rect.collidepoint(mouse_pos):
                    self.difficulty = 5
                    self.reset_game()
                    return
                # 检查是否点击了拼图块
                if not self.completed:
                    for piece in self.pieces:
                        if piece['rect'].collidepoint(mouse_pos):
                            if not self.selected_piece:
                                # 第一次选中拼图块（可以是空块）
                                self.selected_piece = piece
                                self.selected_piece['original_pos'] = piece['rect'].topleft
                            else:
                                # 第二次选中拼图块，交换位置
                                if self.selected_piece != piece:
                                        # 开始交换动画
                                    self.swapping = True
                                    self.swap_pieces = [self.selected_piece, piece]
                                    self.swap_progress = 0
                                    # 交换位置
                                    self.selected_piece['current_pos'], piece['current_pos'] = piece['current_pos'], self.selected_piece['current_pos']
                                    self.update_piece_rects()
                                    self.moves += 1
                                    # 检查是否完成
                                    if self.check_completion():
                                        self.completed = True
                                        self.completion_time = time.time() - self.start_time
                                        # 更新玩家数据
                                        if 'pintu_best_score' not in player_data.data or self.moves < player_data.data['pintu_best_score']:
                                            player_data.data['pintu_best_score'] = self.moves
                                            player_data._save_data()
                                # 取消选中
                                self.selected_piece = None
                            break
            elif event.type == pygame.MOUSEMOTION and self.selected_piece:
                # 鼠标移动，拖动拼图块
                self.selected_piece['rect'].center = event.pos
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1 and self.selected_piece:
                # 鼠标左键释放，尝试放置拼图块
                placed = False
                # 检查是否可以放置到其他拼图块的位置
                # 找到鼠标释放位置下方的拼图块
                mouse_pos = event.pos
                target_piece = None
                for piece in self.pieces:
                    if piece != self.selected_piece and piece['rect'].collidepoint(mouse_pos):
                        target_piece = piece
                        break
                if target_piece:
                    # 开始交换动画
                    self.swapping = True
                    self.swap_pieces = [self.selected_piece, target_piece]
                    self.swap_progress = 0
                    # 交换位置
                    self.selected_piece['current_pos'], target_piece['current_pos'] = target_piece['current_pos'], self.selected_piece['current_pos']
                    self.update_piece_rects()
                    self.moves += 1
                    # 检查是否完成
                    if self.check_completion():
                        self.completed = True
                        self.completion_time = time.time() - self.start_time
                        # 更新玩家数据
                        if 'pintu_best_score' not in player_data.data or self.moves < player_data.data['pintu_best_score']:
                            player_data.data['pintu_best_score'] = self.moves
                            player_data._save_data()
                    placed = True
                # 如果没有放置成功，则放回原位
                if not placed and hasattr(self.selected_piece, 'original_pos'):
                    self.selected_piece['rect'].topleft = self.selected_piece['original_pos']
                    del self.selected_piece['original_pos']
                self.selected_piece = None
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.parent.page = 'main'

    def reset_game(self):
        """重置游戏"""
        self.is_running = True
        self.selected_piece = None
        self.completed = False
        self.start_time = time.time()
        self.moves = 0
        self.create_pieces()
        self.shuffle_pieces()

    def draw(self):
        """绘制游戏界面"""
        # 绘制背景
        self.surface.fill(BACKGROUND_COLOR)
        if self.show_image_selector:
            # 绘制标题
            title_text = self.title_font.render("选择拼图图片", True, (66, 165, 245))
            title_rect = title_text.get_rect(center=(self.panel_x + self.panel_w // 2, self.panel_y + 40))
            self.surface.blit(title_text, title_rect)
            # 绘制图片选择区域背景
            selection_area_rect = pygame.Rect(self.panel_x + 20, self.panel_y + 60, self.panel_w - 40, self.panel_h - 140)
            pygame.draw.rect(self.surface, (245, 245, 245), selection_area_rect, border_radius=10)
            pygame.draw.rect(self.surface, (200, 200, 200), selection_area_rect, 1, border_radius=10)

            # 绘制图片缩略图
            pintu_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'pintu')
            thumb_margin = 15
            cols = 5  # 增加列数使布局更紧凑
            # 计算起始x坐标，使缩略图区域居中
            total_width = cols * (self.thumbnail_size[0] + thumb_margin) - thumb_margin
            start_x = self.panel_x + (self.panel_w - total_width) // 2
            start_y = self.panel_y + 70

            for i, image_file in enumerate(self.image_files):
                try:
                    row = i // cols
                    col = i % cols
                    x = start_x + col * (self.thumbnail_size[0] + thumb_margin)
                    y = start_y + row * (self.thumbnail_size[1] + thumb_margin)
                    
                    # 绘制缩略图背景
                    pygame.draw.rect(self.surface, (255, 255, 255), (x - 2, y - 2, self.thumbnail_size[0] + 4, self.thumbnail_size[1] + 4), border_radius=5)
                    pygame.draw.rect(self.surface, (220, 220, 220), (x - 2, y - 2, self.thumbnail_size[0] + 4, self.thumbnail_size[1] + 4), 1, border_radius=5)
                     
                    # 加载并缩放图片为缩略图
                    image = pygame.image.load(os.path.join(pintu_dir, image_file))
                    image = pygame.transform.scale(image, self.thumbnail_size)
                    self.surface.blit(image, (x, y))
                    
                    # 绘制选中效果
                    if i == self.selected_image_index:
                        # 选中时显示彩色边框和阴影效果
                        pygame.draw.rect(self.surface, (66, 165, 245), (x - 3, y - 3, self.thumbnail_size[0] + 6, self.thumbnail_size[1] + 6), 3, border_radius=6)
                        # 添加轻微缩放效果突出选中状态
                        scaled_image = pygame.transform.scale(image, (int(self.thumbnail_size[0] * 1.05), int(self.thumbnail_size[1] * 1.05)))
                        scaled_x = x - (scaled_image.get_width() - self.thumbnail_size[0]) // 2
                        scaled_y = y - (scaled_image.get_height() - self.thumbnail_size[1]) // 2
                        self.surface.blit(scaled_image, (scaled_x, scaled_y))
                    else:
                        # 未选中时显示简单边框
                        pygame.draw.rect(self.surface, (200, 200, 200), (x - 1, y - 1, self.thumbnail_size[0] + 2, self.thumbnail_size[1] + 2), 1, border_radius=3)

                except Exception as e:
                    print(f"加载缩略图出错: {e}")
            # 绘制返回按钮
            back_btn_rect = pygame.Rect(self.panel_x + self.panel_w - 130, self.panel_y + self.panel_h - 60, 110, 45)
            pygame.draw.rect(self.surface, (220, 220, 220), back_btn_rect, border_radius=10)
            pygame.draw.rect(self.surface, (0, 0, 0), back_btn_rect, 2, border_radius=10)
            back_text = self.font.render("返回", True, (0, 0, 0))
            back_rect = back_text.get_rect(center=back_btn_rect.center)
            self.surface.blit(back_text, back_rect)
        else:
            # 绘制标题
            title_text = self.title_font.render("拼图游戏", True, (66, 165, 245))
            title_rect = title_text.get_rect(center=(self.panel_x + self.panel_w // 2, self.panel_y + 40))
            self.surface.blit(title_text, title_rect)
            # 绘制拼图块
            if self.swapping and len(self.swap_pieces) == 2:
                # 绘制交换动画
                piece1, piece2 = self.swap_pieces
                # 计算动画位置
                x1, y1 = piece1['rect'].topleft
                x2, y2 = piece2['rect'].topleft
                # 插值计算
                progress = self.swap_progress
                # 缓动函数 - 先快后慢
                progress = 1 - (1 - progress) ** 3
                # 计算当前位置
                curr_x1 = x1 + (x2 - x1) * progress
                curr_y1 = y1 + (y2 - y1) * progress
                curr_x2 = x2 + (x1 - x2) * progress
                curr_y2 = y2 + (y1 - y2) * progress
                # 绘制交换中的拼图块
                self.surface.blit(piece1['image'], (curr_x1, curr_y1))
                self.surface.blit(piece2['image'], (curr_x2, curr_y2))
                # 绘制边框
                pygame.draw.rect(self.surface, (255, 255, 0), (curr_x1, curr_y1, piece1['rect'].width, piece1['rect'].height), 3)
                pygame.draw.rect(self.surface, (255, 255, 0), (curr_x2, curr_y2, piece2['rect'].width, piece2['rect'].height), 3)
                # 绘制其他拼图块
                for piece in self.pieces:
                    if piece != piece1 and piece != piece2:
                        self.surface.blit(piece['image'], piece['rect'])
                        pygame.draw.rect(self.surface, (0, 0, 0), piece['rect'], 1)
            else:
                # 正常绘制拼图块
                for piece in self.pieces:
                    self.surface.blit(piece['image'], piece['rect'])
                    # 绘制边框
                    if piece == self.selected_piece:
                        # 高亮选中的拼图块
                        pygame.draw.rect(self.surface, (255, 255, 0), piece['rect'], 3)
                    else:
                        pygame.draw.rect(self.surface, (0, 0, 0), piece['rect'], 1)
            # 绘制游戏信息
            moves_text = self.font.render(f"步数: {self.moves}", True, (0, 0, 0))
            self.surface.blit(moves_text, (self.panel_x + 20, self.panel_y + 20))
            # 绘制最佳成绩
            best_score = player_data.data.get('pintu_best_score', 999)
            best_text = self.font.render(f"最佳步数: {best_score}", True, (0, 0, 0))
            self.surface.blit(best_text, (self.panel_x + 150, self.panel_y + 20))
            # 绘制难度
            difficulty_text = self.font.render(f"难度: {self.difficulty}x{self.difficulty}", True, (0, 0, 0))
            self.surface.blit(difficulty_text, (self.panel_x + 300, self.panel_y + 20))
            # 如果游戏完成，显示完成信息
            if self.completed:
                # 绘制完成文本到底部区域
                complete_text1 = self.title_font.render("恭喜完成!", True, (66, 165, 245))
                complete_rect1 = complete_text1.get_rect(center=(self.panel_x + self.panel_w // 2, self.panel_y + self.panel_h - 120))
                self.surface.blit(complete_text1, complete_rect1)
                complete_text2 = self.font.render(f"用时: {self.completion_time:.1f}秒", True, (0, 0, 0))
                complete_rect2 = complete_text2.get_rect(center=(self.panel_x + self.panel_w // 2, self.panel_y + self.panel_h - 80))
                self.surface.blit(complete_text2, complete_rect2)
                complete_text3 = self.font.render(f"步数: {self.moves}", True, (0, 0, 0))
                complete_rect3 = complete_text3.get_rect(center=(self.panel_x + self.panel_w // 2, self.panel_y + self.panel_h - 40))
                self.surface.blit(complete_text3, complete_rect3)
            # 绘制按钮
            # 返回按钮
            back_btn_rect = pygame.Rect(self.panel_x + self.panel_w - 130, self.panel_y + self.panel_h - 60, 110, 45)
            pygame.draw.rect(self.surface, (220, 220, 220), back_btn_rect, border_radius=10)
            pygame.draw.rect(self.surface, (0, 0, 0), back_btn_rect, 2, border_radius=10)
            back_text = self.font.render("返回", True, (0, 0, 0))
            back_rect = back_text.get_rect(center=back_btn_rect.center)
            self.surface.blit(back_text, back_rect)
            # 重新开始按钮
            restart_btn_rect = pygame.Rect(self.panel_x + 20, self.panel_y + self.panel_h - 60, 130, 45)
            pygame.draw.rect(self.surface, (220, 220, 220), restart_btn_rect, border_radius=10)
            pygame.draw.rect(self.surface, (0, 0, 0), restart_btn_rect, 2, border_radius=10)
            restart_text = self.font.render("重新开始", True, (0, 0, 0))
            restart_rect = restart_text.get_rect(center=restart_btn_rect.center)
            self.surface.blit(restart_text, restart_rect)
            # 更换图片按钮
            change_image_btn_rect = pygame.Rect(self.panel_x + 430, self.panel_y + self.panel_h - 60, 130, 45)
            pygame.draw.rect(self.surface, (220, 220, 220), change_image_btn_rect, border_radius=10)
            pygame.draw.rect(self.surface, (0, 0, 0), change_image_btn_rect, 2, border_radius=10)
            change_image_text = self.font.render("更换图片", True, (0, 0, 0))
            change_image_rect = change_image_text.get_rect(center=change_image_btn_rect.center)
            self.surface.blit(change_image_text, change_image_rect)
            # 难度按钮
            easy_btn_rect = pygame.Rect(self.panel_x + 160, self.panel_y + self.panel_h - 60, 80, 45)
            pygame.draw.rect(self.surface, (144, 238, 144) if self.difficulty == 3 else (220, 220, 220), easy_btn_rect, border_radius=10)
            pygame.draw.rect(self.surface, (0, 0, 0), easy_btn_rect, 2, border_radius=10)
            easy_text = self.font.render("简单", True, (0, 0, 0))
            easy_rect = easy_text.get_rect(center=easy_btn_rect.center)
            self.surface.blit(easy_text, easy_rect)
            medium_btn_rect = pygame.Rect(self.panel_x + 250, self.panel_y + self.panel_h - 60, 80, 45)
            pygame.draw.rect(self.surface, (144, 238, 144) if self.difficulty == 4 else (220, 220, 220), medium_btn_rect, border_radius=10)
            pygame.draw.rect(self.surface, (0, 0, 0), medium_btn_rect, 2, border_radius=10)
            medium_text = self.font.render("中等", True, (0, 0, 0))
            medium_rect = medium_text.get_rect(center=medium_btn_rect.center)
            self.surface.blit(medium_text, medium_rect)
            hard_btn_rect = pygame.Rect(self.panel_x + 340, self.panel_y + self.panel_h - 60, 80, 45)
            pygame.draw.rect(self.surface, (144, 238, 144) if self.difficulty == 5 else (220, 220, 220), hard_btn_rect, border_radius=10)
            pygame.draw.rect(self.surface, (0, 0, 0), hard_btn_rect, 2, border_radius=10)
            hard_text = self.font.render("困难", True, (0, 0, 0))
            hard_rect = hard_text.get_rect(center=hard_btn_rect.center)
            self.surface.blit(hard_text, hard_rect)

    def run(self):
        """运行游戏主循环"""
        clock = pygame.time.Clock()
        while self.is_running:
            for event in pygame.event.get():
                self.handle_event(event)
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
            # 处理交换动画
            if self.swapping:
                self.swap_progress += 0.1
                if self.swap_progress >= 1.0:
                    self.swapping = False
                    self.swap_pieces = []
                    self.swap_progress = 0
            self.draw()
            pygame.display.flip()
            clock.tick(FPS)