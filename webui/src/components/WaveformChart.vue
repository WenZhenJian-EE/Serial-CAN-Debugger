<template>
  <div class="waveform-container">
    <!-- 顶部工具控制栏 -->
    <div class="chart-toolbar">
      <div class="toolbar-left">
        <button
          :class="isPaused ? 'btn-success' : 'btn-primary'"
          @click="togglePause"
          title="[Space]"
        >
          <component :is="isPaused ? Play : Square" :size="13" />
          <span>{{ isPaused ? t('wave.run') : t('wave.pause') }}</span>
          <span class="kbd-hint">Space</span>
        </button>

        <button @click="clearData" title="[Ctrl+L]">
          <Trash2 :size="13" />
          <span>{{ t('wave.clear') }}</span>
          <span class="kbd-hint">Ctrl+L</span>
        </button>

        <div class="toolbar-divider"></div>

        <!-- 框选放大与复位缩放快捷工具 -->
        <button
          :class="{ 'btn-primary': isBoxZoomActive }"
          @click="toggleBoxZoom"
          :title="t('wave.boxZoomTip')"
        >
          <ZoomIn :size="13" />
          <span>{{ t('wave.boxZoom') }}</span>
        </button>

        <button
          @click="resetZoomAndResume"
          :title="t('wave.resetZoomTip')"
        >
          <RotateCcw :size="13" />
          <span>{{ t('wave.resetZoom') }}</span>
        </button>

        <div class="toolbar-divider"></div>

        <!-- 横轴时基视窗直接设定 (秒数直接输入 + 快捷预设) -->
        <div class="axis-control-group" :title="t('wave.timeBaseLabel')">
          <span class="axis-label">{{ t('wave.timeBaseLabel') }}</span>
          <select v-model="timeWindowPreset" class="mini-select time-select" @change="onTimeWindowPresetChange">
            <option :value="0.05">50ms</option>
            <option :value="0.1">100ms</option>
            <option :value="0.2">200ms</option>
            <option :value="0.5">500ms</option>
            <option :value="1.0">1.0s</option>
            <option :value="2.0">{{ t('wave.rollStandard') }}</option>
            <option :value="5.0">5.0s</option>
            <option :value="10.0">10.0s</option>
            <option :value="0">{{ t('wave.rollFull') }}</option>
            <option value="custom">{{ t('wave.timeBaseCustom') }}</option>
          </select>
          <div class="direct-input-wrap" v-if="timeWindowPreset !== 0">
            <input
              type="number"
              v-model.number="customTimeWindow"
              step="0.1"
              min="0.01"
              max="3600"
              class="mini-input-number"
              @change="onCustomTimeWindowChange"
              @keydown.enter="onCustomTimeWindowChange"
              :title="t('wave.timeBaseCustom')"
            />
            <span class="unit-suffix">{{ t('wave.timeBaseUnit') }}</span>
          </div>
        </div>

        <!-- 纵轴量程直接设定 (Auto 自动量程 + 快速预设 + Min/Max 直接数值输入) -->
        <div class="axis-control-group" :title="t('wave.yAxisLabel')">
          <span class="axis-label">{{ t('wave.yAxisLabel') }}</span>
          <select v-model="yAxisPreset" class="mini-select range-select" @change="onYAxisPresetChange">
            <option value="auto">{{ t('wave.yAxisAuto') }}</option>
            <option value="pm5">±5 V</option>
            <option value="pm10">±10 V</option>
            <option value="pm15">±15 V</option>
            <option value="pm24">±24 V</option>
            <option value="pm50">±50 V</option>
            <option value="pm100">±100 V</option>
            <option value="0_3v3">0 ~ 3.3 V</option>
            <option value="0_5v">0 ~ 5.0 V</option>
            <option value="0_24v">0 ~ 24 V</option>
            <option value="0_380v">0 ~ 380 V</option>
            <option value="custom">{{ t('wave.yAxisCustom') }}</option>
          </select>
          <div class="direct-input-wrap" v-if="yAxisPreset !== 'auto'">
            <input
              type="number"
              v-model.number="yAxisMin"
              step="1"
              class="mini-input-number y-min"
              @change="onCustomYAxisChange"
              @keydown.enter="onCustomYAxisChange"
              placeholder="Min"
              title="Y-Min"
            />
            <span class="range-sep">~</span>
            <input
              type="number"
              v-model.number="yAxisMax"
              step="1"
              class="mini-input-number y-max"
              @change="onCustomYAxisChange"
              @keydown.enter="onCustomYAxisChange"
              placeholder="Max"
              title="Y-Max"
            />
            <span class="unit-suffix">V</span>
          </div>
        </div>

        <div class="toolbar-divider"></div>

        <!-- 测量光标开关 -->
        <button
          :class="{ 'btn-primary': showCursors }"
          @click="showCursors = !showCursors"
          :title="t('wave.cursors')"
        >
          <Crosshair :size="13" />
          <span>{{ t('wave.cursors') }}</span>
        </button>

        <!-- FFT 频域副图开关 -->
        <button
          :class="{ 'btn-primary': showFft }"
          @click="showFft = !showFft"
        >
          <TrendingUp :size="13" />
          <span>{{ t('wave.fft') }}</span>
        </button>

        <!-- 连续平滑样条插值开关 -->
        <button
          :class="{ 'btn-primary': isSmoothCurve }"
          @click="toggleSmoothCurve"
        >
          <span>{{ isSmoothCurve ? t('wave.spline') : t('wave.rawLine') }}</span>
        </button>

        <!-- 下位机高频灌流压测 / 仿真开关 -->
        <button
          :class="isSimulating ? 'btn-success pulse-anim' : ''"
          @click="toggleSimulation"
          :title="t('wave.simRateHint')"
        >
          <Activity :size="13" />
          <span>{{ isSimulating ? t('wave.stopSim') : t('wave.startSim') }}</span>
        </button>

        <!-- 压测吞吐率选择器 -->
        <div class="picker-group" :title="t('wave.simRateHint')">
          <select v-model.number="simRate" class="mini-select rate-select" :disabled="isSimulating">
            <option :value="1000">{{ t('wave.simRate1k') }}</option>
            <option :value="10000">{{ t('wave.simRate10k') }}</option>
            <option :value="50000">{{ t('wave.simRate50k') }}</option>
            <option :value="100000">{{ t('wave.simRate100k') }}</option>
          </select>
        </div>

        <div class="fps-badge" title="FPS">
          <span>FPS: {{ currentFps }}</span>
        </div>

        <!-- 刷新率目标选择器 -->
        <div class="picker-group">
          <select v-model.number="targetFps" class="mini-select">
            <option :value="60">{{ t('wave.fps60') }}</option>
            <option :value="120">{{ t('wave.fps120') }}</option>
            <option :value="0">{{ t('wave.fpsNative') }}</option>
            <option :value="30">{{ t('wave.fps30') }}</option>
          </select>
        </div>

      </div>

      <div class="toolbar-right">
        <!-- 外部 CSV 数据文件导入入口 -->
        <button class="btn-primary" @click="triggerCsvImport" :title="t('wave.importCsv')">
          <Upload :size="13" />
          <span>{{ t('wave.importCsv') }}</span>
        </button>
        <input
          ref="csvFileInputRef"
          type="file"
          accept=".csv,.txt"
          style="display: none"
          @change="handleCsvFileImport"
        />

        <button @click="exportCsv" :title="t('wave.exportCsv')">
          <Download :size="13" />
          <span>{{ t('wave.exportCsv') }}</span>
        </button>
        <button @click="exportMat" title="MATLAB .mat">
          <FileText :size="13" />
          <span>MAT</span>
        </button>
      </div>
    </div>

    <!-- 图表主体区域 -->
    <div class="chart-content" :class="{ 'with-fft': showFft }">
      <!-- 局部细节放大与后台持续缓冲悬浮 HUD 胶囊 -->
      <div v-if="isUserZooming" class="zoom-active-banner">
        <div class="zoom-banner-left">
          <Search :size="13" class="zoom-icon-pulse" />
          <span class="zoom-banner-text">{{ t('wave.zoomActiveHint') }}</span>
          <span class="zoom-banner-tip">{{ t('wave.wheelZoomHint') }}</span>
        </div>
        <button class="btn-resume" @click="resetZoomAndResume">
          <RotateCcw :size="12" />
          <span>{{ t('wave.resumeTrack') }}</span>
        </button>
      </div>

      <!-- 主时域示波图 -->
      <div class="echarts-wrapper" ref="chartRef"></div>

      <!-- 双测量光标悬浮仪表板 (Cursor A & Cursor B) -->
      <div v-if="showCursors" class="cursor-hud">
        <div class="cursor-hud-header">
          <div class="hud-title">
            <Crosshair :size="12" class="text-accent" />
            <span>{{ t('wave.cursorTitle') }}</span>
          </div>
          <div class="hud-channel-sel">
            <span>测量通道:</span>
            <select v-model="cursorChannel" class="mini-select">
              <option v-for="c in channels.filter(c => c.enabled)" :key="c.id" :value="c.id">
                CH{{ c.id }} ({{ c.name }})
              </option>
            </select>
          </div>
        </div>

        <div class="hud-grid">
          <div class="hud-card card-a">
            <div class="hud-tag">Cursor A</div>
            <div class="hud-val">T: {{ cursorA.toFixed(4) }} s</div>
            <div class="hud-val">V: {{ cursorValA.toFixed(2) }} V</div>
          </div>
          <div class="hud-card card-b">
            <div class="hud-tag">Cursor B</div>
            <div class="hud-val">T: {{ cursorB.toFixed(4) }} s</div>
            <div class="hud-val">V: {{ cursorValB.toFixed(2) }} V</div>
          </div>
        </div>

        <!-- 差异参数自动解算 -->
        <div class="hud-delta">
          <div class="delta-item">
            <span class="delta-label">{{ t('wave.deltaT') }}:</span>
            <strong class="delta-value">{{ formatDeltaT(deltaT) }}</strong>
          </div>
          <div class="delta-item">
            <span class="delta-label">{{ t('wave.freq') }} (1/ΔT):</span>
            <strong class="delta-value highlight">{{ formatFrequency(frequency) }}</strong>
          </div>
          <div class="delta-item">
            <span class="delta-label">{{ t('wave.deltaV') }}:</span>
            <strong class="delta-value">{{ Math.abs(cursorValB - cursorValA).toFixed(2) }} V</strong>
          </div>
        </div>

        <!-- 滑块微调光标 -->
        <div class="hud-sliders">
          <div class="slider-row">
            <span>A:</span>
            <input
              type="range"
              :min="timeMin"
              :max="timeMax"
              step="0.0001"
              v-model.number="cursorA"
            />
          </div>
          <div class="slider-row">
            <span>B:</span>
            <input
              type="range"
              :min="timeMin"
              :max="timeMax"
              step="0.0001"
              v-model.number="cursorB"
            />
          </div>
        </div>
      </div>

      <!-- FFT 频域副抽屉图 -->
      <div v-if="showFft" class="fft-drawer">
        <div class="fft-header">
          <div class="fft-title">
            <TrendingUp :size="12" />
            <span>FFT 频域谱图 (THD: {{ fftThd.toFixed(2) }}%)</span>
          </div>
          <select v-model="activeFftCh" class="mini-select">
            <option v-for="ch in channels" :key="ch.id" :value="ch.id">
              CH{{ ch.id }} ({{ ch.name }})
            </option>
          </select>
        </div>
        <div class="fft-chart" ref="fftChartRef"></div>
      </div>
    </div>

    <!-- 通道控制与测量仪表盘 -->
    <div class="channels-footer">
      <div
        v-for="ch in channels"
        :key="ch.id"
        class="channel-strip"
        :class="{ active: ch.enabled }"
        :style="{ '--ch-color': ch.color }"
      >
        <div class="ch-header">
          <label class="ch-check">
            <input type="checkbox" v-model="ch.enabled" />
            <span class="color-dot" :style="{ backgroundColor: ch.color }"></span>
            <span class="ch-name">{{ ch.name }}</span>
          </label>
          <span class="ch-val">{{ (channelLastVals[ch.id] ?? 0).toFixed(2) }} {{ ch.unit }}</span>
        </div>

        <!-- 通道数值测量卡 -->
        <div class="ch-metrics">
          <span>RMS: {{ (channelMetrics[ch.id]?.rms ?? 0).toFixed(1) }}</span>
          <span>Pk-Pk: {{ (channelMetrics[ch.id]?.pkpk ?? 0).toFixed(1) }}</span>
        </div>

        <div class="ch-controls">
          <label>
            倍率:
            <input
              type="number"
              step="0.1"
              v-model.number="ch.scale"
              class="mini-input"
            />
          </label>
          <label>
            偏移:
            <input
              type="number"
              step="0.5"
              v-model.number="ch.offset"
              class="mini-input"
            />
          </label>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onBeforeUnmount, watch } from 'vue';
import * as echarts from 'echarts';
import {
  Play,
  Square,
  Trash2,
  TrendingUp,
  Download,
  FileText,
  Crosshair,
  Activity,
  Upload,
  ZoomIn,
  RotateCcw,
  Search,
} from 'lucide-vue-next';
import { api } from '../api';
import { t } from '../i18n';

const props = defineProps({
  streamer: Object,
});

const emit = defineEmits(['toast']);

const chartRef = ref(null);
const fftChartRef = ref(null);
const csvFileInputRef = ref(null);
let myChart = null;
let fftChart = null;

const isPaused = ref(false);
const isSimulating = ref(false);
let simTimer = null;
let simT = 0;

const showFft = ref(false);
const activeFftCh = ref(1);
const fftThd = ref(0.0);
const currentFps = ref(0);
const targetFps = ref(60); // 默认 60 FPS 标准高刷
const timeWindow = ref(2.0); // 内部生效时基秒数 (0 代表全量历史)
const timeWindowPreset = ref(2.0); // 下拉预设选择
const customTimeWindow = ref(2.0); // 直接数值输入的秒数
const isSmoothCurve = ref(false);
const simRate = ref(10000); // 模拟压测灌流速率 (1k ~ 100k Sps)
const AUTO_BUFFER_CAPACITY = 200000; // 自动深度内存管理 (单通道 20 万点)

// 纵轴量程直接控制
const yAxisPreset = ref('pm10'); // 'auto', 'pm5', 'pm10', 'pm15', 'pm24', 'pm50', 'pm100', '0_3v3', '0_5v', '0_24v', '0_380v', 'custom'
const yAxisMin = ref(-10.0);
const yAxisMax = ref(10.0);

// 缩放与脱机细节检查模式控制器
const isUserZooming = ref(false);
const isBoxZoomActive = ref(false);
let isProgrammaticZoom = false;
let zoomedXMin = null;
let zoomedXMax = null;

const minFrameInterval = computed(() => {
  if (targetFps.value <= 0) return 0;
  return 1000 / targetFps.value;
});

// 双光标测量功能
const showCursors = ref(false);
const cursorA = ref(0.0);
const cursorB = ref(0.1);
const cursorChannel = ref(1);

// 8 个标准示波通道配置
const CHANNEL_COLORS = [
  '#3b82f6', // 蓝
  '#10b981', // 绿
  '#f59e0b', // 橙
  '#ef4444', // 红
  '#a855f7', // 紫
  '#06b6d4', // 青
  '#ec4899', // 粉
  '#84cc16', // 荧光绿
];

const channels = reactive(
  Array.from({ length: 8 }, (_, i) => ({
    id: i + 1,
    name: `CH${i + 1}`,
    color: CHANNEL_COLORS[i],
    enabled: i < 4,
    unit: 'V',
    scale: 1.0,
    offset: 0.0,
    axisIndex: i % 2 === 0 ? 0 : 1, // 偶数通道左轴，奇数通道右轴
  }))
);

// 高性能裸数组物理环形缓冲区 (彻底脱离 Vue 3 Proxy 拦截，实现 100,000 点/秒零 GC 级吸纳)
const seriesData = {};
const rawLastVals = {};
const channelLastVals = reactive({});
const channelMetrics = reactive({});
const channelMap = {};

function initChannelStructures() {
  channels.forEach((ch) => {
    channelMap[ch.id] = ch;
    seriesData[ch.id] = [];
    rawLastVals[ch.id] = 0.0;
    channelLastVals[ch.id] = 0.0;
    channelMetrics[ch.id] = { rms: 0, pkpk: 0 };
  });
}
initChannelStructures();

// 计算当前时域波形窗口上下限
const timeMin = computed(() => {
  const buf = seriesData[cursorChannel.value] || [];
  return buf.length > 0 ? buf[0][0] : 0.0;
});
const timeMax = computed(() => {
  const buf = seriesData[cursorChannel.value] || [];
  return buf.length > 0 ? buf[buf.length - 1][0] : 1.0;
});

// 二分搜索与线性插值提取指定时间点的通道幅值
function interpolateValue(chId, targetTime) {
  const buf = seriesData[chId];
  if (!buf || buf.length === 0) return 0.0;
  if (targetTime <= buf[0][0]) return buf[0][1];
  if (targetTime >= buf[buf.length - 1][0]) return buf[buf.length - 1][1];

  let low = 0;
  let high = buf.length - 1;
  while (low <= high) {
    const mid = (low + high) >> 1;
    if (buf[mid][0] < targetTime) {
      low = mid + 1;
    } else {
      high = mid - 1;
    }
  }
  const p0 = buf[Math.max(0, low - 1)];
  const p1 = buf[Math.min(buf.length - 1, low)];
  if (!p0 || !p1 || p1[0] === p0[0]) return (p0 || p1)?.[1] ?? 0.0;
  const alpha = (targetTime - p0[0]) / (p1[0] - p0[0]);
  return p0[1] + alpha * (p1[1] - p0[1]);
}

const cursorValA = computed(() => interpolateValue(cursorChannel.value, cursorA.value));
const cursorValB = computed(() => interpolateValue(cursorChannel.value, cursorB.value));
const deltaT = computed(() => Math.abs(cursorB.value - cursorA.value));
const frequency = computed(() => (deltaT.value > 1e-9 ? 1.0 / deltaT.value : 0.0));

function formatDeltaT(dt) {
  if (dt < 1e-6) return `${(dt * 1e9).toFixed(1)} ns`;
  if (dt < 1e-3) return `${(dt * 1e6).toFixed(2)} µs`;
  if (dt < 1.0) return `${(dt * 1e3).toFixed(2)} ms`;
  return `${dt.toFixed(4)} s`;
}

function formatFrequency(f) {
  if (f >= 1e6) return `${(f / 1e6).toFixed(3)} MHz`;
  if (f >= 1e3) return `${(f / 1e3).toFixed(2)} kHz`;
  return `${f.toFixed(1)} Hz`;
}

// 数据流动标记与高能效自适应调度控制器
let hasNewData = false;
let animationFrameId = null;
let lastRenderTime = 0;
let renderedFrames = 0;
let lastFpsUpdate = performance.now();

function initCharts() {
  if (chartRef.value) {
    myChart = echarts.init(chartRef.value, null, { renderer: 'canvas' });
    const option = {
      backgroundColor: '#0d0e11',
      animation: false,
      grid: {
        top: 25,
        left: 48,
        right: 48,
        bottom: 30,
        borderColor: '#282a32',
      },
      tooltip: {
        trigger: 'axis',
        backgroundColor: '#181a1f',
        borderColor: '#282a32',
        textStyle: { color: '#f3f4f6', fontSize: 11 },
      },
      toolbox: {
        show: false,
        feature: {
          dataZoom: {
            yAxisIndex: [0, 1],
          },
        },
      },
      dataZoom: [
        {
          id: 'dataZoomX',
          type: 'inside',
          xAxisIndex: [0],
          filterMode: 'none',
          zoomOnMouseWheel: true,
          moveOnMouseMove: true,
          preventDefaultMouseMove: false,
        },
        {
          id: 'dataZoomY',
          type: 'inside',
          yAxisIndex: [0, 1],
          filterMode: 'none',
          zoomOnMouseWheel: 'shift',
          moveOnMouseMove: 'shift',
          preventDefaultMouseMove: false,
        },
      ],
      xAxis: {
        type: 'value',
        min: 0,
        max: timeWindow.value > 0 ? timeWindow.value : 2.0,
        splitLine: { show: true, lineStyle: { color: '#1e2028', type: 'dashed' } },
        axisLine: { show: true, lineStyle: { color: '#2e323e' } },
        axisLabel: { color: '#838896', fontSize: 10, formatter: (v) => `${Number(v).toFixed(2)}s` },
      },
      yAxis: [
        {
          type: 'value',
          min: yAxisPreset.value === 'auto' ? null : yAxisMin.value,
          max: yAxisPreset.value === 'auto' ? null : yAxisMax.value,
          scale: yAxisPreset.value === 'auto',
          position: 'left',
          splitLine: { show: true, lineStyle: { color: '#1e2028', type: 'dashed' } },
          axisLine: { show: true, lineStyle: { color: '#2e323e' } },
          axisLabel: { color: '#838896', fontSize: 10, formatter: (v) => `${v}V` },
        },
        {
          type: 'value',
          min: yAxisPreset.value === 'auto' ? null : yAxisMin.value,
          max: yAxisPreset.value === 'auto' ? null : yAxisMax.value,
          scale: yAxisPreset.value === 'auto',
          position: 'right',
          splitLine: { show: false },
          axisLine: { show: true, lineStyle: { color: '#2e323e' } },
          axisLabel: { color: '#838896', fontSize: 10, formatter: (v) => `${v}V` },
        },
      ],
      series: channels.map((ch) => ({
        id: `ch-${ch.id}`,
        name: ch.name,
        type: 'line',
        showSymbol: false,
        smooth: isSmoothCurve.value ? 0.25 : false,
        yAxisIndex: ch.axisIndex,
        lineStyle: { width: 1.5, color: ch.color },
        data: [],
      })),
    };
    myChart.setOption(option);

    myChart.on('dataZoom', (params) => {
      if (isProgrammaticZoom) return;
      isUserZooming.value = true;
      isBoxZoomActive.value = false;

      try {
        if (params.batch && params.batch.length > 0) {
          const item = params.batch.find((b) => b.dataZoomId === 'dataZoomX' || b.xAxisIndex === 0) || params.batch[0];
          if (item.startValue !== undefined && item.endValue !== undefined) {
            zoomedXMin = Math.min(item.startValue, item.endValue);
            zoomedXMax = Math.max(item.startValue, item.endValue);
          }
        } else if (params.startValue !== undefined && params.endValue !== undefined) {
          zoomedXMin = Math.min(params.startValue, params.endValue);
          zoomedXMax = Math.max(params.startValue, params.endValue);
        }

        if (zoomedXMin === null || zoomedXMax === null) {
          const axis = myChart?.getModel()?.getComponent('xAxis', 0)?.axis;
          if (axis?.scale) {
            const extent = axis.scale.getExtent();
            if (extent && extent.length === 2 && !isNaN(extent[0]) && !isNaN(extent[1])) {
              zoomedXMin = extent[0];
              zoomedXMax = extent[1];
            }
          }
        }
      } catch (_) {}
    });

    myChart.getZr().on('click', (params) => {
      if (!showCursors.value || !myChart) return;
      const pointInPixel = [params.offsetX, params.offsetY];
      if (myChart.containPixel('grid', pointInPixel)) {
        const pointInGrid = myChart.convertFromPixel('grid', pointInPixel);
        const clickedTime = pointInGrid[0];
        const distA = Math.abs(clickedTime - cursorA.value);
        const distB = Math.abs(clickedTime - cursorB.value);
        if (distA <= distB) {
          cursorA.value = clickedTime;
        } else {
          cursorB.value = clickedTime;
        }
      }
    });
  }
}

function toggleBoxZoom() {
  isBoxZoomActive.value = !isBoxZoomActive.value;
  if (myChart) {
    myChart.dispatchAction({
      type: 'takeGlobalCursor',
      key: 'dataZoomSelect',
      dataZoomSelectActive: isBoxZoomActive.value,
    });
  }
  if (isBoxZoomActive.value) {
    emit('toast', t('wave.boxZoomTip'), 'info');
  }
}

function resetZoomAndResume() {
  isUserZooming.value = false;
  isBoxZoomActive.value = false;
  zoomedXMin = null;
  zoomedXMax = null;

  if (myChart) {
    myChart.dispatchAction({
      type: 'takeGlobalCursor',
      key: 'dataZoomSelect',
      dataZoomSelectActive: false,
    });

    isProgrammaticZoom = true;
    try {
      myChart.dispatchAction({
        type: 'dataZoom',
        dataZoomId: 'dataZoomX',
        start: 0,
        end: 100,
      });
      myChart.dispatchAction({
        type: 'dataZoom',
        dataZoomId: 'dataZoomY',
        start: 0,
        end: 100,
      });
    } catch (_) {}
    setTimeout(() => {
      isProgrammaticZoom = false;
    }, 50);

    applyYAxis();

    if (isPaused.value) {
      const tw = timeWindow.value > 0 ? timeWindow.value : 2.0;
      let latestT = 0;
      for (let i = 0; i < channels.length; i++) {
        const buf = seriesData[channels[i].id];
        if (buf && buf.length > 0) {
          const t = buf[buf.length - 1][0];
          if (t > latestT) latestT = t;
        }
      }
      const xMin = Math.max(0, latestT - tw);
      const xMax = Math.max(tw, latestT);
      myChart.setOption({
        xAxis: { min: xMin, max: xMax },
        series: channels.map((ch) => ({
          id: `ch-${ch.id}`,
          data: ch.enabled ? getWindowedDownsampledData(ch.id, xMin, xMax) : [],
        })),
      }, false, true);
    }
  }
  emit('toast', t('wave.resetZoomTip'), 'info');
}

function onTimeWindowPresetChange() {
  if (timeWindowPreset.value === 'custom') {
    timeWindow.value = Number(customTimeWindow.value) || 2.0;
  } else {
    const val = Number(timeWindowPreset.value);
    timeWindow.value = val;
    if (val > 0) {
      customTimeWindow.value = val;
    }
  }
  if (isUserZooming.value) {
    resetZoomAndResume();
  }
}

function onCustomTimeWindowChange() {
  const val = parseFloat(customTimeWindow.value);
  if (isNaN(val) || val <= 0) {
    customTimeWindow.value = 2.0;
    timeWindow.value = 2.0;
    timeWindowPreset.value = 2.0;
    emit('toast', '时基秒数必须大于 0', 'error');
    return;
  }
  timeWindow.value = val;
  const STANDARD_PRESETS = [0.05, 0.1, 0.2, 0.5, 1.0, 2.0, 5.0, 10.0];
  if (STANDARD_PRESETS.includes(val)) {
    timeWindowPreset.value = val;
  } else {
    timeWindowPreset.value = 'custom';
  }
  if (isUserZooming.value) {
    resetZoomAndResume();
  }
}

function onYAxisPresetChange() {
  switch (yAxisPreset.value) {
    case 'auto':
      break;
    case 'pm5':
      yAxisMin.value = -5;
      yAxisMax.value = 5;
      break;
    case 'pm10':
      yAxisMin.value = -10;
      yAxisMax.value = 10;
      break;
    case 'pm15':
      yAxisMin.value = -15;
      yAxisMax.value = 15;
      break;
    case 'pm24':
      yAxisMin.value = -24;
      yAxisMax.value = 24;
      break;
    case 'pm50':
      yAxisMin.value = -50;
      yAxisMax.value = 50;
      break;
    case 'pm100':
      yAxisMin.value = -100;
      yAxisMax.value = 100;
      break;
    case '0_3v3':
      yAxisMin.value = 0;
      yAxisMax.value = 3.3;
      break;
    case '0_5v':
      yAxisMin.value = 0;
      yAxisMax.value = 5.0;
      break;
    case '0_24v':
      yAxisMin.value = 0;
      yAxisMax.value = 24.0;
      break;
    case '0_380v':
      yAxisMin.value = 0;
      yAxisMax.value = 380.0;
      break;
    case 'custom':
      return;
  }
  applyYAxis();
}

function onCustomYAxisChange() {
  const minVal = parseFloat(yAxisMin.value);
  const maxVal = parseFloat(yAxisMax.value);
  if (isNaN(minVal) || isNaN(maxVal)) {
    emit('toast', '请输入有效的数值量程', 'error');
    return;
  }
  if (minVal >= maxVal) {
    emit('toast', '纵轴最小值 (Min) 必须小于最大值 (Max)', 'error');
    return;
  }
  yAxisPreset.value = 'custom';
  applyYAxis();
}

function applyYAxis() {
  if (!myChart) return;
  if (yAxisPreset.value === 'auto') {
    myChart.setOption({
      yAxis: [
        { min: null, max: null, scale: true },
        { min: null, max: null, scale: true },
      ],
    }, false, true);
  } else {
    const minVal = Number(yAxisMin.value);
    const maxVal = Number(yAxisMax.value);
    if (!isNaN(minVal) && !isNaN(maxVal) && minVal < maxVal) {
      myChart.setOption({
        yAxis: [
          { min: minVal, max: maxVal, scale: false },
          { min: minVal, max: maxVal, scale: false },
        ],
      }, false, true);
    }
  }
}

function getMarkLineOption() {
  if (!showCursors.value) return undefined;
  return {
    symbol: 'none',
    silent: true,
    animation: false,
    data: [
      {
        name: 'Cursor A',
        xAxis: cursorA.value,
        lineStyle: { color: '#f59e0b', type: 'solid', width: 1.5 },
        label: {
          show: true,
          position: 'insideEndTop',
          formatter: `A: ${cursorA.value.toFixed(3)}s`,
          backgroundColor: 'rgba(245, 158, 11, 0.25)',
          padding: [2, 4],
          borderRadius: 2,
          color: '#f59e0b',
        },
      },
      {
        name: 'Cursor B',
        xAxis: cursorB.value,
        lineStyle: { color: '#38bdf8', type: 'solid', width: 1.5 },
        label: {
          show: true,
          position: 'insideEndTop',
          formatter: `B: ${cursorB.value.toFixed(3)}s`,
          backgroundColor: 'rgba(56, 189, 248, 0.25)',
          padding: [2, 4],
          borderRadius: 2,
          color: '#38bdf8',
        },
      },
    ],
  };
}

function initFftChart() {
  if (fftChartRef.value) {
    fftChart = echarts.init(fftChartRef.value, null, { renderer: 'canvas' });
    fftChart.setOption({
      backgroundColor: '#0a0a0c',
      animation: false,
      grid: { top: 20, left: 40, right: 20, bottom: 25 },
      xAxis: {
        type: 'value',
        name: 'Hz',
        splitLine: { lineStyle: { color: '#1a1c22' } },
        axisLabel: { color: '#838896', fontSize: 9 },
      },
      yAxis: {
        type: 'value',
        splitLine: { lineStyle: { color: '#1a1c22' } },
        axisLabel: { color: '#838896', fontSize: 9 },
      },
      series: [
        {
          type: 'line',
          showSymbol: false,
          areaStyle: { color: 'rgba(59, 130, 246, 0.2)' },
          lineStyle: { width: 1.2, color: '#3b82f6' },
          data: [],
        },
      ],
    });
  }
}

function onNewDataPoint(t, chId, val) {
  if (isPaused.value) return;

  const ch = channelMap[chId];
  if (!ch) return;

  const finalVal = val * ch.scale + ch.offset;
  const buf = seriesData[chId];
  if (buf) {
    buf.push([t, finalVal]);
  }
  rawLastVals[chId] = finalVal;
  hasNewData = true;

  if (showCursors.value && cursorA.value === 0 && cursorB.value === 0.1 && buf && buf.length > 50) {
    const startT = buf[0][0];
    const endT = buf[buf.length - 1][0];
    const span = endT - startT;
    cursorA.value = startT + span * 0.3;
    cursorB.value = startT + span * 0.7;
  }
}

function onNewDataBatch(dv, totalPoints) {
  if (isPaused.value) return;
  const POINT_SIZE = 14;

  for (let i = 0; i < totalPoints; i++) {
    const offset = i * POINT_SIZE;
    const t = dv.getFloat64(offset, true);
    const chId = dv.getUint16(offset + 8, true);
    const val = dv.getFloat32(offset + 10, true);

    const ch = channelMap[chId];
    if (!ch) continue;

    const finalVal = val * ch.scale + ch.offset;
    const buf = seriesData[chId];
    if (buf) {
      buf.push([t, finalVal]);
    }
    rawLastVals[chId] = finalVal;
  }
  hasNewData = true;
}

function getDownsampledDisplayData(raw, startIdx = 0, endIdx = -1) {
  if (!raw || raw.length === 0) return [];
  if (endIdx < 0 || endIdx >= raw.length) endIdx = raw.length - 1;
  if (endIdx < startIdx) return [];

  const len = endIdx - startIdx + 1;
  const TARGET_POINTS = 1600;
  if (len <= TARGET_POINTS) {
    return raw.slice(startIdx, endIdx + 1);
  }

  const result = [];
  const buckets = TARGET_POINTS / 2;
  const bucketSize = len / buckets;

  for (let b = 0; b < buckets; b++) {
    const bStart = startIdx + Math.floor(b * bucketSize);
    const bEnd = Math.min(startIdx + len, startIdx + Math.floor((b + 1) * bucketSize));
    if (bStart >= bEnd) continue;

    let minPt = raw[bStart];
    let maxPt = raw[bStart];
    let minIdx = bStart;
    let maxIdx = bStart;

    for (let i = bStart + 1; i < bEnd; i++) {
      const pt = raw[i];
      if (pt[1] < minPt[1]) {
        minPt = pt;
        minIdx = i;
      }
      if (pt[1] > maxPt[1]) {
        maxPt = pt;
        maxIdx = i;
      }
    }

    if (minIdx <= maxIdx) {
      result.push(minPt);
      if (maxIdx !== minIdx) result.push(maxPt);
    } else {
      result.push(maxPt);
      if (maxIdx !== minIdx) result.push(minPt);
    }
  }
  return result;
}

function getWindowedDownsampledData(chId, xMin, xMax) {
  const raw = seriesData[chId];
  if (!raw || raw.length === 0) return [];

  if (xMin === undefined || xMax === undefined || (timeWindow.value === 0 && !isUserZooming.value)) {
    return getDownsampledDisplayData(raw, 0, raw.length - 1);
  }

  const targetStart = xMin - 0.05;
  let startIdx = 0;
  let low = 0, high = raw.length - 1;
  while (low <= high) {
    const mid = (low + high) >> 1;
    if (raw[mid][0] >= targetStart) {
      startIdx = mid;
      high = mid - 1;
    } else {
      low = mid + 1;
    }
  }

  const targetEnd = xMax + 0.05;
  let endIdx = raw.length - 1;
  low = startIdx; high = raw.length - 1;
  while (low <= high) {
    const mid = (low + high) >> 1;
    if (raw[mid][0] <= targetEnd) {
      endIdx = mid;
      low = mid + 1;
    } else {
      high = mid - 1;
    }
  }

  if (endIdx < startIdx) return [];
  return getDownsampledDisplayData(raw, startIdx, endIdx);
}

function renderLoop(timestamp) {
  animationFrameId = requestAnimationFrame(renderLoop);

  if (timestamp - lastFpsUpdate >= 1000) {
    currentFps.value = renderedFrames;
    renderedFrames = 0;
    lastFpsUpdate = timestamp;

    channels.forEach((ch) => {
      const buf = seriesData[ch.id];
      if (buf && buf.length > AUTO_BUFFER_CAPACITY + 5000) {
        buf.splice(0, buf.length - AUTO_BUFFER_CAPACITY);
      }
    });

    channels.forEach((ch) => {
      const data = seriesData[ch.id];
      if (data && data.length > 20) {
        let sumSq = 0;
        let min = Infinity;
        let max = -Infinity;
        const slice = data.slice(-200);
        for (let i = 0; i < slice.length; i++) {
          const v = slice[i][1];
          sumSq += v * v;
          if (v < min) min = v;
          if (v > max) max = v;
        }
        channelMetrics[ch.id] = {
          rms: Math.sqrt(sumSq / slice.length),
          pkpk: max - min,
        };
      }
    });

    if (showFft.value) {
      triggerFftUpdate();
    }
  }

  const minInterval = minFrameInterval.value;
  if (hasNewData && !isPaused.value && (minInterval === 0 || timestamp - lastRenderTime >= minInterval)) {
    lastRenderTime = timestamp;
    hasNewData = false;
    renderedFrames++;

    for (const chId in rawLastVals) {
      channelLastVals[chId] = rawLastVals[chId];
    }

    if (myChart) {
      let latestT = 0;
      for (let i = 0; i < channels.length; i++) {
        const ch = channels[i];
        if (ch.enabled && seriesData[ch.id]?.length > 0) {
          const lastPt = seriesData[ch.id][seriesData[ch.id].length - 1];
          if (lastPt[0] > latestT) latestT = lastPt[0];
        }
      }

      if (isUserZooming.value) {
        const seriesUpdate = channels.map((ch) => ({
          id: `ch-${ch.id}`,
          data: ch.enabled ? getWindowedDownsampledData(ch.id, zoomedXMin, zoomedXMax) : [],
        }));
        myChart.setOption({ series: seriesUpdate }, false, true);
      } else {
        const tw = timeWindow.value;
        let xMin, xMax;
        if (tw > 0) {
          xMin = Math.max(0, latestT - tw);
          xMax = Math.max(tw, latestT);
        } else {
          xMin = seriesData[1]?.[0]?.[0] ?? 0;
          xMax = Math.max(1.0, latestT);
        }

        const seriesUpdate = channels.map((ch) => ({
          id: `ch-${ch.id}`,
          data: ch.enabled ? getWindowedDownsampledData(ch.id, xMin, xMax) : [],
        }));

        myChart.setOption({
          xAxis: { min: xMin, max: xMax },
          series: seriesUpdate,
        }, false, true);
      }
    }
  }
}

function updateCursorMarkLine() {
  if (myChart) {
    myChart.setOption({
      series: [
        {
          id: `ch-${channels[0].id}`,
          markLine: getMarkLineOption(),
        },
      ],
    }, false, true);
  }
}
watch([cursorA, cursorB, showCursors, cursorChannel], updateCursorMarkLine);

watch(channels, () => {
  hasNewData = true;
}, { deep: true });

async function triggerFftUpdate() {
  const buf = seriesData[activeFftCh.value];
  if (!buf || buf.length < 64) return;

  const tArr = buf.map((p) => p[0]);
  const dArr = buf.map((p) => p[1]);

  try {
    const res = await api.computeFft(tArr, dArr);
    if (res.status === 'success' && fftChart) {
      fftThd.value = res.thd || 0.0;
      const pts = res.frequencies.map((f, i) => [f, res.amplitudes[i]]);
      fftChart.setOption({ series: [{ data: pts }] }, false, true);
    }
  } catch (_) {}
}

function toggleSmoothCurve() {
  isSmoothCurve.value = !isSmoothCurve.value;
  if (myChart) {
    myChart.setOption({
      series: channels.map((ch) => ({
        id: `ch-${ch.id}`,
        smooth: isSmoothCurve.value ? 0.25 : false,
      })),
    }, false, true);
  }
  emit('toast', isSmoothCurve.value ? '已开启样条平滑插值 (连续模拟平滑波形)' : '已切换为原始离散采样折线', 'info');
}

function toggleSimulation() {
  isSimulating.value = !isSimulating.value;
  if (isSimulating.value) {
    isPaused.value = false;

    const rate = simRate.value || 10000;
    const dt = 1.0 / rate;
    const pointsPerTick = Math.max(1, Math.round(rate / 60));

    const lastT = Math.max(0, seriesData[1]?.at(-1)?.[0] ?? 0);
    simT = lastT > 0 ? lastT : 0;

    for (let i = 0; i < Math.min(200, pointsPerTick); i++) {
      simT += dt;
      const v1 = 5.0 * Math.sin(2 * Math.PI * 50 * simT);
      const v2 = Math.sin(2 * Math.PI * 100 * simT) >= 0 ? 3.3 : 0.0;
      const phase = (simT * 20) % 1.0;
      const v3 = (phase < 0.5 ? phase * 4 - 1 : 3 - phase * 4) * 2.5;
      const v4 = 12.0 + 0.3 * Math.sin(2 * Math.PI * 200 * simT);

      onNewDataPoint(simT, 1, v1);
      onNewDataPoint(simT, 2, v2);
      onNewDataPoint(simT, 3, v3);
      onNewDataPoint(simT, 4, v4);
    }
    hasNewData = true;

    simTimer = setInterval(() => {
      if (isPaused.value) return;
      const b1 = seriesData[1];
      const b2 = seriesData[2];
      const b3 = seriesData[3];
      const b4 = seriesData[4];
      let lastV1 = 0, lastV2 = 0, lastV3 = 0, lastV4 = 0;

      for (let i = 0; i < pointsPerTick; i++) {
        simT += dt;
        lastV1 = 5.0 * Math.sin(2 * Math.PI * 50 * simT);
        lastV2 = Math.sin(2 * Math.PI * 100 * simT) >= 0 ? 3.3 : 0.0;
        const phase = (simT * 20) % 1.0;
        lastV3 = (phase < 0.5 ? phase * 4 - 1 : 3 - phase * 4) * 2.5;
        lastV4 = 12.0 + 0.3 * Math.sin(2 * Math.PI * 200 * simT);

        if (b1) b1.push([simT, lastV1]);
        if (b2) b2.push([simT, lastV2]);
        if (b3) b3.push([simT, lastV3]);
        if (b4) b4.push([simT, lastV4]);
      }
      rawLastVals[1] = lastV1;
      rawLastVals[2] = lastV2;
      rawLastVals[3] = lastV3;
      rawLastVals[4] = lastV4;
      hasNewData = true;
    }, 16);

    emit('toast', `已启动下位机 ${rate >= 1000 ? (rate / 1000) + 'kSps' : rate + 'Sps'} 高频数据流压测 (每秒 ${rate * 4} 点并发灌流)`, 'info');
  } else {
    if (simTimer) {
      clearInterval(simTimer);
      simTimer = null;
    }
    emit('toast', '已停止高速硬件灌流压测', 'info');
  }
}

function togglePause() {
  isPaused.value = !isPaused.value;
  emit('toast', isPaused.value ? '示波器已暂停冻结 (可滚轮缩放与滑条漫游历史)' : '示波器继续实时运行', 'info');

  if (myChart) {
    if (isPaused.value) {
      myChart.setOption({
        dataZoom: [
          { id: 'dataZoomX', type: 'inside', disabled: false },
          { id: 'dataZoomY', type: 'inside', disabled: false },
          {
            id: 'dataZoomSlider',
            type: 'slider',
            xAxisIndex: [0],
            show: true,
            bottom: 2,
            height: 18,
            borderColor: '#282a32',
            fillerColor: 'rgba(59, 130, 246, 0.25)',
            textStyle: { color: '#838896', fontSize: 10 },
          },
        ],
      }, false, true);
    } else {
      myChart.setOption({
        dataZoom: [
          { id: 'dataZoomX', type: 'inside', disabled: false },
          { id: 'dataZoomY', type: 'inside', disabled: false },
          { id: 'dataZoomSlider', type: 'slider', show: false },
        ],
      }, false, true);
    }
  }
}

function clearData() {
  channels.forEach((ch) => {
    seriesData[ch.id] = [];
    channelLastVals[ch.id] = 0.0;
    channelMetrics[ch.id] = { rms: 0, pkpk: 0 };
  });
  if (myChart) {
    myChart.setOption({
      xAxis: { min: 0, max: timeWindow.value > 0 ? timeWindow.value : 2.0 },
      series: channels.map((ch) => ({ id: `ch-${ch.id}`, data: [] })),
    });
  }
  simT = 0;
  hasNewData = false;
  isUserZooming.value = false;
  emit('toast', '波形缓冲区已全部清空', 'info');
}

function triggerCsvImport() {
  if (csvFileInputRef.value) {
    csvFileInputRef.value.click();
  }
}

function handleCsvFileImport(e) {
  const file = e.target.files?.[0];
  if (!file) return;

  const reader = new FileReader();
  reader.onload = (evt) => {
    try {
      const text = evt.target.result;
      parseAndLoadCsv(text, file.name);
    } catch (err) {
      emit('toast', `CSV 解析失败: ${err.message}`, 'error');
    }
    e.target.value = '';
  };
  reader.readAsText(file);
}

function parseAndLoadCsv(text, filename) {
  const lines = text.split(/\r?\n/).map((l) => l.trim()).filter((l) => l.length > 0);
  if (lines.length === 0) {
    emit('toast', 'CSV 文件内容为空！', 'error');
    return;
  }

  channels.forEach((ch) => {
    seriesData[ch.id] = [];
    channelLastVals[ch.id] = 0.0;
  });
  isPaused.value = true;
  if (isSimulating.value) {
    toggleSimulation();
  }

  const firstLine = lines[0];
  let sep = ',';
  if (firstLine.includes('\t')) sep = '\t';
  else if (firstLine.includes(';') && !firstLine.includes(',')) sep = ';';

  let startLineIdx = 0;
  const headerCols = lines[0].split(sep).map((c) => c.trim().replace(/^["']|["']$/g, ''));
  const isFirstColNumeric = !isNaN(parseFloat(headerCols[0]));

  let isLongFormat = false;
  if (!isFirstColNumeric) {
    startLineIdx = 1;
    const lowerCols = headerCols.map((c) => c.toLowerCase());
    if (lowerCols.includes('channel_id') || lowerCols.includes('channel') || lowerCols.includes('chid')) {
      isLongFormat = true;
    }
  }

  let totalParsed = 0;
  let tMin = Infinity;
  let tMax = -Infinity;

  if (isLongFormat) {
    for (let i = startLineIdx; i < lines.length; i++) {
      const parts = lines[i].split(sep).map((p) => p.trim());
      if (parts.length < 3) continue;
      const t = parseFloat(parts[0]);
      const ch = parseInt(parts[1]);
      const v = parseFloat(parts[2]);
      if (isNaN(t) || isNaN(ch) || isNaN(v)) continue;
      if (ch >= 1 && ch <= 8) {
        if (!seriesData[ch]) seriesData[ch] = [];
        seriesData[ch].push([t, v]);
        totalParsed++;
        if (t < tMin) tMin = t;
        if (t > tMax) tMax = t;
      }
    }
  } else {
    for (let i = startLineIdx; i < lines.length; i++) {
      const parts = lines[i].split(sep).map((p) => p.trim());
      if (parts.length === 0) continue;

      let t = parseFloat(parts[0]);
      let colOffset = 1;
      if (isNaN(t)) {
        t = (i - startLineIdx) * 0.001;
        colOffset = 0;
      }

      for (let c = colOffset; c < parts.length && c - colOffset < 8; c++) {
        const val = parseFloat(parts[c]);
        const chId = c - colOffset + 1;
        if (!isNaN(val)) {
          if (!seriesData[chId]) seriesData[chId] = [];
          seriesData[chId].push([t, val]);
          totalParsed++;
          if (t < tMin) tMin = t;
          if (t > tMax) tMax = t;
        }
      }
    }
  }

  if (totalParsed === 0) {
    emit('toast', '未解析出有效数值波形点！', 'error');
    return;
  }

  channels.forEach((ch) => {
    const d = seriesData[ch.id] || [];
    ch.enabled = d.length > 0;
    if (d.length > 0) {
      channelLastVals[ch.id] = d[d.length - 1][1];
      let sumSq = 0, minV = Infinity, maxV = -Infinity;
      for (let k = 0; k < d.length; k++) {
        const v = d[k][1];
        sumSq += v * v;
        if (v < minV) minV = v;
        if (v > maxV) maxV = v;
      }
      channelMetrics[ch.id] = {
        rms: Math.sqrt(sumSq / d.length),
        pkpk: maxV - minV,
      };
    }
  });

  if (!isFinite(tMin) || !isFinite(tMax) || tMin >= tMax) {
    tMin = 0.0;
    tMax = 1.0;
  }

  const span = tMax - tMin;
  cursorA.value = tMin + span * 0.3;
  cursorB.value = tMin + span * 0.7;

  timeWindow.value = 0;
  timeWindowPreset.value = 0;
  hasNewData = false;

  if (myChart) {
    const seriesUpdate = channels.map((ch) => ({
      id: `ch-${ch.id}`,
      data: ch.enabled ? getDownsampledDisplayData(seriesData[ch.id]) : [],
    }));
    myChart.setOption({
      xAxis: { min: tMin, max: tMax },
      series: seriesUpdate,
      dataZoom: [
        { id: 'dataZoomX', type: 'inside', disabled: false },
        { id: 'dataZoomY', type: 'inside', disabled: false },
        {
          id: 'dataZoomSlider',
          type: 'slider',
          xAxisIndex: [0],
          show: true,
          bottom: 2,
          height: 18,
          borderColor: '#282a32',
          fillerColor: 'rgba(59, 130, 246, 0.25)',
          textStyle: { color: '#838896', fontSize: 10 },
        },
      ],
    }, false, false);
  }

  emit('toast', `成功导入 CSV (${filename}): 共 ${totalParsed} 点 [${tMin.toFixed(3)}s ~ ${tMax.toFixed(3)}s]`, 'success');
}

function exportCsv() {
  const lines = ['Time,CH1,CH2,CH3,CH4,CH5,CH6,CH7,CH8'];
  const maxLen = Math.max(...Object.values(seriesData).map((s) => s.length));
  if (maxLen === 0) {
    emit('toast', '暂无波形数据可导出！', 'error');
    return;
  }

  const refBuf = seriesData[1] || [];
  for (let i = 0; i < refBuf.length; i++) {
    const t = refBuf[i][0];
    const row = [t.toFixed(6)];
    for (let c = 1; c <= 8; c++) {
      const pt = seriesData[c]?.[i];
      row.push(pt ? pt[1].toFixed(4) : '');
    }
    lines.push(row.join(','));
  }

  const blob = new Blob([lines.join('\n')], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `waveform_${Date.now()}.csv`;
  a.click();
  URL.revokeObjectURL(url);
  emit('toast', '波形数据已成功导出为 CSV 文件', 'success');
}

async function exportMat() {
  const payload = {
    channels: channels
      .filter((c) => c.enabled && seriesData[c.id]?.length > 0)
      .map((c) => ({
        id: c.id,
        name: c.name,
        unit: c.unit,
        scale: c.scale,
        offset: c.offset,
        x: seriesData[c.id].map((p) => p[0]),
        y: seriesData[c.id].map((p) => p[1]),
      })),
  };
  if (payload.channels.length === 0) {
    emit('toast', '暂无有效数据通道可导出！', 'error');
    return;
  }
  try {
    const res = await fetch(`${api.API_BASE || ''}/api/export/mat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `waveform_${Date.now()}.mat`;
    a.click();
    URL.revokeObjectURL(url);
    emit('toast', '波形数据已成功导出为 MAT 文件', 'success');
  } catch (e) {
    emit('toast', `导出 MAT 失败: ${e.message}`, 'error');
  }
}

function handleResize() {
  if (myChart) myChart.resize();
  if (fftChart) fftChart.resize();
}

watch(showFft, (val) => {
  if (val) {
    setTimeout(() => initFftChart(), 50);
  } else if (fftChart) {
    fftChart.dispose();
    fftChart = null;
  }
});

defineExpose({
  togglePause,
  clearData,
  toggleSimulation,
  isPaused,
  isSimulating,
});

onMounted(() => {
  initCharts();
  window.addEventListener('resize', handleResize);

  if (props.streamer) {
    props.streamer.on('onPointsBatch', onNewDataBatch);
    props.streamer.on('onPoint', onNewDataPoint);
  }

  animationFrameId = requestAnimationFrame(renderLoop);
});

onBeforeUnmount(() => {
  if (simTimer) clearInterval(simTimer);
  if (animationFrameId) cancelAnimationFrame(animationFrameId);
  window.removeEventListener('resize', handleResize);
  if (myChart) myChart.dispose();
  if (fftChart) fftChart.dispose();
});
</script>

<style scoped>
.waveform-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
  background-color: var(--bg-app);
}

.chart-toolbar {
  min-height: 38px;
  background-color: var(--bg-sidebar);
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 12px;
  flex-shrink: 0;
  user-select: none;
  overflow-x: auto;
  overflow-y: hidden;
  scrollbar-width: none;
}
.chart-toolbar::-webkit-scrollbar {
  display: none;
}

.toolbar-left, .toolbar-right {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}
.toolbar-divider {
  width: 1px;
  height: 16px;
  background: var(--border);
  margin: 0 3px;
}
.kbd-hint {
  font-size: 9px;
  font-family: var(--font-mono);
  background: rgba(0, 0, 0, 0.25);
  padding: 1px 4px;
  border-radius: 3px;
  color: var(--text-dim);
  margin-left: 2px;
}

.pulse-anim {
  animation: pulse-glow 1.5s infinite;
}
@keyframes pulse-glow {
  0% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.6); }
  70% { box-shadow: 0 0 0 8px rgba(16, 185, 129, 0); }
  100% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
}

.fps-badge {
  font-size: 11px;
  font-family: var(--font-mono);
  color: var(--text-muted);
  background: rgba(255, 255, 255, 0.04);
  padding: 2px 8px;
  border-radius: 4px;
  border: 1px solid var(--border-light);
  display: flex;
  align-items: center;
  gap: 5px;
}

.picker-group {
  display: flex;
  align-items: center;
}
.mini-select {
  background: rgba(0, 0, 0, 0.35);
  color: var(--accent);
  border: 1px solid var(--border-light);
  border-radius: 4px;
  padding: 2px 6px;
  font-size: 11px;
  font-family: var(--font-mono);
  font-weight: 500;
  cursor: pointer;
  outline: none;
  transition: all 0.15s ease;
}
.mini-select:hover, .mini-select:focus {
  border-color: var(--accent);
  background: rgba(0, 0, 0, 0.5);
}
.mini-select option {
  background: #181a1f;
  color: #f3f4f6;
}
.time-select {
  color: #10b981;
}
.range-select {
  color: #f59e0b;
}

/* 轴直接设定控制组 */
.axis-control-group {
  display: flex;
  align-items: center;
  gap: 4px;
  background: rgba(0, 0, 0, 0.25);
  border: 1px solid var(--border-light);
  border-radius: 4px;
  padding: 2px 6px;
}
.axis-label {
  font-size: 10px;
  color: var(--text-muted);
  white-space: nowrap;
  font-weight: 500;
}
.direct-input-wrap {
  display: flex;
  align-items: center;
  gap: 3px;
}
.mini-input-number {
  width: 44px;
  height: 20px;
  background: rgba(0, 0, 0, 0.4);
  border: 1px solid var(--border-light);
  border-radius: 3px;
  color: #38bdf8;
  font-family: var(--font-mono);
  font-size: 10px;
  text-align: center;
  padding: 0 2px;
  outline: none;
  transition: border-color 0.15s ease;
}
.mini-input-number:focus {
  border-color: var(--accent);
}
.mini-input-number:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
.mini-input-number.y-min {
  color: #f59e0b;
}
.mini-input-number.y-max {
  color: #10b981;
}
.unit-suffix {
  font-size: 10px;
  color: var(--text-dim);
  font-family: var(--font-mono);
}
.range-sep {
  font-size: 10px;
  color: var(--text-dim);
}

.chart-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  position: relative;
  min-height: 0;
}
.echarts-wrapper {
  flex: 1;
  width: 100%;
  min-height: 0;
}

/* 局部放大与后台持续缓冲悬浮横条 */
.zoom-active-banner {
  position: absolute;
  top: 8px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 25;
  background: rgba(18, 24, 38, 0.92);
  backdrop-filter: blur(8px);
  border: 1px solid rgba(59, 130, 246, 0.5);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.5), 0 0 10px rgba(59, 130, 246, 0.2);
  border-radius: 20px;
  padding: 4px 12px;
  display: flex;
  align-items: center;
  gap: 12px;
  user-select: none;
  animation: banner-slide-down 0.2s ease-out;
}
@keyframes banner-slide-down {
  from { opacity: 0; transform: translate(-50%, -10px); }
  to { opacity: 1; transform: translate(-50%, 0); }
}
.zoom-banner-left {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
}
.zoom-icon-pulse {
  color: #38bdf8;
  animation: pulse-glow 1.5s infinite;
}
.zoom-banner-text {
  color: #f3f4f6;
  font-weight: 600;
}
.zoom-banner-tip {
  color: var(--text-dim);
  font-size: 10px;
}
.btn-resume {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  background: #2563eb;
  color: #ffffff;
  border: none;
  border-radius: 12px;
  padding: 2px 10px;
  font-size: 11px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s ease;
}
.btn-resume:hover {
  background: #1d4ed8;
  box-shadow: 0 0 8px rgba(37, 99, 235, 0.6);
}

/* 双测量光标 HUD 浮层 */
.cursor-hud {
  position: absolute;
  top: 10px;
  right: 12px;
  background: rgba(18, 20, 24, 0.88);
  backdrop-filter: blur(8px);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: 8px 12px;
  box-shadow: var(--shadow-lg);
  z-index: 20;
  min-width: 260px;
}
.cursor-hud-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
  padding-bottom: 6px;
  border-bottom: 1px solid var(--border);
}
.hud-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  font-weight: 600;
  color: var(--text-main);
}
.hud-channel-sel {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 10px;
  color: var(--text-muted);
}
.hud-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  margin-bottom: 8px;
}
.hud-card {
  padding: 6px 8px;
  border-radius: var(--radius-sm);
  background: rgba(0, 0, 0, 0.25);
  border: 1px solid var(--border);
}
.card-a { border-left: 3px solid #f59e0b; }
.card-b { border-left: 3px solid #38bdf8; }
.hud-tag {
  font-size: 9px;
  font-weight: bold;
  text-transform: uppercase;
  margin-bottom: 2px;
}
.card-a .hud-tag { color: #f59e0b; }
.card-b .hud-tag { color: #38bdf8; }
.hud-val {
  font-size: 11px;
  font-family: var(--font-mono);
  color: var(--text-main);
  line-height: 1.3;
}
.hud-delta {
  background: rgba(0, 0, 0, 0.35);
  border-radius: var(--radius-sm);
  padding: 6px 8px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}
.delta-item {
  display: flex;
  flex-direction: column;
}
.delta-label {
  font-size: 9px;
  color: var(--text-dim);
}
.delta-value {
  font-size: 11px;
  font-family: var(--font-mono);
  color: var(--text-main);
}
.delta-value.highlight {
  color: #10b981;
  font-weight: 700;
}
.hud-sliders {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.slider-row {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 10px;
  color: var(--text-muted);
}
.slider-row input[type='range'] {
  flex: 1;
  height: 4px;
  accent-color: var(--accent);
}

/* FFT 抽屉 */
.fft-drawer {
  height: 180px;
  border-top: 1px solid var(--border);
  background-color: #0d0e11;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}
.fft-header {
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 12px;
  background-color: rgba(0, 0, 0, 0.2);
  border-bottom: 1px solid var(--border);
}
.fft-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  color: var(--text-muted);
}
.fft-chart {
  flex: 1;
  width: 100%;
}

/* 通道控制栏 */
.channels-footer {
  height: 62px;
  background-color: var(--bg-sidebar);
  border-top: 1px solid var(--border);
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0 12px;
  overflow-x: auto;
  flex-shrink: 0;
}
.channel-strip {
  display: flex;
  flex-direction: column;
  gap: 3px;
  padding: 5px 8px;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  min-width: 145px;
  transition: all 0.15s ease;
  border-left: 3px solid var(--ch-color);
}
.channel-strip.active {
  background: rgba(255, 255, 255, 0.03);
}
.ch-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.ch-check {
  display: flex;
  align-items: center;
  gap: 5px;
  cursor: pointer;
  font-weight: 600;
  font-size: 11px;
}
.color-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}
.ch-name {
  color: var(--text-main);
}
.ch-val {
  font-size: 11px;
  font-family: var(--font-mono);
  color: var(--ch-color);
  font-weight: 600;
}
.ch-metrics {
  display: flex;
  justify-content: space-between;
  font-size: 9px;
  color: var(--text-dim);
  font-family: var(--font-mono);
}
.ch-controls {
  display: flex;
  gap: 6px;
  font-size: 10px;
  color: var(--text-muted);
}
.ch-controls label {
  display: flex;
  align-items: center;
  gap: 3px;
}
.mini-input {
  width: 36px;
  padding: 1px 3px;
  font-size: 10px;
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid var(--border);
  color: var(--text-main);
  border-radius: 2px;
}
</style>
