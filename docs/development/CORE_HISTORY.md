> 历史记录：Phase 13 已将开发机路径通用化。文中的源代码 / validation / dist 路径相对仓库根目录；原始验证数据不随 Git 提供。当前开发步骤见 [README 开发者指南](../../README.md#开发者指南)。

# Local ASR Desktop — Phase 8

Windows 本地语音转文字桌面应用。GUI 保留文件和实时两页，启动时后台检测硬件并选择已安装模型，提供 Auto / 可用质量档位、CPU 回退提示。支持实时会话恢复及五种格式导出。最新策略、资源依据及验证见 [PHASE8.md](PHASE8.md)，会话使用说明见 [PHASE7.md](PHASE7.md)。以下保留各 Core 阶段说明；未实现安装包或云服务。

```powershell
conda run -n asr --no-capture-output python src/gui.py
```

## 开发环境

只在现有 Conda `asr` 环境中开发、安装依赖和测试：

```powershell
conda activate asr
python --version
where.exe python
python src/main.py
```

如果当前终端未加载 Conda 激活脚本，可使用等效的明确环境调用：

```powershell
conda run -n asr --no-capture-output python src/main.py
conda run -n asr --no-capture-output python -m unittest discover -s tests -v
```

2026-10-05 本机实际验证：Python 3.11.15、faster-whisper 1.2.1、CTranslate2 4.8.1、PyTorch 2.6.0+cu124、python-docx 1.2.0；RTX 3060 Laptop GPU；PyTorch CUDA 12.4；CTranslate2 检测到 1 块 CUDA 设备，支持 float16。

`requirements.txt` 仅列核心依赖并固定当前版本，不是整个 Conda 环境快照。现有工作环境无需重新安装。`torch==2.6.0` 可匹配现有 `2.6.0+cu124` 构建，但不能保证新机器从默认软件源安装相同 CUDA 构建。迁移环境时应另行选择合适的 PyTorch wheel，并检查 NVIDIA 驱动、CTranslate2 所需 CUDA/cuBLAS/cuDNN 动态库。仅执行 `pip install -r requirements.txt` 不保证 GPU 可用；不要为匹配理论版本组合升级当前可运行环境。

## 使用与数据

将 MP3 / WAV / M4A / FLAC / AAC / OGG / MP4 放入 `input/`，运行原有入口。当前只扫描该目录的直接子文件，不递归。

- 模型：`models/large-v3/`，使用现有 CTranslate2 `model.bin`，不自动下载。
- 配置：`src/config.py`，`LANGUAGE = "en"` 为默认；可设 `"zh"`、`"auto"` 或 `None`。
- 输出：`output/meeting.mp3.txt`、`.docx`、`.json`、`.srt`、`.vtt`。源扩展名参与命名，避免与 `meeting.wav` 冲突。
- 输出格式：`src/config.py` 的 `OUTPUT_FORMATS` 默认启用五种格式；可设为 `("txt", "docx")` 或其他非空子集。导出和跳过检查使用同一配置。
- 旧版 `meeting.txt/docx` 保留，不自动迁移或认作新版任务完成。
- 日志：`logs/asr.log`，单文件约 2 MB，最多 3 个滚动备份；记录文件名、异常和耗时，不主动记录转录正文。日志中的文件路径、异常信息也应视为本地隐私数据。
- 音频、模型推理、结果和日志均在本机处理；无上传或在线翻译逻辑。

退出码为 `0` 表示无失败任务，`1` 表示任务失败或应用错误。没有输入或所有文件均已完成时不创建 WhisperModel。批次结束显示 found / processed / success / skipped / failed 和失败文件名。

## 数据流与接口

关闭翻译：`main → BatchProcessor → Transcriber → TranscriptionResult → Formatter → Exporter`

开启翻译：`ASR → 英文导出检查点 → TranslationService → Translator → TranslationResult → 双语导出`

`TranscriptionResult` 包含 `text`、`language`、`duration` 和 `segments`；每个 `Segment` 保留原始秒数 `start/end` 及文字。JSON 持久化完整结果，字幕直接使用这些 segment；TXT/DOCX 单独进行自然分段，不改变 JSON 或字幕的时间数据。`Transcriber.transcribe` 返回结构化对象，旧的外部字符串调用方需要访问 `.text`。

`Exporter.export(name, result, output_dir, formats=OUTPUT_FORMATS)` 返回按所选格式顺序排列的输出路径元组。默认返回五个路径。旧字符串调用需要显式使用 `formats=("txt", "docx")`，仍返回两个路径；字符串请求 JSON/SRT/VTT 会报错，不会伪造时间戳、语言或时长。

`BatchProcessor.run()` 返回 `BatchSummary`，可供未来界面调用；推理引擎工厂、输入输出目录可注入测试。默认推理参数保留 VAD 和 beam size 5。GPU 初始化失败会尝试 CPU/int8；迭代 segment 时出现明确 CUDA/cuBLAS/cuDNN/显存错误也会重试 CPU。会记录警告，不保证 CPU 重试必然成功。

设备初选仍沿用原有 PyTorch 检测；本次检查额外验证了 CTranslate2 能力和实际 GPU 模型加载。完整硬件探测及模型推荐属于后续阶段。

## 完成判定与恢复

完成判定根据当前 `OUTPUT_FORMATS`，不再固定为两个文件。全部所选文件必须存在、可读，并与成功导出时记录的 SHA-256 摘要一致，且没有 `.pending` 标记，才算完成。

每次导出生成 `<源文件名>.complete.json` 作为完整性记录，含版本、输出摘要及可选的翻译配置/完成状态，不含转录正文。它与保存转录数据的 `<源文件名>.json` 是两个不同文件。导出先暂存所有所选文件及完整性记录，再创建 `.pending` 标记，依次替换文件，最后发布完整性记录并移除标记。多文件替换不是一个文件系统事务：若断电或文件被 Word 占用，标记会让下次重新处理，避免误跳过。生成阶段失败不触碰旧输出；正常异常路径会清理自己的临时文件。强制终止可能留下临时目录，可在确认没有运行任务后人工检查。

缺少任何所需格式、文件内容改变、完整性记录丢失或损坏，都视为未完成。Phase 1 输出没有新记录，也会重新处理；不会仅看到旧 TXT/DOCX 就跳过新增字幕。扩大格式集合会重新处理；缩小集合可复用同一次成功导出中已验证的子集。导出较小集合时不删除其他旧格式，但新的完整性记录只认可本次生成的格式，防止混用不同批次的结果。手动编辑输出也会使摘要失配，请另存需要保留的编辑版本。

空结果允许完成：JSON 的 segments 为 `[]`，SRT 为空文件，VTT 仅含 `WEBVTT` 头及空行。不会用“文件必须非空”错误拒绝静音结果。

当前只支持单进程执行同一输出目录；不要同时启动两个实例。完成判定尚未记录输入内容指纹或 ASR 模型/语言参数：若替换了同名输入、修改了 ASR 语言或模型，请设 `SKIP_EXISTING = False` 重新处理。翻译开关、源/目标语言、后端、模型路径或 REVISION 变化会触发重新处理；未改变 REVISION 的手工权重替换不会自动识别。重新处理可能覆盖同名新版输出，请先保存需要保留的版本。

## 段落与验证范围

Formatter 只调整空白，不机械修改网址、邮箱、缩写和小数内部的标点。英文通常每 4 句或约 600 字符在句尾分段，无句号长文本约 1200 字符在词边界分段。已有空行保留。中文无空格长文本的精细分段留待后续优化。

DOCX 每个自然段对应独立 Word 段落，Calibri 11 pt、左对齐、1.15 倍行距、段后 8 pt。

自动测试在临时目录中生成文件，不读写用户音频和输出；模拟推理验证结构化数据、错误处理、GPU 回退与批次状态，不替代真实音频识别质量测试。真实音频测试须使用已有合适短音频并选择独立输出目录。

## JSON 与字幕规则

- JSON 使用标准库 `dataclasses.asdict` 和 `json`，UTF-8、`ensure_ascii=False`；保留原始 `text/language/duration` 及所有 segment 的原始浮点时间、文字，不经过 Formatter，不允许 NaN/Infinity。
- SRT：从 1 开始连续编号，`HH:MM:SS,mmm --> HH:MM:SS,mmm`。
- VTT：`WEBVTT` 头、空行，`HH:MM:SS.mmm --> HH:MM:SS.mmm`；规则参考 [W3C WebVTT](https://www.w3.org/TR/webvtt1/)。文字中的 `&`、`<`、`>` 被转义，避免作为字幕标记解释。
- 时间只来自 segment；用十进制四舍五入到最近毫秒后统一分解时分秒，正确处理跨分钟、小时及超过 24 小时的时长。不会按字数、句数或音频时长推算。
- 字幕忽略空白文字段；保留非空行，去除段内空行以免提前结束字幕块。零时长或舍入后无正时长的段会记录警告并省略字幕，绝不人工延长时间；这些段仍完整保存在 JSON 中。
- 负数、非有限时间或 end < start 会失败；字幕要求非空有效段按 start 排序，允许时间重叠，不自动排序或修改原始时间。
- 字幕/JSON 格式功能只使用标准库；翻译后端的可选依赖见下文。

## 可选本地翻译（Phase 3）

在 `src/config.py` 中设置：

```python
TRANSLATION_ENABLED = True  # 默认 False
TRANSLATION_SOURCE_LANGUAGE = "en"
TRANSLATION_TARGET_LANGUAGE = "zh-Hans"
TRANSLATION_BACKEND = "marian_local"
TRANSLATION_MODEL_PATH = PROJECT_ROOT / "models" / "opus-mt-en-zh"
```

然后仍运行 `python src/main.py`。关闭翻译时不会创建翻译后端或加载翻译模型，既有 Phase 2 JSON 结构保持不变。既有 ASR 依赖可能自行导入 Transformers，这不代表翻译已开启。没有待处理任务时，也不会加载任何推理模型。

### 模型、依赖与隐私

后端使用 [Helsinki-NLP/opus-mt-en-zh](https://huggingface.co/Helsinki-NLP/opus-mt-en-zh)，Apache-2.0；固定模型版本 `408d9bc410a388e1d9aef112a2daba955b945255`。PyTorch 权重约 312 MB，加上分词器等约 315 MB，不下载同仓库的 TensorFlow/Flax/Rust 权重。模型支持简体普通话前缀 `>>cmn_Hans<<`，输出再经 OpenCC `t2s` 统一简体。模型文件应放在独立的 `models/opus-mt-en-zh/`；已有 large-v3 不变。

本阶段固定 **CPU/FP32 翻译**，翻译模型不占 GPU 显存，可与 GPU Whisper 共存，适合当前 RTX 3060 6 GB 的显存约束；代价是翻译速度取决于 CPU。约 312 MB 是权重文件大小，不是进程 RAM 占用。建议为翻译额外预留约 2 GB 可用 RAM，整机建议 16 GB 或以上；这属于容量规划建议，长文本、库版本及 ASR 并存会影响峰值。实际样例的进程峰值可由下面的验证脚本输出。

`requirements-translation.txt` 单独记录翻译依赖。当前 `asr` 已有 Transformers 5.13.1 和 SentencePiece 0.2.2，本阶段只补充 Sacremoses 0.1.1（Marian 文本规范化）和 opencc-python-reimplemented 0.1.7（简繁转换），未升级 ASR 依赖。新环境按需执行：

```powershell
conda run -n asr --no-capture-output python -m pip install --no-user -r requirements-translation.txt
```

运行代码始终使用 `local_files_only=True`，不包含模型下载器。模型缺失时翻译失败并保留英文，不自动联网补齐。只有本次开发准备模型时访问了公开模型仓库；运行时不发送音频、视频、转录文本或译文。不需要 API key。本阶段没有在线后端；未来新后端实现 `Translator.translate(text, source_language, target_language)` 即可，通过 factory 注入，不能由现有本地后端隐式切换到在线服务。

### 对齐、失败与导出

`TranslationResult` 独立于原有 `TranscriptionResult`，包含源/目标语言、完整英文原文、完整译文和逐段结果。每段的 `start/end/original_text` 原样复制；新增 `translated_text` 和可选 `error`。单段失败只影响该段，译文设为 null 并记录错误代码，后续段继续。空白段保留位置、译文为空且不调用模型。源语言与配置不一致时拒绝错误方向的翻译，保留原文。

长 segment 按最多 256 个输入 token 内部分块并合并译文，外部 segment 和时间轴不变，不静默截断输入。输出达到模型 token 上限时将该段标为失败。逐段翻译和 token 分块可能降低跨句上下文质量，专有名词、宗教术语等需要人工复核。

- **英文检查点**：翻译开始前先导出原始结果；初始化失败、单段失败或双语导出失败，都不能删除已保存英文。
- **JSON**：原有顶层 `language/duration/text/segments` 不变，开启翻译后新增 `translation` 对象，包含完整双语数据、错误和 `complete` 标志。为了持久化原始结果和逐段译文，开启翻译时 Batch 会自动确保输出格式包含 JSON。
- **DOCX**：相邻约 4 个 segment 或累计约 600 字符形成一组，先英文自然段，再中文段；失败段显示明确占位提示。保持 Calibri 11 pt 和原有段落样式。
- **TXT/SRT/VTT**：保持英文，字幕时间轴不变。本阶段不实现双语字幕。
- **完成判定**：开启翻译后还必须匹配翻译配置且所有段翻译成功，才能跳过。翻译失败会计入 `failed` 和 `translation_failed`，退出码为 1；原始 ASR 仍已保存。下次会重新处理整个文件，目前没有仅重试翻译或断点缓存。
- 翻译阶段日志仅记录段索引和异常类型，不记录正文、译文或供应商异常响应正文。

### 验证

```powershell
conda run -n asr --no-capture-output python -m unittest discover -s tests -v
conda run -n asr --no-capture-output python tests/manual_translation_smoke.py --with-asr
```

第二条为手动、可选的真实本地模型验证：使用代码中自写的英文句子翻译，检查中文输出、段对齐、导出、完成判定，并同时加载原有 Whisper GPU 模型；不会下载模型。默认输出放入临时目录并自动清理，可用 `--output-dir` 指定独立验证目录保存样例。其中字幕时间为合成测试数据，**不是音频识别结果，也不能据此宣称真实音频端到端已验证**。

2026-10-05 本机验证：64 项自动测试通过；5 句自写英文的真实本地翻译加首次模型加载耗时约 12.1 秒，翻译阶段整个 Python 进程峰值工作集约 967.8 MiB（在加载 Whisper 前测量，不是双模型总内存）。翻译模型驻留时 large-v3 仍成功加载为 CUDA/float16。完整双语样例及测量记录保存在 `validation/phase3-translation/`。这只是功能 smoke test，不是翻译准确率评测；例如模型将 “Good morning, everyone.” 译为“大家早上好,谢谢”，存在增译，因此不能视为无需人工复核的准确翻译。

## Phase 4：麦克风近实时英文 ASR

文件入口、large-v3 配置、导出和 Translation Layer 保持原样。实时入口是 `src/realtime_demo.py`，配置独立位于 `src/realtime_config.py`。运行时不上传音频或文字，不自动下载模型，也不保存麦克风录音。

### 安装与启动

新增可选依赖 sounddevice 0.5.4（Windows wheel 附带 PortAudio）和 webrtcvad-wheels 2.0.14；numpy 2.4.4 已在环境中。没有升级现有 ASR 依赖。新环境按需安装：

```powershell
conda run -n asr --no-capture-output python -m pip install --no-user -r requirements-realtime.txt
conda run -n asr --no-capture-output python src/realtime_demo.py --list-devices
conda run -n asr --no-capture-output python src/realtime_demo.py
# 指定输入设备、GPU，并在 15 秒后停止
conda run -n asr --no-capture-output python src/realtime_demo.py --input-device 1 --device cuda --seconds 15
```

默认模型 `small` 使用本机已有 Hugging Face 缓存，权重约 483.5 MB，无新增模型下载。也可用 `--model` 指定本地 CTranslate2 模型目录。默认 auto 优先 CUDA/float16，加载失败可回退 CPU/int8；显式 cuda 不自动回退。small 的本机实测已达到近实时速度，因此没有再下载 medium。large-v3 仍仅用于原有文件流程；同时启动多个 GPU 模型的显存占用未作保证。

启动后持续打印 partial/final；Ctrl+C 停止采集并处理剩余语段。每 5 秒及停止时打印指标。`logs/realtime.log` 采用 2 MB、3 份备份的滚动日志，记录状态、错误和性能，不记录转录正文。设备不支持 16 kHz 输入或麦克风权限不足时会明确失败，不自动重采样。

### 架构、事件与时间轴

`Microphone → bounded PCM queue → WebRTC VAD / assembler → bounded ASR jobs → Whisper → bounded event dispatcher → callback`

PortAudio 回调只复制并入队音频。独立线程负责 VAD/组句、Whisper 推理、事件回调；采集所有者负责打开/关闭麦克风和协调退出。任何 Whisper 推理或用户回调都不在音频采集回调中执行。

默认单声道 PCM16 / 16 kHz / 30 ms 帧，WebRTC VAD mode 2；连续 3 帧语音触发开始，保留 210 ms 前滚，600 ms 静音结束语段；每约 1 秒请求一次 partial，单个语段最多 8 秒，避免无限缓冲。不会逐个小帧调用 Whisper。final 裁掉尾部静音，停止时也会提交未完成语段。

事件包含 `speech_started / partial_transcript / final_transcript / speech_ended / error / stopped`。使用 `(session_id, utterance_id)` 对齐；同一语段的 partial 是可替换快照，已结束语段的过期 partial 会被抑制。final 为不可变对象，包含 `text/start/end/language`，之后不会被 partial 修改。`speech_ended` 表示组句结束，final 可能稍后才到达。final 的 `reason` 区分 `silence/max_duration/stop/audio_gap`。

时间为本次会话的音频采样位置，包含前滚；这是语段时间，不是 Whisper 单词对齐时间。已知队列丢帧会打断语段，避免把不连续音频直接拼接；驱动溢出的未知丢失时长无法精确恢复。

从 `src` 可导入以下接口：

```python
from realtime import RealtimeSession
from realtime_config import RealtimeConfig

session = RealtimeSession(lambda event: print(event), RealtimeConfig(model="small"))
try:
    session.start()
    input("Press Enter to stop\n")
finally:
    session.stop()
# stop 完全结束后，同一对象可再次 start；每次会话有新 session_id。
```

回调在单一 dispatcher 线程运行，应快速返回；可调用 `request_stop()`。回调内部调用 `stop()` 只请求退出并返回 False，避免自等待；由所有者线程调用 stop 完成等待。外部 stop 默认等待 30 秒，无法完成则抛出 TimeoutError，并禁止旧线程尚存时 restart。Python 不能强制安全终止卡住的原生推理或任意用户回调，因此不会在超时后假报已停止。

### 有界队列及过载策略

- 音频队列默认 100 帧（约 3 秒）；满时丢最旧帧，记录计数和警告，保持采集非阻塞。
- partial 只有一个最新待处理槽，旧请求合并；final 优先处理。
- final 队列默认最多 4 个、每段最多 8 秒；持续过载时拒绝新语段、计数并报错停止，保留此前已排队的 final。
- 事件队列默认 128 项；优先合并/丢弃 partial。关键事件占满时停止采集并等待回调释放空间，不静默丢弃已生成 final。额外保留一个错误槽。
- 所有指标为累计值或当前值，不在核心内无限保存事件历史。调用者若自行存储事件，需自行限制容量。

指标包括推理次数/总耗时、单次事件推理耗时、各队列当前积压及高水位、丢弃帧/样本数、PortAudio 溢出次数和端点延迟。端点延迟从最后一个有声帧被接收至 final 创建，包含 VAD 等待、排队和推理，不含 UI/回调渲染等待；强制切块/停止的延迟不能直接与自然静音端点相比。应用丢帧数可精确统计，驱动溢出只有次数，不能假装知道其丢失样本数。

### 验证及手动麦克风测试

```powershell
conda run -n asr --no-capture-output python -m unittest discover -s tests -v
conda run -n asr --no-capture-output python tests/manual_realtime_benchmark.py validation/phase4-realtime/authored-sapi-fixture.wav --report validation/phase4-realtime/small-gpu-report.json --device cuda
```

91 项自动测试通过，其中原有 64 项回归测试保持通过。新增覆盖生命周期、重复启停、静音、事件顺序、partial/final 隔离、队列过载、采集/推理/VAD/回调异常、空音频、停止超时和资源关闭。大部分状态机测试使用注入的模拟组件；另验证实际 WebRTC VAD 的数字静音。

性能验证使用 Windows SAPI 生成的 11.235 秒英文合成语音，按 30 ms 实时节奏送入真实 WebRTC VAD 和 GPU small；不是人声录音或麦克风测试。逐事件测量、推理耗时和队列指标见 `validation/phase4-realtime/small-gpu-report.json`。最终版本复测有 9 次 partial、3 条 final，自然端点延迟 0.734–0.875 秒、中位数 0.735 秒，无音频丢帧；这不是正式准确率或长时间稳定性评测。

另在正常 Windows 桌面权限下实际打开默认 Realtek 麦克风约 5 秒：采集 166 帧、4 次 partial、1 条停止时提交的 final，无队列丢帧/驱动溢出，所有队列排空并成功退出；未保存录音。沙箱内打开设备曾失败，桌面会话重试成功。没有指定的人声朗读参考，检测到的文字不足以证明人声准确率，也说明环境噪声/误触发需进一步实测。

人工 smoke test：先列设备，启动 15–30 秒测试；朗读一段已知英文，停顿至少 1 秒，检查 final 不再被后续 partial 改写；讲话中按 Ctrl+C，确认最后语段与 stopped；再次启动，确认设备可重新打开。保持安静检查误触发，并核对 dropped 计数。不要把模拟音频测试代替此步骤。

Phase 4 ASR 限制：噪声可能误触发 VAD 并引起 Whisper 幻觉；8 秒硬切块可能损失跨边界单词和上下文；CPU ASR 延迟未评测；未进行长时间运行或多设备兼容测试；实时结果通过事件/终端输出，没有接入文件导出。可选实时翻译见下文 Phase 5。

## Phase 5：独立实时翻译

启用方式（不加 `--translate` 时仍使用 Phase 4 原有 RealtimeSession）：

```powershell
conda run -n asr --no-capture-output python src/realtime_demo.py --translate
conda run -n asr --no-capture-output python src/realtime_demo.py --translate --seconds 30 --translation-target zh-Hans --translation-backend marian_local
```

partial 仅显示英文；final 显示 `[EN FINAL #编号]`，翻译完成显示 `[ZH #编号]`。两个回调线程独立，中文可晚于后续英文出现，调用者使用会话 ID 和语段编号配对。运行时不上传文字或音频，不下载模型。本阶段没有新依赖，也没有修改文件转录/文件翻译逻辑。

### 队列、模型与事件

`RealtimeSession final → RealtimeTranslation.submit → 有界 FIFO → translation worker → CPU 子进程 → 翻译事件队列 → 翻译回调`

`src/realtime_translation.py` 提供 `RealtimeTranslationConfig`、`RealtimeTranslation` 和组合接口 `TranslatedRealtimeSession`。实时 ASR 核心仅增加事件创建时刻 `created_at`，用于计算包含事件派发等待的延迟；不改变 VAD、音频队列或推理逻辑。英文和翻译可以使用不同 callback；翻译回调不占用 ASR dispatcher。应用自己的英文回调仍应快速返回。

配置包括 `enabled=False`、`target_language="zh-Hans"`、`backend="marian_local"`、独立模型路径、`queue_size=8`、`event_queue_size=64`、`request_timeout=60` 和 `shutdown_timeout=15`（秒）。目前本地后端仍只支持英文到简体中文；无效目标/后端通过翻译失败事件报告，英文继续。后续后端可通过独立 translator factory 注入，Windows spawn 要求 factory 可序列化且定义在模块顶层。

复用 Phase 3 的 `create_translator` 和 `MarianLocalTranslator`，使用已有 Helsinki-NLP/opus-mt-en-zh + OpenCC，明确 CPU 推理，不加载到 Whisper GPU。每次实时会话首次翻译时才启动子进程并加载模型，同一会话所有语段复用该实例。重新 start 是新会话，会重新加载；没有后台常驻模型管理器。

仅 final 入队；partial、其他会话和重复/过期 final 不触发翻译。去重使用本会话单调递增的 utterance_id，不保存无限增长的历史集合。原文和 start/end 原样复制到不可变的 `TranslationEvent`，不重新估算时间轴。

事件为 `translation_started`、`translation_completed`、`translation_failed`，包含会话/语段 ID、原文、译文、start/end、源语言和目标语言；完成事件另含翻译延迟、总延迟和本次调用耗时。空文字返回空译文，不加载模型。单段异常产生失败事件并继续处理后续语段；初始化失败在该会话内缓存，避免反复加载。进程崩溃/请求超时后，该会话后续请求明确失败，英文仍继续；重新开始会话后可重试。

- 翻译队列最多 8 条待处理 final，另有 1 条执行中；队列满时拒绝最新翻译，保留已接受任务，发出失败事件，记录 dropped_translations 和日志。submit 不等待翻译或用户翻译回调。
- 翻译事件队列最多 64 项。极慢的翻译事件消费者会造成事件丢弃，并增加 dropped_events 和警告；不会反向阻塞英文 ASR。此指标与 dropped_translations 分开，前者是通知未送达，后者是翻译任务因队列满而拒绝。没有无限保留结果的缓存。
- 日志只记录错误类型、耗时和队列情况，不写原文或译文。CLI 终端按请求显示双语内容。

### 停止与复用

组合接口先停止麦克风和 ASR，等待最后的英文 final 派发完成，再关闭翻译入队并尽量排空已接受任务。翻译默认最多等待 15 秒，超时的当前/待处理任务产生失败事件；阻塞的翻译模型进程会被 terminate，必要时 kill，清理阶段最多额外等待约 5 秒。正常空闲进程通过退出消息关闭。测试验证了无限慢翻译不会永久卡住 stop。

任意用户回调本身若永久阻塞，Python 不能安全强杀其线程；此时 stop 明确抛出 TimeoutError、拒绝重启，不假报已清理。回调内应调用 `request_stop()`，由所有者线程调用 `stop()` 完成等待。`stopped` 仍是 ASR 停止事件，中文可能随后到达；组合接口 stop 返回 True 才代表两条流水线均已结束。

Windows 中使用组合接口的自定义脚本必须将运行入口放在 `if __name__ == "__main__":` 内，避免 spawn 重复执行主程序。

### 指标与实测

`translation_latency_seconds` 从英文 final 创建至中文结果就绪，包括 ASR 事件派发、翻译排队、首次加载与推理；`end_to_end_latency_seconds` 加上 ASR 已测的端点延迟，即最后有声帧接收到中文就绪。不含中文 UI 渲染。子进程返回的 `inference_seconds` 包含首次模型初始化（若发生），后续才是纯翻译调用耗时。两种时间不可混用。metrics 提供 backlog、高水位、完成/失败/丢弃次数及最近延迟。

可重复验证（使用 Phase 4 合成英文 WAV，非真实麦克风）：

```powershell
conda run -n asr --no-capture-output python tests/manual_realtime_benchmark.py validation/phase4-realtime/authored-sapi-fixture.wav --report validation/phase5-realtime-translation/repeated-replay-report.json --device cuda --translate --passes 2
```

2026-10-05 同一会话两次回放：18 次 partial、6 条 final、6 条中文；818 帧音频，无音频丢帧、无翻译丢弃、无回调事件丢弃。ASR 端点延迟 0.703–0.797 秒，中位数 0.734 秒。首次中文含冷启动为 13.954 秒；积压消退后最后两条 final→中文为 0.516 / 0.328 秒，总端点→中文为 1.297 / 1.031 秒。最初三条及第二次回放的第一条受到冷启动排队影响，不能把这些数值当作长期延迟分布。单次独立冷启动测试首次翻译为 15.234 秒。

逐事件及完整指标保存在 `validation/phase5-realtime-translation/replay-report.json` 和 `repeated-replay-report.json`。本阶段未再次打开真实麦克风；此前 Phase 4 麦克风验证不代表本阶段双语麦克风链路已实测。翻译示例中 local 被译为“当地”，沿用现有模型质量，未做质量改造。

完整自动测试 108 项通过（原有 91 项 + 新增 17 项）。新增测试覆盖 final-only、禁用翻译、逐段对齐/中文、复用、空文本、失败、溢出、进程崩溃/启动异常、超时清理、重复启停、慢翻译不阻塞英文和慢/异常回调。语法检查和 CLI 参数检查通过；所有 Python/测试操作均在 Conda asr 中执行。

## Phase 5 时的后续规划（历史记录）

建议 Phase 6 优先进行真实麦克风双语测试和长时间压力测试，并改善冷启动体验（例如明确的模型准备状态）。随后再规划 GUI 接口；本阶段没有 GUI、云翻译、总结或安装包。


