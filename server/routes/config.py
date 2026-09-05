# -*- coding: utf-8 -*-
"""
文件名: server/routes/config.py
配置存储与元器件/磁芯库 SQLite CRUD 路由
"""

import json
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from core.db.db_manager import get_db_connection

router = APIRouter()


class ConfigItem(BaseModel):
    key: str
    value: Any


@router.get("/api/config/{key}")
def get_config(key: str):
    """读取指定配置键"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT config_value FROM debug_configs WHERE config_key = ?", (key,))
    row = cursor.fetchone()
    conn.close()
    if row:
        try:
            return {"status": "success", "key": key, "value": json.loads(row["config_value"])}
        except Exception:
            return {"status": "success", "key": key, "value": row["config_value"]}
    return {"status": "not_found", "key": key, "value": None}


@router.post("/api/config/{key}")
def set_config(key: str, item: ConfigItem):
    """保存指定配置键"""
    conn = get_db_connection()
    cursor = conn.cursor()
    val_str = json.dumps(item.value, ensure_ascii=False) if not isinstance(item.value, str) else item.value
    cursor.execute("""
    INSERT INTO debug_configs (config_key, config_value)
    VALUES (?, ?)
    ON CONFLICT(config_key) DO UPDATE SET config_value=excluded.config_value
    """, (key, val_str))
    conn.commit()
    conn.close()
    return {"status": "success", "message": f"配置 {key} 保存成功"}

