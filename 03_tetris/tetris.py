# -*- coding: utf-8 -*-
"""
俄罗斯方块（Tetris）—— 基于 pygame 实现
操作说明：
  ← →   左右移动
  ↓     软降
  ↑     旋转
  空格   硬降（瞬间落底）
  P     暂停 / 继续
  R     重新开始（游戏结束后）
  ESC   退出
"""

import array
import math
import random
import sys

import pygame

# ---------- 常量 ----------
COLS, ROWS = 10, 20
CELL = 30
SIDE_PANEL = 220
WIDTH = COLS * CELL + SIDE_PANEL
HEIGHT = ROWS * CELL
FPS = 60

# 消行动画时长（毫秒）
FLASH_DURATION = 420

# 游戏区背景 / 网格线
BG_TOP, BG_BOTTOM = (24, 28, 44), (10, 12, 20)
GRID_COLOR = (38, 44, 66)
BORDER_COLOR = (90, 100, 140)
TEXT_COLOR = (235, 240, 250)
MUTED_COLOR = (150, 160, 185)
ACCENT = (110, 200, 255)

# 7 种方块：每种给出若干旋转形态的坐标
SHAPES = {
    "I": [
        [(0, 0), (1, 0), (2, 0), (3, 0)],
        [(1, -1), (1, 0), (1, 1), (1, 2)],
    ],
    "O": [
        [(1, 0), (2, 0), (1, 1), (2, 1)],
    ],
    "T": [
        [(1, 0), (0, 1), (1, 1), (2, 1)],
        [(1, 0), (1, 1), (2, 1), (1, 2)],
        [(0, 1), (1, 1), (2, 1), (1, 2)],
        [(1, 0), (0, 1), (1, 1), (1, 2)],
    ],
    "S": [
        [(1, 0), (2, 0), (0, 1), (1, 1)],
        [(1, 0), (1, 1), (2, 1), (2, 2)],
    ],
    "Z": [
        [(0, 0), (1, 0), (1, 1), (2, 1)],
        [(2, 0), (1, 1), (2, 1), (1, 2)],
    ],
    "J": [
        [(0, 0), (0, 1), (1, 1), (2, 1)],
        [(1, 0), (2, 0), (1, 1), (1, 2)],
        [(0, 1), (1, 1), (2, 1), (2, 2)],
        [(1, 0), (1, 1), (0, 2), (1, 2)],
    ],
    "L": [
        [(2, 0), (0, 1), (1, 1), (2, 1)],
        [(1, 0), (1, 1), (1, 2), (2, 2)],
        [(0, 1), (1, 1), (2, 1), (0, 2)],
        [(0, 0), (1, 0), (1, 1), (1, 2)],
    ],
}

COLORS = {
    "I": (0, 210, 235),
    "O": (245, 210, 60),
    "T": (170, 90, 235),
    "S": (70, 200, 110),
    "Z": (235, 80, 90),
    "J": (70, 130, 235),
    "L": (240, 140, 60),
}

# 消行得分（1/2/3/4 行）
LINE_SCORES = {1: 100, 2: 300, 3: 500, 4: 800}
# 各等级下落间隔（毫秒）
LEVEL_SPEEDS = [800, 700, 620, 540, 470, 400, 330, 270, 210, 160, 110, 80]


# ---------- 音效（合成生成，无需外部音频文件） ----------
sounds = {}  # 全局音效缓存


def make_tone(freq, duration, volume=0.4):
    """合成一段带指数衰减的正弦波音效，返回 pygame Sound 对象。"""
    rate = 44100
    n = int(rate * duration)
    buf = array.array(
        "h",
        (
            int(
                volume * 32000 * (1 - i / n) ** 1.5 * math.sin(2 * math.pi * freq * i / rate)
            )
            for i in range(n)
        ),
    )
    try:
        return pygame.mixer.Sound(buffer=buf.tobytes())
    except pygame.error:
        return None  # 无音频设备时静音降级


def init_sounds():
    """初始化各消行音效（按消除行数音高递增）。"""
    global sounds
    if not pygame.mixer.get_init():
        return
    # 依次对应消除 1/2/3/4 行
    tones = [
        (880, 0.10),
        (988, 0.13),
        (1108, 0.16),
        (1318, 0.24),
    ]
    sounds = {i + 1: make_tone(f, d) for i, (f, d) in enumerate(tones)}


def play_clear_sound(n):
    """播放消行音效，n 为消除行数（1~4）。"""
    snd = sounds.get(min(max(n, 1), 4))
    if snd:
        snd.play()



class Tetris:
    """游戏核心逻辑。"""

    def __init__(self):
        self.reset()

    def reset(self):
        self.board = [[None] * COLS for _ in range(ROWS)]
        self.score = 0
        self.level = 1
        self.lines = 0
        self.game_over = False
        self.paused = False
        self.current = None  # {"key", "rot", "x", "y"}
        self.next_key = random.choice(list(SHAPES))
        # 消行动画状态
        self.pending_rows = []  # 待消除的行索引
        self.clearing = False  # 是否正在播放消行动画
        self.flash_timer = 0  # 闪烁剩余毫秒
        self.spawn()

    # ---- 方块管理 ----
    def spawn(self):
        key = self.next_key
        self.next_key = random.choice(list(SHAPES))
        shape = SHAPES[key][0]
        width = max(x for x, _ in shape) + 1
        x = (COLS - width) // 2
        y = 0 if min(y for _, y in shape) == 0 else -1
        self.current = {"key": key, "rot": 0, "x": x, "y": y}
        if self.collides(self.current):
            self.game_over = True

    def cells_of(self, piece):
        """返回当前方块占用的所有格子坐标（x, y）。"""
        shape = SHAPES[piece["key"]][piece["rot"]]
        return [(piece["x"] + dx, piece["y"] + dy) for dx, dy in shape]

    def collides(self, piece):
        for x, y in self.cells_of(piece):
            if x < 0 or x >= COLS or y >= ROWS:
                return True
            if y >= 0 and self.board[y][x] is not None:
                return True
        return False

    def move(self, dx, dy):
        piece = dict(self.current)
        piece["x"] += dx
        piece["y"] += dy
        if not self.collides(piece):
            self.current = piece
            return True
        return False

    def rotate(self):
        key = self.current["key"]
        if key == "O":  # O 方块无需旋转
            return
        rot_count = len(SHAPES[key])
        piece = dict(self.current)
        piece["rot"] = (piece["rot"] + 1) % rot_count
        # 简单的墙踢：先试原位置，再左右试探 1~2 格
        for kick in (0, -1, 1, -2, 2):
            trial = dict(piece)
            trial["x"] = piece["x"] + kick
            if not self.collides(trial):
                self.current = trial
                return

    def drop(self):
        """硬降，落底并锁定。"""
        while self.move(0, 1):
            pass
        self.lock()

    def ghost(self):
        """返回当前方块的投影位置（模拟下落到最近碰撞点之前）。"""
        piece = dict(self.current)
        while not self.collides(piece):
            piece["y"] += 1
        piece["y"] -= 1  # 回退到最后一个不碰撞的位置
        return piece

    def lock(self):
        for x, y in self.cells_of(self.current):
            if y < 0:  # 方块锁在顶外
                self.game_over = True
                return
            self.board[y][x] = self.current["key"]
        # 检测完整行，进入消行动画
        self.pending_rows = [
            i for i, row in enumerate(self.board) if all(c is not None for c in row)
        ]
        if self.pending_rows:
            self.clearing = True
            self.flash_timer = FLASH_DURATION
            play_clear_sound(len(self.pending_rows))
        else:
            self.spawn()

    def update(self, dt):
        """推进消行动画计时，动画结束真正消除并生成新方块。"""
        if not self.clearing:
            return
        self.flash_timer -= dt
        if self.flash_timer <= 0:
            self.finish_clear()

    def finish_clear(self):
        """消除待消除行、更新得分并生成新方块。"""
        n = len(self.pending_rows)
        removed = set(self.pending_rows)
        remaining = [row for i, row in enumerate(self.board) if i not in removed]
        for _ in range(n):
            remaining.insert(0, [None] * COLS)
        self.board = remaining
        self.lines += n
        self.score += LINE_SCORES[n] * self.level
        self.level = min(1 + self.lines // 10, len(LEVEL_SPEEDS))
        self.pending_rows = []
        self.clearing = False
        self.flash_timer = 0
        self.spawn()

    def tick_ms(self):
        """当前等级下落间隔。"""
        return LEVEL_SPEEDS[min(self.level - 1, len(LEVEL_SPEEDS) - 1)]


# ---------- 渲染辅助 ----------
def draw_cell(surface, x, y, color, size=CELL):
    """画一个带高光和内阴影的立体小方块。"""
    rect = pygame.Rect(x * size, y * size, size, size)
    pygame.draw.rect(surface, color, rect, border_radius=5)
    # 顶部高光
    hi = tuple(min(255, c + 55) for c in color)
    pygame.draw.line(surface, hi, (rect.x + 4, rect.y + 4), (rect.right - 4, rect.y + 4), 2)
    # 底部阴影
    sh = tuple(max(0, c - 70) for c in color)
    pygame.draw.line(surface, sh, (rect.x + 4, rect.bottom - 3), (rect.right - 4, rect.bottom - 3), 2)
    # 边框
    pygame.draw.rect(surface, (0, 0, 0), rect, width=1, border_radius=5)


def draw_flash(surface, game):
    """消行动画：待消除行白色脉动闪烁，随后淡出。"""
    if not game.clearing:
        return
    t = 1 - game.flash_timer / FLASH_DURATION  # 动画进度 0 -> 1
    if t < 0.6:
        # 前 60%：高频白色脉动（闪约 2.5 次）
        pulse = abs(math.sin(t * math.pi * 5))
        alpha = int(230 * pulse + 40)
    else:
        # 后 40%：渐隐
        alpha = int(230 * (1 - t) / 0.4)
    alpha = max(0, min(255, alpha))
    width = WIDTH - SIDE_PANEL
    for row in game.pending_rows:
        overlay = pygame.Surface((width, CELL), pygame.SRCALPHA)
        overlay.fill((255, 255, 255, alpha))
        surface.blit(overlay, (0, row * CELL))


def draw_board(surface, game):
    # 已固定方块
    for y in range(ROWS):
        for x in range(COLS):
            key = game.board[y][x]
            if key:
                draw_cell(surface, x, y, COLORS[key])
    # 消行动画：闪烁特效层
    draw_flash(surface, game)
    # 当前活动方块
    if game.current and not game.game_over:
        # 投影预览：半透明线框显示落底位置
        ghost = game.ghost()
        for x, y in game.cells_of(ghost):
            if y >= 0:
                color = COLORS[game.current["key"]]
                overlay = pygame.Surface((CELL, CELL), pygame.SRCALPHA)
                overlay.fill((*color, 55))
                surface.blit(overlay, (x * CELL, y * CELL))
                pygame.draw.rect(surface, (*color, 255), (x * CELL, y * CELL, CELL, CELL), 2, border_radius=4)
        # 当前活动方块
        for x, y in game.cells_of(game.current):
            if y >= 0:
                color = COLORS[game.current["key"]]
                # 半透明叠加
                overlay = pygame.Surface((CELL, CELL), pygame.SRCALPHA)
                overlay.fill((*color, 230))
                surface.blit(overlay, (x * CELL, y * CELL))
                pygame.draw.rect(surface, (0, 0, 0), (x * CELL, y * CELL, CELL, CELL), 1)
                draw_cell(surface, x, y, color)
    # 网格线
    for x in range(COLS + 1):
        pygame.draw.line(surface, GRID_COLOR, (x * CELL, 0), (x * CELL, HEIGHT))
    for y in range(ROWS + 1):
        pygame.draw.line(surface, GRID_COLOR, (0, y * CELL), (WIDTH - SIDE_PANEL, y * CELL))
    # 边框
    pygame.draw.rect(surface, BORDER_COLOR, (0, 0, WIDTH - SIDE_PANEL, HEIGHT), 3)


def draw_panel(surface, game):
    panel_x = WIDTH - SIDE_PANEL + 20
    font_big = pygame.font.SysFont("microsoftyahei", 26, bold=True)
    font_mid = pygame.font.SysFont("microsoftyahei", 20)
    font_small = pygame.font.SysFont("microsoftyahei", 15)

    surface.blit(font_big.render("俄罗斯方块", True, ACCENT), (panel_x, 20))
    surface.blit(font_small.render("Tetris", True, MUTED_COLOR), (panel_x + 2, 52))

    # 分数
    surface.blit(font_mid.render("得分", True, TEXT_COLOR), (panel_x, 90))
    surface.blit(font_big.render(str(game.score), True, TEXT_COLOR), (panel_x, 115))

    # 等级 / 行数
    surface.blit(font_mid.render(f"等级  {game.level}", True, TEXT_COLOR), (panel_x, 165))
    surface.blit(font_mid.render(f"行数  {game.lines}", True, TEXT_COLOR), (panel_x, 195))

    # 下一个方块
    surface.blit(font_mid.render("下一个", True, TEXT_COLOR), (panel_x, 245))
    next_box = pygame.Rect(panel_x, 275, 120, 120)
    pygame.draw.rect(surface, (30, 36, 56), next_box, border_radius=10)
    pygame.draw.rect(surface, BORDER_COLOR, next_box, 1, border_radius=10)
    if game.next_key:
        shape = SHAPES[game.next_key][0]
        color = COLORS[game.next_key]
        xs = [x for x, _ in shape]
        ys = [y for _, y in shape]
        cw = max(xs) - min(xs) + 1
        ch = max(ys) - min(ys) + 1
        ox = next_box.x + (120 - cw * 24) // 2
        oy = next_box.y + (120 - ch * 24) // 2
        # 直接按小尺寸绘制
        for dx, dy in shape:
            r = pygame.Rect(ox + dx * 24, oy + dy * 24, 24, 24)
            pygame.draw.rect(surface, color, r, border_radius=4)
            pygame.draw.rect(surface, (0, 0, 0), r, 1, border_radius=4)

    # 操作提示
    tips = ["← → 移动", "↑ 旋转", "↓ 软降", "空格 硬降", "P 暂停", "R 重开", "ESC 退出"]
    ty = HEIGHT - 30 - len(tips) * 22
    for t in tips:
        surface.blit(font_small.render(t, True, MUTED_COLOR), (panel_x, ty))
        ty += 22


def draw_gradient(surface):
    """垂直渐变背景。"""
    for y in range(HEIGHT):
        t = y / HEIGHT
        color = tuple(int(a + (b - a) * t) for a, b in zip(BG_TOP, BG_BOTTOM))
        pygame.draw.line(surface, color, (0, y), (WIDTH, y))


def show_center(surface, lines):
    """居中叠加显示多层文字。"""
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 150))
    surface.blit(overlay, (0, 0))
    total_h = sum(l[1].get_height() + 8 for l in lines)
    y = (HEIGHT - total_h) // 2
    for text, font in lines:
        surface.blit(text, ((WIDTH - text.get_width()) // 2, y))
        y += text.get_height() + 8


def main():
    # 提前初始化混音器（单声道 16bit，合成音效用）
    try:
        pygame.mixer.pre_init(44100, -16, 1, 512)
    except pygame.error:
        pass
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("俄罗斯方块 Tetris")
    clock = pygame.time.Clock()

    init_sounds()

    font_big = pygame.font.SysFont("microsoftyahei", 42, bold=True)
    font_mid = pygame.font.SysFont("microsoftyahei", 22)

    game = Tetris()
    fall_timer = 0  # 累计毫秒

    running = True
    while running:
        dt = clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif game.game_over:
                    if event.key == pygame.K_r:
                        game.reset()
                elif event.key == pygame.K_p:
                    game.paused = not game.paused
                elif not game.paused:
                    if event.key == pygame.K_LEFT:
                        game.move(-1, 0)
                    elif event.key == pygame.K_RIGHT:
                        game.move(1, 0)
                    elif event.key == pygame.K_DOWN:
                        if game.move(0, 1):
                            game.score += 1
                        fall_timer = 0
                    elif event.key == pygame.K_UP:
                        game.rotate()
                    elif event.key == pygame.K_SPACE:
                        game.drop()

        if running and not game.game_over and not game.paused:
            if game.clearing:
                # 消行动画进行中：推进动画计时，暂停下落
                game.update(dt)
            else:
                fall_timer += dt
                if fall_timer >= game.tick_ms():
                    if not game.move(0, 1):
                        game.lock()
                    fall_timer = 0

        # ---- 渲染 ----
        draw_gradient(screen)
        draw_board(screen, game)
        draw_panel(screen, game)

        if game.game_over:
            show_center(screen, [
                (font_big.render("游戏结束", True, (255, 110, 110)), font_big),
                (font_mid.render(f"最终得分：{game.score}", True, TEXT_COLOR), font_mid),
                (font_mid.render("按 R 重新开始", True, MUTED_COLOR), font_mid),
            ])
        elif game.paused:
            show_center(screen, [
                (font_big.render("已暂停", True, ACCENT), font_big),
                (font_mid.render("按 P 继续", True, MUTED_COLOR), font_mid),
            ])

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
