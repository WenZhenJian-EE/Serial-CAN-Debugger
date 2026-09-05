# -*- coding: utf-8 -*-
"""
文件名: server/routes/trigger.py
示波器触发引擎路由
"""

import struct
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

import server.state as state

router = APIRouter()


class TriggerConfig(BaseModel):
    mode: str
    source_id: int
    level: float
    edge: str
    points: Optional[int] = 1000


@router.post("/api/trigger/configure")
def configure_trigger(config: TriggerConfig):
    """配置触发参数，并在有硬件连接时下发触发配置指令"""
    try:
        state.trigger_engine.configure(config.mode, config.source_id, config.level, config.edge)
        has_hardware = False
        points_val = getattr(config, "points", 1000) or 1000
        if config.mode in ("Normal", "Single"):
            with state.active_workers_lock:
                serial_worker = state.active_workers.get("serial")
                can_worker = state.active_workers.get("can")
                if serial_worker and serial_worker.is_connected:
                    has_hardware = True
                    mode_code = {"Auto": 0, "Normal": 1, "Single": 2}.get(config.mode, 0)
                    edge_code = {"Rising": 0, "Falling": 1}.get(config.edge, 0)
                    body = bytearray([int(config.source_id), mode_code, edge_code])
                    body.extend(struct.pack("<f", float(config.level)))
                    body.extend(struct.pack("<H", int(points_val)))
                    csum = sum(body) & 0xFF
                    frame = b'T' + body + bytes([csum]) + b'E'
                    serial_worker.write_data(frame)
                    print(f"[Trigger] Serial 0xE0 config frame sent: {frame.hex()}")
                elif can_worker and can_worker.is_connected:
                    has_hardware = True
                    mode_code = {"Auto": 0, "Normal": 1, "Single": 2}.get(config.mode, 0)
                    edge_code = {"Rising": 0, "Falling": 1}.get(config.edge, 0)
                    pts_scale = min(255, points_val // 20)
                    payload = bytearray([int(config.source_id), mode_code, edge_code])
                    payload.extend(struct.pack("<f", float(config.level)))
                    payload.append(pts_scale)
                    can_worker.write_data_frame(0x1E0, bytes(payload), is_extended=False)
                    print(f"[Trigger] CAN 0x1E0 config frame sent: {payload.hex()}")
        return {
            "status": "success",
            "message": f"触发参数配置成功 ({'物理硬件已同步' if has_hardware else '本地仿真已同步'})",
            "is_armed": state.trigger_engine.is_armed,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/trigger/reset")
def reset_trigger():
    """重新 Arm 触发器"""
    state.trigger_engine.reset()
    return {"status": "success", "message": "触发器已重新 armed"}


@router.get("/api/trigger/status")
def get_trigger_status():
    """查询触发器当前状态"""
    return {
        "mode": state.trigger_engine.mode,
        "is_armed": state.trigger_engine.is_armed,
        "is_triggered": state.trigger_engine.is_triggered,
    }
