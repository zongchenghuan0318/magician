import pygame
import random
import time
from .constants import *

class SudokuGame:
    def __init__(self, surface, parent):
        self.surface = surface
        self.parent = parent
        self.active = True
        self.difficulty = 3  # 1-5，默认为3
        self.board = self.generate_board()
        self.original_board = [row[:] for row in self.board]
        self.selected_cell = None
        self.font = pygame.font.Font(FONT_NAME, 36)
        self.small_font = pygame.font.Font(FONT_NAME, 20)
        self.note_font = pygame.font.Font(FONT_NAME, 12)  # 注释字体
        self.error_count = 0
        self.start_time = time.time()
        self.difficulty = 3  # 1-5，默认为3
        self.show_submit_message = False
        self.submit_message = ""
        self.show_errors = False
        self.show_solution = False
        self.solution_board = None
        self.note_mode = False  # 注释模式开关
        self.notes = [[[] for _ in range(9)] for _ in range(9)]  # 存储每个格子的注释
        
        # 从constants获取窗口尺寸
        from game.constants import WINDOW_WIDTH, WINDOW_HEIGHT
        self.window_width = WINDOW_WIDTH
        self.window_height = WINDOW_HEIGHT
        
        # 计算棋盘位置和大小
        self.board_size = min(int(WINDOW_WIDTH * 0.7), int(WINDOW_HEIGHT * 0.7))
        self.cell_size = self.board_size // 9
        self.board_x = (WINDOW_WIDTH - self.board_size) // 2
        self.board_y = (WINDOW_HEIGHT - self.board_size) // 2 + 30
        
        # 按钮区域 - 重新规划布局避免重叠
        # 左上角按钮
        self.back_button_rect = pygame.Rect(20, 20, 100, 40)
        
        # 右上角按钮区（分三行放置）
        self.reset_button_rect = pygame.Rect(WINDOW_WIDTH - 120, 20, 100, 40)
        self.note_button_rect = pygame.Rect(WINDOW_WIDTH - 240, 20, 100, 40)  # 注释按钮
        self.submit_button_rect = pygame.Rect(WINDOW_WIDTH - 120, 80, 100, 40)
        self.hint_button_rect = pygame.Rect(WINDOW_WIDTH - 240, 80, 100, 40)
        self.solution_button_rect = pygame.Rect(WINDOW_WIDTH - 120, 140, 100, 40)
        self.auto_note_button_rect = pygame.Rect(WINDOW_WIDTH - 240, 140, 100, 40)  # 一键注释按钮
        self.delete_button_rect = pygame.Rect(WINDOW_WIDTH - 180, 200, 100, 40)  # 删除按钮
        
        # 难度按钮放在棋盘下方中央
        self.difficulty_rects = [
            pygame.Rect(WINDOW_WIDTH // 2 - 100, self.board_y + self.board_size + 60, 40, 40),
            pygame.Rect(WINDOW_WIDTH // 2 - 50, self.board_y + self.board_size + 60, 40, 40),
            pygame.Rect(WINDOW_WIDTH // 2, self.board_y + self.board_size + 60, 40, 40),
            pygame.Rect(WINDOW_WIDTH // 2 + 50, self.board_y + self.board_size + 60, 40, 40),
            pygame.Rect(WINDOW_WIDTH // 2 + 100, self.board_y + self.board_size + 60, 40, 40)
        ]

    def generate_board(self):
        # 创建一个空棋盘
        board = [[0 for _ in range(9)] for _ in range(9)]
        
        # 填充对角线的3x3子网格
        for i in range(0, 9, 3):
            self.fill_box(board, i, i)
        
        # 使用回溯法填充剩余部分
        self.solve_board(board)
        
        # 根据难度移除数字
        self.remove_numbers(board, self.difficulty)
        
        return board

    def fill_box(self, board, row, col):
        numbers = list(range(1, 10))
        random.shuffle(numbers)
        
        for i in range(3):
            for j in range(3):
                board[row + i][col + j] = numbers.pop()

    def is_safe(self, board, row, col, num):
        # 检查行
        for x in range(9):
            if x != col and board[row][x] == num:
                return False
        
        # 检查列
        for x in range(9):
            if x != row and board[x][col] == num:
                return False
        
        # 检查3x3子网格
        start_row, start_col = 3 * (row // 3), 3 * (col // 3)
        for i in range(3):
            for j in range(3):
                current_row, current_col = i + start_row, j + start_col
                if current_row != row or current_col != col:
                    if board[current_row][current_col] == num:
                        return False
        
        return True

    def solve_board(self, board):
        for i in range(9):
            for j in range(9):
                if board[i][j] == 0:
                    for num in range(1, 10):
                        if self.is_safe(board, i, j, num):
                            board[i][j] = num
                            if self.solve_board(board):
                                return True
                            board[i][j] = 0
                    return False
        return True

    def remove_numbers(self, board, difficulty):
        # 根据难度级别移除数字
        # 难度1: 移除30个数字
        # 难度5: 移除60个数字
        remove_count = 30 + (difficulty - 1) * 7.5
        count = 0
        
        while count < remove_count:
            row = random.randint(0, 8)
            col = random.randint(0, 8)
            
            if board[row][col] != 0:
                board[row][col] = 0
                count += 1

    def draw(self):
        # 绘制背景
        grad = pygame.Surface((self.window_width, self.window_height), pygame.SRCALPHA)
        for y in range(self.window_height):
            c = 245 - int(60 * y / self.window_height)
            pygame.draw.line(grad, (c, c+8, 255, 255), (0, y), (self.window_width, y))
        self.surface.blit(grad, (0, 0))
        
        # 绘制标题
        title_font = pygame.font.Font(FONT_NAME, 40)
        title_text = title_font.render("数独挑战", True, (66, 165, 245))
        title_rect = title_text.get_rect(center=(self.window_width // 2, 100))
        self.surface.blit(title_text, title_rect)
        
        # 绘制棋盘
        self.draw_board()
        
        # 绘制按钮
        self.draw_buttons()
        
        # 绘制游戏信息
        self.draw_game_info()

    def draw_board(self):
        # 绘制棋盘背景
        board_bg_rect = pygame.Rect(self.board_x - 10, self.board_y - 10, 
                                    self.board_size + 20, self.board_size + 20)
        pygame.draw.rect(self.surface, (255, 255, 255), board_bg_rect, border_radius=10)
        pygame.draw.rect(self.surface, (0, 0, 0), board_bg_rect, 2, border_radius=10)
        
        # 绘制单元格
        for i in range(9):
            for j in range(9):
                rect = pygame.Rect(
                    self.board_x + j * self.cell_size,
                    self.board_y + i * self.cell_size,
                    self.cell_size,
                    self.cell_size
                )
                
                # 选中的单元格高亮
                if self.selected_cell == (i, j):
                    pygame.draw.rect(self.surface, (200, 200, 255), rect)
                
                # 绘制单元格边框
                pygame.draw.rect(self.surface, (200, 200, 200), rect, 1)
                
                # 绘制3x3子网格的粗边框
                if i % 3 == 0 and i > 0:
                    pygame.draw.line(self.surface, (0, 0, 0),
                                     (self.board_x, self.board_y + i * self.cell_size),
                                     (self.board_x + self.board_size, self.board_y + i * self.cell_size),
                                     3)
                if j % 3 == 0 and j > 0:
                    pygame.draw.line(self.surface, (0, 0, 0),
                                     (self.board_x + j * self.cell_size, self.board_y),
                                     (self.board_x + j * self.cell_size, self.board_y + self.board_size),
                                     3)
                
                # 绘制数字
                if self.show_solution and self.solution_board:
                    # 显示解决方案
                    color = (0, 150, 0) if self.original_board[i][j] == 0 else (0, 0, 0)
                    text = self.font.render(str(self.solution_board[i][j]), True, color)
                    text_rect = text.get_rect(center=rect.center)
                    self.surface.blit(text, text_rect)
                elif self.board[i][j] != 0:
                    # 检查是否为错误
                    is_error = self.show_errors and self.original_board[i][j] == 0 and not self.is_safe(self.board, i, j, self.board[i][j])
                    color = (200, 0, 0) if is_error else ((0, 0, 0) if self.original_board[i][j] != 0 else (66, 165, 245))
                    text = self.font.render(str(self.board[i][j]), True, color)
                    text_rect = text.get_rect(center=rect.center)
                    self.surface.blit(text, text_rect)
                # 显示注释
                if self.notes[i][j] and not self.show_solution and self.board[i][j] == 0:
                    # 绘制注释背景，选中的格子使用不同颜色
                    bg_color = (200, 200, 255) if self.selected_cell == (i, j) else (240, 240, 240)
                    pygame.draw.rect(self.surface, bg_color, rect)
                    # 绘制注释数字（3x3网格排列）
                    for idx, num in enumerate(self.notes[i][j]):
                        x_offset = (idx % 3) * (self.cell_size // 3) + 5
                        y_offset = (idx // 3) * (self.cell_size // 3) + 2
                        note_text = self.note_font.render(str(num), True, (100, 100, 100))
                        self.surface.blit(note_text, (rect.x + x_offset, rect.y + y_offset))
                    
                    # 重新绘制单元格边框
                    pygame.draw.rect(self.surface, (200, 200, 200), rect, 1)
                    
                    # 重新绘制3x3子网格的粗边框
                    if i % 3 == 0 and i > 0:
                        pygame.draw.line(self.surface, (0, 0, 0),
                                         (self.board_x, self.board_y + i * self.cell_size),
                                         (self.board_x + self.board_size, self.board_y + i * self.cell_size),
                                         3)
                    if j % 3 == 0 and j > 0:
                        pygame.draw.line(self.surface, (0, 0, 0),
                                         (self.board_x + j * self.cell_size, self.board_y),
                                         (self.board_x + j * self.cell_size, self.board_y + self.board_size),
                                         3)
                
                # 显示错误提示
                if self.show_errors and self.original_board[i][j] == 0 and self.board[i][j] != 0 and not self.is_safe(self.board, i, j, self.board[i][j]):
                    # 绘制错误单元格背景
                    pygame.draw.rect(self.surface, (255, 200, 200), rect)
        
        # 绘制棋盘外边框
        pygame.draw.rect(self.surface, (0, 0, 0),
                         (self.board_x, self.board_y, self.board_size, self.board_size), 3)

    def draw_buttons(self):
        # 返回按钮
        pygame.draw.rect(self.surface, (220, 220, 220), self.back_button_rect, border_radius=5)
        pygame.draw.rect(self.surface, (0, 0, 0), self.back_button_rect, 2, border_radius=5)
        back_text = self.small_font.render("返回", True, (0, 0, 0))
        back_text_rect = back_text.get_rect(center=self.back_button_rect.center)
        self.surface.blit(back_text, back_text_rect)
        
        # 绘制重置按钮
        pygame.draw.rect(self.surface, (220, 220, 220), self.reset_button_rect, border_radius=5)
        pygame.draw.rect(self.surface, (0, 0, 0), self.reset_button_rect, 2, border_radius=5)
        reset_text = self.small_font.render("重置", True, (0, 0, 0))
        reset_text_rect = reset_text.get_rect(center=self.reset_button_rect.center)
        self.surface.blit(reset_text, reset_text_rect)
        
        # 绘制注释按钮
        note_color = (255, 215, 0) if self.note_mode else (220, 220, 220)
        pygame.draw.rect(self.surface, note_color, self.note_button_rect, border_radius=5)
        pygame.draw.rect(self.surface, (0, 0, 0), self.note_button_rect, 2, border_radius=5)
        note_text = self.small_font.render("注释", True, (0, 0, 0))
        note_text_rect = note_text.get_rect(center=self.note_button_rect.center)
        self.surface.blit(note_text, note_text_rect)
        
        # 绘制提交按钮
        pygame.draw.rect(self.surface, (100, 200, 255), self.submit_button_rect, border_radius=5)
        pygame.draw.rect(self.surface, (0, 0, 0), self.submit_button_rect, 2, border_radius=5)
        submit_text = self.small_font.render("提交", True, (0, 0, 0))
        submit_text_rect = submit_text.get_rect(center=self.submit_button_rect.center)
        self.surface.blit(submit_text, submit_text_rect)
        
        # 绘制提示错误按钮
        pygame.draw.rect(self.surface, (255, 150, 150), self.hint_button_rect, border_radius=5)
        pygame.draw.rect(self.surface, (0, 0, 0), self.hint_button_rect, 2, border_radius=5)
        hint_text = self.small_font.render("提示错误", True, (0, 0, 0))
        hint_text_rect = hint_text.get_rect(center=self.hint_button_rect.center)
        self.surface.blit(hint_text, hint_text_rect)
        
        # 绘制显示答案按钮
        pygame.draw.rect(self.surface, (150, 255, 150), self.solution_button_rect, border_radius=5)
        pygame.draw.rect(self.surface, (0, 0, 0), self.solution_button_rect, 2, border_radius=5)
        solution_text = self.small_font.render("显示答案", True, (0, 0, 0))
        solution_text_rect = solution_text.get_rect(center=self.solution_button_rect.center)
        self.surface.blit(solution_text, solution_text_rect)
        
        # 绘制一键注释按钮
        pygame.draw.rect(self.surface, (200, 150, 255), self.auto_note_button_rect, border_radius=5)
        pygame.draw.rect(self.surface, (0, 0, 0), self.auto_note_button_rect, 2, border_radius=5)
        auto_note_text = self.small_font.render("一键注释", True, (0, 0, 0))
        auto_note_text_rect = auto_note_text.get_rect(center=self.auto_note_button_rect.center)
        self.surface.blit(auto_note_text, auto_note_text_rect)

        # 绘制删除按钮
        pygame.draw.rect(self.surface, (255, 100, 100), self.delete_button_rect, border_radius=5)
        pygame.draw.rect(self.surface, (0, 0, 0), self.delete_button_rect, 2, border_radius=5)
        delete_text = self.small_font.render("删除", True, (0, 0, 0))
        delete_text_rect = delete_text.get_rect(center=self.delete_button_rect.center)
        self.surface.blit(delete_text, delete_text_rect)
        
        # 难度按钮
        difficulty_text = self.small_font.render("难度:", True, (0, 0, 0))
        self.surface.blit(difficulty_text, (self.window_width // 2 - 140, self.board_y + self.board_size + 70))
        
        for i in range(5):
            color = (100, 200, 255) if i + 1 == self.difficulty else (220, 220, 220)
            pygame.draw.rect(self.surface, color, self.difficulty_rects[i], border_radius=5)
            pygame.draw.rect(self.surface, (0, 0, 0), self.difficulty_rects[i], 2, border_radius=5)
            diff_text = self.small_font.render(str(i + 1), True, (0, 0, 0))
            diff_text_rect = diff_text.get_rect(center=self.difficulty_rects[i].center)
            self.surface.blit(diff_text, diff_text_rect)        
        
        # 显示提交消息
        if self.show_submit_message:
            msg_rect = pygame.Rect(
                self.window_width // 2 - 200,
                self.window_height // 2 - 50,
                400,
                100
            )
            pygame.draw.rect(self.surface, (255, 255, 255), msg_rect, border_radius=10)
            pygame.draw.rect(self.surface, (0, 0, 0), msg_rect, 2, border_radius=10)
            
            msg_text = self.small_font.render(self.submit_message, True, (200, 0, 0) if "错误" in self.submit_message else (0, 150, 0))
            msg_text_rect = msg_text.get_rect(center=msg_rect.center)
            self.surface.blit(msg_text, msg_text_rect)
            
            # 确定按钮
            ok_rect = pygame.Rect(
                self.window_width // 2 - 60,
                self.window_height // 2 + 10,
                120,
                30
            )
            pygame.draw.rect(self.surface, (100, 200, 255), ok_rect, border_radius=5)
            pygame.draw.rect(self.surface, (0, 0, 0), ok_rect, 2, border_radius=5)
            ok_text = self.small_font.render("确定", True, (0, 0, 0))
            ok_text_rect = ok_text.get_rect(center=ok_rect.center)
            self.surface.blit(ok_text, ok_text_rect)

    def draw_game_info(self):
        # 显示时间
        elapsed_time = int(time.time() - self.start_time)
        time_text = self.small_font.render(f"时间: {elapsed_time}秒", True, (0, 0, 0))
        self.surface.blit(time_text, (self.board_x, self.board_y + self.board_size + 20))
        
        # 显示错误次数
        error_text = self.small_font.render(f"错误: {self.error_count}", True, (0, 0, 0))
        self.surface.blit(error_text, (self.board_x + self.board_size - 100, self.board_y + self.board_size + 20))



    def handle_event(self, event):
        if self.show_submit_message:
            if event.type == pygame.MOUSEBUTTONDOWN:
                # 点击确定按钮关闭消息
                ok_rect = pygame.Rect(
                    self.window_width // 2 - 60,
                    self.window_height // 2 + 10,
                    120,
                    30
                )
                if ok_rect.collidepoint(event.pos):
                    self.show_submit_message = False
                    # 如果是提交成功，返回菜单
                    if "恭喜" in self.submit_message:
                        self.active = False
                return True
            return False

        if event.type == pygame.MOUSEBUTTONDOWN:
            # 检查返回按钮
            if self.back_button_rect.collidepoint(event.pos):
                self.active = False
                # 通知父组件返回活动页面
                if hasattr(self.parent, 'return_to_activity'):
                    self.parent.return_to_activity()
                return True
            
            # 检查重置按钮
            if self.reset_button_rect.collidepoint(event.pos):
                self.board = [row[:] for row in self.original_board]
                self.error_count = 0
                self.start_time = time.time()
                self.show_errors = False
                self.show_solution = False
                self.note_mode = False
                self.notes = [[[] for _ in range(9)] for _ in range(9)]  # 重置注释
                return True
            
            # 检查注释按钮
            if self.note_button_rect.collidepoint(event.pos):
                self.note_mode = not self.note_mode
                return True
            
            # 检查提交按钮
            if self.submit_button_rect.collidepoint(event.pos):
                self.check_submission()
                return True
            
            # 检查提示错误按钮
            if self.hint_button_rect.collidepoint(event.pos):
                self.show_errors = not self.show_errors
                self.show_solution = False  # 显示错误时关闭答案显示
                return True
            
            # 检查显示答案按钮
            if self.solution_button_rect.collidepoint(event.pos):
                # 每次点击重新生成解决方案，确保与当前题目一致
                self.solution_board = [row[:] for row in self.original_board]
                self.solve_board(self.solution_board)
                self.show_solution = not self.show_solution
                self.show_errors = False  # 显示答案时关闭错误提示
                return True
            
            # 检查一键注释按钮
            if self.auto_note_button_rect.collidepoint(event.pos):
                self.auto_note_all()
                return True
            
            # 检查删除按钮
            if self.delete_button_rect.collidepoint(event.pos):
                if self.selected_cell:
                    row, col = self.selected_cell
                    if self.original_board[row][col] == 0:
                        if self.note_mode:
                            self.notes[row][col] = []  # 清空注释
                        else:
                            self.board[row][col] = 0
                return True
            
            # 检查难度按钮
            for i in range(5):
                if self.difficulty_rects[i].collidepoint(event.pos):
                    self.difficulty = i + 1
                    self.board = self.generate_board()
                    self.original_board = [row[:] for row in self.board]
                    self.error_count = 0
                    self.start_time = time.time()
                    self.show_errors = False
                    self.show_solution = False
                    return True
            
            # 检查棋盘点击
            if (self.board_x <= event.pos[0] <= self.board_x + self.board_size and
                self.board_y <= event.pos[1] <= self.board_y + self.board_size):
                col = (event.pos[0] - self.board_x) // self.cell_size
                row = (event.pos[1] - self.board_y) // self.cell_size
                self.selected_cell = (row, col)
                return True
        
        # 处理键盘输入
        elif event.type == pygame.KEYDOWN:
            if self.selected_cell and event.unicode.isdigit() and event.unicode != '0':
                row, col = self.selected_cell
                # 检查是否是原始数字
                if self.original_board[row][col] == 0:
                    if self.note_mode:
                        # 注释模式：添加或移除注释
                        num = int(event.unicode)
                        if num in self.notes[row][col]:
                            self.notes[row][col].remove(num)
                        else:
                            self.notes[row][col].append(num)
                            self.notes[row][col].sort()  # 保持排序
                    else:
                        # 正常模式：设置数字
                        self.board[row][col] = int(event.unicode)
                return True
            elif event.key == pygame.K_BACKSPACE or event.key == pygame.K_DELETE:
                if self.selected_cell:
                    row, col = self.selected_cell
                    if self.original_board[row][col] == 0:
                        if self.note_mode:
                            self.notes[row][col] = []  # 清空注释
                        else:
                            self.board[row][col] = 0
                return True
            elif event.key == pygame.K_ESCAPE:
                self.active = False
                return True
            elif event.key == pygame.K_n:
                # 快捷键：切换注释模式
                self.note_mode = not self.note_mode
                return True
        
        return False
        
    def check_submission(self):
        # 检查是否填满
        for i in range(9):
            for j in range(9):
                if self.board[i][j] == 0:
                    self.submit_message = "棋盘未填满，请继续填写！"
                    self.show_submit_message = True
                    return
        
        # 检查是否有错误
        for i in range(9):
            for j in range(9):
                if not self.is_safe(self.board, i, j, self.board[i][j]):
                    self.submit_message = "提交失败！棋盘中存在错误。"
                    self.show_submit_message = True
                    return
        
        # 提交成功
        elapsed_time = int(time.time() - self.start_time)
        self.submit_message = f"恭喜完成！用时: {elapsed_time}秒"
        self.show_submit_message = True

    def is_game_complete(self):
        for i in range(9):
            for j in range(9):
                if self.board[i][j] == 0:
                    return False
                if not self.is_safe(self.board, i, j, self.board[i][j]):
                    return False
        return True

    def draw_failure_message(self):
        # 绘制失败消息背景
        msg_rect = pygame.Rect(
            self.window_width // 2 - 200,
            self.window_height // 2 - 100,
            400,
            200
        )
        pygame.draw.rect(self.surface, (255, 255, 255), msg_rect, border_radius=10)
        pygame.draw.rect(self.surface, (0, 0, 0), msg_rect, 2, border_radius=10)
        
        # 绘制失败消息文本
        msg_font = pygame.font.Font(FONT_NAME, 36)
        msg_text = msg_font.render("游戏失败！", True, (200, 0, 0))
        msg_text_rect = msg_text.get_rect(center=(self.window_width // 2, self.window_height // 2 - 30))
        self.surface.blit(msg_text, msg_text_rect)
        
        # 显示错误次数
        error_text = self.small_font.render(f"错误次数达到 {self.max_errors} 次", True, (0, 0, 0))
        error_text_rect = error_text.get_rect(center=(self.window_width // 2, self.window_height // 2 + 20))
        self.surface.blit(error_text, error_text_rect)
        
        # 重新开始按钮
        retry_rect = pygame.Rect(
            self.window_width // 2 - 140,
            self.window_height // 2 + 60,
            120,
            40
        )
        pygame.draw.rect(self.surface, (100, 200, 255), retry_rect, border_radius=5)
        pygame.draw.rect(self.surface, (0, 0, 0), retry_rect, 2, border_radius=5)
        retry_text = self.small_font.render("重新开始", True, (0, 0, 0))
        retry_text_rect = retry_text.get_rect(center=retry_rect.center)
        self.surface.blit(retry_text, retry_text_rect)
        
        # 返回菜单按钮
        menu_rect = pygame.Rect(
            self.window_width // 2 + 20,
            self.window_height // 2 + 60,
            120,
            40
        )
        pygame.draw.rect(self.surface, (100, 200, 255), menu_rect, border_radius=5)
        pygame.draw.rect(self.surface, (0, 0, 0), menu_rect, 2, border_radius=5)
        menu_text = self.small_font.render("返回菜单", True, (0, 0, 0))
        menu_text_rect = menu_text.get_rect(center=menu_rect.center)
        self.surface.blit(menu_text, menu_text_rect)
        
        # 捕获鼠标事件以关闭消息
        for event in pygame.event.get():
            if event.type == pygame.MOUSEBUTTONDOWN:
                if retry_rect.collidepoint(event.pos):
                    self.board = [row[:] for row in self.original_board]
                    self.error_count = 0
                    self.start_time = time.time()
                    return True
                elif menu_rect.collidepoint(event.pos):
                    self.active = False
                    return True
        
    def auto_note_all(self):
        """为所有未填写的格子自动添加可能的数字注释"""
        # 确保先有解决方案
        if not self.solution_board:
            self.solution_board = [row[:] for row in self.original_board]
            self.solve_board(self.solution_board)
        
        # 为每个未填写的格子添加注释
        for i in range(9):
            for j in range(9):
                if self.board[i][j] == 0 and self.original_board[i][j] == 0:
                    # 找出所有可能的数字
                    possible_numbers = []
                    for num in range(1, 10):
                        if self.is_safe(self.board, i, j, num):
                            possible_numbers.append(num)
                    self.notes[i][j] = possible_numbers
        
        # 自动关闭注释模式
        self.note_mode = False

    def update(self):
        # 处理事件
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.active = False
                return False
            self.handle_event(event)
        return True