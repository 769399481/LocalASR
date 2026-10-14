> 历史记录：Phase 13 已将开发机路径通用化。文中的源代码 / validation / dist 路径相对仓库根目录；原始验证数据不随 Git 提供。当前开发步骤见 [README 开发者指南](../../README.md#开发者指南)。

# Phase 12.5 — Visual Polish

日期：2026-10-11–12。状态：**COMPLETE WITH KNOWN VALIDATION LIMITATIONS**。仅视觉与交互状态整理，保留 Phase 12 信息架构及 Core。最终候选验收结果见文末。

## 设计与实现（按本阶段要求）

1. **视觉方向**：白色、极浅蓝、浅灰；保留原有两页结构，降低设置区视觉权重，让文件任务与字幕内容更突出。无渐变、动画、深色主题或新框架。
2. **Theme Tokens**：`src/ui_theme.py` 集中定义 `COLORS / SPACE / TYPE / CONTROL`，主界面、模型 / 帮助窗口、Overlay 复用。
3. **Spacing System**：4 / 8 / 12 / 16 / 24 / 32；页面边缘、行距、按钮间距、设置区及对话框迁移到同一组参数，紧凑布局保护小窗口。
4. **颜色**：背景 `#F8FBFF`，内容表面白色，辅助表面 `#F2F7FC`，选中区 `#EEF6FF`，强调蓝 `#4D86C6`，正文 `#1F2937`，辅助文字 `#6B7280`，边框 `#DDE7F0`。
5. **主导航**：仍使用原有 ttk Notebook，两页标签文字和字体不变；选中使用浅蓝背景 / 深蓝文字，不通过改大小表达选中。
6. **状态 geometry**：消除 clam 默认 selected tab expand，所有状态 expand 为零、padding 相同；按钮 `shiftrelief=0`。测试 normal / active / pressed / disabled / selected / focus 的位置、实际尺寸和请求尺寸。最终 EXE 另有同类控件状态审计。
7. **阴影等价层次**：使用固定 1 px 浅蓝灰边框与浅蓝选中背景，不引入真实投影、Canvas、额外渲染系统或尺寸补偿 hack。
8. **Checkbox 修复**：根因是 clam 的 indicator 绘制样式，而非中文字体。借用 Windows `vista` 主题原生 `Checkbutton.indicator`，替换为 `NativeCheck.indicator`；不使用“✓”文字替换、图标字体或字符覆盖。Windows 实际预览已看到标准白色勾选标记。其他平台的 alt fallback 未作物理认证。
9. **Toggle / Checkbox**：格式多选使用标准 Checkbox；功能开关使用独立 `Toggle.TCheckbutton` 样式和明确中文标签。采用用户允许的轻量 Checkbutton 方案，没有为滑动开关新增 Canvas 状态机。悬浮字幕继续使用现有显示 / 隐藏按钮。
10. **Combobox**：集中 padding、白色输入区、轻边框和柔和 focus 色；字体不随状态改变，保持现有键盘 / 显示标签到 Core 标识映射。
11. **文件拖拽区**：简洁提示“拖拽音频或视频文件到这里”、格式说明及“选择文件”按钮。整个空状态及子控件继续接入原生文件拖放；加入文件后隐藏，不挤占列表空间。
12. **文件列表**：保留 Treeview，行高 32，浅色 heading、白色内容、浅蓝选中，不重做表格或行数据结构。中文状态始终保留，不只依赖颜色。
13. **文件按钮层级**：开始为 Primary；添加、目录、导出为 Secondary；移除、清空和低频设置为 Tertiary。危险操作常态不使用大红填充，原确认逻辑不变。
14. **实时页层级**：保持来源 / 设备 / 字幕 / 操作结构，通过减少边框、弱化辅助文字、压缩工具行间距增加字幕空间，未折叠设置以避免增加复杂状态。
15. **Transcript**：英文 final 与中文使用清晰正文，partial 使用次级色；移除文本框厚边框。Phase 12 非空末行自动滚动修复保留，数据与事件协议不变。
16. **Empty State**：文件空状态可选文件；实时空状态显示“等待开始”和操作指引。提示只是展示控件，不插入 transcript、Session 或导出数据；partial / final 到来后隐藏。
17. **Overlay**：中性深色 `#20262E`、白字、原有默认 0.85 透明度；轻工具条、纯文字按钮。保留字体、透明度、模式、拖动、编辑 / 观看和原生穿透实现。观看模式隐藏工具条，未添加动画。
18. **字体层级**：17 标题、11 section / transcript、10 正文、9 辅助的集中参数；优先系统微软雅黑 UI，英文使用现有 Segoe UI。未打包字体。
19. **图标**：纯文字按钮与系统原生 checkbox，未新增 Emoji / PNG / icon 库或混用图标资源。
20. **边框**：内容区和 Labelframe 去除明显外框；输入、导航使用固定轻边框；focus / active 仅改变颜色。错误文字复用集中错误色。
21. **小窗口**：完整回归包含 880×600、100 行文件列表滚动及底部进度预留；未提高最小窗口尺寸。
22. **DPI**：重新检查 125% / 150% Tk scaling，880×600 / 1366×768 / 1920×1080 几何。属于受控布局验证，不冒称真实切换 Windows DPI 或多显示器。
23. **中文一致性**：212 条集中目录扫描通过；主要控件、First-run、下载和错误说明扫描无禁用英文残留。格式名称、用户内容和设备厂商名保留原样。
24. **自动测试**：**269 项通过，55.373 秒**。原 256 项回归保留，新增 13 项主题 / spacing / geometry / checkbox / empty state / toggle / combobox / 缩放测试。不依赖截图像素。日志内故障注入异常是预期测试数据，不是失败。
25. **人工视觉**：源 GUI 已实际检查文件页、实时页、导航来回、原生勾选、翻译开关和双语空状态；最终 packaged 操作记录在文末，不用源 GUI 冒充 EXE 验证。
26. **Packaged EXE**：独立 `dist/LocalASR-Phase12.5`；仅增加独立构建目标参数，未改变 PyInstaller 架构、运行库方案或模型策略。真实 EXE 的核心、中文界面与视觉状态验收通过，详情见文末。
27. **体积**：最终目录 **2,497,271,306 字节（2.497271306 GB，十进制）**，比 Phase 12 的 2,497,263,772 字节增加 **7,534 字节**；无体积异常，不进行 DLL 瘦身或引入新 runtime。
28. **依赖**：无新增依赖，无现有依赖升级；继续使用 Tk/ttk 和既有 tkinterdnd2，主题仅 Python 源码。
29. **限制**：资源管理器跨窗口拖放、实体多显示器 / Windows DPI 切换、耳机、真人讲话等既有物理验证缺项继续保留；不把受控测试写成实际硬件认证。
30. **结论**：**Phase 12.5 COMPLETE WITH KNOWN VALIDATION LIMITATIONS**。全部 269 项测试、最终 EXE 核心回归和本阶段视觉验收通过。物理验证边界见下文；保留独立候选，不改写 Phase 10 正式版本记录。停止在 Phase 12.5。

## 文件与证据

- 主题：`src/ui_theme.py`；接入：`src/ui_support.py`、`src/gui.py`、`src/setup_ui.py`、`src/subtitle_overlay.py`、`src/ui_strings.py`。
- 测试：`tests/test_visual_theme.py`；独立 frozen 验收：`src/ui_visual_audit.py`、`src/packaged_check.py`。
- 构建：`distribution/build.py` 仅增加 `--phase12-5` 独立输出目标，旧 Phase 10 / 11 / 12 不作为清理目标。
- `validation/phase12_5/core-audit.json`：与 Phase 12 哈希比较，ASR / Translation / Realtime audio / Session / Recovery / Export / Model Registry / Hardware Detection / System Audio Core 未变化。
- `validation/phase12_5/regression-final.txt`、`chinese-audit.json`、`source-hashes.json`：最终回归、中文扫描及源文件溯源。
- `validation/phase12_5/edit_visual.py` 为已执行的一次性修改记录，**不要再次运行**；不是构建依赖。

复现构建：`conda run -n asr --no-capture-output python distribution/build.py --variant optimized --phase12-5`。测试：`conda run -n asr --no-capture-output python -m unittest discover -s tests -q`。

## 最终候选验收（2026-10-12）

交付路径：`<checkout>/dist\LocalASR-Phase12.5\LocalASR.exe`。运行时需要保留整个候选目录。EXE SHA-256：`205783DD4E7264148E101B058DE249430CD8A44EA90AEC96B2596698DF7718F6`。

真实验收使用该目录的隔离副本，位于 `<isolated-validation>/LocalASR/LocalASR.exe`。Core 回归清理 PATH / Conda / Python 环境，使用独立用户目录和本地模型；不是 Conda GUI。验证机仍安装了开发环境，不能等同于全新 Windows 物理机。

| 检查 | 最终结果与证据范围 |
| --- | --- |
| 导航与控件 | frozen 状态审计检查 15 个控件，selected / active / pressed / disabled / focus 均无几何差异；导航两项可点击跨度均为 106 px，切页前后相同。实际鼠标切页观察无缩放。 |
| Checkbox | packaged 使用 Windows vista 原生 indicator；实际取消 / 勾选 TXT，标准白色勾选可见，不再是 ×。不依赖字体替代。 |
| 文件页 | 实际原生拖入 11 秒测试音频，再经文件选择器加入 100 个验证副本；101 行可滚动至 lesson-100，底部进度、统计和状态始终可见，时长显示 0:11。 |
| Drag & Drop | `interactive.json` 记录一次真实 native drag、copy 结束及 native_drop_added=true。**已验证应用内原生拖放路径；未验证资源管理器跨窗口拖入。** |
| 文件 Core | 真实 large-v3 CUDA/float16 文件转录与 CPU Marian/OpenCC 翻译通过，五种输出完整，双语 DOCX 通过；缺少 VTT 时 completion 正确判断未完成。 |
| 实时页 | 实际空状态、系统音频英文 partial/final 与中文、按钮及层级观察通过。60 px 英文框 23 次、53 px 中文框 22 次、partial 43 次可见性检查均通过；未滚到纯空白尾行。 |
| 实时 Core | small GPU 回放、WebRTC VAD、翻译及麦克风设备枚举通过；实际麦克风启停两次并收到帧，未验证真人讲话。 |
| 系统音频 | Windows 默认 Realtek 输出回采既有测试语音，经英文 ASR → 简体中文 → Overlay；23 个 final、23 个翻译完成，音频和翻译丢弃均为 0，无错误。 |
| Overlay | 实际双语字幕可读；轻工具条、透明度调整并恢复、观看隐藏工具条、主窗口恢复编辑、显示 / 隐藏操作通过。跨应用鼠标穿透的完整物理交互未补验。 |
| Session / Recovery / 输出 | 系统音频会话保留恢复记录，TXT / DOCX / JSON / SRT / VTT 均实际生成；原自动恢复与导出回归保留。 |
| First-run / 中文 / 诊断 | 空用户目录首次启动、模型缺失中文提示、诊断、离线启动通过；下载取消 / 重试 / 完整性用受控本地资源验证，不声称真实互联网下载。源文案 212 条，frozen 文案扫描无违规项。 |
| 小窗口 / DPI | 自动受控测试覆盖 880×600、1366×768、1920×1080 和 125% / 150% Tk scaling；packaged 实际小窗口列表与字幕通过。未物理改变 Windows DPI，未验证实体多显示器。 |
| 安全退出 | Core、系统音频和交互报告均正常结束；窗口关闭后再次检查 LocalASR.exe，残留进程为 0。 |

人工操作通过 Computer Use 对真实 EXE 执行并观察；几何与文本可见性用控件状态检查，未采用截图像素断言。实际输入使用窗口坐标，工具返回的 screenshotId 缓存失效仅影响工具调用，重新观察后按受支持的窗口坐标方式完成操作。

## 性能与体积

本次系统音频采集记录 98.172 秒。中位数 / P95 分别为：ASR 语音结束至 final **0.734 / 0.797 秒**，final 至中文 **0.375 / 3.156 秒**，语音结束至中文 **1.110 / 3.859 秒**。翻译预热 8.328 秒，首次翻译等待会拉高尾延迟，不能只报稳定阶段数字。完整统计见 `validation/phase12_5/performance-summary.json`。

独立短回放中首条翻译延迟 8.235 秒（包括首次加载 / 等待），有 1 次可覆盖 partial 被丢弃；final、音频与翻译均未丢失。真实系统音频一轮 partial 丢弃也为 0。两种验证不合并为“所有事件始终零丢弃”。

完整打包验收启动记录：GUI 创建 2.256 秒、GUI ready 21.908 秒（含环境 / 模型检查），文件模型加载 5.437 秒。Windows 文件缓存未清空，非冷启动基准。短测尾部进程合计 RSS 约 1.595 GB，期间 GUI 可操作；短测不能证明长期无内存泄漏。

| 构建 | 总字节数 | 保留情况 |
| --- | ---: | --- |
| Phase 10 stable | 2,494,371,015 | 目录大小、EXE 哈希复核未变 |
| Phase 11 candidate | 2,494,297,628 | 目录大小、EXE 哈希复核未变 |
| Phase 12 final | 2,497,263,772 | 目录大小、EXE 哈希复核未变 |
| Phase 12.5 candidate | 2,497,271,306 | 独立目录，增加 7,534 字节 |

无新增第三方依赖、字体、图标包或 native runtime。所有最终源文件哈希与构建前快照一致；与 Phase 12 的 Core 哈希审计仍通过。

## 已知验证限制与证据索引

未实际完成：耳机专项、真人麦克风讲话、实体多显示器与 Windows 物理 DPI 切换、资源管理器跨窗口拖放、完整跨应用鼠标穿透、白 / 黑 / 彩色视频背景逐一物理验收、干净 Windows 机器与长期运行认证。默认 0.85 中性深色背景上的双语已观察，但不把该观察扩大成所有视频背景验证。上述范围不影响本阶段已完成的视觉修改验收。

证据：`validation/phase12_5/packaged/`（full / startup / isolation / shutdown）、`system/`（真实回采、输出、恢复记录、日志、进程采样）、`interactive.json`（原生拖放、101 行任务、中文与关闭）、`build-sizes.json`、`performance-summary.json`、`acceptance.json`。公开发布前仍需沿用原有许可、签名及干净环境核验清单，本阶段不制作 Installer 或清理仓库。


