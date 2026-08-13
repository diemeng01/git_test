# -*- coding: utf-8 -*-
"""
豆瓣电影 Top 250 爬虫
- 使用 requests + BeautifulSoup
- 提取：排名、中文名、导演、上映年份、评分、一句经典短评
- 每页请求后暂停 2 秒，防止被封
- 结果保存到本地 movies.csv（UTF-8 编码）
"""

import csv
import os
import re
import time

import requests
from bs4 import BeautifulSoup

# 输出文件基于脚本所在目录，保证从任何位置运行都能找到
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

BASE_URL = "https://movie.douban.com/top250"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}


def fetch_page(start: int) -> list:
    """抓取指定起始位置的豆瓣 Top 250 页面，返回电影信息列表。"""
    params = {"start": start, "filter": ""}
    resp = requests.get(BASE_URL, params=params, headers=HEADERS, timeout=10)
    resp.raise_for_status()  # 非 2xx 状态码抛出异常
    resp.encoding = "utf-8"

    soup = BeautifulSoup(resp.text, "html.parser")
    items = soup.select("ol.grid_view li")
    movies = []

    for item in items:
        # 排名
        rank = item.select_one("div.pic em").get_text(strip=True)

        # 中文名（标题中 '/' 分隔多个名称，取第一个）
        title_node = item.select_one("div.hd span.title")
        title = title_node.get_text(strip=True) if title_node else ""

        # 导演 / 上映年份（位于 info 的 p 标签内）
        info = item.select_one("div.info div.bd p")
        info_text = info.get_text("\n", strip=True) if info else ""
        lines = [line.strip() for line in info_text.split("\n") if line.strip()]

        director = ""
        year = ""
        for line in lines:
            if "导演" in line:
                director = line.split("导演:", 1)[-1].split("\xa0\xa0\xa0")[0].strip()
            elif "主演" in line:
                continue
        # 年份行通常是 "1994 / 中国大陆 / ..."，
        # 老片可能是 "1961(中国大陆) / 动画 / ..."，用正则只取 4 位数字
        year_line = next((line for line in lines if "/" in line and line[0].isdigit()), "")
        if year_line:
            m = re.match(r"(\d{4})", year_line)
            year = m.group(1) if m else ""

        # 评分（部分页面评级位于 div.star 内，部分直接位于 div.bd，用通用选择器兼容）
        rating_node = item.select_one(".rating_num")
        rating = rating_node.get_text(strip=True) if rating_node else ""

        # 一句经典短评（标准页面为 span.inq，部分页面无该 class，用通用选择器兼容）
        quote_node = item.select_one("p.quote span")
        quote = quote_node.get_text(strip=True) if quote_node else ""

        movies.append(
            {
                "rank": rank,
                "title": title,
                "director": director,
                "year": year,
                "rating": rating,
                "quote": quote,
            }
        )

    return movies


def main() -> None:
    all_movies = []

    for page in range(10):
        start = page * 25
        try:
            print(f"正在抓取第 {page + 1}/10 页 (start={start}) ...")
            movies = fetch_page(start)
            all_movies.extend(movies)
            print(f"  第 {page + 1} 页获取到 {len(movies)} 条数据")
        except requests.RequestException as exc:
            print(f"第 {page + 1} 页请求失败: {exc}")
        except Exception as exc:  # 解析等其它异常
            print(f"第 {page + 1} 页处理出错: {exc}")

        # 每页抓取后暂停 2 秒，防止被封
        if page < 9:
            time.sleep(2)

    if not all_movies:
        print("未获取到任何数据，程序退出。")
        return

    # 写入 CSV（UTF-8 编码，带 BOM 以便 Excel 直接打开不乱码）
    csv_path = os.path.join(BASE_DIR, "movies.csv")
    try:
        with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=["rank", "title", "director", "year", "rating", "quote"],
            )
            writer.writeheader()
            writer.writerows(all_movies)
        print(f"数据已保存到 {csv_path}，共 {len(all_movies)} 条记录。")
    except OSError as exc:
        print(f"写入文件失败: {exc}")


if __name__ == "__main__":
    main()
