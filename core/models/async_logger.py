# -*- coding: utf-8 -*-
"""
文件名: core/models/async_logger.py
高频异步数据落盘日志记录器
设计用于在独立线程中执行写盘操作，不阻塞通信主线程，防止高波特率/高CAN吞吐下丢包。
"""

import csv
import time
import queue
import threading
import os


class AsyncLogger:
    """高频异步数据落盘日志记录器"""

    def __init__(self, log_dir="trend_logs"):
        self.log_dir = log_dir
        self.log_queue = queue.Queue()
        self.is_running = False
        self.thread = None
        self.file_handle = None
        self.csv_writer = None
        self.file_path = ""

        if not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)

    def start_logging(self, filename_prefix="debug_log"):
        if self.is_running:
            return

        timestamp = time.strftime("%Y%m%d_%H%M%S")
        self.file_path = os.path.join(
            self.log_dir, f"{filename_prefix}_{timestamp}.csv"
        )

        self.file_handle = open(
            self.file_path, "w", newline="", encoding="utf-8"
        )
        self.csv_writer = csv.writer(self.file_handle)
        self.csv_writer.writerow(["Timestamp", "ChannelID", "Value"])

        self.is_running = True
        self.thread = threading.Thread(target=self._log_worker_loop, daemon=True)
        self.thread.start()
        print(f"[AsyncLogger] Started logging to: {self.file_path}")

    def log_data(self, t_abs: float, pkt_id: int, val: float):
        if self.is_running:
            self.log_queue.put((t_abs, pkt_id, val))

    def _log_worker_loop(self):
        batch = []
        batch_size = 500
        last_flush = time.time()

        while self.is_running or not self.log_queue.empty():
            try:
                item = self.log_queue.get(timeout=0.1)
                batch.append(item)

                if len(batch) >= batch_size or (
                    time.time() - last_flush > 0.5 and len(batch) > 0
                ):
                    self.csv_writer.writerows(batch)
                    self.file_handle.flush()
                    batch.clear()
                    last_flush = time.time()

                self.log_queue.task_done()
            except queue.Empty:
                if len(batch) > 0:
                    self.csv_writer.writerows(batch)
                    self.file_handle.flush()
                    batch.clear()
                    last_flush = time.time()

    def stop_logging(self) -> str:
        if not self.is_running:
            return ""

        self.is_running = False
        if self.thread:
            self.thread.join(timeout=1.0)

        if self.file_handle:
            self.file_handle.close()
            self.file_handle = None
            self.csv_writer = None

        print(f"[AsyncLogger] Stopped. Log saved at: {self.file_path}")
        return self.file_path
