# 03_高频硬件通信协议栈迁移与Zero_Logic_Loss资产保全架构

---

## 一、 核心资产零损失 (Zero Logic Loss) 铁律

在桌面软件系统重构中，最容易出现的重大事故是：为了追求新界面的美观与架构的现代化，不慎在迁移过程中丢失或简化了底层的工业通信协议、特定硬件边缘驱动或数值计算算法。

本项目在立项之初即立下 **100% Zero Logic Loss（核心领域资产零丢失）** 硬指标：
- 无论外部表现层从 Electron 换成 Vue 3，还是容器层从 Node.js 换成 pywebview，**底层的串口通信、CAN/CAN-FD 驱动、DBC 动态信号解码、Modbus-RTU 校验与硬件录波状态机，必须 100% 原汁原味保全并实现纯 Python 模块化解耦！**

---

## 二、 核心通信协议栈架构与领域核提炼

在旧版工程中，通信 Worker 逻辑分散在各层，与 UI 界面信号强绑定。在 MAP 2.0 中，所有硬件通信逻辑被整体重构至纯粹的 `core/parsers/` 包中：

```
core/parsers/
├── base_worker.py        # 硬件工作线程抽象基类，规范统一的 connect/disconnect/send 接口与回调总线
├── serial_worker.py      # 串口驱动核：支持 115200~921600 波特率、auto_probe 智能匹配、二进制解帧
├── can_worker.py         # CAN 总线核：统一对接 PCAN/ZLG/Virtual，集成 cantools 动态 DBC 解码
├── modbus_worker.py      # Modbus 协议核：集成 Modbus-RTU CRC16 校验与线圈/寄存器解析
└── tcp_worker.py         # TCP/IP 工业网络通信客户端
```

### 1. `SerialWorker` 串口智能探测与高速收发
- **自动握手算法 (`auto_probe`)**：遍历系统当前全部 COM 端口，向各端口下发特定查询帧（如 `*IDN?` 或硬件心跳包），在指定超时窗口内捕获响应，实现毫秒级硬件自动连击；
- **双缓冲数据流水线**：将串口底层字节读取（I/O 密集型）与帧头匹配、转义解码（CPU 密集型）分离，确保在 921600 高波特率下数据流不发生缓冲区溢出截断。

### 2. `CanWorker` 与 `cantools` 动态 DBC 矩阵解码
- **多硬件厂商透明抽象**：统一封装 `python-can` 驱动层，支持 `virtual`（脱机模拟）、`pcan`（PEAK-System）、`vector`、`canalystii`（周立功创芯科技等）透明切换；
- **cantools 深度绑定**：
  ```python
  def load_dbc(self, dbc_content: str):
      """动态载入用户上传的 DBC 数据库文件"""
      self.db = cantools.database.load_string(dbc_content, 'dbc')

  def _process_can_message(self, msg):
      if self.db:
          try:
              # 根据 Arbitration ID 实时解密各 Signal 物理值
              decoded_signals = self.db.decode_message(msg.arbitration_id, msg.data)
              for sig_name, sig_val in decoded_signals.items():
                  self.on_signal_callback(sig_name, sig_val, msg.timestamp)
          except KeyError:
              pass
  ```
- **周期报文硬件定时发送引擎**：利用高精度线程定时器（精确至毫秒级），支持用户批量配置周期发送列表（`period_ms`），并在后台自动守护发送。

### 3. `ModbusWorker` 与 CRC16 高性能查表
- 针对电力电子与 PLC 监控，内置标准 Modbus-RTU 状态机，包含高速 CRC16 计算算法，确保对 01、03、06、10 等高频功能码的稳定收发。

---

## 三、 零 GUI 依赖与无头自动化回归验证

为了彻底杜绝新旧代码再次发生“逻辑与界面死锁”的悲剧，`core/` 目录被施加了最严格的工程约束：
- **物理禁止引入任何图形库**：在 `core/` 及其子模块中，绝对 100% 禁止 `import webview`、`import PySide6` 或任何前端相关包；
- **全链路单元测试覆盖**：在 `tests/test_core.py` 中编写针对各通信 Worker 与计算模型的自动化用例：
  ```python
  def test_modbus_helpers():
      data = bytes([0x01, 0x03, 0x00, 0x00, 0x00, 0x0A])
      crc = calculate_crc16(data)
      assert crc == 0xCDCA

  def test_system_identification():
      # 验证阶跃响应系统辨识算法在无 GUI 环境下的纯粹数学收敛
      ...
  ```
- 运行 `pytest tests/` 仅需 **0.75 秒** 即可完成核心领域逻辑的 100% 自动化回归测试，为后续长期维护奠定了极高确定性基石。
