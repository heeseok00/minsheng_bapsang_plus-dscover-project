# -*- coding: utf-8 -*-
"""민생밥상+ 스마트 장바구니 대시보드."""
import os
import requests
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import date, timedelta

try:
    from dotenv import load_dotenv
    load_dotenv("config/.env")
except Exception:
    pass

CERT_KEY = (st.secrets.get("KAMIS_CERT_KEY", "") or os.getenv("KAMIS_CERT_KEY", "")).strip()
CERT_ID  = (st.secrets.get("KAMIS_CERT_ID",  "") or os.getenv("KAMIS_CERT_ID",  "")).strip()

st.set_page_config(
    page_title="민생밥상+ 스마트 장바구니",
    page_icon="🛒",
    layout="wide",
)

# ── 스타일 ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  .hero-card {
    background: linear-gradient(135deg, #1a6b3c 0%, #2d9e5f 100%);
    color: white;
    border-radius: 12px;
    padding: 20px 24px;
    margin-bottom: 8px;
  }
  .hero-title { font-size: 22px; font-weight: 700; margin: 0 0 4px 0; }
  .hero-sub   { font-size: 13px; opacity: 0.85; margin: 0; }
  .drop-badge {
    background: #ff4b4b;
    color: white;
    border-radius: 8px;
    padding: 6px 14px;
    font-size: 26px;
    font-weight: 800;
    text-align: center;
    margin-bottom: 6px;
  }
  .item-name  { font-size: 17px; font-weight: 700; margin-bottom: 2px; }
  .item-price { font-size: 13px; color: #555; }
  .price-down { color: #0068c9; font-weight: 600; }
  .price-up   { color: #d62728; font-weight: 600; }
  .section-title {
    font-size: 18px; font-weight: 700;
    border-left: 4px solid #1a6b3c;
    padding-left: 10px;
    margin: 28px 0 14px 0;
  }
  .compare-box {
    border-radius: 10px;
    padding: 16px;
    margin-bottom: 10px;
  }
  .market-tag {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 600;
    margin-right: 6px;
  }
</style>
""", unsafe_allow_html=True)

# ── KAMIS API ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_period(category, code, kind, rank, start, end):
    url = "https://www.kamis.or.kr/service/price/xml.do"
    params = dict(
        action="periodProductList", p_cert_key=CERT_KEY, p_cert_id=CERT_ID,
        p_returntype="json", p_productclscode="01",
        p_startday=start, p_endday=end,
        p_itemcategorycode=category, p_itemcode=code,
        p_kindcode=kind, p_productrankcode=rank,
        p_countrycode="1101", p_convert_kg_yn="N",
    )
    try:
        rows = requests.get(url, params=params, timeout=10).json()["data"]["item"]
        result = []
        for r in rows:
            try:
                price = float(r["price"].replace(",", ""))
                m, d  = r["regday"].split("/")
                result.append({"date": f"{r['yyyy']}-{m}-{d}", "price": price})
            except Exception:
                continue
        return result
    except Exception:
        return []

# ── 품목 정의 ─────────────────────────────────────────────────────────────
ITEMS = [
    {"name":"배추",         "cat":"200","code":"212","kind":"00","rank":"04","unit":"1포기","qty":2},
    {"name":"무",           "cat":"200","code":"213","kind":"00","rank":"04","unit":"1개",  "qty":2},
    {"name":"양파",         "cat":"200","code":"215","kind":"00","rank":"04","unit":"1kg",  "qty":2},
    {"name":"대파",         "cat":"200","code":"216","kind":"00","rank":"04","unit":"1kg",  "qty":0.5},
    {"name":"감자",         "cat":"200","code":"217","kind":"00","rank":"04","unit":"1kg",  "qty":1},
    {"name":"고구마",       "cat":"200","code":"218","kind":"00","rank":"04","unit":"1kg",  "qty":0.5},
    {"name":"시금치",       "cat":"200","code":"231","kind":"00","rank":"04","unit":"1kg",  "qty":0.5},
    {"name":"상추",         "cat":"200","code":"232","kind":"00","rank":"04","unit":"100g", "qty":4},
    {"name":"오이",         "cat":"200","code":"221","kind":"00","rank":"04","unit":"10개", "qty":10},
    {"name":"호박",         "cat":"200","code":"222","kind":"00","rank":"04","unit":"1개",  "qty":4},
    {"name":"사과",         "cat":"300","code":"311","kind":"00","rank":"04","unit":"10개", "qty":10},
    {"name":"배",           "cat":"300","code":"312","kind":"00","rank":"04","unit":"10개", "qty":4},
    {"name":"토마토",       "cat":"300","code":"321","kind":"00","rank":"04","unit":"1kg",  "qty":1},
    {"name":"닭고기",       "cat":"400","code":"412","kind":"00","rank":"04","unit":"1kg",  "qty":1.5},
    {"name":"계란",         "cat":"400","code":"411","kind":"00","rank":"04","unit":"30개", "qty":60},
]

# ── 날짜 범위 ─────────────────────────────────────────────────────────────
today      = date.today()
end_str    = today.strftime("%Y-%m-%d")
start_12m  = (today - timedelta(days=365)).strftime("%Y-%m-%d")

# 지난주 / 이번주
this_mon        = today - timedelta(days=today.weekday())
last_mon        = this_mon - timedelta(days=7)
last_sun        = this_mon - timedelta(days=1)
this_week_start = this_mon.strftime("%Y-%m-%d")
last_week_start = last_mon.strftime("%Y-%m-%d")
last_week_end   = last_sun.strftime("%Y-%m-%d")

# 지난달 / 이번달
this_month_start = today.replace(day=1).strftime("%Y-%m-%d")
last_month_end   = (today.replace(day=1) - timedelta(days=1))
last_month_start = last_month_end.replace(day=1).strftime("%Y-%m-%d")
last_month_end   = last_month_end.strftime("%Y-%m-%d")

# 종합 점수 가중치
W_WOW = 0.35   # 지난주 대비 (단기 트렌드)
W_MOM = 0.30   # 지난달 대비 (중기 트렌드)
W_YOY = 0.35   # 12개월 평균 대비 (장기 기준)

# ── 데이터 수집 ───────────────────────────────────────────────────────────
with st.spinner("KAMIS 가격 데이터 불러오는 중..."):
    data = []
    for item in ITEMS:
        rows = fetch_period(item["cat"], item["code"], item["kind"], item["rank"], start_12m, end_str)
        if len(rows) < 2:
            continue

        prices    = [r["price"] for r in rows]
        avg_12m   = sum(prices) / len(prices)
        now_price = prices[-1]

        # 이번주 / 지난주 평균
        this_week_rows = [r["price"] for r in rows if r["date"] >= this_week_start]
        last_week_rows = [r["price"] for r in rows if last_week_start <= r["date"] <= last_week_end]
        this_week_avg  = sum(this_week_rows) / len(this_week_rows) if this_week_rows else now_price
        last_week_avg  = sum(last_week_rows) / len(last_week_rows) if last_week_rows else now_price

        # 이번달 / 지난달 평균
        this_month_rows = [r["price"] for r in rows if r["date"] >= this_month_start]
        last_month_rows = [r["price"] for r in rows if last_month_start <= r["date"] <= last_month_end]
        this_month_avg  = sum(this_month_rows) / len(this_month_rows) if this_month_rows else now_price
        last_month_avg  = sum(last_month_rows) / len(last_month_rows) if last_month_rows else now_price

        wow_pct = round((this_week_avg  - last_week_avg)  / last_week_avg  * 100, 1) if last_week_avg  else 0
        mom_pct = round((this_month_avg - last_month_avg) / last_month_avg * 100, 1) if last_month_avg else 0
        yoy_pct = round((now_price      - avg_12m)        / avg_12m        * 100, 1) if avg_12m        else 0

        # 종합 절감 점수: 세 지표의 가중 평균 (음수일수록 더 저렴)
        score = W_WOW * wow_pct + W_MOM * mom_pct + W_YOY * yoy_pct

        # 지표 일치도: 세 방향이 모두 하락이면 확신도 높음
        direction_count = sum([wow_pct < 0, mom_pct < 0, yoy_pct < 0])
        confidence = {3: "높음", 2: "보통", 1: "낮음", 0: "없음"}[direction_count]

        data.append({**item,
            "rows": rows, "now": now_price, "avg_12m": avg_12m,
            "this_week": this_week_avg, "last_week": last_week_avg,
            "this_month": this_month_avg, "last_month": last_month_avg,
            "wow_pct": wow_pct, "mom_pct": mom_pct, "yoy_pct": yoy_pct,
            "score": round(score, 2), "confidence": confidence,
        })

# ── 헤더 ──────────────────────────────────────────────────────────────────
week_no = today.isocalendar()[1]
st.markdown(f"""
<div class="hero-card">
  <p class="hero-title">🛒 민생밥상+ 주간 알뜰장보기 {week_no}호</p>
  <p class="hero-sub">발행일 {end_str} · KAMIS 공공 데이터 기반 · 서울 소매가 기준</p>
</div>
""", unsafe_allow_html=True)

# ── 종합 추천 TOP 3 ───────────────────────────────────────────────────────
st.markdown('<p class="section-title">📉 지금 사기 가장 좋은 품목 TOP 3</p>', unsafe_allow_html=True)
st.caption(f"종합 점수 = 지난주 대비 {int(W_WOW*100)}% + 지난달 대비 {int(W_MOM*100)}% + 12개월 평균 대비 {int(W_YOY*100)}% 가중 합산 · 점수가 낮을수록 더 저렴")

top3 = sorted(data, key=lambda x: x["score"])[:3]

if top3:
    cols = st.columns(3)
    conf_color = {"높음": "#1a6b3c", "보통": "#e07b00", "낮음": "#888", "없음": "#bbb"}
    for col, d in zip(cols, top3):
        with col:
            c = conf_color[d["confidence"]]
            st.markdown(f"""
            <div style="border:2px solid {c}; border-radius:12px; padding:18px; text-align:center;">
              <div class="drop-badge">▼ {abs(d['score']):.1f}점</div>
              <div class="item-name">{d['name']} / {d['unit']}</div>
              <div class="item-price" style="margin-top:8px; line-height:1.8;">
                지난주 대비 <b class="price-down">{d['wow_pct']:+.1f}%</b><br>
                지난달 대비 <b class="price-down">{d['mom_pct']:+.1f}%</b><br>
                12개월 평균 대비 <b class="price-down">{d['yoy_pct']:+.1f}%</b>
              </div>
              <div style="margin-top:10px; font-size:12px; color:{c}; font-weight:700;">
                신뢰도 {d['confidence']}
              </div>
            </div>
            """, unsafe_allow_html=True)
else:
    st.info("추천 데이터가 없습니다.")

# ── 주요 농축산물 소매가격 표 ─────────────────────────────────────────────
st.markdown('<p class="section-title">📊 주요 농축산물 소매가격</p>', unsafe_allow_html=True)
st.caption(f"(단위: 원, 상품)   지난주 {last_week_start}~{last_week_end} / 이번주 {this_week_start}~{end_str}")

if data:
    half = len(data) // 2 + len(data) % 2
    left, right = data[:half], data[half:]

    def make_table(items):
        rows = []
        for d in items:
            pct  = d["wow_pct"]
            flag = f"🔵 {pct}%" if pct < 0 else (f"🔴 +{pct}%" if pct > 0 else f"➖ {pct}%")
            rows.append({
                "품목": d["name"], "단위": d["unit"],
                "지난주": f"{d['last_week']:,.0f}",
                "이번주": f"{d['this_week']:,.0f}",
                "등락(%)": flag,
            })
        return pd.DataFrame(rows)

    c1, c2 = st.columns(2)
    with c1:
        st.dataframe(make_table(left), use_container_width=True, hide_index=True)
    with c2:
        st.dataframe(make_table(right), use_container_width=True, hide_index=True)

# ── 12개월 평균 대비 저가 TOP 5 ───────────────────────────────────────────
st.markdown('<p class="section-title">💰 지금 사기 좋은 TOP 5 (12개월 평균 대비)</p>', unsafe_allow_html=True)

cheap5 = sorted([d for d in data if d["yoy_pct"] < 0], key=lambda x: x["yoy_pct"])[:5]
total_saving = sum(max((d["avg_12m"] - d["now"]) * d["qty"], 0) for d in cheap5)

m1, m2, m3 = st.columns(3)
m1.metric("저가 품목 수",     f"{len(cheap5)}종")
m2.metric("예상 월 절감액",   f"약 {total_saving:,.0f}원")
m3.metric("비교 기준",        "최근 12개월 평균가")

if cheap5:
    df5 = pd.DataFrame([{
        "품목": d["name"], "단위": d["unit"],
        "현재가": f"{d['now']:,.0f}원",
        "12개월 평균": f"{d['avg_12m']:,.0f}원",
        "절감률": f"▼ {abs(d['yoy_pct'])}%",
    } for d in cheap5])
    st.dataframe(df5, use_container_width=True, hide_index=True)

# ── 품목별 가격 추이 차트 ─────────────────────────────────────────────────
st.markdown('<p class="section-title">📈 품목별 가격 추이</p>', unsafe_allow_html=True)

names    = [d["name"] for d in data]
selected = st.selectbox("품목 선택", names if names else ["데이터 없음"])

sel = next((d for d in data if d["name"] == selected), None)
if sel:
    df_chart = pd.DataFrame(sel["rows"]).sort_values("date")
    df_chart = df_chart[df_chart["date"] >= (today - timedelta(days=90)).strftime("%Y-%m-%d")]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_chart["date"], y=df_chart["price"],
        mode="lines+markers", name="일별 가격",
        line=dict(color="#1a6b3c", width=2), marker=dict(size=4),
    ))
    fig.add_hline(y=sel["avg_12m"], line_dash="dash", line_color="#aaa",
                  annotation_text=f"12개월 평균 {sel['avg_12m']:,.0f}원",
                  annotation_position="top left")
    fig.update_layout(
        yaxis_title="가격 (원)", xaxis_title="날짜",
        height=340, margin=dict(t=20, b=20), plot_bgcolor="white",
        yaxis=dict(gridcolor="#f0f0f0"), xaxis=dict(gridcolor="#f0f0f0"),
    )
    st.plotly_chart(fig, use_container_width=True)

# ── 전체 현황 ─────────────────────────────────────────────────────────────
with st.expander("전체 품목 종합 순위 보기"):
    st.caption("종합 점수 기준 오름차순 정렬 (낮을수록 더 저렴)")
    df_all = pd.DataFrame([{
        "순위": i+1,
        "품목": d["name"],
        "단위": d["unit"],
        "현재가": f"{d['now']:,.0f}원",
        "지난주 대비": f"{'▼' if d['wow_pct']<0 else '▲'} {abs(d['wow_pct'])}%",
        "지난달 대비": f"{'▼' if d['mom_pct']<0 else '▲'} {abs(d['mom_pct'])}%",
        "12개월 평균 대비": f"{'▼' if d['yoy_pct']<0 else '▲'} {abs(d['yoy_pct'])}%",
        "종합 점수": f"{d['score']:+.1f}",
        "신뢰도": d["confidence"],
    } for i, d in enumerate(sorted(data, key=lambda x: x["score"]))])
    st.dataframe(df_all, use_container_width=True, hide_index=True)

st.divider()
st.caption("데이터 출처: 한국농수산식품유통공사(aT) KAMIS Open API  |  민생밥상+ DScover팀 프로토타입")
