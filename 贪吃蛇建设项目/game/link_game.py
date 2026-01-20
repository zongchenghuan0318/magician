import pygame
import random
from .constants import WINDOW_WIDTH, WINDOW_HEIGHT, FONT_NAME
import math

class LinkGamePage:
    def __init__(self, surface, parent):
        self.surface = surface
        self.parent = parent
        self.panel_x = parent.panel_x
        self.panel_y = parent.panel_y
        self.panel_w = parent.panel_w
        self.panel_h = parent.panel_h
        self.level = None
        self.state = 'level_select'  # 'playing', 'win', 'fail'
        self.grid = []
        self.selected = []
        self.path = []
        self.rows = 8
        self.cols = 12
        self.tile_size = 48
        self.margin = 18
        self.levels = [
            {'name': '初级', 'rows': 6, 'cols': 8, 'types': 8},
            {'name': '中级', 'rows': 8, 'cols': 12, 'types': 12},
            {'name': '高级', 'rows': 10, 'cols': 16, 'types': 18},
        ]
        # 不生成棋盘，等用户选择难度后再生成
        self.hint_button_rect = None
        self.last_hint_time = 0
        self.hint_cooldown = 2000  # 2秒冷却
        self.animation_timer = 0
        self.pulsing_tiles = []
        self.path_clear_timer = 0  # 路径清除计时器
        
        # 加载连连看游戏音效
        self.load_sounds()
    
    def load_sounds(self):
        """加载连连看游戏音效"""
        try:
            # 尝试加载音效文件，如果找不到特定音效文件，使用默认音乐文件
            if not self.parent.audio_manager.load_sound('match', 'audio/match.mp3'):
                # 使用默认音乐文件作为匹配音效
                self.parent.audio_manager.load_sound('match', 'audio/wet_hands.mp3')
            if not self.parent.audio_manager.load_sound('win', 'audio/win.mp3'):
                # 使用默认音乐文件作为胜利音效
                self.parent.audio_manager.load_sound('win', 'audio/wet_hands.mp3')
            if not self.parent.audio_manager.load_sound('hint', 'audio/hint.mp3'):
                # 使用默认音乐文件作为提示音效
                self.parent.audio_manager.load_sound('hint', 'audio/wet_hands.mp3')
            if not self.parent.audio_manager.load_sound('fail', 'audio/fail.mp3'):
                # 使用默认音乐文件作为失败音效
                self.parent.audio_manager.load_sound('fail', 'audio/wet_hands.mp3')
        except Exception as e:
            # 音效加载失败时静默处理
            pass

    def show_level_select(self):
        self.state = 'level_select'
        self.selected = []
        self.path = []
        self.level = None  # 不默认选中任何难度

    def reset_game(self):
        lv = self.levels[self.level-1]
        self.rows = lv['rows']
        self.cols = lv['cols']
        types = lv['types']
        total = self.rows * self.cols
        if total % 2 != 0:
            total -= 1
        types = min(types, total // 2)
        pair_count = total // 2
        icons = []
        for i in range(pair_count):
            icons.append(i % types)
        icons = icons * 2  # 每种类型两次
        random.shuffle(icons)
        self.grid = [[-1 for _ in range(self.cols)] for _ in range(self.rows)]
        idx = 0
        for r in range(self.rows):
            for c in range(self.cols):
                if idx < total:
                    self.grid[r][c] = icons[idx]
                    idx += 1
        self.selected = []
        self.path = []
        self.state = 'playing'
        # 调试输出每种类型数量和棋盘分布
        # from collections import Counter
        # flat = [self.grid[r][c] for r in range(self.rows) for c in range(self.cols) if self.grid[r][c] != -1]
        # print('类型分布:', Counter(flat))
        # print('棋盘分布:')
        # for row in self.grid:
        #     print(row)

    def is_board_solvable(self, grid):
        # 用连连看消除算法模拟，能全部消除则返回True
        from copy import deepcopy
        rows, cols = len(grid), len(grid[0])
        board = deepcopy(grid)
        def find_pair(board):
            for r1 in range(rows):
                for c1 in range(cols):
                    if board[r1][c1] == -1:
                        continue
                    for r2 in range(rows):
                        for c2 in range(cols):
                            if (r1, c1) == (r2, c2):
                                continue
                            if board[r2][c2] == board[r1][c1]:
                                path = self.find_link_path([r1, c1], [r2, c2], board)
                                if path:
                                    return (r1, c1, r2, c2)
            return None
        while True:
            pair = find_pair(board)
            if not pair:
                break
            r1, c1, r2, c2 = pair
            board[r1][c1] = -1
            board[r2][c2] = -1
        return all(board[r][c] == -1 for r in range(rows) for c in range(cols))

    def draw_icon(self, surface, rect, type_id):
        import math
        center = (rect.x + rect.w//2, rect.y + rect.h//2)
        # 形状和颜色一一对应，类型多时自动补充
        base_shape_color_list = [
            ((255,87,34), 'circle'),      # 红-圆
            ((66,165,245), 'rect'),       # 蓝-方
            ((76,175,80), 'triangle'),    # 绿-三角
            ((156,39,176), 'ellipse'),    # 紫-椭圆
            ((255,152,0), 'cross'),       # 橙-交叉
            ((0,188,212), 'arc'),         # 青-弧线
            ((205,220,57), 'diamond'),    # 黄绿-菱形
            ((233,30,99), 'star'),        # 粉-五角星
            ((121,85,72), 'pentagon'),    # 棕-五边形
            ((124,77,255), 'hexagon'),    # 靛-六边形
            ((255,235,59), 'moon'),       # 亮黄-月牙
            ((0,150,136), 'heart'),       # 青绿-心形
            ((244,67,54), 'parallelogram'), # 红-平行四边形
            ((63,81,181), 'octagon'),     # 蓝-八边形
            ((139,195,74), 'plus'),       # 绿-加号
            ((158,158,158), 'lightning'), # 灰-闪电
            ((255,87,127), 'wave'),       # 粉-波浪
            ((0,0,0), 'smile'),           # 黑-笑脸
        ]
        # 动态扩展
        types_count = getattr(self, 'types', len(base_shape_color_list))
        shape_color_list = base_shape_color_list.copy()
        extra_idx = 0
        while len(shape_color_list) < types_count:
            # 自动生成新颜色和形状名
            color = (random.randint(30,255), random.randint(30,255), random.randint(30,255))
            shape = f'custom{extra_idx}'
            shape_color_list.append((color, shape))
            extra_idx += 1
        color, shape = shape_color_list[type_id]
        if shape == 'circle':
            pygame.draw.circle(surface, color, center, rect.w//3)
        elif shape == 'rect':
            pygame.draw.rect(surface, color, rect.inflate(-rect.w//3, -rect.h//3), border_radius=6)
        elif shape == 'triangle':
            pygame.draw.polygon(surface, color, [
                (center[0], rect.y+8),
                (rect.x+rect.w-8, rect.y+rect.h-8),
                (rect.x+8, rect.y+rect.h-8)
            ])
        elif shape == 'ellipse':
            pygame.draw.ellipse(surface, color, rect.inflate(-rect.w//4, -rect.h//6))
        elif shape == 'cross':
            pygame.draw.line(surface, color, (rect.x+10, rect.y+10), (rect.x+rect.w-10, rect.y+rect.h-10), 6)
            pygame.draw.line(surface, color, (rect.x+rect.w-10, rect.y+10), (rect.x+10, rect.y+rect.h-10), 6)
        elif shape == 'arc':
            pygame.draw.arc(surface, color, rect.inflate(-rect.w//5, -rect.h//5), 0, 3.14, 5)
        elif shape == 'diamond':
            pygame.draw.polygon(surface, color, [
                (center[0], rect.y+8),
                (rect.x+rect.w-8, center[1]),
                (center[0], rect.y+rect.h-8),
                (rect.x+8, center[1])
            ])
        elif shape == 'star':
            points = []
            for i in range(5):
                angle = i * 2 * 3.14159 / 5 - 3.14159/2
                x = center[0] + math.cos(angle) * rect.w//3
                y = center[1] + math.sin(angle) * rect.h//3
                points.append((x, y))
            for i in range(5):
                pygame.draw.line(surface, color, points[i], points[(i+2)%5], 3)
        elif shape == 'pentagon':
            points = []
            for i in range(5):
                angle = i * 2 * 3.14159 / 5 - 3.14159/2
                x = center[0] + math.cos(angle) * rect.w//3
                y = center[1] + math.sin(angle) * rect.h//3
                points.append((x, y))
            pygame.draw.polygon(surface, color, points)
        elif shape == 'hexagon':
            points = []
            for i in range(6):
                angle = i * 2 * 3.14159 / 6 - 3.14159/2
                x = center[0] + math.cos(angle) * rect.w//3
                y = center[1] + math.sin(angle) * rect.h//3
                points.append((x, y))
            pygame.draw.polygon(surface, color, points)
        elif shape == 'moon':
            pygame.draw.circle(surface, color, center, rect.w//3)
            pygame.draw.circle(surface, (245,245,245), (center[0]+rect.w//8, center[1]-rect.h//8), rect.w//4)
        elif shape == 'heart':
            p1 = (center[0], center[1]+rect.h//6)
            p2 = (center[0]-rect.w//6, center[1])
            p3 = (center[0]+rect.w//6, center[1])
            pygame.draw.polygon(surface, color, [p1, p2, p3])
            pygame.draw.circle(surface, color, (center[0]-rect.w//12, center[1]), rect.w//8)
            pygame.draw.circle(surface, color, (center[0]+rect.w//12, center[1]), rect.w//8)
        elif shape == 'parallelogram':
            pygame.draw.polygon(surface, color, [
                (rect.x+rect.w//4, rect.y+8),
                (rect.x+rect.w-8, rect.y+8),
                (rect.x+rect.w*3//4, rect.y+rect.h-8),
                (rect.x+8, rect.y+rect.h-8)
            ])
        elif shape == 'octagon':
            points = []
            for i in range(8):
                angle = i * 2 * 3.14159 / 8 - 3.14159/2
                x = center[0] + math.cos(angle) * rect.w//3
                y = center[1] + math.sin(angle) * rect.h//3
                points.append((x, y))
            pygame.draw.polygon(surface, color, points)
        elif shape == 'plus':
            w = rect.w//5
            pygame.draw.rect(surface, color, (center[0]-w//2, rect.y+8, w, rect.h-16))
            pygame.draw.rect(surface, color, (rect.x+8, center[1]-w//2, rect.w-16, w))
        elif shape == 'lightning':
            pts = [
                (rect.x+rect.w//4, rect.y+8),
                (rect.x+rect.w//2, center[1]),
                (rect.x+rect.w*3//4, rect.y+8),
                (center[0], rect.y+rect.h-8),
                (rect.x+rect.w//2, center[1]),
                (rect.x+8, rect.y+rect.h-8)
            ]
            pygame.draw.lines(surface, color, False, pts, 5)
        elif shape == 'wave':
            for i in range(3):
                pygame.draw.arc(surface, color, rect.inflate(-rect.w//6, -rect.h//3).move(0, i*rect.h//6), math.pi, 2*math.pi, 3)
        elif shape == 'smile':
            pygame.draw.circle(surface, color, center, rect.w//3, 3)
            pygame.draw.arc(surface, color, rect.inflate(-rect.w//3, -rect.h//3), math.pi/6, math.pi-math.pi/6, 3)
            pygame.draw.circle(surface, color, (center[0]-rect.w//10, center[1]-rect.h//10), 3)
            pygame.draw.circle(surface, color, (center[0]+rect.w//10, center[1]-rect.h//10), 3)
        else:
            # 自动生成的自定义形状：画一个大X
            pygame.draw.line(surface, color, (rect.x+8, rect.y+8), (rect.x+rect.w-8, rect.y+rect.h-8), 4)
            pygame.draw.line(surface, color, (rect.x+rect.w-8, rect.y+8), (rect.x+8, rect.y+rect.h-8), 4)

    def draw(self):
        # 动漫风蓝粉渐变背景+星星点缀
        panel_rect = pygame.Rect(self.panel_x, self.panel_y, self.panel_w, self.panel_h)
        grad = pygame.Surface((self.panel_w, self.panel_h), pygame.SRCALPHA)
        for y in range(self.panel_h):
            blend = y / self.panel_h
            c1 = (120, 180, 255)
            c2 = (255, 180, 240)
            c = tuple(int(c1[j]*(1-blend)+c2[j]*blend) for j in range(3))
            pygame.draw.line(grad, c, (0, y), (self.panel_w, y))
        # 顶部Q版星星点缀
        for i in range(8):
            cx = self.panel_w//10 + i*self.panel_w//9
            cy = 38 + (8 if i%2==0 else -8)
            points = [
                (cx, cy-12), (cx+5, cy+4), (cx-10, cy-2), (cx+10, cy-2), (cx-5, cy+4)
            ]
            pygame.draw.polygon(grad, (255, 223, 77), points)
            pygame.draw.circle(grad, (255,255,255), (cx,cy), 4)
        self.surface.blit(grad, (self.panel_x, self.panel_y))
        # 不再绘制任何白色底板
        # 顶部按钮（紧贴面板顶部，半透明）
        btn_font = pygame.font.Font(FONT_NAME, 26)
        btn_height = 44
        btn_margin_top = 10
        btn_y = self.panel_y + btn_margin_top
        restart_rect = pygame.Rect(self.panel_x+60, btn_y, 140, btn_height)
        back_rect = pygame.Rect(self.panel_x+self.panel_w-200, btn_y, 140, btn_height)
        # 半透明背景
        restart_surf = pygame.Surface((140, btn_height), pygame.SRCALPHA)
        pygame.draw.rect(restart_surf, (255,152,0,160), (0,0,140,btn_height), border_radius=16)
        pygame.draw.rect(restart_surf, (255,193,7,180), (0,0,140,btn_height), 3, border_radius=16)
        self.surface.blit(restart_surf, (restart_rect.x, restart_rect.y))
        restart_text = btn_font.render('重新开始', True, (255,255,255,220))
        self.surface.blit(restart_text, (restart_rect.x+restart_rect.w//2-restart_text.get_width()//2, restart_rect.y+8))
        
        # 提示按钮
        hint_rect = pygame.Rect(self.panel_x+self.panel_w//2-70, btn_y, 140, btn_height)
        self.hint_button_rect = hint_rect
        hint_surf = pygame.Surface((140, btn_height), pygame.SRCALPHA)
        current_time = pygame.time.get_ticks()
        cooldown_alpha = 100 if current_time - self.last_hint_time < self.hint_cooldown else 160
        pygame.draw.rect(hint_surf, (76,175,80,cooldown_alpha), (0,0,140,btn_height), border_radius=16)
        pygame.draw.rect(hint_surf, (120,220,120,180), (0,0,140,btn_height), 3, border_radius=16)
        self.surface.blit(hint_surf, (hint_rect.x, hint_rect.y))
        hint_text = btn_font.render('提示', True, (255,255,255,220))
        self.surface.blit(hint_text, (hint_rect.x+hint_rect.w//2-hint_text.get_width()//2, hint_rect.y+8))
        
        back_surf = pygame.Surface((140, btn_height), pygame.SRCALPHA)
        pygame.draw.rect(back_surf, (66,165,245,160), (0,0,140,btn_height), border_radius=16)
        pygame.draw.rect(back_surf, (120,200,255,180), (0,0,140,btn_height), 3, border_radius=16)
        self.surface.blit(back_surf, (back_rect.x, back_rect.y))
        back_text = btn_font.render('返回活动', True, (255,255,255,220))
        self.surface.blit(back_text, (back_rect.x+back_rect.w//2-back_text.get_width()//2, back_rect.y+8))
        # 标题
        font = pygame.font.Font(FONT_NAME, 44)
        title = font.render('连连看', True, (255,87,34))
        # 添加标题阴影效果
        shadow = font.render('连连看', True, (0,0,0,100))
        self.surface.blit(shadow, (self.panel_x + self.panel_w//2 - title.get_width()//2 + 2, self.panel_y+btn_height+btn_margin_top+8))
        self.surface.blit(title, (self.panel_x + self.panel_w//2 - title.get_width()//2, self.panel_y+btn_height+btn_margin_top+6))
        # 等级与剩余
        info_font = pygame.font.Font(FONT_NAME, 22)
        if self.level is not None and self.state == 'playing' and self.grid and len(self.grid) == self.rows and all(len(row) == self.cols for row in self.grid):
            left_pairs = sum(1 for r in range(self.rows) for c in range(self.cols) if self.grid[r][c]!=-1)//2
            info = info_font.render(f'等级: {self.levels[self.level-1]["name"]}   剩余对数: {left_pairs}', True, (66,165,245))
            # 添加信息背景
            info_bg = pygame.Surface((info.get_width()+20, info.get_height()+10), pygame.SRCALPHA)
            pygame.draw.rect(info_bg, (255,255,255,100), (0,0,info_bg.get_width(),info_bg.get_height()), border_radius=10)
            self.surface.blit(info_bg, (self.panel_x+30, self.panel_y+105))
            self.surface.blit(info, (self.panel_x+40, self.panel_y+110))
        # 等级选择
        if self.state == 'level_select':
            self.draw_level_select()
            return
        # 绘制棋盘
        grid_x = self.panel_x + (self.panel_w - self.cols*self.tile_size)//2
        grid_y = self.panel_y + 140
        
        # 添加棋盘背景
        board_bg = pygame.Surface((self.cols*self.tile_size, self.rows*self.tile_size), pygame.SRCALPHA)
        pygame.draw.rect(board_bg, (255,255,255,80), (0,0,self.cols*self.tile_size,self.rows*self.tile_size), border_radius=15)
        self.surface.blit(board_bg, (grid_x, grid_y))
        
        # 更新动画计时器
        self.animation_timer += 1
        if self.animation_timer > 60:
            self.animation_timer = 0
        for r in range(self.rows):
            for c in range(self.cols):
                val = self.grid[r][c]
                rect = pygame.Rect(grid_x + c*self.tile_size, grid_y + r*self.tile_size, self.tile_size, self.tile_size)
                # 渐变立体方块
                if val == -1:
                    pygame.draw.rect(self.surface, (230,230,230), rect, border_radius=10)
                else:
                    # 渐变
                    block_surf = pygame.Surface((self.tile_size, self.tile_size), pygame.SRCALPHA)
                    for y in range(self.tile_size):
                        color = [255, 224-int(46*y/self.tile_size), 178-int(80*y/self.tile_size), 255]
                        pygame.draw.line(block_surf, color, (0, y), (self.tile_size, y))
                    block_surf.set_alpha(220)
                    self.surface.blit(block_surf, rect.topleft)
                    
                    # 脉动动画效果
                    pulse_factor = 0
                    if [r,c] in self.pulsing_tiles:
                        pulse_factor = math.sin(self.animation_timer * 0.2) * 0.1
                    
                    # 边框
                    border_color = (255,152,0) if [r,c] not in self.selected else (66,165,245)
                    border_width = 3 + int(pulse_factor * 3)
                    pygame.draw.rect(self.surface, border_color, rect, border_width, border_radius=10)
                    
                    # 选中高亮
                    if [r,c] in self.selected:
                        highlight_alpha = 80 + int(math.sin(self.animation_timer * 0.3) * 40)
                        pygame.draw.rect(self.surface, (66,165,245,highlight_alpha), rect, border_radius=10)
                    
                    # 图标
                    self.draw_icon(self.surface, rect, val)
                    

        # 绘制选中路径
        if self.path:
            for i in range(len(self.path)-1):
                x1, y1 = self.path[i][1], self.path[i][0]
                x2, y2 = self.path[i+1][1], self.path[i+1][0]
                sx = grid_x + x1*self.tile_size + self.tile_size//2
                sy = grid_y + y1*self.tile_size + self.tile_size//2
                ex = grid_x + x2*self.tile_size + self.tile_size//2
                ey = grid_y + y2*self.tile_size + self.tile_size//2
                # 添加发光效果
                glow_surf = pygame.Surface((abs(ex-sx)+20, abs(ey-sy)+20), pygame.SRCALPHA)
                pygame.draw.line(glow_surf, (66,165,245,100), (10,10), (abs(ex-sx)+10, abs(ey-sy)+10), 15)
                self.surface.blit(glow_surf, (min(sx,ex)-10, min(sy,ey)-10))
                pygame.draw.line(self.surface, (66,165,245), (sx,sy), (ex,ey), 7)
                # 添加路径端点
                pygame.draw.circle(self.surface, (255,255,255), (sx,sy), 8)
                pygame.draw.circle(self.surface, (66,165,245), (sx,sy), 6)
                pygame.draw.circle(self.surface, (255,255,255), (ex,ey), 8)
                pygame.draw.circle(self.surface, (66,165,245), (ex,ey), 6)
        
        # 路径清除计时器逻辑
        if self.path_clear_timer > 0:
            self.path_clear_timer -= 1
            if self.path_clear_timer <= 0:
                self.path = []
        
        # 按钮
        btn_font = pygame.font.Font(FONT_NAME, 26)
        # 底部留白
        pygame.draw.rect(self.surface, (245,245,245), (self.panel_x, self.panel_y+self.panel_h-30, self.panel_w, 30), border_radius=0)
        
        # 添加操作提示
        if self.state == 'playing':
            tip_font = pygame.font.Font(FONT_NAME, 16)
            tip_text = tip_font.render('提示：点击相同类型的方块进行连接，最多可以拐2次弯', True, (150,150,150))
            self.surface.blit(tip_text, (self.panel_x+self.panel_w//2-tip_text.get_width()//2, self.panel_y+self.panel_h-25))
        # 胜利/失败提示
        if self.state == 'win':
            # 胜利动画效果
            win_alpha = abs(math.sin(self.animation_timer * 0.1)) * 255
            win_font = pygame.font.Font(FONT_NAME, 44)
            win_text = win_font.render('恭喜通关！', True, (76,175,80))
            # 添加发光效果
            glow_surf = pygame.Surface((win_text.get_width()+40, win_text.get_height()+40), pygame.SRCALPHA)
            pygame.draw.ellipse(glow_surf, (76,175,80,int(win_alpha*0.3)), glow_surf.get_rect())
            self.surface.blit(glow_surf, (self.panel_x+self.panel_w//2-win_text.get_width()//2-20, self.panel_y+80))
            self.surface.blit(win_text, (self.panel_x+self.panel_w//2-win_text.get_width()//2, self.panel_y+100))
            
            # 添加庆祝文字
            celebrate_font = pygame.font.Font(FONT_NAME, 24)
            celebrate_text = celebrate_font.render('点击"重新开始"再来一局！', True, (255,193,7))
            self.surface.blit(celebrate_text, (self.panel_x+self.panel_w//2-celebrate_text.get_width()//2, self.panel_y+150))
            
        elif self.state == 'fail':
            fail_font = pygame.font.Font(FONT_NAME, 44)
            fail_text = fail_font.render('无解，已失败！', True, (220,0,0))
            self.surface.blit(fail_text, (self.panel_x+self.panel_w//2-fail_text.get_width()//2, self.panel_y+100))
            
            # 添加提示文字
            retry_font = pygame.font.Font(FONT_NAME, 24)
            retry_text = retry_font.render('点击"重新开始"重试！', True, (255,152,0))
            self.surface.blit(retry_text, (self.panel_x+self.panel_w//2-retry_text.get_width()//2, self.panel_y+150))
        # 不再绘制任何白色底板 

    def draw_level_select(self):
        font = pygame.font.Font(FONT_NAME, 32)
        desc_font = pygame.font.Font(FONT_NAME, 22)
        mouse_pos = pygame.mouse.get_pos()
        # 动漫风蓝粉渐变背景+星星气泡点缀
        overlay = pygame.Surface((self.panel_w, self.panel_h), pygame.SRCALPHA)
        for y in range(self.panel_h):
            blend = y / self.panel_h
            c1 = (120, 180, 255)
            c2 = (255, 180, 240)
            c = tuple(int(c1[j]*(1-blend)+c2[j]*blend) for j in range(3))
            pygame.draw.line(overlay, c, (0, y), (self.panel_w, y))
        # 星星点缀
        for i in range(8):
            cx = self.panel_w//10 + i*self.panel_w//9
            cy = 38 + (8 if i%2==0 else -8)
            points = [
                (cx, cy-12), (cx+5, cy+4), (cx-10, cy-2), (cx+10, cy-2), (cx-5, cy+4)
            ]
            pygame.draw.polygon(overlay, (255, 223, 77), points)
            pygame.draw.circle(overlay, (255,255,255), (cx,cy), 4)
        self.surface.blit(overlay, (self.panel_x, self.panel_y))
        # 居中排列动漫风卡片
        card_w, card_h = 210, 120
        gap = 60
        total_w = card_w * len(self.levels) + gap * (len(self.levels)-1)
        start_x = self.panel_x + (self.panel_w - total_w) // 2
        center_y = self.panel_y + self.panel_h // 2 - 60
        for i, lv in enumerate(self.levels):
            rect = pygame.Rect(start_x + i*(card_w+gap), center_y, card_w, card_h)
            is_hover = rect.collidepoint(mouse_pos)
            is_selected = self.level == i+1
            # 动漫风弹跳动画
            t = pygame.time.get_ticks() / 1000.0
            bounce = math.sin(t*3 + i) * 6 if is_hover or is_selected else 0
            scale = 1.0
            if is_hover or is_selected:
                scale = 1.10 if is_hover else 1.05
            scaled_rect = rect.inflate(int(card_w*(scale-1)), int(card_h*(scale-1)))
            scaled_rect.center = (rect.centerx, rect.centery + bounce)
            # 多层阴影
            for s in range(3,0,-1):
                shadow = pygame.Surface((scaled_rect.width+16+s*8, scaled_rect.height+16+s*8), pygame.SRCALPHA)
                pygame.draw.ellipse(shadow, (120,120,180,30//s), shadow.get_rect())
                self.surface.blit(shadow, (scaled_rect.x-8-s*4, scaled_rect.y+12+s*2))
            # 蓝粉渐变卡片
            card_surf = pygame.Surface((scaled_rect.width, scaled_rect.height), pygame.SRCALPHA)
            for y in range(scaled_rect.height):
                blend = y / scaled_rect.height
                c1 = (120, 180, 255)
                c2 = (255, 180, 240)
                c = tuple(int(c1[j]*(1-blend)+c2[j]*blend) for j in range(3))
                pygame.draw.line(card_surf, c, (0, y), (scaled_rect.width, y))
            # 高光
            highlight = pygame.Surface((scaled_rect.width, int(scaled_rect.height*0.4)), pygame.SRCALPHA)
            pygame.draw.ellipse(highlight, (255,255,255,80), (0,0,scaled_rect.width,int(scaled_rect.height*0.8)))
            card_surf.blit(highlight, (0,0))
            # Q版星星/皇冠图标
            icon_center = (scaled_rect.width//2, 28)
            if i==0:
                # 星星
                pygame.draw.polygon(card_surf, (255, 223, 77), [(icon_center[0],icon_center[1]-16),(icon_center[0]+8,icon_center[1]+8),(icon_center[0]-14,icon_center[1]-4),(icon_center[0]+14,icon_center[1]-4),(icon_center[0]-8,icon_center[1]+8)])
                pygame.draw.circle(card_surf, (255,255,255), icon_center, 7)
            elif i==1:
                # 皇冠
                pygame.draw.polygon(card_surf, (255, 128, 192), [(icon_center[0]-18,icon_center[1]+12),(icon_center[0]-12,icon_center[1]-10),(icon_center[0],icon_center[1]+6),(icon_center[0]+12,icon_center[1]-10),(icon_center[0]+18,icon_center[1]+12)])
                pygame.draw.rect(card_surf, (255,255,255), (icon_center[0]-14,icon_center[1]+8,28,8), border_radius=4)
            else:
                # 闪电
                pygame.draw.polygon(card_surf, (120, 220, 255), [(icon_center[0],icon_center[1]-12),(icon_center[0]+8,icon_center[1]+2),(icon_center[0]-2,icon_center[1]+2),(icon_center[0]+2,icon_center[1]+16),(icon_center[0]-8,icon_center[1]+2),(icon_center[0]+2,icon_center[1]+2)])
            # 动态发光描边
            if is_selected:
                glow = pygame.Surface((scaled_rect.width+24, scaled_rect.height+24), pygame.SRCALPHA)
                for r in range(18,0,-1):
                    alpha = int(120 * (r/18)**2)
                    pygame.draw.ellipse(glow, (255, 128, 192, alpha), glow.get_rect().inflate(-r*2, -r*2))
                self.surface.blit(glow, (scaled_rect.x-12, scaled_rect.y-12), special_flags=pygame.BLEND_RGBA_ADD)
                pygame.draw.rect(card_surf, (255, 128, 192), (0,0,scaled_rect.width,scaled_rect.height), 6, border_radius=28)
            elif is_hover:
                pygame.draw.rect(card_surf, (120, 180, 255), (0,0,scaled_rect.width,scaled_rect.height), 4, border_radius=28)
            # 卡片本体
            pygame.draw.rect(card_surf, (255,255,255,40), (0,0,scaled_rect.width,scaled_rect.height), border_radius=28)
            self.surface.blit(card_surf, scaled_rect)
            # 难度名称（卡通描边）
            text = font.render(lv['name'], True, (255,255,255))
            for dx,dy in [(-2,0),(2,0),(0,-2),(0,2)]:
                outline = font.render(lv['name'], True, (80,80,160))
                self.surface.blit(outline, (scaled_rect.x+scaled_rect.w//2-text.get_width()//2+dx, scaled_rect.y+38+dy))
            self.surface.blit(text, (scaled_rect.x+scaled_rect.w//2-text.get_width()//2, scaled_rect.y+38))
            # 详细参数
            desc = f"{lv['rows']}行{lv['cols']}列  {lv['types']}种图标"
            desc_text = desc_font.render(desc, True, (255,255,255))
            for dx,dy in [(-1,0),(1,0),(0,-1),(0,1)]:
                outline = desc_font.render(desc, True, (120,120,180))
                self.surface.blit(outline, (scaled_rect.x+scaled_rect.w//2-desc_text.get_width()//2+dx, scaled_rect.y+80+dy))
            self.surface.blit(desc_text, (scaled_rect.x+scaled_rect.w//2-desc_text.get_width()//2, scaled_rect.y+80))
        # 开始按钮
        start_rect = pygame.Rect(self.panel_x+self.panel_w//2-90, center_y+card_h+50, 180, 60)
        if self.level is not None:
            btn_scale = 1.10 if start_rect.collidepoint(mouse_pos) else 1.0
            btn_rect = start_rect.inflate(int(180*(btn_scale-1)), int(60*(btn_scale-1)))
            btn_rect.center = start_rect.center
            btn_surf = pygame.Surface((btn_rect.width, btn_rect.height), pygame.SRCALPHA)
            for y in range(btn_rect.height):
                blend = y / btn_rect.height
                c1 = (120, 180, 255)
                c2 = (255, 180, 240)
                c = tuple(int(c1[j]*(1-blend)+c2[j]*blend) for j in range(3))
                pygame.draw.line(btn_surf, c, (0, y), (btn_rect.width, y))
            pygame.draw.rect(btn_surf, (255,255,255,60), (0,0,btn_rect.width,btn_rect.height//2), border_radius=20)
            pygame.draw.rect(btn_surf, (255, 128, 192), (0,0,btn_rect.width,btn_rect.height), 4, border_radius=20)
            self.surface.blit(btn_surf, btn_rect)
            sfont = pygame.font.Font(FONT_NAME, 30)
            stext = sfont.render('开始游戏', True, (255,255,255))
            for dx,dy in [(-2,0),(2,0),(0,-2),(0,2)]:
                outline = sfont.render('开始游戏', True, (120,120,180))
                self.surface.blit(outline, (btn_rect.x+btn_rect.w//2-stext.get_width()//2+dx, btn_rect.y+btn_rect.h//2-stext.get_height()//2+dy))
            self.surface.blit(stext, (btn_rect.x+btn_rect.w//2-stext.get_width()//2, btn_rect.y+btn_rect.h//2-stext.get_height()//2))
        else:
            pygame.draw.rect(self.surface, (180,180,180), start_rect, border_radius=20)
            sfont = pygame.font.Font(FONT_NAME, 30)
            stext = sfont.render('开始游戏', True, (220,220,220))
            self.surface.blit(stext, (start_rect.x+start_rect.w//2-stext.get_width()//2, start_rect.y+start_rect.h//2-stext.get_height()//2))
        
        # 添加返回按钮
        # 移到底部
        back_rect = pygame.Rect(self.panel_x+20, self.panel_y + self.panel_h - 80, 140, 60)
        back_btn_scale = 1.05 if back_rect.collidepoint(mouse_pos) else 1.0
        back_btn_rect = back_rect.inflate(int(140*(back_btn_scale-1)), int(60*(back_btn_scale-1)))
        back_btn_rect.center = back_rect.center
        
        # 绘制返回按钮
        back_surf = pygame.Surface((back_btn_rect.width, back_btn_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(back_surf, (255, 87, 34, 200), (0,0,back_btn_rect.width,back_btn_rect.height), border_radius=20)
        pygame.draw.rect(back_surf, (255, 120, 80, 220), (0,0,back_btn_rect.width,back_btn_rect.height), 3, border_radius=20)
        self.surface.blit(back_surf, back_btn_rect)
        
        back_font = pygame.font.Font(FONT_NAME, 28)
        back_text = back_font.render('返回', True, (255,255,255))
        self.surface.blit(back_text, (back_btn_rect.x+back_btn_rect.w//2-back_text.get_width()//2, 
                                   back_btn_rect.y+back_btn_rect.h//2-back_text.get_height()//2))

    def handle_event(self, event):
        btn_height = 44
        btn_margin_top = 10
        btn_y = self.panel_y + btn_margin_top
        restart_rect = pygame.Rect(self.panel_x+60, btn_y, 140, btn_height)
        hint_rect = pygame.Rect(self.panel_x+self.panel_w//2-70, btn_y, 140, btn_height)
        back_rect = pygame.Rect(self.panel_x+self.panel_w-200, btn_y, 140, btn_height)
        current_time = pygame.time.get_ticks()
        if self.state == 'level_select':
            if event.type == pygame.MOUSEBUTTONDOWN:
                # 动漫风卡片区域参数与draw_level_select一致
                card_w, card_h = 210, 120
                gap = 60
                total_w = card_w * len(self.levels) + gap * (len(self.levels)-1)
                start_x = self.panel_x + (self.panel_w - total_w) // 2
                center_y = self.panel_y + self.panel_h // 2 - 60
                for i, lv in enumerate(self.levels):
                    rect = pygame.Rect(start_x + i*(card_w+gap), center_y, card_w, card_h)
                    t = pygame.time.get_ticks() / 1000.0
                    bounce = math.sin(t*3 + i) * 6 if self.level == i+1 else 0
                    scale = 1.10 if rect.collidepoint(pygame.mouse.get_pos()) else (1.05 if self.level == i+1 else 1.0)
                    scaled_rect = rect.inflate(int(card_w*(scale-1)), int(card_h*(scale-1)))
                    scaled_rect.center = (rect.centerx, rect.centery + bounce)
                    if scaled_rect.collidepoint(event.pos):
                        self.level = i+1
                        return
                # 开始按钮区域
                start_rect = pygame.Rect(self.panel_x+self.panel_w//2-90, center_y+card_h+50, 180, 60)
                btn_scale = 1.10 if start_rect.collidepoint(pygame.mouse.get_pos()) else 1.0
                btn_rect = start_rect.inflate(int(180*(btn_scale-1)), int(60*(btn_scale-1)))
                btn_rect.center = start_rect.center
                
                # 返回按钮区域
                # 移到底部
                back_rect = pygame.Rect(self.panel_x+20, self.panel_y + self.panel_h - 80, 140, 60)
                back_btn_scale = 1.05 if back_rect.collidepoint(pygame.mouse.get_pos()) else 1.0
                back_btn_rect = back_rect.inflate(int(140*(back_btn_scale-1)), int(60*(back_btn_scale-1)))
                back_btn_rect.center = back_rect.center
                
                if btn_rect.collidepoint(event.pos) and self.level is not None:
                    self.reset_game()
                    self.state = 'playing'
                    return
                # 返回按钮事件处理
                if back_rect.collidepoint(event.pos):
                    self.parent.page = 'main'
                    return
                if restart_rect.collidepoint(event.pos):
                    self.show_level_select()
                    return
                if hint_rect.collidepoint(event.pos) and current_time - self.last_hint_time >= self.hint_cooldown:
                    self.provide_hint()
                    self.last_hint_time = current_time
                    return
                if back_rect.collidepoint(event.pos):
                    self.parent.page = 'main'
                    return
        elif self.state == 'playing':
            grid_x = self.panel_x + (self.panel_w - self.cols*self.tile_size)//2
            grid_y = self.panel_y + 140
            if event.type == pygame.MOUSEBUTTONDOWN:
                # 先判断是否点了顶部按钮
                if restart_rect.collidepoint(event.pos):
                    self.show_level_select()
                    return
                if hint_rect.collidepoint(event.pos) and current_time - self.last_hint_time >= self.hint_cooldown:
                    self.provide_hint()
                    self.last_hint_time = current_time
                    return
                if back_rect.collidepoint(event.pos):
                    self.parent.page = 'main'
                    return
                mx, my = event.pos
                for r in range(self.rows):
                    for c in range(self.cols):
                        rect = pygame.Rect(grid_x + c*self.tile_size, grid_y + r*self.tile_size, self.tile_size, self.tile_size)
                        if rect.collidepoint(mx, my) and self.grid[r][c] != -1:
                            if len(self.selected) == 0:
                                self.selected = [[r,c]]
                            elif len(self.selected) == 1 and [r,c] != self.selected[0]:
                                # 先判断类型是否一致
                                if self.grid[r][c] == self.grid[self.selected[0][0]][self.selected[0][1]]:
                                    path = self.find_link_path(self.selected[0], [r,c])
                                    if path:
                                        r1,c1 = self.selected[0]
                                        r2,c2 = [r,c]
                                        assert (r1, c1) != (r2, c2), f'消除同一个格子: {(r1, c1)}'
                                        assert self.grid[r1][c1] == self.grid[r2][c2], f'消除类型不一致: {self.grid[r1][c1]}, {self.grid[r2][c2]}'
                                        self.grid[r1][c1] = -1
                                        self.grid[r2][c2] = -1
                                        self.selected = []
                                        # 保持路径显示一段时间
                                        self.path_clear_timer = 30  # 30帧的显示时间
                                        # 播放消除音效
                                        try:
                                            self.parent.audio_manager.play_sound('match')
                                        except:
                                            pass
                                        # 检查胜利
                                        if all(self.grid[rr][cc]==-1 for rr in range(self.rows) for cc in range(self.cols)):
                                            self.state = 'win'
                                            # 播放胜利音效
                                            try:
                                                self.parent.audio_manager.play_sound('win')
                                            except:
                                                pass
                                        # 消除后调试输出
                                        # print('消除后棋盘分布:')
                                        # for row in self.grid:
                                        #     print(row)
                                    else:
                                        self.selected = []
                                        self.path = []
                                else:
                                    self.selected = [[r,c]]
                                return
                            elif len(self.selected) == 2:
                                # 如果已经有提示的方块对，点击任意方块重置选择
                                self.selected = [[r,c]]
                                self.path = []
                                return
            if event.type == pygame.USEREVENT+1:
                # 消除
                if self.selected and self.path:
                    r1,c1 = self.selected[0]
                    r2,c2 = self.path[-1]
                    # 加断言，防止消除不同类型或同一个格子
                    assert (r1, c1) != (r2, c2), f'消除同一个格子: {(r1, c1)}'
                    assert self.grid[r1][c1] == self.grid[r2][c2], f'消除类型不一致: {self.grid[r1][c1]}, {self.grid[r2][c2]}'
                    self.grid[r1][c1] = -1
                    self.grid[r2][c2] = -1
                    self.selected = []
                    self.path = []
                    # 检查胜利
                    if all(self.grid[rr][cc]==-1 for rr in range(self.rows) for cc in range(self.cols)):
                        self.state = 'win'
                    # 消除后调试输出
                    # print('消除后棋盘分布:')
                    # for row in self.grid:
                    #     print(row)
                pygame.time.set_timer(pygame.USEREVENT+1, 0)
                return
            # 即使没有消除也要解锁动画，防止卡死
            pygame.time.set_timer(pygame.USEREVENT+1, 0)
            return
        elif self.state in ['win','fail']:
            if event.type == pygame.MOUSEBUTTONDOWN and restart_rect.collidepoint(event.pos):
                self.show_level_select()
                return
            if event.type == pygame.MOUSEBUTTONDOWN and back_rect.collidepoint(event.pos):
                self.parent.page = 'main'
                return

    def provide_hint(self):
        """提供游戏提示，找到一对可以连接的方块"""
        from copy import deepcopy
        board = deepcopy(self.grid)
        
        # 查找所有可以连接的方块对
        for r1 in range(self.rows):
            for c1 in range(self.cols):
                if board[r1][c1] == -1:
                    continue
                for r2 in range(self.rows):
                    for c2 in range(self.cols):
                        if (r1, c1) == (r2, c2):
                            continue
                        if board[r2][c2] == board[r1][c1]:
                            path = self.find_link_path([r1, c1], [r2, c2], board)
                            if path:
                                # 高亮显示提示的方块
                                self.selected = [[r1, c1], [r2, c2]]
                                self.path = path
                                # 播放提示音效
                                try:
                                    self.parent.audio_manager.play_sound('hint')
                                    # 添加脉动效果
                                    self.pulsing_tiles = [[r1, c1], [r2, c2]]
                                except:
                                    pass
                                return
        
        # 如果没有找到可连接的方块，播放失败音效
        try:
            self.parent.audio_manager.play_sound('fail')
        except:
            pass
        # 清除脉动效果
        self.pulsing_tiles = []

    def find_link_path(self, start, end, grid_override=None):
        # 完全支持边界消除：起点终点也能直接走出边界
        from collections import deque
        rows, cols = self.rows, self.cols
        grid = grid_override if grid_override is not None else self.grid
        dirs = [(-1,0),(1,0),(0,-1),(0,1)]
        ext_rows, ext_cols = rows+2, cols+2
        ext_grid = [[-1 for _ in range(ext_cols)] for _ in range(ext_rows)]
        for r in range(rows):
            for c in range(cols):
                ext_grid[r+1][c+1] = grid[r][c]
        sx, sy = start[0]+1, start[1]+1
        ex, ey = end[0]+1, end[1]+1
        queue = deque()
        visited = [[[False]*4 for _ in range(ext_cols)] for _ in range(ext_rows)]
        for d, (dx,dy) in enumerate(dirs):
            nx, ny = sx+dx, sy+dy
            if 0<=nx<ext_rows and 0<=ny<ext_cols and (ext_grid[nx][ny]==-1 or [nx,ny]==[ex,ey]):
                queue.append((nx,ny,d,0,[(sx,sy),(nx,ny)]))
        while queue:
            x,y,dirc,turns,path = queue.popleft()
            if [x,y]==[ex,ey] and turns<=2:
                return [[p[0]-1,p[1]-1] for p in path]
            for nd,(dx,dy) in enumerate(dirs):
                nx,ny = x+dx,y+dy
                nturns = turns + (dirc!=nd)
                if 0<=nx<ext_rows and 0<=ny<ext_cols and (ext_grid[nx][ny]==-1 or [nx,ny]==[ex,ey]) and nturns<=2 and not visited[nx][ny][nd]:
                    visited[nx][ny][nd]=True
                    queue.append((nx,ny,nd,nturns,path+[(nx,ny)]))
        return None
