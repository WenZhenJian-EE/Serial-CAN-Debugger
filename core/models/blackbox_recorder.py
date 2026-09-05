# -*- coding: utf-8 -*-
"""
文件名: core/models/blackbox_recorder.py
黑匣子故障录波记录器
- 循环维护一个前 5 秒的环形缓冲区 (Pre-fault Buffer)
- 监控特定通道的电压、电流幅值，一旦超限，立即触发录波
- 自动追加采集后 5 秒的数据 (Post-fault Buffer)
- 自动将完整 10 秒的前后波形数据持久化落盘，用于现场故障复盘分析
"""

from collections import deque
import os
import csv
import time


class BlackboxRecorder:
    """黑匣子故障录波记录器"""

    def __init__(self, log_dir="fault_logs", max_pre_points=10000):
        self.log_dir = log_dir
        self.max_pre_points = max_pre_points
        self.pre_buffer = deque(maxlen=max_pre_points)

        self.is_triggered = False
        self.trigger_channel = 1
        self.max_limit = 350.0
        self.min_limit = -350.0

        self.post_buffer = []
        self.post_points_needed = 0
        self.total_post_points = 5000
        self.trigger_time_str = ""

        if not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)

    def configure_protection(
        self, channel_id: int, max_limit: float, min_limit: float
    ):
        self.trigger_channel = channel_id
        self.max_limit = max_limit
        self.min_limit = min_limit
        print(
            f"[Blackbox] Configured: CH={channel_id}, MaxLimit={max_limit}, MinLimit={min_limit}"
        )

    def feed(self, t_abs: float, pkt_id: int, val: float) -> str:
        """塞入实时通信数据。录波完成返回文件绝对路径，否则返回空字符串。"""
        if not self.is_triggered:
            self.pre_buffer.append((t_abs, pkt_id, val))

            if pkt_id == self.trigger_channel:
                if val > self.max_limit or val < self.min_limit:
                    self.is_triggered = True
                    self.post_points_needed = self.total_post_points
                    self.post_buffer.clear()
                    self.trigger_time_str = time.strftime("%Y%m%d_%H%M%S")
                    print(
                        f"[Blackbox] FAULT TRIGGERED! Channel {pkt_id} exceeded limits ({val:.2f}). Recording post-fault..."
                    )
        else:
            self.post_buffer.append((t_abs, pkt_id, val))
            self.post_points_needed -= 1

            if self.post_points_needed <= 0:
                filepath = self._save_fault_file()
                self.is_triggered = False
                self.post_buffer.clear()
                return filepath

        return ""

    def _save_fault_file(self) -> str:
        filepath = os.path.join(
            self.log_dir, f"fault_blackbox_{self.trigger_time_str}.csv"
        )
        all_data = list(self.pre_buffer) + self.post_buffer

        try:
            with open(filepath, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Timestamp", "ChannelID", "Value"])
                writer.writerows(all_data)
            print(f"[Blackbox] Fault wave saved successfully to: {filepath}")
            return filepath
        except Exception as e:
            print(f"[Blackbox] Failed to save fault file: {e}")
            return ""

    def reset(self):
        self.is_triggered = False
        self.pre_buffer.clear()
        self.post_buffer.clear()
        self.post_points_needed = 0
