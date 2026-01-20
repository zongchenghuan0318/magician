import pygame
import random
import time
import datetime
import math
import os
from .constants import *
from .player import player_data

class WhackAMolePage:
    def __init__(self, surface, parent):
        self.surface = surface
        self.parent = parent
        self.panel_x = parent.panel_x
        self.panel_y = parent.panel_y
        self.panel_w = parent.panel_w
        self.panel_h = parent.panel_h
        self.audio_manager = parent.audio_manager  # 从父级获取音频管理器
        self.state = 'ready'  # ready, running, finished
        self.active = True
        self.start_time = 0
        self.duration = 30  # 游戏时长增加到30秒
        self.score = 0
        self.miss = 0
        self.combo = 0
        self.max_combo = 0
        self.holes = self.generate_holes()
        self.moles = []  # 支持多个地鼠同时出现
        self.mole_radius = 45
        self.mole_show_time = 1.5  # 初始地鼠存活时间
        self.next_mole_time = 0
        self.reward = 0
        self._back_btn_rect = None
        self._start_btn_rect = None
        
        # 锤子特效相关
        self.hammer_down = False
        self.hammer_time = 0
        self.hammer_pos = (0, 0)
        
        # 游戏难度设置
        self.limit_per_day = 5  # 每日次数增加到5次
        self._today = datetime.date.today().isoformat()
        self._load_play_count()
        
        # 动画与特效系统
        self.mole_animations = {}  # 地鼠动画状态
        self.score_fly = []  # 分数飘字动画
        self.hit_effects = []  # 打击特效
        self.combo_effects = []  # 连击特效
        
        # 加载图片资源
        self.load_images()
        
        # 音效设置
        self.sound_enabled = True
        
    def load_images(self):
        # 尝试加载地鼠图片资源
        self.mole_images = {}
        image_dir = os.path.join(os.path.dirname(__file__), '..', 'snake_images')
        
        # 定义地鼠类型和对应的图片
        mole_types = ['normal', 'golden', 'bomb', 'fast']
        
        for mole_type in mole_types:
            # 尝试加载对应图片，如果不存在则使用默认绘制
            image_path = os.path.join(image_dir, f'mole_{mole_type}.png')
            if os.path.exists(image_path):
                try:
                    img = pygame.image.load(image_path).convert_alpha()
                    self.mole_images[mole_type] = pygame.transform.scale(img, (90, 90))
                except:
                    self.mole_images[mole_type] = None
            else:
                self.mole_images[mole_type] = None
        
        # 加载锤子图片
        hammer_path = os.path.join(image_dir, 'hammer.png')
        if os.path.exists(hammer_path):
            try:
                self.hammer_img = pygame.image.load(hammer_path).convert_alpha()
                self.hammer_img = pygame.transform.scale(self.hammer_img, (80, 80))
            except:
                self.hammer_img = None
        else:
            self.hammer_img = None

    def _load_play_count(self):
        data = player_data.data
        if data.get('whack_a_mole_date') != self._today:
            data['whack_a_mole_date'] = self._today
            data['whack_a_mole_count'] = 0
            player_data._save_data()
        self.play_count = data.get('whack_a_mole_count', 0)

    def _inc_play_count(self):
        player_data.data['whack_a_mole_count'] = player_data.data.get('whack_a_mole_count', 0) + 1
        player_data.data['whack_a_mole_date'] = self._today
        player_data._save_data()
        self.play_count = player_data.data['whack_a_mole_count']

    def reset_play_count(self):
        player_data.data['whack_a_mole_count'] = 0
        player_data.data['whack_a_mole_date'] = self._today
        player_data._save_data()
        self.play_count = 0

    def generate_holes(self):
        # 更美观的布局：圆形排列，12个洞位
        holes = []
        center_x = self.panel_x + self.panel_w // 2
        center_y = self.panel_y + self.panel_h // 2 - 20  # 向上偏移，为UI留空间
        radius = min(self.panel_w, self.panel_h) // 3
        
        # 外圈8个洞位
        for i in range(8):
            angle = i * (360 / 8)
            rad = math.radians(angle)
            x = center_x + radius * math.cos(rad)
            y = center_y + radius * math.sin(rad)
            holes.append((int(x), int(y)))
        
        # 内圈4个洞位
        for i in range(4):
            angle = i * (360 / 4) + 45  # 偏移45度
            rad = math.radians(angle)
            x = center_x + radius * 0.6 * math.cos(rad)
            y = center_y + radius * 0.6 * math.sin(rad)
            holes.append((int(x), int(y)))
        
        return holes

    def start_game(self):
        self._load_play_count()
        if self.play_count >= self.limit_per_day:
            return  # 不允许再玩
        self.state = 'running'
        self.start_time = time.time()
        self.score = 0
        self.miss = 0
        self.combo = 0
        self.max_combo = 0
        self.next_mole_time = 0
        self.moles = []
        self.mole_animations = {}
        self.score_fly = []
        self.hit_effects = []
        self.combo_effects = []
        self.reward = 0
        
        # 播放游戏开始音效
        if self.sound_enabled and self.audio_manager:
            self.audio_manager.play_sound('game_start')
        
        # 初始生成2个地鼠
        self.spawn_new_mole()
        self.spawn_new_mole()

    def spawn_new_mole(self):
        # 智能选择地鼠出现位置，避免连续出现在同一位置
        available_holes = list(range(len(self.holes)))
        
        # 移除已经有地鼠的洞位
        for mole in self.moles:
            if mole[0] in available_holes:
                available_holes.remove(mole[0])
        
        if not available_holes:
            return  # 没有可用洞位
        
        # 随机选择洞位
        idx = random.choice(available_holes)
        
        # 随机选择地鼠类型
        mole_type = self.get_random_mole_type()
        
        # 创建地鼠
        mole = (idx, time.time(), True, mole_type)
        self.moles.append(mole)
        
        # 初始化动画状态
        self.mole_animations[idx] = {
            'scale': 0.5,
            'bounce': 1.2,
            'face': 'normal',
            'rotation': 0,
            'pulse': 0
        }
        
        # 动态调整难度
        self.adjust_difficulty()
        
        # 播放地鼠出现音效
        if self.sound_enabled and self.audio_manager:
            self.audio_manager.play_sound('mole_appear')
    
    def get_random_mole_type(self):
        # 根据地鼠类型设置概率
        weights = {
            'normal': 70,    # 普通地鼠：70%
            'golden': 15,    # 黄金地鼠：15%
            'fast': 10,      # 快速地鼠：10%
            'bomb': 5        # 炸弹地鼠：5%
        }
        
        # 随着分数增加，特殊地鼠概率增加
        if self.score > 20:
            weights['golden'] += 5
            weights['fast'] += 3
            weights['bomb'] += 2
            weights['normal'] -= 10
        
        # 随机选择类型
        types = list(weights.keys())
        probabilities = [weights[t] for t in types]
        return random.choices(types, weights=probabilities)[0]
    
    def adjust_difficulty(self):
        # 根据分数动态调整游戏难度
        base_time = 1.5
        score_factor = self.score / 15
        
        # 使用更平滑的难度曲线
        speedup = 0.8 * (1 - 1 / (1 + 0.1 * score_factor))
        self.mole_show_time = max(0.8, base_time - speedup)
        
        # 随着分数增加，同时出现的地鼠数量增加
        if self.score > 30 and len(self.moles) < 3:
            self.spawn_new_mole()
        elif self.score > 50 and len(self.moles) < 4:
            self.spawn_new_mole()

    def update_moles(self, now):
        # 更新所有地鼠的状态
        moles_to_remove = []
        
        for i, mole in enumerate(self.moles):
            idx, appear_time, is_alive, mole_type = mole
            elapsed = now - appear_time
            
            # 更新动画状态
            if idx in self.mole_animations:
                anim = self.mole_animations[idx]
                
                # 出现动画
                if elapsed < 0.3:
                    anim['scale'] = 0.3 + (1.0 - 0.3) * (elapsed / 0.3)
                # 预警动画（即将消失）
                elif elapsed > self.mole_show_time - 0.4:
                    warning_progress = (elapsed - (self.mole_show_time - 0.4)) / 0.4
                    if warning_progress < 1:
                        # 闪烁效果
                        anim['face'] = 'normal' if random.random() > warning_progress * 0.8 else 'sad'
                        anim['pulse'] = math.sin(warning_progress * 15) * 0.1
                
                # 特殊地鼠的动画效果
                if mole_type == 'golden':
                    anim['rotation'] = (anim['rotation'] + 2) % 360
                elif mole_type == 'fast':
                    anim['scale'] = 0.9 + 0.1 * math.sin(now * 10)
            
            # 地鼠消失
            if elapsed > self.mole_show_time:
                if is_alive:  # 地鼠未被击中
                    self.miss += 1
                    self.combo = 0
                    
                    # 添加错过特效
                    pos = self.holes[idx]
                    self.add_miss_effect(pos)
                    
                    # 播放错过音效
                    if self.sound_enabled and self.audio_manager:
                        self.audio_manager.play_sound('mole_miss')
                
                moles_to_remove.append(i)
        
        # 移除消失的地鼠
        for i in sorted(moles_to_remove, reverse=True):
            idx = self.moles[i][0]
            if idx in self.mole_animations:
                del self.mole_animations[idx]
            del self.moles[i]
        
        # 生成新的地鼠
        if len(self.moles) < 2 or (now - self.start_time) > self.next_mole_time:
            self.spawn_new_mole()
            self.next_mole_time = now + random.uniform(0.5, 1.5)
    
    def add_miss_effect(self, pos):
        # 添加错过特效
        self.hit_effects.append({
            'type': 'miss',
            'pos': pos,
            'start_time': time.time(),
            'scale': 1.0
        })

    def end_game(self):
        self.state = 'finished'
        
        # 计算奖励（根据不同类型的地鼠给予不同奖励）
        self.reward = self.score * 40  # 提高奖励系数
        
        # 连击奖励
        if self.max_combo >= 5:
            self.reward += self.max_combo * 10
        
        player_data.add_coins(self.reward)
        player_data._save_data()
        self._inc_play_count()
        
        # 播放游戏结束音效
        if self.sound_enabled and self.audio_manager:
            self.audio_manager.play_sound('game_over')
    
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = pygame.mouse.get_pos()
            
            # 检查按钮点击
            if self._back_btn_rect and self._back_btn_rect.collidepoint(pos):
                self.active = False
                return True
            
            if self.state == 'ready':
                if self._start_btn_rect and self._start_btn_rect.collidepoint(pos):
                    self.start_game()
                    return True
            elif self.state == 'running':
                # 锤子打击效果
                self.hammer_down = True
                self.hammer_time = time.time()
                self.hammer_pos = pos
                
                # 检查是否击中地鼠
                self.check_hit_mole(pos)
                return True
            elif self.state == 'finished':
                if self._start_btn_rect and self._start_btn_rect.collidepoint(pos):
                    self.start_game()
                    return True
        
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.state == 'running':
                self.hammer_down = False
        
        return False
    
    def check_hit_mole(self, pos):
        now = time.time()
        
        for i, mole in enumerate(self.moles):
            idx, appear_time, is_alive, mole_type = mole
            if not is_alive:
                continue
                
            hole_pos = self.holes[idx]
            distance = math.sqrt((pos[0] - hole_pos[0])**2 + (pos[1] - hole_pos[1])**2)
            
            # 检查是否击中
            if distance < self.mole_radius:
                # 击中地鼠
                self.hit_mole(i, mole_type, hole_pos)
                break
    
    def hit_mole(self, mole_index, mole_type, pos):
        # 移除被击中的地鼠
        mole = self.moles[mole_index]
        idx = mole[0]
        
        # 更新地鼠状态为已击中
        self.moles[mole_index] = (idx, mole[1], False, mole_type)
        
        # 根据地鼠类型计算分数
        score_value = self.calculate_score(mole_type)
        self.score += score_value
        
        # 连击计数
        self.combo += 1
        if self.combo > self.max_combo:
            self.max_combo = self.combo
        
        # 添加打击特效
        self.add_hit_effect(pos, mole_type)
        
        # 添加分数飘字
        self.score_fly.append({
            'x': pos[0] - 20,
            'y': pos[1],
            'value': score_value,
            'start': time.time()
        })
        
        # 播放音效
        if self.sound_enabled and self.audio_manager:
            self.play_hit_sound(mole_type)
        
        # 移除动画状态
        if idx in self.mole_animations:
            del self.mole_animations[idx]
    
    def calculate_score(self, mole_type):
        # 根据地鼠类型计算分数
        base_scores = {
            'normal': 10,
            'golden': 30,
            'fast': 15,
            'bomb': -20  # 炸弹地鼠扣分
        }
        
        base_score = base_scores.get(mole_type, 10)
        
        # 连击加成
        combo_bonus = min(10, self.combo)  # 最大连击加成为10倍
        
        return base_score * (1 + combo_bonus * 0.1)
    
    def add_hit_effect(self, pos, mole_type):
        # 添加打击特效
        effect_type = 'hit'
        if mole_type == 'bomb':
            effect_type = 'explosion'
        
        self.hit_effects.append({
            'type': effect_type,
            'pos': pos,
            'start_time': time.time(),
            'mole_type': mole_type
        })
    
    def play_hit_sound(self, mole_type):
        # 播放不同地鼠的打击音效
        if mole_type == 'golden':
            self.audio_manager.play_sound('golden_hit')
        elif mole_type == 'bomb':
            self.audio_manager.play_sound('bomb_explosion')
        else:
            self.audio_manager.play_sound('mole_hit')
    
    def draw_hammer(self):
        if self.hammer_down and time.time() - self.hammer_time < 0.2:
            # 绘制锤子
            x, y = self.hammer_pos
            
            if self.hammer_img:
                # 使用图片绘制锤子
                hammer_rect = self.hammer_img.get_rect(center=(x, y))
                # 添加旋转效果
                rotated_hammer = pygame.transform.rotate(self.hammer_img, -30)
                rotated_rect = rotated_hammer.get_rect(center=(x, y))
                self.surface.blit(rotated_hammer, rotated_rect)
            else:
                # 绘制简单的锤子图形
                pygame.draw.rect(self.surface, (150, 75, 0), 
                                (x-25, y-5, 50, 10))
                pygame.draw.circle(self.surface, (200, 100, 0), (x, y), 15)

    def draw(self):
        self._load_play_count()  # 每次绘制都刷新日期和次数
        
        # 1. 更精美的渐变背景
        self.draw_beautiful_background()
        
        # 2. 游戏主面板
        self.draw_main_panel()
        
        # 3. 状态区分
        if self.state == 'ready':
            self.draw_ready()
        elif self.state == 'running':
            self.draw_running()
        elif self.state == 'finished':
            self.draw_finished()
        
        # 4. 锤子特效
        self.draw_hammer()
        
        # 5. 特效绘制
        self.draw_effects()
    
    def draw_beautiful_background(self):
        # 创建渐变背景
        grad = pygame.Surface((self.panel_w, self.panel_h), pygame.SRCALPHA)
        
        # 更柔和的渐变颜色
        for y in range(self.panel_h):
            # 从浅蓝色到浅紫色的渐变
            progress = y / self.panel_h
            r = int(100 + 80 * progress)
            g = int(180 + 40 * progress)
            b = int(255 - 30 * progress)
            pygame.draw.line(grad, (r, g, b, 255), (0, y), (self.panel_w, y))
        
        # 添加装饰性元素
        # 气泡效果
        for _ in range(25):
            bx = random.randint(20, self.panel_w-20)
            by = random.randint(20, self.panel_h-20)
            br = random.randint(5, 25)
            alpha = random.randint(30, 80)
            pygame.draw.circle(grad, (255, 255, 255, alpha), (bx, by), br)
            # 气泡高光
            if br > 10:
                pygame.draw.circle(grad, (255, 255, 255, alpha+50), 
                                 (bx - br//3, by - br//3), br//3)
        
        # 星光效果
        for _ in range(15):
            sx = random.randint(10, self.panel_w-10)
            sy = random.randint(10, self.panel_h-10)
            size = random.randint(2, 4)
            pygame.draw.circle(grad, (255, 255, 255, 200), (sx, sy), size)
        
        self.surface.blit(grad, (self.panel_x, self.panel_y))
    
    def draw_main_panel(self):
        # 面板阴影
        panel_rect = pygame.Rect(self.panel_x, self.panel_y, self.panel_w, self.panel_h)
        shadow_rect = panel_rect.move(8, 12)
        pygame.draw.rect(self.surface, (60, 80, 120, 120), shadow_rect, border_radius=40)
        
        # 主面板
        pygame.draw.rect(self.surface, (255, 255, 255, 250), panel_rect, border_radius=40)
        
        # 边框装饰
        pygame.draw.rect(self.surface, (66, 165, 245), panel_rect, 8, border_radius=40)
        
        # 内发光效果
        inner_rect = panel_rect.inflate(-20, -20)
        pygame.draw.rect(self.surface, (255, 255, 255, 100), inner_rect, 4, border_radius=30)
        
        # 精美标题
        self.draw_title()
    
    def draw_title(self):
        font = pygame.font.Font(FONT_NAME, 56)
        text = "打地鼠大冒险"
        cx = self.panel_x + self.panel_w // 2
        cy = self.panel_y + 75
        
        # 多重阴影效果
        for dx, dy, alpha in [(4, 4, 100), (2, 2, 150), (-2, -2, 80)]:
            shadow = font.render(text, True, (0, 0, 0, alpha))
            shadow_rect = shadow.get_rect(center=(cx + dx, cy + dy))
            self.surface.blit(shadow, shadow_rect)
        
        # 渐变文字效果
        title_surf = font.render(text, True, (66, 165, 245))
        title_rect = title_surf.get_rect(center=(cx, cy))
        self.surface.blit(title_surf, title_rect)
        
        # 装饰性图标
        self.draw_title_decorations(cx, cy, title_rect)
    
    def draw_title_decorations(self, cx, cy, title_rect):
        # 锤子图标
        hammer_x = title_rect.right + 45
        hammer_y = cy - 5
        
        if self.hammer_img:
            # 使用图片
            hammer_rect = self.hammer_img.get_rect(center=(hammer_x, hammer_y))
            self.surface.blit(self.hammer_img, hammer_rect)
        else:
            # 绘制锤子
            pygame.draw.rect(self.surface, (255, 213, 79), 
                           (hammer_x-10, hammer_y+8, 20, 40), border_radius=8)
            pygame.draw.ellipse(self.surface, (255, 99, 132), 
                              (hammer_x-25, hammer_y-25, 50, 35))
            pygame.draw.ellipse(self.surface, (255, 255, 255, 180), 
                              (hammer_x-10, hammer_y-15, 20, 12))
        
        # 地鼠图标
        mole_x = title_rect.left - 45
        mole_y = cy - 5
        
        # 绘制可爱地鼠
        pygame.draw.circle(self.surface, (200, 150, 100), (mole_x, mole_y), 20)
        pygame.draw.circle(self.surface, (0, 0, 0), (mole_x-8, mole_y-5), 6)  # 左眼
        pygame.draw.circle(self.surface, (0, 0, 0), (mole_x+8, mole_y-5), 6)  # 右眼
        pygame.draw.ellipse(self.surface, (255, 0, 0), (mole_x-4, mole_y+5, 8, 5))  # 鼻子

    def draw_ready(self):
        font = pygame.font.Font(FONT_NAME, 28)
        tip = font.render("点击开始，限时打地鼠，得金币奖励！", True, (80,80,80))
        tip_rect = tip.get_rect(center=(self.panel_x+self.panel_w//2, self.panel_y+140))
        self.surface.blit(tip, tip_rect)
        # 次数提示
        count_tip = f"今日剩余次数：{max(0, self.limit_per_day - self.play_count)} / {self.limit_per_day}"
        count_font = pygame.font.Font(FONT_NAME, 24)
        count_text = count_font.render(count_tip, True, (255,140,0))
        count_rect = count_text.get_rect(center=(self.panel_x+self.panel_w//2, self.panel_y+180))
        self.surface.blit(count_text, count_rect)
        # 按钮
        btn_rect = pygame.Rect(self.panel_x+self.panel_w//2-80, self.panel_y+self.panel_h//2-30, 160, 60)
        if self.play_count >= self.limit_per_day:
            pygame.draw.rect(self.surface, (180,180,180), btn_rect, border_radius=16)
            btn_font = pygame.font.Font(FONT_NAME, 30)
            btn_font.set_bold(True)
            btn_text = btn_font.render("今日已达上限", True, (220,80,80))
        else:
            pygame.draw.rect(self.surface, (66, 165, 245), btn_rect, border_radius=16)
            btn_font = pygame.font.Font(FONT_NAME, 30)
            btn_font.set_bold(True)
            btn_text = btn_font.render("开始游戏", True, (255,255,255))
        btn_text_rect = btn_text.get_rect(center=btn_rect.center)
        self.surface.blit(btn_text, btn_text_rect)
        self._start_btn_rect = btn_rect
        # 返回按钮
        back_rect = pygame.Rect(self.panel_x+30, self.panel_y+self.panel_h-70, 120, 44)
        pygame.draw.rect(self.surface, (66, 165, 245), back_rect, border_radius=12)
        back_font = pygame.font.Font(FONT_NAME, 24)
        back_font.set_bold(True)
        back_text = back_font.render("返回", True, (255,255,255))
        back_text_rect = back_text.get_rect(center=back_rect.center)
        self.surface.blit(back_text, back_text_rect)
        self._back_btn_rect = back_rect

    def draw_running(self):
        now = time.time()
        left = max(0, int(self.duration - (now - self.start_time)))
        
        # 更新地鼠状态
        self.update_moles(now)
        
        # 1. 绘制游戏信息面板
        self.draw_game_info(now, left)
        
        # 2. 绘制洞位
        self.draw_holes()
        
        # 3. 绘制地鼠
        self.draw_moles(now)
        
        # 4. 检查游戏结束
        if left <= 0:
            self.end_game()
        
        # 5. 返回按钮
        self.draw_back_button()
    
    def draw_game_info(self, now, left):
        # 计时器
        self.draw_timer(left)
        
        # 分数显示
        self.draw_score()
        
        # Miss计数
        self.draw_miss_count()
        
        # Combo显示
        self.draw_combo_display(now)
        
        # 分数飘字动画
        self.draw_score_fly_animation(now)
    
    def draw_timer(self, left):
        timer_x = self.panel_x + 120
        timer_y = self.panel_y + 60
        
        # 计时器背景
        pygame.draw.rect(self.surface, (240, 248, 255), 
                        (timer_x-50, timer_y-35, 100, 70), border_radius=20)
        pygame.draw.rect(self.surface, (66, 165, 245), 
                        (timer_x-50, timer_y-35, 100, 70), 4, border_radius=20)
        
        # 计时器数字
        font = pygame.font.Font(FONT_NAME, 38)
        timer_text = font.render(str(left), True, (66, 165, 245))
        timer_rect = timer_text.get_rect(center=(timer_x, timer_y))
        self.surface.blit(timer_text, timer_rect)
        
        # 计时器标签
        label_font = pygame.font.Font(FONT_NAME, 18)
        label = label_font.render("剩余时间", True, (100, 100, 100))
        label_rect = label.get_rect(center=(timer_x, timer_y+30))
        self.surface.blit(label, label_rect)
    
    def draw_score(self):
        score_x = self.panel_x + self.panel_w - 150
        score_y = self.panel_y + 60
        
        # 分数背景
        pygame.draw.rect(self.surface, (255, 240, 220), 
                        (score_x-60, score_y-35, 120, 70), border_radius=20)
        pygame.draw.rect(self.surface, (255, 140, 0), 
                        (score_x-60, score_y-35, 120, 70), 4, border_radius=20)
        
        # 分数文本
        font = pygame.font.Font(FONT_NAME, 38)
        score_text = font.render(str(self.score), True, (255, 140, 0))
        score_rect = score_text.get_rect(center=(score_x, score_y))
        self.surface.blit(score_text, score_rect)
        
        # 分数标签
        label_font = pygame.font.Font(FONT_NAME, 18)
        label = label_font.render("得分", True, (150, 100, 0))
        label_rect = label.get_rect(center=(score_x, score_y+30))
        self.surface.blit(label, label_rect)
    
    def draw_miss_count(self):
        miss_x = self.panel_x + self.panel_w - 150
        miss_y = self.panel_y + 150
        
        # Miss背景
        pygame.draw.rect(self.surface, (255, 230, 230), 
                        (miss_x-60, miss_y-25, 120, 50), border_radius=15)
        pygame.draw.rect(self.surface, (255, 99, 132), 
                        (miss_x-60, miss_y-25, 120, 50), 3, border_radius=15)
        
        # Miss文本
        font = pygame.font.Font(FONT_NAME, 28)
        miss_text = f"Miss: {self.miss}"
        miss_surf = font.render(miss_text, True, (255, 99, 132))
        miss_rect = miss_surf.get_rect(center=(miss_x, miss_y))
        self.surface.blit(miss_surf, miss_rect)
    
    def draw_combo_display(self, now):
        if self.combo >= 2:
            combo_x = self.panel_x + self.panel_w - 150
            combo_y = self.panel_y + 210
            
            # Combo动画效果
            scale = 1.0
            if hasattr(self, '_last_combo') and self.combo > self._last_combo:
                self._combo_anim_time = time.time()
            if hasattr(self, '_combo_anim_time') and time.time() - self._combo_anim_time < 0.2:
                scale = 1.15
            self._last_combo = self.combo
            
            # Combo背景
            pygame.draw.rect(self.surface, (255, 255, 200, 180), 
                            (combo_x-80, combo_y-25, 160, 50), border_radius=20)
            pygame.draw.rect(self.surface, (255, 213, 79), 
                            (combo_x-80, combo_y-25, 160, 50), 3, border_radius=20)
            
            # Combo文本
            font = pygame.font.Font(FONT_NAME, 32)
            combo_text = f"Combo! {self.combo}"
            combo_surf = font.render(combo_text, True, (255, 140, 0))
            combo_surf = pygame.transform.rotozoom(combo_surf, 0, scale)
            combo_rect = combo_surf.get_rect(center=(combo_x, combo_y))
            self.surface.blit(combo_surf, combo_rect)
    
    def draw_score_fly_animation(self, now):
        for fly in self.score_fly[:]:
            elapsed = now - fly['start']
            if elapsed > 0.8:
                self.score_fly.remove(fly)
                continue
            alpha = max(0, 255 - int(elapsed * 320))
            font = pygame.font.Font(FONT_NAME, 32)
            surf = font.render(f"+{fly['value']}", True, (255, 213, 79))
            surf.set_alpha(alpha)
            self.surface.blit(surf, (fly['x'], fly['y'] - elapsed * 60))
    
    def draw_holes(self):
        for hx, hy in self.holes:
            # 洞位阴影
            pygame.draw.ellipse(self.surface, (80, 60, 40), 
                              (hx-52, hy+20, 104, 36))
            # 洞位主体
            pygame.draw.ellipse(self.surface, (120, 90, 60), 
                              (hx-50, hy+18, 100, 32))
            # 洞位内阴影
            pygame.draw.ellipse(self.surface, (80, 60, 40, 120), 
                              (hx-48, hy+24, 96, 24))
    def draw_moles(self, now):
        for mole in self.moles:
            idx, appear_time, is_alive, mole_type = mole
            if is_alive and idx in self.mole_animations:
                pos = self.holes[idx]
                anim = self.mole_animations[idx]
                self.draw_mole_with_animation(pos, mole_type, anim)
    
    def draw_mole_with_animation(self, pos, mole_type, anim):
        x, y = pos
        scale = anim['scale'] + anim['pulse']
        rotation = anim['rotation']
        
        # 绘制地鼠阴影
        shadow_size = int(self.mole_radius * scale * 0.8)
        pygame.draw.circle(self.surface, (0, 0, 0, 80), 
                          (x, y + shadow_size//2), shadow_size//3)
        
        # 尝试使用图片绘制地鼠
        if mole_type in self.mole_images and self.mole_images[mole_type]:
            # 使用图片绘制
            img = self.mole_images[mole_type]
            scaled_size = int(self.mole_radius * 2 * scale)
            scaled_img = pygame.transform.scale(img, (scaled_size, scaled_size))
            
            if rotation != 0:
                scaled_img = pygame.transform.rotate(scaled_img, rotation)
            
            img_rect = scaled_img.get_rect(center=(x, y))
            self.surface.blit(scaled_img, img_rect)
        else:
            # 使用代码绘制地鼠
            self.draw_cute_mole(pos, self.mole_radius, scale, anim['face'])
        
        # 特殊地鼠的标识
        if mole_type == 'golden':
            # 黄金地鼠的光环
            for i in range(3):
                radius = int(self.mole_radius * scale * 1.2 + i * 5)
                pygame.draw.circle(self.surface, (255, 215, 0, 100 - i*30), 
                                  (x, y), radius, 2)
        elif mole_type == 'bomb':
            # 炸弹地鼠的危险标识
            danger_size = int(self.mole_radius * scale * 0.6)
            pygame.draw.polygon(self.surface, (255, 0, 0), 
                               [(x, y - danger_size), (x + danger_size, y), 
                                (x, y + danger_size), (x - danger_size, y)])
    
    def draw_back_button(self):
        back_rect = pygame.Rect(self.panel_x + 40, self.panel_y + self.panel_h - 80, 100, 50)
        
        # 按钮阴影
        shadow_rect = back_rect.move(3, 3)
        pygame.draw.rect(self.surface, (60, 100, 180, 120), shadow_rect, border_radius=12)
        
        # 按钮主体
        pygame.draw.rect(self.surface, (66, 165, 245), back_rect, border_radius=12)
        
        # 按钮文字
        back_font = pygame.font.Font(FONT_NAME, 24)
        back_font.set_bold(True)
        back_text = back_font.render("返回", True, (255, 255, 255))
        back_text_rect = back_text.get_rect(center=back_rect.center)
        self.surface.blit(back_text, back_text_rect)
        
        self._back_btn_rect = back_rect
    
    def draw_effects(self):
        now = time.time()
        effects_to_remove = []
        
        for i, effect in enumerate(self.hit_effects):
            elapsed = now - effect['start_time']
            if elapsed > 0.6:
                effects_to_remove.append(i)
                continue
            
            pos = effect['pos']
            x, y = pos
            
            if effect['type'] == 'hit':
                # 打击特效
                radius = int(20 + elapsed * 40)
                alpha = max(0, 255 - int(elapsed * 400))
                pygame.draw.circle(self.surface, (255, 255, 0, alpha), (x, y), radius, 3)
            elif effect['type'] == 'miss':
                # 错过特效
                size = int(15 + elapsed * 20)
                alpha = max(0, 200 - int(elapsed * 300))
                pygame.draw.circle(self.surface, (255, 0, 0, alpha), (x, y), size, 2)
        
        # 移除过期特效
        for i in sorted(effects_to_remove, reverse=True):
            del self.hit_effects[i]

    def draw_finished(self):
        font = pygame.font.Font(FONT_NAME, 36)
        over = font.render("游戏结束！", True, (66, 165, 245))
        over_rect = over.get_rect(center=(self.panel_x+self.panel_w//2, self.panel_y+140))
        self.surface.blit(over, over_rect)
        reward_font = pygame.font.Font(FONT_NAME, 30)
        reward_font.set_bold(True)
        reward_text = reward_font.render(f"奖励：{self.reward} 金币", True, (255,140,0))
        reward_rect = reward_text.get_rect(center=(self.panel_x+self.panel_w//2, self.panel_y+200))
        self.surface.blit(reward_text, reward_rect)
        btn_rect = pygame.Rect(self.panel_x+self.panel_w//2-80, self.panel_y+self.panel_h//2-30, 160, 60)
        pygame.draw.rect(self.surface, (66, 165, 245), btn_rect, border_radius=16)
        btn_font = pygame.font.Font(FONT_NAME, 30)
        btn_font.set_bold(True)
        btn_text = btn_font.render("再玩一次", True, (255,255,255))
        btn_text_rect = btn_text.get_rect(center=btn_rect.center)
        self.surface.blit(btn_text, btn_text_rect)
        self._start_btn_rect = btn_rect
        # 返回按钮
        back_rect = pygame.Rect(self.panel_x+30, self.panel_y+self.panel_h-70, 120, 44)
        pygame.draw.rect(self.surface, (66, 165, 245), back_rect, border_radius=12)
        back_font = pygame.font.Font(FONT_NAME, 24)
        back_font.set_bold(True)
        back_text = back_font.render("返回", True, (255,255,255))
        back_text_rect = back_text.get_rect(center=back_rect.center)
        self.surface.blit(back_text, back_text_rect)
        self._back_btn_rect = back_rect

    def draw_cute_mole(self, pos, radius, scale=1.0, face='normal'):
        x, y = pos
        # 缩放动画
        r = radius * scale
        # 柔和阴影（更大更柔和）
        shadow_surf = pygame.Surface((int(r*2.2), int(r*0.9)), pygame.SRCALPHA)
        for i in range(15):
            alpha = 100 - i * 6
            pygame.draw.ellipse(shadow_surf, (160,160,160,alpha), (i, i, r*2.2-i*2, r*0.9-i*2))
        shadow_rect = shadow_surf.get_rect(center=(x, y+r*0.85))
        self.surface.blit(shadow_surf, shadow_rect)
        
        # 身体渐变（更圆润的形状）
        body_r = int(r*0.65)
        body_surf = pygame.Surface((body_r*2, body_r*1.5), pygame.SRCALPHA)
        for i in range(body_r*2):
            progress = i/(body_r*2)
            color = (
                int(200 + progress*30),  # 更亮的颜色
                int(150 + progress*40),
                int(100 + progress*50),
                255
            )
            pygame.draw.line(body_surf, color, (i,0), (i,body_r*1.5))
        body_rect = body_surf.get_rect(center=(x, y+r*0.55))
        self.surface.blit(body_surf, body_rect)
        
        # 头部渐变（更大更圆）
        head_r = int(r*0.8)
        head_surf = pygame.Surface((head_r*2, head_r*2), pygame.SRCALPHA)
        for i in range(head_r*2):
            progress = i/(head_r*2)
            color = (
                int(200 + progress*40),  # 更亮的颜色
                int(150 + progress*50),
                int(100 + progress*60),
                255
            )
            pygame.draw.line(head_surf, color, (i,0), (i,head_r*2))
        head_rect = head_surf.get_rect(center=(x, y))
        self.surface.blit(head_surf, head_rect)
        
        # 耳朵（更大更可爱）
        ear_r = int(head_r*0.35)
        ear_surf = pygame.Surface((ear_r*2, ear_r*2), pygame.SRCALPHA)
        for i in range(ear_r*2):
            progress = i/(ear_r*2)
            color = (
                int(200 + progress*30),
                int(150 + progress*40),
                int(100 + progress*50),
                255
            )
            pygame.draw.line(ear_surf, color, (i,0), (i,ear_r*2))
        # 左耳（稍微倾斜）
        left_ear = pygame.transform.rotate(ear_surf, -15)
        left_ear_rect = left_ear.get_rect(center=(int(x-head_r*0.75), int(y-head_r*0.65)))
        self.surface.blit(left_ear, left_ear_rect)
        # 右耳（稍微倾斜）
        right_ear = pygame.transform.rotate(ear_surf, 15)
        right_ear_rect = right_ear.get_rect(center=(int(x+head_r*0.75), int(y-head_r*0.65)))
        self.surface.blit(right_ear, right_ear_rect)
        
        # 鼻子（更大更可爱）
        nose_w, nose_h = 24, 18
        nose_surf = pygame.Surface((nose_w, nose_h), pygame.SRCALPHA)
        for i in range(nose_w):
            progress = i/nose_w
            color = (
                255,
                int(100 + progress*60),
                int(50 + progress*60),
                255
            )
            pygame.draw.line(nose_surf, color, (i,0), (i,nose_h))
        nose_rect = nose_surf.get_rect(center=(x, y+head_r//3+8))
        self.surface.blit(nose_surf, nose_rect)
        # 鼻子高光（更明显）
        pygame.draw.ellipse(self.surface, (255,255,255,200), (x-6, y+head_r//3+4, 12, 7))
        
        # 眼睛（更大更生动）
        eye_r = int(head_r*0.22)
        if face == 'normal':
            # 眼白
            pygame.draw.circle(self.surface, (255,255,255), (int(x-head_r*0.35), int(y-8)), eye_r)
            pygame.draw.circle(self.surface, (255,255,255), (int(x+head_r*0.35), int(y-8)), eye_r)
            # 眼球（更大）
            pygame.draw.circle(self.surface, (0,0,0), (int(x-head_r*0.35), int(y-8)), eye_r*0.75)
            pygame.draw.circle(self.surface, (0,0,0), (int(x+head_r*0.35), int(y-8)), eye_r*0.75)
            # 高光（更亮）
            pygame.draw.circle(self.surface, (255,255,255), (int(x-head_r*0.35)-3, int(y-10)), int(eye_r*0.35))
            pygame.draw.circle(self.surface, (255,255,255), (int(x+head_r*0.35)-3, int(y-10)), int(eye_r*0.35))
        elif face == 'happy':
            # 眯眼（更可爱）
            pygame.draw.ellipse(self.surface, (0,0,0), (int(x-head_r*0.45), int(y-10), eye_r*1.4, eye_r*0.5))
            pygame.draw.ellipse(self.surface, (0,0,0), (int(x+head_r*0.25), int(y-10), eye_r*1.4, eye_r*0.5))
        elif face == 'sad':
            # 难过的眼睛（更夸张）
            pygame.draw.arc(self.surface, (0,0,0), (int(x-head_r*0.45), int(y-10), eye_r*2.2, eye_r*1.4), 3.14, 6.28, 4)
            pygame.draw.arc(self.surface, (0,0,0), (int(x+head_r*0.25), int(y-10), eye_r*2.2, eye_r*1.4), 3.14, 6.28, 4)
        
        # 腮红（更大更可爱）
        cheek_w, cheek_h = int(head_r*0.32), int(head_r*0.16)
        cheek_surf = pygame.Surface((cheek_w, cheek_h), pygame.SRCALPHA)
        for i in range(cheek_w):
            progress = i/cheek_w
            alpha = int(180 - progress*80)
            color = (255, 150, 150, alpha)  # 更粉嫩的颜色
            pygame.draw.line(cheek_surf, color, (i,0), (i,cheek_h))
        # 左腮
        left_cheek_rect = cheek_surf.get_rect(center=(x-head_r*0.45, y+head_r*0.2))
        self.surface.blit(cheek_surf, left_cheek_rect)
        # 右腮
        right_cheek_rect = cheek_surf.get_rect(center=(x+head_r*0.45, y+head_r*0.2))
        self.surface.blit(cheek_surf, right_cheek_rect)
        
        # 嘴巴（更可爱的表情）
        if face == 'happy':
            # 开心的大笑（更圆润）
            pygame.draw.arc(self.surface, (255,100,50), (x-20, y+head_r//3+6, 40, 20), 3.8, 6.0, 5)
            pygame.draw.arc(self.surface, (255,200,180), (x-15, y+head_r//3+8, 30, 15), 3.8, 6.0, 3)
        elif face == 'sad':
            # 难过的表情（更夸张）
            pygame.draw.arc(self.surface, (255,100,50), (x-20, y+head_r//3+16, 40, 20), 3.14, 4.2, 4)
        else:
            # 普通表情（更可爱）
            pygame.draw.arc(self.surface, (255,100,50), (x-20, y+head_r//3+8, 40, 20), 3.4, 6.0, 4)
            pygame.draw.arc(self.surface, (255,200,180), (x-15, y+head_r//3+10, 30, 15), 3.4, 6.0, 3)

    def draw_hammer(self):
        mx, my = pygame.mouse.get_pos()
        # 更精致的卡通锤子
        hammer_w, hammer_h = 54, 80
        offset_y = 0
        scale = 1.0
        if self.hammer_down and time.time() - self.hammer_time < 0.13:
            offset_y = 18 + random.randint(-4,4)
            scale = 0.92 + random.uniform(-0.03,0.03)
        else:
            self.hammer_down = False
        # 锤把渐变
        for i in range(14):
            color = (
                int(180 - i*4),
                int(120 - i*2),
                int(60 + i*6)
            )
            pygame.draw.rect(self.surface, color, (mx-7, my-10+offset_y+i*4, 14, 4), border_radius=3)
        # 锤把装饰圈
        pygame.draw.rect(self.surface, (255, 215, 0), (mx-7, my-10+offset_y+int(hammer_h*0.5), 14, 7), border_radius=3)
        # 锤头主色渐变
        for i in range(int(hammer_h*0.32)):
            ratio = i/(hammer_h*0.32)
            color = (
                int(255 - 60*ratio),
                int(180 + 40*ratio),
                int(120 + 80*ratio)
            )
            pygame.draw.ellipse(
                self.surface, color,
                (mx-hammer_w//2, my-38+offset_y+i, int(hammer_w*scale), int(hammer_h*0.32*scale)-i)
            )
        # 锤头高光
        pygame.draw.ellipse(self.surface, (255,255,255,120), (mx-hammer_w//2+8, my-38+offset_y+6, int(hammer_w*0.5*scale), int(hammer_h*0.10*scale)))
        # 锤头阴影
        pygame.draw.ellipse(self.surface, (120,120,120,90), (mx-hammer_w//2, my-38+offset_y+int(hammer_h*0.18*scale), int(hammer_w*scale), int(hammer_h*0.13*scale)))
        # 锤头轮廓
        pygame.draw.ellipse(self.surface, (80,80,80), (mx-hammer_w//2, my-38+offset_y, int(hammer_w*scale), int(hammer_h*0.32*scale)), 2)
        # 锤把轮廓
        pygame.draw.rect(self.surface, (80,80,80), (mx-7, my-10+offset_y, 14, int(hammer_h*0.7*scale)), 2, border_radius=6)
        # 锤把底部圆头
        pygame.draw.ellipse(self.surface, (120,80,40), (mx-11, my-10+offset_y+int(hammer_h*0.7*scale)-6, 22, 14))
        pygame.draw.ellipse(self.surface, (80,80,80), (mx-11, my-10+offset_y+int(hammer_h*0.7*scale)-6, 22, 14), 2)
