# -*- coding: utf-8 -*-
"""
文件名: server/routes/analysis.py
分析与高级算法路由（CSV 解析 / DSP / Bode 扫频 / 阶跃响应 / 系统辨识 / MAT 导出）
"""

import os
import json
import time
import math
import io
from datetime import datetime
from typing import Optional, List, Dict, Any

import numpy as np
from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from scipy.io import savemat

import server.state as state
from core.models import dsp_engine, bode_sweeper
from core.models.loop_id_helper import identify_second_order_system

router = APIRouter()


# ─── Pydantic 模型 ────────────────────────────────────────────────────────────

class FFTConfig(BaseModel):
    time_arr: list[float]
    data_arr: list[float]


class MathConfig(BaseModel):
    expression: str
    channels_data: dict[int, list[float]]
    dt: Optional[float] = 0.0001


class BodeConfig(BaseModel):
    start_freq: float
    stop_freq: float
    steps: int
    amplitude: float


class BodeSaveConfig(BaseModel):
    name: str
    points: List[List[float]]
    margins: Optional[Dict[str, Any]] = None


class SystemIdentifyRequest(BaseModel):
    t_arr: List[float]
    y_arr: List[float]
    step_val: Optional[float] = 1.0


class StepResponseRequest(BaseModel):
    t_arr: List[float]
    y_arr: List[float]
    settle_band: Optional[float] = 2.0


class MatExportRequest(BaseModel):
    channels: List[Dict[str, Any]]


# ─── CSV 离线分析 ─────────────────────────────────────────────────────────────

@router.post("/api/analyze/csv")
async def analyze_oscilloscope_csv(file: UploadFile = File(...)):
    """解析示波器导出的 CSV 文件"""
    try:
        contents = await file.read()
        lines = contents.decode('utf-8', errors='ignore').split('\n')
        skip_rows = 0
        for i, line in enumerate(lines[:150]):
            parts = line.strip().split(',')
            if len(parts) >= 2:
                try:
                    float(parts[0].strip())
                    float(parts[1].strip())
                    skip_rows = i
                    break
                except (ValueError, IndexError):
                    continue

        raw_df = pd.read_csv(
            io.BytesIO(contents),
            skiprows=skip_rows,
            header=None,
            on_bad_lines='skip',
            encoding='utf-8',
            encoding_errors='ignore'
        )
        raw_df = raw_df.dropna(how='all').reset_index(drop=True)

        col_names = []
        if skip_rows > 0:
            for i, line in enumerate(lines[:skip_rows]):
                parts = [p.strip() for p in line.split(',')]
                if len(parts) >= raw_df.shape[1]:
                    col_names = parts[:raw_df.shape[1]]
                    break
        if not col_names or len(col_names) != raw_df.shape[1]:
            col_names = [f"CH{i+1}" if i > 0 else "Time" for i in range(raw_df.shape[1])]

        df = raw_df.copy()
        df.columns = col_names[:df.shape[1]]
        for col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        df = df.dropna()

        return {
            "status": "success",
            "columns": col_names,
            "data": df.values.tolist(),
            "total_points": len(df)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"CSV 解析失败: {str(e)}")


@router.get("/api/analyze/csv_by_path")
async def analyze_csv_by_path(path: str):
    """通过本地文件路径直接解析 CSV（用于故障回放录波）"""
    try:
        if not os.path.exists(path):
            raise HTTPException(status_code=404, detail=f"文件不存在: {path}")
        df = pd.read_csv(path)
        return {
            "status": "success",
            "columns": df.columns.tolist(),
            "data": df.values.tolist(),
            "total_points": len(df)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"CSV 路径解析失败: {str(e)}")


# ─── DSP ─────────────────────────────────────────────────────────────────────

@router.post("/api/dsp/fft")
def post_dsp_fft(config: FFTConfig):
    """计算所给一维波形数据的 FFT 谱与 THD"""
    try:
        freqs, amps = dsp_engine.compute_fft(config.time_arr, config.data_arr)
        if freqs is None:
            raise HTTPException(status_code=400, detail="数据点数过少，无法计算 FFT")
        thd_val = dsp_engine.calculate_thd(freqs, amps)
        return {"status": "success", "frequencies": freqs, "amplitudes": amps, "thd": thd_val}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/dsp/math")
def post_dsp_math(config: MathConfig):
    """解析并计算数学通道矢量"""
    try:
        res = dsp_engine.evaluate_math_expression(config.expression, config.channels_data, config.dt)
        if res is None:
            raise HTTPException(status_code=400, detail="数学表达式解析失败或输入通道数据为空")
        return {"status": "success", "data": res}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── Bode 扫频 ────────────────────────────────────────────────────────────────

@router.post("/api/bode/sweep")
def run_bode_sweep(config: BodeConfig):
    """运行扫频仪，在指定频段范围内执行对数频率步进扫频"""
    results = []
    freq_points = np.logspace(
        math.log10(config.start_freq),
        math.log10(config.stop_freq),
        config.steps
    )
    old_is_streaming = state.is_streaming
    state.is_streaming = True
    try:
        for freq in freq_points:
            gain, phase = bode_sweeper.sweep_point(
                freq=float(freq),
                amplitude=config.amplitude,
                active_workers=state.active_workers,
                active_workers_lock=state.active_workers_lock,
                data_queue=state.data_queue
            )
            results.append({"frequency": float(freq), "gain": float(gain), "phase": float(phase)})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"扫频执行异常: {e}")
    finally:
        state.is_streaming = old_is_streaming
    return {"status": "success", "data": results}


@router.post("/api/bode/history/save")
def save_bode_history(config: BodeSaveConfig):
    """保存单次扫频数据到本地 JSON 文件"""
    try:
        history_dir = os.path.join(os.getcwd(), "bode_history")
        os.makedirs(history_dir, exist_ok=True)
        safe_name = "".join(c for c in config.name if c.isalnum() or c in (' ', '_', '-')).rstrip().replace(' ', '_') or "unnamed"
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"bode_{timestamp}_{safe_name}.json"
        filepath = os.path.join(history_dir, filename)
        data_to_save = {"name": config.name, "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"), "points": config.points, "margins": config.margins}
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data_to_save, f, ensure_ascii=False, indent=2)
        return {"status": "success", "filename": filename, "data": data_to_save}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/bode/history/list")
def list_bode_history():
    """获取所有历史扫频数据曲线列表"""
    history_dir = os.path.join(os.getcwd(), "bode_history")
    if not os.path.exists(history_dir):
        return {"status": "success", "data": []}
    results = []
    try:
        for file in os.listdir(history_dir):
            if file.endswith(".json") and file.startswith("bode_"):
                filepath = os.path.join(history_dir, file)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        results.append({"filename": file, "name": data.get("name", "未命名"), "timestamp": data.get("timestamp", ""), "points": data.get("points", []), "margins": data.get("margins", None)})
                except Exception as ex:
                    print(f"Error reading Bode history file {file}: {ex}")
        results.sort(key=lambda x: x["filename"], reverse=True)
        return {"status": "success", "data": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/bode/history/delete")
def delete_bode_history(filename: str):
    """删除指定的历史扫频文件"""
    try:
        history_dir = os.path.join(os.getcwd(), "bode_history")
        if ".." in filename or os.path.isabs(filename):
            raise HTTPException(status_code=400, detail="非法文件名")
        filepath = os.path.join(history_dir, filename)
        if os.path.exists(filepath):
            os.remove(filepath)
            return {"status": "success", "message": f"Deleted {filename}"}
        else:
            raise HTTPException(status_code=404, detail="文件不存在")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── 阶跃响应 & 系统辨识 ──────────────────────────────────────────────────────

@router.post("/api/identify_system")
def identify_system_tf(req: SystemIdentifyRequest):
    """在线时域二阶环路系统参数及传递函数辨识"""
    res = identify_second_order_system(req.t_arr, req.y_arr, req.step_val)
    if not res["success"]:
        raise HTTPException(status_code=400, detail=res["message"])
    return res


@router.post("/api/analyze/step_response")
def analyze_step_response(req: StepResponseRequest):
    """阶跃响应自动评估（超调/峰值/上升时间/调节时间/下冲）"""
    t = np.array(req.t_arr, dtype=float)
    y = np.array(req.y_arr, dtype=float)
    band_pct = float(req.settle_band) / 100.0
    if len(t) < 10:
        raise HTTPException(status_code=400, detail="数据点数过少，至少需要10个点")
    if len(t) != len(y):
        raise HTTPException(status_code=400, detail="t_arr 与 y_arr 长度不一致")
    if not (0.1 <= req.settle_band <= 20.0):
        raise HTTPException(status_code=400, detail="settle_band 必须在 0.1% ~ 20% 之间")
    n = len(y)
    pre_n = max(2, n // 5)
    post_n = max(2, n // 5)
    y_ss_pre = float(np.mean(y[:pre_n]))
    y_ss_post = float(np.mean(y[n - post_n:]))
    step_amp = y_ss_post - y_ss_pre
    if abs(step_amp) < 1e-12:
        raise HTTPException(status_code=400, detail="信号阶跃幅度过小（<1e-12），无法识别阶跃响应")

    t_step = float(t[0])
    for i in range(n):
        if abs(y[i] - y_ss_pre) > 0.02 * abs(step_amp):
            t_step = float(t[i])
            break

    peak_idx = int(np.argmax(y)) if step_amp > 0 else int(np.argmin(y))
    y_peak = float(y[peak_idx])
    overshoot = (y_peak - y_ss_post) / abs(step_amp) * 100.0
    peak_time = max(0.0, float(t[peak_idx] - t_step))

    y10 = y_ss_pre + 0.10 * step_amp
    y90 = y_ss_pre + 0.90 * step_amp
    t_rise_start = t_rise_end = None
    for i in range(n):
        if step_amp > 0:
            if t_rise_start is None and y[i] >= y10:
                t_rise_start = float(t[i])
            if t_rise_end is None and y[i] >= y90:
                t_rise_end = float(t[i])
                break
        else:
            if t_rise_start is None and y[i] <= y10:
                t_rise_start = float(t[i])
            if t_rise_end is None and y[i] <= y90:
                t_rise_end = float(t[i])
                break
    rise_time = round(t_rise_end - t_rise_start, 6) if (t_rise_start is not None and t_rise_end is not None) else None

    band_abs = abs(step_amp) * band_pct
    last_out_idx = -1
    for i in range(n):
        if abs(y[i] - y_ss_post) > band_abs:
            last_out_idx = i

    if last_out_idx >= 0:
        settle_time = max(0.0, float(t[last_out_idx] - t_step))
        settle_time = round(settle_time, 6)
    else:
        settle_time = 0.0
    undershoot = 0.0
    if step_amp > 0:
        y_min = float(np.min(y))
        if y_min < y_ss_pre:
            undershoot = (y_ss_pre - y_min) / abs(step_amp) * 100.0
    else:
        y_max = float(np.max(y))
        if y_max > y_ss_pre:
            undershoot = (y_max - y_ss_pre) / abs(step_amp) * 100.0

    return {
        "success": True,
        "y_ss_pre": round(y_ss_pre, 6), "y_ss_post": round(y_ss_post, 6),
        "step_amp": round(step_amp, 6), "overshoot_pct": round(overshoot, 3),
        "peak_time_s": round(peak_time, 6), "y_peak": round(y_peak, 6),
        "rise_time_s": rise_time, "settling_time_s": settle_time,
        "undershoot_pct": round(undershoot, 3),
        "settle_band_pct": req.settle_band, "band_abs": round(band_abs, 6),
        "t_start": round(float(t[0]), 6), "t_end": round(float(t[-1]), 6)
    }


# ─── MATLAB .mat 文件导出 ─────────────────────────────────────────────────────

@router.post("/api/export/mat")
def export_to_mat(req: MatExportRequest):
    """将前端传来的多通道波形数据导出为 MATLAB .mat 文件。"""
    if not req.channels:
        raise HTTPException(status_code=400, detail="没有可导出的通道数据")

    mat_dict: Dict[str, Any] = {}

    for ch in req.channels:
        ch_id = ch.get("id", 0)
        name = ch.get("name", f"ch{ch_id}")
        scale = float(ch.get("scale", 1.0))
        offset = float(ch.get("offset", 0.0))
        x_arr = np.array(ch.get("x", []), dtype=np.float64)
        y_raw = np.array(ch.get("y", []), dtype=np.float64)
        y_scaled = y_raw * scale + offset

        safe_name = ''.join(c if c.isalnum() or c == '_' else '_' for c in name)
        if not safe_name or not safe_name[0].isalpha():
            safe_name = f"ch{ch_id}"

        mat_dict[f"{safe_name}_time_s"] = x_arr
        mat_dict[f"{safe_name}_raw"] = y_raw
        mat_dict[f"{safe_name}_scaled"] = y_scaled
        mat_dict[f"{safe_name}_unit"] = ch.get("unit", "")

    mat_dict["export_timestamp"] = datetime.now().strftime("%Y%m%d_%H%M%S")
    mat_dict["channel_count"] = len(req.channels)

    buf = io.BytesIO()
    savemat(buf, mat_dict, format='5', do_compression=True)
    buf.seek(0)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"capture_{ts}.mat"

    return StreamingResponse(
        buf,
        media_type="application/octet-stream",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
