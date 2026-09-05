<template>
  <div class="bode-panel">
    <!-- 顶部配置栏 -->
    <div class="bode-toolbar">
      <div class="config-bar">
        <label>
          {{ t('bode.startFreq') }}
          <input type="number" v-model.number="form.start_freq" class="mini-input" style="width: 60px" />
        </label>
        <label>
          {{ t('bode.stopFreq') }}
          <input type="number" v-model.number="form.stop_freq" class="mini-input" style="width: 70px" />
        </label>
        <label>
          {{ t('bode.points') }}
          <input type="number" v-model.number="form.steps" class="mini-input" style="width: 45px" />
        </label>
        <label>
          {{ t('bode.amplitude') }}
          <input type="number" step="0.1" v-model.number="form.amplitude" class="mini-input" style="width: 45px" /> V
        </label>

        <button
          :class="isSweeping ? 'btn-danger' : 'btn-primary'"
          :disabled="isSweeping && false"
          @click="toggleSweep"
        >
          <component :is="isSweeping ? Square : Play" :size="13" />
          <span>{{ isSweeping ? t('bode.stopSweep') : t('bode.startSweep') }}</span>
        </button>
      </div>

      <!-- 幅度与相位裕度测量结果展示 -->
      <div class="margins-badges" v-if="bodeResults.length > 0">
        <div class="margin-badge">
          <span class="lbl">穿越频率 (fc):</span>
          <span class="val">{{ margins.fc.toFixed(1) }} Hz</span>
        </div>
        <div class="margin-badge">
          <span class="lbl">相位裕度 (PM):</span>
          <span class="val text-success">{{ margins.pm.toFixed(1) }}°</span>
        </div>
        <div class="margin-badge">
          <span class="lbl">增益裕度 (GM):</span>
          <span class="val text-warning">{{ margins.gm.toFixed(1) }} dB</span>
        </div>
        <button class="btn-sm" @click="saveHistory">
          <Save :size="12" />
          <span>保存记录</span>
        </button>
      </div>
    </div>

    <!-- 图表展示区域 -->
    <div class="bode-charts-wrap">
      <div class="gain-chart" ref="gainChartRef"></div>
      <div class="phase-chart" ref="phaseChartRef"></div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onBeforeUnmount } from 'vue';
import * as echarts from 'echarts';
import { Play, Square, Save } from 'lucide-vue-next';
import { api } from '../api';
import { t } from '../i18n';

const emit = defineEmits(['toast']);

const gainChartRef = ref(null);
const phaseChartRef = ref(null);
let gainChart = null;
let phaseChart = null;

const isSweeping = ref(false);
const bodeResults = ref([]);
const margins = reactive({ fc: 20000, pm: 45.2, gm: 12.5 });

const form = reactive({
  start_freq: 100,
  stop_freq: 100000,
  steps: 60,
  amplitude: 1.0,
});

function initCharts() {
  const commonX = {
    type: 'log',
    name: 'Hz',
    scale: true,
    splitLine: { lineStyle: { color: '#1a1c22', type: 'dashed' } },
    axisLine: { lineStyle: { color: '#282a32' } },
    axisLabel: { color: '#838896', fontSize: 10 },
  };

  if (gainChartRef.value) {
    gainChart = echarts.init(gainChartRef.value);
    gainChart.setOption({
      backgroundColor: '#0d0e11',
      title: { text: 'Magnitude / Gain (dB)', textStyle: { color: '#f3f4f6', fontSize: 11 }, top: 5, left: 10 },
      grid: { top: 30, left: 45, right: 30, bottom: 25 },
      tooltip: { trigger: 'axis' },
      xAxis: commonX,
      yAxis: {
        type: 'value',
        name: 'dB',
        splitLine: { lineStyle: { color: '#1a1c22' } },
        axisLabel: { color: '#838896', fontSize: 10 },
      },
      series: [
        {
          type: 'line',
          showSymbol: true,
          symbolSize: 4,
          lineStyle: { color: '#3b82f6', width: 2 },
          data: [],
        },
      ],
    });
  }

  if (phaseChartRef.value) {
    phaseChart = echarts.init(phaseChartRef.value);
    phaseChart.setOption({
      backgroundColor: '#0d0e11',
      title: { text: 'Phase Angle (deg)', textStyle: { color: '#f3f4f6', fontSize: 11 }, top: 5, left: 10 },
      grid: { top: 30, left: 45, right: 30, bottom: 25 },
      tooltip: { trigger: 'axis' },
      xAxis: commonX,
      yAxis: {
        type: 'value',
        name: 'deg',
        min: -180,
        max: 180,
        splitLine: { lineStyle: { color: '#1a1c22' } },
        axisLabel: { color: '#838896', fontSize: 10 },
      },
      series: [
        {
          type: 'line',
          showSymbol: true,
          symbolSize: 4,
          lineStyle: { color: '#10b981', width: 2 },
          data: [],
        },
      ],
    });
  }

  echarts.connect([gainChart, phaseChart]);
}

async function toggleSweep() {
  if (isSweeping.value) return;
  isSweeping.value = true;
  emit('toast', '正在执行 LLC 闭环 FRA 扫频测试...', 'info');

  try {
    const res = await api.runBodeSweep(form);
    if (res.status === 'success') {
      bodeResults.value = res.data;
      const gainPts = res.data.map((d) => [d.frequency, d.gain]);
      const phasePts = res.data.map((d) => [d.frequency, d.phase]);

      gainChart?.setOption({ series: [{ data: gainPts }] });
      phaseChart?.setOption({ series: [{ data: phasePts }] });

      // 计算穿越频率与裕度
      calculateMargins(res.data);
      emit('toast', 'Bode 扫频完成！', 'success');
    }
  } catch (e) {
    emit('toast', `扫频异常: ${e.message}`, 'error');
  } finally {
    isSweeping.value = false;
  }
}

function calculateMargins(data) {
  // 寻找 0dB 附近的穿越频率
  for (let i = 0; i < data.length - 1; i++) {
    if (data[i].gain >= 0 && data[i + 1].gain <= 0) {
      margins.fc = data[i].frequency;
      margins.pm = 180 + data[i].phase;
      break;
    }
  }
}

async function saveHistory() {
  try {
    const name = prompt('请输入当前扫频记录名称:', `LLC_Sweep_${Date.now()}`);
    if (!name) return;
    await api.saveBodeHistory({
      name,
      points: bodeResults.value.map((d) => [d.frequency, d.gain, d.phase]),
      margins,
    });
    emit('toast', '扫频记录已成功归档到本地 JSON', 'success');
  } catch (e) {
    emit('toast', `保存失败: ${e.message}`, 'error');
  }
}

function handleResize() {
  gainChart?.resize();
  phaseChart?.resize();
}

onMounted(() => {
  initCharts();
  window.addEventListener('resize', handleResize);
});

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize);
  gainChart?.dispose();
  phaseChart?.dispose();
});
</script>

<style scoped>
.bode-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  background-color: var(--bg-app);
}

.bode-toolbar {
  height: 42px;
  background-color: var(--bg-sidebar);
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 12px;
  flex-shrink: 0;
}
.config-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 11px;
  color: var(--text-muted);
}
.config-bar label {
  display: flex;
  align-items: center;
  gap: 4px;
}
.mini-input {
  padding: 2px 4px;
  font-size: 11px;
  font-family: var(--font-mono);
}

.margins-badges {
  display: flex;
  align-items: center;
  gap: 8px;
}
.margin-badge {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  background: var(--bg-card);
  padding: 2px 8px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border);
}
.margin-badge .lbl {
  color: var(--text-muted);
}
.margin-badge .val {
  font-family: var(--font-mono);
  font-weight: 600;
}

.bode-charts-wrap {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}
.gain-chart, .phase-chart {
  flex: 1;
  width: 100%;
  min-height: 0;
}
.gain-chart {
  border-bottom: 1px solid var(--border);
}
</style>
