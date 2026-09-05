<template>
  <header class="navbar">
    <div class="nav-brand">
      <div class="brand-icon">
        <img src="/cat_avatar.png" alt="Icon" class="brand-logo-img" />
      </div>
      <div class="brand-info">
        <span class="brand-title">{{ t('nav.brand') }}</span>
        <span class="brand-badge">{{ t('nav.badge') }}</span>
      </div>
    </div>

    <!-- 导航标签 -->
    <nav class="nav-tabs">
      <button
        v-for="(tab, idx) in tabs"
        :key="tab.id"
        :class="['nav-tab', { active: activeTab === tab.id }]"
        @click="$emit('update:activeTab', tab.id)"
        :title="`[${idx + 1}] ${tab.label}`"
      >
        <component :is="tab.icon" :size="14" />
        <span>{{ tab.label }}</span>
        <span class="tab-shortcut">{{ idx + 1 }}</span>
      </button>
    </nav>

    <!-- 右侧状态指标与实时遥测 -->
    <div class="nav-status">
      <!-- 实时遥测吞吐量指标 -->
      <div class="telemetry-badge" title="WebSocket 实时吞吐量与帧率">
        <Activity :size="11" class="telemetry-icon" />
        <span class="telemetry-val">{{ telemetry.kbps.toFixed(1) }}</span>
        <span class="telemetry-unit">KB/s</span>
        <span class="telemetry-sep">|</span>
        <span class="telemetry-val">{{ telemetry.pps }}</span>
        <span class="telemetry-unit">pps</span>
      </div>

      <!-- 硬件状态小胶囊 -->
      <div class="status-pill" :class="{ active: connectionStatus.serial.connected }">
        <span class="dot"></span>
        <span>{{ connectionStatus.serial.connected ? t('nav.serialConnected') : t('nav.serialDisconnected') }}</span>
      </div>
      <div class="status-pill" :class="{ active: connectionStatus.can.connected }">
        <span class="dot"></span>
        <span>{{ connectionStatus.can.connected ? t('nav.canConnected') : t('nav.canDisconnected') }}</span>
      </div>
      <div class="status-pill" :class="{ active: wsConnected }">
        <span class="dot"></span>
        <span>{{ wsConnected ? t('nav.wsConnected') : t('nav.wsDisconnected') }}</span>
      </div>

      <div class="divider"></div>

      <!-- 中英文一键切换按钮 -->
      <button class="btn-icon lang-btn" :title="t('nav.langToggle')" @click="toggleLocale">
        <Globe :size="14" />
        <span class="lang-code">{{ currentLocale === 'zh-CN' ? 'EN' : '中' }}</span>
      </button>

      <!-- GitHub 开源仓库跳转 -->
      <button class="btn-icon github-btn" :title="t('nav.github')" @click="openGithub">
        <Github :size="15" />
      </button>

      <!-- 系统信息与关于 -->
      <button class="btn-icon" :title="t('nav.systemInfo')" @click="$emit('openInfo')">
        <Info :size="15" />
      </button>
    </div>
  </header>
</template>

<script setup>
import { computed } from 'vue';
import {
  Activity,
  Zap,
  Terminal,
  BarChart2,
  Info,
  Globe,
  Github,
} from 'lucide-vue-next';
import { t, currentLocale, toggleLocale } from '../i18n';

defineProps({
  activeTab: {
    type: String,
    default: 'wave',
  },
  connectionStatus: {
    type: Object,
    default: () => ({
      serial: { connected: false },
      can: { connected: false },
      tcp: { connected: false },
    }),
  },
  wsConnected: {
    type: Boolean,
    default: false,
  },
  telemetry: {
    type: Object,
    default: () => ({ kbps: 0, pps: 0 }),
  },
});

defineEmits(['update:activeTab', 'openInfo']);

const tabs = computed(() => [
  { id: 'wave', label: t('nav.wave'), icon: Activity },
  { id: 'monitor', label: t('nav.monitor'), icon: Terminal },
  { id: 'bode', label: t('nav.bode'), icon: BarChart2 },
]);

function openGithub() {
  const url = 'https://github.com/WenZhenJian-EE/Serial-CAN-Debugger';
  if (window.pywebview && window.pywebview.api && window.pywebview.api.open_external_url) {
    window.pywebview.api.open_external_url(url);
  } else {
    window.open(url, '_blank');
  }
}
</script>

<style scoped>
.navbar {
  height: 48px;
  background-color: var(--bg-sidebar);
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 14px;
  flex-shrink: 0;
  z-index: 50;
  user-select: none;
}

.nav-brand {
  display: flex;
  align-items: center;
  gap: 10px;
}
.brand-icon {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  border: 1.5px solid rgba(var(--accent-rgb), 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  box-shadow: 0 0 10px rgba(0, 0, 0, 0.4);
  flex-shrink: 0;
}
.brand-logo-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.brand-info {
  display: flex;
  align-items: center;
  gap: 8px;
}
.brand-title {
  font-size: 14px;
  font-weight: 700;
  color: var(--text-main);
  letter-spacing: -0.2px;
}
.brand-badge {
  font-size: 10px;
  font-weight: 700;
  padding: 1px 5px;
  border-radius: 3px;
  background: rgba(var(--accent-rgb), 0.15);
  color: var(--accent);
  border: 1px solid rgba(var(--accent-rgb), 0.3);
}

.nav-tabs {
  display: flex;
  gap: 4px;
  background-color: var(--bg-app);
  padding: 3px;
  border-radius: var(--radius-md);
  border: 1px solid var(--border);
}
.nav-tab {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 5px 12px;
  font-size: 12px;
  font-weight: 500;
  color: var(--text-muted);
  border-radius: var(--radius-sm);
  background: transparent;
  border: none;
  cursor: pointer;
  transition: all 0.15s ease;
}
.nav-tab:hover {
  color: var(--text-main);
  background-color: var(--bg-card-hover);
}
.nav-tab.active {
  color: var(--text-main);
  background-color: var(--bg-card);
  box-shadow: var(--shadow-sm);
}
.tab-shortcut {
  font-size: 10px;
  color: var(--text-dim);
  font-family: var(--font-mono);
  background: var(--bg-input);
  padding: 0 4px;
  border-radius: 2px;
}

.nav-status {
  display: flex;
  align-items: center;
  gap: 8px;
}

.telemetry-badge {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 3px 8px;
  background: var(--bg-app);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  font-family: var(--font-mono);
  font-size: 11px;
}
.telemetry-icon {
  color: var(--accent);
  animation: pulse 1.5s infinite;
}
.telemetry-val {
  color: var(--text-main);
  font-weight: 600;
}
.telemetry-unit {
  color: var(--text-muted);
  font-size: 9px;
}
.telemetry-sep {
  color: var(--border);
  margin: 0 2px;
}

.status-pill {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 3px 8px;
  border-radius: var(--radius-sm);
  font-size: 11px;
  background: var(--bg-app);
  border: 1px solid var(--border);
  color: var(--text-muted);
}
.status-pill .dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background-color: var(--text-dim);
}
.status-pill.active {
  color: var(--text-regular);
  border-color: rgba(var(--success-rgb), 0.3);
}
.status-pill.active .dot {
  background-color: var(--success);
  box-shadow: 0 0 6px rgba(var(--success-rgb), 0.6);
}

.divider {
  width: 1px;
  height: 18px;
  background: var(--border);
  margin: 0 4px;
}

.btn-icon {
  width: 28px;
  height: 28px;
  border-radius: var(--radius-sm);
  background: transparent;
  border: 1px solid transparent;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-muted);
  cursor: pointer;
  transition: all 0.15s ease;
}
.btn-icon:hover {
  background: var(--bg-card);
  border-color: var(--border);
  color: var(--text-main);
}

.lang-btn {
  width: auto;
  padding: 0 8px;
  gap: 4px;
  border-color: var(--border);
  background: var(--bg-app);
}
.lang-code {
  font-size: 10px;
  font-weight: 700;
  font-family: var(--font-mono);
}

.github-btn:hover {
  color: #fff;
  background: #24292e;
  border-color: #444d56;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}
</style>
