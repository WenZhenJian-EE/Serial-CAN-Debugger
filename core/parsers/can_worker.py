# -*- coding: utf-8 -*-
"""
文件名: core/parsers/can_worker.py
CAN总线通信工作线程
支持：
1. 基于 python-can 驱动各种硬件设备接口（PCAN, Vector, SLCAN, Kvaser, IXXAT, Virtual等）
2. 加载 .dbc 文件解析信号，支持动态物理量映射
3. 拦截高频录波分包帧 (CAN ID 0x1E1)
4. 支持 CAN FD 模式与数据段高波特率
"""

import can
import cantools
import time
import queue
import threading
import struct
from core.parsers.base_worker import BaseWorker


class CanWorker(BaseWorker):
    """CAN总线通信工作线程"""

    def __init__(
        self,
        interface: str,
        channel: str,
        bitrate: int,
        data_queue: queue.Queue,
        raw_data_queue: queue.Queue = None,
        fd_mode: bool = False,
        data_bitrate: int = 2000000,
    ):
        super().__init__(data_queue)
        self.interface = interface
        self.channel = channel
        self.bitrate = bitrate
        self.bus = None
        self.raw_data_queue = raw_data_queue
        self.fd_mode = fd_mode
        self.data_bitrate = data_bitrate

        self.db = None
        self.signal_id_map = {}  # 'SignalName' -> Channel ID
        self.next_ch_id = 100
        self.dbc_msg_cache = {}
        self._dbc_lock = threading.Lock()

    def set_dbc(self, dbc_db: cantools.database.can.Database):
        with self._dbc_lock:
            self.db = dbc_db
            self.dbc_msg_cache.clear()
            self.signal_id_map.clear()
            self.next_ch_id = 100

            for msg in self.db.messages:
                for sig in msg.signals:
                    if sig.name not in self.signal_id_map:
                        self.signal_id_map[sig.name] = self.next_ch_id
                        self.next_ch_id += 1
            print(f"[CanWorker] DBC loaded. Mapped {len(self.signal_id_map)} signals.")

    def get_signal_mappings(self):
        with self._dbc_lock:
            return dict(self.signal_id_map)

    def connect_device(self) -> bool:
        try:
            if self.interface == "virtual":
                self.bus = can.Bus(interface="virtual", channel=self.channel)
            else:
                kwargs = dict(
                    interface=self.interface,
                    channel=self.channel,
                    bitrate=self.bitrate,
                )
                if self.fd_mode:
                    kwargs["fd"] = True
                    kwargs["data_bitrate"] = self.data_bitrate
                self.bus = can.Bus(**kwargs)

            fd_info = (
                f" [FD {self.data_bitrate//1000}kbps]" if self.fd_mode else ""
            )
            self.set_status(
                True,
                f"已连接 CAN {self.interface} ({self.channel} @ {self.bitrate}bps){fd_info}",
            )
            return True
        except Exception as e:
            self.set_status(False, f"CAN 总线初始化失败: {e}")
        return False

    def disconnect_device(self):
        if self.bus:
            try:
                self.bus.shutdown()
            except Exception:
                pass
            self.bus = None
        self.set_status(False, "连接断开")

    def write_data_frame(
        self, arbitration_id: int, data: bytes, is_extended: bool = False
    ) -> bool:
        if not self.is_connected or not self.bus:
            return False
        try:
            msg = can.Message(
                arbitration_id=arbitration_id,
                data=data,
                is_extended_id=is_extended,
            )
            self.bus.send(msg)
            return True
        except Exception as e:
            print(f"[CanWorker] Send frame error: {e}")
            return False

    def run(self):
        self.running = True
        if not self.is_connected:
            if not self.connect_device():
                return

        while self.running:
            try:
                if not self.bus:
                    time.sleep(1.0)
                    self.connect_device()
                    continue

                msg = self.bus.recv(0.05)
                if msg is not None:
                    t_now = time.time()
                    if self.raw_data_queue is not None:
                        try:
                            is_fd_frame = self.fd_mode and getattr(
                                msg, "is_fd", False
                            )
                            frame_type = "FD" if is_fd_frame else "STD"
                            self.raw_data_queue.put_nowait(
                                (
                                    "can",
                                    (
                                        t_now,
                                        msg.arbitration_id,
                                        bytes(msg.data),
                                        msg.is_extended_id,
                                        frame_type,
                                    ),
                                )
                            )
                        except queue.Full:
                            try:
                                self.raw_data_queue.get_nowait()
                            except Exception:
                                pass
                            try:
                                is_fd_frame = self.fd_mode and getattr(
                                    msg, "is_fd", False
                                )
                                frame_type = "FD" if is_fd_frame else "STD"
                                self.raw_data_queue.put_nowait(
                                    (
                                        "can",
                                        (
                                            t_now,
                                            msg.arbitration_id,
                                            bytes(msg.data),
                                            msg.is_extended_id,
                                            frame_type,
                                        ),
                                    )
                                )
                            except Exception:
                                pass

                    if msg.arbitration_id == 0x1E1:
                        if len(msg.data) >= 7:
                            packet_idx = int(msg.data[0])
                            total_packets = int(msg.data[1])
                            channel_id = int(msg.data[2])
                            val_val = struct.unpack("<f", msg.data[3:7])[0]
                            t_offset = (
                                float(msg.data[7]) * 0.001
                                if len(msg.data) >= 8
                                else float(packet_idx) * 0.001
                            )

                            self.data_queue.put(
                                (
                                    time.time(),
                                    "triggered_log",
                                    (
                                        packet_idx,
                                        total_packets,
                                        channel_id,
                                        t_offset,
                                        val_val,
                                    ),
                                )
                            )
                        continue

                    db_msg = None
                    sig_map_copy = None

                    with self._dbc_lock:
                        if self.db is not None:
                            arb_id = msg.arbitration_id

                            if arb_id not in self.dbc_msg_cache:
                                try:
                                    self.dbc_msg_cache[arb_id] = (
                                        self.db.get_message_by_frame_id(arb_id)
                                    )
                                except KeyError:
                                    self.dbc_msg_cache[arb_id] = None

                            db_msg = self.dbc_msg_cache[arb_id]
                            if db_msg is not None:
                                sig_map_copy = dict(self.signal_id_map)

                    if db_msg is not None and sig_map_copy is not None:
                        try:
                            decoded = db_msg.decode(msg.data)
                            for sig_name, val in decoded.items():
                                if isinstance(
                                    val, (int, float)
                                ) and not isinstance(val, bool):
                                    pkt_id = sig_map_copy.get(sig_name)
                                    if pkt_id is not None:
                                        self.data_queue.put(
                                            (t_now, pkt_id, float(val))
                                        )
                        except Exception:
                            pass

            except Exception as e:
                print(f"[CanWorker] Read error: {e}")
                self.set_status(False, f"总线异常: {e}")
                time.sleep(1.0)

        self.disconnect_device()
