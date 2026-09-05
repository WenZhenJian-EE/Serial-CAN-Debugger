# 24_示波调试器领域术语净化与GitHub正统仓库重命名规范

## 一、 用户指导性反馈与认知纠偏

在本项目完成多语言（i18n）、人机工程双层侧边栏与个人博客同步后，用户审视全局，提出了两条至关重要的工程与产品定位指导意见：

1. **术语混淆纠偏：严禁在示波调试器中使用 "MAP" 标签**：
   > “我们目前这个软件是调试工具、示波器，你一直强调这个 MAP 是干嘛呀？MAP 不是那个代码静态代码分析工具吗？”
   - **痛点分析**：在电力电子、汽车电子与嵌入式开发中，“MAP” 通常具有极强的既定业务含义：
     - **代码静态分析 / 链接映射文件（.map）**：Keil/IAR/GCC 编译输出的内存段分布、符号地址映射表；
     - **汽车标定图谱（Engine MAP / Fuel MAP）**：发动机喷油、点火提前角等二维/三维标定曲面；
     - **存储映射（Memory Map）**：寄存器与外设地址映射空间。
   - 此前开发中，系统曾将内部软件工程元架构代号（Modern, Accelerated, Portable）简写为 “MAP 2.0”，并将其置于软件标题、弹窗、技术描述与对外宣传中。这严重违背了工控示波调试工具的业务本义，极易误导使用者以为这是一个静态代码分析器或标定软件。
   - **决策结论**：**100% 彻底抹除软件内部所有的 "MAP / MAP 2.0" 标签**。全面回归工控仪器领域通行的规范表达：
     - 中文产品名：**工业级串口与 CAN/CAN-FD 示波调试终端**；
     - 英文产品名：**High-Speed Serial & CAN/CAN-FD Bus Debugger & Oscilloscope**；
     - 架构描述：**现代极速桌面架构 (FastAPI + WebSocket + Vue 3 + Edge WebView2)**。

2. **代码仓库正统规范化：移除历史残留 "-V2" 后缀**：
   > “而且我仓库的名称可以命名成目前最合适的啊，Serial-CAN-Debugger-V2，这是原来的仓库的名称，怎么有个V2的东西？”
   - **历史渊源**：仓库名称中的 `-V2` 是早期第一代 PyQt5 版本的遗留产物。如今软件已完成全面技术蜕变，作为个人主打的工业级开源旗舰，带 `-V2` 后缀显得历史包袱沉重、不正式且不够纯粹。
   - **可行性论证**：通过 GitHub API 查询确认，作者空间（`WenZhenJian-EE`）下尚未占用正统的 `Serial-CAN-Debugger`，名称完全可用！
   - **决策结论**：全面将对外仓库链接标准化为 `https://github.com/WenZhenJian-EE/Serial-CAN-Debugger`。

---

## 二、 术语净化实施细节清单

本次净化作业采取全方位无死角扫描与替换，覆盖以下核心组件与文件：

| 模块 / 文件 | 净化前内容 | 净化后标准工控术语 |
| :--- | :--- | :--- |
| `webui/src/i18n.js` (zh-CN) | `appDesc: '... · MAP 2.0 极速引擎'` | `appDesc: '... · 现代极速桌面架构'` |
| `webui/src/i18n.js` (en-US) | `appDesc: '... · MAP 2.0 Engine'` | `appDesc: '... · High-Performance Desktop Architecture'` |
| `webui/src/theme.css` | `(MAP 2.0 规范)` | `(现代工控暗黑设计系统)` |
| `main.py` | `Serial-CAN-Debugger V3.0 (MAP 2.0 ...)` | `Serial-CAN-Debugger V3.0 (现代桌面工业示波调试终端)` |
| `server/api.py` | `FastAPI(title="... MAP 2.0 Backend")`<br>`architecture: "MAP 2.0"` | `FastAPI(title="Serial-CAN-Debugger Backend")`<br>`architecture: "FastAPI + WebSocket + WebView2"` |
| `build_exe.py` | `MAP 2.0 Meta-Architecture`<br>`MAP 2.0 打包工具` | `现代桌面工业示波调试终端 离线打包流水线`<br>`Serial-CAN-Debugger 离线单文件打包工具` |
| `README.md` | `MAP 2.0 Meta-Architecture`<br>`MAP 2.0 对标` | `modern decoupled desktop architecture`<br>`现代桌面架构对标` |
| 个人博客 `projects/index.md` | `工业高刷示波 / 总线调试 / MAP 2.0` | `工业高刷示波 / 总线调试 / 现代极速架构` |
| 个人博客 `about/index.md` | `采用全新 MAP 2.0 极速元架构` | `采用现代极速桌面架构（FastAPI + WebSocket + Vue 3 + WebView2）` |
| 个人博客 `personal-homepage.md` | `采用全新 MAP 2.0 极速元架构` | `采用现代极速桌面架构（FastAPI + WebSocket + Vue 3 + WebView2）` |

---

## 三、 GitHub 仓库重命名与全域生态链接迁移

### 1. 仓库 URL 映射标准化

所有指向代码仓库与发布下载的链接统一升格为正规域名：
- **旧仓库地址**: `https://github.com/WenZhenJian-EE/Serial-CAN-Debugger-V2`
- **新规范地址**: `https://github.com/WenZhenJian-EE/Serial-CAN-Debugger`
- **Release 发布直链**: `https://github.com/WenZhenJian-EE/Serial-CAN-Debugger/releases`

### 2. GitHub 官方重命名与 API 自动化落地

已通过 GitHub REST API 成功将仓库从 `Serial-CAN-Debugger-V2` 重命名为 **`Serial-CAN-Debugger`**，并同步更新了仓库 Description、Homepage 以及工控标签主题（`topics`）。
*(注：GitHub 会对历史 `Serial-CAN-Debugger-V2` 自动保留永久 301 重定向，任何旧链接访问都不会失效)*

### 3. 本地 Git Remote 迁移指令

本地工程已成功绑定至新仓库地址：
```bash
git remote set-url origin https://github.com/WenZhenJian-EE/Serial-CAN-Debugger.git
```

---

## 四、 成果与工程收益

1. **产品定义零歧义**：彻底杜绝“MAP 分析软件”的误会，将软件纯正定位于串口 / CAN / CAN-FD 高速示波与现场总线调试利器；
2. **开源品牌专业度提升**：去除 `-V2` 历史补丁感，树立正式、纯正的开源工控旗舰形象；
3. **全域资产 100% 同步**：主程序、编译脚本、前端 UI、说明文档、个人博客与 Git 配置全链路实现一次性无缝对齐；
4. **拒绝抽象黑话，确立【上位机】直白表达**：坚决摒弃“高刷示波与总线调试终端”等过于抽象学术的词汇，直面硬件工程师核心认知，全域统一定义为【支持串口、CAN 与实时示波器调试的上位机】。
