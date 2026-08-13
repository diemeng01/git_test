# 豆瓣 Top 250 爬虫

- **技术**：`requests` + `BeautifulSoup`
- **功能**：爬取豆瓣电影 Top 250 的排名、中文名、导演、上映年份、评分、一句经典短评
- **输出**：`movies.csv`（UTF-8 编码，写入本目录）

## 运行

```bash
python spider.py
```

## 依赖安装

```bash
pip install requests beautifulsoup4 -i https://pypi.tuna.tsinghua.edu.cn/simple
```

## 说明

- 每抓一页自动暂停 2 秒防封
- 完整异常处理，单页失败不中断
- 数据供 `02_movie_analysis` 与 `04_web_portfolio` 使用（已各自放置副本）
