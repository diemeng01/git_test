# -*- coding: utf-8 -*-
"""
豆瓣电影 Top 250 数据分析脚本
输入：movies.csv（由爬虫生成）
输出：
  - rating_dist.png   评分分布直方图
  - director_top10.png 导演作品数 Top10 条形图
  - year_dist.png     年份分布折线图
  - decade_dist.png   年代分布柱状图
  - movies_analysis.html  plotly 交互式图表网页（可选）
用法：
  python analyze_movies.py          # 仅保存图片 + 打印摘要
  python analyze_movies.py --show   # 额外弹出 matplotlib 图表窗口
"""

import os
import re
import sys
from collections import Counter

import matplotlib.pyplot as plt
import pandas as pd

# ---- 中文字体设置（避免图表中文乱码）----
plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "Arial Unicode MS"]
plt.rcParams["axes.unicode_minus"] = False

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, "movies.csv")


def load_data():
    """读取并清洗 movies.csv。"""
    df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
    # 字符串转数值，无效值置为 NaN
    df["rating"] = pd.to_numeric(df["rating"], errors="coerce")
    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df["director"] = df["director"].astype(str)
    print(f"共读取 {len(df)} 条记录，有效评分 {df['rating'].notna().sum()} 条，"
          f"有效年份 {df['year'].notna().sum()} 条。\n")
    return df


def extract_director_names(director_str):
    """拆分合导并提取中文名：'拜伦·霍华德 Byron Howard / 瑞奇·摩尔 Rich Moore'
    -> ['拜伦·霍华德', '瑞奇·摩尔']"""
    if not director_str or director_str.strip() in ("nan", "None"):
        return []
    names = []
    for part in re.split(r"[\/,，]", director_str):
        part = part.strip()
        if not part:
            continue
        # 取第一个空格前的 token（中文译名），若以英文开头则保留整段
        names.append(part.split()[0] if part.split() else part)
    return names


# ---------- 图 1：评分分布直方图 ----------
def plot_rating_distribution(df):
    fig, ax = plt.subplots(figsize=(9, 5), dpi=120)
    ratings = df["rating"].dropna()
    ax.hist(ratings, bins=24, range=(8.0, 10.0), color="#4a90d9",
            edgecolor="white", alpha=0.85)
    ax.set_title("豆瓣 Top 250 评分分布", fontsize=14, fontweight="bold")
    ax.set_xlabel("评分")
    ax.set_ylabel("电影数量")
    # 标注均值和最集中区间
    mean = ratings.mean()
    ax.axvline(mean, color="#d9534f", linestyle="--", linewidth=1.5,
               label=f"平均分 {mean:.2f}")
    ax.legend()
    fig.tight_layout()
    fig.savefig(os.path.join(BASE_DIR, "rating_dist.png"))
    plt.close(fig)
    # 控制台摘要
    print("=" * 46)
    print("【评分分布】")
    print(f"  最高分 {ratings.max():.1f} / 最低分 {ratings.min():.1f} / 平均分 {mean:.2f}")
    most = ratings.round(1).value_counts().idxmax()
    print(f"  出现最多的评分: {most} 分（{int(ratings.round(1).value_counts().max())} 部）\n")
    return ratings


# ---------- 图 2：导演作品数 Top 10 ----------
def plot_director_top10(df):
    counter = Counter()
    for d in df["director"]:
        counter.update(extract_director_names(d))
    top10 = counter.most_common(10)

    names = [n for n, _ in top10][::-1]
    counts = [c for _, c in top10][::-1]

    fig, ax = plt.subplots(figsize=(9, 6), dpi=120)
    ax.barh(names, counts, color="#5cb85c", edgecolor="white")
    for i, c in enumerate(counts):
        ax.text(c + 0.1, i, str(c), va="center", fontsize=10)
    ax.set_title("导演作品数 Top 10", fontsize=14, fontweight="bold")
    ax.set_xlabel("作品数")
    ax.set_xlim(0, max(counts) + 1)
    fig.tight_layout()
    fig.savefig(os.path.join(BASE_DIR, "director_top10.png"))
    plt.close(fig)

    print("=" * 46)
    print("【导演作品数 Top 10】")
    for rank, (name, cnt) in enumerate(top10, 1):
        print(f"  {rank:>2}. {name:<14} {cnt} 部")
    print()
    return top10


# ---------- 图 3：年份分布折线图 ----------
def plot_year_distribution(df):
    yearly = df["year"].dropna().astype(int).value_counts().sort_index()

    fig, ax = plt.subplots(figsize=(11, 5), dpi=120)
    ax.plot(yearly.index, yearly.values, color="#4a90d9",
            marker="o", markersize=4, linewidth=1.8)
    ax.fill_between(yearly.index, yearly.values, color="#4a90d9", alpha=0.2)
    ax.set_title("豆瓣 Top 250 电影按年份分布", fontsize=14, fontweight="bold")
    ax.set_xlabel("上映年份")
    ax.set_ylabel("电影数量")
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(BASE_DIR, "year_dist.png"))
    plt.close(fig)

    # 年代（十年）分布：附加柱状图（用原始年份数据，勿用去重后的 yearly.index）
    year_series = df["year"].dropna().astype(int)
    decade = (year_series // 10 * 10).value_counts().sort_index()
    fig2, ax2 = plt.subplots(figsize=(9, 5), dpi=120)
    ax2.bar([str(d) for d in decade.index], decade.values, color="#f0ad4e",
            edgecolor="white")
    for i, v in enumerate(decade.values):
        ax2.text(i, v + 0.3, str(v), ha="center", fontsize=10)
    ax2.set_title("豆瓣 Top 250 电影按年代分布", fontsize=14, fontweight="bold")
    ax2.set_xlabel("年代")
    ax2.set_ylabel("电影数量")
    fig2.tight_layout()
    fig2.savefig(os.path.join(BASE_DIR, "decade_dist.png"))
    plt.close(fig2)

    print("=" * 46)
    print("【年份分布】")
    print(f"  最早 {yearly.index.min()} 年，最晚 {yearly.index.max()} 年")
    peak_year = yearly.idxmax()
    print(f"  上榜影片最多的年份: {peak_year}（{int(yearly.max())} 部）")
    best_decade = decade.idxmax()
    print(f"  上榜影片最多的年代: {best_decade}s（{int(decade.max())} 部）\n")
    return yearly, decade


# ---------- 图 4：plotly 交互式图表（可选） ----------
def plot_interactive(df):
    try:
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots
    except ImportError:
        print("未安装 plotly，跳过交互式图表。")
        return

    ratings = df["rating"].dropna()
    yearly = df["year"].dropna().astype(int).value_counts().sort_index()
    counter = Counter()
    for d in df["director"]:
        counter.update(extract_director_names(d))
    top10 = counter.most_common(10)

    fig = make_subplots(
        rows=3, cols=1,
        subplot_titles=("评分分布", "导演作品数 Top 10", "按年份分布"),
        vertical_spacing=0.12,
    )
    # 评分直方图
    fig.add_trace(
        go.Histogram(x=ratings, nbinsx=24, marker_color="#4a90d9",
                     name="评分分布"),
        row=1, col=1,
    )
    # 导演 top10
    fig.add_trace(
        go.Bar(x=[c for _, c in top10][::-1],
               y=[n for n, _ in top10][::-1],
               orientation="h", marker_color="#5cb85c", name="导演 Top10"),
        row=2, col=1,
    )
    # 年份折线
    fig.add_trace(
        go.Scatter(x=yearly.index, y=yearly.values, mode="lines+markers",
                   line=dict(color="#f0ad4e", width=2), name="年份分布"),
        row=3, col=1,
    )
    fig.update_layout(
        title="豆瓣电影 Top 250 数据分析",
        height=1200, showlegend=False,
        font=dict(family="Microsoft YaHei"),
    )
    fig.write_html(os.path.join(BASE_DIR, "movies_analysis.html"))
    print("交互式图表已保存到 movies_analysis.html")


def main():
    show = "--show" in sys.argv
    df = load_data()

    plot_rating_distribution(df)
    plot_director_top10(df)
    plot_year_distribution(df)
    plot_interactive(df)

    print("=" * 46)
    print("已生成图片文件：")
    print("  rating_dist.png / director_top10.png / year_dist.png / decade_dist.png")
    if show:
        # 汇总展示（仅当 --show 时弹出窗口）
        plt.show()


if __name__ == "__main__":
    main()
