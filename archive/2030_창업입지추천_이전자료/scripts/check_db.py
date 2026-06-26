# -*- coding: utf-8 -*-
import sqlite3

conn = sqlite3.connect("data/processed/kamis.db")
cur = conn.execute("""
    SELECT item_name,
           COUNT(*)          AS cnt,
           MIN(date)         AS start_date,
           MAX(date)         AS end_date,
           ROUND(AVG(price)) AS avg_price
    FROM daily_price
    GROUP BY item_name
    ORDER BY item_name
""")
rows = cur.fetchall()
conn.close()

print(f"{'품목':<16} {'일수':>5} {'시작일':>12} {'종료일':>12} {'평균가':>10}")
print("-" * 60)
for r in rows:
    print(f"{r[0]:<16} {r[1]:>5} {r[2]:>12} {r[3]:>12} {r[4]:>10,.0f}원")
print(f"\n총 {sum(r[1] for r in rows):,}건 / {len(rows)}개 품목")
