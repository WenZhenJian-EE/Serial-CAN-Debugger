# -*- coding: utf-8 -*-
"""
文件名: core/models/trigger_engine.py
示波器级硬件/软件触发引擎
支持：
- 触发模式：Auto (自动), Normal (常规), Single (单次)
- 触发边沿：Rising (上升沿), Falling (下降沿)
- 触发电平 (Level) 与源通道 (Source ID)
"""


class TriggerEngine:
    """上位机软件触发引擎"""

    def __init__(self):
        self.mode = "Auto"
        self.source_id = 1
        self.level = 0.0
        self.edge = "Rising"

        self.is_armed = False
        self.is_triggered = False

        self.last_val = None
        self.post_trigger_samples_needed = 0
        self.captured_data = {}

    def configure(self, mode: str, source_id: int, level: float, edge: str):
        self.mode = mode
        self.source_id = source_id
        self.level = level
        self.edge = edge

        if mode in ("Normal", "Single"):
            self.is_armed = True
            self.is_triggered = False
        else:
            self.is_armed = False
            self.is_triggered = False

        self.last_val = None
        self.post_trigger_samples_needed = 0
        self.captured_data.clear()
        print(
            f"[TriggerEngine] Configured: Mode={mode}, Source={source_id}, Level={level}, Edge={edge}"
        )

    def check_trigger(self, ch_id: int, val: float) -> bool:
        """检查是否满足触发边沿条件"""
        if not self.is_armed or ch_id != self.source_id:
            return False

        if self.last_val is None:
            self.last_val = val
            return False

        triggered = False
        if self.edge == "Rising":
            if self.last_val < self.level <= val:
                triggered = True
        else:
            if self.last_val > self.level >= val:
                triggered = True

        self.last_val = val

        if triggered:
            self.is_triggered = True
            print(f"[TriggerEngine] Triggered on channel {ch_id}!")
            return True

        return False

    def reset(self):
        if self.mode in ("Normal", "Single"):
            self.is_armed = True
            self.is_triggered = False
        self.last_val = None
        self.post_trigger_samples_needed = 0
        self.captured_data.clear()
