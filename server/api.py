# -*- coding: utf-8 -*-
"""
文件名: server/api.py
FastAPI 实例创建、CORS 配置、静态资源挂载与高速 WebSocket 推流总线
"""

import asyncio
import collections
import os
import queue
import re
import struct
import threading
import time
from contextlib import asynccontextmanager
from typing import Optional

import cantools
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

import server.state as state
from core.db.db_manager import init_database
from core.models import dsp_engine
from server.routes import connection, send, analysis, trigger, logging as logging_router, config as config_router

PACK_FMT = "<dHf"
POINT_SIZE = struct.calcsize(PACK_FMT)

# 触发录波状态机缓存
triggered_log_cache = {}
triggered_log_total = 0
triggered_log_timer = 0.0
triggered_log_lock = threading.Lock()


async def can_periodic_send_loop():
    print("[Server] CAN periodic send loop background task started.")
    while True:
        running = state.can_periodic_config["running"]
        interval = state.can_periodic_config["interval"]
        arb_id = state.can_periodic_config["arbitration_id"]
        data_bytes = state.can_periodic_config["data"]
        is_extended = state.can_periodic_config["is_extended"]

        try:
            if running:
                worker = None
                with state.active_workers_lock:
                    w = state.active_workers.get("can")
                    if w and w.is_connected:
                        worker = w

                if worker:
                    worker.write_data_frame(
                        arbitration_id=arb_id,
                        data=data_bytes,
                        is_extended=is_extended,
                    )
        except Exception as e:
            print(f"[Server] CAN periodic send error: {e}")
        await asyncio.sleep(interval)


def stop_all_workers():
    with state.active_workers_lock:
        for name, worker in list(state.active_workers.items()):
            if worker:
                try:
                    worker.stop()
                except Exception:
                    pass
                state.active_workers[name] = None
    print("[Server] All communication workers stopped.")


async def queue_drainer():
    print("[Server] Queue drainer background task started.")
    while True:
        try:
            if not state.is_streaming:
                while not state.data_queue.empty():
                    try:
                        state.data_queue.get_nowait()
                    except queue.Empty:
                        break
        except Exception as e:
            print(f"[Server] Queue drainer error: {e}")
        await asyncio.sleep(0.1)


def process_math_channel(local_buffers, local_timestamps):
    math_buffer = bytearray()
    if state.math_expressions:
        for math_id, expr in state.math_expressions.items():
            if not expr:
                continue
            try:
                matches = re.findall(r'(?i)ch(\d+)', expr)
                if not matches:
                    continue
                used_ids = sorted(list(set([int(m) for m in matches])))
                first_ch_id = used_ids[0]

                min_len = float('inf')
                for ch_id in used_ids:
                    if ch_id not in local_buffers or len(local_buffers[ch_id]) < 2:
                        min_len = 0
                        break
                    min_len = min(min_len, len(local_buffers[ch_id]))

                if min_len == 0 or min_len == float('inf'):
                    continue

                channels_data = {}
                for ch_id in used_ids:
                    channels_data[ch_id] = list(local_buffers[ch_id])[-min_len:]

                math_time = list(local_timestamps[first_ch_id])[-min_len:]
                dt = 0.0001
                if len(math_time) >= 2:
                    t_span = math_time[-1] - math_time[0]
                    dt = t_span / (len(math_time) - 1)
                    if dt <= 0:
                        dt = 0.0001

                res = dsp_engine.evaluate_math_expression(expr, channels_data, dt)
                if not res:
                    continue

                last_t = state.last_math_ts.get(math_id, 0.0)
                for idx in range(min_len):
                    t_pt = math_time[idx]
                    if t_pt > last_t:
                        val_pt = res[idx]
                        math_buffer.extend(struct.pack(PACK_FMT, t_pt, int(math_id), val_pt))
                        last_t = t_pt
                state.last_math_ts[math_id] = last_t
            except Exception as e:
                print(f"[Server] Math channel {math_id} evaluation error: {e}")

    return math_buffer


async def save_and_notify_triggered_log(websocket: WebSocket):
    global triggered_log_cache, triggered_log_total
    try:
        channels_pts = {}
        all_t_offsets = set()

        sorted_indices = sorted(list(triggered_log_cache.keys()))
        for idx in sorted_indices:
            ch_id, t_offset, val = triggered_log_cache[idx]
            if ch_id not in channels_pts:
                channels_pts[ch_id] = {}
            channels_pts[ch_id][t_offset] = val
            all_t_offsets.add(t_offset)

        if not all_t_offsets:
            return

        sorted_t = sorted(list(all_t_offsets))
        ch_ids = sorted(list(channels_pts.keys()))

        import csv
        log_dir = "fault_logs"
        os.makedirs(log_dir, exist_ok=True)
        filename = f"triggered_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        filepath = os.path.abspath(os.path.join(log_dir, filename))

        headers = ["Timestamp"] + [f"CH{cid}" for cid in ch_ids]
        last_vals = {cid: 0.0 for cid in ch_ids}

        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            for t in sorted_t:
                row = [f"{t:.6f}"]
                for cid in ch_ids:
                    if t in channels_pts[cid]:
                        val = channels_pts[cid][t]
                        last_vals[cid] = val
                    else:
                        val = last_vals[cid]
                    row.append(f"{val:.6f}")
                writer.writerow(row)

        print(f"[TriggeredLog] Reconstructed CSV saved to: {filepath}")
        await websocket.send_text(f"TRIGGERED_BUFFER_READY:{filepath}")
    except Exception as e:
        print(f"[TriggeredLog] Failed to save CSV and notify: {e}")
    finally:
        triggered_log_cache.clear()
        triggered_log_total = 0


async def process_triggered_log_packet(packet_idx: int, total_packets: int, channel_id: int, t_offset: float, val_val: float, websocket: WebSocket):
    global triggered_log_cache, triggered_log_total, triggered_log_timer

    with triggered_log_lock:
        if triggered_log_total != total_packets or time.time() - triggered_log_timer > 5.0:
            triggered_log_cache.clear()
            triggered_log_total = total_packets
            print(f"[TriggeredLog] Start receiving triggered buffer. Total = {total_packets}")

        triggered_log_timer = time.time()
        triggered_log_cache[packet_idx] = (channel_id, t_offset, val_val)

        if len(triggered_log_cache) >= triggered_log_total:
            asyncio.create_task(save_and_notify_triggered_log(websocket))


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_database()
    drainer_task = asyncio.create_task(queue_drainer())
    periodic_task = asyncio.create_task(can_periodic_send_loop())

    # 自动恢复 DBC
    dbc_path = os.path.join(os.path.dirname(__file__), "uploaded.dbc")
    if os.path.exists(dbc_path):
        try:
            state.pending_dbc = cantools.database.load_file(dbc_path)
            print(f"[Server] Automatically restored DBC from: {dbc_path}")
        except Exception as e:
            print(f"[Server] Failed to restore DBC on startup: {e}")

    yield

    # Shutdown
    drainer_task.cancel()
    periodic_task.cancel()
    stop_all_workers()


def create_app() -> FastAPI:
    app = FastAPI(title="Serial-CAN-Debugger Backend", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(connection.router)
    app.include_router(send.router)
    app.include_router(analysis.router)
    app.include_router(trigger.router)
    app.include_router(logging_router.router)
    app.include_router(config_router.router)

    @app.get("/health")
    def health_check():
        return {"status": "healthy", "architecture": "FastAPI + WebSocket + WebView2", "timestamp": time.time()}

    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        await websocket.accept()
        state.is_streaming = True
        print("[WebSocket] Client connected, streaming started.")

        local_buffers = {}
        local_timestamps = {}

        try:
            while True:
                buffer = bytearray()
                limit = 5000
                count = 0
                single_triggered = False

                while count < limit:
                    try:
                        item = state.data_queue.get_nowait()
                        if len(item) == 3 and item[1] == "triggered_log":
                            t_rec, tag, payload = item
                            packet_idx, total_packets, channel_id, t_offset, val_val = payload
                            await process_triggered_log_packet(packet_idx, total_packets, channel_id, t_offset, val_val, websocket)
                            state.data_queue.task_done()
                            continue

                        t_abs, pkt_id, val = item

                        if pkt_id not in local_buffers:
                            local_buffers[pkt_id] = collections.deque(maxlen=1000)
                            local_timestamps[pkt_id] = collections.deque(maxlen=1000)
                        local_buffers[pkt_id].append(val)
                        local_timestamps[pkt_id].append(t_abs)

                        # 1. 异步日志记录
                        state.logger_instance.log_data(t_abs, pkt_id, val)

                        # 2. 黑匣子故障录波监测
                        blackbox_path = state.blackbox_instance.feed(t_abs, pkt_id, val)
                        if blackbox_path:
                            await websocket.send_text(f"FAULT_TRIGGERED:{blackbox_path}")

                        # 3. 触发状态机判定
                        if state.trigger_engine.is_armed and not state.trigger_engine.is_triggered:
                            if state.trigger_engine.check_trigger(pkt_id, val):
                                if state.trigger_engine.mode == "Single":
                                    single_triggered = True
                                    state.trigger_engine.is_armed = False

                        buffer.extend(struct.pack(PACK_FMT, t_abs, pkt_id, val))
                        state.data_queue.task_done()
                        count += 1
                    except queue.Empty:
                        break

                math_buf = process_math_channel(local_buffers, local_timestamps)
                if len(math_buf) > 0:
                    buffer.extend(math_buf)

                if len(buffer) > 0:
                    await websocket.send_bytes(buffer)

                # 提取原始数据并分发
                raw_lines = []
                while not state.raw_data_queue.empty():
                    try:
                        src, item = state.raw_data_queue.get_nowait()
                        if src == "serial":
                            raw_lines.append(f"RAW_SERIAL:{item.hex()}")
                        elif src == "can":
                            if len(item) >= 5:
                                t_now, arb_id, msg_data, is_ext, frame_type = item[0], item[1], item[2], item[3], item[4]
                            else:
                                t_now, arb_id, msg_data, is_ext = item
                                frame_type = "STD"
                            raw_lines.append(f"RAW_CAN:{frame_type},{t_now:.3f},{arb_id},{msg_data.hex()},{1 if is_ext else 0}")
                        elif src == "tcp":
                            raw_lines.append(f"RAW_TCP:{item.hex()}")
                    except queue.Empty:
                        break
                if raw_lines:
                    await websocket.send_text("RAW_DATA_BATCH:" + "\n".join(raw_lines))

                if single_triggered:
                    await asyncio.sleep(0.1)
                    extra_buf = bytearray()
                    while not state.data_queue.empty():
                        try:
                            item = state.data_queue.get_nowait()
                            if len(item) == 3 and item[1] == "triggered_log":
                                state.data_queue.task_done()
                                continue
                            t_abs, pkt_id, val = item
                            extra_buf.extend(struct.pack(PACK_FMT, t_abs, pkt_id, val))
                            state.data_queue.task_done()
                        except queue.Empty:
                            break
                    if extra_buf:
                        await websocket.send_bytes(extra_buf)
                    await websocket.send_text("TRIGGER_FIRED:Single")
                    print("[WebSocket] Single trigger fired. Waveform frozen.")

                await asyncio.sleep(0.016)

        except (WebSocketDisconnect, asyncio.CancelledError):
            print("[WebSocket] Client disconnected.")
        finally:
            state.is_streaming = False

    # 挂载前端静态页面 (兼容源码与 PyInstaller 打包单文件环境)
    import sys
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        webui_dist = os.path.join(sys._MEIPASS, "webui", "dist")
    else:
        webui_dist = os.path.join(os.path.dirname(os.path.dirname(__file__)), "webui", "dist")

    if os.path.exists(webui_dist):
        app.mount("/", StaticFiles(directory=webui_dist, html=True), name="webui")

    return app


app = create_app()
