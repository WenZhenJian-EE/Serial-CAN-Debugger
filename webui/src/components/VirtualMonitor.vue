<template>
  <div class="virtual-monitor">
    <!-- 顶部工具控制栏 -->
    <div class="monitor-toolbar">
      <div class="toolbar-left">
        <span class="toolbar-title">
          <Terminal :size="14" class="text-cyan" />
          <span>{{ t('monitor.title') }} ({{ filteredPackets.length }})</span>
        </span>

        <!-- 过滤选择 -->
        <select v-model="filterType" class="type-select">
          <option value="ALL">All Channels</option>
          <option value="CAN">CAN Bus Only</option>
          <option value="SERIAL">Serial Port Only</option>
          <option value="TCP">TCP Only</option>
        </select>

        <input
          type="text"
          v-model="searchKeyword"
          :placeholder="t('monitor.filterPlaceholder')"
          class="mono search-input"
        />
      </div>

      <div class="toolbar-right">
        <label class="auto-scroll-label">
          <input type="checkbox" v-model="autoScroll" />
          <span>{{ t('monitor.autoScroll') }}</span>
        </label>
        <button class="btn-sm" @click="clearPackets">
          <Trash2 :size="12" />
          <span>{{ t('monitor.clear') }}</span>
        </button>
        <button class="btn-sm" @click="exportText">
          <Download :size="12" />
          <span>{{ t('monitor.export') }}</span>
        </button>
      </div>
    </div>

    <!-- 表头 -->
    <div class="table-header">
      <span class="col-idx">#</span>
      <span class="col-time">{{ t('monitor.colTime') }}</span>
      <span class="col-src">{{ t('monitor.colBus') }}</span>
      <span class="col-type">Type</span>
      <span class="col-id">{{ t('monitor.colId') }}</span>
      <span class="col-data flex-1">{{ t('monitor.colData') }} (HEX)</span>
    </div>

    <!-- 虚拟滚动视口容器 -->
    <div
      class="virtual-viewport"
      ref="viewportRef"
      @scroll="onScroll"
    >
      <!-- 虚拟撑高占位层 -->
      <div
        class="virtual-phantom"
        :style="{ height: `${filteredPackets.length * ROW_HEIGHT}px` }"
      ></div>

      <!-- 真实 DOM 可见切片渲染层 -->
      <div
        class="virtual-content"
        :style="{ transform: `translate3d(0, ${startIndex * ROW_HEIGHT}px, 0)` }"
      >
        <div
          v-for="(pkt, idx) in visibleSlice"
          :key="startIndex + idx"
          class="packet-row"
          :class="`src-${pkt.source.toLowerCase()}`"
        >
          <span class="col-idx mono">{{ startIndex + idx + 1 }}</span>
          <span class="col-time mono">{{ pkt.timeStr }}</span>
          <span class="col-src badge-src">{{ pkt.source }}</span>
          <span class="col-type">{{ pkt.frameType }}</span>
          <span class="col-id mono font-semibold">{{ pkt.arbId }}</span>
          <span class="col-data mono flex-1">{{ pkt.hexData }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount, nextTick } from 'vue';
import { Terminal, Trash2, Download } from 'lucide-vue-next';
import { t } from '../i18n';

const props = defineProps({
  streamer: Object,
});

const ROW_HEIGHT = 22; // 单行固定高度 px
const BUFFER_COUNT = 15; // 上下多渲染的缓冲条目数

const viewportRef = ref(null);
const scrollTop = ref(0);
const viewportHeight = ref(400);

const autoScroll = ref(true);
const filterType = ref('ALL');
const searchKeyword = ref('');

// 数据源: 内存可维持多达 50,000 条报文
const packets = ref([]);
const MAX_PACKETS = 50000;

function parseRawBatch(lines) {
  const now = new Date();
  const timeStr = `${now.toTimeString().split(' ')[0]}.${String(now.getMilliseconds()).padStart(3, '0')}`;

  const newItems = [];
  for (const line of lines) {
    if (!line) continue;
    if (line.startsWith('RAW_SERIAL:')) {
      const hex = line.substring(11);
      newItems.push({
        source: 'SERIAL',
        frameType: 'RAW',
        arbId: '--',
        hexData: formatHex(hex),
        timeStr,
      });
    } else if (line.startsWith('RAW_CAN:')) {
      const parts = line.substring(8).split(',');
      if (parts.length >= 4) {
        const [frameType, t, arbId, dataHex, isExt] = parts;
        newItems.push({
          source: 'CAN',
          frameType: `${frameType} ${isExt === '1' ? 'EXT' : 'STD'}`,
          arbId: `0x${parseInt(arbId).toString(16).toUpperCase().padStart(3, '0')}`,
          hexData: formatHex(dataHex),
          timeStr,
        });
      }
    } else if (line.startsWith('RAW_TCP:')) {
      const hex = line.substring(8);
      newItems.push({
        source: 'TCP',
        frameType: 'STREAM',
        arbId: '--',
        hexData: formatHex(hex),
        timeStr,
      });
    }
  }

  if (newItems.length > 0) {
    packets.value.push(...newItems);
    if (packets.value.length > MAX_PACKETS) {
      packets.value.splice(0, packets.value.length - MAX_PACKETS);
    }
    if (autoScroll.value) {
      scrollToBottom();
    }
  }
}

function formatHex(hexStr) {
  return hexStr.match(/.{1,2}/g)?.join(' ') || hexStr;
}

// 过滤后的数据列表
const filteredPackets = computed(() => {
  let list = packets.value;
  if (filterType.value !== 'ALL') {
    list = list.filter((p) => p.source === filterType.value);
  }
  if (searchKeyword.value.trim()) {
    const kw = searchKeyword.value.trim().toLowerCase();
    list = list.filter(
      (p) =>
        p.arbId.toLowerCase().includes(kw) ||
        p.hexData.toLowerCase().includes(kw)
    );
  }
  return list;
});

// 虚拟滚动核心切片算法
const startIndex = computed(() => {
  return Math.max(0, Math.floor(scrollTop.value / ROW_HEIGHT) - BUFFER_COUNT);
});

const visibleCount = computed(() => {
  return Math.ceil(viewportHeight.value / ROW_HEIGHT) + 2 * BUFFER_COUNT;
});

const visibleSlice = computed(() => {
  const start = startIndex.value;
  const end = Math.min(filteredPackets.value.length, start + visibleCount.value);
  return filteredPackets.value.slice(start, end);
});

function onScroll(e) {
  scrollTop.value = e.target.scrollTop;
  // 如果用户手动向上滚动，自动取消锁定
  const atBottom =
    e.target.scrollHeight - e.target.scrollTop - e.target.clientHeight < 30;
  if (!atBottom && autoScroll.value) {
    autoScroll.value = false;
  }
}

function scrollToBottom() {
  nextTick(() => {
    if (viewportRef.value) {
      viewportRef.value.scrollTop = viewportRef.value.scrollHeight;
    }
  });
}

function clearPackets() {
  packets.value = [];
}

function exportText() {
  const text = filteredPackets.value
    .map(
      (p, i) =>
        `[${i + 1}] ${p.timeStr} [${p.source}] [${p.frameType}] ID:${p.arbId} Data:${p.hexData}`
    )
    .join('\n');
  const blob = new Blob([text], { type: 'text/plain;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `packets_log_${Date.now()}.txt`;
  a.click();
  URL.revokeObjectURL(url);
}

function updateViewportSize() {
  if (viewportRef.value) {
    viewportHeight.value = viewportRef.value.clientHeight;
  }
}

onMounted(() => {
  updateViewportSize();
  window.addEventListener('resize', updateViewportSize);

  if (props.streamer) {
    props.streamer.on('onRawBatch', parseRawBatch);
  }
});

onBeforeUnmount(() => {
  window.removeEventListener('resize', updateViewportSize);
});
</script>

<style scoped>
.virtual-monitor {
  display: flex;
  flex-direction: column;
  height: 100%;
  background-color: var(--bg-app);
  overflow: hidden;
}

.monitor-toolbar {
  height: 38px;
  background-color: var(--bg-sidebar);
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 12px;
  flex-shrink: 0;
}
.toolbar-left, .toolbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
}
.toolbar-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 600;
  color: var(--text-regular);
}
.type-select {
  font-size: 11px;
  padding: 2px 6px;
}
.search-input {
  width: 180px;
  font-size: 11px;
}
.auto-scroll-label {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  color: var(--text-muted);
  cursor: pointer;
}

.table-header {
  height: 26px;
  background: var(--bg-card);
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  padding: 0 10px;
  font-size: 11px;
  font-weight: 600;
  color: var(--text-muted);
  flex-shrink: 0;
}
.col-idx { width: 50px; }
.col-time { width: 90px; }
.col-src { width: 60px; }
.col-type { width: 90px; }
.col-id { width: 80px; }
.col-data { min-width: 200px; }

.virtual-viewport {
  flex: 1;
  position: relative;
  overflow-y: auto;
  overflow-x: hidden;
  background: #090a0d;
}
.virtual-phantom {
  position: absolute;
  left: 0;
  top: 0;
  right: 0;
  z-index: -1;
}
.virtual-content {
  position: absolute;
  left: 0;
  right: 0;
  top: 0;
}

.packet-row {
  height: 22px;
  display: flex;
  align-items: center;
  padding: 0 10px;
  font-size: 11px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.02);
  transition: background 0.1s;
}
.packet-row:hover {
  background: rgba(255, 255, 255, 0.04);
}
.packet-row.src-can {
  color: #60a5fa;
}
.packet-row.src-serial {
  color: #34d399;
}
.packet-row.src-tcp {
  color: #c084fc;
}
.badge-src {
  font-size: 9px;
  font-weight: 700;
  padding: 1px 4px;
  border-radius: 3px;
  background: rgba(255, 255, 255, 0.06);
}
.flex-1 { flex: 1; }
</style>
