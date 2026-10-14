> 历史记录：Phase 13 已将开发机路径通用化。文中的源代码 / validation / dist 路径相对仓库根目录；原始验证数据不随 Git 提供。当前开发步骤见 [README 开发者指南](../../README.md#开发者指南)。

# Phase 12.6 — Apple-inspired UI Refinement

日期：2026-10-12。状态：**COMPLETE WITH KNOWN VALIDATION LIMITATIONS**。

## 实现与验证（按续接要求的 32 项）

1. **Event loop stall 根因**：50 ms GUI 轮询无条件重新 configure / pack / place，反复触发原生控件重绘；新增 ttk 九宫格圆角素材原为 32×32，大容器边距各 16 px，中心区域为零，小控件中心也过小，放大了原生绘制开销。没有发现 Configure 递归或每帧创建 Canvas / 图片。停轮询对照、cProfile、主题对照及素材尺寸对照均保留在验证目录。
2. **修复**：控件最终状态变化时才 configure，避免先设 normal 再覆盖 disabled；空状态、开始 / 停止按钮仅在显示状态变化时 pack / place；图片初始化一次并复用。圆角素材改为 128×128，保留充足平铺中心，ttk 最小控件尺寸独立固定为 32，圆角和外观没有撤回。新增空中心拒绝检查。
3. **UI layer**：保留 DesktopApp / Controller 接口。`ui_theme.py` 定义 tokens 与 ttk layouts，新增 `ui_shapes.py` 生成小型装饰素材；`gui.py` 仅调整展示布局和重复刷新。Core 文件与 Phase 12.5 哈希比较。
4. **自绘范围**：使用 Tk PhotoImage 生成圆角装饰与滑动开关轨道 / thumb，交互仍由 ttk Button / Checkbutton / Combobox / Notebook 执行。不增加独立 Canvas 事件状态机，不持续动画。
5. **设计语言**：白色、极浅蓝灰、柔和蓝色；任务区优先，减少边框与并排工具，圆润控件、安静的辅助文字。仍是 Windows 应用，不仿制 macOS 标题栏或字体。
6. **Color Tokens**：背景 #F8FBFF、内容白色、辅助 #F2F7FC、激活 #EEF6FF、主色 #4D86C6、正文 #1F2937、辅助 #6B7280，统一在 COLORS。
7. **Spacing Tokens**：SPACE 为 4 / 8 / 12 / 16 / 24 / 32。文件设置共享标签列；阅读面板使用 12 的内边距。小窗口优先保留任务与字幕空间。
8. **Radius Tokens**：control 8、button 12、surface 16。开关使用完整圆轨道。九宫格素材尺寸不等于控件尺寸；所有状态素材同尺寸、同边距。
9. **Shadow Tokens**：SHADOW 为极浅 #E6EBF2、1 px 层次，用于 selected / 阅读面板边缘。采用克制的静态边缘层次，没有实时模糊或重投影系统；不是 macOS 原生模糊阴影。
10. **Typography**：系统微软雅黑 UI / Segoe UI，标题 17 pt、section / transcript 11 pt、正文 10 pt、辅助 9 pt；不打包 Apple 字体，减少普通标签粗体。
11. **Segmented Navigation**：继续顶部圆润双段导航，浅底、选中浅蓝与轻边缘；不使用固定 Sidebar。Notebook 页面及键盘接口保留，selected / hover / pressed 的 padding、字体与 geometry 不变。
12. **Buttons**：Primary 柔和蓝底白字，文件页放右侧；Secondary 白色 / 浅蓝；Tertiary 降低强调。统一圆角，禁用与焦点保持固定尺寸。
13. **Toggle**：翻译和悬浮字幕使用 36×20 轨道及圆形 thumb，灰色 OFF / 蓝色 ON；绑定现有变量及命令，支持键盘和 disabled，无动画。Overlay toolbar 或快捷键修改可同步回开关。
14. **Checkbox**：输出格式继续 Windows vista 原生 indicator，选中为标准勾选，绝不使用 × 或 Unicode 模拟。
15. **Combobox**：保留原生下拉、键盘选择和显示标签映射；仅替换圆角 field 外观，统一 padding 与 focus 边缘。
16. **Drag & Drop**：大圆角浅蓝空状态，提示居中、无大图标；文件加入后显示列表，复用既有 TkDnD 绑定，不改变文件去重和格式检查。
17. **File List**：保留稳定 Treeview，32 行高、轻表头、无粗网格线；表头与对应单元格统一左对齐，时长 / 状态仍有中文文本。未更换数据模型。
18. **File 设置对齐**：任务区置于顶部，设置位于下方、主操作靠右；识别语言、中文翻译、质量、输出格式与目录共享固定宽度左对齐标签列。按钮或 Empty State 的居中不影响表单轴线。
19. **Realtime**：来源与当前设备在上方，字幕为主体；翻译、悬浮字幕和显示模式在下方。质量、快捷键、会话导出 / 恢复等低频选项放入“更多设置”，原命令不变。
20. **Transcript Panel**：白色圆润阅读面板、英文在上中文在下，partial 较浅，不为每句添加边框。保留 Phase 12 的最后非空行滚动修复。
21. **Empty State**：文件提示和实时“等待开始”居中，只是展示控件，不进入 Session、transcript 或导出数据。
22. **Overlay**：复用圆润轻量按钮，保留半透明深色字幕底、编辑 / 观看 / 穿透 / 字号等原实现。原生无边框窗口外轮廓未引入新的裁切或 DWM hack，工具条圆角不等同于整个窗口圆角。
23. **DPI**：100% / 125% / 150% Tk scaling 受控检查。验证器临时放宽窗口最大尺寸，实际核对 1920×1080，避免显示器工作区截断后误报。不是 Windows 物理 DPI / 多显示器认证。
24. **Small window**：880×600、1366×768、1920×1080，文件进度始终可见，标签轴线一致；最终 packaged 字幕面板在 880×600 下高度 207–215 px（受控测试），没有提高最小窗口尺寸。
25. **GUI responsiveness**：修复后受控 5.004 秒空闲消耗 CPU 0.0625 秒，最大心跳间隔 32.7 ms；图片数量在重复 theme / resize / 切页后稳定。修复前 5.001 秒消耗 3.844 秒 CPU。数据为真实 Tk + fake Core，不冒充 ASR 延迟或长期无泄漏认证。
26. **自动测试**：280 项全量测试通过，48.782 秒（269 基线 + 11 新测试）。原有线程、停止、导出、Session、Recovery 与 ASR / 翻译断言保留；旧视觉断言仅更新 Toggle 渲染方式。
27. **Packaged EXE**：独立 `dist/LocalASR-Phase12.6`，最终隔离 EXE full / startup 验证均 exit 0，完整 PASS，无 crash、无残留。文件转录、翻译、双语 DOCX、五种导出、系统音频及九组布局通过。详见下方人工收尾记录。
28. **Candidate size**：**2,497,279,284 字节（2.497279284 GB）**；比 Phase 12.5 增加 **7,978 字节**。最终验收未改代码、未重新构建。
29. **依赖**：没有新增或升级依赖，所有 Python / 测试 / 构建均使用 Conda asr。装饰素材在运行时由 Tk 生成，不新增字体、图片库或 native runtime。
30. **相对 Phase 12.5**：新增圆角与 pill 开关，任务区前置、文件设置成列、表头左对齐；实时低频设置收起、字幕占比增加，保留原架构和核心能力。
31. **Known limitations**：耳机、真人麦克风讲话、实体多显示器 / Windows 物理 DPI、Explorer 跨窗口拖放、完整跨应用穿透、白 / 黑 / 彩色视频逐项物理验收、干净 Windows 机器与长期运行认证均不得推定通过。设计采用静态轻边缘层次，Overlay 外轮廓仍保留现有原生窗口行为。
32. **Verdict**：**Phase 12.6 COMPLETE WITH KNOWN VALIDATION LIMITATIONS**。未发现阻塞问题；完成后停止，不进入下一阶段。

## 变更与证据

UI：`src/gui.py`、`src/ui_theme.py`、`src/ui_shapes.py`、`src/ui_strings.py`；验收：`src/ui_visual_audit.py`；测试：`tests/test_ui_refinement.py`、`tests/test_visual_theme.py`；构建仅在 `distribution/build.py` 增加 `--phase12-6` 独立目标。

证据目录：`validation/phase12_6/`。其中 `responsiveness-before-tile-fix.json` 为未完成修复时的数据，不能当作最终性能；`responsiveness.json` / `regression-final.txt` / `core-audit.json` / `chinese-audit.json` / `source-hashes.json` 为最终源码验证链。故障注入测试日志内预期异常不等于测试失败。

构建：`conda run -n asr --no-capture-output python distribution/build.py --variant optimized --phase12-6`。

## 最终 packaged 人工验收收尾

- 最终 EXE：`<checkout>/dist\LocalASR-Phase12.6\LocalASR.exe`。SHA256：`26DC7688E71DA04FEBC290A95C0BC03E3103798C820303B7383CBA6407A3DBDC`。实际人工操作使用该构建的隔离副本，`interactive.json` 确认 frozen=true；不是 Conda GUI。
- 拖放范围：真实 packaged 内部 TkDnD 原生拖放两次，首次加入音频并显示 0:11，第二次去重。通过系统文件选择器添加不支持的 Markdown 文件，中文提示正确且未入列。后者不是“不支持文件原生拖放”的单独物理验证；Explorer 跨窗口拖放仍未验证。
- 文件列表：加入既有 100 个测试 WAV，加原始文件共 101 行。实际滚到末尾，时长、就绪状态正确，进度条和底部操作始终可见；无重叠、明显滚动卡顿。没有启动这 101 个文件的批量转录。
- 连续交互：本次人工会话约 483 秒（包含截图观察与操作间隔，并非 483 秒连续输入）。实际切页、选中导航、勾选格式、翻译 OFF/ON、语言下拉切换、长列表滚动；未出现卡死、明显闪烁或布局跳动。边缘缩小拖动未改变当前尺寸，不能把该动作单独算作尺寸验证；尺寸变化依据最终九组受控布局检查。Hover/pressed 固定尺寸同时由最终状态几何检查支持。
- 实时和 Overlay：同一最终 EXE 的独立 150.641 秒真实系统回采会话，实际观察英文、中文及悬浮字幕持续更新；运行中切页正常，观看模式隐藏工具条、主窗口开关隐藏 Overlay 正常。不是真人麦克风讲话测试。
- 系统回采记录 32 个 final 事件、32 个 translation 事件（包含空识别结果），0 错误，audio drop=0，translation drop=0；partial 丢弃计数为 5，不能称所有事件零丢弃。最后一次 ASR endpoint latency 0.734 秒、translation latency 0.344 秒、总延迟 1.078 秒；这些为末次值，不是均值。TXT / DOCX / JSON / SRT / VTT 五种会话导出完成。英文 / 中文最终文字可见性记录均通过；切到文件页时 partial 控件不可见属于隐藏页面，不当作滚动缺陷。
- 视觉结论：白色与极浅蓝、统一圆角和留白、轻边缘层次符合本次 Apple-inspired 方向；相对 12.5 的 pill 开关、设置轴线、阅读区比重改善明确。导航有分段层次、设置统一左对齐、列表弱化网格，实时阅读区是主体。Checkbox ✓、Toggle thumb、原生下拉显示正常。保留原生 Windows 标题栏、下拉行为及轻量静态阴影，不宣称 macOS 原生外观；无需继续主观微调。
- 中文一致性：217 条集中文案；源码扫描与 frozen 扫描无新增主要界面英文回归。本次人工入口扫描 70 个标签，0 violation。
- 性能范围：人工未见明显停滞；空闲 CPU 与图片复用依据第 25 项受控数据，系统音频进程采样另存 `system/process-samples.csv`。不把 ASR / 翻译推理 CPU 使用算为 UI 绘制负载，也不把短观察称作长期无泄漏认证。
- 退出：系统会话和人工会话均 clean_shutdown=true，人工关闭后 LocalASR 进程数为 0。
- 自动测试继续引用最后一次完整 **280 / 280 PASS**；此后只有报告与验收记录修改，没有代码修改，因此按要求不重复全量测试或已经通过的 packaged 全套验证。
- Phase 10 / 11 / 12 / 12.5 回退目录保持原状，哈希及大小记录见 `rollback-builds.json`。没有新增依赖，也未覆盖正式基线。
- 已知验证限制：耳机、实体多显示器、物理 Windows DPI、Explorer 跨窗口拖放及第 31 项未实际执行的物理场景继续保留。macOS 尚未实现。这些不阻止本阶段完成。

最终证据：`packaged.log`、`packaged/`、`interactive.json`、`system/report.json`、`system/process-samples.csv`、`build-size.json`、`regression-final.txt`。本次仅完成验收与文档；不进入下一阶段。



