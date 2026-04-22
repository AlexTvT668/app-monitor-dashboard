"""FastAPI 数据接口，供 Dashboard 读取"""
from __future__ import annotations

from datetime import date
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from analytics.stats import daily_share, trend, anomaly

app = FastAPI(title="Slot Monitor API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)


@app.get("/api/daily_snapshot")
def api_daily(d: str | None = Query(default=None)) -> dict:
    target = date.fromisoformat(d) if d else date.today()
    return daily_share(target)


@app.get("/api/trend")
def api_trend(days: int = 14) -> list[dict]:
    return trend(days)


@app.get("/api/anomaly")
def api_anomaly(d: str | None = Query(default=None)) -> list[str]:
    target = date.fromisoformat(d) if d else date.today()
    return anomaly(target)


# 直接把 dashboard 作为静态页挂上
app.mount("/", StaticFiles(directory="dashboard", html=True), name="dashboard")
