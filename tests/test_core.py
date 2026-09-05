# -*- coding: utf-8 -*-
"""
Core and Server Integration Unit Tests
100% 验证核心算法守恒性与接口健壮性
"""

import numpy as np
import pytest
from fastapi.testclient import TestClient

from core.models.trigger_engine import TriggerEngine
from core.models import dsp_engine, bode_sweeper, loop_id_helper
from core.models.async_logger import AsyncLogger
from core.models.blackbox_recorder import BlackboxRecorder
from core.models import modbus_helper
from core.db.db_manager import init_database, get_db_connection
from server.api import app


def test_trigger_engine():
    engine = TriggerEngine()
    engine.configure(mode="Normal", source_id=1, level=100.0, edge="Rising")
    assert engine.is_armed is True
    assert engine.is_triggered is False
    assert engine.check_trigger(1, 90.0) is False
    assert engine.check_trigger(1, 105.0) is True
    assert engine.is_triggered is True

    engine.configure(mode="Single", source_id=1, level=-50.0, edge="Falling")
    assert engine.check_trigger(1, -40.0) is False
    assert engine.check_trigger(1, -60.0) is True


def test_dsp_calculations():
    fs = 1000.0
    N = 1000
    t = np.linspace(0, (N - 1) / fs, N)
    data = 100.0 * np.sin(2.0 * np.pi * 50.0 * t) + 10.0 * np.sin(2.0 * np.pi * 150.0 * t)

    freqs, amps = dsp_engine.compute_fft(t.tolist(), data.tolist())
    assert freqs is not None

    peak_idx_50 = np.argmin(np.abs(np.array(freqs) - 50.0))
    peak_idx_150 = np.argmin(np.abs(np.array(freqs) - 150.0))

    assert abs(amps[peak_idx_50] - 100.0) < 1.5
    assert abs(amps[peak_idx_150] - 10.0) < 1.5

    thd = dsp_engine.calculate_thd(freqs, amps)
    assert abs(thd - 10.0) < 1.5


def test_math_expressions():
    data1 = [1.0, 2.0, 3.0, 4.0, 5.0]
    data2 = [10.0, 20.0, 30.0, 40.0, 50.0]
    res = dsp_engine.evaluate_math_expression("ch1 + ch2", {1: data1, 2: data2})
    assert res == [11.0, 22.0, 33.0, 44.0, 55.0]

    res_mul = dsp_engine.evaluate_math_expression("ch1 * ch2", {1: data1, 2: data2})
    assert res_mul == [10.0, 40.0, 90.0, 160.0, 250.0]


def test_modbus_helpers():
    crc = modbus_helper.calculate_crc16(b"\x01\x03\x00\x00\x00\x0A")
    assert isinstance(crc, int)

    frame = modbus_helper.make_read_registers_frame(1, 3, 100, 2)
    assert len(frame) == 8
    assert frame[0] == 1
    assert frame[1] == 3


def test_system_identification():
    t = np.linspace(0, 5, 200)
    # Underdamped step response
    wn = 10.0
    zeta = 0.5
    wd = wn * np.sqrt(1 - zeta**2)
    phi = np.arctan(np.sqrt(1 - zeta**2) / zeta)
    y = 1.0 - (np.exp(-zeta * wn * t) / np.sqrt(1 - zeta**2)) * np.sin(wd * t + phi)

    res = loop_id_helper.identify_second_order_system(t.tolist(), y.tolist(), step_val=1.0)
    assert res["success"] is True
    assert "欠阻尼" in res["system_type"]
    assert abs(res["zeta"] - 0.5) < 0.15


def test_fastapi_endpoints():
    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"

    resp = client.get("/api/ports")
    assert resp.status_code == 200
    assert "ports" in resp.json()

    resp = client.get("/api/can/providers")
    assert resp.status_code == 200
    assert len(resp.json()["providers"]) >= 5

    resp = client.get("/api/connection/status")
    assert resp.status_code == 200
    assert "serial" in resp.json()
    assert "can" in resp.json()
