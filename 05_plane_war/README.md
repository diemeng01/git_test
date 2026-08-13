# 飞机大战（pygame 射击游戏）

- **技术**：`pygame`
  - 精灵类（`pygame.sprite.Sprite`）与碰撞检测
  - 事件驱动（键盘、鼠标、定时器）
  - 游戏状态管理（开始 / 进行中 / 结束）
  - 资源管理（图片 PNG + 音效 WAV + 背景音乐，首次运行自动生成到 `assets/`）
- **功能**：
  - 滚动星空背景
  - 双类型敌人（普通 / 精英，精英会发射子弹）
  - 难度递增（敌人生成速度随得分加快）
  - 生命值、爆炸特效、最高分保存（`highscore.txt`）

## 直接玩（无需 Python）

双击 **`dist/飞机大战.exe`** 即可运行（已打包，单文件）。

## 运行源码

```bash
python plane_war.py
```

## 操作

| 按键 | 功能 |
|------|------|
| 方向键 / WASD / 鼠标 | 移动 |
| 空格 / 鼠标左键 | 射击 |
| `P` | 暂停 |
| `R` | 重新开始 |
| `ESC` | 退出 |

## 依赖 / 打包

```bash
pip install pygame -i https://pypi.tuna.tsinghua.edu.cn/simple
pyinstaller --onefile --windowed --name 飞机大战 plane_war.py
```

> 打包后的程序数据与存档保存在 `%APPDATA%\PlaneWar\`。
