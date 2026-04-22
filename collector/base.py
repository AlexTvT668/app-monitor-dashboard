"""采集器基类：
- 支持 channel × platform 维度
- 华为可选 harmony_next 分支（用 hdc + OpenHarmony 自动化协议，非 uiautomator2）

配置取值路径： cfg[store][channel][platform]
"""
from __future__ import annotations

import subprocess
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import yaml
from loguru import logger

try:
    import uiautomator2 as u2  # Android / EMUI
except ImportError:  # 允许在纯鸿蒙环境缺失
    u2 = None


@dataclass
class SlotItem:
    store: str
    channel: str                 # app_store / game_center
    platform: str                # android / emui / harmony_next
    slot_type: str               # splash / banner / bigcard / header
    rank: int
    app_name: str = ""
    package_name: str = ""        # Android 包名 或 HarmonyOS bundleName
    screenshot_path: str = ""
    extra: dict = field(default_factory=dict)


# ============ 平台识别 ============
def detect_huawei_platform(serial: str) -> str:
    """识别华为设备是 EMUI(双框架) 还是 HarmonyOS NEXT(纯血鸿蒙)。

    判定规则（按优先级）：
      1) hdc list targets 里能看到 → 优先按纯血鸿蒙处理
      2) adb shell getprop const.ohos.apiversion >= 12 且 ro.build.characteristics 含 harmony
         → harmony_next
      3) 其他 → emui
    """
    # 1) 尝试 hdc（纯血鸿蒙专用调试桥）
    try:
        out = subprocess.check_output(["hdc", "list", "targets"],
                                      stderr=subprocess.DEVNULL, timeout=3).decode()
        if serial in out:
            return "harmony_next"
    except (FileNotFoundError, subprocess.SubprocessError):
        pass

    # 2) adb 读取系统属性
    try:
        def _getprop(key: str) -> str:
            return subprocess.check_output(
                ["adb", "-s", serial, "shell", "getprop", key],
                stderr=subprocess.DEVNULL, timeout=3).decode().strip()

        ohos_api = _getprop("const.ohos.apiversion")
        chars = _getprop("ro.build.characteristics")
        if ohos_api and ohos_api.isdigit() and int(ohos_api) >= 12 and "harmony" in chars.lower():
            return "harmony_next"
    except subprocess.SubprocessError:
        pass
    return "emui"


class BaseCollector:
    """采集器父类。子类重写 _wait_home / goto_game_page。"""
    store_name: str = ""

    def __init__(self, device_serial: str, channel: str = "app_store",
                 platform: str | None = None,
                 config_path: str = "config/slots.yaml"):
        self.serial = device_serial
        self.channel = channel  # app_store / game_center

        # 华为需要区分 platform；其他厂商固定 android
        if self.store_name == "huawei":
            self.platform = platform or detect_huawei_platform(device_serial)
        else:
            self.platform = "android"

        with open(config_path, "r", encoding="utf-8") as f:
            all_cfg = yaml.safe_load(f)

        try:
            self.cfg = all_cfg[self.store_name][self.channel][self.platform]
        except KeyError as e:
            raise RuntimeError(
                f"[{self.store_name}] 未找到配置: channel={self.channel} "
                f"platform={self.platform}，请检查 config/slots.yaml") from e

        # 纯血鸿蒙走 hdc；其它走 uiautomator2
        if self.platform == "harmony_next":
            self.device = None  # 纯血鸿蒙单独实现（见 _harmony_*）
        else:
            if u2 is None:
                raise RuntimeError("uiautomator2 未安装，无法采集 Android/EMUI 设备")
            self.device = u2.connect(device_serial)

        date_str = datetime.now().strftime("%Y%m%d")
        self.snapshot_root = (Path("snapshots") / date_str / self.store_name
                              / self.channel / self.platform)
        self.snapshot_root.mkdir(parents=True, exist_ok=True)

    # ---------- 生命周期 ----------
    def start(self) -> None:
        if self.platform == "harmony_next":
            bundle = self.cfg["bundle_name"]
            logger.info(f"[{self.tag}] hdc restart {bundle}")
            self._hdc(f"shell aa force-stop -b {bundle}")
            time.sleep(0.8)
            self._hdc(f"shell aa start -b {bundle} -a {self.cfg.get('ability','EntryAbility')}")
            time.sleep(1.2)
        else:
            pkg = self.cfg["package"]
            logger.info(f"[{self.tag}] stop & relaunch {pkg}")
            self.device.app_stop(pkg)
            time.sleep(1)
            self.device.app_start(pkg, use_monkey=True)
            time.sleep(1.2)
        self._shot("splash", 0)

    def collect_all(self) -> list[SlotItem]:
        results: list[SlotItem] = []
        try:
            self.start()
            results.append(self._mk(slot="splash", rank=0,
                                    screenshot=str(self.snapshot_root / "splash_0.png")))
            self._wait_home()
            results += self._collect_slot("banner")
            self.goto_game_page()
            results += self._collect_slot("bigcard")
            results += self._collect_slot("header")
        except Exception as e:
            logger.exception(f"[{self.tag}] collect failed: {e}")
        return results

    # ---------- 通用 ----------
    def _collect_slot(self, slot_type: str) -> list[SlotItem]:
        slot_cfg = (self.cfg.get("slots") or {}).get(slot_type)
        if not slot_cfg:
            return []

        if self.platform == "harmony_next":
            # 纯血鸿蒙：先截图 + 通过 hdc hidumper 拿控件树（实现见子类 / 后期替换）
            return self._harmony_collect_slot(slot_type, slot_cfg)

        # Android / EMUI
        locator = slot_cfg.get("locator", {})
        if "resource_id" in locator:
            el = self.device(resourceId=locator["resource_id"])
        elif "xpath" in locator:
            el = self.device.xpath(locator["xpath"])
        else:
            return []
        if not el.exists:
            logger.warning(f"[{self.tag}] slot {slot_type} not found")
            return []

        count = slot_cfg.get("item_count", 1)
        items: list[SlotItem] = []
        for rank in range(count):
            path = self._shot(slot_type, rank)
            app_name, pkg = self._extract_app_info(el)
            items.append(self._mk(slot=slot_type, rank=rank,
                                  app_name=app_name, pkg=pkg, screenshot=str(path)))
            if count > 1:
                self._swipe_banner_next()
                time.sleep(0.6)
        return items

    # ---------- 纯血鸿蒙分支（初版：截图 + OCR 兜底） ----------
    def _harmony_collect_slot(self, slot_type: str, slot_cfg: dict) -> list[SlotItem]:
        count = slot_cfg.get("item_count", 1)
        items: list[SlotItem] = []
        for rank in range(count):
            path = self._shot(slot_type, rank)
            items.append(self._mk(slot=slot_type, rank=rank, screenshot=str(path),
                                  extra={"ocr_needed": True}))
            if count > 1:
                # 纯血鸿蒙通过 hdc shell uinput 模拟滑动
                self._hdc("shell uinput -T -m 800 600 200 600 300")
                time.sleep(0.6)
        return items

    # ---------- 工具 ----------
    def _shot(self, slot_type: str, rank: int) -> Path:
        path = self.snapshot_root / f"{slot_type}_{rank}.png"
        if self.platform == "harmony_next":
            # 纯血鸿蒙截图
            self._hdc(f"file send /data/local/tmp/_cap.png {path}")  # 占位：真实用 snapshot_display
            self._hdc("shell snapshot_display -f /data/local/tmp/_cap.png")
            self._hdc(f"file recv /data/local/tmp/_cap.png {path}")
        else:
            self.device.screenshot(str(path))
        return path

    def _swipe_banner_next(self) -> None:
        w, h = self.device.window_size()
        self.device.swipe(w * 0.8, h * 0.35, w * 0.2, h * 0.35, duration=0.3)

    def _extract_app_info(self, el):
        try:
            text = el.get_text() if hasattr(el, "get_text") else ""
        except Exception:
            text = ""
        return text, ""

    def _hdc(self, cmd: str) -> str:
        """执行 hdc 命令（纯血鸿蒙专用）"""
        try:
            out = subprocess.check_output(
                ["hdc", "-t", self.serial] + cmd.split(),
                stderr=subprocess.DEVNULL, timeout=10).decode()
            return out
        except subprocess.SubprocessError as e:
            logger.warning(f"hdc {cmd} failed: {e}")
            return ""

    def _mk(self, slot: str, rank: int, app_name: str = "", pkg: str = "",
            screenshot: str = "", extra: dict | None = None) -> SlotItem:
        return SlotItem(
            store=self.store_name, channel=self.channel, platform=self.platform,
            slot_type=slot, rank=rank, app_name=app_name, package_name=pkg,
            screenshot_path=screenshot, extra=extra or {},
        )

    @property
    def tag(self) -> str:
        return f"{self.store_name}/{self.channel}/{self.platform}"

    # 子类实现
    def _wait_home(self) -> None:
        if self.platform == "harmony_next":
            time.sleep(2.0); return
        raise NotImplementedError

    def goto_game_page(self) -> None:
        if self.platform == "harmony_next":
            # 默认走底部 tab 第2项（游戏），子类可按需覆盖
            self._hdc("shell uinput -T -m 540 2200 540 2200 100")
            time.sleep(1.0); return
        raise NotImplementedError
