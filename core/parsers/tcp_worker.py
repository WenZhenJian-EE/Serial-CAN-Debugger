# -*- coding: utf-8 -*-
"""
文件名: core/parsers/tcp_worker.py
TCP Socket 客户端 Worker — 支持 Wi-Fi 下位机数据透传。
协议格式与 SerialWorker 完全兼容（14 字节二进制帧：little-endian double + uint16 + float）。
"""

import socket
import struct
import queue
import threading
from core.parsers.base_worker import BaseWorker

PACK_FMT = "<dHf"
POINT_SIZE = struct.calcsize(PACK_FMT)


class TcpWorker(BaseWorker):
    """TCP 客户端 Worker，以流模式接收下位机的二进制数据帧。"""

    def __init__(
        self,
        host: str,
        port: int,
        data_queue: queue.Queue,
        raw_data_queue: queue.Queue = None,
    ):
        super().__init__(data_queue)
        self.host = host
        self.port = port
        self.raw_data_queue = raw_data_queue
        self._sock = None
        self._sock_lock = threading.Lock()
        self._recv_buf = bytearray()

    def connect_device(self) -> bool:
        """建立 TCP 连接，成功返回 True，失败返回 False。"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5.0)
            sock.connect((self.host, self.port))
            sock.settimeout(1.0)
            with self._sock_lock:
                self._sock = sock
            self.set_status(True, f"已连接 {self.host}:{self.port}")
            return True
        except Exception as e:
            self.set_status(False, f"TCP 连接失败: {e}")
            return False

    def disconnect_device(self):
        """关闭 TCP Socket。"""
        with self._sock_lock:
            if self._sock:
                try:
                    self._sock.close()
                except Exception:
                    pass
                self._sock = None
        self.set_status(False, "TCP 已断开")

    def write_data(self, data: bytes) -> bool:
        """向下位机发送原始字节（如控制指令）。"""
        with self._sock_lock:
            sock = self._sock
        if sock and self.is_connected:
            try:
                sock.sendall(data)
                return True
            except Exception as e:
                print(f"[TcpWorker] Send error: {e}")
        return False

    def run(self):
        """后台线程主循环：持续接收并解析二进制帧，写入 data_queue。"""
        self.running = True
        if not self.is_connected:
            if not self.connect_device():
                self.running = False
                return

        print(
            f"[TcpWorker] Connected to {self.host}:{self.port}, POINT_SIZE={POINT_SIZE}"
        )
        self._recv_buf.clear()

        while self.running:
            try:
                with self._sock_lock:
                    sock = self._sock
                if sock is None:
                    break

                try:
                    chunk = sock.recv(4096)
                except socket.timeout:
                    continue
                except (ConnectionResetError, OSError):
                    print("[TcpWorker] Remote closed connection.")
                    break

                if not chunk:
                    print("[TcpWorker] Remote closed connection (empty recv).")
                    break

                self._recv_buf.extend(chunk)

                if self.raw_data_queue is not None:
                    try:
                        self.raw_data_queue.put_nowait(("tcp", chunk))
                    except queue.Full:
                        try:
                            self.raw_data_queue.get_nowait()
                        except Exception:
                            pass
                        try:
                            self.raw_data_queue.put_nowait(("tcp", chunk))
                        except Exception:
                            pass

                while len(self._recv_buf) >= POINT_SIZE:
                    frame = bytes(self._recv_buf[:POINT_SIZE])
                    self._recv_buf = self._recv_buf[POINT_SIZE:]
                    try:
                        t, ch_id, val = struct.unpack(PACK_FMT, frame)
                        self.data_queue.put_nowait((t, ch_id, val))
                    except struct.error:
                        self._recv_buf = bytearray(frame[1:]) + self._recv_buf

            except Exception as e:
                print(f"[TcpWorker] Thread error: {e}")
                break

        self.disconnect_device()
        print("[TcpWorker] Worker thread exited.")
