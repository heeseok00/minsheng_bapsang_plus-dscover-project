# -*- coding: utf-8 -*-
"""GitHub Actions에서 실행: KAMIS 데이터 수집 후 data/kamis_latest.json 저장."""
import os, json, requests
from datetime import date, timedelta
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv("config/.env")
except Exception:
    pass

CERT_KEY = os.environ.get("KAMIS_CERT_KEY", "").strip()
CERT_ID  = os.environ.get("KAMIS_CERT_ID",  "").strip()
BASE_URL = "https://www.kamis.or.kr/service/price/xml.do"

ITEMS = [
    {"name":"배추",   "cat":"200","code":"212","kind":"00","rank":"04","unit":"1포기","qty":2},
    {"name":"무",     "cat":"200","code":"213","kind":"00","rank":"04","unit":"1개",  "qty":2},
    {"name":"양파",   "cat":"200","code":"215","kind":"00","rank":"04","unit":"1kg",  "qty":2},
    {"name":"대파",   "cat":"200","code":"216","kind":"00","rank":"04","unit":"1kg",  "qty":0.5},
    {"name":"감자",   "cat":"200","code":"217","kind":"00","rank":"04","unit":"1kg",  "qty":1},
    {"name":"고구마", "cat":"200","code":"218","kind":"00","rank":"04","unit":"1kg",  "qty":0.5},
    {"name":"시금치", "cat":"200","code":"231","kind":"00","rank":"04","unit":"1kg",  "qty":0.5},
    {"name":"상추",   "cat":"200","code":"232","kind":"00","rank":"04","unit":"100g", "qty":4},
    {"name":"오이",   "cat":"200","code":"221","kind":"00","rank":"04","unit":"10개", "qty":10},
    {"name":"호박",   "cat":"200","code":"222","kind":"00","rank":"04","unit":"1개",  "qty":4},
    {"name":"사과",   "cat":"300","code":"311","kind":"00","rank":"04","unit":"10개", "qty":10},
    {"name":"배",     "cat":"300","code":"312","kind":"00","rank":"04","unit":"10개", "qty":4},
    {"name":"토마토", "cat":"300","code":"321","kind":"00","rank":"04","unit":"1kg",  "qty":1},
    {"name":"닭고기", "cat":"400","code":"412","kind":"00","rank":"04","unit":"1kg",  "qty":1.5},
    {"name":"계란",   "cat":"400","code":"411","kind":"00","rank":"04","unit":"30개", "qty":60},
]

def fetch(cat, code, kind, rank, start, end):
    params = dict(
        action="periodProductList", p_cert_key=CERT_KEY, p_cert_id=CERT_ID,
        p_returntype="json", p_productclscode="01",
        p_startday=start, p_endday=end,
        p_itemcategorycode=cat, p_itemcode=code,
        p_kindcode=kind, p_productrankcode=rank,
        p_countrycode="1101", p_convert_kg_yn="N",
    )
    try:
        rows = requests.get(BASE_URL, params=params, timeout=15).json()["data"]["item"]
        result = []
        for r in rows:
            try:
                price = float(r["price"].replace(",", ""))
                m, d  = r["regday"].split("/")
                result.append({"date": f"{r['yyyy']}-{m}-{d}", "price": price})
            except Exception:
                continue
        return result
    except Exception as e:
        print(f"  [FAIL] {e}")
        return []

today     = date.today()
end_str   = today.strftime("%Y-%m-%d")
start_12m = (today - timedelta(days=365)).strftime("%Y-%m-%d")

print(f"[collect] {end_str} 수집 시작 / KEY={CERT_KEY[:8]}... / ID={CERT_ID}")

output = {"collected_at": end_str, "items": []}

for item in ITEMS:
    print(f"  {item['name']} ...", end=" ")
    rows = fetch(item["cat"], item["code"], item["kind"], item["rank"], start_12m, end_str)
    print(f"{len(rows)}건")
    if rows:
        output["items"].append({**item, "rows": rows})

out_path = Path("data/kamis_latest.json")
out_path.parent.mkdir(parents=True, exist_ok=True)
out_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"[collect] 저장 완료: {out_path} ({len(output['items'])}/{len(ITEMS)}종)")
