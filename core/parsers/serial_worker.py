# -*- coding: utf-8 -*-
"""
文件名: core/parsers/serial_worker.py
串口通信工作线程
支持：
1. 自定义 9 字节 (S帧) 与 17 字节 (D帧 录波分包) 二进制帧头尾判定与校验解析
2. 掉线自动重连机制 (Auto-Reconnect)
3. 线程安全的数据发送
"""

import serial
import struct
import time
import queue
import threading
from core.parsers.base_worker import BaseWorker


class SerialWorker(BaseWorker):
    """串口通信工作线程"""

    def __init__(
        self,
        port: str,
        baudrate: int,
        data_queue: queue.Queue,
        bytesize: int = 8,
        parity: str = "None",
        stopbits: float = 1.0,
        raw_data_queue: queue.Queue = None,
    ):
        super().__init__(data_queue)
        self.port = port
        self.baudrate = baudrate
        self.bytesize = bytesize
        self.parity = parity
        self.stopbits = stopbits
        self.serial_port = None
        self._serial_lock = threading.Lock()
        self.buffer = bytearray()
        self.max_buffer_size = 100000
        self.raw_data_queue = raw_data_queue

    def connect_device(self) -> bool:
        try:
            p_map = {"None": "N", "Even": "E", "Odd": "O", "Mark": "M", "Space": "S"}
            parity_val = p_map.get(self.parity, "N")

            self.serial_port = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                bytesize=self.bytesize,
                parity=parity_val,
                stopbits=self.stopbits,
                timeout=0.05,
                write_timeout=0.5,
            )
            if self.serial_port.is_open:
                self.set_status(
                    True,
                    f"已连接 {self.port} ({self.baudrate}bps, {self.bytesize}{parity_val}{self.stopbits})",
                )
                self.buffer.clear()
                return True
        except Exception as e:
            self.set_status(False, f"串口打开失败: {e}")
        return False

    def disconnect_device(self):
        with self._serial_lock:
            if self.serial_port and self.serial_port.is_open:
                try:
                    self.serial_port.close()
                except Exception:
                    pass
            self.serial_port = None
        self.set_status(False, "连接断开")

    def write_data(self, data: bytes) -> bool:
        if not self.is_connected or not self.serial_port:
            return False
        try:
            with self._serial_lock:
                if self.serial_port and self.serial_port.is_open:
                    self.serial_port.write(data)
                    return True
            return False
        except Exception as e:
            print(f"[SerialWorker] Write error: {e}")
            return False

    def run(self):
        self.running = True
        if not self.is_connected:
            if not self.connect_device():
                self.set_status(False, "连接失败，正在尝试重连...")

        FRAME_LEN = 9
        TAIL = ord("E")  # 0x45

        while self.running:
            try:
                with self._serial_lock:
                    is_open = (
                        self.serial_port and self.serial_port.is_open
                        if self.serial_port
                        else False
                    )

                if not is_open:
                    time.sleep(1.0)
                    if self.running:
                        self.connect_device()
                    continue

                data = None
                with self._serial_lock:
                    if self.serial_port and self.serial_port.is_open:
                        data = self.serial_port.read(1)
                        if data and self.serial_port.in_waiting:
                            data += self.serial_port.read(self.serial_port.in_waiting)

                if data:
                    self.buffer.extend(data)
                    if self.raw_data_queue is not None:
                        try:
                            self.raw_data_queue.put_nowait(("serial", data))
                        except queue.Full:
                            try:
                                self.raw_data_queue.get_nowait()
                            except Exception:
                                pass
                            try:
                                self.raw_data_queue.put_nowait(("serial", data))
                            except Exception:
                                pass
                    if len(self.buffer) > self.max_buffer_size:
                        del self.buffer[:-4096]

                    while True:
                        idx_s = self.buffer.find(b"S")
                        idx_d = self.buffer.find(b"D")

                        if idx_s == -1 and idx_d == -1:
                            self.buffer.clear()
                            break

                        if idx_s != -1 and (idx_d == -1 or idx_s < idx_d):
                            idx = idx_s
                            frame_type = "S"
                            frame_len = 9
                        else:
                            idx = idx_d
                            frame_type = "D"
                            frame_len = 17

                        if idx > 0:
                            del self.buffer[:idx]

                        if len(self.buffer) < frame_len:
                            break

                        if self.buffer[frame_len - 1] == TAIL:
                            if frame_type == "S":
                                calc_sum = sum(self.buffer[1:7]) & 0xFF
                                recv_sum = self.buffer[7]
                                if calc_sum == recv_sum:
                                    pkt_id = int.from_bytes(
                                        self.buffer[1:3], byteorder="little", signed=False
                                    )
                                    val = struct.unpack("<f", self.buffer[3:7])[0]
                                    t_now = time.time()
                                    self.data_queue.put((t_now, pkt_id, val))
                                else:
                                    print("[SerialWorker] S Checksum error")
                            else:
                                calc_sum = sum(self.buffer[1:15]) & 0xFF
                                recv_sum = self.buffer[15]
                                if calc_sum == recv_sum:
                                    packet_idx = int.from_bytes(
                                        self.buffer[1:3], byteorder="little", signed=False
                                    )
                                    total_packets = int.from_bytes(
                                        self.buffer[3:5], byteorder="little", signed=False
                                    )
                                    channel_id = int.from_bytes(
                                        self.buffer[5:7], byteorder="little", signed=False
                                    )
                                    timestamp_val = struct.unpack("<f", self.buffer[7:11])[0]
                                    val_val = struct.unpack("<f", self.buffer[11:15])[0]
                                    self.data_queue.put(
                                        (
                                            time.time(),
                                            "triggered_log",
                                            (
                                                packet_idx,
                                                total_packets,
                                                channel_id,
                                                timestamp_val,
                                                val_val,
                                            ),
                                        )
                                    )
                                else:
                                    print("[SerialWorker] D Checksum error")

                            del self.buffer[:frame_len]
                        else:
                            del self.buffer[:1]

            except (serial.SerialException, OSError) as e:
                print(f"[SerialWorker] Serial exception: {e}")
                self.set_status(False, "连接断开，正在重新连接...")
                try:
                    self.serial_port.close()
                except Exception:
                    pass
                time.sleep(1.0)
            except Exception as e:
                print(f"[SerialWorker] Thread error: {e}")
                time.sleep(1.0)

        self.disconnect_device()
