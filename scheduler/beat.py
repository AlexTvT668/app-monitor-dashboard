"""Celery Beat 定时调度：
- 06:00 并发启动 5 台设备采集
- 09:00 统计 + 渲染 + 推送
"""
from __future__ import annotations

from celery import Celery
from celery.schedules import crontab
from datetime import date

from collector.device_pool import get_device
from collector.huawei import HuaweiCollector
from collector.xiaomi import XiaomiCollector
from collector.vivo import VivoCollector
from collector.oppo import OppoCollector
from collector.honor import HonorCollector

from parser.publisher_matcher import match_publisher, is_game
from storage.db import SessionLocal
from storage.models import SlotSnapshot

app = Celery("slot_monitor", broker="redis://localhost:6379/0")

COLLECTORS = {
    "huawei": HuaweiCollector,
    "xiaomi": XiaomiCollector,
    "vivo":   VivoCollector,
    "oppo":   OppoCollector,
    "honor":  HonorCollector,
}


@app.task
def collect_store(store: str):
    cls = COLLECTORS[store]
    serial = get_device(store)
    collector = cls(serial)
    items = collector.collect_all()

    session = SessionLocal()
    try:
        for it in items:
            pub = match_publisher(it.package_name)
            session.merge(SlotSnapshot(
                snapshot_date=date.today(),
                store=it.store,
                slot_type=it.slot_type,
                rank=it.rank,
                app_name=it.app_name,
                package_name=it.package_name,
                publisher=pub,
                is_game=is_game(it.package_name, it.app_name),
                screenshot_url=it.screenshot_path,
                raw=it.extra or {},
            ))
        session.commit()
    finally:
        session.close()
    return f"{store}: {len(items)} records"


@app.task
def push_daily():
    from pusher.wecom import push_today
    push_today()


app.conf.beat_schedule = {
    "collect-huawei": {"task": "scheduler.beat.collect_store",
                       "schedule": crontab(hour=6, minute=0),  "args": ("huawei",)},
    "collect-xiaomi": {"task": "scheduler.beat.collect_store",
                       "schedule": crontab(hour=6, minute=5),  "args": ("xiaomi",)},
    "collect-vivo":   {"task": "scheduler.beat.collect_store",
                       "schedule": crontab(hour=6, minute=10), "args": ("vivo",)},
    "collect-oppo":   {"task": "scheduler.beat.collect_store",
                       "schedule": crontab(hour=6, minute=15), "args": ("oppo",)},
    "collect-honor":  {"task": "scheduler.beat.collect_store",
                       "schedule": crontab(hour=6, minute=20), "args": ("honor",)},
    "daily-push":     {"task": "scheduler.beat.push_daily",
                       "schedule": crontab(hour=9, minute=0)},
}
