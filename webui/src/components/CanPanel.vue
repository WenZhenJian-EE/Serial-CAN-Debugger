<template>
  <div class="card can-panel">
    <div class="card-header">
      <div class="card-title">
        <Cpu :size="14" class="text-accent" />
        <span>{{ t('can.title') }}</span>
      </div>
      <span class="badge" :class="isConnected ? 'connected' : 'disconnected'">
        <span class="badge-dot"></span>
        {{ isConnected ? t('can.statusConnected') : t('can.statusDisconnected') }}
      </span>
    </div>

    <!-- 参数配置表单 -->
    <div class="config-grid">
      <div class="form-group">
        <label>{{ t('can.interface') }}</label>
        <select v-model="form.interface" :disabled="isConnected">
          <option v-for="p in providers" :key="p.value" :value="p.value">{{ p.label }}</option>
        </select>
      </div>

      <div class="form-group">
        <label>{{ t('can.channel') }}</label>
        <input type="text" v-model="form.channel" :disabled="isConnected" placeholder="0 / PCAN_USBBUS1" />
      </div>

      <div class="form-group">
        <label>{{ t('can.bitrate') }}</label>
        <select v-model.number="form.bitrate" :disabled="isConnected">
          <option v-for="b in [125000, 250000, 500000, 1000000]" :key="b" :value="b">
            {{ b / 1000 }} kbps
          </option>
        </select>
      </div>

      <div class="form-group">
        <label>{{ t('can.canfd') }}</label>
        <div class="fd-row">
          <label class="checkbox-label">
            <input type="checkbox" v-model="form.fd_mode" :disabled="isConnected" />
            <span>FD</span>
          </label>
          <select v-if="form.fd_mode" v-model.number="form.data_bitrate" :disabled="isConnected" class="flex-1">
            <option :value="2000000">2 Mbps</option>
            <option :value="5000000">5 Mbps</option>
          </select>
        </div>
      </div>
    </div>

    <!-- DBC 数据库映射状态 -->
    <div class="dbc-section">
      <div class="dbc-header">
        <span>{{ t('can.dbcTitle') }}</span>
        <span class="dbc-count" v-if="signalsCount > 0">{{ signalsCount }} signals</span>
      </div>
      <div class="dbc-actions">
        <button class="flex-1" @click="handleLoadDbc">
          <FolderOpen :size="13" />
          <span>{{ dbcLoadedName ? dbcLoadedName : t('can.loadDbc') }}</span>
        </button>
        <input type="file" ref="fileInputRef" accept=".dbc" style="display: none" @change="onFileSelected" />
      </div>
    </div>

    <!-- 连接与断开按钮 -->
    <div class="action-row">
      <button
        class="flex-1"
        :class="isConnected ? 'btn-danger' : 'btn-primary'"
        :disabled="loading"
        @click="toggleConnect"
      >
        <component :is="isConnected ? Unplug : Plug" :size="14" />
        <span>{{ isConnected ? t('can.disconnect') : t('can.connect') }}</span>
      </button>
    </div>

    <!-- CAN 帧发送区 -->
    <div class="send-section" v-if="isConnected">
      <div class="send-header">
        <span>{{ t('can.sendTitle') }}</span>
        <label class="ext-toggle">
          <input type="checkbox" v-model="sendExt" />
          <span>{{ t('can.extended') }}</span>
        </label>
      </div>
      <div class="send-inputs">
        <input type="text" v-model="sendId" placeholder="ID (HEX)" class="mono id-input" />
        <input type="text" v-model="sendData" placeholder="Data 8B (HEX)" class="mono data-input flex-1" />
        <button class="btn-primary" @click="sendFrame" :disabled="!sendData.trim()">
          <Send :size="12" />
          <span>{{ t('can.sendBtn') }}</span>
        </button>
      </div>

      <!-- 周期发送设置 -->
      <div class="periodic-bar">
        <label>
          {{ t('can.interval') }}
          <input type="number" v-model.number="periodicInterval" class="mini-input" style="width: 50px" /> ms
        </label>
        <button
          :class="isPeriodicRunning ? 'btn-danger' : ''"
          @click="togglePeriodic"
        >
          <span>{{ isPeriodicRunning ? t('can.stopPeriodic') : t('can.startPeriodic') }}</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue';
import { Cpu, FolderOpen, Plug, Unplug, Send } from 'lucide-vue-next';
import { api, desktopBridge } from '../api';
import { t } from '../i18n';

const props = defineProps({
  isConnected: Boolean,
});

const emit = defineEmits(['statusChange', 'toast']);

const fileInputRef = ref(null);
const loading = ref(false);
const providers = ref([]);
const signalsCount = ref(0);
const dbcLoadedName = ref('');

const form = reactive({
  interface: 'virtual',
  channel: '0',
  bitrate: 500000,
  fd_mode: false,
  data_bitrate: 2000000,
});

const sendId = ref('100');
const sendData = ref('01 02 03 04 05 06 07 08');
const sendExt = ref(false);

const isPeriodicRunning = ref(false);
const periodicInterval = ref(100);

async function fetchProviders() {
  try {
    const res = await api.getCanProviders();
    providers.value = res.providers;
  } catch (_) {}
}

async function handleLoadDbc() {
  if (desktopBridge.isAvailable()) {
    const filePath = await desktopBridge.chooseFile('选择 DBC 文件', ['DBC 协议文件 (*.dbc)']);
    if (filePath) {
      dbcLoadedName.value = filePath.split('\\').pop() || filePath.split('/').pop();
      emit('toast', { type: 'info', msg: `DBC: ${dbcLoadedName.value}` });
    }
  } else {
    fileInputRef.value?.click();
  }
}

async function onFileSelected(e) {
  const file = e.target.files?.[0];
  if (!file) return;
  dbcLoadedName.value = file.name;
  try {
    const res = await api.uploadDbc(file);
    if (res.status === 'success') {
      signalsCount.value = Object.keys(res.signals || {}).length;
      emit('toast', { type: 'success', msg: `成功加载 DBC，已解析 ${signalsCount.value} 个信号` });
    }
  } catch (err) {
    emit('toast', { type: 'error', msg: `DBC 解析异常: ${err.message}` });
  }
}

async function toggleConnect() {
  loading.value = true;
  try {
    if (props.isConnected) {
      await api.disconnectCan();
      emit('statusChange');
      emit('toast', { type: 'info', msg: t('can.statusDisconnected') });
    } else {
      await api.connectCan(form);
      emit('statusChange');
      emit('toast', { type: 'success', msg: `${t('can.statusConnected')} ${form.interface}` });
    }
  } catch (e) {
    emit('toast', { type: 'error', msg: e.message });
  } finally {
    loading.value = false;
  }
}

async function sendFrame() {
  try {
    const arbId = parseInt(sendId.value, 16);
    await api.sendCanRaw(arbId, sendData.value, true, sendExt.value);
    emit('toast', { type: 'success', msg: t('can.sentSuccess') });
  } catch (e) {
    emit('toast', { type: 'error', msg: `发送帧失败: ${e.message}` });
  }
}

async function togglePeriodic() {
  try {
    if (isPeriodicRunning.value) {
      await api.stopCanPeriodic();
      isPeriodicRunning.value = false;
      emit('toast', { type: 'info', msg: t('can.stopPeriodic') });
    } else {
      const arbId = parseInt(sendId.value, 16);
      await api.startCanPeriodic({
        arbitration_id: arbId,
        data_hex: sendData.value,
        is_hex: true,
        interval_ms: periodicInterval.value,
        is_extended: sendExt.value,
      });
      isPeriodicRunning.value = true;
      emit('toast', { type: 'success', msg: `${t('can.startPeriodic')} (${periodicInterval.value}ms)` });
    }
  } catch (e) {
    emit('toast', { type: 'error', msg: `周期发送异常: ${e.message}` });
  }
}

onMounted(() => {
  fetchProviders();
});
</script>

<style scoped>
.can-panel {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.config-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}
.form-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.form-group label {
  font-size: 11px;
  color: var(--text-muted);
}
.fd-row {
  display: flex;
  align-items: center;
  gap: 6px;
}
.flex-1 {
  flex: 1;
}
.action-row {
  display: flex;
  margin-top: 2px;
}
.dbc-section {
  border-top: 1px solid var(--border-light);
  padding-top: 8px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.dbc-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 11px;
  color: var(--text-regular);
}
.dbc-count {
  font-size: 10px;
  color: var(--accent);
  font-family: var(--font-mono);
}
.dbc-actions {
  display: flex;
  gap: 6px;
}
.send-section {
  border-top: 1px solid var(--border-light);
  padding-top: 8px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.send-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 11px;
  color: var(--text-regular);
}
.ext-toggle {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  cursor: pointer;
  color: var(--text-muted);
}
.send-inputs {
  display: flex;
  gap: 4px;
}
.id-input {
  width: 70px;
  text-align: center;
}
.periodic-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 11px;
  color: var(--text-muted);
  margin-top: 4px;
}
</style>
