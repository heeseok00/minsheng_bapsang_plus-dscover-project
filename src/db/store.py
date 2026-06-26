# -*- coding: utf-8 -*-
"""SQLite 저장소 — KAMIS 일별 가격 수집 데이터 관리."""
import sqlite3
from datetime import date
from pathlib import Path

DB_PATH = Path("data/processed/kamis.db")


def get_conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH)


def init_db() -> None:
    """테이블 생성."""
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS daily_price (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                date        TEXT NOT NULL,
                item_code   TEXT NOT NULL,
                item_name   TEXT,
                unit        TEXT,
                price       REAL,
                region      TEXT DEFAULT '1101',
                created_at  TEXT DEFAULT (datetime('now','localtime')),
                UNIQUE(date, item_code, region)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS monthly_avg (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                yyyymm      TEXT NOT NULL,
                item_code   TEXT NOT NULL,
                item_name   TEXT,
                avg_price   REAL,
                min_price   REAL,
                max_price   REAL,
                UNIQUE(yyyymm, item_code)
            )
        """)
        conn.commit()
    print("[DB] 초기화 완료")


def save_daily(records: list[dict]) -> None:
    """일별 가격 저장.
    
    records: [{"date", "item_code", "item_name", "unit", "price", "region"}, ...]
    """
    with get_conn() as conn:
        conn.executemany("""
            INSERT OR REPLACE INTO daily_price
                (date, item_code, item_name, unit, price, region)
            VALUES
                (:date, :item_code, :item_name, :unit, :price, :region)
        """, records)
        conn.commit()
    print(f"[DB] {len(records)}건 저장")


def get_recent(item_code: str, days: int = 30) -> list[dict]:
    """최근 N일 가격 조회."""
    with get_conn() as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.execute("""
            SELECT date, price, unit
            FROM daily_price
            WHERE item_code = ?
            ORDER BY date DESC
            LIMIT ?
        """, (item_code, days))
        return [dict(r) for r in cur.fetchall()]


def get_12m_avg(item_code: str) -> float:
    """최근 12개월 평균가 계산."""
    with get_conn() as conn:
        cur = conn.execute("""
            SELECT AVG(price)
            FROM daily_price
            WHERE item_code = ?
              AND date >= date('now', '-365 days')
              AND price IS NOT NULL
        """, (item_code,))
        row = cur.fetchone()
        return row[0] if row and row[0] else 0.0
