<template>
  <div class="card custom-controls-panel">
    <!-- 面板标题与操作栏 -->
    <div class="card-header">
      <div class="card-title">
        <Sliders :size="13" class="text-accent" />
        <span>{{ t('custom.title') }}</span>
      </div>
      <div class="header-actions">
        <button class="btn-xs" @click="openAddDialog" :title="t('custom.addControl')">
          <Plus :size="11" />
          <span>{{ t('custom.addControl') }}</span>
        </button>
        <button class="btn-xs" @click="exportJson" :title="t('custom.exportJson')">
          <Download :size="11" />
        </button>
        <button class="btn-xs" @click="triggerImport" :title="t('custom.importJson')">
          <Upload :size="11" />
        </button>
        <button class="btn-xs btn-ghost" @click="clearAll" :title="t('custom.clearAll')">
          <Trash2 :size="11" />
        </button>
        <input type="file" ref="fileInputRef" accept=".json" class="hidden-input" @change="onFileImport" />
      </div>
    </div>

    <!-- 控件展示与操作区 (纯净自定义，无预设捆绑) -->
    <div class="controls-container">
      <div v-if="controls.length === 0" class="empty-placeholder">
        <span>{{ t('custom.emptyTip') }}</span>
        <div class="empty-slots-grid">
          <div
            v-for="i in 4"
            :key="i"
            class="empty-slot-card"
            @click="openAddDialogWithSlot(i)"
          >
            <Plus :size="13" />
            <span>{{ t('custom.unconfiguredSlot') }}</span>
          </div>
        </div>
      </div>

      <!-- 控件列表: 智能混合排布 (滑块占整行，按钮两列排布) -->
      <div v-else class="controls-stream">
        <template v-for="(ctrl, idx) in controls" :key="ctrl.id || idx">
          <!-- 1. 滑块控件 (Slider) -->
          <div v-if="ctrl.type === 'slider'" class="slider-control-card">
            <div class="slider-card-top">
              <div class="slider-info">
                <span class="slider-name">{{ ctrl.name || `滑块 ${idx + 1}` }}</span>
                <span class="slider-val mono">{{ ctrl.value }}</span>
              </div>
              <button class="btn-edit" @click.stop="openEditDialog(ctrl, idx)" :title="t('custom.btnConfigTitle')">
                <Settings :size="11" />
              </button>
            </div>

            <div class="slider-action-row">
              <button class="step-btn" @click="adjustSlider(ctrl, -ctrl.step)" title="Step -">
                <Minus :size="11" />
              </button>
              <input
                type="range"
                :min="ctrl.min"
                :max="ctrl.max"
                :step="ctrl.step"
                v-model.number="ctrl.value"
                class="slider-range flex-1"
                @input="onSliderInput(ctrl)"
              />
              <button class="step-btn" @click="adjustSlider(ctrl, ctrl.step)" title="Step +">
                <Plus :size="11" />
              </button>
            </div>
          </div>

          <!-- 2. 按钮控件 (Button) -->
          <div
            v-else
            class="button-control-card"
            :class="{ active: activeBtnId === ctrl.id, 'unconfigured-card': !ctrl.data || !ctrl.data.trim() }"
            @click="onButtonClick(ctrl)"
          >
            <div class="btn-main-info">
              <span class="btn-label">{{ ctrl.name || `按钮 ${idx + 1}` }}</span>
              <span class="btn-meta mono" :class="{ 'meta-warn': !ctrl.data || !ctrl.data.trim() }">
                {{ (!ctrl.data || !ctrl.data.trim()) ? t('custom.noPayload') : (ctrl.is_hex ? 'HEX' : 'ASC') }}
              </span>
            </div>
            <button class="btn-edit" @click.stop="openEditDialog(ctrl, idx)" :title="t('custom.btnConfigTitle')">
              <Settings :size="12" />
            </button>
          </div>
        </template>

        <!-- 末尾常驻添加卡片 -->
        <div class="add-slot-card" @click="openAddDialog">
          <Plus :size="12" />
          <span>{{ t('custom.addControl') }}</span>
        </div>
      </div>
    </div>

    <!-- 弹窗：配置控件 (按钮 / 滑块) -->
    <div v-if="showModal" class="modal-backdrop" @click.self="showModal = false">
      <div class="card modal-dialog-box">
        <div class="card-header">
          <span class="card-title">{{ t('custom.btnConfigTitle') }}</span>
          <button class="btn-icon" @click="showModal = false"><X :size="14" /></button>
        </div>

        <div class="modal-body-content">
          <!-- 类型选择: 按钮 or 滑块 -->
          <div class="form-group">
            <label>{{ t('custom.controlType') }}</label>
            <div class="type-segment">
              <button
                type="button"
                class="seg-btn"
                :class="{ active: form.type === 'button' }"
                @click="form.type = 'button'"
              >
                {{ t('custom.typeButton') }}
              </button>
              <button
                type="button"
                class="seg-btn"
                :class="{ active: form.type === 'slider' }"
                @click="form.type = 'slider'"
              >
                {{ t('custom.typeSlider') }}
              </button>
            </div>
          </div>

          <!-- 控件自定义名称 (用户自由指定，绝不强加预设) -->
          <div class="form-group">
            <label>{{ t('custom.nameLabel') }}</label>
            <input
              type="text"
              v-model="form.name"
              :placeholder="t('custom.namePlaceholder')"
              class="flex-1"
            />
          </div>

          <!-- 目标总线选择 -->
          <div class="form-group">
            <label>{{ t('custom.targetBus') }}</label>
            <select v-model="form.target">
              <option value="auto">{{ t('custom.busAuto') }}</option>
              <option value="serial">{{ t('custom.busSerial') }}</option>
              <option value="can">{{ t('custom.busCan') }}</option>
            </select>
          </div>

          <!-- 按钮模式专有表单 -->
          <div v-if="form.type === 'button'" class="form-sub-section">
            <div class="form-group">
              <label>
                {{ t('custom.dataLabel') }}
                <span class="required-tag">*</span>
              </label>
              <input
                type="text"
                v-model="form.data"
                :placeholder="t('custom.dataPlaceholder')"
                class="mono"
              />
            </div>
            <div class="form-row">
              <label class="checkbox-label">
                <input type="checkbox" v-model="form.is_hex" />
                <span>{{ t('custom.isHex') }}</span>
              </label>
            </div>
          </div>

          <!-- 滑块模式专有表单 -->
          <div v-else class="form-sub-section">
            <div class="grid-3">
              <div class="form-group">
                <label>{{ t('custom.sliderMin') }}</label>
                <input type="number" step="any" v-model.number="form.min" class="mono" />
              </div>
              <div class="form-group">
                <label>{{ t('custom.sliderMax') }}</label>
                <input type="number" step="any" v-model.number="form.max" class="mono" />
              </div>
              <div class="form-group">
                <label>{{ t('custom.sliderStep') }}</label>
                <input type="number" step="any" v-model.number="form.step" class="mono" />
              </div>
            </div>

            <div class="form-group">
              <label>{{ t('custom.sliderTemplate') }}</label>
              <input
                type="text"
                v-model="form.template"
                :placeholder="t('custom.templatePlaceholder')"
                class="mono"
              />
            </div>
          </div>

          <!-- 底部操作按钮 -->
          <div class="modal-footer-actions">
            <button v-if="editingIndex !== -1" class="btn-danger btn-sm" @click="deleteControl">
              <Trash2 :size="12" />
              <span>{{ t('custom.delete') }}</span>
            </button>
            <div class="flex-1"></div>
            <button class="btn-outline btn-sm" @click="showModal = false">{{ t('custom.cancel') }}</button>
            <button class="btn-primary btn-sm" @click="saveControl">{{ t('custom.confirm') }}</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue';
import {
  Sliders,
  Plus,
  Minus,
  Settings,
  X,
  Trash2,
  Download,
  Upload,
} from 'lucide-vue-next';
import { t } from '../i18n';
import { api } from '../api';

const props = defineProps({
  activeBus: {
    type: String,
    default: 'serial',
  },
  isSerialConnected: {
    type: Boolean,
    default: false,
  },
  isCanConnected: {
    type: Boolean,
    default: false,
  },
});

const emit = defineEmits(['toast']);

const controls = ref([]);
const activeBtnId = ref(null);
const fileInputRef = ref(null);

const showModal = ref(false);
const editingIndex = ref(-1);

const form = reactive({
  type: 'button', // 'button' | 'slider'
  name: '',
  data: '',
  is_hex: false,
  target: 'auto', // 'auto' | 'serial' | 'can'
  min: 0,
  max: 100,
  step: 1,
  value: 0,
  template: '{val}\\r\\n',
});

// 节流下发计时器字典 (避免滑块快速拖动导致串口或 CAN 阻塞)
const throttleTimers = {};

function loadStoredControls() {
  const stored = localStorage.getItem('custom_controls_items');
  if (stored) {
    try {
      controls.value = JSON.parse(stored);
      return;
    } catch (_) {}
  }
  // 零预设捆绑！完全保持纯净，由用户自由命名
  controls.value = [];
}

function saveStoredControls() {
  localStorage.setItem('custom_controls_items', JSON.stringify(controls.value));
}

// ─── 点击按钮发送 ────────────────────────────────────────────────────────────
async function onButtonClick(ctrl) {
  if (!ctrl.data || !ctrl.data.trim()) {
    emit('toast', {
      type: 'warn',
      msg: t('custom.emptyPayloadTip', { name: ctrl.name || '按钮' }),
    });
    return;
  }
  activeBtnId.value = ctrl.id;
  setTimeout(() => (activeBtnId.value = null), 200);

  await dispatchPayload(ctrl.target, ctrl.data, ctrl.is_hex, ctrl.name);
}

// ─── 滑块输入与步进 ──────────────────────────────────────────────────────────
function adjustSlider(ctrl, delta) {
  const newVal = parseFloat((ctrl.value + delta).toFixed(4));
  if (newVal >= ctrl.min && newVal <= ctrl.max) {
    ctrl.value = newVal;
    onSliderInput(ctrl);
  }
}

function onSliderInput(ctrl) {
  // 节流处理: 80ms 发送一次
  if (throttleTimers[ctrl.id]) return;
  throttleTimers[ctrl.id] = setTimeout(async () => {
    delete throttleTimers[ctrl.id];
    let payload = ctrl.template || '{val}\\r\\n';
    payload = payload.replace('{val}', ctrl.value);
    await dispatchPayload(ctrl.target, payload, false, `${ctrl.name}: ${ctrl.value}`);
  }, 80);
}

// ─── 统一分发到串口或 CAN ───────────────────────────────────────────────────
async function dispatchPayload(target, rawData, isHex, label) {
  try {
    let dest = target;
    if (dest === 'auto') {
      dest = props.activeBus === 'can' ? 'can' : 'serial';
    }

    if (dest === 'can') {
      await api.sendCanRaw(0x100, rawData, isHex, false);
    } else {
      await api.sendSerialRaw(rawData, isHex);
    }
    emit('toast', { type: 'success', msg: t('custom.sentSuccess', { name: label, data: rawData }) });
  } catch (err) {
    emit('toast', { type: 'warn', msg: `${label}: ${err.message}` });
  }
}

// ─── 弹窗交互 ────────────────────────────────────────────────────────────────
function openAddDialog() {
  editingIndex.value = -1;
  form.type = 'button';
  form.name = '';
  form.data = '';
  form.is_hex = false;
  form.target = 'auto';
  form.min = 0;
  form.max = 100;
  form.step = 1;
  form.value = 0;
  form.template = '{val}\\r\\n';
  showModal.value = true;
}

function openAddDialogWithSlot(slotNum) {
  openAddDialog();
  form.name = `自定义 ${slotNum}`;
}

function openEditDialog(ctrl, idx) {
  editingIndex.value = idx;
  form.type = ctrl.type || 'button';
  form.name = ctrl.name || '';
  form.data = ctrl.data || '';
  form.is_hex = !!ctrl.is_hex;
  form.target = ctrl.target || 'auto';
  form.min = ctrl.min ?? 0;
  form.max = ctrl.max ?? 100;
  form.step = ctrl.step ?? 1;
  form.value = ctrl.value ?? 0;
  form.template = ctrl.template || '{val}\\r\\n';
  showModal.value = true;
}

function saveControl() {
  if (form.type === 'button') {
    if (!form.data || !form.data.trim()) {
      emit('toast', { type: 'warn', msg: t('custom.dataRequired') });
      return;
    }
  }

  const item = {
    id: editingIndex.value !== -1 ? controls.value[editingIndex.value].id : `c_${Date.now()}`,
    type: form.type,
    name: form.name.trim() || (form.type === 'slider' ? '滑块' : '按钮'),
    data: form.data ? form.data.trim() : '',
    is_hex: form.is_hex,
    target: form.target,
    min: form.min,
    max: form.max,
    step: form.step,
    value: form.value,
    template: form.template,
  };

  if (editingIndex.value !== -1) {
    controls.value[editingIndex.value] = item;
  } else {
    controls.value.push(item);
  }

  saveStoredControls();
  showModal.value = false;
  emit('toast', { type: 'success', msg: t('custom.configSaved') });
}

function deleteControl() {
  if (editingIndex.value !== -1) {
    controls.value.splice(editingIndex.value, 1);
    saveStoredControls();
    showModal.value = false;
  }
}

function clearAll() {
  if (controls.value.length === 0) return;
  controls.value = [];
  saveStoredControls();
  emit('toast', { type: 'info', msg: t('custom.clearAll') });
}

// ─── 导入与导出 ──────────────────────────────────────────────────────────────
function exportJson() {
  const jsonStr = JSON.stringify(controls.value, null, 2);
  const blob = new Blob([jsonStr], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'custom_controls.json';
  a.click();
  URL.revokeObjectURL(url);
  emit('toast', { type: 'success', msg: t('custom.configExported') });
}

function triggerImport() {
  if (fileInputRef.value) fileInputRef.value.click();
}

function onFileImport(e) {
  const file = e.target.files[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = (event) => {
    try {
      const parsed = JSON.parse(event.target.result);
      if (Array.isArray(parsed)) {
        controls.value = parsed;
        saveStoredControls();
        emit('toast', { type: 'success', msg: t('custom.configImported') });
      }
    } catch (_) {
      emit('toast', { type: 'error', msg: 'JSON 解析失败' });
    }
  };
  reader.readAsText(file);
  e.target.value = '';
}

onMounted(() => {
  loadStoredControls();
});
</script>

<style scoped>
.custom-controls-panel {
  display: flex;
  flex-direction: column;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  margin-top: 10px;
  flex-shrink: 0;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 4px;
}

.btn-ghost {
  background: transparent;
  border-color: transparent;
  color: var(--text-dim);
}
.btn-ghost:hover {
  color: var(--danger);
}

.hidden-input {
  display: none;
}

.controls-container {
  padding: 8px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.empty-placeholder {
  display: flex;
  flex-direction: column;
  gap: 8px;
  font-size: 11px;
  color: var(--text-dim);
}

.empty-slots-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 6px;
}

.empty-slot-card {
  height: 42px;
  border: 1px dashed var(--border);
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  cursor: pointer;
  color: var(--text-muted);
  font-size: 11px;
  transition: all 0.15s;
}
.empty-slot-card:hover {
  border-color: var(--accent);
  color: var(--accent);
  background: rgba(var(--accent-rgb), 0.05);
}

.controls-stream {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 6px;
}

/* 按钮样式卡片 (采用两两并排或自适应网格) */
.button-control-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: var(--bg-input);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: 6px 10px;
  cursor: pointer;
  user-select: none;
  transition: all 0.15s ease;
}
.button-control-card:hover {
  border-color: var(--accent);
  background: var(--bg-card-hover);
}
.button-control-card.active {
  transform: scale(0.98);
  background: rgba(var(--accent-rgb), 0.2);
  border-color: var(--accent);
}

.btn-main-info {
  display: flex;
  align-items: center;
  gap: 6px;
  overflow: hidden;
}
.btn-label {
  font-size: 11px;
  font-weight: 600;
  color: var(--text-main);
  white-space: nowrap;
  text-overflow: ellipsis;
  overflow: hidden;
}
.btn-meta {
  font-size: 9px;
  color: var(--text-dim);
  background: var(--bg-app);
  padding: 1px 4px;
  border-radius: 2px;
}

/* 滑块样式卡片 */
.slider-control-card {
  grid-column: 1 / -1;
  display: flex;
  flex-direction: column;
  gap: 4px;
  background: var(--bg-input);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: 8px 10px;
}
.slider-card-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.slider-info {
  display: flex;
  align-items: center;
  gap: 8px;
}
.slider-name {
  font-size: 11px;
  font-weight: 600;
  color: var(--text-main);
}
.slider-val {
  font-size: 11px;
  color: var(--accent);
  font-weight: 700;
}

.slider-action-row {
  display: flex;
  align-items: center;
  gap: 6px;
}
.slider-range {
  height: 4px;
  accent-color: var(--accent);
  cursor: pointer;
}
.step-btn {
  width: 22px;
  height: 22px;
  padding: 0;
  border-radius: 3px;
  background: var(--bg-card);
  border: 1px solid var(--border);
  color: var(--text-regular);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}
.step-btn:hover {
  border-color: var(--accent);
  color: var(--accent);
}

.btn-edit {
  opacity: 0.6;
  background: transparent;
  border: 1px solid transparent;
  color: var(--text-muted);
  cursor: pointer;
  padding: 3px;
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s ease;
}
.button-control-card:hover .btn-edit,
.slider-control-card:hover .btn-edit {
  opacity: 1;
}
.btn-edit:hover {
  color: var(--accent);
  background: rgba(var(--accent-rgb), 0.15);
  border-color: rgba(var(--accent-rgb), 0.3);
}

.btn-meta.meta-warn {
  color: var(--warning);
  background: rgba(var(--warning-rgb), 0.15);
  border: 1px solid rgba(var(--warning-rgb), 0.3);
}

.required-tag {
  color: var(--danger);
  margin-left: 3px;
  font-weight: bold;
}

.add-slot-card {
  grid-column: 1 / -1;
  height: 32px;
  border: 1px dashed var(--border);
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  font-size: 11px;
  color: var(--text-dim);
  cursor: pointer;
  transition: all 0.15s;
}
.add-slot-card:hover {
  color: var(--accent);
  border-color: var(--accent);
}

/* 弹窗样式 */
.modal-dialog-box {
  width: 380px;
  max-width: 90vw;
  background: var(--bg-card);
}
.modal-body-content {
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.type-segment {
  display: flex;
  background: var(--bg-app);
  border-radius: var(--radius-sm);
  padding: 2px;
  border: 1px solid var(--border);
}
.seg-btn {
  flex: 1;
  background: transparent;
  border: none;
  font-size: 11px;
  padding: 5px;
  color: var(--text-muted);
  border-radius: 3px;
  cursor: pointer;
}
.seg-btn.active {
  background: var(--bg-card-hover);
  color: var(--accent);
  font-weight: 600;
}

.form-sub-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
  background: rgba(255, 255, 255, 0.02);
  padding: 8px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border-light);
}

.grid-3 {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 6px;
}

.modal-footer-actions {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 6px;
}
</style>
