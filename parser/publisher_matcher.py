"""根据 package_name 判断 App 归属：tencent / netease / other"""
from __future__ import annotations

import yaml
from functools import lru_cache
from pathlib import Path


CONFIG_PATH = Path("config/publishers.yaml")


@lru_cache(maxsize=1)
def _load() -> dict:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def match_publisher(package_name: str) -> str:
    """返回 tencent / netease / other；未知返回 other"""
    if not package_name:
        return "other"
    cfg = _load()

    # 精确匹配
    tencent_set = set(cfg.get("tencent", []) or [])
    netease_set = set(cfg.get("netease", []) or [])
    # prefix 规则
    tencent_prefixes = []
    netease_prefixes = []
    # 配置结构容错：prefix 可能在 list 内部
    for key in ("tencent", "netease"):
        items = cfg.get(key, []) or []
        for it in items:
            if isinstance(it, dict) and "prefix" in it:
                if key == "tencent":
                    tencent_prefixes = it["prefix"]
                else:
                    netease_prefixes = it["prefix"]

    if package_name in tencent_set:
        return "tencent"
    if package_name in netease_set:
        return "netease"
    for p in tencent_prefixes:
        if package_name.startswith(p):
            return "tencent"
    for p in netease_prefixes:
        if package_name.startswith(p):
            return "netease"
    return "other"


def is_game(package_name: str, app_name: str = "") -> bool:
    """简易判定是否为游戏。正式环境建议接入 iTunes/应用商店分类接口或维护白名单。"""
    if not package_name:
        return False
    game_keywords = ("game", "tmgp", "mihoyo", "miHoYo", "lilith", "netease.g",
                     "netease.x", "netease.y", "netease.o", "netease.party")
    pkg_lower = package_name.lower()
    for kw in game_keywords:
        if kw.lower() in pkg_lower:
            return True
    # 按名称兜底
    name_game_hits = ("王者", "吃鸡", "和平精英", "原神", "崩坏", "蛋仔", "阴阳师",
                      "梦幻", "星穹", "弹弹堂", "魔域", "逆水寒", "三国", "战神")
    return any(k in app_name for k in name_game_hits)
