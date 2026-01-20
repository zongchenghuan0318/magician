import pygame
from .constants import *
from .player import player_data
import math
import time
import datetime

def draw_rounded_rect(surface, rect, color, corner_radius, shadow=False):
    if not isinstance(rect, pygame.Rect):
        rect = pygame.Rect(rect)
    if shadow:
        shadow_surf = pygame.Surface((rect.width+12, rect.height+12), pygame.SRCALPHA)
        pygame.draw.rect(shadow_surf, (30,60,120,60), (6,6,rect.width,rect.height), border_radius=corner_radius+6)
        surface.blit(shadow_surf, (rect.x-6, rect.y-6))
    shape_surf = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(shape_surf, color, (0,0,rect.width,rect.height), border_radius=corner_radius)
    surface.blit(shape_surf, rect)

class ActivityPage:
    def __init__(self, surface, audio_manager=None):
        self.surface = surface
        self.audio_manager = audio_manager  # 添加音频管理器
        self.is_open = False
        self.page = "main"
        from game.constants import WINDOW_WIDTH, WINDOW_HEIGHT
        self.panel_w = int(WINDOW_WIDTH * 0.80)
        self.panel_h = int(WINDOW_HEIGHT * 0.96)
        self.panel_x = (WINDOW_WIDTH - self.panel_w) // 2
        self.panel_y = (WINDOW_HEIGHT - self.panel_h) // 2
        self.start_time = None
        self.signin_page = SignInPage(surface, self)
        # 重新设计的滚动系统
        self.scroll_offset = 0
        self.scroll_max = 0
        self.scroll_step = 100
        self.content_height = 0  # 实际内容高度
        self.viewport_height = 0  # 可视区域高度
        self.card_count = 0  # 卡片数量
        self.card_height = 150  # 单个卡片高度
        self.card_spacing = 30  # 卡片间距
        self._card_rects = {}
        self._mouse_down_pos = None
        self._mouse_dragging = False

    def open(self):
        self.is_open = True
        self.start_time = time.time()
        self.page = "main"
        self.signin_page.reset_msg()

    def close(self):
        self.is_open = False

    def calculate_scroll_range(self, last_y, content_rect):
        """重新设计的滚动范围计算"""
        # 精确计算实际内容高度
        actual_content_height = last_y - content_rect.y
        self.content_height = actual_content_height +2000  # 大幅增加底部边距，确保能滚动到所有内容
        self.viewport_height = content_rect.height

        # 计算最大滚动距离
        self.scroll_max = max(0, self.content_height - self.viewport_height)

        # 确保当前滚动位置在有效范围内
        self.scroll_offset = max(0, min(self.scroll_offset, self.scroll_max))

        # 调试信息（已禁用）
        # print(f"实际内容高度: {actual_content_height}, 总内容高度: {self.content_height}")
        # print(f"视口高度: {self.viewport_height}, 最大滚动: {self.scroll_max}")

    def get_activity_count(self):
        """获取活动数量"""
        return 11  # 当前活动数量（新增2048游戏）

    def get_estimated_content_height(self):
        """精确估算内容高度"""
        # 卡片数量
        card_count = self.get_activity_count()

        # 每个卡片的实际占用空间：150像素高度 + 30像素间距
        # 但最后一个卡片后面还有额外的底部边距
        total_cards_height = card_count * 150  # 所有卡片的高度
        total_spacing = (card_count - 1) * 30  # 卡片间的间距（最后一个卡片后面没有间距）
        bottom_margin = 900  # 大幅增加底部边距，确保能滚动到最后的卡片（相当于5个卡片的高度）

        total_height = total_cards_height + total_spacing + bottom_margin

        # 调试信息已禁用
        # print(f"卡片数量: {card_count}, 卡片总高度: {total_cards_height}, 间距总高度: {total_spacing}, 底部边距: {bottom_margin}, 总高度: {total_height}")

        return total_height

    def draw(self):
        if self.page == "main":
            grad = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
            for y in range(WINDOW_HEIGHT):
                c = 245 - int(60 * y / WINDOW_HEIGHT)
                pygame.draw.line(grad, (c, c+8, 255, 255), (0, y), (WINDOW_WIDTH, y))
            self.surface.blit(grad, (0, 0))
            panel_rect = pygame.Rect(self.panel_x, self.panel_y, self.panel_w, self.panel_h)
            draw_rounded_rect(self.surface, panel_rect, (255,255,255,230), 28, shadow=True)
            # 标题栏固定
            icon_center = (self.panel_x + self.panel_w // 2, self.panel_y + 40)
            self.draw_gift_icon(self.surface, icon_center, 44)
            title_font = pygame.font.Font(FONT_NAME, 40)
            title_text = title_font.render("活动", True, (66, 165, 245))
            title_rect = title_text.get_rect(center=(self.panel_x + self.panel_w // 2, self.panel_y + 90))
            self.surface.blit(title_text, title_rect)
            for i in range(4):
                pygame.draw.line(self.surface, (66, 165, 245, 180-40*i), (self.panel_x+60, self.panel_y+140+i), (self.panel_x+self.panel_w-60, self.panel_y+140+i), 2)
            close_rect = self.get_close_rect()
            mouse_pos = pygame.mouse.get_pos()
            is_hover = close_rect.collidepoint(mouse_pos)
            pygame.draw.circle(self.surface, (220, 0, 0) if not is_hover else (255,80,80), close_rect.center, 18)
            x_font = pygame.font.Font(FONT_NAME, 28)
            x_text = x_font.render("×", True, (255,255,255))
            x_rect = x_text.get_rect(center=close_rect.center)
            self.surface.blit(x_text, x_rect)
            # 滚动内容区
            content_rect = pygame.Rect(self.panel_x+8, self.panel_y+60, self.panel_w-16, self.panel_h-80)
            clip = self.surface.get_clip()
            self.surface.set_clip(content_rect)
            self._card_rects = {}
            y = content_rect.y - self.scroll_offset
            y = self.draw_activity_card(y, content_rect, 'signin', '每日签到', '每日签到领奖励，连续签到有额外奖励', (33,150,243), (120,180,255), '签到', 'gift')
            y = self.draw_activity_card(y, content_rect, 'whackamole', '打地鼠活动', '限时打地鼠，赢金币奖励！', (255,152,0), (255,236,179), '进入', 'hammer')
            # 新增扫雷活动卡片
            y = self.draw_activity_card(y, content_rect, 'minesweeper', '扫雷游戏', '经典扫雷，挑战你的逻辑推理！', (76,175,80), (200,255,200), '进入', 'mine')
            # 新增弹球游戏活动卡片
            y = self.draw_activity_card(y, content_rect, 'pong', '弹球游戏', '经典弹球，击碎砖块赢金币！', (156,39,176), (230,200,255), '进入', 'ball')
            # 新增24点游戏卡片
            y = self.draw_activity_card(y, content_rect, 'twentyfour', '24点游戏', '用四张牌通过加减乘除算出24，赢奖励！', (255,87,34), (255,235,205), '进入', '24')
            # 新增"尽请期待"占位活动卡片（不可点击）
            y = self.draw_activity_card(y, content_rect, 'linkgame', '连连看', '经典连连看，考验你的眼力和记忆力！', (255,87,34), (255,224,178), '进入', 'link')
            # 新增走迷宫游戏卡片
            y = self.draw_activity_card(y, content_rect, 'maze', '走迷宫挑战', '6个难度等级，自动生成迷宫，挑战你的路径规划！', (138,43,226), (220,200,255), '进入', 'maze')
            # 新增手残大师游戏卡片
            y = self.draw_activity_card(y, content_rect, 'piano', '手残大师', '节奏感挑战！用DFJK键击打黑块，考验你的反应速度！', (63,81,181), (159,168,218), '进入', 'piano')
            # 新增俄罗斯方块游戏卡片
            y = self.draw_activity_card(y, content_rect, 'tetris', '俄罗斯方块', '经典俄罗斯方块，挑战反应速度和空间思维！', (255,105,180), (255,200,230), '进入', 'tetris')
            # 新增2048游戏卡片
            y = self.draw_activity_card(y, content_rect, 'game2048', '2048游戏', '经典数字合成游戏，挑战你的策略思维！', (156,39,176), (230,200,255), '进入', '2048')
            y = self.draw_activity_card(y, content_rect, 'pintu', '拼图游戏', '将图片分割成块，重新组合成完整图片！', (76,175,80), (200,255,200), '进入', 'puzzle')
            # 新增数独游戏卡片
            y = self.draw_activity_card(y, content_rect, 'sudoku', '数独挑战', '经典数独游戏，锻炼你的逻辑思维能力！', (55,118,171), (187,222,251), '进入', 'sudoku')
            # 新增推箱子游戏卡片
            y = self.draw_activity_card(y, content_rect, 'sokoban', '推箱子挑战', '经典推箱子游戏，挑战你的空间思维能力！', (255,152,0), (255,236,179), '进入', 'sokoban')
            y = self.draw_activity_card(y, content_rect, 'comingsoon', '尽请期待', '更多精彩活动即将上线，敬请期待！', (180,180,180), (230,230,230), '', 'soon')
            # 重新计算滚动范围
            self.calculate_scroll_range(y, content_rect)
            self.surface.set_clip(clip)
            # 美观滚动条
            if self.scroll_max > 0:
                # 滚动条轨道
                track_rect = pygame.Rect(self.panel_x+self.panel_w-20, self.panel_y+80, 12, self.panel_h-120)
                pygame.draw.rect(self.surface, (200, 200, 200, 100), track_rect, border_radius=6)

                # 滚动条滑块
                available_height = self.panel_h - 120
                viewport_height = self.panel_h - 80
                content_height = self.content_height if hasattr(self, 'content_height') and self.content_height > 0 else viewport_height + self.scroll_max

                bar_h = max(20, int(available_height * viewport_height / content_height))
                bar_y = int(self.panel_y + 80 + (self.scroll_offset / self.scroll_max) * (available_height - bar_h))
                bar_rect = pygame.Rect(self.panel_x+self.panel_w-20, bar_y, 12, bar_h)

                # 滑块主体
                pygame.draw.rect(self.surface, (100, 150, 255, 200), bar_rect, border_radius=6)
                pygame.draw.rect(self.surface, (80, 120, 200), bar_rect, 2, border_radius=6)

                # 滚动提示
                if self.scroll_max > 0:
                    hint_font = pygame.font.Font(FONT_NAME, 16)
                    hint_text = hint_font.render("滚轮滚动", True, (150, 150, 150))
                    hint_rect = hint_text.get_rect(center=(self.panel_x + self.panel_w - 14, self.panel_y + self.panel_h - 30))
                    self.surface.blit(hint_text, hint_rect)
        # 其他页面
        if self.page == "signin":
            self.signin_page.draw()
        elif self.page == "whackamole":
            if not hasattr(self, 'whackamole_page'):
                from .whack_a_mole import WhackAMolePage
                self.whackamole_page = WhackAMolePage(self.surface, self)
            self.whackamole_page.draw()
            # 检查active状态，若为False则切回活动页
            if hasattr(self, 'whackamole_page') and getattr(self.whackamole_page, 'active', True) is False:
                self.page = 'main'
                del self.whackamole_page
        elif self.page == "minesweeper":
            if not hasattr(self, 'minesweeper_game'):
                from .minesweeper import MinesweeperGame
                self.minesweeper_game = MinesweeperGame(self.surface)
            self.minesweeper_game.draw()
            # 只负责绘制难度按钮和重开按钮，点击判定交由handle_event处理
            # 返回按钮 - 顶部布局，优先放在“笑脸-保护键”之间，其次“难度-笑脸”之间，否则退到顶栏下方
            surface_w, surface_h = self.surface.get_size()
            # 与 minesweeper 顶栏保持一致的参数
            diff_names = ['初级', '中级', '高级', '全屏']
            btn_gap = 8
            diff_btn_w = 64
            diff_start_x = 20
            diff_right = diff_start_x + len(diff_names) * (diff_btn_w + btn_gap) - btn_gap
            face_size = 32
            face_left = (surface_w - face_size) // 2
            face_right = face_left + face_size
            # 右侧保护按钮与计时器的估算位置（需与 minesweeper.py 保持一致）
            timer_w = 14*3 + 6*2
            protect_w = 90
            protect_left = surface_w - 20 - timer_w - 12 - protect_w
            lane_left = diff_right + 12
            lane_right = face_left - 12
            lane_width_left = max(0, lane_right - lane_left)
            lane2_left = face_right + 12
            lane2_right = protect_left - 12
            lane_width_right = max(0, lane2_right - lane2_left)
            top_btn_min_w, top_btn_max_w = 90, 110
            top_btn_h = 28
            # 选择放置位置：优先右侧通道，其次左侧通道，否则退到顶栏下方
            if lane_width_right >= top_btn_min_w:
                top_btn_w = min(top_btn_max_w, lane_width_right)
                btn_rect = pygame.Rect(lane2_left, 14, top_btn_w, top_btn_h)
            elif lane_width_left >= top_btn_min_w:
                top_btn_w = min(top_btn_max_w, lane_width_left)
                btn_rect = pygame.Rect(lane_left, 14, top_btn_w, top_btn_h)
            else:
                # 顶栏下方退让布局
                top_btn_w = 110
                x = self.panel_x + self.panel_w - top_btn_w - 12
                y = 60
                btn_rect = pygame.Rect(x, y, top_btn_w, top_btn_h)
            # 添加阴影效果 - 进一步透明
            shadow_rect = pygame.Rect(btn_rect.x+2, btn_rect.y+2, btn_rect.width, btn_rect.height)
            shadow_surface = pygame.Surface((shadow_rect.width, shadow_rect.height), pygame.SRCALPHA)
            pygame.draw.rect(shadow_surface, (0, 0, 0, 40), (0, 0, shadow_rect.width, shadow_rect.height), border_radius=12)
            self.surface.blit(shadow_surface, shadow_rect)
            # 主按钮背景 - 更透明
            button_surface = pygame.Surface((btn_rect.width, btn_rect.height), pygame.SRCALPHA)
            pygame.draw.rect(button_surface, (66, 165, 245, 120), (0, 0, btn_rect.width, btn_rect.height), border_radius=12)
            self.surface.blit(button_surface, btn_rect)
            # 添加高光效果 - 更透明
            highlight_rect = pygame.Rect(btn_rect.x+1, btn_rect.y+1, btn_rect.width-2, btn_rect.height//2)
            highlight_surface = pygame.Surface((highlight_rect.width, highlight_rect.height), pygame.SRCALPHA)
            pygame.draw.rect(highlight_surface, (100, 200, 255, 50), (0, 0, highlight_rect.width, highlight_rect.height), border_radius=12)
            self.surface.blit(highlight_surface, highlight_rect)
            # 按钮文字
            font = pygame.font.Font(FONT_NAME, 20)
            font.set_bold(True)
            text = font.render("返回", True, (255,255,255))
            text_rect = text.get_rect(center=btn_rect.center)
            # 添加文字阴影 - 更透明
            shadow_text = font.render("返回", True, (0, 0, 0, 60))
            shadow_rect = shadow_text.get_rect(center=(text_rect.centerx+1, text_rect.centery+1))
            self.surface.blit(shadow_text, shadow_rect)
            self.surface.blit(text, text_rect)
        elif self.page == "pong":
            from .pong_game import PongGame
            if not hasattr(self, 'pong_game'):
                self.pong_game = PongGame(self.surface)
                self.pong_game.game_state = "level_select"
                self.pong_game.selected_level = 1
            self.pong_game.draw()
            # 检查active状态，若为False则切回活动页
            if hasattr(self, 'pong_game') and getattr(self.pong_game, 'active', True) is False:
                self.page = 'main'
                del self.pong_game
            # 删除弹球游戏返回按钮的绘制
            # （原有返回按钮相关代码已移除）
        elif self.page == "linkgame":
            if not hasattr(self, 'linkgame_page'):
                from .link_game import LinkGamePage
                self.linkgame_page = LinkGamePage(self.surface, self)
            self.linkgame_page.draw()
        elif self.page == "twentyfour":
            if not hasattr(self, 'twentyfour_page'):
                from .twentyfour_game import TwentyFourPage
                self.twentyfour_page = TwentyFourPage(self.surface, self)
            self.twentyfour_page.draw()
        elif self.page == "maze":
            if not hasattr(self, 'maze_game'):
                from .maze_game import MazeGame
                self.maze_game = MazeGame(self.surface)
            self.maze_game.draw()
            # 检查active状态，若为False则切回活动页
            if hasattr(self, 'maze_game') and getattr(self.maze_game, 'active', True) is False:
                self.page = 'main'
                del self.maze_game
        elif self.page == "piano":
            if not hasattr(self, 'piano_game'):
                from .piano_tiles import PianoTilesGame
                self.piano_game = PianoTilesGame(self.surface)
            self.piano_game.update()
            self.piano_game.draw()
            # 检查active状态，若为False则切回活动页
            if hasattr(self, 'piano_game') and getattr(self.piano_game, 'active', True) is False:
                self.page = 'main'
                del self.piano_game
        elif self.page == "tetris":
            if not hasattr(self, 'tetris_game'):
                from .tetris_game import TetrisGame
                self.tetris_game = TetrisGame(self.surface)
            self.tetris_game.update()
            self.tetris_game.handle_key_repeat()
            self.tetris_game.draw()
            # 检查active状态，若为False则切回活动页
            if hasattr(self, 'tetris_game') and getattr(self.tetris_game, 'active', True) is False:
                self.page = 'main'
                del self.tetris_game
        elif self.page == "game2048":
            if not hasattr(self, 'game2048'):
                from .game_2048 import Game2048
                self.game2048 = Game2048(self.surface)
            self.game2048.draw()
            # 检查active状态，若为False则切回活动页
            if hasattr(self, 'game2048') and getattr(self.game2048, 'active', True) is False:
                self.page = 'main'
                del self.game2048
        elif self.page == "pintu":
            if not hasattr(self, 'pintu_game'):
                from .pintu_game import PintuGame
                self.pintu_game = PintuGame(self.surface, self)
            self.pintu_game.draw()
            # 检查active状态，若为False则切回活动页
            if hasattr(self, 'pintu_game') and getattr(self.pintu_game, 'active', True) is False:
                self.page = 'main'
                del self.pintu_game
        elif self.page == "sudoku":
            if not hasattr(self, 'sudoku_game'):
                from .sudoku_game import SudokuGame
                self.sudoku_game = SudokuGame(self.surface)
            self.sudoku_game.draw()
            # 检查active状态，若为False则切回活动页
            if hasattr(self, 'sudoku_game') and getattr(self.sudoku_game, 'active', True) is False:
                self.page = 'main'
                del self.sudoku_game
        elif self.page == "sokoban":
            if not hasattr(self, 'sokoban_game'):
                from .sokoban_game import SokobanGame
                self.sokoban_game = SokobanGame(self.surface)
            self.sokoban_game.update()
            self.sokoban_game.draw()
            # 检查active状态，若为False则切回活动页
            if hasattr(self, 'sokoban_game') and getattr(self.sokoban_game, 'active', True) is False:
                self.page = 'main'
                del self.sokoban_game

    def draw_activity_card(self, y, content_rect, key, title, desc, color, bg_color, btn_text, icon_type):
        card_h = 150
        card_rect = pygame.Rect(content_rect.x+2, y, content_rect.width-4, card_h)
        mouse_pos = pygame.mouse.get_pos()
        # “尽请期待”卡片不可点击高亮
        is_hover = card_rect.collidepoint(mouse_pos[0], mouse_pos[1]) and self.page == 'main' and key != 'comingsoon'
        # 背景
        draw_rounded_rect(self.surface, card_rect, bg_color if not is_hover else (bg_color[0],bg_color[1],bg_color[2],255), 32, shadow=True)
        # 图标
        icon_x = card_rect.x+48
        icon_y = card_rect.y+card_h//2
        if icon_type == 'gift':
            self.draw_gift_icon(self.surface, (icon_x, icon_y), 60)
        elif icon_type == 'hammer':
            pygame.draw.rect(self.surface, (255,193,7), (icon_x-20, icon_y-28, 40, 56), border_radius=14)
            pygame.draw.rect(self.surface, (255,152,0), (icon_x-10, icon_y-10, 20, 40), border_radius=8)
        elif icon_type == 'mine':
            pass
        elif icon_type == 'sudoku':
            # 绘制数独图标
            pygame.draw.rect(self.surface, (200,200,255), (icon_x-25, icon_y-25, 50, 50), border_radius=8)
            pygame.draw.rect(self.surface, (100,150,255), (icon_x-25, icon_y-25, 50, 50), 2, border_radius=8)
            # 绘制简单的数独图案
            for i in range(3):
                for j in range(3):
                    mini_x = icon_x - 18 + j * 12
                    mini_y = icon_y - 18 + i * 12
                    if (i + j) % 2 == 0:
                        pygame.draw.rect(self.surface, (100,150,255), (mini_x, mini_y, 8, 8))
            pygame.draw.circle(self.surface, (60,60,60), (icon_x, icon_y), 24)
            for i in range(8):
                angle = math.pi/4*i
                x1 = icon_x + int(32*math.cos(angle))
                y1 = icon_y + int(32*math.sin(angle))
                x2 = icon_x + int(16*math.cos(angle))
                y2 = icon_y + int(16*math.sin(angle))
                pygame.draw.line(self.surface, (80,80,80), (x1,y1), (x2,y2), 4)
            pygame.draw.circle(self.surface, (180,0,0), (icon_x, icon_y), 9)
        elif icon_type == 'ball':
            pygame.draw.circle(self.surface, (156,39,176), (icon_x, icon_y), 24)
            pygame.draw.line(self.surface, (156,39,176), (icon_x-12, icon_y), (icon_x+12, icon_y), 4)
            pygame.draw.line(self.surface, (156,39,176), (icon_x, icon_y-12), (icon_x, icon_y+12), 4)
            pygame.draw.circle(self.surface, (156,39,176), (icon_x, icon_y), 8)
        elif icon_type == 'soon':
            # “尽请期待”图标：沙漏
            pygame.draw.rect(self.surface, (180,180,180), (icon_x-16, icon_y-24, 32, 48), border_radius=12)
            pygame.draw.polygon(self.surface, (120,120,120), [(icon_x-12,icon_y-20),(icon_x+12,icon_y-20),(icon_x,icon_y)], 0)
            pygame.draw.polygon(self.surface, (120,120,120), [(icon_x-12,icon_y+20),(icon_x+12,icon_y+20),(icon_x,icon_y)], 0)
            pygame.draw.circle(self.surface, (220,220,220), (icon_x, icon_y), 8)
        elif icon_type == 'link':
            # 连连看图标：两个相交的圆
            pygame.draw.circle(self.surface, (255,87,34), (icon_x, icon_y), 24)
            pygame.draw.circle(self.surface, (255,87,34), (icon_x+12, icon_y), 24)
            pygame.draw.line(self.surface, (255,87,34), (icon_x, icon_y-12), (icon_x+12, icon_y-12), 4)
            pygame.draw.line(self.surface, (255,87,34), (icon_x, icon_y+12), (icon_x+12, icon_y+12), 4)
            pygame.draw.circle(self.surface, (255,87,34), (icon_x, icon_y), 8)
        elif icon_type == '24':
            # 24点图标：四张扑克牌叠放+数字24
            card_w, card_h = 22, 32
            for i in range(4):
                offset = i * 4
                pygame.draw.rect(self.surface, (255,255,255), (icon_x-18+offset, icon_y-16+offset, card_w, card_h), border_radius=6)
                pygame.draw.rect(self.surface, (200,200,200), (icon_x-18+offset, icon_y-16+offset, card_w, card_h), 2, border_radius=6)
            font = pygame.font.Font(FONT_NAME, 22)
            text = font.render('24', True, (255,87,34))
            self.surface.blit(text, (icon_x-8, icon_y+8))
        elif icon_type == 'maze':
            # 迷宫图标 - 简化的迷宫路径
            maze_size = 30
            maze_rect = pygame.Rect(icon_x - maze_size//2, icon_y - maze_size//2, maze_size, maze_size)
            # 外框
            pygame.draw.rect(self.surface, (255,255,255), maze_rect, 3)
            # 内部迷宫路径
            pygame.draw.line(self.surface, (255,255,255), (icon_x-12, icon_y-12), (icon_x-12, icon_y), 3)
            pygame.draw.line(self.surface, (255,255,255), (icon_x-12, icon_y), (icon_x, icon_y), 3)
            pygame.draw.line(self.surface, (255,255,255), (icon_x, icon_y), (icon_x, icon_y+12), 3)
            pygame.draw.line(self.surface, (255,255,255), (icon_x, icon_y+12), (icon_x+12, icon_y+12), 3)
            # 起点和终点
            pygame.draw.circle(self.surface, (100,255,100), (icon_x-12, icon_y-12), 4)
            pygame.draw.circle(self.surface, (255,215,0), (icon_x+12, icon_y+12), 4)
        elif icon_type == 'piano':
            # 手残大师图标 - 钢琴键盘
            key_width = 8
            key_height = 24
            # 白键
            for i in range(4):
                x = icon_x - 16 + i * key_width
                pygame.draw.rect(self.surface, (255,255,255), (x, icon_y-8, key_width-1, key_height))
                pygame.draw.rect(self.surface, (63,81,181), (x, icon_y-8, key_width-1, key_height), 1)
            # 黑键
            for i in range(3):
                x = icon_x - 12 + i * key_width + key_width//2
                pygame.draw.rect(self.surface, (30,30,30), (x, icon_y-8, key_width//2, key_height//2))
            # 音符
            pygame.draw.circle(self.surface, (63,81,181), (icon_x+8, icon_y-15), 3)
            pygame.draw.line(self.surface, (63,81,181), (icon_x+11, icon_y-15), (icon_x+11, icon_y-5), 2)
        elif icon_type == 'tetris':
            # 俄罗斯方块图标 - 几个不同颜色的方块
            block_size = 12
            blocks = [
                (icon_x-18, icon_y-12, (255,105,180)),  # 粉色
                (icon_x-6, icon_y-12, (0,255,255)),     # 青色
                (icon_x+6, icon_y-12, (255,255,0)),     # 黄色
                (icon_x-12, icon_y, (255,165,0)),       # 橙色
                (icon_x, icon_y, (0,0,255)),            # 蓝色
                (icon_x+12, icon_y, (0,255,0)),         # 绿色
                (icon_x-6, icon_y+12, (255,0,0))        # 红色
            ]
            for x, y, color in blocks:
                pygame.draw.rect(self.surface, color, (x, y, block_size, block_size))
                pygame.draw.rect(self.surface, (255,255,255), (x, y, block_size, block_size), 1)
        elif icon_type == '2048':
            # 2048图标 - 4x4网格，显示2048数字
            grid_size = 32
            cell_size = 6
            margin = 1
            
            # 绘制4x4网格背景
            grid_rect = pygame.Rect(icon_x - grid_size//2, icon_y - grid_size//2, grid_size, grid_size)
            pygame.draw.rect(self.surface, (187, 173, 160), grid_rect, border_radius=4)
            
            # 绘制网格线
            for i in range(1, 4):
                # 垂直线
                pygame.draw.line(self.surface, (205, 193, 180), 
                               (icon_x - grid_size//2 + i * (cell_size + margin), icon_y - grid_size//2),
                               (icon_x - grid_size//2 + i * (cell_size + margin), icon_y + grid_size//2), 1)
                # 水平线
                pygame.draw.line(self.surface, (205, 193, 180), 
                               (icon_x - grid_size//2, icon_y - grid_size//2 + i * (cell_size + margin)),
                               (icon_x + grid_size//2, icon_y - grid_size//2 + i * (cell_size + margin)), 1)
            
            # 绘制2048数字
            font = pygame.font.Font(FONT_NAME, 16)
            text = font.render('2048', True, (119, 110, 101))
            text_rect = text.get_rect(center=(icon_x, icon_y))
            self.surface.blit(text, text_rect)
        elif icon_type == 'puzzle':
            # 拼图图标：四分块拼图
            piece_size = 16
            # 左上块
            pygame.draw.rect(self.surface, (76, 175, 80), (icon_x-20, icon_y-20, piece_size, piece_size), border_radius=4)
            pygame.draw.rect(self.surface, (255, 255, 255), (icon_x-20, icon_y-20, piece_size, piece_size), 1, border_radius=4)
            # 右上块
            pygame.draw.rect(self.surface, (76, 175, 80), (icon_x-20+piece_size+4, icon_y-20, piece_size, piece_size), border_radius=4)
            pygame.draw.rect(self.surface, (255, 255, 255), (icon_x-20+piece_size+4, icon_y-20, piece_size, piece_size), 1, border_radius=4)
            # 左下块
            pygame.draw.rect(self.surface, (76, 175, 80), (icon_x-20, icon_y-20+piece_size+4, piece_size, piece_size), border_radius=4)
            pygame.draw.rect(self.surface, (255, 255, 255), (icon_x-20, icon_y-20+piece_size+4, piece_size, piece_size), 1, border_radius=4)
            # 右下块
            pygame.draw.rect(self.surface, (76, 175, 80), (icon_x-20+piece_size+4, icon_y-20+piece_size+4, piece_size, piece_size), border_radius=4)
            pygame.draw.rect(self.surface, (255, 255, 255), (icon_x-20+piece_size+4, icon_y-20+piece_size+4, piece_size, piece_size), 1, border_radius=4)
        elif icon_type == 'sokoban':
            # 推箱子图标：玩家和箱子
            # 绘制玩家
            pygame.draw.circle(self.surface, (55,118,171), (icon_x, icon_y), 12)
            # 绘制箱子
            pygame.draw.rect(self.surface, (255,152,0), (icon_x+15, icon_y-8, 16, 16), border_radius=4)
            pygame.draw.rect(self.surface, (255,255,255), (icon_x+15, icon_y-8, 16, 16), 1, border_radius=4)
            # 绘制目标点
            pygame.draw.rect(self.surface, (76,175,80), (icon_x+35, icon_y-8, 16, 16), border_radius=4)
            pygame.draw.rect(self.surface, (255,255,255), (icon_x+35, icon_y-8, 16, 16), 1, border_radius=4)
        # 标题
        font = pygame.font.Font(FONT_NAME, 36)
        title_text = font.render(title, True, color)
        self.surface.blit(title_text, (icon_x+70, card_rect.y+38))
        # 描述
        desc_font = pygame.font.Font(FONT_NAME, 24)
        desc_text = desc_font.render(desc, True, (80,80,80))
        self.surface.blit(desc_text, (icon_x+70, card_rect.y+88))
        # 大按钮（判定区扩大，视觉更明显）
        if key != 'comingsoon':
            btn_rect = pygame.Rect(card_rect.right-170, 0, 140, 64)
            btn_rect.centery = card_rect.centery
            btn_color = color if not is_hover else (min(color[0]+50,255), min(color[1]+50,255), min(color[2]+50,255))
            pygame.draw.rect(self.surface, btn_color, btn_rect, border_radius=20)
            btn_font = pygame.font.Font(FONT_NAME, 32)
            btn_text_surf = btn_font.render(btn_text, True, (255,255,255))
            btn_text_rect = btn_text_surf.get_rect(center=btn_rect.center)
            self.surface.blit(btn_text_surf, btn_text_rect)
        # 只允许按钮区域可点击
        if key != 'comingsoon':
            self._card_rects[key] = btn_rect
        return card_rect.bottom + 30

    def draw_gift_icon(self, surface, center, size):
        x, y = center
        box_w, box_h = size, size*0.6
        bow_h = size*0.28
        color = (66, 165, 245)
        pygame.draw.rect(surface, color, (x-box_w//2, y, box_w, box_h), border_radius=8)
        pygame.draw.rect(surface, (255,255,255), (x-box_w//2+box_w//2-5, y, 10, box_h), 0)
        pygame.draw.rect(surface, color, (x-box_w//2, y-bow_h, box_w, bow_h*0.7), border_radius=8)
        pygame.draw.ellipse(surface, (255,255,255), (x-18, y-bow_h-10, 18, 18), 3)
        pygame.draw.ellipse(surface, (255,255,255), (x+1, y-bow_h-10, 18, 18), 3)
        pygame.draw.circle(surface, (255,255,255), (x, int(y-bow_h+2)), 7)

    def get_close_rect(self):
        return pygame.Rect(self.panel_x+self.panel_w-44, self.panel_y+24, 36, 36)

    def handle_event(self, event):
        if self.page == "signin":
            self.signin_page.handle_event(event)
            return
        if self.page == "whackamole":
            if hasattr(self, 'whackamole_page'):
                self.whackamole_page.handle_event(event)
            return
        if self.page == "minesweeper":
            if hasattr(self, 'minesweeper_game'):
                self.minesweeper_game.handle_event(event)
            # 扫雷顶部难度按钮点击判定
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = event.pos
                # 难度按钮区域与draw一致
                surface_w, surface_h = self.surface.get_size()
                diff_names = list(['初级','中级','高级'])
                btn_gap = 30
                btn_w = 100
                btn_h = 48
                total_btn_w = btn_w * len(diff_names) + btn_gap * (len(diff_names)-1)
                btn_start_x = (surface_w - total_btn_w) // 2
                for i, name in enumerate(diff_names):
                    rect = pygame.Rect(btn_start_x + i*(btn_w+btn_gap), 28, btn_w, btn_h)
                    if rect.collidepoint(mouse_pos):
                        self.minesweeper_game.set_difficulty(name)
                        return
                # 重开按钮
                reset_rect = pygame.Rect(self.minesweeper_game.cols*32-100, 20, 80, 36)
                if reset_rect.collidepoint(mouse_pos):
                    self.minesweeper_game.reset()
                # 返回按钮（顶部优先，次选左侧通道，最后退到顶栏下方）
                surface_w, surface_h = self.surface.get_size()
                diff_names = ['初级', '中级', '高级', '全屏']
                btn_gap = 8
                diff_btn_w = 64
                diff_start_x = 20
                diff_right = diff_start_x + len(diff_names) * (diff_btn_w + btn_gap) - btn_gap
                face_size = 32
                face_left = (surface_w - face_size) // 2
                face_right = face_left + face_size
                timer_w = 14*3 + 6*2
                protect_w = 90
                protect_left = surface_w - 20 - timer_w - 12 - protect_w
                lane_left = diff_right + 12
                lane_right = face_left - 12
                lane_width_left = max(0, lane_right - lane_left)
                lane2_left = face_right + 12
                lane2_right = protect_left - 12
                lane_width_right = max(0, lane2_right - lane2_left)
                top_btn_min_w, top_btn_max_w = 90, 110
                top_btn_h = 28
                if lane_width_right >= top_btn_min_w:
                    top_btn_w = min(top_btn_max_w, lane_width_right)
                    btn_rect = pygame.Rect(lane2_left, 14, top_btn_w, top_btn_h)
                elif lane_width_left >= top_btn_min_w:
                    top_btn_w = min(top_btn_max_w, lane_width_left)
                    btn_rect = pygame.Rect(lane_left, 14, top_btn_w, top_btn_h)
                else:
                    top_btn_w = 110
                    x = self.panel_x + self.panel_w - top_btn_w - 12
                    y = 60
                    btn_rect = pygame.Rect(x, y, top_btn_w, top_btn_h)
                if btn_rect.collidepoint(mouse_pos):
                    self.page = 'main'
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.page = 'main'
            return
        if self.page == "pong":
            if hasattr(self, 'pong_game'):
                self.pong_game.handle_event(event)
            # 删除弹球游戏返回按钮的点击判定
            # if event.type == pygame.MOUSEBUTTONDOWN:
            #     mouse_pos = event.pos
            #     btn_rect = pygame.Rect(self.panel_x+self.panel_w-130, self.panel_y+self.panel_h-60, 110, 45)
            #     if btn_rect.collidepoint(mouse_pos):
            #         self.page = 'main'
            # if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            #     self.page = 'main'
            return
        if self.page == "linkgame":
            if hasattr(self, 'linkgame_page'):
                self.linkgame_page.handle_event(event)
            return
        if self.page == "twentyfour":
            if hasattr(self, 'twentyfour_page'):
                self.twentyfour_page.handle_event(event)
            return
        if self.page == "maze":
            if hasattr(self, 'maze_game'):
                self.maze_game.handle_event(event)
            return
        if self.page == "piano":
            if hasattr(self, 'piano_game'):
                self.piano_game.handle_event(event)
            return
        if self.page == "tetris":
            if hasattr(self, 'tetris_game'):
                self.tetris_game.handle_event(event)
            return
        if self.page == "game2048":
            if hasattr(self, 'game2048'):
                self.game2048.handle_event(event)
            return
        if self.page == "pintu":
            if hasattr(self, 'pintu_game'):
                self.pintu_game.handle_event(event)
            return
        if self.page == "sudoku":
            if hasattr(self, 'sudoku_game'):
                self.sudoku_game.handle_event(event)
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.page = 'main'
            return
        if self.page == "sokoban":
            if hasattr(self, 'sokoban_game'):
                self.sokoban_game.handle_event(event)
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.page = 'main'
            return
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.close()
            elif event.key == pygame.K_UP:
                # 上键向上滚动
                self.scroll_offset -= self.scroll_step
                self.scroll_offset = max(0, self.scroll_offset)
            elif event.key == pygame.K_DOWN:
                # 下键向下滚动
                # 使用更准确的内容高度估算
                estimated_content_height = self.get_estimated_content_height()
                viewport_height = self.panel_h - 80
                self.scroll_max = max(0, estimated_content_height - viewport_height)

                self.scroll_offset += self.scroll_step
                self.scroll_offset = min(self.scroll_offset, self.scroll_max)
            elif event.key == pygame.K_HOME:
                # Home键回到顶部
                self.scroll_offset = 0
            elif event.key == pygame.K_END:
                # End键滚动到底部
                estimated_content_height = self.get_estimated_content_height()
                viewport_height = self.panel_h - 80
                self.scroll_max = max(0, estimated_content_height - viewport_height)
                self.scroll_offset = self.scroll_max
        elif event.type == pygame.MOUSEBUTTONDOWN:
            self._mouse_down_pos = event.pos
            self._mouse_dragging = False
            if self.get_close_rect().collidepoint(event.pos):
                self.close()
            if hasattr(self, '_back_btn_rect') and self._back_btn_rect.collidepoint(event.pos):
                self.close()
        elif event.type == pygame.MOUSEMOTION:
            if self._mouse_down_pos:
                dx = abs(event.pos[0] - self._mouse_down_pos[0])
                dy = abs(event.pos[1] - self._mouse_down_pos[1])
                if dy > 8:
                    self._mouse_dragging = True
                    # 改进的拖拽滚动
                    drag_dy = event.pos[1] - self._mouse_down_pos[1]
                    self.scroll_offset -= drag_dy * 1.0  # 增加拖拽敏感度

                    # 使用更准确的内容高度估算
                    estimated_content_height = self.get_estimated_content_height()
                    viewport_height = self.panel_h - 80
                    self.scroll_max = max(0, estimated_content_height - viewport_height)

                    self.scroll_offset = max(0, min(self.scroll_offset, self.scroll_max))
                    self._mouse_down_pos = event.pos  # 更新鼠标位置
        elif event.type == pygame.MOUSEBUTTONUP:
            # 只处理左键松开
            if getattr(event, 'button', None) == 1 and self._mouse_down_pos and not self._mouse_dragging:
                for key, rect in self._card_rects.items():
                    if rect.collidepoint(event.pos):
                        if key == 'signin':
                            self.page = 'signin'
                        elif key == 'whackamole':
                            self.page = 'whackamole'
                        elif key == 'minesweeper':
                            self.page = 'minesweeper'
                        elif key == 'pong':
                            self.page = 'pong'
                        elif key == 'linkgame':
                            self.page = 'linkgame'
                            from .link_game import LinkGamePage
                            self.linkgame_page = LinkGamePage(self.surface, self)  # 每次都新建，自动弹出难度选择
                        elif key == 'twentyfour':
                            self.page = 'twentyfour'
                        elif key == 'maze':
                            self.page = 'maze'
                        elif key == 'piano':
                            self.page = 'piano'
                        elif key == 'tetris':
                            self.page = 'tetris'
                        elif key == 'game2048':
                            self.page = 'game2048'
                        elif key == 'pintu':
                            self.page = 'pintu'
                            from .pintu_game import PintuGame
                            self.pintu_game = PintuGame(self.surface, self)
                        elif key == 'sudoku':
                            self.page = 'sudoku'
                            from .sudoku_game import SudokuGame
                            self.sudoku_game = SudokuGame(self.surface, self)
                        elif key == 'sokoban':
                            self.page = 'sokoban'
                            from .sokoban_game import SokobanGame
                            self.sokoban_game = SokobanGame(self.surface)
                self._mouse_down_pos = None
                self._mouse_dragging = False
        elif event.type == pygame.MOUSEWHEEL:
            if self.page == 'main':
                # 改进的滚轮滚动
                scroll_amount = event.y * self.scroll_step
                self.scroll_offset -= scroll_amount

                # 使用更准确的内容高度估算
                estimated_content_height = self.get_estimated_content_height()
                viewport_height = self.panel_h - 80
                self.scroll_max = max(0, estimated_content_height - viewport_height)

                # 应用滚动限制
                self.scroll_offset = max(0, min(self.scroll_offset, self.scroll_max))

                # print(f"滚轮滚动: offset={self.scroll_offset}, max={self.scroll_max}")

            self._mouse_down_pos = None
            self._mouse_dragging = False

class SignInPage:
    def __init__(self, surface, parent):
        self.surface = surface
        self.parent = parent
        self.panel_x = parent.panel_x
        self.panel_y = parent.panel_y
        self.panel_w = parent.panel_w
        self.panel_h = parent.panel_h
        self.msg = ""
        self.msg_time = 0

    def reset_msg(self):
        self.msg = ""
        self.msg_time = 0

    def get_streak(self):
        return player_data.data.get("sign_in_streak", 0)

    def get_max_streak(self):
        return player_data.data.get("max_sign_in_streak", 0)

    def is_signed_today(self):
        last_date = player_data.data.get("last_signin_date", "")
        today = datetime.date.today().isoformat()
        return last_date == today

    def calc_reward(self, streak):
        return 300 + (streak-1)*100 if streak > 0 else 300

    def do_signin(self):
        today = datetime.date.today().isoformat()
        last_date = player_data.data.get("last_signin_date", "")
        last_streak = player_data.data.get("sign_in_streak", 0)
        # 判断是否断签
        if last_date:
            last_dt = datetime.date.fromisoformat(last_date)
            if (datetime.date.today() - last_dt).days == 1:
                streak = last_streak + 1
            elif (datetime.date.today() - last_dt).days == 0:
                self.msg = "今日已签到"
                self.msg_time = time.time()
                return
            else:
                streak = 1
        else:
            streak = 1
        reward = self.calc_reward(streak)
        player_data.data["last_signin_date"] = today
        player_data.data["sign_in_streak"] = streak
        if streak > player_data.data.get("max_sign_in_streak", 0):
            player_data.data["max_sign_in_streak"] = streak
        player_data.add_coins(reward)
        player_data._save_data()
        self.msg = f"+{reward} 金币，连续{streak}天！"
        self.msg_time = time.time()

    def draw(self):
        # 签到详情卡片
        card_rect = pygame.Rect(self.panel_x+60, self.panel_y+120, self.panel_w-120, 340)
        draw_rounded_rect(self.surface, card_rect, (187,222,251,230), 22, shadow=True)
        # 标题
        font = pygame.font.Font(FONT_NAME, 34)
        text = font.render("每日签到", True, (33, 150, 243))
        title_rect = text.get_rect(center=(card_rect.centerx, card_rect.y+38))
        self.surface.blit(text, title_rect)
        # 连续天数
        streak = self.get_streak()
        max_streak = self.get_max_streak()
        streak_font = pygame.font.Font(FONT_NAME, 26)
        streak_font.set_bold(True)
        streak_bg_rect = pygame.Rect(card_rect.x+40, card_rect.y+90, card_rect.width-80, 44)
        pygame.draw.rect(self.surface, (225,245,254), streak_bg_rect, border_radius=10)
        streak_text = streak_font.render(f"连续签到：{streak} 天", True, (66, 165, 245))
        self.surface.blit(streak_text, (streak_bg_rect.x+18, streak_bg_rect.y+6))
        max_text = streak_font.render(f"历史最高：{max_streak} 天", True, (120,120,120))
        self.surface.blit(max_text, (streak_bg_rect.x+260, streak_bg_rect.y+6))
        # 今日奖励
        reward = self.calc_reward(streak+1 if not self.is_signed_today() else streak)
        reward_font = pygame.font.Font(FONT_NAME, 26)
        reward_font.set_bold(True)
        reward_bg_rect = pygame.Rect(card_rect.x+40, card_rect.y+150, card_rect.width-80, 54)
        pygame.draw.rect(self.surface, (255,243,224), reward_bg_rect, border_radius=10)
        reward_text = reward_font.render(f"本次签到奖励：{reward} 金币", True, (255,140,0))
        self.surface.blit(reward_text, (reward_bg_rect.x+18, reward_bg_rect.y+10))
        # 签到按钮（更大更明显，靠下居中）
        btn_rect = pygame.Rect(card_rect.centerx-80, card_rect.y+230, 160, 56)
        mouse_pos = pygame.mouse.get_pos()
        is_hover = btn_rect.collidepoint(mouse_pos)
        btn_color = (66, 165, 245) if not self.is_signed_today() else (180, 180, 180)
        if is_hover and not self.is_signed_today():
            btn_color = (33, 150, 243)
        pygame.draw.rect(self.surface, btn_color, btn_rect, border_radius=16)
        btn_font = pygame.font.Font(FONT_NAME, 28)
        btn_font.set_bold(True)
        btn_text = "已签到" if self.is_signed_today() else "签到"
        text_color = (255,255,255) if not self.is_signed_today() else (220,220,220)
        text_surf = btn_font.render(btn_text, True, text_color)
        text_rect = text_surf.get_rect(center=btn_rect.center)
        self.surface.blit(text_surf, text_rect)
        self._signin_btn_rect = btn_rect
        # 返回按钮（更大，靠下居中，签到按钮下方）
        back_rect = pygame.Rect(card_rect.centerx-60, btn_rect.bottom+24, 120, 44)
        pygame.draw.rect(self.surface, (66, 165, 245), back_rect, border_radius=12)
        back_font = pygame.font.Font(FONT_NAME, 24)
        back_font.set_bold(True)
        back_text = back_font.render("返回", True, (255,255,255))
        back_text_rect = back_text.get_rect(center=back_rect.center)
        self.surface.blit(back_text, back_text_rect)
        self._back_btn_rect = back_rect
        # 签到提示
        if self.msg and time.time()-self.msg_time<2.5:
            tip_font = pygame.font.Font(FONT_NAME, 26)
            tip = tip_font.render(self.msg, True, (66, 165, 245))
            tip_rect = tip.get_rect(center=(self.panel_x+self.panel_w//2, card_rect.bottom+60))
            self.surface.blit(tip, tip_rect)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.parent.page = "main"
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if hasattr(self, '_signin_btn_rect') and self._signin_btn_rect.collidepoint(event.pos):
                if not self.is_signed_today():
                    self.do_signin()
            elif hasattr(self, '_back_btn_rect') and self._back_btn_rect.collidepoint(event.pos):
                self.parent.page = "main"