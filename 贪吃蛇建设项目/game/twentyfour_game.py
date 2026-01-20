import pygame
import random
import math
from .constants import *
from .ui_elements import Button
from .player import player_data

class TwentyFourPage:
    def __init__(self, surface, parent):
        self.surface = surface
        self.parent = parent
        self.init_cards = []
        self.cards = []
        self.selected = []  # 选中的卡片索引
        self.selected_op = None
        self.result = None
        self.msg = ''
        self.msg_alpha = 255  # 成功提示信息的透明度
        self.msg_timer = 0  # 成功提示信息计时器
        self.history = []  # 用于复原
        self.operators = ['+', '-', '*', '/']
        self.op_buttons = []
        self.solved_count = 0  # 成功次数
        # 新增：计分与计时
        self.score = 0
        self.timer_duration = 60  # 每轮60秒
        self.round_start_ticks = pygame.time.get_ticks()
        self.anim_tick = 0
        self._auto_next_time = None  # 自动切换时间戳
        self._card_rects = []  # 初始化_card_rects
        # 美化新增：背景缓存与资源
        self._bg_surf = None
        # 提示文本
        self.hint_text = ''
        self.hint_solutions = []
        self.hint_index = 0
        self.hint_cards_snapshot = None
        self.generate_cards()
        self._init_op_buttons()
        self._ensure_background()

    def _solve_24_expression(self, numbers):
        """基于当前游戏规则（整数加法、乘法、绝对值减法、整除）搜索一个表达式=24。找不到返回None。"""
        items = [(int(n), str(int(n))) for n in numbers]
        memo = set()

        def key(vals):
            return tuple(sorted(v for v, _ in vals))

        def dfs(vals):
            k = key(vals)
            if k in memo:
                return None
            memo.add(k)

            if len(vals) == 1:
                if vals[0][0] == 24:
                    return vals[0][1]
                return None

            n = len(vals)
            for i in range(n):
                for j in range(i+1, n):
                    a_val, a_expr = vals[i]
                    b_val, b_expr = vals[j]
                    rest = [vals[k] for k in range(n) if k != i and k != j]

                    candidates = []
                    # a + b
                    candidates.append((a_val + b_val, f'({a_expr}+{b_expr})'))
                    # a * b
                    candidates.append((a_val * b_val, f'({a_expr}×{b_expr})'))
                    # |a - b|
                    if a_val >= b_val:
                        candidates.append((a_val - b_val, f'({a_expr}-{b_expr})'))
                    else:
                        candidates.append((b_val - a_val, f'({b_expr}-{a_expr})'))
                    # 大除小（整除）
                    big, small = (a_val, b_val) if a_val >= b_val else (b_val, a_val)
                    if small != 0 and big % small == 0:
                        if a_val >= b_val:
                            candidates.append((big // small, f'({a_expr}/{b_expr})'))
                        else:
                            candidates.append((big // small, f'({b_expr}/{a_expr})'))

                    for v, e in candidates:
                        res = dfs(rest + [(v, e)])
                        if res is not None:
                            return res
            return None

        return dfs(items)

    def _enumerate_24_expressions(self, numbers, limit=20):
        """枚举若干个可行表达式，最多返回 limit 条。"""
        items = [(int(n), str(int(n))) for n in numbers]
        results = []
        memo = set()

        def key(vals):
            return tuple(sorted(v for v, _ in vals))

        def dfs(vals):
            if len(results) >= limit:
                return
            k = key(vals)
            if k in memo:
                return
            memo.add(k)
            if len(vals) == 1:
                if vals[0][0] == 24:
                    results.append(vals[0][1])
                return
            n = len(vals)
            for i in range(n):
                for j in range(i+1, n):
                    a_val, a_expr = vals[i]
                    b_val, b_expr = vals[j]
                    rest = [vals[k] for k in range(n) if k != i and k != j]

                    candidates = []
                    # a + b
                    candidates.append((a_val + b_val, f'({a_expr}+{b_expr})'))
                    # a * b
                    candidates.append((a_val * b_val, f'({a_expr}×{b_expr})'))
                    # |a - b|
                    if a_val >= b_val:
                        candidates.append((a_val - b_val, f'({a_expr}-{b_expr})'))
                    else:
                        candidates.append((b_val - a_val, f'({b_expr}-{a_expr})'))
                    # 大除小（整除）
                    big, small = (a_val, b_val) if a_val >= b_val else (b_val, a_val)
                    if small != 0 and big % small == 0:
                        if a_val >= b_val:
                            candidates.append((big // small, f'({a_expr}/{b_expr})'))
                        else:
                            candidates.append((big // small, f'({b_expr}/{a_expr})'))

                    for v, e in candidates:
                        if len(results) >= limit:
                            break
                        dfs(rest + [(v, e)])

        dfs(items)
        # 去重
        dedup = []
        seen = set()
        for expr in results:
            if expr not in seen:
                seen.add(expr)
                dedup.append(expr)
        return dedup

    def _handle_hint_click(self):
        # 若牌组发生变化，则重算解集
        cards_now = tuple(self.cards)
        if self.hint_cards_snapshot != cards_now or not self.hint_solutions:
            if len(self.cards) >= 2:
                sols = self._enumerate_24_expressions(self.cards, limit=20)
                self.hint_solutions = sols
                self.hint_cards_snapshot = cards_now
                self.hint_index = 0
            else:
                self.hint_solutions = []
                self.hint_text = '请先保留至少两张牌'
                return

        # 无解
        if not self.hint_solutions:
            self.hint_text = '当前牌面无整除条件的解（或较难），试试换一组'
            return

        # 显示当前解并推进索引
        self.hint_text = self.hint_solutions[self.hint_index]
        self.hint_index = (self.hint_index + 1) % len(self.hint_solutions)

    def generate_cards(self):
        self.init_cards = [random.randint(1, 10) for _ in range(4)]
        self.cards = self.init_cards[:]
        self.selected = []
        self.selected_op = None
        self.result = None
        self.msg = ''
        self.history = []
        self._auto_next_time = None
        self._init_op_buttons()
        self.hint_text = ''
        self.hint_solutions = []
        self.hint_index = 0
        self.hint_cards_snapshot = None
        # 重置本轮计时
        self.round_start_ticks = pygame.time.get_ticks()

    def _init_op_buttons(self):
        self.op_buttons = []
        win_rect = self.surface.get_rect()
        op_y = int(win_rect.height * 0.65)
        btn_w, btn_h = 110, 64
        gap = 40
        total_w = btn_w * 4 + gap * 3
        start_x = win_rect.centerx - total_w // 2
        
        # 添加按钮背景光晕效果
        self.op_buttons_bg = pygame.Surface((total_w, btn_h), pygame.SRCALPHA)
        pygame.draw.rect(self.op_buttons_bg, (255, 255, 255, 30), (0, 0, total_w, btn_h), border_radius=20)
        pygame.draw.rect(self.op_buttons_bg, (255, 255, 255, 60), (0, 0, total_w, btn_h), 2, border_radius=20)
        
        for i, op in enumerate(self.operators):
            x = start_x + i * (btn_w + gap)
            b = Button(x, op_y, btn_w, btn_h, op, font_size=36)
            self.op_buttons.append(b)

    def _ensure_background(self):
        """构建更鲜艳的多彩背景并缓存，窗口尺寸变化时重建。"""
        try:
            win_rect = self.surface.get_rect()
            need_rebuild = (
                self._bg_surf is None or
                self._bg_surf.get_width() != win_rect.width or
                self._bg_surf.get_height() != win_rect.height
            )
            if not need_rebuild:
                return

            w, h = win_rect.width, win_rect.height
            base = pygame.Surface((w, h), pygame.SRCALPHA)

            # 1) 横向多段渐变（暖黄 -> 樱粉 -> 亮蓝），明快且活泼
            c0 = (255, 248, 200)   # 暖黄
            c1 = (255, 167, 196)   # 樱粉
            c2 = (120, 220, 255)   # 亮蓝
            for x in range(w):
                t = x / max(1, w - 1)
                if t < 0.5:
                    u = t / 0.5
                    r = int(c0[0] * (1 - u) + c1[0] * u)
                    g = int(c0[1] * (1 - u) + c1[1] * u)
                    b = int(c0[2] * (1 - u) + c1[2] * u)
                else:
                    u = (t - 0.5) / 0.5
                    r = int(c1[0] * (1 - u) + c2[0] * u)
                    g = int(c1[1] * (1 - u) + c2[1] * u)
                    b = int(c1[2] * (1 - u) + c2[2] * u)
                pygame.draw.line(base, (r, g, b, 255), (x, 0), (x, h))

            # 2) 纵向柔光提升层次（居中最亮，四周略暗）
            vert = pygame.Surface((w, h), pygame.SRCALPHA)
            for yy in range(h):
                # 中间更亮，两端更淡
                a = int(60 * (1 - abs((yy - h / 2) / (h / 2)) ** 0.8))
                pygame.draw.line(vert, (255, 255, 255, max(0, a)), (0, yy), (w, yy))
            base.blit(vert, (0, 0))

            # 3) 多彩「色块云」：大尺寸径向渐变，营造趣味与深度
            def draw_blob(cx, cy, radius, color):
                overlay = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
                cr, cg, cb = color
                for r in range(radius, 0, -2):
                    alpha = int(140 * (r / radius) ** 1.6)
                    pygame.draw.circle(overlay, (cr, cg, cb, alpha), (radius, radius), r)
                base.blit(overlay, (int(cx - radius), int(cy - radius)))

            m = min(w, h)
            draw_blob(w * 0.22, h * 0.28, int(m * 0.22), (76, 175, 80))     # 明绿
            draw_blob(w * 0.78, h * 0.22, int(m * 0.20), (255, 128, 171))   # 粉樱
            draw_blob(w * 0.86, h * 0.66, int(m * 0.18), (124, 77, 255))    # 紫罗兰
            draw_blob(w * 0.30, h * 0.74, int(m * 0.18), (255, 213, 79))    # 琥珀
            draw_blob(w * 0.50, h * 0.45, int(m * 0.16), (3, 169, 244))     # 天蓝

            # 4) 斜向高光条纹（极淡），增强现代感
            stripe = pygame.Surface((w, h), pygame.SRCALPHA)
            step = max(24, int(m * 0.03))
            for i in range(-h, w, step):
                pygame.draw.line(stripe, (255, 255, 255, 18), (i, 0), (i + h, h), 2)
            base.blit(stripe, (0, 0))

            # 5) 轻微散景（bokeh）点，带来活力与质感
            rng = random.Random(12345)
            for _ in range(70):
                r = rng.randint(6, 16)
                xx = rng.randint(0, max(0, w - 1))
                yy = rng.randint(0, max(0, h - 1))
                alpha = rng.randint(8, 18)
                pygame.draw.circle(base, (255, 255, 255, alpha), (xx, yy), r)

            # 6) 轻磨砂玻璃遮罩，提升对比度（不影响颜色鲜艳度）
            glass = pygame.Surface((w, h), pygame.SRCALPHA)
            glass.fill((255, 255, 255, 34))
            base.blit(glass, (0, 0))

            # 7) 细微暗角，使中央内容更聚焦
            vignette = pygame.Surface((w, h), pygame.SRCALPHA)
            for yy in range(h):
                a = int(85 * (1 - abs((yy - h / 2) / (h / 2))))
                pygame.draw.line(vignette, (0, 0, 0, max(0, a // 5)), (0, yy), (w, yy))
            base.blit(vignette, (0, 0))

            self._bg_surf = base
        except Exception:
            # 出错时忽略，保持原有绘制
            self._bg_surf = None

    def draw(self):
        win_rect = self.surface.get_rect()
        self.anim_tick += 1
        
        # 自动切换到下一组
        if self._auto_next_time and pygame.time.get_ticks() >= self._auto_next_time:
            self.generate_cards()
            self._auto_next_time = None
            
        # 背景（缓存）
        self._ensure_background()
        if self._bg_surf is not None:
            self.surface.blit(self._bg_surf, (0, 0))
        else:
            # 兜底的渐变
            grad = pygame.Surface((win_rect.width, win_rect.height), pygame.SRCALPHA)
            for y in range(win_rect.height):
                c = 245 - int(60 * y / win_rect.height)
                pygame.draw.line(grad, (c, c+8, 255, 255), (0, y), (win_rect.width, y))
            self.surface.blit(grad, (0, 0))
        
        # 标题
        left_margin = win_rect.x + 60
        y_cursor = 40
        font = pygame.font.Font(FONT_NAME, 54)
        title_shadow = font.render('24点游戏', True, (0,0,0))
        title_rect = title_shadow.get_rect(topleft=(left_margin+2, y_cursor+2))
        self.surface.blit(title_shadow, title_rect)
        title_text = font.render('24点游戏', True, (255,87,34))
        title_rect_fg = title_text.get_rect(topleft=(left_margin, y_cursor))
        self.surface.blit(title_text, title_rect_fg)
        y_cursor = title_rect_fg.bottom

        # 简短提示（紧随标题下方）
        sub_font = pygame.font.Font(FONT_NAME, 22)
        tip = sub_font.render('选择两张牌后点运算符；也支持三/四张牌的加法或乘法合成', True, (255,255,255))
        tip_bg = pygame.Surface((tip.get_width()+20, tip.get_height()+12), pygame.SRCALPHA)
        pygame.draw.rect(tip_bg, (0,0,0,100), tip_bg.get_rect(), border_radius=10)
        tip_pos = (left_margin-2, y_cursor + 10)
        self.surface.blit(tip_bg, tip_pos)
        self.surface.blit(tip, (tip_pos[0]+10, tip_pos[1]+6))
        y_cursor = tip_pos[1] + tip_bg.get_height()

        # 顶部右侧：金币、进度与得分
        info_font = pygame.font.Font(FONT_NAME, 28)
        coins = player_data.get_coins()
        info_text = info_font.render(f'金币 {coins}｜已解 {self.solved_count}｜得分 {self.score}', True, (255,255,255))
        info_rect = info_text.get_rect()
        pill_w, pill_h = info_rect.width + 28, info_rect.height + 12
        pill_x, pill_y = win_rect.right - pill_w - 40, 42
        pill_surf = pygame.Surface((pill_w, pill_h), pygame.SRCALPHA)
        pygame.draw.rect(pill_surf, (0,0,0,120), (0,0,pill_w,pill_h), border_radius=18)
        pygame.draw.rect(pill_surf, (255,255,255,80), (0,0,pill_w,pill_h), 2, border_radius=18)
        self.surface.blit(pill_surf, (pill_x, pill_y))
        self.surface.blit(info_text, (pill_x + 14, pill_y + 6))
        
        # 圆形计时器（位于信息胶囊左侧）
        elapsed_ms = pygame.time.get_ticks() - self.round_start_ticks
        total_ms = self.timer_duration * 1000
        remain_ms = max(0, total_ms - elapsed_ms)
        remain_sec = int((remain_ms + 999) // 1000)
        progress = max(0.0, 1.0 - (elapsed_ms / total_ms if total_ms > 0 else 0.0))
        timer_radius = 28
        timer_cx = pill_x - 80
        timer_cy = pill_y + pill_h // 2
        # 背景环
        for i in range(36):
            angle = i * 10
            start = (timer_cx + timer_radius * math.cos(math.radians(angle)),
                     timer_cy + timer_radius * math.sin(math.radians(angle)))
            end = (timer_cx + (timer_radius-4) * math.cos(math.radians(angle)),
                   timer_cy + (timer_radius-4) * math.sin(math.radians(angle)))
            pygame.draw.line(self.surface, (220,220,220), start, end, 3)
        # 进度环（绿-橙-红渐变）
        segs = int(progress * 36 + 0.5)
        for i in range(segs):
            t = i / max(1, 36-1)
            # 颜色插值：绿->橙->红
            if t < 0.5:
                u = t/0.5
                c = (int(76*(1-u)+255*u), int(175*(1-u)+193*u), int(80*(1-u)+7*u))
            else:
                u = (t-0.5)/0.5
                c = (int(255*(1-u)+244*u), int(193*(1-u)+67*u), int(7*(1-u)+54*u))
            angle = i * 10
            start = (timer_cx + timer_radius * math.cos(math.radians(angle)),
                     timer_cy + timer_radius * math.sin(math.radians(angle)))
            end = (timer_cx + (timer_radius-4) * math.cos(math.radians(angle)),
                   timer_cy + (timer_radius-4) * math.sin(math.radians(angle)))
            pygame.draw.line(self.surface, c, start, end, 3)
        # 中心数字
        tfont = pygame.font.Font(FONT_NAME, 24)
        tnum = tfont.render(str(remain_sec), True, (255, 87, 34))
        trect = tnum.get_rect(center=(timer_cx, timer_cy))
        self.surface.blit(tnum, trect)
        # 时间到则提示并切换
        if remain_ms == 0 and not self._auto_next_time:
            self.msg = '时间到，已换一组'
            self._auto_next_time = pygame.time.get_ticks() + 800
        
        # （移除旧的统计渐变条，避免与提示重叠）
        
        # 卡片区
        card_font = pygame.font.Font(FONT_NAME, 72)
        card_w, card_h = int(win_rect.width*0.15), int(win_rect.height*0.18)
        card_gap = int(win_rect.width*0.05)
        total_cards_w = card_w * len(self.cards) + card_gap * (len(self.cards)-1)
        start_x = win_rect.centerx - total_cards_w // 2
        
        # 创建卡片背景效果（玻璃化卡槽），紧随提示下方
        cards_bg_height = int(win_rect.height * 0.25)
        cards_bg_y = y_cursor + 16
        cards_bg_rect = pygame.Rect(win_rect.centerx - total_cards_w//2 - 20, 
                                  cards_bg_y - 20, 
                                  total_cards_w + 40, 
                                  cards_bg_height + 40)
        
        # 轻磨砂底
        cards_glass = pygame.Surface((cards_bg_rect.width, cards_bg_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(cards_glass, (255, 255, 255, 38), (0, 0, cards_bg_rect.width, cards_bg_rect.height), border_radius=22)
        pygame.draw.rect(cards_glass, (255, 255, 255, 80), (0, 0, cards_bg_rect.width, cards_bg_rect.height), 2, border_radius=22)
        self.surface.blit(cards_glass, cards_bg_rect.topleft)
        
        # 绘制卡片
        self._card_rects = []  # 清空之前的_rects
        for i, card in enumerate(self.cards):
            x = start_x + i * (card_w + card_gap)
            y = cards_bg_y + math.sin(self.anim_tick * 0.1 + i) * 5  # 添加上下浮动动画
            
            # 创建卡片表面
            card_surface = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
            
            # 卡片基础（玻璃质感+高光）
            if i in self.selected:
                pulse = abs(math.sin(self.anim_tick * 0.2))
                base_alpha = 215
                border_alpha = min(255, 180 + int(pulse * 75))
                pygame.draw.rect(card_surface, (255, 255, 255, base_alpha), (0, 0, card_w, card_h), border_radius=16)
                pygame.draw.rect(card_surface, (255, 87, 34, border_alpha), (0, 0, card_w, card_h), 5, border_radius=16)
            else:
                pygame.draw.rect(card_surface, (255, 255, 255, 205), (0, 0, card_w, card_h), border_radius=16)
                pygame.draw.rect(card_surface, (230, 230, 230), (0, 0, card_w, card_h), 4, border_radius=16)

            # 顶部高光条
            highlight = pygame.Surface((card_w-8, card_h//3), pygame.SRCALPHA)
            pygame.draw.rect(highlight, (255,255,255,90), highlight.get_rect(), border_radius=12)
            card_surface.blit(highlight, (4, 4))
            
            # 绘制数字
            text = card_font.render(str(card), True, (255, 87, 34))
            text_rect = text.get_rect(center=(card_w//2, card_h//2))
            card_surface.blit(text, text_rect)
            
            # 添加阴影效果
            shadow = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
            pygame.draw.rect(shadow, (0, 0, 0, 40), (2, 2, card_w-4, card_h-4), 4, border_radius=16)
            self.surface.blit(shadow, (x+2, y+2))
            
            # 绘制卡片
            self.surface.blit(card_surface, (x, y))
            
            # 记录卡片矩形区域
            self._card_rects.append(pygame.Rect(x, y, card_w, card_h))
        
        # 操作符区域（放在卡片区下方，避免重叠）
        flow_y = cards_bg_rect.bottom
        if self.selected_op is not None and len(self.selected) == 2:
            # 创建操作符背景
            op_result_w, op_result_h = 120, 80
            op_result_x = win_rect.centerx - op_result_w // 2
            op_result_y = flow_y + 12
            
            # 操作符背景动画
            result_glow = pygame.Surface((op_result_w, op_result_h), pygame.SRCALPHA)
            pygame.draw.rect(result_glow, (255, 215, 0, 100), (0, 0, op_result_w, op_result_h), border_radius=20)
            pygame.draw.rect(result_glow, (255, 215, 0), (0, 0, op_result_w, op_result_h), 3, border_radius=20)
            
            # 添加脉冲效果
            pulse = abs(math.sin(self.anim_tick * 0.1)) * 0.1
            scaled_result_w = int(op_result_w * (1 + pulse))
            scaled_result_h = int(op_result_h * (1 + pulse))
            scaled_result_x = op_result_x - (scaled_result_w - op_result_w) // 2
            scaled_result_y = op_result_y - (scaled_result_h - op_result_h) // 2
            
            # 绘制放大后的结果框
            scaled_glow = pygame.transform.scale(result_glow, (scaled_result_w, scaled_result_h))
            self.surface.blit(scaled_glow, (scaled_result_x, scaled_result_y))
            
            # 绘制操作符
            op_font = pygame.font.Font(FONT_NAME, 48)
            op_text = op_font.render(self.operators[self.selected_op], True, (255, 87, 34))
            op_text_rect = op_text.get_rect(center=(scaled_result_x + scaled_result_w//2, 
                                                    scaled_result_y + scaled_result_h//2))
            self.surface.blit(op_text, op_text_rect)
            flow_y = scaled_result_y + scaled_result_h
        
        # 结果展示
        if self.result is not None:
            result_font = pygame.font.Font(FONT_NAME, 48)
            result_text = result_font.render(f'结果: {self.result}', True, (255, 87, 34))
            result_rect = result_text.get_rect()
            result_rect.midtop = (win_rect.centerx, flow_y + 12)
            
            # 添加结果背景光晕
            result_glow = pygame.Surface((result_rect.width + 40, result_rect.height + 20), pygame.SRCALPHA)
            pygame.draw.rect(result_glow, (255, 215, 0, 100), (0, 0, result_glow.get_width(), result_glow.get_height()), border_radius=15)
            pygame.draw.rect(result_glow, (255, 215, 0), (0, 0, result_glow.get_width(), result_glow.get_height()), 2, border_radius=15)
            
            # 添加脉冲效果
            pulse = abs(math.sin(self.anim_tick * 0.1)) * 0.1
            scaled_result_glow = pygame.transform.scale(result_glow, 
                (int(result_glow.get_width() * (1 + pulse)), 
                 int(result_glow.get_height() * (1 + pulse))))
            
            scaled_result_rect = scaled_result_glow.get_rect(center=result_rect.center)
            
            self.surface.blit(scaled_result_glow, scaled_result_rect.topleft)
            self.surface.blit(result_text, result_rect)
            flow_y = scaled_result_rect.bottom

        # 提示文本显示（多方案循环展示，跟随内容流）
        if getattr(self, 'hint_text', ''):
            hint_font = pygame.font.Font(FONT_NAME, 28)
            page_info = ''
            if self.hint_solutions:
                page_info = f'  ({self.hint_index+1}/{len(self.hint_solutions)})'
            hint_surf = hint_font.render(f'提示：{self.hint_text}{page_info}', True, (255, 213, 79))
            hint_bg = pygame.Surface((hint_surf.get_width()+20, hint_surf.get_height()+12), pygame.SRCALPHA)
            pygame.draw.rect(hint_bg, (0, 0, 0, 90), hint_bg.get_rect(), border_radius=10)
            hint_pos = (win_rect.centerx - hint_bg.get_width()//2, flow_y + 12)
            self.surface.blit(hint_bg, hint_pos)
            self.surface.blit(hint_surf, (hint_pos[0]+10, hint_pos[1]+6))
            flow_y = hint_pos[1] + hint_bg.get_height()
        
        # 消息显示（全局，跟随内容流）
        if self.msg:
            # 成功提示淡入/停留/淡出动画
            if self.msg.startswith('恭喜，算出24!'):
                self.msg_timer += 1
                fade_duration = 60
                fade_out_start = 180
                if self.msg_timer < fade_duration:
                    self.msg_alpha = int(255 * (self.msg_timer / fade_duration))
                elif self.msg_timer > fade_out_start:
                    self.msg_alpha = int(255 * ((fade_out_start + fade_duration - self.msg_timer) / fade_duration))
                if self.msg_timer > fade_out_start + fade_duration:
                    self.msg = ''
                    self.msg_timer = 0
                    self.msg_alpha = 255
            else:
                self.msg_alpha = 255
                self.msg_timer = 0

            msg_font = pygame.font.Font(FONT_NAME, 36)
            msg_text = msg_font.render(self.msg, True, (0, 255, 0))
            msg_bg = pygame.Surface((msg_text.get_width()+24, msg_text.get_height()+16), pygame.SRCALPHA)
            pygame.draw.rect(msg_bg, (0, 0, 0, 100), msg_bg.get_rect(), border_radius=12)
            msg_bg.set_alpha(self.msg_alpha)
            msg_text.set_alpha(self.msg_alpha)
            msg_x = win_rect.centerx - msg_bg.get_width() // 2
            msg_y = flow_y + 12
            self.surface.blit(msg_bg, (msg_x, msg_y))
            self.surface.blit(msg_text, (msg_x + 12, msg_y + 8))
            flow_y = msg_y + msg_bg.get_height()

        # 操作按钮
        btn_w, btn_h = 110, 64
        gap = 40
        total_w = btn_w * 4 + gap * 3
        start_x = win_rect.centerx - total_w // 2

        # 操作按钮容器位置：跟随内容流（不与上方重叠）
        op_buttons_y = flow_y + 24
        self.op_buttons_bg_rect = pygame.Rect(start_x - 16, op_buttons_y, total_w + 32, btn_h)
        pygame.draw.rect(self.surface, (255, 255, 255, 30), self.op_buttons_bg_rect, border_radius=20)
        pygame.draw.rect(self.surface, (255, 255, 255, 60), self.op_buttons_bg_rect, 2, border_radius=20)

        # 同步按钮坐标，避免与背景错位
        for i, b in enumerate(self.op_buttons):
            b.rect.x = start_x + i * (btn_w + gap)
            b.rect.y = op_buttons_y
        
        # 绘制操作按钮（动画风格）
        for i, b in enumerate(self.op_buttons):
            # 动画参数
            pulse = 1.0 + 0.08 * math.sin(self.anim_tick * 0.15 + i)
            angle = 8 * math.sin(self.anim_tick * 0.12 + i)  # 轻微旋转
            # 判断按钮是否可用（选中三张及以上且为+或*）
            can_multi = len(self.selected) >= 3 and b.text in ('+', '*')
            # 高亮时使用金色渐变和更强发光
            if can_multi:
                grad_btn = pygame.Surface((b.rect.width, b.rect.height), pygame.SRCALPHA)
                for y in range(b.rect.height):
                    blend = y / b.rect.height
                    c1 = (255, 215, 0)
                    c2 = (255, 193, 7)
                    c = tuple(int(c1[j] * (1 - blend) + c2[j] * blend) for j in range(3))
                    pygame.draw.line(grad_btn, c, (0, y), (b.rect.width, y))
                grad_btn = pygame.transform.smoothscale(grad_btn, (int(b.rect.width * pulse), int(b.rect.height * pulse)))
                grad_rect = grad_btn.get_rect(center=b.rect.center)
                self.surface.blit(grad_btn, grad_rect)
                # 金色外发光
                glow = pygame.Surface((b.rect.width + 48, b.rect.height + 48), pygame.SRCALPHA)
                for r in range(24, 0, -1):
                    alpha = int(120 * (r/24)**2)
                    pygame.draw.ellipse(glow, (255, 215, 0, alpha), glow.get_rect().inflate(-r*2, -r*2))
                self.surface.blit(glow, (b.rect.centerx - glow.get_width() // 2, b.rect.centery - glow.get_height() // 2), special_flags=pygame.BLEND_RGBA_ADD)
                # 金色边框
                pygame.draw.rect(self.surface, (255, 215, 0), grad_rect, 5, border_radius=18)
            else:
                grad_btn = pygame.Surface((b.rect.width, b.rect.height), pygame.SRCALPHA)
                for y in range(b.rect.height):
                    blend = y / b.rect.height
                    c1 = (255, 193, 7)
                    c2 = (66, 165, 245)
                    c = tuple(int(c1[j] * (1 - blend) + c2[j] * blend) for j in range(3))
                    pygame.draw.line(grad_btn, c, (0, y), (b.rect.width, y))
                grad_btn = pygame.transform.smoothscale(grad_btn, (int(b.rect.width * pulse), int(b.rect.height * pulse)))
                grad_rect = grad_btn.get_rect(center=b.rect.center)
                self.surface.blit(grad_btn, grad_rect)
                # 普通外发光
                glow = pygame.Surface((b.rect.width + 28, b.rect.height + 28), pygame.SRCALPHA)
                pygame.draw.ellipse(glow, (255, 255, 255, 70), glow.get_rect())
                self.surface.blit(glow, (b.rect.centerx - glow.get_width() // 2, b.rect.centery - glow.get_height() // 2), special_flags=pygame.BLEND_RGBA_ADD)
                # 普通蓝色边框
                pygame.draw.rect(self.surface, (33, 150, 243), grad_rect, 4, border_radius=18)
            # 运算符符号动画
            op_font = pygame.font.Font(FONT_NAME, 44)
            op_text = op_font.render(b.text, True, (40, 40, 40))  # 深色符号
            op_text = pygame.transform.rotate(op_text, angle)
            op_rect = op_text.get_rect(center=b.rect.center)
            self.surface.blit(op_text, op_rect)
        # 复原、提示、换一组、返回按钮（渐变+阴影+圆角）
        btn_font = pygame.font.Font(FONT_NAME, 36)
        btn_y = int(win_rect.height * 0.85)
        btn_w, btn_h = 180, 64
        side_margin = int(win_rect.width * 0.06)
        space = (win_rect.width - side_margin*2 - btn_w*4) // 3
        btns = []
        x_cursor = win_rect.x + side_margin
        btns.append((x_cursor, btn_y, (66, 165, 245), '复原'))
        x_cursor += btn_w + space
        btns.append((x_cursor, btn_y, (76, 175, 80), '提示'))
        x_cursor += btn_w + space
        btns.append((x_cursor, btn_y, (255, 193, 7), '换一组'))
        x_cursor += btn_w + space
        btns.append((x_cursor, btn_y, (180, 180, 180), '返回'))
        btn_rects = []
        for x, y, color, label in btns:
            # 阴影
            shadow = pygame.Surface((btn_w+12, btn_h+12), pygame.SRCALPHA)
            pygame.draw.ellipse(shadow, (80,120,180,60), (6, btn_h//2, btn_w, btn_h//2))
            self.surface.blit(shadow, (x-6, y+btn_h//3))
            # 渐变按钮
            grad_btn = pygame.Surface((btn_w, btn_h), pygame.SRCALPHA)
            for yy in range(btn_h):
                blend = yy/btn_h
                c = tuple(int(color[i]*(1-blend)+255*blend) for i in range(3))
                pygame.draw.line(grad_btn, c, (0,yy), (btn_w,yy))
            pygame.draw.rect(grad_btn, (255,255,255,80), (0,0,btn_w,btn_h//2), border_radius=18)
            self.surface.blit(grad_btn, (x,y))
            pygame.draw.rect(self.surface, color, (x,y,btn_w,btn_h), 3, border_radius=18)
            text = btn_font.render(label, True, (255,255,255) if label!='返回' else (80,80,80))
            self.surface.blit(text, (x+38, y+10))
            btn_rects.append(pygame.Rect(x,y,btn_w,btn_h))
        self._undo_rect, self._hint_rect, self._new_rect, self._back_rect = btn_rects

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            # 选卡片
            for i, rect in enumerate(self._card_rects):
                if rect.collidepoint(event.pos):
                    if i in self.selected:
                        self.selected.remove(i)
                    elif len(self.selected) < len(self.cards):
                        self.selected.append(i)
                    return
            # 运算符
            # 新增：三张或四张牌时支持加法或乘法合成
            if len(self.selected) in (3, 4):
                selected_values = [self.cards[idx] for idx in self.selected]
                for b, op in zip(self.op_buttons, self.operators):
                    if b.rect.collidepoint(event.pos):
                        if op == '+':
                            val = sum(selected_values)
                        elif op == '*':
                            val = 1
                            for v in selected_values:
                                val *= v
                        else:
                            continue  # 只支持加法和乘法
                        self.history.append((self.cards[:], self.selected[:], self.result, self.msg, self.solved_count))
                        new_cards = [self.cards[j] for j in range(len(self.cards)) if j not in self.selected]
                        new_cards.append(val)
                        self.cards = new_cards
                        self.selected = []
                        self.result = val
                        # 若合并后只剩一张牌，进行终局判断
                        if len(self.cards) == 1:
                            if abs(val - 24) < 1e-6:
                                # 计分：基础100 + 剩余秒*5
                                secs_left = max(0, int(self.timer_duration - (pygame.time.get_ticks()-self.round_start_ticks)/1000))
                                points = 100 + secs_left * 5
                                self.score += points
                                self.msg = f'恭喜，算出24! +{points}分'
                                self.solved_count += 1
                                player_data.add_coins(100)
                                player_data._save_data()
                                self._auto_next_time = pygame.time.get_ticks() + 1000
                            else:
                                self.msg = '未能算出24'
                        else:
                            self.msg = ''
                        return
            # 新增：只剩两张牌时自动选中
            if len(self.cards) == 2:
                n1, n2 = self.cards[0], self.cards[1]
                for b, op in zip(self.op_buttons, self.operators):
                    if b.rect.collidepoint(event.pos):
                        try:
                            if op == '-':
                                a, b_ = max(n1, n2), min(n1, n2)
                                val = a - b_
                            elif op == '/':
                                a, b_ = max(n1, n2), min(n1, n2)
                                if b_ == 0:
                                    self.msg = '除数不能为0'
                                    return
                                if a % b_ != 0:
                                    self.msg = '不能整除'
                                    return
                                val = a // b_
                            elif op == '+':
                                val = n1 + n2
                            elif op == '*':
                                val = n1 * n2
                            # 判断是否为24
                            self.history.append((self.cards[:], self.selected[:], self.result, self.msg, self.solved_count))
                            self.cards = [val]
                            self.selected = []
                            self.result = val
                            self.msg = ''
                            if abs(val-24)<1e-6:
                                # 计分：基础100 + 剩余秒*5
                                secs_left = max(0, int(self.timer_duration - (pygame.time.get_ticks()-self.round_start_ticks)/1000))
                                points = 100 + secs_left * 5
                                self.score += points
                                self.msg = f'恭喜，算出24! +{points}分'
                                self.solved_count += 1
                                player_data.add_coins(100)
                                player_data._save_data()
                                self._auto_next_time = pygame.time.get_ticks() + 1000
                            else:
                                self.msg = '未能算出24'
                        except Exception:
                            self.msg = '计算错误'
                        return
            
            # 操作按钮：撤销/提示/换一组/返回
            if hasattr(self, '_undo_rect') and self._undo_rect.collidepoint(event.pos):
                if self.history:
                    self.cards, self.selected, self.result, self.msg, self.solved_count = self.history.pop()
                    self.hint_text = ''
                    self.hint_solutions = []
                    self.hint_index = 0
                    self.hint_cards_snapshot = None
                return
            elif hasattr(self, '_hint_rect') and self._hint_rect.collidepoint(event.pos):
                self._handle_hint_click()
                return
            elif hasattr(self, '_new_rect') and self._new_rect.collidepoint(event.pos):
                self.generate_cards()
                self.hint_text = ''
                self.hint_solutions = []
                self.hint_index = 0
                self.hint_cards_snapshot = None
                return
            elif hasattr(self, '_back_rect') and self._back_rect.collidepoint(event.pos):
                self.parent.page = 'main'
                return
            # 原有：选中两张牌时
            if len(self.selected) == 2:
                idx1, idx2 = self.selected
                n1, n2 = self.cards[idx1], self.cards[idx2]
                for b, op in zip(self.op_buttons, self.operators):
                    if b.rect.collidepoint(event.pos):
                        try:
                            # 减法自动大减小
                            if op == '-':
                                a, b_ = max(n1, n2), min(n1, n2)
                                val = a - b_
                            # 除法自动大除以小，且必须整除
                            elif op == '/':
                                a, b_ = max(n1, n2), min(n1, n2)
                                if b_ == 0:
                                    self.msg = '除数不能为0'
                                    return
                                if a % b_ != 0:
                                    self.msg = '不能整除'
                                    return
                                val = a // b_
                            # 其他运算
                            elif op == '+':
                                val = n1 + n2
                            elif op == '*':
                                val = n1 * n2
                            # 保存历史
                            self.history.append((self.cards[:], self.selected[:], self.result, self.msg, self.solved_count))
                            # 合成新卡片
                            new_cards = [self.cards[i] for i in range(len(self.cards)) if i not in self.selected]
                            new_cards.append(val)
                            self.cards = new_cards
                            self.selected = []
                            self.result = val
                            self.msg = ''
                            # 判断是否结束
                            if len(self.cards) == 1:
                                if abs(self.cards[0]-24)<1e-6:
                                    # 计分：基础100 + 剩余秒*5
                                    secs_left = max(0, int(self.timer_duration - (pygame.time.get_ticks()-self.round_start_ticks)/1000))
                                    points = 100 + secs_left * 5
                                    self.score += points
                                    self.msg = f'恭喜，算出24! +{points}分'
                                    self.solved_count += 1
                                    player_data.add_coins(100)
                                    player_data._save_data()
                                    self._auto_next_time = pygame.time.get_ticks() + 1000
                                else:
                                    self.msg = '未能算出24'
                        except Exception:
                            self.msg = '计算错误'
                        return