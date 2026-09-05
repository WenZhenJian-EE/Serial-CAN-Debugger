# 08_W3C_View_Transitions与工控极简暗黑设计系统规范

---

## 一、 工业美学原则：拒绝霓虹光污染，回归专业工控沉浸

在专业工程上位机软件中，视觉设计绝非花哨的装饰，而是直接决定了工程师在长达数小时排查高压电源、电机振荡或总线故障时的**用眼疲劳度与信息识别效率**：
- 浅色白底界面在暗光实验室环境下极其刺眼；
- 过于艳丽的高饱和霓虹配色容易造成视觉噪音，干扰关键故障报警与波形特征的辨识。

为此，Serial-CAN-Debugger V3.0 制定了**极简工业暗黑设计系统规范**，并在 `webui/src/theme.css` 中建立了完整的变量标准：
1. **VS Code 级层叠明度空间**：
   - 根底色 `--bg-app: #0e1014`（深曜石黑，零纯黑死板）；
   - 侧边栏 `--bg-sidebar: #121419`；
   - 仪表卡片 `--bg-card: #181b22`；
   - 悬浮反衬 `--bg-card-hover: #1e222b`；
2. **高对比度功能色规范**：
   - 强调色 `--accent: #3b82f6`（科技蓝，用于高亮操作与通信连接）；
   - 成功/运行 `--success: #10b981`（工业翡翠绿，指示总线已连通或波形正常流转）；
   - 告警/异常 `--warning: #f59e0b`（琥珀橙，指示硬件单次边沿触发等待）；
   - 故障/报错 `--danger: #ef4444`（报警红，指示总线离线或黑匣子严重故障）；
3. **等宽工控字体规范**：
   - 全面引入 JetBrains Mono / Fira Code / Consolas，保证十六进制报文（`0xAA 0x55`）与时间戳对齐工整，杜绝字符宽窄不一导致的视觉抖动。

---

## 二、 零重量级第三方 UI 库准则 (Zero Bloatware)

在旧版中，项目一度引入了 Element Plus 或 Ant Design Vue，导致：
- 打包体积中仅 CSS 和通用组件就占去数兆字节；
- 第三方组件库自带强烈的网页后台管理系统（CRUD Admin）风格，圆角过大、边距过宽，与紧凑硬核的专业示波器界面格格不入。

**MAP 2.0 确立的铁律**：
- **绝对 100% 拒绝任何全家桶式第三方 UI 组件库**；
- 纯净依托原生 Vue 3.5 + 纯 CSS 变量原子类开发；
- 仅保留超轻量矢量图标库 `lucide-vue-next`；
- 使得前端整体编译产物仅有数百 KB，构建极速，完全受控。

---

## 三、 2026 前沿：W3C View Transitions API 丝滑转场

在传统的单页桌面应用中，Tab 切换往往伴随着视图突变或容易掉帧的第三方过渡动画库。

本项目全面拥抱现代浏览器标准的 **W3C View Transitions API**：
```javascript
// webui/src/App.vue
function switchTab(newTab) {
  if (activeTab.value === newTab) return;
  
  // 原生检测浏览器是否支持 View Transitions API
  if (typeof document !== 'undefined' && document.startViewTransition) {
    document.startViewTransition(() => {
      activeTab.value = newTab;
    });
  } else {
    activeTab.value = newTab;
  }
}
```

在 CSS 层通过伪元素注入极简硬件加速渐变：
```css
::view-transition-old(root) {
  animation: 0.15s cubic-bezier(0.4, 0, 1, 1) both fluid-fade-out;
}
::view-transition-new(root) {
  animation: 0.2s cubic-bezier(0, 0, 0.2, 1) both fluid-fade-in;
}
```
切换主视图（实时示波 / 硬件触发 / 报文监视 / Bode扫频）时，浏览器在底层自动截取旧视口与新视口纹理，由 GPU 在 150 毫秒内完成丝滑平滑过渡，体感达到专业原生操作系统级流畅度。

---

## 四、 工控高频盲操全局快捷键设计

现场调试时，工程师的一只手往往握着示波器探头或手持万用表表笔，另一只手操作键盘。必须实现高频盲操：

| 快捷键 | 功能定义 | 触发行为 |
| :--- | :--- | :--- |
| **`Space` (空格键)** | 示波器暂停 / 运行瞬时冻结 | 瞬间锁定当前 100k 点阵，防止关键瞬态滑出视野 |
| **`Ctrl + L`** | 波形与监视器数据清空 | 一键重置清空历史点阵，开启新一轮捕获 |
| **`1`** | 切换至 **实时示波** 主视图 | 快速查看 8 通道时域波形 |
| **`2`** | 切换至 **硬件触发** 主视图 | 配置边沿/故障触发状态机 |
| **`3`** | 切换至 **报文监视** 主视图 | 虚拟滚动分析原始总线数据帧 |
| **`4`** | 切换至 **Bode扫频** 主视图 | 执行 LLC 变换器频响对数扫频 |

**输入隔离安全机制**：全局键盘监听器自动判定当前焦点的 HTML 标签（`input`, `textarea`, `select`），在用户输入数值或文本时自动跳过全局快捷键，绝无输入打字被误吞或误切视图的缺陷。
