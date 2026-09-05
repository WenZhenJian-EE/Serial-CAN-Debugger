# Serial & CAN Bus Host Debugging Tool (Serial-CAN-Debugger V3.0)

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Vite](https://img.shields.io/badge/Vite-6.4-blueviolet.svg)](https://vite.dev/)
[![Vue](https://img.shields.io/badge/Vue-3.5-brightgreen.svg)](https://vuejs.org/)
[![WebView2](https://img.shields.io/badge/pywebview-6.2-teal.svg)](https://pywebview.flowrl.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<div align="center">
  <img src="./app_icon.png" width="128" height="128" alt="Serial-CAN-Debugger Cat Icon" />
  <p><strong>Serial-CAN-Debugger · 支持串口、CAN 与实时示波器调试的工业级上位机</strong></p>
  <p><em>Industrial Host Computer Debugger for Serial, CAN/CAN-FD & Real-Time Oscilloscope</em></p>
</div>

---

## 📖 English Summary (For Global Developers & Engineers)

**Serial-CAN-Debugger V3.0** is an open-source, industrial-grade desktop debugging workbench for high-speed **Serial (UART)** and **CAN / CAN-FD** bus systems. Rebuilt from the ground up using a **modern decoupled desktop architecture** (FastAPI + WebSocket + Vue 3 + Microsoft Edge WebView2), it completely eliminates the memory overhead and lag of legacy Electron and PyQt frameworks:

* 🚀 **Fluid 60~120 FPS High-Refresh Waveform Display**: 100,000-point circular ring buffer, real-time LTTB downsampling, time-base rolling mode (0.5s / 2.0s / Full History), dual measurement cursors (Cursor A & B, $\Delta T$, $1/\Delta T$, $\Delta V$), and FFT frequency spectrum analysis.
* ⚡ **Hardware-Level Edge Trigger System**: Embedded into the left sidebar for instant access. Supports Auto, Normal, Single triggering modes, edge polarity (Rising / Falling), threshold voltages, holdoff samples, and a 10-second panoramic blackbox fault recorder.
* 🎛️ **Custom Debugging Control Matrix (Buttons & Sliders)**: Docked at the bottom of the sidebar. Supports click-to-dispatch buttons and smooth tuning sliders with hardware-level step steppers (`[-]` / `[+]`), throttled transmission (80ms), and custom command formatting (e.g. `P={val}\r\n`).
* 📡 **High-Throughput Virtual Monitor**: Virtual scrolling table supporting 100,000+ bus frames without DOM lag or memory leakage, featuring realtime Hex/ASCII decoding, filtering, and CSV export.
* 🌐 **Automatic Environment Locale Detection & 1-Click i18n**: Automatically boots in **English (`en-US`)** on international operating systems and in **Chinese (`zh-CN`)** on Chinese environments, with 0 external web fonts for instant startup.
* 📦 **Zero-Clutter Portable Single EXE**: Packaged as a clean, standalone 69 MB executable with embedded multi-resolution cat icon. No external dependencies or Python installation required.

---

## 🌟 核心架构代际优势 (现代桌面架构对标)

| 核心维度 | 传统上位机 (PyQt5 / Electron) | 现代极速架构 (Serial-CAN-Debugger V3.0) |
| :--- | :--- | :--- |
| **容器运行时** | 自打包庞大 Chromium + Node.js (180MB+) | **Windows Edge WebView2** 原生常青内核 (GPU 硬件加速，零多余外壳) |
| **单文件打包体积** | 170MB ~ 250MB 臃肿体积 | **便携单文件 EXE**，秒级极速解压与冷启 |
| **编译构建管道** | 仅支持外部运行时打包 | **双编译器管道**: PyInstaller 单文件 + **Nuitka C++ 原生机器码转译** |
| **示波渲染性能** | 几千点易卡顿掉帧，甚至假死未响应 | **自适应 60~120 FPS 高刷** + 十万点深度环形缓冲 (LTTB 降采样) |
| **双标尺测量系统** | 无或仅有简陋标尺 | **双测量光标 (Cursor A & B)** 即时解算时间差 $\Delta T$、频率 $1/\Delta T$ 与电压差 $\Delta V$ |
| **硬件触发器布局** | 隐藏于深层二级菜单 | **常驻左侧边栏中央**：支持 Auto / Normal / Single，上升沿/下降沿与阈值电平精确捕获 |
| **自定义控制矩阵** | 仅支持固定文本发送框 | **常驻左侧边栏底部**：支持**按钮 (Button)** 与 **滑块 (Slider)** 双形态，80ms 防抖节流 |
| **高频报文监视器** | 全量 DOM 渲染导致浏览器崩溃 | **虚拟滚动 (Virtual Scroll)** 锁定仅渲染可见区 DOM，十万级报文丝滑流畅 |
| **国际化与多语言** | 界面语言写死，国外工程师无法阅读 | **智能识别系统语言**（英文系统自动默认 English），支持一键无刷新双语即切 |
| **字体渲染架构** | 内嵌动辄几十兆的外部字体文件 | **零内嵌原生系统字体栈 (Zero-Embedded Fonts)**，100% 依托宿主亚像素抗锯齿引擎 |
| **核心算法资产** | 算法与 UI 混杂，难以单元测试 | **Core 算力领域核物理隔离**，100% 纯 Python 原生无 GUI 依赖，通过 pytest 持续验证 |

---

## 👨‍💻 开源作者与技术支持 (Author & Open Source)

*   **项目作者**: **温振键 (WenZhenJian-EE)**
*   **GitHub 主页**: [https://github.com/WenZhenJian-EE](https://github.com/WenZhenJian-EE)
*   **开源代码仓库**: [https://github.com/WenZhenJian-EE/Serial-CAN-Debugger](https://github.com/WenZhenJian-EE/Serial-CAN-Debugger)
*   **技术博客 / 个人主页**: [https://WenZhenJian-EE.github.io](https://WenZhenJian-EE.github.io)
*   **开源协议**: [MIT License](LICENSE) (自由商用、个人研发与深度定制)

---

## 🎛️ 界面人机工学双层布局

```text
┌──────────────────────────────────────────────────────────────┐
│ [Brand Logo] Serial-CAN-Debugger V3.0    [实时示波 1] [报文监视 2] [Bode 扫频 3]  [KB/s|pps] [中/EN] [Github] │
├──────────────────────────────┬───────────────────────────────┤
│ 左侧控制面板 (宽度 350px)    │ 右侧主视图投影面 (Main View)   │
│                              │                               │
│ [串口总线 (UART)] [CAN/FD]   │ 📈 实时示波主视图 (Waveform)  │
│ 端口: COM3  波特率: 115200   │  - 0.5s / 2.0s 滚动时基选择    │
│ [ 打开串口 ]                 │  - 双测量光标 Cursor A/B HUD   │
│                              │  - 样条插值曲线平滑 (Spline)  │
│ ⚡ 硬件边沿触发器 (Trigger)  │  - 运行/暂停冻结 / 清空数据    │
│ 模式: [Auto] [Normal] [Single]│                              │
│ 通道: CH1  极性: [上升沿]    │ 📋 高频虚拟监视器 (Monitor)   │
│ 阈值电平: 50.0V (滑动微调)   │  - 十万帧虚拟滚动报文列表     │
│ [ 应用触发 (ARM) ] [ 复位 ]  │  - 实时 HEX / ASCII 解码与过滤 │
│                              │                               │
│ 🎛️ 自定义控制矩阵 (Controls) │ 📊 Bode 扫频仪 (Bode Sweeper) │
│ [P+  ASC ⚙]  [P-  ASC ⚙]    │  - 幅频特性曲线 (dB)          │
│ [速度调节: 45.0  [-]══●══[+] ]│  - 相频特性曲线 (deg)         │
│ [+ 添加自定义按钮 / 滑块]    │                               │
└──────────────────────────────┴───────────────────────────────┘
```

---

## 📂 工程拓扑规范 (三权分立元架构)

```text
Serial-CAN-Debugger/
├── main.py                  # 统一调度总入口：desktop (默认GUI) / serve (调试) / cli (无头自动化) 三模态
├── desktop/                 # 桌面容器宿主层 (pywebview 原生窗口拉起、动态端口监听、DesktopApi JS Bridge)
│   └── window.py
├── server/                  # 业务中枢与本地接口层 (FastAPI 实例创建、CORS 配置与静态资源挂载)
│   ├── api.py               # WebSocket /ws 14B 二进制推流总线 (<dHf)
│   ├── state.py             # 内存级共享状态与单例管理
│   └── routes/              # 业务路由 (connection, send, analysis, trigger, logging, config)
├── core/                    # 纯粹算法与硬件通信引擎 (100% 语言原生 Python，绝对零 GUI 依赖)
│   ├── parsers/             # 串口/CAN/Modbus/TCP 通信 Worker 与 cantools DBC 解析
│   ├── models/              # DSP 引擎 (FFT/THD), Bode 扫频, 硬件触发器, 异步日志, 故障黑匣子
│   └── db/                  # SQLite 嵌入式数据库 (元器件规格库 CRUD)
├── webui/                   # 纯净现代 Web 前端工程 (Vite + Vue 3 驱动)
│   ├── index.html           # SPA 挂载主页
│   ├── package.json         # 极简受控依赖：vue, echarts, lucide-vue-next，零外部重型依赖
│   └── src/
│       ├── main.js          # Vue 挂载入口
│       ├── theme.css        # VS Code 级统一工控暗黑 CSS 变量系统与原生系统字体栈
│       ├── i18n.js          # 国际化引擎 (操作系统环境自适应识别 + 中英文一键秒切)
│       ├── api.js           # REST / WebSocket 本地回环通信封装与吞吐遥测统计
│       └── components/      # 标准化高内聚组件 (Navbar, WaveformChart, OscTriggerPanel, etc.)
├── build_exe.py             # 双编译器打包流水线 (PyInstaller / Nuitka C++)
├── requirements.txt         # Python 依赖清单
└── tests/                   # 单元与集成自动化回归测试套件
```

---

## 🚀 快速开始与运行

### 1. 安装 Python 环境依赖
```bash
pip install -r requirements.txt
```

### 2. 运行模式

#### A. 桌面原生 GUI 模式 (默认)
拉起 Windows Edge WebView2 GPU 显卡硬件加速的原生桌面窗口：
```bash
python main.py
# 或双击运行 start_app.bat
```

#### B. 浏览器调试与网络联调服务模式 (Serve)
在后台启动 FastAPI 服务，可通过 Chrome / Edge 打开 `http://127.0.0.1:8000`：
```bash
python main.py --mode serve --port 8000
# 或双击运行 start_serve.bat
```

#### C. 无头环境自检模式 (CLI)
验证底层 Core 算法引擎、Server 路由总线与桌面容器可用性：
```bash
python main.py --mode cli
```

---

## 🛠️ 前端独立热重载开发 (WebUI)

```bash
cd webui
npm install
npm run dev
```

---

## 📦 一键单文件离线打包 (Build EXE)

### 选项 1: PyInstaller 单文件打包 (默认开箱即用)
```bash
python build_exe.py
```

### 选项 2: Nuitka C++ 机器码深度转译 (极致性能与安全防逆向)
```bash
python build_exe.py --compiler nuitka
```

打包生成的可执行程序位于项目根目录的 [`Serial-CAN-Debugger.exe`](Serial-CAN-Debugger.exe)，开箱即用，无需安装 Python 环境。

---

## 🧪 自动化测试验证
```bash
pytest tests/ -v
```
所有底层协议解包、DSP 算法、Modbus CRC 与 FastAPI 接口回归测试通过。
