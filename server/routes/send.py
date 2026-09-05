# -*- coding: utf-8 -*-
"""
文件名: server/routes/send.py
数据发送路由（串口原始/协议发送 + CAN 原始/协议/周期发送）
"""

import struct
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

import server.state as state

router = APIRouter()


# ─── Pydantic 模型 ────────────────────────────────────────────────────────────

class SerialSendRawConfig(BaseModel):
    data: str
    is_hex: bool


class SerialSendProtocolConfig(BaseModel):
    id: int
    value: float


class CanSendRawConfig(BaseModel):
    arbitration_id: int
    data_hex: str
    is_hex: bool
    is_extended: Optional[bool] = False


class CanSendProtocolConfig(BaseModel):
    arbitration_id: int
    value: float


class CanPeriodicConfig(BaseModel):
    arbitration_id: int
    data_hex: str
    is_hex: bool
    interval_ms: int
    is_extended: Optional[bool] = False


# ─── 工具函数 ─────────────────────────────────────────────────────────────────

def parse_hex_bytes(hex_str: str) -> bytes:
    cleaned = ''.join(c for c in hex_str if c.isalnum())
    return bytes.fromhex(cleaned)


# ─── 串口发送 ─────────────────────────────────────────────────────────────────

@router.post("/api/serial/send_raw")
def serial_send_raw(config: SerialSendRawConfig):
    with state.active_workers_lock:
        worker = state.active_workers["serial"]
        if not worker or not worker.is_connected:
            raise HTTPException(status_code=400, detail="串口未打开或未连接")
        try:
            data = parse_hex_bytes(config.data) if config.is_hex else config.data.encode('utf-8')
            worker.write_data(data)
            return {"status": "success", "message": "串口数据已发送"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/serial/send_protocol")
def serial_send_protocol(config: SerialSendProtocolConfig):
    with state.active_workers_lock:
        worker = state.active_workers["serial"]
        if not worker or not worker.is_connected:
            raise HTTPException(status_code=400, detail="串口未打开或未连接")
        try:
            payload = config.id.to_bytes(2, byteorder='little', signed=False) + struct.pack('<f', config.value)
            checksum = sum(payload) & 0xFF
            packet = bytearray([0x53]) + payload + bytearray([checksum, 0x45])
            worker.write_data(bytes(packet))
            return {"status": "success", "message": f"协议包已发送 (ID: {config.id}, Val: {config.value})"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


# ─── CAN 发送 ─────────────────────────────────────────────────────────────────

@router.post("/api/can/send_raw")
def can_send_raw(config: CanSendRawConfig):
    with state.active_workers_lock:
        worker = state.active_workers["can"]
        if not worker or not worker.is_connected:
            raise HTTPException(status_code=400, detail="CAN未打开或未连接")
        try:
            data = parse_hex_bytes(config.data_hex) if config.is_hex else config.data_hex.encode('utf-8')
            worker.write_data_frame(arbitration_id=config.arbitration_id, data=data[:8], is_extended=config.is_extended)
            return {"status": "success", "message": "CAN帧已发送"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/can/send_protocol")
def can_send_protocol(config: CanSendProtocolConfig):
    with state.active_workers_lock:
        worker = state.active_workers["can"]
        if not worker or not worker.is_connected:
            raise HTTPException(status_code=400, detail="CAN未打开或未连接")
        try:
            data = struct.pack('<f', config.value)
            worker.write_data_frame(arbitration_id=config.arbitration_id, data=data, is_extended=(config.arbitration_id > 0x7FF))
            return {"status": "success", "message": f"CAN协议数据已发送 (ID: 0x{config.arbitration_id:X}, Val: {config.value})"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/can/periodic/start")
def can_periodic_start(config: CanPeriodicConfig):
    with state.active_workers_lock:
        worker = state.active_workers["can"]
        if not worker or not worker.is_connected:
            raise HTTPException(status_code=400, detail="CAN未打开或未连接")
        try:
            data = parse_hex_bytes(config.data_hex) if config.is_hex else config.data_hex.encode('utf-8')
            state.can_periodic_config["arbitration_id"] = config.arbitration_id
            state.can_periodic_config["data"] = data[:8]
            state.can_periodic_config["interval"] = max(0.01, config.interval_ms / 1000.0)
            state.can_periodic_config["is_extended"] = config.is_extended
            state.can_periodic_config["running"] = True
            return {"status": "success", "message": "CAN周期发送已启动"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/can/periodic/stop")
def can_periodic_stop():
    state.can_periodic_config["running"] = False
    return {"status": "success", "message": "CAN周期发送已停止"}
