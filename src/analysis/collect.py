# -*- coding: utf-8 -*-
"""일별 KAMIS 데이터 수집 배치."""
import yaml
from datetime import date

from src.api.kamis import get_period_price
from src.db.store import init_db, save_daily


def load_items(config_path: str = "config/items.yaml") -> list[dict]:
    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f)["items"]


def parse_price(raw: dict) -> list[dict]:
    """periodProductList 응답에서 날짜·가격 리스트 추출."""
    try:
        return raw["data"]["item"]
    except (KeyError, TypeError):
        return []


def collect_today(region: str = "1101") -> None:
    """대표 품목 전체의 오늘 가격을 수집해 DB에 저장."""
    today = date.today().strftime("%Y-%m-%d")
    items = load_items()
    records = []
    skipped = []

    for item in items:
        raw = get_period_price(
            itemcategorycode = str(item["category"]),
            itemcode         = str(item["item_code"]),
            kindcode         = str(item.get("kind_code", "00")),
            rankcode         = str(item.get("rank_code", "04")),
            start            = today,
            end              = today,
            country          = region,
        )

        rows = parse_price(raw)
        if not rows:
            skipped.append(item["name"])
            continue

        # 오늘 날짜의 가장 마지막 레코드 사용
        price_str = rows[-1].get("price", "")
        try:
            price = float(price_str.replace(",", ""))
        except ValueError:
            skipped.append(item["name"])
            continue

        records.append({
            "date"      : today,
            "item_code" : str(item["item_code"]),
            "item_name" : item["name"],
            "unit"      : item.get("unit", "-"),
            "price"     : price,
            "region"    : region,
        })

    if records:
        save_daily(records)

    print(f"[COLLECT] {today} — 수집 {len(records)}/{len(items)}건"
          + (f" | 건너뜀: {skipped}" if skipped else ""))


def collect_range(start: str, end: str, region: str = "1101") -> None:
    """기간 데이터 수집 (과거 데이터 보정용).

    Args:
        start / end: "YYYY-MM-DD"
    """
    items = load_items()
    records = []

    for item in items:
        raw = get_period_price(
            itemcategorycode = str(item["category"]),
            itemcode         = str(item["item_code"]),
            kindcode         = str(item.get("kind_code", "00")),
            rankcode         = str(item.get("rank_code", "04")),
            start            = start,
            end              = end,
            country          = region,
        )

        for row in parse_price(raw):
            price_str = row.get("price", "")
            try:
                price = float(price_str.replace(",", ""))
            except ValueError:
                continue

            yyyy = row.get("yyyy", "")
            regday = row.get("regday", "")   # "MM/DD"
            if yyyy and regday:
                m, d = regday.split("/")
                row_date = f"{yyyy}-{m}-{d}"
            else:
                continue

            records.append({
                "date"      : row_date,
                "item_code" : str(item["item_code"]),
                "item_name" : item["name"],
                "unit"      : item.get("unit", "-"),
                "price"     : price,
                "region"    : region,
            })

    if records:
        save_daily(records)
    print(f"[COLLECT RANGE] {start}~{end} : {len(records)}건 저장")


if __name__ == "__main__":
    init_db()
    # 오늘 + 최근 12개월 과거 데이터 한 번에 수집
    from datetime import date, timedelta
    today     = date.today()
    start_12m = (today.replace(day=1) - timedelta(days=365)).strftime("%Y-%m-%d")
    end_str   = today.strftime("%Y-%m-%d")

    print("=== 12개월 과거 데이터 수집 (최초 1회) ===")
    collect_range(start_12m, end_str)
