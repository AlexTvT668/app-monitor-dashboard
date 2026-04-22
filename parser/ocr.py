"""基于 PaddleOCR 的文字识别。仅在 UI dump 无法取得文案时兜底调用。"""
from __future__ import annotations

from typing import List

try:
    from paddleocr import PaddleOCR
    _OCR = PaddleOCR(use_angle_cls=True, lang="ch", show_log=False)
except Exception:  # noqa: BLE001
    _OCR = None


def ocr_image(image_path: str) -> List[str]:
    """返回识别到的所有文字行；PaddleOCR 未安装时返回空。"""
    if _OCR is None:
        return []
    try:
        result = _OCR.ocr(image_path, cls=True)
    except Exception:  # noqa: BLE001
        return []
    lines: list[str] = []
    if not result:
        return lines
    for page in result:
        if not page:
            continue
        for item in page:
            if not item or len(item) < 2:
                continue
            txt = item[1][0]
            if txt:
                lines.append(txt)
    return lines
