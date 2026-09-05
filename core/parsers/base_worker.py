# -*- coding: utf-8 -*-
"""
文件名: core/parsers/base_worker.py
上位机通信工作线程基类
定义了标准的线程周期、队列推送和连接管理接口，方便后续自由扩展新硬件通道。
"""

import threading
import queue
import time


class BaseWorker(threading.Thread):
    """上位机通信工作线程基类"""

    def __init__(self, data_queue: queue.Queue):
        super().__init__()
        self.data_queue = data_queue
        self.running = False
        self.is_connected = False
        self.status_message = "未连接"
        self._status_lock = threading.Lock()

    def set_status(self, connected: bool, message: str):
        with self._status_lock:
            self.is_connected = connected
            self.status_message = message
            print(f"[{self.__class__.__name__}] Status changed: {message}")

    def get_status(self):
        with self._status_lock:
            return {
                "connected": self.is_connected,
                "message": self.status_message,
            }

    def connect_device(self) -> bool:
        """子类需实现具体的设备连接逻辑"""
        raise NotImplementedError

    def disconnect_device(self):
        """子类需实现具体的设备断开逻辑"""
        raise NotImplementedError

    def run(self):
        """子类需实现具体的数据读取主循环"""
        raise NotImplementedError

    def write_data(self, data: bytes) -> bool:
        """子类需实现具体的数据发送逻辑"""
        raise NotImplementedError

    def stop(self):
        self.running = False
        self.disconnect_device()
        print(f"[{self.__class__.__name__}] Worker thread stopped.")
