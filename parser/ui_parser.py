"""UI dump 解析：从 uiautomator2 dump 的 xml 里抽 app_name / 包名关联。

策略：
1. 从 dump XML 中抓取带有 content-desc / text 的节点；
2. 针对点击跳转型 Banner，记录 on-click intent 或 resource-id 可推断的包名；
3. 拿不到包名时（图片 Banner），把截图交给 OCR 兜底抓文字。
"""
from __future__ import annotations

import re
from lxml import etree


def parse_dump(xml_str: str) -> list[dict]:
    if not xml_str:
        return []
    try:
        root = etree.fromstring(xml_str.encode("utf-8"))
    except Exception:
        return []
    nodes = []
    for node in root.iter("node"):
        text = node.attrib.get("text", "").strip()
        desc = node.attrib.get("content-desc", "").strip()
        rid = node.attrib.get("resource-id", "")
        clickable = node.attrib.get("clickable", "false") == "true"
        if not (text or desc):
            continue
        nodes.append({
            "text": text,
            "desc": desc,
            "resource_id": rid,
            "clickable": clickable,
            "bounds": node.attrib.get("bounds", ""),
        })
    return nodes


PKG_RE = re.compile(r"([a-z][a-z0-9_]+\.[a-z0-9_.]+\.[a-z0-9_.]+)")


def guess_package(text: str) -> str:
    m = PKG_RE.search(text or "")
    return m.group(1) if m else ""
