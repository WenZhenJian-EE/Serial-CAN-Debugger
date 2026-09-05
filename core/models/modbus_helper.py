# -*- coding: utf-8 -*-
"""
文件名: core/models/modbus_helper.py
Modbus 协议编码与辅助工具
"""

import struct


def calculate_crc16(data: bytes) -> int:
    """计算 Modbus CRC16 校验和"""
    crc = 0xFFFF
    for pos in data:
        crc ^= pos
        for _ in range(8):
            if (crc & 1) != 0:
                crc >>= 1
                crc ^= 0xA001
            else:
                crc >>= 1
    return crc


def make_read_registers_frame(
    slave_id: int, function_code: int, start_addr: int, num_regs: int
) -> bytes:
    """构建 03(读保持) 或 04(读输入) 寄存器读取请求帧"""
    frame = bytearray(
        [
            slave_id & 0xFF,
            function_code & 0xFF,
            (start_addr >> 8) & 0xFF,
            start_addr & 0xFF,
            (num_regs >> 8) & 0xFF,
            num_regs & 0xFF,
        ]
    )
    crc = calculate_crc16(frame)
    frame.extend([crc & 0xFF, (crc >> 8) & 0xFF])
    return bytes(frame)


def make_write_single_register_frame(
    slave_id: int, addr: int, val: int
) -> bytes:
    """构建 06 写入单个寄存器请求帧"""
    frame = bytearray(
        [
            slave_id & 0xFF,
            0x06,
            (addr >> 8) & 0xFF,
            addr & 0xFF,
            (val >> 8) & 0xFF,
            val & 0xFF,
        ]
    )
    crc = calculate_crc16(frame)
    frame.extend([crc & 0xFF, (crc >> 8) & 0xFF])
    return bytes(frame)


def verify_and_parse_response(
    slave_id: int, expected_func: int, response: bytes
) -> bytes:
    """校验响应帧并析出数据负载"""
    if len(response) < 5:
        return None

    crc = calculate_crc16(response[:-2])
    recv_crc = int.from_bytes(response[-2:], byteorder="little")
    if crc != recv_crc:
        print(
            f"[ModbusHelper] CRC error. Expected {crc:04X}, received {recv_crc:04X}"
        )
        return None

    if response[0] != slave_id or response[1] != expected_func:
        print(
            f"[ModbusHelper] Response error. SlaveID/Func mismatch: expected {slave_id}/{expected_func}, received {response[0]}/{response[1]}"
        )
        return None

    if expected_func == 0x06:
        return response[2:6]

    byte_count = response[2]
    if len(response) < 3 + byte_count + 2:
        return None

    return bytes(response[3 : 3 + byte_count])


def decode_register_value(
    raw_bytes: bytes,
    offset: int,
    data_type: str,
    byte_order: str = "big",
) -> float:
    """根据数据类型解析 Modbus 寄存器里的物理量。"""
    try:
        if data_type in ("int16", "uint16"):
            if len(raw_bytes) - offset < 2:
                return 0.0
            val_bytes = raw_bytes[offset : offset + 2]
            fmt = ">h" if byte_order == "big" else "<h"
            if data_type == "uint16":
                fmt = ">H" if byte_order == "big" else "<H"
            return float(struct.unpack(fmt, val_bytes)[0])

        elif data_type in ("int32", "uint32", "float32"):
            if len(raw_bytes) - offset < 4:
                return 0.0
            val_bytes = raw_bytes[offset : offset + 4]

            if byte_order == "swap":
                val_bytes = val_bytes[2:4] + val_bytes[0:2]
                fmt = ">i"
                if data_type == "uint32":
                    fmt = ">I"
                elif data_type == "float32":
                    fmt = ">f"
            elif byte_order == "little":
                fmt = "<i"
                if data_type == "uint32":
                    fmt = "<I"
                elif data_type == "float32":
                    fmt = "<f"
            else:
                fmt = ">i"
                if data_type == "uint32":
                    fmt = ">I"
                elif data_type == "float32":
                    fmt = ">f"

            return float(struct.unpack(fmt, val_bytes)[0])
    except Exception as e:
        print(f"[ModbusHelper] Decoding error: {e}")
    return 0.0
