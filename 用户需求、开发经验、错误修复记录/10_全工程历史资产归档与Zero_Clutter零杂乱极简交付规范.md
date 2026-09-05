# 10_全工程历史资产归档与Zero_Clutter零杂乱极简交付规范

---

## 一、 工作区零杂乱准则 (Zero-Clutter Workspace)

在遵循《AGENTS.md》与现代软件工程管理规范时，我们设立了极高标准的工程交付纪律：
> **项目根目录下保持极简纯净，严禁散落临时调试脚本、临时文本或碎片文件；所有文档、脚本与交付物必须各归其位、自包含归档。**

在项目长期迭代过程中，容易堆积以下五类“历史垃圾”：
1. **旧技术栈遗留母本**：如旧版 Electron 源码库（`Source_Code/`），包含数万行已被全面淘汰的旧代码；
2. **临时调试与修复脚本**：如在应急阶段编写的 `fix_app.py`、`fix_app_smart.py`、`start_dev.bat` 等；
3. **空壳残留目录**：如旧版遗留的 `backend/`；
4. **编译器中间产物与缓存**：如 PyInstaller 的 `build/`、`dist/`，Python 字节码 `__pycache__/`，测试缓存 `.pytest_cache/`；
5. **测试过程生成的临时文件**：如单元测试时产生的空日志目录 `fault_logs/`、`trend_logs/`、`bode_history/`。

如果任由这些文件散落于根目录，用户在打开工程时眼花缭乱，根本无法辨别哪个是最新程序，极易误触旧脚本或旧执行文件。

---

## 二、 历史资产彻底清理与最终工程收敛

在用户明确发出指令：
> **“所有历史垃圾文件全部删除，整理好”**

我们对项目根目录执行了坚决、彻底的清理战役：
- **`Source_Code/`** 整体彻底清理；
- **`archive/`** 临时脚本库彻底清理；
- **`backend/`** 旧空目录彻底清理；
- **`build/`** 与 **`dist/`** 彻底清理；
- **所有缓存与临时测试目录** 彻底清除。

### 清理后的绝对纯净工程结构全景：

```text
D:\Data\Agent\MyDev\Serial-CAN-Debugger-Electron/
│
├── Serial-CAN-Debugger.exe           <--- 【唯一交付程序：双击即开，纯净独立】
│
├── core/                             # 100% 领域核心算法与通信驱动核 (Zero Logic Loss)
│   ├── parsers/                      # 串口/CAN(cantools)/Modbus/TCP 通信 Worker
│   ├── models/                       # DSP(FFT/THD)、FRA Bode 扫频、边沿触发器、黑匣子
│   └── db/                           # SQLite 嵌入式数据库 (WAL 模式)
│
├── desktop/                          # Windows Edge WebView2 原生桌面窗口宿主
│   └── window.py
│
├── server/                           # FastAPI 本地高速网络总线
│   ├── api.py                        # WebSocket /ws 14B 二进制流协议与静态挂载
│   ├── state.py                      # 内存单例状态机
│   └── routes/                       # 连接/发送/分析/触发/日志/配置高内聚路由
│
├── webui/                            # 纯净 Vue 3 前端工程源码
│   ├── src/theme.css                 # 工控极简暗黑变量系统与 View Transitions 动画
│   ├── src/api.js                    # 二进制解包引擎与吞吐量遥测
│   └── src/components/               # 示波器(100k点+双光标)、虚拟滚动监视器等
│
├── tests/                            # 自动化全链路单元与集成测试套件
│   └── test_core.py
│
├── 用户需求、开发经验、错误修复记录/      <--- 【学习 PinDock 永久沉淀的技术档案库】
│   ├── README.md                     # 全景技术档案索引
│   ├── 01_Serial-CAN-Debugger总体架构演进与用户需求全景规范.md
│   ├── 02_踩坑复盘_从Electron到MAP2.0去重型运行时与秒级启动突围.md
│   ├── 03_高频硬件通信协议栈迁移与Zero_Logic_Loss资产保全架构.md
│   ├── 04_WebSocket_14字节二进制推流总线与前后端解包性能突围.md
│   ├── 05_十万点深度波形环形缓冲与LTTB降采样60FPS流畅渲染.md
│   ├── 06_双测量光标Cursor_AB即时解算与二分插值频率标尺架构.md
│   ├── 07_海量工控报文虚拟滚动VirtualScroll彻底根除掉帧卡顿.md
│   ├── 08_W3C_View_Transitions与工控极简暗黑设计系统规范.md
│   ├── 09_离线单文件EXE打包工程_PyInstaller依赖精简与Nuitka深度转译规范.md
│   └── 10_全工程历史资产归档与Zero_Clutter零杂乱极简交付规范.md
│
├── build_exe.py                      # 双编译器自动化打包流水线
├── main.py                           # 调度中枢入口 (desktop / serve / cli 三模态)
├── README.md                         # 现代项目说明与快速上手手册
├── requirements.txt                  # Python 极简核心依赖
├── database.db                       # SQLite 元器件规格库与配置存储
├── start_app.bat                     # 源码模式原生客户端启动脚本
└── start_serve.bat                   # 浏览器联调服务启动脚本
```

---

## 三、 持续演进准则与后续更新规范

本目录 `用户需求、开发经验、错误修复记录/` 将作为本项目的**技术基因库与演化日志**：
1. **新需求提出时**：在目录内追加 `11_...`，记录用户痛点背景、架构设计方案与实现边界；
2. **发生严重 Bug 时**：以 `踩坑复盘_...` 为题，详细记录故障复现现象、白盒推演排查过程与最终根治代码；
3. **性能调优时**：记录压测指标、算法对比与量化提升数据；
4. **README 同步维护**：每新增一篇档案，同步更新 `README.md` 的索引表格，确保项目知识资产随时可查、清晰透明、自洽传承。
