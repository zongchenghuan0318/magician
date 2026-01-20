# -*- coding: utf-8 -*-
import pygame
import os
import tkinter as tk
from tkinter import filedialog
import win32api
import win32con
import random
from .snake import Snake
from .food import Food
from .game_board import GameBoard
from .menu import Menu, PauseMenu, SettingsMenu, GameOverMenuSingle, HelpMenu, MusicSelectionMenu
from .shop import ShopMenu
from .backpack import BackpackMenu
from .player import player_data
from .constants import *
from .audio_manager import AudioManager
from .image_skins import image_skin_manager
from .activity_page import ActivityPage
# 成就系统已移除
# from .achievements import AchievementSystem

class GameController:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("贪吃蛇")
        self.clock = pygame.time.Clock()
        
        # 初始化音频管理器
        self.audio_manager = AudioManager()
        
        # 加载音效
        self.load_sounds()
        
        # 强制设置英文输入法
        self.set_english_input_method()
        
        self.menu = Menu(self.screen)
        self.pause_menu = PauseMenu(self.screen)
        self.settings_menu = SettingsMenu(self.screen)
        self.game_over_menu = GameOverMenuSingle(self.screen)
        self.shop_menu = ShopMenu(self.screen, self)
        self.backpack_menu = BackpackMenu(self.screen, self)
        self.help_menu = HelpMenu(self.screen)
        self.activity_page = ActivityPage(self.screen, self.audio_manager)
        self.music_selection_menu = MusicSelectionMenu(self.screen, self.audio_manager, self)
        
        # 成就系统已移除
        # self.achievement_system = AchievementSystem(self.screen)
        
        self.reset_game(play_music=False)  # 初始化时不播放音乐
        
        # 音频状态标志
        self.in_game = False
        self.menu_music_playing = False
        
        # 游戏统计数据
        self.game_stats = {
            "games_played": 0,
            "highest_score": 0,
            "total_apples": 0,
            "special_food": 0,
            "wall_deaths": 0,
            "self_deaths": 0,
            "max_speed_reached": False
        }

    def set_english_input_method(self):
        # 获取前景窗口句柄
        try:
            import win32gui
            hwnd = win32gui.GetForegroundWindow()
            # 设置英文输入法
            win32api.SendMessage(hwnd, win32con.WM_IME_CONTROL, 0x0001, 0)
        except ImportError:
            pass  # print("win32api模块未安装，无法设置英文输入法")
        except Exception as e:
            pass  # print(f"设置英文输入法失败: {e}")

    def reset_game(self, play_music=True):
        """重置游戏状态"""
        self.snake = Snake()
        self.foods = []
        self.game_board = GameBoard()
        self.game_over = False
        self.is_paused = False
        self.game_over_sound_played = False
        
        # 生成初始食物
        self.spawn_food()
        
        # 播放音乐
        if play_music:
            self.start_game_music()

    def get_current_skin_audio_config(self):
        """获取当前装备皮肤的音频配置"""
        current_skin = player_data.get_equipped_skin()
        return image_skin_manager.get_skin_audio_config(current_skin)

    def start_game_music(self):
        """开始播放游戏音乐"""
        # 标记为在游戏中
        self.in_game = True
        
        # 先停止当前播放的音乐
        self.stop_game_music()
        
        # 获取当前装备皮肤的音频配置
        audio_config = self.get_current_skin_audio_config()
        
        if not audio_config:
            return
        
        background_music = audio_config.get("background_music")
        if background_music:
            if os.path.exists(background_music):
                self.audio_manager.music_enabled = True
                if self.audio_manager.play_music(background_music, loop=True):
                    return
                else:
                    pass
            else:
                pass
        else:
            pass

    def stop_game_music(self):
        """停止游戏音乐，如果不在游戏中则恢复菜单音乐"""
        self.audio_manager.stop_music()
        
        # 如果不在游戏中，恢复菜单音乐
        if not self.in_game:
            self.play_menu_music()

    def pause_game_music(self):
        """暂停游戏音乐"""
        self.audio_manager.pause_music()

    def resume_game_music(self):
        """恢复游戏音乐"""
        self.audio_manager.unpause_music()

    def spawn_food(self):
        score = self.snake.score

        # 根据分数定义不同等级食物的生成概率
        if score < 15:
            # 游戏早期: 高概率普通食物
            levels = [1, 2]
            weights = [0.9, 0.1]  # 90% 等级1, 10% 等级2
        elif score < 50:
            # 游戏中期: 增加高级食物概率
            levels = [1, 2, 3]
            weights = [0.6, 0.3, 0.1]  # 60% 等级1, 30% 等级2, 10% 等级3
        else:
            # 游戏后期: 更高概率的高级食物
            levels = [1, 2, 3]
            weights = [0.4, 0.4, 0.2]  # 40% 等级1, 40% 等级2, 20% 等级3

        # 根据权重随机选择一个食物等级
        level = random.choices(levels, weights=weights, k=1)[0]
            
        new_food = Food(level=level)
        all_positions = self.snake.positions + [f.position for f in self.foods]
        new_food.randomize_position(all_positions, self.game_board.obstacles)
        self.foods.append(new_food)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "exit"
                
            if self.game_over:
                result = self.game_over_menu.handle_event(event)
                if result == "restart":
                        self.reset_game()
                elif result == "main_menu":
                    self.stop_game_music()  # 停止游戏音乐
                    return "menu"
                continue
                
            if self.is_paused:
                result = self.pause_menu.handle_event(event)
                if result == "continue":
                    self.is_paused = False
                    self.resume_game_music()  # 恢复游戏音乐
                elif result == "main_menu":
                    self.stop_game_music()  # 停止游戏音乐
                    return "menu"
                continue
                
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.is_paused = True
                    self.pause_game_music()  # 暂停游戏音乐
                elif event.key == pygame.K_SPACE:
                    self.is_paused = not self.is_paused
                    if self.is_paused:
                        self.pause_game_music()  # 暂停游戏音乐
                    else:
                        self.resume_game_music()  # 恢复游戏音乐
                    
                if not self.is_paused:
                    if event.key in [pygame.K_UP, pygame.K_w]:
                        self.snake.change_direction((0, -1))
                    elif event.key in [pygame.K_DOWN, pygame.K_s]:
                        self.snake.change_direction((0, 1))
                    elif event.key in [pygame.K_LEFT, pygame.K_a]:
                        self.snake.change_direction((-1, 0))
                    elif event.key in [pygame.K_RIGHT, pygame.K_d]:
                        self.snake.change_direction((1, 0))

        return "continue"

    def update(self):
        if self.game_over or self.is_paused:
            return
            
        current_time = pygame.time.get_ticks()
        
        # 更新游戏元素
        if not self.snake.update(current_time):
            self.game_over = True
            # 更新游戏统计数据 - 自身碰撞死亡
            self.game_stats["self_deaths"] += 1
            # 立即停止背景音乐
            self.stop_game_music()
            # 播放游戏结束音效
            if not self.game_over_sound_played:
                self.play_game_over_sound()
                self.game_over_sound_played = True
            # 成就系统已移除
            # self.achievement_system.check_achievement(self.game_stats)
            return
            
        for food in self.foods:
            food.update(current_time)
            
        self.game_board.update(current_time) # 更新障碍物动画
            
        # 检查是否吃到食物
        head_pos = self.snake.get_head_position()
        for food in self.foods[:]:
            if head_pos == food.position:
                self.snake.grow(food.score)
                player_data.add_coins(food.score)
                # 更新游戏统计数据
                self.game_stats["total_apples"] += 1
                if food.level > 1:
                    self.game_stats["special_food"] += 1
                self.foods.remove(food)
                self.spawn_food()
            
        if self.game_board.check_collision(self.snake.get_head_position()):
            self.game_over = True
            # 更新游戏统计数据 - 墙壁碰撞死亡
            self.game_stats["wall_deaths"] += 1
            # 立即停止背景音乐
            self.stop_game_music()
            # 播放游戏结束音效
            if not self.game_over_sound_played:
                self.play_game_over_sound()
                self.game_over_sound_played = True
            # 检查成就
            # 成就系统已移除
            # self.achievement_system.check_achievements(self.game_stats)

    def draw(self):
        # 1. 绘制背景
        self.screen.fill(BACKGROUND_COLOR)
        
        # 2. 绘制游戏面板（网格和障碍物）
        self.game_board.draw(self.screen)
        
        for food in self.foods:
            food.draw(self.screen)
        
        # 4. 绘制蛇（在食物上方）
        self.snake.draw(self.screen)
        
        # 5. 绘制分数面板（半透明，在游戏元素上方）
        self.draw_score_panel()
        
        # 6. 绘制暂停菜单（最顶层）
        if self.is_paused:
            self.draw_pause_menu()
            
        # 7. 绘制游戏结束画面（最顶层）
        if self.game_over:
            self.draw_game_over_screen()
        
        
    def draw_score_panel(self):
        # 创建分数面板
        score_panel = pygame.Surface((200, 60), pygame.SRCALPHA)
        score_panel.fill((0, 0, 0, 30))  # 极高透明度的黑色背景
        # 更淡的渐变边框
        border_color = (255, 255, 255, 10)
        pygame.draw.rect(score_panel, border_color, score_panel.get_rect(), 2, border_radius=10)
        # 绘制分数
        if not hasattr(self, '_score_font'):
            self._score_font = pygame.font.Font(FONT_NAME, SCORE_FONT_SIZE)
        font = self._score_font
        score_text = font.render(f"分数: {self.snake.score}", True, WHITE)
        score_rect = score_text.get_rect(center=(100, 30))
        score_panel.blit(score_text, score_rect)
        # 绘制分数面板
        self.screen.blit(score_panel, (10, 10))
        
    def draw_pause_menu(self):
        self.pause_menu.draw()
        
    def draw_game_over_screen(self):
        self.game_over_menu.draw(self.snake.score)

    def run(self):
        """运行游戏主循环"""
        last_english_check = pygame.time.get_ticks()
        english_check_interval = 1000  # 每秒检查一次英文输入法
        
        while True:
            current_time = pygame.time.get_ticks()
            
            # 定期检查并强制设置英文输入法
            if current_time - last_english_check > english_check_interval:
                self.set_english_input_method()
                last_english_check = current_time
            
            result = self.handle_events()
            if result == "exit":
                return "exit"
            elif result == "menu":
                return "menu"
            elif result == "continue":
                # 继续游戏循环
                pass
                
            self.update()
            self.draw()
            
            pygame.display.flip()
            self.clock.tick(FPS)

    def play_menu_music(self):
        """播放菜单音乐，如果音乐未播放则启动"""
        try:
            if not self.audio_manager.is_music_playing() and not self.in_game:
                # 获取用户选择的背景音乐
                music_path = self.music_selection_menu.get_current_music_path()
                self.audio_manager.play_music(music_path, loop=True)
                self.menu_music_playing = True
        except Exception as e:
            pass  # print(f"主菜单音乐播放失败: {e}")
    
    def update_menu_music(self):
        """更新菜单音乐为用户选择的音乐"""
        if not self.in_game:
            self.stop_menu_music()
            self.play_menu_music()

    def stop_menu_music(self):
        """停止菜单音乐"""
        try:
            self.audio_manager.stop_music()
            self.menu_music_playing = False
        except Exception as e:
            pass  # print(f"主菜单音乐停止失败: {e}")

    def run_menu(self):
        """运行主菜单"""
        last_english_check = pygame.time.get_ticks()
        english_check_interval = 1000  # 每秒检查一次英文输入法
        
        # 标记不在游戏中并播放菜单音乐
        self.in_game = False
        self.play_menu_music()
        
        while True:
            current_time = pygame.time.get_ticks()
            # 定期检查并强制设置英文输入法
            if current_time - last_english_check > english_check_interval:
                self.set_english_input_method()
                last_english_check = current_time
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.stop_menu_music()
                    return "exit"
                result = self.menu.handle_event(event)
                if result is not None:
                    # 只有进入游戏时才停止菜单音乐
                    if result == "start_game":
                        # 更新游戏统计数据
                        self.game_stats["games_played"] += 1
                        # 成就系统已移除
        # self.achievement_system.unlock_achievement("first_game")
                        self.stop_menu_music()
                    elif result == "achievements":
                        return self.run_achievements()
                    return result
            self.menu.draw()
            # 成就系统已移除
            # self.achievement_system.update()
            # self.achievement_system.draw_notification()
            pygame.display.flip()
            self.clock.tick(FPS)
            
    def run_achievements(self):
        """成就页面已移除"""
        # return self.achievement_system.run_achievements_page()
        return "menu"  # 直接返回菜单

    def run_settings(self):
        running = True
        # 确保菜单音乐在设置页面播放
        self.play_menu_music()
        while running:
            # --- Event Handling ---
            event_list = pygame.event.get()
            for event in event_list:
                if event.type == pygame.QUIT:
                    # To prevent the main loop from exiting, we should handle this gracefully
                    # or have a clear exit strategy. For now, just return.
                    return
                    
                result = self.settings_menu.handle_event(event)
                if result == "add_background":
                    self.add_background()
                elif result == "background_music":
                    self.run_music_selection()
                elif result == "volume_settings":
                    self.run_volume_settings()
                elif result == "help":
                    self.run_help(from_settings=True)
                elif result == "back":
                    return

            # --- Drawing ---
            # 1. Draw the main menu in the background to keep its animations
            self.menu.draw()

            # 2. Draw the settings panel and its buttons
            self.settings_menu.draw()
            
            # 3. Draw the animated snake on top of everything
            self.settings_menu.draw_animated_snake()
            
            # 4. Update the display
            pygame.display.flip()
            self.clock.tick(FPS)
    
    def run_music_selection(self):
        """运行背景音乐选择菜单"""
        running = True
        # 确保菜单音乐在音乐选择页面播放
        self.play_menu_music()
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return
                result = self.music_selection_menu.handle_event(event)
                if result == "back":
                    return
            
            # 绘制背景（设置菜单）
            self.settings_menu.draw()
            
            # 绘制音乐选择界面
            self.music_selection_menu.draw()
            
            pygame.display.flip()
            self.clock.tick(FPS)
    
    def run_volume_settings(self):
        """运行音量设置菜单"""
        running = True
        self.play_menu_music()
        
        # 创建音量设置界面
        font = pygame.font.Font(FONT_NAME, 26)
        title_font = pygame.font.Font(FONT_NAME, 36)
        music_volume = self.audio_manager.get_music_volume()
        sound_volume = self.audio_manager.get_sound_volume()
        
        # 音量条参数 - 更宽更美观
        bar_width = 350
        bar_height = 30
        bar_x = WINDOW_WIDTH//2 - bar_width//2
        
        # 滑块参数
        slider_radius = 18
        music_slider_dragging = False
        sound_slider_dragging = False
        
        # 按钮参数
        button_width = 50
        button_height = 50
        button_margin = 20
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return
                    elif event.key == pygame.K_UP:
                        music_volume = min(1.0, music_volume + 0.05)
                        self.audio_manager.set_music_volume(music_volume)
                    elif event.key == pygame.K_DOWN:
                        music_volume = max(0.0, music_volume - 0.05)
                        self.audio_manager.set_music_volume(music_volume)
                    elif event.key == pygame.K_RIGHT:
                        sound_volume = min(1.0, sound_volume + 0.05)
                        self.audio_manager.set_sound_volume(sound_volume)
                    elif event.key == pygame.K_LEFT:
                        sound_volume = max(0.0, sound_volume - 0.05)
                        self.audio_manager.set_sound_volume(sound_volume)
                
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # 左键点击
                        mouse_x, mouse_y = event.pos
                        
                        # 计算音量条位置
                        panel_rect = pygame.Rect(WINDOW_WIDTH//2 - 350, WINDOW_HEIGHT//2 - 250, 700, 500)
                        music_y = panel_rect.y + 150
                        music_bar_y = music_y + 50
                        sound_y = music_y + 160
                        sound_bar_y = sound_y + 50
                        
                        # 音乐音量滑块区域
                        music_slider_x = bar_x + int(bar_width * music_volume)
                        music_slider_rect = pygame.Rect(music_slider_x - slider_radius, music_bar_y - slider_radius + bar_height//2, 
                                                      slider_radius*2, slider_radius*2)
                        if music_slider_rect.collidepoint(mouse_x, mouse_y):
                            music_slider_dragging = True
                        
                        # 音效音量滑块区域
                        sound_slider_x = bar_x + int(bar_width * sound_volume)
                        sound_slider_rect = pygame.Rect(sound_slider_x - slider_radius, sound_bar_y - slider_radius + bar_height//2, 
                                                      slider_radius*2, slider_radius*2)
                        if sound_slider_rect.collidepoint(mouse_x, mouse_y):
                            sound_slider_dragging = True
                        
                        # 音乐音量条点击区域
                        music_bar_rect = pygame.Rect(bar_x, music_bar_y, bar_width, bar_height)
                        if music_bar_rect.collidepoint(mouse_x, mouse_y) and not music_slider_dragging:
                            # 计算点击位置对应的音量值
                            relative_x = mouse_x - bar_x
                            music_volume = max(0.0, min(1.0, relative_x / bar_width))
                            self.audio_manager.set_music_volume(music_volume)
                        
                        # 音效音量条点击区域
                        sound_bar_rect = pygame.Rect(bar_x, sound_bar_y, bar_width, bar_height)
                        if sound_bar_rect.collidepoint(mouse_x, mouse_y) and not sound_slider_dragging:
                            # 计算点击位置对应的音量值
                            relative_x = mouse_x - bar_x
                            sound_volume = max(0.0, min(1.0, relative_x / bar_width))
                            self.audio_manager.set_sound_volume(sound_volume)
                        
                        # 音乐音量快捷按钮
                        music_minus_rect = pygame.Rect(bar_x - button_width - button_margin, music_bar_y - (button_height - bar_height)//2, 
                                                     button_width, button_height)
                        if music_minus_rect.collidepoint(mouse_x, mouse_y):
                            music_volume = max(0.0, music_volume - 0.1)
                            self.audio_manager.set_music_volume(music_volume)
                        
                        music_plus_rect = pygame.Rect(bar_x + bar_width + button_margin, music_bar_y - (button_height - bar_height)//2, 
                                                    button_width, button_height)
                        if music_plus_rect.collidepoint(mouse_x, mouse_y):
                            music_volume = min(1.0, music_volume + 0.1)
                            self.audio_manager.set_music_volume(music_volume)
                        
                        # 音效音量快捷按钮
                        sound_minus_rect = pygame.Rect(bar_x - button_width - button_margin, sound_bar_y - (button_height - bar_height)//2, 
                                                     button_width, button_height)
                        if sound_minus_rect.collidepoint(mouse_x, mouse_y):
                            sound_volume = max(0.0, sound_volume - 0.1)
                            self.audio_manager.set_sound_volume(sound_volume)
                        
                        sound_plus_rect = pygame.Rect(bar_x + bar_width + button_margin, sound_bar_y - (button_height - bar_height)//2, 
                                                    button_width, button_height)
                        if sound_plus_rect.collidepoint(mouse_x, mouse_y):
                            sound_volume = min(1.0, sound_volume + 0.1)
                            self.audio_manager.set_sound_volume(sound_volume)
                
                elif event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:  # 左键释放
                        music_slider_dragging = False
                        sound_slider_dragging = False
                
                elif event.type == pygame.MOUSEMOTION:
                    if music_slider_dragging:
                        mouse_x, mouse_y = event.pos
                        relative_x = mouse_x - bar_x
                        music_volume = max(0.0, min(1.0, relative_x / bar_width))
                        self.audio_manager.set_music_volume(music_volume)
                    
                    if sound_slider_dragging:
                        mouse_x, mouse_y = event.pos
                        relative_x = mouse_x - bar_x
                        sound_volume = max(0.0, min(1.0, relative_x / bar_width))
                        self.audio_manager.set_sound_volume(sound_volume)
            
            # 绘制背景
            self.settings_menu.draw()
            
            # 绘制音量设置界面 - 美化背景设计
            overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            self.screen.blit(overlay, (0, 0))
            
            # 绘制设置面板 - 采用现代化玻璃态设计
            panel_rect = pygame.Rect(WINDOW_WIDTH//2 - 350, WINDOW_HEIGHT//2 - 250, 700, 500)
            
            # 多层阴影效果
            for i in range(4):
                shadow_offset = 5 + i * 2
                shadow_alpha = 35 - i * 8
                shadow_surface = pygame.Surface((700, 500), pygame.SRCALPHA)
                pygame.draw.rect(shadow_surface, (0, 0, 0, shadow_alpha), 
                               (0, 0, 700, 500), border_radius=30)
                self.screen.blit(shadow_surface, (panel_rect.x + shadow_offset, panel_rect.y + shadow_offset))
            
            # 玻璃态面板背景 - 渐变效果
            glass_surface = pygame.Surface((700, 500), pygame.SRCALPHA)
            for y in range(500):
                ratio = y / 500
                # 从深紫到浅蓝的渐变，更加精美
                r = int(240 + (255 - 240) * ratio)
                g = int(245 + (255 - 245) * ratio) 
                b = int(255)
                alpha = int(220 + (255 - 220) * (1 - ratio * 0.3))
                
                line_surface = pygame.Surface((700, 1), pygame.SRCALPHA)
                line_surface.fill((r, g, b, alpha))
                glass_surface.blit(line_surface, (0, y))
            
            self.screen.blit(glass_surface, panel_rect)
            
            # 多层边框效果
            pygame.draw.rect(self.screen, (200, 220, 255, 180), panel_rect, 3, border_radius=30)
            pygame.draw.rect(self.screen, (255, 255, 255, 120), panel_rect, 1, border_radius=30)
            
            # 发光效果
            import time
            import math
            glow_pulse = time.time() * 2
            glow_intensity = math.sin(glow_pulse) * 0.3 + 0.7
            for i in range(3):
                glow_alpha = int(80 * glow_intensity / (i + 1))
                glow_rect = pygame.Rect(panel_rect.x - i * 2, panel_rect.y - i * 2, 
                                      panel_rect.width + i * 4, panel_rect.height + i * 4)
                pygame.draw.rect(self.screen, (156, 39, 176, glow_alpha), glow_rect, 2, border_radius=30)
            
            # 标题 - 更大更醒目
            title_shadow = title_font.render("🔊 音量设置", True, (0, 0, 0, 100))
            title_shadow_rect = title_shadow.get_rect(center=(WINDOW_WIDTH//2 + 2, panel_rect.y + 70 + 2))
            self.screen.blit(title_shadow, title_shadow_rect)
            
            title = title_font.render("🔊 音量设置", True, (66, 165, 245))
            title_rect = title.get_rect(center=(WINDOW_WIDTH//2, panel_rect.y + 70))
            self.screen.blit(title, title_rect)
            
            # 装饰线
            line_y = panel_rect.y + 110
            line_width = 400
            line_x = (WINDOW_WIDTH - line_width) // 2
            
            # 渐变线条
            for i in range(line_width):
                progress = i / line_width
                # 从紫色渐变到蓝色
                r = int(156 + (66 - 156) * progress)
                g = int(39 + (165 - 39) * progress)
                b = int(176 + (245 - 176) * progress)
                alpha = int(200 * (1 - abs(2*progress - 1)))  # 中间最亮
                
                line_surface = pygame.Surface((1, 3), pygame.SRCALPHA)
                line_surface.fill((r, g, b, alpha))
                self.screen.blit(line_surface, (line_x + i, line_y))
            
            # 音乐音量区域 - 增加间距
            music_y = panel_rect.y + 150
            music_label = font.render("🎵 背景音乐音量", True, (80, 80, 100))
            music_label_rect = music_label.get_rect(center=(WINDOW_WIDTH//2, music_y))
            self.screen.blit(music_label, music_label_rect)
            
            # 音乐音量条 - 增加间距和美化
            music_bar_y = music_y + 50
            
            # 绘制音乐音量快捷按钮
            music_minus_rect = pygame.Rect(bar_x - button_width - button_margin, music_bar_y - (button_height - bar_height)//2, 
                                         button_width, button_height)
            pygame.draw.rect(self.screen, (240, 240, 250), music_minus_rect, border_radius=25)
            pygame.draw.rect(self.screen, (156, 39, 176), music_minus_rect, 2, border_radius=25)
            minus_font = pygame.font.Font(FONT_NAME, 30)
            minus_text = minus_font.render("-", True, (156, 39, 176))
            minus_rect = minus_text.get_rect(center=music_minus_rect.center)
            self.screen.blit(minus_text, minus_rect)
            
            music_plus_rect = pygame.Rect(bar_x + bar_width + button_margin, music_bar_y - (button_height - bar_height)//2, 
                                        button_width, button_height)
            pygame.draw.rect(self.screen, (240, 240, 250), music_plus_rect, border_radius=25)
            pygame.draw.rect(self.screen, (156, 39, 176), music_plus_rect, 2, border_radius=25)
            plus_text = minus_font.render("+", True, (156, 39, 176))
            plus_rect = plus_text.get_rect(center=music_plus_rect.center)
            self.screen.blit(plus_text, plus_rect)
            
            # 背景条 - 更美观的凹槽效果
            pygame.draw.rect(self.screen, (220, 220, 230), (bar_x, music_bar_y, bar_width, bar_height), border_radius=15)
            pygame.draw.rect(self.screen, (200, 200, 210), (bar_x, music_bar_y, bar_width, bar_height), 1, border_radius=15)
            
            # 进度条 - 渐变效果
            progress_width = int(bar_width * music_volume)
            if progress_width > 0:
                progress_surface = pygame.Surface((progress_width, bar_height), pygame.SRCALPHA)
                for x in range(progress_width):
                    ratio = x / bar_width
                    r = int(66 + (156 - 66) * ratio)
                    g = int(165 + (39 - 165) * ratio)
                    b = int(245 + (176 - 245) * ratio)
                    pygame.draw.line(progress_surface, (r, g, b), (x, 0), (x, bar_height), 1)
                
                # 圆角蒙版
                mask = pygame.Surface((progress_width, bar_height), pygame.SRCALPHA)
                pygame.draw.rect(mask, (255, 255, 255), (0, 0, progress_width, bar_height), border_radius=15)
                progress_surface.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                
                self.screen.blit(progress_surface, (bar_x, music_bar_y))
            
            # 滑块 - 更现代的设计
            music_slider_x = bar_x + progress_width
            # 滑块阴影
            pygame.draw.circle(self.screen, (0, 0, 0, 50), (music_slider_x, music_bar_y + bar_height//2 + 2), slider_radius)
            # 滑块本体
            pygame.draw.circle(self.screen, (255, 255, 255), (music_slider_x, music_bar_y + bar_height//2), slider_radius)
            pygame.draw.circle(self.screen, (156, 39, 176), (music_slider_x, music_bar_y + bar_height//2), slider_radius, 2)
            
            # 音乐音量值 - 调整位置，增加间距
            music_value = font.render(f"{int(music_volume * 100)}%", True, (156, 39, 176))
            music_value_rect = music_value.get_rect(center=(WINDOW_WIDTH//2, music_bar_y + 60))
            self.screen.blit(music_value, music_value_rect)
            
            # 音效音量区域 - 增加间距
            sound_y = music_y + 160
            sound_label = font.render("🔔 游戏音效音量", True, (80, 80, 100))
            sound_label_rect = sound_label.get_rect(center=(WINDOW_WIDTH//2, sound_y))
            self.screen.blit(sound_label, sound_label_rect)
            
            # 音效音量条 - 增加间距和美化
            sound_bar_y = sound_y + 50
            
            # 绘制音效音量快捷按钮
            sound_minus_rect = pygame.Rect(bar_x - button_width - button_margin, sound_bar_y - (button_height - bar_height)//2, 
                                         button_width, button_height)
            pygame.draw.rect(self.screen, (240, 240, 250), sound_minus_rect, border_radius=25)
            pygame.draw.rect(self.screen, (66, 165, 245), sound_minus_rect, 2, border_radius=25)
            self.screen.blit(minus_text, minus_text.get_rect(center=sound_minus_rect.center))
            
            sound_plus_rect = pygame.Rect(bar_x + bar_width + button_margin, sound_bar_y - (button_height - bar_height)//2, 
                                        button_width, button_height)
            pygame.draw.rect(self.screen, (240, 240, 250), sound_plus_rect, border_radius=25)
            pygame.draw.rect(self.screen, (66, 165, 245), sound_plus_rect, 2, border_radius=25)
            self.screen.blit(plus_text, plus_text.get_rect(center=sound_plus_rect.center))
            
            # 背景条 - 更美观的凹槽效果
            pygame.draw.rect(self.screen, (220, 220, 230), (bar_x, sound_bar_y, bar_width, bar_height), border_radius=15)
            pygame.draw.rect(self.screen, (200, 200, 210), (bar_x, sound_bar_y, bar_width, bar_height), 1, border_radius=15)
            
            # 进度条 - 渐变效果
            sound_progress_width = int(bar_width * sound_volume)
            if sound_progress_width > 0:
                sound_progress_surface = pygame.Surface((sound_progress_width, bar_height), pygame.SRCALPHA)
                for x in range(sound_progress_width):
                    ratio = x / bar_width
                    r = int(255 - (255 - 66) * ratio)
                    g = int(99 + (165 - 99) * ratio)
                    b = int(132 + (245 - 132) * ratio)
                    pygame.draw.line(sound_progress_surface, (r, g, b), (x, 0), (x, bar_height), 1)
                
                # 圆角蒙版
                sound_mask = pygame.Surface((sound_progress_width, bar_height), pygame.SRCALPHA)
                pygame.draw.rect(sound_mask, (255, 255, 255), (0, 0, sound_progress_width, bar_height), border_radius=15)
                sound_progress_surface.blit(sound_mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                
                self.screen.blit(sound_progress_surface, (bar_x, sound_bar_y))
            
            # 滑块 - 更现代的设计
            sound_slider_x = bar_x + sound_progress_width
            # 滑块阴影
            pygame.draw.circle(self.screen, (0, 0, 0, 50), (sound_slider_x, sound_bar_y + bar_height//2 + 2), slider_radius)
            # 滑块本体
            pygame.draw.circle(self.screen, (255, 255, 255), (sound_slider_x, sound_bar_y + bar_height//2), slider_radius)
            pygame.draw.circle(self.screen, (66, 165, 245), (sound_slider_x, sound_bar_y + bar_height//2), slider_radius, 2)
            
            # 音效音量值 - 调整位置，增加间距
            sound_value = font.render(f"{int(sound_volume * 100)}%", True, (66, 165, 245))
            sound_value_rect = sound_value.get_rect(center=(WINDOW_WIDTH//2, sound_bar_y + 60))
            self.screen.blit(sound_value, sound_value_rect)
            
            # 控制说明 - 优化提示位置和布局，增加间距
            help_y = panel_rect.bottom - 70
            
            # 创建提示背景 - 更美观的卡片式设计
            help_bg_rect = pygame.Rect(panel_rect.x + 50, help_y - 20, panel_rect.width - 100, 50)
            help_bg_surface = pygame.Surface((panel_rect.width - 100, 50), pygame.SRCALPHA)
            pygame.draw.rect(help_bg_surface, (255, 255, 255, 50), (0, 0, panel_rect.width - 100, 50), border_radius=15)
            self.screen.blit(help_bg_surface, help_bg_rect)
            
            # 分行显示操作提示，更清晰易读
            small_font = pygame.font.Font(FONT_NAME, 20)
            help_text = "🖱️ 拖动滑块或点击音量条调节  |  ⚙️ ↑↓←→微调  |  ❌ ESC返回"
            
            help_surface = small_font.render(help_text, True, (80, 80, 100))
            help_rect = help_surface.get_rect(center=(WINDOW_WIDTH//2, help_y))
            self.screen.blit(help_surface, help_rect)
            
            pygame.display.flip()
            self.clock.tick(FPS)

    def run_help(self, from_settings=False):
        running = True
        # 确保菜单音乐在帮助页面播放
        self.play_menu_music()
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.run_menu() # Or some other exit logic
                    return
                result = self.help_menu.handle_event(event)
                if result == "back":
                    return
            # 根据入口来源绘制不同背景
            if from_settings:
                self.settings_menu.draw()
            else:
                self.menu.draw()
            self.help_menu.draw()
            pygame.display.flip()
            self.clock.tick(FPS)

    def run_shop(self):
        self.shop_menu.run()

    def run_backpack(self):
        self.backpack_menu.run()

    def add_background(self):
        # 创建临时的tkinter根窗口（隐藏）
        root = tk.Tk()
        root.withdraw()
        
        # 打开文件选择对话框
        file_path = filedialog.askopenfilename(
            title="选择背景图片",
            filetypes=[
                ("图片文件", "*.png *.jpg *.jpeg *.bmp"),
                ("所有文件", "*.*")
            ]
        )
        
        if file_path:
            try:
                # 复制文件到backgrounds目录
                if not os.path.exists("backgrounds"):
                    os.makedirs("backgrounds")
                    
                # 获取文件名
                file_name = os.path.basename(file_path)
                target_path = os.path.join("backgrounds", file_name)
                
                # 复制文件
                import shutil
                shutil.copy2(file_path, target_path)
                
                # 重新加载背景图片
                self.menu.load_backgrounds()
                
            except Exception as e:
                print(f"添加背景图片时出错: {e}")
        
        # 销毁临时的tkinter根窗口
        root.destroy() 

    def load_sounds(self):
        """加载游戏音效"""
        # 获取当前装备皮肤的音频配置
        audio_config = self.get_current_skin_audio_config()
        
        if audio_config and "game_over_sound" in audio_config:
            game_over_sound_path = audio_config["game_over_sound"]
            if os.path.exists(game_over_sound_path):
                if self.audio_manager.load_sound("game_over", game_over_sound_path):
                    pass # print(f"皮肤专属游戏结束音效加载成功: {game_over_sound_path}")
                else:
                    pass # print(f"皮肤专属游戏结束音效加载失败: {game_over_sound_path}")
            else:
                pass # print(f"未找到皮肤专属游戏结束音效文件: {game_over_sound_path}")
        else:
            # 如果没有皮肤专属音效，不加载默认音效
            pass # print("当前皮肤没有游戏结束音效配置，不播放默认音效")

    def play_game_over_sound(self):
        """播放游戏结束音效"""
        # 获取当前装备皮肤的音频配置
        audio_config = self.get_current_skin_audio_config()
        
        if audio_config and "game_over_sound" in audio_config:
            # 动态加载当前皮肤的游戏结束音效
            game_over_sound_path = audio_config["game_over_sound"]
            if os.path.exists(game_over_sound_path):
                # 先卸载之前的音效，然后加载新的
                if "game_over" in self.audio_manager.sounds:
                    del self.audio_manager.sounds["game_over"]
                
                if self.audio_manager.load_sound("game_over", game_over_sound_path):
                    pass # print(f"动态加载皮肤专属游戏结束音效: {game_over_sound_path}")
                    # 播放皮肤专属音效
                    self.audio_manager.play_sound("game_over")
                else:
                    pass # print(f"动态加载皮肤专属游戏结束音效失败: {game_over_sound_path}")
            else:
                pass # print(f"未找到皮肤专属游戏结束音效文件: {game_over_sound_path}")
        else:
            # 如果没有皮肤专属音效，不播放任何音效
            pass # print("当前皮肤没有游戏结束音效，不播放音效")

    def reload_skin_audio(self, play_music=False):
        """重新加载当前皮肤的音频配置"""
        # print("重新加载皮肤音频配置...")
        # 重新加载音效
        self.load_sounds()
        # 只有在游戏进行中时才重新开始播放背景音乐
        if play_music:
            self.start_game_music() 

    def run_activity(self):
        running = True
        self.activity_page.open()
        # 确保菜单音乐在活动页面播放
        self.in_game = False
        self.play_menu_music()
        while running and self.activity_page.is_open:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return
                self.activity_page.handle_event(event)
            # 关键：弹球和连连看页面时调用update（连连看用draw即可刷新）
            if self.activity_page.page == "pong" and hasattr(self.activity_page, "pong_game"):
                self.activity_page.pong_game.update()
            # 连连看需要强制刷新draw以响应USEREVENT+1
            if self.activity_page.page == "linkgame" and hasattr(self.activity_page, "linkgame_page"):
                pass  # draw已在下方调用，事件已分发
            self.screen.fill((245, 245, 245))
            self.activity_page.draw()
            pygame.display.flip()
            self.clock.tick(FPS)
        self.activity_page.close()

    def return_to_activity(self):
        """返回活动页面"""
        self.stop_game_music()
        self.run_activity()