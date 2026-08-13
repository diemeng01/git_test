# 作品集网站（Flask）

- **技术**：`Flask` + `SQLite`
- **功能**：
  - 电影列表页 `/`：展示豆瓣 Top 250，支持评分区间、年份筛选 + 导演名搜索
  - 小游戏页 `/tetris`：俄罗斯方块（纯 JS + Canvas 浏览器版，含投影与消行特效）
- **数据**：首次启动自动从 `movies.csv` 导入 `movies.db`（本目录内）

## 运行

```bash
python app.py
```

浏览器访问 **http://localhost:5000**

## 依赖安装

```bash
pip install flask -i https://pypi.tuna.tsinghua.edu.cn/simple
```
