# 豆瓣 Top 250 数据分析

- **技术**：`pandas` + `matplotlib` + `plotly`
- **功能**：统计评分分布、导演作品数排名、年份/年代分布并生成图表
- **输入**：`movies.csv`（本目录内）
- **输出**：
  - `rating_dist.png` 评分分布直方图
  - `director_top10.png` 导演作品数 Top 10
  - `year_dist.png` 按年份分布折线图
  - `decade_dist.png` 按年代分布柱状图
  - `movies_analysis.html` plotly 交互式图表网页

## 运行

```bash
python analyze_movies.py          # 保存图表 + 打印统计摘要
python analyze_movies.py --show   # 额外弹出图表窗口
```

## 依赖安装

```bash
pip install pandas matplotlib plotly -i https://pypi.tuna.tsinghua.edu.cn/simple
```
