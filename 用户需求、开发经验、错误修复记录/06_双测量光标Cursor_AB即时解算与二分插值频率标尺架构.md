# 06_双测量光标Cursor_AB即时解算与二分插值频率标尺架构

---

## 一、 示波器专业化标杆：为什么必须有双测量光标？

普通图表库（如单纯的折线图）通常只能通过 Tooltip 鼠标悬停显示单一数据点的数值。但这与真正的**专业台式数字示波器（如 Keysight、Tektronix、Rigol）**相去甚远。

在实际电力电子调机时，工程师核心依赖的操作是打出两条垂直时间标尺（Cursor A 与 Cursor B），用以精准测量：
1. **开关周期与谐振频率**：$T = \Delta T, f = \frac{1}{\Delta T}$；
2. **驱动死区时间与下冲延时**：纳秒/微秒级传输延时；
3. **输出纹波与瞬态过冲压降**：$\Delta V = |V_B - V_A|$。

如果上位机不支持双光标自动求差解算，工程师必须暂停后人工看坐标轴做减法，体验极其原始落后。

---

## 二、 数学模型：$O(\log N)$ 二分搜索与线性高精度插值

在 100,000 点深度环形缓冲中，光标指定的时间点 $T_{\text{target}}$ 往往并不恰好等于某一个采样时钟刻度。如果用线性遍历查找最接近的点，单次拖动就需要遍历 10 万次循环，导致拖动滑块时界面严重卡顿。

### 1. 二分极速定位与边界探测
由于时间序列在时钟驱动下具有严格单调递增性，可使用 **二分查找（Bisection Search）**，在至多 $\lceil \log_2(100000) \rceil \approx 17$ 次比对内，以亚微秒级时间复杂度瞬间锁定相邻的两点 $(t_0, v_0)$ 与 $(t_1, v_1)$：

```javascript
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

  // 线性一阶内插，消灭阶梯量化误差
  const alpha = (targetTime - p0[0]) / (p1[0] - p0[0]);
  return p0[1] + alpha * (p1[1] - p0[1]);
}
```

### 2. 差值与频率自适应单位换算
在物理参数解算层，系统对不同数量级的 $\Delta T$ 与频率 $f$ 实施工程量纲自动转换：
- **时间量纲自适应**：
  $$\Delta T < 1\mu\text{s} \implies \text{ns} \quad|\quad \Delta T < 1\text{ms} \implies \mu\text{s} \quad|\quad \Delta T < 1\text{s} \implies \text{ms} \quad|\quad \text{其它} \implies \text{s}$$
- **频率量纲自适应**：
  $$f \ge 1\text{MHz} \implies \text{MHz} \quad|\quad f \ge 1\text{kHz} \implies \text{kHz} \quad|\quad \text{其它} \implies \text{Hz}$$

---

## 三、 现代化前端交互与 HUD 悬浮仪表盘实现

为了最大化操作便捷性，在 `webui/src/components/WaveformChart.vue` 中实现了**多维交互模式**：
1. **HUD 亚克力悬浮测量卡**：
   - 包含 Cursor A（橙色标尺）与 Cursor B（青色标尺）两个独立时间列，以及中间的高亮 $\Delta$ 差值结果区；
   - 支持通过通道下拉选单，瞬间切换正在测量的示波通道（CH1~CH8）；
2. **全动态范围时间滑块**：
   - 滑块的 `min` 和 `max` 动态绑定当前内存缓冲区的 `timeMin` 与 `timeMax`，随波形滚动自适应伸缩；
3. **图表点击直接拾取定标**：
   - 监听 ECharts ZRender 底层点击事件，当用户直接在波形区域任意位置点击时，自动计算该点与 Cursor A、Cursor B 的距离，并将**距离最近的光标瞬时移动至该点**，真正实现“所点即所测”。
