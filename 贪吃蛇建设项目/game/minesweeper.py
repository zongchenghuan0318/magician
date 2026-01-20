import pygame
import random
from .constants import FONT_NAME, WINDOW_WIDTH, WINDOW_HEIGHT

DIFFICULTY = {
    "初级": {"rows": 9, "cols": 9, "mines": 10},
    "中级": {"rows": 16, "cols": 16, "mines": 40},
    "高级": {"rows": 16, "cols": 30, "mines": 99},
    "自定义": {"rows": 9, "cols": 9, "mines": 10}
}
# 更贴近经典扫雷的尺寸与布局
CELL_SIZE = 24
TOP_BAR = 56
BOTTOM_BAR = 56

class Cell:
    def __init__(self):
        self.is_mine = False
        self.is_open = False
        self.is_flag = False
        self.number = 0

class MinesweeperGame:
    def __init__(self, surface):
        self.surface = surface
        self.difficulty = "初级"
        self.custom_setting = {"rows": 9, "cols": 9, "mines": 10}
        # 猜测保护开关：当无法推出任何安全/地雷时，点击若踩雷则搬移该雷到别处
        self.safe_click_protect_enabled = True
        # 暴露棋盘外框用于外层 UI（如返回键）避让
        self.grid_outer_rect = pygame.Rect(0, 0, 0, 0)
        # 全屏模式下棋盘整体下移像素（避免与顶部返回键重叠）
        self.fullscreen_board_shift_y = 24
        self.init_game()

    def set_difficulty(self, diff):
        self.difficulty = diff
        self.init_game()

    def set_custom_setting(self, rows, cols, mines):
        self.custom_setting = {"rows": rows, "cols": cols, "mines": mines}
        self.difficulty = "自定义"
        self.init_game()

    def init_game(self):
        if self.difficulty == "全屏":
            surface_w, surface_h = self.surface.get_size()
            available_w = max(0, surface_w - 12)
            available_h = max(0, surface_h - TOP_BAR - BOTTOM_BAR - 12)
            cols = max(9, available_w // CELL_SIZE)
            rows = max(9, available_h // CELL_SIZE)
            mines = max(1, int(rows * cols * 0.18))
            self.rows, self.cols, self.mines = rows, cols, mines
        elif self.difficulty == "自定义":
            setting = self.custom_setting
            self.rows = setting["rows"]
            self.cols = setting["cols"]
            self.mines = setting["mines"]
        else:
            setting = DIFFICULTY[self.difficulty]
            self.rows = setting["rows"]
            self.cols = setting["cols"]
            self.mines = setting["mines"]
        self.grid = [[Cell() for _ in range(self.cols)] for _ in range(self.rows)]
        self.first_click = True
        self.game_over = False
        self.win = False
        self.flagged_cells = 0
        self.remaining_cells = self.rows * self.cols - self.mines
        self.exploded_pos = None

    def place_mines(self, safe_x, safe_y):
        positions = [(x, y) for x in range(self.cols) for y in range(self.rows)
                     if abs(x - safe_x) > 1 or abs(y - safe_y) > 1]
        mines = random.sample(positions, self.mines)
        for x, y in mines:
            self.grid[y][x].is_mine = True
        for y in range(self.rows):
            for x in range(self.cols):
                if not self.grid[y][x].is_mine:
                    self.grid[y][x].number = sum(
                        self.grid[ny][nx].is_mine
                        for nx in range(max(0, x-1), min(self.cols, x+2))
                        for ny in range(max(0, y-1), min(self.rows, y+2))
                    )

    def open_cell(self, x, y):
        from .player import player_data
        cell = self.grid[y][x]
        if cell.is_flag or cell.is_open or self.game_over:
            return
        if self.first_click:
            self.place_mines(x, y)
            self.first_click = False
        cell.is_open = True
        if cell.is_mine:
            self.game_over = True
            self.exploded_pos = (x, y)
            return
        # 点开非地雷格子奖励
        player_data.add_coins(2)
        self.remaining_cells -= 1
        if cell.number == 0:
            for nx in range(max(0, x-1), min(self.cols, x+2)):
                for ny in range(max(0, y-1), min(self.rows, y+2)):
                    if not self.grid[ny][nx].is_open:
                        self.open_cell(nx, ny)
        self.check_win()

    def flag_cell(self, x, y):
        cell = self.grid[y][x]
        if not cell.is_open and not self.game_over:
            cell.is_flag = not cell.is_flag
            self.flagged_cells += 1 if cell.is_flag else -1

    def check_win(self):
        if self.remaining_cells == 0 and not self.game_over:
            self.win = True
            self.game_over = True
            # 胜利额外奖励
            from .player import player_data
            if self.difficulty == '初级':
                player_data.add_coins(100)
            elif self.difficulty == '中级':
                player_data.add_coins(200)
            elif self.difficulty == '高级':
                player_data.add_coins(500)

    def reset(self):
        self.init_game()

    def auto_open_around(self, x, y):
        """
        如果周围旗子数等于数字，自动打开周围未标记未打开的格子。
        """
        cell = self.grid[y][x]
        if not cell.is_open or cell.number == 0:
            return
        # 统计周围旗子数量
        flag_count = 0
        for nx in range(max(0, x-1), min(self.cols, x+2)):
            for ny in range(max(0, y-1), min(self.rows, y+2)):
                if self.grid[ny][nx].is_flag:
                    flag_count += 1
        if flag_count == cell.number:
            for nx in range(max(0, x-1), min(self.cols, x+2)):
                for ny in range(max(0, y-1), min(self.rows, y+2)):
                    neighbor = self.grid[ny][nx]
                    if not neighbor.is_flag and not neighbor.is_open:
                        self.open_cell(nx, ny)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos
            surface_w, surface_h = self.surface.get_size()
            # 检查重开按钮（笑脸）点击
            face_size = 32
            face_rect = pygame.Rect((surface_w-face_size)//2, (TOP_BAR-face_size)//2, face_size, face_size)
            if face_rect.collidepoint(mx, my):
                self.reset()
                return
            # 保护开关按钮
            protect_rect = self._get_protect_toggle_rect(surface_w)
            if protect_rect.collidepoint(mx, my):
                self.safe_click_protect_enabled = not self.safe_click_protect_enabled
                return
            # 检查难度按钮（含“全屏”）
            diff_names = ['初级', '中级', '高级', '全屏']
            btn_gap = 8
            btn_w = 64
            btn_h = 28
            btn_start_x = 20
            for i, name in enumerate(diff_names):
                rect = pygame.Rect(btn_start_x + i*(btn_w+btn_gap), 14, btn_w, btn_h)
                if rect.collidepoint(mx, my):
                    self.set_difficulty(name)
                    return
            # 只处理游戏区点击
            if not self.game_over:
                offset_x, offset_y = self.get_grid_offset()
                if offset_y <= my < offset_y + self.rows*CELL_SIZE and offset_x <= mx < offset_x + self.cols*CELL_SIZE:
                    x = (mx - offset_x) // CELL_SIZE
                    y = (my - offset_y) // CELL_SIZE
                    if 0 <= x < self.cols and 0 <= y < self.rows:
                        if event.button == 1:
                            cell = self.grid[y][x]
                            if cell.is_open and cell.number > 0:
                                self.auto_open_around(x, y)
                            else:
                                # 非首击，且开启保护：当无法推出任何安全/地雷时，若点到的是雷，则搬移这颗雷
                                if (not self.first_click and self.safe_click_protect_enabled and
                                    self._no_deduction_available() and cell.is_mine and not cell.is_flag and not cell.is_open):
                                    self._relocate_mine_from(x, y)
                                    self._recount_numbers()
                                # 正常开格
                                self.open_cell(x, y)
                        elif event.button == 3:
                            self.flag_cell(x, y)
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_r:
            self.reset()

    # ======= 逻辑与工具函数 =======
    def _neighbors(self, cx, cy):
        for nx in range(max(0, cx-1), min(self.cols, cx+2)):
            for ny in range(max(0, cy-1), min(self.rows, cy+2)):
                if nx == cx and ny == cy:
                    continue
                yield nx, ny

    def _is_adjacent_to_any_opened(self, x, y):
        for nx, ny in self._neighbors(x, y):
            if self.grid[ny][nx].is_open:
                return True
        return False

    def _compute_logic_sets(self):
        """基于已打开数字，计算必然安全与必然为雷的集合。"""
        safe = set()
        mines = set()
        for y in range(self.rows):
            for x in range(self.cols):
                c = self.grid[y][x]
                if not c.is_open or c.number == 0:
                    continue
                unopened = []
                flags = 0
                for nx, ny in self._neighbors(x, y):
                    n = self.grid[ny][nx]
                    if n.is_flag:
                        flags += 1
                    elif not n.is_open:
                        unopened.append((nx, ny))
                need = c.number - flags
                if need == 0:
                    for pos in unopened:
                        safe.add(pos)
                elif need == len(unopened) and need > 0:
                    for pos in unopened:
                        mines.add(pos)
        return safe, mines

    def _no_deduction_available(self):
        safe, mines = self._compute_logic_sets()
        return len(safe) == 0 and len(mines) == 0

    def _recount_numbers(self):
        for y in range(self.rows):
            for x in range(self.cols):
                if not self.grid[y][x].is_mine:
                    self.grid[y][x].number = sum(
                        self.grid[ny][nx].is_mine
                        for nx in range(max(0, x-1), min(self.cols, x+2))
                        for ny in range(max(0, y-1), min(self.rows, y+2))
                    )

    def _relocate_mine_from(self, mx, my):
        """
        将(mx,my)处的地雷搬到“争议区”且不改变当前已显示数字：
        - 源格子与目标格子都不能邻接任何已打开格子（这样不会影响已显示数字）
        - 目标必须是未翻开、未插旗、非地雷，且属于“不可推理集合”（既非必然安全也非必然地雷）
        若无法满足，则不搬运。
        """
        # 源格若邻接已打开格子，则移走会改变这些格子的数字，禁止搬运
        if self._is_adjacent_to_any_opened(mx, my):
            return
        # 计算推理集合
        safe_set, mine_set = self._compute_logic_sets()
        # 目标候选：未开、未旗、非雷、非safe_set、非mine_set，且不邻接任何已打开格
        candidates = []
        for y in range(self.rows):
            for x in range(self.cols):
                if x == mx and y == my:
                    continue
                c = self.grid[y][x]
                if c.is_open or c.is_flag or c.is_mine:
                    continue
                if (x, y) in safe_set or (x, y) in mine_set:
                    continue
                if self._is_adjacent_to_any_opened(x, y):
                    continue
                candidates.append((x, y))
        if not candidates:
            return
        tx, ty = random.choice(candidates)
        # 搬运（此时不会影响任何已打开格子的数字）
        self.grid[my][mx].is_mine = False
        self.grid[ty][tx].is_mine = True

    def _get_protect_toggle_rect(self, surface_w):
        # 放在计时器左侧
        w, h = 90, 28
        x = surface_w - 20 - 14*3 - 6*2 - w - 12
        y = 14
        return pygame.Rect(x, y, w, h)

    def get_grid_offset(self):
        surface_w, surface_h = self.surface.get_size()
        total_width = self.cols * CELL_SIZE
        total_height = self.rows * CELL_SIZE
        offset_x = (surface_w - total_width) // 2
        offset_y = TOP_BAR + (surface_h - TOP_BAR - BOTTOM_BAR - total_height) // 2
        if self.difficulty == "全屏":
            offset_y += self.fullscreen_board_shift_y
        return offset_x, offset_y

    def draw(self):
        surface_w, surface_h = self.surface.get_size()
        # 渐变背景
        for i in range(surface_h):
            color = (
                220 - i//8,
                230 - i//12,
                255 - i//16
            )
            pygame.draw.line(self.surface, color, (0, i), (surface_w, i))
        # 顶部栏：经典灰金风格（计雷器/计时器/笑脸重开）
        # 顶部底色
        pygame.draw.rect(self.surface, (192, 192, 192), (0, 0, surface_w, TOP_BAR))
        pygame.draw.line(self.surface, (255,255,255), (0, TOP_BAR-2), (surface_w, TOP_BAR-2), 2)
        pygame.draw.line(self.surface, (128,128,128), (0, TOP_BAR-1), (surface_w, TOP_BAR-1), 2)

        # 七段数码管样式渲染
        def draw_seven_seg(x, y, value):
            val = max(0, min(999, value))
            s = f"{val:03d}"
            seg_w, seg_h, gap = 14, 24, 6
            for i, ch in enumerate(s):
                rect = pygame.Rect(x + i*(seg_w+gap), y, seg_w, seg_h)
                pygame.draw.rect(self.surface, (0,0,0), rect)
                # 使用红色数字模拟数码管
                dig_font = pygame.font.Font(FONT_NAME, 24)
                txt = dig_font.render(ch, True, (255,0,0))
                self.surface.blit(txt, txt.get_rect(center=rect.center))

        # 左侧：难度按钮与剩余雷数（含“全屏”）
        diff_names = ['初级', '中级', '高级', '全屏']
        btn_gap = 8
        btn_w = 64
        btn_h = 28
        btn_start_x = 20
        small_font = pygame.font.Font(FONT_NAME, 18)
        for i, name in enumerate(diff_names):
            sel = name == self.difficulty
            rect = pygame.Rect(btn_start_x + i*(btn_w+btn_gap), 14, btn_w, btn_h)
            pygame.draw.rect(self.surface, (160,160,160) if sel else (210,210,210), rect)
            pygame.draw.rect(self.surface, (255,255,255), rect, 1)
            label = small_font.render(name, True, (0,0,0))
            self.surface.blit(label, label.get_rect(center=rect.center))
        # 剩余雷数
        remaining = max(0, self.mines - self.flagged_cells)
        draw_seven_seg(btn_start_x + len(diff_names)*(btn_w+btn_gap) + 18, 16, remaining)

        # 中间：笑脸重开按钮（根据胜负切换表情）
        face_size = 32
        face_rect = pygame.Rect((surface_w-face_size)//2, (TOP_BAR-face_size)//2, face_size, face_size)
        pygame.draw.circle(self.surface, (255, 255, 0), face_rect.center, face_size//2)
        if self.game_over and not self.win:
            # 失败：X 眼 + 下弯嘴
            # X 眼
            for ex in (-6, 6):
                cx = face_rect.centerx + ex
                cy = face_rect.centery - 5
                pygame.draw.line(self.surface, (0,0,0), (cx-3, cy-3), (cx+3, cy+3), 2)
                pygame.draw.line(self.surface, (0,0,0), (cx-3, cy+3), (cx+3, cy-3), 2)
            # 下弯嘴
            pygame.draw.arc(self.surface, (0,0,0), (face_rect.centerx-10, face_rect.centery+2, 20, 12), 3.4, 6.0, 2)
        else:
            # 正常：圆眼 + 上弯嘴
            pygame.draw.circle(self.surface, (0,0,0), (face_rect.centerx-6, face_rect.centery-5), 3)
            pygame.draw.circle(self.surface, (0,0,0), (face_rect.centerx+6, face_rect.centery-5), 3)
            pygame.draw.arc(self.surface, (0,0,0), (face_rect.centerx-10, face_rect.centery-3, 20, 14), 0.3, 2.84, 2)
        self.face_rect = face_rect

        # 顶部栏胜利提示（不在棋盘上显示）
        if self.game_over and self.win:
            victory_font = pygame.font.Font(FONT_NAME, 24)
            victory_text = victory_font.render("胜利！", True, (255, 255, 0))
            vx = face_rect.right + 16
            vy = face_rect.centery - victory_text.get_height() // 2
            self.surface.blit(victory_text, (vx, vy))

        # 右侧：计时器（秒）
        elapsed = 0 if self.first_click else int((pygame.time.get_ticks()//1000) % 1000)
        draw_seven_seg(surface_w - 20 - 14*3 - 6*2, 16, elapsed)
        # 计时器左侧：保护开关
        protect_rect = self._get_protect_toggle_rect(surface_w)
        pygame.draw.rect(self.surface, (210,210,210), protect_rect)
        pygame.draw.rect(self.surface, (255,255,255), protect_rect, 1)
        small_font = pygame.font.Font(FONT_NAME, 18)
        label = "保护:开" if self.safe_click_protect_enabled else "保护:关"
        txt = small_font.render(label, True, (0,0,0))
        self.surface.blit(txt, txt.get_rect(center=protect_rect.center))
        # 游戏区外框（经典凹凸边）
        offset_x, offset_y = self.get_grid_offset()
        grid_w = self.cols * CELL_SIZE
        grid_h = self.rows * CELL_SIZE
        outer = pygame.Rect(offset_x-6, offset_y-6, grid_w+12, grid_h+12)
        # 暴露网格外框给外层用于避让按钮摆放
        self.grid_outer_rect = outer
        pygame.draw.rect(self.surface, (192,192,192), outer)
        # 外框高光/阴影
        pygame.draw.line(self.surface, (255,255,255), outer.topleft, outer.topright, 2)
        pygame.draw.line(self.surface, (255,255,255), outer.topleft, outer.bottomleft, 2)
        pygame.draw.line(self.surface, (128,128,128), outer.bottomleft, outer.bottomright, 2)
        pygame.draw.line(self.surface, (128,128,128), outer.topright, outer.bottomright, 2)
        # 扫雷格子
        mx, my = pygame.mouse.get_pos()
        for y in range(self.rows):
            for x in range(self.cols):
                rect = pygame.Rect(offset_x + x*CELL_SIZE, offset_y + y*CELL_SIZE, CELL_SIZE, CELL_SIZE)
                cell = self.grid[y][x]
                # 经典银灰色格子
                if cell.is_open:
                    # 更浅的平面灰，增强与未翻开的对比
                    pygame.draw.rect(self.surface, (224, 224, 224), rect)
                    # 内凹边：上/左深、下/右亮
                    pygame.draw.line(self.surface, (128,128,128), rect.topleft, rect.topright, 1)
                    pygame.draw.line(self.surface, (128,128,128), rect.topleft, rect.bottomleft, 1)
                    pygame.draw.line(self.surface, (255,255,255), (rect.left, rect.bottom-1), (rect.right-1, rect.bottom-1), 1)
                    pygame.draw.line(self.surface, (255,255,255), (rect.right-1, rect.top), (rect.right-1, rect.bottom), 1)
                else:
                    # 未打开：更深的凸起银灰 + 强对比高光/阴影
                    base = (192,192,192)
                    pygame.draw.rect(self.surface, base, rect)
                    pygame.draw.line(self.surface, (255,255,255), rect.topleft, rect.topright, 3)
                    pygame.draw.line(self.surface, (255,255,255), rect.topleft, rect.bottomleft, 3)
                    pygame.draw.line(self.surface, (64,64,64), rect.bottomleft, rect.bottomright, 3)
                    pygame.draw.line(self.surface, (64,64,64), rect.topright, rect.bottomright, 3)
                    # 悬停高亮（便于和已打开区分）
                    if rect.collidepoint(mx, my) and not cell.is_flag and not self.game_over:
                        pygame.draw.rect(self.surface, (255, 255, 180), rect.inflate(-3, -3), 2)
                # 地雷
                if cell.is_open:
                    if cell.is_mine:
                        # 更像“雷”的造型：圆体+8向尖刺+高光；爆炸雷为红色主体
                        def draw_mine(target_rect, exploded=False):
                            cx, cy = target_rect.center
                            radius = CELL_SIZE//3
                            # 主体颜色
                            body_color = (220, 40, 40) if exploded else (0, 0, 0)
                            outline = (0, 0, 0)
                            # 画尖刺（8方向）
                            dirs = [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(1,-1),(1,1),(-1,1)]
                            r_out = CELL_SIZE//2 - 2
                            r_in = max(2, radius - 4)
                            for dx, dy in dirs:
                                x1 = cx + dx * r_in
                                y1 = cy + dy * r_in
                                x2 = cx + dx * r_out
                                y2 = cy + dy * r_out
                                pygame.draw.line(self.surface, outline, (x1, y1), (x2, y2), 2)
                            # 主体圆
                            pygame.draw.circle(self.surface, body_color, (cx, cy), radius)
                            pygame.draw.circle(self.surface, outline, (cx, cy), radius, 2)
                            # 高光
                            hl_r = max(2, radius//3)
                            pygame.draw.circle(self.surface, (255,255,255), (cx - radius//2, cy - radius//2), hl_r)
                            # 爆炸时加黑色“X”
                            if exploded:
                                pygame.draw.line(self.surface, (0,0,0), (cx-radius, cy-radius), (cx+radius, cy+radius), 2)
                                pygame.draw.line(self.surface, (0,0,0), (cx-radius, cy+radius), (cx+radius, cy-radius), 2)

                        draw_mine(rect, exploded=(self.exploded_pos == (x, y)))
                    elif cell.number > 0:
                        # 数字字号下调，提升清晰度并留白
                        num_font = pygame.font.Font(FONT_NAME, 18)
                        text = num_font.render(str(cell.number), True, self.get_number_color(cell.number))
                        self.surface.blit(text, text.get_rect(center=rect.center))
                elif cell.is_flag:
                    # 经典旗帜样式（红旗+黑杆）
                    pole_x = rect.left + 6
                    pygame.draw.line(self.surface, (0,0,0), (pole_x, rect.bottom-6), (pole_x, rect.top+6), 2)
                    pygame.draw.polygon(self.surface, (255,0,0), [(pole_x+2, rect.top+6), (pole_x+2, rect.top+16), (pole_x+14, rect.top+11)])
        # 不在棋盘上绘制胜负横幅
        # ...existing code...

    def get_number_color(self, number):
        colors = {
            1: (0,0,255), 2: (0,128,0), 3: (255,0,0), 4: (128,0,128),
            5: (128,0,0), 6: (0,128,128), 7: (0,0,0), 8: (128,128,128)
        }
        return colors.get(number, (0,0,0)) 