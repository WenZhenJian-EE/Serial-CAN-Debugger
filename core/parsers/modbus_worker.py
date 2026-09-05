# -*- coding: utf-8 -*-
"""
文件名: core/parsers/modbus_worker.py
Modbus-RTU 异步轮询主站工作线程。
支持:
  1. 自定义多寄存器按不同周期轮询。
  2. 读保持寄存器 (03) 与读输入寄存器 (04)。
  3. 线程安全地发送写入单个寄存器 (06) 帧。
  4. 自动掉线重连与异常校验过滤。
"""

import serial
import time
import struct
import queue
import threading
from core.parsers.base_worker import BaseWorker
from core.models import modbus_helper


class ModbusWorker(BaseWorker):
    """Modbus-RTU 异步轮询主站工作线程。"""

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
        self.raw_data_queue = raw_data_queue

        self.registers = []
        self._reg_lock = threading.Lock()
        self._serial_lock = threading.Lock()
        self._slave_status = {}

    def update_registers(self, new_registers: list):
        """在线更新轮询变量表"""
        with self._reg_lock:
            self.registers = list(new_registers)
            print(
                f"[ModbusWorker] Updated registers list. Total: {len(self.registers)}"
            )

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
                timeout=0.08,
                write_timeout=0.5,
            )
            if self.serial_port.is_open:
                self.set_status(
                    True, f"Modbus 已连接 {self.port} ({self.baudrate}bps)"
                )
                return True
        except Exception as e:
            self.set_status(False, f"Modbus 串口打开失败: {e}")
        return False

    def disconnect_device(self):
        with self._serial_lock:
            if self.serial_port and self.serial_port.is_open:
                try:
                    self.serial_port.close()
                except Exception:
                    pass
            self.serial_port = None
        self.set_status(False, "Modbus 连接断开")

    def write_register(self, slave_id: int, addr: int, val: int) -> bool:
        """主线程向串口中途插入 06 码写入帧（线程安全，支持最多 3 次重试）"""
        if not self.is_connected or not self.serial_port:
            return False

        frame = modbus_helper.make_write_single_register_frame(slave_id, addr, val)
        for attempt in range(3):
            with self._serial_lock:
                try:
                    if not self.serial_port or not self.serial_port.is_open:
                        return False

                    if self.serial_port.in_waiting:
                        self.serial_port.read(self.serial_port.in_waiting)

                    self.serial_port.write(frame)
                    time.sleep(0.01)

                    if self.raw_data_queue is not None:
                        self.raw_data_queue.put(("serial", frame))

                    resp = self.serial_port.read(8)
                    if self.raw_data_queue is not None and resp:
                        self.raw_data_queue.put(("serial", resp))

                    parsed = modbus_helper.verify_and_parse_response(
                        slave_id, 0x06, resp
                    )
                    if parsed is not None:
                        return True
                except Exception as e:
                    print(f"[ModbusWorker] Write attempt {attempt+1} failed: {e}")
            time.sleep(0.05)
        return False

    def run(self):
        self.running = True
        if not self.is_connected:
            if not self.connect_device():
                time.sleep(1.0)

        while self.running:
            try:
                if not self.serial_port or not self.serial_port.is_open:
                    time.sleep(1.0)
                    if self.running:
                        self.connect_device()
                    continue

                with self._reg_lock:
                    current_regs = list(self.registers)

                if not current_regs:
                    time.sleep(0.1)
                    continue

                for reg in current_regs:
                    if not self.running:
                        break

                    slave_id = reg.get("slave_id", 1)

                    now = time.time()
                    status = self._slave_status.get(slave_id)
                    if status and status.get("fail_count", 0) >= 3:
                        if now < status.get("suspended_until", 0.0):
                            continue

                    func = reg.get("func", 3)
                    addr = reg.get("addr", 0)
                    data_type = reg.get("type", "int16")
                    order = reg.get("order", "big")
                    coef = reg.get("coef", 1.0)
                    ch_id = reg.get("ch_id", 1)

                    num_regs = (
                        2 if data_type in ("int32", "uint32", "float32") else 1
                    )

                    frame = modbus_helper.make_read_registers_frame(
                        slave_id, func, addr, num_regs
                    )

                    with self._serial_lock:
                        if not self.serial_port or not self.serial_port.is_open:
                            break

                        if self.serial_port.in_waiting:
                            try:
                                self.serial_port.read(
                                    self.serial_port.in_waiting
                                )
                            except Exception:
                                pass

                        self.serial_port.write(frame)
                        if self.raw_data_queue is not None:
                            self.raw_data_queue.put(("serial", frame))

                        expected_len = 3 + num_regs * 2 + 2
                        resp = self.serial_port.read(expected_len)

                        if self.raw_data_queue is not None and resp:
                            self.raw_data_queue.put(("serial", resp))

                    payload = modbus_helper.verify_and_parse_response(
                        slave_id, func, resp
                    )
                    if payload is not None:
                        if slave_id in self._slave_status:
                            self._slave_status[slave_id]["fail_count"] = 0

                        raw_val = modbus_helper.decode_register_value(
                            payload, 0, data_type, order
                        )
                        scaled_val = raw_val * coef
                        t_now = time.time()
                        self.data_queue.put((t_now, ch_id, scaled_val))
                    else:
                        if slave_id not in self._slave_status:
                            self._slave_status[slave_id] = {
                                "fail_count": 0,
                                "suspended_until": 0.0,
                            }
                        self._slave_status[slave_id]["fail_count"] += 1
                        if self._slave_status[slave_id]["fail_count"] >= 3:
                            self._slave_status[slave_id]["suspended_until"] = (
                                time.time() + 5.0
                            )
                            print(
                                f"[ModbusWorker] Slave ID {slave_id} consecutive timeout. Suspending poll for 5s."
                            )

                    time.sleep(0.015)

                time.sleep(0.05)

            except (serial.SerialException, OSError) as e:
                self.set_status(
                    False, "Modbus 串口连接断开，正在尝试重连..."
                )
                try:
                    self.serial_port.close()
                except Exception:
                    pass
                self.serial_port = None
                time.sleep(1.0)
            except Exception as e:
                print(f"[ModbusWorker] Loop error: {e}")
                time.sleep(1.0)

        self.disconnect_device()
