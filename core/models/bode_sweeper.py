# -*- coding: utf-8 -*-
"""
文件名: core/models/bode_sweeper.py
Bode 图扫频仪与单点 DFT 幅相求解器
支持：
- 单点 DFT 幅值与相位提取
- LLC 二阶闭环系统仿真频响
- 物理串口与 CAN 总线硬件扰动闭环扫频测试
"""

import time
import math
import struct
import queue
import numpy as np


def compute_single_bin_dft(t, x, freq):
    """对信号 x 在特定频率 freq 下进行单点 DFT 计算，获取其复数幅值与相位值"""
    t = np.array(t)
    x = np.array(x)

    x_detrended = x - np.mean(x)
    exp_basis = np.exp(-1j * 2.0 * np.pi * freq * t)
    complex_val = np.sum(x_detrended * exp_basis) / len(t)
    return complex_val


def sweep_point(
    freq: float,
    amplitude: float,
    active_workers: dict,
    active_workers_lock,
    data_queue: queue.Queue,
) -> tuple:
    """对单个频点进行物理扫频测量或仿真。返回: (gain_db, phase_deg)"""
    has_hardware = False
    worker_type = None
    worker = None

    with active_workers_lock:
        if active_workers.get("serial"):
            has_hardware = True
            worker_type = "serial"
            worker = active_workers["serial"]
        elif active_workers.get("can"):
            has_hardware = True
            worker_type = "can"
            worker = active_workers["can"]

    if not has_hardware:
        fn = 20000.0
        zeta = 0.35
        ratio = freq / fn

        magnitude = 1.0 / math.sqrt(
            math.pow(1.0 - ratio * ratio, 2) + math.pow(2.0 * zeta * ratio, 2)
        )
        if 1.0 - ratio * ratio == 0:
            phase_rad = -math.pi / 2
        else:
            phase_rad = -math.atan2(2.0 * zeta * ratio, 1.0 - ratio * ratio)

        noise_gain = np.random.normal(0, 0.1)
        noise_phase = np.random.normal(0, 0.5)

        gain_db = 20.0 * math.log10(magnitude) + noise_gain
        phase_deg = math.degrees(phase_rad) + noise_phase

        if phase_deg < -180.0:
            phase_deg += 360.0
        elif phase_deg > 180.0:
            phase_deg -= 360.0

        time.sleep(0.05)
        return gain_db, phase_deg

    if worker_type == "serial":
        freq_bytes = struct.pack("<f", float(freq))
        freq_payload = bytearray([0xF0, 0x00]) + freq_bytes
        csum_freq = sum(freq_payload) & 0xFF
        frame_freq = b"S" + freq_payload + bytes([csum_freq]) + b"E"

        amp_bytes = struct.pack("<f", float(amplitude))
        amp_payload = bytearray([0xF1, 0x00]) + amp_bytes
        csum_amp = sum(amp_payload) & 0xFF
        frame_amp = b"S" + amp_payload + bytes([csum_amp]) + b"E"

        worker.write_data(frame_freq)
        time.sleep(0.01)
        worker.write_data(frame_amp)

    elif worker_type == "can":
        payload = struct.pack("<ff", float(freq), float(amplitude))
        worker.write_data_frame(0x1F0, payload, is_extended=False)

    settle_time = max(0.05, 8.0 / freq)
    time.sleep(settle_time)

    while not data_queue.empty():
        try:
            data_queue.get_nowait()
        except queue.Empty:
            break

    record_duration = max(0.1, min(2.0, 10.0 / freq))
    t_start = time.time()
    raw_points = []

    while time.time() - t_start < record_duration:
        try:
            item = data_queue.get(timeout=0.01)
            raw_points.append(item)
        except queue.Empty:
            pass

    t_u, u_vals = [], []
    t_y, y_vals = [], []

    for t_pt, pkt_id, val in raw_points:
        if pkt_id == 1:
            t_u.append(t_pt)
            u_vals.append(val)
        elif pkt_id == 2:
            t_y.append(t_pt)
            y_vals.append(val)

    if len(u_vals) < 10 or len(y_vals) < 10:
        return -100.0, 0.0

    u_complex = compute_single_bin_dft(t_u, u_vals, freq)
    y_complex = compute_single_bin_dft(t_y, y_vals, freq)

    if abs(u_complex) < 1e-8:
        return -100.0, 0.0

    transfer_val = y_complex / u_complex
    gain_db = 20.0 * math.log10(abs(transfer_val))
    phase_deg = math.degrees(math.atan2(transfer_val.imag, transfer_val.real))

    if phase_deg < -180.0:
        phase_deg += 360.0
    elif phase_deg > 180.0:
        phase_deg -= 360.0

    return gain_db, phase_deg
