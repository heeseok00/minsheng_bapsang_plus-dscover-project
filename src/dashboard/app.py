# -*- coding: utf-8 -*-
"""민생밥상+ 스마트 장바구니 대시보드 (Streamlit Community Cloud 배포용)."""
import os
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import date, timedelta
from dotenv import load_dotenv

load_dotenv("config/.env")

# Streamlit Cloud Secrets → 환경변수 fallback
CERT_KEY = st.secrets.get("KAMIS_CERT_KEY", os.getenv("KAMIS_CERT_KEY", ""))
CERT_ID  = st.secrets.get("KAMIS_CERT_ID",  os.getenv("KAMIS_CERT_ID",  ""))

st.set_page_config(
    page_title="민생밥상+ · 스마트 장바구니",
    page_icon="🛒",
    layout="wide",
)

# ── KAMIS 직접 호출 (캐싱 1시간) ────────────────────────────────────────
import requests

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_kamis(category: str, code: str, kind: str, rank: str,
                start: str, end: str) -> list[dict]:
    """KAMIS API #2 periodProductList 호출 → [{date, price}, ...] 반환."""
    url = "https://www.kamis.or.kr/service/price/xml.do"
    params = {
        "action"            : "periodProductList",
        "p_cert_key"        : CERT_KEY,
        "p_cert_id"         : CERT_ID,
        "p_returntype"      : "json",
        "p_productclscode"  : "01",
        "p_startday"        : start,
        "p_endday"          : end,
        "p_itemcategorycode": category,
        "p_itemcode"        : code,
        "p_kindcode"        : kind,
        "p_productrankcode" : rank,
        "p_countrycode"     : "1101",
        "p_convert_kg_yn"   : "N",
    }
    try:
        r = requests.get(url, params=params, timeout=10)
        rows = r.json()["data"]["item"]
        result = []
        for row in rows:
            try:
                price = float(row["price"].replace(",", ""))
                yyyy  = row.get("yyyy", "")
                mm, dd = row["regday"].split("/")
                result.append({"date": f"{yyyy}-{mm}-{dd}", "price": price})
            except Exception:
                continue
        return result
    except Exception:
        return []


# ── 품목 정의 ────────────────────────────────────────────────────────────
ITEMS = [
    {"name": "배추",       "category": "200", "code": "212", "kind": "00", "rank": "04", "unit": "1포기", "qty": 2},
    {"name": "무",         "category": "200", "code": "213", "kind": "00", "rank": "04", "unit": "1개",   "qty": 2},
    {"name": "양파",       "category": "200", "code": "215", "kind": "00", "rank": "04", "unit": "1kg",   "qty": 2},
    {"name": "대파",       "category": "200", "code": "216", "kind": "00", "rank": "04", "unit": "1kg",   "qty": 0.5},
    {"name": "감자",       "category": "200", "code": "217", "kind": "00", "rank": "04", "unit": "1kg",   "qty": 1},
    {"name": "고구마",     "category": "200", "code": "218", "kind": "00", "rank": "04", "unit": "1kg",   "qty": 0.5},
    {"name": "시금치",     "category": "200", "code": "231", "kind": "00", "rank": "04", "unit": "1kg",   "qty": 0.5},
    {"name": "상추",       "category": "200", "code": "232", "kind": "00", "rank": "04", "unit": "100g",  "qty": 4},
    {"name": "오이",       "category": "200", "code": "221", "kind": "00", "rank": "04", "unit": "10개",  "qty": 10},
    {"name": "호박",       "category": "200", "code": "222", "kind": "00", "rank": "04", "unit": "1개",   "qty": 4},
    {"name": "사과",       "category": "300", "code": "311", "kind": "00", "rank": "04", "unit": "10개",  "qty": 10},
    {"name": "배",         "category": "300", "code": "312", "kind": "00", "rank": "04", "unit": "10개",  "qty": 4},
    {"name": "토마토",     "category": "300", "code": "321", "kind": "00", "rank": "04", "unit": "1kg",   "qty": 1},
    {"name": "닭고기",     "category": "400", "code": "412", "kind": "00", "rank": "04", "unit": "1kg",   "qty": 1.5},
    {"name": "계란",       "category": "400", "code": "411", "kind": "00", "rank": "04", "unit": "30개",  "qty": 60},
]

# ── 데이터 로드 ───────────────────────────────────────────────────────────
today     = date.today()
end_str   = today.strftime("%Y-%m-%d")
start_12m = (today - timedelta(days=365)).strftime("%Y-%m-%d")
start_30d = (today - timedelta(days=30)).strftime("%Y-%m-%d")

st.title("🛒 민생밥상+  스마트 장바구니")
st.caption(f"KAMIS 공공 데이터 기반 · 기준일 {end_str} · 서울 소매가")
st.divider()

with st.spinner("KAMIS 가격 데이터 불러오는 중..."):
    results = []
    for item in ITEMS:
        rows_12m = fetch_kamis(
            item["category"], item["code"], item["kind"], item["rank"],
            start_12m, end_str,
        )
        if not rows_12m:
            continue

        prices    = [r["price"] for r in rows_12m]
        avg_12m   = sum(prices) / len(prices)
        today_price = prices[-1]          # 가장 최근 가격
        ratio       = today_price / avg_12m if avg_12m else 1.0
        saving_pct  = round((1 - ratio) * 100, 1)

        results.append({
            **item,
            "rows"       : rows_12m,
            "today"      : today_price,
            "avg_12m"    : avg_12m,
            "ratio"      : ratio,
            "saving_pct" : saving_pct,
            "is_cheap"   : ratio < 1.0,
        })

# ── TOP 5 저가 품목 ────────────────────────────────────────────────────────
cheap  = sorted([r for r in results if r["is_cheap"]],
                key=lambda x: x["saving_pct"], reverse=True)
top5   = cheap[:5]

total_saving = sum(
    max((r["avg_12m"] - r["today"]) * r["qty"], 0) for r in top5
)

col1, col2, col3 = st.columns(3)
col1.metric("이번 주 저가 품목",  f"{len(cheap)}종")
col2.metric("TOP 5 예상 월 절감액", f"약 {total_saving:,.0f}원")
col3.metric("비교 기준", "최근 12개월 평균가")

st.divider()
st.subheader("📉 지금 사기 좋은 TOP 5")

if top5:
    df_top = pd.DataFrame([{
        "품목"          : r["name"],
        "단위"          : r["unit"],
        "오늘 가격"     : f"{r['today']:,.0f}원",
        "12개월 평균"   : f"{r['avg_12m']:,.0f}원",
        "절감률"        : f"▼ {r['saving_pct']}%",
    } for r in top5])
    st.dataframe(df_top, use_container_width=True, hide_index=True)
else:
    st.info("현재 12개월 평균보다 저렴한 품목이 없습니다.")

st.divider()

# ── 품목별 가격 추이 ──────────────────────────────────────────────────────
st.subheader("📈 품목별 최근 30일 가격 추이")

name_map  = {r["name"]: r for r in results}
item_names = [r["name"] for r in results]
selected   = st.selectbox("품목 선택", item_names if item_names else ["데이터 없음"])

if selected and selected in name_map:
    r    = name_map[selected]
    df30 = pd.DataFrame(r["rows"]).sort_values("date")
    df30 = df30[df30["date"] >= start_30d]

    if not df30.empty:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df30["date"], y=df30["price"],
            mode="lines+markers", name="일별 가격",
            line=dict(color="#FF6B35", width=2),
            marker=dict(size=5),
        ))
        fig.add_hline(
            y=r["avg_12m"], line_dash="dash", line_color="#888",
            annotation_text=f"12개월 평균 {r['avg_12m']:,.0f}원",
            annotation_position="top left",
        )
        fig.update_layout(
            yaxis_title="가격 (원)", xaxis_title="날짜",
            height=360, margin=dict(t=20, b=20),
            plot_bgcolor="white",
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("최근 30일 데이터가 없습니다.")

st.divider()

# ── 전체 품목 현황 ─────────────────────────────────────────────────────────
with st.expander("전체 품목 현황 보기"):
    df_all = pd.DataFrame([{
        "품목"       : r["name"],
        "단위"       : r["unit"],
        "오늘"       : f"{r['today']:,.0f}원",
        "12개월 평균": f"{r['avg_12m']:,.0f}원",
        "등락"       : f"{'▼' if r['is_cheap'] else '▲'} {abs(r['saving_pct'])}%",
        "상태"       : "저가" if r["is_cheap"] else "고가",
    } for r in sorted(results, key=lambda x: x["saving_pct"], reverse=True)])
    st.dataframe(df_all, use_container_width=True, hide_index=True)

st.caption("데이터 출처: 한국농수산식품유통공사 KAMIS Open API  |  민생밥상+ 팀 내부 프로토타입")
