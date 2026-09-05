<template>
  <div class="card serial-panel">
    <div class="card-header">
      <div class="card-title">
        <Radio :size="14" class="text-accent" />
        <span>{{ t('serial.title') }}</span>
      </div>
      <span class="badge" :class="isConnected ? 'connected' : 'disconnected'">
        <span class="badge-dot"></span>
        {{ isConnected ? t('serial.statusOpen') : t('serial.statusClosed') }}
      </span>
    </div>

    <!-- 配置表单 -->
    <div class="config-grid">
      <div class="form-group">
        <label>{{ t('serial.port') }}</label>
        <div class="input-row">
          <select v-model="form.port" :disabled="isConnected" class="flex-1">
            <option v-for="p in availablePorts" :key="p" :value="p">{{ p }}</option>
          </select>
          <button class="btn-icon" :title="t('serial.refresh')" @click="fetchPorts" :disabled="isConnected">
            <RefreshCw :size="12" />
          </button>
          <button class="btn-icon" :title="t('serial.autoProbe')" @click="autoProbe" :disabled="isConnected">
            <Search :size="12" />
          </button>
        </div>
      </div>

      <div class="form-group">
        <label>{{ t('serial.baudrate') }}</label>
        <select v-model.number="form.baudrate" :disabled="isConnected">
          <option v-for="b in [9600, 19200, 38400, 57600, 115200, 230400, 460800, 921600]" :key="b" :value="b">
            {{ b }} bps
          </option>
        </select>
      </div>

      <div class="form-group">
        <label>{{ t('serial.protocol') }}</label>
        <select v-model="form.protocol" :disabled="isConnected">
          <option value="custom">{{ t('serial.protoCustom') }}</option>
          <option value="modbus">{{ t('serial.protoModbus') }}</option>
        </select>
      </div>

      <div class="form-group">
        <label>{{ t('serial.parity') }}</label>
        <select v-model="form.parity" :disabled="isConnected">
          <option value="None">{{ t('serial.parityNone') }}</option>
          <option value="Even">{{ t('serial.parityEven') }}</option>
          <option value="Odd">{{ t('serial.parityOdd') }}</option>
        </select>
      </div>
    </div>

    <!-- 连接动作按钮 -->
    <div class="action-row">
      <button
        class="flex-1"
        :class="isConnected ? 'btn-danger' : 'btn-primary'"
        :disabled="loading"
        @click="toggleConnect"
      >
        <component :is="isConnected ? Unplug : Plug" :size="14" />
        <span>{{ isConnected ? t('serial.closePort') : t('serial.openPort') }}</span>
      </button>
    </div>

    <!-- 快捷发送条 -->
    <div class="send-section" v-if="isConnected">
      <div class="send-header">
        <span>{{ t('serial.sendTitle') }}</span>
        <label class="hex-toggle">
          <input type="checkbox" v-model="sendIsHex" />
          <span>{{ sendIsHex ? t('serial.sendHex') : t('serial.sendAscii') }}</span>
        </label>
      </div>
      <div class="send-input-row">
        <input
          type="text"
          v-model="sendText"
          :placeholder="t('serial.placeholderSend')"
          class="mono flex-1"
          @keyup.enter="sendRaw"
        />
        <button class="btn-primary" @click="sendRaw" :disabled="!sendText.trim()">
          <Send :size="12" />
          <span>{{ t('serial.sendBtn') }}</span>
        </button>
      </div>

      <!-- 自定义宏按钮列表 -->
      <div class="macro-buttons" v-if="customButtons.length > 0">
        <button
          v-for="btn in customButtons"
          :key="btn.id"
          class="macro-btn"
          @click="sendMacro(btn.command)"
        >
          {{ btn.label }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue';
import { Radio, RefreshCw, Search, Plug, Unplug, Send } from 'lucide-vue-next';
import { api } from '../api';
import { t } from '../i18n';

const props = defineProps({
  isConnected: Boolean,
});

const emit = defineEmits(['statusChange', 'toast']);

const availablePorts = ref([]);
const loading = ref(false);

const form = reactive({
  port: 'COM1',
  baudrate: 115200,
  protocol: 'custom',
  parity: 'None',
  bytesize: 8,
  stopbits: 1.0,
});

const sendText = ref('A5 01 01 00 00 00 00 E5');
const sendIsHex = ref(true);
const customButtons = ref([
  { id: 1, label: '开机使能', command: 'A5 01 01 00 00 00 00 E5' },
  { id: 2, label: '停机封锁', command: 'A5 01 00 00 00 00 00 E4' },
]);

async function fetchPorts() {
  try {
    const res = await api.getPorts();
    if (res.status === 'success') {
      availablePorts.value = res.ports;
      if (res.ports.length > 0 && !res.ports.includes(form.port)) {
        form.port = res.ports[0];
      }
    }
  } catch (e) {
    emit('toast', { type: 'error', msg: `获取串口失败: ${e.message}` });
  }
}

async function autoProbe() {
  loading.value = true;
  try {
    const res = await api.autoProbe();
    if (res.success && res.port) {
      form.port = res.port;
      emit('toast', { type: 'success', msg: `识别到特征串口: ${res.port}` });
    } else {
      emit('toast', { type: 'warn', msg: '未能自动识别下位机串口' });
    }
  } catch (e) {
    emit('toast', { type: 'error', msg: `探针识别异常: ${e.message}` });
  } finally {
    loading.value = false;
  }
}

async function toggleConnect() {
  loading.value = true;
  try {
    if (props.isConnected) {
      await api.disconnectSerial();
      emit('statusChange');
      emit('toast', { type: 'info', msg: t('serial.statusClosed') });
    } else {
      await api.connectSerial(form);
      emit('statusChange');
      emit('toast', { type: 'success', msg: `${t('serial.statusOpen')} ${form.port}` });
    }
  } catch (e) {
    emit('toast', { type: 'error', msg: e.message });
  } finally {
    loading.value = false;
  }
}

async function sendRaw() {
  if (!sendText.value.trim()) return;
  try {
    await api.sendSerialRaw(sendText.value.trim(), sendIsHex.value);
    emit('toast', { type: 'success', msg: t('serial.sentSuccess') });
  } catch (e) {
    emit('toast', { type: 'error', msg: `发送失败: ${e.message}` });
  }
}

function sendMacro(cmd) {
  sendText.value = cmd;
  sendIsHex.value = true;
  sendRaw();
}

onMounted(() => {
  fetchPorts();
});
</script>

<style scoped>
.serial-panel {
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
.input-row {
  display: flex;
  gap: 4px;
}
.flex-1 {
  flex: 1;
}
.action-row {
  display: flex;
  margin-top: 2px;
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
.hex-toggle {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  cursor: pointer;
  color: var(--text-muted);
}
.send-input-row {
  display: flex;
  gap: 4px;
}
.macro-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-top: 2px;
}
.macro-btn {
  font-size: 11px;
  padding: 3px 8px;
  background: rgba(255, 255, 255, 0.04);
}
</style>
