# -*- coding: utf-8 -*-
"""
文件名: core/db/db_manager.py
SQLite 本地轻量数据库管理器
负责：
- 调试配置存储 (debug_configs: serial_profiles, custom_buttons, etc.)
- 支持 WAL 高速并发读写模式
"""

import sqlite3
import os
import json

DB_FILE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "database.db")


def get_db_connection():
    conn = sqlite3.connect(DB_FILE_PATH, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn


def init_database():
    """初始化 SQLite 数据库表格"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS debug_configs (
        config_key TEXT PRIMARY KEY,
        config_value TEXT NOT NULL
    )
    """)

    conn.commit()

    cursor.execute("SELECT COUNT(*) FROM debug_configs")
    if cursor.fetchone()[0] == 0:
        default_configs = [
            (
                "serial_profiles",
                json.dumps([
                    {
                        "name": "默认通信配置",
                        "baudrate": 115200,
                        "parity": "None",
                        "bytesize": 8,
                        "stopbits": 1,
                    }
                ]),
            ),
            (
                "custom_buttons",
                json.dumps([
                    {
                        "id": 1,
                        "label": "开机使能",
                        "command": "A5 01 01 00 00 00 00 E5",
                    },
                    {
                        "id": 2,
                        "label": "停机封锁",
                        "command": "A5 01 00 00 00 00 00 E4",
                    },
                ]),
            ),
        ]
        cursor.executemany("""
        INSERT OR IGNORE INTO debug_configs (config_key, config_value)
        VALUES (?, ?)
        """, default_configs)

    conn.commit()
    conn.close()
    print("[SQLite] Core Database initialized successfully.")


if __name__ == "__main__":
    init_database()
