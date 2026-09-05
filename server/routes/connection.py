# -*- coding: utf-8 -*-
"""
文件名: server/routes/connection.py
硬件连接管理路由（串口 / CAN / TCP / Modbus / DBC 解析）
"""

import struct
import threading
import os
from typing import Optional, List

from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
import serial.tools.list_ports
import cantools

import server.state as state
from core.parsers.serial_worker import SerialWorker
from core.parsers.modbus_worker import ModbusWorker
from core.parsers.can_worker import CanWorker
from core.parsers.tcp_worker import TcpWorker

router = APIRouter()


# ─── Pydantic 模型 ────────────────────────────────────────────────────────────

class SerialConnectConfig(BaseModel):
    port: str
    baudrate: int
    bytesize: Optional[int] = 8
    parity: Optional[str] = "None"
    stopbits: Optional[float] = 1.0
    protocol: Optional[str] = "custom"


class CanConnectConfig(BaseModel):
    interface: str
    channel: str
    bitrate: int
    fd_mode: Optional[bool] = False
    data_bitrate: Optional[int] = 2000000


class TcpConnectConfig(BaseModel):
    host: str
    port: int


class ModbusRegisterItem(BaseModel):
    slave_id: int
    func: int
    addr: int
    type: str
    order: str
    coef: float
    ch_id: int


class ModbusWriteRequest(BaseModel):
    slave_id: int
    addr: int
    val: int


# ─── 串口 ─────────────────────────────────────────────────────────────────────

@router.get("/api/ports")
def get_com_ports():
    """扫描系统可用串口列表"""
    try:
        ports = [p.device for p in serial.tools.list_ports.comports()]
        return {"status": "success", "ports": ports}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.post("/api/auto_probe")
async def auto_probe_serial():
    """自动探针串口，检测特征下位机"""
    import serial
    ports = [p.device for p in serial.tools.list_ports.comports()]
    detected_port = None
    for port in ports:
        try:
            for baud in [115200, 9600]:
                import time
                s = serial.Serial(port, baud, timeout=0.08)
                s.write(b"PING\r\n")
                time.sleep(0.015)
                resp = s.read(10)
                if b"PONG" in resp or len(resp) > 0:
                    detected_port = port
                    s.close()
                    break
                s.close()
            if detected_port:
                break
        except Exception:
            pass
    if not detected_port:
        for p in serial.tools.list_ports.comports():
            desc = p.description.lower()
            if any(term in desc for term in ["ch340", "cp210", "usb-to-uart", "pl2303", "ftdi", "ft232"]):
                detected_port = p.device
                break
    return {"status": "success", "success": detected_port is not None, "port": detected_port}


@router.post("/api/serial/connect")
def connect_serial(config: SerialConnectConfig):
    """连接串口"""
    with state.active_workers_lock:
        if state.active_workers["serial"] is not None:
            raise HTTPException(status_code=400, detail="串口已处于连接状态，请先断开。")
        try:
            if config.protocol == "modbus":
                worker = ModbusWorker(
                    port=config.port, baudrate=config.baudrate,
                    data_queue=state.data_queue,
                    bytesize=config.bytesize, parity=config.parity,
                    stopbits=config.stopbits, raw_data_queue=state.raw_data_queue
                )
            else:
                worker = SerialWorker(
                    port=config.port, baudrate=config.baudrate,
                    data_queue=state.data_queue,
                    bytesize=config.bytesize, parity=config.parity,
                    stopbits=config.stopbits, raw_data_queue=state.raw_data_queue
                )
            if worker.connect_device():
                if config.protocol == "modbus":
                    worker.update_registers(state.global_modbus_registers)
                worker.start()
                state.active_workers["serial"] = worker
                return {"status": "success", "message": f"成功连接至串口 {config.port} ({'Modbus' if config.protocol == 'modbus' else 'Custom'}模式)"}
            else:
                status_info = worker.get_status()
                raise HTTPException(status_code=500, detail=status_info["message"])
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/serial/disconnect")
def disconnect_serial():
    """断开串口"""
    with state.active_workers_lock:
        worker = state.active_workers["serial"]
        if worker:
            worker.stop()
            state.active_workers["serial"] = None
            return {"status": "success", "message": "串口连接已断开"}
        return {"status": "info", "message": "串口未连接"}


@router.post("/api/modbus/registers")
def configure_modbus_registers(registers: List[ModbusRegisterItem]):
    """配置与同步 Modbus 寄存器轮询表"""
    with state.active_workers_lock:
        regs_list = [r.model_dump() for r in registers]
        state.global_modbus_registers = regs_list
        worker = state.active_workers["serial"]
        if worker is not None and isinstance(worker, ModbusWorker):
            worker.update_registers(regs_list)
            return {"status": "success", "message": "Modbus 寄存器轮询表已同步更新"}
        return {"status": "success", "message": "Modbus 寄存器表配置已缓存 (串口连上后会自动载入)"}


@router.post("/api/modbus/write")
def write_modbus_register(config: ModbusWriteRequest):
    """向指定 Modbus 设备写入单个寄存器 (06 功能码)"""
    with state.active_workers_lock:
        worker = state.active_workers["serial"]
        if (worker is None or not isinstance(worker, ModbusWorker)) and state.is_streaming:
            state.simulated_modbus_values[(config.slave_id, config.addr)] = config.val
            return {"status": "success", "message": f"[仿真] 成功写入寄存器 {config.addr} = {config.val}"}
        if worker is None or not isinstance(worker, ModbusWorker):
            raise HTTPException(status_code=400, detail="Modbus 串口未连接，无法执行写入。")
        success = worker.write_register(config.slave_id, config.addr, config.val)
        if success:
            return {"status": "success", "message": f"成功写入寄存器 {config.addr} = {config.val}"}
        else:
            raise HTTPException(status_code=500, detail="写入寄存器失败，设备未响应或 CRC 错误。")


# ─── CAN ─────────────────────────────────────────────────────────────────────

@router.get("/api/can/providers")
def get_can_providers():
    """获取支持的 CAN 硬件适配器列表"""
    return {
        "providers": [
            {"label": "Virtual (虚拟测试)", "value": "virtual"},
            {"label": "PCAN (PEAK-System)", "value": "pcan"},
            {"label": "SLCAN (USB-CAN 转换器)", "value": "slcan"},
            {"label": "Vector (VN16xx/VN56xx)", "value": "vector"},
            {"label": "Kvaser (Leaf/Memorator)", "value": "kvaser"},
            {"label": "IXXAT (USB-to-CAN)", "value": "ixxat"},
            {"label": "SocketCAN (Linux)", "value": "socketcan"},
        ]
    }


@router.post("/api/can/connect")
def connect_can(config: CanConnectConfig):
    """连接 CAN 总线"""
    with state.active_workers_lock:
        if state.active_workers["can"] is not None:
            raise HTTPException(status_code=400, detail="CAN总线已处于连接状态，请先断开。")
        try:
            worker = CanWorker(
                config.interface, config.channel, config.bitrate, state.data_queue,
                raw_data_queue=state.raw_data_queue,
                fd_mode=config.fd_mode,
                data_bitrate=config.data_bitrate,
            )
            if state.pending_dbc:
                worker.set_dbc(state.pending_dbc)
            if worker.connect_device():
                worker.start()
                state.active_workers["can"] = worker
                return {"status": "success", "message": f"成功连接至 CAN {config.interface}"}
            else:
                status_info = worker.get_status()
                raise HTTPException(status_code=500, detail=status_info["message"])
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/can/disconnect")
def disconnect_can():
    """断开 CAN 总线"""
    with state.active_workers_lock:
        worker = state.active_workers["can"]
        if worker:
            worker.stop()
            state.active_workers["can"] = None
            return {"status": "success", "message": "CAN连接已断开"}
        return {"status": "info", "message": "CAN未连接"}


@router.post("/api/can/load_dbc")
async def load_dbc(file: UploadFile = File(...)):
    """上传 .dbc 文件，应用到当前 CAN worker"""
    try:
        contents = await file.read()
        dbc_text = contents.decode("utf-8", errors="ignore")
        db = cantools.database.load_string(dbc_text)
        dbc_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploaded.dbc")
        try:
            with open(dbc_path, "wb") as f:
                f.write(contents)
        except Exception as e:
            print(f"[Server] Failed to persist DBC: {e}")
        with state.active_workers_lock:
            state.pending_dbc = db
            worker = state.active_workers["can"]
            if worker:
                worker.set_dbc(db)
                signal_map = worker.get_signal_mappings()
            else:
                signal_map = {}
                next_id = 100
                for msg in db.messages:
                    for sig in msg.signals:
                        if sig.name not in signal_map:
                            signal_map[sig.name] = next_id
                            next_id += 1
            return {
                "status": "success",
                "message": "DBC 加载成功！已在 CAN Worker 部署配置并重建信号通道映射。",
                "signals": signal_map,
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DBC 解析失败: {e}")


@router.get("/api/connection/status")
def get_connection_status():
    """获取所有硬件接口的连接状态"""
    with state.active_workers_lock:
        serial_status = state.active_workers["serial"].get_status() if state.active_workers["serial"] else {"connected": False, "message": "未连接"}
        can_status = state.active_workers["can"].get_status() if state.active_workers["can"] else {"connected": False, "message": "未连接"}
        tcp_w = state.active_workers.get("tcp")
        tcp_status = {"connected": bool(tcp_w and tcp_w.is_connected), "message": tcp_w.status_message if tcp_w else "未连接"}
        return {"serial": serial_status, "can": can_status, "tcp": tcp_status}


# ─── TCP ─────────────────────────────────────────────────────────────────────

@router.post("/api/tcp/connect")
def connect_tcp(config: TcpConnectConfig):
    """连接到 TCP 下位机（Wi-Fi 数据透传）"""
    with state.active_workers_lock:
        existing = state.active_workers.get("tcp")
        if existing and existing.is_connected:
            return {"status": "already_connected"}
        if existing:
            existing.stop()
            state.active_workers["tcp"] = None
    worker = TcpWorker(config.host, config.port, state.data_queue, state.raw_data_queue)
    if not worker.connect_device():
        raise HTTPException(status_code=500, detail=f"无法连接到 {config.host}:{config.port}")
    t = threading.Thread(target=worker.run, daemon=True)
    t.start()
    with state.active_workers_lock:
        state.active_workers["tcp"] = worker
    return {"status": "connected", "host": config.host, "port": config.port}


@router.post("/api/tcp/disconnect")
def disconnect_tcp():
    """断开 TCP 连接"""
    with state.active_workers_lock:
        w = state.active_workers.get("tcp")
        if w:
            w.stop()
            state.active_workers["tcp"] = None
    return {"status": "disconnected"}


@router.get("/api/tcp/status")
def tcp_status():
    """获取当前 TCP 连接状态"""
    with state.active_workers_lock:
        w = state.active_workers.get("tcp")
        connected = bool(w and w.is_connected)
    return {"connected": connected}
