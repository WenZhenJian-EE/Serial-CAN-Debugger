# -*- coding: utf-8 -*-
"""
文件名: server/state.py
全局共享状态与引擎单例管理模块
"""

import queue
import threading

from core.models.trigger_engine import TriggerEngine
from core.models.async_logger import AsyncLogger
from core.models.blackbox_recorder import BlackboxRecorder

# ─── 共享数据队列 ─────────────────────────────────────────────────────────────
data_queue: queue.Queue = queue.Queue()
raw_data_queue: queue.Queue = queue.Queue(maxsize=2000)

# ─── 硬件 Worker 注册表 ───────────────────────────────────────────────────────
active_workers: dict = {
    "serial": None,
    "can": None,
    "tcp": None,
}
active_workers_lock = threading.Lock()

# ─── 硬件引擎与记录器单例 ─────────────────────────────────────────────────────
trigger_engine = TriggerEngine()
logger_instance = AsyncLogger()
blackbox_instance = BlackboxRecorder()

# ─── 数据流与协议状态 ─────────────────────────────────────────────────────────
is_streaming: bool = False
pending_dbc = None

# ─── 数学通道表达式缓存 ───────────────────────────────────────────────────────
math_expressions: dict = {}
last_math_ts: dict = {}

# ─── Modbus 寄存器表 ──────────────────────────────────────────────────────────
global_modbus_registers: list = []
simulated_modbus_values: dict = {}

# ─── CAN 周期发送配置 ─────────────────────────────────────────────────────────
can_periodic_config: dict = {
    "running": False,
    "interval": 0.1,
    "arbitration_id": 0x100,
    "data": b"",
    "is_extended": False,
}
