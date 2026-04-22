"""vivo —— 应用商店 + 游戏中心"""
import time
from loguru import logger
from .base import BaseCollector


class VivoCollector(BaseCollector):
    store_name = "vivo"

    _HOME_ID = {
        "app_store":   "com.bbk.appstore:id/home_page_banner",
        "game_center": "com.vivo.game:id/home_banner",
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


def collect_vivo_all(device_serial: str) -> list:
    results = []
    for ch in ("app_store", "game_center"):
        try:
            results += VivoCollector(device_serial, channel=ch).collect_all()
        except Exception as e:
            logger.exception(f"[vivo/{ch}] failed: {e}")
    return results
