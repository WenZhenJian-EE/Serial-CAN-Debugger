// ==========================================================================
// i18n.js - 响应式多语言国际化引擎 (支持中英文一键即时无刷新切换与持久化)
// ==========================================================================

import { ref, computed } from 'vue';

const STORAGE_KEY = 'app_locale';

// 自动检测用户操作系统与运行环境语言:
// 若用户先前在软件中手动切换过，优先遵从用户偏好；
// 若首次启动，根据操作系统环境语言自动识别：非中文系统一律自适应呈现纯正英文 en-US，免除手动切换
function detectInitialLocale() {
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved && (saved === 'zh-CN' || saved === 'en-US')) {
      return saved;
    }
  } catch (_) {}

  try {
    const sysLang = (typeof navigator !== 'undefined' && navigator.languages && navigator.languages.length > 0)
      ? navigator.languages[0]
      : (typeof navigator !== 'undefined' ? (navigator.language || navigator.userLanguage || '') : '');
    if (sysLang && sysLang.toLowerCase().startsWith('zh')) {
      return 'zh-CN';
    }
    return 'en-US';
  } catch (_) {
    return 'en-US';
  }
}

export const currentLocale = ref(detectInitialLocale());

export const messages = {
  'zh-CN': {
    nav: {
      brand: 'Serial-CAN-Debugger',
      badge: 'V3.0',
      wave: '实时示波',
      trigger: '硬件触发',
      monitor: '报文监视',
      bode: 'Bode 扫频',
      serialConnected: '串口: 已连接',
      serialDisconnected: '串口: 未连接',
      canConnected: 'CAN: 已连接',
      canDisconnected: 'CAN: 未连接',
      wsConnected: 'WS: 已联机',
      wsDisconnected: 'WS: 未连接',
      systemInfo: '系统信息与关于',
      langToggle: '中 / EN',
      github: 'GitHub 开源仓库',
    },
    sidebar: {
      serial: '串口总线 (UART)',
      can: 'CAN 总线 (CAN/FD)',
      custom: '快捷调参 (Tuning)',
    },
    wave: {
      run: '继续运行',
      pause: '暂停冻结',
      clear: '清空波形',
      cursors: '双光标测量',
      fft: 'FFT 频域分析',
      startSim: '启动仿真',
      stopSim: '停止压测',
      simRateHint: '设置下位机模拟灌流速率：实测 1,000 ~ 100,000 点/秒高速吞吐与 60FPS 稳定性',
      simRate1k: '1 kSps (串口115200)',
      simRate10k: '10 kSps (高速串口/CAN)',
      simRate50k: '50 kSps (CAN-FD/USB)',
      simRate100k: '100 kSps (极限高频灌流)',
      spline: '样条平滑',
      rawLine: '原始折线',
      rollStandard: '2.0s (标准滚屏)',
      rollFull: '全量历史 (不滚屏)',
      rollSec: '{s}s 视窗',
      fps60: '60 FPS (推荐)',
      fps120: '120 FPS (超高刷)',
      fpsNative: '原生 (屏幕同步)',
      fps30: '30 FPS (节能)',
      exportCsv: '导出 CSV',
      importCsv: '导入 CSV',
      cursorTitle: '双光标测量',
      deltaT: 'ΔT',
      freq: '频率',
      deltaV: 'ΔV',
      timeUnit: '时间 (s)',
      voltUnit: '数值 / 电压',
      pointCount: '渲染点数',
      sampleFreq: '估算采样率',
      csvExportSuccess: 'CSV 文件已成功导出',
      csvImportSuccess: 'CSV 文件已成功导入并在图表中冻结分析',
      csvImportError: 'CSV 文件解析失败',
    },
    serial: {
      title: '串口总线设置 (SCI / UART)',
      statusOpen: '已打开',
      statusClosed: '已关闭',
      port: '端口 (COM):',
      refresh: '刷新串口列表',
      autoProbe: '自动探针识别',
      baudrate: '波特率:',
      protocol: '协议模式:',
      protoCustom: '通用二进制/自定义 (9B / 17B)',
      protoModbus: 'Modbus-RTU 工业总线',
      parity: '校验位:',
      parityNone: 'None (无校验)',
      parityEven: 'Even (偶校验)',
      parityOdd: 'Odd (奇校验)',
      dataBits: '数据位:',
      stopBits: '停止位:',
      flowControl: '硬件流控:',
      openPort: '打开串口',
      closePort: '关闭串口',
      sendTitle: '串口手动下发',
      sendBtn: '发送',
      sendHex: 'Hex (十六进制)',
      sendAscii: 'ASCII 字符串',
      placeholderSend: '输入待下发数据...',
      sentSuccess: '串口数据已发送',
    },
    can: {
      title: 'CAN 总线设置 (CAN / CAN-FD)',
      statusConnected: '已连接',
      statusDisconnected: '已断开',
      interface: '适配器硬件提供商:',
      channel: '通道 (Channel):',
      bitrate: '仲裁段波特率:',
      canfd: 'CAN FD 扩展:',
      dataBitrate: '数据段波特率:',
      connect: '连接 CAN 总线',
      disconnect: '断开 CAN 总线',
      dbcTitle: 'DBC 信号数据库解析',
      loadDbc: '导入 DBC 文件',
      dbcLoaded: '已加载 DBC',
      sendTitle: '发送 CAN 报文',
      canId: '帧 ID (Hex):',
      dataHex: '数据载荷 (Hex):',
      extended: '扩展帧 (29-bit)',
      sendBtn: '发送单帧',
      periodicTitle: '周期循环发送',
      interval: '周期 (ms):',
      startPeriodic: '启动周期发送',
      stopPeriodic: '停止周期发送',
      sentSuccess: 'CAN 报文已下发',
    },
    custom: {
      title: '自定义调试控制',
      addControl: '添加',
      saveConfig: '保存配置',
      exportJson: '导出',
      importJson: '导入',
      clearAll: '清空',
      btnConfigTitle: '配置自定义控件',
      controlType: '控件类型:',
      typeButton: '按钮 (点按即发)',
      typeSlider: '滑块 (拖动调参)',
      nameLabel: '控件名称 (自定义):',
      namePlaceholder: '如: P+, 启动, 停机, 速度, 电压',
      dataLabel: '发送指令 (必填):',
      dataPlaceholder: '如: SET P=1.2 或 A5 01 02 5A',
      dataRequired: '请填写发送指令内容（必填项）',
      emptyPayloadTip: '按钮 [{name}] 尚未配置发送指令！请点击右侧齿轮 ⚙ 设置',
      noPayload: '未填指令',
      sliderMin: '最小值:',
      sliderMax: '最大值:',
      sliderStep: '步长:',
      sliderDefault: '初始默认值:',
      sliderTemplate: '下发模板 ({val} 为数值占位符):',
      templatePlaceholder: '如: P={val}\\r\\n 或 SET SPEED={val}\\r\\n',
      isHex: '十六进制 (HEX) 编码',
      targetBus: '目标总线:',
      busAuto: '自动跟随当前硬件总线',
      busSerial: '强制指定: 串口 UART',
      busCan: '强制指定: CAN 总线',
      confirm: '保存生效',
      cancel: '取消',
      delete: '删除此控件',
      emptyTip: '暂无自定义控件，点击上方“+”或下方插槽新建按钮与滑块',
      sentSuccess: '已下发 [{name}]: {data}',
      configSaved: '控件配置已本地保存',
      configExported: '配置已导出为 JSON',
      configImported: '配置已成功导入',
      unconfiguredSlot: '未配置 (点击设置)',
    },
    trigger: {
      title: '硬件边沿触发器',
      mode: '触发模式:',
      modeAuto: 'Auto (自动刷新)',
      modeNormal: 'Normal (达标单次等待)',
      modeSingle: 'Single (捕获即冻结)',
      edge: '边沿极性:',
      edgeRising: '上升沿 (Rising)',
      edgeFalling: '下降沿 (Falling)',
      channel: '触发通道:',
      threshold: '触发电平 / 阈值:',
      holdoff: '释抑采样点数:',
      apply: '应用配置',
      reset: '复位触发状态',
      statusWaiting: '等待触发条件满足...',
      statusTriggered: '已触发捕获！',
    },
    monitor: {
      title: '高频报文实时虚拟监视器',
      filterPlaceholder: '按 ID / 协议 / 关键词过滤...',
      autoScroll: '自动滚屏',
      hexMode: '十六进制 Hex 视图',
      clear: '清空列表',
      export: '导出报文',
      colTime: '时间戳',
      colBus: '总线',
      colId: 'ID / 通道',
      colLen: '长度',
      colData: '数据载荷',
    },
    bode: {
      title: 'Bode 图动态扫频分析',
      startFreq: '起始频率 (Hz):',
      stopFreq: '终止频率 (Hz):',
      points: '扫频点数:',
      amplitude: '激励幅值:',
      startSweep: '开始扫频',
      stopSweep: '停止扫频',
      magTitle: '幅频特性曲线 (Magnitude, dB)',
      phaseTitle: '相频特性曲线 (Phase, deg)',
    },
    modal: {
      title: 'Serial-CAN-Debugger 系统信息与关于',
      appDesc: '支持串口、CAN/CAN-FD 与实时示波器调试的现代化工业级上位机',
      authorTitle: '开源作者与项目信息',
      authorName: '开源作者:',
      authorVal: '温振键 (WenZhenJian-EE)',
      githubHome: 'GitHub 个人主页:',
      githubRepo: '开源项目仓库:',
      techBlog: '技术博客 / 主页:',
      license: '开源授权协议:',
      licenseVal: 'MIT License (自由商用与深度定制)',
      openInBrowser: '在浏览器中打开',
      badgeDesc: 'Cat App Icon Studio 家族化徽章',
      versionKey: '软件版本:',
      versionVal: 'Serial-CAN-Debugger V3.0 专业版',
      runtimeKey: '宿主内核:',
      runtimeVal: 'Microsoft Edge WebView2 (GPU 硬件加速)',
      busKey: '本地总线:',
      busVal: 'FastAPI + WebSocket (<dHf 14B 二进制高速流)',
      engineKey: '算力引擎:',
      engineVal: 'Python 3.11 + NumPy + SciPy + cantools',
      transitionsKey: '视图过渡:',
      transitionsVal: 'W3C View Transitions API (丝滑 60FPS)',
      depthKey: '波形深度:',
      depthVal: '100,000 点深度环形缓冲 + 双测量光标',
      shortcutsKey: '快捷键组:',
      shortcutsVal: 'Space (暂停/运行) | Ctrl+L (清空) | 1-3 (切主视图)',
      packageKey: '打包形态:',
      packageVal: '极简独立离线单文件 .exe (零额外依赖)',
    },
  },
  'en-US': {
    nav: {
      brand: 'Serial-CAN-Debugger',
      badge: 'V3.0',
      wave: 'Oscilloscope',
      trigger: 'Trigger',
      monitor: 'Monitor',
      bode: 'Bode Plot',
      serialConnected: 'Serial: Connected',
      serialDisconnected: 'Serial: Disconnected',
      canConnected: 'CAN: Connected',
      canDisconnected: 'CAN: Disconnected',
      wsConnected: 'WS: Connected',
      wsDisconnected: 'WS: Disconnected',
      systemInfo: 'System Info & About',
      langToggle: '中 / EN',
      github: 'GitHub Repository',
    },
    sidebar: {
      serial: 'Serial (UART)',
      can: 'CAN Bus (CAN/FD)',
      custom: 'Quick Controls (Tuning)',
    },
    wave: {
      run: 'Resume Run',
      pause: 'Pause Freeze',
      clear: 'Clear Wave',
      cursors: 'Measure Cursors',
      fft: 'FFT Analysis',
      startSim: 'Start Sim',
      stopSim: 'Stop Sim',
      simRateHint: 'Set simulation streaming rate: benchmark 1,000 ~ 100,000 Sps throughput and 60FPS stability',
      simRate1k: '1 kSps (Serial 115200)',
      simRate10k: '10 kSps (High-speed Serial/CAN)',
      simRate50k: '50 kSps (CAN-FD/USB)',
      simRate100k: '100 kSps (Extreme Benchmark)',
      spline: 'Spline',
      rawLine: 'Raw Lines',
      rollStandard: '2.0s (Standard Roll)',
      rollFull: 'Full History (No Roll)',
      rollSec: '{s}s Window',
      fps60: '60 FPS (Recommended)',
      fps120: '120 FPS (Ultra High)',
      fpsNative: 'Native (Screen Sync)',
      fps30: '30 FPS (Power Save)',
      exportCsv: 'Export CSV',
      importCsv: 'Import CSV',
      cursorTitle: 'Cursor Measurements',
      deltaT: 'ΔT',
      freq: 'Freq',
      deltaV: 'ΔV',
      timeUnit: 'Time (s)',
      voltUnit: 'Value / Voltage',
      pointCount: 'Render Points',
      sampleFreq: 'Est. Sample Rate',
      csvExportSuccess: 'CSV file exported successfully',
      csvImportSuccess: 'CSV imported and frozen for waveform inspection',
      csvImportError: 'Failed to parse CSV file',
    },
    serial: {
      title: 'Serial Port Settings (SCI / UART)',
      statusOpen: 'Opened',
      statusClosed: 'Closed',
      port: 'Port (COM):',
      refresh: 'Refresh Ports',
      autoProbe: 'Auto Probe',
      baudrate: 'Baudrate:',
      protocol: 'Protocol:',
      protoCustom: 'Binary / Custom (9B / 17B)',
      protoModbus: 'Modbus-RTU Fieldbus',
      parity: 'Parity:',
      parityNone: 'None',
      parityEven: 'Even',
      parityOdd: 'Odd',
      dataBits: 'Data Bits:',
      stopBits: 'Stop Bits:',
      flowControl: 'Flow Control:',
      openPort: 'Open Port',
      closePort: 'Close Port',
      sendTitle: 'Manual Serial Transmit',
      sendBtn: 'Send',
      sendHex: 'Hexadecimal (Hex)',
      sendAscii: 'ASCII String',
      placeholderSend: 'Enter data to send...',
      sentSuccess: 'Serial data sent successfully',
    },
    can: {
      title: 'CAN Bus Settings (CAN / CAN-FD)',
      statusConnected: 'Connected',
      statusDisconnected: 'Disconnected',
      interface: 'Hardware Provider:',
      channel: 'Channel:',
      bitrate: 'Arbitration Bitrate:',
      canfd: 'CAN FD Extension:',
      dataBitrate: 'Data Bitrate:',
      connect: 'Connect CAN',
      disconnect: 'Disconnect CAN',
      dbcTitle: 'DBC Signal Database Parser',
      loadDbc: 'Load DBC File',
      dbcLoaded: 'DBC Loaded',
      sendTitle: 'Transmit CAN Frame',
      canId: 'Frame ID (Hex):',
      dataHex: 'Payload (Hex):',
      extended: 'Extended Frame (29-bit)',
      sendBtn: 'Send Frame',
      periodicTitle: 'Periodic Cyclic Transmit',
      interval: 'Interval (ms):',
      startPeriodic: 'Start Periodic',
      stopPeriodic: 'Stop Periodic',
      sentSuccess: 'CAN frame transmitted',
    },
    custom: {
      title: 'Custom Debug Controls',
      addControl: 'Add',
      saveConfig: 'Save Config',
      exportJson: 'Export',
      importJson: 'Import',
      clearAll: 'Clear',
      btnConfigTitle: 'Configure Custom Control',
      controlType: 'Control Type:',
      typeButton: 'Button (Click to Send)',
      typeSlider: 'Slider (Tuning)',
      nameLabel: 'Label / Name (Custom):',
      namePlaceholder: 'e.g. P+, Run, Stop, Speed, Volt',
      dataLabel: 'Command / Payload (Required):',
      dataPlaceholder: 'e.g. SET P=1.2 or A5 01 02 5A',
      dataRequired: 'Please enter command / payload (Required)',
      emptyPayloadTip: 'Button [{name}] has no command payload! Click gear ⚙ to configure',
      noPayload: 'NO CMD',
      sliderMin: 'Min Value:',
      sliderMax: 'Max Value:',
      sliderStep: 'Step:',
      sliderDefault: 'Default Value:',
      sliderTemplate: 'Send Template ({val} placeholder):',
      templatePlaceholder: 'e.g. P={val}\\r\\n or SET SPEED={val}\\r\\n',
      isHex: 'Hexadecimal (HEX) Encoding',
      targetBus: 'Target Bus:',
      busAuto: 'Auto (Current Active Bus)',
      busSerial: 'Force: Serial (UART)',
      busCan: 'Force: CAN Bus',
      confirm: 'Save Control',
      cancel: 'Cancel',
      delete: 'Delete Control',
      emptyTip: 'No custom controls yet. Click "+" or an empty slot to create buttons/sliders.',
      sentSuccess: 'Dispatched [{name}]: {data}',
      configSaved: 'Configuration saved locally',
      configExported: 'Configuration exported to JSON',
      configImported: 'Configuration imported successfully',
      unconfiguredSlot: 'Unconfigured (Click to Setup)',
    },
    trigger: {
      title: 'Hardware Edge Trigger',
      mode: 'Trigger Mode:',
      modeAuto: 'Auto (Continuous)',
      modeNormal: 'Normal (Wait for Condition)',
      modeSingle: 'Single (Freeze on Hit)',
      edge: 'Edge Slope:',
      edgeRising: 'Rising Edge',
      edgeFalling: 'Falling Edge',
      channel: 'Trigger Channel:',
      threshold: 'Threshold Level:',
      holdoff: 'Holdoff Samples:',
      apply: 'Apply Config',
      reset: 'Reset Trigger',
      statusWaiting: 'Waiting for trigger condition...',
      statusTriggered: 'Triggered & captured!',
    },
    monitor: {
      title: 'High-Frequency Real-Time Virtual Monitor',
      filterPlaceholder: 'Filter by ID / Protocol / Keyword...',
      autoScroll: 'Auto Scroll',
      hexMode: 'Hexadecimal View',
      clear: 'Clear List',
      export: 'Export Logs',
      colTime: 'Timestamp',
      colBus: 'Bus',
      colId: 'ID / Channel',
      colLen: 'Length',
      colData: 'Payload',
    },
    bode: {
      title: 'Bode Dynamic Frequency Sweeper',
      startFreq: 'Start Freq (Hz):',
      stopFreq: 'Stop Freq (Hz):',
      points: 'Sweep Points:',
      amplitude: 'Excitation Amp:',
      startSweep: 'Start Sweep',
      stopSweep: 'Stop Sweep',
      magTitle: 'Magnitude Curve (dB)',
      phaseTitle: 'Phase Curve (deg)',
    },
    modal: {
      title: 'Serial-CAN-Debugger System Info & About',
      appDesc: 'Industrial Host Computer Debugger for Serial, CAN/CAN-FD & Real-Time Oscilloscope',
      authorTitle: 'Author & Open Source Project Info',
      authorName: 'Author:',
      authorVal: 'Zhenjian Wen (WenZhenJian-EE)',
      githubHome: 'GitHub Profile:',
      githubRepo: 'GitHub Repository:',
      techBlog: 'Technical Blog / Home:',
      license: 'License:',
      licenseVal: 'MIT License (Commercial & Modification Friendly)',
      openInBrowser: 'Open in Browser',
      badgeDesc: 'Cat App Icon Studio Family Badge',
      versionKey: 'Version:',
      versionVal: 'Serial-CAN-Debugger V3.0 Pro',
      runtimeKey: 'Host Runtime:',
      runtimeVal: 'Microsoft Edge WebView2 (GPU Accelerated)',
      busKey: 'Local Loopback:',
      busVal: 'FastAPI + WebSocket (<dHf 14B Binary Stream)',
      engineKey: 'Compute Engine:',
      engineVal: 'Python 3.11 + NumPy + SciPy + cantools',
      transitionsKey: 'Transitions:',
      transitionsVal: 'W3C View Transitions API (Fluid 60FPS)',
      depthKey: 'Buffer Depth:',
      depthVal: '100,000 Points Deep Circular Ring + Cursors',
      shortcutsKey: 'Shortcuts:',
      shortcutsVal: 'Space (Pause/Run) | Ctrl+L (Clear) | 1-3 (Switch Views)',
      packageKey: 'Packaging:',
      packageVal: 'Compact Standalone Portable .exe (Zero External Deps)',
    },
  },
};

/**
 * 获取翻译文本，支持点分隔路径与参数替换
 * 例如: t('wave.rollSec', { s: 2.0 })
 */
export function t(path, params = {}) {
  const lang = currentLocale.value;
  const dict = messages[lang] || messages['zh-CN'];
  
  const keys = path.split('.');
  let val = dict;
  for (const k of keys) {
    if (val && typeof val === 'object' && k in val) {
      val = val[k];
    } else {
      // 回退至中文
      val = null;
      break;
    }
  }

  if (val === null || val === undefined) {
    let fallback = messages['zh-CN'];
    for (const k of keys) {
      if (fallback && typeof fallback === 'object' && k in fallback) {
        fallback = fallback[k];
      } else {
        return path;
      }
    }
    val = fallback;
  }

  if (typeof val === 'string') {
    return val.replace(/\{(\w+)\}/g, (_, match) => (match in params ? params[match] : `{${match}}`));
  }
  return val || path;
}

/**
 * 一键切换中英文
 */
export function toggleLocale() {
  const next = currentLocale.value === 'zh-CN' ? 'en-US' : 'zh-CN';
  setLocale(next);
  return next;
}

/**
 * 设置指定语言并保存到 localStorage
 */
export function setLocale(lang) {
  if (messages[lang]) {
    currentLocale.value = lang;
    localStorage.setItem(STORAGE_KEY, lang);
  }
}
