# -*- coding: utf-8 -*-
"""
文件名: core/models/loop_id_helper.py
基于时域阶跃响应数据，在线辨识二阶系统传递函数及关键参数
"""

import numpy as np


def identify_second_order_system(
    t_arr: list, y_arr: list, step_val: float = 1.0
) -> dict:
    """基于时域阶跃响应数据，在线辨识二阶系统传递函数及关键参数。"""
    t = np.array(t_arr)
    y = np.array(y_arr)

    if len(t) < 10 or len(y) < 10:
        return {"success": False, "message": "数据点数过少 (至少10点)"}

    y_init = y[0]
    tail_len = max(1, len(y) // 10)
    y_ss = np.mean(y[-tail_len:])

    delta_y = y_ss - y_init
    if abs(delta_y) < 1e-6:
        return {"success": False, "message": "响应无明显阶跃变化"}

    K = delta_y / step_val

    if delta_y > 0:
        peak_idx = np.argmax(y)
        y_max = y[peak_idx]
        t_peak = t[peak_idx]
        overshoot = y_max - y_ss
    else:
        peak_idx = np.argmin(y)
        y_max = y[peak_idx]
        t_peak = t[peak_idx]
        overshoot = y_ss - y_max

    t_start = t[0]
    tp = t_peak - t_start

    overshoot_pct = (overshoot / abs(delta_y)) * 100.0

    if overshoot_pct > 0.5 and tp > 1e-6:
        sigma = overshoot_pct / 100.0
        ln_sig = np.log(sigma)
        zeta = -ln_sig / np.sqrt(np.pi**2 + ln_sig**2)

        wd = np.pi / tp
        wn = wd / np.sqrt(1.0 - zeta**2)
        system_type = "欠阻尼 (Underdamped)"
    else:
        target_63 = y_init + 0.632 * delta_y
        idx_63 = np.where(np.abs(y - target_63) == np.min(np.abs(y - target_63)))[0][0]
        T = t[idx_63] - t_start
        if T <= 0:
            T = 0.001
        wn = 1.0 / T
        zeta = 1.0
        overshoot_pct = 0.0
        tp = 0.0
        system_type = "过阻尼/临界阻尼 (Overdamped)"

    error_band = 0.02 * abs(delta_y)
    ts = 0.0
    for i in range(len(y) - 1, -1, -1):
        if abs(y[i] - y_ss) > error_band:
            ts = t[i] - t_start
            break
    if ts == 0.0:
        ts = t[-1] - t_start

    den_a = 2.0 * zeta * wn
    den_b = wn**2
    num_val = K * wn**2

    return {
        "success": True,
        "system_type": system_type,
        "zeta": float(zeta),
        "wn": float(wn),
        "fn": float(wn / (2.0 * np.pi)),
        "overshoot_pct": float(overshoot_pct),
        "tp": float(tp),
        "ts": float(ts),
        "K": float(K),
        "tf_str": f"{num_val:.4g} / (s^2 + {den_a:.4g}s + {den_b:.4g})",
    }
