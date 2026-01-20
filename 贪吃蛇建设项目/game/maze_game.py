# -*- coding: utf-8 -*-
import pygame
import random
import time
import math
from .constants import *

class MazeGame:
    def __init__(self, surface):
        self.surface = surface
        self.active = True
        self.state = "level_select"  # level_select, playing, win, lose
        
        # 游戏等级配置 - 增加更大更复杂的迷宫
        self.levels = {
            1: {"name": "新手", "size": (30, 30), "time_limit": 120, "color": (102, 204, 102)},
            2: {"name": "初级", "size": (42, 42), "time_limit": 180, "color": (255, 213, 79)},
            3: {"name": "中级", "size": (54, 54), "time_limit": 240, "color": (255, 152, 0)},
            4: {"name": "高级", "size": (70, 70), "time_limit": 300, "color": (255, 87, 34)},
            5: {"name": "专家", "size": (82, 82), "time_limit": 360, "color": (156, 39, 176)},
            6: {"name": "大师", "size": (98, 98), "time_limit": 420, "color": (244, 67, 54)},
            7: {"name": "宗师", "size": (110, 110), "time_limit": 480, "color": (180, 0, 0)}
        }
        
        self.current_level = 1
        self.maze = []
        self.player_pos = [1, 1]
        self.end_pos = [1, 1]
        self.cell_size = 8
        self.start_time = 0
        self.game_time = 0
        
        # 视觉效果
        self.particle_effects = []
        self.trail_positions = []
        self.animation_time = 0
        self.win_animation = 0
        
        # 迷宫偏移（用于居中显示）
        self.maze_offset_x = 0
        self.maze_offset_y = 0

        # 连续移动控制
        self.last_move_time = 0
        self.move_delay = 150  # 移动间隔（毫秒）
        self.first_move_delay = 300  # 首次移动延迟（毫秒）
        self.key_pressed_time = {}  # 记录按键按下的时间

        # 等级选择页面动画
        self.level_select_animation = 0
        self.floating_particles = []

        # 视野限制系统 - 减小视野范围以增加难度
        self.vision_enabled = True  # 是否启用视野限制
        self.vision_radius = 2.5  # 减小视野半径（格子数）从3减到2.5
        self.explored_cells = set()  # 已探索的格子
        self.fog_surface = None  # 迷雾遮罩层
        self.button_animations = {}  # 存储每个按钮的动画状态

        # 背景迷宫效果
        self.background_maze = self.generate_background_maze()
        self.path_animation = 0
        self.animated_path = []

        # 唯一路径模式
        self.unique_path_mode = True  # 默认开启唯一路径模式

        # 新增：迷宫生成风格与参数
        # 0 标准、1 长走廊、2 带环、3 房间
        self.maze_style_index = 0
        self.maze_style_names = ["标准", "长走廊", "带环", "房间"]
        # 生成参数（可由风格驱动）
        self.twistiness = 0.6          # 越低越直，越高越弯
        self.loop_rate = 0.0           # 打通墙形成环路的比例
        self.room_rate = 0.0           # 房间覆盖率（0~0.25 合理）
        self.min_path_len_ratio = 0.7  # 最短路下限，相对 (宽+高)

        # 随机起终点模式
        self.random_spawn_enabled = False

        # 顶部信息栏自动隐藏（仅在视野限制开启时启用）
        self.ui_auto_hide_enabled = True
        self.ui_current_height = 64
        self.ui_target_height = 64
        self.ui_last_interaction_time = 0


        # 背景迷宫效果
        self.background_maze = self.generate_background_maze()
        self.path_animation = 0
        self.animated_path = []

        # 唯一路径模式
        self.unique_path_mode = True  # 默认开启唯一路径模式

    def generate_maze(self, width, height):
        """使用迭代回溯算法生成迷宫 - 保证唯一路径"""
        # 初始化迷宫（全是墙）
        maze = [[1 for _ in range(width)] for _ in range(height)]

        # 使用栈实现迭代回溯算法
        stack = [(1, 1)]  # 从起点开始
        maze[1][1] = 0  # 标记起点为通路

        while stack:
            x, y = stack[-1]

            # 随机方向
            directions = [(0, 2), (2, 0), (0, -2), (-2, 0)]
            random.shuffle(directions)

            found = False
            for dx, dy in directions:
                nx, ny = x + dx, y + dy
                if 0 < nx < width-1 and 0 < ny < height-1 and maze[ny][nx] == 1:
                    # 打通中间的墙
                    maze[y + dy//2][x + dx//2] = 0
                    maze[ny][nx] = 0  # 标记新位置为通路
                    stack.append((nx, ny))
                    found = True
                    break

            if not found:
                stack.pop()  # 回溯

        # 确保起点和终点是通路
        maze[1][1] = 0
        maze[height-2][width-2] = 0

        # 验证路径唯一性并确保终点可达
        if not self.has_unique_path(maze, width, height):
            # 如果没有唯一路径或终点不可达，重新生成
            return self.generate_maze(width, height)

        return maze

    def has_unique_path(self, maze, width, height):
        """验证迷宫是否有从起点到终点的路径"""
        start = (1, 1)
        end = (width-2, height-2)

        # 简单检查：确保终点可达即可
        # 递归回溯算法本身就保证了路径的唯一性
        return self.is_reachable(maze, width, height, start, end)

    def is_reachable(self, maze, width, height, start, end):
        """使用BFS检查终点是否可达"""
        from collections import deque

        queue = deque([start])
        visited = {start}

        while queue:
            x, y = queue.popleft()

            if (x, y) == end:
                return True

            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                nx, ny = x + dx, y + dy
                if (0 <= nx < width and 0 <= ny < height and
                    maze[ny][nx] == 0 and (nx, ny) not in visited):
                    visited.add((nx, ny))
                    queue.append((nx, ny))

        return False

    def generate_perfect_maze(self, width, height):
        """生成完美迷宫 - 所有通路都连通，但任意两点间只有唯一路径"""
        # 初始化迷宫（全是墙）
        maze = [[1 for _ in range(width)] for _ in range(height)]

        # 使用Kruskal算法或修改的递归回溯算法生成完美迷宫
        # 这里使用递归回溯算法，但不添加额外通路

        # 使用栈实现迭代式路径生成
        stack = [(1, 1)]  # 从起点开始
        maze[1][1] = 0  # 标记起点为通路

        while stack:
            x, y = stack[-1]

            # 随机方向
            directions = [(0, 2), (2, 0), (0, -2), (-2, 0)]
            random.shuffle(directions)

            found = False
            for dx, dy in directions:
                nx, ny = x + dx, y + dy
                if 0 < nx < width-1 and 0 < ny < height-1 and maze[ny][nx] == 1:
                    # 打通中间的墙
                    maze[y + dy//2][x + dx//2] = 0
                    maze[ny][nx] = 0  # 标记新位置为通路
                    stack.append((nx, ny))
                    found = True
                    break

            if not found:
                stack.pop()  # 回溯

        # 确保起点和终点是通路
        maze[1][1] = 0
        maze[height-2][width-2] = 0

        # 不添加任何额外通路，保持完美迷宫的性质
        # 完美迷宫的特点：任意两点间只有唯一路径

        return maze

    def generate_unique_path_maze(self, width, height):
        """生成保证从起点到终点只有唯一路径的迷宫"""
        # 使用完美迷宫算法
        return self.generate_perfect_maze(width, height)

    def generate_complex_maze(self, width, height):
        """生成复杂迷宫 - 有多条路径、岔路和死胡同"""
        # 先生成基础迷宫结构
        maze = [[1 for _ in range(width)] for _ in range(height)]

        # 使用迭代方式实现递归回溯算法生成基础路径网络
        stack = [(1, 1)]  # 从起点开始
        maze[1][1] = 0  # 标记起点为通路

        while stack:
            x, y = stack[-1]

            # 随机方向
            directions = [(0, 2), (2, 0), (0, -2), (-2, 0)]
            random.shuffle(directions)

            found = False
            for dx, dy in directions:
                nx, ny = x + dx, y + dy
                if (0 < nx < width-1 and 0 < ny < height-1 and maze[ny][nx] == 1):
                    # 打通中间的墙
                    maze[y + dy//2][x + dx//2] = 0
                    maze[ny][nx] = 0  # 标记新位置为通路
                    stack.append((nx, ny))
                    found = True
                    break

            if not found:
                stack.pop()  # 回溯

        # 添加额外的通路来创建多条路径
        self.add_extra_paths(maze, width, height)

        # 添加一些循环路径
        self.add_loops(maze, width, height)

        # 添加更多死胡同来增加难度
        self.add_dead_ends(maze, width, height)

        # 确保起点和终点可达
        self.ensure_connectivity(maze, width, height)

        return maze

    def add_extra_paths(self, maze, width, height):
        """添加额外的通路创建多条路径"""
        # 增加额外路径数量以提高复杂度
        extra_paths = max(20, (width * height) // 25)  # 增加额外路径数量到原来的两倍

        for _ in range(extra_paths):
            # 随机选择一个墙壁位置
            for attempt in range(50):  # 最多尝试50次
                x = random.randrange(1, width-1)
                y = random.randrange(1, height-1)

                if maze[y][x] == 1:  # 是墙壁
                    # 检查周围是否有至少两个通路
                    adjacent_paths = 0
                    for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                        nx, ny = x + dx, y + dy
                        if (0 <= nx < width and 0 <= ny < height and maze[ny][nx] == 0):
                            adjacent_paths += 1

                    # 如果周围有2个或更多通路，可以打通这个墙壁
                    if adjacent_paths >= 2:
                        maze[y][x] = 0
                        break

    def add_loops(self, maze, width, height):
        """添加循环路径"""
        # 增加循环数量以提高复杂度
        loop_count = max(16, (width * height) // 40)  # 增加循环数量到原来的两倍

        for _ in range(loop_count):
            # 随机选择一个位置尝试创建循环
            for attempt in range(30):
                x = random.randrange(2, width-2, 2)  # 只在奇数位置
                y = random.randrange(2, height-2, 2)

                if maze[y][x] == 0:  # 是通路
                    # 尝试在四个方向创建循环
                    directions = [(0, 2), (2, 0), (0, -2), (-2, 0)]
                    random.shuffle(directions)

                    for dx, dy in directions:
                        nx, ny = x + dx, y + dy
                        if (0 < nx < width-1 and 0 < ny < height-1 and maze[ny][nx] == 0):
                            # 检查中间的墙是否可以打通
                            mx, my = x + dx//2, y + dy//2
                            if maze[my][mx] == 1:
                                # 打通墙壁创建循环
                                maze[my][mx] = 0
                                break
                    break

    def add_dead_ends(self, maze, width, height):
        """添加更多死胡同来增加难度"""
        dead_end_count = max(30, (width * height) // 20)  # 增加死胡同数量到原来的两倍

        for _ in range(dead_end_count):
            # 随机选择一个通路位置尝试创建死胡同
            for attempt in range(50):
                x = random.randrange(1, width-1)
                y = random.randrange(1, height-1)

                if maze[y][x] == 0:  # 是通路
                    # 检查周围是否只有一个通路连接
                    connections = 0
                    for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                        nx, ny = x + dx, y + dy
                        if (0 <= nx < width and 0 <= ny < height and maze[ny][nx] == 0):
                            connections += 1

                    # 如果只有一个连接，可以尝试将其扩展为死胡同
                    if connections == 1:
                        # 随机选择一个方向扩展死胡同
                        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
                        random.shuffle(directions)
                        
                        for dx, dy in directions:
                            nx, ny = x + dx, y + dy
                            # 检查是否可以扩展为死胡同
                            if (0 < nx < width-1 and 0 < ny < height-1 and 
                                maze[ny][nx] == 0 and random.random() < 0.3):  # 30%概率创建死胡同
                                # 创建死胡同入口
                                maze[ny][nx] = 1
                                # 在死胡同内再添加一堵墙
                                nnx, nny = nx + dx, ny + dy
                                if (0 < nnx < width-1 and 0 < nny < height-1):
                                    maze[nny][nnx] = 1
                                break
                    break

    def ensure_connectivity(self, maze, width, height):
        """确保起点和终点之间有连通性"""
        start = (1, 1)
        end = (width-2, height-2)

        # 使用BFS检查连通性
        if not self.has_path(maze, start, end, width, height):
            # 如果不连通，强制创建一条路径（最短路径走墙开路）
            self.force_path(maze, start, end, width, height)

    def has_path(self, maze, start, end, width, height):
        """使用BFS检查起点和终点之间是否有路径"""
        from collections import deque

        queue = deque([start])
        visited = {start}

        while queue:
            x, y = queue.popleft()

            if (x, y) == end:
                return True

            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                nx, ny = x + dx, y + dy
                if (0 <= nx < width and 0 <= ny < height and
                    maze[ny][nx] == 0 and (nx, ny) not in visited):
                    visited.add((nx, ny))
                    queue.append((nx, ny))

        return False

    def force_path(self, maze, start, end, width, height):
        """强制创建从起点到终点的路径：采用BFS在墙上开路，使最短可达。"""
        from collections import deque
        sx, sy = start
        ex, ey = end
        # 若终点在墙中，先打通
        maze[sy][sx] = 0
        maze[ey][ex] = 0

        # 0/1 BFS：穿过墙代价为1，通路代价为0，寻最小开墙路径
        dq = deque()
        dq.append((sx, sy))
        dist = [[float('inf')] * width for _ in range(height)]
        prev = [[None] * width for _ in range(height)]
        dist[sy][sx] = 0
        while dq:
            x, y = dq.popleft()
            for dx, dy in [(0,1),(1,0),(0,-1),(-1,0)]:
                nx, ny = x+dx, y+dy
                if 0 <= nx < width and 0 <= ny < height:
                    cost = 0 if maze[ny][nx] == 0 else 1
                    nd = dist[y][x] + cost
                    if nd < dist[ny][nx]:
                        dist[ny][nx] = nd
                        prev[ny][nx] = (x, y)
                        if cost == 0:
                            dq.appendleft((nx, ny))
                        else:
                            dq.append((nx, ny))
        # 回溯并开路
        cx, cy = ex, ey
        if prev[cy][cx] is None:
            return
        while (cx, cy) != (sx, sy):
            maze[cy][cx] = 0
            cx, cy = prev[cy][cx]
        maze[sy][sx] = 0

    def generate_background_maze(self):
        """生成用于背景装饰的简化迷宫"""
        width, height = 40, 30  # 背景迷宫尺寸
        maze = [[1 for _ in range(width)] for _ in range(height)]

        # 简化的迷宫生成，创建一些通路
        for y in range(1, height-1, 2):
            for x in range(1, width-1, 2):
                maze[y][x] = 0
                # 随机打通一些墙壁
                if random.random() < 0.7:
                    if x < width-2:
                        maze[y][x+1] = 0
                if random.random() < 0.7:
                    if y < height-2:
                        maze[y+1][x] = 0

        return maze

    def generate_animated_path(self, surface_width, surface_height):
        """生成动画路径"""
        if not self.animated_path:
            # 创建一条从左上到右下的蜿蜒路径
            path = []
            x, y = 50, 100
            target_x, target_y = surface_width - 50, surface_height - 100

            while x < target_x and y < target_y:
                path.append((x, y))
                # 随机选择方向，但总体趋向目标
                if random.random() < 0.6:
                    x += random.randint(15, 25)
                else:
                    y += random.randint(10, 20)

                # 添加一些随机偏移
                x += random.randint(-5, 5)
                y += random.randint(-5, 5)

            self.animated_path = path

    def start_level(self, level):
        """开始指定等级的游戏"""
        self.current_level = level
        level_config = self.levels[level]
        width, height = level_config["size"]

        # 根据“迷宫风格”设置参数
        style = self.maze_style_index % len(self.maze_style_names)
        if style == 0:  # 标准：完美迷宫，唯一路径
            self.twistiness = 0.6
            self.loop_rate = 0.0
            self.room_rate = 0.0
        elif style == 1:  # 长走廊：更直的走廊，少量环
            self.twistiness = 0.35
            self.loop_rate = 0.05
            self.room_rate = 0.0
        elif style == 2:  # 带环：适量环路，多岔路
            self.twistiness = 0.55
            self.loop_rate = 0.15
            self.room_rate = 0.0
        elif style == 3:  # 房间：若干矩形房间+走廊
            self.twistiness = 0.5
            self.loop_rate = 0.08
            self.room_rate = 0.12

        # 生成迷宫（优先使用新生成器）
        self.maze = self.generate_advanced_maze(width, height,
                                                twistiness=self.twistiness,
                                                loop_rate=self.loop_rate,
                                                room_rate=self.room_rate,
                                                min_path_ratio=self.min_path_len_ratio)

        # 选取起点终点
        if self.random_spawn_enabled:
            # 从通路中选择两个相距较远的点
            candidates = [(x, y) for y in range(1, height-1) for x in range(1, width-1) if self.maze[y][x] == 0]
            if len(candidates) >= 2:
                start = random.choice(candidates)
                # 选与start最远的一个（以 BFS 距离估计）
                far = self._farthest_cell(self.maze, width, height, start)
                end = far if far else (width-2, height-2)
                self.player_pos = [start[0], start[1]]
                self.end_pos = [end[0], end[1]]
            else:
                self.player_pos = [1, 1]
                self.end_pos = [width-2, height-2]
        else:
            self.player_pos = [1, 1]
            self.end_pos = [width-2, height-2]

        # 统一保证起点/终点为通路，并强制连通（避免被围无法抵达）
        self.maze[self.player_pos[1]][self.player_pos[0]] = 0
        self.maze[self.end_pos[1]][self.end_pos[0]] = 0
        self.ensure_connectivity(self.maze, width, height)
        
        # 计算迷宫显示大小和偏移
        surface_width, surface_height = self.surface.get_size()
        maze_pixel_width = width * self.cell_size
        maze_pixel_height = height * self.cell_size
        
        self.maze_offset_x = (surface_width - maze_pixel_width) // 2
        self.maze_offset_y = (surface_height - maze_pixel_height) // 2 + 20  # 从+40改为+20，使迷宫向上移动20像素
        
        # 初始化视野系统
        self.init_vision_system()

        self.start_time = time.time()
        self.state = "playing"
        self.trail_positions = []
        self.particle_effects = []
        self.win_animation = 0

    def _farthest_cell(self, maze, width, height, start):
        """从 start 出发的最远通路点（BFS 距离）。"""
        from collections import deque
        sx, sy = start
        dq = deque([(sx, sy, 0)])
        vis = set([(sx, sy)])
        best = (sx, sy, 0)
        while dq:
            x, y, d = dq.popleft()
            if d > best[2]:
                best = (x, y, d)
            for dx, dy in [(0,1),(1,0),(0,-1),(-1,0)]:
                nx, ny = x+dx, y+dy
                if 0 <= nx < width and 0 <= ny < height and maze[ny][nx] == 0 and (nx,ny) not in vis:
                    vis.add((nx,ny))
                    dq.append((nx,ny,d+1))
        return (best[0], best[1]) if best else None

    def generate_advanced_maze(self, width, height, twistiness=0.6, loop_rate=0.1, room_rate=0.0, min_path_ratio=0.7):
        """综合型生成器：房间+Growing-Tree（长走廊偏好）+环路+最短路校验。"""
        attempts = 0
        best = None
        best_len = -1
        while attempts < 6:
            attempts += 1
            # 初始化全墙
            maze = [[1 for _ in range(width)] for _ in range(height)]
            # 可选：先挖房间
            if room_rate > 0:
                self._carve_rooms(maze, width, height, room_rate)
            # 用 Growing-Tree 填充剩余区域（生成连通树）
            self._growing_tree_carve(maze, width, height, bias_straight=max(0.0, min(1.0, 1.0 - twistiness)))
            # 加环
            if loop_rate > 0:
                self._add_loops_ratio(maze, width, height, loop_rate)
            # 起终点
            maze[1][1] = 0
            maze[height-2][width-2] = 0
            # 路径长度评估
            plen = self._shortest_path_len(maze, (1,1), (width-2, height-2))
            if plen is None:
                continue
            best = maze
            best_len = plen
            if plen >= int((width + height) * min_path_ratio):
                break
        return best if best is not None else self.generate_unique_path_maze(width, height)

    def _neighbors_two_step(self, x, y, width, height):
        for dx, dy in [(0,2),(2,0),(0,-2),(-2,0)]:
            nx, ny = x + dx, y + dy
            if 0 < nx < width-1 and 0 < ny < height-1:
                yield nx, ny, dx, dy

    def _growing_tree_carve(self, maze, width, height, bias_straight=0.7):
        """Growing-Tree 算法，偏好直行形成长走廊。bias_straight 越高越直。"""
        start_x, start_y = 1, 1
        maze[start_y][start_x] = 0
        cells = [(start_x, start_y, 0, 0)]  # (x,y,last_dx,last_dy)
        while cells:
            # 以一定概率选最近加入的（形成蛇形），否则随机（增多分支）
            if random.random() < 0.7:
                idx = len(cells) - 1
            else:
                idx = random.randrange(len(cells))
            x, y, ldx, ldy = cells[idx]

            # 候选方向，优先尝试与上一步同向
            dirs = [(0,2),(2,0),(0,-2),(-2,0)]
            if (ldx, ldy) in dirs and random.random() < bias_straight:
                dirs.remove((ldx, ldy))
                dirs = [(ldx, ldy)] + dirs
            random.shuffle(dirs)

            carved = False
            for dx, dy in dirs:
                nx, ny = x + dx, y + dy
                if 0 < nx < width-1 and 0 < ny < height-1 and maze[ny][nx] == 1:
                    # 打通中间墙
                    maze[y + dy//2][x + dx//2] = 0
                    maze[ny][nx] = 0
                    cells.append((nx, ny, dx, dy))
                    carved = True
                    break
            if not carved:
                cells.pop(idx)

    def _carve_rooms(self, maze, width, height, room_rate=0.1):
        """随机开凿若干矩形房间（奇数对齐）。"""
        area = width * height
        target_area = int(area * min(0.25, max(0.02, room_rate)))
        carved = 0
        tries = 0
        while carved < target_area and tries < 200:
            tries += 1
            rw = random.randrange(5, 11, 2)
            rh = random.randrange(5, 11, 2)
            x = random.randrange(1, width - rw - 1, 2)
            y = random.randrange(1, height - rh - 1, 2)
            # 简单避免与已有通路过度重叠
            overlap = False
            for yy in range(y, y+rh):
                for xx in range(x, x+rw):
                    if maze[yy][xx] == 0:
                        overlap = True
                        break
                if overlap:
                    break
            if overlap:
                continue
            for yy in range(y, y+rh):
                for xx in range(x, x+rw):
                    maze[yy][xx] = 0
            carved += rw * rh

    def _add_loops_ratio(self, maze, width, height, loop_rate=0.1):
        """按比例随机打通墙壁形成环路。"""
        walls = []
        for y in range(1, height-1):
            for x in range(1, width-1):
                if maze[y][x] == 1:
                    # 仅考虑两侧相邻为通路的内墙
                    neighbors = 0
                    if maze[y-1][x] == 0: neighbors += 1
                    if maze[y+1][x] == 0: neighbors += 1
                    if maze[y][x-1] == 0: neighbors += 1
                    if maze[y][x+1] == 0: neighbors += 1
                    if neighbors >= 2:
                        walls.append((x, y))
        random.shuffle(walls)
        to_open = int(len(walls) * min(0.35, max(0.0, loop_rate)))
        for i in range(to_open):
            x, y = walls[i]
            maze[y][x] = 0

    def _shortest_path_len(self, maze, start, end):
        from collections import deque
        w, h = len(maze[0]), len(maze)
        sx, sy = start
        ex, ey = end
        if not (0 <= sx < w and 0 <= sy < h and 0 <= ex < w and 0 <= ey < h):
            return None
        dq = deque([(sx, sy, 0)])
        vis = set([(sx, sy)])
        while dq:
            x, y, d = dq.popleft()
            if (x, y) == (ex, ey):
                return d
            for dx, dy in [(0,1),(1,0),(0,-1),(-1,0)]:
                nx, ny = x+dx, y+dy
                if 0 <= nx < w and 0 <= ny < h and maze[ny][nx] == 0 and (nx,ny) not in vis:
                    vis.add((nx,ny))
                    dq.append((nx,ny,d+1))
        return None

    def update(self):
        """更新游戏状态"""
        current_time = pygame.time.get_ticks()

        if self.state == "playing":
            self.game_time = time.time() - self.start_time
            time_limit = self.levels[self.current_level]["time_limit"]

            if self.game_time >= time_limit:
                self.state = "lose"

            # 检查是否到达终点
            if self.player_pos == self.end_pos:
                self.state = "win"
                self.win_animation = 0

            # 处理连续移动
            self.handle_continuous_movement(current_time)

        # 更新动画
        self.animation_time += 0.1
        if self.state == "win":
            self.win_animation += 0.15

        # 更新粒子效果
        self.particle_effects = [p for p in self.particle_effects if p['life'] > 0]
        for particle in self.particle_effects:
            particle['x'] += particle['vx']
            particle['y'] += particle['vy']
            particle['life'] -= 1
            particle['vy'] += 0.1  # 重力

    def handle_continuous_movement(self, current_time):
        """处理连续移动"""
        if current_time - self.last_move_time < self.move_delay:
            return

        keys = pygame.key.get_pressed()
        moved = False

        # 检查各个方向键
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            if self.should_move(pygame.K_UP, current_time):
                self.move_player(0, -1)
                moved = True
        elif keys[pygame.K_s] or keys[pygame.K_DOWN]:
            if self.should_move(pygame.K_DOWN, current_time):
                self.move_player(0, 1)
                moved = True
        elif keys[pygame.K_a] or keys[pygame.K_LEFT]:
            if self.should_move(pygame.K_LEFT, current_time):
                self.move_player(-1, 0)
                moved = True
        elif keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            if self.should_move(pygame.K_RIGHT, current_time):
                self.move_player(1, 0)
                moved = True

        if moved:
            self.last_move_time = current_time

    def should_move(self, key, current_time):
        """判断是否应该移动（处理首次移动延迟）"""
        if key not in self.key_pressed_time:
            return False

        time_since_press = current_time - self.key_pressed_time[key]

        # 首次移动需要更长的延迟
        if time_since_press < self.first_move_delay:
            return False

        return True

    def move_player(self, dx, dy):
        """移动玩家"""
        if self.state != "playing":
            return
            
        new_x = self.player_pos[0] + dx
        new_y = self.player_pos[1] + dy
        
        # 检查边界和墙壁
        if (0 <= new_x < len(self.maze[0]) and 
            0 <= new_y < len(self.maze) and 
            self.maze[new_y][new_x] == 0):
            
            # 添加轨迹
            self.trail_positions.append(self.player_pos.copy())
            if len(self.trail_positions) > 20:
                self.trail_positions.pop(0)
            
            self.player_pos = [new_x, new_y]
            
            # 添加移动粒子效果
            for _ in range(3):
                self.particle_effects.append({
                    'x': self.maze_offset_x + new_x * self.cell_size + self.cell_size//2,
                    'y': self.maze_offset_y + new_y * self.cell_size + self.cell_size//2,
                    'vx': random.uniform(-2, 2),
                    'vy': random.uniform(-3, -1),
                    'life': 20,
                    'color': (100, 200, 255)
                })

            # 更新视野
            if self.vision_enabled:
                self.update_vision()

    def init_vision_system(self):
        """初始化视野系统"""
        if not self.vision_enabled:
            return

        # 清空已探索区域
        self.explored_cells = set()

        # 添加起始位置和终点到已探索区域
        self.explored_cells.add(tuple(self.player_pos))
        self.explored_cells.add(tuple(self.end_pos))

        # 初始化玩家周围的视野
        self.update_vision()

        # 创建迷雾遮罩层
        maze_width = len(self.maze[0]) * self.cell_size
        maze_height = len(self.maze) * self.cell_size
        self.fog_surface = pygame.Surface((maze_width, maze_height), pygame.SRCALPHA)

    def update_vision(self):
        """更新玩家视野"""
        if not self.vision_enabled:
            return

        player_x, player_y = self.player_pos
        current_explored = set()

        # 添加玩家周围的格子到当前视野区域 - 使用更严格的视野计算
        for dy in range(-int(self.vision_radius), int(self.vision_radius) + 1):
            for dx in range(-int(self.vision_radius), int(self.vision_radius) + 1):
                # 计算距离，使用更严格的圆形视野
                distance = math.sqrt(dx*dx + dy*dy)
                if distance <= self.vision_radius:
                    new_x = player_x + dx
                    new_y = player_y + dy

                    # 检查边界
                    if (0 <= new_x < len(self.maze[0]) and
                        0 <= new_y < len(self.maze)):
                        current_explored.add((new_x, new_y))

        # 更新视野区域为当前视野（之前的区域会变黑）
        self.explored_cells = current_explored
        # 添加终点到视野区域
        self.explored_cells.add(tuple(self.end_pos))

    def is_cell_visible(self, x, y):
        """检查格子是否可见"""
        if not self.vision_enabled:
            return True

        # 终点始终可见
        if (x, y) == tuple(self.end_pos):
            return True

        # 检查是否在当前视野区域
        return (x, y) in self.explored_cells

    def draw_level_select(self):
        """绘制等级选择界面"""
        surface_width, surface_height = self.surface.get_size()

        # 更新动画
        self.level_select_animation += 0.05
        self.path_animation += 0.1

        # 绘制迷宫风格背景
        self.draw_maze_background(surface_width, surface_height)

        # 更新和绘制浮动粒子（暂时禁用以避免错误）
        # self.update_floating_particles(surface_width, surface_height)

        # 动态标题
        title_font = pygame.font.Font(FONT_NAME, 52)
        title_offset = math.sin(self.level_select_animation * 1.5) * 3
        title_text = title_font.render("🎯 走迷宫挑战 🎯", True, (255, 255, 255))
        title_rect = title_text.get_rect(center=(surface_width//2, 70 + title_offset))

        # 多层标题阴影
        for i in range(3):
            shadow_alpha = 100 - i * 30
            shadow_offset = (i + 1) * 2
            shadow_surface = pygame.Surface(title_text.get_size(), pygame.SRCALPHA)
            shadow_text = title_font.render("🎯 走迷宫挑战 🎯", True, (0, 0, 0, shadow_alpha))
            shadow_rect = shadow_text.get_rect(center=(surface_width//2 + shadow_offset, 73 + title_offset + shadow_offset))
            self.surface.blit(shadow_text, shadow_rect)

        self.surface.blit(title_text, title_rect)

        # 副标题
        subtitle_font = pygame.font.Font(FONT_NAME, 20)
        subtitle_text = subtitle_font.render("选择你的挑战等级", True, (200, 200, 255))
        subtitle_rect = subtitle_text.get_rect(center=(surface_width//2, 110))
        self.surface.blit(subtitle_text, subtitle_rect)
        
        # 等级按钮 - 改进布局
        button_width = 220
        button_height = 100
        cols = 3
        gap_x = 30
        gap_y = 40
        total_width = cols * button_width + (cols - 1) * gap_x
        start_x = (surface_width - total_width) // 2
        start_y = 160

        for i, (level, config) in enumerate(self.levels.items()):
            row = i // cols
            col = i % cols
            x = start_x + col * (button_width + gap_x)
            y = start_y + row * (button_height + gap_y)

            # 按钮动画
            if level not in self.button_animations:
                self.button_animations[level] = {
                    'hover_scale': 1.0,
                    'glow_intensity': 0,
                    'float_offset': 0
                }

            anim = self.button_animations[level]
            mouse_pos = pygame.mouse.get_pos()
            button_rect = pygame.Rect(x, y, button_width, button_height)
            is_hover = button_rect.collidepoint(mouse_pos)

            # 更新动画
            target_scale = 1.05 if is_hover else 1.0
            anim['hover_scale'] += (target_scale - anim['hover_scale']) * 0.1

            target_glow = 150 if is_hover else 0
            anim['glow_intensity'] += (target_glow - anim['glow_intensity']) * 0.1

            anim['float_offset'] = math.sin(self.level_select_animation * 2 + level * 0.5) * 2

            # 计算实际绘制位置和大小
            scaled_width = int(button_width * anim['hover_scale'])
            scaled_height = int(button_height * anim['hover_scale'])
            scaled_x = x + (button_width - scaled_width) // 2
            scaled_y = y + (button_height - scaled_height) // 2 + anim['float_offset']
            scaled_rect = pygame.Rect(scaled_x, scaled_y, scaled_width, scaled_height)

            # 发光效果
            if anim['glow_intensity'] > 5:
                glow_size = int(anim['glow_intensity'] * 0.3)
                glow_surface = pygame.Surface((scaled_width + glow_size*2, scaled_height + glow_size*2), pygame.SRCALPHA)
                glow_alpha = int(anim['glow_intensity'])
                pygame.draw.rect(glow_surface, (*config["color"], glow_alpha),
                               (glow_size, glow_size, scaled_width, scaled_height), border_radius=20)
                self.surface.blit(glow_surface, (scaled_x - glow_size, scaled_y - glow_size))

            # 按钮主体 - 渐变效果
            base_color = config["color"]
            highlight_color = tuple(min(255, c + 40) for c in base_color)

            # 绘制渐变按钮
            for i in range(scaled_height):
                blend = i / scaled_height
                color = tuple(int(base_color[j] * (1-blend) + highlight_color[j] * blend) for j in range(3))
                pygame.draw.line(self.surface, color,
                               (scaled_x, scaled_y + i), (scaled_x + scaled_width, scaled_y + i))

            # 按钮边框
            border_color = (255, 255, 255) if not is_hover else (255, 255, 100)
            pygame.draw.rect(self.surface, border_color, scaled_rect, 4, border_radius=15)

            # 难度图标
            icon_size = 24
            icon_x = scaled_x + 20
            icon_y = scaled_y + 15
            self.draw_difficulty_icon(level, icon_x, icon_y, icon_size, config["color"])

            # 等级信息 - 改进排版
            level_font = pygame.font.Font(FONT_NAME, 28)
            name_font = pygame.font.Font(FONT_NAME, 22)
            info_font = pygame.font.Font(FONT_NAME, 16)

            level_text = level_font.render(f"等级 {level}", True, (255, 255, 255))
            name_text = name_font.render(config["name"], True, (255, 255, 100))
            size_text = info_font.render(f"迷宫: {config['size'][0]}×{config['size'][1]}", True, (200, 200, 255))
            time_text = info_font.render(f"时限: {config['time_limit']}秒", True, (200, 255, 200))

            # 文字位置
            text_x = scaled_x + 55
            self.surface.blit(level_text, (text_x, scaled_y + 10))
            self.surface.blit(name_text, (text_x, scaled_y + 35))
            self.surface.blit(size_text, (text_x, scaled_y + 60))
            self.surface.blit(time_text, (text_x, scaled_y + 78))

            # 存储按钮区域用于点击检测
            setattr(self, f'level_{level}_rect', button_rect)
        
        # 完美迷宫模式切换按钮
        mode_rect = pygame.Rect(surface_width - 250, surface_height - 130, 180, 50)
        mode_color = (100, 200, 100) if self.unique_path_mode else (200, 100, 100)
        pygame.draw.rect(self.surface, mode_color, mode_rect, border_radius=8)
        pygame.draw.rect(self.surface, (255, 255, 255), mode_rect, 2, border_radius=8)
        mode_font = pygame.font.Font(FONT_NAME, 18)
        mode_text = "完美迷宫: 开" if self.unique_path_mode else "完美迷宫: 关"
        mode_text_surface = mode_font.render(mode_text, True, (255, 255, 255))
        mode_text_rect = mode_text_surface.get_rect(center=mode_rect.center)
        self.surface.blit(mode_text_surface, mode_text_rect)
        self.mode_rect = mode_rect

        # 视野限制模式切换按钮
        vision_rect = pygame.Rect(surface_width - 250, surface_height - 70, 180, 50)
        vision_color = (150, 100, 200) if self.vision_enabled else (100, 100, 100)
        pygame.draw.rect(self.surface, vision_color, vision_rect, border_radius=8)
        pygame.draw.rect(self.surface, (255, 255, 255), vision_rect, 2, border_radius=8)
        vision_font = pygame.font.Font(FONT_NAME, 18)
        vision_text = "视野限制: 开" if self.vision_enabled else "视野限制: 关"
        vision_text_surface = vision_font.render(vision_text, True, (255, 255, 255))
        vision_text_rect = vision_text_surface.get_rect(center=vision_rect.center)
        self.surface.blit(vision_text_surface, vision_text_rect)
        self.vision_rect = vision_rect

        # 迷宫风格切换按钮（移动到右侧，与其他按钮同区）
        style_rect = pygame.Rect(surface_width - 250, surface_height - 190, 180, 50)
        pygame.draw.rect(self.surface, (80, 140, 220), style_rect, border_radius=8)
        pygame.draw.rect(self.surface, (255, 255, 255), style_rect, 2, border_radius=8)
        style_font = pygame.font.Font(FONT_NAME, 18)
        style_name = self.maze_style_names[self.maze_style_index % len(self.maze_style_names)]
        style_text_surface = style_font.render(f"迷宫风格: {style_name}", True, (255, 255, 255))
        style_text_rect = style_text_surface.get_rect(center=style_rect.center)
        self.surface.blit(style_text_surface, style_text_rect)
        self.style_rect = style_rect

        # 随机起终点开关按钮（位于风格按钮上方）
        rand_rect = pygame.Rect(surface_width - 250, surface_height - 250, 180, 50)
        rand_color = (100, 200, 160) if self.random_spawn_enabled else (120, 120, 120)
        pygame.draw.rect(self.surface, rand_color, rand_rect, border_radius=8)
        pygame.draw.rect(self.surface, (255, 255, 255), rand_rect, 2, border_radius=8)
        rand_font = pygame.font.Font(FONT_NAME, 18)
        rand_text = "随机起终点: 开" if self.random_spawn_enabled else "随机起终点: 关"
        rand_text_surface = rand_font.render(rand_text, True, (255, 255, 255))
        rand_text_rect = rand_text_surface.get_rect(center=rand_rect.center)
        self.surface.blit(rand_text_surface, rand_text_rect)
        self.random_rect = rand_rect

        # 添加说明文字
        if self.vision_enabled:
            hint_text = "视野限制模式：复杂迷宫，多条路径"
        elif self.unique_path_mode:
            hint_text = "完美迷宫：任意两点间只有唯一路径"
        else:
            hint_text = "普通迷宫：可能存在多条路径和环路"
        hint_font = pygame.font.Font(FONT_NAME, 14)
        hint_surface = hint_font.render(hint_text, True, (200, 200, 200))
        hint_rect = hint_surface.get_rect(center=(surface_width - 160, surface_height - 25))
        self.surface.blit(hint_surface, hint_rect)

        # 返回按钮
        back_rect = pygame.Rect(50, surface_height - 80, 100, 50)
        pygame.draw.rect(self.surface, (100, 100, 100), back_rect, border_radius=8)
        pygame.draw.rect(self.surface, (255, 255, 255), back_rect, 2, border_radius=8)
        back_font = pygame.font.Font(FONT_NAME, 24)
        back_text = back_font.render("返回", True, (255, 255, 255))
        back_text_rect = back_text.get_rect(center=back_rect.center)
        self.surface.blit(back_text, back_text_rect)
        self.back_rect = back_rect

    def draw_maze_background(self, surface_width, surface_height):
        """绘制迷宫风格的背景"""
        # 创建渐变背景
        gradient_surface = pygame.Surface((surface_width, surface_height), pygame.SRCALPHA)
        for y in range(surface_height):
            # 顶部深蓝渐变到底部紫色
            r = int(10 + (y / surface_height) * 20)
            g = int(15 + (y / surface_height) * 15)
            b = int(40 + (y / surface_height) * 60)
            pygame.draw.line(gradient_surface, (r, g, b), (0, y), (surface_width, y))
        self.surface.blit(gradient_surface, (0, 0))

        # 绘制星空效果
        for _ in range(200):
            x = random.randint(0, surface_width)
            y = random.randint(0, surface_height)
            size = random.uniform(1, 3)
            # 闪烁效果
            alpha = random.randint(50, 200) + int(50 * math.sin(self.level_select_animation + x * 0.01 + y * 0.01))
            alpha = max(0, min(255, alpha))
            star_surface = pygame.Surface((size*2, size*2), pygame.SRCALPHA)
            pygame.draw.circle(star_surface, (255, 255, 255, alpha), (size, size), size)
            self.surface.blit(star_surface, (x - size, y - size))

        # 绘制背景迷宫图案
        cell_size = 20

        for y in range(len(self.background_maze)):
            for x in range(len(self.background_maze[0])):
                screen_x = x * cell_size
                screen_y = y * cell_size

                if screen_x >= surface_width or screen_y >= surface_height:
                    continue

                if self.background_maze[y][x] == 1:  # 墙壁
                    # 添加动态效果
                    wave_effect = math.sin(self.level_select_animation + x * 0.1 + y * 0.1) * 15
                    # 改进颜色方案：蓝紫色调
                    wall_color = (
                        max(0, min(255, 60 + wave_effect)),
                        max(0, min(255, 70 + wave_effect * 0.5)),
                        max(0, min(255, 120 + wave_effect * 1.5))
                    )
                    # 绘制墙壁主体
                    pygame.draw.rect(self.surface, wall_color,
                                   (screen_x, screen_y, cell_size, cell_size))

                    # 添加边框效果
                    border_color = (
                        max(0, min(255, 100 + wave_effect)),
                        max(0, min(255, 120 + wave_effect * 0.5)),
                        max(0, min(255, 180 + wave_effect * 1.5))
                    )
                    pygame.draw.rect(self.surface, border_color,
                                   (screen_x, screen_y, cell_size, cell_size), 1)

                else:  # 通路
                    # 为通路添加微弱的发光效果
                    path_color = (
                        20 + int(10 * math.sin(self.level_select_animation + x * 0.2 + y * 0.2)),
                        30 + int(10 * math.sin(self.level_select_animation + x * 0.2 + y * 0.2 + 1)),
                        50 + int(15 * math.sin(self.level_select_animation + x * 0.2 + y * 0.2 + 2))
                    )
                    pygame.draw.rect(self.surface, path_color,
                                   (screen_x, screen_y, cell_size, cell_size))

        # 绘制动态路径效果
        self.draw_animated_path(surface_width, surface_height)

        # 添加迷宫主题的装饰元素
        self.draw_maze_decorations(surface_width, surface_height)

    def draw_animated_path(self, surface_width, surface_height):
        """绘制动画路径"""
        self.generate_animated_path(surface_width, surface_height)

        if len(self.animated_path) < 2:
            return

        # 绘制发光路径
        path_progress = (math.sin(self.path_animation) + 1) / 2
        visible_length = int(len(self.animated_path) * 0.4)
        start_index = int((len(self.animated_path) - visible_length) * path_progress)

        for i in range(start_index, min(start_index + visible_length, len(self.animated_path) - 1)):
            if i < 0 or i >= len(self.animated_path) - 1:
                continue

            start_pos = self.animated_path[i]
            end_pos = self.animated_path[i + 1]

            # 计算路径的透明度和颜色
            progress = (i - start_index) / visible_length if visible_length > 0 else 0
            alpha = int(255 * (1 - progress) * 0.9)

            # 路径颜色：从蓝紫色过渡到金黄色
            hue = 270 - int(progress * 210)  # 从紫色(270)到黄色(60)
            saturation = 100
            value = 100

            # HSV到RGB转换
            c = value / 100 * saturation / 100
            x = c * (1 - abs((hue / 60) % 2 - 1))
            m = value / 100 - c

            if 0 <= hue < 60:
                r, g, b = c, x, 0
            elif 60 <= hue < 120:
                r, g, b = x, c, 0
            elif 120 <= hue < 180:
                r, g, b = 0, c, x
            elif 180 <= hue < 240:
                r, g, b = 0, x, c
            elif 240 <= hue < 300:
                r, g, b = x, 0, c
            else:
                r, g, b = c, 0, x

            r = int((r + m) * 255)
            g = int((g + m) * 255)
            b = int((b + m) * 255)

            # 绘制发光效果
            glow_radius = 6 + int(4 * (1 - progress))
            glow_surface = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow_surface, (r, g, b, int(alpha * 0.3)), (glow_radius, glow_radius), glow_radius)

            # 绘制路径线条
            if start_pos != end_pos:
                # 绘制主线
                pygame.draw.line(self.surface, (r, g, b, alpha), start_pos, end_pos, 3)
                # 添加外发光
                pygame.draw.line(self.surface, (255, 255, 255, int(alpha * 0.5)), start_pos, end_pos, 1)

                # 在路径端点添加粒子效果
                if random.random() < 0.5:
                    particle_size = 2 + int(3 * (1 - progress))
                    particle_surface = pygame.Surface((particle_size * 2, particle_size * 2), pygame.SRCALPHA)
                    pygame.draw.circle(particle_surface, (r, g, b, alpha), (particle_size, particle_size), particle_size)
                    self.surface.blit(particle_surface, (end_pos[0] - particle_size, end_pos[1] - particle_size))

    def draw_maze_decorations(self, surface_width, surface_height):
        """绘制迷宫主题装饰"""
        # 绘制角落的迷宫图案
        corner_size = 60

        # 左上角
        self.draw_mini_maze(20, 20, corner_size, corner_size)

        # 右上角
        self.draw_mini_maze(surface_width - corner_size - 20, 20, corner_size, corner_size)

        # 左下角
        self.draw_mini_maze(20, surface_height - corner_size - 20, corner_size, corner_size)

        # 右下角
        self.draw_mini_maze(surface_width - corner_size - 20, surface_height - corner_size - 20,
                           corner_size, corner_size)

        # 绘制边框装饰
        border_color = (100, 150, 200, 100)
        border_width = 3

        # 顶部和底部边框
        for i in range(0, surface_width, 40):
            x = i
            # 顶部
            pygame.draw.rect(self.surface, (60, 80, 120), (x, 0, 20, border_width))
            # 底部
            pygame.draw.rect(self.surface, (60, 80, 120), (x, surface_height - border_width, 20, border_width))

        # 左侧和右侧边框
        for i in range(0, surface_height, 40):
            y = i
            # 左侧
            pygame.draw.rect(self.surface, (60, 80, 120), (0, y, border_width, 20))
            # 右侧
            pygame.draw.rect(self.surface, (60, 80, 120), (surface_width - border_width, y, border_width, 20))

    def draw_mini_maze(self, x, y, width, height):
        """绘制小型迷宫装饰"""
        cell_size = 6
        cols = width // cell_size
        rows = height // cell_size

        # 简单的迷宫图案
        for row in range(rows):
            for col in range(cols):
                cell_x = x + col * cell_size
                cell_y = y + row * cell_size

                # 创建简单的迷宫图案
                is_wall = (row + col) % 3 == 0 or (row % 2 == 0 and col % 4 == 0)

                if is_wall:
                    # 添加动态颜色变化
                    wave = math.sin(self.level_select_animation + col * 0.2 + row * 0.2) * 20
                    wall_color = (
                        max(0, min(255, 80 + wave)),
                        max(0, min(255, 120 + wave * 0.8)),
                        max(0, min(255, 160 + wave * 1.2))
                    )
                    pygame.draw.rect(self.surface, wall_color,
                                   (cell_x, cell_y, cell_size, cell_size))
                else:
                    # 通路
                    path_color = (20, 30, 50)
                    pygame.draw.rect(self.surface, path_color,
                                   (cell_x, cell_y, cell_size, cell_size))

    def update_floating_particles(self, surface_width, surface_height):
        """更新浮动粒子效果"""
        # 添加新粒子
        if len(self.floating_particles) < 20 and random.random() < 0.1:
            self.floating_particles.append({
                'x': random.randint(0, surface_width),
                'y': surface_height + 10,
                'vx': random.uniform(-0.5, 0.5),
                'vy': random.uniform(-2, -0.5),
                'life': random.randint(300, 500),
                'max_life': random.randint(300, 500),
                'size': random.randint(2, 5),
                'color': random.choice([(100, 150, 255), (150, 100, 255), (255, 150, 100)])
            })

        # 更新和绘制粒子
        for particle in self.floating_particles[:]:
            particle['x'] += particle['vx']
            particle['y'] += particle['vy']
            particle['life'] -= 1

            if particle['life'] <= 0 or particle['y'] < -10:
                self.floating_particles.remove(particle)
                continue

            # 绘制粒子
            alpha_ratio = particle['life'] / particle['max_life']
            # 根据生命周期调整颜色亮度
            color = tuple(int(c * alpha_ratio) for c in particle['color'])
            pygame.draw.circle(self.surface, color,
                             (int(particle['x']), int(particle['y'])), particle['size'])

    def draw_difficulty_icon(self, level, x, y, size, color):
        """绘制难度图标"""
        if level == 1:  # 新手 - 笑脸
            pygame.draw.circle(self.surface, (255, 255, 100), (x, y), size//2)
            pygame.draw.circle(self.surface, (0, 0, 0), (x-6, y-4), 2)
            pygame.draw.circle(self.surface, (0, 0, 0), (x+6, y-4), 2)
            pygame.draw.arc(self.surface, (0, 0, 0), (x-8, y-2, 16, 12), 0.5, 2.6, 2)
        elif level == 2:  # 初级 - 一颗星
            self.draw_star(x, y, size//2, (255, 255, 100))
        elif level == 3:  # 中级 - 两颗星
            self.draw_star(x-6, y, size//3, (255, 200, 100))
            self.draw_star(x+6, y, size//3, (255, 200, 100))
        elif level == 4:  # 高级 - 三颗星
            self.draw_star(x-8, y, size//4, (255, 150, 100))
            self.draw_star(x, y, size//4, (255, 150, 100))
            self.draw_star(x+8, y, size//4, (255, 150, 100))
        elif level == 5:  # 专家 - 钻石
            points = []
            for i in range(4):
                angle = math.radians(i * 90 + 45)
                px = x + (size//2) * math.cos(angle)
                py = y + (size//2) * math.sin(angle)
                points.append((px, py))
            pygame.draw.polygon(self.surface, (200, 100, 255), points)
        elif level == 6:  # 大师 - 皇冠
            # 皇冠底部
            pygame.draw.rect(self.surface, (255, 215, 0), (x-size//2, y+size//4, size, size//4))
            # 皇冠尖峰
            for i in range(3):
                peak_x = x - size//3 + i * size//3
                peak_y = y - size//4
                pygame.draw.polygon(self.surface, (255, 215, 0),
                                  [(peak_x-3, y+size//4), (peak_x+3, y+size//4), (peak_x, peak_y)])

    def draw_star(self, x, y, radius, color):
        """绘制星星"""
        points = []
        for i in range(10):
            angle = math.radians(i * 36 - 90)
            r = radius if i % 2 == 0 else radius * 0.5
            px = x + r * math.cos(angle)
            py = y + r * math.sin(angle)
            points.append((px, py))
        pygame.draw.polygon(self.surface, color, points)

    def draw_playing(self):
        """绘制游戏进行界面"""
        surface_width, surface_height = self.surface.get_size()

        # 深色背景
        self.surface.fill((25, 25, 35))

        # 绘制迷宫（带视野限制）
        for y in range(len(self.maze)):
            for x in range(len(self.maze[0])):
                cell_x = self.maze_offset_x + x * self.cell_size
                cell_y = self.maze_offset_y + y * self.cell_size

                # 检查是否在视野范围内
                is_visible = self.is_cell_visible(x, y)

                if self.maze[y][x] == 1:  # 墙壁
                    if is_visible:
                        # 可见的墙壁 - 正常颜色
                        wall_color = (60 + (x+y) % 40, 60 + (x+y) % 40, 80 + (x+y) % 40)
                        pygame.draw.rect(self.surface, wall_color,
                                       (cell_x, cell_y, self.cell_size, self.cell_size))
                        # 墙壁边框
                        pygame.draw.rect(self.surface, (40, 40, 50),
                                       (cell_x, cell_y, self.cell_size, self.cell_size), 1)
                    else:
                        # 不可见的墙壁 - 黑色迷雾
                        pygame.draw.rect(self.surface, (5, 5, 5),
                                       (cell_x, cell_y, self.cell_size, self.cell_size))
                else:  # 通路
                    if is_visible:
                        # 可见的通路 - 正常颜色
                        path_color = (15, 15, 25)
                        pygame.draw.rect(self.surface, path_color,
                                       (cell_x, cell_y, self.cell_size, self.cell_size))
                    else:
                        # 不可见的通路 - 黑色迷雾
                        pygame.draw.rect(self.surface, (5, 5, 5),
                                       (cell_x, cell_y, self.cell_size, self.cell_size))

        # 绘制轨迹（只在可见区域）
        for i, pos in enumerate(self.trail_positions):
            if self.is_cell_visible(pos[0], pos[1]):
                alpha = int(50 * (i / len(self.trail_positions)))
                trail_surface = pygame.Surface((self.cell_size-2, self.cell_size-2), pygame.SRCALPHA)
                pygame.draw.rect(trail_surface, (100, 200, 255, alpha),
                               (0, 0, self.cell_size-2, self.cell_size-2), border_radius=3)
                self.surface.blit(trail_surface,
                                (self.maze_offset_x + pos[0] * self.cell_size + 1,
                                 self.maze_offset_y + pos[1] * self.cell_size + 1))

        # 绘制终点（发光效果）
        end_x = self.maze_offset_x + self.end_pos[0] * self.cell_size
        end_y = self.maze_offset_y + self.end_pos[1] * self.cell_size

        # 终点光晕
        glow_radius = int(self.cell_size + 5 * math.sin(self.animation_time))
        glow_surface = pygame.Surface((glow_radius*2, glow_radius*2), pygame.SRCALPHA)
        pygame.draw.circle(glow_surface, (255, 215, 0, 100),
                         (glow_radius, glow_radius), glow_radius)
        self.surface.blit(glow_surface,
                        (end_x + self.cell_size//2 - glow_radius,
                         end_y + self.cell_size//2 - glow_radius))

        # 终点主体
        pygame.draw.rect(self.surface, (255, 215, 0),
                       (end_x + 2, end_y + 2, self.cell_size - 4, self.cell_size - 4),
                       border_radius=4)
        pygame.draw.rect(self.surface, (255, 255, 255),
                       (end_x + 2, end_y + 2, self.cell_size - 4, self.cell_size - 4),
                       2, border_radius=4)

        # 绘制玩家（动画效果）
        player_x = self.maze_offset_x + self.player_pos[0] * self.cell_size
        player_y = self.maze_offset_y + self.player_pos[1] * self.cell_size

        # 玩家光晕
        player_glow = int(3 * math.sin(self.animation_time * 2))
        player_surface = pygame.Surface((self.cell_size + player_glow*2, self.cell_size + player_glow*2), pygame.SRCALPHA)
        pygame.draw.circle(player_surface, (100, 255, 100, 150),
                         (self.cell_size//2 + player_glow, self.cell_size//2 + player_glow),
                         self.cell_size//2 + player_glow)
        self.surface.blit(player_surface,
                        (player_x - player_glow, player_y - player_glow))

        # 玩家主体
        pygame.draw.circle(self.surface, (100, 255, 100),
                         (player_x + self.cell_size//2, player_y + self.cell_size//2),
                         self.cell_size//2 - 2)
        pygame.draw.circle(self.surface, (255, 255, 255),
                         (player_x + self.cell_size//2, player_y + self.cell_size//2),
                         self.cell_size//2 - 2, 2)

        # 绘制粒子效果
        for particle in self.particle_effects:
            alpha = int(255 * (particle['life'] / 20))
            particle_surface = pygame.Surface((6, 6), pygame.SRCALPHA)
            pygame.draw.circle(particle_surface, (*particle['color'], alpha), (3, 3), 3)
            self.surface.blit(particle_surface, (particle['x']-3, particle['y']-3))

        # 绘制UI信息（在视野限制开启时，顶部半透明高度更小且更透明，已在 draw_game_ui 调整）
        self.draw_game_ui()

    def draw_game_ui(self):
        """绘制游戏UI信息"""
        surface_width, surface_height = self.surface.get_size()
        level_config = self.levels[self.current_level]

        # 顶部信息栏：在视野限制时自动隐藏（高度从64缓动到24），鼠标或按键活动时恢复
        now_ticks = pygame.time.get_ticks()
        show_full = not self.vision_enabled or not self.ui_auto_hide_enabled
        # 若有输入活动则记录时间
        keys = pygame.key.get_pressed()
        mouse_moved = any(pygame.mouse.get_rel())
        if self.state == "playing" and (any(keys) or mouse_moved):
            self.ui_last_interaction_time = now_ticks
        # 计算目标高度
        if show_full:
            self.ui_target_height = 64
        else:
            # 交互后2秒内展示完整高度，否则收缩为24
            self.ui_target_height = 64 if (now_ticks - self.ui_last_interaction_time) < 2000 else 24
        # 高度缓动
        self.ui_current_height += (self.ui_target_height - self.ui_current_height) * 0.15
        ui_height = int(self.ui_current_height)
        ui_alpha = 110 if (self.vision_enabled and not show_full and ui_height <= 32) else (140 if self.vision_enabled else 160)
        ui_rect = pygame.Rect(0, 0, surface_width, ui_height)
        ui_surface = pygame.Surface((surface_width, ui_height), pygame.SRCALPHA)
        pygame.draw.rect(ui_surface, (0, 0, 0, ui_alpha), (0, 0, surface_width, ui_height))
        self.surface.blit(ui_surface, (0, 0))

        # 等级信息
        level_font = pygame.font.Font(FONT_NAME, 28)
        level_text = level_font.render(f"等级 {self.current_level}: {level_config['name']}", True, (255, 255, 255))
        self.surface.blit(level_text, (20, 15))

        # 时间信息
        time_limit = level_config["time_limit"]
        remaining_time = max(0, time_limit - self.game_time)
        minutes = int(remaining_time // 60)
        seconds = int(remaining_time % 60)

        time_color = (255, 255, 255)
        if remaining_time < 30:
            time_color = (255, 100, 100)
        elif remaining_time < 60:
            time_color = (255, 200, 100)

        time_font = pygame.font.Font(FONT_NAME, 24)
        time_text = time_font.render(f"时间: {minutes:02d}:{seconds:02d}", True, time_color)
        # 文本纵向位置根据高度自适应（底部对齐）
        text_base_y = max(12, ui_height - 19)
        self.surface.blit(time_text, (20, text_base_y))

        # 迷宫大小信息
        size_text = time_font.render(f"迷宫: {level_config['size'][0]}×{level_config['size'][1]}", True, (200, 200, 200))
        self.surface.blit(size_text, (surface_width - 200, 12))

        # 操作提示
        hint_text = time_font.render("WASD/方向键移动", True, (200, 200, 200))
        self.surface.blit(hint_text, (surface_width - 200, text_base_y))

        # 视野限制状态显示
        if self.vision_enabled:
            vision_font = pygame.font.Font(FONT_NAME, 18)
            vision_text = vision_font.render("🔦 视野限制模式", True, (150, 100, 200))
            self.surface.blit(vision_text, (surface_width // 2 - 60, 12))

            # 探索进度
            total_cells = len(self.maze) * len(self.maze[0])
            explored_count = len(self.explored_cells)
            progress = (explored_count / total_cells) * 100
            progress_text = vision_font.render(f"探索进度: {progress:.1f}%", True, (150, 200, 150))
            if ui_height >= 40:
                self.surface.blit(progress_text, (surface_width // 2 - 60, 32))

        # 返回按钮
        back_rect = pygame.Rect(surface_width - 120, surface_height - 60, 100, 40)
        pygame.draw.rect(self.surface, (100, 100, 100, 200), back_rect, border_radius=8)
        pygame.draw.rect(self.surface, (255, 255, 255), back_rect, 2, border_radius=8)
        back_font = pygame.font.Font(FONT_NAME, 20)
        back_text = back_font.render("返回", True, (255, 255, 255))
        back_text_rect = back_text.get_rect(center=back_rect.center)
        self.surface.blit(back_text, back_text_rect)
        self.game_back_rect = back_rect

    def draw_win(self):
        """绘制胜利界面"""
        surface_width, surface_height = self.surface.get_size()

        # 继续绘制游戏界面作为背景
        self.draw_playing()

        # 半透明遮罩
        overlay = pygame.Surface((surface_width, surface_height), pygame.SRCALPHA)
        pygame.draw.rect(overlay, (0, 0, 0, 150), (0, 0, surface_width, surface_height))
        self.surface.blit(overlay, (0, 0))

        # 胜利面板
        panel_width = 400
        panel_height = 300
        panel_x = (surface_width - panel_width) // 2
        panel_y = (surface_height - panel_height) // 2

        # 面板背景
        panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)
        pygame.draw.rect(self.surface, (50, 50, 70), panel_rect, border_radius=20)
        pygame.draw.rect(self.surface, (255, 215, 0), panel_rect, 4, border_radius=20)

        # 胜利动画效果
        for i in range(10):
            star_angle = self.win_animation * 2 + i * 36
            star_x = panel_x + panel_width//2 + 80 * math.cos(math.radians(star_angle))
            star_y = panel_y + 80 + 30 * math.sin(math.radians(star_angle))
            star_size = 3 + int(2 * math.sin(self.win_animation + i))
            pygame.draw.circle(self.surface, (255, 255, 100), (int(star_x), int(star_y)), star_size)

        # 胜利文字
        win_font = pygame.font.Font(FONT_NAME, 48)
        win_text = win_font.render("恭喜通关！", True, (255, 215, 0))
        win_rect = win_text.get_rect(center=(panel_x + panel_width//2, panel_y + 60))
        self.surface.blit(win_text, win_rect)

        # 完成时间
        time_font = pygame.font.Font(FONT_NAME, 24)
        minutes = int(self.game_time // 60)
        seconds = int(self.game_time % 60)
        time_text = time_font.render(f"完成时间: {minutes:02d}:{seconds:02d}", True, (255, 255, 255))
        time_rect = time_text.get_rect(center=(panel_x + panel_width//2, panel_y + 120))
        self.surface.blit(time_text, time_rect)

        # 等级信息
        level_text = time_font.render(f"等级: {self.levels[self.current_level]['name']}", True, (255, 255, 255))
        level_rect = level_text.get_rect(center=(panel_x + panel_width//2, panel_y + 150))
        self.surface.blit(level_text, level_rect)

        # 按钮
        button_width = 120
        button_height = 40
        button_y = panel_y + 200

        # 下一关按钮
        if self.current_level < len(self.levels):
            next_rect = pygame.Rect(panel_x + 50, button_y, button_width, button_height)
            pygame.draw.rect(self.surface, (100, 200, 100), next_rect, border_radius=8)
            pygame.draw.rect(self.surface, (255, 255, 255), next_rect, 2, border_radius=8)
            next_font = pygame.font.Font(FONT_NAME, 20)
            next_text = next_font.render("下一关", True, (255, 255, 255))
            next_text_rect = next_text.get_rect(center=next_rect.center)
            self.surface.blit(next_text, next_text_rect)
            self.next_rect = next_rect

        # 重新开始按钮
        restart_rect = pygame.Rect(panel_x + panel_width - 170, button_y, button_width, button_height)
        pygame.draw.rect(self.surface, (100, 100, 200), restart_rect, border_radius=8)
        pygame.draw.rect(self.surface, (255, 255, 255), restart_rect, 2, border_radius=8)
        restart_font = pygame.font.Font(FONT_NAME, 20)
        restart_text = restart_font.render("重新开始", True, (255, 255, 255))
        restart_text_rect = restart_text.get_rect(center=restart_rect.center)
        self.surface.blit(restart_text, restart_text_rect)
        self.restart_rect = restart_rect

        # 返回按钮
        back_rect = pygame.Rect(panel_x + (panel_width - button_width)//2, button_y + 50, button_width, button_height)
        pygame.draw.rect(self.surface, (150, 150, 150), back_rect, border_radius=8)
        pygame.draw.rect(self.surface, (255, 255, 255), back_rect, 2, border_radius=8)
        back_font = pygame.font.Font(FONT_NAME, 20)
        back_text = back_font.render("返回选择", True, (255, 255, 255))
        back_text_rect = back_text.get_rect(center=back_rect.center)
        self.surface.blit(back_text, back_text_rect)
        self.win_back_rect = back_rect

    def draw_lose(self):
        """绘制失败界面"""
        surface_width, surface_height = self.surface.get_size()

        # 继续绘制游戏界面作为背景
        self.draw_playing()

        # 半透明遮罩
        overlay = pygame.Surface((surface_width, surface_height), pygame.SRCALPHA)
        pygame.draw.rect(overlay, (0, 0, 0, 150), (0, 0, surface_width, surface_height))
        self.surface.blit(overlay, (0, 0))

        # 失败面板
        panel_width = 350
        panel_height = 250
        panel_x = (surface_width - panel_width) // 2
        panel_y = (surface_height - panel_height) // 2

        # 面板背景
        panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)
        pygame.draw.rect(self.surface, (70, 50, 50), panel_rect, border_radius=20)
        pygame.draw.rect(self.surface, (255, 100, 100), panel_rect, 4, border_radius=20)

        # 失败文字
        lose_font = pygame.font.Font(FONT_NAME, 42)
        lose_text = lose_font.render("时间到！", True, (255, 100, 100))
        lose_rect = lose_text.get_rect(center=(panel_x + panel_width//2, panel_y + 60))
        self.surface.blit(lose_text, lose_rect)

        # 提示文字
        hint_font = pygame.font.Font(FONT_NAME, 24)
        hint_text = hint_font.render("再试一次吧！", True, (255, 255, 255))
        hint_rect = hint_text.get_rect(center=(panel_x + panel_width//2, panel_y + 110))
        self.surface.blit(hint_text, hint_rect)

        # 按钮
        button_width = 120
        button_height = 40
        button_y = panel_y + 160

        # 重新开始按钮
        restart_rect = pygame.Rect(panel_x + 30, button_y, button_width, button_height)
        pygame.draw.rect(self.surface, (100, 100, 200), restart_rect, border_radius=8)
        pygame.draw.rect(self.surface, (255, 255, 255), restart_rect, 2, border_radius=8)
        restart_font = pygame.font.Font(FONT_NAME, 20)
        restart_text = restart_font.render("重新开始", True, (255, 255, 255))
        restart_text_rect = restart_text.get_rect(center=restart_rect.center)
        self.surface.blit(restart_text, restart_text_rect)
        self.lose_restart_rect = restart_rect

        # 返回按钮
        back_rect = pygame.Rect(panel_x + panel_width - 150, button_y, button_width, button_height)
        pygame.draw.rect(self.surface, (150, 150, 150), back_rect, border_radius=8)
        pygame.draw.rect(self.surface, (255, 255, 255), back_rect, 2, border_radius=8)
        back_font = pygame.font.Font(FONT_NAME, 20)
        back_text = back_font.render("返回选择", True, (255, 255, 255))
        back_text_rect = back_text.get_rect(center=back_rect.center)
        self.surface.blit(back_text, back_text_rect)
        self.lose_back_rect = back_rect

    def draw(self):
        """主绘制方法"""
        self.update()

        if self.state == "level_select":
            self.draw_level_select()
        elif self.state == "playing":
            self.draw_playing()
        elif self.state == "win":
            self.draw_win()
        elif self.state == "lose":
            self.draw_lose()

    def handle_event(self, event):
        """处理事件"""
        current_time = pygame.time.get_ticks()

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if self.state == "level_select":
                    self.active = False
                else:
                    self.state = "level_select"

            # 游戏中的移动控制
            elif self.state == "playing":
                # 记录按键按下时间，用于连续移动
                if event.key in [pygame.K_w, pygame.K_UP]:
                    self.key_pressed_time[pygame.K_UP] = current_time
                    self.move_player(0, -1)  # 立即移动一次
                elif event.key in [pygame.K_s, pygame.K_DOWN]:
                    self.key_pressed_time[pygame.K_DOWN] = current_time
                    self.move_player(0, 1)
                elif event.key in [pygame.K_a, pygame.K_LEFT]:
                    self.key_pressed_time[pygame.K_LEFT] = current_time
                    self.move_player(-1, 0)
                elif event.key in [pygame.K_d, pygame.K_RIGHT]:
                    self.key_pressed_time[pygame.K_RIGHT] = current_time
                    self.move_player(1, 0)
                elif event.key == pygame.K_r:  # R键重新开始
                    self.start_level(self.current_level)

        elif event.type == pygame.KEYUP:
            # 清除按键记录，停止连续移动
            if self.state == "playing":
                if event.key in [pygame.K_w, pygame.K_UP]:
                    self.key_pressed_time.pop(pygame.K_UP, None)
                elif event.key in [pygame.K_s, pygame.K_DOWN]:
                    self.key_pressed_time.pop(pygame.K_DOWN, None)
                elif event.key in [pygame.K_a, pygame.K_LEFT]:
                    self.key_pressed_time.pop(pygame.K_LEFT, None)
                elif event.key in [pygame.K_d, pygame.K_RIGHT]:
                    self.key_pressed_time.pop(pygame.K_RIGHT, None)

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # 左键点击
                mouse_pos = event.pos

                if self.state == "level_select":
                    # 检查等级按钮点击
                    for level in self.levels:
                        if hasattr(self, f'level_{level}_rect'):
                            rect = getattr(self, f'level_{level}_rect')
                            if rect.collidepoint(mouse_pos):
                                self.start_level(level)
                                return

                    # 检查模式切换按钮
                    if hasattr(self, 'mode_rect') and self.mode_rect.collidepoint(mouse_pos):
                        self.unique_path_mode = not self.unique_path_mode

                    # 检查视野限制按钮
                    elif hasattr(self, 'vision_rect') and self.vision_rect.collidepoint(mouse_pos):
                        self.vision_enabled = not self.vision_enabled

                    # 检查返回按钮
                    elif hasattr(self, 'back_rect') and self.back_rect.collidepoint(mouse_pos):
                        self.active = False
                    # 检查风格切换按钮
                    elif hasattr(self, 'style_rect') and self.style_rect.collidepoint(mouse_pos):
                        self.maze_style_index = (self.maze_style_index + 1) % len(self.maze_style_names)
                    # 检查随机起终点按钮
                    elif hasattr(self, 'random_rect') and self.random_rect.collidepoint(mouse_pos):
                        self.random_spawn_enabled = not self.random_spawn_enabled

                elif self.state == "playing":
                    # 检查返回按钮
                    if hasattr(self, 'game_back_rect') and self.game_back_rect.collidepoint(mouse_pos):
                        self.state = "level_select"

                elif self.state == "win":
                    # 检查下一关按钮
                    if (hasattr(self, 'next_rect') and self.next_rect.collidepoint(mouse_pos)
                        and self.current_level < len(self.levels)):
                        self.start_level(self.current_level + 1)

                    # 检查重新开始按钮
                    elif hasattr(self, 'restart_rect') and self.restart_rect.collidepoint(mouse_pos):
                        self.start_level(self.current_level)

                    # 检查返回按钮
                    elif hasattr(self, 'win_back_rect') and self.win_back_rect.collidepoint(mouse_pos):
                        self.state = "level_select"

                elif self.state == "lose":
                    # 检查重新开始按钮
                    if hasattr(self, 'lose_restart_rect') and self.lose_restart_rect.collidepoint(mouse_pos):
                        self.start_level(self.current_level)

                    # 检查返回按钮
                    elif hasattr(self, 'lose_back_rect') and self.lose_back_rect.collidepoint(mouse_pos):
                        self.state = "level_select"
