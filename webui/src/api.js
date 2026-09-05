// ==========================================================================
// api.js - 本地回环 REST / WebSocket 通信封装与二进制解包
// ==========================================================================

const isDev = window.location.port === '5173';
export const API_BASE = isDev ? 'http://127.0.0.1:8000' : window.location.origin;
export const WS_BASE = isDev ? 'ws://127.0.0.1:8000/ws' : `ws://${window.location.host}/ws`;

// ─── 通用 HTTP 请求封装 ────────────────────────────────────────────────────────

async function request(path, options = {}) {
  const url = `${API_BASE}${path}`;
  const res = await fetch(url, {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  });
  if (!res.ok) {
    let errDetail = res.statusText;
    try {
      const data = await res.json();
      errDetail = data.detail || data.message || errDetail;
    } catch (_) {}
    throw new Error(errDetail);
  }
  return res.json();
}

// ─── 硬件连接接口 ────────────────────────────────────────────────────────────

export const api = {
  // 串口
  getPorts: () => request('/api/ports'),
  autoProbe: () => request('/api/auto_probe', { method: 'POST' }),
  connectSerial: (data) => request('/api/serial/connect', { method: 'POST', body: JSON.stringify(data) }),
  disconnectSerial: () => request('/api/serial/disconnect', { method: 'POST' }),

  // CAN 总线
  getCanProviders: () => request('/api/can/providers'),
  connectCan: (data) => request('/api/can/connect', { method: 'POST', body: JSON.stringify(data) }),
  disconnectCan: () => request('/api/can/disconnect', { method: 'POST' }),
  uploadDbc: async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`${API_BASE}/api/can/load_dbc`, { method: 'POST', body: formData });
    return res.json();
  },

  // TCP
  connectTcp: (data) => request('/api/tcp/connect', { method: 'POST', body: JSON.stringify(data) }),
  disconnectTcp: () => request('/api/tcp/disconnect', { method: 'POST' }),
  getConnectionStatus: () => request('/api/connection/status'),

  // 发送指令
  sendSerialRaw: (data, is_hex) => request('/api/serial/send_raw', { method: 'POST', body: JSON.stringify({ data, is_hex }) }),
  sendSerialProtocol: (id, value) => request('/api/serial/send_protocol', { method: 'POST', body: JSON.stringify({ id, value }) }),
  sendCanRaw: (arbitration_id, data_hex, is_hex, is_extended = false) =>
    request('/api/can/send_raw', { method: 'POST', body: JSON.stringify({ arbitration_id, data_hex, is_hex, is_extended }) }),
  sendCanProtocol: (arbitration_id, value) => request('/api/can/send_protocol', { method: 'POST', body: JSON.stringify({ arbitration_id, value }) }),
  startCanPeriodic: (data) => request('/api/can/periodic/start', { method: 'POST', body: JSON.stringify(data) }),
  stopCanPeriodic: () => request('/api/can/periodic/stop', { method: 'POST' }),

  // 示波器触发
  configureTrigger: (data) => request('/api/trigger/configure', { method: 'POST', body: JSON.stringify(data) }),
  resetTrigger: () => request('/api/trigger/reset', { method: 'POST' }),
  getTriggerStatus: () => request('/api/trigger/status'),

  // 日志与黑匣子
  startLogging: (filename_prefix) => request('/api/logger/start', { method: 'POST', body: JSON.stringify({ filename_prefix }) }),
  stopLogging: () => request('/api/logger/stop', { method: 'POST' }),
  configureBlackbox: (data) => request('/api/blackbox/configure', { method: 'POST', body: JSON.stringify(data) }),
  getFaultLogs: () => request('/api/fault_logs/list'),

  // DSP 与 Bode 扫频
  computeFft: (time_arr, data_arr) => request('/api/dsp/fft', { method: 'POST', body: JSON.stringify({ time_arr, data_arr }) }),
  runBodeSweep: (data) => request('/api/bode/sweep', { method: 'POST', body: JSON.stringify(data) }),
  saveBodeHistory: (data) => request('/api/bode/history/save', { method: 'POST', body: JSON.stringify(data) }),
  listBodeHistory: () => request('/api/bode/history/list'),
  deleteBodeHistory: (filename) => request(`/api/bode/history/delete?filename=${encodeURIComponent(filename)}`, { method: 'POST' }),
  identifySystem: (t_arr, y_arr, step_val = 1.0) => request('/api/identify_system', { method: 'POST', body: JSON.stringify({ t_arr, y_arr, step_val }) }),
  analyzeStepResponse: (t_arr, y_arr, settle_band = 2.0) => request('/api/analyze/step_response', { method: 'POST', body: JSON.stringify({ t_arr, y_arr, settle_band }) }),

  // SQLite 元器件库
  listComponents: (category) => request(`/api/components/list${category ? `?category=${encodeURIComponent(category)}` : ''}`),
  addComponent: (data) => request('/api/components/add', { method: 'POST', body: JSON.stringify(data) }),
  deleteComponent: (id) => request(`/api/components/${id}`, { method: 'DELETE' }),

  // 配置存储
  getConfig: (key) => request(`/api/config/${key}`),
  setConfig: (key, value) => request(`/api/config/${key}`, { method: 'POST', body: JSON.stringify({ key, value }) }),
};

// ─── WebSocket 全双工流引擎与二进制解包器 ──────────────────────────────────────

export class WebSocketStreamer {
  constructor() {
    this.ws = null;
    this.reconnectTimer = null;
    this.statsTimer = null;
    this.byteCounter = 0;
    this.packetCounter = 0;
    this.telemetry = { kbps: 0, pps: 0 };
    this.callbacks = {
      onPoint: () => {},
      onPointsBatch: null,
      onRawBatch: () => {},
      onTriggerFired: () => {},
      onFaultTriggered: () => {},
      onTriggeredReady: () => {},
      onStatusChange: () => {},
      onTelemetry: () => {},
    };
  }

  on(event, cb) {
    if (this.callbacks[event] !== undefined) {
      this.callbacks[event] = cb;
    }
  }

  startStatsTimer() {
    if (this.statsTimer) clearInterval(this.statsTimer);
    this.statsTimer = setInterval(() => {
      const kbps = (this.byteCounter / 1024).toFixed(1);
      const pps = this.packetCounter;
      this.telemetry = { kbps: parseFloat(kbps), pps };
      this.callbacks.onTelemetry(this.telemetry);
      this.byteCounter = 0;
      this.packetCounter = 0;
    }, 1000);
  }

  stopStatsTimer() {
    if (this.statsTimer) {
      clearInterval(this.statsTimer);
      this.statsTimer = null;
    }
    this.telemetry = { kbps: 0, pps: 0 };
    this.callbacks.onTelemetry(this.telemetry);
  }

  connect() {
    if (this.ws && (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)) {
      return;
    }

    try {
      this.ws = new WebSocket(WS_BASE);
      this.ws.binaryType = 'arraybuffer';

      this.ws.onopen = () => {
        this.callbacks.onStatusChange(true);
        this.startStatsTimer();
      };

      this.ws.onclose = () => {
        this.callbacks.onStatusChange(false);
        this.stopStatsTimer();
        this.scheduleReconnect();
      };

      this.ws.onerror = () => {
        this.callbacks.onStatusChange(false);
        this.stopStatsTimer();
      };

      this.ws.onmessage = (evt) => {
        if (evt.data instanceof ArrayBuffer) {
          this.byteCounter += evt.data.byteLength;
          // 二进制数据点分发 (<dHf: Little-Endian 8B double + 2B uint16 + 4B float = 14B)
          const POINT_SIZE = 14;
          const dv = new DataView(evt.data);
          const totalPoints = Math.floor(evt.data.byteLength / POINT_SIZE);
          this.packetCounter += totalPoints;

          if (this.callbacks.onPointsBatch) {
            this.callbacks.onPointsBatch(dv, totalPoints);
          } else {
            for (let i = 0; i < totalPoints; i++) {
              const offset = i * POINT_SIZE;
              const t = dv.getFloat64(offset, true);
              const chId = dv.getUint16(offset + 8, true);
              const val = dv.getFloat32(offset + 10, true);
              this.callbacks.onPoint(t, chId, val);
            }
          }
        } else if (typeof evt.data === 'string') {
          this.byteCounter += evt.data.length;
          this.packetCounter += 1;
          // 文本消息协议处理
          const msg = evt.data;
          if (msg.startsWith('RAW_DATA_BATCH:')) {
            const lines = msg.substring(15).split('\n');
            this.callbacks.onRawBatch(lines);
          } else if (msg.startsWith('TRIGGER_FIRED:')) {
            this.callbacks.onTriggerFired(msg.substring(14));
          } else if (msg.startsWith('FAULT_TRIGGERED:')) {
            this.callbacks.onFaultTriggered(msg.substring(16));
          } else if (msg.startsWith('TRIGGERED_BUFFER_READY:')) {
            this.callbacks.onTriggeredReady(msg.substring(23));
          }
        }
      };
    } catch (e) {
      this.scheduleReconnect();
    }
  }

  scheduleReconnect() {
    if (this.reconnectTimer) return;
    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null;
      this.connect();
    }, 2000);
  }

  disconnect() {
    this.stopStatsTimer();
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}

// ─── Desktop 原生桥接能力 ────────────────────────────────────────────────────

export const desktopBridge = {
  isAvailable: () => typeof window !== 'undefined' && !!window.pywebview,
  chooseFile: async (title, fileTypes) => {
    if (window.pywebview && window.pywebview.api) {
      return await window.pywebview.api.choose_file(title, fileTypes);
    }
    return null;
  },
  saveFile: async (title, defaultName, fileTypes) => {
    if (window.pywebview && window.pywebview.api) {
      return await window.pywebview.api.save_file(title, defaultName, fileTypes);
    }
    return null;
  },
  chooseFolder: async (title) => {
    if (window.pywebview && window.pywebview.api) {
      return await window.pywebview.api.choose_folder(title);
    }
    return null;
  },
  getSystemInfo: async () => {
    if (window.pywebview && window.pywebview.api) {
      return await window.pywebview.api.get_system_info();
    }
    return { app_name: 'Serial-CAN-Debugger', version: '3.0.0 (Web Mode)' };
  },
};
