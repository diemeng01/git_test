# -*- coding: utf-8 -*-
"""
飞机大战（射击游戏）—— 基于 pygame
功能：
  - 滚动星空背景
  - 玩家飞机（键盘/鼠标控制 + 射击）
  - 多种敌人 + 敌人子弹，难度随得分递增
  - 生命值、爆炸特效、计分
  - 开始 / 进行中 / 结束 三种游戏状态
  - 合成音效与背景音乐（资源自动生成到 assets/）
  - 最高分保存到本地文件
操作：
  方向键 / WASD  移动
  空格 / 鼠标左键 射击（按住连发）
  P            暂停
  R            结束后重新开始
  ESC          退出
"""

import array
import math
import os
import random
import sys
import wave

import pygame

WIDTH, HEIGHT = 480, 700
FPS = 60

# 数据目录：开发时为脚本所在目录；
# 打包为 exe 后使用用户可写目录（避免 exe 放在只读位置导致无法写存档）
if getattr(sys, "frozen", False):
    DATA_DIR = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "PlaneWar")
else:
    DATA_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(DATA_DIR, "assets")
HIGHSCORE_FILE = os.path.join(DATA_DIR, "highscore.txt")

# 游戏状态
START, PLAYING, GAMEOVER = 0, 1, 2

# 事件
ENEMY_EVENT = pygame.USEREVENT + 1  # 定时生成敌人
SHOOT_EVENT = pygame.USEREVENT + 2  # 定时玩家开火


# ================= 资源生成（图片 / 音效 / BGM） =================
def save_wav(path, samples, rate=44100):
    """把整数样本列表写入单声道 16bit WAV。"""
    with wave.open(path, "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(array.array("h", samples).tobytes())


def tone_samples(freq, dur, vol=0.4, decay=1.5, rate=44100):
    """带指数衰减的正弦波样本。"""
    n = int(rate * dur)
    out = []
    for i in range(n):
        env = (1 - i / n) ** decay
        s = math.sin(2 * math.pi * freq * i / rate)
        s += 0.35 * math.sin(2 * math.pi * freq * 2 * i / rate)  # 泛音
        out.append(int(vol * 30000 * env * s))
    return out


def noise_samples(dur, vol=0.6, decay=2.0, rate=44100):
    """带衰减的白噪声样本（用于爆炸）。"""
    n = int(rate * dur)
    return [
        int(vol * 30000 * (1 - i / n) ** decay * random.uniform(-1, 1))
        for i in range(n)
    ]


def make_bgm():
    """合成一段轻快循环的 8-bit 风格旋律。"""
    notes = [523, 659, 784, 659, 784, 880, 784, 659,
             523, 587, 659, 784, 880, 784, 659, 587]
    note_dur = 0.17
    samples = []
    for _ in range(2):  # 循环两遍
        for f in notes:
            for i in range(int(44100 * note_dur)):
                env = min(1.0, i / 400, (int(44100 * note_dur) - i) / 400)
                s = math.sin(2 * math.pi * f * i / 44100)
                samples.append(int(0.28 * 30000 * env * s))
    save_wav(os.path.join(ASSETS_DIR, "bgm.wav"), samples)


def generate_assets():
    """首次运行时生成全部资源文件（图片 PNG + 音效 WAV + BGM）。"""
    os.makedirs(ASSETS_DIR, exist_ok=True)
    pygame.init()

    # ---- 玩家飞机：蓝色喷气机 ----
    img = pygame.Surface((46, 54), pygame.SRCALPHA)
    pygame.draw.polygon(img, (80, 170, 255),
                        [(23, 2), (6, 44), (23, 34), (40, 44)])  # 机身
    pygame.draw.polygon(img, (200, 230, 255), [(23, 6), (14, 40), (23, 33)])  # 高光
    pygame.draw.polygon(img, (255, 120, 60),
                        [(14, 44), (23, 52), (32, 44), (23, 38)])  # 尾焰
    pygame.draw.rect(img, (255, 230, 150), (20, 12, 6, 10), border_radius=3)  # 机舱
    pygame.image.save(img, os.path.join(ASSETS_DIR, "player.png"))

    # ---- 普通敌人：红色 ----
    img = pygame.Surface((40, 44), pygame.SRCALPHA)
    pygame.draw.polygon(img, (240, 80, 90),
                        [(20, 2), (2, 38), (20, 26), (38, 38)])
    pygame.draw.polygon(img, (255, 170, 170), [(20, 6), (10, 34), (20, 27)])
    pygame.image.save(img, os.path.join(ASSETS_DIR, "enemy1.png"))

    # ---- 精英敌人：紫色、更大 ----
    img = pygame.Surface((56, 56), pygame.SRCALPHA)
    pygame.draw.polygon(img, (180, 90, 235),
                        [(28, 2), (2, 26), (10, 52), (28, 40), (46, 52), (54, 26)])
    pygame.draw.polygon(img, (220, 160, 255), [(28, 8), (12, 28), (28, 34)])
    pygame.draw.circle(img, (255, 255, 255), (28, 22), 5)
    pygame.image.save(img, os.path.join(ASSETS_DIR, "enemy2.png"))

    # ---- 玩家子弹：黄色光弹 ----
    img = pygame.Surface((8, 20), pygame.SRCALPHA)
    pygame.draw.rect(img, (255, 240, 120), (0, 0, 8, 20), border_radius=4)
    pygame.draw.rect(img, (255, 255, 255), (2, 2, 4, 16), border_radius=2)
    pygame.image.save(img, os.path.join(ASSETS_DIR, "bullet.png"))

    # ---- 敌人子弹：红色圆点 ----
    img = pygame.Surface((12, 12), pygame.SRCALPHA)
    pygame.draw.circle(img, (255, 90, 90), (6, 6), 6)
    pygame.draw.circle(img, (255, 220, 220), (4, 4), 2)
    pygame.image.save(img, os.path.join(ASSETS_DIR, "ebullet.png"))

    # ---- 音效 ----
    save_wav(os.path.join(ASSETS_DIR, "shoot.wav"), tone_samples(880, 0.08, 0.3))
    save_wav(os.path.join(ASSETS_DIR, "explosion.wav"), noise_samples(0.35, 0.7))
    save_wav(os.path.join(ASSETS_DIR, "hit.wav"),
             tone_samples(300, 0.18, 0.5, decay=1.0) + tone_samples(90, 0.15, 0.5, decay=2.0))
    make_bgm()
    try:
        print(f"已生成资源到 {ASSETS_DIR}")
    except Exception:
        pass  # windowed 打包后无控制台，print 可能失败


def load_assets():
    """从 assets/ 加载图片与音效资源。"""
    def img(name):
        image = pygame.image.load(os.path.join(ASSETS_DIR, name))
        try:
            return image.convert_alpha()
        except pygame.error:
            return image  # 无显示设备时原样返回（测试环境）

    def snd(name):
        try:
            return pygame.mixer.Sound(os.path.join(ASSETS_DIR, name))
        except pygame.error:
            return None  # 无音频设备时静音降级

    return {
        "player": img("player.png"),
        "enemy1": img("enemy1.png"),
        "enemy2": img("enemy2.png"),
        "bullet": img("bullet.png"),
        "ebullet": img("ebullet.png"),
        "shoot": snd("shoot.wav"),
        "explosion": snd("explosion.wav"),
        "hit": snd("hit.wav"),
    }


def play_sound(sound):
    """安全播放音效（无声卡时静音）。"""
    if sound:
        sound.play()


def load_highscore():
    """读取最高分。"""
    try:
        with open(HIGHSCORE_FILE, encoding="utf-8") as f:
            return int(f.read().strip() or 0)
    except (OSError, ValueError):
        return 0


def save_highscore(score):
    """保存最高分。"""
    try:
        with open(HIGHSCORE_FILE, "w", encoding="utf-8") as f:
            f.write(str(score))
    except OSError:
        pass


# ================= 精灵类 =================
class Player(pygame.sprite.Sprite):
    def __init__(self, assets):
        super().__init__()
        self.image = assets["player"]
        self.rect = self.image.get_rect(center=(WIDTH // 2, HEIGHT - 70))
        self.speed = 6
        self.hp = 3
        self.invincible_timer = 0  # 受击后短暂无敌
        self.shoot_cd = 0          # 射击冷却

    def update(self, keys, mouse_pos, mouse_down):
        # 键盘移动
        dx = (keys[pygame.K_RIGHT] or keys[pygame.K_d]) - \
             (keys[pygame.K_LEFT] or keys[pygame.K_a])
        dy = (keys[pygame.K_DOWN] or keys[pygame.K_s]) - \
             (keys[pygame.K_UP] or keys[pygame.K_w])
        self.rect.x += dx * self.speed
        self.rect.y += dy * self.speed
        # 鼠标移动（仅当鼠标已移动过、且不在键盘控制时）
        if mouse_pos:
            self.rect.center = mouse_pos
        # 边界限制
        self.rect.clamp_ip(pygame.Rect(0, 0, WIDTH, HEIGHT))
        # 无敌计时
        if self.invincible_timer > 0:
            self.invincible_timer -= 1
        if self.shoot_cd > 0:
            self.shoot_cd -= 1

    def try_shoot(self):
        """冷却结束后允许射击。"""
        if self.shoot_cd <= 0:
            self.shoot_cd = 12  # 每 12 帧一发
            return True
        return False

    def hit(self):
        """受到伤害；无敌期间免疫。"""
        if self.invincible_timer > 0:
            return False
        self.hp -= 1
        self.invincible_timer = 90  # 1.5 秒无敌
        return True


class Enemy(pygame.sprite.Sprite):
    def __init__(self, assets, elite=False):
        super().__init__()
        self.elite = elite
        self.image = assets["enemy2"] if elite else assets["enemy1"]
        self.rect = self.image.get_rect(
            midtop=(random.randint(30, WIDTH - 30), -60))
        self.speed = random.uniform(1.5, 2.5) + (0.5 if elite else 0)
        self.hp = 3 if elite else 1
        self.points = 30 if elite else 10
        self.wobble = random.uniform(0, math.tau)
        self.shoot_timer = random.randint(30, 90)  # 精英敌射击计时

    def update(self, assets, enemy_bullets):
        self.wobble += 0.04
        self.rect.y += self.speed
        if self.elite:
            self.rect.x += math.sin(self.wobble) * 1.2  # 横向摇摆
        # 精英敌发射子弹
        if self.elite and self.rect.y > 0:
            self.shoot_timer -= 1
            if self.shoot_timer <= 0:
                self.shoot_timer = random.randint(60, 110)
                eb = EnemyBullet(assets["ebullet"], self.rect.centerx, self.rect.bottom)
                enemy_bullets.add(eb)


class Bullet(pygame.sprite.Sprite):
    def __init__(self, image, x, y):
        super().__init__()
        self.image = image
        self.rect = self.image.get_rect(center=(x, y))
        self.speed = -12  # 向上

    def update(self):
        self.rect.y += self.speed
        if self.rect.bottom < 0:
            self.kill()


class EnemyBullet(pygame.sprite.Sprite):
    def __init__(self, image, x, y):
        super().__init__()
        self.image = image
        self.rect = self.image.get_rect(center=(x, y))
        self.speed = 5

    def update(self):
        self.rect.y += self.speed
        if self.rect.top > HEIGHT:
            self.kill()


class Explosion(pygame.sprite.Sprite):
    """爆炸动画：逐帧放大后淡出。"""
    def __init__(self, center, size=50):
        super().__init__()
        self.center = center
        self.size = size
        self.frame = 0
        self.max_frame = 8

    def update(self):
        self.frame += 1
        if self.frame >= self.max_frame:
            self.kill()

    def draw(self, surface):
        t = self.frame / self.max_frame
        r = int(self.size * (0.3 + t))
        alpha = int(255 * (1 - t))
        for color, radius in [((255, 240, 150), r), ((255, 150, 60), int(r * 0.7)),
                              ((255, 80, 40), int(r * 0.4))]:
            s = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*color, alpha), (radius, radius), radius)
            surface.blit(s, (self.center[0] - radius, self.center[1] - radius))


class Star:
    """滚动背景星星。"""
    def __init__(self):
        self.x = random.randint(0, WIDTH)
        self.y = random.randint(0, HEIGHT)
        self.speed = random.uniform(0.5, 3.0)
        self.size = random.choice([1, 1, 2, 2, 3])
        self.bright = random.randint(100, 255)

    def update(self):
        self.y += self.speed
        if self.y > HEIGHT:
            self.y = -5
            self.x = random.randint(0, WIDTH)

    def draw(self, surface):
        pygame.draw.circle(surface, (self.bright, self.bright, min(255, self.bright + 20)),
                           (self.x, self.y), self.size)


# ================= 游戏主循环 =================
def draw_text(surface, text, size, color, center, bold=True):
    font = pygame.font.SysFont("microsoftyahei", size, bold=bold)
    img = font.render(text, True, color)
    surface.blit(img, img.get_rect(center=center))


def main():
    """入口：捕获异常并写入日志，便于无控制台模式下排查问题。"""
    try:
        _main()
    except Exception:
        import traceback
        try:
            with open(os.path.join(DATA_DIR, "error.log"), "w", encoding="utf-8") as f:
                traceback.print_exc(file=f)
        except OSError:
            pass
        raise


def debug_log(msg):
    """追加写调试日志（打包排错用）。"""
    try:
        with open(os.path.join(DATA_DIR, "debug.log"), "a", encoding="utf-8") as f:
            f.write(msg + "\n")
    except OSError:
        pass


def _main():
    debug_log("进入 _main")
    # ---- 初始化 ----
    try:
        pygame.mixer.pre_init(44100, -16, 1, 512)
    except pygame.error:
        pass
    pygame.init()
    debug_log("pygame.init OK")
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    debug_log("set_mode OK")
    pygame.display.set_caption("飞机大战 射击游戏")
    clock = pygame.time.Clock()

    if not os.path.isdir(ASSETS_DIR):
        generate_assets()
    assets = load_assets()
    highscore = load_highscore()

    # 背景音乐（无音频设备时静音降级）
    try:
        pygame.mixer.music.load(os.path.join(ASSETS_DIR, "bgm.wav"))
        pygame.mixer.music.play(-1)
    except pygame.error:
        pass

    # ---- 游戏状态 ----
    state = START
    score = 0
    player = None
    all_sprites = pygame.sprite.Group()
    enemies = pygame.sprite.Group()
    bullets = pygame.sprite.Group()
    enemy_bullets = pygame.sprite.Group()
    explosions = []
    stars = [Star() for _ in range(70)]
    current_interval = 1200
    pygame.time.set_timer(ENEMY_EVENT, current_interval)

    def start_game():
        nonlocal score, player, all_sprites, enemies, bullets, enemy_bullets, explosions
        score = 0
        player = Player(assets)
        all_sprites = pygame.sprite.Group(player)
        enemies = pygame.sprite.Group()
        bullets = pygame.sprite.Group()
        enemy_bullets = pygame.sprite.Group()
        explosions = []
        pygame.time.set_timer(ENEMY_EVENT, 1200)

    running = True
    paused = False
    mouse_pos = None

    debug_log("进入主循环")
    while running:
        dt = clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif state == START:
                    start_game()
                    state = PLAYING
                elif state == GAMEOVER:
                    if event.key == pygame.K_r:
                        start_game()
                        state = PLAYING
                elif event.key == pygame.K_p:
                    paused = not paused
            elif event.type == pygame.MOUSEMOTION:
                mouse_pos = event.pos
            elif event.type == pygame.MOUSEBUTTONDOWN and state == START:
                start_game()
                state = PLAYING
            # 定时器：生成敌人
            elif event.type == ENEMY_EVENT and state == PLAYING and not paused:
                elite = random.random() < 0.18 + min(0.2, score / 5000)
                enemies.add(Enemy(assets, elite=elite))
            # 定时器：玩家射击
            elif event.type == SHOOT_EVENT and state == PLAYING and not paused:
                pass  # 射击改为按键驱动 + 冷却，见下

        # ---- 更新 ----
        if state == PLAYING and not paused:
            keys = pygame.key.get_pressed()
            mouse_down = pygame.mouse.get_pressed()[0]
            player.update(keys, mouse_pos if pygame.mouse.get_focused() else None,
                          mouse_down)
            # 射击：空格或鼠标左键
            if (keys[pygame.K_SPACE] or mouse_down) and player.try_shoot():
                Bullet(assets["bullet"], player.rect.centerx, player.rect.top).add(bullets)
                play_sound(assets["shoot"])
            # 子弹 / 敌人更新
            bullets.update()
            enemies.update(assets, enemy_bullets)
            enemy_bullets.update()

            # 玩家子弹 vs 敌人
            for b in bullets:
                for enemy in pygame.sprite.spritecollide(b, enemies, False):
                    enemy.hp -= 1
                    b.kill()
                    play_sound(assets["hit"])
                    if enemy.hp <= 0:
                        enemy.kill()
                        score += enemy.points
                        explosions.append(Explosion(enemy.rect.center, 46 if enemy.elite else 30))
                        play_sound(assets["explosion"])
                    break

            # 敌人 / 敌人子弹 vs 玩家
            if pygame.sprite.spritecollide(player, enemies, True) or \
               pygame.sprite.spritecollide(player, enemy_bullets, True):
                if player.hit():
                    play_sound(assets["hit"])
                    explosions.append(Explosion(player.rect.center, 60))
                    if player.hp <= 0:
                        state = GAMEOVER
                        if score > highscore:
                            highscore = score
                            save_highscore(highscore)

            # 爆炸动画 / 星星
            for e in explosions:
                e.update()
            explosions = [e for e in explosions if e.frame < e.max_frame]
            for s in stars:
                s.update()

            # 难度递增：得分越高敌人生成越快
            new_interval = max(250, 1200 - (score // 100) * 60)
            if new_interval != current_interval:
                current_interval = new_interval
                pygame.time.set_timer(ENEMY_EVENT, current_interval)

        # ---- 渲染 ----
        screen.fill((8, 10, 18))
        for s in stars:
            s.draw(screen)

        if state == START:
            draw_text(screen, "✈ 飞机大战", 54, (255, 220, 120), (WIDTH // 2, 200))
            draw_text(screen, f"历史最高分：{highscore}", 24, (180, 200, 230), (WIDTH // 2, 280))
            draw_text(screen, "方向键 / WASD 移动 · 空格 / 鼠标左键 射击", 20, (150, 160, 190), (WIDTH // 2, 360))
            draw_text(screen, "按任意键开始", 26, (255, 255, 255), (WIDTH // 2, 440))
        elif state == PLAYING:
            all_sprites.draw(screen)
            bullets.draw(screen)
            enemies.draw(screen)
            enemy_bullets.draw(screen)
            for e in explosions:
                e.draw(screen)
            # 玩家受击闪烁
            if player and player.invincible_timer > 0 and player.invincible_timer % 6 < 3:
                screen.blit(player.image, player.rect, special_flags=pygame.BLEND_ADD)
            # HUD
            draw_text(screen, f"得分 {score}", 22, (255, 255, 255), (70, 28))
            draw_text(screen, "♥ " * max(player.hp, 0), 22, (255, 90, 90), (WIDTH - 60, 28))
            if paused:
                draw_text(screen, "已暂停 · 按 P 继续", 32, (255, 255, 255), (WIDTH // 2, HEIGHT // 2))
        else:  # GAMEOVER
            draw_text(screen, "游戏结束", 52, (255, 110, 110), (WIDTH // 2, 220))
            draw_text(screen, f"本次得分 {score}", 28, (255, 255, 255), (WIDTH // 2, 300))
            if score >= highscore and score > 0:
                draw_text(screen, "🎉 新纪录！", 30, (255, 220, 120), (WIDTH // 2, 350))
            draw_text(screen, f"历史最高分 {highscore}", 24, (180, 200, 230), (WIDTH // 2, 390))
            draw_text(screen, "按 R 重新开始", 26, (255, 255, 255), (WIDTH // 2, 460))

        pygame.display.flip()

    debug_log("主循环结束")
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
