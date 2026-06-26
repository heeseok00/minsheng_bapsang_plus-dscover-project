# -*- coding: utf-8 -*-
"""민생밥상+ 스마트 장바구니 대시보드."""
import os, requests
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import date, timedelta

try:
    from dotenv import load_dotenv
    load_dotenv("config/.env")
except Exception:
    pass

CERT_KEY = (st.secrets.get("KAMIS_CERT_KEY", "") or os.getenv("KAMIS_CERT_KEY", "")).strip()
CERT_ID  = (st.secrets.get("KAMIS_CERT_ID",  "") or os.getenv("KAMIS_CERT_ID",  "")).strip()

st.set_page_config(page_title="민생밥상+ 스마트 장바구니", page_icon="🥬", layout="wide")

# ── 글로벌 스타일 ─────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700&display=swap');

  html, body, [class*="css"] { font-family: 'Noto Sans KR', sans-serif; }

  /* 헤더 배너 */
  .banner {
    background: #1b5e38;
    color: #fff;
    border-radius: 10px;
    padding: 22px 28px;
    display: flex;
    align-items: flex-end;
    justify-content: space-between;
    margin-bottom: 4px;
  }
  .banner-title { font-size: 22px; font-weight: 700; margin: 0; letter-spacing: -0.3px; }
  .banner-sub   { font-size: 12px; opacity: 0.75; margin: 4px 0 0 0; }
  .banner-badge {
    background: #fff;
    color: #1b5e38;
    border-radius: 20px;
    padding: 6px 16px;
    font-size: 13px;
    font-weight: 700;
    white-space: nowrap;
  }

  /* 추천 카드 */
  .rec-card {
    border: 1px solid #e4e4e4;
    border-radius: 10px;
    padding: 18px 20px;
    height: 100%;
    background: #fff;
  }
  .rec-rank   { font-size: 12px; color: #888; margin: 0 0 4px 0; font-weight: 500; }
  .rec-name   { font-size: 20px; font-weight: 700; margin: 0 0 2px 0; color: #111; }
  .rec-unit   { font-size: 12px; color: #999; margin: 0 0 14px 0; }
  .rec-price  { font-size: 26px; font-weight: 700; color: #1b5e38; margin: 0 0 12px 0; }
  .rec-row    { display: flex; justify-content: space-between; font-size: 13px;
                color: #555; padding: 5px 0; border-bottom: 1px solid #f2f2f2; }
  .rec-row:last-child { border-bottom: none; }
  .down       { color: #0057b8; font-weight: 600; }
  .up         { color: #c0392b; font-weight: 600; }
  .conf-high  { color: #1b5e38; }
  .conf-mid   { color: #d07000; }
  .conf-low   { color: #999; }

  /* 섹션 타이틀 */
  .sec { font-size: 16px; font-weight: 700; color: #111;
         margin: 32px 0 12px 0; padding-bottom: 8px;
         border-bottom: 2px solid #1b5e38; }

  /* 점수 바 레이블 */
  .score-label { font-size: 11px; color: #888; }

  /* 탭 커스텀 */
  .stTabs [data-baseweb="tab"] { font-size: 14px; }
</style>
""", unsafe_allow_html=True)

# ── KAMIS API ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=3600, show_spinner=False)
def fetch(category, code, kind, rank, start, end):
    params = dict(
        action="periodProductList", p_cert_key=CERT_KEY, p_cert_id=CERT_ID,
        p_returntype="json", p_productclscode="01",
        p_startday=start, p_endday=end,
        p_itemcategorycode=category, p_itemcode=code,
        p_kindcode=kind, p_productrankcode=rank,
        p_countrycode="1101", p_convert_kg_yn="N",
    )
    try:
        rows = requests.get(
            "https://www.kamis.or.kr/service/price/xml.do",
            params=params, timeout=10
        ).json()["data"]["item"]
        out = []
        for r in rows:
            try:
                price = float(r["price"].replace(",", ""))
                m, d  = r["regday"].split("/")
                out.append({"date": f"{r['yyyy']}-{m}-{d}", "price": price})
            except Exception:
                continue
        return out
    except Exception:
        return []

# ── 품목 정의 ─────────────────────────────────────────────────────────────
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

# ── 날짜 계산 ─────────────────────────────────────────────────────────────
today     = date.today()
end_str   = today.strftime("%Y-%m-%d")
start_12m = (today - timedelta(days=365)).strftime("%Y-%m-%d")

this_mon        = today - timedelta(days=today.weekday())
this_week_start = this_mon.strftime("%Y-%m-%d")
last_week_start = (this_mon - timedelta(days=7)).strftime("%Y-%m-%d")
last_week_end   = (this_mon - timedelta(days=1)).strftime("%Y-%m-%d")

this_month_start = today.replace(day=1).strftime("%Y-%m-%d")
_lme             = today.replace(day=1) - timedelta(days=1)
last_month_start = _lme.replace(day=1).strftime("%Y-%m-%d")
last_month_end   = _lme.strftime("%Y-%m-%d")

W_WOW, W_MOM, W_YOY = 0.35, 0.30, 0.35

def avg(lst): return sum(lst) / len(lst) if lst else None
def pct(a, b): return round((a - b) / b * 100, 1) if b else 0

# ── 데이터 수집 ───────────────────────────────────────────────────────────
with st.spinner("가격 데이터를 불러오는 중입니다..."):
    data = []
    for item in ITEMS:
        rows = fetch(item["cat"], item["code"], item["kind"], item["rank"], start_12m, end_str)
        if len(rows) < 2:
            continue
        prices = [r["price"] for r in rows]
        now    = prices[-1]
        a12    = avg(prices)

        tw = avg([r["price"] for r in rows if r["date"] >= this_week_start]) or now
        lw = avg([r["price"] for r in rows if last_week_start <= r["date"] <= last_week_end]) or now
        tm = avg([r["price"] for r in rows if r["date"] >= this_month_start]) or now
        lm = avg([r["price"] for r in rows if last_month_start <= r["date"] <= last_month_end]) or now

        wow = pct(tw, lw);  mom = pct(tm, lm);  yoy = pct(now, a12)
        score = round(W_WOW * wow + W_MOM * mom + W_YOY * yoy, 2)
        conf  = {3:"높음", 2:"보통", 1:"낮음", 0:"없음"}[sum([wow<0, mom<0, yoy<0])]

        data.append({**item,
            "rows": rows, "now": now, "avg_12m": a12,
            "tw": tw, "lw": lw, "tm": tm, "lm": lm,
            "wow": wow, "mom": mom, "yoy": yoy,
            "score": score, "conf": conf,
        })

ranked = sorted(data, key=lambda x: x["score"])

# ═══════════════════════════════════════════════════════════════════════════
# 화면 렌더링
# ═══════════════════════════════════════════════════════════════════════════

# ── 헤더 배너 ─────────────────────────────────────────────────────────────
week_no = today.isocalendar()[1]
st.markdown(f"""
<div class="banner">
  <div>
    <p class="banner-title">민생밥상+ 주간 알뜰장보기 {week_no}호</p>
    <p class="banner-sub">발행일 {end_str} &nbsp;|&nbsp; KAMIS 공공 데이터 기반 &nbsp;|&nbsp; 서울 소매가 기준</p>
  </div>
  <div class="banner-badge">이번 주 저가 품목 {len([d for d in data if d['score']<0])}종</div>
</div>
""", unsafe_allow_html=True)

# ── KPI ───────────────────────────────────────────────────────────────────
top5 = ranked[:5]
saving = sum(max((d["avg_12m"] - d["now"]) * d["qty"], 0) for d in top5)
c1, c2, c3, c4 = st.columns(4)
c1.metric("분석 품목 수",       f"{len(data)}종")
c2.metric("저가 추천 품목",     f"{len([d for d in data if d['score']<0])}종")
c3.metric("TOP 5 월 절감 예상", f"{saving:,.0f}원")
c4.metric("데이터 기준일",      end_str)

# ── 탭 구성 ───────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["종합 추천", "가격 비교표", "가격 추이"])

# ════════════════════════ 탭 1: 종합 추천 ════════════════════════════════
with tab1:
    st.markdown('<p class="sec">종합 점수 TOP 3 추천</p>', unsafe_allow_html=True)
    st.caption(f"종합 점수 = 지난주 대비({int(W_WOW*100)}%) + 지난달 대비({int(W_MOM*100)}%) + 12개월 평균 대비({int(W_YOY*100)}) 가중 합산")

    conf_cls = {"높음": "conf-high", "보통": "conf-mid", "낮음": "conf-low", "없음": "conf-low"}
    cols = st.columns(3)
    for i, (col, d) in enumerate(zip(cols, ranked[:3])):
        def _arrow(v): return f'<span class="down">▼ {abs(v):.1f}%</span>' if v < 0 else f'<span class="up">▲ {abs(v):.1f}%</span>'
        with col:
            st.markdown(f"""
            <div class="rec-card">
              <p class="rec-rank">{i+1}위</p>
              <p class="rec-name">{d['name']}</p>
              <p class="rec-unit">{d['unit']}</p>
              <p class="rec-price">{d['now']:,.0f}원</p>
              <div class="rec-row"><span>지난주 대비</span>{_arrow(d['wow'])}</div>
              <div class="rec-row"><span>지난달 대비</span>{_arrow(d['mom'])}</div>
              <div class="rec-row"><span>12개월 평균 대비</span>{_arrow(d['yoy'])}</div>
              <div class="rec-row">
                <span>종합 점수</span>
                <b style="color:#1b5e38">{d['score']:+.1f}</b>
              </div>
              <div class="rec-row">
                <span>추천 신뢰도</span>
                <b class="{conf_cls[d['conf']]}">{d['conf']}</b>
              </div>
            </div>
            """, unsafe_allow_html=True)

    # ── 종합 점수 막대 차트 ────────────────────────────────────────────────
    st.markdown('<p class="sec">전체 품목 종합 점수 비교</p>', unsafe_allow_html=True)

    df_score = pd.DataFrame([{
        "품목": d["name"],
        "종합 점수": d["score"],
        "신뢰도": d["conf"],
    } for d in ranked])

    color_map = {"높음": "#1b5e38", "보통": "#e07b00", "낮음": "#bbbbbb", "없음": "#dddddd"}
    colors = [color_map[c] for c in df_score["신뢰도"]]

    fig_bar = go.Figure(go.Bar(
        x=df_score["품목"],
        y=df_score["종합 점수"],
        marker_color=colors,
        text=[f"{v:+.1f}" for v in df_score["종합 점수"]],
        textposition="outside",
        hovertemplate="%{x}: %{y:+.1f}점<extra></extra>",
    ))
    fig_bar.add_hline(y=0, line_color="#333", line_width=1)
    fig_bar.update_layout(
        yaxis_title="종합 점수 (낮을수록 저렴)",
        xaxis_title=None,
        height=340,
        plot_bgcolor="white",
        yaxis=dict(gridcolor="#f0f0f0", zeroline=False),
        xaxis=dict(tickangle=-30),
        margin=dict(t=30, b=10),
        showlegend=False,
    )
    st.plotly_chart(fig_bar, use_container_width=True)

    # 신뢰도 범례
    st.markdown("""
    <div style="font-size:12px; color:#666; display:flex; gap:18px; margin-top:-10px;">
      <span><span style="color:#1b5e38">■</span> 신뢰도 높음 (3지표 모두 하락)</span>
      <span><span style="color:#e07b00">■</span> 신뢰도 보통 (2지표 하락)</span>
      <span><span style="color:#bbb">■</span> 신뢰도 낮음 (1지표 이하)</span>
    </div>
    """, unsafe_allow_html=True)

    # ── 3축 비교 레이더 (TOP 3) ────────────────────────────────────────────
    st.markdown('<p class="sec">TOP 3 품목 지표별 비교</p>', unsafe_allow_html=True)
    st.caption("지난주 / 지난달 / 12개월 평균 대비 변화율(%) — 음수일수록 저렴")

    categories = ["지난주 대비", "지난달 대비", "12개월 평균 대비"]
    fig_radar = go.Figure()
    palette   = ["#1b5e38", "#0057b8", "#d07000"]

    for d, color in zip(ranked[:3], palette):
        vals = [d["wow"], d["mom"], d["yoy"]]
        fig_radar.add_trace(go.Scatterpolar(
            r=vals + [vals[0]],
            theta=categories + [categories[0]],
            fill="toself",
            fillcolor=color,
            opacity=0.15,
            line=dict(color=color, width=2),
            name=d["name"],
        ))
    fig_radar.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, tickfont=dict(size=10), gridcolor="#ddd"),
            angularaxis=dict(tickfont=dict(size=12)),
        ),
        showlegend=True,
        height=360,
        margin=dict(t=30, b=30),
    )
    st.plotly_chart(fig_radar, use_container_width=True)

# ════════════════════════ 탭 2: 가격 비교표 ══════════════════════════════
with tab2:
    st.markdown('<p class="sec">주요 농축산물 소매가격</p>', unsafe_allow_html=True)
    st.caption(f"(단위: 원, 상품)   지난주 {last_week_start}~{last_week_end} / 이번주 {this_week_start}~{end_str}")

    def arrow_str(v):
        return f"▼ {abs(v):.1f}%" if v < 0 else (f"▲ {abs(v):.1f}%" if v > 0 else "-")

    half = len(data) // 2 + len(data) % 2
    def make_tbl(items):
        return pd.DataFrame([{
            "품목": d["name"], "단위": d["unit"],
            "지난주": f"{d['lw']:,.0f}",
            "이번주": f"{d['tw']:,.0f}",
            "등락(%)": arrow_str(d["wow"]),
        } for d in items])

    cl, cr = st.columns(2)
    with cl: st.dataframe(make_tbl(data[:half]),  use_container_width=True, hide_index=True)
    with cr: st.dataframe(make_tbl(data[half:]),  use_container_width=True, hide_index=True)

    st.markdown('<p class="sec">전체 품목 종합 순위</p>', unsafe_allow_html=True)
    df_full = pd.DataFrame([{
        "순위": i+1, "품목": d["name"], "단위": d["unit"],
        "현재가": f"{d['now']:,.0f}원",
        "지난주 대비": arrow_str(d["wow"]),
        "지난달 대비": arrow_str(d["mom"]),
        "12개월 평균 대비": arrow_str(d["yoy"]),
        "종합 점수": f"{d['score']:+.1f}",
        "신뢰도": d["conf"],
    } for i, d in enumerate(ranked)])
    st.dataframe(df_full, use_container_width=True, hide_index=True)

# ════════════════════════ 탭 3: 가격 추이 ════════════════════════════════
with tab3:
    st.markdown('<p class="sec">품목별 가격 추이 (최근 90일)</p>', unsafe_allow_html=True)

    sel_name = st.selectbox("품목 선택", [d["name"] for d in data])
    sel = next(d for d in data if d["name"] == sel_name)

    df_line = pd.DataFrame(sel["rows"]).sort_values("date")
    cutoff  = (today - timedelta(days=90)).strftime("%Y-%m-%d")
    df_line = df_line[df_line["date"] >= cutoff]

    fig_line = go.Figure()
    fig_line.add_trace(go.Scatter(
        x=df_line["date"], y=df_line["price"],
        mode="lines+markers", name="일별 가격",
        line=dict(color="#1b5e38", width=2),
        marker=dict(size=4, color="#1b5e38"),
        hovertemplate="%{x}: %{y:,.0f}원<extra></extra>",
    ))
    fig_line.add_hline(
        y=sel["avg_12m"], line_dash="dot", line_color="#aaa",
        annotation_text=f"12개월 평균 {sel['avg_12m']:,.0f}원",
        annotation_font_size=11, annotation_position="top left",
    )
    fig_line.update_layout(
        yaxis_title="가격 (원)", xaxis_title=None,
        height=360, plot_bgcolor="white",
        yaxis=dict(gridcolor="#f0f0f0"),
        xaxis=dict(gridcolor="#f0f0f0"),
        margin=dict(t=20, b=20),
        hovermode="x unified",
    )
    st.plotly_chart(fig_line, use_container_width=True)

    # 지난주 vs 지난달 vs 12개월 평균 요약
    sc1, sc2, sc3 = st.columns(3)
    sc1.metric("지난주 대비", f"{sel['wow']:+.1f}%",  delta_color="inverse")
    sc2.metric("지난달 대비", f"{sel['mom']:+.1f}%",  delta_color="inverse")
    sc3.metric("12개월 평균 대비", f"{sel['yoy']:+.1f}%", delta_color="inverse")

st.divider()
st.caption("데이터 출처: 한국농수산식품유통공사(aT) KAMIS Open API  |  민생밥상+ DScover팀")
