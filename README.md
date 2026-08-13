# 🐍 我的 Python 作品集

按项目整理的 Python 作品集，每个项目独立成一个目录（"一个项目一个包"）。

## 项目总览

| 目录 | 项目 | 技术栈 | 说明 |
|------|------|--------|------|
| `01_douban_spider` | 豆瓣 Top 250 爬虫 | requests + BeautifulSoup | 爬取电影排名/导演/年份/评分/短评 |
| `02_movie_analysis` | 数据分析 | pandas + matplotlib + plotly | 评分分布、导演排名、年份分布并出图 |
| `03_tetris` | 俄罗斯方块 | pygame | 桌面小游戏，含投影预览、消行特效与音效 |
| `04_web_portfolio` | 作品集网站 | Flask + SQLite | 电影列表（筛选/搜索）+ 俄罗斯方块网页版 |
| `05_plane_war` | 飞机大战 | pygame | 射击游戏，含打包好的可执行程序 |

## 各项目入口

- 爬虫：`01_douban_spider/spider.py`
- 分析：`02_movie_analysis/analyze_movies.py`
- 游戏：`03_tetris/tetris.py`、`05_plane_war/plane_war.py`
- 网站：`04_web_portfolio/app.py`（启动后访问 http://localhost:5000）
- 可直接玩的程序：`05_plane_war/dist/飞机大战.exe`

> 各项目依赖安装可用清华镜像：`pip install <包名> -i https://pypi.tuna.tsinghua.edu.cn/simple`

> 根目录的 `hello.py`、`fruit.txt` 等为早期测试文件，不属于任何项目，暂留此处。
