# -*- coding: utf-8 -*-
"""KAMIS Open API 호출 모듈."""
import os
import requests
from datetime import date
from dotenv import load_dotenv

load_dotenv(dotenv_path="config/.env")

BASE_URL   = "https://www.kamis.or.kr/service/price/xml.do"   # http → https 자동 리다이렉트
CERT_KEY   = os.getenv("KAMIS_CERT_KEY", "").strip()
CERT_ID    = os.getenv("KAMIS_CERT_ID", "").strip()


def _get(action: str, extra: dict) -> dict:
    """공통 GET 요청. action 파라미터를 가장 먼저 전달한다."""
    params = {
        "action"       : action,
        "p_cert_key"   : CERT_KEY,
        "p_cert_id"    : CERT_ID,
        "p_returntype" : "json",
        **extra,
    }
    try:
        r = requests.get(BASE_URL, params=params, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"[KAMIS ERROR] {action}: {e}")
        return {}


def get_period_price(
    itemcategorycode: str,
    itemcode: str,
    kindcode: str   = "00",
    rankcode: str   = "04",
    start: str      = None,
    end: str        = None,
    country: str    = "1101",
    clscode: str    = "01",         # 01=소매, 02=도매
) -> dict:
    """일별 품목별 가격 조회 (API #2).

    Args:
        itemcategorycode : 부류코드 (100=곡류, 200=채소, 300=과일, 400=축산, 500=수산)
        itemcode         : 품목코드
        kindcode         : 품종코드 (00=전체)
        rankcode         : 등급코드 (04=상품, 05=중품)
        start / end      : "YYYY-MM-DD" (기본: 이번 달 1일 ~ 오늘)
        country          : 지역코드 (1101=서울)
        clscode          : 01=소매, 02=도매
    """
    today = date.today()
    start = start or today.strftime("%Y-%m-01")
    end   = end   or today.strftime("%Y-%m-%d")

    return _get("periodProductList", {
        "p_productclscode"  : clscode,
        "p_startday"        : start,
        "p_endday"          : end,
        "p_itemcategorycode": itemcategorycode,
        "p_itemcode"        : itemcode,
        "p_kindcode"        : kindcode,
        "p_productrankcode" : rankcode,
        "p_countrycode"     : country,
        "p_convert_kg_yn"   : "N",
    })


def get_monthly_trend(product_no: str, regday: str = None) -> dict:
    """월평균 가격추이 (API #8).

    Args:
        product_no : 상품코드 (periodProductList 결과의 productno 필드)
        regday     : 기준일 "YYYY-MM-DD" (기본: 오늘)
    """
    regday = regday or date.today().strftime("%Y-%m-%d")
    return _get("monthlyPriceTrendList", {
        "p_productno": product_no,
        "p_regday"   : regday,
    })


def get_recent_trend(product_no: str, regday: str = None) -> dict:
    """최근 가격추이 (API #7)."""
    regday = regday or date.today().strftime("%Y-%m-%d")
    return _get("recentPriceTrendList", {
        "p_productno": product_no,
        "p_regday"   : regday,
    })
