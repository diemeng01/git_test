# -*- coding: utf-8 -*-
"""
豆瓣 Top 250 电影作品集网站 —— Flask
- 首页 /          : 电影列表（支持按评分 / 年份筛选 + 导演搜索）
- 小游戏 /tetris  : 俄罗斯方块（浏览器版）
- 数据            : 首次启动从 movies.csv 导入 SQLite（movies.db）
启动：python app.py  -> 浏览器访问 http://localhost:5000
"""

import csv
import os
import sqlite3

from flask import Flask, g, render_template, request

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "movies.db")
CSV_PATH = os.path.join(BASE_DIR, "movies.csv")

app = Flask(__name__)


def get_db():
    """获取当前请求的 SQLite 连接。"""
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def _import_csv():
    """从 movies.csv 导入数据到 SQLite。"""
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS movies (
            rank     INTEGER PRIMARY KEY,
            title    TEXT NOT NULL,
            director TEXT NOT NULL,
            year     INTEGER,
            rating   REAL,
            quote    TEXT
        )
        """
    )
    with open(CSV_PATH, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            conn.execute(
                "INSERT OR IGNORE INTO movies "
                "(rank, title, director, year, rating, quote) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    int(row["rank"]),
                    row["title"],
                    row["director"],
                    int(row["year"]) if row["year"] else None,
                    float(row["rating"]) if row["rating"] else None,
                    (row.get("quote") or "").strip(),
                ),
            )
    conn.commit()
    conn.close()
    print(f"已将 movies.csv 导入 {DB_PATH}")


def init_db():
    """确保数据库存在且包含数据。"""
    if not os.path.exists(DB_PATH):
        _import_csv()
        return
    conn = sqlite3.connect(DB_PATH)
    try:
        count = conn.execute("SELECT COUNT(*) FROM movies").fetchone()[0]
    except sqlite3.OperationalError:
        count = 0
    conn.close()
    if count == 0:
        _import_csv()


@app.route("/")
def index():
    """电影列表页，支持评分区间 / 年份 / 导演名 筛选。"""
    rating_min = request.args.get("rating_min", type=float)
    rating_max = request.args.get("rating_max", type=float)
    year = request.args.get("year", type=int)
    q = request.args.get("q", "").strip()

    sql = "SELECT * FROM movies WHERE 1=1"
    params = []
    if rating_min is not None:
        sql += " AND rating >= ?"
        params.append(rating_min)
    if rating_max is not None:
        sql += " AND rating <= ?"
        params.append(rating_max)
    if year:
        sql += " AND year = ?"
        params.append(year)
    if q:
        sql += " AND director LIKE ?"
        params.append(f"%{q}%")
    sql += " ORDER BY rank"

    movies = get_db().execute(sql, params).fetchall()
    return render_template(
        "index.html",
        movies=movies,
        q=q,
        rating_min=rating_min,
        rating_max=rating_max,
        year=year,
    )


@app.route("/tetris")
def tetris():
    """俄罗斯方块小游戏页。"""
    return render_template("tetris.html")


if __name__ == "__main__":
    init_db()
    app.run(host="127.0.0.1", port=5000, debug=True)
