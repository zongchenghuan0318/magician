import json
import os
import pygame
from game.constants import FONT_NAME

class Achievement:
    def __init__(self, id, name, description, icon=None, secret=False):
        self.id = id
        self.name = name
        self.description = description
        self.icon = icon
        self.secret = secret  # 是否为隐藏成就
        self.unlocked = False
        self.unlock_time = None

class AchievementSystem:
    def __init__(self, screen):
        self.screen = screen
        self.achievements = []
        self.notification_queue = []
        self.notification_time = 0
        self.font_title = pygame.font.Font(FONT_NAME, 24)
        self.font_desc = pygame.font.Font(FONT_NAME, 18)
        self.save_file = "achievements.json"
        
        # 初始化成就列表
        self._init_achievements()
        self._load_achievements()
    
    def _init_achievements(self):
        """初始化所有可能的成就"""
        self.achievements = [
            Achievement("first_game", "初次体验", "第一次开始游戏"),
            Achievement("score_100", "小有成就", "单局游戏得分达到100分"),
            Achievement("score_500", "蛇王传说", "单局游戏得分达到500分"),
            Achievement("games_10", "坚持不懈", "游戏10次"),
            Achievement("eat_apple_50", "果然爱吃", "总共吃掉50个苹果"),
            Achievement("eat_special_10", "特殊收藏家", "吃掉10个特殊食物"),
            Achievement("die_wall_5", "撞墙专家", "撞墙死亡5次"),
            Achievement("die_self_5", "自食其果", "咬到自己5次"),
            Achievement("speed_max", "极速狂飙", "达到最高速度"),
            Achievement("all_skins", "蛇皮收藏家", "解锁所有皮肤", secret=True),
        ]
    
    def _load_achievements(self):
        """从文件加载成就状态"""
        if os.path.exists(self.save_file):
            try:
                with open(self.save_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                for achievement_data in data:
                    for achievement in self.achievements:
                        if achievement.id == achievement_data["id"]:
                            achievement.unlocked = achievement_data["unlocked"]
                            achievement.unlock_time = achievement_data.get("unlock_time")
            except Exception as e:
                print(f"加载成就出错: {e}")
    
    def save_achievements(self):
        """保存成就状态到文件"""
        data = []
        for achievement in self.achievements:
            data.append({
                "id": achievement.id,
                "unlocked": achievement.unlocked,
                "unlock_time": achievement.unlock_time
            })
            
        try:
            with open(self.save_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存成就出错: {e}")
    
    def unlock_achievement(self, achievement_id):
        """解锁指定ID的成就"""
        import time
        
        for achievement in self.achievements:
            if achievement.id == achievement_id and not achievement.unlocked:
                achievement.unlocked = True
                achievement.unlock_time = time.time()
                self.notification_queue.append(achievement)
                self.save_achievements()
                return True
        return False
    
    def check_achievement(self, stats):
        """根据游戏统计数据检查并解锁成就"""
        # 示例检查逻辑
        if stats.get("games_played", 0) >= 1:
            self.unlock_achievement("first_game")
            
        if stats.get("highest_score", 0) >= 100:
            self.unlock_achievement("score_100")
            
        if stats.get("highest_score", 0) >= 500:
            self.unlock_achievement("score_500")
            
        if stats.get("games_played", 0) >= 10:
            self.unlock_achievement("games_10")
            
        if stats.get("total_apples", 0) >= 50:
            self.unlock_achievement("eat_apple_50")
            
        if stats.get("special_food", 0) >= 10:
            self.unlock_achievement("eat_special_10")
            
        if stats.get("wall_deaths", 0) >= 5:
            self.unlock_achievement("die_wall_5")
            
        if stats.get("self_deaths", 0) >= 5:
            self.unlock_achievement("die_self_5")
            
        if stats.get("max_speed_reached", False):
            self.unlock_achievement("speed_max")
            
        if stats.get("all_skins_unlocked", False):
            self.unlock_achievement("all_skins")
    
    def update(self):
        """更新成就通知"""
        import time
        
        current_time = time.time()
        
        # 处理通知队列
        if self.notification_queue and current_time - self.notification_time > 3:
            self.notification_queue.pop(0)
            if self.notification_queue:
                self.notification_time = current_time
    
    def draw_notification(self):
        """绘制成就解锁通知"""
        if not self.notification_queue:
            return
            
        achievement = self.notification_queue[0]
        
        # 绘制通知背景
        notification_width = 400
        notification_height = 80
        x = (self.screen.get_width() - notification_width) // 2
        y = 50
        
        # 绘制背景和边框
        pygame.draw.rect(self.screen, (0, 0, 0, 180), (x, y, notification_width, notification_height), border_radius=10)
        pygame.draw.rect(self.screen, (255, 215, 0), (x, y, notification_width, notification_height), 2, border_radius=10)
        
        # 绘制标题
        title_text = f"🏆 成就解锁: {achievement.name}"
        title_surface = self.font_title.render(title_text, True, (255, 215, 0))
        self.screen.blit(title_surface, (x + 20, y + 15))
        
        # 绘制描述
        desc_surface = self.font_desc.render(achievement.description, True, (200, 200, 200))
        self.screen.blit(desc_surface, (x + 20, y + 45))
    
    def draw_achievements_page(self):
        """绘制成就页面"""
        # 清屏
        self.screen.fill((20, 30, 40))
        
        # 绘制标题
        title_font = pygame.font.Font(FONT_NAME, 36)
        title_surface = title_font.render("游戏成就", True, (255, 255, 255))
        title_rect = title_surface.get_rect(center=(self.screen.get_width()//2, 50))
        self.screen.blit(title_surface, title_rect)
        
        # 绘制成就列表
        y_start = 120
        x_margin = 100
        width = self.screen.get_width() - 2 * x_margin
        height = 80
        spacing = 20
        
        for i, achievement in enumerate(self.achievements):
            # 跳过未解锁的隐藏成就
            if achievement.secret and not achievement.unlocked:
                continue
                
            y = y_start + i * (height + spacing)
            
            # 绘制成就背景
            color = (60, 60, 70) if achievement.unlocked else (40, 40, 50)
            pygame.draw.rect(self.screen, color, (x_margin, y, width, height), border_radius=10)
            
            # 绘制边框
            border_color = (255, 215, 0) if achievement.unlocked else (100, 100, 100)
            pygame.draw.rect(self.screen, border_color, (x_margin, y, width, height), 2, border_radius=10)
            
            # 绘制成就图标
            icon_rect = pygame.Rect(x_margin + 20, y + 20, 40, 40)
            if achievement.unlocked:
                pygame.draw.rect(self.screen, (255, 215, 0), icon_rect, border_radius=5)
                text = "🏆"
            else:
                pygame.draw.rect(self.screen, (100, 100, 100), icon_rect, border_radius=5)
                text = "🔒"
            
            icon_font = pygame.font.Font(FONT_NAME, 24)
            icon_surface = icon_font.render(text, True, (255, 255, 255))
            icon_text_rect = icon_surface.get_rect(center=icon_rect.center)
            self.screen.blit(icon_surface, icon_text_rect)
            
            # 绘制成就名称
            name_surface = self.font_title.render(achievement.name, True, (255, 255, 255))
            self.screen.blit(name_surface, (x_margin + 80, y + 15))
            
            # 绘制成就描述
            if achievement.secret and not achievement.unlocked:
                desc_text = "???"
            else:
                desc_text = achievement.description
                
            desc_surface = self.font_desc.render(desc_text, True, (200, 200, 200))
            self.screen.blit(desc_surface, (x_margin + 80, y + 45))
            
            # 如果已解锁，显示解锁时间
            if achievement.unlocked and achievement.unlock_time:
                import time
                unlock_time_str = time.strftime("%Y-%m-%d %H:%M", time.localtime(achievement.unlock_time))
                time_surface = self.font_desc.render(f"解锁于: {unlock_time_str}", True, (150, 150, 150))
                time_rect = time_surface.get_rect(right=x_margin + width - 20, centery=y + height//2)
                self.screen.blit(time_surface, time_rect)
        
        # 绘制返回提示
        back_text = "按ESC返回"
        back_surface = self.font_desc.render(back_text, True, (150, 150, 150))
        back_rect = back_surface.get_rect(center=(self.screen.get_width()//2, self.screen.get_height() - 30))
        self.screen.blit(back_surface, back_rect)
    
    def run_achievements_page(self):
        """运行成就页面"""
        running = True
        clock = pygame.time.Clock()
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "exit"
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return
            
            self.draw_achievements_page()
            pygame.display.flip()
            clock.tick(60)