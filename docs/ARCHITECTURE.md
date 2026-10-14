# 架构概览

GUI 只收集输入、调用 Controller、消费事件。模型加载、推理、翻译和批处理不在 Tk 主线程运行。

| 边界 | 模块 / 职责 |
| --- | --- |
| File ASR | `batch.py`、`transcriber.py`：批次与延迟加载；`result.py` 保存真实 segment 时间 |
| Realtime ASR | `realtime.py`、`realtime_audio.py`：有界队列、VAD 组句、独立推理及 partial / final 事件 |
| AudioSource | `audio_sources.py`、`windows_system_audio.py`：麦克风与 Windows 默认播放设备回采；不实现混音 |
| Translation | `translation.py`：独立本地 Marian / OpenCC；`realtime_translation.py` 仅对 final 入独立有界翻译队列，CPU 工作进程隔离 |
| Session | `realtime_document.py`：已确认文本、译文、恢复及会话导出，partial 不覆盖 final |
| Export | `formatter.py` / `exporter.py`：自然段落、五种格式与完整性记录；字幕沿用 ASR 时间 |
| UI | `gui.py` / `gui_controller.py`、`ui_*`：状态桥接、中文文案、主题和展示；`subtitle_overlay.py` 悬浮字幕 |
| Model Registry | `model_registry.py` / `model_download.py` / `model_catalog.json`：本地发现、固定 revision、完整性检查、按需下载 |
| Hardware | `hardware.py` / `recommendation.py`：优先检测 CTranslate2 能力，选择模型与精度、CPU 回退 |
| Distribution | `desktop_entry.py` / `desktop_platform.py` / `app_paths.py`、`distribution/`：freeze 支持、资源与用户数据分离、standalone 构建 |

文件链路：输入 → ASR → 原文检查点 → 可选逐段翻译 → 所选格式导出 → completion record。

实时链路：持续采集 → 音频有界队列 → VAD / utterance → ASR → partial / final → UI；final 另送翻译队列 → 中文事件 → Session / UI / Overlay。翻译失败保留英文，不阻塞采集。

停止会协调采集、推理、事件、翻译进程与队列；文件任务采用现有安全边界停止，不强杀正在导出的工作。UI 状态轮询只在状态变化时重新布局，圆角素材创建后复用。

版本由 `src/app_version.py` 唯一定义；诊断为白名单结构，不序列化 transcript 或原始日志。更详细的历史决策见 [开发历史](development/VALIDATION.md)。
