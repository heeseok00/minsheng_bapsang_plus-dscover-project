# 민생밥상+

**민생 식비 절감 통합 플랫폼** — 2026 민생플러스 생활비 경감 정책 아이디어 공모전

---

## 디렉토리 구조

```
project_DScover_메인프로젝트/
├── config/
│   ├── .env              ← API 키 (로컬 only, git 제외)
│   ├── .env.example      ← 키 양식 (공유용)
│   └── items.yaml        ← 대표 품목 15~20종 + 지역코드
├── data/
│   ├── raw/kamis/        ← 수집 원본 (json)
│   ├── processed/        ← kamis.db (SQLite)
│   └── output/           ← 분석 결과물
├── src/
│   ├── api/kamis.py      ← KAMIS API 호출
│   ├── db/store.py       ← SQLite 저장·조회
│   ├── analysis/
│   │   ├── basket.py     ← 저가 판별 + 절감액 계산
│   │   └── collect.py    ← 일별 수집 배치
│   └── dashboard/app.py  ← Streamlit 대시보드
├── notebooks/            ← EDA용 Jupyter
├── tests/
├── scripts/              ← 기획안 docx 생성 등
├── requirements.txt
└── .gitignore
```

---

## 시작하기

### 1. 환경 설정

```bash
pip install -r requirements.txt
cp config/.env.example config/.env
# config/.env 에 KAMIS 키 입력
```

### 2. DB 초기화 + 첫 수집

```bash
python -m src.analysis.collect
```

### 3. 대시보드 실행

```bash
streamlit run src/dashboard/app.py
```

---

## 단계별 로드맵

| 단계 | 내용 | 상태 |
|------|------|------|
| 1단계 | KAMIS 스마트 장바구니 | 🔧 개발 중 |
| 2단계 | 마감픽업 맵 (혜화·광장시장) | 📋 기획 |
| 3단계 | 음식물 낭비 절감 가이드 | 📋 기획 |

---

## 공모전 정보

- **주최:** 재정경제부 민생안정지원단
- **마감:** 2026.07.27
- **형식:** 정책제안서(A4 3쪽) 또는 카드뉴스(6쪽+)
