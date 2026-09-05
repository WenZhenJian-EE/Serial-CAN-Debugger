# -*- coding: utf-8 -*-
"""
文件名: server/routes/logging.py
数据落盘日志与黑匣子故障录波路由
"""

import os
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

import server.state as state

router = APIRouter()


class LoggerConfig(BaseModel):
    filename_prefix: Optional[str] = "debug_log"


class BlackboxConfig(BaseModel):
    channel_id: int
    max_limit: float
    min_limit: float


@router.post("/api/logger/start")
def start_logger(config: LoggerConfig):
    """开启异步高频数据落盘"""
    try:
        state.logger_instance.start_logging(config.filename_prefix)
        return {"status": "success", "message": f"异步日志已启动落盘: {config.filename_prefix}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/logger/stop")
def stop_logger():
    """停止异步高频数据落盘并返回文件路径"""
    try:
        path = state.logger_instance.stop_logging()
        return {"status": "success", "file_path": path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/blackbox/configure")
def configure_blackbox(config: BlackboxConfig):
    """配置黑匣子越限报警保护阈值"""
    try:
        state.blackbox_instance.configure_protection(config.channel_id, config.max_limit, config.min_limit)
        return {"status": "success", "message": "黑匣子录波安全限值配置成功"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/blackbox/status")
def get_blackbox_status():
    """获取黑匣子当前监测保护值"""
    return {
        "trigger_channel": state.blackbox_instance.trigger_channel,
        "max_limit": state.blackbox_instance.max_limit,
        "min_limit": state.blackbox_instance.min_limit,
        "is_triggered": state.blackbox_instance.is_triggered,
    }


@router.get("/api/fault_logs/list")
def list_fault_logs():
    """列出所有已记录的黑匣子故障日志"""
    log_dir = "fault_logs"
    if not os.path.exists(log_dir):
        return {"status": "success", "logs": []}
    files = [f for f in os.listdir(log_dir) if f.endswith(".csv")]
    files.sort(reverse=True)
    return {
        "status": "success",
        "logs": [
            {
                "filename": f,
                "path": os.path.abspath(os.path.join(log_dir, f)),
                "size": os.path.getsize(os.path.join(log_dir, f)),
            }
            for f in files
        ]
    }
