<template>
  <div class="app-layout">
    <!-- 顶部统一导航 -->
    <Navbar
      :activeTab="activeTab"
      :connectionStatus="connectionStatus"
      :wsConnected="wsConnected"
      :telemetry="telemetry"
      @update:activeTab="switchTab"
      @openInfo="showInfoModal = true"
    />

    <!-- 主体工作区 -->
    <main class="app-workspace">
      <!-- 左侧硬件总线控制面板 (宽度 350px) -->
      <aside class="sidebar" :class="{ collapsed: isSidebarCollapsed }">
        <div class="sidebar-tabs">
          <button
            class="sidebar-tab-btn"
            :class="{ active: sidebarTab === 'serial' }"
            @click="sidebarTab = 'serial'"
          >
            {{ t('sidebar.serial') }}
          </button>
          <button
            class="sidebar-tab-btn"
            :class="{ active: sidebarTab === 'can' }"
            @click="sidebarTab = 'can'"
          >
            {{ t('sidebar.can') }}
          </button>
        </div>

        <div class="sidebar-content">
          <SerialPanel
            v-show="sidebarTab === 'serial'"
            :isConnected="connectionStatus.serial.connected"
            @statusChange="fetchStatus"
            @toast="showToast"
          />
          <CanPanel
            v-show="sidebarTab === 'can'"
            :isConnected="connectionStatus.can.connected"
            @statusChange="fetchStatus"
            @toast="showToast"
          />
          <OscTriggerPanel @toast="showToast" />
          <CustomButtonsPanel
            :activeBus="sidebarTab"
            :isSerialConnected="connectionStatus.serial.connected"
            :isCanConnected="connectionStatus.can.connected"
            @toast="showToast"
          />
        </div>
      </aside>

      <!-- 侧边栏折叠/展开把手 -->
      <div class="sidebar-handle" @click="isSidebarCollapsed = !isSidebarCollapsed">
        <component :is="isSidebarCollapsed ? ChevronRight : ChevronLeft" :size="12" />
      </div>

      <!-- 右侧主视图投影面 (支持 W3C View Transitions API 原生跨度渐变) -->
      <section class="main-view">
        <!-- 实时示波主图 -->
        <WaveformChart
          ref="waveChartRef"
          v-show="activeTab === 'wave'"
          :streamer="streamer"
          @toast="showToast"
        />

        <!-- 高性能虚拟滚动报文监视器 -->
        <VirtualMonitor
          v-show="activeTab === 'monitor'"
          :streamer="streamer"
        />

        <!-- LLC FRA Bode 扫频仪 -->
        <BodeSweeperPanel
          v-show="activeTab === 'bode'"
          @toast="showToast"
        />
      </section>
    </main>

    <!-- 系统信息与关于弹窗 -->
    <div v-if="showInfoModal" class="modal-backdrop" @click.self="showInfoModal = false">
      <div class="card modal-dialog-custom">
        <div class="card-header">
          <span class="card-title">{{ t('modal.title') }}</span>
          <button class="btn-icon" @click="showInfoModal = false"><X :size="14" /></button>
        </div>

        <!-- 软件核心徽章 -->
        <div class="modal-branding">
          <img src="/cat_avatar.png" alt="Cat Icon" class="modal-avatar" />
          <div class="modal-brand-text">
            <div class="modal-app-name">Serial-CAN-Debugger V3.0</div>
            <div class="modal-app-desc">{{ t('modal.appDesc') }}</div>
          </div>
        </div>

        <!-- 开源作者与技术博客专属卡片 (满足开源诉求) -->
        <div class="author-card">
          <div class="author-header">
            <Github :size="15" class="text-accent" />
            <span class="author-card-title">{{ t('modal.authorTitle') }}</span>
          </div>
          <div class="author-grid">
            <div class="author-row">
              <span class="author-k">{{ t('modal.authorName') }}</span>
              <strong class="author-v text-main">{{ t('modal.authorVal') }}</strong>
            </div>
            <div class="author-row">
              <span class="author-k">{{ t('modal.githubRepo') }}</span>
              <a href="javascript:void(0)" class="author-link" @click="openExternalUrl('https://github.com/WenZhenJian-EE/Serial-CAN-Debugger')">
                github.com/WenZhenJian-EE/Serial-CAN-Debugger
                <ExternalLink :size="11" />
              </a>
            </div>
            <div class="author-row">
              <span class="author-k">{{ t('modal.techBlog') }}</span>
              <a href="javascript:void(0)" class="author-link" @click="openExternalUrl('https://WenZhenJian-EE.github.io')">
                https://WenZhenJian-EE.github.io
                <ExternalLink :size="11" />
              </a>
            </div>
            <div class="author-row">
              <span class="author-k">{{ t('modal.license') }}</span>
              <span class="author-v">{{ t('modal.licenseVal') }}</span>
            </div>
          </div>
        </div>

        <!-- 软件运行时与工程规范指标 -->
        <div class="info-list">
          <div><span>{{ t('modal.versionKey') }}</span> <strong>{{ t('modal.versionVal') }}</strong></div>
          <div><span>{{ t('modal.runtimeKey') }}</span> <strong>{{ t('modal.runtimeVal') }}</strong></div>
          <div><span>{{ t('modal.busKey') }}</span> <strong>{{ t('modal.busVal') }}</strong></div>
          <div><span>{{ t('modal.engineKey') }}</span> <strong>{{ t('modal.engineVal') }}</strong></div>
          <div><span>{{ t('modal.transitionsKey') }}</span> <strong>{{ t('modal.transitionsVal') }}</strong></div>
          <div><span>{{ t('modal.depthKey') }}</span> <strong>{{ t('modal.depthVal') }}</strong></div>
          <div><span>{{ t('modal.shortcutsKey') }}</span> <strong>{{ t('modal.shortcutsVal') }}</strong></div>
          <div><span>{{ t('modal.packageKey') }}</span> <strong>{{ t('modal.packageVal') }}</strong></div>
        </div>
      </div>
    </div>

    <!-- Toast 通知浮层 -->
    <div class="toast-container">
      <div
        v-for="t in toasts"
        :key="t.id"
        class="toast-item"
        :class="`toast-${t.type}`"
      >
        <span>{{ t.msg }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onBeforeUnmount } from 'vue';
import { ChevronLeft, ChevronRight, X, Github, ExternalLink } from 'lucide-vue-next';
import Navbar from './components/Navbar.vue';
import WaveformChart from './components/WaveformChart.vue';
import SerialPanel from './components/SerialPanel.vue';
import CanPanel from './components/CanPanel.vue';
import CustomButtonsPanel from './components/CustomButtonsPanel.vue';
import OscTriggerPanel from './components/OscTriggerPanel.vue';
import VirtualMonitor from './components/VirtualMonitor.vue';
import BodeSweeperPanel from './components/BodeSweeperPanel.vue';
import { api, WebSocketStreamer } from './api';
import { t } from './i18n';

const activeTab = ref('wave');
const sidebarTab = ref('serial');
const isSidebarCollapsed = ref(false);

const waveChartRef = ref(null);
const showInfoModal = ref(false);

const wsConnected = ref(false);
const telemetry = reactive({ kbps: 0.0, pps: 0 });
const connectionStatus = reactive({
  serial: { connected: false },
  can: { connected: false },
  tcp: { connected: false },
});

function openExternalUrl(url) {
  if (window.pywebview && window.pywebview.api && window.pywebview.api.open_external_url) {
    window.pywebview.api.open_external_url(url);
  } else {
    window.open(url, '_blank');
  }
}

// W3C View Transitions 丝滑视图过渡
function switchTab(newTab) {
  if (activeTab.value === newTab) return;
  if (typeof document !== 'undefined' && document.startViewTransition) {
    document.startViewTransition(() => {
      activeTab.value = newTab;
    });
  } else {
    activeTab.value = newTab;
  }
}

// Toast 通知系统
const toasts = ref([]);
let toastSeq = 0;
function showToast(msg, type = 'info') {
  const id = ++toastSeq;
  toasts.value.push({ id, msg, type });
  setTimeout(() => {
    toasts.value = toasts.value.filter((t) => t.id !== id);
  }, 3500);
}

// 初始化 WebSocket 流引擎与遥测指标
const streamer = new WebSocketStreamer();
streamer.on('onStatusChange', (connected) => {
  wsConnected.value = connected;
  if (connected) fetchStatus();
});
streamer.on('onTelemetry', (stats) => {
  telemetry.kbps = stats.kbps;
  telemetry.pps = stats.pps;
});
streamer.on('onTriggerFired', (mode) => {
  showToast(`触发器已捕获波形 (${mode})！界面已自动锁定冻结。`, 'warn');
});
streamer.on('onFaultTriggered', (path) => {
  showToast(`黑匣子故障录波完成！已自动落盘至: ${path}`, 'error');
});
streamer.on('onTriggeredReady', (path) => {
  showToast(`硬件录波分包已完整拼接并保存: ${path}`, 'success');
});

async function fetchStatus() {
  try {
    const res = await api.getConnectionStatus();
    connectionStatus.serial = res.serial || { connected: false };
    connectionStatus.can = res.can || { connected: false };
    connectionStatus.tcp = res.tcp || { connected: false };
  } catch (_) {}
}

// 全局工控高频交互快捷键监听
function handleKeyDown(e) {
  const tag = e.target?.tagName?.toLowerCase();
  if (tag === 'input' || tag === 'textarea' || tag === 'select') return;

  if (e.code === 'Space') {
    e.preventDefault();
    if (waveChartRef.value) {
      waveChartRef.value.togglePause();
      showToast(waveChartRef.value.isPaused ? '波形已暂停' : '波形继续运行', 'info');
    }
  } else if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'l') {
    e.preventDefault();
    if (waveChartRef.value) {
      waveChartRef.value.clearData();
      showToast('波形数据已清空', 'info');
    }
  } else if (e.key === '1') {
    switchTab('wave');
  } else if (e.key === '2') {
    switchTab('monitor');
  } else if (e.key === '3') {
    switchTab('bode');
  }
}

let statusTimer = null;
onMounted(() => {
  streamer.connect();
  fetchStatus();
  statusTimer = setInterval(fetchStatus, 3000);
  window.addEventListener('keydown', handleKeyDown);
});

onBeforeUnmount(() => {
  streamer.disconnect();
  if (statusTimer) clearInterval(statusTimer);
  window.removeEventListener('keydown', handleKeyDown);
});
</script>

<style scoped>
.app-layout {
  width: 100vw;
  height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.app-workspace {
  flex: 1;
  display: flex;
  min-height: 0;
  position: relative;
}

.sidebar {
  width: 350px;
  background-color: var(--bg-sidebar);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  transition: width 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
}
.sidebar.collapsed {
  width: 0;
  border-right: none;
}

.sidebar-tabs {
  display: flex;
  border-bottom: 1px solid var(--border);
  background: var(--bg-app);
}
.sidebar-tab-btn {
  flex: 1;
  background: transparent;
  border: none;
  border-radius: 0;
  padding: 8px 6px;
  font-size: 11px;
  color: var(--text-muted);
  border-bottom: 2px solid transparent;
  white-space: nowrap;
  text-overflow: ellipsis;
  overflow: hidden;
}
.sidebar-tab-btn.active {
  color: var(--text-main);
  background: var(--bg-sidebar);
  border-bottom-color: var(--accent);
  font-weight: 600;
}

.sidebar-content {
  flex: 1;
  overflow-y: auto;
  padding: 10px;
  display: flex;
  flex-direction: column;
}

.sidebar-handle {
  width: 8px;
  background: var(--bg-card);
  border-right: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: var(--text-dim);
  transition: all 0.15s;
  z-index: 10;
}
.sidebar-handle:hover {
  background: var(--bg-card-hover);
  color: var(--text-main);
}

.main-view {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  height: 100%;
  overflow: hidden;
  background-color: var(--bg-app);
}

.view-padding {
  padding: 16px;
  overflow-y: auto;
}

.modal-dialog-custom {
  width: 520px;
  max-width: 90vw;
  background: var(--bg-card);
}
.modal-branding {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 12px 14px;
  margin-bottom: 8px;
  background: rgba(255, 255, 255, 0.03);
  border-radius: var(--radius-sm);
  border: 1px solid var(--border-light);
}
.modal-avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  border: 2px solid rgba(var(--accent-rgb), 0.5);
  box-shadow: 0 0 12px rgba(0, 0, 0, 0.5);
  flex-shrink: 0;
}
.modal-brand-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.modal-app-name {
  font-size: 14px;
  font-weight: 700;
  color: var(--text-main);
}
.modal-app-desc {
  font-size: 11px;
  color: var(--text-muted);
}

/* 开源作者卡片 */
.author-card {
  background: rgba(var(--accent-rgb), 0.06);
  border: 1px solid rgba(var(--accent-rgb), 0.25);
  border-radius: var(--radius-sm);
  padding: 10px 14px;
  margin-bottom: 10px;
}
.author-header {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 8px;
}
.author-card-title {
  font-size: 12px;
  font-weight: 700;
  color: var(--text-main);
}
.author-grid {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.author-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 11px;
}
.author-k {
  color: var(--text-muted);
}
.author-v {
  color: var(--text-regular);
}
.author-link {
  color: var(--accent);
  text-decoration: none;
  display: flex;
  align-items: center;
  gap: 3px;
}
.author-link:hover {
  text-decoration: underline;
  color: var(--accent-hover);
}

.info-list {
  display: flex;
  flex-direction: column;
  gap: 7px;
  padding: 8px 0;
  font-size: 11px;
}
.info-list div {
  display: flex;
  justify-content: space-between;
  border-bottom: 1px solid var(--border-light);
  padding-bottom: 4px;
}

.toast-container {
  position: fixed;
  bottom: 24px;
  right: 24px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  z-index: 1000;
  pointer-events: none;
}
.toast-item {
  padding: 8px 14px;
  border-radius: var(--radius-sm);
  font-size: 12px;
  font-weight: 500;
  background: var(--bg-card);
  border: 1px solid var(--border);
  color: var(--text-main);
  box-shadow: var(--shadow-md);
  pointer-events: auto;
  animation: slideIn 0.2s ease-out;
}
.toast-success {
  border-left: 3px solid var(--success);
}
.toast-error {
  border-left: 3px solid var(--danger);
  color: #f87171;
}
.toast-warn {
  border-left: 3px solid var(--warning);
  color: #fbbf24;
}
.toast-info {
  border-left: 3px solid var(--accent);
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
