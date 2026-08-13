# 俄罗斯方块（pygame 桌面版）

- **技术**：`pygame`
- **功能**：经典俄罗斯方块
  - 7 种方块、墙踢旋转、难度随等级提升
  - 下落投影预览（ghost piece）
  - 消行白色闪烁特效 + 合成音效
  - 得分、等级、下一个方块预览、暂停/重开

## 运行

```bash
python tetris.py
```

## 操作

| 按键 | 功能 |
|------|------|
| `← →` | 左右移动 |
| `↑` | 旋转 |
| `↓` | 软降 |
| `空格` | 硬降 |
| `P` / `R` | 暂停 / 重开 |
| `ESC` | 退出 |

## 依赖安装

```bash
pip install pygame -i https://pypi.tuna.tsinghua.edu.cn/simple
```

> 另有网页版（JavaScript）俄罗斯方块，位于 `04_web_portfolio/templates/tetris.html`。
