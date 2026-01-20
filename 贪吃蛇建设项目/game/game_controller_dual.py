import pygame
from .snake import Snake
from .game_board_dual import GameBoardDual
from .menu import GameOverMenuDual

FONT_NAME = "msyh.ttc"  # 如有自定义字体可替换

class GameControllerDual:
    def __init__(self, screen, board_size=(20, 20)):
        self.screen = screen
        self.board_size = board_size
        # 让WASD控制的蛇为玩家1，方向键为玩家2
        self.snake1 = Snake(allow_cross_self=True)  # WASD
        self.snake1.positions = [(15, 10)]
        self.snake2 = Snake(allow_cross_self=True)  # 方向键
        self.snake2.positions = [(5, 10)]
        self.board = GameBoardDual(self.snake1, self.snake2, board_size)
        self.running = True
        self.clock = pygame.time.Clock()
        self.score1 = 0
        self.score2 = 0
        self.game_over = False
        self.paused = False
        self.winner = None
        self.game_over_menu = GameOverMenuDual(self.screen)

    def handle_event(self, event):
        # ESC暂停
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.paused = not self.paused
        # 玩家1：WASD，玩家2：方向键
        if event.type == pygame.KEYDOWN and not self.paused and not self.game_over:
            # 玩家2（方向键）
            if event.key == pygame.K_UP:
                self.snake2.change_direction((0, -1))
            elif event.key == pygame.K_DOWN:
                self.snake2.change_direction((0, 1))
            elif event.key == pygame.K_LEFT:
                self.snake2.change_direction((-1, 0))
            elif event.key == pygame.K_RIGHT:
                self.snake2.change_direction((1, 0))
            # 玩家1（WASD）
            elif event.key == pygame.K_w:
                self.snake1.change_direction((0, -1))
            elif event.key == pygame.K_s:
                self.snake1.change_direction((0, 1))
            elif event.key == pygame.K_a:
                self.snake1.change_direction((-1, 0))
            elif event.key == pygame.K_d:
                self.snake1.change_direction((1, 0))

    def update(self):
        if self.paused or self.game_over:
            return
        self.snake1.move()
        self.snake2.move()
        self.board.update()
        # 头撞头判定
        if len(self.snake1.positions) > 0 and len(self.snake2.positions) > 0 and self.snake1.positions[0] == self.snake2.positions[0]:
            l1 = len(self.snake1.positions)
            l2 = len(self.snake2.positions)
            if l1 > l2:
                self.winner = 1
            elif l2 > l1:
                self.winner = 2
            else:
                self.winner = 0  # 平局
            self.game_over = True
            return
        # 头撞对方身体
        if len(self.snake1.positions) > 0 and self.snake1.positions[0] in self.snake2.positions[1:]:
            self.winner = 2
            self.game_over = True
            return
        if len(self.snake2.positions) > 0 and self.snake2.positions[0] in self.snake1.positions[1:]:
            self.winner = 1
            self.game_over = True
            return
        # 撞自己（允许穿过自己，不再判game_over）
        # if len(self.snake1.positions) > 0 and self.snake1.positions[0] in self.snake1.positions[1:]:
        #     self.winner = 2
        #     self.game_over = True
        #     return
        # if len(self.snake2.positions) > 0 and self.snake2.positions[0] in self.snake2.positions[1:]:
        #     self.winner = 1
        #     self.game_over = True
        #     return
        # 撞对方（头撞头和头撞身体已覆盖，无需再判）

    def draw_score_panel(self):
        # 玩家1分数
        panel1 = pygame.Surface((180, 50), pygame.SRCALPHA)
        panel1.fill((0, 200, 0, 180))
        font = pygame.font.SysFont('Microsoft YaHei', 28)
        text1 = font.render(f"玩家1分数: {self.snake1.score}", True, (255,255,255))
        panel1.blit(text1, (16, 10))
        self.screen.blit(panel1, (10, 10))
        # 玩家2分数
        panel2 = pygame.Surface((180, 50), pygame.SRCALPHA)
        panel2.fill((0, 120, 255, 180))
        text2 = font.render(f"玩家2分数: {self.snake2.score}", True, (255,255,255))
        panel2.blit(text2, (16, 10))
        self.screen.blit(panel2, (self.screen.get_width()-190, 10))

    def draw_game_over(self):
        # 复用GameOverMenu，显示双人分数和胜负（美观排版）
        self.game_over_menu.draw(self.snake1.score, self.snake2.score, self.winner)

    def draw_pause(self):
        overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0,0,0,120))
        self.screen.blit(overlay, (0,0))
        font = pygame.font.SysFont('Microsoft YaHei', 56)
        text = font.render("暂停", True, (255,255,255))
        rect = text.get_rect(center=(self.screen.get_width()//2, self.screen.get_height()//2))
        self.screen.blit(text, rect)
        tip = pygame.font.SysFont('Microsoft YaHei', 28).render("按ESC继续", True, (255,255,255))
        tip_rect = tip.get_rect(center=(self.screen.get_width()//2, self.screen.get_height()//2+60))
        self.screen.blit(tip, tip_rect)

    def draw(self):
        self.board.draw(self.screen)
        self.draw_score_panel()
        if self.paused:
            self.draw_pause()
        if self.game_over:
            self.draw_game_over()

    def run(self):
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                self.handle_event(event)
            if self.game_over:
                self.draw()
                pygame.display.flip()
                # 阻塞等待按钮选择
                waiting = True
                while waiting:
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            self.running = False
                            waiting = False
                        result = self.game_over_menu.handle_event(event)
                        if result == "restart":
                            self.__init__(self.screen, self.board_size)  # 重新开始
                            waiting = False
                        elif result == "main_menu":
                            self.running = False
                            waiting = False
                    self.draw()
                    pygame.display.flip()
                continue
            if not self.paused and not self.game_over:
                self.update()
            self.draw()
            pygame.display.flip()
            self.clock.tick(10) 