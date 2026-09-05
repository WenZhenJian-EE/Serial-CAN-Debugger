# -*- coding: utf-8 -*-
"""
文件名: core/models/dsp_engine.py
数字信号处理引擎
支持：
- compute_fft: Hanning 加窗与幅值修正的 FFT 频谱分析
- calculate_thd: 高精度总谐波失真计算 (2~10次谐波)
- evaluate_math_expression: 虚拟数学通道表达式求解 (integrate, diff, rms, mean, 代数运算)
"""

import numpy as np
import re


def compute_fft(time_arr, data_arr):
    """计算频域 FFT 谱图，并返回频率轴与双边谱振幅轴（应用 Hanning 窗并作幅值修正）"""
    N = len(data_arr)
    if N < 32:
        return None, None

    data_detrended = data_arr - np.mean(data_arr)
    window = np.hanning(N)
    data_windowed = data_detrended * window

    t_span = time_arr[-1] - time_arr[0]
    fs = (N - 1) / t_span if t_span > 0 else 1000.0

    yf = np.fft.fft(data_windowed)
    xf = np.fft.fftfreq(N, 1 / fs)

    half_N = N // 2
    freqs = xf[:half_N]
    amplitudes = np.abs(yf[:half_N]) * 2 / np.sum(window)

    valid_idx = freqs >= 0
    return freqs[valid_idx].tolist(), amplitudes[valid_idx].tolist()


def calculate_thd(freqs, amplitudes):
    """高精度 THD (总谐波失真) 计算"""
    if len(amplitudes) < 10:
        return 0.0

    freqs = np.array(freqs)
    amplitudes = np.array(amplitudes)

    search_idx = np.where(freqs >= 5.0)[0]
    if len(search_idx) == 0:
        return 0.0

    start_idx = search_idx[0]
    peak_offset = np.argmax(amplitudes[start_idx:])
    peak_idx = start_idx + peak_offset

    fund_freq = freqs[peak_idx]

    left_bound = max(0, peak_idx - 2)
    right_bound = min(len(amplitudes) - 1, peak_idx + 2)
    fund_energy = np.sum(np.square(amplitudes[left_bound : right_bound + 1]))

    if fund_energy < 1e-10:
        return 0.0

    harm_energy = 0.0
    for h in range(2, 11):
        h_freq = h * fund_freq
        if h_freq > freqs[-1]:
            break
        h_idx = np.argmin(np.abs(freqs - h_freq))
        h_left = max(0, h_idx - 1)
        h_right = min(len(amplitudes) - 1, h_idx + 1)

        if h_left < right_bound:
            continue

        harm_energy += np.sum(np.square(amplitudes[h_left : h_right + 1]))

    thd = np.sqrt(harm_energy) / np.sqrt(fund_energy)
    return float(thd * 100)


def evaluate_math_expression(expression: str, channels_data: dict, dt: float = 0.0001):
    """解析并计算电力电子自定义数学通道波形。"""
    if not expression.strip():
        return None

    matches = re.findall(r"(?i)ch(\d+)", expression)
    if not matches:
        return None

    used_ids = sorted(list(set([int(m) for m in matches])))

    min_len = float("inf")
    for ch_id in used_ids:
        if ch_id not in channels_data or len(channels_data[ch_id]) < 2:
            return None
        min_len = min(min_len, len(channels_data[ch_id]))

    if min_len == float("inf") or min_len == 0:
        return None

    context = {}
    for ch_id in used_ids:
        context[f"ch{ch_id}"] = np.array(channels_data[ch_id][-min_len:])

    def integrate(y):
        return np.cumsum(y) * dt

    def diff(y):
        d = np.diff(y) / dt
        return np.insert(d, 0, d[0])

    def rms(y):
        r = np.sqrt(np.mean(np.square(y)))
        return np.full_like(y, r)

    def mean(y):
        return np.full_like(y, np.mean(y))

    context["integrate"] = integrate
    context["diff"] = diff
    context["rms"] = rms
    context["mean"] = mean
    context["np"] = np

    safe_expr = expression.lower()
    allowed_pattern = r"^[a-z0-9_ch\+\-\*\/\(\)\s\.\,]+$"
    if not re.match(allowed_pattern, safe_expr):
        print(f"[DSP] Expression contains unsafe characters: {expression}")
        return None

    try:
        result = eval(safe_expr, {"__builtins__": None}, context)
        if isinstance(result, np.ndarray):
            return result.tolist()
    except Exception as e:
        print(f"[DSP] Math evaluation error: {e}")
    return None
