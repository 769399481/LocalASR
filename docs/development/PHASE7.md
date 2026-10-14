> 历史记录：Phase 13 已将开发机路径通用化。文中的源代码 / validation / dist 路径相对仓库根目录；原始验证数据不随 Git 提供。当前开发步骤见 [README 开发者指南](../../README.md#开发者指南)。

# Phase 7 — 实时会话导出与两页 GUI

启动：`conda run -n asr --no-capture-output python src/gui.py`

使用既有 Tkinter/ttk 和 Conda asr，无新增或升级依赖。模型策略不变：文件 large-v3，实时 small CUDA/float16，Marian + OpenCC 翻译 CPU。

## 两页工作流

独立 Settings 页面及导航已移除，原 Settings 配置类和已有配置兼容保留；内部模型路径仍可从旧配置读取，但不出现在普通用户页面。

- **文件**：添加单个/多个文件、状态列表、English/Chinese/Auto、英文→简体中文开关和固定目标、五种输出格式、输出目录、Start、停止批次、打开输出目录。沿用 BatchProcessor/Exporter；停止等待当前文件安全完成，其他未处理文件仍为 Pending。
- **实时**：麦克风及刷新、翻译开关、Start/Stop/Clear/Save-Export、恢复会话、输出格式/目录、打开输出目录。英文 partial 独立更新，final 保留；停止后双语内容不清空。

两个页面共享输出目录、格式和翻译偏好。启动任务及关闭时异步保存偏好到 `gui_settings.json`，包含最后语言、翻译开关、格式、目录、麦克风。用户不需要配置 CUDA、VAD、queue 或技术后端。

## 会话数据与恢复

`src/realtime_document.py` 独立于 GUI。RealtimeDocument 保存 session_id、带时区 started_at/ended_at、duration、源/目标语言、翻译开关、segments、修订号与导出记录。每个 FinalSegment 保存 segment_id、原 start/end、original_text、translated_text、translation_status、created_at。状态为 disabled/pending/completed/failed；partial 永远不进入正式文档。

duration 是会话墙钟时长（含准备、等待），字幕始终使用 final 自己的音频采样时间轴。Core 回调先更新会话，再通知 GUI；提前到达的翻译按编号暂存对齐，旧会话事件忽略。GUI 仅保留约千行显示历史，正式导出来自完整会话，不读取 Text widget。

每次 final、翻译完成/失败和停止后，由一个后台 IO worker 合并最新快照，写入 `recovery/<session_id>.json`。流程为临时文件→flush/fsync→原子替换，失败保留上一次有效文件；partial 不写磁盘。恢复文件包含正文，仅在本地保存。

启动时提示已有 recovery；“恢复会话”可打开恢复 JSON 或导出的完整 JSON。后台校验失败不会覆盖当前会话；中断时 pending 翻译恢复为 failed，保留英文，不自动重新翻译。没有数据库、云备份或自动历史清理。

Start 遇到已有内容时明确确认，旧恢复文件保留。Clear 对未导出修订要求确认；只清空当前工作视图，旧恢复文件仍保留。恢复写入失败时需先成功导出，才能清空或开始新会话。关闭时安全停止 Core 并等待 IO；若恢复失败，明确询问是否仍退出，不能假报保存成功。

突然断电仍可能丢失最后一次未完成的异步写入；这是基础恢复能力，不是零丢失保证。

## 导出与未完成翻译

会话转换为已有 TranscriptionResult/TranslationResult，复用 Exporter 的自然段、双语分组、时间格式、暂存发布和摘要记录。Exporter 只增加可选的 session_data/bilingual_txt 参数，文件流程默认行为不变。

- TXT：英文或双语自然段。
- DOCX：Calibri 11 pt、左对齐、1.15 行距、8 pt 段后距；沿用约四段/600 字符分组，英文在前、对应中文在后。失败译文显示占位说明，不阻止英文保存。
- JSON：始终随实时导出附带，UTF-8。保留原有 text/language/duration/segments，新增 `realtime_session` 保存完整元数据、逐段双语状态、修订和导出记录。它不同于 `.complete.json` 摘要记录。
- SRT/VTT：默认英文，严格复用 final start/end，不估算或拆分时间轴。

采集中点击导出会先 Stop，等待约 10 秒；尚有 pending 或 Core 未停时，明确提供“仅保存英文快照”或“取消导出并继续等待”。英文快照 JSON 仍保存已有译文和 pending 状态，后续更新属于新修订，需要再次导出。正常停止后未返回译文记录为 failed。

导出名为 `realtime_日期_时刻_会话短ID`，重复导出追加数字；排他占位文件保证不覆盖同名输出。翻译失败时可读文档照常输出，但原 Exporter 的 translation complete 仍为 false，不将失败误判为完整双语。

## 测试与验证（2026-10-09）

**139 项自动测试通过**，含 Phase 1–6 回归。新增结构化会话、partial 排除、乱序翻译、五格式/双语 Word、pending/failed、恢复损坏/写入失败、命名冲突、新会话/Clear 保护、两页控件、缩小窗口、响应性和关闭清理。

可重复的可见 GUI 回放（使用已有合成英文 WAV，不是真人麦克风）：

```powershell
conda run -n asr --no-capture-output python tests/manual_gui_session_replay.py --auto-close
conda run -n asr --no-capture-output python tests/manual_gui_session_replay.py --translate --auto-close
```

真实 GPU Whisper/CPU 翻译回放各生成 3 条 final、五种输出和恢复文件。50 ms GUI 定时器最大间隔约 0.156 秒（英文）/0.125 秒（双语）。报告及输出位于 `validation/phase7-gui/`。这不是长期稳定性或端到端延迟评测。

Windows 界面工具实际检查：两页布局、Stop 后双语保留、点击 Save/Export 成功且不覆盖、新会话确认并取消后保留内容、退出重启后从恢复文件还原。英文和双语 DOCX 均在 Microsoft Word 打开，段落可读、双语顺序正确；SRT/VTT 时间与 final 对应。Clear 确认和崩溃恢复使用安全自动测试，没有破坏用户数据。

**未完成真人麦克风朗读的 A/B 验收。** 本次语音来源为合成音频回放，不能称为真人麦克风测试。受限执行沙箱无法启动当前 Conda/Tk，所有 Python 验证在正常桌面下的 asr 环境执行，没有重装环境。

## 已知限制及 Phase 8 建议

尚需真人噪声环境和长会话压力测试。会话快照仍整体序列化；没有 History 列表、磁盘配额清理或失败翻译重试。文件名含会话短 ID，恢复文件含正文且不会自动删除。原有 ASR 幻觉、硬切块、冷启动翻译延迟仍存在。

Phase 8 优先真人麦克风验收、长会话恢复/磁盘压力测试，再考虑简洁历史浏览与失败翻译重试；不优先引入硬件管理器或安装包。


