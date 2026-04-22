"""OPPO —— 软件商店 + 游戏空间/游戏中心"""
import time
from loguru import logger
from .base import BaseCollector


class OppoCollector(BaseCollector):
    store_name = "oppo"

    _HOME_ID = {
        "app_store":   "com.oppo.market:id/home_banner_viewpager",
        "game_center": "com.oppo.play:id/discover_banner",
    }

    def _wait_home(self):
        rid = self._HOME_ID.get(self.channel)
        if rid:
            self.device(resourceId=rid).wait(timeout=10)

    def goto_game_page(self):
        if self.channel == "app_store":
            self.device(text="游戏").click_exists(timeout=3)
        else:
            self.device(text="发现").click_exists(timeout=3)
        time.sleep(1.5)


def collect_oppo_all(device_serial: str) -> list:
    results = []
    for ch in ("app_store", "game_center"):
        try:
            results += OppoCollector(device_serial, channel=ch).collect_all()
        except Exception as e:
            logger.exception(f"[oppo/{ch}] failed: {e}")
    return results
