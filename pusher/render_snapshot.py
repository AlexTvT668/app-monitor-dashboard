"""用 pyppeteer 把 Dashboard 截成 PNG，供推送使用。"""
from __future__ import annotations

import asyncio
from datetime import date
from pathlib import Path


async def _shoot(url: str, out: str) -> str:
    from pyppeteer import launch
    browser = await launch(headless=True, args=["--no-sandbox"])
    page = await browser.newPage()
    await page.setViewport({"width": 1440, "height": 2100})
    await page.goto(url, {"waitUntil": "networkidle0", "timeout": 60000})
    await page.screenshot({"path": out, "fullPage": True})
    await browser.close()
    return out


def render_dashboard(target: date, base_url: str = "http://localhost:8000") -> str:
    Path("snapshots/dashboard").mkdir(parents=True, exist_ok=True)
    out = f"snapshots/dashboard/{target.isoformat()}.png"
    url = f"{base_url}/?date={target.isoformat()}"
    try:
        return asyncio.get_event_loop().run_until_complete(_shoot(url, out))
    except Exception as e:
        print(f"[render] failed: {e}")
        return ""
