"""企业微信机器人推送：每日把看板截图发送到群。"""
from __future__ import annotations

import os
import base64
import hashlib
from datetime import date
from pathlib import Path

import requests

WECOM_WEBHOOK = os.getenv("WECOM_WEBHOOK", "")


def _post(payload: dict) -> None:
    if not WECOM_WEBHOOK:
        print("[wecom] WECOM_WEBHOOK not set, skip")
        return
    r = requests.post(WECOM_WEBHOOK, json=payload, timeout=15)
    r.raise_for_status()


def send_image(image_path: str) -> None:
    data = Path(image_path).read_bytes()
    b64 = base64.b64encode(data).decode()
    md5 = hashlib.md5(data).hexdigest()
    _post({"msgtype": "image", "image": {"base64": b64, "md5": md5}})


def send_markdown(md: str) -> None:
    _post({"msgtype": "markdown", "markdown": {"content": md}})


def push_today() -> None:
    from analytics.stats import daily_share, anomaly
    from pusher.render_snapshot import render_dashboard

    today = date.today()
    data = daily_share(today)
    img = render_dashboard(today)          # -> PNG
    send_markdown(
        f"# 📊 应用商店资源位日报 ({today})\n\n"
        f"- **腾讯游戏占比**: {data['totals'].get('tencent', 0) * 100:.1f}%\n"
        f"- **网易游戏占比**: {data['totals'].get('netease', 0) * 100:.1f}%\n"
        f"- **其他游戏占比**: {data['totals'].get('other', 0) * 100:.1f}%\n"
    )
    if img:
        send_image(img)
    for a in anomaly(today):
        send_markdown(f"⚠️ **异常**: {a}")
