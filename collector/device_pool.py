"""设备池：
为每个 (store, platform) 配对一台设备。
  - 华为需要两台：一台 EMUI(双框架) + 一台 HarmonyOS NEXT(纯血鸿蒙)
  - 其他四家各一台安卓设备
真实环境建议对接 STF / ATX Server / 云手机 API。
"""
from __future__ import annotations

import json
from pathlib import Path

DEVICE_FILE = Path("config/devices.json")


# key = "store:platform"
DEFAULT_POOL: dict[str, str] = {
    "huawei:emui":         "127.0.0.1:7100",  # ADB over TCP
    "huawei:harmony_next": "127.0.0.1:7200",  # hdc 连接的纯血鸿蒙设备
    "xiaomi:android":      "127.0.0.1:7101",
    "vivo:android":        "127.0.0.1:7102",
    "oppo:android":        "127.0.0.1:7103",
    "honor:android":       "127.0.0.1:7104",
}


def _load() -> dict[str, str]:
    if DEVICE_FILE.exists():
        return json.loads(DEVICE_FILE.read_text(encoding="utf-8"))
    return DEFAULT_POOL


def get_device(store: str, platform: str = "android") -> str:
    pool = _load()
    key = f"{store}:{platform}"
    if key not in pool:
        raise ValueError(f"no device configured for {key}")
    return pool[key]


def list_devices() -> list[tuple[str, str, str]]:
    """返回 (store, platform, serial) 三元组列表。"""
    out = []
    for k, serial in _load().items():
        store, platform = k.split(":", 1)
        out.append((store, platform, serial))
    return out


def register(store: str, platform: str, serial: str) -> None:
    pool = _load()
    pool[f"{store}:{platform}"] = serial
    DEVICE_FILE.parent.mkdir(parents=True, exist_ok=True)
    DEVICE_FILE.write_text(json.dumps(pool, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"registered {store}:{platform} -> {serial}")
