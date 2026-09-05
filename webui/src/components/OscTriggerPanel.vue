<template>
  <div class="card trigger-panel">
    <div class="card-header">
      <div class="card-title">
        <Zap :size="14" class="text-warning" />
        <span>{{ t('trigger.title') }}</span>
      </div>
      <span class="badge" :class="triggerStateBadgeClass">
        <span class="badge-dot"></span>
        {{ triggerStateText }}
      </span>
    </div>

    <!-- 触发模式与参数配置 -->
    <div class="trigger-grid">
      <div class="form-group">
        <label>{{ t('trigger.mode') }}</label>
        <div class="mode-buttons">
          <button
            v-for="m in ['Auto', 'Normal', 'Single']"
            :key="m"
            class="mode-btn"
            :class="{ active: form.mode === m }"
            @click="setMode(m)"
          >
            {{ m }}
          </button>
        </div>
      </div>

      <div class="form-group">
        <label>{{ t('trigger.channel') }}</label>
        <select v-model.number="form.source_id" @change="applyTrigger">
          <option v-for="c in 8" :key="c" :value="c">CH{{ c }}</option>
        </select>
      </div>

      <div class="form-group">
        <label>{{ t('trigger.edge') }}</label>
        <div class="edge-buttons">
          <button
            class="edge-btn"
            :class="{ active: form.edge === 'Rising' }"
            @click="setEdge('Rising')"
          >
            {{ t('trigger.edgeRising') }}
          </button>
          <button
            class="edge-btn"
            :class="{ active: form.edge === 'Falling' }"
            @click="setEdge('Falling')"
          >
            {{ t('trigger.edgeFalling') }}
          </button>
        </div>
      </div>

      <div class="form-group">
        <label>{{ t('trigger.threshold') }} <span class="mono text-accent">{{ form.level }} V</span></label>
        <div class="level-slider-row">
          <input
            type="range"
            min="-100"
            max="400"
            step="0.5"
            v-model.number="form.level"
            @input="applyTrigger"
            class="flex-1"
          />
          <input
            type="number"
            v-model.number="form.level"
            @change="applyTrigger"
            class="mono level-input"
          />
        </div>
      </div>
    </div>

    <!-- 操作与复位按钮 -->
    <div class="action-row">
      <button class="flex-1 btn-primary" @click="applyTrigger">
        <span>{{ t('trigger.apply') }} (ARM)</span>
      </button>
      <button @click="resetTrigger">
        <RotateCcw :size="13" />
        <span>{{ t('trigger.reset') }}</span>
      </button>
    </div>

    <!-- 黑匣子故障越限保护录波配置 -->
    <div class="blackbox-section">
      <div class="blackbox-header">
        <ShieldAlert :size="13" class="text-danger" />
        <span>黑匣子 10 秒故障全景录波器 (Pre 5s + Post 5s)</span>
      </div>
      <div class="blackbox-inputs">
        <label>
          CH:
          <select v-model.number="bb.channel_id" class="mini-select">
            <option v-for="c in 8" :key="c" :value="c">CH{{ c }}</option>
          </select>
        </label>
        <label>
          Max:
          <input type="number" v-model.number="bb.max_limit" class="mini-input" /> V
        </label>
        <label>
          Min:
          <input type="number" v-model.number="bb.min_limit" class="mini-input" /> V
        </label>
        <button class="btn-sm" @click="saveBlackbox">设置防护</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue';
import { Zap, RotateCcw, ShieldAlert } from 'lucide-vue-next';
import { api } from '../api';
import { t } from '../i18n';

const emit = defineEmits(['toast']);

const form = reactive({
  mode: 'Auto',
  source_id: 1,
  level: 50.0,
  edge: 'Rising',
  points: 1000,
});

const isArmed = ref(false);
const isTriggered = ref(false);

const bb = reactive({
  channel_id: 1,
  max_limit: 350.0,
  min_limit: -350.0,
});

const triggerStateText = computed(() => {
  if (form.mode === 'Auto') return 'Auto';
  if (isTriggered.value) return 'Triggered!';
  if (isArmed.value) return 'Armed';
  return 'Idle';
});

const triggerStateBadgeClass = computed(() => {
  if (isTriggered.value) return 'connected';
  if (isArmed.value) return 'warning';
  return 'disconnected';
});

function setMode(m) {
  form.mode = m;
  applyTrigger();
}

function setEdge(e) {
  form.edge = e;
  applyTrigger();
}

async function applyTrigger() {
  try {
    await api.configureTrigger({
      mode: form.mode,
      source_id: form.source_id,
      threshold: form.level,
      edge: form.edge.toLowerCase(),
      holdoff: 100,
    });
    isArmed.value = true;
    isTriggered.value = false;
    emit('toast', { type: 'success', msg: `触发器已就绪: ${form.mode} CH${form.source_id} @ ${form.level}V` });
  } catch (e) {
    emit('toast', { type: 'error', msg: `配置失败: ${e.message}` });
  }
}

async function resetTrigger() {
  try {
    await api.resetTrigger();
    isArmed.value = true;
    isTriggered.value = false;
    emit('toast', { type: 'info', msg: '触发状态已重置' });
  } catch (e) {
    emit('toast', { type: 'error', msg: e.message });
  }
}

async function saveBlackbox() {
  try {
    await api.configureBlackbox({
      enabled: true,
      channel_id: bb.channel_id,
      max_limit: bb.max_limit,
      min_limit: bb.min_limit,
      window_samples: 5000,
    });
    emit('toast', { type: 'success', msg: `黑匣子防护已开启: CH${bb.channel_id} [${bb.min_limit}, ${bb.max_limit}]V` });
  } catch (e) {
    emit('toast', { type: 'error', msg: `黑匣子设置失败: ${e.message}` });
  }
}
</script>

<style scoped>
.trigger-panel {
  display: flex;
  flex-direction: column;
  gap: 10px;
  width: 100%;
  margin-top: 10px;
  flex-shrink: 0;
}
.trigger-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}
.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.form-group label {
  font-size: 11px;
  color: var(--text-muted);
}
.mode-buttons, .edge-buttons {
  display: flex;
  gap: 4px;
}
.mode-btn, .edge-btn {
  flex: 1;
  padding: 5px 8px;
  font-size: 11px;
  background: var(--bg-input);
  border: 1px solid var(--border);
  color: var(--text-muted);
  border-radius: var(--radius-sm);
  cursor: pointer;
}
.mode-btn.active, .edge-btn.active {
  background: rgba(var(--accent-rgb), 0.15);
  border-color: var(--accent);
  color: var(--accent);
  font-weight: 600;
}
.level-slider-row {
  display: flex;
  align-items: center;
  gap: 8px;
}
.level-input {
  width: 60px;
  text-align: center;
}
.action-row {
  display: flex;
  gap: 8px;
  margin-top: 4px;
}
.blackbox-section {
  border-top: 1px solid var(--border);
  padding-top: 10px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.blackbox-header {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 600;
  color: var(--text-regular);
}
.blackbox-inputs {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
  font-size: 11px;
}
.mini-select, .mini-input {
  background: var(--bg-input);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: 3px 6px;
  color: var(--text-main);
  font-size: 11px;
}
.mini-input {
  width: 60px;
  text-align: center;
}
</style>
