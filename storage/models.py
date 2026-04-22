"""SQLAlchemy 数据模型

维度升级：
  store     5 大厂商 (huawei/xiaomi/vivo/oppo/honor)
  channel   入口类型 (app_store 应用商店 / game_center 游戏中心)
  platform  平台    (android 默认 / emui 华为双框架 / harmony_next 华为纯血鸿蒙)
  slot_type 资源位  (splash/banner/bigcard/header)
"""
from __future__ import annotations

from datetime import datetime
from sqlalchemy import (Column, String, Integer, Date, DateTime, Boolean, JSON,
                        BigInteger, Index, UniqueConstraint)
from sqlalchemy.orm import declarative_base

Base = declarative_base()

# 枚举常量
CHANNEL_APP_STORE = "app_store"
CHANNEL_GAME_CENTER = "game_center"

PLATFORM_ANDROID = "android"        # 小米/vivo/OPPO/荣耀 默认
PLATFORM_EMUI = "emui"              # 华为双框架
PLATFORM_HARMONY_NEXT = "harmony_next"  # 华为纯血鸿蒙


class SlotSnapshot(Base):
    __tablename__ = "slot_snapshot"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    snapshot_date = Column(Date, nullable=False, index=True)
    store = Column(String(20), nullable=False, index=True)      # huawei/xiaomi/...
    channel = Column(String(20), nullable=False, index=True,
                     default=CHANNEL_APP_STORE)                 # app_store / game_center
    platform = Column(String(20), nullable=False, index=True,
                      default=PLATFORM_ANDROID)                 # android / emui / harmony_next
    slot_type = Column(String(20), nullable=False, index=True)  # splash/banner/bigcard/header
    rank = Column(Integer, nullable=False)
    app_name = Column(String(100), default="")
    package_name = Column(String(120), default="", index=True)  # 安卓包名 或 鸿蒙 bundleName
    publisher = Column(String(20), default="other", index=True) # tencent/netease/other
    is_game = Column(Boolean, default=False)
    screenshot_url = Column(String(512), default="")
    raw = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        # 同一天 × 同一厂商 × 同一入口 × 同一平台 × 同一资源位 × 同一位次 唯一
        UniqueConstraint("snapshot_date", "store", "channel", "platform",
                         "slot_type", "rank", name="uq_slot_per_day"),
        Index("idx_date_store_chan_plat", "snapshot_date", "store", "channel", "platform"),
        Index("idx_publisher", "snapshot_date", "publisher"),
    )


class PublisherMap(Base):
    """包名/bundleName → 发行商归属映射。
    同一游戏在安卓和鸿蒙上的包名/bundleName 可能不同，需都写入。"""
    __tablename__ = "pkg_publisher_map"
    package_name = Column(String(120), primary_key=True)
    app_name = Column(String(100), default="")
    publisher = Column(String(20), default="other")
    is_game = Column(Boolean, default=False)
    platform_hint = Column(String(20), default="")   # 可选：标识这是安卓包还是鸿蒙 bundle
    confirmed = Column(Boolean, default=False)
    updated_at = Column(DateTime, default=datetime.utcnow)


class DeviceRegistry(Base):
    """采集设备登记表 —— 用于区分华为的 EMUI / 纯血鸿蒙设备"""
    __tablename__ = "device_registry"
    device_id = Column(String(64), primary_key=True)   # ADB serial 或 hdc serial
    store = Column(String(20), index=True)
    platform = Column(String(20), index=True)           # android / emui / harmony_next
    os_version = Column(String(30), default="")
    api_version = Column(String(10), default="")        # Android SDK / OHOS API
    model = Column(String(50), default="")
    enabled = Column(Boolean, default=True)
    note = Column(String(200), default="")
    updated_at = Column(DateTime, default=datetime.utcnow)
