"""小米 —— 应用商店 + 游戏中心"""
import time
from loguru import logger
from .base import BaseCollector


class XiaomiCollector(BaseCollector):
    store_name = "xiaomi"

    _HOME_ID = {
        "app_store":   "com.xiaomi.market:id/home_banner",
        "game_center": "com.xiaomi.gamecenter:id/home_banner_pager",
    }

    def _wait_home(self):
        rid = self._HOME_ID.get(self.channel)
        if rid:
            self.device(resourceId=rid).wait(timeout=10)

    def goto_game_page(self):
        if self.channel == "app_store":
            self.device(text="游戏").click_exists(timeout=3)
        else:
            self.device(text="精选").click_exists(timeout=3)
        time.sleep(1.5)


def collect_xiaomi_all(device_serial: str) -> list:
    results = []
    for ch in ("app_store", "game_center"):
        try:
            results += XiaomiCollector(device_serial, channel=ch).collect_all()
        except Exception as e:
            logger.exception(f"[xiaomi/{ch}] failed: {e}")
    return results
