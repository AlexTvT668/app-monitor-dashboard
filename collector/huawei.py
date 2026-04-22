"""华为采集器 —— 同时支持：
  channel=app_store (应用市场 AppGallery)
  channel=game_center (华为游戏中心)
  platform=emui (双框架)
  platform=harmony_next (纯血鸿蒙 HarmonyOS NEXT)

注意：
  纯血鸿蒙下无法使用 uiautomator2，走 hdc + 截图 + OCR 兜底。
"""
import time

from loguru import logger

from .base import BaseCollector


class HuaweiCollector(BaseCollector):
    store_name = "huawei"

    # -------- EMUI(双框架) 的控件等待 --------
    _HOME_ID_MAP = {
        ("app_store", "emui"):   "com.huawei.appmarket:id/banner_view_pager",
        ("game_center", "emui"): "com.huawei.gamebox:id/banner_view_pager",
    }

    def _wait_home(self):
        if self.platform == "harmony_next":
            # 纯血鸿蒙：无 resource-id 体系，等待固定时长
            time.sleep(2.5)
            return
        rid = self._HOME_ID_MAP.get((self.channel, self.platform))
        if rid:
            self.device(resourceId=rid).wait(timeout=10)
        else:
            time.sleep(2.0)

    def goto_game_page(self):
        if self.platform == "harmony_next":
            # 纯血鸿蒙：点击底部 "游戏" tab（通过 OCR 定位或坐标）
            # 此处使用坐标占位：真实使用前在 DevEco Testing 里抓准
            self._hdc("shell uinput -T -m 540 2200 540 2200 100")
            time.sleep(1.5)
            return

        if self.channel == "app_store":
            # 华为应用市场：底部 tab "游戏"
            self.device(text="游戏").click_exists(timeout=3)
        else:
            # 华为游戏中心：首页就是游戏，这里切到 "分类/精选"
            self.device(text="精选").click_exists(timeout=3)
        time.sleep(1.5)


def collect_huawei_all(device_serial: str) -> list:
    """一次性采集华为的 应用市场 + 游戏中心 × 设备所在平台。"""
    results = []
    for channel in ("app_store", "game_center"):
        try:
            c = HuaweiCollector(device_serial, channel=channel)
            logger.info(f"[huawei] start channel={channel} platform={c.platform}")
            results += c.collect_all()
        except Exception as e:
            logger.exception(f"[huawei/{channel}] failed: {e}")
    return results
