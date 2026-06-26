# -*- coding: utf-8 -*-
"""스마트 장바구니 — 저가 품목 선정 및 절감액 계산."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional


@dataclass
class ItemResult:
    name      : str
    item_code : str
    unit      : str
    today     : float          # 오늘 가격
    avg_12m   : float          # 12개월 평균
    ratio     : float          # 오늘 / 평균 (1.0 미만이면 저가)
    saving_pct: float          # 절감률 (%)
    is_cheap  : bool           # 저가 여부


def evaluate(name: str, item_code: str, unit: str,
             today_price: float, avg_12m: float) -> Optional[ItemResult]:
    """품목 하나의 저가 여부와 절감률을 반환한다."""
    if avg_12m <= 0 or today_price <= 0:
        return None
    ratio      = today_price / avg_12m
    saving_pct = round((1 - ratio) * 100, 1)
    return ItemResult(
        name       = name,
        item_code  = item_code,
        unit       = unit,
        today      = today_price,
        avg_12m    = avg_12m,
        ratio      = round(ratio, 3),
        saving_pct = saving_pct,
        is_cheap   = ratio < 1.0,
    )


def rank_basket(results: list[ItemResult], top_n: int = 5) -> list[ItemResult]:
    """저가 품목만 절감률 내림차순으로 TOP N 반환."""
    cheap = [r for r in results if r.is_cheap]
    return sorted(cheap, key=lambda x: x.saving_pct, reverse=True)[:top_n]


def calc_monthly_saving(results: list[ItemResult],
                        monthly_qty: dict[str, float]) -> float:
    """월간 총 절감액 시뮬레이션.
    
    Args:
        results    : rank_basket() 결과
        monthly_qty: {item_code: 월 구매량(단위 기준)}
    """
    total = 0.0
    for r in results:
        qty = monthly_qty.get(r.item_code, 1.0)
        saving = (r.avg_12m - r.today) * qty
        total += max(saving, 0)
    return round(total)
