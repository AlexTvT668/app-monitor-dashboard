"""每日统计：发行商占比、环比趋势、异常检测"""
from __future__ import annotations

from datetime import date, timedelta
from collections import defaultdict
from typing import Any

from sqlalchemy import select, func
from storage.db import SessionLocal
from storage.models import SlotSnapshot


STORES = ["huawei", "xiaomi", "vivo", "oppo", "honor"]
SLOTS = ["splash", "banner", "bigcard", "header"]
PUBS = ["tencent", "netease", "other"]


def daily_share(target: date) -> dict[str, Any]:
    """返回结构：
    {
      "date": "2026-04-21",
      "stores": {
         "huawei": { "splash": {"tencent": 0.5, "netease": 0.2, "other": 0.3}, ... },
         ...
      },
      "totals": { "tencent": 0.42, "netease": 0.25, "other": 0.33 }
    }"""
    session = SessionLocal()
    try:
        q = select(SlotSnapshot.store, SlotSnapshot.slot_type,
                   SlotSnapshot.publisher, func.count()).where(
            SlotSnapshot.snapshot_date == target,
            SlotSnapshot.is_game.is_(True)
        ).group_by(SlotSnapshot.store, SlotSnapshot.slot_type, SlotSnapshot.publisher)
        rows = session.execute(q).all()
    finally:
        session.close()

    agg: dict = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    totals = defaultdict(int)
    for store, slot, pub, cnt in rows:
        agg[store][slot][pub] += cnt
        totals[pub] += cnt

    def _norm(d: dict[str, int]) -> dict[str, float]:
        s = sum(d.values()) or 1
        return {k: round(v / s, 4) for k, v in d.items()}

    stores_out = {}
    for store in STORES:
        stores_out[store] = {}
        for slot in SLOTS:
            counts = {p: agg[store][slot].get(p, 0) for p in PUBS}
            stores_out[store][slot] = _norm(counts)

    total_counts = {p: totals.get(p, 0) for p in PUBS}
    return {
        "date": target.isoformat(),
        "stores": stores_out,
        "totals": _norm(total_counts),
    }


def trend(days: int = 14) -> list[dict]:
    """过去 N 天每日"全站游戏资源位"发行商占比，用于趋势图。"""
    today = date.today()
    out = []
    for i in range(days - 1, -1, -1):
        d = today - timedelta(days=i)
        s = daily_share(d)
        out.append({
            "date": d.isoformat(),
            "tencent": s["totals"].get("tencent", 0),
            "netease": s["totals"].get("netease", 0),
            "other":   s["totals"].get("other", 0),
        })
    return out


def anomaly(today: date) -> list[str]:
    """最简单的环比异常：若腾讯或网易占比日间变化 > 10pp，标记告警。"""
    yesterday = today - timedelta(days=1)
    a = daily_share(today)["totals"]
    b = daily_share(yesterday)["totals"]
    alerts = []
    for pub in ("tencent", "netease"):
        delta = a.get(pub, 0) - b.get(pub, 0)
        if abs(delta) >= 0.10:
            direction = "↑" if delta > 0 else "↓"
            alerts.append(f"{pub} 占比环比{direction} {abs(delta) * 100:.1f}pp")
    return alerts
