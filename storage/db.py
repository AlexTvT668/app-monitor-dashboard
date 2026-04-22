"""数据库连接 & 初始化"""
from __future__ import annotations

import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .models import Base

DB_URL = os.getenv("DB_URL", "postgresql://postgres:postgres@localhost:5432/slot_monitor")

engine = create_engine(DB_URL, pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def init() -> None:
    Base.metadata.create_all(engine)
    print("[db] tables created")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "init":
        init()
